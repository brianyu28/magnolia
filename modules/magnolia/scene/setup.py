from typing import cast, Callable

import bpy


def create_scene(
    name: str = "Scene", setup_function: Callable[[bpy.types.Scene], None] | None = None
) -> bpy.types.Scene:
    # Create a new scene
    scene = bpy.data.scenes.new(name)
    bpy.context.window.scene = scene

    # Call custom setup function, or otherwise just create a camera
    if setup_function is not None:
        setup_function(scene)
    else:
        # Minimally, if no custom setup function, create a camera and set framerate
        camera_data = bpy.data.cameras.new("Camera")
        camera = bpy.data.objects.new("Camera", camera_data)
        scene.camera = camera
        scene.collection.objects.link(camera)

        scene.render.engine = "BLENDER_EEVEE"  # pyright: ignore
        scene.render.fps = 30

    return scene


def add_scene_audio(scene: bpy.types.Scene, filename: str = "", start_frame=1):
    """
    Add audio clip to scene.
    Temporarily moves into the sequence editor to ensure that the context exists.

    Arguments:

    - scene: Scene to add audio to.
    - filename: Absolute path to audio file.

    Optional Arguments:

    - start_frame: Frame of audio to start at.
    """
    # Ensure there is a sequence editor
    if not scene.sequence_editor:
        scene.sequence_editor_create()

    # Add sound to sequence editor
    sound = scene.sequence_editor.sequences.new_sound(
        "Scene Audio", filename, 1, -start_frame
    )
    sound.frame_offset_start = start_frame
    return sound


def setup_composition_scene(
    narration_audio_path: str,
    create_new_scene: bool = False,
    setup_function: Callable[[bpy.types.Scene], None] | None = None,
    framerate: int = 30,
) -> bpy.types.Scene:
    """
    Sets up a new composition scene with narration audio.

    `create_new_scene` controls whether a new scene is created or if we just use the
    existing scene.

    If we use the existing scene, default objects are removed from the scene.
    """
    if create_new_scene:
        scene = create_scene("Composition", setup_function=setup_function)
    else:
        scene = bpy.context.scene
        scene.name = "Composition"

        # Remove default objects from scene
        for obj in scene.objects:
            if obj.name in ["Cube", "Light", "Camera"]:
                bpy.data.objects.remove(obj)
        for coll in scene.collection.children:
            if coll.name == "Collection":
                bpy.data.collections.remove(coll)

        if setup_function is not None:
            setup_function(scene)

    # If there is a setup function, then let it handle the FPS setting.
    if setup_function is None:
        scene.render.fps = 30

    # Add narration audio
    add_scene_audio(scene, narration_audio_path)
    return scene


def get_max_scene_index(
    scenes: list[bpy.types.Scene],
) -> tuple[int, bpy.types.Scene | None]:
    """
    Get the maximum scene index from a list of scenes.
    Assumes scene names are formatted as `xxx. Scene Name`.
    """
    max_index = 0
    max_scene = None
    for scene in scenes:
        if "." in scene.name:
            try:
                index = int(scene.name.split(".")[0])
                max_index = max(max_index, index)
                max_scene = scene
            except ValueError:
                pass
    return max_index, max_scene


def get_next_unused_frame(channel: int = 2) -> int:
    """
    Gets the next unused frame in the current sequence editor.
    """
    video_seqs = [
        seq
        for seq in bpy.context.scene.sequence_editor.sequences_all
        if seq.channel == channel
    ]
    return max([1] + [seq.frame_final_end for seq in video_seqs])


def add_scene_continuation(
    name: str = "Scene", setup_function: Callable[[bpy.types.Scene], None] | None = None
) -> bpy.types.Scene:
    """
    In a multi-scene video, a "scene continuiation" is a new scene that continues
    with the audio from the original scene.

    We make a few assumptions here:
    - There is a single audio clip on channel 1 named "Scene Audio".
    - All video clips are on channel 2.
    - Video scenes are numbered as `xxx. Scene Name`.
    """

    # Find the audio clip on channel 1 and get its path.
    sound_seq = bpy.context.scene.sequence_editor.sequences_all["Scene Audio"]
    sound_path = sound_seq.sound.filepath  # pyright: ignore

    # Find all clips on channel 2, which are the video channels
    next_frame = get_next_unused_frame(channel=2)

    # Determine the maximum sequence used so far
    video_seqs = [
        seq
        for seq in bpy.context.scene.sequence_editor.sequences_all
        if seq.channel == 2
    ]
    max_scene_index, _ = get_max_scene_index(
        [seq.scene for seq in video_seqs]
    )  # pyright: ignore

    # Create a new scene
    scene_name = f"{max_scene_index + 1}. {name}"
    scene = create_scene(scene_name, setup_function=setup_function)
    add_scene_audio(scene, sound_path, start_frame=next_frame)
    return scene


def add_latest_scene_to_video() -> bpy.types.Scene:
    """
    Takes the scene with the highest numbered name (e.g. `xxx. Scene Name`)
    and adds it to the end of the current video sequence.

    Assumes the currently selected scene is the composition to add to.
    """
    composition_scene = bpy.context.scene

    # Get scene with the highest index value
    _, max_scene = get_max_scene_index(list(bpy.data.scenes))
    max_scene = cast(bpy.types.Scene, max_scene)

    # Get the current video sequence
    video_seq = bpy.context.scene.sequence_editor.sequences_all

    # Add the new scene to the end of the video sequence
    next_frame = get_next_unused_frame(channel=2)
    composition_scene.sequence_editor.sequences.new_scene(
        max_scene.name, max_scene, 2, next_frame
    )
    return max_scene
