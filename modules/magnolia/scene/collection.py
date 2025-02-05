from typing import Optional

import bpy

from .context import CollectionArg
from ..objects.object import ObjectArg, resolve_object


def create_collection(name: str, link: bool = True) -> bpy.types.Collection:
    """
    Creates a collection with the given name.

    Arguments:

    - `name`: The name of the collection

    Optional arguments:

    - `link`: Whether to link the collection to the current scene. Defaults to `True`

    Returns: The created collection
    """
    coll = bpy.data.collections.new(name)
    if link:
        bpy.context.scene.collection.children.link(coll)
    return coll


def resolve_collection(arg: Optional[CollectionArg] = None) -> bpy.types.Collection:
    """
    Returns a collection, given the collection or a collection identifier.
    If neither is specified, the current context's collection is used.

    Optional arguments:

    - `arg`: A collection or collection ID

    Returns: The resulting collection
    """
    if arg is None:
        return bpy.context.scene.collection
    if isinstance(arg, bpy.types.Collection):
        return arg
    return bpy.data.collections[arg]


def scene_collection() -> bpy.types.Collection:
    """
    Returns the current scene collection.
    """
    return bpy.context.scene.collection


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
