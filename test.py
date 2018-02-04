import re


a = ["17:00", "9:00"]

for x in a:
    print(re.search("\d+(?=:)", x).group(0))
