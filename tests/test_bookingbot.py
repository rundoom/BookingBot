import functools
import logging
import random
import unittest
from datetime import datetime
from unittest import TestCase, suite
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

def lncmp(self, testCaseClass):
    def isTestMethod(attrname, testCaseClass=testCaseClass,
                     prefix=self.testMethodPrefix):
        return attrname.startswith(prefix) and \
               callable(getattr(testCaseClass, attrname))

    testFnNames = list(filter(isTestMethod, list(testCaseClass.__dict__)))
    return testFnNames


patch('unittest.TestLoader.getTestCaseNames', lncmp).start()

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
        logging.info(f"Now in {acc.current_method}")

    def test_date_seq(self):
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
        month_pick_call = acc.accum["test_book"]

        update = update_callback_factory(user_id=153174359, first_name="Nanodesu", usename="Nanodesuizlesu",
                                         text="/book",
                                         query_data=datacore.data_as_json(month_pick_call[0][1]["reply_markup"]['inline_keyboard'][0][0].callback_data))

        self.dispatcher.process_update(update)
        self.assertTrue(153174359 in self.repository.user_data)
        self.assertEqual(self.repository.user_stances[153174359], datacore.consts.MONTH_PICKED)
        self.assertEqual(self.repository.user_data[153174359][datacore.consts.MONTH_PICKED], 9)
        self.assertEqual(self.repository.user_data[153174359][datacore.consts.YEAR_PICKED], 2007)

    def test_day_to_time_pick(self):
        update = update_factory(user_id=153174359, first_name="Nanodesu", usename="Nanodesuizlesu", text="10")
        self.dispatcher.process_update(update)
        self.assertEqual(acc[0][1]["text"], "Допустимые значения: 29 - 30")

        update = update_factory(user_id=153174359, first_name="Nanodesu", usename="Nanodesuizlesu", text="31")
        self.dispatcher.process_update(update)
        self.assertEqual(acc[0][1]["text"], "Допустимые значения: 29 - 30")

        update = update_factory(user_id=153174359, first_name="Nanodesu", usename="Nanodesuizlesu", text="28")
        self.dispatcher.process_update(update)
        self.assertEqual(acc[0][1]["text"], "Допустимые значения: 29 - 30")

        update = update_factory(user_id=153174359, first_name="Nanodesu", usename="Nanodesuizlesu", text="wrong")
        self.dispatcher.process_update(update)
        self.assertEqual(acc[0][1]["text"], "Допустимые значения: 29 - 30")

        update = update_factory(user_id=153174359, first_name="Nanodesu", usename="Nanodesuizlesu", text="30")
        self.dispatcher.process_update(update)

    # def test_start_to_end_time_pick(self):
    #     start_time_pick_call = acc.accum["test_day_to_time_pick"]
    #     update = update_callback_factory(user_id=153174359, first_name="Nanodesu", usename="Nanodesuizlesu",
    #                                      text="/book",
    #                                      query_data=datacore.data_as_json(start_time_pick_call[0][1]["reply_markup"]['inline_keyboard'][0][0].callback_data))


def update_factory(user_id, first_name, usename, text=None, time=datetime.now()) -> Update:
    return Update(update_id=random.randrange(0, 999999),
                  message=Message(from_user=User(is_bot=False, id=user_id, first_name=first_name),
                                  message_id=random.randrange(0, 999999), date=time,
                                  chat=Chat(id=user_id, type="private", username=usename, first_name=first_name),
                                  text=text, bot=MagicMock()))


def send_side_effect(*args, **kwargs):
    logging.info(f"Proxy args: {args}, {kwargs}")
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



