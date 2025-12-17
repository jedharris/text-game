"""Alignment tracking for moral choice systems.

This module provides functions for tracking player moral choices and maintaining
an alignment score that can affect NPC reactions, puzzle outcomes, etc.

Alignment is stored in actor.states.alignment as a numeric value (-10 to +10).

NOTE: This is a library behavior pattern that could be useful to migrate to core
if alignment-based mechanics become a common pattern across many games.
"""

from typing import Any, Optional

from src.types import ActorId


def record_choice(
    accessor: Any,
    actor_id: ActorId,
    choice_type: str,
    weight: float = 1.0
) -> bool:
    """
    Record a moral choice and update alignment score.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of the actor making the choice
        choice_type: Type of choice - "good", "neutral", or "evil"
        weight: How much this choice affects alignment (default 1.0)

    Returns:
        True if choice recorded, False if actor not found

    Example:
        # Player spared an enemy
        record_choice(accessor, "player", "good", weight=2.0)

        # Player was cruel
        record_choice(accessor, "player", "evil", weight=1.5)

        # Player took neutral action
        record_choice(accessor, "player", "neutral", weight=1.0)
    """
    actor = accessor.get_actor(actor_id)
    if not actor:
        return False

    # Initialize states if needed
    if not hasattr(actor, 'states') or actor.states is None:
        actor.states = {}

    # Initialize alignment if needed (0 = neutral)
    if "alignment" not in actor.states:
        actor.states["alignment"] = 0.0

    # Update alignment based on choice type
    if choice_type.lower() in ["good", "merciful", "kind"]:
        actor.states["alignment"] += weight
    elif choice_type.lower() in ["evil", "cruel", "malicious"]:
        actor.states["alignment"] -= weight
    # neutral choices don't change alignment

    # Clamp alignment to -10 to +10 range
    actor.states["alignment"] = max(-10.0, min(10.0, actor.states["alignment"]))

    return True


def get_alignment(accessor: Any, actor_id: ActorId) -> float:
    """
    Get the current alignment score of an actor.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of the actor

    Returns:
        Alignment score (-10 to +10, 0 is neutral). Returns 0 if actor not found.

    Example:
        alignment = get_alignment(accessor, "player")
        if alignment > 5:
            # Player is very good
        elif alignment < -5:
            # Player is very evil
    """
    actor = accessor.get_actor(actor_id)
    if not actor or not hasattr(actor, 'states') or actor.states is None:
        return 0.0

    return actor.states.get("alignment", 0.0)


def get_alignment_descriptor(alignment_score: float) -> str:
    """
    Get a text descriptor for an alignment score.

    Args:
        alignment_score: Numeric alignment (-10 to +10)

    Returns:
        Descriptive string

    Example:
        desc = get_alignment_descriptor(7.5)
        # Returns: "Virtuous"
    """
    if alignment_score >= 7:
        return "Saintly"
    elif alignment_score >= 4:
        return "Virtuous"
    elif alignment_score >= 1:
        return "Good"
    elif alignment_score > -1:
        return "Neutral"
    elif alignment_score > -4:
        return "Questionable"
    elif alignment_score > -7:
        return "Wicked"
    else:
        return "Malevolent"


def get_alignment_category(alignment_score: float) -> str:
    """
    Get a simple category for alignment (good/neutral/evil).

    Args:
        alignment_score: Numeric alignment (-10 to +10)

    Returns:
        "good", "neutral", or "evil"

    Example:
        category = get_alignment_category(get_alignment(accessor, "player"))
        if category == "evil":
            # Evil NPCs are friendly, good NPCs are hostile
    """
    if alignment_score > 2:
        return "good"
    elif alignment_score < -2:
        return "evil"
    else:
        return "neutral"


def reset_alignment(accessor: Any, actor_id: ActorId) -> bool:
    """
    Reset actor's alignment to neutral (0).

    Args:
        accessor: StateAccessor instance
        actor_id: ID of the actor

    Returns:
        True if reset, False if actor not found

    Example:
        # Player found redemption
        reset_alignment(accessor, "player")
    """
    actor = accessor.get_actor(actor_id)
    if not actor:
        return False

    if not hasattr(actor, 'states') or actor.states is None:
        actor.states = {}

    actor.states["alignment"] = 0.0
    return True


def get_alignment_effects(alignment_score: float) -> dict:
    """
    Get suggested mechanical effects based on alignment.

    This is a helper function - games can choose to apply these effects or not.

    Args:
        alignment_score: Numeric alignment (-10 to +10)

    Returns:
        Dict with suggested effects

    Example:
        effects = get_alignment_effects(8.0)
        # Returns: {"npc_reaction_bonus": 2, "evil_npc_reaction_penalty": -3, ...}
    """
    category = get_alignment_category(alignment_score)
    abs_score = abs(alignment_score)

    if category == "good":
        return {
            "good_npc_reaction": int(abs_score / 2),  # 0-5 bonus with good NPCs
            "evil_npc_reaction": -int(abs_score / 2),  # 0-5 penalty with evil NPCs
            "holy_power_bonus": int(abs_score / 3),  # 0-3 bonus to holy abilities
            "dark_power_penalty": -int(abs_score / 3)  # 0-3 penalty to dark abilities
        }
    elif category == "evil":
        return {
            "good_npc_reaction": -int(abs_score / 2),  # 0-5 penalty with good NPCs
            "evil_npc_reaction": int(abs_score / 2),  # 0-5 bonus with evil NPCs
            "holy_power_penalty": -int(abs_score / 3),  # 0-3 penalty to holy abilities
            "dark_power_bonus": int(abs_score / 3)  # 0-3 bonus to dark abilities
        }
    else:
        return {
            "good_npc_reaction": 0,
            "evil_npc_reaction": 0,
            "holy_power_bonus": 0,
            "dark_power_bonus": 0
        }
