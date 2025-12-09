"""Interaction behaviors - use, pull, push, climb, read.

Vocabulary for general object interactions.
"""

from typing import Dict, Any, Optional

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item
from utilities.handler_utils import find_action_target, find_openable_target
from utilities.entity_serializer import serialize_for_handler_result
from utilities.positioning import try_implicit_positioning, build_message_with_positioning


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
            "word": "use",
            "event": "on_use",
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
    ],
    "directions": []
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

    # Apply implicit positioning
    moved, move_msg = try_implicit_positioning(accessor, actor_id, item)

    # Check if it's a door item
    if hasattr(item, 'is_door') and item.is_door:
        data = serialize_for_handler_result(item)
        if item.door_open:
            message = build_message_with_positioning(
                [f"The {item.name} is already open."],
                move_msg
            )
            return HandlerResult(
                success=True,
                message=message,
                data=data
            )
        if item.door_locked:
            return HandlerResult(
                success=False,
                message=f"The {item.name} is locked."
            )
        item.door_open = True
        message = build_message_with_positioning(
            [f"You open the {item.name}."],
            move_msg
        )
        return HandlerResult(
            success=True,
            message=message,
            data=data
        )

    # Check if it's a container
    if not item.container:
        return HandlerResult(
            success=False,
            message=f"You can't open the {item.name}."
        )

    # Check if already open
    if item.container.open:
        data = serialize_for_handler_result(item)
        message = build_message_with_positioning(
            [f"The {item.name} is already open."],
            move_msg
        )
        return HandlerResult(
            success=True,
            message=message,
            data=data
        )

    # Open the container using accessor.update() to invoke behaviors
    result = accessor.update(
        item,
        {"container.open": True},
        verb="open",
        actor_id=actor_id
    )

    if not result.success:
        return HandlerResult(
            success=False,
            message=result.message or f"You can't open the {item.name}."
        )

    # Build message - include behavior message if present
    base_messages = [f"You open the {item.name}."]
    if result.message:
        base_messages.append(result.message)

    message = build_message_with_positioning(base_messages, move_msg)
    data = serialize_for_handler_result(item)

    return HandlerResult(
        success=True,
        message=message,
        data=data
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

    # Apply implicit positioning
    moved, move_msg = try_implicit_positioning(accessor, actor_id, item)

    # Check if it's a door item
    if hasattr(item, 'is_door') and item.is_door:
        data = serialize_for_handler_result(item)
        if not item.door_open:
            message = build_message_with_positioning(
                [f"The {item.name} is already closed."],
                move_msg
            )
            return HandlerResult(
                success=True,
                message=message,
                data=data
            )
        item.door_open = False
        message = build_message_with_positioning(
            [f"You close the {item.name}."],
            move_msg
        )
        return HandlerResult(
            success=True,
            message=message,
            data=data
        )

    # Check if it's a container
    if not item.container:
        return HandlerResult(
            success=False,
            message=f"You can't close the {item.name}."
        )

    # Check if already closed
    data = serialize_for_handler_result(item)
    if not item.container.open:
        message = build_message_with_positioning(
            [f"The {item.name} is already closed."],
            move_msg
        )
        return HandlerResult(
            success=True,
            message=message,
            data=data
        )

    # Close the container
    item.container.open = False

    message = build_message_with_positioning(
        [f"You close the {item.name}."],
        move_msg
    )
    return HandlerResult(
        success=True,
        message=message,
        data=data
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
            message="INCONSISTENT STATE: verb not provided in action"
        )

    actor_id = action.get("actor_id", "player")

    # Property validation if required
    if required_property and not item.properties.get(required_property, False):
        return HandlerResult(
            success=False,
            message=f"You can't {verb} the {item.name}."
        )

    # Invoke entity behaviors
    result = accessor.update(item, {}, verb=verb, actor_id=actor_id)

    # Build base message
    if base_message_builder:
        base_message = base_message_builder(item, verb)
    else:
        base_message = f"You {verb} the {item.name}."

    data = serialize_for_handler_result(item)
    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}", data=data)

    return HandlerResult(success=True, message=base_message, data=data)


def handle_use(accessor, action):
    """
    Handle use command.

    Allows an actor to use an item in a generic way.
    Entity behaviors (on_use) can provide specific functionality.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item to use (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    return _handle_generic_interaction(accessor, action)


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
