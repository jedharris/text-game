"""
Tests for location query refactoring (Phase I-3).

Reference: behavior_refactoring_testing.md lines 573-605 (NPC test pattern)
"""

import unittest
from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager
from src.state_manager import Actor
from tests.conftest import create_test_state


class TestLocationQueryRefactoring(unittest.TestCase):
    """Test location query uses utilities correctly."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.handler = LLMProtocolHandler(self.state, self.behavior_manager)

    def test_query_location_returns_items(self):
        """Test that location query returns items."""
        message = {
            "type": "query",
            "query_type": "location",
            "include": ["items"]
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "query_response")
        self.assertIn("items", result["data"])
        # Should include sword from test state
        item_names = [i["name"] for i in result["data"]["items"]]
        self.assertIn("sword", item_names)

    def test_query_location_returns_actors_excluding_viewer(self):
        """Test that location query returns actors, excluding the viewing actor.

        Reference: behavior_refactoring_testing.md lines 573-605 - NPC test pattern
        """
        # Add NPC to same location as player
        npc = Actor(id="npc_guard", name="guard", description="A guard",
                   location="location_room", inventory=[], properties={}, behaviors=[])
        self.state.actors["npc_guard"] = npc

        message = {
            "type": "query",
            "query_type": "location",
            "include": ["actors"],
            "actor_id": "player"
        }

        result = self.handler.handle_message(message)

        actor_ids = [a["id"] for a in result["data"].get("actors", [])]
        self.assertIn("npc_guard", actor_ids)
        self.assertNotIn("player", actor_ids)

    def test_query_location_npc_perspective(self):
        """Test that location query works from NPC perspective.

        NPC should see player but not themselves.
        """
        npc = Actor(id="npc_guard", name="guard", description="A guard",
                   location="location_room", inventory=[], properties={}, behaviors=[])
        self.state.actors["npc_guard"] = npc

        message = {
            "type": "query",
            "query_type": "location",
            "include": ["actors"],
            "actor_id": "npc_guard"
        }

        result = self.handler.handle_message(message)

        actor_ids = [a["id"] for a in result["data"].get("actors", [])]
        self.assertIn("player", actor_ids)
        self.assertNotIn("npc_guard", actor_ids)

    def test_query_location_default_actor_is_player(self):
        """Test that missing actor_id defaults to player."""
        npc = Actor(id="npc_guard", name="guard", description="A guard",
                   location="location_room", inventory=[], properties={}, behaviors=[])
        self.state.actors["npc_guard"] = npc

        message = {
            "type": "query",
            "query_type": "location",
            "include": ["actors"]
            # No actor_id - should default to player
        }

        result = self.handler.handle_message(message)

        actor_ids = [a["id"] for a in result["data"].get("actors", [])]
        self.assertIn("npc_guard", actor_ids)
        self.assertNotIn("player", actor_ids)


if __name__ == '__main__':
    unittest.main()
