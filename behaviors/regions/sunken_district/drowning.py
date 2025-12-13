"""Drowning System for Sunken District.

Implements held-breath mechanics and water hazards.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import get_current_turn

# Vocabulary: wire hooks to events
# Note: Turn phase events are handled by infrastructure/turn_phase_dispatcher.py
# Note: Movement events are handled by infrastructure/movement_reactions.py
# Locations must have turn_phase_effects and movement_effects configuration
vocabulary: Dict[str, Any] = {
    "events": []
}

# Drowning parameters
MAX_BREATH = 12
WARNING_BREATH = 8
CRITICAL_BREATH = 10
DROWN_DAMAGE = 20


def on_underwater_turn(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Apply drowning damage while underwater.

    Players have limited breath; exceeding it causes damage.

    Args:
        entity: None (regional check)
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with drowning message if applicable
    """
    state = accessor.state
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, message=None)

    # Check if underwater
    if not player.properties.get("underwater"):
        return EventResult(allow=True, message=None)

    # Check for breathing equipment
    equipment = player.properties.get("equipment", {})
    if "breathing" in str(equipment) or "gill" in str(equipment).lower():
        return EventResult(allow=True, message=None)

    # Get/create breath condition
    conditions = player.properties.get("conditions", [])
    breath = None
    for cond in conditions:
        if cond.get("type") == "held_breath":
            breath = cond
            break

    if not breath:
        breath = {
            "type": "held_breath",
            "current": 0,
            "max": MAX_BREATH,
        }
        conditions.append(breath)
        player.properties["conditions"] = conditions

    # Increment breath counter
    current = breath.get("current", 0) + 1
    breath["current"] = current

    # Check status
    if current >= MAX_BREATH:
        # Apply drowning damage
        health = player.properties.get("health", 100)
        player.properties["health"] = max(0, health - DROWN_DAMAGE)
        return EventResult(
            allow=True,
            message=(
                f"You're drowning! [{DROWN_DAMAGE} damage] "
                "Your lungs scream for air. You must surface NOW."
            ),
        )

    if current >= CRITICAL_BREATH:
        return EventResult(
            allow=True,
            message="You're suffocating! Find air immediately!",
        )

    if current >= WARNING_BREATH:
        return EventResult(
            allow=True,
            message="Your lungs are burning. You need air soon.",
        )

    return EventResult(allow=True, message=None)


def on_water_entry(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Start breath timer when entering flooded area.

    Args:
        entity: The player
        accessor: StateAccessor instance
        context: Context with destination

    Returns:
        EventResult with water entry message
    """
    destination = context.get("destination")
    if not destination:
        return EventResult(allow=True, message=None)

    dest_props = destination.properties if hasattr(destination, "properties") else {}
    water_level = dest_props.get("water_level", "none")

    if water_level not in ["submerged", "flooded"]:
        return EventResult(allow=True, message=None)

    state = accessor.state
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, message=None)

    player.properties["underwater"] = True

    # Check for breathing equipment
    equipment = player.properties.get("equipment", {})
    if "breathing" in str(equipment):
        return EventResult(
            allow=True,
            message="You enter the flooded passage. Your breathing mask keeps you safe.",
        )

    return EventResult(
        allow=True,
        message=(
            f"You plunge into the flooded passage. Hold your breath! "
            f"You have {MAX_BREATH} turns of air."
        ),
    )


def on_surface(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Reset breath timer when reaching surface.

    Args:
        entity: The player
        accessor: StateAccessor instance
        context: Context with destination

    Returns:
        EventResult with surfacing message
    """
    destination = context.get("destination")
    if not destination:
        return EventResult(allow=True, message=None)

    dest_props = destination.properties if hasattr(destination, "properties") else {}
    water_level = dest_props.get("water_level", "none")

    if water_level in ["submerged", "flooded"]:
        return EventResult(allow=True, message=None)

    state = accessor.state
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, message=None)

    # Check if was underwater
    if not player.properties.get("underwater"):
        return EventResult(allow=True, message=None)

    player.properties["underwater"] = False

    # Reset breath
    conditions = player.properties.get("conditions", [])
    for cond in conditions:
        if cond.get("type") == "held_breath":
            cond["current"] = 0
            break

    return EventResult(
        allow=True,
        message="You break the surface, gasping for air. Sweet oxygen fills your lungs.",
    )
