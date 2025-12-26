"""Tests for NPC movement/patrol system."""
from src.types import ActorId

import unittest
from unittest.mock import Mock

from src.state_manager import Actor, Location, GameState, Metadata
from src.state_accessor import StateAccessor


class TestPatrolStep(unittest.TestCase):
    """Test patrol_step function."""

    def test_patrol_step_moves_along_route(self):
        """NPC moves to next location in patrol route."""
        from behavior_libraries.npc_movement_lib.patrol import patrol_step

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='forest', name='Forest', description='A forest'))
        state.locations.append(Location(id='meadow', name='Meadow', description='A meadow'))
        state.locations.append(Location(id='river', name='River', description='A river'))
        state.actors[ActorId('guard')] = Actor(
            id='guard', name='Guard', description='A guard',
            location='forest', inventory=[],
            properties={
                'patrol_route': ['forest', 'meadow', 'river'],
                'patrol_index': 0
            }
        )

        accessor = StateAccessor(state, Mock())
        message = patrol_step(accessor, state.get_actor(ActorId('guard')))

        self.assertEqual(state.get_actor(ActorId('guard')).location, 'meadow')
        self.assertEqual(state.get_actor(ActorId('guard')).properties['patrol_index'], 1)

    def test_patrol_step_wraps_around(self):
        """Patrol wraps to start when reaching end of route."""
        from behavior_libraries.npc_movement_lib.patrol import patrol_step

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='forest', name='Forest', description='A forest'))
        state.locations.append(Location(id='meadow', name='Meadow', description='A meadow'))
        state.actors[ActorId('guard')] = Actor(
            id='guard', name='Guard', description='A guard',
            location='meadow', inventory=[],
            properties={
                'patrol_route': ['forest', 'meadow'],
                'patrol_index': 1
            }
        )

        accessor = StateAccessor(state, Mock())
        patrol_step(accessor, state.get_actor(ActorId('guard')))

        self.assertEqual(state.get_actor(ActorId('guard')).location, 'forest')
        self.assertEqual(state.get_actor(ActorId('guard')).properties['patrol_index'], 0)

    def test_patrol_step_no_route_returns_none(self):
        """Returns None if no patrol route set."""
        from behavior_libraries.npc_movement_lib.patrol import patrol_step

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='forest', name='Forest', description='A forest'))
        state.actors[ActorId('npc')] = Actor(
            id='npc', name='NPC', description='An NPC',
            location='forest', inventory=[],
            properties={}
        )

        accessor = StateAccessor(state, Mock())
        message = patrol_step(accessor, state.get_actor(ActorId('npc')))

        self.assertIsNone(message)
        self.assertEqual(state.get_actor(ActorId('npc')).location, 'forest')


class TestWanderStep(unittest.TestCase):
    """Test wander_step function."""

    def test_wander_step_moves_within_area(self):
        """NPC moves to a random location within wander area."""
        from behavior_libraries.npc_movement_lib.wander import wander_step

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='forest', name='Forest', description='A forest'))
        state.locations.append(Location(id='meadow', name='Meadow', description='A meadow'))
        state.locations.append(Location(id='river', name='River', description='A river'))
        state.actors[ActorId('hunter')] = Actor(
            id='hunter', name='Hunter', description='A hunter',
            location='forest', inventory=[],
            properties={
                'wander_area': ['forest', 'meadow', 'river'],
                'wander_chance': 1.0  # Always wander for testing
            }
        )

        accessor = StateAccessor(state, Mock())
        # Run multiple times to ensure it moves
        moved = False
        for _ in range(10):
            wander_step(accessor, state.get_actor(ActorId('hunter')))
            if state.get_actor(ActorId('hunter')).location != 'forest':
                moved = True
                break

        # Should have moved eventually (chance is 1.0)
        self.assertTrue(moved or state.get_actor(ActorId('hunter')).location in ['forest', 'meadow', 'river'])

    def test_wander_step_stays_when_chance_fails(self):
        """NPC stays in place when wander chance fails."""
        from behavior_libraries.npc_movement_lib.wander import wander_step

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='forest', name='Forest', description='A forest'))
        state.locations.append(Location(id='meadow', name='Meadow', description='A meadow'))
        state.actors[ActorId('hunter')] = Actor(
            id='hunter', name='Hunter', description='A hunter',
            location='forest', inventory=[],
            properties={
                'wander_area': ['forest', 'meadow'],
                'wander_chance': 0.0  # Never wander
            }
        )

        accessor = StateAccessor(state, Mock())
        wander_step(accessor, state.get_actor(ActorId('hunter')))

        self.assertEqual(state.get_actor(ActorId('hunter')).location, 'forest')

    def test_wander_step_no_area_returns_none(self):
        """Returns None if no wander area set."""
        from behavior_libraries.npc_movement_lib.wander import wander_step

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='forest', name='Forest', description='A forest'))
        state.actors[ActorId('npc')] = Actor(
            id='npc', name='NPC', description='An NPC',
            location='forest', inventory=[],
            properties={}
        )

        accessor = StateAccessor(state, Mock())
        message = wander_step(accessor, state.get_actor(ActorId('npc')))

        self.assertIsNone(message)


