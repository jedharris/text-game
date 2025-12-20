"""
Tests for inventory command refactoring.

Tests that inventory works as a command behavior instead of a query.

Updated for Phase 4 (Narration API) to handle NarrationResult format.
"""
from src.types import ActorId
from typing import Any, Dict

import unittest
from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager
from src.state_manager import Actor, Item
from tests.conftest import BaseTestCase


def get_result_message(result: Dict[str, Any]) -> str:
    """
    Extract message text from result, handling both old and new formats.

    New format (Phase 4): result["narration"]["primary_text"]
    Old format: result["message"] or result["error"]["message"]

    For the new format, also concatenates secondary_beats.
    """
    # New format: NarrationResult
    if "narration" in result:
        narration = result["narration"]
        parts = [narration.get("primary_text", "")]
        if "secondary_beats" in narration:
            parts.extend(narration["secondary_beats"])
        return "\n".join(parts)

    # Old format - success case
    if result.get("success") and "message" in result:
        return result["message"]

    # Old format - error case
    if "error" in result and "message" in result["error"]:
        return result["error"]["message"]

    return result.get("message", "")


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
        player = self.state.actors[ActorId("player")]
        player.inventory.append("item_sword")

        message = {
            "type": "command",
            "action": {"verb": "inventory"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "result")
        self.assertTrue(result["success"])
        self.assertIn("sword", get_result_message(result).lower())

    def test_inventory_command_npc(self):
        """Test inventory command for NPC.

        NPC inventory should be separate from player inventory.
        """
        # Add NPC with item in inventory
        npc = Actor(id="npc_guard", name="guard", description="A guard",
                   location="location_room", inventory=["item_key"],
                   properties={}, behaviors=[])
        self.state.actors[ActorId("npc_guard")] = npc

        # Add the key item
        key = Item(id="item_key", name="key", description="A key",
                  location="npc_guard", properties={"portable": True}, behaviors=[])
        self.state.items.append(key)

        # Also put sword in player inventory
        player = self.state.actors[ActorId("player")]
        player.inventory.append("item_sword")

        message = {
            "type": "command",
            "action": {"verb": "inventory", "actor_id": "npc_guard"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertIn("key", get_result_message(result).lower())
        self.assertNotIn("sword", get_result_message(result).lower())

    def test_inventory_command_explicit_player(self):
        """Test inventory command with explicit player actor_id."""
        player = self.state.actors[ActorId("player")]
        player.inventory.append("item_sword")

        message = {
            "type": "command",
            "action": {"verb": "inventory", "actor_id": "player"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertIn("sword", get_result_message(result).lower())

    def test_inventory_command_empty(self):
        """Test inventory command with no items."""
        message = {
            "type": "command",
            "action": {"verb": "inventory"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertIn("carrying nothing", get_result_message(result).lower())


if __name__ == '__main__':
    unittest.main()
