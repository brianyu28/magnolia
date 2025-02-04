from typing import cast, Optional

import bpy

from bpy.types import Object

from ..scene import CollectionArg, resolve_collection, selection
from .object import ObjectArg, resolve_object


# A vertex is represented as a tuple of (x, y, z)
Vertex = tuple[float, float, float]

# An edge is represented as a pair of vertex indices
Edge = tuple[int, int]

# A face is represented as a variable-length tuple of vertex indices
Face = tuple[int, ...]

# Meshes contain data about their vertices, edges, and faces
MeshData = tuple[list[Vertex], list[Edge], list[Face]]


def object_to_mesh_data(arg: Optional[ObjectArg] = None) -> MeshData:
    """
    Return the mesh data associated with an object.

    Optional arguments:

    - `arg`: The object whose mesh data should be returned. Defaults to current
      selection.

    Returns:

    - `vertices`: List of vertices, each a tuple (x, y, z)
    - `edges`: List of edges, each a tuple pair of vertex indices
    - `faces`: List of faces, each a tuple of vertex indices
    """
    obj = resolve_object(arg or selection())
    mesh = cast(bpy.types.Mesh, obj.data)
    vertices = [vertex.co[:] for vertex in mesh.vertices]
    edges = [edge.vertices[:] for edge in mesh.edges]
    faces = [face.vertices[:] for face in mesh.polygons]
    return vertices, edges, faces  # pyright: ignore


def create_object_from_mesh_data(
    data: MeshData,
    name: str,
    collection: Optional[CollectionArg] = None,
    shade_flat: bool = False,
) -> Object:
    """
    Converts mesh data to a new Blender object with that mesh.

    Arguments:

    - `data`: The mesh data for the new object
    - `name`: The name for the new object

    Optional arguments:

    - `collection`: The collection to link the new object to
    - `shade_flat`: Whether to shade flat or smooth

    Returns: The newly created object
    """
    vertices, edges, faces = data
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, edges, faces, shade_flat=shade_flat)
    obj = bpy.data.objects.new(name, mesh)
    coll = resolve_collection(collection)
    coll.objects.link(obj)
    return obj


def get_selected_vertex_location() -> tuple[float, float, float]:
    """
    Gets the location of the currently selected vertex.
    Assumes only one vertex selected.

    User must leave edit mode and go back to object mode for the selection to be
    detected. (When interacting with edit mode, the user is working with a
    temporary copy of the mesh.)
    """
    obj = selection()

    if isinstance(obj.data, bpy.types.Mesh):
        vertices = [v for v in obj.data.vertices if v.select]
    elif isinstance(obj.data, bpy.types.Curve):
        vertices = [v for spline in obj.data.splines for v in spline.points if v.select]
        pass
    else:
        # Other object types not yet supported
        raise ValueError("Selected object is not a mesh or curve")

    if not vertices:
        raise ValueError("No vertices selected")
    if len(vertices) > 1:
        raise ValueError("More than one vertex selected")
    return tuple(vertices[0].co)  # pyright: ignore


def set_selected_vertex_location(location: tuple[float, float, float]):
    obj = selection()

    if isinstance(obj.data, bpy.types.Mesh):
        vertices = [v for v in obj.data.vertices if v.select]
    elif isinstance(obj.data, bpy.types.Curve):
        vertices = [v for spline in obj.data.splines for v in spline.points if v.select]
        pass
    else:
        # Other object types not yet supported
        raise ValueError("Selected object is not a mesh or curve")

    if not vertices:
        raise ValueError("No vertices selected")
    if len(vertices) > 1:
        raise ValueError("More than one vertex selected")

    if location[0] is not None:
        vertices[0].co[0] = location[0]

    if location[1] is not None:
        vertices[0].co[1] = location[1]

    if location[2] is not None:
        vertices[0].co[2] = location[2]
