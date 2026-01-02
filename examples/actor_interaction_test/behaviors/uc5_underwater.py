"""UC5: Drowning Sailor - Custom behaviors for breath and rescue mechanics.

These behaviors demonstrate how game-specific code integrates with library modules.
They are NOT part of the library - they are custom behaviors for the test game.

Custom behaviors needed for UC5:
1. get_breath_warning - Generate warning messages based on breath level
2. rescue_to_surface - Move actor to breathable location and restore breath
3. check_breath_critical - Check if actor is critically low on breath

Library modules used:
- environment.py: check_breath, needs_breath, apply_environmental_effects
"""

from typing import Any, Optional


# Breath warning thresholds and messages (ordered from most to least severe)
BREATH_WARNINGS = [
    (10, "{name} is about to drown!"),
    (30, "{name} is gasping for air!"),
    (50, "{name}'s breath is running low."),
]


def get_breath_warning(actor) -> Optional[str]:
    """
    Get an appropriate warning message based on actor's breath level.

    Args:
        actor: The Actor to check

    Returns:
        Warning message string, or None if breath is fine
    """
    if not actor:
        return None

    breath = actor.properties.get("breath", 60)
    max_breath = actor.properties.get("max_breath", 60)

    # Calculate percentage
    percent = (breath / max_breath * 100) if max_breath > 0 else 100

    for threshold, message in BREATH_WARNINGS:
        if percent <= threshold:
            return message.format(name=actor.name)

    return None


def check_breath_critical(actor, threshold: int = 10) -> bool:
    """
    Check if actor's breath is critically low.

    Args:
        actor: The Actor to check
        threshold: Breath value considered critical (default: 10)

    Returns:
        True if breath is at or below threshold
    """
    if not actor:
        return False

    breath = actor.properties.get("breath", 60)
    return breath <= threshold


def rescue_to_surface(accessor, actor, surface_location: str) -> str:
    """
    Move an actor to a breathable location and restore their breath.

    Args:
        accessor: StateAccessor for state queries
        actor: The Actor to rescue
        surface_location: ID of the breathable location to move to

    Returns:
        Message describing the rescue
    """
    from behaviors.actor_lib.environment import needs_breath

    if not actor:
        return "No one to rescue."

    if not needs_breath(actor):
        return f"{actor.name} doesn't need to breathe."

    old_location = actor.location
    accessor.set_entity_where(actor.id, surface_location)

    # Restore breath to max
    max_breath = actor.properties.get("max_breath", 60)
    actor.properties["breath"] = max_breath

    return f"{actor.name} is pulled to safety and gasps for air!"


def give_breathing_item(accessor, item, actor) -> Optional[str]:
    """
    Give a breathing item to an actor.

    If item has provides_breathing property, add it to actor's inventory.
    This will protect them from drowning in areas where breathing_item_works.

    Args:
        accessor: StateAccessor for state queries
        item: The Item to give
        actor: The Actor receiving the item

    Returns:
        Message if successful, None if item doesn't provide breathing
    """
    if not item or not actor:
        return None

    if not item.properties.get("provides_breathing"):
        return None

    # Add to actor's inventory
    if item.id not in actor.inventory:
        actor.inventory.append(item.id)

    return f"{actor.name} now has the {item.name} for breathing underwater."


def on_enter_water(entity, accessor, context) -> Optional[Any]:
    """
    Handle actor entering water.

    Called when an actor moves to an underwater location.
    Provides initial breath warning if needed.

    Args:
        entity: The Actor entering water
        accessor: StateAccessor for state queries
        context: Context dict

    Returns:
        EventResult with warning if breath is low, None otherwise
    """
    from src.state_accessor import EventResult
    from behaviors.actor_lib.environment import needs_breath

    if not needs_breath(entity):
        return None

    warning = get_breath_warning(entity)
    if warning:
        return EventResult(allow=True, feedback=warning)

    return None


# Vocabulary extension for UC5-specific events
vocabulary = {
    "events": [
        {
            "event": "on_enter_water",
            "description": "Handle actor entering underwater area (UC5 custom behavior)"
        }
    ]
}
