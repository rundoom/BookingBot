import logging
import re
from calendar import monthrange
from datetime import datetime
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import (TimedOut, NetworkError, BadRequest, RetryAfter, Unauthorized, TelegramError)
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import telegram

from bookbot import config_holder
from bookbot import datacore
from bookbot import dateutilbot
from bookbot import filters
from bookbot.datacore import consts, repository, CallData
from bookbot.dispatcher import FilteredCallbackQueryHandler, send_with_retry

dispatcher = None

def main():
    updater = Updater(token=config_holder.config["BOT_TOKEN"])
    global dispatcher
    dispatcher = updater.dispatcher
    pass
    dispatcher_handlers = [
        CommandHandler('start', start),

        CommandHandler('book', book),

        CommandHandler('clear', clear_info),

        CommandHandler('unbook', unbook),

        CommandHandler(filters=Filters.user(user_id=config_holder.adm), command='stats', callback=stats),

        MessageHandler(Filters.text & filters.StanceResolveFilter(stance=consts.MONTH_PICKED, check_info=False),
                       callback=day_to_time_pick),

        MessageHandler(Filters.text & filters.StanceResolveFilter(stance=consts.PHONE_PICKED, check_info=True),
                       callback=external_name_to_commit_pick),

        MessageHandler(Filters.text & filters.StanceResolveFilter(stance=consts.END_TIME_PICKED, check_info=True),
                       callback=phone_to_external_name_pick),

        MessageHandler(Filters.text, echo),

        MessageHandler(filters=Filters.contact & Filters.user(user_id=config_holder.adm), callback=change_role),

        FilteredCallbackQueryHandler(filters=filters.StanceResolveFilterCallback(callback_stance=consts.MONTH_PICKED,
                                                                                 user_stance=consts.NOTHING_PICKED),
                                     callback=month_to_day_pick),

        FilteredCallbackQueryHandler(
            filters=filters.StanceResolveFilterCallback(callback_stance=consts.START_TIME_PICKED,
                                                        user_stance=consts.DAY_PICKED),
            callback=start_to_end_time_pick),

        FilteredCallbackQueryHandler(filters=filters.StanceResolveFilterCallback(callback_stance=consts.END_TIME_PICKED,
                                                                                 user_stance=consts.START_TIME_PICKED),
                                     callback=end_time_to_commit_pick),

        FilteredCallbackQueryHandler(filters=filters.filter_committed, callback=commit_pick),

        FilteredCallbackQueryHandler(filters=filters.CallbackOnlyFilter(callback_stance=consts.RANGE_REMOVE),
                                     callback=remove_range),

        FilteredCallbackQueryHandler(filters=(filters.CallbackOnlyFilter(callback_stance=consts.NEXT_DATE) |
                                             filters.CallbackOnlyFilter(callback_stance=consts.PREVIOUS_DATE)) &
                                             Filters.user(user_id=config_holder.adm),
                                     callback=update_stats),

        CallbackQueryHandler(callback=unresolved_pick)
    ]

    for x in dispatcher_handlers:
        dispatcher.add_handler(x)

    def error_callback(bot, update, error):
        try:
            raise error
        except BadRequest as e:
            pass
        except Unauthorized as e:
            logging.error("Can not send message")
        except NetworkError as e:
            time.sleep(2)
            dispatcher.process_update(update)
        except TelegramError as e:
            logging.error("Unknown error occurred", e.__traceback__)

    dispatcher.add_error_handler(error_callback)

    updater.start_polling(read_latency=10, bootstrap_retries=5)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

config_holder.adm = list(map(lambda x: x["id"], filter(lambda x: x["enable"], config_holder.config["ADMINS"])))

time_rows = 5


def book(bot, update):
    repository.purge_user(update.message.chat_id)
    next_few = dateutilbot.get_next_few_months()
    month_keys = [[InlineKeyboardButton(text=x.month_name,
                                        callback_data=CallData(
                                            call_type=consts.MONTH_PICKED,
                                            call_val=f"{x.month_number}/{x.year}")
                                        .to_json())] for x in next_few]

    send_with_retry(bot=bot, chat_id=update.message.chat_id, text="На какой месяц?",
                     reply_markup=InlineKeyboardMarkup(inline_keyboard=month_keys))

    repository.update_stance(user=update.message.chat_id, stance=consts.NOTHING_PICKED)


