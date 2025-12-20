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

from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult
from src.infrastructure_utils import (
    get_current_state,
    modify_trust,
    transition_state,
)

# Vocabulary: wire hooks to events
vocabulary = {
    "events": [
        {
            "event": "on_gift_given",
            "hook": "after_give",
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
    Otherwise, processes the data-driven config.

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

    # Data-driven processing
    item = context.get("item") or entity
    item_id = item.id if hasattr(item, "id") else str(item)
    item_lower = item_id.lower()

    # Check each reaction type (skip special keys)
    for reaction_type, reaction_config in gift_config.items():
        if reaction_type in ("handler", "reject_message"):
            continue
        if not isinstance(reaction_config, dict):
            continue

        accepted_items = reaction_config.get("accepted_items", [])

        # Check if item matches any accepted pattern
        item_matches = any(
            pattern.lower() in item_lower for pattern in accepted_items
        )
        if not item_matches:
            continue

        # Item is accepted - process the reaction
        return _process_gift_reaction(
            target=target,
            item_id=item_id,
            reaction_type=reaction_type,
            reaction_config=reaction_config,
            accessor=accessor,
        )

    # Check for rejection message
    reject_message = gift_config.get("reject_message")
    if reject_message:
        return EventResult(allow=True, feedback=reject_message)

    return EventResult(allow=True, feedback=None)


def _process_gift_reaction(
    target: Any,
    item_id: str,
    reaction_type: str,
    reaction_config: dict[str, Any],
    accessor: Any,
) -> EventResult:
    """Process a matched gift reaction using data-driven config."""
    state = accessor.state

    # Apply trust changes if configured
    trust_delta = reaction_config.get("trust_delta", 0)
    if trust_delta:
        trust_state = target.properties.get("trust_state", {"current": 0})
        old_trust = trust_state.get("current", 0)
        new_trust = modify_trust(
            current=old_trust,
            delta=trust_delta,
            floor=trust_state.get("floor", -5),
            ceiling=trust_state.get("ceiling", 5),
        )
        trust_state["current"] = new_trust
        target.properties["trust_state"] = trust_state

        # Check for state transitions based on trust thresholds
        transitions = reaction_config.get("trust_transitions", {})
        sm = target.properties.get("state_machine")
        if sm and transitions:
            current_state = get_current_state(sm)
            for threshold_str, new_state in transitions.items():
                threshold = int(threshold_str)
                if old_trust < threshold <= new_trust:
                    transition_state(sm, new_state)

    # Set flags if configured
    flags = reaction_config.get("set_flags", {})
    for flag_name, flag_value in flags.items():
        state.extra[flag_name] = flag_value

    # Track items given if configured
    track_key = reaction_config.get("track_items_key")
    if track_key:
        tracked = state.extra.get(track_key, [])
        # Extract item type from item_id (remove item_ prefix etc)
        item_type = item_id.lower().replace("item_", "")
        if item_type not in tracked:
            tracked.append(item_type)
            state.extra[track_key] = tracked

    # Get appropriate message
    message = reaction_config.get("accept_message", "")
    if message and "{item}" in message:
        message = message.format(item=item_id)

    return EventResult(allow=True, feedback=message if message else None)
