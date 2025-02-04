from typing import Literal

from .object import ObjectArg, ObjectsArg, resolve_object, resolve_objects
from ..scene.context import selections

Axis = Literal["x", "y", "z"]
AlignmentMode = Literal["min", "center", "max"]


def align(
    objects: ObjectsArg | None = None,
    axis: Axis = "x",
    mode: AlignmentMode = "center",
):
    """
    Align objects.
    """
    validate_axis(axis)
    if objects is None:
        targets = selections()
    else:
        targets = resolve_objects(objects)

    # Don't do anything if there's no targets
    if not targets:
        return

    # Get all attribute values based on object location
    values = [getattr(obj.location, axis) for obj in targets]

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
        setattr(obj.location, axis, value)


def alignX(objects: ObjectsArg | None = None, mode: AlignmentMode = "center"):
    align(objects=objects, axis="x", mode=mode)


def alignY(objects: ObjectsArg | None = None, mode: AlignmentMode = "center"):
    align(objects=objects, axis="y", mode=mode)


def alignZ(objects: ObjectsArg | None = None, mode: AlignmentMode = "center"):
    align(objects=objects, axis="z", mode=mode)


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
    target_location = getattr(target.location, axis)

    # Get the group's average location
    group_location = sum(getattr(obj.location, axis) for obj in group) / len(group)

    # Calculate the difference between the target and group
    difference = target_location - group_location

    # Move the group to align with the target
    for obj in group:
        setattr(obj.location, axis, getattr(obj.location, axis) + difference)


def distribute(
    objects: ObjectsArg | None = None,
    axis: Axis = "x",
):
    """
    Distribute objects evenly.
    """
    validate_axis(axis)
    if objects is None:
        targets = selections()
    else:
        targets = resolve_objects(objects)

    # Don't do anything if there's no targets
    if not targets:
        return

    # Order targets by location attribute
    targets = sorted(targets, key=lambda obj: getattr(obj.location, axis))

    # Determine values for distributing each object
    min_value = getattr(targets[0].location, axis)
    interval = (getattr(targets[-1].location, axis) - min_value) / (len(targets) - 1)

    # Distribute objects
    for i, obj in enumerate(targets):
        setattr(obj.location, axis, min_value + interval * i)


def distributeX(objects: ObjectsArg | None = None):
    distribute(objects=objects, axis="x")


def distributeY(objects: ObjectsArg | None = None):
    distribute(objects=objects, axis="y")


def distributeZ(objects: ObjectsArg | None = None):
    distribute(objects=objects, axis="z")


def validate_axis(axis: Axis):
    if axis not in {"x", "y", "z"}:
        raise ValueError(f"Invalid axis: {axis}")
