"""Take Reaction Infrastructure.

Handles reactions when items are taken from locations.

Example data-driven config:
    "take_reactions": {
        "message": "The bees become agitated!",
        "set_flags": {"theft_detected": true}
    }
"""

from typing import Any

from behaviors.shared.infrastructure.reaction_interpreter import process_reaction
from behaviors.shared.infrastructure.reaction_specs import TAKE_SPEC
from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult

vocabulary = {
    "hook_definitions": [{"hook_id": "item_taken", "invocation": "entity"}],
    "events": [{"event": "on_take", "hook": "item_taken"}]
}


def on_take(entity: Any, accessor: Any, context: dict[str, Any]) -> EventResult:
    """Handle item take reactions."""
    if not hasattr(entity, "properties"):
        return EventResult(allow=True, feedback=None)

    take_config = entity.properties.get("take_reactions", {})
    if not take_config:
        return EventResult(allow=True, feedback=None)

    handler_path = take_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)

    return process_reaction(entity, take_config, accessor, context, TAKE_SPEC)
