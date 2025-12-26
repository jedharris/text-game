"""Tests for companion following system."""
from src.types import ActorId

import unittest
from unittest.mock import Mock, MagicMock

from src.state_manager import Actor, Location, GameState, Metadata
from src.state_accessor import StateAccessor


class TestGetCompanions(unittest.TestCase):
    """Test get_companions function."""

    def test_get_companions_returns_actors_with_is_companion(self):
        """Returns all actors with is_companion=True at player's location."""
        from behavior_libraries.companion_lib.following import get_companions

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='forest', name='Forest', description='A forest'
        ))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='forest', inventory=[]
        )
        state.actors[ActorId('wolf')] = Actor(
            id='wolf', name='Wolf', description='A tame wolf',
            location='forest', inventory=[],
            properties={'is_companion': True}
        )
        state.actors[ActorId('deer')] = Actor(
            id='deer', name='Deer', description='A deer',
            location='forest', inventory=[],
            properties={}
        )

        accessor = StateAccessor(state, Mock())
        companions = get_companions(accessor)

        self.assertEqual(len(companions), 1)
        self.assertEqual(companions[0].id, 'wolf')

    def test_get_companions_empty_when_none(self):
        """Returns empty list when no companions exist."""
        from behavior_libraries.companion_lib.following import get_companions

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='forest', name='Forest', description='A forest'
        ))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='forest', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        companions = get_companions(accessor)

        self.assertEqual(companions, [])

    def test_get_companions_only_at_player_location(self):
        """Only returns companions at player's current location."""
        from behavior_libraries.companion_lib.following import get_companions

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='forest', name='Forest', description='A forest'
        ))
        state.locations.append(Location(
            id='cave', name='Cave', description='A cave'
        ))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='forest', inventory=[]
        )
        state.actors[ActorId('wolf')] = Actor(
            id='wolf', name='Wolf', description='A tame wolf',
            location='cave', inventory=[],
            properties={'is_companion': True}
        )

        accessor = StateAccessor(state, Mock())
        companions = get_companions(accessor)

        self.assertEqual(companions, [])


class TestMakeCompanion(unittest.TestCase):
    """Test make_companion function."""

    def test_make_companion_sets_is_companion(self):
        """make_companion sets is_companion property to True."""
        from behavior_libraries.companion_lib.following import make_companion

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='forest', name='Forest', description='A forest'
        ))
        state.actors[ActorId('wolf')] = Actor(
            id='wolf', name='Wolf', description='A wolf',
            location='forest', inventory=[],
            properties={}
        )

        accessor = StateAccessor(state, Mock())
        make_companion(accessor, 'wolf')

        self.assertTrue(state.get_actor(ActorId('wolf')).properties.get('is_companion'))

    def test_make_companion_nonexistent_actor(self):
        """make_companion with nonexistent actor raises KeyError (authoring error)."""
        from behavior_libraries.companion_lib.following import make_companion

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='forest', name='Forest', description='A forest'
        ))

        accessor = StateAccessor(state, Mock())
        with self.assertRaises(KeyError) as ctx:
            make_companion(accessor, 'nonexistent')
        self.assertIn("Actor not found", str(ctx.exception))


class TestDismissCompanion(unittest.TestCase):
    """Test dismiss_companion function."""

    def test_dismiss_companion_removes_is_companion(self):
        """dismiss_companion removes is_companion property."""
        from behavior_libraries.companion_lib.following import dismiss_companion

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='forest', name='Forest', description='A forest'
        ))
        state.actors[ActorId('wolf')] = Actor(
            id='wolf', name='Wolf', description='A wolf',
            location='forest', inventory=[],
            properties={'is_companion': True}
        )

        accessor = StateAccessor(state, Mock())
        dismiss_companion(accessor, 'wolf')

        self.assertFalse(state.get_actor(ActorId('wolf')).properties.get('is_companion', False))


class TestCheckCanFollow(unittest.TestCase):
    """Test check_can_follow function."""

    def test_can_follow_no_restrictions(self):
        """Companion with no restrictions can follow anywhere."""
        from behavior_libraries.companion_lib.following import check_can_follow

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='town', name='Town', description='A town'
        ))
        state.actors[ActorId('wolf')] = Actor(
            id='wolf', name='Wolf', description='A wolf',
            location='forest', inventory=[],
            properties={'is_companion': True}
        )

        accessor = StateAccessor(state, Mock())
        can_follow, message = check_can_follow(accessor, state.get_actor(ActorId('wolf')), 'town')

        self.assertTrue(can_follow)
        self.assertEqual(message, '')

    def test_cannot_follow_location_restriction(self):
        """Companion with location_restrictions cannot enter restricted locations."""
        from behavior_libraries.companion_lib.following import check_can_follow

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='town', name='Town', description='A town'
        ))
        state.actors[ActorId('wolf')] = Actor(
            id='wolf', name='Wolf', description='A wolf',
            location='forest', inventory=[],
            properties={
                'is_companion': True,
                'location_restrictions': ['town'],
                'cannot_follow_message': "The wolf refuses to enter the town."
            }
        )

        accessor = StateAccessor(state, Mock())
        can_follow, message = check_can_follow(accessor, state.get_actor(ActorId('wolf')), 'town')

        self.assertFalse(can_follow)
        self.assertEqual(message, "The wolf refuses to enter the town.")

    def test_cannot_follow_terrain_restriction(self):
        """Companion with terrain_restrictions cannot enter locations with that terrain."""
        from behavior_libraries.companion_lib.following import check_can_follow

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='lake', name='Lake', description='A lake',
            properties={'terrain': 'underwater'}
        ))
        state.actors[ActorId('wolf')] = Actor(
            id='wolf', name='Wolf', description='A wolf',
            location='forest', inventory=[],
            properties={
                'is_companion': True,
                'terrain_restrictions': ['underwater']
            }
        )

        accessor = StateAccessor(state, Mock())
        can_follow, message = check_can_follow(accessor, state.get_actor(ActorId('wolf')), 'lake')

        self.assertFalse(can_follow)
        self.assertIn('wolf', message.lower())

    def test_default_cannot_follow_message(self):
        """Uses default message when cannot_follow_message not set."""
        from behavior_libraries.companion_lib.following import check_can_follow

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='town', name='Town', description='A town'
        ))
        state.actors[ActorId('wolf')] = Actor(
            id='wolf', name='Wolf', description='A wolf',
            location='forest', inventory=[],
            properties={
                'is_companion': True,
                'location_restrictions': ['town']
            }
        )

        accessor = StateAccessor(state, Mock())
        can_follow, message = check_can_follow(accessor, state.get_actor(ActorId('wolf')), 'town')

        self.assertFalse(can_follow)
        self.assertIn('Wolf', message)


