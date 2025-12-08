"""Condition system for actor interaction.

Conditions represent temporary or ongoing states that affect actors,
such as poison, bleeding, fear, or entanglement. Conditions can:
- Deal damage over time
- Apply effects that modify behavior
- Progress in severity
- Expire after a duration

Condition data structure:
{
    "severity": int,           # How severe the condition is (0-100 typical)
    "damage_per_turn": int,    # Health damage each turn (optional)
    "duration": int,           # Turns until auto-removal (optional)
    "progression_rate": int,   # Severity increase per turn (optional)
    "effect": str,             # Effect string from effects registry (optional)
    "contagious_range": str,   # "touch", "near", etc. (optional)
}

Usage:
    from behaviors.library.actors.conditions import (
        apply_condition, tick_conditions, treat_condition,
        remove_condition, is_immune, has_condition
    )
"""

from typing import Dict, List, Optional

# Conditions that constructs are inherently immune to
CONSTRUCT_IMMUNITIES = {"disease", "poison"}


def get_conditions(actor) -> Dict[str, dict]:
    """
    Get the conditions dict for an actor.

    Args:
        actor: The Actor object

    Returns:
        Dict of condition_name -> condition_data, or empty dict
    """
    if not actor:
        return {}
    return actor.properties.get("conditions", {})


def has_condition(actor, condition_name: str) -> bool:
    """
    Check if an actor has a specific condition.

    Args:
        actor: The Actor object
        condition_name: Name of the condition to check

    Returns:
        True if actor has the condition
    """
    return condition_name in get_conditions(actor)


def is_immune(actor, condition_name: str) -> bool:
    """
    Check if an actor is immune to a condition.

    Immunity sources:
    1. Explicit immunities array in properties
    2. Construct body form (immune to disease, poison)

    Args:
        actor: The Actor object
        condition_name: Name of the condition

    Returns:
        True if actor is immune to the condition
    """
    if not actor:
        return False

    # Check explicit immunities array
    immunities = actor.properties.get("immunities", [])
    if condition_name in immunities:
        return True

    # Check construct immunity
    body = actor.properties.get("body", {})
    if body.get("form") == "construct":
        if condition_name in CONSTRUCT_IMMUNITIES:
            return True

    return False


def apply_condition(actor, condition_name: str, condition_data: dict) -> str:
    """
    Apply or worsen a condition on an actor.

    If the actor is immune, the condition is not applied.
    If the condition already exists, severity is stacked.

    Args:
        actor: The Actor object
        condition_name: Name of the condition
        condition_data: Dict with condition properties (severity required)

    Returns:
        Message describing what happened
    """
    if not actor:
        return "No target for condition."

    # Check immunity
    if is_immune(actor, condition_name):
        return f"{actor.name} is immune to {condition_name}."

    # Ensure conditions dict exists
    if "conditions" not in actor.properties:
        actor.properties["conditions"] = {}

    conditions = actor.properties["conditions"]

    if condition_name in conditions:
        # Stack severity
        existing = conditions[condition_name]
        new_severity = existing.get("severity", 0) + condition_data.get("severity", 0)
        existing["severity"] = new_severity
        return f"{actor.name}'s {condition_name} worsens (severity {new_severity})."
    else:
        # Apply new condition
        conditions[condition_name] = condition_data.copy()
        severity = condition_data.get("severity", 0)
        return f"{actor.name} is afflicted with {condition_name} (severity {severity})."


def tick_conditions(actor) -> List[str]:
    """
    Progress all conditions on an actor for one turn.

    For each condition:
    - Apply damage_per_turn to health
    - Decrease duration (remove if <= 0)
    - Increase severity by progression_rate

    Args:
        actor: The Actor object

    Returns:
        List of messages describing what happened
    """
    if not actor:
        return []

    conditions = actor.properties.get("conditions", {})
    if not conditions:
        return []

    messages = []
    conditions_to_remove = []

    for condition_name, condition_data in conditions.items():
        # Apply damage
        damage = condition_data.get("damage_per_turn", 0)
        if damage > 0:
            current_health = actor.properties.get("health", 100)
            new_health = current_health - damage
            actor.properties["health"] = new_health
            messages.append(f"{condition_name} deals {damage} damage to {actor.name}.")

        # Decrease duration
        if "duration" in condition_data:
            condition_data["duration"] -= 1
            if condition_data["duration"] <= 0:
                conditions_to_remove.append(condition_name)
                messages.append(f"{actor.name}'s {condition_name} has worn off.")

        # Increase severity by progression rate
        if "progression_rate" in condition_data:
            condition_data["severity"] = (
                condition_data.get("severity", 0) +
                condition_data["progression_rate"]
            )

    # Remove expired conditions
    for condition_name in conditions_to_remove:
        del conditions[condition_name]

    return messages


def treat_condition(actor, condition_name: str, amount: int) -> str:
    """
    Reduce the severity of a condition.

    If severity drops to 0 or below, the condition is removed.

    Args:
        actor: The Actor object
        condition_name: Name of the condition to treat
        amount: Amount to reduce severity by

    Returns:
        Message describing the result
    """
    if not actor:
        return "No target to treat."

    conditions = actor.properties.get("conditions", {})

    if condition_name not in conditions:
        return f"{actor.name} does not have {condition_name}."

    condition = conditions[condition_name]
    new_severity = condition.get("severity", 0) - amount

    if new_severity <= 0:
        del conditions[condition_name]
        return f"{actor.name}'s {condition_name} has been cured!"
    else:
        condition["severity"] = new_severity
        return f"{actor.name}'s {condition_name} is reduced (severity {new_severity})."


def remove_condition(actor, condition_name: str) -> str:
    """
    Completely remove a condition from an actor.

    Args:
        actor: The Actor object
        condition_name: Name of the condition to remove

    Returns:
        Message describing the result
    """
    if not actor:
        return "No target."

    conditions = actor.properties.get("conditions", {})

    if condition_name in conditions:
        del conditions[condition_name]
        return f"{actor.name}'s {condition_name} has been removed."
    else:
        return f"{actor.name} does not have {condition_name}."


def get_condition_severity(actor, condition_name: str) -> int:
    """
    Get the severity of a condition on an actor.

    Args:
        actor: The Actor object
        condition_name: Name of the condition

    Returns:
        Severity value, or 0 if condition not present
    """
    conditions = get_conditions(actor)
    if condition_name in conditions:
        return conditions[condition_name].get("severity", 0)
    return 0


# Vocabulary extension - registers the condition tick event
vocabulary = {
    "events": [
        {
            "event": "on_condition_tick",
            "hook": "condition_tick",
            "description": "Called each turn to progress all conditions on actors. "
                          "Applies damage, decrements duration, increases severity."
        }
    ]
}


def on_condition_tick(entity, accessor, context):
    """
    Turn phase handler for condition progression.

    This is called by the CONDITION_TICK hook after each successful command.
    It ticks conditions on all actors in the game.

    Args:
        entity: Not used (turn phase has no specific entity)
        accessor: StateAccessor for querying actors
        context: Context dict with hook info

    Returns:
        EventResult with combined messages
    """
    from src.state_accessor import EventResult

    all_messages = []

    # Tick conditions on all actors
    for actor_id, actor in accessor.game_state.actors.items():
        messages = tick_conditions(actor)
        all_messages.extend(messages)

    if all_messages:
        return EventResult(allow=True, message="\n".join(all_messages))
    return EventResult(allow=True, message=None)