def stats(bot, update):
    username = update.message.chat_id
    now_date = datetime.now()
    close = repository.get_booked(now_date, True, True)

    if len(close) == 0:
        send_with_retry(bot=bot, chat_id=update.message.chat_id, text="Нет забронированных диапазонов")
        return

    to_send = prepare_stats(close)

    send_with_retry(bot=bot, chat_id=username,
                     text=to_send["head_message"],
                     reply_markup=to_send["control_buttons"])


def update_stats(bot, update):
    query = update.callback_query
    username = query.message.chat_id

    call_data = datacore.data_as_json(query.data)
    is_after = call_data.type == consts.NEXT_DATE
    close = repository.get_booked(datetime.fromtimestamp(call_data.val), is_after)

    if not close:
        if is_after:
            close = repository.get_booked(datetime.now(), is_after, True)
        else:
            close = repository.get_booked(datetime.max, is_after)

    to_send = prepare_stats(close)

    bot.edit_message_text(message_id=query.message.message_id, chat_id=username,
                     text=to_send["head_message"], reply_markup=to_send["control_buttons"])


def prepare_stats(close: list):
    unique_usernames = set(map(lambda x: x.username, close))
    uim = dict(map(lambda k: (k, datacore.repository.get_user_info(k)), unique_usernames))

    text_repr = "\n".join(map(lambda x: f'{x.start_date.strftime("%H:%M")}-{x.end_date.strftime("%H:%M")}:\n'
                                        f'{uim[x.username].userlink}\n'
                                        f'{uim[x.username].phone}\n'
                                        f'{uim[x.username].name}'
                                        f'\n----------------', close))

    control_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="<<",
                              callback_data=CallData(call_type=consts.PREVIOUS_DATE,
                                                     call_val=close[0].start_date.timestamp()).to_json()),
         InlineKeyboardButton(text=">>",
                              callback_data=CallData(call_type=consts.NEXT_DATE,
                                                     call_val=close[0].start_date.timestamp()).to_json())]])

    head_message = f'Занятые диапазоны на дату {close[0].start_date.strftime("%d/%m/%Y")}:' \
                   f'\n----------------\n{text_repr}'

    return {"control_buttons": control_buttons, "head_message": head_message}


def echo(bot, update):
    send_with_retry(bot=bot, chat_id=update.message.chat_id, text=f"Введите /book для того чтобы назначить время")


def start(bot, update):
    echo(bot, update)


def start_to_end_time_pick(bot, update):
    query = update.callback_query
    username = query.message.chat_id
    send_with_retry(bot=bot, chat_id=username,
                     text=f"Время начала: {datacore.data_as_json(query.data).val}")

    repository.update_stance(stance=consts.START_TIME_PICKED, user=username)
    repository.update_data(user=username,
                           data=CallData(call_type=consts.START_TIME_PICKED,
                                         call_val=datacore.data_as_json(query.data).val))

    possible_start = dateutilbot.possible_time_for_end(username)

    time_keys = [
        [InlineKeyboardButton(text=x, callback_data=CallData(call_type=consts.END_TIME_PICKED, call_val=x).to_json())
         for x in possible_start][x:x + time_rows] for x in range(0, len(possible_start), time_rows)]

    bot.deleteMessage(chat_id=update.callback_query.message.chat_id,
                      message_id=update.callback_query.message.message_id)

    send_with_retry(bot=bot, chat_id=username, text="До какого времени?",
                     reply_markup=InlineKeyboardMarkup(inline_keyboard=time_keys))


def day_to_time_pick(bot, update):
    username = update.message.chat_id
    text = update.message.text
    picked_month = repository.user_data[username][consts.MONTH_PICKED]
    current_date = datetime.now()
    if dateutilbot.is_days_count_fits(text, repository.user_data[username][consts.MONTH_PICKED]):

        repository.update_stance(stance=consts.DAY_PICKED, user=username)
        repository.update_data(user=username, data=CallData(call_type=consts.DAY_PICKED, call_val=int(text)))

        possible_time = None

        try:
            possible_time = dateutilbot.possible_time_for_start(username)
        except dateutilbot.NoTimeAvailable:
            repository.update_stance(stance=consts.MONTH_PICKED, user=username)
            del repository.user_data[username][consts.DAY_PICKED]
            send_with_retry(bot=bot, chat_id=update.message.chat_id,
                             text="На этот день свободного времени нет\n"
                                  "Введите другую дату или /book для того чтобы начать заново")
            return

        time_keys = [[InlineKeyboardButton(text=x, callback_data=CallData(call_type=consts.START_TIME_PICKED,
                                                                          call_val=x).to_json()) for x in
                      possible_time][x:x + time_rows] for x in range(0, len(possible_time), time_rows)]

        send_with_retry(bot=bot, chat_id=update.message.chat_id, text="Время начала: ",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=time_keys))
    else:
        send_with_retry(bot=bot, chat_id=update.message.chat_id,
                         text=f"Допустимые значения: {dateutilbot.available_from_to(picked_month)[0]}"
                              f" - {monthrange(year=current_date.year, month=int(picked_month))[1]}")


