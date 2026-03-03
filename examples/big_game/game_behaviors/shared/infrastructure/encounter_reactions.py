"""Encounter Reaction Infrastructure.

Handles first-encounter reactions when entering a location with an NPC.

Supports two modes:
1. Data-driven: Entity properties define encounter effects and messages
2. Handler escape hatch: Entity properties specify a Python function to call

Example data-driven config:
    "encounter_reactions": {
        "encounter_message": "A wounded hunter lies against the rocks...",
        "set_flags": {"sira_encountered": true},
        "requires_not_flags": {"sira_encountered": true}
    }

Example handler escape hatch:
    "encounter_reactions": {
        "handler": "behaviors.regions.beast_wilds.sira_rescue:on_sira_encounter"
    }
"""

from typing import Any

from behaviors.shared.infrastructure.reaction_interpreter import process_reaction
from behaviors.shared.infrastructure.reaction_specs import ENCOUNTER_SPEC
from examples.big_game.game_behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult

# Vocabulary: wire hooks to events
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "entity_encounter",
            "invocation": "entity",
            "description": "Called on first encounter with entity"
        }
    ],
    "events": [
        {
            "event": "on_encounter",
            "hook": "entity_encounter",
            "description": "Handle first encounter reactions",
        },
    ]
}


def on_encounter(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle first-encounter reactions for NPCs.

    Checks the entity for encounter_reactions configuration.
    If config has "handler" key, calls that Python function.
    Otherwise, processes the data-driven config using unified interpreter.

    Args:
        entity: The NPC being encountered
        accessor: StateAccessor instance
        context: Context with location, actor_id

    Returns:
        EventResult with encounter reaction
    """
    if not hasattr(entity, "properties"):
        return EventResult(allow=True, feedback=None)

    # Check for encounter_reactions configuration
    encounter_config = entity.properties.get("encounter_reactions", {})
    if not encounter_config:
        return EventResult(allow=True, feedback=None)

    # Check for handler escape hatch first
    handler_path = encounter_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)
        # Handler failed to load - fall through to data-driven

    # Use unified interpreter for data-driven processing
    # NoMatchStrategy - single config object
    return process_reaction(entity, encounter_config, accessor, context, ENCOUNTER_SPEC)
