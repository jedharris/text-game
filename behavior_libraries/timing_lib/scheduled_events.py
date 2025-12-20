"""Scheduled events mechanics.

Allows scheduling events to fire at specific turn counts.

Events are stored in GameState.extra['scheduled_events'] as a list:
[
    {
        "id": "unique_id",
        "event_type": "on_spore_spread",
        "trigger_turn": 100,
        "data": {"severity": "high"},
        "repeating": true,
        "interval": 10
    }
]

Usage:
    from behavior_libraries.timing_lib import (
        schedule_event, cancel_event, get_scheduled_events,
        on_check_scheduled_events
    )
"""

import uuid
from typing import Any, Dict, List, Optional

from src.behavior_manager import EventResult
from src.infrastructure_types import ScheduledEvent, ScheduledEventId, TurnNumber
from src.infrastructure_utils import get_scheduled_events as _get_state_scheduled_events


def schedule_event(
    accessor,
    event_name: str,
    trigger_turn: int,
    data: Optional[Dict[str, str]] = None,
    repeating: bool = False,
    interval: Optional[int] = None
) -> str:
    """
    Schedule an event to fire at a specific turn.

    Args:
        accessor: StateAccessor instance
        event_name: Name of the event
        trigger_turn: Turn number when event should fire
        data: Optional data to pass with event
        repeating: If True, event reschedules after firing
        interval: For repeating events, turns between fires

    Returns:
        Unique ID for the scheduled event
    """
    event_id = ScheduledEventId(str(uuid.uuid4())[:8])

    event: ScheduledEvent = {
        'id': event_id,
        'event_type': event_name,
        'trigger_turn': TurnNumber(trigger_turn),
    }
    if data:
        event['data'] = data
    if repeating:
        event['repeating'] = repeating
    if interval is not None:
        event['interval'] = interval

    events = _get_state_scheduled_events(accessor.game_state)
    events.append(event)
    return event_id


def cancel_event(accessor, event_name: str) -> bool:
    """
    Cancel a scheduled event by name.

    Args:
        accessor: StateAccessor instance
        event_name: Name of the event to cancel

    Returns:
        True if event was found and cancelled, False otherwise
    """
    events = _get_state_scheduled_events(accessor.game_state)

    for i, event in enumerate(events):
        if event['event_type'] == event_name:
            events.pop(i)
            return True

    return False


def get_scheduled_events(accessor) -> List[ScheduledEvent]:
    """Expose scheduled events through the typed infrastructure helper."""
    return _get_state_scheduled_events(accessor.game_state)


def on_check_scheduled_events(entity: Any, accessor: Any, context: dict) -> EventResult:
    """
    Hook handler - check and fire due scheduled events.

    This should be registered for the CONDITION_TICK hook.

    Args:
        entity: Ignored (can be None)
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with messages about fired events
    """
    current_turn = accessor.game_state.turn_count
    events = _get_state_scheduled_events(accessor.game_state)

    fired_messages: List[str] = []
    to_remove: List[int] = []
    to_add: List[ScheduledEvent] = []

    for i, event in enumerate(events):
        if event['trigger_turn'] <= current_turn:
            # Event is due - fire it
            fired_messages.append(f"Event '{event['event_type']}' triggered.")

            if event.get('repeating') and event.get('interval'):
                # Reschedule for next interval
                interval = event['interval']
                new_event: ScheduledEvent = {
                    'id': event['id'],
                    'event_type': event['event_type'],
                    'trigger_turn': TurnNumber(current_turn + interval),
                    'repeating': True,
                    'interval': interval,
                }
                if event.get('data'):
                    new_event['data'] = event['data']
                to_add.append(new_event)
                to_remove.append(i)
            else:
                # One-time event - remove
                to_remove.append(i)

    # Remove fired one-time events (in reverse order to preserve indices)
    for i in sorted(to_remove, reverse=True):
        events.pop(i)

    # Add rescheduled repeating events
    for event in to_add:
        events.append(event)

    message = '\n'.join(fired_messages) if fired_messages else ''
    return EventResult(allow=True, feedback=message)


# Vocabulary extension
vocabulary = {
    "hooks": {
        "condition_tick": "on_check_scheduled_events"
    }
}
