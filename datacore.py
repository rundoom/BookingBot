import json
import logging
import re
from _datetime import datetime
from typing import Union


class Consts:
    def __init__(self):
        self.NOTHING_PICKED = "nothing_picked"
        self.MONTH_PICKED = "month_picked"
        self.YEAR_PICKED = "year_picked"
        self.DAY_PICKED = "day_picked"
        self.START_TIME_PICKED = "start_time_picked"
        self.END_TIME_PICKED = "end_time_picked"
        self.COMMITTED = "committed"


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
    def __init__(self, call_type: str, call_val: Union[str, int], opt_payload=None):
        self.type = call_type
        self.val = call_val
        self.load = opt_payload

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True)


class Repository:
    def __init__(self):
        self.user_stances = {}
        self.user_data = {}
        self.booked = []

    def purge_user(self, user):
        if user in self.user_stances:
            del self.user_stances[user]

        if user in self.user_data:
            del self.user_data[user]

    def book_range(self, user: str):
        sts = self.user_data[user]

        start_date = datetime(year=int(sts[consts.YEAR_PICKED]), day=int(sts[consts.DAY_PICKED]),
                              month=int(sts[consts.MONTH_PICKED]),
                              hour=int(re.search("\d+(?=:)", sts[consts.START_TIME_PICKED]).group(0)))

        end_date = datetime(year=int(sts[consts.YEAR_PICKED]), day=int(sts[consts.DAY_PICKED]),
                            month=int(sts[consts.MONTH_PICKED]),
                            hour=int(re.search("\d+(?=:)", sts[consts.END_TIME_PICKED]).group(0)))

        booked_range = BookedRange(start_date=start_date, end_date=end_date, username=user)
        self.booked.append(booked_range)
        print(self.booked)

    def update_stance(self, stance: str, user: str):
        logging.info(f"user: {user} in {stance}")
        self.user_stances[user] = stance

    def get_busy_on_date(self, day, month, year):
        on_day = list(filter(lambda x: x.start_date.day == int(day) and x.start_date.month == int(month) and x.start_date.year == int(year), self.booked))
        return list(map(lambda x: [x.start_date.hour, x.end_date.hour], on_day))

    def update_data(self, data: CallData, user: str, custom_type: str = None):
        if user in self.user_data:
            self.user_data[user][data.type] = data.val
        else:
            user_inner = {data.type: data.val}
            self.user_data[user] = user_inner

        if custom_type is not None and data.load is not None:
            self.user_data[user][custom_type] = data.load
        logging.info(f"user: {user} input data {self.user_data[user]}")


repository = Repository()


def as_call_data(dct):
    return CallData(dct['type'], dct['val'], dct['load'])


def data_as_json(serial_json) -> CallData:
    return json.loads(serial_json, object_hook=as_call_data)
