"""Scheduled events mechanics.

Allows scheduling events to fire at specific turn counts.

Events are stored in GameState.extra['scheduled_events'] as a list:
[
    {
        "id": "unique_id",
        "event": "on_spore_spread",
        "turn": 100,
        "data": {"severity": "high"},
        "repeating": false,
        "interval": null
    }
]

Usage:
    from behavior_libraries.timing_lib import (
        schedule_event, cancel_event, get_scheduled_events,
        on_check_scheduled_events
    )
"""

import uuid
from typing import Dict, List, Optional

from src.behavior_manager import EventResult


def schedule_event(
    accessor,
    event_name: str,
    trigger_turn: int,
    data: Optional[Dict] = None,
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
    if 'scheduled_events' not in accessor.game_state.extra:
        accessor.game_state.extra['scheduled_events'] = []

    event_id = str(uuid.uuid4())[:8]

    event = {
        'id': event_id,
        'event': event_name,
        'turn': trigger_turn,
        'data': data or {},
        'repeating': repeating,
        'interval': interval
    }

    accessor.game_state.extra['scheduled_events'].append(event)
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
    events = accessor.game_state.extra.get('scheduled_events', [])

    for i, event in enumerate(events):
        if event['event'] == event_name:
            events.pop(i)
            return True

    return False


def get_scheduled_events(accessor) -> List[Dict]:
    """
    Get all scheduled events.

    Args:
        accessor: StateAccessor instance

    Returns:
        List of scheduled event dicts
    """
    return accessor.game_state.extra.get('scheduled_events', [])


def on_check_scheduled_events(entity, accessor, context: dict) -> EventResult:
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
    events = accessor.game_state.extra.get('scheduled_events', [])

    fired_messages = []
    to_remove = []
    to_add = []

    for i, event in enumerate(events):
        if event['turn'] <= current_turn:
            # Event is due - fire it
            fired_messages.append(f"Event '{event['event']}' triggered.")

            if event.get('repeating') and event.get('interval'):
                # Reschedule for next interval
                new_event = event.copy()
                new_event['turn'] = current_turn + event['interval']
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
    return EventResult(allow=True, message=message)


# Vocabulary extension
vocabulary = {
    "hooks": {
        "condition_tick": "on_check_scheduled_events"
    }
}
