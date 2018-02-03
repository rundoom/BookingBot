import datetime
from calendar import monthrange
import datacore
import re

month_map = {1: "Январь", 2: "Февраль",
             3: "Март", 4: "Апрель", 5: "Май",
             6: "Июнь", 7: "Июль", 8: "Август",
             9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь",
             12: "Декабрь"}


class MonthWithName:
    def __init__(self, month_number: int, year: int):
        self.month_number = month_number
        self.month_name = month_map[month_number]
        self.year = year


def get_next_month(current: int, increment: int = 0) -> MonthWithName:
    current = current + increment
    year_inc = current // 12
    next_month = current - year_inc * 12
    if next_month == 0:
        next_month = 12
        if year_inc > 0:
            year_inc -= 1
    return MonthWithName(next_month, datetime.datetime.now().year + year_inc)


def get_next_few_months(month_count: int = 3):
    now_time = datetime.datetime.now()
    return [get_next_month(now_time.month, x) for x in range(0, month_count)]


def is_days_count_fits(msg: str, month: str) -> bool:
    from_date = available_from_to(month)[0]
    to_date = available_from_to(month)[1]
    return msg.isdigit() and (from_date <= int(msg) <= to_date)


def available_from_to(msg: str):
    current = datetime.datetime.now()
    if current.month == int(msg):
        return current.day, monthrange(year=current.year, month=current.month)[1]
    else:
        return 1, monthrange(year=current.year, month=current.month)[1]


def possible_time() -> list:
    return [f"{str(x)}:00" for x in range(7, 22)]


def possible_time_for_end(user: str) -> list:
    start_time = datacore.repository.user_data[user][datacore.consts.START_TIME_PICKED]
    possible_end = [f"{str(x)}:00" for x in range(7, 23)]
    return possible_end[list.index(possible_end, start_time)+1:]


def morph_month_name(name: str):
    if re.match(".*ь$", name):
        return re.sub("ь$", "я", name)
    else:
        return f"{name}а"
