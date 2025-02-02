import bpy


def time_to_frames(time: float, fps: int | None = None) -> int:
    """
    Converts a time in seconds to frames per second.
    """
    if fps is None:
        fps = bpy.context.scene.render.fps
    return int(time * fps)
