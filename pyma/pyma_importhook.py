#
# (c) 2018, Tobias Kohn
#
# Created: 22.08.2018
# Updated: 22.08.2018
#
# License: Apache 2.0
#
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
            return result

        else:
            return None
