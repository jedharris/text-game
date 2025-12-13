"""Gossip Propagation Turn Phase Handler.

Delivers gossip entries that have reached their arrival turn.
Handles point-to-point, broadcast, and network gossip types.
"""

from typing import Any

from src.behavior_manager import EventResult
from src.infrastructure_types import TurnNumber
from src.infrastructure_utils import (
    deliver_due_gossip,
    get_current_turn,
)

# Vocabulary: wire hook to event
vocabulary = {
    "events": [
        {
            "event": "on_gossip_propagate",
            "hook": "turn_phase_gossip",
            "description": "Deliver gossip that has reached its destination",
        }
    ]
}


def on_gossip_propagate(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Deliver gossip entries that have reached their arrival turn.

    This is called once per turn as part of the turn phase sequence.
    When gossip arrives:
    - Target NPCs receive the information
    - NPC trust/disposition may change based on content
    - Confession windows may close

    Args:
        entity: None (game-wide handler)
        accessor: StateAccessor instance
        context: Context dict with current_turn

    Returns:
        EventResult with messages about delivered gossip
    """
    state = accessor.state
    current_turn = get_current_turn(state)

    # Deliver all due gossip
    delivered = deliver_due_gossip(state, current_turn)

    if not delivered:
        return EventResult(allow=True, message=None)

    # Build messages for narration
    # Note: These are internal state changes, not necessarily
    # narrated to the player. The effect is that NPCs now know things.
    messages: list[str] = []
    for entry in delivered:
        content = entry.get("content", "")
        target_npcs = entry.get("target_npcs", [])
        # Gossip delivery is usually silent unless player witnesses it
        # The effect manifests in NPC dialog and reactions

    # Return without message - gossip effects are indirect
    return EventResult(allow=True, message=None)
