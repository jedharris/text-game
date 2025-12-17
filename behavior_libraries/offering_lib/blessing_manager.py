"""Blessing and curse management for offering-based puzzles.

This module provides functions for applying temporary or permanent effects to actors
based on offerings made to altars, shrines, wells, etc.

Effects are stored in actor.states.effects as a list of effect dictionaries.

NOTE: This is a library behavior pattern that could be useful to migrate to core
if effect-based mechanics become a common pattern across many games.
"""

from typing import Dict, Any, Optional, List

from src.types import ActorId


def apply_blessing(
    accessor: Any,
    actor_id: ActorId,
    blessing_type: str,
    duration: int = -1,
    value: Any = None
) -> bool:
    """
    Apply a blessing (positive effect) to an actor.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of the actor to bless
        blessing_type: Type of blessing (e.g., "strength", "protection", "luck")
        duration: Number of turns effect lasts (-1 for permanent, 0 for instant)
        value: Optional value associated with effect (e.g., +2 strength)

    Returns:
        True if blessing applied, False if actor not found

    Example:
        apply_blessing(accessor, "player", "strength", duration=10, value=2)
    """
    actor = accessor.get_actor(actor_id)
    if not actor:
        return False

    # Initialize states if needed
    if not hasattr(actor, 'states') or actor.states is None:
        actor.states = {}

    # Initialize effects list if needed
    if "effects" not in actor.states:
        actor.states["effects"] = []

    # Create effect dict
    effect = {
        "type": blessing_type,
        "is_blessing": True,
        "duration": duration,
        "value": value
    }

    # Add to effects list
    actor.states["effects"].append(effect)

    return True


def apply_curse(
    accessor: Any,
    actor_id: ActorId,
    curse_type: str,
    duration: int = -1,
    value: Any = None
) -> bool:
    """
    Apply a curse (negative effect) to an actor.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of the actor to curse
        curse_type: Type of curse (e.g., "weakness", "vulnerability", "misfortune")
        duration: Number of turns effect lasts (-1 for permanent, 0 for instant)
        value: Optional value associated with effect (e.g., -2 strength)

    Returns:
        True if curse applied, False if actor not found

    Example:
        apply_curse(accessor, "player", "weakness", duration=5, value=-1)
    """
    actor = accessor.get_actor(actor_id)
    if not actor:
        return False

    # Initialize states if needed
    if not hasattr(actor, 'states') or actor.states is None:
        actor.states = {}

    # Initialize effects list if needed
    if "effects" not in actor.states:
        actor.states["effects"] = []

    # Create effect dict
    effect = {
        "type": curse_type,
        "is_blessing": False,
        "duration": duration,
        "value": value
    }

    # Add to effects list
    actor.states["effects"].append(effect)

    return True


def get_active_effects(accessor: Any, actor_id: ActorId) -> List[Dict]:
    """
    Get all active effects on an actor.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of the actor

    Returns:
        List of effect dicts (empty list if no effects)

    Example:
        effects = get_active_effects(accessor, "player")
        for effect in effects:
            print(f"{effect['type']}: {effect['duration']} turns left")
    """
    actor = accessor.get_actor(actor_id)
    if not actor or not hasattr(actor, 'states') or actor.states is None:
        return []

    return actor.states.get("effects", [])


def has_effect(accessor: Any, actor_id: ActorId, effect_type: str) -> bool:
    """
    Check if actor has a specific effect type.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of the actor
        effect_type: Type of effect to check for

    Returns:
        True if actor has this effect type, False otherwise

    Example:
        if has_effect(accessor, "player", "strength"):
            # Player has strength buff
    """
    effects = get_active_effects(accessor, actor_id)
    return any(effect["type"] == effect_type for effect in effects)


def remove_effect(accessor: Any, actor_id: ActorId, effect_type: str) -> bool:
    """
    Remove a specific effect type from actor.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of the actor
        effect_type: Type of effect to remove

    Returns:
        True if effect was removed, False if not found

    Example:
        remove_effect(accessor, "player", "curse_of_frogs")
    """
    actor = accessor.get_actor(actor_id)
    if not actor or not hasattr(actor, 'states') or actor.states is None:
        return False

    effects = actor.states.get("effects", [])

    # Find and remove first matching effect
    for i, effect in enumerate(effects):
        if effect["type"] == effect_type:
            effects.pop(i)
            return True

    return False


def tick_effects(accessor: Any, actor_id: ActorId) -> List[str]:
    """
    Decrement duration of all temporary effects and remove expired ones.

    This should be called each turn/action to manage effect durations.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of the actor

    Returns:
        List of effect types that expired this tick

    Example:
        expired = tick_effects(accessor, "player")
        if "strength" in expired:
            return "Your strength blessing fades."
    """
    actor = accessor.get_actor(actor_id)
    if not actor or not hasattr(actor, 'states') or actor.states is None:
        return []

    effects = actor.states.get("effects", [])
    expired_effects = []

    # Iterate backwards to safely remove while iterating
    for i in range(len(effects) - 1, -1, -1):
        effect = effects[i]

        # Skip permanent effects (duration = -1) and instant effects (duration = 0)
        if effect["duration"] <= 0:
            continue

        # Decrement duration
        effect["duration"] -= 1

        # Remove if expired
        if effect["duration"] == 0:
            expired_effects.append(effect["type"])
            effects.pop(i)

    return expired_effects


def get_effect_description(effect_type: str, is_blessing: bool = True) -> str:
    """
    Get a narrative description of an effect.

    This is a helper for generating flavor text. Games can override with custom descriptions.

    Args:
        effect_type: Type of effect
        is_blessing: Whether it's a blessing (True) or curse (False)

    Returns:
        Description string

    Example:
        desc = get_effect_description("strength", is_blessing=True)
        # Returns: "You feel stronger!"
    """
    descriptions = {
        # Blessings
        ("strength", True): "You feel stronger!",
        ("protection", True): "A protective aura surrounds you.",
        ("luck", True): "Fortune smiles upon you.",
        ("speed", True): "You feel lighter and faster.",
        ("wisdom", True): "Your mind feels clearer.",
        ("health", True): "Vitality flows through you.",

        # Curses
        ("weakness", False): "You feel drained and weak.",
        ("vulnerability", False): "An ominous chill runs through you.",
        ("misfortune", False): "A sense of doom weighs upon you.",
        ("slowness", False): "Your limbs feel heavy and sluggish.",
        ("confusion", False): "Your thoughts grow muddled.",
        ("sickness", False): "Nausea overwhelms you.",
    }

    # Try to find exact match
    key = (effect_type, is_blessing)
    if key in descriptions:
        return descriptions[key]

    # Generic fallback
    if is_blessing:
        return f"You are blessed with {effect_type}."
    else:
        return f"You are cursed with {effect_type}."
