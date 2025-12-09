"""Faction reputation system for The Shattered Meridian.

Tracks reputation with factions that affects multiple NPCs.
Uses the existing relationship system as foundation.

Faction definitions are stored in GameState.extra['factions']:
{
    "myconid_collective": {
        "representative": "faction_myconid",
        "members": ["npc_fd_myconid_elder", "npc_fd_myconid_guard"],
        "sync_dimensions": ["trust", "gratitude"],
        "description": "The collective will of the Myconid colony"
    },
    "town_council": {
        "representative": "faction_council",
        "members": ["npc_cr_guard_captain", "npc_cr_herbalist"],
        "sync_dimensions": ["trust"],
        "description": "The governing body of the civilized remnants"
    }
}

Usage:
    from big_game.behaviors.factions import (
        get_faction_reputation, modify_faction_reputation,
        get_faction_for_actor, sync_faction_reputation
    )
"""

from typing import Dict, List, Optional

# Import from main behaviors directory
from behaviors.actors.relationships import (
    get_relationship, modify_relationship
)
from src.behavior_manager import EventResult


# Faction IDs for reference
FACTION_MYCONID = "myconid_collective"
FACTION_COUNCIL = "town_council"
FACTION_UNDERCITY = "undercity"
FACTION_BEAST_SPIRITS = "beast_spirits"
FACTION_FROZEN_KEEPERS = "frozen_keepers"


def get_factions(accessor) -> Dict:
    """
    Get all faction definitions.

    Args:
        accessor: StateAccessor instance

    Returns:
        Dict of faction_id -> faction definition
    """
    return accessor.game_state.extra.get('factions', {})


def get_faction_for_actor(accessor, actor_id: str) -> Optional[str]:
    """
    Find which faction an actor belongs to.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of the actor

    Returns:
        Faction ID if found, None otherwise
    """
    factions = get_factions(accessor)

    for faction_id, faction_def in factions.items():
        members = faction_def.get('members', [])
        if actor_id in members:
            return faction_id
        # Also check if this is the faction representative
        if faction_def.get('representative') == actor_id:
            return faction_id

    return None


def get_faction_reputation(accessor, faction_id: str) -> Dict[str, int]:
    """
    Get current reputation with a faction.

    Args:
        accessor: StateAccessor instance
        faction_id: ID of the faction

    Returns:
        Dict of relationship dimensions (trust, gratitude, fear)
    """
    factions = get_factions(accessor)
    faction_def = factions.get(faction_id)

    if not faction_def:
        return {}

    rep_actor_id = faction_def.get('representative')
    if not rep_actor_id:
        return {}

    rep_actor = accessor.get_actor(rep_actor_id)
    if not rep_actor:
        return {}

    return get_relationship(rep_actor, 'player')


def modify_faction_reputation(
    accessor,
    faction_id: str,
    dimension: str,
    delta: int,
    sync_to_members: bool = True
) -> List[str]:
    """
    Modify reputation with a faction.

    Args:
        accessor: StateAccessor instance
        faction_id: ID of the faction
        dimension: Relationship dimension ('trust', 'gratitude', 'fear')
        delta: Amount to change (positive or negative)
        sync_to_members: Whether to sync to faction members

    Returns:
        List of messages about reputation changes
    """
    factions = get_factions(accessor)
    faction_def = factions.get(faction_id)

    if not faction_def:
        return [f"Unknown faction: {faction_id}"]

    messages = []

    # Modify faction representative's relationship
    rep_actor_id = faction_def.get('representative')
    if rep_actor_id:
        rep_actor = accessor.get_actor(rep_actor_id)
        if rep_actor:
            result = modify_relationship(accessor, rep_actor, 'player', dimension, delta)

            faction_name = faction_def.get('description', faction_id.replace('_', ' '))
            if delta > 0:
                messages.append(f"Your {dimension} with the {faction_name} has increased.")
            else:
                messages.append(f"Your {dimension} with the {faction_name} has decreased.")

            if result.threshold_crossed:
                messages.append(f"Threshold crossed: {result.threshold_crossed}")

    # Sync to members if this dimension syncs
    if sync_to_members:
        sync_dimensions = faction_def.get('sync_dimensions', [])
        if dimension in sync_dimensions:
            member_messages = sync_faction_reputation(accessor, faction_id, dimension)
            messages.extend(member_messages)

    return messages


