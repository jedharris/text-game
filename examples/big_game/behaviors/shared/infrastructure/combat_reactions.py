"""Combat Reaction Infrastructure.

Handles entity reactions to combat events (damage taken, attacking, etc).

Supports two modes:
1. Data-driven: Entity properties define combat effects and messages
2. Handler escape hatch: Entity properties specify a Python function to call

Example data-driven config:
    "combat_reactions": {
        "modify_property": {"path": "health", "delta": -10},
        "message": "The golem takes damage...",
        "set_flags": {"combat_initiated": true}
    }

Example handler escape hatch:
    "combat_reactions": {
        "handler": "behaviors.regions.frozen_reaches.golem_puzzle:on_damage"
    }
"""

from typing import Any

from behaviors.shared.infrastructure.reaction_interpreter import process_reaction
from behaviors.shared.infrastructure.reaction_specs import COMBAT_SPEC
from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult

# Vocabulary: wire hooks to events
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "entity_combat",
            "invocation": "entity",
            "description": "Called on combat events"
        }
    ],
    "events": [
        {
            "event": "on_combat",
            "hook": "entity_combat",
            "description": "Handle combat reactions",
        },
    ]
}


def on_combat(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle combat reactions for entities.

    Checks the entity for combat_reactions configuration.
    If config has "handler" key, calls that Python function.
    Otherwise, processes the data-driven config using unified interpreter.

    Args:
        entity: The entity in combat
        accessor: StateAccessor instance
        context: Context with damage, attacker, weapon

    Returns:
        EventResult with combat reaction
    """
    if not hasattr(entity, "properties"):
        return EventResult(allow=True, feedback=None)

    # Check for combat_reactions configuration
    combat_config = entity.properties.get("combat_reactions", {})
    if not combat_config:
        return EventResult(allow=True, feedback=None)

    # Check for handler escape hatch first
    handler_path = combat_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)
        # Handler failed to load - fall through to data-driven

    # Use unified interpreter for data-driven processing
    # NoMatchStrategy - single config object
    return process_reaction(entity, combat_config, accessor, context, COMBAT_SPEC)
