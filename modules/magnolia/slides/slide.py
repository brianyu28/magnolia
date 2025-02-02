from typing import cast

import bpy

from ..objects.material import assign_material
from ..objects.mesh import create_object_from_mesh_data, MeshData
from ..scene.camera import create_camera
from ..scene.collection import create_collection
from ..scene.output import set_framerate
from .colors import Color, color_material
from .position import scale_size, set_slide_dimensions


def create_slide(
    scene: bpy.types.Scene | None = None,
    color: Color = (255, 255, 255),
    width: int = 3840,
    height: int = 2160,
    framerate: int = 30,
):
    """
    Sets up a Magnolia slide in Blender.

    Optional arguments:

    - `scene`: The scene to add the slide to. Defaults to the current scene.
    - `color`: The background color of the slide. Defaults to white.
    - `framerate`: The framerate of the slide. Defaults to 60.
    """
    if scene is None:
        scene = bpy.context.scene
    coll = create_collection("Production")

    # Set color management settings
    scene.view_settings.view_transform = "Standard"  # pyright: ignore

    set_slide_dimensions(width, height)

    # Create slide
    slide_width, slide_height = scale_size(width, height)
    background_data: MeshData = (
        [
            (0, 0, 0),
            (0, slide_height, 0),
            (slide_width, slide_height, 0),
            (slide_width, 0, 0),
        ],
        [(0, 1), (1, 2), (2, 3), (3, 0)],
        [(0, 1, 2, 3)],
    )
    base = create_object_from_mesh_data(
        background_data, name="Background", collection=coll
    )
    assign_material(
        base,
        color_material(color=color, name="MgSlideBackground", opacity_controls=False),
    )
    # Disable selection of slide
    base.hide_select = True

    # Set up camera
    camera_obj = create_camera("Camera", collection=coll)
    camera_obj.location = (slide_width / 2, slide_height / 2, 20)
    camera_data = cast(bpy.types.Camera, camera_obj.data)
    camera_data.type = "ORTHO"
    # Set scale so that camera covers entire region
    # TODO: Figure out how this needs to scale for different widths, heights
    camera_data.ortho_scale = 38.3

    # Ensure scene world exists
    if scene.world is None:
        world = bpy.data.worlds.new("World")
        scene.world = world
        scene.world.use_nodes = True

    # Set world surface background color to black
    world_bg = scene.world.node_tree.nodes["Background"]  # pyright: ignore
    world_bg.inputs["Color"].default_value = (0, 0, 0, 1)  # pyright: ignore

    # Set framerate
    set_framerate(scene, framerate)
