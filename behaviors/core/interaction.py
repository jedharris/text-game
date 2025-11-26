"""Interaction behaviors - use, pull, push, climb, read.

Vocabulary for general object interactions.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item, find_door_with_adjective


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

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to open (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    adjective = action.get("adjective")

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

    # Get current location for door searches
    location = accessor.get_current_location(actor_id)
    location_id = location.id if location else None

    # For door-related searches, use smart door selection
    item = None
    if object_name.lower() == "door" and location_id:
        # Use find_door_with_adjective for smart selection
        item = find_door_with_adjective(
            accessor, object_name, adjective, location_id,
            actor_id=actor_id, verb="open"
        )

    # Fall back to general item search
    if not item:
        item = find_accessible_item(accessor, object_name, actor_id, adjective)

    if not item:
        # Try door lookup for backward compatibility during migration
        if location_id:
            door = find_door_with_adjective(
                accessor, object_name, adjective, location_id,
                actor_id=actor_id, verb="open"
            )
            if door:
                # Could be unified door Item or old-style Door
                # Assign to item and let the unified handling below take over
                item = door

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Check if it's a door item (unified model) or old-style Door
    if hasattr(item, 'is_door') and item.is_door:
        # Unified door item
        if item.door_open:
            return HandlerResult(
                success=True,
                message=f"The {object_name} is already open."
            )
        if item.door_locked:
            return HandlerResult(
                success=False,
                message=f"The {object_name} is locked."
            )
        # Open the door item
        item.door_open = True
        return HandlerResult(
            success=True,
            message=f"You open the {object_name}."
        )
    elif hasattr(item, 'locations'):
        # Old-style Door entity
        if item.open:
            return HandlerResult(
                success=True,
                message=f"The {object_name} is already open."
            )
        if item.locked:
            return HandlerResult(
                success=False,
                message=f"The {object_name} is locked."
            )
        item.open = True
        return HandlerResult(
            success=True,
            message=f"You open the {object_name}."
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
    if result.message:
        return HandlerResult(
            success=True,
            message=f"{base_message} {result.message}"
        )

    return HandlerResult(
        success=True,
        message=base_message
    )


def handle_close(accessor, action):
    """
    Handle close command.

    Allows an actor to close a container or door item.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to close (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    adjective = action.get("adjective")

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

    # Get current location for door searches
    location = accessor.get_current_location(actor_id)
    location_id = location.id if location else None

    # For door-related searches, use smart door selection
    item = None
    if object_name.lower() == "door" and location_id:
        # Use find_door_with_adjective for smart selection
        item = find_door_with_adjective(
            accessor, object_name, adjective, location_id,
            actor_id=actor_id, verb="close"
        )

    # Fall back to general item search
    if not item:
        item = find_accessible_item(accessor, object_name, actor_id, adjective)

    if not item:
        # Try door lookup for backward compatibility during migration
        if location_id:
            door = find_door_with_adjective(
                accessor, object_name, adjective, location_id,
                actor_id=actor_id, verb="close"
            )
            if door:
                # Could be unified door Item or old-style Door
                # Assign to item and let the unified handling below take over
                item = door

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Check if it's a door item (unified model) or old-style Door
    if hasattr(item, 'is_door') and item.is_door:
        # Unified door item
        if not item.door_open:
            return HandlerResult(
                success=True,
                message=f"The {object_name} is already closed."
            )
        # Close the door item
        item.door_open = False
        return HandlerResult(
            success=True,
            message=f"You close the {object_name}."
        )
    elif hasattr(item, 'locations'):
        # Old-style Door entity
        if not item.open:
            return HandlerResult(
                success=True,
                message=f"The {object_name} is already closed."
            )
        item.open = False
        return HandlerResult(
            success=True,
            message=f"You close the {object_name}."
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


def handle_use(accessor, action):
    """
    Handle use command.

    Allows an actor to use an item in a generic way.
    Entity behaviors (on_use) can provide specific functionality.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item to use (required)

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to use?"
        )

    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    item = find_accessible_item(accessor, object_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Invoke entity behaviors (on_use)
    result = accessor.update(item, {}, verb="use", actor_id=actor_id)

    base_message = f"You use the {item.name}."
    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}")

    return HandlerResult(success=True, message=base_message)


def handle_read(accessor, action):
    """
    Handle read command.

    Allows an actor to read a readable item.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item to read (required)

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to read?"
        )

    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    item = find_accessible_item(accessor, object_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Check if item is readable
    if not item.properties.get("readable", False):
        return HandlerResult(
            success=False,
            message=f"You can't read the {item.name}."
        )

    # Invoke entity behaviors (on_read)
    result = accessor.update(item, {}, verb="read", actor_id=actor_id)

    # Get text content if available
    text = item.properties.get("text", "")
    if text:
        base_message = f"You read the {item.name}: {text}"
    else:
        base_message = f"You read the {item.name}."

    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}")

    return HandlerResult(success=True, message=base_message)


def handle_climb(accessor, action):
    """
    Handle climb command.

    Allows an actor to climb a climbable object.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item to climb (required)

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to climb?"
        )

    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    item = find_accessible_item(accessor, object_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Check if item is climbable
    if not item.properties.get("climbable", False):
        return HandlerResult(
            success=False,
            message=f"You can't climb the {item.name}."
        )

    # Invoke entity behaviors (on_climb)
    result = accessor.update(item, {}, verb="climb", actor_id=actor_id)

    base_message = f"You climb the {item.name}."
    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}")

    return HandlerResult(success=True, message=base_message)


def handle_pull(accessor, action):
    """
    Handle pull command.

    Allows an actor to pull an object (e.g., lever).

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item to pull (required)

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to pull?"
        )

    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    item = find_accessible_item(accessor, object_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Invoke entity behaviors (on_pull)
    result = accessor.update(item, {}, verb="pull", actor_id=actor_id)

    base_message = f"You pull the {item.name}."
    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}")

    return HandlerResult(success=True, message=base_message)


def handle_push(accessor, action):
    """
    Handle push command.

    Allows an actor to push an object (e.g., button).

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item to push (required)

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to push?"
        )

    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    item = find_accessible_item(accessor, object_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Invoke entity behaviors (on_push)
    result = accessor.update(item, {}, verb="push", actor_id=actor_id)

    base_message = f"You push the {item.name}."
    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}")

    return HandlerResult(success=True, message=base_message)
