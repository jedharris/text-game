"""Sequence tracking utilities for puzzle mechanics.

This module provides functions for tracking and validating sequences of player actions,
useful for musical puzzles, combination locks, gesture-based puzzles, etc.

NOTE: This is a library behavior pattern that could be useful to migrate to core
if sequence-based puzzles become a common pattern across many games.
"""

from typing import Any, List


def track_action(entity: Any, action_key: str, max_length: int = 20) -> List[str]:
    """
    Append an action to the entity's sequence tracker.

    Args:
        entity: The entity tracking the sequence
        action_key: The action to add to the sequence
        max_length: Maximum sequence length (default 20, prevents infinite growth)

    Returns:
        The current sequence after adding this action

    Example:
        # Track musical notes
        sequence = track_action(stalactite_puzzle, "note_c")
        sequence = track_action(stalactite_puzzle, "note_e")
    """
    # Initialize states if needed
    if not hasattr(entity, 'states') or entity.states is None:
        entity.states = {}

    # Initialize sequence if needed
    if "action_sequence" not in entity.states:
        entity.states["action_sequence"] = []

    # Append action
    entity.states["action_sequence"].append(action_key)

    # Trim if too long (prevent memory issues)
    if len(entity.states["action_sequence"]) > max_length:
        entity.states["action_sequence"] = entity.states["action_sequence"][-max_length:]

    return entity.states["action_sequence"]


def check_sequence(entity: Any, expected_sequence: List[str], exact: bool = True) -> bool:
    """
    Check if the entity's tracked sequence matches the expected sequence.

    Args:
        entity: The entity tracking the sequence
        expected_sequence: The sequence to match against
        exact: If True, must match exactly. If False, expected can be subset at end.

    Returns:
        True if sequence matches, False otherwise

    Example:
        # Exact match required
        if check_sequence(puzzle, ["red", "blue", "green"], exact=True):
            # Sequence matches exactly

        # Check if sequence ends with expected pattern
        if check_sequence(puzzle, ["blue", "green"], exact=False):
            # Last two actions match pattern
    """
    if not hasattr(entity, 'states') or entity.states is None:
        return False

    current_sequence = entity.states.get("action_sequence", [])

    if exact:
        return current_sequence == expected_sequence
    else:
        # Check if current sequence ends with expected sequence
        if len(current_sequence) < len(expected_sequence):
            return False
        return current_sequence[-len(expected_sequence):] == expected_sequence


def get_sequence(entity: Any) -> List[str]:
    """
    Get the current action sequence without modifying it.

    Args:
        entity: The entity tracking the sequence

    Returns:
        The current sequence (empty list if none)

    Example:
        current = get_sequence(puzzle)
        if len(current) > 5:
            # Player has tried many things
    """
    if not hasattr(entity, 'states') or entity.states is None:
        return []

    return entity.states.get("action_sequence", [])


def reset_sequence(entity: Any) -> None:
    """
    Clear the entity's tracked sequence.

    Args:
        entity: The entity tracking the sequence

    Example:
        # Wrong sequence, reset the puzzle
        reset_sequence(stalactite_puzzle)
    """
    if not hasattr(entity, 'states') or entity.states is None:
        entity.states = {}

    entity.states["action_sequence"] = []


def get_sequence_progress(entity: Any, expected_sequence: List[str]) -> int:
    """
    Get how many actions at the end of current sequence match expected sequence.

    Useful for providing partial feedback ("you got 3 out of 5 notes correct").

    Args:
        entity: The entity tracking the sequence
        expected_sequence: The target sequence

    Returns:
        Number of matching actions from the end (0 if none match)

    Example:
        # Expected: ["do", "re", "mi", "fa", "sol"]
        # Current:  ["do", "re", "mi"]
        # Returns: 3

        # Expected: ["do", "re", "mi", "fa", "sol"]
        # Current:  ["do", "re", "la"]
        # Returns: 0 (sequence broke at "la")
    """
    current_sequence = get_sequence(entity)

    # Check how many from the start match
    matches = 0
    for i, expected_action in enumerate(expected_sequence):
        if i < len(current_sequence) and current_sequence[i] == expected_action:
            matches += 1
        else:
            break  # Sequence broke

    return matches
