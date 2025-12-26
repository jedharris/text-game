"""
Phase 2 tests - StateAccessor._set_path()

These tests verify the low-level state mutation primitive.
Following TDD: Write tests first, then implement to make them pass.

Tests cover:
- Simple field access
- Nested dict access with dots
- List operations (+append, -remove)
- Error cases
"""
from src.types import ActorId
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.conftest import create_test_state
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager


class TestSetPathSimpleFields(unittest.TestCase):
    """Test _set_path() with simple field access."""

    def test_set_simple_field(self):
        """Test setting a simple field."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        item = state.get_item("item_sword")
        error = accessor._set_path(item, "location", "new_location")

        self.assertIsNone(error)
        self.assertEqual(item.location, "new_location")

    def test_set_simple_field_different_type(self):
        """Test setting a field with different value type."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        item = state.get_item("item_sword")
        # Set name (string field)
        error = accessor._set_path(item, "name", "new_name")

        self.assertIsNone(error)
        self.assertEqual(item.name, "new_name")


class TestSetPathNestedDict(unittest.TestCase):
    """Test _set_path() with nested dict access using dots."""

    def test_set_nested_property(self):
        """Test setting nested dict property."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        item = state.get_item("item_sword")
        error = accessor._set_path(item, "properties.health", 50)

        self.assertIsNone(error)
        self.assertEqual(item.properties.get("health"), 50)

    def test_set_deeply_nested(self):
        """Test setting deeply nested property."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        item = state.get_item("item_sword")
        # First set up container dict
        item.properties["container"] = {}
        error = accessor._set_path(item, "properties.container.open", True)

        self.assertIsNone(error)
        self.assertEqual(item.properties["container"]["open"], True)

    def test_set_nested_creates_intermediate(self):
        """Test that setting nested path creates intermediate dicts."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        item = state.get_item("item_sword")
        # Container doesn't exist yet
        error = accessor._set_path(item, "properties.container.capacity", 10)

        self.assertIsNone(error)
        self.assertIn("container", item.properties)
        self.assertEqual(item.properties["container"]["capacity"], 10)


class TestSetPathListOperations(unittest.TestCase):
    """Test _set_path() with list operations."""

    def test_append_to_list(self):
        """Test appending to a list with + prefix."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        actor = state.actors.get(ActorId("player"))
        initial_count = len(actor.inventory)
        error = accessor._set_path(actor, "+inventory", "new_item")

        self.assertIsNone(error)
        self.assertEqual(len(actor.inventory), initial_count + 1)
        self.assertIn("new_item", actor.inventory)

    def test_remove_from_list(self):
        """Test removing from a list with - prefix."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        actor = state.actors.get(ActorId("player"))
        actor.inventory.append("item_to_remove")

        error = accessor._set_path(actor, "-inventory", "item_to_remove")

        self.assertIsNone(error)
        self.assertNotIn("item_to_remove", actor.inventory)

    def test_append_to_nested_list(self):
        """Test appending to nested list in properties."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        item = state.get_item("item_sword")
        item.properties["tags"] = ["weapon"]

        error = accessor._set_path(item, "+properties.tags", "sharp")

        self.assertIsNone(error)
        self.assertIn("sharp", item.properties["tags"])

    def test_remove_from_nested_list(self):
        """Test removing from nested list in properties."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        item = state.get_item("item_sword")
        item.properties["tags"] = ["weapon", "sharp"]

        error = accessor._set_path(item, "-properties.tags", "sharp")

        self.assertIsNone(error)
        self.assertNotIn("sharp", item.properties["tags"])


class TestSetPathErrors(unittest.TestCase):
    """Test _set_path() error cases."""

    def test_field_not_found(self):
        """Test error when field doesn't exist."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        item = state.get_item("item_sword")
        error = accessor._set_path(item, "nonexistent_field", "value")

        self.assertIsNotNone(error)
        self.assertIn("not found", error.lower())

    def test_append_to_non_list(self):
        """Test error when trying to append to non-list."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        item = state.get_item("item_sword")
        error = accessor._set_path(item, "+location", "value")

        self.assertIsNotNone(error)
        self.assertIn("list", error.lower())

    def test_remove_from_non_list(self):
        """Test error when trying to remove from non-list."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        item = state.get_item("item_sword")
        error = accessor._set_path(item, "-location", "value")

        self.assertIsNotNone(error)
        self.assertIn("list", error.lower())

    def test_remove_missing_value(self):
        """Test that removing value not in list raises ValueError (state bug)."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        actor = state.actors.get(ActorId("player"))

        # ValueError should propagate - indicates state bug (item not actually in list)
        with self.assertRaises(ValueError) as ctx:
            accessor._set_path(actor, "-inventory", "not_in_list")
        self.assertIn("not in list", str(ctx.exception))

    def test_nested_field_not_found(self):
        """Test that nested paths create intermediate dicts in properties."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        item = state.get_item("item_sword")
        # This should succeed, creating intermediate dict
        error = accessor._set_path(item, "properties.nonexistent.field", "value")

        # Should succeed (creates intermediate dicts)
        self.assertIsNone(error)
        self.assertEqual(item.properties["nonexistent"]["field"], "value")

    def test_invalid_field_on_dataclass(self):
        """Test error when trying to set non-existent field on dataclass."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        item = state.get_item("item_sword")
        # Try to set a field that doesn't exist on Item dataclass
        error = accessor._set_path(item, "nonexistent_dataclass_field", "value")

        self.assertIsNotNone(error)
        self.assertIn("not found", error.lower())


if __name__ == '__main__':
    unittest.main()
