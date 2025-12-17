"""
Tests for put handler - Phase C-8.
"""
from src.types import ActorId

import unittest
from src.state_manager import GameState, Location, Item, Actor, Metadata
from src.behavior_manager import BehaviorManager
from src.state_accessor import StateAccessor
from tests.conftest import make_action


def create_test_state():
    """Create a minimal test state with containers."""
    return GameState(
        metadata=Metadata(title="Test"),
        locations=[
            Location(id="loc1", name="Room", description="A test room")
        ],
        items=[
            Item(
                id="item_key",
                name="key",
                description="A brass key",
                location="player",
                properties={"portable": True}
            ),
            Item(
                id="item_box",
                name="box",
                description="A wooden box",
                location="loc1",
                properties={
                    "portable": False,
                    "container": {
                        "is_surface": False,
                        "open": True,
                        "capacity": 5
                    }
                }
            ),
            Item(
                id="item_table",
                name="table",
                description="A wooden table",
                location="loc1",
                properties={
                    "portable": False,
                    "container": {
                        "is_surface": True,
                        "capacity": 10
                    }
                }
            ),
            Item(
                id="item_closed_chest",
                name="chest",
                description="A closed chest",
                location="loc1",
                properties={
                    "portable": False,
                    "container": {
                        "is_surface": False,
                        "open": False,
                        "capacity": 5
                    }
                }
            ),
            Item(
                id="item_rock",
                name="rock",
                description="A plain rock",
                location="loc1",
                properties={"portable": True}
            )
        ],
        actors={
            "player": Actor(
                id="player",
                name="Adventurer",
                description="The player",
                location="loc1",
                inventory=["item_key"]
            ),
            "npc_guard": Actor(
                id="npc_guard",
                name="guard",
                description="A guard",
                location="loc1",
                inventory=[]
            )
        }
    )


class TestHandlePut(unittest.TestCase):
    """Test handle_put behavior handler."""

    def setUp(self):
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.manipulation
        self.behavior_manager.load_module(behaviors.core.manipulation)

        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_put_no_object(self):
        """Test put without specifying object."""
        from behaviors.core.manipulation import handle_put

        action = {"actor_id": "player"}
        result = handle_put(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what", result.message.lower())

    def test_put_no_container(self):
        """Test put without specifying container."""
        from behaviors.core.manipulation import handle_put

        action = make_action(verb="put", object="key", actor_id="player")
        result = handle_put(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("where", result.message.lower())

    def test_put_item_not_in_inventory(self):
        """Test putting item not in inventory."""
        from behaviors.core.manipulation import handle_put

        action = make_action(object="rock", indirect_object="box", actor_id="player")
        result = handle_put(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't have", result.message.lower())

    def test_put_in_open_container(self):
        """Test putting item in open container."""
        from behaviors.core.manipulation import handle_put

        action = make_action(object="key", indirect_object="box", actor_id="player")
        result = handle_put(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("put", result.message.lower())
        # Key should be moved to box
        key = self.state.get_item("item_key")
        self.assertEqual(key.location, "item_box")
        # Key should be removed from inventory
        self.assertNotIn("item_key", self.state.actors[ActorId("player")].inventory)

    def test_put_on_surface(self):
        """Test putting item on surface container."""
        from behaviors.core.manipulation import handle_put

        action = make_action(object="key", indirect_object="table", actor_id="player")
        result = handle_put(self.accessor, action)

        self.assertTrue(result.success)
        # Key should be moved to table
        key = self.state.get_item("item_key")
        self.assertEqual(key.location, "item_table")

    def test_put_in_closed_container_fails(self):
        """Test putting item in closed container fails."""
        from behaviors.core.manipulation import handle_put

        action = make_action(object="key", indirect_object="chest", actor_id="player")
        result = handle_put(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("closed", result.message.lower())

    def test_put_in_noncontainer_fails(self):
        """Test putting item in non-container fails."""
        from behaviors.core.manipulation import handle_put

        action = make_action(object="key", indirect_object="rock", actor_id="player")
        result = handle_put(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't put", result.message.lower())


class TestPutVocabulary(unittest.TestCase):
    """Test that put vocabulary is properly defined."""

    def test_vocabulary_has_put(self):
        """Test that put verb is in vocabulary."""
        from behaviors.core.manipulation import vocabulary

        verbs = {v["word"] for v in vocabulary["verbs"]}
        self.assertIn("put", verbs)


if __name__ == '__main__':
    unittest.main()