def sync_faction_reputation(
    accessor,
    faction_id: str,
    dimension: str
) -> List[str]:
    """
    Sync faction reputation to all member NPCs.

    Args:
        accessor: StateAccessor instance
        faction_id: ID of the faction
        dimension: Relationship dimension to sync

    Returns:
        List of messages about synced changes
    """
    factions = get_factions(accessor)
    faction_def = factions.get(faction_id)

    if not faction_def:
        return []

    messages: List[str] = []

    # Get faction representative's current value
    rep_actor_id = faction_def.get('representative')
    if not rep_actor_id:
        return []

    rep_actor = accessor.get_actor(rep_actor_id)
    if not rep_actor:
        return []

    faction_rel = get_relationship(rep_actor, 'player')
    faction_value = faction_rel.get(dimension, 0)

    # Sync to all members
    for member_id in faction_def.get('members', []):
        member = accessor.get_actor(member_id)
        if member:
            member_rel = get_relationship(member, 'player')
            current_value = member_rel.get(dimension, 0)

            # Calculate delta to match faction value
            delta = faction_value - current_value
            if delta != 0:
                modify_relationship(accessor, member, 'player', dimension, delta)

    return messages


def get_faction_disposition(accessor, faction_id: str) -> str:
    """
    Get overall disposition of a faction toward the player.

    Args:
        accessor: StateAccessor instance
        faction_id: ID of the faction

    Returns:
        Disposition: 'hostile', 'neutral', 'friendly', or 'allied'
    """
    rep = get_faction_reputation(accessor, faction_id)

    if not rep:
        return 'neutral'

    trust = rep.get('trust', 0)
    fear = rep.get('fear', 0)

    # High trust without fear = friendly/allied
    if trust >= 5:
        if trust >= 8:
            return 'allied'
        return 'friendly'

    # High fear without trust = hostile
    if fear >= 5 and trust < 3:
        return 'hostile'

    return 'neutral'


def check_faction_threshold(
    accessor,
    faction_id: str,
    dimension: str,
    threshold: int
) -> bool:
    """
    Check if faction reputation meets a threshold.

    Args:
        accessor: StateAccessor instance
        faction_id: ID of the faction
        dimension: Dimension to check
        threshold: Threshold value

    Returns:
        True if dimension >= threshold
    """
    rep = get_faction_reputation(accessor, faction_id)
    return rep.get(dimension, 0) >= threshold


def on_faction_action(entity, accessor, context: dict) -> EventResult:
    """
    Event handler for actions affecting faction reputation.

    Args:
        entity: The actor involved
        accessor: StateAccessor instance
        context: Must contain 'action' and optionally 'faction_id'

    Returns:
        EventResult with reputation messages
    """
    action = context.get('action')
    faction_id = context.get('faction_id')

    if not action:
        return EventResult(allow=True, message='')

    # If no explicit faction, try to determine from entity
    if not faction_id and entity:
        faction_id = get_faction_for_actor(accessor, entity.id)

    if not faction_id:
        return EventResult(allow=True, message='')

    # Determine reputation change based on action
    # Positive actions
    positive_actions = ['help', 'heal', 'gift', 'rescue', 'defend']
    negative_actions = ['attack', 'steal', 'kill', 'threaten', 'betray']

    if action in positive_actions:
        messages = modify_faction_reputation(accessor, faction_id, 'trust', 1)
        messages.extend(modify_faction_reputation(accessor, faction_id, 'gratitude', 1))
    elif action in negative_actions:
        messages = modify_faction_reputation(accessor, faction_id, 'trust', -2)
        messages.extend(modify_faction_reputation(accessor, faction_id, 'fear', 1))
    else:
        messages = []

    return EventResult(allow=True, message='\n'.join(messages))


# Vocabulary extension
vocabulary = {
    "events": [
        {
            "event": "on_faction_action",
            "description": "Called when an action affects faction reputation"
        }
    ]
}