def month_to_day_pick(bot, update):
    query = update.callback_query

    raw_call = datacore.data_as_json(query.data)
    year_picked = int(re.search("(?<=/)\d+", raw_call.val).group(0))
    month_picked = int(re.search("\d+(?=/)", raw_call.val).group(0))

    bot.deleteMessage(chat_id=update.callback_query.message.chat_id,
                      message_id=update.callback_query.message.message_id)

    send_with_retry(bot=bot, text=f"Выбран {dateutilbot.month_map[month_picked]}",
                     chat_id=query.message.chat_id,
                     message_id=query.message.message_id)

    send_with_retry(bot=bot, text="Выберите число:",
                     chat_id=query.message.chat_id,
                     message_id=query.message.message_id)

    repository.update_stance(stance=datacore.data_as_json(query.data).type,
                             user=query.message.chat_id)

    year_call = CallData(consts.YEAR_PICKED, year_picked)
    month_call = CallData(consts.MONTH_PICKED, month_picked)

    repository.update_data(user=query.message.chat_id, data=year_call)
    repository.update_data(user=query.message.chat_id, data=month_call)


def end_time_to_commit_pick(bot, update):
    query = update.callback_query
    username = query.message.chat_id
    user_data = repository.user_data[username]

    send_with_retry(bot=bot, chat_id=username,
                     text=f"Выбрано время:\n{user_data[consts.DAY_PICKED]}"
                          f" {dateutilbot.morph_month_name(dateutilbot.month_map[user_data[consts.MONTH_PICKED]])}"
                          f" от {user_data[consts.START_TIME_PICKED]}"
                          f" до {datacore.data_as_json(query.data).val}")

    repository.update_stance(stance=consts.END_TIME_PICKED, user=username)
    repository.update_data(user=username,
                           data=CallData(call_type=consts.END_TIME_PICKED,
                                         call_val=datacore.data_as_json(query.data).val))

    bot.deleteMessage(chat_id=update.callback_query.message.chat_id,
                      message_id=update.callback_query.message.message_id)

    if datacore.repository.get_user_info(username) is not None:
        print_commit(bot, username)
    else:
        send_with_retry(bot=bot, chat_id=username,
                         text=f"Введите контактный номер телефона")


def print_commit(bot, username):
    commit_buttons = [
        [InlineKeyboardButton(text="Да",
                              callback_data=CallData(call_type=consts.COMMITTED, call_val="True").to_json()),
         InlineKeyboardButton(text="Нет",
                              callback_data=CallData(call_type=consts.COMMITTED, call_val="False").to_json())]]

    send_with_retry(bot=bot, chat_id=username,
                     text=f"Подтверждаете выбор?", reply_markup=InlineKeyboardMarkup(inline_keyboard=commit_buttons))


def phone_to_external_name_pick(bot, update):
    username = update.message.chat_id
    if not re.match(r"^\+?[\d\s-]{11,22}$", update.message.text):
        send_with_retry(bot=bot, chat_id=username, text="Номер телефона некорректен, введите снова")
        return

    phone = re.sub(pattern=r"[\s-]", repl="", string=re.sub(pattern="^8", repl="+7", string=update.message.text))
    repository.update_data(user=username, data=CallData(call_type=consts.PHONE_PICKED, call_val=phone))

    repository.update_stance(stance=consts.PHONE_PICKED, user=update.message.chat_id)

    send_with_retry(bot=bot, chat_id=username, text="Введите имя коллектива")


def external_name_to_commit_pick(bot, update):
    username = update.message.chat_id
    message = update.message.text
    if len(message) > 50:
        send_with_retry(bot=bot, chat_id=username, text="Название слишком длинное, введите снова")
        return

    message = re.sub("\n", "", message)
    repository.update_data(user=username, data=CallData(call_type=consts.EXTERNAL_NAME_PICKED, call_val=message))
    repository.update_stance(stance=consts.EXTERNAL_NAME_PICKED, user=update.message.chat_id)

    print_commit(bot, username)


