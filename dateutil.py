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
    current += increment
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


def calc_free_time(user: str):
    possible_time_for_start(user)


def possible_time_for_start(user: str) -> list:
    user_data = datacore.repository.user_data[user]
    cns = datacore.consts
    current_date = datetime.datetime.now()
    busy = datacore.repository.get_busy_on_date(year=user_data[cns.YEAR_PICKED], day=user_data[cns.DAY_PICKED],
                                                month=user_data[cns.MONTH_PICKED])

    possible_start = 7
    if current_date.year == user_data[cns.YEAR_PICKED] and current_date.month == user_data[cns.MONTH_PICKED] and current_date.day == user_data[cns.DAY_PICKED]:
        if current_date.hour > 7:
            possible_start = current_date.hour + 1

    all_aval = set(range(possible_start, 23))

    for x in busy:
        all_aval -= set(range(x[0], x[1]))

    if not all_aval:
        raise NoTimeAvailable()

    return [f"{str(x)}:00" for x in list(all_aval)]


def possible_time_for_end(user: str) -> list:
    user_data = datacore.repository.user_data[user]
    cns = datacore.consts

    busy = datacore.repository.get_busy_on_date(year=user_data[cns.YEAR_PICKED], day=user_data[cns.DAY_PICKED],
                                                month=user_data[cns.MONTH_PICKED])

    start_int = int(re.search("\d+(?=:)", user_data[datacore.consts.START_TIME_PICKED]).group(0))

    all_aval = set(range(7, 24))
    for x in busy:
        busy_range = set(range(x[0]+1, x[1]+1)) - {start_int}
        all_aval -= busy_range

    all_aval = trim_to_border(list(all_aval), start_int)

    start_time = datacore.repository.user_data[user][datacore.consts.START_TIME_PICKED]
    possible_end = [f"{str(x)}:00" for x in all_aval]
    return possible_end[list.index(possible_end, start_time)+1:]


def trim_to_border(c: list, start: int):
    for x in range(list.index(c, start), len(c)):
        if x+1 < len(c) and c[x+1] - c[x] > 1:
            return c[list.index(c, start):x+1]
    return c


def morph_month_name(name: str):
    if re.match(".*ь$", name):
        return re.sub("ь$", "я", name)
    else:
        return f"{name}а"


class NoTimeAvailable(Exception):
    def __init__(self):
        pass
