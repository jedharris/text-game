"""Turn Environmental Reaction Infrastructure.

Handles per-turn environmental effects (cold, spores, predatory fish, etc.).
Checks the player's current location each turn for turn_environmental config.

Supports two modes:
1. Data-driven: Location properties define environmental effects
2. Handler escape hatch: Location properties specify a Python function to call

Example data-driven config (on a location):
    "turn_environmental": {
        "fish_attack": {
            "damage": 8,
            "message": "The predatory fish snap at your legs."
        }
    }

Example handler escape hatch:
    "turn_environmental": {
        "handler": "behaviors.regions.frozen_reaches.hypothermia:on_turn_cold"
    }
"""

from typing import Any

from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult

vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_environmental",
            "invocation": "turn_phase",
            "description": "Called each turn for location-based environmental effects"
        }
    ],
    "events": [
        {
            "event": "on_turn_environmental",
            "hook": "turn_environmental",
            "description": "Handle per-turn environmental effects at player's location"
        }
    ]
}


def on_turn_environmental(
    entity: None,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle per-turn environmental effects at player's current location.

    Looks up the player's location, checks for turn_environmental config,
    and applies effects (damage, messages).

    Args:
        entity: None (turn phase hook)
        accessor: StateAccessor instance
        context: Context with actor_id, turn info

    Returns:
        EventResult with environmental effect messages
    """
    state = accessor.game_state
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    # Find player's current location
    location = next(
        (loc for loc in state.locations if loc.id == player.location), None
    )
    if not location:
        return EventResult(allow=True, feedback=None)

    # Check for turn_environmental configuration
    env_config = location.properties.get("turn_environmental")
    if not env_config:
        return EventResult(allow=True, feedback=None)

    # Check for top-level handler escape hatch
    handler_path = env_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(location, accessor, context)

    # Process each named environmental effect
    messages = []
    for effect_name, effect_config in env_config.items():
        if effect_name == "handler":
            continue
        if not isinstance(effect_config, dict):
            continue

        # Per-effect handler escape hatch
        effect_handler_path = effect_config.get("handler")
        if effect_handler_path:
            handler = load_handler(effect_handler_path)
            if handler:
                result = handler(location, accessor, context)
                if result and result.feedback:
                    messages.append(result.feedback)
                continue

        # Data-driven: apply damage and collect message
        damage = effect_config.get("damage", 0)
        message = effect_config.get("message", "")

        if damage > 0:
            health = player.properties.get("health", 100)
            player.properties["health"] = max(0, health - damage)
            if message:
                messages.append(f"{message} [{damage} damage]")
            else:
                messages.append(f"The environment damages you. [{damage} damage]")
        elif message:
            messages.append(message)

    if messages:
        return EventResult(allow=True, feedback="\n".join(messages))

    return EventResult(allow=True, feedback=None)
