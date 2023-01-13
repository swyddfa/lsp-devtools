# Not a server, used to simulate the case where the server crashes before
# it can boot.


def f(x):
    return x / 0


def g(x):
    return f(x) * f(x)


def h(x):
    return g(x) - f(x)


h(2)
