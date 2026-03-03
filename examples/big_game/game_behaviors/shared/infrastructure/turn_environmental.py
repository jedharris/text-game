"""Turn Environmental Reaction Infrastructure.

Handles per-turn environmental effects (cold, spores, water, etc.).

Supports two modes:
1. Data-driven: Location properties define environmental conditions
2. Handler escape hatch: Location properties specify a Python function to call

Example data-driven config:
    "turn_environmental": {
        "cold_damage": {
            "condition_check": "cold",
            "damage": 5,
            "message": "The freezing air saps your strength."
        }
    }

Example handler escape hatch:
    "turn_environmental": {
        "handler": "behaviors.regions.frozen_reaches.hypothermia:on_turn_cold"
    }
"""

from typing import Any

from behaviors.shared.infrastructure.reaction_interpreter import process_reaction
from behaviors.shared.infrastructure.reaction_specs import TURN_ENV_SPEC
from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult

vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_environmental",
            "invocation": "turn_phase",
            "description": "Called each turn for environmental effects"
        }
    ],
    "events": [
        {
            "event": "on_turn_environmental",
            "hook": "turn_environmental",
            "description": "Handle per-turn environmental effects"
        }
    ]
}


def on_turn_environmental(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle per-turn environmental effects.

    Checks location for turn_environmental configuration.
    If config has "handler" key, calls that Python function.
    Otherwise, processes the data-driven config using unified interpreter.

    Args:
        entity: The location with environmental effects
        accessor: StateAccessor instance
        context: Context with actor_id, turn info

    Returns:
        EventResult with environmental effect messages
    """
    if not hasattr(entity, "properties"):
        return EventResult(allow=True, feedback=None)

    # Check for turn_environmental configuration
    env_config = entity.properties.get("turn_environmental", {})
    if not env_config:
        return EventResult(allow=True, feedback=None)

    # Check for handler escape hatch first
    handler_path = env_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)
        # Handler failed to load - fall through to data-driven

    # Use unified interpreter for data-driven processing
    return process_reaction(entity, env_config, accessor, context, TURN_ENV_SPEC)
