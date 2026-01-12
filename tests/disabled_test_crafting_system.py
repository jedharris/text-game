"""Tests for crafting/combining system."""
from src.types import ActorId

import unittest
from unittest.mock import Mock

from src.state_manager import Actor, Item, Location, GameState, Metadata
from src.state_accessor import StateAccessor
from tests.conftest import make_word_entry


class TestFindRecipe(unittest.TestCase):
    """Test find_recipe function."""

    def test_find_recipe_matching_ingredients(self):
        """Finds recipe when ingredients match."""
        from behavior_libraries.crafting_lib.recipes import find_recipe

        state = GameState(metadata=Metadata(title="Test"))
        state.extra['recipes'] = {
            'healing_potion': {
                'ingredients': ['herb', 'water'],
                'creates': 'healing_potion'
            }
        }

        accessor = StateAccessor(state, Mock())
        recipe = find_recipe(accessor, ['herb', 'water'])

        self.assertIsNotNone(recipe)
        self.assertEqual(recipe['creates'], 'healing_potion')

    def test_find_recipe_order_independent(self):
        """Finds recipe regardless of ingredient order."""
        from behavior_libraries.crafting_lib.recipes import find_recipe

        state = GameState(metadata=Metadata(title="Test"))
        state.extra['recipes'] = {
            'healing_potion': {
                'ingredients': ['herb', 'water'],
                'creates': 'healing_potion'
            }
        }

        accessor = StateAccessor(state, Mock())
        recipe = find_recipe(accessor, ['water', 'herb'])

        self.assertIsNotNone(recipe)
        self.assertEqual(recipe['creates'], 'healing_potion')

    def test_find_recipe_no_match(self):
        """Returns None when no recipe matches."""
        from behavior_libraries.crafting_lib.recipes import find_recipe

        state = GameState(metadata=Metadata(title="Test"))
        state.extra['recipes'] = {
            'healing_potion': {
                'ingredients': ['herb', 'water'],
                'creates': 'healing_potion'
            }
        }

        accessor = StateAccessor(state, Mock())
        recipe = find_recipe(accessor, ['rock', 'stick'])

        self.assertIsNone(recipe)

    def test_find_recipe_partial_match_fails(self):
        """Partial ingredient match does not find recipe."""
        from behavior_libraries.crafting_lib.recipes import find_recipe

        state = GameState(metadata=Metadata(title="Test"))
        state.extra['recipes'] = {
            'healing_potion': {
                'ingredients': ['herb', 'water', 'moss'],
                'creates': 'healing_potion'
            }
        }

        accessor = StateAccessor(state, Mock())
        recipe = find_recipe(accessor, ['herb', 'water'])

        self.assertIsNone(recipe)


class TestCheckRequirements(unittest.TestCase):
    """Test check_requirements function."""

    def test_check_requirements_no_requirements(self):
        """Recipe with no requirements passes."""
        from behavior_libraries.crafting_lib.recipes import check_requirements

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='anywhere', name='Anywhere', description='A place'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='anywhere', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        recipe = {'ingredients': ['a', 'b'], 'creates': 'c'}

        can_craft, message = check_requirements(accessor, recipe)

        self.assertTrue(can_craft)
        self.assertEqual(message, '')

    def test_check_requirements_location_required(self):
        """Recipe requiring location fails when not at location."""
        from behavior_libraries.crafting_lib.recipes import check_requirements

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='forest', name='Forest', description='A forest'))
        state.locations.append(Location(id='forge', name='Forge', description='A forge'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='forest', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        recipe = {
            'ingredients': ['iron', 'coal'],
            'creates': 'sword',
            'requires_location': 'forge'
        }

        can_craft, message = check_requirements(accessor, recipe)

        self.assertFalse(can_craft)
        self.assertIn('forge', message.lower())

    def test_check_requirements_location_satisfied(self):
        """Recipe passes when at required location."""
        from behavior_libraries.crafting_lib.recipes import check_requirements

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='forge', name='Forge', description='A forge'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='forge', inventory=[]
        )

        accessor = StateAccessor(state, Mock())
        recipe = {
            'ingredients': ['iron', 'coal'],
            'creates': 'sword',
            'requires_location': 'forge'
        }

        can_craft, message = check_requirements(accessor, recipe)

        self.assertTrue(can_craft)

    def test_check_requirements_skill_required(self):
        """Recipe requiring skill fails when player lacks skill."""
        from behavior_libraries.crafting_lib.recipes import check_requirements

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='anywhere', name='Anywhere', description='A place'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='anywhere', inventory=[],
            _properties={'skills': []}
        )

        accessor = StateAccessor(state, Mock())
        recipe = {
            'ingredients': ['herb', 'water'],
            'creates': 'potion',
            'requires_skill': 'herbalism'
        }

        can_craft, message = check_requirements(accessor, recipe)

        self.assertFalse(can_craft)
        self.assertIn('herbalism', message.lower())

    def test_check_requirements_skill_satisfied(self):
        """Recipe passes when player has required skill."""
        from behavior_libraries.crafting_lib.recipes import check_requirements

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='anywhere', name='Anywhere', description='A place'))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='anywhere', inventory=[],
            _properties={'skills': ['herbalism']}
        )

        accessor = StateAccessor(state, Mock())
        recipe = {
            'ingredients': ['herb', 'water'],
            'creates': 'potion',
            'requires_skill': 'herbalism'
        }

        can_craft, message = check_requirements(accessor, recipe)

        self.assertTrue(can_craft)


