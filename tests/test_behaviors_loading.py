"""Tests for loading game state with behaviors field (Phase 3)."""

import unittest
import json
import tempfile
from pathlib import Path

from src.state_manager import load_game_state, Item, Actor, Location


class TestBehaviorsFieldInModels(unittest.TestCase):
    """Test that behaviors field exists and works in models."""

    def test_item_has_behaviors_field(self):
        """Test that Item model has behaviors field."""
        item = Item(
            id="test_item",
            name="Test",
            description="A test item",
            location="room1",
            properties={"type": "tool", "portable": True}
        )
        self.assertEqual(item.behaviors, [])

    def test_item_with_behaviors(self):
        """Test creating Item with behaviors."""
        item = Item(
            id="test_item",
            name="Test",
            description="A test item",
            location="room1",
            properties={"type": "tool", "portable": True},
            behaviors=["module:on_take", "module:on_drop"]
        )
        self.assertIn("module:on_take", item.behaviors)
        self.assertIn("module:on_drop", item.behaviors)

    def test_actor_has_behaviors_field(self):
        """Test that Actor model has behaviors field."""
        actor = Actor(
            id="test_npc",
            name="Test NPC",
            description="A test NPC",
            location="room1"
        )
        self.assertEqual(actor.behaviors, [])

    def test_actor_with_behaviors(self):
        """Test creating Actor with behaviors."""
        actor = Actor(
            id="test_npc",
            name="Test NPC",
            description="A test NPC",
            location="room1",
            behaviors=["module:on_talk"]
        )
        self.assertIn("module:on_talk", actor.behaviors)

    def test_door_item_has_behaviors_field(self):
        """Test that door item has behaviors field."""
        door_item = Item(
            id="test_door",
            name="door",
            description="A test door",
            location="exit:room1:north",
            properties={"door": {"open": False}},
            behaviors=[]
        )
        self.assertEqual(door_item.behaviors, [])
        self.assertTrue(door_item.is_door)

    def test_door_item_with_behaviors(self):
        """Test creating door item with behaviors."""
        door_item = Item(
            id="test_door",
            name="door",
            description="A test door",
            location="exit:room1:north",
            properties={"door": {"open": False}},
            behaviors=["module:on_open", "module:on_close"]
        )
        self.assertIn("module:on_open", door_item.behaviors)
        self.assertTrue(door_item.is_door)

    def test_location_has_behaviors_field(self):
        """Test that Location model has behaviors field."""
        location = Location(
            id="room1",
            name="Test Room",
            description="A test room"
        )
        self.assertEqual(location.behaviors, [])

    def test_location_with_behaviors(self):
        """Test creating Location with behaviors."""
        location = Location(
            id="room1",
            name="Test Room",
            description="A test room",
            behaviors=["module:on_enter", "module:on_exit"]
        )
        self.assertIn("module:on_enter", location.behaviors)


