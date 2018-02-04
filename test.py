def a() -> bool:
    print("a")
    return False


def b() -> bool:
    print("b")
    return True


if a() and b():
    pass
