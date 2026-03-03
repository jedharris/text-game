"""Gift Reaction Infrastructure.

Provides generic handling for entity-specific reactions to receiving gifts.

Supports two modes:
1. Data-driven: Entity properties define accepted items, trust changes, messages
2. Handler escape hatch: Entity properties specify a Python function to call

Example data-driven config:
    "gift_reactions": {
        "food": {
            "accepted_items": ["venison", "meat", "rabbit"],
            "trust_delta": 1,
            "trust_transitions": {"3": "friendly"},
            "accept_message": "The wolf accepts the {item}...",
            "set_flags": {"wolf_fed": true}
        },
        "reject_message": "The wolf ignores the offering."
    }

Example handler escape hatch:
    "gift_reactions": {
        "handler": "behaviors.regions.beast_wilds.bee_queen:on_flower_offer"
    }
"""

from typing import Any

from behaviors.shared.infrastructure.reaction_interpreter import process_reaction
from behaviors.shared.infrastructure.reaction_specs import GIFT_SPEC
from examples.big_game.game_behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult

# Vocabulary: wire hooks to events
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "entity_gift_given",
            "invocation": "entity",
            "description": "Called when an item is given to an entity"
        }
    ],
    "events": [
        {
            "event": "on_gift_given",
            "hook": "entity_gift_given",
            "description": "Handle entity reactions to receiving gifts",
        },
    ]
}


def on_gift_given(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle entity-specific reactions to receiving gifts.

    Checks the target entity for gift_reactions configuration.
    If config has "handler" key, calls that Python function.
    Otherwise, processes the data-driven config using unified interpreter.

    Args:
        entity: The item being given
        accessor: StateAccessor instance
        context: Context with target_actor, item

    Returns:
        EventResult with gift reaction
    """
    target = context.get("target_actor")
    if not target:
        return EventResult(allow=True, feedback=None)

    if not hasattr(target, "properties"):
        return EventResult(allow=True, feedback=None)

    # Check for gift_reactions configuration
    gift_config = target.properties.get("gift_reactions", {})
    if not gift_config:
        return EventResult(allow=True, feedback=None)

    # Check for handler escape hatch first
    handler_path = gift_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)
        # Handler failed to load - fall through to data-driven

    # Use unified interpreter for data-driven processing
    match = GIFT_SPEC.match_strategy.find_match(gift_config, context)
    if not match:
        # No match - return reject message if configured
        reject_message = gift_config.get("reject_message")
        return EventResult(allow=True, feedback=reject_message)

    reaction_name, reaction_config = match
    return process_reaction(target, reaction_config, accessor, context, GIFT_SPEC)
