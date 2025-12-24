"""Commitment System Turn Phase Handler.

Checks commitment deadlines each turn and handles:
- Expired commitments (transition to abandoned state)
- Hope-extended survival for NPCs
- Echo trust impacts from abandonment
"""

from typing import Any

from src.behavior_manager import EventResult
from src.infrastructure_types import CommitmentState
from src.infrastructure_utils import (
    get_current_turn,
    get_expired_commitments,
    transition_commitment_state,
)

# Vocabulary: wire hook to event
vocabulary = {
    "events": [
        {
            "event": "on_commitment_check",
            "hook": "turn_phase_commitment",
            "description": "Check commitment deadlines each turn",
        }
    ]
}


def on_commitment_check(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Check commitment deadlines and handle expirations.

    This is called once per turn as part of the turn phase sequence.
    When a commitment expires:
    - Commitment transitions to ABANDONED state
    - Target NPC may die (if dying and not stabilized)
    - Echo trust decreases

    Args:
        entity: None (game-wide handler)
        accessor: StateAccessor instance
        context: Context dict with current_turn

    Returns:
        EventResult with messages about expired commitments
    """
    state = accessor.game_state
    current_turn = get_current_turn(state)

    # Find expired commitments
    expired = get_expired_commitments(state, current_turn)

    if not expired:
        return EventResult(allow=True, feedback=None)

    messages = []
    for commitment in expired:
        # Transition to abandoned
        transition_commitment_state(commitment, CommitmentState.ABANDONED)

        commitment_id = commitment.get("id", "unknown")
        config_id = commitment.get("config_id", commitment_id)

        # Build message for narration
        messages.append(f"Your commitment to {config_id} has expired.")

        # TODO: Handle NPC death if applicable
        # TODO: Apply Echo trust penalty

    return EventResult(
        allow=True,
        feedback="\n".join(messages) if messages else None,
    )
