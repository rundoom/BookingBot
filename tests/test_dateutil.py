import logging
import random
from datetime import datetime
from unittest import TestCase
from unittest.mock import patch, MagicMock

from telegram import Chat
from telegram import Message
from telegram import Update
from telegram import User

import bookingbot

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


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

    def setUp(self):
        global sea
        sea = []

    def test_book(self):
        update = update_factory(user_id=153174359, first_name="Nanodesu", usename="Nanodesuizlesu", text="/book")
        self.dispatcher.process_update(update)
        self.assertEqual(sea[0][1]['text'], 'На какой месяц?')
        # self.assertEqual(sea[0][1]['reply_markup'], 'На какой месяц?')

    def test_echo(self):
        update = update_factory(user_id=153174359, first_name="Nanodesu", usename="Nanodesuizlesu", text="random")
        self.dispatcher.process_update(update)
        self.assertEqual(sea[0][1]['text'], 'Введите /book для того чтобы назначить время')


def update_factory(user_id, first_name, usename, text=None, time=datetime.now()) -> Update:
    return Update(update_id=random.randrange(0, 999999),
                  message=Message(from_user=User(is_bot=False, id=user_id, first_name=first_name),
                                  message_id=random.randrange(0, 999999), date=time,
                                  chat=Chat(id=user_id, type="private", username=usename, first_name=first_name),
                                  text=text, bot=MagicMock()))


def send_side_effect(*args, **kwargs):
    logging.info(f"{args}, {kwargs}")
    sea.append([args, kwargs])

# def update_callback_factory():
#     return Update
#         {'update_id': 739916029, 'callback_query': {'id': '657878866749121315', 'chat_instance': '-1007589049144120027', 'message': {'message_id': 6402, 'date': 1518046371, 'chat': {'id': 153174359, 'type': 'private', 'username': 'Nanodesuizlesu', 'first_name': 'Nanodesu'}, 'text': 'На какой месяц?', 'entities': [], 'caption_entities': [], 'photo': [], 'new_chat_members': [], 'new_chat_photo': [], 'delete_chat_photo': False, 'group_chat_created': False, 'supergroup_chat_created': False, 'channel_chat_created': False, 'from': {'id': 307563270, 'first_name': 'MySender', 'is_bot': True, 'username': 'MessageRnddBot'}, 'new_chat_member': None}, 'data': '{"load": 2018, "type": "month_picked", "val": 3}', 'from': {'id': 153174359, 'first_name': 'Nanodesu', 'is_bot': False, 'username': 'Nanodesuizlesu', 'language_code': 'ru'}}, '_effective_user': {'id': 153174359, 'first_name': 'Nanodesu', 'is_bot': False, 'username': 'Nanodesuizlesu', 'language_code': 'ru'}, '_effective_chat': {'id': 153174359, 'type': 'private', 'username': 'Nanodesuizlesu', 'first_name': 'Nanodesu'}, '_effective_message': {'message_id': 6402, 'date': 1518046371, 'chat': {'id': 153174359, 'type': 'private', 'username': 'Nanodesuizlesu', 'first_name': 'Nanodesu'}, 'text': 'На какой месяц?', 'entities': [], 'caption_entities': [], 'photo': [], 'new_chat_members': [], 'new_chat_photo': [], 'delete_chat_photo': False, 'group_chat_created': False, 'supergroup_chat_created': False, 'channel_chat_created': False, 'from': {'id': 307563270, 'first_name': 'MySender', 'is_bot': True, 'username': 'MessageRnddBot'}, 'new_chat_member': None}}
