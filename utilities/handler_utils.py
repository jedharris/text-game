"""
Handler utility functions.

Provides shared preamble utilities for item-targeting handlers.
"""

from typing import Tuple, Optional, Dict, Any

from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item


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
            message=f"You don't see any {object_name} here."
        )

    return item, None
