#
# (c) 2018, Tobias Kohn
#
# Created: 11.09.2018
# Updated: 11.09.2018
#
# License: Apache 2.0
#

def atom(arg):
    match arg:
        case {int}:
            return int(arg)
        case {float}:
            return float(arg)
        case {identifier}:
            return arg
        case '(' + x + ')':
            return x


def main():
    print(atom("(x + 4)"))