class TestExecuteCraft(unittest.TestCase):
    """Test execute_craft function."""

    def test_execute_craft_consumes_ingredients(self):
        """Crafting consumes ingredients from inventory."""
        from behavior_libraries.crafting_lib.recipes import execute_craft

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='anywhere', name='Anywhere', description='A place'))
        state.items.append(Item(id='herb', name='Herb', description='An herb', location=None))
        state.items.append(Item(id='water', name='Water', description='Water', location=None))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='anywhere', inventory=['herb', 'water']
        )
        state.extra['recipes'] = {
            'healing_potion': {
                'ingredients': ['herb', 'water'],
                'creates': 'healing_potion',
                'consumes_ingredients': True,
                'success_message': 'You brew a healing potion.'
            }
        }
        state.extra['item_templates'] = {
            'healing_potion': {
                'name': 'Healing Potion',
                'description': 'A glowing red potion'
            }
        }

        accessor = StateAccessor(state, Mock())
        recipe = state.extra['recipes']['healing_potion']

        result = execute_craft(accessor, recipe, ['herb', 'water'])

        self.assertTrue(result.success)
        self.assertNotIn('herb', state.get_actor(ActorId('player')).inventory)
        self.assertNotIn('water', state.get_actor(ActorId('player')).inventory)

    def test_execute_craft_creates_result_item(self):
        """Crafting creates the result item in inventory."""
        from behavior_libraries.crafting_lib.recipes import execute_craft

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='anywhere', name='Anywhere', description='A place'))
        state.items.append(Item(id='herb', name='Herb', description='An herb', location=None))
        state.items.append(Item(id='water', name='Water', description='Water', location=None))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='anywhere', inventory=['herb', 'water']
        )
        state.extra['recipes'] = {
            'healing_potion': {
                'ingredients': ['herb', 'water'],
                'creates': 'healing_potion',
                'consumes_ingredients': True,
                'success_message': 'You brew a healing potion.'
            }
        }
        state.extra['item_templates'] = {
            'healing_potion': {
                'name': 'Healing Potion',
                'description': 'A glowing red potion'
            }
        }

        accessor = StateAccessor(state, Mock())
        recipe = state.extra['recipes']['healing_potion']

        execute_craft(accessor, recipe, ['herb', 'water'])

        self.assertIn('healing_potion', state.get_actor(ActorId('player')).inventory)

    def test_execute_craft_returns_success_message(self):
        """Crafting returns the recipe success message."""
        from behavior_libraries.crafting_lib.recipes import execute_craft

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='anywhere', name='Anywhere', description='A place'))
        state.items.append(Item(id='herb', name='Herb', description='An herb', location=None))
        state.items.append(Item(id='water', name='Water', description='Water', location=None))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='anywhere', inventory=['herb', 'water']
        )
        state.extra['recipes'] = {}
        state.extra['item_templates'] = {
            'healing_potion': {
                'name': 'Healing Potion',
                'description': 'A glowing red potion'
            }
        }

        accessor = StateAccessor(state, Mock())
        recipe = {
            'ingredients': ['herb', 'water'],
            'creates': 'healing_potion',
            'consumes_ingredients': True,
            'success_message': 'You brew a healing potion.'
        }

        result = execute_craft(accessor, recipe, ['herb', 'water'])

        self.assertEqual(result.description, 'You brew a healing potion.')

    def test_execute_craft_preserves_ingredients_when_not_consumed(self):
        """When consumes_ingredients is False, ingredients remain."""
        from behavior_libraries.crafting_lib.recipes import execute_craft

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='anywhere', name='Anywhere', description='A place'))
        state.items.append(Item(id='lens', name='Lens', description='A lens', location=None))
        state.items.append(Item(id='frame', name='Frame', description='A frame', location=None))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='anywhere', inventory=['lens', 'frame']
        )
        state.extra['item_templates'] = {
            'telescope': {
                'name': 'Telescope',
                'description': 'A working telescope'
            }
        }

        accessor = StateAccessor(state, Mock())
        recipe = {
            'ingredients': ['lens', 'frame'],
            'creates': 'telescope',
            'consumes_ingredients': False,
            'success_message': 'You assemble the telescope.'
        }

        execute_craft(accessor, recipe, ['lens', 'frame'])

        # Ingredients should still be in inventory (not consumed)
        self.assertIn('lens', state.get_actor(ActorId('player')).inventory)
        self.assertIn('frame', state.get_actor(ActorId('player')).inventory)


