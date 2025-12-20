"""Turn Phase Dispatcher Infrastructure.

Provides centralized handling for regional turn phase events.
Each region can register turn phase handlers via entity/location properties.

Supports two modes:
1. Data-driven: Location properties define turn_phase_effects
2. Handler escape hatch: Location properties specify a Python function to call

Example data-driven config:
    "turn_phase_effects": {
        "spore_damage": 5,
        "cold_damage": 3,
        "light_decay": true
    }

Example handler escape hatch:
    "turn_phase_effects": {
        "handler": "behaviors.regions.fungal_depths.spore_zones:on_turn_in_spore_zone"
    }
"""
from src.types import ActorId

from typing import Any

from examples.big_game.behaviors.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult

# Vocabulary: wire hooks to events
vocabulary = {
    "events": [
        {
            "event": "on_regional_turn",
            "hook": "turn_phase_regional",
            "description": "Dispatch regional turn phase to configured handlers",
        },
    ]
}


def on_regional_turn(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Dispatch regional turn phase events.

    Checks locations and entities for turn_phase_handlers configuration
    and calls appropriate logic based on current game state.

    This is a dispatcher - actual logic lives in the regional behavior
    modules which export functions that this dispatcher calls.

    Args:
        entity: None (global check)
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with combined messages
    """
    state = accessor.state
    messages: list[str] = []

    # Get player location to determine which region is active
    player = state.actors.get(ActorId("player"))
    if not player:
        return EventResult(allow=True, feedback=None)

    player_loc = player.properties.get("location", "")

    # Check for location-based turn effects
    location = None
    if hasattr(state, "locations"):
        for loc in state.locations:
            if hasattr(loc, "id") and loc.id == player_loc:
                location = loc
                break

    if location and hasattr(location, "properties"):
        turn_config = location.properties.get("turn_phase_effects", {})
        if turn_config:
            # Check for handler escape hatch first
            handler_path = turn_config.get("handler")
            if handler_path:
                handler = load_handler(handler_path)
                if handler:
                    handler_result = handler(location, accessor, context)
                    if handler_result and handler_result.feedback:
                        messages.append(handler_result.feedback)
                # Handler failed or missing - fall through to data-driven
                else:
                    effects_result = _process_turn_effects(turn_config, state, accessor, context)
                    if effects_result and effects_result.feedback:
                        messages.append(effects_result.feedback)
            else:
                effects_result = _process_turn_effects(turn_config, state, accessor, context)
                if effects_result and effects_result.feedback:
                    messages.append(effects_result.feedback)

    # Check player for turn-based conditions (drowning, hypothermia, etc)
    player_conditions = player.properties.get("conditions", [])
    for condition in player_conditions:
        if isinstance(condition, dict):
            cond_type = condition.get("type")
            if cond_type:
                condition_result = _process_condition_turn(cond_type, condition, player, state)
                if condition_result and condition_result.feedback:
                    messages.append(condition_result.feedback)

    if messages:
        return EventResult(allow=True, feedback="\n".join(messages))

    return EventResult(allow=True, feedback=None)


def _process_turn_effects(
    config: dict[str, Any],
    state: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult | None:
    """Process location-based turn phase effects."""
    messages: list[str] = []

    # Light decay
    if config.get("light_decay"):
        # Check for lit mushrooms and decay them
        pass  # Would be implemented based on game state

    # Spore infection
    if config.get("spore_infection"):
        # Apply spore damage based on location spore_level
        pass

    # Temperature effects
    if config.get("cold_damage"):
        # Apply cold damage if player lacks warmth
        pass

    return None


def _process_condition_turn(
    cond_type: str,
    condition: dict[str, Any],
    player: Any,
    state: Any,
) -> EventResult | None:
    """Process player condition turn effects."""
    # Conditions handle their own turn progression
    # This is just a placeholder for the dispatcher pattern
    return None
