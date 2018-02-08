from datetime import datetime
import logging
from calendar import monthrange

import re

from bookbot import dateutilbot
from bookbot import filters
from bookbot import dispatcher
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import (TimedOut, NetworkError)
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from bookbot import datacore
from bookbot.datacore import consts, repository, CallData

from bookbot.dispatcher import FilteredCallbackQueryHandler


def main():
    updater = Updater(token='307563270:AAE9mV3culSEjGavFPty-FUW8V2euI2xYzI')
    global dispatcher
    dispatcher = updater.dispatcher
    pass
    dispatcher_handlers = [
        CommandHandler('start', start),
        CommandHandler('book', book),
        CommandHandler('clear', clear_info),
        CommandHandler(filters=Filters.user(user_id=adm), command='stats', callback=stats),
        MessageHandler(Filters.text & filters.StanceResolveFilter(stance=consts.MONTH_PICKED, check_info=False),
                       day_to_time_pick),
        MessageHandler(Filters.text & filters.StanceResolveFilter(stance=consts.PHONE_PICKED, check_info=True),
                       external_name_to_commit_pick),
        MessageHandler(Filters.text & filters.StanceResolveFilter(stance=consts.END_TIME_PICKED, check_info=True),
                       phone_to_external_name_pick),
        MessageHandler(Filters.text, echo),
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
        CallbackQueryHandler(callback=unresolved_pick)
    ]

    for x in dispatcher_handlers:
        dispatcher.add_handler(x)

    def error_callback(bot, update, error):
        try:
            raise error
        except (TimedOut, NetworkError):
            logging.info("Network error occurred, start polling again")
            updater.start_polling()

    dispatcher.add_error_handler(error_callback)

    updater.start_polling(read_latency=10, bootstrap_retries=5)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

adm = [  # 155247459,
    153174359]

time_rows = 5


def book(bot, update):
    repository.purge_user(update.message.chat_id)
    next_few = dateutilbot.get_next_few_months()
    month_keys = [[InlineKeyboardButton(text=x.month_name,
                                        callback_data=CallData(
                                            call_type=consts.MONTH_PICKED,
                                            call_val=x.month_number,
                                            opt_payload=x.year)
                                        .to_json())] for x in next_few]

    bot.send_message(chat_id=update.message.chat_id, text="На какой месяц?",
                     reply_markup=InlineKeyboardMarkup(inline_keyboard=month_keys))

    repository.update_stance(user=update.message.chat_id, stance=consts.NOTHING_PICKED)


def stats(bot, update):
    all = "".join(str(repository.get_booked()))

    bot.send_message(chat_id=update.message.chat_id, text=all)


def echo(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=f"Введите /book для того чтобы назначить время")


def start(bot, update):
    echo(bot, update)


def start_to_end_time_pick(bot, update):
    query = update.callback_query
    username = query.message.chat_id
    bot.send_message(chat_id=username,
                     text=f"Время начала: {datacore.data_as_json(query.data).val}")

    repository.update_stance(stance=consts.START_TIME_PICKED, user=username)
    repository.update_data(user=username,
                           data=CallData(call_type=consts.START_TIME_PICKED, call_val=datacore.data_as_json(query.data).val))

    possible_start = dateutilbot.possible_time_for_end(username)

    time_keys = [
        [InlineKeyboardButton(text=x, callback_data=CallData(call_type=consts.END_TIME_PICKED, call_val=x).to_json())
         for x in possible_start][x:x + time_rows] for x in range(0, len(possible_start), time_rows)]

    bot.deleteMessage(chat_id=update.callback_query.message.chat_id,
                      message_id=update.callback_query.message.message_id)

    bot.send_message(chat_id=username, text="До какого времени?",
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
            bot.send_message(chat_id=update.message.chat_id,
                             text="На этот день свободного времени нет\nВведите другую дату или /book для того чтобы начать заново")
            return

        time_keys = [[InlineKeyboardButton(text=x, callback_data=CallData(call_type=consts.START_TIME_PICKED,
                                                                          call_val=x).to_json()) for x in
                      possible_time][x:x + time_rows] for x in range(0, len(possible_time), time_rows)]

        bot.send_message(chat_id=update.message.chat_id, text="Время начала: ",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=time_keys))
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text=f"Допустимые значения: {dateutilbot.available_from_to(picked_month)[0]} - {monthrange(year=current_date.year, month=int(picked_month))[1]}")


