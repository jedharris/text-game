"""Weighted Idol Chamber puzzle behavior.

Demonstrates:
- Using puzzle_lib.threshold_checker for weight validation
- Using puzzle_lib.threshold_checker helper functions for item weight
- Automatic door unlocking based on threshold
- Custom verb for examining the pressure mechanism
"""

from typing import Dict, Any, cast
from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from src.types import ActorId
from utilities.utils import find_accessible_item

# Import library functions
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from behavior_libraries.puzzle_lib.threshold_checker import (
    check_threshold, get_threshold_feedback, calculate_item_weight, get_items_in_location
)


# Vocabulary extension - adds "check" verb for examining pressure plates
vocabulary = {
    "verbs": [
        {
            "word": "check",
            "event": "on_check",
            "synonyms": [],
            "object_required": True
        }
    ],
    "nouns": [],
    "adjectives": []
}


def handle_check(accessor, action: Dict) -> HandlerResult:
    """
    Handle the check command for examining pressure mechanism.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, actor_id

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = cast(ActorId, action.get("actor_id") or ActorId("player"))
    obj_name = action.get("object")
    adjective = action.get("adjective")

    if not obj_name:
        return HandlerResult(success=False, message="Check what?")

    # Find the target
    target = find_accessible_item(accessor, obj_name, actor_id, adjective)

    if not target:
        return HandlerResult(success=False, message=f"You don't see any {obj_name} here.")

    # Invoke entity behavior
    result = accessor.update(target, {}, verb="check", actor_id=actor_id)

    if not result.success:
        # Fall back to regular examine
        return HandlerResult(success=False, message=result.message)

    return HandlerResult(success=True, message=result.message)


def on_check(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Entity behavior for checking the pedestal/pressure plates.

    Provides feedback on current weight vs target weight.

    Args:
        entity: The pedestal
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb

    Returns:
        EventResult with allow and message
    """
    # Get target weight from entity states
    target_weight = entity.states.get("target_weight", 3.5)
    tolerance = entity.states.get("tolerance", 0.2)

    # Calculate current weight on pedestal
    items_on_pedestal = get_items_in_location(accessor, entity.id)
    current_weight = calculate_item_weight(accessor, items_on_pedestal)

    # Get feedback
    feedback = get_threshold_feedback(
        current_weight,
        target_weight,
        tolerance,
        labels={
            "too_low": "The plates are barely depressed. You need more weight.",
            "too_high": "The plates are depressed too far. You need less weight.",
            "close": "The plates are almost in balance. You're very close!",
            "exact": "The plates are perfectly balanced!"
        }
    )

    message = (
        f"You examine the pressure plates around the pedestal.\n"
        f"Current weight: {current_weight:.1f} kg\n"
        f"Target weight: {target_weight:.1f} kg (±{tolerance} kg)\n\n"
        f"{feedback}"
    )

    return EventResult(allow=True, message=message)


def on_after_item_moved(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Entity behavior triggered after items are moved to/from pedestal.

    Checks if the weight threshold is met and unlocks the door if so.

    Args:
        entity: The pedestal
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb, item_id

    Returns:
        EventResult with allow and message
    """
    # Get target weight from entity states
    target_weight = entity.states.get("target_weight", 3.5)
    tolerance = entity.states.get("tolerance", 0.2)

    # Calculate current weight on pedestal
    items_on_pedestal = get_items_in_location(accessor, entity.id)
    current_weight = calculate_item_weight(accessor, items_on_pedestal)

    # Check if threshold is met
    if check_threshold(current_weight, target_weight, tolerance, mode="exact"):
        # Success! Unlock the door
        door = accessor.get_item("door_treasure")
        if door and hasattr(door, 'door'):
            was_locked = door.door.get("locked", False)
            door.door["locked"] = False
            door.door["open"] = True

            if was_locked:
                message = (
                    f"\nThe pressure plates click into place!\n"
                    f"You hear a grinding sound as the sealed door swings open!"
                )
            else:
                message = "\nThe pressure plates are perfectly balanced."

            return EventResult(allow=True, message=message)

    return EventResult(allow=True, message=None)


# Hook into the core "put" and "take" handlers to trigger weight check
# This is called after items are moved
def on_put(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """Entity behavior after item put on pedestal."""
    return on_after_item_moved(entity, accessor, context)


def on_take(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """Entity behavior after item taken from pedestal."""
    return on_after_item_moved(entity, accessor, context)
