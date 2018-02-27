from numpy import float64, int64


def iterable(a):
    if type(a) in [int, float, float64, int64]:
        return [a]

    else:
        return a
