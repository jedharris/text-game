"""Tests for loading game state with behaviors field (Phase 3)."""

import unittest
import json
import tempfile
from pathlib import Path

from src.state_manager import load_game_state, Item, NPC, Door, Location


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
        self.assertEqual(item.behaviors, {})

    def test_item_with_behaviors(self):
        """Test creating Item with behaviors."""
        item = Item(
            id="test_item",
            name="Test",
            description="A test item",
            location="room1",
            properties={"type": "tool", "portable": True},
            behaviors={"on_take": "module:on_take", "on_drop": "module:on_drop"}
        )
        self.assertEqual(item.behaviors["on_take"], "module:on_take")
        self.assertEqual(item.behaviors["on_drop"], "module:on_drop")

    def test_npc_has_behaviors_field(self):
        """Test that NPC model has behaviors field."""
        npc = NPC(
            id="test_npc",
            name="Test NPC",
            description="A test NPC",
            location="room1"
        )
        self.assertEqual(npc.behaviors, {})

    def test_npc_with_behaviors(self):
        """Test creating NPC with behaviors."""
        npc = NPC(
            id="test_npc",
            name="Test NPC",
            description="A test NPC",
            location="room1",
            behaviors={"on_talk": "module:on_talk"}
        )
        self.assertEqual(npc.behaviors["on_talk"], "module:on_talk")

    def test_door_has_behaviors_field(self):
        """Test that Door model has behaviors field."""
        door = Door(
            id="test_door",
            locations=("room1", "room2"),
            properties={"description": "A test door"}
        )
        self.assertEqual(door.behaviors, {})

    def test_door_with_behaviors(self):
        """Test creating Door with behaviors."""
        door = Door(
            id="test_door",
            locations=("room1", "room2"),
            properties={"description": "A test door"},
            behaviors={"on_open": "module:on_open", "on_close": "module:on_close"}
        )
        self.assertEqual(door.behaviors["on_open"], "module:on_open")

    def test_location_has_behaviors_field(self):
        """Test that Location model has behaviors field."""
        location = Location(
            id="room1",
            name="Test Room",
            description="A test room"
        )
        self.assertEqual(location.behaviors, {})

    def test_location_with_behaviors(self):
        """Test creating Location with behaviors."""
        location = Location(
            id="room1",
            name="Test Room",
            description="A test room",
            behaviors={"on_enter": "module:on_enter", "on_exit": "module:on_exit"}
        )
        self.assertEqual(location.behaviors["on_enter"], "module:on_enter")


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
            "doors": [],
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
                    "behaviors": {
                        "on_drink": "behaviors.consumables:on_drink_health_potion"
                    }
                }
            ]
        )

        state = load_game_state(game_data)

        item = state.get_item("potion")
        self.assertEqual(item.behaviors["on_drink"], "behaviors.consumables:on_drink_health_potion")

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
        self.assertEqual(item.behaviors, {})

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
                    "behaviors": {
                        "on_take": "behaviors.light:on_take",
                        "on_drop": "behaviors.light:on_drop",
                        "on_use": "behaviors.light:on_use"
                    }
                }
            ]
        )

        state = load_game_state(game_data)

        item = state.get_item("lantern")
        self.assertEqual(len(item.behaviors), 3)
        self.assertEqual(item.behaviors["on_take"], "behaviors.light:on_take")
        self.assertEqual(item.behaviors["on_drop"], "behaviors.light:on_drop")
        self.assertEqual(item.behaviors["on_use"], "behaviors.light:on_use")

    def test_load_npc_with_behaviors(self):
        """Test loading NPC with behaviors field from JSON."""
        game_data = self._create_minimal_game_state(
            npcs=[
                {
                    "id": "wizard",
                    "name": "wizard",
                    "description": "A wise old wizard",
                    "location": "room1",
                    "behaviors": {
                        "on_talk": "behaviors.npcs:on_talk_wizard"
                    }
                }
            ]
        )

        state = load_game_state(game_data)

        npc = state.get_npc("wizard")
        self.assertEqual(npc.behaviors["on_talk"], "behaviors.npcs:on_talk_wizard")

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

        npc = state.get_npc("guard")
        self.assertEqual(npc.behaviors, {})

    def test_load_door_with_behaviors(self):
        """Test loading door with behaviors field from JSON."""
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
            doors=[
                {
                    "id": "door1",
                    "locations": ["room1", "room2"],
                    "description": "A heavy oak door",
                    "behaviors": {
                        "on_open": "behaviors.doors:on_open_creaky"
                    }
                }
            ]
        )

        state = load_game_state(game_data)

        door = state.get_door("door1")
        self.assertEqual(door.behaviors["on_open"], "behaviors.doors:on_open_creaky")

    def test_load_door_without_behaviors(self):
        """Test loading door without behaviors defaults to empty dict."""
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
            doors=[
                {
                    "id": "door1",
                    "locations": ["room1", "room2"],
                    "description": "A plain door"
                }
            ]
        )

        state = load_game_state(game_data)

        door = state.get_door("door1")
        self.assertEqual(door.behaviors, {})

    def test_load_location_with_behaviors(self):
        """Test loading location with behaviors field from JSON."""
        game_data = self._create_minimal_game_state(
            locations=[
                {
                    "id": "room1",
                    "name": "Haunted Room",
                    "description": "A spooky room",
                    "behaviors": {
                        "on_enter": "behaviors.rooms:on_enter_haunted"
                    }
                }
            ]
        )

        state = load_game_state(game_data)

        location = state.get_location("room1")
        self.assertEqual(location.behaviors["on_enter"], "behaviors.rooms:on_enter_haunted")

    def test_load_location_without_behaviors(self):
        """Test loading location without behaviors defaults to empty dict."""
        game_data = self._create_minimal_game_state()

        state = load_game_state(game_data)

        location = state.get_location("room1")
        self.assertEqual(location.behaviors, {})

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
                    "behaviors": {
                        "on_squeeze": "behaviors.items.rubber_duck:on_squeeze"
                    }
                }
            ]
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(game_data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            item = state.get_item("duck")
            self.assertEqual(item.behaviors["on_squeeze"], "behaviors.items.rubber_duck:on_squeeze")
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
                    "behaviors": {"on_drink": "behaviors:on_drink"}
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

        self.assertEqual(potion.behaviors["on_drink"], "behaviors:on_drink")
        self.assertEqual(rock.behaviors, {})


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
                    "behaviors": {"on_use": "behaviors:toggle_light"},
                    "provides_light": True
                }
            ]
        }

        state = load_game_state(game_data)
        item = state.get_item("lantern")

        self.assertEqual(item.behaviors["on_use"], "behaviors:toggle_light")
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
                    "behaviors": {"on_drink": "behaviors:heal"}
                }
            ]
        }

        state = load_game_state(game_data)
        item = state.get_item("potion")

        self.assertEqual(item.behaviors["on_drink"], "behaviors:heal")
        self.assertEqual(item.llm_context, "This is a magical healing potion")


if __name__ == '__main__':
    unittest.main()
