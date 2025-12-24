"""Item Use Reaction Infrastructure.

Provides generic handling for entity-specific reactions to items being used.

Supports two modes:
1. Data-driven: Entity properties define accepted items, effects, messages
2. Handler escape hatch: Entity properties specify a Python function to call

Example data-driven config:
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

from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult
from src.infrastructure_utils import (
    modify_trust,
    transition_state,
)

# Vocabulary: wire hooks to events
vocabulary = {
    "events": [
        {
            "event": "on_item_used",
            "hook": "after_item_use",
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
    Otherwise, processes the data-driven config.

    Args:
        entity: The item being used
        accessor: StateAccessor instance
        context: Context with target

    Returns:
        EventResult with reaction
    """
    item_id = entity.id if hasattr(entity, "id") else str(entity)
    item_lower = item_id.lower()

    state = accessor.game_state

    # Check target entity for reactions
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

            # Data-driven processing
            result = _check_target_reactions(target, item_lower, accessor, context)
            if result and result.feedback:
                return result

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

            result = _process_item_use(entity, item_config, accessor, context)
            if result and result.feedback:
                return result

    return EventResult(allow=True, feedback=None)


def _check_target_reactions(
    target: Any,
    item_lower: str,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult | None:
    """Check target entity for item use reactions (data-driven mode)."""
    target_config = target.properties.get("item_use_reactions", {})
    if not target_config:
        return None

    state = accessor.game_state

    # Find matching reaction
    for reaction_name, reaction_config in target_config.items():
        if reaction_name in ("handler", "_metadata"):
            continue  # Skip special keys

        if not isinstance(reaction_config, dict):
            continue

        accepted_items = reaction_config.get("accepted_items", [])
        if not any(item.lower() in item_lower for item in accepted_items):
            continue

        # Check conditions
        required_flags = reaction_config.get("requires_flags", {})
        if not all(state.extra.get(k) == v for k, v in required_flags.items()):
            continue

        # Process the reaction
        return _process_reaction(target, reaction_config, accessor)

    return None


def _process_item_use(
    entity: Any,
    config: dict[str, Any],
    accessor: Any,
    context: dict[str, Any],
) -> EventResult | None:
    """Process item's self-use reaction (data-driven mode)."""
    state = accessor.game_state
    target = context.get("target")
    target_id = target.id if target and hasattr(target, "id") else ""

    for reaction_name, reaction_config in config.items():
        if reaction_name in ("handler", "_metadata"):
            continue  # Skip special keys

        if not isinstance(reaction_config, dict):
            continue

        # Check target requirements
        target_types = reaction_config.get("target_types", [])
        if target_types and not any(t.lower() in target_id.lower() for t in target_types):
            continue

        return _process_reaction(entity, reaction_config, accessor)

    return None


def _process_reaction(
    entity: Any,
    reaction_config: dict[str, Any],
    accessor: Any,
) -> EventResult:
    """Process a matched item use reaction."""
    state = accessor.game_state

    # Set flags
    flags = reaction_config.get("set_flags", {})
    for flag_name, flag_value in flags.items():
        state.extra[flag_name] = flag_value

    # Apply trust changes
    trust_delta = reaction_config.get("trust_delta", 0)
    if trust_delta and hasattr(entity, "properties"):
        trust_state = entity.properties.get("trust_state", {"current": 0})
        new_trust = modify_trust(
            current=trust_state.get("current", 0),
            delta=trust_delta,
            floor=trust_state.get("floor", -5),
            ceiling=trust_state.get("ceiling", 5),
        )
        trust_state["current"] = new_trust
        entity.properties["trust_state"] = trust_state

    # State transitions
    new_state = reaction_config.get("transition_to")
    if new_state and hasattr(entity, "properties"):
        sm = entity.properties.get("state_machine")
        if sm:
            transition_state(sm, new_state)

    # Get response message
    message = reaction_config.get("response", "")

    return EventResult(allow=True, feedback=message if message else None)
