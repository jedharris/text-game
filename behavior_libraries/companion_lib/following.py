"""Companion following mechanics.

Allows domesticated creatures and befriended NPCs to follow the player
between locations, with support for location/terrain restrictions.

Actor properties:
{
    "is_companion": true,           # Whether actor follows player
    "location_restrictions": [...], # Location IDs companion won't enter
    "terrain_restrictions": [...],  # Terrain types companion won't enter
    "follow_message": "...",        # Message when companion follows
    "cannot_follow_message": "..."  # Message when companion can't follow
}

Usage:
    from behavior_libraries.companion_lib import (
        get_companions, make_companion, dismiss_companion,
        check_can_follow, on_player_move_companions_follow
    )
"""

from typing import List, Tuple

from src.behavior_manager import EventResult


def get_companions(accessor) -> List:
    """
    Get all actors marked as companions at player's current location.

    Args:
        accessor: StateAccessor instance

    Returns:
        List of Actor objects that are companions at player's location
    """
    player = accessor.get_actor('player')
    if not player:
        return []

    player_location = player.location
    companions = []

    for actor_id, actor in accessor.game_state.actors.items():
        if actor_id == 'player':
            continue
        if actor.location == player_location:
            if actor.properties.get('is_companion', False):
                companions.append(actor)

    return companions


def make_companion(accessor, actor_id: str) -> None:
    """
    Mark an actor as a companion (will follow player).

    Args:
        accessor: StateAccessor instance
        actor_id: ID of actor to make companion
    """
    actor = accessor.get_actor(actor_id)
    if actor:
        actor.properties['is_companion'] = True


def dismiss_companion(accessor, actor_id: str) -> None:
    """
    Remove companion status from an actor.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of actor to dismiss
    """
    actor = accessor.get_actor(actor_id)
    if actor:
        actor.properties['is_companion'] = False


def check_can_follow(accessor, companion, destination_id: str) -> Tuple[bool, str]:
    """
    Check if a companion can follow to a destination.

    Args:
        accessor: StateAccessor instance
        companion: Actor object (the companion)
        destination_id: ID of destination location

    Returns:
        Tuple of (can_follow: bool, message: str)
        If can_follow is True, message is empty.
        If can_follow is False, message explains why.
    """
    # Check location restrictions
    location_restrictions = companion.properties.get('location_restrictions', [])
    if destination_id in location_restrictions:
        message = companion.properties.get(
            'cannot_follow_message',
            f"{companion.name} won't follow you there."
        )
        return False, message

    # Check terrain restrictions
    terrain_restrictions = companion.properties.get('terrain_restrictions', [])
    if terrain_restrictions:
        destination = accessor.get_location(destination_id)
        if destination:
            terrain = destination.properties.get('terrain', '')
            if terrain in terrain_restrictions:
                message = companion.properties.get(
                    'cannot_follow_message',
                    f"{companion.name} can't follow you into the {terrain} terrain."
                )
                return False, message

    return True, ''


def on_player_move_companions_follow(entity, accessor, context: dict) -> EventResult:
    """
    Hook handler - companions follow player when they move.

    This should be registered for the LOCATION_ENTERED hook.

    Args:
        entity: The destination location
        accessor: StateAccessor instance
        context: Context dict with:
            - actor_id: ID of actor who moved (should be 'player')
            - from_location: Previous location ID
            - to_location: New location ID

    Returns:
        EventResult with follow/stay messages
    """
    actor_id = context.get('actor_id', 'player')
    if actor_id != 'player':
        # Only process for player movement
        return EventResult(allow=True, message='')

    from_location = context.get('from_location')
    to_location = context.get('to_location')

    if not from_location or not to_location:
        return EventResult(allow=True, message='')

    # Find companions at the previous location
    messages = []
    for actor_id_key, actor in accessor.game_state.actors.items():
        if actor_id_key == 'player':
            continue
        if actor.location != from_location:
            continue
        if not actor.properties.get('is_companion', False):
            continue

        # This is a companion at the previous location
        can_follow, cannot_message = check_can_follow(accessor, actor, to_location)

        if can_follow:
            # Move companion to new location
            actor.location = to_location
            follow_msg = actor.properties.get(
                'follow_message',
                f"{actor.name} follows you."
            )
            messages.append(follow_msg)
        else:
            # Companion stays behind
            messages.append(cannot_message)

    return EventResult(allow=True, message='\n'.join(messages))


# Vocabulary extension - adds hooks for companion following
vocabulary = {
    "hooks": {
        "location_entered": "on_player_move_companions_follow"
    }
}
