"""
Tests for inventory query refactoring (Phase I-4).

Reference: behavior_refactoring_testing.md lines 573-605 (NPC test pattern)
"""

import unittest
from src.llm_protocol import JSONProtocolHandler
from src.behavior_manager import BehaviorManager
from src.state_manager import Actor, Item
from tests.conftest import create_test_state


class TestInventoryQueryRefactoring(unittest.TestCase):
    """Test inventory query supports actor_id."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.handler = JSONProtocolHandler(self.state, self.behavior_manager)

    def test_query_inventory_player_default(self):
        """Test inventory query defaults to player."""
        player = self.state.actors["player"]
        player.inventory.append("item_sword")

        message = {
            "type": "query",
            "query_type": "inventory"
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "query_response")
        item_ids = [i["id"] for i in result["data"]["items"]]
        self.assertIn("item_sword", item_ids)

    def test_query_inventory_npc(self):
        """Test inventory query for NPC.

        NPC inventory should be separate from player inventory.
        """
        # Add NPC with item in inventory
        npc = Actor(id="npc_guard", name="guard", description="A guard",
                   location="location_room", inventory=["item_key"],
                   properties={}, behaviors=[])
        self.state.actors["npc_guard"] = npc

        # Add the key item
        key = Item(id="item_key", name="key", description="A key",
                  location="npc_guard", properties={"portable": True}, behaviors=[])
        self.state.items.append(key)

        # Also put sword in player inventory
        player = self.state.actors["player"]
        player.inventory.append("item_sword")

        message = {
            "type": "query",
            "query_type": "inventory",
            "actor_id": "npc_guard"
        }

        result = self.handler.handle_message(message)

        item_ids = [i["id"] for i in result["data"]["items"]]
        self.assertIn("item_key", item_ids)
        self.assertNotIn("item_sword", item_ids)

    def test_query_inventory_explicit_player(self):
        """Test inventory query with explicit player actor_id."""
        player = self.state.actors["player"]
        player.inventory.append("item_sword")

        message = {
            "type": "query",
            "query_type": "inventory",
            "actor_id": "player"
        }

        result = self.handler.handle_message(message)

        item_ids = [i["id"] for i in result["data"]["items"]]
        self.assertIn("item_sword", item_ids)


if __name__ == '__main__':
    unittest.main()
