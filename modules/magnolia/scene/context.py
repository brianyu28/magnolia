from typing import Any, Callable, Union

import bpy

from bpy.types import Object


# An collection argument can be that collection's identifier, or the collection itself
CollectionArg = Union[str, bpy.types.Collection]


def current_frame() -> int:
    """
    Returns the current frame number of the current scene.
    """
    return bpy.context.scene.frame_current


def selections(
    key: Callable[[Object], Any] | str | None = None,
) -> list[Object]:
    """
    Returns a list of currently selected objects.
    """
    objects = list(bpy.context.selected_objects)
    if key is not None:
        if isinstance(key, str):
            if key == "x":
                key = lambda obj: obj.location.x
            elif key == "y":
                key = lambda obj: obj.location.y
            elif key == "z":
                key = lambda obj: obj.location.z
            elif key == "-x":
                key = lambda obj: -obj.location.x
            elif key == "-y":
                key = lambda obj: -obj.location.y
            elif key == "-z":
                key = lambda obj: -obj.location.z
            else:
                raise Exception(f"Unknown key string: {key}")
        objects.sort(key=key)
    return objects


def selection() -> Object:
    """
    Returns the currently selected object.

    Raises an `Exception` if no objects are selected or more than one object is selected.
    """
    objects = selections()
    if len(objects) != 1:
        raise Exception("More than one object selected")
    return objects[0]


def reset_cursor():
    """
    Resets the 3D cursor to the origin.
    """
    bpy.context.scene.cursor.location = (0, 0, 0)
