"""Interaction behaviors - use, pull, push, climb, read.

Vocabulary for general object interactions.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item
from utilities.handler_utils import find_action_target, find_openable_target
from utilities.entity_serializer import serialize_for_handler_result


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
    "adjectives": [],
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

    # Check if it's a door item
    if hasattr(item, 'is_door') and item.is_door:
        data = serialize_for_handler_result(item)
        if item.door_open:
            return HandlerResult(
                success=True,
                message=f"The {item.name} is already open.",
                data=data
            )
        if item.door_locked:
            return HandlerResult(
                success=False,
                message=f"The {item.name} is locked."
            )
        item.door_open = True
        return HandlerResult(
            success=True,
            message=f"You open the {item.name}.",
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
        return HandlerResult(
            success=True,
            message=f"The {item.name} is already open.",
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
    base_message = f"You open the {item.name}."
    data = serialize_for_handler_result(item)
    if result.message:
        return HandlerResult(
            success=True,
            message=f"{base_message} {result.message}",
            data=data
        )

    return HandlerResult(
        success=True,
        message=base_message,
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

    # Check if it's a door item
    if hasattr(item, 'is_door') and item.is_door:
        data = serialize_for_handler_result(item)
        if not item.door_open:
            return HandlerResult(
                success=True,
                message=f"The {item.name} is already closed.",
                data=data
            )
        item.door_open = False
        return HandlerResult(
            success=True,
            message=f"You close the {item.name}.",
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
        return HandlerResult(
            success=True,
            message=f"The {item.name} is already closed.",
            data=data
        )

    # Close the container
    item.container.open = False

    return HandlerResult(
        success=True,
        message=f"You close the {item.name}.",
        data=data
    )


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
    item, error = find_action_target(accessor, action)
    if error:
        return error

    verb = action.get("verb", "use")
    actor_id = action.get("actor_id", "player")

    # Invoke entity behaviors (on_use)
    result = accessor.update(item, {}, verb=verb, actor_id=actor_id)

    base_message = f"You {verb} the {item.name}."
    data = serialize_for_handler_result(item)
    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}", data=data)

    return HandlerResult(success=True, message=base_message, data=data)


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
    item, error = find_action_target(accessor, action)
    if error:
        return error

    # Property validation specific to this verb
    if not item.properties.get("readable", False):
        return HandlerResult(
            success=False,
            message=f"You can't read the {item.name}."
        )

    verb = action.get("verb", "read")
    actor_id = action.get("actor_id", "player")

    # Invoke entity behaviors (on_read)
    result = accessor.update(item, {}, verb=verb, actor_id=actor_id)

    # Get text content if available
    text = item.properties.get("text", "")
    if text:
        base_message = f"You {verb} the {item.name}: {text}"
    else:
        base_message = f"You {verb} the {item.name}."

    data = serialize_for_handler_result(item)
    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}", data=data)

    return HandlerResult(success=True, message=base_message, data=data)


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
    item, error = find_action_target(accessor, action)
    if error:
        return error

    verb = action.get("verb", "pull")
    actor_id = action.get("actor_id", "player")

    # Invoke entity behaviors (on_pull)
    result = accessor.update(item, {}, verb=verb, actor_id=actor_id)

    base_message = f"You {verb} the {item.name}."
    data = serialize_for_handler_result(item)
    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}", data=data)

    return HandlerResult(success=True, message=base_message, data=data)


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
    item, error = find_action_target(accessor, action)
    if error:
        return error

    verb = action.get("verb", "push")
    actor_id = action.get("actor_id", "player")

    # Invoke entity behaviors (on_push)
    result = accessor.update(item, {}, verb=verb, actor_id=actor_id)

    base_message = f"You {verb} the {item.name}."
    data = serialize_for_handler_result(item)
    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}", data=data)

    return HandlerResult(success=True, message=base_message, data=data)
