from telegram.ext import BaseFilter

from bookbot import datacore


class CommitPick(BaseFilter):
    def filter(self, callback_query):
        return datacore.data_as_json(
            callback_query.data).type == datacore.consts.COMMITTED and (resolve_stance_for_callback(callback_query,
                                                                                                    datacore.consts.END_TIME_PICKED) or (callback_query.message.chat_id not in datacore.repository.user_info and (resolve_stance_for_callback(callback_query,
                                                                                                                                                                                                                                              datacore.consts.EXTERNAL_NAME_PICKED))))


class StanceResolveFilterCallback(BaseFilter):
    def __init__(self, callback_stance, user_stance):
        self.callback_stance = callback_stance
        self.user_stance = user_stance

    def filter(self, callback_query):
        return datacore.data_as_json(
            callback_query.data).type == self.callback_stance and resolve_stance_for_callback(callback_query, self.user_stance)


class StanceResolveFilter(BaseFilter):
    def __init__(self, stance, check_info: bool):
        self.stance = stance
        self.check_info = check_info

    def filter(self, message):
        return resolve_stance(message, self.stance) and (not self.check_info or message.chat_id not in datacore.repository.user_info)


def resolve_stance(message, stance) -> bool:
    username = message.chat_id
    return username in datacore.repository.user_stances and datacore.repository.user_stances[username] == stance


def resolve_stance_for_callback(callback, stance) -> bool:
    username = callback.message.chat_id
    return username in datacore.repository.user_stances and datacore.repository.user_stances[username] == stance


filter_committed = CommitPick()
