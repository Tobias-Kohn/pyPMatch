#
# (c) 2018, Tobias Kohn
#
# Created: 27.08.2018
# Updated: 29.08.2018
#
# License: Apache 2.0
#
import ast
try:
    from astunparse import unparse as dump
except ImportError:
    from ast import dump


class AstSimplifier(ast.NodeTransformer):
    """
    Simplifies an AST using pattern matching.  This is for demonstration purposes only; the output will not be
    compileable because the returned nodes might lack proper `lineno` and `col_offset` fields (cf. `copy_location`
    in the `ast` module).
    """

    def generic_visit(self, node):
        match super().generic_visit(node):
            case ast.UnaryOp(ast.USub, ast.UnaryOp(ast.USub, e)):
                return e
            case ast.BinOp(e, ast.Add|ast.Sub, ast.Num(0)):
                return e
            case ast.BinOp(_, ast.Mult, e @ ast.Num(0)):
                return e
            case ast.BinOp(e, ast.Mult|ast.Div, ast.Num(1)):
                return e
            case ast.BinOp(ast.Num(a), ast.Add, ast.Num(b)):
                return ast.Num(a + b)
            case ast.BinOp(ast.Num(a), ast.Sub, ast.Num(b)):
                return ast.Num(a - b)
            case ast.BinOp(ast.Name(x), ast.Sub, ast.Name(y)) if x == y:
                return ast.Num(0)
            case x:
                return x


def simplify(tree):
    simplifier = AstSimplifier()
    return simplifier.visit(tree)


def juxtapose(left, right):
    """
    Takes two texts/strings with several lines, and creates a new string, where both original texts are displayed
    side by side.  This is, however, just a helper function for the purpose of illustration, and not necessarily
    a generally useable function.
    """
    if type(left) is str:
        left = left.split('\n')
    else:
        left = left[:]
    if type(right) is str:
        right = right.split('\n')
    else:
        right = right[:]
    left = [line.expandtabs() for line in left]
    right = [line.expandtabs() for line in right]
    m = max([len(line) for line in left]) + 2
    for i, line in enumerate(left):
        left[i] = line + ' ' * (m - len(line)) + '| '
    empty = ' ' * m + '| '
    while len(left) < len(right):
        left.append(empty)
    while len(left) > len(right):
        right.append('')
    result = [l + r for l, r in zip(left, right)]
    return '\n'.join(result)


def simplify_and_print(program: str):
    tree = ast.parse(program)
    if isinstance(tree, ast.Module) and len(tree.body) == 1:
        tree = tree.body[0]
    left = dump(tree)
    tree = simplify(tree)
    right = dump(tree)
    if '\n' in left and '\n' in right:
        print(juxtapose(left, right))
    else:
        print(left)
        print(right)



# The program does not make much sense, but is rather a show case for the implemented optimisations/simplifications...
_STD_PROGRAM = """
def foo(x):
    y = x * (3 - 2) + (4 + (3 - 7)) + 3
    z = x + (y - y)
    return y + y * 0 + z
"""

def main():
    simplify_and_print(_STD_PROGRAM)
