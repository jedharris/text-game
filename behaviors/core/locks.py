"""Lock behaviors - unlock and lock.

Vocabulary for lock-related actions.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item, find_door_with_adjective


# Vocabulary extension - adds unlock and lock verbs
vocabulary = {
    "verbs": [
        {
            "word": "unlock",
            "event": "on_unlock",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["requires correct key", "changes locked state"],
                "failure_narration": {
                    "no_key": "need the right key",
                    "wrong_key": "key doesn't fit",
                    "not_locked": "not locked"
                }
            }
        },
        {
            "word": "lock",
            "event": "on_lock",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["secures object", "requires correct key"],
                "failure_narration": {
                    "no_key": "need the right key",
                    "already_locked": "already locked",
                    "must_close_first": "must close it first"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}


def handle_unlock(accessor, action):
    """
    Handle unlock command.

    Allows an actor to unlock a door item or container with the correct key.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to unlock (required)
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
            message="What do you want to unlock?"
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
            actor_id=actor_id, verb="unlock"
        )

    # Fall back to general item search
    if not item:
        item = find_accessible_item(accessor, object_name, actor_id, adjective)

    if not item:
        # Try door lookup for backward compatibility during migration
        if location_id:
            door = find_door_with_adjective(
                accessor, object_name, adjective, location_id,
                actor_id=actor_id, verb="unlock"
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
        if not item.door_locked:
            return HandlerResult(
                success=True,
                message=f"The {object_name} is already unlocked."
            )
        if not item.door_lock_id:
            return HandlerResult(
                success=False,
                message=f"The {object_name} has no lock."
            )
        lock = accessor.get_lock(item.door_lock_id)
        if not lock:
            return HandlerResult(
                success=False,
                message=f"INCONSISTENT STATE: Lock {item.door_lock_id} not found"
            )
        has_key = any(key_id in actor.inventory for key_id in lock.opens_with)
        if not has_key:
            return HandlerResult(
                success=False,
                message=f"You don't have the right key to unlock the {object_name}."
            )
        # Unlock the door item
        item.door_locked = False
        return HandlerResult(
            success=True,
            message=f"You unlock the {object_name}."
        )
    elif hasattr(item, 'locations'):
        # Old-style Door entity
        if not item.locked:
            return HandlerResult(
                success=True,
                message=f"The {object_name} is already unlocked."
            )
        if not item.lock_id:
            return HandlerResult(
                success=False,
                message=f"The {object_name} has no lock."
            )
        lock = accessor.get_lock(item.lock_id)
        if not lock:
            return HandlerResult(
                success=False,
                message=f"INCONSISTENT STATE: Lock {item.lock_id} not found"
            )
        has_key = any(key_id in actor.inventory for key_id in lock.opens_with)
        if not has_key:
            return HandlerResult(
                success=False,
                message=f"You don't have the right key to unlock the {object_name}."
            )
        item.locked = False
        return HandlerResult(
            success=True,
            message=f"You unlock the {object_name}."
        )

    # Check if it's a container
    if not item.container:
        return HandlerResult(
            success=False,
            message=f"The {item.name} has no lock."
        )

    # Check if locked
    locked = item.container.get("locked", False)
    if not locked:
        return HandlerResult(
            success=True,
            message=f"The {item.name} is already unlocked."
        )

    # Check if container has a lock_id
    lock_id = item.container.get("lock_id")
    if not lock_id:
        return HandlerResult(
            success=False,
            message=f"The {item.name} has no lock."
        )

    # Get the lock
    lock = accessor.get_lock(lock_id)
    if not lock:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Lock {lock_id} not found"
        )

    # Check if actor has any of the keys
    has_key = any(key_id in actor.inventory for key_id in lock.opens_with)

    if not has_key:
        return HandlerResult(
            success=False,
            message=f"You don't have the right key to unlock the {item.name}."
        )

    # Unlock the container
    item.container._data["locked"] = False

    return HandlerResult(
        success=True,
        message=f"You unlock the {item.name}."
    )


def handle_lock(accessor, action):
    """
    Handle lock command.

    Allows an actor to lock a door item or container with the correct key.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to lock (required)
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
            message="What do you want to lock?"
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
            actor_id=actor_id, verb="lock"
        )

    # Fall back to general item search
    if not item:
        item = find_accessible_item(accessor, object_name, actor_id, adjective)

    if not item:
        # Try door lookup for backward compatibility during migration
        if location_id:
            door = find_door_with_adjective(
                accessor, object_name, adjective, location_id,
                actor_id=actor_id, verb="lock"
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
                success=False,
                message=f"You must close the {object_name} first."
            )
        if item.door_locked:
            return HandlerResult(
                success=True,
                message=f"The {object_name} is already locked."
            )
        if not item.door_lock_id:
            return HandlerResult(
                success=False,
                message=f"The {object_name} has no lock."
            )
        lock = accessor.get_lock(item.door_lock_id)
        if not lock:
            return HandlerResult(
                success=False,
                message=f"INCONSISTENT STATE: Lock {item.door_lock_id} not found"
            )
        has_key = any(key_id in actor.inventory for key_id in lock.opens_with)
        if not has_key:
            return HandlerResult(
                success=False,
                message=f"You don't have the right key to lock the {object_name}."
            )
        # Lock the door item
        item.door_locked = True
        return HandlerResult(
            success=True,
            message=f"You lock the {object_name}."
        )
    elif hasattr(item, 'locations'):
        # Old-style Door entity
        if item.open:
            return HandlerResult(
                success=False,
                message=f"You must close the {object_name} first."
            )
        if item.locked:
            return HandlerResult(
                success=True,
                message=f"The {object_name} is already locked."
            )
        if not item.lock_id:
            return HandlerResult(
                success=False,
                message=f"The {object_name} has no lock."
            )
        lock = accessor.get_lock(item.lock_id)
        if not lock:
            return HandlerResult(
                success=False,
                message=f"INCONSISTENT STATE: Lock {item.lock_id} not found"
            )
        has_key = any(key_id in actor.inventory for key_id in lock.opens_with)
        if not has_key:
            return HandlerResult(
                success=False,
                message=f"You don't have the right key to lock the {object_name}."
            )
        item.locked = True
        return HandlerResult(
            success=True,
            message=f"You lock the {object_name}."
        )

    # Check if it's a container
    if not item.container:
        return HandlerResult(
            success=False,
            message=f"The {item.name} has no lock."
        )

    # Check if container is open (can't lock an open container)
    if item.container.open:
        return HandlerResult(
            success=False,
            message=f"You must close the {item.name} first."
        )

    # Check if already locked
    locked = item.container.get("locked", False)
    if locked:
        return HandlerResult(
            success=True,
            message=f"The {item.name} is already locked."
        )

    # Check if container has a lock_id
    lock_id = item.container.get("lock_id")
    if not lock_id:
        return HandlerResult(
            success=False,
            message=f"The {item.name} has no lock."
        )

    # Get the lock
    lock = accessor.get_lock(lock_id)
    if not lock:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Lock {lock_id} not found"
        )

    # Check if actor has any of the keys
    has_key = any(key_id in actor.inventory for key_id in lock.opens_with)

    if not has_key:
        return HandlerResult(
            success=False,
            message=f"You don't have the right key to lock the {item.name}."
        )

    # Lock the container
    item.container._data["locked"] = True

    return HandlerResult(
        success=True,
        message=f"You lock the {item.name}."
    )
