"""
Tests for Part entity validation.

Following TDD approach - these tests are written first before implementation.
"""
import unittest
from src.state_manager import Part, GameState, Metadata, Location, Item
from src.validators import ValidationError, validate_game_state


class TestPartValidation(unittest.TestCase):
    """Test Part validation rules."""

    def test_valid_part_passes_validation(self):
        """Test that valid part passes validation."""
        location = Location(id="loc_room", name="Room", description="A room")
        part = Part(id="part_wall", name="wall", part_of="loc_room")

        metadata = Metadata(title="Test", start_location="loc_room")
        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[],
            actors={},
            locks=[],
            parts=[part]
        )

        # Should not raise ValidationError
        try:
            validate_game_state(game_state)
        except ValidationError:
            self.fail("Valid part should not raise ValidationError")

    def test_part_with_invalid_parent_fails(self):
        """Test part referencing non-existent parent fails validation."""
        part = Part(id="part_wall", name="wall", part_of="loc_nonexistent")

        metadata = Metadata(title="Test", start_location="loc_room")
        location = Location(id="loc_room", name="Room", description="A room")
        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[],
            actors={},
            locks=[],
            parts=[part]
        )

        with self.assertRaises(ValidationError) as cm:
            validate_game_state(game_state)

        error_msg = str(cm.exception).lower()
        self.assertTrue(
            "non-existent" in error_msg or "not found" in error_msg,
            f"Expected error about non-existent parent, got: {error_msg}"
        )

    def test_part_duplicate_id_fails(self):
        """Test part with duplicate ID fails validation."""
        location = Location(id="loc_room", name="Room", description="A room")
        item = Item(
            id="item_duplicate",
            name="Item",
            description="An item",
            location="loc_room"
        )
        part = Part(
            id="item_duplicate",  # Duplicate ID
            name="wall",
            part_of="loc_room"
        )

        metadata = Metadata(title="Test", start_location="loc_room")
        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[item],
            actors={},
            locks=[],
            parts=[part]
        )

        with self.assertRaises(ValidationError) as cm:
            validate_game_state(game_state)

        error_msg = str(cm.exception).lower()
        self.assertTrue(
            "duplicate" in error_msg,
            f"Expected error about duplicate ID, got: {error_msg}"
        )

    def test_nested_part_fails_in_phase_1(self):
        """Test part with part as parent fails in Phase 1."""
        location = Location(id="loc_room", name="Room", description="A room")
        parent_part = Part(id="part_wall", name="wall", part_of="loc_room")
        nested_part = Part(
            id="part_wall_section",
            name="section",
            part_of="part_wall"  # Not allowed in Phase 1
        )

        metadata = Metadata(title="Test", start_location="loc_room")
        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[],
            actors={},
            locks=[],
            parts=[parent_part, nested_part]
        )

        with self.assertRaises(ValidationError) as cm:
            validate_game_state(game_state)

        error_msg = str(cm.exception).lower()
        self.assertTrue(
            "nested" in error_msg or "part as parent" in error_msg,
            f"Expected error about nested parts, got: {error_msg}"
        )

    def test_part_can_have_item_as_parent(self):
        """Test part can have item as parent (multi-sided objects)."""
        location = Location(id="loc_room", name="Room", description="A room")
        item = Item(
            id="item_bench",
            name="bench",
            description="A bench",
            location="loc_room"
        )
        part = Part(id="part_bench_left", name="left side", part_of="item_bench")

        metadata = Metadata(title="Test", start_location="loc_room")
        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[item],
            actors={},
            locks=[],
            parts=[part]
        )

        # Should not raise ValidationError
        try:
            validate_game_state(game_state)
        except ValidationError:
            self.fail("Part with item as parent should not raise ValidationError")


if __name__ == '__main__':
    unittest.main()
