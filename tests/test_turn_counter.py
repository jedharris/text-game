"""Tests for turn counter functionality."""
from src.types import ActorId

import unittest
import json
import tempfile
from pathlib import Path

from src.state_manager import GameState, Metadata, load_game_state, game_state_to_dict


class TestTurnCounterBasic(unittest.TestCase):
    """Test basic turn counter operations."""

    def test_initial_turn_count_is_zero(self):
        """New game state should have turn_count = 0."""
        state = GameState(metadata=Metadata(title="Test"))
        self.assertEqual(state.turn_count, 0)

    def test_increment_turn_increases_count(self):
        """increment_turn should increase turn_count by 1."""
        state = GameState(metadata=Metadata(title="Test"))
        self.assertEqual(state.turn_count, 0)

        result = state.increment_turn()

        self.assertEqual(state.turn_count, 1)
        self.assertEqual(result, 1)

    def test_increment_turn_returns_new_value(self):
        """increment_turn should return the new turn count."""
        state = GameState(metadata=Metadata(title="Test"))
        state.turn_count = 5

        result = state.increment_turn()

        self.assertEqual(result, 6)

    def test_multiple_increments(self):
        """Multiple calls to increment_turn should accumulate."""
        state = GameState(metadata=Metadata(title="Test"))

        for i in range(10):
            state.increment_turn()

        self.assertEqual(state.turn_count, 10)


class TestTurnCounterSerialization(unittest.TestCase):
    """Test turn counter serialization/deserialization."""

    def test_turn_count_serialized_when_nonzero(self):
        """turn_count should be included in serialization when > 0."""
        state = GameState(metadata=Metadata(title="Test"))
        state.turn_count = 42

        data = game_state_to_dict(state)

        self.assertIn('turn_count', data)
        self.assertEqual(data['turn_count'], 42)

    def test_turn_count_not_serialized_when_zero(self):
        """turn_count should be omitted from serialization when = 0."""
        state = GameState(metadata=Metadata(title="Test"))
        state.turn_count = 0

        data = game_state_to_dict(state)

        self.assertNotIn('turn_count', data)

    def test_turn_count_loaded_from_save(self):
        """turn_count should be restored when loading saved game."""
        data = {
            'metadata': {'title': 'Test'},
            'turn_count': 100,
            'locations': [{'id': 'start', 'name': 'Start', 'description': 'A room'}],
            'items': [],
            'locks': [],
            'actors': {
                'player': {
                    'id': 'player',
                    'name': 'Adventurer',
                    'description': 'The player',
                    'location': 'start',
                    'inventory': []
                }
            }
        }

        state = load_game_state(data)

        self.assertEqual(state.turn_count, 100)

    def test_turn_count_defaults_to_zero_when_missing(self):
        """turn_count should default to 0 if not in save data."""
        data = {
            'metadata': {'title': 'Test'},
            'locations': [{'id': 'start', 'name': 'Start', 'description': 'A room'}],
            'items': [],
            'locks': [],
            'actors': {
                'player': {
                    'id': 'player',
                    'name': 'Adventurer',
                    'description': 'The player',
                    'location': 'start',
                    'inventory': []
                }
            }
        }

        state = load_game_state(data)

        self.assertEqual(state.turn_count, 0)

    def test_turn_count_roundtrip(self):
        """turn_count should survive save/load roundtrip."""
        from src.state_manager import Actor, Location

        original = GameState(metadata=Metadata(title="Test"))
        original.turn_count = 75

        # Add minimal location and player for validation
        original.locations.append(Location(
            id='start',
            name='Start',
            description='A room'
        ))
        original.actors[ActorId('player')] = Actor(
            id='player',
            name='Adventurer',
            description='The player',
            location='start',
            inventory=[]
        )

        # Serialize and deserialize
        data = game_state_to_dict(original)
        loaded = load_game_state(data)

        self.assertEqual(loaded.turn_count, 75)


class TestTurnCounterIntegration(unittest.TestCase):
    """Test turn counter integration with game engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_data = {
            'metadata': {'title': 'Turn Test'},
            'locations': [{
                'id': 'start',
                'name': 'Start',
                'description': 'Starting location'
            }],
            'items': [{
                'id': 'rock',
                'name': 'rock',
                'description': 'A rock',
                'location': 'start',
                'properties': {'portable': True}
            }],
            'locks': [],
            'actors': {
                'player': {
                    'id': 'player',
                    'name': 'Adventurer',
                    'description': 'The player',
                    'location': 'start',
                    'inventory': []
                }
            }
        }

    def test_turn_increments_on_successful_command(self):
        """Turn counter should increment after successful command."""
        from src.llm_protocol import LLMProtocolHandler
        from src.state_manager import load_game_state
        from src.word_entry import WordEntry, WordType

        state = load_game_state(self.game_data)
        handler = LLMProtocolHandler(state)

        self.assertEqual(state.turn_count, 0)

        # Execute a successful command (take rock)
        rock_word = WordEntry(word="rock", word_type=WordType.NOUN, synonyms=[])
        handler.handle_message({
            'type': 'command',
            'action': {
                'verb': 'take',
                'object': rock_word
            }
        })

        self.assertEqual(state.turn_count, 1)

    def test_turn_increments_multiple_commands(self):
        """Turn counter should increment for each successful command."""
        from src.llm_protocol import LLMProtocolHandler
        from src.state_manager import load_game_state
        from src.word_entry import WordEntry, WordType

        state = load_game_state(self.game_data)
        handler = LLMProtocolHandler(state)

        rock_word = WordEntry(word="rock", word_type=WordType.NOUN, synonyms=[])

        # Execute several commands
        handler.handle_message({
            'type': 'command',
            'action': {'verb': 'take', 'object': rock_word}
        })
        handler.handle_message({
            'type': 'command',
            'action': {'verb': 'drop', 'object': rock_word}
        })
        handler.handle_message({
            'type': 'command',
            'action': {'verb': 'take', 'object': rock_word}
        })

        self.assertEqual(state.turn_count, 3)

    def test_turn_does_not_increment_on_failed_command(self):
        """Turn counter should not increment when command fails."""
        from src.llm_protocol import LLMProtocolHandler
        from src.state_manager import load_game_state
        from src.word_entry import WordEntry, WordType

        state = load_game_state(self.game_data)
        handler = LLMProtocolHandler(state)

        self.assertEqual(state.turn_count, 0)

        # Try to take an item that doesn't exist
        fake_word = WordEntry(word="diamond", word_type=WordType.NOUN, synonyms=[])
        result = handler.handle_message({
            'type': 'command',
            'action': {'verb': 'take', 'object': fake_word}
        })

        # Command should fail (no diamond) and turn should not increment
        self.assertFalse(result.get('success', True))
        self.assertEqual(state.turn_count, 0)


if __name__ == '__main__':
    unittest.main()
