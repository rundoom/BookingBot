import re

from future.utils import string_types
from retrying import retry
from telegram import Update
from telegram.error import NetworkError
from telegram.ext import CallbackQueryHandler


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


def is_network(error):
    return isinstance(error, NetworkError)


@retry(wait_exponential_multiplier=200, wait_exponential_max=5000,
       stop_max_attempt_number=10, retry_on_exception=is_network)
def send_with_retry(bot,
                    chat_id,
                    text,
                    parse_mode=None,
                    disable_web_page_preview=None,
                    disable_notification=False,
                    reply_to_message_id=None,
                    reply_markup=None,
                    timeout=None,
                    **kwargs):
    bot.send_message(text=text, chat_id=chat_id, reply_markup=reply_markup)
