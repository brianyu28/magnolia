from typing import cast

from bpy.types import Object

import bpy
import magnolia as mg

from ..position import Position, resolve_position
from ...objects.geonodes import (
    apply_geonodes,
    create_geonodes_group,
    get_geonodes_group,
)
from ...objects.material import MaterialArg, resolve_material
from ...objects.object import ObjectArg, ObjectsArg, resolve_object, resolve_objects
from ...scene.context import selection, selections


def set_object_default_properties(obj: ObjectArg):
    obj = resolve_object(obj)
    # Set opacity
    obj["mg_opacity"] = 1.0

    # Set UI limits on opacity
    opacity_manager = obj.id_properties_ui("mg_opacity")
    opacity_manager.update(min=0.0, max=1.0)


def set_opacity(obj: ObjectArg, opacity: float):
    obj = resolve_object(obj)
    obj["mg_opacity"] = opacity


def fade_out(
    objs: ObjectsArg | None = None,
    frame: int | None = None,
    duration: int = 20,
    include_children: bool = True,
):
    targets = resolve_objects(objs) if objs is not None else mg.objects.selections()
    frame = mg.scene.current_frame() if frame is None else frame

    for object in targets:
        object["mg_opacity"] = 1.0
        object.keyframe_insert(data_path='["mg_opacity"]', frame=frame)
        object["mg_opacity"] = 0.0
        object.keyframe_insert(data_path='["mg_opacity"]', frame=frame + duration)

        if include_children:
            for child in object.children:
                fade_out(child, frame, duration, include_children=include_children)


def set_position(object: ObjectArg, position: Position):
    """
    Set the position of an object.

    Arguments:

    - `object`: The object to move.
    - `position`: The new position of the object.
    """
    obj = resolve_object(object)
    obj.location = resolve_position(position)


def setX(x: float, objects: ObjectsArg | None = None):
    objs = resolve_objects(objects) if objects else selections()
    position = resolve_position((x, 0, 0))
    for obj in objs:
        obj.location.x = position[0]


def setY(y: float, objects: ObjectsArg | None = None):
    objs = resolve_objects(objects) if objects else selections()
    position = resolve_position((0, y, 0))
    for obj in objs:
        obj.location.y = position[1]


def setZ(z: float, objects: ObjectsArg | None = None):
    objs = resolve_objects(objects) if objects else selections()
    position = resolve_position((0, 0, z))
    for obj in objs:
        obj.location.z = position[2]


def apply_border_modifier(
    obj: ObjectArg,
    width: float = 0.5,
    material: MaterialArg | None = None,
) -> bpy.types.NodesModifier:
    """
    Adds a Border modifier to an object.

    Arguments:

    - `obj`: The object to which to add the modifier.

    Optional arguments:

    - `width`: The width of the border, defaults to 0.5.
    - `material`: The material to use for the border.
    """
    obj = resolve_object(obj)
    result = apply_geonodes(obj, "Border", get_or_create_border_modifier_group())
    result["Socket_1"] = width
    if material is not None:
        result["Socket_2"] = resolve_material(material)
    return result


