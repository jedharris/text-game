"""Tests for Phase 15: Take-from-container validation.

Tests that "take X from Y" validates that container Y exists.
Currently, indirect_object (container) is ignored and item is found anywhere.
"""
from src.types import ActorId

import unittest
from tests.conftest import make_action, create_test_state
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.state_manager import Item


class TestTakeFromContainerValidation(unittest.TestCase):
    """Test that handle_take validates indirect_object parameter."""

    def setUp(self):
        """Set up test state with containers."""
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()

        # Load manipulation module
        import behaviors.core.manipulation
        self.behavior_manager.load_module(behaviors.core.manipulation)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Get player's location
        player = self.game_state.get_actor(ActorId("player"))
        location_id = player.location

        # Add a surface container (table)
        table = Item(
            id="item_table_container",
            name="table",
            description="A wooden table",
            location=location_id,
            properties={
                "portable": False,
                "container": {
                    "is_surface": True,
                    "capacity": 5
                }
            }
        )

        # Add a key on the table
        key_on_table = Item(
            id="item_key_on_table",
            name="key",
            description="A brass key on the table.",
            location="item_table_container",  # On the table
            properties={"portable": True}
        )

        # Add a chest (enclosed container)
        chest = Item(
            id="item_chest",
            name="chest",
            description="A wooden chest",
            location=location_id,
            properties={
                "portable": False,
                "container": {
                    "is_surface": False,
                    "open": True,  # Start open for testing
                    "capacity": 10
                }
            }
        )

        # Add a ring in the chest
        ring_in_chest = Item(
            id="item_ring_in_chest",
            name="ring",
            description="A gold ring in the chest.",
            location="item_chest",  # In the chest
            properties={"portable": True}
        )

        # Add items directly in room (not in containers)
        coin_in_room = Item(
            id="item_coin_room",
            name="coin",
            description="A silver coin on the floor.",
            location=location_id,
            properties={"portable": True}
        )

        self.game_state.items.append(table)
        self.game_state.items.append(key_on_table)
        self.game_state.items.append(chest)
        self.game_state.items.append(ring_in_chest)
        self.game_state.items.append(coin_in_room)

    def test_take_from_nonexistent_container_fails(self):
        """Test that take from nonexistent container fails."""
        from behaviors.core.manipulation import handle_take

        action = make_action(object="key", indirect_object="shelf", actor_id="player")
        result = handle_take(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("shelf", result.primary.lower())

    def test_take_from_valid_container_succeeds(self):
        """Test that take from valid container succeeds."""
        from behaviors.core.manipulation import handle_take

        action = make_action(object="key", indirect_object="table", actor_id="player")
        result = handle_take(self.accessor, action)

        self.assertTrue(result.success)
        player = self.game_state.get_actor(ActorId("player"))
        self.assertIn("item_key_on_table", player.inventory)

    def test_take_from_container_item_not_in_container_fails(self):
        """Test that take X from Y fails if X is not in container Y."""
        from behaviors.core.manipulation import handle_take

        # Coin is in the room, not on the table
        action = make_action(object="coin", indirect_object="table", actor_id="player")
        result = handle_take(self.accessor, action)

        self.assertFalse(result.success)
        # Should mention can't find coin in/on table
        self.assertIn("coin", result.primary.lower())

    def test_take_without_indirect_object_still_works(self):
        """Test that take without indirect_object finds item anywhere."""
        from behaviors.core.manipulation import handle_take

        action = make_action(object="coin", actor_id="player")
        result = handle_take(self.accessor, action)

        self.assertTrue(result.success)
        player = self.game_state.get_actor(ActorId("player"))
        self.assertIn("item_coin_room", player.inventory)

    def test_take_from_enclosed_container_succeeds_when_open(self):
        """Test taking from open enclosed container succeeds."""
        from behaviors.core.manipulation import handle_take

        action = make_action(object="ring", indirect_object="chest", actor_id="player")
        result = handle_take(self.accessor, action)

        self.assertTrue(result.success)
        player = self.game_state.get_actor(ActorId("player"))
        self.assertIn("item_ring_in_chest", player.inventory)

    def test_take_from_enclosed_container_fails_when_closed(self):
        """Test taking from closed enclosed container fails."""
        from behaviors.core.manipulation import handle_take

        # Close the chest
        chest = self.game_state.get_item("item_chest")
        chest.properties["container"]["open"] = False

        action = make_action(object="ring", indirect_object="chest", actor_id="player")
        result = handle_take(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("closed", result.primary.lower())

    def test_take_from_non_container_item_fails(self):
        """Test that take from non-container item fails gracefully."""
        from behaviors.core.manipulation import handle_take

        # sword is not a container
        action = make_action(object="key", indirect_object="sword", actor_id="player")
        result = handle_take(self.accessor, action)

        self.assertFalse(result.success)
        # Should mention sword is not a container
        self.assertIn("sword", result.primary.lower())


class TestTakeFromContainerWithAdjective(unittest.TestCase):
    """Test take-from-container works with adjective disambiguation."""

    def setUp(self):
        """Set up test state with multiple similar items in different containers."""
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.manipulation
        self.behavior_manager.load_module(behaviors.core.manipulation)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        player = self.game_state.get_actor(ActorId("player"))
        location_id = player.location

        # Add two tables
        wooden_table = Item(
            id="item_wooden_table",
            name="table",
            description="A rough wooden table",
            location=location_id,
            properties={
                "portable": False,
                "container": {"is_surface": True, "capacity": 5}
            }
        )

        marble_table = Item(
            id="item_marble_table",
            name="table",
            description="A polished marble table",
            location=location_id,
            properties={
                "portable": False,
                "container": {"is_surface": True, "capacity": 5}
            }
        )

        # Keys on different tables
        iron_key = Item(
            id="item_iron_key",
            name="key",
            description="An iron key",
            location="item_wooden_table",
            properties={"portable": True}
        )

        gold_key = Item(
            id="item_gold_key",
            name="key",
            description="A gold key",
            location="item_marble_table",
            properties={"portable": True}
        )

        self.game_state.items.append(wooden_table)
        self.game_state.items.append(marble_table)
        self.game_state.items.append(iron_key)
        self.game_state.items.append(gold_key)

    def test_take_with_container_adjective_selects_correct_container(self):
        """Test that adjective on container selects correct container."""
        from behaviors.core.manipulation import handle_take

        action = make_action(object="key", indirect_object="table", indirect_adjective="marble", actor_id="player")
        result = handle_take(self.accessor, action)

        self.assertTrue(result.success)
        player = self.game_state.get_actor(ActorId("player"))
        # Should take the key from marble table (gold key)
        self.assertIn("item_gold_key", player.inventory)
        self.assertNotIn("item_iron_key", player.inventory)


if __name__ == '__main__':
    unittest.main()
