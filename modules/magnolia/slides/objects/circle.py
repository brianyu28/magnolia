import math

from typing import Optional

from magnolia.slides.objects.object import set_object_default_properties

from ...objects.material import MaterialArg, assign_material, resolve_material
from ...objects.mesh import Edge, Face, MeshData, Vertex, create_object_from_mesh_data
from ...scene.collection import resolve_collection
from ...scene.context import CollectionArg
from ..colors import Color, color_material
from ..position import Anchor, Position, resolve_position, set_anchor, scale_size


def create_circle(
    name: str = "Circle",
    material: MaterialArg | None = None,
    position: Position = (0.5, 0.5),
    radius: float = 100,
    vertex_count: int = 64,
    anchor: Anchor = "center",
    collection: Optional[CollectionArg] = None,
    needs_resolve_position: bool = True,
):
    # Get circle material
    if material is None:
        material = color_material(color=(0, 0, 0))
    material = resolve_material(material)
    coll = resolve_collection(collection)

    # Create circle
    radius, _ = scale_size(radius, 0)
    circle_data = generate_circle_data(radius, vertex_count)

    obj = create_object_from_mesh_data(circle_data, name=name, collection=collection)
    set_anchor(obj, anchor)
    assign_material(obj, material)
    obj.location = resolve_position(position) if needs_resolve_position else position
    set_object_default_properties(obj)
    return obj


def generate_circle_data(
    radius: float,
    vertex_count: int = 64,
) -> MeshData:
    vertices: list[Vertex] = []
    for i in range(vertex_count):
        angle = 2 * math.pi * i / vertex_count
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        vertices.append((x, y, 0))

    edges: list[Edge] = [(i, (i + 1) % vertex_count) for i in range(vertex_count)]
    faces: list[Face] = [tuple(i for i in range(vertex_count))]
    return vertices, edges, faces