def get_or_create_border_modifier_group() -> bpy.types.GeometryNodeTree:
    """
    Gets or creates the Magnolia Border modifier.

    The Magnolia Border modifier is a Gemoetry Nodes node group
    that adds a border around a 2D object.

    It can be used inside a Geometry Nodes modifier to control the border
    of a shape.
    """
    modifier_name = "Magnolia_Border_NodeGroup"

    # Check if group already exists.
    group = get_geonodes_group(modifier_name)
    if group is not None:
        return group

    # Create new group.
    group = cast(
        bpy.types.GeometryNodeTree,
        bpy.data.node_groups.new(
            type="GeometryNodeTree", name=modifier_name  # pyright: ignore
        ),
    )
    group.is_modifier = True

    # Socket Inputs: Geometry, Border Width, Border Material
    geo_input = group.interface.new_socket(
        name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry"
    )
    geo_input.attribute_domain = "POINT"

    border_width_input = cast(
        bpy.types.NodeSocketFloat,
        group.interface.new_socket(
            name="Width", in_out="INPUT", socket_type="NodeSocketFloat"
        ),
    )
    border_width_input.default_value = 0.5

    border_material_input = cast(
        bpy.types.NodeSocketMaterial,
        group.interface.new_socket(
            name="Material", in_out="INPUT", socket_type="NodeSocketMaterial"
        ),
    )

    # Socket Output
    socket_output = group.interface.new_socket(
        name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry"
    )
    socket_output.attribute_domain = "POINT"

    # Group Input, input of geometry to entire geometry node group
    group_input = group.nodes.new("NodeGroupInput")
    group_input.name = "Group Input"

    # Group Output, output of geometry node group
    group_output = cast(bpy.types.NodeGroupOutput, group.nodes.new("NodeGroupOutput"))
    group_output.name = "Group Output"
    group_output.is_active_output = True

    # Mesh to Curve: take the geometry and convert it to a curve representing border
    mesh_to_curve = group.nodes.new("GeometryNodeMeshToCurve")
    mesh_to_curve.name = "Mesh to Curve"
    mesh_to_curve.inputs[1].default_value = True  # pyright: ignore

    # Curve to Mesh: convert curve into border mesh, extruding along
    # the "Profile Curve" to give it thickness
    curve_to_mesh = group.nodes.new("GeometryNodeCurveToMesh")
    curve_to_mesh.name = "Curve to Mesh"
    curve_to_mesh.inputs[2].default_value = False  # pyright: ignore

    # Curve Line: create a line representing the thickness of the border
    curve_line = group.nodes.new("GeometryNodeCurvePrimitiveLine")
    curve_line.name = "Curve Line"
    curve_line.mode = "POINTS"  # pyright: ignore
    curve_line.inputs[0].default_value = (0.0, 0.0, 0.0)  # pyright: ignore

    # Join Geometry: combine shape and the shape's border
    join_geometry = group.nodes.new("GeometryNodeJoinGeometry")
    join_geometry.name = "Join Geometry"

    # Math (Division): divide thickness by scale, so that when object is scaled,
    # the border width doesn't change.
    division_node = cast(bpy.types.ShaderNodeMath, group.nodes.new("ShaderNodeMath"))
    division_node.name = "Divide"
    division_node.operation = "DIVIDE"
    division_node.use_clamp = False

    # Math (Multiplication): multiply by -1, since a negative border will allow
    # the border to appear outside the shape.
    multiply_node = cast(bpy.types.ShaderNodeMath, group.nodes.new("ShaderNodeMath"))
    multiply_node.name = "Multiply"
    multiply_node.operation = "MULTIPLY"
    multiply_node.use_clamp = False
    multiply_node.inputs[1].default_value = -1.0  # pyright: ignore

    # Combine XYZ: take the scalar thickness value and convert to a vector
    combine_xyz = group.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz.name = "Combine XYZ"
    combine_xyz.inputs[1].default_value = 0.0  # pyright: ignore
    combine_xyz.inputs[2].default_value = 0.0  # pyright: ignore

    # Separate XYZ: extract the Z value from the object scale
    separate_xyz = group.nodes.new("ShaderNodeSeparateXYZ")
    separate_xyz.name = "Separate XYZ"

    # Self Object: get access to the original object so we can extract scale
    self_object = group.nodes.new("GeometryNodeSelfObject")
    self_object.name = "Self Object"

    # Object Info: extract scale from object
    object_info = cast(
        bpy.types.GeometryNodeObjectInfo, group.nodes.new("GeometryNodeObjectInfo")
    )
    object_info.name = "Object Info"
    object_info.transform_space = "ORIGINAL"
    object_info.inputs[1].default_value = False  # pyright: ignore

    # node Set Material
    set_material = group.nodes.new("GeometryNodeSetMaterial")
    set_material.name = "Set Material"
    set_material.inputs[1].default_value = True  # pyright: ignore

    # Set locations
    group_input.location = (-700, 150)
    group_output.location = (1000, 0)
    mesh_to_curve.location = (-400, 0)
    curve_to_mesh.location = (50, -50)
    curve_line.location = (-150, -200)
    join_geometry.location = (500, 0)
    division_node.location = (-700, -200)
    multiply_node.location = (-500, -200)
    combine_xyz.location = (-300, -200)
    separate_xyz.location = (-900, 0)
    self_object.location = (-1400, -150)
    object_info.location = (-1200, -150)
    set_material.location = (350, -150)

    # Original geometry included in joined geometry
    group.links.new(group_input.outputs[0], join_geometry.inputs[0])
    group.links.new(join_geometry.outputs[0], group_output.inputs[0])

    # Convert border width to a line to use as profile curve
    group.links.new(group_input.outputs[1], division_node.inputs[0])
    group.links.new(division_node.outputs[0], multiply_node.inputs[0])
    group.links.new(multiply_node.outputs[0], combine_xyz.inputs[0])
    group.links.new(combine_xyz.outputs[0], curve_line.inputs[1])
    group.links.new(curve_line.outputs[0], curve_to_mesh.inputs[1])

    # Get scale to use in border width calculation
    group.links.new(self_object.outputs[0], object_info.inputs[0])
    group.links.new(object_info.outputs[2], separate_xyz.inputs[0])
    group.links.new(separate_xyz.outputs[2], division_node.inputs[1])

    # Generate mesh for border
    group.links.new(group_input.outputs[0], mesh_to_curve.inputs[0])
    group.links.new(mesh_to_curve.outputs[0], curve_to_mesh.inputs[0])
    group.links.new(curve_to_mesh.outputs[0], set_material.inputs[0])
    group.links.new(set_material.outputs[0], join_geometry.inputs[0])

    # Set mesh material for border
    group.links.new(group_input.outputs[2], set_material.inputs[2])

    return group
