#
# (c) 2018, Tobias Kohn
#
# Created: 15.08.2018
# Updated: 22.08.2018
#
# License: Apache 2.0
#
import ast


class Alternatives(ast.expr):

    def __init__(self, elts: list):
        super().__init__()
        self.elts = elts

    _fields = ('elts',)


class AttributeDeconstructor(ast.expr):

    def __init__(self, name, args: dict):
        super().__init__()
        self.name = name    # type: str or tuple
        self.args = args

    _fields = ('name', 'args',)


class Binding(ast.expr):

    def __init__(self, target: str, value: ast.expr):
        super().__init__()
        self.target = target
        self.value = value

    _fields = ('target', 'value')


Constant = ast.Constant


class Deconstructor(ast.expr):

    def __init__(self, name: str, args: list):
        super().__init__()
        self.name = name
        self.args = args

    _fields = ('name', 'args',)


class ListPattern(ast.expr):

    def __init__(self, left: list, right: list, sub_seqs: list, gap_bindings: list, min_length: int):
        super().__init__()
        self.left = left
        self.right = right
        self.sub_seqs = sub_seqs
        self.gap_bindings = gap_bindings
        self.min_length = min_length

    _fields = ('left', 'right', 'sub_seqs', 'gap_bindings', 'min_length')


class RegularExpression(ast.expr):

    def __init__(self, pattern: str):
        super().__init__()
        self.pattern = pattern

    _fields = ('pattern',)


class SequenceDeconstructor(ast.expr):

    def __init__(self, elts: list):
        super().__init__()
        self.elts = elts

    _fields = ('elts',)


class TuplePattern(ast.expr):

    def __init__(self, elts: list):
        super().__init__()
        self.elts = elts

    _fields = ('elts')


class Wildcard(ast.expr):

    def __init__(self, is_seq: bool):
        super().__init__()
        self.is_seq = is_seq

    _fields = ('is_seq',)