class TestHandleCombine(unittest.TestCase):
    """Test handle_combine command handler."""

    def test_handle_combine_success(self):
        """Combine command succeeds with valid ingredients."""
        from behavior_libraries.crafting_lib.handlers import handle_combine
        from src.state_accessor import HandlerResult

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='anywhere', name='Anywhere', description='A place'))
        state.items.append(Item(id='herb', name='Herb', description='An herb', location=None))
        state.items.append(Item(id='water', name='Water', description='Water', location=None))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='anywhere', inventory=['herb', 'water']
        )
        state.extra['recipes'] = {
            'healing_potion': {
                'ingredients': ['herb', 'water'],
                'creates': 'healing_potion',
                'consumes_ingredients': True,
                'success_message': 'You brew a healing potion.'
            }
        }
        state.extra['item_templates'] = {
            'healing_potion': {
                'name': 'Healing Potion',
                'description': 'A glowing red potion'
            }
        }

        accessor = StateAccessor(state, Mock())
        action = {
            'verb': 'combine',
            'object': make_word_entry('herb'),
            'target': make_word_entry('water'),
            'actor_id': 'player'
        }

        result = handle_combine(accessor, action)

        self.assertIsInstance(result, HandlerResult)
        self.assertTrue(result.success)

    def test_handle_combine_no_recipe(self):
        """Combine fails when no recipe matches."""
        from behavior_libraries.crafting_lib.handlers import handle_combine

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='anywhere', name='Anywhere', description='A place'))
        state.items.append(Item(id='rock', name='Rock', description='A rock', location=None))
        state.items.append(Item(id='stick', name='Stick', description='A stick', location=None))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='anywhere', inventory=['rock', 'stick']
        )
        state.extra['recipes'] = {}

        accessor = StateAccessor(state, Mock())
        action = {
            'verb': 'combine',
            'object': make_word_entry('rock'),
            'target': make_word_entry('stick'),
            'actor_id': 'player'
        }

        result = handle_combine(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't", result.primary.lower())

    def test_handle_combine_missing_item(self):
        """Combine fails when player doesn't have item."""
        from behavior_libraries.crafting_lib.handlers import handle_combine

        state = GameState(metadata=Metadata(title="Test"))
        state.locations.append(Location(id='anywhere', name='Anywhere', description='A place'))
        state.items.append(Item(id='herb', name='Herb', description='An herb', location=None))
        state.actors[ActorId('player')] = Actor(
            id='player', name='Hero', description='The hero',
            location='anywhere', inventory=['herb']
        )
        state.extra['recipes'] = {
            'healing_potion': {
                'ingredients': ['herb', 'water'],
                'creates': 'healing_potion'
            }
        }

        accessor = StateAccessor(state, Mock())
        action = {
            'verb': 'combine',
            'object': make_word_entry('herb'),
            'target': make_word_entry('water'),
            'actor_id': 'player'
        }

        result = handle_combine(accessor, action)

        self.assertFalse(result.success)


if __name__ == '__main__':
    unittest.main()
