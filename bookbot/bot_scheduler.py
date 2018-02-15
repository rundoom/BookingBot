from datetime import datetime, timedelta
import time
import os

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from bookbot import config_holder, datacore, bookingbot

bot = None
scheduler = None


def main():
    global bot

    jobstores = {
        'default': SQLAlchemyJobStore(url=config_holder.config["DB_PATH"])
    }

    global scheduler
    scheduler = BackgroundScheduler(jobstores=jobstores)

    scheduler.start()


def schedule_notifications(book_id):
    booked = datacore.repository.get_booked_by_id(book_id)
    run_date_earl = booked.start_date - timedelta(hours=3)

    if run_date_earl.hour >= 22:
        run_date_earl -= timedelta(hours=run_date_earl.hour - 21)
    elif run_date_earl.hour <= 7:
        run_date_earl -= timedelta(hours=run_date_earl.hour + 3)

    delta_for_earl = booked.start_date - timedelta(hours=3) - run_date_earl
    total_hour = delta_for_earl.seconds // 3600 + delta_for_earl.days * 24

    scheduler.add_job(func=send_notification, id=f"{book_id}:3", trigger='date', run_date=run_date_earl,
                      kwargs={"username": booked.username, "hour_num": total_hour, "book_id": book_id})

    print(total_hour)

    scheduler.add_job(func=send_notification, id=f"{book_id}:24", trigger='date', run_date=booked.start_date - timedelta(hours=24),
                      kwargs={"username": booked.username, "hour_num": 24, "book_id": book_id})


def remove_notification(book_id):
    scheduler.remove_job(f"{book_id}:3")
    scheduler.remove_job(f"{book_id}:24")


def send_notification(username, hour_num, book_id):
    user_info = datacore.repository.get_user_info(username)
    booked = datacore.repository.get_booked_by_id(book_id)
    for x in config_holder.adm:
        bot.send_message(chat_id=x,
                         text=f"Напоминание:\nЧерез {hour_num} часа забронировано на:\n"
                              f"{user_info.userlink}\nКонтактный телефон:\n{user_info.phone}\n"
                              f"Коллектив:\n{user_info.name}\n"
                              f"от {booked.start_date.hour}:00"
                              f" до {booked.end_date.hour}:00")

    bot.send_message(chat_id=username,
                     text=f"Напоминание:\nЧерез {hour_num} часа забронировано время в студии\n"
                          f"от {booked.start_date.hour}:00"
                          f" до {booked.end_date.hour}:00")