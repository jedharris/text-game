"""Scheduled Events Turn Phase Handler.

Fires scheduled events that have reached their trigger turn.
Events can set flags, transition states, or queue gossip.
"""

from typing import Any

from src.behavior_manager import EventResult
from src.state_manager import ScheduledEvent

# Vocabulary: wire hook to event
vocabulary = {
    "events": [
        {
            "event": "on_turn_scheduled",
            "hook": "turn_phase_scheduled",
            "description": "Check and fire scheduled event if trigger turn reached (per-entity)",
        }
    ]
}


def on_turn_scheduled(
    entity: ScheduledEvent,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Check if this scheduled event should fire (per-entity handler).

    Called once per event per turn as part of the turn phase sequence.
    When an event fires, it can:
    - Set flags
    - Transition states
    - Queue gossip
    - Trigger other game effects

    Args:
        entity: The ScheduledEvent entity being checked
        accessor: StateAccessor instance
        context: Context dict with current_turn

    Returns:
        EventResult with message if event fired, None otherwise
    """
    current_turn = context.get("current_turn", 0)

    # Check if trigger turn has been reached
    trigger_turn = entity.properties.get("trigger_turn")
    if not trigger_turn or current_turn < trigger_turn:
        return EventResult(allow=True, feedback=None)

    # Event is due to fire
    event_type = entity.properties.get("event_type", "unknown")
    event_data = entity.properties.get("data", {})

    # TODO: Actually process the event based on event_type
    # For now, just report that it would fire
    # In full implementation, this would:
    # - Set flags based on event_type
    # - Create gossip if event_type indicates gossip
    # - Update state based on event_data
    # - Handle repeating events by updating trigger_turn

    message = f"[Event fired: {event_type}]"

    # Handle repeating events
    if entity.properties.get("repeating", False):
        interval = entity.properties.get("interval", 1)
        entity.properties["trigger_turn"] = trigger_turn + interval
        message += f" (next at turn {trigger_turn + interval})"

    return EventResult(allow=True, feedback=message)
