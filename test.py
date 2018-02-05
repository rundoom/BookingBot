a = list(range(1, 15))
b = list(range(17, 25))


def trim_to_border(c: list):
    for x in range(0, len(c)):
        if c[x+1] - c[x] > 1:
            return c[:x+1]


def group_by_gaps(c: list):
    list_to_return = []
    for x in range(0, len(c)):
        if x+1 < len(c) and c[x+1] - c[x] > 1:
            return c[:x+1]

print(trim_to_border(a+b))