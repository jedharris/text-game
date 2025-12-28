"""Environmental effects system for actor interaction.

Handles environmental hazards that affect actors based on their location part:
- Breath/drowning in non-breathable areas (underwater, toxic gas)
- Spore exposure causing fungal infection
- Temperature extremes causing hypothermia or burning

Environmental properties are defined on Parts, not Locations. This allows
different areas within the same location to have different hazards.

Part environmental properties:
{
    "breathable": bool,            # Whether actors can breathe here
    "breathing_item_works": bool,  # Whether breathing items help (default True)
    "spore_level": str,            # "none", "low", "medium", "high"
    "temperature": str,            # "normal", "freezing", "burning"
}

Actor environmental properties:
{
    "breath": int,                 # Current breath (0-max_breath)
    "max_breath": int,             # Maximum breath capacity (default 60)
}

Usage:
    from behavior_libraries.actor_lib.environment import (
        apply_environmental_effects, check_breath, check_spores,
        check_temperature, needs_breath
    )
"""

from typing import Dict, List, Optional

from src.state_accessor import IGNORE_EVENT

# Default breath values
DEFAULT_MAX_BREATH = 60
BREATH_DECREASE_PER_TURN = 10
DROWNING_DAMAGE = 10

# Spore level to severity mapping
SPORE_LEVEL_SEVERITY: Dict[str, int] = {
    "none": 0,
    "low": 5,
    "medium": 15,
    "high": 30,
}

# Temperature to condition mapping
TEMPERATURE_CONDITIONS: Dict[str, str] = {
    "freezing": "hypothermia",
    "burning": "burning",
}

# Temperature condition severities
TEMPERATURE_SEVERITY: Dict[str, int] = {
    "freezing": 20,
    "burning": 25,
}


def needs_breath(actor) -> bool:
    """
    Check if an actor needs to breathe.

    Constructs (golems, automatons) don't need to breathe.

    Args:
        actor: The Actor object

    Returns:
        True if actor needs to breathe, False otherwise
    """
    if not actor:
        return False

    body = actor.properties.get("body", {})
    if body.get("form") == "construct":
        return False

    return True


def _has_breathing_item(actor, accessor=None) -> bool:
    """
    Check if actor has an item that provides breathing.

    Args:
        actor: The Actor object
        accessor: Optional StateAccessor for looking up items

    Returns:
        True if actor has a provides_breathing item
    """
    if not accessor or not actor:
        return False

    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item and item.properties.get("provides_breathing"):
            return True

    return False


def check_breath(actor, part, accessor=None):
    """
    Check and update breath for an actor in a part.

    - If part is breathable: restore breath to max
    - If not breathable: decrease breath by 10
    - If breath <= 0: apply 10 drowning damage

    Special cases:
    - If actor has item with provides_breathing=true AND part allows it: don't decrease
    - Constructs don't need to breathe

    Args:
        actor: The Actor object
        part: The Part the actor is in
        accessor: Optional StateAccessor for looking up items

    Returns:
        Message describing what happened, or None if nothing notable
    """
    if not actor or not part:
        return IGNORE_EVENT

    # Constructs don't need to breathe
    if not needs_breath(actor):
        return IGNORE_EVENT

    # Initialize breath if not present
    if "breath" not in actor.properties:
        actor.properties["breath"] = actor.properties.get("max_breath", DEFAULT_MAX_BREATH)
    if "max_breath" not in actor.properties:
        actor.properties["max_breath"] = DEFAULT_MAX_BREATH

    breathable = part.properties.get("breathable", True)

    if breathable:
        # Restore breath to max
        old_breath = actor.properties["breath"]
        max_breath = actor.properties["max_breath"]
        actor.properties["breath"] = max_breath
        return IGNORE_EVENT  # No message for normal breathing

    # Non-breathable area - check for breathing items
    if _has_breathing_item(actor, accessor):
        # Check if part allows breathing items
        if part.properties.get("breathing_item_works", True):
            return IGNORE_EVENT  # Breathing item protects

    # Decrease breath
    actor.properties["breath"] -= BREATH_DECREASE_PER_TURN

    if actor.properties["breath"] <= 0:
        # Apply drowning damage
        current_health = actor.properties.get("health", 100)
        actor.properties["health"] = current_health - DROWNING_DAMAGE
        return f"{actor.name} is drowning! (-{DROWNING_DAMAGE} health)"

    return f"{actor.name}'s breath is running low ({actor.properties['breath']} remaining)."


def check_spores(actor, part):
    """
    Check spore exposure for an actor in a part.

    Spore levels apply/increase fungal_infection:
    - "none": No effect
    - "low": +5 severity
    - "medium": +15 severity
    - "high": +30 severity

    Constructs are immune to spores.

    Args:
        actor: The Actor object
        part: The Part the actor is in

    Returns:
        Message describing what happened, or None if no effect
    """
    if not actor or not part:
        return IGNORE_EVENT

    # Constructs are immune
    body = actor.properties.get("body", {})
    if body.get("form") == "construct":
        return IGNORE_EVENT

    spore_level = part.properties.get("spore_level", "none")
    severity = SPORE_LEVEL_SEVERITY.get(spore_level, 0)

    if severity == 0:
        return IGNORE_EVENT

    # Apply or increase fungal_infection
    if "conditions" not in actor.properties:
        actor.properties["conditions"] = {}

    conditions = actor.properties["conditions"]

    if "fungal_infection" in conditions:
        # Stack severity
        conditions["fungal_infection"]["severity"] += severity
        new_severity = conditions["fungal_infection"]["severity"]
        return f"{actor.name}'s fungal infection worsens from spore exposure (severity {new_severity})."
    else:
        # New infection
        conditions["fungal_infection"] = {
            "severity": severity,
            "progression_rate": 2,  # Slowly gets worse on its own
        }
        return f"{actor.name} is exposed to spores and contracts a fungal infection (severity {severity})."


