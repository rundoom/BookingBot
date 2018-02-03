from telegram.ext import BaseFilter
import datacore


class DayToTimePick(BaseFilter):
    def filter(self, message):
        return resolve_stance(message, datacore.consts.MONTH_PICKED)


class StartToEndTimePick(BaseFilter):
    def filter(self, message):
        return resolve_stance_for_callback(message, datacore.consts.DAY_PICKED)


class MonthToDayPick(BaseFilter):
    def filter(self, callback_query):
        return resolve_stance_for_callback(callback_query, datacore.consts.NOTHING_PICKED)


class EndTimeToCommitPick(BaseFilter):
    def filter(self, callback_query):
        return resolve_stance_for_callback(callback_query, datacore.consts.START_TIME_PICKED)


def resolve_stance(message, stance) -> bool:
    username = message.chat_id
    return username in datacore.repository.user_stances and datacore.repository.user_stances[username] == stance


def resolve_stance_for_callback(callback, stance) -> bool:
    username = callback.message.chat_id
    return username in datacore.repository.user_stances and datacore.repository.user_stances[username] == stance


filter_day_to_time_pick = DayToTimePick()
filter_start_to_end_time_pick = StartToEndTimePick()
filter_month_to_day_pick = MonthToDayPick()
filter_end_time_to_commit_pick = EndTimeToCommitPick()
