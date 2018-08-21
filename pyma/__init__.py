#
# (c) 2018, Tobias Kohn
#
# Created: 15.08.2018
# Updated: 21.08.2018
#
# License: Apache 2.0
#
import builtins, os.path, types
from . import syntax_support


def pyma_exec(source: str, filename: str = '<string>'):
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
    mod = types.ModuleType(name)
    mod.__match__ = match_mod
    exec(compiled_code, mod.__dict__)
    return mod
