from math import cos, log, sin, exp 

def df(x):
    return round((x ** cos(x)) * ((-log(x, exp(1))) * sin(x) + ((1/x) * cos(x))), 4)

for x in range(1, 11):
    print(x, df(x))