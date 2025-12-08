"""Pack coordination system for actor interaction.

Handles pack behavior where followers sync with their alpha:
- Pack members share a pack_id
- Alpha has pack_role="alpha"
- Followers have pack_role="follower"
- Followers copy alpha's disposition

Actor pack properties:
{
    "pack_id": "wolf_pack",     # Pack identifier
    "pack_role": "alpha",       # "alpha" or "follower"
    "disposition": "hostile"    # Synced from alpha to followers
}

Usage:
    from behaviors.actors.packs import (
        get_pack_members, get_alpha, is_alpha,
        sync_pack_disposition, sync_follower_disposition
    )
"""

from typing import List, Optional


def get_pack_members(accessor, pack_id: str) -> List:
    """
    Get all actors in a pack.

    Args:
        accessor: StateAccessor for state queries
        pack_id: The pack identifier

    Returns:
        List of Actor objects in the pack
    """
    members = []
    for actor_id, actor in accessor.game_state.actors.items():
        if actor.properties.get("pack_id") == pack_id:
            members.append(actor)
    return members


def is_alpha(actor) -> bool:
    """
    Check if actor is a pack alpha.

    Args:
        actor: The Actor to check

    Returns:
        True if actor has pack_role="alpha"
    """
    if not actor:
        return False
    return actor.properties.get("pack_role") == "alpha"


def get_alpha(accessor, actor) -> Optional:
    """
    Get the alpha for an actor's pack.

    Args:
        accessor: StateAccessor for state queries
        actor: The Actor to find alpha for

    Returns:
        Alpha Actor, or None if no pack/alpha
    """
    if not actor:
        return None

    pack_id = actor.properties.get("pack_id")
    if not pack_id:
        return None

    # If actor is alpha, return self
    if is_alpha(actor):
        return actor

    # Find the alpha in the pack
    for actor_id, other in accessor.game_state.actors.items():
        if other.properties.get("pack_id") == pack_id:
            if is_alpha(other):
                return other

    return None


def sync_pack_disposition(accessor, pack_id: str) -> List:
    """
    Sync all followers to their alpha's disposition.

    Args:
        accessor: StateAccessor for state queries
        pack_id: The pack identifier

    Returns:
        List of actors that were changed
    """
    members = get_pack_members(accessor, pack_id)

    # Find the alpha
    alpha = None
    for member in members:
        if is_alpha(member):
            alpha = member
            break

    if not alpha:
        return []

    alpha_disposition = alpha.properties.get("disposition")
    if not alpha_disposition:
        return []

    changed = []
    for member in members:
        if is_alpha(member):
            continue  # Don't change alpha

        current = member.properties.get("disposition")
        if current != alpha_disposition:
            member.properties["disposition"] = alpha_disposition
            changed.append(member)

    return changed


def sync_follower_disposition(accessor, follower) -> bool:
    """
    Sync a single follower to their alpha's disposition.

    Called before a follower takes action to ensure it matches alpha.

    Args:
        accessor: StateAccessor for state queries
        follower: The follower Actor to sync

    Returns:
        True if disposition was changed, False otherwise
    """
    if not follower:
        return False

    # Alpha actors don't sync
    if is_alpha(follower):
        return False

    # Get the alpha
    alpha = get_alpha(accessor, follower)
    if not alpha:
        return False

    alpha_disposition = alpha.properties.get("disposition")
    if not alpha_disposition:
        return False

    current = follower.properties.get("disposition")
    if current == alpha_disposition:
        return False

    follower.properties["disposition"] = alpha_disposition
    return True


# Vocabulary extension - registers pack events
vocabulary = {
    "events": [
        {
            "event": "on_pack_sync",
            "description": "Called when pack disposition is synchronized"
        },
        {
            "event": "on_alpha_disposition_change",
            "description": "Called when a pack alpha's disposition changes"
        }
    ]
}
