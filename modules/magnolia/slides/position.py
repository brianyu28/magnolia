from typing import cast, Literal

import bpy
import mathutils

from ..objects.object import ObjectArg, resolve_object

Anchor = Literal[
    "topleft",
    "top",
    "topright",
    "left",
    "center",
    "right",
    "bottomleft",
    "bottom",
    "bottomright",
]

Position = tuple[float, float] | tuple[float, float, float]


def resolve_position(position: Position) -> tuple[float, float, float]:
    """
    A Magnolia position can be in one of two units:
        - Pixels, as used in Magnolia slides
        - Proportion of total slide

    Magnolia positions also optionally include a "layer"
    defining its z-index.

    Regardless of the unit, resolving the position converts the position
    to a Blender world position.
    """
    if len(position) == 2:
        x, y = position
        z = 1
    else:
        x, y, z = position

    slide_width, slide_height = get_slide_dimensions()

    if x >= 0 and x <= 1:
        x = x * slide_width
    if y >= 0 and y <= 1:
        y = y * slide_height

    # x and y values get scaled by 100 to get correct position.
    # Each layer is 0.02 meters above the previous.
    return (x / 100, y / 100, z * 0.02)


def scale_length(length: float):
    """
    Scales a length unit from pixels to the slide proportions.
    """
    return length / 100


def scale_size(width: float, height: float):
    """
    Scales size appropriately for a slide.

    On a slide, each output rendered pixel takes up 1/100th of a meter of
    space in the scene.
    """
    return scale_length(width), scale_length(height)


def set_slide_dimensions(width: int, height: int):
    """
    Sets the dimensions of the slide.
    """
    bpy.context.scene.render.resolution_x = width
    bpy.context.scene.render.resolution_y = height


def get_slide_dimensions() -> tuple[int, int]:
    """
    Returns the dimensions of the slide in (width, height).
    """
    return (
        bpy.context.scene.render.resolution_x,
        bpy.context.scene.render.resolution_y,
    )


def get_bounding_box(
    object: ObjectArg,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """
    Given an object, returns the 2D bounding box of the object.
    Bounding box is of the form ((min_x, min_y), (max_x, max_y)).
    """
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    object = resolve_object(object)
    mesh = cast(bpy.types.Mesh, object.data)
    for vertex in mesh.vertices:
        # Get the world coordinates of the vertex
        world_vertex = object.matrix_world @ vertex.co
        x, y, _ = world_vertex

        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)

    return ((min_x, min_y), (max_x, max_y))


def set_anchor(object: ObjectArg, anchor: Anchor):
    """
    Changes the anchor of the object to the given anchor.
    """
    object = resolve_object(object)
    (min_x, min_y), (max_x, max_y) = get_bounding_box(object)
    avg_x = (min_x + max_x) / 2
    avg_y = (min_y + max_y) / 2

    match anchor:
        case "topleft":
            target = (min_x, max_y)
        case "top":
            target = (avg_x, max_y)
        case "topright":
            target = (max_x, max_y)
        case "left":
            target = (min_x, avg_y)
        case "center":
            target = (avg_x, avg_y)
        case "right":
            target = (max_x, avg_y)
        case "bottomleft":
            target = (min_x, min_y)
        case "bottom":
            target = (avg_x, min_y)
        case "bottomright":
            target = (max_x, min_y)

    # Translate object mesh data to match the new trasnformation
    (x, y) = object.matrix_world.translation[:2]
    translation = mathutils.Matrix.Translation((x - target[0], y - target[1], 0))
    mesh = cast(bpy.types.Mesh, object.data)
    mesh.transform(translation)
