"""
Tests for inventory command refactoring.

Tests that inventory works as a command behavior instead of a query.
"""

import unittest
from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager
from src.state_manager import Actor, Item
from tests.conftest import BaseTestCase


class TestInventoryCommandRefactoring(BaseTestCase):
    """Test inventory command supports actor_id."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.behavior_manager = BehaviorManager()
        self.behavior_manager.load_module("behaviors.core.perception")
        self.handler = LLMProtocolHandler(self.state, self.behavior_manager)

    def test_inventory_command_player_default(self):
        """Test inventory command defaults to player."""
        player = self.state.actors["player"]
        player.inventory.append("item_sword")

        message = {
            "type": "command",
            "action": {"verb": "inventory"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "result")
        self.assertTrue(result["success"])
        self.assertIn("sword", result["message"].lower())

    def test_inventory_command_npc(self):
        """Test inventory command for NPC.

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
            "type": "command",
            "action": {"verb": "inventory", "actor_id": "npc_guard"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertIn("key", result["message"].lower())
        self.assertNotIn("sword", result["message"].lower())

    def test_inventory_command_explicit_player(self):
        """Test inventory command with explicit player actor_id."""
        player = self.state.actors["player"]
        player.inventory.append("item_sword")

        message = {
            "type": "command",
            "action": {"verb": "inventory", "actor_id": "player"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertIn("sword", result["message"].lower())

    def test_inventory_command_empty(self):
        """Test inventory command with no items."""
        message = {
            "type": "command",
            "action": {"verb": "inventory"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertIn("carrying nothing", result["message"].lower())


if __name__ == '__main__':
    unittest.main()
