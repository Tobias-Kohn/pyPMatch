#
# (c) 2018, Tobias Kohn
#
# Created: 24.08.2018
# Updated: 24.08.2018
#
# License: Apache 2.0
#
import ast, builtins, types
import os.path
from . import pama_compiler


def _resolve_name(frame, name: str):
    while frame is not None:
        if name in frame.f_locals:
            return frame.f_locals[name]
        if frame.f_back is not None:
            frame = frame.f_back
        elif name in frame.f_globals:
            return frame.f_globals[name]
    if name in builtins.__dict__:
        return builtins.__dict__[name]
    else:
        return None


# TODO: Complete the implementation
# TODO: Make sure it follows already existing designs as far as possible
#    -> PEP  443, https://www.python.org/dev/peps/pep-0443/   (cf. functools)
#    -> PEP 3124, https://www.python.org/dev/peps/pep-3124/
# TODO: Make sure it works with methods

class MultiFunction(object):

    def __init__(self, name: str, filename: str):
        self.name = name
        self.functions = []
        self.compiler = pama_compiler.Compiler(filename, None)
        self._module = None
        self._name_index = 0
        self._mod_code = []
        name = os.path.join(os.path.dirname(__file__), 'match_template.py')
        with open(name) as f:
            self._mod_code.append(''.join(list(f.readlines())))

    def __call__(self, *args, **kwargs):
        if len(args) == 1:
            args = args[0]
        else:
            args = tuple(args)
        return self.dispatch(args, kwargs)

    def dispatch(self, arg, kwargs):
        if self.validate():
            mod = self._module.__dict__
            for (name, sources, targets, _, function) in self.functions:
                P = mod[name]
                p = P([arg, False], **sources)
                q = p.__enter__()
                if type(q) is bool:
                    guard, f_vars = q, []
                else:
                    guard, *f_vars = q
                if guard:
                    kwargs.update({ key: value for key, value in zip(targets, f_vars) })
                    return function(**kwargs)

            return None
        else:
            raise SystemError("could not compile patterns")

    def invalidate(self):
        self._module = None

    def register(self, frame, pattern: str, function):
        self._name_index += 1
        name = f"Case{self._name_index}"
        ast_node = ast.parse(pattern)
        code = self.compiler.create_class(ast_node, name, None)
        self._mod_code.append(code)
        targets = self.compiler.targets
        sources = self.compiler.sources
        sources = { s: _resolve_name(frame, s) for s in sources }
        self.functions.append((name, sources, targets, pattern, function))
        self.invalidate()

    def validate(self):
        if self._module is None:
            code = '\n\n'.join(self._mod_code)
            self._module = types.ModuleType('__match__')
            exec(builtins.compile(code, '__match__', 'exec'), self._module.__dict__)

        return self._module is not None
