from telegram.ext import BaseFilter

import datacore


class DayToTimePick(BaseFilter):
    def filter(self, message):
        return resolve_stance(message, datacore.consts.MONTH_PICKED)


class StartToEndTimePick(BaseFilter):
    def filter(self, callback_query):
        return datacore.data_as_json(
            callback_query.data).type == datacore.consts.START_TIME_PICKED and resolve_stance_for_callback(
            callback_query, datacore.consts.DAY_PICKED)


class MonthToDayPick(BaseFilter):
    def filter(self, callback_query):
        return datacore.data_as_json(
            callback_query.data).type == datacore.consts.MONTH_PICKED and resolve_stance_for_callback(callback_query,
                                                                                                      datacore.consts.NOTHING_PICKED)


class EndTimeToCommitPick(BaseFilter):
    def filter(self, callback_query):
        return datacore.data_as_json(
            callback_query.data).type == datacore.consts.END_TIME_PICKED and resolve_stance_for_callback(callback_query,
                                                                                                         datacore.consts.START_TIME_PICKED)


class CommitPick(BaseFilter):
    def filter(self, callback_query):
        return datacore.data_as_json(
            callback_query.data).type == datacore.consts.COMMITTED and (resolve_stance_for_callback(callback_query,
                                                                                                   datacore.consts.END_TIME_PICKED) or (callback_query.message.chat_id not in datacore.repository.user_info and (resolve_stance_for_callback(callback_query,
                                                                                                   datacore.consts.EXTERNAL_NAME_PICKED))))


class PhoneToExternalNamePick(BaseFilter):
    def filter(self, message):
        return resolve_stance(message, datacore.consts.END_TIME_PICKED) and message.chat_id not in datacore.repository.user_info


class ExternalNameToCommitPick(BaseFilter):
    def filter(self, message):
        return resolve_stance(message, datacore.consts.PHONE_PICKED) and message.chat_id not in datacore.repository.user_info


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
filter_committed = CommitPick()
filter_phone_to_external_name_pick = PhoneToExternalNamePick()
filter_external_name_to_commit_pick = ExternalNameToCommitPick()
