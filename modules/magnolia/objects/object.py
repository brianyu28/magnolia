from typing import cast, Optional, Union

import bpy

from bpy.types import Object
from mathutils import Matrix

from ..scene.collection import CollectionArg, resolve_collection
from ..scene.context import selection


ObjectArg = Union[str, Object]
"""
An object argument is an object's unique identifier or the object itself.
Most Magnolia functions that work with objects accept an ObjectArg.
"""

ObjectsArg = Union[ObjectArg, list[ObjectArg]]
"""
A single object argument, or a list of object arguments.
"""

ScaleArg = Union[tuple[float, float, float], float]
"""
Represents a scale. Could be a (x, y, z) scale tuple, or a single
value x representing scale (x, x, x).
"""


def resolve_object(arg: ObjectArg) -> Object:
    """
    Returns an object, given the object or an object identifier.

    Arguments:

    - `arg`: An object or object ID

    Returns: The resulting object
    """
    if isinstance(arg, Object):
        return arg
    return bpy.data.objects[arg]


def resolve_objects(args: ObjectsArg) -> list[Object]:
    """
    Given an object argument or a list of object arguments, returns a list of corresponding
    objects.

    Arguments:

    - `args`: An object argument, or a list of object arguments

    Returns: List of objects
    """
    if isinstance(args, list):
        return [resolve_object(arg) for arg in args]
    return [resolve_object(args)]


def resolve_scale(arg: ScaleArg) -> tuple[float, float, float]:
    """
    Given a scale argument, returns a scale tuple.

    Arguments:

    - `arg`: The scale argument

    Returns: A tuple of (x, y, z) scale values
    """
    if isinstance(arg, tuple):
        return arg
    return (arg, arg, arg)


def apply_new_scale(obj: ObjectArg | None = None, scale: ScaleArg = 1):
    obj = resolve_object(obj or selection())
    obj.scale = resolve_scale(scale)

    # Trigger scale apply
    obj.select_set(True)
    bpy.ops.object.transform_apply(
        scale=True, location=False, rotation=False, properties=False
    )


def copy_object(
    arg: ObjectArg,
    name: Optional[str] = None,
    collection: Optional[CollectionArg] = None,
    scale: Optional[ScaleArg] = None,
) -> Object:
    """
    Copies an object from a template object.

    Arguments:

    - `arg`: Template object to copy

    Optional arguments:

    - `name`: Name to give to the new object
    - `collection`: What collection to place the object in, defaults to the first collection of the
      object being copied
    - `scale`: Scale for the new object

    Returns: The newly copied object
    """
    # Get object to copy
    template_obj = resolve_object(arg)

    # Copy the object and its mesh data
    obj = template_obj.copy()
    obj.data = cast(bpy.types.Mesh, template_obj.data).copy()

    # Link the object to the new collection
    coll = resolve_collection(collection)
    coll.objects.link(obj)

    # Recursively create copies of all children
    for template_child in template_obj.children:
        child = copy_object(template_child, collection=collection)
        child.parent = obj
        child.matrix_parent_inverse = obj.matrix_world.inverted()

    # Possibly give the object a name
    if name is not None:
        obj.name = name
        obj.data.name = name

    # Possibly set scale
    if scale is not None:
        obj.scale = resolve_scale(scale)

    return obj


def apply_transform(
    object: ObjectArg | None = None,
    location: bool = False,
    rotation: bool = False,
    scale: bool = False,
):
    """
    Applies a set of transformations to an object.
    Equivalent to "Apply Scale" or "Apply Rotation" in Blender.

    Adapted from: https://blender.stackexchange.com/a/283228
    """
    if not location and not rotation and not scale:
        raise ValueError("At least one of location, rotation, or scale must be True")

    obj = resolve_object(object or selection())

    matrix = obj.matrix_local
    mat_loc, mat_rot, mat_scale = matrix.decompose()
    mat_trasnformation = Matrix.LocRotScale(
        mat_loc if location else None,
        mat_rot if rotation else None,
        mat_scale if scale else None,
    )
    cast(bpy.types.Mesh, obj.data).transform(mat_trasnformation)

    if location:
        obj.location = (0, 0, 0)
    if rotation:
        obj.rotation_euler = (0, 0, 0)
    if scale:
        obj.scale = (1, 1, 1)


def move_to_collection(
    obj: ObjectArg, collection: CollectionArg, include_children: bool = True
):
    """
    Moves an object out of its current collections to a new collection.

    Arguments:

    - `obj`: The object to move
    - `collection`: The collection to move the object to

    Optional arguments:

    - `include_children`: Whether to move the object's children as well.
      Defaults to `True`
    """
    obj = resolve_object(obj)
    collection = resolve_collection(collection)

    # Remove object from all existing collections
    for coll in obj.users_collection:
        coll.objects.unlink(obj)

    # Add object to new collection
    collection.objects.link(obj)

    if include_children:
        for child in obj.children:
            move_to_collection(child, collection, include_children=True)
