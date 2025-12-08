"""Wander mechanics for NPCs.

Allows NPCs to move randomly within a defined area.

Actor properties:
{
    "wander_area": ["loc1", "loc2", "loc3"],  # Allowed locations
    "wander_frequency": 2,                     # Move every N turns (default 1)
    "wander_chance": 0.5                       # Probability of moving (0.0-1.0)
}

Usage:
    from behavior_libraries.npc_movement_lib import (
        wander_step, set_wander_area
    )
"""

import random
from typing import List, Optional


def wander_step(accessor, actor) -> Optional[str]:
    """
    Move actor to a random location within their wander area.

    Args:
        accessor: StateAccessor instance
        actor: Actor object to move

    Returns:
        Message describing movement, or None if no movement
    """
    area = actor.properties.get('wander_area', [])
    if not area:
        return None

    # Check wander chance
    chance = actor.properties.get('wander_chance', 0.5)
    if random.random() > chance:
        return None  # Stayed in place

    # Pick random location (can be same as current)
    current = actor.location
    available = [loc for loc in area if loc != current]
    if not available:
        return None  # Nowhere else to go

    next_location = random.choice(available)

    # Move actor
    actor.location = next_location

    return f"{actor.name} wanders to {next_location}."


def set_wander_area(accessor, actor_id: str, locations: List[str]) -> None:
    """
    Set wander area for an actor.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of actor to set area for
        locations: List of location IDs for wander area
    """
    actor = accessor.get_actor(actor_id)
    if actor:
        actor.properties['wander_area'] = locations
