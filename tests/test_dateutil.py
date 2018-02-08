import logging
import random
from datetime import datetime
from unittest import TestCase
from unittest.mock import patch, MagicMock

from freezegun import freeze_time
from telegram import Chat, CallbackQuery
from telegram import Message
from telegram import Update
from telegram import User

from bookbot import bookingbot
from bookbot import datacore
from bookbot import dateutilbot
from bookbot.datacore import CallData

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

freezer = freeze_time(datetime(year=2007, month=9, day=29, hour=15), tick=True)
freezer.start()


class Accumulator:
    def __init__(self):
        self.current_method = None
        self.accum = {}

    def append(self, other):
        if self.current_method not in self.accum:
            self.accum[self.current_method] = []
        self.accum[self.current_method].append(other)

    def __getitem__(self, item: int):
        return self.accum[self.current_method][item]


class BotTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stubs = [
            patch('telegram.ext.updater.Updater.start_polling'),
            patch('telegram.bot.Bot.send_message', new=send_side_effect),
            patch('telegram.bot.Bot.deleteMessage', new=send_side_effect)
        ]

        for x in cls.stubs:
            x.start()

        bookingbot.main()
        cls.dispatcher = bookingbot.dispatcher
        cls.repository = bookingbot.repository

        global acc
        acc = Accumulator()

    def setUp(self):
        acc.current_method = self._testMethodName

    def testDateSeq(self):
        self.assertEqual(dateutilbot.month_map[1], 'Январь')
        self.assertEqual(dateutilbot.month_map[12], 'Декабрь')

    def test_book(self):
        update = update_factory(user_id=153174359, first_name="Nanodesu", usename="Nanodesuizlesu", text="/book")
        self.dispatcher.process_update(update)
        self.assertEqual(acc[0][1]['text'], 'На какой месяц?')
        self.assertEqual(len(acc[0][1]['reply_markup']['inline_keyboard']), 3)

        keyboard = acc[0][1]['reply_markup']['inline_keyboard']
        self.assertEqual(keyboard[0][0].text, "Сентябрь")
        self.assertEqual(keyboard[1][0].text, "Октябрь")
        self.assertEqual(keyboard[2][0].text, "Ноябрь")

    def test_echo(self):
        update = update_factory(user_id=153174359, first_name="Nanodesu", usename="Nanodesuizlesu", text="random")
        self.dispatcher.process_update(update)
        self.assertEqual(acc[0][1]['text'], 'Введите /book для того чтобы назначить время')

    def test_month_to_day_pick(self):
        update = update_callback_factory(user_id=153174359, first_name="Nanodesu", usename="Nanodesuizlesu",
                                         text="/book",
                                         query_data=CallData(call_type=datacore.consts.MONTH_PICKED, call_val=1,
                                                             opt_payload=2018))
        self.dispatcher.process_update(update)


def update_factory(user_id, first_name, usename, text=None, time=datetime.now()) -> Update:
    return Update(update_id=random.randrange(0, 999999),
                  message=Message(from_user=User(is_bot=False, id=user_id, first_name=first_name),
                                  message_id=random.randrange(0, 999999), date=time,
                                  chat=Chat(id=user_id, type="private", username=usename, first_name=first_name),
                                  text=text, bot=MagicMock()))


def send_side_effect(*args, **kwargs):
    logging.info(f"{args}, {kwargs}")
    acc.append([args, kwargs])


def update_callback_factory(user_id, first_name, usename, text=None, time=datetime.now(), query_data: CallData = None):
    query_data = query_data.to_json()
    return Update(update_id=random.randrange(0, 999999), callback_query=CallbackQuery(id=random.randrange(0, 999999),
                                                                                      message=Message(
                                                                                          from_user=User(is_bot=False,
                                                                                                         id=user_id,
                                                                                                         first_name=first_name),
                                                                                          message_id=random.randrange(0,
                                                                                                                      999999),
                                                                                          date=time,
                                                                                          chat=Chat(id=user_id,
                                                                                                    type="private",
                                                                                                    username=usename,
                                                                                                    first_name=first_name),
                                                                                          text=text, bot=MagicMock()),
                                                                                      from_user=User(is_bot=False,
                                                                                                     id=user_id,
                                                                                                     first_name=first_name),
                                                                                      chat_instance=-random.randrange(0,
                                                                                                                      999999),
                                                                                      data=query_data),
                  )



