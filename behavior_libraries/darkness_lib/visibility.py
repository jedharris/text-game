"""Visibility mechanics for darkness/light.

Implements darkness enforcement where certain locations require light to
see and interact with objects.

Location properties:
{
    "requires_light": true,     # Location is dark without light
    "ambient_light": false,     # Location has natural light (bioluminescence, etc.)
    "darkness_description": "..." # Custom description when dark
}

Item properties:
{
    "provides_light": true      # Item can provide light
}

Item states:
{
    "lit": true                 # Light source is currently lit
}

Actions allowed in darkness:
- go (movement)
- inventory
- drop

Actions blocked in darkness:
- examine, look
- take
- attack
- use
- (most other actions)

Usage:
    from behavior_libraries.darkness_lib import (
        check_visibility, get_light_sources, get_darkness_description,
        on_visibility_check
    )
"""

from typing import List

from src.behavior_manager import EventResult


# Actions that can be performed in complete darkness
DARK_ALLOWED_VERBS = {'go', 'inventory', 'drop', 'north', 'south', 'east', 'west',
                       'up', 'down', 'in', 'out', 'enter', 'exit', 'leave'}


def check_visibility(accessor, location_id: str) -> bool:
    """
    Check if a location has sufficient light for visibility.

    Args:
        accessor: StateAccessor instance
        location_id: ID of location to check

    Returns:
        True if location is visible (has light), False if dark
    """
    location = accessor.get_location(location_id)
    if not location:
        return True  # Unknown location, allow

    # Check if location requires light
    if not location.properties.get('requires_light', False):
        return True  # Doesn't require light, always visible

    # Check for ambient light (bioluminescence, etc.)
    if location.properties.get('ambient_light', False):
        return True

    # Check for active light sources
    light_sources = get_light_sources(accessor, location_id)
    return len(light_sources) > 0


def get_light_sources(accessor, location_id: str) -> List:
    """
    Get all active light sources in a location.

    Includes:
    - Items in the location with provides_light=True and lit=True
    - Items carried by player if player is at location

    Args:
        accessor: StateAccessor instance
        location_id: ID of location to check

    Returns:
        List of Item objects that are active light sources
    """
    sources = []
    player = accessor.get_actor('player')

    for item in accessor.game_state.items:
        if not item.properties.get('provides_light', False):
            continue
        if not item.states.get('lit', False):
            continue

        # Check if item is in location
        if item.location == location_id:
            sources.append(item)
            continue

        # Check if item is carried by player at this location
        if player and player.location == location_id:
            if item.id in player.inventory:
                sources.append(item)

    return sources


def get_darkness_description(accessor, location_id: str) -> str:
    """
    Get description for a dark location.

    Args:
        accessor: StateAccessor instance
        location_id: ID of location

    Returns:
        Darkness description string
    """
    location = accessor.get_location(location_id)
    if location:
        custom = location.properties.get('darkness_description')
        if custom:
            return custom

    return "It's too dark to see anything."


def on_visibility_check(entity, accessor, context: dict) -> EventResult:
    """
    Hook handler - block actions in darkness.

    This should be registered for the VISIBILITY_CHECK hook.

    Args:
        entity: The location entity
        accessor: StateAccessor instance
        context: Context dict with:
            - verb: The action being attempted
            - actor_id: ID of actor attempting action

    Returns:
        EventResult allowing or blocking the action
    """
    verb = context.get('verb', '')
    actor_id = context.get('actor_id', 'player')

    # Always allow certain actions in darkness
    if verb.lower() in DARK_ALLOWED_VERBS:
        return EventResult(allow=True, message='')

    # Check if location has light
    location_id = entity.id if hasattr(entity, 'id') else None
    if not location_id:
        # Try to get from actor's location
        actor = accessor.get_actor(actor_id)
        if actor:
            location_id = actor.location

    if not location_id:
        return EventResult(allow=True, message='')

    # Check visibility
    if check_visibility(accessor, location_id):
        return EventResult(allow=True, message='')

    # Block action due to darkness
    darkness_msg = get_darkness_description(accessor, location_id)
    return EventResult(allow=False, message=darkness_msg)


# Vocabulary extension - register hook
vocabulary = {
    "hooks": {
        "visibility_check": "on_visibility_check"
    }
}
