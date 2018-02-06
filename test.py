from threading import Thread
from time import sleep


def threaded_function(arg):
    for i in range(arg):
        print(f"running {i}")
        sleep(1)


def threaded_function1(arg):
    for i in range(arg):
        print(f"executing {i}")
        sleep(1)


if __name__ == "__main__":
    thread1 = Thread(target=threaded_function, args=(10,))
    thread2 = Thread(target=threaded_function1, args=(2,))
    thread1.start()
    thread2.start()
    pass
