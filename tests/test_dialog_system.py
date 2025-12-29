"""Tests for dialog/conversation system."""
from typing import Any

from src.types import ActorId, LocationId

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
        state.locations.append(Location(id=LocationId('start'), name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id=ActorId('player'), name='Hero', description='The hero',
            location=LocationId('start'), inventory=[]
        )
        state.actors[ActorId('scholar')] = Actor(
            id=ActorId('scholar'), name='Scholar', description='A scholar',
            location=LocationId('start'), inventory=[],
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
        topics = get_available_topics(accessor, state.get_actor(ActorId('scholar')))

        self.assertIn('infection', topics)

    def test_get_available_topics_with_requirements(self):
        """Excludes topics when requirements not met."""
        from behavior_libraries.dialog_lib.topics import get_available_topics

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id=LocationId('start'), name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id=ActorId('player'), name='Hero', description='The hero',
            location=LocationId('start'), inventory=[],
            properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id=ActorId('scholar'), name='Scholar', description='A scholar',
            location=LocationId('start'), inventory=[],
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
        topics = get_available_topics(accessor, state.get_actor(ActorId('scholar')))

        self.assertNotIn('cure', topics)

    def test_get_available_topics_requirements_satisfied(self):
        """Includes topics when requirements are met."""
        from behavior_libraries.dialog_lib.topics import get_available_topics

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id=LocationId('start'), name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id=ActorId('player'), name='Hero', description='The hero',
            location=LocationId('start'), inventory=[],
            properties={'flags': {'knows_about_infection': True}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id=ActorId('scholar'), name='Scholar', description='A scholar',
            location=LocationId('start'), inventory=[],
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
        topics = get_available_topics(accessor, state.get_actor(ActorId('scholar')))

        self.assertIn('cure', topics)


class TestGetTopicHints(unittest.TestCase):
    """Test get_topic_hints function."""

    def test_get_topic_hints(self):
        """Returns hint keywords for available topics."""
        from behavior_libraries.dialog_lib.topics import get_topic_hints

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id=LocationId('start'), name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id=ActorId('player'), name='Hero', description='The hero',
            location=LocationId('start'), inventory=[]
        )
        state.actors[ActorId('scholar')] = Actor(
            id=ActorId('scholar'), name='Scholar', description='A scholar',
            location=LocationId('start'), inventory=[],
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
        hints = get_topic_hints(accessor, state.get_actor(ActorId('scholar')))

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
            _properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            _properties={
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
        result = handle_ask_about(accessor, state.get_actor(ActorId('scholar')), 'sick')

        self.assertTrue(result.success)
        self.assertIn('infection', result.response.lower())

    def test_handle_ask_about_sets_flags(self):
        """Sets flags when topic is discussed."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[],
            _properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            _properties={
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
        handle_ask_about(accessor, state.get_actor(ActorId('scholar')), 'infection')

        self.assertTrue(state.get_actor(ActorId('player')).properties['flags'].get('knows_about_infection'))

    def test_handle_ask_about_unlocks_topics(self):
        """Unlocks new topics when discussed."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[],
            _properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            _properties={
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
        handle_ask_about(accessor, state.get_actor(ActorId('scholar')), 'infection')

        unlocked = state.get_actor(ActorId('scholar')).properties.get('unlocked_topics', [])
        self.assertIn('cure', unlocked)

    def test_handle_ask_about_unknown_topic(self):
        """Returns default message for unknown topic."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[],
            _properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            _properties={
                'dialog_topics': {},
                'default_topic_summary': "The scholar shrugs. 'I don't know about that.'"
            }
        )

        accessor = StateAccessor(state, Mock())
        result = handle_ask_about(accessor, state.get_actor(ActorId('scholar')), 'dragons')

        self.assertTrue(result.success)  # Still succeeds, just with default message
        self.assertIn("don't know", result.response.lower())


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
            _properties={
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
        result = handle_talk_to(accessor, state.get_actor(ActorId('scholar')))

        self.assertTrue(result.success)
        self.assertIn('infection', result.response.lower())


class TestRequiresState(unittest.TestCase):
    """Tests for requires_state gating in dialog topics."""

    def _make_game_state_with_npc(self, npc_state: str | None, topic_requires_state):
        """Create a game state with an NPC that has a state machine.

        Args:
            npc_state: Current state of the NPC's state machine, or None for no machine
            topic_requires_state: Value for topic's requires_state field

        Returns:
            Tuple of (GameState, Accessor, NPC)
        """
        from behavior_libraries.dialog_lib.topics import get_available_topics

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id=LocationId('start'), name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id=ActorId('player'), name='Hero', description='The hero',
            location=LocationId('start'), inventory=[]
        )

        npc_props: dict[str, Any] = {
            'dialog_topics': {
                'teaching': {
                    'keywords': ['teach', 'learn'],
                    'summary': 'I can teach you now.',
                    'requires_state': topic_requires_state
                }
            }
        }
        if npc_state is not None:
            npc_props['state_machine'] = {'current': npc_state}

        state.actors[ActorId('scholar')] = Actor(
            id=ActorId('scholar'), name='Scholar', description='A scholar',
            location=LocationId('start'), inventory=[],
            properties=npc_props
        )

        accessor = StateAccessor(state, Mock())
        return state, accessor, state.get_actor(ActorId('scholar'))

    def test_requires_state_single_value_matches(self):
        """Topic with requires_state='cured' available when NPC in 'cured' state."""
        from behavior_libraries.dialog_lib.topics import get_available_topics

        _, accessor, npc = self._make_game_state_with_npc(
            npc_state='cured',
            topic_requires_state='cured'
        )

        topics = get_available_topics(accessor, npc)
        self.assertIn('teaching', topics)

    def test_requires_state_single_value_no_match(self):
        """Topic with requires_state='cured' hidden when NPC in 'critical' state."""
        from behavior_libraries.dialog_lib.topics import get_available_topics

        _, accessor, npc = self._make_game_state_with_npc(
            npc_state='critical',
            topic_requires_state='cured'
        )

        topics = get_available_topics(accessor, npc)
        self.assertNotIn('teaching', topics)

    def test_requires_state_list_matches(self):
        """Topic with requires_state=['stabilized', 'cured'] available in either state."""
        from behavior_libraries.dialog_lib.topics import get_available_topics

        _, accessor, npc = self._make_game_state_with_npc(
            npc_state='stabilized',
            topic_requires_state=['stabilized', 'cured']
        )

        topics = get_available_topics(accessor, npc)
        self.assertIn('teaching', topics)

    def test_requires_state_list_no_match(self):
        """Topic with requires_state=['stabilized', 'cured'] hidden when in 'critical'."""
        from behavior_libraries.dialog_lib.topics import get_available_topics

        _, accessor, npc = self._make_game_state_with_npc(
            npc_state='critical',
            topic_requires_state=['stabilized', 'cured']
        )

        topics = get_available_topics(accessor, npc)
        self.assertNotIn('teaching', topics)

    def test_no_requires_state_always_available(self):
        """Topic without requires_state is available regardless of NPC state."""
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
            _properties={
                'dialog_topics': {
                    'greeting': {
                        'keywords': ['hello', 'hi'],
                        'summary': 'Hello there!'
                        # No requires_state
                    }
                },
                'state_machine': {'current': 'any_state'}
            }
        )

        accessor = StateAccessor(state, Mock())
        topics = get_available_topics(accessor, state.get_actor(ActorId('scholar')))
        self.assertIn('greeting', topics)

    def test_requires_state_no_state_machine(self):
        """Topic with requires_state hidden if NPC has no state_machine."""
        from behavior_libraries.dialog_lib.topics import get_available_topics

        _, accessor, npc = self._make_game_state_with_npc(
            npc_state=None,  # No state machine
            topic_requires_state='cured'
        )

        topics = get_available_topics(accessor, npc)
        self.assertNotIn('teaching', topics)


class TestRequiresTrust(unittest.TestCase):
    """Tests for requires_trust gating in dialog topics."""

    def _make_game_state_with_trust(
        self, npc_trust: int, topic_requires_trust: int | None
    ) -> tuple[GameState, StateAccessor, Actor]:
        """Create game state with NPC having specific trust level.

        Args:
            npc_trust: Current NPC trust level
            topic_requires_trust: Required trust for topic (None = no requirement)

        Returns:
            Tuple of (GameState, Accessor, NPC)
        """
        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id=LocationId('start'), name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id=ActorId('player'), name='Hero', description='The hero',
            location=LocationId('start'), inventory=[]
        )

        topic_config: dict[str, Any] = {
            'keywords': ['secret'],
            'summary': 'A secret is revealed.'
        }
        if topic_requires_trust is not None:
            topic_config['requires_trust'] = topic_requires_trust

        state.actors[ActorId('npc')] = Actor(
            id=ActorId('npc'), name='Dealer', description='A dealer',
            location=LocationId('start'), inventory=[],
            properties={
                'dialog_topics': {
                    'secret': topic_config
                },
                'trust_state': {'current': npc_trust}
            }
        )

        accessor = StateAccessor(state, Mock())
        return state, accessor, state.get_actor(ActorId('npc'))

    def test_requires_trust_met(self):
        """Topic available when trust requirement is met."""
        from behavior_libraries.dialog_lib.topics import get_available_topics

        _, accessor, npc = self._make_game_state_with_trust(
            npc_trust=3, topic_requires_trust=2
        )

        topics = get_available_topics(accessor, npc)
        self.assertIn('secret', topics)

    def test_requires_trust_exact(self):
        """Topic available when trust exactly equals requirement."""
        from behavior_libraries.dialog_lib.topics import get_available_topics

        _, accessor, npc = self._make_game_state_with_trust(
            npc_trust=2, topic_requires_trust=2
        )

        topics = get_available_topics(accessor, npc)
        self.assertIn('secret', topics)

    def test_requires_trust_not_met(self):
        """Topic hidden when trust requirement not met."""
        from behavior_libraries.dialog_lib.topics import get_available_topics

        _, accessor, npc = self._make_game_state_with_trust(
            npc_trust=1, topic_requires_trust=2
        )

        topics = get_available_topics(accessor, npc)
        self.assertNotIn('secret', topics)

    def test_no_requires_trust_always_available(self):
        """Topic without requires_trust is available regardless of trust level."""
        from behavior_libraries.dialog_lib.topics import get_available_topics

        _, accessor, npc = self._make_game_state_with_trust(
            npc_trust=0, topic_requires_trust=None
        )

        topics = get_available_topics(accessor, npc)
        self.assertIn('secret', topics)


class TestTrustDelta(unittest.TestCase):
    """Tests for trust_delta modification in dialog topics."""

    def _make_game_state_with_trust(self, initial_trust: int, trust_delta: int | None):
        """Create a game state with an NPC that has trust.

        Args:
            initial_trust: Initial trust value
            trust_delta: Value for topic's trust_delta field (None = no field)

        Returns:
            Tuple of (GameState, Accessor, NPC)
        """
        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id=LocationId('start'), name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id=ActorId('player'), name='Hero', description='The hero',
            location=LocationId('start'), inventory=[],
            properties={'flags': {}}
        )

        topic_config: dict[str, Any] = {
            'keywords': ['infection', 'sick'],
            'summary': 'The scholar explains the infection.'
        }
        if trust_delta is not None:
            topic_config['trust_delta'] = trust_delta

        state.actors[ActorId('scholar')] = Actor(
            id=ActorId('scholar'), name='Scholar', description='A scholar',
            location=LocationId('start'), inventory=[],
            properties={
                'dialog_topics': {
                    'infection': topic_config
                },
                'trust_state': {'current': initial_trust}
            }
        )

        accessor = StateAccessor(state, Mock())
        return state, accessor, state.get_actor(ActorId('scholar'))

    def test_trust_delta_positive(self):
        """Topic with trust_delta=2 increases NPC trust by 2."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about

        state, accessor, npc = self._make_game_state_with_trust(
            initial_trust=3,
            trust_delta=2
        )

        handle_ask_about(accessor, npc, 'infection')

        self.assertEqual(npc.properties['trust_state']['current'], 5)

    def test_trust_delta_negative(self):
        """Topic with trust_delta=-1 decreases NPC trust by 1."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about

        state, accessor, npc = self._make_game_state_with_trust(
            initial_trust=3,
            trust_delta=-1
        )

        handle_ask_about(accessor, npc, 'infection')

        self.assertEqual(npc.properties['trust_state']['current'], 2)

    def test_trust_delta_zero(self):
        """Topic with trust_delta=0 doesn't change trust."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about

        state, accessor, npc = self._make_game_state_with_trust(
            initial_trust=3,
            trust_delta=0
        )

        handle_ask_about(accessor, npc, 'infection')

        self.assertEqual(npc.properties['trust_state']['current'], 3)

    def test_no_trust_delta(self):
        """Topic without trust_delta doesn't change trust."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about

        state, accessor, npc = self._make_game_state_with_trust(
            initial_trust=3,
            trust_delta=None
        )

        handle_ask_about(accessor, npc, 'infection')

        self.assertEqual(npc.properties['trust_state']['current'], 3)

    def test_trust_delta_no_trust_state(self):
        """Topic with trust_delta initializes trust_state if missing."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[],
            _properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            _properties={
                'dialog_topics': {
                    'infection': {
                        'keywords': ['infection'],
                        'summary': 'The infection.',
                        'trust_delta': 2
                    }
                }
                # No trust_state
            }
        )

        accessor = StateAccessor(state, Mock())
        npc = state.get_actor(ActorId('scholar'))

        handle_ask_about(accessor, npc, 'infection')

        # Should initialize to 0 then add delta
        self.assertEqual(npc.properties['trust_state']['current'], 2)


class TestPerTopicHandler(unittest.TestCase):
    """Tests for per-topic handler invocation in dialog topics."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Clear any cached handlers
        from behavior_libraries.dialog_lib.handlers import clear_dialog_handler_cache
        clear_dialog_handler_cache()

    def test_topic_with_handler_invoked(self):
        """Topic with handler key invokes the handler function."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about
        from unittest.mock import patch, MagicMock
        from src.behavior_manager import EventResult

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[],
            _properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            _properties={
                'dialog_topics': {
                    'commitment': {
                        'keywords': ['promise', 'help'],
                        'summary': 'Default summary',
                        'handler': 'some.module:handler_func'
                    }
                }
            }
        )

        accessor = StateAccessor(state, Mock())
        npc = state.get_actor(ActorId('scholar'))

        # Mock the handler loading
        mock_handler = MagicMock(return_value=EventResult(allow=True, feedback="Handler response"))
        with patch('behavior_libraries.dialog_lib.topics._load_topic_handler', return_value=mock_handler):
            result = handle_ask_about(accessor, npc, 'promise')

        mock_handler.assert_called_once()
        self.assertEqual(result.response, "Handler response")

    def test_topic_handler_feedback_none_uses_summary(self):
        """If handler returns feedback=None, topic summary is used."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about
        from unittest.mock import patch, MagicMock
        from src.behavior_manager import EventResult

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[],
            _properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            _properties={
                'dialog_topics': {
                    'commitment': {
                        'keywords': ['promise', 'help'],
                        'summary': 'Fallback summary text',
                        'handler': 'some.module:handler_func'
                    }
                }
            }
        )

        accessor = StateAccessor(state, Mock())
        npc = state.get_actor(ActorId('scholar'))

        # Mock handler returns None feedback - should fall through to summary
        mock_handler = MagicMock(return_value=EventResult(allow=True, feedback=None))
        with patch('behavior_libraries.dialog_lib.topics._load_topic_handler', return_value=mock_handler):
            result = handle_ask_about(accessor, npc, 'promise')

        self.assertEqual(result.response, "Fallback summary text")

    def test_topic_handler_context_includes_topic_name(self):
        """Handler receives topic_name in context."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about
        from unittest.mock import patch, MagicMock
        from src.behavior_manager import EventResult

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[],
            _properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            _properties={
                'dialog_topics': {
                    'help_commitment': {
                        'keywords': ['promise', 'help'],
                        'summary': 'Summary',
                        'handler': 'some.module:handler_func'
                    }
                }
            }
        )

        accessor = StateAccessor(state, Mock())
        npc = state.get_actor(ActorId('scholar'))

        mock_handler = MagicMock(return_value=EventResult(allow=True, feedback="Response"))
        with patch('behavior_libraries.dialog_lib.topics._load_topic_handler', return_value=mock_handler):
            handle_ask_about(accessor, npc, 'promise')

        # Check the context passed to handler
        call_args = mock_handler.call_args
        context = call_args[0][2]  # Third positional arg is context
        self.assertEqual(context['topic_name'], 'help_commitment')
        self.assertEqual(context['keyword'], 'promise')

    def test_topic_without_handler_uses_summary(self):
        """Topic without handler returns its summary."""
        from behavior_libraries.dialog_lib.topics import handle_ask_about

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='start', name='Start', description='A room'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='start', inventory=[],
            _properties={'flags': {}}
        )
        state.actors[ActorId('scholar')] = Actor(
            id='scholar', name='Scholar', description='A scholar',
            location='start', inventory=[],
            _properties={
                'dialog_topics': {
                    'infection': {
                        'keywords': ['infection', 'sick'],
                        'summary': 'The infection is terrible.'
                        # No handler
                    }
                }
            }
        )

        accessor = StateAccessor(state, Mock())
        npc = state.get_actor(ActorId('scholar'))

        result = handle_ask_about(accessor, npc, 'infection')

        self.assertEqual(result.response, 'The infection is terrible.')


if __name__ == '__main__':
    unittest.main()
