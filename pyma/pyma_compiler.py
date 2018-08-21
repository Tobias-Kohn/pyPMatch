#
# (c) 2018, Tobias Kohn
#
# Created: 15.08.2018
# Updated: 21.08.2018
#
# License: Apache 2.0
#
import ast
from . import p_ast
from . import pattern_parser


def replace_dot(s):
    if '.' in s:
        return '_' + s.replace('.', '_') + '_'
    else:
        return s


class Compiler(ast.NodeVisitor):
    """

    """

    def __init__(self, filename: str, source_text: str):
        self.filename = filename
        self.source_text = source_text
        self.methods = []
        self.alternative_lock = 0
        self.sources = set()
        self.targets = []
        self._parser = pattern_parser.PatternParser(self.filename, self.source_text)

    def _syntax_error(self, msg: str, node: ast.AST):
        if hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
            line = self.source_text.split('\n')[node.lineno-1] if self.source_text is not None else None
            return SyntaxError(msg, (self.filename, node.lineno, node.col_offset, line))
        else:
            return SyntaxError(msg)

    def create_class(self, node, name: str, guard: str):
        node = self._parser.parse(node)
        self.methods = []
        self.alternative_lock = 0
        self.sources = set()
        self.targets = []
        cond = self.visit(node).format('node')
        self.targets.sort()
        result = [
            f"class {name}(CaseManager):",
            self._create_init(),
            self._create_enter(),
            self._create_test(cond, guard),
        ]
        result += self.methods
        return '\n\n'.join(result) + '\n'

    def get_targets(self):
        return self.targets

    def _create_enter(self):
        result = "\tdef __enter__(self):\n" \
                 "\t\tself._guard = self.test(self._value)\n" \
                 "\t\tt = self.targets\n"
        if len(self.targets) > 0:
            targets = ', '.join(["t['{}']".format(name) for name in self.targets])
            result += f"\t\treturn self._guard, {targets}"
        else:
            result += "\t\treturn self._guard"
        return result

    def _create_init(self):
        targets = ', '.join([" '{}': None".format(name) for name in self.targets])
        result = "\tdef __init__(self, value, do_break, **source):\n" \
                 "\t\tsuper().__init__(value, do_break)\n" \
                 "\t\tself.source = source\n" \
                 "\t\tself.targets = {" + targets + " }"
        return result

    def _create_test(self, cond: str, guard: str):
        result = f"\tdef test(self, node):\n" \
                 f"\t\tresult = {cond}\n"
        if guard is not None and guard != '':
            result += "\t\tif not {guard}:\n" \
                      "\t\t\treturn False\n"
        result += "\t\treturn result"
        return result

    def check_target(self, target: str, node: ast.AST):
        if self.alternative_lock > 0:
            raise self._syntax_error("name bindings are not allowed inside alternative branches", node)
        if target in self.targets:
            raise self._syntax_error(f"redefinition of name {target}", node)
        self.targets.append(target)

    def make_method(self, code):
        name = f"_test_{len(self.methods)}"
        method = f"\tdef {name}(self, node):\n" \
                 f"\t\t" + '\n\t\t'.join(code)
        self.methods.append(method)
        return f"self.{name}({{}})"

    def use_name(self, name):
        if type(name) is str:
            self.sources.add(name)
            name = replace_dot(name)
            return f"self.source['{name}']"
        elif type(name) in (list, set, tuple):
            names = [self.use_name(n) for n in name]
            return '(' + ', '.join(names) + ')'
        else:
            raise SystemError(f"this is not a name: '{name}'")

    def generic_visit(self, node):
        raise SystemError(f"unexpected node in pattern matching: '{ast.dump(node)}'")

    def visit_Alternatives(self, node: p_ast.Alternatives):
        if all(isinstance(elt, p_ast.Constant) for elt in node.elts):
            return f"{{}} in ({', '.join([repr(elt) for elt in node.elts])})"

        code = []
        if all(isinstance(elt, (p_ast.AttributeDeconstructor, p_ast.Deconstructor)) for elt in node.elts):
            names = set()
            for elt in node.elts:
                if type(elt.name) is str:
                    names.add(elt.name)
                else:
                    for n in elt.name:
                        names.add(n)

            test = f"isinstance({{}}, {self.use_name(names)})"
            if all(isinstance(elt, p_ast.Deconstructor) and len(elt.args) == 0 for elt in node.elts):
                return test
            code.append(f"if not {test.format('node')}: return False")

        self.alternative_lock += 1
        for elt in node.elts:
            test = self.visit(elt)
            code.append(f"if {test.format('node')}: return True")
        self.alternative_lock -= 1
        return self.make_method(code)

    def visit_AttributeDeconstructor(self, node: p_ast.AttributeDeconstructor):
        code = [
            f"if not isinstance(node, {self.use_name(node.name)}): return False",
        ]
        for key in node.args:
            cond = self.visit(node.args[key]).format(key)
            code.append(f"if not hasattr(node, '{key}') or not {cond}: return False")
        code.append("return True")
        return self.make_method(code)

    def visit_Binding(self, node: p_ast.Binding):
        self.check_target(node.target, node)
        cond = self.visit(node.value)
        code = [
            f"self.targets['{node.target}'] = node",
            f"return {cond.format(node)}"
        ]
        return self.make_method(code)

    def visit_Constant(self, node: p_ast.Constant):
        return f"{{}} == {repr(node.value)}"

    def visit_Deconstructor(self, node: p_ast.Deconstructor):
        if len(node.args) == 0:
            return "(unapply({{}}, {self.use_name(node.name)}) is not None)"

        code = [
            f"u = unapply(node, {self.use_name(node.name)})",
            "if u is None: return False",
            f"if len(u) < {len(node.args)}:",
            f"\traise TypeError(\"unpacking of '{node.name}'-value did not provide enough arguments\")",
        ]
        if len(node.args) == 1:
            arg = node.args[0]
            test = self.visit(arg).format("u[0]")
            code.append(f"return {test}")
        else:
            for i, arg in enumerate(node.args):
                test = self.visit(arg).format(f"u[{i}]")
                if test != "True":
                    code.append(f"if not {test}: return False")
            code.append("return True")
        return self.make_method(code)

    def visit_ListPattern(self, node: p_ast.ListPattern):
        raise NotImplementedError("List Pattern Not Yet Implemented!")

    def visit_Wildcard(self, node: p_ast.Wildcard):
        if node.is_seq:
            raise self._syntax_error("unexpected sequence wildcard", node)
        return "True"
