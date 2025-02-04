import bpy

from typing import Optional, cast

from magnolia.slides.objects.object import set_object_default_properties

from ...objects.material import MaterialArg, assign_material, resolve_material
from ...objects.mesh import create_object_from_mesh_data
from ...scene.collection import resolve_collection
from ...scene.context import CollectionArg
from ..colors import Color, color_material
from ..position import Anchor, Position, resolve_position, set_anchor, scale_size


def create_text(
    content: str,
    size: float = 2.0,
    font: str | None = None,
    name: str = "Text",
    material: MaterialArg | None = None,
    position: Position = (0.5, 0.5),
    anchor: Anchor = "center",
    collection: Optional[CollectionArg] = None,
):
    # Get rectangle material
    if material is None:
        material = color_material(color=(0, 0, 0))
    material = resolve_material(material)
    coll = resolve_collection(collection)

    # Create text
    text_data = cast(bpy.types.TextCurve, bpy.data.curves.new(name=name, type="FONT"))
    text_data.body = content
    obj = bpy.data.objects.new(name=name, object_data=text_data)
    set_text_alignment(obj, anchor)

    # Set font if it exists
    if font is not None and bpy.data.fonts.get(font) is not None:
        text_data.font = bpy.data.fonts.get(font)
    text_data.size = size

    assign_material(obj, material)
    obj.location = resolve_position(position)
    set_object_default_properties(obj)
    coll.objects.link(obj)
    return obj


def set_text_alignment(
    text: bpy.types.Object,
    anchor: Anchor,
):
    data = cast(bpy.types.TextCurve, text.data)
    match anchor:
        case "topleft":
            data.align_x = "LEFT"
            data.align_y = "TOP"
        case "top":
            data.align_x = "CENTER"
            data.align_y = "TOP"
        case "topright":
            data.align_x = "RIGHT"
            data.align_y = "TOP"
        case "left":
            data.align_x = "LEFT"
            data.align_y = "CENTER"
        case "center":
            data.align_x = "CENTER"
            data.align_y = "CENTER"
        case "right":
            data.align_x = "RIGHT"
            data.align_y = "CENTER"
        case "bottomleft":
            data.align_x = "LEFT"
            data.align_y = "BOTTOM"
        case "bottomcenter":
            data.align_x = "CENTER"
            data.align_y = "BOTTOM"
        case "bottomright":
            data.align_x = "RIGHT"
            data.align_y = "BOTTOM"
