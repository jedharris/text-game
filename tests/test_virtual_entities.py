"""Tests for virtual entity types (Commitment, ScheduledEvent, Gossip, Spread).

Tests parsing, serialization, and GameState accessors for first-class virtual entities.
"""
import unittest
from src.state_manager import (
    Commitment, ScheduledEvent, Gossip, Spread,
    GameState, Metadata,
    _parse_commitment, _parse_scheduled_event, _parse_gossip, _parse_spread,
    _serialize_commitment, _serialize_scheduled_event, _serialize_gossip, _serialize_spread,
    load_game_state, game_state_to_dict
)
from src.types import CommitmentId, ScheduledEventId, GossipId, SpreadId, ActorId, LocationId


class TestCommitmentEntity(unittest.TestCase):
    """Test Commitment entity parsing and serialization."""

    def test_parse_commitment_minimal(self):
        """Parse commitment with only required fields."""
        raw = {
            'id': 'commit_test',
        }
        commitment = _parse_commitment(raw)
        self.assertEqual(commitment.id, CommitmentId('commit_test'))
        self.assertEqual(commitment.name, 'commit_test')  # Defaults to ID
        self.assertEqual(commitment.description, '')
        self.assertEqual(commitment.properties, {})
        self.assertEqual(commitment.behaviors, [])

    def test_parse_commitment_full(self):
        """Parse commitment with all fields."""
        raw = {
            'id': 'commit_sira_rescue',
            'name': "Sira's rescue promise",
            'description': 'Promised to rescue Sira from wolves by turn 15',
            'properties': {
                'state': 'ACTIVE',
                'deadline_turn': 15,
                'target_npc': 'npc_sira',
                'config_id': 'commit_sira_rescue'
            },
            'behaviors': ['behaviors.shared.infrastructure.commitments']
        }
        commitment = _parse_commitment(raw)
        self.assertEqual(commitment.id, CommitmentId('commit_sira_rescue'))
        self.assertEqual(commitment.name, "Sira's rescue promise")
        self.assertEqual(commitment.description, 'Promised to rescue Sira from wolves by turn 15')
        self.assertEqual(commitment.properties['state'], 'ACTIVE')
        self.assertEqual(commitment.properties['deadline_turn'], 15)
        self.assertEqual(commitment.behaviors, ['behaviors.shared.infrastructure.commitments'])

    def test_serialize_commitment(self):
        """Serialize commitment to dict."""
        commitment = Commitment(
            id=CommitmentId('commit_test'),
            name='Test commitment',
            description='Test description',
            properties={'state': 'ACTIVE', 'deadline_turn': 10},
            behaviors=['behaviors.test']
        )
        serialized = _serialize_commitment(commitment)
        self.assertEqual(serialized['id'], 'commit_test')
        self.assertEqual(serialized['name'], 'Test commitment')
        self.assertEqual(serialized['description'], 'Test description')
        self.assertEqual(serialized['state'], 'ACTIVE')
        self.assertEqual(serialized['deadline_turn'], 10)
        self.assertEqual(serialized['behaviors'], ['behaviors.test'])

    def test_gamestate_get_commitment(self):
        """Test GameState.get_commitment accessor."""
        commitment1 = Commitment(
            id=CommitmentId('commit_1'),
            name='First',
            description='First commitment',
            properties={},
            behaviors=[]
        )
        commitment2 = Commitment(
            id=CommitmentId('commit_2'),
            name='Second',
            description='Second commitment',
            properties={},
            behaviors=[]
        )

        state = GameState(
            metadata=Metadata(title='Test'),
            commitments=[commitment1, commitment2]
        )

        # Test successful lookup
        found = state.get_commitment(CommitmentId('commit_1'))
        self.assertEqual(found.id, CommitmentId('commit_1'))
        self.assertEqual(found.name, 'First')

        # Test fail-fast on missing commitment
        with self.assertRaises(KeyError) as ctx:
            state.get_commitment(CommitmentId('missing'))
        self.assertIn('Commitment not found', str(ctx.exception))


