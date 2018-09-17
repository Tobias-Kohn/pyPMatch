#
# (c) 2018, Tobias Kohn
#
# Created: 15.08.2018
# Updated: 17.09.2018
#
# License: Apache 2.0
#
import builtins, inspect, os.path, types
from . import syntax_support
from . import pama_decorators
from .match_template import MatchException


def case(pattern: str):
    """
    Use `case` as a decorator for functions, with full unpacking of the argument(s).
    ```
    @case("[x @ int|float, *y]")
    def foo(x, y):
        ...
    ```

    Guards are not supported at the moment.
    """
    def decorate(f):
        name = f.__code__.co_name
        frame = inspect.currentframe().f_back
        multi = frame.f_locals.get(name, None)
        if not isinstance(multi, pama_decorators.MultiFunction):
            multi = pama_decorators.MultiFunction(name, frame.f_code.co_filename)
        multi.register(frame, pattern, f)
        return multi

    return decorate


def pama_exec(source: str, filename: str = '<string>', module=None):
    """
    Takes the source code of a program as string, compiles, and then executes the given program.  The program can
    contain `match`/`case` statements, which are duly replaced before using Python's builtin compiler.

    The code is run inside a new dedicated module, which is then returned.
    """
    scanner = syntax_support.TextScanner(filename, source)
    code = scanner.get_text()
    match_module = scanner.get_match_code()
    match_mod = types.ModuleType('__match__')
    exec(builtins.compile(match_module, '__match__', 'exec'), match_mod.__dict__)
    compiled_code = builtins.compile(code, filename, 'exec')
    if not filename.startswith('<'):
        name = os.path.basename(filename)
        if name.endswith('.py'): name = name[:-3]
    else:
        name = filename
    mod = types.ModuleType(name) if module is None else module
    mod.__match__ = match_mod
    exec(compiled_code, mod.__dict__)
    return mod


def pama_translate(source: str, filename: str = '<string>'):
    """
    Translates the given source program to regular Python code, and returns the translated code, as well as the
    code of the auxiliary `__match__` module.
    """
    if source is None:
        with open(filename) as f:
            source = f.read()
    scanner = syntax_support.TextScanner(filename, source)
    code = scanner.get_text()
    match_module = scanner.get_match_code()
    return code, match_module
