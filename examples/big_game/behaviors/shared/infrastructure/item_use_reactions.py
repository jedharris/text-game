"""Item Use Reaction Infrastructure.

Provides generic handling for entity-specific reactions to items being used.

Supports two modes:
1. Data-driven: Entity properties define accepted items, effects, messages
2. Handler escape hatch: Entity properties specify a Python function to call

Example data-driven config (target entity):
    "item_use_reactions": {
        "healing": {
            "accepted_items": ["silvermoss", "healing_potion"],
            "transition_to": "stabilized",
            "response": "The medicine takes effect...",
            "set_flags": {"patient_healed": true}
        }
    }

Example handler escape hatch:
    "item_use_reactions": {
        "handler": "behaviors.regions.fungal_depths.aldric_rescue:on_aldric_heal"
    }
"""

from typing import Any

from behaviors.shared.infrastructure.reaction_interpreter import process_reaction
from behaviors.shared.infrastructure.reaction_specs import ITEM_USE_SPEC
from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult

# Vocabulary: wire hooks to events
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "entity_item_used",
            "invocation": "entity",
            "description": "Called when an item is used"
        }
    ],
    "events": [
        {
            "event": "on_item_used",
            "hook": "entity_item_used",
            "description": "Handle entity reactions to item use",
        },
    ]
}


def on_item_used(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle entity-specific reactions to item use.

    Checks both the item and target for item_use_reactions configuration.
    If config has "handler" key, calls that Python function.
    Otherwise, processes the data-driven config using unified interpreter.

    Args:
        entity: The item being used
        accessor: StateAccessor instance
        context: Context with target

    Returns:
        EventResult with reaction
    """
    # Ensure item is in context for matching
    if "item" not in context:
        context["item"] = entity

    # Check target entity for reactions first
    target = context.get("target")
    if target and hasattr(target, "properties"):
        target_config = target.properties.get("item_use_reactions", {})
        if target_config:
            # Check for handler escape hatch first
            handler_path = target_config.get("handler")
            if handler_path:
                handler = load_handler(handler_path)
                if handler:
                    return handler(entity, accessor, context)
                # Handler failed to load - fall through to data-driven

            # Use unified interpreter for data-driven processing
            match = ITEM_USE_SPEC.match_strategy.find_match(target_config, context)
            if match:
                reaction_name, reaction_config = match
                return process_reaction(target, reaction_config, accessor, context, ITEM_USE_SPEC)

    # Check item for self-reactions (e.g., using bucket to water)
    if hasattr(entity, "properties"):
        item_config = entity.properties.get("item_use_reactions", {})
        if item_config:
            # Check for handler escape hatch first
            handler_path = item_config.get("handler")
            if handler_path:
                handler = load_handler(handler_path)
                if handler:
                    return handler(entity, accessor, context)
                # Handler failed to load - fall through to data-driven

            # Use unified interpreter for item self-use
            match = ITEM_USE_SPEC.match_strategy.find_match(item_config, context)
            if match:
                reaction_name, reaction_config = match
                return process_reaction(entity, reaction_config, accessor, context, ITEM_USE_SPEC)

    return EventResult(allow=True, feedback=None)
