"""Interaction behaviors - use, pull, push, climb, read.

Vocabulary for general object interactions.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item, find_exit_by_name, describe_location
from utilities.handler_utils import find_action_target, find_openable_target, get_display_name
from utilities.entity_serializer import serialize_for_handler_result
from utilities.location_serializer import serialize_location_for_llm


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
            "word": "climb",
            "event": "on_climb",
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


def handle_climb(accessor, action):
    """
    Handle climb command.

    Allows an actor to climb a climbable object or exit (like stairs).

    Search order:
    1. Look for a climbable Item (property "climbable": true)
    2. Look for an exit by name (e.g., "stairs" matches "spiral staircase")
       - If exit found, move the actor to that destination

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item/exit to climb (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    adjective = action.get("adjective")
    verb = action.get("verb", "climb")

    if not object_name:
        return HandlerResult(
            success=False,
            message=f"What do you want to {verb}?"
        )

    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # First, try to find a climbable item
    item = find_accessible_item(accessor, object_name, actor_id, adjective)
    if item and item.properties.get("climbable", False):
        # Found a climbable item - invoke behaviors and return
        result = accessor.update(item, {}, verb=verb, actor_id=actor_id)
        base_message = f"You {verb} the {item.name}."
        data = serialize_for_handler_result(item)
        if result.message:
            return HandlerResult(success=True, message=f"{base_message} {result.message}", data=data)
        return HandlerResult(success=True, message=base_message, data=data)

    # No climbable item found - try to find an exit by name
    exit_result = find_exit_by_name(accessor, object_name, actor_id, adjective)
    if exit_result:
        direction, exit_descriptor = exit_result
        destination_id = exit_descriptor.to

        # Check for door blocking
        if exit_descriptor.type == 'door' and exit_descriptor.door_id:
            door_item = accessor.get_door_item(exit_descriptor.door_id)
            if door_item:
                if not door_item.door_open:
                    return HandlerResult(
                        success=False,
                        message=f"The {door_item.name} is closed."
                    )
            else:
                door = accessor.get_door(exit_descriptor.door_id)
                if door and not door.open:
                    return HandlerResult(
                        success=False,
                        message=f"The {door.description or 'door'} is closed."
                    )

        destination = accessor.get_location(destination_id)
        if not destination:
            return HandlerResult(
                success=False,
                message=f"INCONSISTENT STATE: Destination {destination_id} not found"
            )

        # Move the actor
        result = accessor.update(actor, {"location": destination_id})
        if not result.success:
            return HandlerResult(
                success=False,
                message=f"INCONSISTENT STATE: Failed to move actor: {result.message}"
            )

        # Build message with climb action and auto-look
        exit_name = exit_descriptor.name if exit_descriptor.name else direction
        message_parts = [f"You climb the {exit_name} to {destination.name}.\n"]
        message_parts.extend(describe_location(accessor, destination, actor_id))
        llm_data = serialize_location_for_llm(accessor, destination, actor_id)

        return HandlerResult(
            success=True,
            message="\n".join(message_parts),
            data=llm_data
        )

    # Neither climbable item nor exit found
    if item:
        # Found an item but it's not climbable
        return HandlerResult(
            success=False,
            message=f"You can't climb the {item.name}."
        )

    return HandlerResult(
        success=False,
        message=f"You don't see any {get_display_name(object_name)} here to climb."
    )


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
