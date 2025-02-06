import math
from mathutils import Vector
from typing import Literal

from .object import ObjectArg, ObjectsArg, resolve_object, resolve_objects
from ..scene.context import selections

Axis = Literal["x", "y", "z"]
AlignmentMode = Literal["min", "center", "max"]


def align(
    objects: ObjectsArg | None = None,
    axis: Axis = "x",
    mode: AlignmentMode = "center",
    use_locations: bool = False,
):
    """
    Align objects.

    Optional arguments:

    - `objects`: The objects to align. Defaults to selected objects.
    - `axis`: The axis to align objects along. Defaults to "x".
    - `mode`: The alignment mode. Can be "min", "center", or "max". Defaults to "center".
    - `use_locations`: Whether to align based on object location attributes.
        Defaults to False, which aligns based on the object's bounding box.
    """
    validate_axis(axis)
    if objects is None:
        targets = selections()
    else:
        targets = resolve_objects(objects)

    # Don't do anything if there's no targets
    if not targets:
        return

    if use_locations:
        # Get all attribute values based on object location
        values = [getattr(obj.matrix_world.translation, axis) for obj in targets]

        # Determine which attribute value to align all objects to
        match mode:
            case "min":
                value = min(values)
            case "center":
                value = sum(values) / len(values)
            case "max":
                value = max(values)

        # Set all objects to the determined value
        for obj in targets:
            setattr(obj.matrix_world.translation, axis, value)

    # Align based on object bounding boxes
    else:
        axis_index = 0 if axis == "x" else 1 if axis == "y" else 2

        # Get the bounding box for each object
        boxes = [bounding_box(obj) for obj in targets]

        # Depending on our alignment mode, we'll get the min, center, or max value
        # for each object's bounding box along the specified axis
        match mode:
            case "min":
                values = [box[0][axis_index] for box in boxes]
                value = min(values)

            case "center":
                values = [
                    (box[0][axis_index] + box[1][axis_index]) / 2 for box in boxes
                ]
                value = sum(values) / len(values)

            case "max":
                values = [box[1][axis_index] for box in boxes]
                value = max(values)

        # Move all objects to the determined value
        for obj in targets:
            box = bounding_box(obj)
            current_value = (
                box[0][axis_index]
                if mode == "min"
                else (
                    (box[0][axis_index] + box[1][axis_index]) / 2
                    if mode == "center"
                    else box[1][axis_index]
                )
            )
            difference = value - current_value
            setattr(obj.location, axis, obj.location[axis_index] + difference)


def alignX(
    objects: ObjectsArg | None = None,
    mode: AlignmentMode = "center",
    use_locations: bool = False,
):
    align(objects=objects, axis="x", mode=mode, use_locations=use_locations)


def alignY(
    objects: ObjectsArg | None = None,
    mode: AlignmentMode = "center",
    use_locations: bool = False,
):
    align(objects=objects, axis="y", mode=mode, use_locations=use_locations)


def alignZ(
    objects: ObjectsArg | None = None,
    mode: AlignmentMode = "center",
    use_locations: bool = False,
):
    align(objects=objects, axis="z", mode=mode, use_locations=use_locations)


def alignTo(target: ObjectArg, objects: ObjectsArg, axis: Axis = "x"):
    """
    Align objects together to target object.
    Moves a group of objects together, so that their combined center lines
    up with the object's center.
    """
    validate_axis(axis)
    target = resolve_object(target)
    group = resolve_objects(objects)
    if not group:
        return

    # Get the target object's location
    target_location = getattr(target.matrix_world.translation, axis)

    # Get the group's average location
    group_location = sum(
        getattr(obj.matrix_world.translation, axis) for obj in group
    ) / len(group)

    # Calculate the difference between the target and group
    difference = target_location - group_location

    # Move the group to align with the target
    for obj in group:
        setattr(
            obj.matrix_world.translation,
            axis,
            getattr(obj.matrix_world.translation, axis) + difference,
        )


