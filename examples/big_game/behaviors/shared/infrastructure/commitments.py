"""Commitment System Turn Phase Handler.

Checks commitment deadlines each turn and handles:
- Expired commitments (transition to abandoned state)
- Hope-extended survival for NPCs
- Echo trust impacts from abandonment
"""

from typing import Any

from src.behavior_manager import EventResult
from src.infrastructure_types import CommitmentState
from src.state_manager import Commitment

# Vocabulary: wire hook to event
vocabulary = {
    "events": [
        {
            "event": "on_turn_commitment",
            "hook": "turn_phase_commitment",
            "description": "Check commitment deadline each turn (per-entity)",
        }
    ]
}


def on_turn_commitment(
    entity: Commitment,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Check if this commitment has expired (per-entity handler).

    Called once per commitment per turn as part of the turn phase sequence.
    When a commitment expires:
    - Commitment transitions to ABANDONED state
    - Target NPC may die (if dying and not stabilized)
    - Echo trust decreases

    Args:
        entity: The Commitment entity being checked
        accessor: StateAccessor instance
        context: Context dict with current_turn

    Returns:
        EventResult with message if commitment expired, None otherwise
    """
    current_turn = context.get("current_turn", 0)

    # Check if this commitment has a deadline
    deadline = entity.properties.get("deadline_turn")
    if not deadline:
        return EventResult(allow=True, feedback=None)

    # Check if deadline has passed
    if current_turn < deadline:
        return EventResult(allow=True, feedback=None)

    # Check if commitment is still active
    state = entity.properties.get("state")
    if state != CommitmentState.ACTIVE:
        return EventResult(allow=True, feedback=None)

    # Deadline passed - transition to abandoned
    entity.properties["state"] = CommitmentState.ABANDONED

    # Build message for narration
    message = f"Your commitment to {entity.name} has expired."

    # TODO: Handle NPC death if applicable
    # TODO: Apply Echo trust penalty

    return EventResult(allow=True, feedback=message)
