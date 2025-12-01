"""Threshold checking utilities for puzzle mechanics.

This module provides functions for evaluating numeric conditions and thresholds,
useful for weight puzzles, resource trading, stat checks, etc.

NOTE: This is a library behavior pattern that could be useful to migrate to core
if threshold-based puzzles become a common pattern across many games.
"""

from typing import Optional, Any


def check_threshold(
    value: float,
    target: float,
    tolerance: float = 0.0,
    mode: str = "exact"
) -> bool:
    """
    Check if a value meets a threshold condition.

    Args:
        value: The value to check
        target: The target value
        tolerance: Acceptable deviation from target (default 0.0)
        mode: Comparison mode - "exact" (within tolerance), "min" (>= target),
              "max" (<= target), "range" (within tolerance of target)

    Returns:
        True if condition met, False otherwise

    Example:
        # Weight puzzle: need exactly 3.5 kg ± 0.2 kg
        check_threshold(3.6, 3.5, tolerance=0.2, mode="exact")  # True

        # Stat check: need at least 10 strength
        check_threshold(12, 10, mode="min")  # True

        # Capacity check: must be under 100 kg
        check_threshold(95, 100, mode="max")  # True
    """
    if mode == "exact" or mode == "range":
        return abs(value - target) <= tolerance
    elif mode == "min":
        return value >= target
    elif mode == "max":
        return value <= target
    else:
        raise ValueError(f"Unknown threshold mode: {mode}")


def get_threshold_feedback(
    value: float,
    target: float,
    tolerance: float = 0.0,
    labels: Optional[dict] = None
) -> str:
    """
    Generate hint message about how close value is to target.

    Args:
        value: The current value
        target: The target value
        tolerance: Acceptable deviation
        labels: Optional dict with custom messages:
                {"too_low": "...", "too_high": "...", "close": "...", "exact": "..."}

    Returns:
        Feedback message

    Example:
        msg = get_threshold_feedback(3.2, 3.5, 0.2)
        # Returns: "Too light. You need a bit more weight."

        msg = get_threshold_feedback(3.6, 3.5, 0.2)
        # Returns: "Almost perfect! Just slightly off."
    """
    # Default labels
    default_labels = {
        "too_low": "Too low. You need more.",
        "too_high": "Too high. You need less.",
        "close": "Very close! Almost there.",
        "exact": "Perfect!"
    }

    # Use custom labels if provided
    if labels:
        default_labels.update(labels)

    diff = value - target
    abs_diff = abs(diff)

    # Check if exact match
    if abs_diff <= tolerance:
        return default_labels["exact"]

    # Check if close (within 2x tolerance)
    if abs_diff <= tolerance * 2:
        return default_labels["close"]

    # Too low or too high
    if diff < 0:
        return default_labels["too_low"]
    else:
        return default_labels["too_high"]


def calculate_item_weight(accessor: Any, item_ids: list) -> float:
    """
    Calculate total weight of a list of items.

    Args:
        accessor: StateAccessor instance
        item_ids: List of item IDs to weigh

    Returns:
        Total weight in kg (assumes items have properties.weight)

    Example:
        items_on_plate = ["item_rock", "item_book", "item_coin"]
        total = calculate_item_weight(accessor, items_on_plate)
    """
    total_weight = 0.0

    for item_id in item_ids:
        item = accessor.get_item(item_id)
        if item and hasattr(item, 'properties') and item.properties:
            weight = item.properties.get("weight", 0.0)
            total_weight += weight

    return total_weight


def get_items_in_location(accessor: Any, location_id: str) -> list:
    """
    Get list of item IDs in a specific location.

    This is a helper for weight puzzles where you need to check what's on a plate/pedestal.

    Args:
        accessor: StateAccessor instance
        location_id: Location ID (can be a room or container item)

    Returns:
        List of item IDs in that location

    Example:
        items_on_pedestal = get_items_in_location(accessor, "item_pedestal")
        weight = calculate_item_weight(accessor, items_on_pedestal)
    """
    all_items = accessor.get_all_items()
    items_in_location = []

    for item in all_items:
        if hasattr(item, 'location') and item.location == location_id:
            items_in_location.append(item.id)

    return items_in_location
