"""
Tests for Phase 13.5: Consumable Property Validation

These tests verify that eat/drink commands require edible/drinkable properties.
"""
from src.types import ActorId

import unittest
from tests.conftest import create_test_state, make_action
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.state_manager import Item
from behaviors.core.consumables import handle_eat, handle_drink


class TestConsumableProperties(unittest.TestCase):
    """Test that eat/drink require edible/drinkable properties."""

    def test_eat_non_edible_item_fails(self):
        """Test that eating a non-edible item fails."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        accessor = StateAccessor(state, behavior_manager)

        # Sword is not edible (no edible property)
        sword = state.get_item("item_sword")
        sword.location = "player"
        state.get_actor(ActorId("player")).inventory.append("item_sword")

        action = make_action(object="sword", actor_id="player")
        result = handle_eat(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't eat", result.primary.lower())

    def test_eat_edible_item_succeeds(self):
        """Test that eating an edible item succeeds."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        accessor = StateAccessor(state, behavior_manager)

        # Create edible apple
        apple = Item(
            id="item_apple",
            name="apple",
            description="A red apple",
            location="player",
            _properties={"edible": True}
        )
        state.items.append(apple)
        state.get_actor(ActorId("player")).inventory.append("item_apple")

        action = make_action(object="apple", actor_id="player")
        result = handle_eat(accessor, action)

        self.assertTrue(result.success)

    def test_drink_non_drinkable_item_fails(self):
        """Test that drinking a non-drinkable item fails."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        accessor = StateAccessor(state, behavior_manager)

        # Sword is not drinkable
        sword = state.get_item("item_sword")
        sword.location = "player"
        state.get_actor(ActorId("player")).inventory.append("item_sword")

        action = make_action(object="sword", actor_id="player")
        result = handle_drink(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't drink", result.primary.lower())

    def test_drink_drinkable_item_succeeds(self):
        """Test that drinking a drinkable item succeeds."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        accessor = StateAccessor(state, behavior_manager)

        # Create drinkable potion
        potion = Item(
            id="item_potion",
            name="potion",
            description="A healing potion",
            location="player",
            _properties={"drinkable": True}
        )
        state.items.append(potion)
        state.get_actor(ActorId("player")).inventory.append("item_potion")

        action = make_action(object="potion", actor_id="player")
        result = handle_drink(accessor, action)

        self.assertTrue(result.success)

    def test_eat_item_with_edible_false_fails(self):
        """Test that items with edible=False explicitly cannot be eaten."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        accessor = StateAccessor(state, behavior_manager)

        # Create item with explicit edible=False
        rock = Item(
            id="item_rock",
            name="rock",
            description="A hard rock",
            location="player",
            _properties={"edible": False}
        )
        state.items.append(rock)
        state.get_actor(ActorId("player")).inventory.append("item_rock")

        action = make_action(object="rock", actor_id="player")
        result = handle_eat(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't eat", result.primary.lower())

    def test_drink_item_with_drinkable_false_fails(self):
        """Test that items with drinkable=False explicitly cannot be drunk."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        accessor = StateAccessor(state, behavior_manager)

        # Create item with explicit drinkable=False
        oil = Item(
            id="item_oil",
            name="oil",
            description="Motor oil",
            location="player",
            _properties={"drinkable": False}
        )
        state.items.append(oil)
        state.get_actor(ActorId("player")).inventory.append("item_oil")

        action = make_action(object="oil", actor_id="player")
        result = handle_drink(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't drink", result.primary.lower())


if __name__ == '__main__':
    unittest.main()
