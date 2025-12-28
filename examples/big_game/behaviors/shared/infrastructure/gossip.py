"""Gossip Propagation Turn Phase Handler.

Delivers gossip entries that have reached their arrival turn.
Handles point-to-point, broadcast, and network gossip types.
"""

from typing import Any

from src.behavior_manager import EventResult
from src.state_manager import Gossip

# Vocabulary: wire hook to event
vocabulary = {
    "events": [
        {
            "event": "on_turn_gossip",
            "hook": "turn_phase_gossip",
            "description": "Deliver gossip if it has reached arrival turn (per-entity)",
        }
    ]
}


def on_turn_gossip(
    entity: Gossip,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Deliver this gossip entry if it has reached arrival turn (per-entity handler).

    Called once per gossip entry per turn as part of the turn phase sequence.
    When gossip arrives:
    - Target NPCs receive the information
    - NPC trust/disposition may change based on content
    - Confession windows may close

    Args:
        entity: The Gossip entity being checked
        accessor: StateAccessor instance
        context: Context dict with current_turn

    Returns:
        EventResult (typically no feedback - gossip effects are indirect)
    """
    current_turn = context.get("current_turn", 0)

    # Check if gossip has reached its arrival turn
    arrives_turn = entity.properties.get("arrives_turn")
    if not arrives_turn or current_turn < arrives_turn:
        return EventResult(allow=True, feedback=None)

    # Gossip has arrived - process delivery
    gossip_type = entity.properties.get("gossip_type", "POINT_TO_POINT")
    content = entity.properties.get("content", "")

    # TODO: Actually deliver gossip to target NPCs
    # For now, just mark as delivered
    # In full implementation, this would:
    # - Update target NPC knowledge/flags based on content
    # - Modify trust/disposition if applicable
    # - Handle broadcast to regions or network propagation
    # - Remove from gossip queue after delivery

    # Gossip delivery is usually silent - effects manifest in NPC behavior
    # Only show debug message in development
    # return EventResult(allow=True, feedback=f"[Gossip delivered: {content[:30]}...]")

    return EventResult(allow=True, feedback=None)
