#
# (c) 2018, Tobias Kohn
#
# Created: 15.08.2018
# Updated: 22.08.2018
#
# License: Apache 2.0
#
import builtins, inspect, os.path, sys, types
from . import pyma_importhook
from . import syntax_support


def enable_auto_import():
    """
    Install an import-hook, so that files with `match`/`case` in them are automatically compiler by PyMa.
    """
    # We only install the import-hook for modules in the caller's directory and sub-directories
    frame = inspect.currentframe().f_back
    parent_file = frame.f_code.co_filename
    if not parent_file.startswith('<'):
        path = os.path.dirname(parent_file)
    else:
        path = ''

    finder = pyma_importhook.PyMa_Finder(path)
    if len(sys.meta_path) > 2:
        sys.meta_path.insert(2, finder)
    else:
        sys.meta_path.append(finder)


def pyma_exec(source: str, filename: str = '<string>', module=None):
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
