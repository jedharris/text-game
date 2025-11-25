"""Interaction behaviors - use, pull, push, climb, read.

Vocabulary for general object interactions.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item


# Vocabulary extension - adds interaction verbs
vocabulary = {
    "verbs": [
        {
            "word": "open",
            "event": "on_open",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["physical action", "changes state", "requires openable object"],
                "failure_narration": {
                    "not_found": "cannot find the object",
                    "already_open": "already open",
                    "locked": "locked"
                }
            }
        },
        {
            "word": "close",
            "event": "on_close",
            "synonyms": ["shut"],
            "object_required": True,
            "llm_context": {
                "traits": ["physical action", "changes state", "requires closeable object"],
                "failure_narration": {
                    "not_found": "cannot find the object",
                    "already_closed": "already closed"
                }
            }
        },
        {
            "word": "use",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["activates object function", "context-dependent"],
                "failure_narration": {
                    "no_effect": "nothing happens",
                    "cannot_use": "cannot use that"
                }
            }
        },
        {
            "word": "read",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["reveals written content", "requires readable object"],
                "failure_narration": {
                    "not_readable": "nothing to read",
                    "too_dark": "too dark to read"
                }
            }
        },
        {
            "word": "climb",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["vertical movement", "requires climbable surface"],
                "failure_narration": {
                    "cannot_climb": "cannot climb that",
                    "too_slippery": "too slippery to climb"
                }
            }
        },
        {
            "word": "pull",
            "synonyms": ["yank"],
            "object_required": True,
            "llm_context": {
                "traits": ["applies force toward self", "may trigger mechanisms"],
                "failure_narration": {
                    "stuck": "won't budge",
                    "nothing_happens": "nothing happens"
                }
            }
        },
        {
            "word": "push",
            "synonyms": ["press"],
            "object_required": True,
            "llm_context": {
                "traits": ["applies force away from self", "may trigger mechanisms"],
                "failure_narration": {
                    "stuck": "won't move",
                    "nothing_happens": "nothing happens"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}


def handle_open(accessor, action):
    """
    Handle open command.

    Allows an actor to open a container or door.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to open (required)

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to open?"
        )

    # Get the actor
    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Try to find as door first
    door = None
    for d in accessor.game_state.doors:
        if object_name.lower() in d.id.lower() or object_name.lower() in d.description.lower():
            door = d
            break

    if door:
        # Check if already open
        if door.open:
            return HandlerResult(
                success=True,
                message=f"The {object_name} is already open."
            )

        # Check if locked
        if door.locked:
            return HandlerResult(
                success=False,
                message=f"The {object_name} is locked."
            )

        # Open the door
        result = accessor.update(door, {"open": True})
        if not result.success:
            return HandlerResult(
                success=False,
                message=f"INCONSISTENT STATE: Failed to open door: {result.message}"
            )

        return HandlerResult(
            success=True,
            message=f"You open the {object_name}."
        )

    # Try to find as item (container)
    item = find_accessible_item(accessor, object_name, actor_id)

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Check if it's a container
    if not item.container:
        return HandlerResult(
            success=False,
            message=f"You can't open the {item.name}."
        )

    # Check if already open
    if item.container.open:
        return HandlerResult(
            success=True,
            message=f"The {item.name} is already open."
        )

    # Open the container
    item.container.open = True

    return HandlerResult(
        success=True,
        message=f"You open the {item.name}."
    )


def handle_close(accessor, action):
    """
    Handle close command.

    Allows an actor to close a container or door.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to close (required)

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to close?"
        )

    # Get the actor
    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Try to find as door first
    door = None
    for d in accessor.game_state.doors:
        if object_name.lower() in d.id.lower() or object_name.lower() in d.description.lower():
            door = d
            break

    if door:
        # Check if already closed
        if not door.open:
            return HandlerResult(
                success=True,
                message=f"The {object_name} is already closed."
            )

        # Close the door
        result = accessor.update(door, {"open": False})
        if not result.success:
            return HandlerResult(
                success=False,
                message=f"INCONSISTENT STATE: Failed to close door: {result.message}"
            )

        return HandlerResult(
            success=True,
            message=f"You close the {object_name}."
        )

    # Try to find as item (container)
    item = find_accessible_item(accessor, object_name, actor_id)

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Check if it's a container
    if not item.container:
        return HandlerResult(
            success=False,
            message=f"You can't close the {item.name}."
        )

    # Check if already closed
    if not item.container.open:
        return HandlerResult(
            success=True,
            message=f"The {item.name} is already closed."
        )

    # Close the container
    item.container.open = False

    return HandlerResult(
        success=True,
        message=f"You close the {item.name}."
    )
