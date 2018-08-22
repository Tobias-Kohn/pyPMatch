#
# (c) 2018, Tobias Kohn
#
# Created: 22.08.2018
# Updated: 22.08.2018
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
import sys


def _get_original_path_finder():
    for item in sys.meta_path:
        try:
            if item.__name__ == 'PathFinder':
                return item
        except:
            pass
    return None


class PyMa_Loader(Loader):

    def __init__(self, filename):
        super().__init__()
        self._filename = filename

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        from . import pyma_exec
        with open(module.__name__) as input_file:
            input_text = ''.join(input_file.readlines())
            pyma_exec(input_text, filename=self._filename, module=module)


class PyMa_Finder(MetaPathFinder):

    def __init__(self, base_path: str):
        super().__init__()
        self._base_path = base_path
        self._path_finder = _get_original_path_finder()

    def find_spec(self, fullname, path, target = None):
        if self._path_finder:
            result = self._path_finder.find_spec(fullname, path, target)
            try:
                if result.origin.startswith(self._base_path):
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
