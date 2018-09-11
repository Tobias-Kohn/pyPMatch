#
# (c) 2018, Tobias Kohn
#
# Created: 15.08.2018
# Updated: 11.09.2018
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


class RegularExpression(ast.expr):

    def __init__(self, pattern: str):
        super().__init__()
        self.pattern = pattern

    _fields = ('pattern',)


class RegularExprType(ast.expr):

    def __init__(self, type_name: str):
        super().__init__()
        self.type_name = type_name

    _fields = ('type_name',)


class SequencePattern(ast.expr):

    def __init__(self, left: list, right: list, sub_seqs: list, targets: list, min_length: int, exact_length: int):
        super().__init__()
        self.left = left
        self.right = right
        self.sub_seqs = sub_seqs
        self.targets = targets
        self.min_length = min_length
        self.exact_length = exact_length

    _fields = ('left', 'right', 'sub_seqs', 'targets', 'min_length', 'exact_length')


class SequenceRepetition(ast.expr):

    def __init__(self, value, rep_count):
        super().__init__()
        self.value = value
        self.rep_count = rep_count

    _fields = ('value', 'rep_count')


class StringDeconstructor(ast.expr):

    def __init__(self, groups: list, fixed_start: bool, targets: list):
        super().__init__()
        self.groups = groups
        self.fixed_start = fixed_start
        self.targets = targets

    _fields = ('groups', 'fixed_start', 'targets')


class Wildcard(ast.expr):

    def __init__(self, is_seq: bool):
        super().__init__()
        self.is_seq = is_seq

    _fields = ('is_seq',)
