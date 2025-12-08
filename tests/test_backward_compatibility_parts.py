"""
Test backward compatibility for Part entities.

Ensures that existing games without parts work unchanged.
"""
import unittest
import json
import tempfile
import os
from src.state_manager import GameState, Metadata, Location, Item, Actor, load_game_state
from src.state_accessor import StateAccessor
from src.validators import validate_game_state


class TestBackwardCompatibilityParts(unittest.TestCase):
    """Test that existing games without parts work unchanged."""

    def test_game_without_parts_field_loads(self):
        """Test game JSON without 'parts' field loads successfully."""
        game_json = {
            "metadata": {
                "title": "Legacy Game",
                "start_location": "loc_start"
            },
            "locations": [
                {
                    "id": "loc_start",
                    "name": "Start Room",
                    "description": "A starting room",
                    "exits": {}
                }
            ],
            "items": [
                {
                    "id": "item_key",
                    "name": "key",
                    "description": "A brass key",
                    "location": "loc_start"
                }
            ],
            "actors": {
                "player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "loc_start"}
            },
            "locks": []
            # Note: No 'parts' field - should default to empty list
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(game_json, f)
            temp_path = f.name

        try:
            game_state = load_game_state(temp_path)

            # Should load successfully
            self.assertIsNotNone(game_state)

            # Parts should be empty list
            self.assertEqual(len(game_state.parts), 0)

            # Other entities should load normally
            self.assertEqual(len(game_state.locations), 1)
            self.assertEqual(len(game_state.items), 1)

        finally:
            os.unlink(temp_path)

    def test_game_with_empty_parts_list(self):
        """Test game with explicit empty parts list."""
        game_json = {
            "metadata": {"title": "Test", "start_location": "loc_1"},
            "locations": [{"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}],
            "items": [],
            "actors": {
                "player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "loc_1"}
            },
            "locks": [],
            "parts": []  # Explicit empty list
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(game_json, f)
            temp_path = f.name

        try:
            game_state = load_game_state(temp_path)
            self.assertEqual(len(game_state.parts), 0)
        finally:
            os.unlink(temp_path)

    def test_state_accessor_methods_safe_with_no_parts(self):
        """Test StateAccessor part methods safe when no parts exist."""
        metadata = Metadata(title="Test", start_location="loc_room")
        location = Location(id="loc_room", name="Room", description="A room")

        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[],
            actors={"player": Actor(id="player", name="Adventurer", description="The player", location="loc_room", inventory=[])},
            locks=[],
            parts=[]  # No parts
        )

        accessor = StateAccessor(game_state, None)

        # All part methods should handle empty parts gracefully
        part = accessor.get_part("nonexistent")
        self.assertIsNone(part)

        parts = accessor.get_parts_of("loc_room")
        self.assertEqual(parts, [])

        items_at_part = accessor.get_items_at_part("nonexistent")
        self.assertEqual(items_at_part, [])

        # get_entity should still work for non-part entities
        loc = accessor.get_entity("loc_room")
        self.assertIsNotNone(loc)
        self.assertEqual(loc.id, "loc_room")

    def test_validation_passes_with_no_parts(self):
        """Test validation succeeds for games without parts."""
        metadata = Metadata(title="Test", start_location="loc_room")
        location = Location(id="loc_room", name="Room", description="A room")
        item = Item(
            id="item_key",
            name="key",
            description="A key",
            location="loc_room"
        )

        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[item],
            actors={"player": Actor(id="player", name="Adventurer", description="The player", location="loc_room", inventory=[])},
            locks=[],
            parts=[]  # No parts
        )

        # Should not raise ValidationError
        try:
            validate_game_state(game_state)
        except Exception as e:
            self.fail(f"Validation should pass for game without parts, but got: {e}")

    def test_items_at_location_not_confused_with_parts(self):
        """Test items in locations not confused with items at parts."""
        metadata = Metadata(title="Test", start_location="loc_room")
        location = Location(id="loc_room", name="Room", description="A room")

        item1 = Item(
            id="item_table",
            name="table",
            description="A table",
            location="loc_room"
        )
        item2 = Item(
            id="item_key",
            name="key",
            description="A key",
            location="loc_room"
        )

        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[item1, item2],
            actors={"player": Actor(id="player", name="Adventurer", description="The player", location="loc_room", inventory=[])},
            locks=[],
            parts=[]  # No parts
        )

        accessor = StateAccessor(game_state, None)

        # Items should be findable at location
        items_in_room = [i for i in game_state.items if i.location == "loc_room"]
        self.assertEqual(len(items_in_room), 2)

        # No items at any part
        items_at_parts = [i for i in game_state.items
                         if i.location.startswith("part_")]
        self.assertEqual(len(items_at_parts), 0)


if __name__ == '__main__':
    unittest.main()