class TestScheduledEventEntity(unittest.TestCase):
    """Test ScheduledEvent entity parsing and serialization."""

    def test_parse_scheduled_event_minimal(self):
        """Parse scheduled event with only required fields."""
        raw = {
            'id': 'evt_test',
        }
        event = _parse_scheduled_event(raw)
        self.assertEqual(event.id, ScheduledEventId('evt_test'))
        self.assertEqual(event.name, 'evt_test')
        self.assertEqual(event.description, '')
        self.assertEqual(event.properties, {})
        self.assertEqual(event.behaviors, [])

    def test_parse_scheduled_event_full(self):
        """Parse scheduled event with all fields."""
        raw = {
            'id': 'evt_cold_spread_75',
            'name': 'Cold spread milestone 75',
            'description': 'Frozen reaches cold spreads to meridian_nexus',
            'properties': {
                'trigger_turn': 75,
                'event_type': 'cold_spread_milestone',
                'data': {'region': 'meridian_nexus'},
                'repeating': False
            },
            'behaviors': ['behaviors.shared.infrastructure.scheduled_events']
        }
        event = _parse_scheduled_event(raw)
        self.assertEqual(event.id, ScheduledEventId('evt_cold_spread_75'))
        self.assertEqual(event.name, 'Cold spread milestone 75')
        self.assertEqual(event.properties['trigger_turn'], 75)
        self.assertEqual(event.properties['event_type'], 'cold_spread_milestone')
        self.assertFalse(event.properties['repeating'])

    def test_serialize_scheduled_event(self):
        """Serialize scheduled event to dict."""
        event = ScheduledEvent(
            id=ScheduledEventId('evt_test'),
            name='Test event',
            description='Test description',
            properties={'trigger_turn': 50, 'event_type': 'test'},
            behaviors=[]
        )
        serialized = _serialize_scheduled_event(event)
        self.assertEqual(serialized['id'], 'evt_test')
        self.assertEqual(serialized['name'], 'Test event')
        self.assertEqual(serialized['trigger_turn'], 50)

    def test_gamestate_get_scheduled_event(self):
        """Test GameState.get_scheduled_event accessor."""
        event = ScheduledEvent(
            id=ScheduledEventId('evt_1'),
            name='Event 1',
            description='Test event',
            properties={},
            behaviors=[]
        )

        state = GameState(
            metadata=Metadata(title='Test'),
            scheduled_events=[event]
        )

        found = state.get_scheduled_event(ScheduledEventId('evt_1'))
        self.assertEqual(found.id, ScheduledEventId('evt_1'))

        with self.assertRaises(KeyError) as ctx:
            state.get_scheduled_event(ScheduledEventId('missing'))
        self.assertIn('Scheduled event not found', str(ctx.exception))


