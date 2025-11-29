"""Lock behaviors - unlock and lock.

Vocabulary for lock-related actions.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.handler_utils import find_openable_target
from utilities.entity_serializer import serialize_for_handler_result


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

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to unlock (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    item, actor_id, error = find_openable_target(accessor, action, "unlock")
    if error:
        return error

    # Get actor for key checking
    actor = accessor.get_actor(actor_id)

    # Check if it's a door item
    if hasattr(item, 'is_door') and item.is_door:
        data = serialize_for_handler_result(item)
        if not item.door_locked:
            return HandlerResult(
                success=True,
                message=f"The {item.name} is already unlocked.",
                data=data
            )
        if not item.door_lock_id:
            return HandlerResult(
                success=False,
                message=f"The {item.name} has no lock."
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
                message=f"You don't have the right key to unlock the {item.name}."
            )
        item.door_locked = False
        return HandlerResult(
            success=True,
            message=f"You unlock the {item.name}.",
            data=data
        )

    # Check if it's a container
    if not item.container:
        return HandlerResult(
            success=False,
            message=f"The {item.name} has no lock."
        )

    data = serialize_for_handler_result(item)

    # Check if locked
    locked = item.container.get("locked", False)
    if not locked:
        return HandlerResult(
            success=True,
            message=f"The {item.name} is already unlocked.",
            data=data
        )

    # Check if container has a lock_id
    lock_id = item.container.get("lock_id")
    if not lock_id:
        return HandlerResult(
            success=False,
            message=f"The {item.name} has no lock."
        )

    lock = accessor.get_lock(lock_id)
    if not lock:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Lock {lock_id} not found"
        )

    has_key = any(key_id in actor.inventory for key_id in lock.opens_with)
    if not has_key:
        return HandlerResult(
            success=False,
            message=f"You don't have the right key to unlock the {item.name}."
        )

    item.container._data["locked"] = False

    return HandlerResult(
        success=True,
        message=f"You unlock the {item.name}.",
        data=data
    )


def handle_lock(accessor, action):
    """
    Handle lock command.

    Allows an actor to lock a door item or container with the correct key.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to lock (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    item, actor_id, error = find_openable_target(accessor, action, "lock")
    if error:
        return error

    # Get actor for key checking
    actor = accessor.get_actor(actor_id)

    # Check if it's a door item
    if hasattr(item, 'is_door') and item.is_door:
        data = serialize_for_handler_result(item)
        if item.door_open:
            return HandlerResult(
                success=False,
                message=f"You must close the {item.name} first."
            )
        if item.door_locked:
            return HandlerResult(
                success=True,
                message=f"The {item.name} is already locked.",
                data=data
            )
        if not item.door_lock_id:
            return HandlerResult(
                success=False,
                message=f"The {item.name} has no lock."
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
                message=f"You don't have the right key to lock the {item.name}."
            )
        item.door_locked = True
        return HandlerResult(
            success=True,
            message=f"You lock the {item.name}.",
            data=data
        )

    # Check if it's a container
    if not item.container:
        return HandlerResult(
            success=False,
            message=f"The {item.name} has no lock."
        )

    data = serialize_for_handler_result(item)

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
            message=f"The {item.name} is already locked.",
            data=data
        )

    # Check if container has a lock_id
    lock_id = item.container.get("lock_id")
    if not lock_id:
        return HandlerResult(
            success=False,
            message=f"The {item.name} has no lock."
        )

    lock = accessor.get_lock(lock_id)
    if not lock:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Lock {lock_id} not found"
        )

    has_key = any(key_id in actor.inventory for key_id in lock.opens_with)
    if not has_key:
        return HandlerResult(
            success=False,
            message=f"You don't have the right key to lock the {item.name}."
        )

    item.container._data["locked"] = True

    return HandlerResult(
        success=True,
        message=f"You lock the {item.name}.",
        data=data
    )
