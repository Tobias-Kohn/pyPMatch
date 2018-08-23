#
# (c) 2018, Tobias Kohn
#
# Created: 23.08.2018
# Updated: 23.08.2018
#
# License: Apache 2.0
#
def sum(L):
    match L:
        case []:
            return 0
        case [x @ int|float, *y]:
            return x + sum(y)
        case [x, ...]:
            raise ValueError(f"cannot add a value of type '{type(x)}'")
        case x:
            raise ValueError(f"cannot sum a value of type '{type(x)}'")


def interleave(*args):
    match args:
        case (x, []):
            return x
        case ([], x):
            return x
        case ([x, *xs], [y, *ys]):
            return [x, y] + interleave(xs, ys)
        case _:
            raise ValueError("there is something wrong here!")


def main():
    print("Sum of [2, 3, 5, 7]:", sum([2, 3, 5, 7]))
    print("zipping [1, 3, 5, 7] and [2, 4]:", interleave([1, 3, 5, 7], [2, 4]))
