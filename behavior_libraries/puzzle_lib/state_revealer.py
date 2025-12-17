"""State revelation utilities for puzzle mechanics.

This module provides reusable functions for revealing hidden items and
generating progressive descriptions based on entity state.

Patterns extracted from extended_game/behaviors/crystal_ball.py and magic_mat.py.

NOTE: This is a library behavior pattern that could be useful to migrate to core
if state-based revelation becomes a common pattern across many games.
"""
from src.types import ActorId

from typing import Dict, Any, List, Callable, Optional


def reveal_item(accessor: Any, item_id: str, condition_fn: Optional[Callable] = None) -> bool:
    """
    Reveal a hidden item by setting states.hidden = False.

    Args:
        accessor: StateAccessor instance
        item_id: ID of the item to reveal
        condition_fn: Optional function(item, accessor) -> bool to check before revealing

    Returns:
        True if item was revealed, False if not found or condition failed

    Example:
        # Unconditional reveal
        reveal_item(accessor, "item_secret_key")

        # Conditional reveal
        def check_magic_level(item, acc):
            player = acc.get_actor(ActorId("player"))
            return player.states.get("magic_level", 0) >= 3
        reveal_item(accessor, "item_secret_key", check_magic_level)
    """
    item = accessor.get_item(item_id)
    if not item:
        return False

    # Check condition if provided
    if condition_fn and not condition_fn(item, accessor):
        return False

    # Initialize states if needed
    if not hasattr(item, 'states') or item.states is None:
        item.states = {}

    # Reveal the item
    was_hidden = item.states.get("hidden", False)
    item.states["hidden"] = False

    return was_hidden  # Return True if we actually changed state


def get_progressive_description(
    entity: Any,
    state_key: str,
    descriptions: List[str],
    increment: bool = True
) -> str:
    """
    Get a description that changes based on how many times entity has been examined.

    Automatically increments the state counter unless increment=False.

    Args:
        entity: The entity being examined
        state_key: Name of the state field to track count (e.g., "examine_count")
        descriptions: List of descriptions, indexed by count (0-based)
        increment: Whether to increment the counter (default True)

    Returns:
        Description string based on current count

    Example:
        descriptions = [
            "You see a dusty old book.",
            "Looking closer, you notice strange runes.",
            "The runes begin to glow!",
            "The runes are glowing brightly."  # Repeats for count >= 3
        ]
        msg = get_progressive_description(entity, "examine_count", descriptions)
    """
    # Initialize states if needed
    if not hasattr(entity, 'states') or entity.states is None:
        entity.states = {}

    # Get current count
    count = entity.states.get(state_key, 0)

    # Increment if requested
    if increment:
        entity.states[state_key] = count + 1

    # Return appropriate description (last one repeats for high counts)
    if count < len(descriptions):
        return descriptions[count]
    else:
        return descriptions[-1] if descriptions else ""


def check_state_threshold(entity: Any, state_key: str, threshold: int) -> bool:
    """
    Check if an entity's state value meets or exceeds a threshold.

    Args:
        entity: The entity to check
        state_key: Name of the state field
        threshold: Minimum value required

    Returns:
        True if state >= threshold, False otherwise

    Example:
        if check_state_threshold(mushroom, "times_watered", 3):
            # Mushroom is fully grown
    """
    if not hasattr(entity, 'states') or entity.states is None:
        return False

    return entity.states.get(state_key, 0) >= threshold