def distribute(
    objects: ObjectsArg | None = None,
    axis: Axis = "x",
    use_locations: bool = False,
):
    """
    Distribute objects evenly.

    Optional arguments:

    - `objects`: The objects to distribute. Defaults to selected objects.
    - `axis`: The axis to distribute objects along. Defaults to "x".
    - `use_locations`: Whether to distribute based on object location attributes.
      Defaults to False, which distributes based on the space between objects.
    """
    validate_axis(axis)
    if objects is None:
        targets = selections()
    else:
        targets = resolve_objects(objects)

    # Don't do anything if there's not enough targets to distribute
    if len(targets) < 2:
        return

    if use_locations:
        # Order targets by location attribute
        targets = sorted(
            targets, key=lambda obj: getattr(obj.matrix_world.translation, axis)
        )

        # Determine values for distributing each object
        min_value = getattr(targets[0].matrix_world.translation, axis)
        interval = (getattr(targets[-1].matrix_world.translation, axis) - min_value) / (
            len(targets) - 1
        )

        # Distribute objects
        for i, obj in enumerate(targets):
            setattr(obj.matrix_world.translation, axis, min_value + interval * i)

    # Use distances between objects
    else:

        axis_index = 0 if axis == "x" else 1 if axis == "y" else 2

        data = []

        # How much space along this axis is occupied by objects (and not empty space)?
        size_used = 0

        # Get leading and trailing for all objects
        for target in targets:
            box = bounding_box(target)
            minimum = box[0][axis_index]
            maximum = box[1][axis_index]
            data.append(
                {
                    "object": target,
                    "min": minimum,
                    "max": maximum,
                }
            )
            size_used += maximum - minimum

        # Sort objects by leading edge
        data = sorted(data, key=lambda x: x["min"])

        min_value = min([x["min"] for x in data])
        max_value = max([x["max"] for x in data])
        total_size = max_value - min_value

        # Calculate how much space is left over
        # This space will be evenly distributed
        total_space = total_size - size_used
        space_per_object = total_space / (len(data) - 1)

        # Distribute objects
        prev_max = bounding_box(data[0]["object"])[1][axis_index]

        for i in range(1, len(data)):
            current_object = data[i]["object"]
            current_bounding = bounding_box(current_object)

            current_min = current_bounding[0][axis_index]
            current_max = current_bounding[1][axis_index]

            # Calculate the space between the two objects
            space = current_min - prev_max

            # Determine how much we should add or remove from the spacing
            difference = space_per_object - space

            # Move the current object
            current_object.location[axis_index] += difference
            prev_max = current_max + difference


def distributeX(objects: ObjectsArg | None = None, use_locations: bool = False):
    distribute(objects=objects, axis="x", use_locations=use_locations)


def distributeY(objects: ObjectsArg | None = None, use_locations: bool = False):
    distribute(objects=objects, axis="y", use_locations=use_locations)


def distributeZ(objects: ObjectsArg | None = None, use_locations: bool = False):
    distribute(objects=objects, axis="z", use_locations=use_locations)


def validate_axis(axis: Axis):
    if axis not in {"x", "y", "z"}:
        raise ValueError(f"Invalid axis: {axis}")


def bounding_box(
    objects: ObjectsArg | None = None,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """
    Returns the bounding box of the selected object or objects
    in global coordinates.

    Optional arguments:

    - `objects`: The objects to get the bounding box of, defaults to current
       selection.
    """
    if objects is None:
        targets = selections()
    else:
        targets = resolve_objects(objects)

    if not targets:
        return (0, 0, 0), (0, 0, 0)

    min_x = float(math.inf)
    min_y = float(math.inf)
    min_z = float(math.inf)
    max_x = float(-math.inf)
    max_y = float(-math.inf)
    max_z = float(-math.inf)

    for target in targets:
        verts = [target.matrix_world @ Vector(vert) for vert in target.bound_box]
        for vert in verts:
            min_x = min(min_x, vert.x)
            min_y = min(min_y, vert.y)
            min_z = min(min_z, vert.z)
            max_x = max(max_x, vert.x)
            max_y = max(max_y, vert.y)
            max_z = max(max_z, vert.z)

    return (min_x, min_y, min_z), (max_x, max_y, max_z)
