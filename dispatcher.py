from telegram.ext import *
from telegram import Update
import re
from future.utils import string_types


updater = Updater(token='307563270:AAE9mV3culSEjGavFPty-FUW8V2euI2xYzI')

dispatcher = updater.dispatcher


class FilteredCallbackQueryHandler(CallbackQueryHandler):
    def __init__(self,
                 callback,
                 pass_update_queue=False,
                 pass_job_queue=False,
                 filters=None,
                 pattern=None,
                 pass_groups=False,
                 pass_groupdict=False,
                 pass_user_data=False,
                 pass_chat_data=False):
        super(CallbackQueryHandler, self).__init__(
            callback,
            pass_update_queue=pass_update_queue,
            pass_job_queue=pass_job_queue,
            pass_user_data=pass_user_data,
            pass_chat_data=pass_chat_data)
        self.filters = filters

        if isinstance(pattern, string_types):
            pattern = re.compile(pattern)

        self.pattern = pattern
        self.pass_groups = pass_groups
        self.pass_groupdict = pass_groupdict

    def check_update(self, update):
        if isinstance(update, Update) and update.callback_query:

            if self.filters:
                message = update.callback_query
                if isinstance(self.filters, list):
                    res = any(func(message) for func in self.filters)
                else:
                    res = self.filters(message)
                if not res:
                    return False

            if self.pattern:
                if update.callback_query.data:
                    match = re.match(self.pattern, update.callback_query.data)
                    return bool(match)
            else:
                return True
