from typing import Optional

import bpy

from .context import CollectionArg


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


def create_or_resolve_collection(arg: CollectionArg):
    """
    Returns a collection, creating it if necessary.
    """
    try:
        return resolve_collection(arg)
    except KeyError:
        if isinstance(arg, str):
            return create_collection(arg)
    return None
