import json
import logging
import operator
import re
from datetime import datetime, timedelta
from typing import Union

from sqlalchemy import extract, exists, desc

from bookbot import dataentities
from bookbot.dataentities import session
from bookbot import bot_scheduler


class Consts:
    def __init__(self):
        self.NOTHING_PICKED = "nothing_picked"
        self.MONTH_PICKED = "month_picked"
        self.YEAR_PICKED = "year_picked"
        self.DAY_PICKED = "day_picked"
        self.START_TIME_PICKED = "start_time_picked"
        self.END_TIME_PICKED = "end_time_picked"
        self.PHONE_PICKED = "phone_picked"
        self.EXTERNAL_NAME_PICKED = "external_name_picked"
        self.COMMITTED = "committed"
        self.RANGE_REMOVE = "range_remove"
        self.NEXT_DATE = "next_date"
        self.PREVIOUS_DATE = "previous_date"


consts = Consts()


class CurrentStance:
    def __init__(self, stance: str, val: str):
        self.stance = stance
        self.val = val


class CallData:
    def __init__(self, call_type: str, call_val: Union[str, int, float]):
        self.type = call_type
        self.val = call_val

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True)


class Repository:
    def __init__(self):
        self.user_stances = {}
        self.user_data = {}

    def purge_user(self, user):
        if user in self.user_stances:
            del self.user_stances[user]

        if user in self.user_data:
            del self.user_data[user]

    def book_range(self, user: str, userlink: str):
        sts = self.user_data[user]

        start_date = datetime(year=int(sts[consts.YEAR_PICKED]), day=int(sts[consts.DAY_PICKED]),
                              month=int(sts[consts.MONTH_PICKED]),
                              hour=int(re.search("\d+(?=:)", sts[consts.START_TIME_PICKED]).group(0)))

        end_date = datetime(year=int(sts[consts.YEAR_PICKED]), day=int(sts[consts.DAY_PICKED]),
                            month=int(sts[consts.MONTH_PICKED]),
                            hour=int(re.search("\d+(?=:)", sts[consts.END_TIME_PICKED]).group(0)))

        booked_range = dataentities.BookedRange(start_date=start_date, end_date=end_date, username=user)
        session.add(booked_range)
        session.commit()
        bot_scheduler.schedule_notifications(booked_range.id)
        self.register_user(user, userlink)
        self.purge_user(user)

    def update_stance(self, stance: str, user: str):
        logging.info(f"user: {user} in {stance}")
        self.user_stances[user] = stance

    def get_busy_on_date(self, day, month, year):
        start_date = dataentities.BookedRange.start_date
        on_day = session.query(dataentities.BookedRange) \
            .filter(extract('day', start_date) == day) \
            .filter(extract('month', start_date) == month) \
            .filter(extract('year', start_date) == year) \
            .all()

        return list(map(lambda x: [x.start_date.hour, x.end_date.hour], on_day))

    def update_data(self, data: CallData, user: str):
        if user in self.user_data:
            self.user_data[user][data.type] = data.val
        else:
            user_inner = {data.type: data.val}
            self.user_data[user] = user_inner

        logging.info(f"user: {user} input data {self.user_data[user]}")

    def register_user(self, user: str, userlink: str):
        user_exists = dataentities.session.query(exists().where(dataentities.UserInfo.username == int(user))).scalar()
        if not user_exists:
            user_inner = dataentities.UserInfo(phone=self.user_data[user][consts.PHONE_PICKED],
                                               name=self.user_data[user][consts.EXTERNAL_NAME_PICKED],
                                               username=int(user),
                                               userlink=userlink)
            session.add(user_inner)
            session.commit()

    def clear_user_info(self, user: str):
        user_to_clear = session.query(dataentities.UserInfo).filter_by(username=int(user)).first()
        if user_to_clear is None:
            raise NoSuchUser()
        session.delete(user_to_clear)
        session.commit()

    def get_booked(self, date: datetime, is_after: bool, is_now: bool = False):
        order_func = None
        compare_op = None
        if is_after:
            compare_op = operator.ge
            if not is_now:
                date += timedelta(days=1)
            order_func = stub_func
        else:
            compare_op = operator.lt
            order_func = desc

        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = dataentities.BookedRange.start_date
        next_date = session.query(dataentities.BookedRange) \
            .filter(dataentities.BookedRange.start_date > datetime.now()) \
            .filter(compare_op(dataentities.BookedRange.start_date, date)) \
            .order_by(order_func(dataentities.BookedRange.start_date)) \
            .limit(1).first()

        if not next_date:
            return None

        return session.query(dataentities.BookedRange) \
            .filter(extract('day', start_date) == next_date.start_date.day) \
            .filter(extract('month', start_date) == next_date.start_date.month) \
            .filter(extract('year', start_date) == next_date.start_date.year) \
            .order_by(dataentities.BookedRange.start_date).all()

    def get_user_info(self, user):
        return session.query(dataentities.UserInfo).filter_by(username=int(user)).first()

    def get_booked_for_user(self, user: str):
        return session.query(dataentities.BookedRange).filter(dataentities.BookedRange.username == int(user)) \
            .filter(dataentities.BookedRange.start_date > datetime.now()) \
            .order_by(dataentities.BookedRange.start_date).all()

    def get_booked_by_id(self, id: int):
        return session.query(dataentities.BookedRange).filter_by(id=id).first()

    def unbook_range(self, id: int):
        session.query(dataentities.BookedRange).filter_by(id=id).delete()
        session.commit()
        bot_scheduler.remove_notification(id)


repository = Repository()


def as_call_data(dct):
    return CallData(dct['type'], dct['val'])


def data_as_json(serial_json) -> CallData:
    return json.loads(serial_json, object_hook=as_call_data)


def stub_func(x):
    return x


class NoSuchUser(Exception):
    def __init__(self):
        pass
