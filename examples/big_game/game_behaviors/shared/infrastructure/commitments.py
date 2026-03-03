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
    "hook_definitions": [
        {
            "hook_id": "turn_commitments",
            "invocation": "turn_phase",
            "after": ["turn_scheduled_events"],
            "description": "Process active commitments and check completion"
        },
        {
            "hook_id": "entity_commitment_check",
            "invocation": "entity",
            "description": "Check if a commitment has expired"
        }
    ],
    "events": [
        {
            "event": "on_turn_commitments",
            "hook": "turn_commitments",
            "description": "Turn phase dispatcher: iterate all commitments",
        },
        {
            "event": "on_commitment_check",
            "hook": "entity_commitment_check",
            "description": "Check commitment deadline each turn (per-entity)",
        }
    ]
}


def on_turn_commitments(
    entity: None,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Turn phase dispatcher: iterate all commitments.

    Called once per turn as part of the turn phase sequence.
    Iterates over all commitments and checks each one.

    Args:
        entity: None (turn phase pattern)
        accessor: StateAccessor instance
        context: Context dict with current_turn

    Returns:
        EventResult with combined messages from all expired commitments
    """
    from src.types import EventName

    state = accessor.game_state
    messages = []

    for commitment in state.commitments:
        result = accessor.behavior_manager.invoke_behavior(
            commitment,
            EventName("on_commitment_check"),
            accessor,
            context
        )
        if result and result.feedback:
            messages.append(result.feedback)

    return EventResult(
        allow=True,
        feedback="\n".join(messages) if messages else None
    )


def on_commitment_check(
    entity: Commitment,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Check if this commitment has expired (per-entity handler).

    Called once per commitment per turn as part of the turn phase sequence.
    When a commitment expires:
    - Commitment transitions to ABANDONED state
    - Target NPC's commitment_reactions handler is invoked
    - NPC may die (if dying and hope was keeping them alive)
    - Echo trust may decrease

    Args:
        entity: The Commitment entity being checked
        accessor: StateAccessor instance
        context: Context dict with current_turn

    Returns:
        EventResult with message if commitment expired, None otherwise
    """
    current_turn = context.get("current_turn", 0)

    # Check if commitment is still active
    commitment_state = entity.properties.get("state")
    if commitment_state != CommitmentState.ACTIVE:
        return EventResult(allow=True, feedback=None)

    # Check if this commitment has a deadline
    deadline = entity.properties.get("deadline_turn")
    if not deadline:
        return EventResult(allow=True, feedback=None)

    # Check if deadline has passed
    if current_turn < deadline:
        return EventResult(allow=True, feedback=None)

    # Deadline passed - transition to abandoned
    entity.properties["state"] = CommitmentState.ABANDONED

    # Build default message
    message = f"Your commitment to {entity.name} has expired."

    # Invoke entity_commitment_state_change hook on target NPC
    from src.types import HookName, EventName

    game_state = accessor.game_state
    target_actor_id = entity.properties.get("target_actor")

    if target_actor_id:
        target_npc = game_state.actors.get(target_actor_id)
        if target_npc:
            event = accessor.behavior_manager.get_event_for_hook(
                HookName("entity_commitment_state_change")
            )
            if event:
                commitment_context = {
                    "commitment_id": entity.id,
                    "state_change": "abandoned",  # StateChangeMatchStrategy requires this
                    "deadline_turn": deadline,
                    "current_turn": current_turn,
                }
                result = accessor.behavior_manager.invoke_behavior(
                    target_npc, event, accessor, commitment_context
                )
                if result and result.feedback:
                    message = result.feedback

    # TODO: Handle NPC death if hope_applied and NPC is dying
    # TODO: Apply Echo trust penalty if configured

    return EventResult(allow=True, feedback=message)
