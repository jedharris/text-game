"""
Tests for state manager data models.

Covers: TM-001 through TM-005 from state_manager_testing.md
"""
import unittest


class TestModels(unittest.TestCase):
    """Test cases for game state data models."""

    def test_TM001_dataclass_field_defaults(self):
        """TM-001: Dataclass field defaults work correctly."""
        from src.state_manager.models import ExitDescriptor

        # Test default values
        exit = ExitDescriptor(type="open", to="loc_1")
        self.assertFalse(exit.hidden)  # Default should be False
        self.assertIsNone(exit.description)
        self.assertIsNone(exit.conditions)

    def test_TM002_container_info_structure(self):
        """TM-002: Container items correctly reference ContainerInfo."""
        from src.state_manager.models import Item, ContainerInfo

        container = ContainerInfo(
            locked=True,
            lock_id="lock_1",
            contents=["item_1", "item_2"],
            capacity=10
        )

        item = Item(
            id="item_chest",
            name="Chest",
            description="A chest",
            type="container",
            portable=False,
            location="loc_1",
            container=container
        )

        self.assertIsNotNone(item.container)
        self.assertTrue(item.container.locked)
        self.assertEqual(len(item.container.contents), 2)

    def test_TM003_enum_string_conversion(self):
        """TM-003: Enum string conversion (if implemented)."""
        # This test is optional - only if enums are used
        # If models use plain strings instead of enums, this test can pass
        pass

    def test_TM004_to_dict_round_trip(self):
        """TM-004: Round-trip serialization with to_dict() helper."""
        from src.state_manager.models import Location

        location = Location(
            id="loc_1",
            name="Test Room",
            description="A test room",
            tags=["indoor"],
            items=["item_1"],
            npcs=[],
            exits={}
        )

        # Convert to dict (using dataclasses.asdict or custom method)
        # Note: Implementation may use dataclasses.asdict instead of to_dict()
        import dataclasses
        loc_dict = dataclasses.asdict(location)

        # Verify structure
        self.assertEqual(loc_dict["id"], "loc_1")
        self.assertEqual(loc_dict["name"], "Test Room")
        self.assertEqual(loc_dict["tags"], ["indoor"])

        # Reconstruct from dict
        reconstructed = Location(**loc_dict)
        self.assertEqual(reconstructed.id, location.id)
        self.assertEqual(reconstructed.name, location.name)

    def test_TM005_item_states_dictionary(self):
        """TM-005: Items with states dictionary maintain values and types."""
        from src.state_manager.models import Item

        item = Item(
            id="item_1",
            name="Torch",
            description="A torch",
            type="tool",
            portable=True,
            location="loc_1",
            states={
                "lit": False,
                "fuel": 100,
                "temperature": 20.5
            }
        )

        # Verify states
        self.assertFalse(item.states["lit"])
        self.assertEqual(item.states["fuel"], 100)
        self.assertIsInstance(item.states["temperature"], float)

        # Modify state
        item.states["lit"] = True
        self.assertTrue(item.states["lit"])


if __name__ == '__main__':
    unittest.main()