class TestBehaviorsLoading(unittest.TestCase):
    """Test loading game state with behaviors from JSON."""

    def _create_minimal_game_state(self, **kwargs):
        """Create a minimal game state dict with optional overrides."""
        state = {
            "metadata": {
                "title": "Test Game",
                "start_location": "room1"
            },
            "locations": [
                {
                    "id": "room1",
                    "name": "Test Room",
                    "description": "A test room"
                }
            ],
            "items": [],
            "npcs": []
        }
        state.update(kwargs)
        return state

    def test_load_item_with_behaviors(self):
        """Test loading item with behaviors field from JSON."""
        game_data = self._create_minimal_game_state(
            items=[
                {
                    "id": "potion",
                    "name": "potion",
                    "description": "A healing potion",
                    "type": "tool",
                    "portable": True,
                    "location": "room1",
                    "behaviors": ["behaviors.consumables:on_drink_health_potion"]
                }
            ]
        )

        state = load_game_state(game_data)

        item = state.get_item("potion")
        self.assertIn("behaviors.consumables:on_drink_health_potion", item.behaviors)

    def test_load_item_without_behaviors(self):
        """Test loading item without behaviors field defaults to empty dict."""
        game_data = self._create_minimal_game_state(
            items=[
                {
                    "id": "sword",
                    "name": "sword",
                    "description": "A rusty sword",
                    "type": "tool",
                    "portable": True,
                    "location": "room1"
                }
            ]
        )

        state = load_game_state(game_data)

        item = state.get_item("sword")
        self.assertEqual(item.behaviors, [])

    def test_load_item_with_multiple_behaviors(self):
        """Test loading item with multiple behaviors."""
        game_data = self._create_minimal_game_state(
            items=[
                {
                    "id": "lantern",
                    "name": "lantern",
                    "description": "A brass lantern",
                    "type": "tool",
                    "portable": True,
                    "location": "room1",
                    "behaviors": ["behaviors.light:on_take", "behaviors.light:on_drop", "behaviors.light:on_use"]
                }
            ]
        )

        state = load_game_state(game_data)

        item = state.get_item("lantern")
        self.assertEqual(len(item.behaviors), 3)
        self.assertIn("behaviors.light:on_take", item.behaviors)
        self.assertIn("behaviors.light:on_drop", item.behaviors)
        self.assertIn("behaviors.light:on_use", item.behaviors)

    def test_load_npc_with_behaviors(self):
        """Test loading NPC with behaviors field from JSON."""
        game_data = self._create_minimal_game_state(
            npcs=[
                {
                    "id": "wizard",
                    "name": "wizard",
                    "description": "A wise old wizard",
                    "location": "room1",
                    "behaviors": ["behaviors.npcs:on_talk_wizard"]
                }
            ]
        )

        state = load_game_state(game_data)

        npc = state.get_actor("wizard")
        self.assertIn("behaviors.npcs:on_talk_wizard", npc.behaviors)

    def test_load_npc_without_behaviors(self):
        """Test loading NPC without behaviors defaults to empty dict."""
        game_data = self._create_minimal_game_state(
            npcs=[
                {
                    "id": "guard",
                    "name": "guard",
                    "description": "A bored guard",
                    "location": "room1"
                }
            ]
        )

        state = load_game_state(game_data)

        npc = state.get_actor("guard")
        self.assertEqual(npc.behaviors, [])

    def test_load_door_item_with_behaviors(self):
        """Test loading door item with behaviors field from JSON."""
        game_data = self._create_minimal_game_state(
            locations=[
                {
                    "id": "room1",
                    "name": "Room 1",
                    "description": "First room",
                    "exits": {
                        "north": {"type": "door", "to": "room2", "door_id": "door1"}
                    }
                },
                {
                    "id": "room2",
                    "name": "Room 2",
                    "description": "Second room"
                }
            ],
            items=[
                {
                    "id": "door1",
                    "name": "door",
                    "description": "A heavy oak door",
                    "location": "exit:room1:north",
                    "properties": {"door": {"open": False}},
                    "behaviors": ["behaviors.doors:on_open_creaky"]
                }
            ]
        )

        state = load_game_state(game_data)

        door_item = state.get_item("door1")
        self.assertTrue(door_item.is_door)
        self.assertIn("behaviors.doors:on_open_creaky", door_item.behaviors)

    def test_load_door_item_without_behaviors(self):
        """Test loading door item without behaviors defaults to empty list."""
        game_data = self._create_minimal_game_state(
            locations=[
                {
                    "id": "room1",
                    "name": "Room 1",
                    "description": "First room",
                    "exits": {
                        "north": {"type": "door", "to": "room2", "door_id": "door1"}
                    }
                },
                {
                    "id": "room2",
                    "name": "Room 2",
                    "description": "Second room"
                }
            ],
            items=[
                {
                    "id": "door1",
                    "name": "door",
                    "description": "A plain door",
                    "location": "exit:room1:north",
                    "properties": {"door": {"open": False}}
                }
            ]
        )

        state = load_game_state(game_data)

        door_item = state.get_item("door1")
        self.assertTrue(door_item.is_door)
        self.assertEqual(door_item.behaviors, [])

    def test_load_location_with_behaviors(self):
        """Test loading location with behaviors field from JSON."""
        game_data = self._create_minimal_game_state(
            locations=[
                {
                    "id": "room1",
                    "name": "Haunted Room",
                    "description": "A spooky room",
                    "behaviors": ["behaviors.rooms:on_enter_haunted"]
                }
            ]
        )

        state = load_game_state(game_data)

        location = state.get_location("room1")
        self.assertIn("behaviors.rooms:on_enter_haunted", location.behaviors)

    def test_load_location_without_behaviors(self):
        """Test loading location without behaviors defaults to empty dict."""
        game_data = self._create_minimal_game_state()

        state = load_game_state(game_data)

        location = state.get_location("room1")
        self.assertEqual(location.behaviors, [])

    def test_load_from_json_file(self):
        """Test loading game state with behaviors from JSON file."""
        game_data = self._create_minimal_game_state(
            items=[
                {
                    "id": "duck",
                    "name": "rubber duck",
                    "description": "A yellow rubber duck",
                    "type": "tool",
                    "portable": True,
                    "location": "room1",
                    "behaviors": ["behaviors.items.rubber_duck:on_squeeze"]
                }
            ]
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(game_data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            item = state.get_item("duck")
            self.assertIn("behaviors.items.rubber_duck:on_squeeze", item.behaviors)
        finally:
            Path(temp_path).unlink()

    def test_mixed_entities_with_and_without_behaviors(self):
        """Test loading game with mixed entities - some with behaviors, some without."""
        game_data = self._create_minimal_game_state(
            items=[
                {
                    "id": "potion",
                    "name": "potion",
                    "description": "A healing potion",
                    "type": "tool",
                    "portable": True,
                    "location": "room1",
                    "behaviors": ["behaviors:on_drink"]
                },
                {
                    "id": "rock",
                    "name": "rock",
                    "description": "A plain rock",
                    "type": "scenery",
                    "portable": False,
                    "location": "room1"
                }
            ]
        )

        state = load_game_state(game_data)

        potion = state.get_item("potion")
        rock = state.get_item("rock")

        self.assertIn("behaviors:on_drink", potion.behaviors)
        self.assertEqual(rock.behaviors, [])


class TestBehaviorsAndOtherFields(unittest.TestCase):
    """Test that behaviors field coexists with other fields."""

    def test_item_behaviors_with_states(self):
        """Test that item can have both behaviors and states."""
        game_data = {
            "metadata": {
                "title": "Test Game",
                "start_location": "room1"
            },
            "locations": [
                {"id": "room1", "name": "Room", "description": "A room"}
            ],
            "items": [
                {
                    "id": "lantern",
                    "name": "lantern",
                    "description": "A brass lantern",
                    "type": "tool",
                    "portable": True,
                    "location": "room1",
                    "states": {"lit": False},
                    "behaviors": ["behaviors:toggle_light"],
                    "provides_light": True
                }
            ]
        }

        state = load_game_state(game_data)
        item = state.get_item("lantern")

        self.assertIn("behaviors:toggle_light", item.behaviors)
        self.assertEqual(item.states["lit"], False)
        self.assertTrue(item.provides_light)

    def test_item_behaviors_with_llm_context(self):
        """Test that item can have both behaviors and llm_context."""
        game_data = {
            "metadata": {
                "title": "Test Game",
                "start_location": "room1"
            },
            "locations": [
                {"id": "room1", "name": "Room", "description": "A room"}
            ],
            "items": [
                {
                    "id": "potion",
                    "name": "potion",
                    "description": "A potion",
                    "type": "tool",
                    "portable": True,
                    "location": "room1",
                    "llm_context": "This is a magical healing potion",
                    "behaviors": ["behaviors:heal"]
                }
            ]
        }

        state = load_game_state(game_data)
        item = state.get_item("potion")

        self.assertIn("behaviors:heal", item.behaviors)
        self.assertEqual(item.llm_context, "This is a magical healing potion")


if __name__ == '__main__':
    unittest.main()
