"""Effect string registry for actor interaction system.

Effects are strings that describe what a condition does to an actor.
Behaviors can check for effects on an actor and respond accordingly.

Standard effects:
- Movement effects: cannot_move, cannot_swim, slowed
- Combat effects: cannot_attack, agility_reduced, strength_reduced
- Sensory effects: blinded, deafened
- Special effects: paralysis, entangled, knockdown

Usage:
    # Check if actor has an effect
    from behavior_libraries.actor_lib.effects import has_effect
    if has_effect(actor, CANNOT_MOVE):
        return HandlerResult(False, "You can't move while entangled.")

    # Get all effects on an actor
    from behavior_libraries.actor_lib.effects import get_effects
    effects = get_effects(actor)
"""

from typing import List, Optional, Set

# Movement effects
CANNOT_MOVE = "cannot_move"
CANNOT_SWIM = "cannot_swim"
SLOWED = "slowed"

# Combat effects
CANNOT_ATTACK = "cannot_attack"
AGILITY_REDUCED = "agility_reduced"
STRENGTH_REDUCED = "strength_reduced"

# Sensory effects
BLINDED = "blinded"
DEAFENED = "deafened"

# Special effects
PARALYSIS = "paralysis"
ENTANGLED = "entangled"
KNOCKDOWN = "knockdown"

# All registered effects
REGISTERED_EFFECTS: Set[str] = {
    CANNOT_MOVE,
    CANNOT_SWIM,
    SLOWED,
    CANNOT_ATTACK,
    AGILITY_REDUCED,
    STRENGTH_REDUCED,
    BLINDED,
    DEAFENED,
    PARALYSIS,
    ENTANGLED,
    KNOCKDOWN,
}


def is_valid_effect(effect: str) -> bool:
    """
    Check if an effect string is a registered effect.

    Args:
        effect: The effect string to validate

    Returns:
        True if the effect is registered, False otherwise
    """
    return effect in REGISTERED_EFFECTS


def get_effects(actor) -> List[str]:
    """
    Get all active effects on an actor from their conditions.

    Scans all conditions on the actor and collects their effect strings.

    Args:
        actor: The Actor object

    Returns:
        List of effect strings currently active on the actor
    """
    if not actor:
        return []

    conditions = actor.properties.get("conditions", {})
    effects = []

    for condition_data in conditions.values():
        effect = condition_data.get("effect")
        if effect:
            effects.append(effect)

    return effects


def has_effect(actor, effect: str) -> bool:
    """
    Check if an actor has a specific effect from any condition.

    Args:
        actor: The Actor object
        effect: The effect string to check for

    Returns:
        True if any condition on the actor has this effect
    """
    return effect in get_effects(actor)


def validate_condition_effects(conditions: dict) -> Optional[str]:
    """
    Validate that all effects in conditions are registered.

    Used during game state loading to catch invalid effect strings.

    Args:
        conditions: Dict of condition_name -> condition_data

    Returns:
        Error message if invalid effects found, None otherwise
    """
    invalid_effects = []

    for condition_name, condition_data in conditions.items():
        effect = condition_data.get("effect")
        if effect and not is_valid_effect(effect):
            invalid_effects.append(f"{condition_name}: '{effect}'")

    if invalid_effects:
        return f"Invalid effects in conditions: {', '.join(invalid_effects)}"

    return None


# Vocabulary extension - documents effects for game authors
vocabulary = {
    "effects": [
        {
            "effect": CANNOT_MOVE,
            "description": "Actor cannot move to different locations or parts"
        },
        {
            "effect": CANNOT_SWIM,
            "description": "Actor cannot swim through water areas"
        },
        {
            "effect": SLOWED,
            "description": "Actor movement takes extra time"
        },
        {
            "effect": CANNOT_ATTACK,
            "description": "Actor cannot perform attack actions"
        },
        {
            "effect": AGILITY_REDUCED,
            "description": "Actor's agility is impaired (dodge, accuracy)"
        },
        {
            "effect": STRENGTH_REDUCED,
            "description": "Actor's strength is impaired (damage, carry)"
        },
        {
            "effect": BLINDED,
            "description": "Actor cannot see"
        },
        {
            "effect": DEAFENED,
            "description": "Actor cannot hear"
        },
        {
            "effect": PARALYSIS,
            "description": "Actor cannot take any actions"
        },
        {
            "effect": ENTANGLED,
            "description": "Actor is caught and cannot move freely"
        },
        {
            "effect": KNOCKDOWN,
            "description": "Actor is knocked to the ground"
        },
    ]
}
