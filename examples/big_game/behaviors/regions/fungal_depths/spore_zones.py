"""Spore Zone Mechanics for Fungal Depths.

Implements infection progression based on location spore levels.
"""

from typing import Any, Dict, cast

from src.behavior_manager import EventResult
from src.infrastructure_types import ConditionInstance
from src.infrastructure_utils import (
    get_current_turn,
    modify_condition_severity,
)

# Vocabulary: wire hooks to events
# Note: Turn phase events are handled by infrastructure/turn_phase_dispatcher.py
# Note: Movement events are handled by infrastructure/movement_reactions.py
# Locations must have turn_phase_effects and movement_effects configuration
vocabulary: Dict[str, Any] = {
    "events": []
}

# Spore levels and their infection rates
SPORE_RATES = {
    "none": 0,
    "low": 2,
    "medium": 5,
    "high": 10,
}

# Reduced rate when safe path is known
SAFE_PATH_HIGH_RATE = 3


def on_spore_zone_turn(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Apply spore infection based on current location.

    Each turn in a spore zone increases infection severity
    based on zone level and equipment/knowledge.

    Args:
        entity: None (regional check)
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with infection message if applicable
    """
    state = accessor.state

    # Get player location
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    player_loc = player.properties.get("location")
    if not player_loc:
        return EventResult(allow=True, feedback=None)

    # Get location spore level
    location = None
    for loc in getattr(state, "locations", []):
        if hasattr(loc, "id") and loc.id == player_loc:
            location = loc
            break

    if not location:
        return EventResult(allow=True, feedback=None)

    spore_level = location.properties.get("spore_level", "none")
    if spore_level == "none":
        return EventResult(allow=True, feedback=None)

    # Calculate infection rate
    base_rate = SPORE_RATES.get(spore_level, 0)
    if base_rate == 0:
        return EventResult(allow=True, feedback=None)

    # Check for safe path knowledge (reduces high spore rate)
    if spore_level == "high" and state.extra.get("safe_path_known"):
        base_rate = SAFE_PATH_HIGH_RATE

    # Check for breathing mask (full protection)
    if _has_breathing_mask(player):
        return EventResult(allow=True, feedback=None)

    # Check for spore resistance skill (50% reduction)
    if player.properties.get("skills", {}).get("spore_resistance"):
        base_rate = base_rate // 2

    # Apply infection
    conditions = player.properties.get("conditions", [])
    infection = None
    for cond in conditions:
        if cond.get("type") == "fungal_infection":
            infection = cond
            break

    if not infection:
        # Create new infection
        infection = {
            "type": "fungal_infection",
            "severity": 0,
            "acquired_turn": get_current_turn(state),
        }
        conditions.append(infection)
        player.properties["conditions"] = conditions

    # Increase severity
    old_severity = infection.get("severity", 0)
    new_severity = modify_condition_severity(cast(ConditionInstance, infection), base_rate)

    # Generate appropriate message
    if new_severity >= 80:
        msg = "The infection is critical. You can barely move."
    elif new_severity >= 60:
        msg = "Every breath is a struggle against the spores."
    elif new_severity >= 40:
        msg = "Fungal patches spread across your skin."
    elif new_severity >= 20:
        msg = "You cough as spores irritate your lungs."
    else:
        msg = None

    return EventResult(allow=True, feedback=msg)


def on_enter_spore_zone(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Warn player about spore level when entering a zone.

    Args:
        entity: The player entity
        accessor: StateAccessor instance
        context: Context with destination

    Returns:
        EventResult with zone warning
    """
    destination = context.get("destination")
    if not destination:
        return EventResult(allow=True, feedback=None)

    dest_props = destination.properties if hasattr(destination, "properties") else {}
    spore_level = dest_props.get("spore_level", "none")

    if spore_level == "none":
        return EventResult(allow=True, feedback=None)

    state = accessor.state
    player = state.actors.get("player")

    # Check equipment
    has_mask = _has_breathing_mask(player) if player else False

    if has_mask:
        if spore_level == "high":
            return EventResult(
                allow=True,
                feedback="Your mask filters the thick spores filling this chamber.",
            )
        return EventResult(allow=True, feedback=None)

    # No mask - warn based on level
    if spore_level == "high":
        safe_known = state.extra.get("safe_path_known", False)
        if safe_known:
            return EventResult(
                allow=True,
                feedback=(
                    "Thick spores fill the air, but you know where the "
                    "clean air pockets are."
                ),
            )
        return EventResult(
            allow=True,
            feedback=(
                "The air is thick with golden spores. Each breath brings "
                "the infection closer to your lungs."
            ),
        )

    if spore_level == "medium":
        return EventResult(
            allow=True,
            feedback="Spores drift lazily in the bioluminescent light.",
        )

    return EventResult(allow=True, feedback=None)


def _has_breathing_mask(player: Any) -> bool:
    """Check if player has breathing mask equipped."""
    if not player:
        return False
    equipment = player.properties.get("equipment", {})
    return "breathing_mask" in equipment.get("face", "") or \
           "breathing_mask" in str(player.properties.get("inventory", []))
