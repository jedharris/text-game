"""
Thermal shock combat mechanics for stone golems.

This behavior implements temperature-based damage modifiers when attacking
stone constructs with fire or cold attacks. Alternating heat and cold causes
thermal shock, fracturing the stone for massive damage.

Damage multipliers:
- Fire/cold attack vs neutral golem: 1.0x (20 damage)
- Fire attack vs hot golem: 0.25x (5 damage)
- Cold attack vs cold golem: 0.25x (5 damage)
- Fire attack vs cold golem: 2.0x (40 damage) - THERMAL SHOCK!
- Cold attack vs hot golem: 2.0x (40 damage) - THERMAL SHOCK!

Temperature decays to neutral after 3 turns of not being hit by fire/cold.
"""

from src.behavior_manager import EventResult, IGNORE_EVENT
from typing import Dict, Any


def on_damage(actor, accessor, context: Dict[str, Any]) -> EventResult:
    """
    Modify damage for thermal shock effects on stone golems.

    Called before damage is applied. Can modify the damage value and update
    the target's temperature state based on attack type.

    Args:
        actor: The target being damaged (stone golem)
        accessor: StateAccessor for queries
        context: Dict with 'damage', 'attacker_id', 'attack_type'

    Returns:
        EventResult with modified damage or IGNORE_EVENT if not applicable
    """
    attack_type = context.get("attack_type", "melee")

    # Only process fire/cold attacks
    if attack_type not in ["fire", "cold"]:
        return IGNORE_EVENT

    # Only process if target has temperature_state property (stone golems)
    if "temperature_state" not in actor.properties:
        return IGNORE_EVENT

    # Get current temperature state
    old_temp = actor.properties.get("temperature_state", "neutral")
    base_damage = context.get("damage", 0)

    # Calculate temperature multiplier
    if old_temp == "neutral":
        multiplier = 1.0
        thermal_shock = False
    elif (attack_type == "fire" and old_temp == "hot") or \
         (attack_type == "cold" and old_temp == "cold"):
        # Same temperature: reduced damage
        multiplier = 0.25
        thermal_shock = False
    elif (attack_type == "fire" and old_temp == "cold") or \
         (attack_type == "cold" and old_temp == "hot"):
        # Opposite temperature: THERMAL SHOCK!
        multiplier = 2.0
        thermal_shock = True
    else:
        multiplier = 1.0
        thermal_shock = False

    # Apply multiplier to damage
    modified_damage = int(base_damage * multiplier)

    # Update temperature state
    if attack_type == "fire":
        actor.properties["temperature_state"] = "hot"
    elif attack_type == "cold":
        actor.properties["temperature_state"] = "cold"

    # Reset decay counter
    actor.properties["temperature_counter"] = 3

    # Build feedback message
    feedback_parts = []

    if thermal_shock:
        if attack_type == "fire" and old_temp == "cold":
            feedback_parts.append("The golem's frozen stone cracks violently as searing heat strikes it!")
        elif attack_type == "cold" and old_temp == "hot":
            feedback_parts.append("The golem's superheated stone shatters as freezing cold hits it!")
        feedback_parts.append(f"THERMAL SHOCK! {modified_damage} damage!")
    else:
        if multiplier == 0.25:
            if attack_type == "fire":
                feedback_parts.append("The golem's runes glow even brighter, but the heat is barely effective.")
            else:
                feedback_parts.append("Ice spreads across the already-frozen golem, but does little damage.")
        else:
            if attack_type == "fire":
                feedback_parts.append("The golem's runes flare red-hot as flame strikes it.")
            elif attack_type == "cold":
                feedback_parts.append("Frost spreads across the golem's surface as cold energy strikes it.")

    # Update the damage in the context for combat.on_damage to apply
    context["damage"] = modified_damage

    # Return IGNORE_EVENT with feedback to delegate damage application to combat.on_damage
    # The behavior manager will filter this as ignored but propagate the feedback
    if feedback_parts:
        return EventResult(
            allow=True,
            feedback=" ".join(feedback_parts),
            _ignored=True
        )
    else:
        return IGNORE_EVENT


def on_turn_end(actor, accessor, context: Dict[str, Any]) -> EventResult:
    """
    Handle temperature decay for stone golems.

    Decrements temperature_counter each turn. When it reaches 0, resets
    temperature_state to neutral.

    Args:
        actor: The actor whose turn is ending
        accessor: StateAccessor for queries
        context: Turn context dict

    Returns:
        EventResult with feedback or IGNORE_EVENT
    """
    # Only process if actor has temperature properties
    if "temperature_state" not in actor.properties:
        return IGNORE_EVENT

    temp_state = actor.properties.get("temperature_state", "neutral")
    counter = actor.properties.get("temperature_counter", 0)

    # If already neutral, nothing to do
    if temp_state == "neutral" or counter <= 0:
        return IGNORE_EVENT

    # Decrement counter
    counter -= 1
    actor.properties["temperature_counter"] = counter

    # If counter reached 0, reset to neutral
    if counter == 0:
        actor.properties["temperature_state"] = "neutral"
        return EventResult(
            allow=True,
            feedback=f"{actor.name}'s runes dim to their normal glow as its temperature returns to normal."
        )

    return IGNORE_EVENT
