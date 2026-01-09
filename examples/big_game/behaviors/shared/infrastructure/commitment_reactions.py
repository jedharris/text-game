"""Commitment Reaction Infrastructure.

Handles reactions when commitments are fulfilled or abandoned.

Example data-driven config:
    "commitment_reactions": {
        "fulfilled": {
            "message": "The bear nods gratefully...",
            "grant_items": ["bear_claw_charm"],
            "transition_to": "grateful"
        },
        "abandoned": {
            "message": "The bear roars in anguish!",
            "transition_to": "enraged"
        }
    }
"""

from typing import Any

from behaviors.shared.infrastructure.reaction_interpreter import process_reaction
from behaviors.shared.infrastructure.reaction_specs import COMMITMENT_SPEC
from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult

vocabulary = {
    "hook_definitions": [{"hook_id": "entity_commitment_state_change", "invocation": "entity"}],
    "events": [{"event": "on_commitment_change", "hook": "entity_commitment_state_change"}]
}


def on_commitment_change(entity: Any, accessor: Any, context: dict[str, Any]) -> EventResult:
    """Handle commitment state change reactions."""
    if not hasattr(entity, "properties"):
        return EventResult(allow=True, feedback=None)

    commitment_config = entity.properties.get("commitment_reactions", {})
    if not commitment_config:
        return EventResult(allow=True, feedback=None)

    # First try to find a state-specific reaction
    match = COMMITMENT_SPEC.match_strategy.find_match(commitment_config, context)
    if match:
        reaction_name, reaction_config = match

        # Check if this reaction has a custom handler
        handler_path = reaction_config.get("handler")
        if handler_path:
            handler = load_handler(handler_path)
            if handler:
                return handler(entity, accessor, context)

        # Otherwise use data-driven interpreter
        return process_reaction(entity, reaction_config, accessor, context, COMMITMENT_SPEC)

    # Fallback: check for top-level handler (legacy pattern)
    handler_path = commitment_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)

    return EventResult(allow=True, feedback=None)
