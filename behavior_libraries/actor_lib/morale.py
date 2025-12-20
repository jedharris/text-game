"""Morale and fleeing system for actor interaction.

Handles NPC morale calculation and fleeing behavior:
- Morale is calculated dynamically from health, allies, enemies
- When morale drops below flee_threshold, NPC may attempt to flee
- Flee success depends on available unlocked exits

Morale factors:
- Health percentage of base_morale
- +10 per ally (same pack) in location
- +20 if pack alpha is present
- -15 per enemy in location

Actor morale properties:
{
    "base_morale": 100,      # Base morale value (default: 100)
    "flee_threshold": 30,    # Morale below this triggers flee (default: 25)
    "fearless": True         # If true, never flees
}

Usage:
    from behavior_libraries.actor_lib.morale import (
        get_morale, check_flee_condition, attempt_flee,
        get_allies, get_enemies, FleeResult
    )
"""

from dataclasses import dataclass
from typing import List, Optional
import random


# Default values
DEFAULT_BASE_MORALE = 100
DEFAULT_FLEE_THRESHOLD = 25

# Morale modifiers
ALLY_BONUS = 10
ALPHA_BONUS = 20
ENEMY_PENALTY = 15


@dataclass
class FleeResult:
    """Result of a flee attempt.

    Fields:
        narration: Description of the flee attempt for narration.
                   Semantic type: NarrationText
    """
    success: bool
    destination: Optional[str]
    narration: str


def get_allies(accessor, actor) -> List:
    """
    Get allies of an actor in the same location.

    Allies are actors with the same pack_id.

    Args:
        accessor: StateAccessor for state queries
        actor: The Actor to find allies for

    Returns:
        List of ally Actor objects
    """
    if not actor:
        return []

    pack_id = actor.properties.get("pack_id")
    if not pack_id:
        return []

    allies = []
    for actor_id, other in accessor.game_state.actors.items():
        if other.id == actor.id:
            continue
        if other.location != actor.location:
            continue
        if other.properties.get("pack_id") == pack_id:
            allies.append(other)

    return allies


def get_enemies(accessor, actor) -> List:
    """
    Get enemies of an actor in the same location.

    Enemies are actors not in the same pack and not neutral.
    The player is always considered an enemy to hostile NPCs.

    Args:
        accessor: StateAccessor for state queries
        actor: The Actor to find enemies for

    Returns:
        List of enemy Actor objects
    """
    if not actor:
        return []

    pack_id = actor.properties.get("pack_id")
    actor_disposition = actor.properties.get("disposition", "neutral")

    enemies = []
    for actor_id, other in accessor.game_state.actors.items():
        if other.id == actor.id:
            continue
        if other.location != actor.location:
            continue

        other_pack = other.properties.get("pack_id")
        other_disposition = other.properties.get("disposition")

        # Same pack = ally, not enemy
        if pack_id and other_pack == pack_id:
            continue

        # Player is always an enemy to hostile NPCs
        if actor_id == "player" and actor_disposition == "hostile":
            enemies.append(other)
            continue

        # Neutral actors are not enemies
        if other_disposition == "neutral":
            continue

        # Hostile actors are enemies to each other (different packs)
        if actor_disposition == "hostile" and other_disposition == "hostile":
            if pack_id != other_pack:
                enemies.append(other)

    return enemies


def get_morale(accessor, actor) -> int:
    """
    Calculate current morale for an actor.

    Morale = (health_percent * base_morale) + ally_bonuses - enemy_penalties

    Args:
        accessor: StateAccessor for state queries
        actor: The Actor to calculate morale for

    Returns:
        Current morale value (clamped to minimum 0)
    """
    if not actor:
        return 0

    base_morale = actor.properties.get("base_morale", DEFAULT_BASE_MORALE)
    health = actor.properties.get("health", 100)
    max_health = actor.properties.get("max_health", 100)

    # Health percentage of base morale
    health_percent = health / max_health if max_health > 0 else 1.0
    morale = int(base_morale * health_percent)

    # Ally bonuses
    allies = get_allies(accessor, actor)
    morale += len(allies) * ALLY_BONUS

    # Alpha presence bonus
    for ally in allies:
        if ally.properties.get("pack_role") == "alpha":
            morale += ALPHA_BONUS
            break  # Only one alpha bonus

    # Enemy penalties
    enemies = get_enemies(accessor, actor)
    morale -= len(enemies) * ENEMY_PENALTY

    # Clamp to minimum 0
    return max(0, morale)


def check_flee_condition(accessor, actor) -> bool:
    """
    Check if an actor should attempt to flee.

    Args:
        accessor: StateAccessor for state queries
        actor: The Actor to check

    Returns:
        True if actor should flee, False otherwise
    """
    if not actor:
        return False

    # Fearless actors never flee
    if actor.properties.get("fearless", False):
        return False

    flee_threshold = actor.properties.get("flee_threshold", DEFAULT_FLEE_THRESHOLD)
    morale = get_morale(accessor, actor)

    return morale < flee_threshold


def attempt_flee(
    accessor,
    actor,
    force_success: Optional[bool] = None
) -> FleeResult:
    """
    Attempt to flee from current location.

    Args:
        accessor: StateAccessor for state queries
        actor: The Actor attempting to flee
        force_success: Override random chance (for testing)

    Returns:
        FleeResult with outcome details
    """
    if not actor:
        return FleeResult(
            success=False,
            destination=None,
            narration="Invalid actor"
        )

    # Get current location
    location = accessor.get_location(actor.location)
    if not location:
        return FleeResult(
            success=False,
            destination=None,
            narration="Invalid location"
        )

    # Get available exits (excluding locked door exits)
    available_exits = []
    exits = getattr(location, 'exits', {}) or {}

    for direction, dest_id in exits.items():
        # Check if exit has a locked door
        is_blocked = False
        exit_location = f"exit:{actor.location}:{direction}"
        for item in accessor.game_state.items:
            if item.location == exit_location:
                door_props = item.properties.get("door", {})
                if door_props.get("locked", False):
                    is_blocked = True
                    break
        if not is_blocked:
            available_exits.append((direction, dest_id))

    if not available_exits:
        return FleeResult(
            success=False,
            destination=None,
            narration=f"{actor.name} looks for an escape but there is no escape route!"
        )

    # Determine success
    if force_success is not None:
        success = force_success
    else:
        # 50% base chance to flee successfully
        success = random.random() < 0.5

    if not success:
        return FleeResult(
            success=False,
            destination=None,
            narration=f"{actor.name} tries to flee but fails!"
        )

    # Choose random exit and move
    direction, destination = random.choice(available_exits)
    actor.location = destination

    return FleeResult(
        success=True,
        destination=destination,
        narration=f"{actor.name} flees to the {direction}!"
    )


# Vocabulary extension - registers morale events
vocabulary = {
    "events": [
        {
            "event": "on_morale_check",
            "description": "Called when checking if an NPC should flee"
        },
        {
            "event": "on_flee_attempt",
            "description": "Called when an NPC attempts to flee"
        }
    ]
}
