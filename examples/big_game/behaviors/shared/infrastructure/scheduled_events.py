"""Scheduled Events Turn Phase Handler.

Fires scheduled events that have reached their trigger turn.
Events can set flags, transition states, or queue gossip.
"""

from typing import Any

from src.behavior_manager import EventResult
from src.state_manager import ScheduledEvent

# Vocabulary: wire hook to event
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_scheduled_events",
            "invocation": "turn_phase",
            "after": [],
            "description": "Process scheduled events that have reached their trigger turn"
        },
        {
            "hook_id": "entity_scheduled_event_trigger",
            "invocation": "entity",
            "description": "Check if a scheduled event should trigger"
        }
    ],
    "events": [
        {
            "event": "on_turn_scheduled_events",
            "hook": "turn_scheduled_events",
            "description": "Turn phase dispatcher: iterate all scheduled events",
        },
        {
            "event": "on_scheduled_event_trigger",
            "hook": "entity_scheduled_event_trigger",
            "description": "Check if this scheduled event should trigger (per-entity)",
        }
    ]
}


def on_turn_scheduled_events(
    entity: None,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Turn phase dispatcher: iterate all scheduled events.

    Called once per turn as part of the turn phase sequence.
    Iterates over all scheduled events and checks each one.

    Args:
        entity: None (turn phase pattern)
        accessor: StateAccessor instance
        context: Context dict with current_turn

    Returns:
        EventResult with combined messages from all triggered events
    """
    from src.types import EventName

    state = accessor.game_state
    messages = []

    for event in state.scheduled_events:
        result = accessor.behavior_manager.invoke_behavior(
            event,
            EventName("on_scheduled_event_trigger"),
            accessor,
            context
        )
        if result and result.feedback:
            messages.append(result.feedback)

    return EventResult(
        allow=True,
        feedback="\n".join(messages) if messages else None
    )


def on_scheduled_event_trigger(
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
