"""Interaction behaviors - use, pull, push, climb, read.

Vocabulary for general object interactions.
"""

from typing import Dict, Any, Optional, cast, Union

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from src.state_manager import Item, Actor
from src.types import ActorId
from utilities.utils import find_accessible_item
from utilities.handler_utils import (
    find_action_target,
    find_openable_target,
    _handle_door_or_container_state_change
)
from utilities.entity_serializer import serialize_for_handler_result
from utilities.positioning import try_implicit_positioning


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
            "narration_mode": "brief",
            "llm_context": {
                "traits": ["physical action", "changes state", "requires closeable object"],
                "failure_narration": {
                    "not_found": "cannot find the object",
                    "already_closed": "already closed"
                }
            }
        },
        {
            "word": "read",
            "event": "on_read",
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
            "word": "pull",
            "event": "on_pull",
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
            "event": "on_push",
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
    "adjectives": [
        # "open" as adjective (e.g., "open door")
        {"word": "open", "synonyms": []}
    ]
}


def handle_open(accessor, action):
    """
    Handle open command.

    Allows an actor to open a container or door item.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to open (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    item, actor_id, error = find_openable_target(accessor, action, "open")
    if error:
        return error

    # Check if it's a valid openable item
    is_door = hasattr(item, 'is_door') and item.is_door
    is_container = item.container is not None

    if not is_door and not is_container:
        return HandlerResult(
            success=False,
            primary=f"You can't open the {item.name}."
        )

    # Apply implicit positioning
    moved, move_msg = try_implicit_positioning(accessor, actor_id, item)

    # Use unified state change logic
    return _handle_door_or_container_state_change(
        accessor, item, actor_id,
        target_state=True,
        verb="open",
        move_msg=move_msg
    )


def handle_close(accessor, action):
    """
    Handle close command.

    Allows an actor to close a container or door item.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to close (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    item, actor_id, error = find_openable_target(accessor, action, "close")
    if error:
        return error

    # Check if it's a valid closeable item
    is_door = hasattr(item, 'is_door') and item.is_door
    is_container = item.container is not None

    if not is_door and not is_container:
        return HandlerResult(
            success=False,
            primary=f"You can't close the {item.name}."
        )

    # Apply implicit positioning
    moved, move_msg = try_implicit_positioning(accessor, actor_id, item)

    # Use unified state change logic
    return _handle_door_or_container_state_change(
        accessor, item, actor_id,
        target_state=False,
        verb="close",
        move_msg=move_msg
    )


def _handle_generic_interaction(accessor, action, required_property: Optional[str] = None, base_message_builder=None) -> HandlerResult:
    """
    Generic interaction handler for use, pull, push, read, and similar verbs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with actor_id, object, adjective, verb
        required_property: Optional property to validate (e.g., "readable")
        base_message_builder: Optional function(item, verb) to build custom message

    Returns:
        HandlerResult with success flag and message
    """
    item, error = find_action_target(accessor, action)
    if error:
        return error

    # Type narrowing: if no error, item must be set
    assert item is not None

    verb = action.get("verb")
    if not verb:
        return HandlerResult(
            success=False,
            primary="INCONSISTENT STATE: verb not provided in action"
        )

    # Convert WordEntry to string if necessary
    from src.word_entry import WordEntry
    verb_str = verb.word if isinstance(verb, WordEntry) else str(verb)

    actor_id = cast(ActorId, action.get("actor_id") or ActorId("player"))

    # Property validation if required
    if required_property and not item.properties.get(required_property, False):
        return HandlerResult(
            success=False,
            primary=f"You can't {verb_str} the {item.name}."
        )

    # Special handling for "use" verb on equippable items
    # If item is equippable and not equipped, equip it instead of triggering on_use
    if verb_str == "use" and item.properties.get("equippable", False):
        is_equipped = item.states.get("equipped", False)
        if not is_equipped:
            # Equip the item
            result = accessor.update(item, {"states.equipped": True})
            data = serialize_for_handler_result(item, accessor, actor_id)
            return HandlerResult(
                success=True,
                primary=f"You equip the {item.name}.",
                data=data
            )
        # If already equipped, fall through to normal use behavior

    # Invoke entity behaviors
    result = accessor.update(item, {}, verb=verb_str, actor_id=actor_id)

    # Build base message
    if base_message_builder:
        base_message = base_message_builder(item, verb_str)
    else:
        base_message = f"You {verb_str} the {item.name}."

    data = serialize_for_handler_result(item, accessor, actor_id)
    if result.detail:
        return HandlerResult(success=True, primary=f"{base_message} {result.detail}", data=data)

    return HandlerResult(success=True, primary=base_message, data=data)


def handle_read(accessor, action):
    """
    Handle read command.

    Allows an actor to read a readable item.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item to read (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    def build_read_message(item, verb):
        """Custom message builder that includes text content."""
        text = item.properties.get("text", "")
        if text:
            return f"You {verb} the {item.name}: {text}"
        else:
            return f"You {verb} the {item.name}."

    return _handle_generic_interaction(accessor, action, required_property="readable", base_message_builder=build_read_message)


def handle_pull(accessor, action):
    """
    Handle pull command.

    Allows an actor to pull an object (e.g., lever).

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item to pull (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    return _handle_generic_interaction(accessor, action)


def handle_push(accessor, action):
    """
    Handle push command.

    Allows an actor to push an object (e.g., button).

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item to push (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    return _handle_generic_interaction(accessor, action)
