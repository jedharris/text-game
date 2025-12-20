"""Light source behaviors - lanterns, torches, etc.

Entity behaviors for light-providing items that automatically
light when taken and extinguish when dropped.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult


def on_take(entity: Any, state: Any, context: Dict) -> EventResult:
    """
    Auto-light when taken (magical runes activate on touch).

    Args:
        entity: The light source being taken
        state: GameState object
        context: Context dict with location, verb

    Returns:
        EventResult with allow and message
    """
    entity.states['lit'] = True

    return EventResult(
        allow=True,
        feedback="As your hand closes around the lantern, the runes flare to life, casting a warm glow."
    )


def on_drop(entity: Any, state: Any, context: Dict) -> EventResult:
    """
    Extinguish when dropped (magical runes deactivate).

    Args:
        entity: The light source being dropped
        state: GameState object
        context: Context dict with location, verb

    Returns:
        EventResult with allow and message
    """
    entity.states['lit'] = False

    return EventResult(
        allow=True,
        feedback="The lantern's runes fade as you set it down, leaving it dark and cold."
    )


def on_put(entity: Any, state: Any, context: Dict) -> EventResult:
    """Extinguish when put down - delegates to on_drop."""
    return on_drop(entity, state, context)
