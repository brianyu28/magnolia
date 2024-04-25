import importlib
import sys


def reload():
    """
    Reloads the Magnolia module and all submodules.
    """
    for module_name, module in list(sys.modules.items()):
        if module_name.startswith(__name__):
            importlib.reload(module)
    importlib.reload(sys.modules[__name__])


__all__ = [
    "objects",
    "scene",
    "visibility",
]


from .objects import *
from .scene import *
from .visibility import *
