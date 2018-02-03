import json
from _datetime import datetime
import logging


class Consts:
    def __init__(self):
        self.NOTHING_PICKED = "nothing_picked"
        self.MONTH_PICKED = "month_picked"
        self.DAY_PICKED = "day_picked"
        self.START_TIME_PICKED = "start_time_picked"
        self.END_TIME_PICKED = "end_time_picked"


consts = Consts()


class BookedRange:
    def __init__(self, start_date: datetime, end_date: datetime, username: str):
        self.start_date = start_date
        self.end_date = end_date
        self.username = username


class CurrentStance:
    def __init__(self, stance: str, val: str):
        self.stance = stance
        self.val = val


class CallData:
    def __init__(self, call_type: str, call_val: str):
        self.call_type = call_type
        self.call_val = call_val

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True)


class Repository:
    def __init__(self):
        self.user_stances = {}
        self.user_data = {}

    def update_stance(self, stance: str, user: str):
        logging.info(f"user: {user} in {stance}")
        self.user_stances[user] = stance

    def update_data(self, data: CallData, user: str):
        if user in self.user_data:
            self.user_data[user][data.call_type] = data.call_val
        else:
            user_inner = {data.call_type: data.call_val}
            self.user_data[user] = user_inner
        logging.info(f"user: {user} input data {self.user_data[user]}")


repository = Repository()


def as_call_data(dct):
    return CallData(dct['call_type'], dct['call_val'])


def data_as_json(serial_json) -> CallData:
    return json.loads(serial_json, object_hook=as_call_data)
