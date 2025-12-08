"""UC1: Infected Scholar - Custom behaviors for resistance and contagion.

These behaviors demonstrate how game-specific code integrates with library modules.
They are NOT part of the library - they are custom behaviors for the test game.

Custom behaviors needed for UC1:
1. resistance_modifier - Reduce condition severity based on resistances property
2. contagion_spread - Spread conditions with contagious_range to nearby actors

Library modules used:
- conditions.py: apply_condition, has_condition, get_condition
- environment.py: check_spores (applies fungal_infection based on spore_level)
"""

from typing import Optional


def apply_resistance(base_severity: int, resistance_percent: int) -> int:
    """
    Calculate severity after applying resistance.

    Formula: actual = base * (1 - resistance/100)
    Minimum result is 1 (can't fully negate)

    Args:
        base_severity: Original condition severity
        resistance_percent: Resistance percentage (0-100)

    Returns:
        Reduced severity value (minimum 1)
    """
    if resistance_percent <= 0:
        return base_severity
    if resistance_percent >= 100:
        return 1

    reduced = int(base_severity * (1 - resistance_percent / 100))
    return max(1, reduced)


def get_actor_resistance(actor, condition_type: str) -> int:
    """
    Get an actor's resistance to a condition type.

    Checks the resistances dict in actor.properties. The condition_type
    is looked up directly (e.g., "disease" for fungal_infection).

    For UC1, we map fungal_infection to "disease" resistance.

    Args:
        actor: The Actor object
        condition_type: Type of condition (e.g., "disease", "poison")

    Returns:
        Resistance percentage (0-100), or 0 if no resistance
    """
    if not actor:
        return 0

    resistances = actor.properties.get("resistances", {})

    # Map condition names to resistance types
    type_mapping = {
        "fungal_infection": "disease",
        "poison": "poison",
        "disease": "disease",
    }

    resistance_key = type_mapping.get(condition_type, condition_type)
    return resistances.get(resistance_key, 0)


def apply_condition_with_resistance(actor, condition_name: str, condition_data: dict) -> str:
    """
    Apply a condition with resistance calculation.

    This wraps the library's apply_condition to add resistance reduction.
    It reduces the incoming severity by the actor's resistance before applying.

    Args:
        actor: The Actor to apply condition to
        condition_name: Name of the condition
        condition_data: Condition data including severity

    Returns:
        Message describing what happened
    """
    from behaviors.actors.conditions import apply_condition

    # Get resistance
    resistance = get_actor_resistance(actor, condition_name)

    # Apply resistance to severity
    original_severity = condition_data.get("severity", 0)
    if resistance > 0 and original_severity > 0:
        reduced_severity = apply_resistance(original_severity, resistance)
        condition_data = condition_data.copy()
        condition_data["severity"] = reduced_severity

        # Apply and add resistance note to message
        result = apply_condition(actor, condition_name, condition_data)
        if "immune" not in result.lower():
            result += f" (resistance reduced severity from {original_severity} to {reduced_severity})"
        return result

    return apply_condition(actor, condition_name, condition_data)


def check_contagion(source_actor, target_actor, accessor) -> Optional[str]:
    """
    Check if source actor can spread contagious conditions to target.

    For UC1, contagion spreads when:
    - Source has a condition with contagious_range: "touch"
    - Target is in the same location as source
    - Target is focused_on source (interacting closely)

    Args:
        source_actor: Actor with potentially contagious condition
        target_actor: Actor who might catch the condition
        accessor: StateAccessor for queries

    Returns:
        Message if contagion spread, None otherwise
    """
    from behaviors.actors.conditions import get_condition, has_condition

    if not source_actor or not target_actor:
        return None

    # Check if in same location
    if source_actor.location != target_actor.location:
        return None

    # Get all conditions on source
    conditions = source_actor.properties.get("conditions", {})

    messages = []
    for cond_name, cond_data in conditions.items():
        contagious_range = cond_data.get("contagious_range")
        if not contagious_range:
            continue

        # For "touch" range, check if target is focused on source
        if contagious_range == "touch":
            focused_on = target_actor.properties.get("focused_on")
            if focused_on != source_actor.id:
                continue

        # Target already has condition? Skip (will stack via library)
        if has_condition(target_actor, cond_name):
            continue

        # Apply condition to target with resistance
        # Use a reduced severity for contagion (spreading is less severe than direct exposure)
        contagion_severity = max(1, cond_data.get("severity", 0) // 4)
        contagion_data = {
            "severity": contagion_severity,
            "damage_per_turn": cond_data.get("damage_per_turn", 0),
            "progression_rate": cond_data.get("progression_rate", 0),
        }

        msg = apply_condition_with_resistance(target_actor, cond_name, contagion_data)
        if "immune" not in msg.lower():
            messages.append(f"Contagion from {source_actor.name}: {msg}")

    return "\n".join(messages) if messages else None


def on_turn_end_contagion(entity, accessor, context) -> Optional:
    """
    Turn phase handler for contagion spread.

    Called at end of turn to check if any contagious conditions spread.
    This is a custom hook handler for UC1, not part of the core library.

    Args:
        entity: Not used (turn phase has no specific entity)
        accessor: StateAccessor for queries
        context: Context dict

    Returns:
        EventResult if contagion spread, None otherwise
    """
    from src.state_accessor import EventResult

    player = accessor.get_actor("player")
    if not player:
        return None

    all_messages = []

    # Check each NPC for contagion to player
    for actor_id, actor in accessor.game_state.actors.items():
        if actor_id == "player":
            continue

        msg = check_contagion(actor, player, accessor)
        if msg:
            all_messages.append(msg)

    if all_messages:
        return EventResult(allow=True, message="\n".join(all_messages))
    return None


# Vocabulary extension for UC1-specific events
vocabulary = {
    "events": [
        {
            "event": "on_turn_end_contagion",
            "hook": "turn_end",
            "description": "Check for contagion spread at end of turn (UC1 custom behavior)"
        }
    ]
}
