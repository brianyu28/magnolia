from typing import cast, TypedDict, Union

import bpy

from .object import ObjectArg, resolve_object


# Note: This is an incomplete list of configuration options. As needed, more input properties may
# need to be added to this type in the future.
# Additionally, these fields should all be `NotRequired`, but that's not supported by Blender's
# version of Python.
PrincipledBSDFMaterialConfig = TypedDict(
    "PrincipledBSDFMaterialConfig",
    {
        "Base Color": tuple[float, float, float, float],
        "Roughness": float,
        "Emission Color": tuple[float, float, float, float],
        "Emission Strength": float,
    },
)

MaterialArg = Union[str, bpy.types.Material]
"""A material argument is a material's unique identifier or the material itself."""


def resolve_material(arg: MaterialArg) -> bpy.types.Material:
    """
    Returns a material, given the material or a material identifier.

    Arguments:

    - `arg`: A material or material ID

    Returns: The resulting material
    """
    if isinstance(arg, bpy.types.Material):
        return arg
    return bpy.data.materials[arg]


def assign_material(arg: ObjectArg, material: bpy.types.Material):
    obj = resolve_object(arg)
    mesh = cast(bpy.types.Mesh, obj.data)
    if mesh.materials:
        mesh.materials[0] = material
    else:
        mesh.materials.append(material)


def create_bsdf_material(
    name: str,
    config: PrincipledBSDFMaterialConfig,
    shadow: str = "OPAQUE",  # "OPAQUE" or "NONE"
) -> bpy.types.Material:
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    bsdf = cast(bpy.types.ShaderNodeTree, material.node_tree).nodes["Principled BSDF"]
    for key, value in config.items():
        bsdf.inputs[key].default_value = value  # pyright: ignore
    material.shadow_method = shadow  # pyright: ignore
    return material


def create_emission_material(
    name: str,
    color: Union[tuple[float, float, float], tuple[float, float, float, float]],
    shadow: str = "OPAQUE",  # "OPAQUE" or "NONE"
    opacity_control: bool = False,
) -> bpy.types.Material:
    """
    Creates a new emission material.
    """
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True

    if len(color) == 3:
        color = (*color, 1)

    # Create a new emission node
    node_tree = cast(bpy.types.ShaderNodeTree, material.node_tree)
    emission_node = node_tree.nodes.new("ShaderNodeEmission")
    emission_node.inputs["Color"].default_value = color  # pyright: ignore
    emission_node.location = (-300, -100)
    material.shadow_method = shadow  # pyright: ignore

    # Link emission node to material output
    node_tree.links.new(
        emission_node.outputs["Emission"],
        node_tree.nodes["Material Output"].inputs["Surface"],
    )

    # Remove the default BSDF node from the node tree
    node_tree.nodes.remove(node_tree.nodes["Principled BSDF"])

    # Whether to add opacity controls to the material
    if opacity_control:
        # Create a new transparent BSDF node
        transparent_node = node_tree.nodes.new("ShaderNodeBsdfTransparent")
        transparent_node.location = (-300, 0)

        # Create new mix node
        mix_node = node_tree.nodes.new("ShaderNodeMixShader")
        mix_node.location = (100, 100)

        # Connect emission and transparency nodes to mix node
        node_tree.links.new(
            transparent_node.outputs["BSDF"],
            mix_node.inputs[1],
        )
        node_tree.links.new(
            emission_node.outputs["Emission"],
            mix_node.inputs[2],
        )

        # Create new attribute node.
        # The `mg_opacity` attribute on an object will control the opacity.
        attribute_node = cast(
            bpy.types.ShaderNodeAttribute, node_tree.nodes.new("ShaderNodeAttribute")
        )
        attribute_node.attribute_name = "mg_opacity"
        attribute_node.attribute_type = "OBJECT"
        attribute_node.location = (-300, 200)
        node_tree.links.new(
            attribute_node.outputs["Color"],
            mix_node.inputs[0],
        )

        # Connect mix node to material output
        node_tree.links.new(
            mix_node.outputs["Shader"],
            node_tree.nodes["Material Output"].inputs["Surface"],
        )

        # Set blend mode of material to alpha blend
        material.blend_method = "BLEND"

    return material


def get_or_create_bsdf_material(
    name: str,
    config: PrincipledBSDFMaterialConfig,
    shadow: str = "OPAQUE",
) -> bpy.types.Material:
    """
    Gets an existing material or creates it from a configuration if needed.
    """
    material = bpy.data.materials.get(name)
    if material is not None:
        return material
    return create_bsdf_material(name, config, shadow=shadow)


def get_or_create_emission_material(
    name: str,
    color: Union[tuple[float, float, float], tuple[float, float, float, float]],
    shadow: str = "OPAQUE",  # "OPAQUE" or "NONE"
    opacity_control: bool = False,
) -> bpy.types.Material:
    """
    Gets an existing material or creates it from a configuration if needed.

    Arguments:

    - `name`: The name of the material.
    - `color`: The color of the emission material.

    Optional arguments:

    - `shadow`: The shadow method of the material. Defaults to "OPAQUE".
    - `opacity_control`: Whether to add opacity controls to the material.
      Defaults to False.
    """
    material = bpy.data.materials.get(name)
    if material is not None:
        return material
    return create_emission_material(
        name, color, shadow=shadow, opacity_control=opacity_control
    )
