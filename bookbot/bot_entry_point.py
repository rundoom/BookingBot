import json

from coverage.files import os

from bookbot import config_holder


def main():
    config_holder.config = json.load(open('resource/config.json'))["DEFAULT"]
    config_holder.config["DB_PATH"] = config_holder.config["DB_PATH"].format(os.path.join(os.getcwd(), "resource"))

    print(f"config is:{config_holder.config}")
    from bookbot import bookingbot

    bookingbot.main()

if __name__ == "__main__":
    main()
