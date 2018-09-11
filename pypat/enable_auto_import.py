#
# (c) 2018, Tobias Kohn
#
# Created: 22.08.2018
# Updated: 22.08.2018
#
# License: Apache 2.0
#
import inspect, os.path
from . import pama_importhook


def _enable_auto_import():
    """
    Install an import-hook, so that files with `match`/`case` in them are automatically compiler by PyMa.
    """
    # We only install the import-hook for modules in the caller's directory and sub-directories.  To that end, we
    # have to extract the path of the calling module first.
    frame = inspect.currentframe().f_back   # <- frame of this module
    frame = frame.f_back                    # <- one step outside
    while frame.f_back is not None and frame.f_code.co_filename.startswith('<'):
        frame = frame.f_back                # <- looking for a frame with a "real" filename
    parent_file = frame.f_code.co_filename
    if not parent_file.startswith('<'):
        path = os.path.dirname(parent_file)
    else:
        path = ''

    pama_importhook.install_hook(path)


_enable_auto_import()