class TestGossipEntity(unittest.TestCase):
    """Test Gossip entity parsing and serialization."""

    def test_parse_gossip_minimal(self):
        """Parse gossip with only required fields."""
        raw = {
            'id': 'gossip_test',
        }
        gossip = _parse_gossip(raw)
        self.assertEqual(gossip.id, GossipId('gossip_test'))
        self.assertEqual(gossip.name, 'gossip_test')
        self.assertEqual(gossip.description, '')

    def test_parse_gossip_full(self):
        """Parse gossip with all fields."""
        raw = {
            'id': 'gossip_sira_rescue',
            'name': 'News of Sira rescue',
            'description': 'Player rescued Sira from wolves',
            'properties': {
                'gossip_type': 'POINT_TO_POINT',
                'content': 'The stranger saved Sira from the wolves',
                'source_npc': 'npc_traveler',
                'target_npcs': ['npc_healer_elara'],
                'created_turn': 5,
                'arrives_turn': 17,
                'confession_window_until': 29
            },
            'behaviors': ['behaviors.shared.infrastructure.gossip']
        }
        gossip = _parse_gossip(raw)
        self.assertEqual(gossip.id, GossipId('gossip_sira_rescue'))
        self.assertEqual(gossip.name, 'News of Sira rescue')
        self.assertEqual(gossip.properties['gossip_type'], 'POINT_TO_POINT')
        self.assertEqual(gossip.properties['source_npc'], 'npc_traveler')
        self.assertEqual(len(gossip.properties['target_npcs']), 1)

    def test_serialize_gossip(self):
        """Serialize gossip to dict."""
        gossip = Gossip(
            id=GossipId('gossip_test'),
            name='Test gossip',
            description='Test description',
            properties={'content': 'Test news', 'created_turn': 1},
            behaviors=[]
        )
        serialized = _serialize_gossip(gossip)
        self.assertEqual(serialized['id'], 'gossip_test')
        self.assertEqual(serialized['content'], 'Test news')

    def test_gamestate_get_gossip(self):
        """Test GameState.get_gossip accessor."""
        gossip = Gossip(
            id=GossipId('gossip_1'),
            name='Gossip 1',
            description='Test gossip',
            properties={},
            behaviors=[]
        )

        state = GameState(
            metadata=Metadata(title='Test'),
            gossip=[gossip]
        )

        found = state.get_gossip(GossipId('gossip_1'))
        self.assertEqual(found.id, GossipId('gossip_1'))

        with self.assertRaises(KeyError) as ctx:
            state.get_gossip(GossipId('missing'))
        self.assertIn('Gossip not found', str(ctx.exception))


class TestSpreadEntity(unittest.TestCase):
    """Test Spread entity parsing and serialization."""

    def test_parse_spread_minimal(self):
        """Parse spread with only required fields."""
        raw = {
            'id': 'spread_test',
        }
        spread = _parse_spread(raw)
        self.assertEqual(spread.id, SpreadId('spread_test'))
        self.assertEqual(spread.name, 'spread_test')
        self.assertEqual(spread.description, '')

    def test_parse_spread_full(self):
        """Parse spread with all fields."""
        raw = {
            'id': 'frozen_reaches_cold',
            'name': 'Frozen reaches cold spread',
            'description': 'Cold from frozen reaches spreading to adjacent regions',
            'properties': {
                'active': True,
                'halt_flag': 'cold_stopped',
                'milestones': [
                    {'turn': 25, 'effects': [{'property': 'temperature', 'value': 'FREEZING'}]},
                    {'turn': 50, 'effects': [{'property': 'temperature', 'value': 'DEADLY_COLD'}]}
                ],
                'reached_milestones': [25]
            },
            'behaviors': ['behaviors.shared.infrastructure.spreads']
        }
        spread = _parse_spread(raw)
        self.assertEqual(spread.id, SpreadId('frozen_reaches_cold'))
        self.assertEqual(spread.name, 'Frozen reaches cold spread')
        self.assertTrue(spread.properties['active'])
        self.assertEqual(spread.properties['halt_flag'], 'cold_stopped')
        self.assertEqual(len(spread.properties['milestones']), 2)

    def test_serialize_spread(self):
        """Serialize spread to dict."""
        spread = Spread(
            id=SpreadId('spread_test'),
            name='Test spread',
            description='Test description',
            properties={'active': True, 'milestones': []},
            behaviors=[]
        )
        serialized = _serialize_spread(spread)
        self.assertEqual(serialized['id'], 'spread_test')
        self.assertTrue(serialized['active'])

    def test_gamestate_get_spread(self):
        """Test GameState.get_spread accessor."""
        spread = Spread(
            id=SpreadId('spread_1'),
            name='Spread 1',
            description='Test spread',
            properties={},
            behaviors=[]
        )

        state = GameState(
            metadata=Metadata(title='Test'),
            spreads=[spread]
        )

        found = state.get_spread(SpreadId('spread_1'))
        self.assertEqual(found.id, SpreadId('spread_1'))

        with self.assertRaises(KeyError) as ctx:
            state.get_spread(SpreadId('missing'))
        self.assertIn('Spread not found', str(ctx.exception))