class TestOnPlayerMoveCompanionsFollow(unittest.TestCase):
    """Test on_player_move_companions_follow hook handler."""

    def test_companion_follows_player(self):
        """Companion at player's previous location follows to new location."""
        from behavior_libraries.companion_lib.following import on_player_move_companions_follow
        from src.behavior_manager import EventResult

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='forest', name='Forest', description='A forest'
        ))
        state.locations.append(Location(
            id='meadow', name='Meadow', description='A meadow'
        ))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='meadow', inventory=[]  # Player already moved
        )
        state.actors[ActorId('wolf')] = Actor(
            id='wolf', name='Wolf', description='A wolf',
            location='forest', inventory=[],
            properties={
                'is_companion': True,
                'follow_message': 'The wolf lopes along beside you.'
            }
        )

        accessor = StateAccessor(state, Mock())
        # Context includes previous location
        context = {
            'actor_id': 'player',
            'from_location': 'forest',
            'to_location': 'meadow'
        }

        result = on_player_move_companions_follow(
            state.locations[1],  # destination (meadow)
            accessor,
            context
        )

        # Wolf should have moved
        self.assertEqual(state.get_actor(ActorId('wolf')).location, 'meadow')
        # Result should include follow message
        self.assertIsInstance(result, EventResult)
        self.assertIn('wolf', result.feedback.lower())

    def test_companion_stays_when_restricted(self):
        """Companion stays at previous location when restricted from destination."""
        from behavior_libraries.companion_lib.following import on_player_move_companions_follow

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='forest', name='Forest', description='A forest'
        ))
        state.locations.append(Location(
            id='town', name='Town', description='A town'
        ))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='town', inventory=[]
        )
        state.actors[ActorId('wolf')] = Actor(
            id='wolf', name='Wolf', description='A wolf',
            location='forest', inventory=[],
            properties={
                'is_companion': True,
                'location_restrictions': ['town'],
                'cannot_follow_message': 'The wolf refuses to enter the town.'
            }
        )

        accessor = StateAccessor(state, Mock())
        context = {
            'actor_id': 'player',
            'from_location': 'forest',
            'to_location': 'town'
        }

        result = on_player_move_companions_follow(
            state.locations[1],  # destination (town)
            accessor,
            context
        )

        # Wolf should NOT have moved
        self.assertEqual(state.get_actor(ActorId('wolf')).location, 'forest')
        # Result should include cannot follow message
        self.assertIn('refuses', result.feedback.lower())

    def test_multiple_companions(self):
        """Multiple companions all follow if able."""
        from behavior_libraries.companion_lib.following import on_player_move_companions_follow

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='forest', name='Forest', description='A forest'
        ))
        state.locations.append(Location(
            id='meadow', name='Meadow', description='A meadow'
        ))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='meadow', inventory=[]
        )
        state.actors[ActorId('wolf')] = Actor(
            id='wolf', name='Wolf', description='A wolf',
            location='forest', inventory=[],
            properties={'is_companion': True}
        )
        state.actors[ActorId('dog')] = Actor(
            id='dog', name='Dog', description='A dog',
            location='forest', inventory=[],
            properties={'is_companion': True}
        )

        accessor = StateAccessor(state, Mock())
        context = {
            'actor_id': 'player',
            'from_location': 'forest',
            'to_location': 'meadow'
        }

        on_player_move_companions_follow(
            state.locations[1],
            accessor,
            context
        )

        # Both should have moved
        self.assertEqual(state.get_actor(ActorId('wolf')).location, 'meadow')
        self.assertEqual(state.get_actor(ActorId('dog')).location, 'meadow')

    def test_no_companions_no_message(self):
        """When no companions, result allows but has no message."""
        from behavior_libraries.companion_lib.following import on_player_move_companions_follow

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='forest', name='Forest', description='A forest'
        ))
        state.locations.append(Location(
            id='meadow', name='Meadow', description='A meadow'
        ))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='meadow', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        context = {
            'actor_id': 'player',
            'from_location': 'forest',
            'to_location': 'meadow'
        }

        result = on_player_move_companions_follow(
            state.locations[1],
            accessor,
            context
        )

        # Should allow but with empty message
        self.assertTrue(result.allow)
        self.assertEqual(result.feedback, '')


if __name__ == '__main__':
    unittest.main()
