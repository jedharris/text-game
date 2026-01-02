"""Tests for exit migration tool."""
import json
import unittest
from pathlib import Path
from typing import Any, Dict

from tests.conftest import BaseTestCase


class TestExitMigration(BaseTestCase):
    """Test exit migration from ExitDescriptor to Exit entities."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.fixtures_dir = Path(__file__).parent / "fixtures" / "exit_migration"

    def _load_fixture(self, filename: str) -> Dict[str, Any]:
        """Load a test fixture JSON file."""
        with open(self.fixtures_dir / filename, 'r') as f:
            return json.load(f)

    def test_simple_exits_migration(self):
        """Test migration of simple directional exits."""
        from tools.migrate_exits_to_entities import migrate_exits

        data = self._load_fixture("simple_exits.json")
        migrated = migrate_exits(data)

        # Should have exits list
        self.assertIn("exits", migrated)
        self.assertIsInstance(migrated["exits"], list)

        # Should have 8 exits (4 directions * 2 ends each)
        # loc_a: north, south, east, west (4)
        # loc_b: south (1)
        # loc_c: north (1)
        # loc_d: west (1)
        # loc_e: east (1)
        self.assertEqual(len(migrated["exits"]), 8)

        # Check first exit (loc_a north)
        exit_a_north = next(e for e in migrated["exits"] if e["id"] == "exit_loc_a_north")
        self.assertEqual(exit_a_north["name"], "exit")
        self.assertEqual(exit_a_north["location"], "loc_a")
        self.assertEqual(exit_a_north["direction"], "north")
        self.assertIn("exit_loc_b_south", exit_a_north["connections"])

        # Check symmetric connection
        exit_b_south = next(e for e in migrated["exits"] if e["id"] == "exit_loc_b_south")
        self.assertEqual(exit_b_south["location"], "loc_b")
        self.assertEqual(exit_b_south["direction"], "south")
        self.assertIn("exit_loc_a_north", exit_b_south["connections"])

    def test_doors_migration(self):
        """Test migration of door exits."""
        from tools.migrate_exits_to_entities import migrate_exits

        data = self._load_fixture("doors.json")
        migrated = migrate_exits(data)

        # Should have 2 exits (door from both sides)
        self.assertEqual(len(migrated["exits"]), 2)

        # Check door exit from room1
        exit_room1_north = next(e for e in migrated["exits"] if e["id"] == "exit_loc_room1_north")
        self.assertEqual(exit_room1_north["name"], "wooden door")
        self.assertEqual(exit_room1_north["location"], "loc_room1")
        self.assertEqual(exit_room1_north["direction"], "north")
        self.assertIn("exit_loc_room2_south", exit_room1_north["connections"])

        # Check properties preserved
        self.assertEqual(exit_room1_north.get("description"), "A sturdy wooden door.")

    def test_exit_id_generation(self):
        """Test exit ID generation is deterministic."""
        from tools.migrate_exits_to_entities import generate_exit_id

        # Directional exit
        exit_id = generate_exit_id("loc_forest", "north", None)
        self.assertEqual(exit_id, "exit_loc_forest_north")

        # Named exit without direction
        exit_id = generate_exit_id("loc_hall", None, "spiral staircase")
        self.assertEqual(exit_id, "exit_loc_hall_spiral_staircase")

        # Named exit with direction (direction takes precedence)
        exit_id = generate_exit_id("loc_hall", "up", "stairs")
        self.assertEqual(exit_id, "exit_loc_hall_up")

    def test_migration_preserves_all_fields(self):
        """Test that migration preserves all optional fields."""
        from tools.migrate_exits_to_entities import migrate_exit_descriptor

        descriptor = {
            "type": "open",
            "to": "loc_target",
            "name": "stone archway",
            "description": "A grand archway of carved stone",
            "behaviors": ["behaviors.exits.custom"],
            "properties": {"hidden": False, "locked": False}
        }

        exit_entity = migrate_exit_descriptor(
            descriptor, "loc_source", "east", "exit_loc_source_east"
        )

        self.assertEqual(exit_entity["name"], "stone archway")
        self.assertEqual(exit_entity["description"], "A grand archway of carved stone")
        self.assertEqual(exit_entity["behaviors"], ["behaviors.exits.custom"])
        self.assertEqual(exit_entity["properties"], {"hidden": False, "locked": False})

    def test_migration_handles_missing_fields(self):
        """Test migration handles exits with minimal/missing fields."""
        from tools.migrate_exits_to_entities import migrate_exit_descriptor

        descriptor = {
            "type": "open",
            "to": "loc_target"
        }

        exit_entity = migrate_exit_descriptor(
            descriptor, "loc_source", "north", "exit_loc_source_north"
        )

        self.assertEqual(exit_entity["name"], "exit")
        self.assertEqual(exit_entity["description"], "")
        self.assertEqual(exit_entity["behaviors"], [])
        self.assertEqual(exit_entity["properties"], {})

    def test_connection_mapping_bidirectional(self):
        """Test that bidirectional connections are mapped correctly."""
        from tools.migrate_exits_to_entities import build_connection_map

        data = self._load_fixture("simple_exits.json")
        connection_map = build_connection_map(data)

        # Check north/south pair
        self.assertIn(("loc_a", "north"), connection_map)
        self.assertIn(("loc_b", "south"), connection_map)

        # They should reference each other
        loc_a_north = connection_map[("loc_a", "north")]
        loc_b_south = connection_map[("loc_b", "south")]

        self.assertEqual(loc_a_north["target_location"], "loc_b")
        self.assertEqual(loc_b_south["target_location"], "loc_a")

    def test_validation_catches_missing_location(self):
        """Test validation catches references to non-existent locations."""
        from tools.migrate_exits_to_entities import validate_pre_migration

        data = {
            "locations": [
                {
                    "id": "loc_a",
                    "name": "Room A",
                    "description": "A room",
                    "exits": {
                        "north": {
                            "type": "open",
                            "to": "loc_nonexistent"
                        }
                    }
                }
            ]
        }

        with self.assertRaises(ValueError) as ctx:
            validate_pre_migration(data)

        self.assertIn("loc_nonexistent", str(ctx.exception))
        self.assertIn("does not exist", str(ctx.exception))

    def test_validation_catches_missing_door(self):
        """Test validation catches references to non-existent doors."""
        from tools.migrate_exits_to_entities import validate_pre_migration

        data = {
            "locations": [
                {
                    "id": "loc_a",
                    "name": "Room A",
                    "description": "A room",
                    "exits": {
                        "north": {
                            "type": "door",
                            "to": "loc_b",
                            "door_id": "door_missing"
                        }
                    }
                },
                {
                    "id": "loc_b",
                    "name": "Room B",
                    "description": "Another room",
                    "exits": {}
                }
            ],
            "items": []
        }

        with self.assertRaises(ValueError) as ctx:
            validate_pre_migration(data)

        self.assertIn("door_missing", str(ctx.exception))

    def test_post_migration_validation(self):
        """Test post-migration validation checks connections."""
        from tools.migrate_exits_to_entities import validate_post_migration

        migrated = {
            "exits": [
                {
                    "id": "exit_a_north",
                    "name": "exit",
                    "location": "loc_a",
                    "connections": ["exit_b_south"],
                    "direction": "north"
                },
                {
                    "id": "exit_b_south",
                    "name": "exit",
                    "location": "loc_b",
                    "connections": ["exit_a_north"],
                    "direction": "south"
                }
            ]
        }

        # Should pass validation
        validate_post_migration(migrated)

    def test_post_migration_validation_catches_orphan(self):
        """Test post-migration validation catches orphaned connections."""
        from tools.migrate_exits_to_entities import validate_post_migration

        migrated = {
            "exits": [
                {
                    "id": "exit_a_north",
                    "name": "exit",
                    "location": "loc_a",
                    "connections": ["exit_nonexistent"],
                    "direction": "north"
                }
            ]
        }

        with self.assertRaises(ValueError) as ctx:
            validate_post_migration(migrated)

        self.assertIn("exit_nonexistent", str(ctx.exception))
        self.assertIn("does not exist", str(ctx.exception))

    def test_migration_is_deterministic(self):
        """Test that migration produces same output for same input."""
        from tools.migrate_exits_to_entities import migrate_exits

        data = self._load_fixture("simple_exits.json")

        migrated1 = migrate_exits(data.copy())
        migrated2 = migrate_exits(data.copy())

        # Sort exits by ID for comparison
        exits1 = sorted(migrated1["exits"], key=lambda e: e["id"])
        exits2 = sorted(migrated2["exits"], key=lambda e: e["id"])

        self.assertEqual(exits1, exits2)


if __name__ == '__main__':
    unittest.main()
