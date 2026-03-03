"""Entry Reaction Infrastructure.

Handles reactions when actors enter locations.

Example data-driven config:
    "entry_reactions": {
        "message": "The cold hits you immediately...",
        "modify_property": {"path": "extra.cold_exposure", "delta": 1}
    }
"""

from typing import Any

from behaviors.shared.infrastructure.reaction_interpreter import process_reaction
from behaviors.shared.infrastructure.reaction_specs import ENTRY_SPEC
from examples.big_game.game_behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult

vocabulary = {
    "hook_definitions": [{"hook_id": "entity_location_entry", "invocation": "entity"}],
    "events": [{"event": "on_entry", "hook": "entity_location_entry"}]
}


def on_entry(entity: Any, accessor: Any, context: dict[str, Any]) -> EventResult:
    """Handle location entry reactions."""
    if not hasattr(entity, "properties"):
        return EventResult(allow=True, feedback=None)

    entry_config = entity.properties.get("entry_reactions", {})
    if not entry_config:
        return EventResult(allow=True, feedback=None)

    handler_path = entry_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)

    return process_reaction(entity, entry_config, accessor, context, ENTRY_SPEC)
