"""Hypothermia System for Frozen Reaches.

Implements cold damage based on temperature zones
and mitigation via gear, salamanders, or hot springs.
"""

from typing import Any, Dict

from behavior_libraries.actor_lib.conditions import (
    apply_condition,
    get_condition,
    MAX_SEVERITY,
)
from src.behavior_manager import EventResult
from src.infrastructure_utils import get_current_turn

# Vocabulary: wire hooks to events
vocabulary: Dict[str, Any] = {
    "hook_definitions": [
        {
            "hook_id": "turn_hypothermia",
            "invocation": "turn_phase",
            "before": ["turn_condition_tick"],
            "description": "Apply hypothermia based on location temperature"
        }
    ],
    "events": [
        {
            "event": "on_cold_zone_turn",
            "hook": "turn_hypothermia",
            "description": "Check player location and apply hypothermia (and cure at hot springs)"
        }
    ],
    # Add adjectives for multi-word item names
    "adjectives": [
        {"word": "cold", "synonyms": []},
        {"word": "weather", "synonyms": []},
        {"word": "preserved", "synonyms": []},
        {"word": "partial", "synonyms": []},
    ]
}

# Temperature zones and their hypothermia rates
COLD_RATES = {
    "warm": 0,        # Normal/warm - no hypothermia
    "cold": 5,        # Cold zones
    "freezing": 10,   # Freezing zones
    "extreme": 20,    # Extreme cold (observatory)
}

# Gear effects
GEAR_COLD_REDUCTION = 0.5       # Cold weather gear: 50% reduction
CLOAK_COLD_IMMUNITY = True      # Cloak: full cold immunity
CLOAK_FREEZING_REDUCTION = 0.5  # Cloak: 50% in freezing/extreme
SALAMANDER_IMMUNITY = True      # Salamander companion: full immunity


def on_cold_zone_turn(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Apply hypothermia based on current location temperature.

    Each turn in a cold zone increases hypothermia based on
    zone severity and equipment/companion protection.

    Args:
        entity: None (regional check)
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with hypothermia message if applicable
    """
    state = accessor.game_state

    # Get player location
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    player_loc = player.location
    if not player_loc:
        return EventResult(allow=True, feedback=None)

    # Get location temperature
    location = None
    for loc in getattr(state, "locations", []):
        if hasattr(loc, "id") and loc.id == player_loc:
            location = loc
            break

    if not location:
        return EventResult(allow=True, feedback=None)

    temp_zone = location.properties.get("temperature", "normal")
    base_rate = COLD_RATES.get(temp_zone, 0)

    # Hot springs provides instant cure
    if temp_zone == "warm" and "hot_springs" in str(player_loc).lower():
        hypothermia = get_condition(player, "hypothermia")
        if hypothermia and hypothermia.get("severity", 0) > 0:
            hypothermia["severity"] = 0
            return EventResult(
                allow=True,
                feedback=(
                    "The warmth of the hot springs washes over you like an embrace. "
                    "The cold drains from your body, your limbs tingling as feeling returns. "
                    "You are fully restored."
                ),
            )
        return EventResult(allow=True, feedback=None)

    if base_rate == 0:
        return EventResult(allow=True, feedback=None)

    # Check for salamander companion (full immunity)
    companions = player.properties.get("companions", [])
    for comp in companions:
        comp_id = comp.get("id", "") if isinstance(comp, dict) else str(comp)
        if "salamander" in comp_id.lower():
            return EventResult(allow=True, feedback=None)

    # Check for cold resistance cloak
    equipment = player.properties.get("equipment", {})
    has_cloak = "cold_resistance_cloak" in str(equipment)

    if has_cloak:
        if temp_zone == "cold":
            return EventResult(allow=True, feedback=None)  # Full immunity
        else:
            base_rate = int(base_rate * CLOAK_FREEZING_REDUCTION)

    # Check for cold weather gear (50% reduction) - must be equipped
    if "cold_weather_gear" in str(equipment):
        base_rate = int(base_rate * GEAR_COLD_REDUCTION)

    if base_rate == 0:
        return EventResult(allow=True, feedback=None)

    # Apply hypothermia using conditions library
    hypothermia = get_condition(player, "hypothermia")

    if not hypothermia:
        apply_condition(player, "hypothermia", {
            "severity": 0,
            "acquired_turn": get_current_turn(state),
        })
        hypothermia = get_condition(player, "hypothermia")
        assert hypothermia is not None  # Just created, must exist

    # Increase severity
    old_severity = hypothermia.get("severity", 0)
    new_severity = min(MAX_SEVERITY, old_severity + base_rate)
    hypothermia["severity"] = new_severity

    # Generate message based on severity
    if new_severity >= 80:
        msg = "Your limbs are numb. You're freezing to death."
    elif new_severity >= 60:
        msg = "Violent shivers wrack your body. You must find warmth."
    elif new_severity >= 40:
        msg = "The cold seeps into your bones."
    elif new_severity >= 20:
        msg = "You're getting cold."
    else:
        msg = None

    return EventResult(allow=True, feedback=msg)


def on_enter_hot_springs(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Cure hypothermia instantly when entering hot springs.

    The hot springs provide instant full cure of hypothermia
    and serve as a sanctuary for planning.

    Args:
        entity: The player entity
        accessor: StateAccessor instance
        context: Context with destination

    Returns:
        EventResult with cure message
    """
    destination = context.get("destination")
    if not destination:
        return EventResult(allow=True, feedback=None)

    dest_id = destination.id if hasattr(destination, "id") else str(destination)
    if "hot_springs" not in dest_id.lower():
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    # Check for hypothermia using conditions library
    hypothermia = get_condition(player, "hypothermia")

    if not hypothermia or hypothermia.get("severity", 0) == 0:
        return EventResult(
            allow=True,
            feedback="Warmth envelops you as you enter the hot springs refuge.",
        )

    # Instant cure
    hypothermia["severity"] = 0

    return EventResult(
        allow=True,
        feedback=(
            "The warmth of the hot springs washes over you like an embrace. "
            "The cold drains from your body, your limbs tingling as feeling returns. "
            "You are fully restored."
        ),
    )
