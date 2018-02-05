a = list(range(7, 10))
b = list(range(11, 13))
c = list(range(15, 20))


def trim_to_border(c: list, start: int):
    for x in range(list.index(c, start), len(c)):
        if x+1 < len(c) and c[x+1] - c[x] > 1:
            return c[list.index(c, start):x+1]
    return c

print(a+b+c)
print(trim_to_border(a+b+c, 16))