"""Tests for scheduled events system."""
from src.types import ActorId

import unittest
from unittest.mock import Mock

from src.state_manager import Actor, Location, GameState, Metadata
from src.state_accessor import StateAccessor


class TestScheduleEvent(unittest.TestCase):
    """Test schedule_event function."""

    def test_schedule_event_adds_to_list(self):
        """Scheduled event is added to state.extra."""
        from behavior_libraries.timing_lib.scheduled_events import schedule_event

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        schedule_event(accessor, 'spore_spread', trigger_turn=100, data={'severity': 'high'})

        events = state.extra.get('scheduled_events', [])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['event'], 'spore_spread')
        self.assertEqual(events[0]['turn'], 100)
        self.assertEqual(events[0]['data'], {'severity': 'high'})

    def test_schedule_event_unique_id(self):
        """Each scheduled event gets a unique ID."""
        from behavior_libraries.timing_lib.scheduled_events import schedule_event

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        schedule_event(accessor, 'event_a', trigger_turn=50)
        schedule_event(accessor, 'event_b', trigger_turn=60)

        events = state.extra.get('scheduled_events', [])
        self.assertEqual(len(events), 2)
        self.assertNotEqual(events[0]['id'], events[1]['id'])


class TestCancelEvent(unittest.TestCase):
    """Test cancel_event function."""

    def test_cancel_event_removes_from_list(self):
        """Cancelled event is removed from state.extra."""
        from behavior_libraries.timing_lib.scheduled_events import schedule_event, cancel_event

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        schedule_event(accessor, 'spore_spread', trigger_turn=100)

        events = state.extra.get('scheduled_events', [])
        self.assertEqual(len(events), 1)

        cancel_event(accessor, 'spore_spread')

        events = state.extra.get('scheduled_events', [])
        self.assertEqual(len(events), 0)

    def test_cancel_event_only_removes_matching(self):
        """Cancel only removes events with matching name."""
        from behavior_libraries.timing_lib.scheduled_events import schedule_event, cancel_event

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        schedule_event(accessor, 'event_a', trigger_turn=50)
        schedule_event(accessor, 'event_b', trigger_turn=60)

        cancel_event(accessor, 'event_a')

        events = state.extra.get('scheduled_events', [])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['event'], 'event_b')


class TestGetScheduledEvents(unittest.TestCase):
    """Test get_scheduled_events function."""

    def test_get_scheduled_events_returns_all(self):
        """Returns all scheduled events."""
        from behavior_libraries.timing_lib.scheduled_events import schedule_event, get_scheduled_events

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        schedule_event(accessor, 'event_a', trigger_turn=50)
        schedule_event(accessor, 'event_b', trigger_turn=60)

        events = get_scheduled_events(accessor)

        self.assertEqual(len(events), 2)

    def test_get_scheduled_events_empty(self):
        """Returns empty list when no events scheduled."""
        from behavior_libraries.timing_lib.scheduled_events import get_scheduled_events

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        events = get_scheduled_events(accessor)

        self.assertEqual(events, [])


class TestOnCheckScheduledEvents(unittest.TestCase):
    """Test on_check_scheduled_events hook handler."""

    def test_fires_event_at_correct_turn(self):
        """Event fires when turn count matches trigger_turn."""
        from behavior_libraries.timing_lib.scheduled_events import (
            schedule_event, on_check_scheduled_events
        )

        state = GameState(metadata=Metadata(title="Test"))
        state.turn_count = 100
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        schedule_event(accessor, 'spore_spread', trigger_turn=100)

        context = {}
        result = on_check_scheduled_events(None, accessor, context)

        # Event should have fired and been removed
        events = state.extra.get('scheduled_events', [])
        self.assertEqual(len(events), 0)
        # Result should indicate event fired
        self.assertTrue(result.allow)
        self.assertIn('spore_spread', result.message)

    def test_does_not_fire_before_turn(self):
        """Event does not fire before trigger_turn."""
        from behavior_libraries.timing_lib.scheduled_events import (
            schedule_event, on_check_scheduled_events
        )

        state = GameState(metadata=Metadata(title="Test"))
        state.turn_count = 50
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        schedule_event(accessor, 'spore_spread', trigger_turn=100)

        context = {}
        on_check_scheduled_events(None, accessor, context)

        # Event should still be scheduled
        events = state.extra.get('scheduled_events', [])
        self.assertEqual(len(events), 1)

    def test_repeating_event_reschedules(self):
        """Repeating event reschedules after firing."""
        from behavior_libraries.timing_lib.scheduled_events import (
            schedule_event, on_check_scheduled_events
        )

        state = GameState(metadata=Metadata(title="Test"))
        state.turn_count = 20
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        # Schedule repeating event
        state.extra['scheduled_events'] = [{
            'id': 'weather_1',
            'event': 'weather_change',
            'turn': 20,
            'data': {},
            'repeating': True,
            'interval': 10
        }]

        context = {}
        on_check_scheduled_events(None, accessor, context)

        # Event should be rescheduled for turn 30
        events = state.extra.get('scheduled_events', [])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['turn'], 30)


if __name__ == '__main__':
    unittest.main()
