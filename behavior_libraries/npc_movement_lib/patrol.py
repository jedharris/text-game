"""Patrol mechanics for NPCs.

Allows NPCs to move along fixed patrol routes.

Actor properties:
{
    "patrol_route": ["loc1", "loc2", "loc3"],  # List of location IDs
    "patrol_index": 0,                          # Current position in route
    "patrol_frequency": 3                       # Move every N turns (default 1)
}

Usage:
    from behavior_libraries.npc_movement_lib import (
        patrol_step, set_patrol_route, on_npc_movement
    )
"""

from typing import List, Optional

from src.behavior_manager import EventResult


def patrol_step(accessor, actor) -> Optional[str]:
    """
    Move actor one step along their patrol route.

    Args:
        accessor: StateAccessor instance
        actor: Actor object to move

    Returns:
        Message describing movement, or None if no movement
    """
    route = actor.properties.get('patrol_route', [])
    if not route:
        return None

    current_index = actor.properties.get('patrol_index', 0)

    # Calculate next index (wrap around)
    next_index = (current_index + 1) % len(route)
    next_location = route[next_index]

    # Move actor
    old_location = actor.location
    accessor.set_entity_where(actor.id, next_location)
    actor.properties['patrol_index'] = next_index

    # Generate message
    return f"{actor.name} moves to {next_location}."


def set_patrol_route(accessor, actor_id: str, route: List[str]) -> None:
    """
    Set patrol route for an actor.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of actor to set route for
        route: List of location IDs for patrol route
    """
    actor = accessor.get_actor(actor_id)
    if actor:
        actor.properties['patrol_route'] = route
        actor.properties['patrol_index'] = 0


def on_npc_movement(entity, accessor, context: dict) -> EventResult:
    """
    Hook handler - process NPC movement during NPC_ACTION phase.

    Checks patrol_frequency and moves NPC if appropriate.

    Args:
        entity: The NPC actor
        accessor: StateAccessor instance
        context: Context dict (may contain 'turn')

    Returns:
        EventResult with movement message
    """
    # Check if this actor has a patrol route
    route = entity.properties.get('patrol_route', [])
    if not route:
        return EventResult(allow=True, feedback='')

    # Check frequency
    frequency = entity.properties.get('patrol_frequency', 1)
    turn = accessor.game_state.turn_count

    if turn % frequency != 0:
        return EventResult(allow=True, feedback='')

    # Execute patrol step
    message = patrol_step(accessor, entity)

    return EventResult(allow=True, feedback=message or '')


# Vocabulary extension
vocabulary = {
    "hooks": {
        "npc_action": "on_npc_movement"
    }
}
