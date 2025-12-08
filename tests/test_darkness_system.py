"""Tests for darkness/visibility system."""

import unittest
from unittest.mock import Mock

from src.state_manager import Actor, Item, Location, Part, GameState, Metadata
from src.state_accessor import StateAccessor


class TestCheckVisibility(unittest.TestCase):
    """Test check_visibility function."""

    def test_visibility_normal_location(self):
        """Location without requires_light is always visible."""
        from behavior_libraries.darkness_lib.visibility import check_visibility

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='meadow', name='Meadow', description='A sunny meadow',
            properties={}
        ))

        accessor = StateAccessor(state, Mock())
        visible = check_visibility(accessor, 'meadow')

        self.assertTrue(visible)

    def test_visibility_dark_location_no_light(self):
        """Location requiring light is not visible without light."""
        from behavior_libraries.darkness_lib.visibility import check_visibility

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='cave', name='Cave', description='A dark cave',
            properties={'requires_light': True}
        ))
        state.actors['player'] = Actor(
            id='player', name='Hero', description='The hero',
            location='cave', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        visible = check_visibility(accessor, 'cave')

        self.assertFalse(visible)

    def test_visibility_dark_location_with_carried_light(self):
        """Dark location is visible when player carries a lit light source."""
        from behavior_libraries.darkness_lib.visibility import check_visibility

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='cave', name='Cave', description='A dark cave',
            properties={'requires_light': True}
        ))
        state.items.append(Item(
            id='torch', name='Torch', description='A lit torch',
            location=None,
            properties={'provides_light': True, 'states': {'lit': True}}
        ))
        state.actors['player'] = Actor(
            id='player', name='Hero', description='The hero',
            location='cave', inventory=['torch']
        )

        accessor = StateAccessor(state, Mock())
        visible = check_visibility(accessor, 'cave')

        self.assertTrue(visible)

    def test_visibility_unlit_light_source_no_help(self):
        """Unlit light source does not provide visibility."""
        from behavior_libraries.darkness_lib.visibility import check_visibility

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='cave', name='Cave', description='A dark cave',
            properties={'requires_light': True}
        ))
        state.items.append(Item(
            id='torch', name='Torch', description='An unlit torch',
            location=None,
            properties={'provides_light': True, 'states': {'lit': False}}
        ))
        state.actors['player'] = Actor(
            id='player', name='Hero', description='The hero',
            location='cave', inventory=['torch']
        )

        accessor = StateAccessor(state, Mock())
        visible = check_visibility(accessor, 'cave')

        self.assertFalse(visible)

    def test_visibility_ambient_light_location(self):
        """Location with ambient_light is visible even if requires_light."""
        from behavior_libraries.darkness_lib.visibility import check_visibility

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='grotto', name='Grotto', description='A glowing grotto',
            properties={'requires_light': True, 'ambient_light': True}
        ))
        state.actors['player'] = Actor(
            id='player', name='Hero', description='The hero',
            location='grotto', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        visible = check_visibility(accessor, 'grotto')

        self.assertTrue(visible)

    def test_visibility_location_light_source(self):
        """Light source in location provides visibility."""
        from behavior_libraries.darkness_lib.visibility import check_visibility

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='cave', name='Cave', description='A dark cave',
            properties={'requires_light': True}
        ))
        state.items.append(Item(
            id='brazier', name='Brazier', description='A burning brazier',
            location='cave',
            properties={'provides_light': True, 'states': {'lit': True}}
        ))
        state.actors['player'] = Actor(
            id='player', name='Hero', description='The hero',
            location='cave', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        visible = check_visibility(accessor, 'cave')

        self.assertTrue(visible)


class TestGetLightSources(unittest.TestCase):
    """Test get_light_sources function."""

    def test_get_light_sources_in_location(self):
        """Returns lit light sources in location."""
        from behavior_libraries.darkness_lib.visibility import get_light_sources

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='cave', name='Cave', description='A cave'
        ))
        state.items.append(Item(
            id='brazier', name='Brazier', description='A brazier',
            location='cave',
            properties={'provides_light': True, 'states': {'lit': True}}
        ))
        state.actors['player'] = Actor(
            id='player', name='Hero', description='The hero',
            location='cave', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        sources = get_light_sources(accessor, 'cave')

        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].id, 'brazier')

    def test_get_light_sources_includes_player_carried(self):
        """Includes lit items carried by player at location."""
        from behavior_libraries.darkness_lib.visibility import get_light_sources

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='cave', name='Cave', description='A cave'
        ))
        state.items.append(Item(
            id='torch', name='Torch', description='A torch',
            location=None,
            properties={'provides_light': True, 'states': {'lit': True}}
        ))
        state.actors['player'] = Actor(
            id='player', name='Hero', description='The hero',
            location='cave', inventory=['torch']
        )

        accessor = StateAccessor(state, Mock())
        sources = get_light_sources(accessor, 'cave')

        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].id, 'torch')

    def test_get_light_sources_excludes_unlit(self):
        """Excludes unlit light sources."""
        from behavior_libraries.darkness_lib.visibility import get_light_sources

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='cave', name='Cave', description='A cave'
        ))
        state.items.append(Item(
            id='torch', name='Torch', description='A torch',
            location='cave',
            properties={'provides_light': True, 'states': {'lit': False}}
        ))
        state.actors['player'] = Actor(
            id='player', name='Hero', description='The hero',
            location='cave', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        sources = get_light_sources(accessor, 'cave')

        self.assertEqual(sources, [])


class TestGetDarknessDescription(unittest.TestCase):
    """Test get_darkness_description function."""

    def test_custom_darkness_description(self):
        """Returns custom darkness_description if set."""
        from behavior_libraries.darkness_lib.visibility import get_darkness_description

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='cave', name='Cave', description='A cave',
            properties={'darkness_description': 'Pitch black. You cannot see.'}
        ))

        accessor = StateAccessor(state, Mock())
        desc = get_darkness_description(accessor, 'cave')

        self.assertEqual(desc, 'Pitch black. You cannot see.')

    def test_default_darkness_description(self):
        """Returns default message if no custom description."""
        from behavior_libraries.darkness_lib.visibility import get_darkness_description

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='cave', name='Cave', description='A cave',
            properties={'requires_light': True}
        ))

        accessor = StateAccessor(state, Mock())
        desc = get_darkness_description(accessor, 'cave')

        self.assertIn('dark', desc.lower())


