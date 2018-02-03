from telegram import InlineKeyboardButton

import datacore
import dateutil
from datacore import CallData

init_list = list(range(0, 7))

list_of_list = [init_list[x:x + 2] for x in range(0, len(init_list), 2)]


time_keys = [[InlineKeyboardButton(text=x, callback_data=CallData(call_type=datacore.consts.START_TIME_PICKED, call_val=x).to_json()) for x in dateutil.possible_time()][x:x + 2] for x in range(0, len(dateutil.possible_time()), 2)]

print(time_keys)