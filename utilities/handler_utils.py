"""
Handler utility functions.

Provides shared preamble utilities for item-targeting handlers.
"""

from typing import Tuple, Optional, Dict, Any, Union

from src.state_accessor import HandlerResult
from src.word_entry import WordEntry
from utilities.utils import find_accessible_item, find_door_with_adjective


def get_object_word(object_name: Union[str, WordEntry, None]) -> Optional[str]:
    """
    Extract the word string from an object name that may be a string or WordEntry.

    Args:
        object_name: Either a string, WordEntry, or None

    Returns:
        The lowercase word string, or None if object_name is None
    """
    if object_name is None:
        return None
    if isinstance(object_name, WordEntry):
        return object_name.word.lower()
    return object_name.lower()


def get_display_name(object_name: Union[str, WordEntry, None]) -> str:
    """
    Extract a display-friendly name from an object name that may be a string or WordEntry.

    Args:
        object_name: Either a string, WordEntry, or None

    Returns:
        The word string suitable for display in messages
    """
    if object_name is None:
        return "something"
    if isinstance(object_name, WordEntry):
        return object_name.word
    return object_name


def find_action_target(
    accessor,
    action: Dict[str, Any]
) -> Tuple[Optional[Any], Optional[HandlerResult]]:
    """
    Standard preamble for item-targeting handlers.

    Extracts actor_id, object, adjective from action.
    Validates actor exists.
    Finds accessible item using adjective for disambiguation.

    The verb in action["verb"] is used for error messages and is the
    canonical form from the parser/vocabulary.

    Args:
        accessor: StateAccessor instance
        action: Action dict containing:
            - verb: Canonical verb from parser (required for messages)
            - actor_id: Actor performing action (default: "player")
            - object: Name of target object
            - adjective: Optional adjective for disambiguation

    Returns:
        Tuple of (item, error_result):
        - If item found: (item, None)
        - If error: (None, HandlerResult with error message)
    """
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    adjective = action.get("adjective")
    verb = action.get("verb", "interact with")

    if not object_name:
        return None, HandlerResult(
            success=False,
            message=f"What do you want to {verb}?"
        )

    actor = accessor.get_actor(actor_id)
    if not actor:
        return None, HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    item = find_accessible_item(accessor, object_name, actor_id, adjective)
    if not item:
        return None, HandlerResult(
            success=False,
            message=f"You don't see any {get_display_name(object_name)} here."
        )

    return item, None


def find_openable_target(
    accessor,
    action: Dict[str, Any],
    verb: str
) -> Tuple[Optional[Any], Optional[str], Optional[HandlerResult]]:
    """
    Shared preamble for door/container handlers (open, close, lock, unlock).

    Extracts actor_id, object, adjective from action.
    Validates actor exists.
    Performs smart door selection when object_word == "door".
    Falls back to general item search.

    Args:
        accessor: StateAccessor instance
        action: Action dict containing:
            - actor_id: Actor performing action (default: "player")
            - object: Name of target object
            - adjective: Optional adjective for disambiguation
        verb: The verb being performed (e.g., "open", "close", "lock", "unlock")
              Used for error messages and smart door selection.

    Returns:
        Tuple of (item, actor_id, error_result):
        - If item found: (item, actor_id, None)
        - If error: (None, actor_id, HandlerResult with error message)
    """
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    adjective = action.get("adjective")

    if not object_name:
        return None, actor_id, HandlerResult(
            success=False,
            message=f"What do you want to {verb}?"
        )

    actor = accessor.get_actor(actor_id)
    if not actor:
        return None, actor_id, HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Get current location for door searches
    location = accessor.get_current_location(actor_id)
    location_id = location.id if location else None

    # For door-related searches, use smart door selection
    item = None
    object_word = get_object_word(object_name)
    if object_word == "door" and location_id:
        item = find_door_with_adjective(
            accessor, object_name, adjective, location_id,
            actor_id=actor_id, verb=verb
        )

    # Fall back to general item search
    if not item:
        item = find_accessible_item(accessor, object_name, actor_id, adjective)

    if not item:
        return None, actor_id, HandlerResult(
            success=False,
            message=f"You don't see any {get_display_name(object_name)} here."
        )

    return item, actor_id, None