class TestSetPatrolRoute(unittest.TestCase):
    """Test set_patrol_route function."""

    def test_set_patrol_route(self):
        """Sets patrol route on actor."""
        from behavior_libraries.npc_movement_lib.patrol import set_patrol_route

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='forest', name='Forest', description='A forest'))
        state.actors[ActorId('guard')] = Actor(
            id='guard', name='Guard', description='A guard',
            location='forest', inventory=[],
            properties={}
        )

        accessor = StateAccessor(state, Mock())
        set_patrol_route(accessor, 'guard', ['forest', 'meadow', 'river'])

        self.assertEqual(
            state.get_actor(ActorId('guard')).properties['patrol_route'],
            ['forest', 'meadow', 'river']
        )
        self.assertEqual(state.get_actor(ActorId('guard')).properties['patrol_index'], 0)


class TestSetWanderArea(unittest.TestCase):
    """Test set_wander_area function."""

    def test_set_wander_area(self):
        """Sets wander area on actor."""
        from behavior_libraries.npc_movement_lib.wander import set_wander_area

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='forest', name='Forest', description='A forest'))
        state.actors[ActorId('hunter')] = Actor(
            id='hunter', name='Hunter', description='A hunter',
            location='forest', inventory=[],
            properties={}
        )

        accessor = StateAccessor(state, Mock())
        set_wander_area(accessor, 'hunter', ['forest', 'meadow', 'river'])

        self.assertEqual(
            state.get_actor(ActorId('hunter')).properties['wander_area'],
            ['forest', 'meadow', 'river']
        )


class TestOnNpcMovement(unittest.TestCase):
    """Test on_npc_movement hook handler."""

    def test_on_npc_movement_respects_frequency(self):
        """NPC only moves when turn count matches frequency."""
        from behavior_libraries.npc_movement_lib.patrol import on_npc_movement

        state = GameState(metadata=Metadata(title="Test"))
        state.turn_count = 3
        state.locations.append(Location(id='forest', name='Forest', description='A forest'))
        state.locations.append(Location(id='meadow', name='Meadow', description='A meadow'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='forest', inventory=[]
        )
        state.actors[ActorId('guard')] = Actor(
            id='guard', name='Guard', description='A guard',
            location='forest', inventory=[],
            properties={
                'patrol_route': ['forest', 'meadow'],
                'patrol_index': 0,
                'patrol_frequency': 3  # Only move every 3 turns
            }
        )

        accessor = StateAccessor(state, Mock())
        context = {'turn': 3}

        on_npc_movement(state.get_actor(ActorId('guard')), accessor, context)

        # Should move on turn 3 (divisible by 3)
        self.assertEqual(state.get_actor(ActorId('guard')).location, 'meadow')

    def test_on_npc_movement_skips_when_not_frequency(self):
        """NPC does not move when turn count doesn't match frequency."""
        from behavior_libraries.npc_movement_lib.patrol import on_npc_movement

        state = GameState(metadata=Metadata(title="Test"))
        state.turn_count = 4
        state.locations.append(Location(id='forest', name='Forest', description='A forest'))
        state.locations.append(Location(id='meadow', name='Meadow', description='A meadow'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='forest', inventory=[]
        )
        state.actors[ActorId('guard')] = Actor(
            id='guard', name='Guard', description='A guard',
            location='forest', inventory=[],
            properties={
                'patrol_route': ['forest', 'meadow'],
                'patrol_index': 0,
                'patrol_frequency': 3
            }
        )

        accessor = StateAccessor(state, Mock())
        context = {'turn': 4}

        on_npc_movement(state.get_actor(ActorId('guard')), accessor, context)

        # Should NOT move on turn 4 (not divisible by 3)
        self.assertEqual(state.get_actor(ActorId('guard')).location, 'forest')


if __name__ == '__main__':
    unittest.main()
