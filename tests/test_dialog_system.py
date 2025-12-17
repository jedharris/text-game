"""Tests for dialog/conversation system."""
from src.types import ActorId

import unittest
from unittest.mock import Mock

from src.state_manager import Actor, Location, GameState, Metadata
from src.state_accessor import StateAccessor


class TestGetAvailableTopics(unittest.TestCase):
    """Test get_available_topics function."""

    def test_get_available_topics_no_requirements(self):
        """Returns topics with no requirements."""
        from behavior_libraries.dialog_lib.topics import get_available_topics

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[]
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            properties={
                'dialog_topics': {
                    'infection': {
                        'keywords': ['infection', 'sick'],
                        'summary': 'The scholar explains the infection.',
                        'requires_flags': {}
                    }
                }
            }
        )

        accessor = StateAccessor(state, Mock())
        topics = get_available_topics(accessor, state.actors[ActorId('scholar')])

        self.assertIn('infection', topics)

    def test_get_available_topics_with_requirements(self):
        """Excludes topics when requirements not met."""
        from behavior_libraries.dialog_lib.topics import get_available_topics

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[],
            properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            properties={
                'dialog_topics': {
                    'cure': {
                        'keywords': ['cure'],
                        'summary': 'The cure requires heartmoss.',
                        'requires_flags': {'knows_about_infection': True}
                    }
                }
            }
        )

        accessor = StateAccessor(state, Mock())
        topics = get_available_topics(accessor, state.actors[ActorId('scholar')])

        self.assertNotIn('cure', topics)

    def test_get_available_topics_requirements_satisfied(self):
        """Includes topics when requirements are met."""
        from behavior_libraries.dialog_lib.topics import get_available_topics

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[],
            properties={'flags': {'knows_about_infection': True}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            properties={
                'dialog_topics': {
                    'cure': {
                        'keywords': ['cure'],
                        'summary': 'The cure requires heartmoss.',
                        'requires_flags': {'knows_about_infection': True}
                    }
                }
            }
        )

        accessor = StateAccessor(state, Mock())
        topics = get_available_topics(accessor, state.actors[ActorId('scholar')])

        self.assertIn('cure', topics)


class TestGetTopicHints(unittest.TestCase):
    """Test get_topic_hints function."""

    def test_get_topic_hints(self):
        """Returns hint keywords for available topics."""
        from behavior_libraries.dialog_lib.topics import get_topic_hints

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[]
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            properties={
                'dialog_topics': {
                    'infection': {
                        'keywords': ['infection', 'sick', 'illness'],
                        'summary': 'The infection is spreading.',
                        'requires_flags': {}
                    }
                }
            }
        )

        accessor = StateAccessor(state, Mock())
        hints = get_topic_hints(accessor, state.actors[ActorId('scholar')])

        self.assertIn('infection', hints)


class TestHandleAskAbout(unittest.TestCase):
    """Test handle_ask_about function."""

    def test_handle_ask_about_matches_keyword(self):
        """Matches topic by keyword."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[],
            properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            properties={
                'dialog_topics': {
                    'infection': {
                        'keywords': ['infection', 'sick', 'illness'],
                        'summary': 'The scholar explains the infection.',
                        'sets_flags': {'knows_about_infection': True},
                        'requires_flags': {}
                    }
                }
            }
        )

        accessor = StateAccessor(state, Mock())
        result = handle_ask_about(accessor, state.actors[ActorId('scholar')], 'sick')

        self.assertTrue(result.success)
        self.assertIn('infection', result.message.lower())

    def test_handle_ask_about_sets_flags(self):
        """Sets flags when topic is discussed."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[],
            properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            properties={
                'dialog_topics': {
                    'infection': {
                        'keywords': ['infection'],
                        'summary': 'The infection spreads.',
                        'sets_flags': {'knows_about_infection': True},
                        'requires_flags': {}
                    }
                }
            }
        )

        accessor = StateAccessor(state, Mock())
        handle_ask_about(accessor, state.actors[ActorId('scholar')], 'infection')

        self.assertTrue(state.actors[ActorId('player')].properties['flags'].get('knows_about_infection'))

    def test_handle_ask_about_unlocks_topics(self):
        """Unlocks new topics when discussed."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[],
            properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            properties={
                'dialog_topics': {
                    'infection': {
                        'keywords': ['infection'],
                        'summary': 'The infection spreads.',
                        'unlocks_topics': ['cure'],
                        'sets_flags': {},
                        'requires_flags': {}
                    },
                    'cure': {
                        'keywords': ['cure'],
                        'summary': 'The cure requires heartmoss.',
                        'requires_flags': {'infection_discussed': True}
                    }
                },
                'unlocked_topics': []
            }
        )

        accessor = StateAccessor(state, Mock())
        handle_ask_about(accessor, state.actors[ActorId('scholar')], 'infection')

        unlocked = state.actors[ActorId('scholar')].properties.get('unlocked_topics', [])
        self.assertIn('cure', unlocked)

    def test_handle_ask_about_unknown_topic(self):
        """Returns default message for unknown topic."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[],
            properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            properties={
                'dialog_topics': {},
                'default_topic_summary': "The scholar shrugs. 'I don't know about that.'"
            }
        )

        accessor = StateAccessor(state, Mock())
        result = handle_ask_about(accessor, state.actors[ActorId('scholar')], 'dragons')

        self.assertTrue(result.success)  # Still succeeds, just with default message
        self.assertIn("don't know", result.message.lower())


class TestHandleTalkTo(unittest.TestCase):
    """Test handle_talk_to function."""

    def test_handle_talk_to_lists_topics(self):
        """Shows available topics when talking to NPC."""
        from behavior_libraries.dialog_lib.topics import handle_talk_to

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[]
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            properties={
                'dialog_topics': {
                    'infection': {
                        'keywords': ['infection', 'sick'],
                        'summary': 'About the infection.',
                        'requires_flags': {}
                    }
                }
            }
        )

        accessor = StateAccessor(state, Mock())
        result = handle_talk_to(accessor, state.actors[ActorId('scholar')])

        self.assertTrue(result.success)
        self.assertIn('infection', result.message.lower())


if __name__ == '__main__':
    unittest.main()
