#
# (c) 2018, Tobias Kohn
#
# Created: 22.08.2018
# Updated: 03.09.2018
#
# License: Apache 2.0
#
"""
Our import hook reuses Python's own `PathFinder`, which is used to locate "external" modules (as opposed to builtin
modules).  Once the `PathFinder` has located a module, we check if the module is in the same directory (or a sub-
directory) as the module that called the `enabled_auto_import`.  In other words: PyMa does not interfere with modules
from other packages in your system.
"""
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from os.path import normpath
import sys


def _get_original_path_finder():
    """
    Try and return Python's `PathFinder`, which is responsible for importing non-builtin modules.  If it can't be
    found, the function returns `None`.

    Our own import hook uses the original `PathFinder` under the hood, and delegates whatever it can to it.
    """
    for item in sys.meta_path:
        try:
            if item.__name__ == 'PathFinder':
                return item
        except:
            pass
    return None


def _has_case_statement(path):
    """
    Check if the file possibly contains a `case` statement at all.  There is a slight chance that the result might
    be wrong in that the function could return `True` for a file containing the word `case` in a position that looks
    like a statement, but is not.

    Our import hook tries to import/compiler only files it has to, i. e. containing a `case` statement.  Everything
    else should be left alone.  The function `_has_case_statement` is used to check if a file needs to be imported by
    our import hook.
    """
    try:
        with open(path) as f:
            for line in f.readlines():
                stripped_line = line.lstrip()
                if stripped_line.startswith('case') and len(stripped_line) > 4 and not stripped_line[4].isidentifier():
                    s = stripped_line[4:].lstrip()
                    if len(s) == 0 or s[0] in ('=', ',', ';', '.'):
                        continue
                    if len(s) > 1 and s[1] == '=' and not s[0].isalnum():
                        continue
                    return True
    except:
        pass
    return False


class PyMa_Loader(Loader):

    def __init__(self, filename):
        super().__init__()
        self._filename = filename

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        from . import pama_exec
        with open(module.__name__) as input_file:
            input_text = ''.join(input_file.readlines())
            pama_exec(input_text, filename=self._filename, module=module)


class PyMa_Finder(MetaPathFinder):

    def __init__(self, base_path: str):
        super().__init__()
        self._base_path = normpath(base_path)
        self._path_finder = _get_original_path_finder()

    def find_spec(self, fullname, path, target = None):
        if self._path_finder:
            result = self._path_finder.find_spec(fullname, path, target)
            try:
                name = normpath(result.origin)
                if name.startswith(self._base_path) and _has_case_statement(name):
                    return ModuleSpec(result.origin, PyMa_Loader(result.origin))
            except:
                pass

        return None


def install_hook(base_path: str):
    finder = PyMa_Finder(base_path)
    for i, item in enumerate(sys.meta_path):
        try:
            if item.__name__ == 'PathFinder':
                sys.meta_path.insert(i, finder)
                return
        except:
            pass

    if len(sys.meta_path) > 2:
        sys.meta_path.insert(2, finder)
    else:
        sys.meta_path.append(finder)
