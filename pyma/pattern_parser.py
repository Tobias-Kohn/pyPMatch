#
# (c) 2018, Tobias Kohn
#
# Created: 15.08.2018
# Updated: 23.08.2018
#
# License: Apache 2.0
#
import ast
from . import pyma_ast


_cl = ast.copy_location


def _flatten_op(node, op):
    if isinstance(node, ast.BinOp) and isinstance(node.op, op):
        left = _flatten_op(node.left, op)
        right = _flatten_op(node.right, op)
        return left + right

    else:
        return [node]


def _get_name(node):
    if isinstance(node, ast.Name):
        return node.id

    elif isinstance(node, ast.Attribute):
        base = _get_name(node.value)
        if base is not None:
            return base + '.' + node.attr

    elif isinstance(node, ast.Tuple):
        names = [_get_name(elt) for elt in node.elts]
        if all(type(item) is str for item in names):
            if any(item == '_' for item in names):
                return '_'
            else:
                return tuple(names)

    return None


def _is_same_const_type(nodeA, nodeB):
    if type(nodeA) is type(nodeB):
        if isinstance(nodeA, ast.Num):
            return type(nodeA.n) is type(nodeB.n) is int

        elif isinstance(nodeA, ast.Str):
            return len(nodeA.s) == len(nodeB.s) == 1

    return False


def is_seq_wildcard(node):
    if isinstance(node, pyma_ast.Wildcard):
        return node.is_seq
    elif isinstance(node, pyma_ast.Binding):
        return is_seq_wildcard(node.value)
    else:
        return False


def is_wildcard(node):
    if isinstance(node, pyma_ast.Wildcard):
        return True
    elif isinstance(node, pyma_ast.Binding):
        return is_wildcard(node.value)
    else:
        return False



