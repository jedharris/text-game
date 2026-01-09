"""Condition Reaction Infrastructure.

Handles NPC reactions to condition changes (status effects).

Supports handler escape hatch where entity properties specify a Python function to call.

Example config:
    "condition_reactions": {
        "bleeding_stopped": {
            "handler": "behaviors.regions.sunken_district.dual_rescue:on_rescue_success"
        }
    }
"""

from typing import Any

from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult

# Vocabulary: wire hooks to events
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "entity_condition_change",
            "invocation": "entity",
            "description": "Called when entity's condition changes"
        }
    ],
    "events": [
        {
            "event": "on_condition_change",
            "hook": "entity_condition_change",
            "description": "Handle condition change reactions",
        },
    ]
}


def on_condition_change(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle condition change reactions for NPCs.

    Checks the entity for condition_reactions configuration.
    Calls the handler function specified for the condition change type.

    Args:
        entity: The NPC whose condition changed
        accessor: StateAccessor instance
        context: Context with condition change data (e.g., condition_type, old_value, new_value)

    Returns:
        EventResult with reaction
    """
    if not hasattr(entity, "properties"):
        return EventResult(allow=True, feedback=None)

    # Check for condition_reactions configuration
    condition_config = entity.properties.get("condition_reactions", {})
    if not condition_config:
        return EventResult(allow=True, feedback=None)

    # Get the specific condition change type from context
    condition_type = context.get("condition_type", "")
    if not condition_type:
        return EventResult(allow=True, feedback=None)

    # Check for handler for this specific condition type
    reaction = condition_config.get(condition_type, {})
    handler_path = reaction.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)

    return EventResult(allow=True, feedback=None)
