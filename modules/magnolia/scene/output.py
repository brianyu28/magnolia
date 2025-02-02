import bpy


def set_framerate(scene: bpy.types.Scene | None = None, rate: int = 30):
    """
    Sets the framerate of the current scene.

    Optional arguments:

    - `scene`: The scene to set the framerate for. Defaults to the current scene.
    - `rate`: The framerate to set. Defaults to 30.
    """
    if scene is None:
        scene = bpy.context.scene
    scene.render.fps = rate
    scene.render.fps_base = 1