class PatternParser(ast.NodeTransformer):
    """
    Transforms the AST of a pattern to a pattern-specific AST.
    """

    def __init__(self, filename: str, source_text: str):
        self.filename = filename
        self.source_text = source_text

    def parse(self, node):
        if type(node) is str:
            node = ast.parse(node)
        return self.visit(node)

    def _syntax_error(self, msg: str, node: ast.AST):
        if hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
            line = self.source_text.split('\n')[node.lineno-1] if self.source_text is not None else None
            return SyntaxError(msg, (self.filename, node.lineno, node.col_offset, line))
        else:
            return SyntaxError(msg)

    def make_binding(self, target, value):
        if isinstance(value, ast.Name):
            value = pyma_ast.Deconstructor(name=value.id, args=[])

        if isinstance(target, ast.Name):
            name = target.id
            if name == '_':
                return value
            elif isinstance(value, pyma_ast.Binding):
                raise self._syntax_error("binding value to more than one name", value)
            else:
                return pyma_ast.Binding(name, value)

        else:
            raise self._syntax_error("the target of a binding must be a valid name", target)

    def make_range_int(self, start, end):
        if start.n < end.n:
            items = []
            for i in range(start.n, end.n):
                items.append(_cl(ast.Num(n=i), start))
            items.append(end)
            return items

        elif start.n == end.n:
            return [start]

        else:
            return None

    def make_range_str(self, start, end):
        if start.s < end.s:
            items = []
            for i in range(ord(start.s), ord(end.s)):
                items.append(_cl(ast.Str(s=chr(i)), start))
            items.append(end)
            return items

        elif start.s == end.s:
            return [start]

        else:
            return []

    def generic_visit(self, node):
        raise self._syntax_error(f"'{type(node)}' is not supported in pattern matching", node)

    def _handle_or(self, elts, node):
        # Special case: `x @ 2 | 3` is interpreted as `x @ (2 | 3)`
        if isinstance(elts[0], ast.BinOp) and isinstance(elts[0].op, ast.MatMult):
            bind_node = elts[0]
            elts[0] = bind_node.right
            result = self._handle_or(elts, node)
            return _cl(self.make_binding(bind_node.left, result), bind_node)

        # Handle the special cases `int | ... | int` and `char | ... | char`
        if len(elts) == 3 and isinstance(elts[1], ast.Ellipsis) and \
                _is_same_const_type(elts[0], elts[2]):
            if type(elts[0]) is int:
                items = self.make_range_int(elts[0], elts[2])
            elif type(elts[0]) is str:
                items = self.make_range_str(elts[0], elts[2])
            else:
                items = None

            if len(items) <= 1:
                raise self._syntax_error("there must be at least two alternatives", node)

        # Special case: `A|B|C` is interpreted as `A()|B()|C()`
        if all(isinstance(elt, ast.Name) for elt in elts):
            elts = [pyma_ast.Deconstructor(elt.id, []) for elt in elts]
        else:
            elts = [self.visit(elt) for elt in elts]

        # There are no wildcards or name bindings allowed
        if any(is_wildcard(elt) for elt in elts):
            raise self._syntax_error("wildcards not allowed in alternatives", node)
        if any(isinstance(elt, pyma_ast.Binding) for elt in elts):
            raise self._syntax_error("bindings not allowed in alternatives", node)

        return _cl(pyma_ast.Alternatives(elts=elts), node)

    def _handle_seq(self, node):
        elts = [self.visit(elt) for elt in node.elts]
        if len(elts) == 0:
            return _cl(pyma_ast.SequencePattern([], [], [], [], 0, 0), node)

        # Split the sequence at each 'sequence wildcard'
        names = []
        sub_seqs = [[]]
        for elt in elts:
            if is_seq_wildcard(elt):
                sub_seqs.append([])
                if isinstance(elt, pyma_ast.Binding):
                    names.append(elt.target)
                else:
                    names.append(None)
            else:
                sub_seqs[-1].append(elt)

        while[-1] is None:
            del names[-1]

        left = sub_seqs[0]
        del sub_seqs[0]
        if len(sub_seqs) == 0:
            exact_length = len(left) if len(left) == len(elts) else None
            return _cl(pyma_ast.SequencePattern(left, [], [], [], len(left), exact_length), node)
        if len(left) > 0 and isinstance(left[-1], pyma_ast.Wildcard):
            raise self._syntax_error("invalid wildcards in sequence", node)

        if len(sub_seqs) > 0:
            right = sub_seqs[-1]
            del sub_seqs[-1]
        else:
            right = []
        if len(right) > 0 and isinstance(right[0], pyma_ast.Wildcard):
            raise self._syntax_error("invalid wildcards in sequence", node)

        # Check for possible errors such as two adjacent wildcard sequences
        for item in sub_seqs:
            # An empty sub-sequence cannot be matched unambiguously
            if len(item) == 0:
                raise self._syntax_error("invalid wildcards in sequence", node)
            # The first and last item of a sequence cannot be plain wildcards
            if isinstance(item[0], pyma_ast.Wildcard) or isinstance(item[-1], pyma_ast.Wildcard):
                raise self._syntax_error("invalid wildcards in sequence", node)
            # If there are only wildcards here, we cannot identify the sub-sequence later on
            if all(is_wildcard(elt) for elt in item):
                raise self._syntax_error("invalid wildcards in sequence", node)

        min_length = len(left) + len(right) + sum([len(item) for item in sub_seqs])
        return _cl(pyma_ast.SequencePattern(left, right, sub_seqs, names, min_length, None), node)

    def visit_Alternatives(self, node: pyma_ast.Alternatives):
        return node

    def visit_AttributeDestructor(self, node: pyma_ast.AttributeDeconstructor):
        return node

    def visit_Binding(self, node: pyma_ast.Binding):
        return node

    def visit_BinOp(self, node: ast.BinOp):
        op = node.op
        if isinstance(op, ast.Add):
            # TODO: add proper support for string deconstructor
            elts = _flatten_op(node, ast.Add)
            elts = [self.visit(elt) for elt in elts]
            return pyma_ast.StringDeconstructor(elts=elts)

        elif isinstance(op, ast.BitOr):
            elts = _flatten_op(node, ast.BitOr)
            return self._handle_or(elts, node)

        elif isinstance(op, ast.MatMult):
            # Special case: `a @ b` is interpreted as `a @ b()`
            if isinstance(node.right, ast.Name):
                right = pyma_ast.Deconstructor(node.right.id, [])
                return _cl(self.make_binding(node.left, right), node)
            else:
                return _cl(self.make_binding(node.left, self.visit(node.right)), node)

        else:
            raise self._syntax_error(f"operator '{type(node.op)}' not supported in pattern matching", node.op)

    def visit_Call(self, node: ast.Call):
        name = _get_name(node.func)
        if len(node.keywords) == 0:
            return pyma_ast.Deconstructor(name, [self.visit(arg) for arg in node.args])

        elif len(node.args) == 0:
            return pyma_ast.AttributeDeconstructor(name, {arg.arg: self.visit(arg.value) for arg in node.keywords})

        else:
            raise self._syntax_error("cannot mix positional and keyword arguments for deconstructor", node)

    def visit_Constant(self, node: ast.Constant):
        return node

    def visit_Deconstructor(self, node: pyma_ast.Deconstructor):
        return node

    def visit_Ellipsis(self, node: ast.Ellipsis):
        return _cl(pyma_ast.Wildcard(is_seq=True), node)

    def visit_Expr(self, node: ast.Expr):
        return self.visit(node.value)

    def visit_List(self, node: ast.List):
        return self._handle_seq(node)

    def visit_ListPattern(self, node: pyma_ast.SequencePattern):
        return node

    def visit_Module(self, node: ast.Module):
        assert len(node.body) == 1
        return self.visit(node.body[0])

    def visit_Name(self, node: ast.Name):
        name = node.id
        result = _cl(pyma_ast.Wildcard(is_seq=False), node)
        if name != '_':
            result = _cl(pyma_ast.Binding(target=name, value=result), node)
        return result

    def visit_NameConstant(self, node: ast.NameConstant):
        return _cl(pyma_ast.Constant(value=node.value), node)

    def visit_Num(self, node: ast.Num):
        return _cl(pyma_ast.Constant(value=node.n), node)

    def visit_Set(self, node: ast.Set):
        if len(node.elts) == 1 and isinstance(node.elts[0], ast.Str):
            return _cl(pyma_ast.RegularExpression(pattern=node.elts[0].s), node)
        else:
            self.generic_visit(node)

    def visit_Starred(self, node: ast.Starred):
        if isinstance(node.value, ast.Name):
            name = node.value.id
            result = _cl(pyma_ast.Wildcard(is_seq=True), node.value)
            if name != '_':
                result = _cl(pyma_ast.Binding(name, result), node)
            return result

        raise self._syntax_error(f"can't assign to '{type(node)}'", node)

    def visit_Str(self, node: ast.Str):
        return _cl(pyma_ast.Constant(value=node.s), node)

    def visit_Tuple(self, node: ast.Tuple):
        return self._handle_seq(node)

    def visit_Wildcard(self, node: pyma_ast.Wildcard):
        return node
