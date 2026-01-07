"""Dialog Reaction Infrastructure.

Handles NPC dialog responses based on keywords.

Supports two modes:
1. Data-driven: Entity properties define keyword-based responses
2. Handler escape hatch: Entity properties specify a Python function to call

Example data-driven config:
    "dialog_reactions": {
        "cubs": {
            "keywords": ["cubs", "sick", "help"],
            "requires_state": ["wary", "neutral"],
            "summary": "The bear explains her cubs are sick...",
            "set_flags": {"knows_cubs_sick": true}
        },
        "default_response": "The bear growls warningly."
    }

Example handler escape hatch:
    "dialog_reactions": {
        "handler": "behaviors.regions.meridian_nexus.echo:on_echo_dialog"
    }
"""

from typing import Any

from behaviors.shared.infrastructure.reaction_interpreter import process_reaction
from behaviors.shared.infrastructure.reaction_specs import DIALOG_SPEC
from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult

# Vocabulary: wire hooks to events
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "entity_dialog",
            "invocation": "entity",
            "description": "Called when player talks to entity"
        }
    ],
    "events": [
        {
            "event": "on_dialog",
            "hook": "entity_dialog",
            "description": "Handle dialog reactions",
        },
    ]
}


def on_dialog(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle keyword-based dialog reactions for NPCs.

    Checks the entity for dialog_reactions configuration.
    If config has "handler" key, calls that Python function.
    Otherwise, processes the data-driven config using unified interpreter.

    Args:
        entity: The NPC being talked to
        accessor: StateAccessor instance
        context: Context with keyword, speaker

    Returns:
        EventResult with dialog response
    """
    if not hasattr(entity, "properties"):
        return EventResult(allow=True, feedback=None)

    # Check for dialog_reactions configuration
    dialog_config = entity.properties.get("dialog_reactions", {})
    if not dialog_config:
        return EventResult(allow=True, feedback=None)

    # Check for handler escape hatch first
    handler_path = dialog_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)
        # Handler failed to load - fall through to data-driven

    # Use unified interpreter for data-driven processing
    match = DIALOG_SPEC.match_strategy.find_match(dialog_config, context)
    if not match:
        # No match - return default response if configured
        default_response = dialog_config.get("default_response")
        return EventResult(allow=True, feedback=default_response)

    reaction_name, reaction_config = match
    return process_reaction(entity, reaction_config, accessor, context, DIALOG_SPEC)
