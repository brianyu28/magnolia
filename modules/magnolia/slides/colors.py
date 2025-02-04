from typing import cast

import bpy

from ..objects.material import create_emission_material, get_or_create_emission_material


Color = tuple[int, int, int]
"""A color used in a Magnolia slide is a tuple of red, green, blue values,
where each value is in the range [0, 255]."""


def color_material(
    color: Color = (0, 0, 0),
    name: str | None = None,
    opacity_controls: bool = True,
):
    """
    Gets or creates an emission color material.

    Optional arguments:

    - `name`: The name of the material.
      A default name is supplied if none provided.
    - `color`: The color of the material.
    - `opacity_controls`: Whether to add opacity controls to the material.
      Defaults to True.
    """
    red, green, blue = color
    name = (
        name or f"MgColorMat_{red}_{green}_{blue}{'_alpha' if opacity_controls else ''}"
    )
    return get_or_create_emission_material(
        name,
        srgb_to_linear_rgb(color),
        shadow="NONE",
        opacity_control=opacity_controls,
    )


def srgb_to_linear_rgb(color: Color) -> tuple[float, float, float, float]:
    """
    Blender interprets hex colors in sRGB color space, but Blender uses
    a linear RGB color space. To get the color to appear correctly, we need to
    convert sRGB colors to linear RGB color space.

    Logic adapted from: https://blender.stackexchange.com/a/158902
    """

    def convert_channel(c: float):
        if c < 0:
            return 0
        elif c < 0.04045:
            return c / 12.92
        else:
            return ((c + 0.055) / 1.055) ** 2.4

    r, g, b = color
    return (
        convert_channel(r / 255),
        convert_channel(g / 255),
        convert_channel(b / 255),
        1,
    )