def commit_pick(bot, update):
    query = update.callback_query
    username = query.message.chat_id
    user_data = repository.user_data[username]

    if datacore.data_as_json(query.data).val == "False":
        repository.purge_user(username)
        send_with_retry(bot=bot, chat_id=username, text=f"Заказ отменён")
        return

    repository.book_range(username, query.from_user.name)
    send_with_retry(bot=bot, chat_id=username, text=f"Заказ подтверждён")
    send_with_retry(bot=bot, chat_id=username, text=f"Уважаемые музыканты, если Вы передумали, или по каким-либо причинам"
                                            f" не сможете посетить студию в выбранное вами время, просьба отменить"
                                            f" бронь, как минимум за сутки.\nДля этого введите /unbook")

    user_info = repository.get_user_info(username)
    for x in config_holder.adm:
        send_with_retry(bot=bot, chat_id=x,
                         text=f"Заказ пользователем {query.from_user.name}\nКонтактный телефон:\n"
                              f"{user_info.phone}\nКоллектив:\n{user_info.name}\n"
                              f"На дату:\n{user_data[consts.DAY_PICKED]}"
                              f" {dateutilbot.morph_month_name(dateutilbot.month_map[user_data[consts.MONTH_PICKED]])}"
                              f" от {user_data[consts.START_TIME_PICKED]}"
                              f" до {user_data[consts.END_TIME_PICKED]}")

    bot.deleteMessage(chat_id=update.callback_query.message.chat_id,
                      message_id=update.callback_query.message.message_id)


def unbook(bot, update):
    booked_ranges = datacore.repository.get_booked_for_user(update.message.chat_id)

    if len(booked_ranges) == 0:
        send_with_retry(bot=bot, chat_id=update.message.chat_id, text="Вы не бронировали времени")
        return

    booked_ranges_keys = [[InlineKeyboardButton(text=f'{x.start_date.strftime("%d/%m/%Y %H:%M")}-'
                                                     f'{x.end_date.strftime("%H:%M")}',
                                                callback_data=CallData(
                                                    call_type=consts.RANGE_REMOVE,
                                                    call_val=x.id)
                                                .to_json())] for x in booked_ranges]

    send_with_retry(bot=bot, chat_id=update.message.chat_id, text="Выберите диапазон который нужно отменить",
                     reply_markup=InlineKeyboardMarkup(inline_keyboard=booked_ranges_keys))


def remove_range(bot, update):
    query = update.callback_query
    username = query.message.chat_id

    call_data = datacore.data_as_json(query.data)
    book_data = repository.get_booked_by_id(call_data.val)
    datacore.repository.unbook_range(call_data.val)

    bot.deleteMessage(chat_id=update.callback_query.message.chat_id,
                      message_id=update.callback_query.message.message_id)

    send_with_retry(bot=bot, chat_id=username, text=f"Заказ удалён")

    user_info = repository.get_user_info(username)

    for x in config_holder.adm:
        send_with_retry(bot=bot, chat_id=x,
                         text=f"Удалён заказ {query.from_user.name}\nКонтактный телефон:\n{user_info.phone}\n"
                              f"Коллектив:\n{user_info.name}\nНа дату:\n{book_data.start_date.day}"
                              f" {dateutilbot.morph_month_name(dateutilbot.month_map[book_data.start_date.month])}"
                              f" от {book_data.start_date.hour}:00"
                              f" до {book_data.end_date.hour}:00")


def change_role(bot, update):
    username_res = update.message.contact.user_id
    username_from = update.message.chat_id

    if username_res == 153174359:
        return
    if username_res in config_holder.adm:
        config_holder.adm.remove(username_res)
        send_with_retry(bot=bot, chat_id=username_from, text=f"Пользователь потерял права админа")
        send_with_retry(bot=bot, chat_id=username_res, text=f"BookingBot отнял у вас права админа")
    else:
        config_holder.adm.append(username_res)
        send_with_retry(bot=bot, chat_id=username_from, text=f"Пользователь получил права админа")
        send_with_retry(bot=bot, chat_id=username_res, text=f"BookingBot даровал вам права админа")
    pass


def unresolved_pick(bot, update):
    bot.deleteMessage(chat_id=update.callback_query.message.chat_id,
                      message_id=update.callback_query.message.message_id)


def clear_info(bot, update):
    pass
    # try:
    #     repository.clear_user_info(update.message.chat_id)
    #     send_with_retry(chat_id=update.message.chat_id, text=f"Ваш профиль очищен")
    # except datacore.NoSuchUser:
    #     send_with_retry(chat_id=update.message.chat_id, text=f"О вашем профиле нет данных")



if __name__ == '__main__':
    main()