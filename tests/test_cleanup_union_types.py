"""
Tests for Union type removal (Phase C-5).

Verifies that behaviors field only accepts List[str] format.
"""

import unittest
from src.state_manager import Location, Item, Actor


class TestBehaviorsListOnly(unittest.TestCase):
    """Test that behaviors field only accepts list format."""

    def test_location_behaviors_is_list(self):
        """Test Location behaviors field accepts list."""
        loc = Location(
            id="test", name="test", description="test",
            behaviors=["behaviors.module1", "behaviors.module2"]
        )
        self.assertIsInstance(loc.behaviors, list)
        self.assertEqual(len(loc.behaviors), 2)

    def test_location_behaviors_default_empty_list(self):
        """Test Location behaviors defaults to empty list."""
        loc = Location(id="test", name="test", description="test")
        self.assertIsInstance(loc.behaviors, list)
        self.assertEqual(loc.behaviors, [])

    def test_item_behaviors_is_list(self):
        """Test Item behaviors field accepts list."""
        item = Item(
            id="test", name="test", description="test",
            location="test", behaviors=["behaviors.module1"]
        )
        self.assertIsInstance(item.behaviors, list)
        self.assertEqual(len(item.behaviors), 1)

    def test_item_behaviors_default_empty_list(self):
        """Test Item behaviors defaults to empty list."""
        item = Item(
            id="test", name="test", description="test",
            location="test"
        )
        self.assertIsInstance(item.behaviors, list)
        self.assertEqual(item.behaviors, [])

    def test_door_item_behaviors_is_list(self):
        """Test door item behaviors field accepts list."""
        door_item = Item(
            id="test_door", name="door", description="A door",
            location="exit:loc1:north",
            properties={"door": {"open": False}},
            behaviors=["behaviors.doors"]
        )
        self.assertIsInstance(door_item.behaviors, list)
        self.assertEqual(len(door_item.behaviors), 1)
        self.assertTrue(door_item.is_door)

    def test_door_item_behaviors_default_empty_list(self):
        """Test door item behaviors defaults to empty list."""
        door_item = Item(
            id="test_door", name="door", description="A door",
            location="exit:loc1:north",
            properties={"door": {"open": False}}
        )
        self.assertIsInstance(door_item.behaviors, list)
        self.assertEqual(door_item.behaviors, [])
        self.assertTrue(door_item.is_door)

    def test_actor_behaviors_is_list(self):
        """Test Actor behaviors field accepts list."""
        actor = Actor(
            id="test", name="test", description="test",
            location="test", behaviors=["behaviors.npcs"]
        )
        self.assertIsInstance(actor.behaviors, list)
        self.assertEqual(len(actor.behaviors), 1)

    def test_actor_behaviors_default_empty_list(self):
        """Test Actor behaviors defaults to empty list."""
        actor = Actor(
            id="test", name="test", description="test",
            location="test"
        )
        self.assertIsInstance(actor.behaviors, list)
        self.assertEqual(actor.behaviors, [])


class TestBehaviorsTypeAnnotation(unittest.TestCase):
    """Test that type annotations are correct."""

    def test_location_behaviors_annotation(self):
        """Test Location.behaviors has List[str] annotation."""
        from typing import get_type_hints, List
        hints = get_type_hints(Location)
        # After removing Union, should be List[str]
        self.assertEqual(hints['behaviors'], List[str])

    def test_item_behaviors_annotation(self):
        """Test Item.behaviors has List[str] annotation."""
        from typing import get_type_hints, List
        hints = get_type_hints(Item)
        self.assertEqual(hints['behaviors'], List[str])

    def test_actor_behaviors_annotation(self):
        """Test Actor.behaviors has List[str] annotation."""
        from typing import get_type_hints, List
        hints = get_type_hints(Actor)
        self.assertEqual(hints['behaviors'], List[str])


if __name__ == '__main__':
    unittest.main()
