from telegram.ext import BaseFilter
import datacore


class MonthPick(BaseFilter):
    def filter(self, message):
        return resolve_stance(message, datacore.consts.MONTH_PICKED)


class DayPick(BaseFilter):
    def filter(self, message):
        return resolve_stance(message, datacore.consts.DAY_PICKED)


class InitPick(BaseFilter):
    def filter(self, callback_query):
        return resolve_stance_for_callback(callback_query, datacore.consts.NOTHING_PICKED)


class TimePick(BaseFilter):
    def filter(self, callback_query):
        return resolve_stance_for_callback(callback_query, datacore.consts.START_TIME_PICKED)


def resolve_stance(message, stance) -> bool:
    username = message.chat_id
    return username in datacore.repository.user_stances and datacore.repository.user_stances[username] == stance


def resolve_stance_for_callback(callback, stance) -> bool:
    username = callback.message.chat_id
    return username in datacore.repository.user_stances and datacore.repository.user_stances[username] == stance


filter_day_to_time_pick = MonthPick()
filter_start_to_end_time_pick = DayPick()
filter_month_to_day_pick = InitPick()
filter_time_pick = TimePick()
