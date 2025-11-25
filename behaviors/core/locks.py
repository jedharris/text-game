"""Lock behaviors - unlock and lock.

Vocabulary for lock-related actions.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item


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

    Allows an actor to unlock a door or container with the correct key.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to unlock (required)

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

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

    # Try to find as door first
    door = None
    for d in accessor.game_state.doors:
        if object_name.lower() in d.id.lower() or object_name.lower() in d.description.lower():
            door = d
            break

    if door:
        # Check if already unlocked
        if not door.locked:
            return HandlerResult(
                success=True,
                message=f"The {object_name} is already unlocked."
            )

        # Check if door has a lock
        if not door.lock_id:
            return HandlerResult(
                success=False,
                message=f"The {object_name} has no lock."
            )

        # Get the lock
        lock = accessor.get_lock(door.lock_id)
        if not lock:
            return HandlerResult(
                success=False,
                message=f"INCONSISTENT STATE: Lock {door.lock_id} not found"
            )

        # Check if actor has any of the keys that open this lock
        has_key = False
        for key_id in lock.opens_with:
            if key_id in actor.inventory:
                has_key = True
                break

        if not has_key:
            return HandlerResult(
                success=False,
                message=f"You don't have the right key to unlock the {object_name}."
            )

        # Unlock the door
        result = accessor.update(door, {"locked": False})
        if not result.success:
            return HandlerResult(
                success=False,
                message=f"INCONSISTENT STATE: Failed to unlock door: {result.message}"
            )

        return HandlerResult(
            success=True,
            message=f"You unlock the {object_name}."
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
    has_key = False
    for key_id in lock.opens_with:
        if key_id in actor.inventory:
            has_key = True
            break

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

    Allows an actor to lock a door or container with the correct key.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to lock (required)

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

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

    # Try to find as door first
    door = None
    for d in accessor.game_state.doors:
        if object_name.lower() in d.id.lower() or object_name.lower() in d.description.lower():
            door = d
            break

    if door:
        # Check if door is open (can't lock an open door)
        if door.open:
            return HandlerResult(
                success=False,
                message=f"You must close the {object_name} first."
            )

        # Check if already locked
        if door.locked:
            return HandlerResult(
                success=True,
                message=f"The {object_name} is already locked."
            )

        # Check if door has a lock
        if not door.lock_id:
            return HandlerResult(
                success=False,
                message=f"The {object_name} has no lock."
            )

        # Get the lock
        lock = accessor.get_lock(door.lock_id)
        if not lock:
            return HandlerResult(
                success=False,
                message=f"INCONSISTENT STATE: Lock {door.lock_id} not found"
            )

        # Check if actor has any of the keys that work with this lock
        has_key = False
        for key_id in lock.opens_with:
            if key_id in actor.inventory:
                has_key = True
                break

        if not has_key:
            return HandlerResult(
                success=False,
                message=f"You don't have the right key to lock the {object_name}."
            )

        # Lock the door
        result = accessor.update(door, {"locked": True})
        if not result.success:
            return HandlerResult(
                success=False,
                message=f"INCONSISTENT STATE: Failed to lock door: {result.message}"
            )

        return HandlerResult(
            success=True,
            message=f"You lock the {object_name}."
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
    has_key = False
    for key_id in lock.opens_with:
        if key_id in actor.inventory:
            has_key = True
            break

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