def check_temperature(actor, part):
    """
    Check temperature effects for an actor in a part.

    Temperature effects:
    - "normal": No effect
    - "freezing": Applies hypothermia condition
    - "burning": Applies burning condition

    Constructs are immune to temperature effects.

    Args:
        actor: The Actor object
        part: The Part the actor is in

    Returns:
        Message describing what happened, or None if no effect
    """
    if not actor or not part:
        return IGNORE_EVENT

    # Constructs are immune
    body = actor.properties.get("body", {})
    if body.get("form") == "construct":
        return IGNORE_EVENT

    temperature = part.properties.get("temperature")

    if not temperature or temperature == "normal":
        return IGNORE_EVENT

    condition_name = TEMPERATURE_CONDITIONS.get(temperature)
    if not condition_name:
        return IGNORE_EVENT

    severity = TEMPERATURE_SEVERITY.get(temperature, 20)

    # Apply or increase temperature condition
    if "conditions" not in actor.properties:
        actor.properties["conditions"] = {}

    conditions = actor.properties["conditions"]

    if condition_name in conditions:
        # Stack severity
        conditions[condition_name]["severity"] += severity
        new_severity = conditions[condition_name]["severity"]
        return f"{actor.name}'s {condition_name} worsens (severity {new_severity})."
    else:
        # New condition
        conditions[condition_name] = {
            "severity": severity,
            "damage_per_turn": 3,  # Temperature conditions deal damage
        }
        return f"{actor.name} suffers from {condition_name} (severity {severity})."


def apply_environmental_effects(actor, part, accessor=None) -> List[str]:
    """
    Apply all environmental effects from a part to an actor.

    Called during environmental effects phase for all actors.
    Checks:
    - breathable: Update breath, apply drowning if depleted
    - spore_level: Apply/increase fungal_infection
    - temperature: Apply temperature conditions

    Args:
        actor: The Actor object
        part: The Part the actor is in
        accessor: Optional StateAccessor for looking up items

    Returns:
        List of messages describing what happened
    """
    if not actor or not part:
        return []

    messages = []

    # Check breath
    breath_msg = check_breath(actor, part, accessor)
    if breath_msg and not getattr(breath_msg, '_ignored', False):
        messages.append(breath_msg)

    # Check spores
    spore_msg = check_spores(actor, part)
    if spore_msg and not getattr(spore_msg, '_ignored', False):
        messages.append(spore_msg)

    # Check temperature
    temp_msg = check_temperature(actor, part)
    if temp_msg and not getattr(temp_msg, '_ignored', False):
        messages.append(temp_msg)

    return messages


def on_environmental_effect(entity, accessor, context):
    """
    Turn phase handler for environmental effects.

    This is called by the ENVIRONMENTAL_EFFECT hook after each successful command.
    It applies environmental effects to all actors based on their current part.

    Args:
        entity: Not used (turn phase has no specific entity)
        accessor: StateAccessor for querying actors and parts
        context: Context dict with hook info

    Returns:
        EventResult with combined messages
    """
    from src.state_accessor import EventResult

    all_messages = []

    # Apply environmental effects to all actors
    for actor_id, actor in accessor.game_state.actors.items():
        # Get the part the actor is in
        part = accessor.get_actor_part(actor)

        if not part:
            # Actor not in a spatial location, skip
            continue

        messages = apply_environmental_effects(actor, part, accessor)
        all_messages.extend(messages)

    if all_messages:
        return EventResult(allow=True, feedback="\n".join(all_messages))
    return EventResult(allow=True, feedback=None)


def on_enter_part(entity, accessor, context):
    """
    Called when an actor enters a new part.

    This event fires when an actor moves to a different part within a location
    or enters a new location. Game-specific behaviors can use this for:
    - Activation triggers (golems activating when player enters center)
    - Alert propagation (spiders alerted when player enters webbed area)
    - Immediate environmental effects

    Args:
        entity: The Actor entering the part
        accessor: StateAccessor for state queries
        context: Context dict with:
            - from_part_id: Optional[str] - previous part ID (None if entering location)
            - to_part_id: str - new part ID

    Returns:
        EventResult if the behavior wants to add a message, IGNORE_EVENT otherwise
    """
    # Base implementation does nothing - game behaviors can override
    # by registering their own on_enter_part handlers on actors or parts
    return IGNORE_EVENT


# Vocabulary extension - registers environmental events
vocabulary = {
    "events": [
        {
            "event": "on_environmental_effect",
            "hook": "environmental_effect",
            "description": "Called each turn to apply environmental effects to all actors. "
                          "Checks breath, spores, temperature, and other environmental hazards."
        },
        {
            "event": "on_enter_part",
            "description": "Called when an actor enters a new location part. "
                          "Useful for activation triggers, alerts, and immediate effects."
        }
    ]
}
