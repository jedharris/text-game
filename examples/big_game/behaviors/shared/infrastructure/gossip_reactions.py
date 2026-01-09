"""Gossip Reaction Infrastructure.

Handles NPC reactions to gossip delivery.

Supports handler escape hatch where entity properties specify a Python function to call.

Example config:
    "gossip_reactions": {
        "handler": "behaviors.regions.civilized_remnants.services:on_gossip_received"
    }
"""

from typing import Any

from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult

# Vocabulary: wire hooks to events
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "entity_gossip_received",
            "invocation": "entity",
            "description": "Called when entity receives gossip"
        }
    ],
    "events": [
        {
            "event": "on_gossip_received",
            "hook": "entity_gossip_received",
            "description": "Handle gossip reception reactions",
        },
    ]
}


def on_gossip_received(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle gossip reception reactions for NPCs.

    Checks the entity for gossip_reactions configuration.
    Calls the handler function specified in the config.

    Args:
        entity: The NPC receiving gossip
        accessor: StateAccessor instance
        context: Context with gossip entry data

    Returns:
        EventResult with reaction
    """
    if not hasattr(entity, "properties"):
        return EventResult(allow=True, feedback=None)

    # Check for gossip_reactions configuration
    gossip_config = entity.properties.get("gossip_reactions", {})
    if not gossip_config:
        return EventResult(allow=True, feedback=None)

    # Load and call handler
    handler_path = gossip_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)

    return EventResult(allow=True, feedback=None)
