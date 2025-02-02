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
    "animation",
    "objects",
    "scene",
]


from .animation import *
from .animation.util import *
from .animation.visibility import *

from .objects import *
from .objects.constraint import *
from .objects.geonodes import *
from .objects.location import *
from .objects.material import *
from .objects.mesh import *
from .objects.modifier import *
from .objects.object import *

from .scene import *
from .scene.camera import *
from .scene.collection import *
from .scene.context import *
from .scene.output import *
from .scene.setup import *

from . import slides
