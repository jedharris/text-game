"""Scheduled Events Turn Phase Handler.

Fires scheduled events that have reached their trigger turn.
Events can set flags, transition states, or queue gossip.
"""

from typing import Any

from src.behavior_manager import EventResult
from src.infrastructure_utils import fire_due_events

# Vocabulary: wire hook to event
vocabulary = {
    "events": [
        {
            "event": "on_scheduled_event_check",
            "hook": "turn_phase_scheduled",
            "description": "Check and fire scheduled events each turn",
        }
    ]
}


def on_scheduled_event_check(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Check and fire scheduled events that have reached their trigger turn.

    This is called once per turn as part of the turn phase sequence.
    The entity parameter is None since this is a game-wide check.

    Args:
        entity: None (game-wide handler)
        accessor: StateAccessor instance
        context: Context dict with current_turn

    Returns:
        EventResult with messages about fired events
    """
    state = accessor.state

    # Fire all due events (reads current turn from state.extra["turn_count"])
    fired_events = fire_due_events(state)

    if not fired_events:
        return EventResult(allow=True, message=None)

    # Build message about fired events
    messages = []
    for event in fired_events:
        event_type = event.get("event_type", "unknown")
        # The actual effect is handled by fire_due_events
        # Here we just report what happened for narration
        messages.append(f"[Event: {event_type}]")

    return EventResult(
        allow=True,
        message="\n".join(messages) if messages else None,
    )