class TestOnVisibilityCheck(unittest.TestCase):
    """Test on_visibility_check hook handler."""

    def test_blocks_examine_in_darkness(self):
        """Blocks examine action in dark location."""
        from behavior_libraries.darkness_lib.visibility import on_visibility_check
        from src.behavior_manager import EventResult

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='cave', name='Cave', description='A dark cave',
            properties={'requires_light': True}
        ))
        state.actors['player'] = Actor(
            id='player', name='Hero', description='The hero',
            location='cave', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        context = {'verb': 'examine', 'actor_id': 'player'}
        location = state.locations[0]

        result = on_visibility_check(location, accessor, context)

        self.assertIsInstance(result, EventResult)
        self.assertFalse(result.allow)

    def test_allows_go_in_darkness(self):
        """Allows go/movement action in dark location."""
        from behavior_libraries.darkness_lib.visibility import on_visibility_check

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='cave', name='Cave', description='A dark cave',
            properties={'requires_light': True}
        ))
        state.actors['player'] = Actor(
            id='player', name='Hero', description='The hero',
            location='cave', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        context = {'verb': 'go', 'actor_id': 'player'}
        location = state.locations[0]

        result = on_visibility_check(location, accessor, context)

        self.assertTrue(result.allow)

    def test_allows_inventory_in_darkness(self):
        """Allows inventory action in dark location."""
        from behavior_libraries.darkness_lib.visibility import on_visibility_check

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='cave', name='Cave', description='A dark cave',
            properties={'requires_light': True}
        ))
        state.actors['player'] = Actor(
            id='player', name='Hero', description='The hero',
            location='cave', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        context = {'verb': 'inventory', 'actor_id': 'player'}
        location = state.locations[0]

        result = on_visibility_check(location, accessor, context)

        self.assertTrue(result.allow)

    def test_allows_drop_in_darkness(self):
        """Allows drop action in dark location."""
        from behavior_libraries.darkness_lib.visibility import on_visibility_check

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='cave', name='Cave', description='A dark cave',
            properties={'requires_light': True}
        ))
        state.actors['player'] = Actor(
            id='player', name='Hero', description='The hero',
            location='cave', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        context = {'verb': 'drop', 'actor_id': 'player'}
        location = state.locations[0]

        result = on_visibility_check(location, accessor, context)

        self.assertTrue(result.allow)

    def test_allows_actions_with_light(self):
        """Allows all actions when player has light."""
        from behavior_libraries.darkness_lib.visibility import on_visibility_check

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(
            id='cave', name='Cave', description='A dark cave',
            properties={'requires_light': True}
        ))
        state.items.append(Item(
            id='torch', name='Torch', description='A torch',
            location=None,
            properties={'provides_light': True, 'states': {'lit': True}}
        ))
        state.actors['player'] = Actor(
            id='player', name='Hero', description='The hero',
            location='cave', inventory=['torch']
        )

        accessor = StateAccessor(state, Mock())
        context = {'verb': 'examine', 'actor_id': 'player'}
        location = state.locations[0]

        result = on_visibility_check(location, accessor, context)

        self.assertTrue(result.allow)


if __name__ == '__main__':
    unittest.main()