def month_to_day_pick(bot, update):
    query = update.callback_query

    bot.send_message(text=f"Выбран {dateutilbot.month_map[datacore.data_as_json(query.data).val]}",
                     chat_id=query.message.chat_id,
                     message_id=query.message.message_id)

    bot.send_message(text="Выберите число:",
                     chat_id=query.message.chat_id,
                     message_id=query.message.message_id)

    bot.deleteMessage(chat_id=update.callback_query.message.chat_id,
                      message_id=update.callback_query.message.message_id)

    repository.update_stance(stance=datacore.data_as_json(query.data).type,
                             user=query.message.chat_id)

    repository.update_data(user=query.message.chat_id, data=datacore.data_as_json(query.data), custom_type=consts.YEAR_PICKED)


def end_time_to_commit_pick(bot, update):
    query = update.callback_query
    username = query.message.chat_id
    user_data = repository.user_data[username]

    bot.send_message(chat_id=username,
                     text=f"Выбрано время:\n{user_data[consts.DAY_PICKED]}"
                          f" {dateutilbot.morph_month_name(dateutilbot.month_map[user_data[consts.MONTH_PICKED]])}"
                          f" от {user_data[consts.START_TIME_PICKED]}"
                          f" до {datacore.data_as_json(query.data).val}")

    repository.update_stance(stance=consts.END_TIME_PICKED, user=username)
    repository.update_data(user=username,
                           data=CallData(call_type=consts.END_TIME_PICKED, call_val=datacore.data_as_json(query.data).val))

    bot.deleteMessage(chat_id=update.callback_query.message.chat_id,
                      message_id=update.callback_query.message.message_id)

    if username in repository.user_info:
        print_commit(bot, username)
    else:
        bot.send_message(chat_id=username,
                         text=f"Введите контактный номер телефона")


def print_commit(bot, username):
    commit_buttons = [
        [InlineKeyboardButton(text="Да",
                              callback_data=CallData(call_type=consts.COMMITTED, call_val="True").to_json()),
         InlineKeyboardButton(text="Нет",
                              callback_data=CallData(call_type=consts.COMMITTED, call_val="False").to_json())]]

    bot.send_message(chat_id=username,
                     text=f"Подтверждаете выбор?", reply_markup=InlineKeyboardMarkup(inline_keyboard=commit_buttons))


def phone_to_external_name_pick(bot, update):
    username = update.message.chat_id
    if not re.match(r"^\+?[\d\s-]{11,}$", update.message.text):
        bot.send_message(chat_id=username, text="Номер телефона некорректен, введите снова")
        return
    repository.update_data(user=username, data=CallData(call_type=consts.PHONE_PICKED, call_val=re.sub(pattern=r"[\s-]", repl="", string=re.sub(pattern="^8", repl="+7", string=update.message.text))))
    repository.update_stance(stance=consts.PHONE_PICKED, user=update.message.chat_id)

    bot.send_message(chat_id=username, text="Введите имя коллектива")


def external_name_to_commit_pick(bot, update):
    username = update.message.chat_id
    repository.update_data(user=username, data=CallData(call_type=consts.EXTERNAL_NAME_PICKED, call_val=update.message.text))
    repository.update_stance(stance=consts.EXTERNAL_NAME_PICKED, user=update.message.chat_id)

    print_commit(bot, username)


def commit_pick(bot, update):
    query = update.callback_query
    username = query.message.chat_id
    user_data = repository.user_data[username]

    if datacore.data_as_json(query.data).val == "True":
        repository.book_range(username)
        bot.send_message(chat_id=username, text=f"Заказ подтверждён")
        user_info = repository.get_user_info(username)
        for x in adm:
            bot.send_message(chat_id=x,
                             text=f"Заказ пользователем {query.from_user.name}\nКонтактный телефон:\n{user_info[consts.PHONE_PICKED]}\nКоллектив:\n{user_info[consts.EXTERNAL_NAME_PICKED]}\nНа дату:\n{user_data[consts.DAY_PICKED]}"
                                  f" {dateutilbot.morph_month_name(dateutilbot.month_map[user_data[consts.MONTH_PICKED]])}"
                                  f" от {user_data[consts.START_TIME_PICKED]}"
                                  f" до {user_data[consts.END_TIME_PICKED]}")
    else:
        repository.purge_user(username)
        bot.send_message(chat_id=username, text=f"Заказ отменён")

    bot.deleteMessage(chat_id=update.callback_query.message.chat_id,
                      message_id=update.callback_query.message.message_id)


def unresolved_pick(bot, update):
    bot.deleteMessage(chat_id=update.callback_query.message.chat_id,
                      message_id=update.callback_query.message.message_id)


def clear_info(bot, update):
    repository.clear_user_info(update.message.chat_id)
    bot.send_message(chat_id=update.message.chat_id, text=f"Ваш профиль очищен")


if __name__ == '__main__':
    main()