class TestGameStateRoundTrip(unittest.TestCase):
    """Test loading and saving GameState with virtual entities."""

    def test_load_save_round_trip(self):
        """Load game state with virtual entities and save it back."""
        game_data = {
            'metadata': {
                'title': 'Test Game',
                'version': '0.1.0'
            },
            'locations': [
                {
                    'id': 'loc_start',
                    'name': 'Start Location',
                    'description': 'The starting location'
                }
            ],
            'items': [],
            'locks': [],
            'actors': {
                'player': {
                    'id': 'player',
                    'name': 'Adventurer',
                    'description': 'A brave soul',
                    'location': 'loc_start',
                    'inventory': []
                }
            },
            'commitments': [
                {
                    'id': 'commit_1',
                    'name': 'Test commitment',
                    'description': 'Test desc',
                    'properties': {'state': 'ACTIVE'},
                    'behaviors': []
                }
            ],
            'scheduled_events': [
                {
                    'id': 'evt_1',
                    'name': 'Test event',
                    'description': 'Test desc',
                    'properties': {'trigger_turn': 10},
                    'behaviors': []
                }
            ],
            'gossip': [
                {
                    'id': 'gossip_1',
                    'name': 'Test gossip',
                    'description': 'Test desc',
                    'properties': {'content': 'News'},
                    'behaviors': []
                }
            ],
            'spreads': [
                {
                    'id': 'spread_1',
                    'name': 'Test spread',
                    'description': 'Test desc',
                    'properties': {'active': True},
                    'behaviors': []
                }
            ]
        }

        # Load from dict
        state = load_game_state(game_data)

        # Verify collections are populated
        self.assertEqual(len(state.commitments), 1)
        self.assertEqual(len(state.scheduled_events), 1)
        self.assertEqual(len(state.gossip), 1)
        self.assertEqual(len(state.spreads), 1)

        # Verify accessors work
        commitment = state.get_commitment(CommitmentId('commit_1'))
        self.assertEqual(commitment.name, 'Test commitment')

        event = state.get_scheduled_event(ScheduledEventId('evt_1'))
        self.assertEqual(event.properties['trigger_turn'], 10)

        gossip = state.get_gossip(GossipId('gossip_1'))
        self.assertEqual(gossip.properties['content'], 'News')

        spread = state.get_spread(SpreadId('spread_1'))
        self.assertTrue(spread.properties['active'])

        # Serialize back to dict
        serialized = game_state_to_dict(state)

        # Verify virtual entities are in output
        self.assertIn('commitments', serialized)
        self.assertIn('scheduled_events', serialized)
        self.assertIn('gossip', serialized)
        self.assertIn('spreads', serialized)

        self.assertEqual(len(serialized['commitments']), 1)
        self.assertEqual(serialized['commitments'][0]['id'], 'commit_1')

    def test_empty_virtual_entities_not_serialized(self):
        """Empty virtual entity collections should not appear in serialized output."""
        game_data = {
            'metadata': {
                'title': 'Test Game',
                'version': '0.1.0'
            },
            'locations': [
                {
                    'id': 'loc_start',
                    'name': 'Start Location',
                    'description': 'The starting location'
                }
            ],
            'items': [],
            'locks': [],
            'actors': {
                'player': {
                    'id': 'player',
                    'name': 'Adventurer',
                    'description': 'A brave soul',
                    'location': 'loc_start',
                    'inventory': []
                }
            }
        }

        state = load_game_state(game_data)
        serialized = game_state_to_dict(state)

        # Empty collections should not be in output
        self.assertNotIn('commitments', serialized)
        self.assertNotIn('scheduled_events', serialized)
        self.assertNotIn('gossip', serialized)
        self.assertNotIn('spreads', serialized)


if __name__ == '__main__':
    unittest.main()
