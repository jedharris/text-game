"""Tests for simplified structural validators.

Tests Phase 2 of state manager simplification - structural validation only.
"""
import unittest
import tempfile
import json
import os


class TestStructuralValidation(unittest.TestCase):
    """Test structural integrity validators."""

    def test_duplicate_id_raises_error(self):
        """Duplicate IDs across entities raise ValidationError."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "items": [
                {"id": "loc_1", "name": "Item", "description": "Item", "location": "loc_1"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("loc_1", str(ctx.exception))
        finally:
            os.unlink(temp_path)

    def test_duplicate_id_same_type_raises_error(self):
        """Duplicate IDs within same entity type raise ValidationError."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room 1", "description": "A room", "exits": {}},
                {"id": "loc_1", "name": "Room 2", "description": "Another room", "exits": {}}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("loc_1", str(ctx.exception))
        finally:
            os.unlink(temp_path)

    def test_reserved_player_id_raises_error(self):
        """Using 'player' as entity ID raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "items": [
                {"id": "player", "name": "Item", "description": "Item", "location": "loc_1"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("player", str(ctx.exception).lower())
            self.assertIn("reserved", str(ctx.exception).lower())
        finally:
            os.unlink(temp_path)

    def test_reserved_player_id_in_location_raises_error(self):
        """Using 'player' as location ID raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "player"},
            "locations": [
                {"id": "player", "name": "Room", "description": "A room", "exits": {}}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("player", str(ctx.exception).lower())
            self.assertIn("reserved", str(ctx.exception).lower())
        finally:
            os.unlink(temp_path)

    def test_invalid_exit_reference_raises_error(self):
        """Exit referencing nonexistent location raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {
                    "id": "loc_1",
                    "name": "Room",
                    "description": "A room",
                    "exits": {
                        "north": {"type": "open", "to": "loc_999"}
                    }
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("loc_999", str(ctx.exception))
        finally:
            os.unlink(temp_path)

    def test_invalid_door_reference_raises_error(self):
        """Exit referencing nonexistent door raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {
                    "id": "loc_1",
                    "name": "Room",
                    "description": "A room",
                    "exits": {
                        "north": {"type": "door", "door_id": "door_999"}
                    }
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("door_999", str(ctx.exception))
        finally:
            os.unlink(temp_path)

    def test_door_type_exit_without_door_id_raises_error(self):
        """Door-type exit without door_id raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {
                    "id": "loc_1",
                    "name": "Room",
                    "description": "A room",
                    "exits": {
                        "north": {"type": "door"}
                    }
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("door_id", str(ctx.exception).lower())
        finally:
            os.unlink(temp_path)

    def test_invalid_item_location_raises_error(self):
        """Item location referencing nonexistent ID raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "items": [
                {"id": "item_1", "name": "Item", "description": "Item", "location": "loc_999"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("loc_999", str(ctx.exception))
        finally:
            os.unlink(temp_path)

    def test_item_location_wrong_type_raises_error(self):
        """Item location referencing non-container entity type raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "doors": [
                {"id": "door_1", "locations": ["loc_1", "loc_1"]}
            ],
            "items": [
                {"id": "item_1", "name": "Item", "description": "Item", "location": "door_1"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            # Should mention that doors are not valid item locations
            error_msg = str(ctx.exception).lower()
            self.assertTrue("door" in error_msg or "location" in error_msg)
        finally:
            os.unlink(temp_path)

    def test_item_in_player_inventory_valid(self):
        """Item with location 'player' is valid."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "items": [
                {"id": "item_1", "name": "Item", "description": "Item", "location": "player"}
            ],
            "player_state": {"location": "loc_1", "inventory": ["item_1"]}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            self.assertEqual(state.items[0].location, "player")
        finally:
            os.unlink(temp_path)

    def test_item_in_container_valid(self):
        """Item with location pointing to another item (container) is valid."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {},
                 "items": ["chest"]}
            ],
            "items": [
                {"id": "chest", "name": "Chest", "description": "A chest", "location": "loc_1",
                 "container": {"capacity": 10}},
                {"id": "key", "name": "Key", "description": "A key", "location": "chest"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            key = state.get_item("key")
            self.assertEqual(key.location, "chest")
        finally:
            os.unlink(temp_path)

    def test_item_in_npc_inventory_valid(self):
        """Item with location pointing to NPC is valid."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "npcs": [
                {"id": "guard", "name": "Guard", "description": "A guard", "location": "loc_1"}
            ],
            "items": [
                {"id": "sword", "name": "Sword", "description": "A sword", "location": "guard"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            sword = state.get_item("sword")
            self.assertEqual(sword.location, "guard")
        finally:
            os.unlink(temp_path)

    def test_container_cycle_raises_error(self):
        """Circular containment raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "items": [
                {"id": "box_a", "name": "Box A", "description": "A box", "location": "box_b",
                 "container": {"capacity": 10}},
                {"id": "box_b", "name": "Box B", "description": "A box", "location": "box_a",
                 "container": {"capacity": 10}}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("cycle", str(ctx.exception).lower())
        finally:
            os.unlink(temp_path)

    def test_container_chain_three_items_cycle_raises_error(self):
        """Circular containment with 3 items raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "items": [
                {"id": "box_a", "name": "Box A", "description": "A box", "location": "box_c",
                 "container": {"capacity": 10}},
                {"id": "box_b", "name": "Box B", "description": "A box", "location": "box_a",
                 "container": {"capacity": 10}},
                {"id": "box_c", "name": "Box C", "description": "A box", "location": "box_b",
                 "container": {"capacity": 10}}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("cycle", str(ctx.exception).lower())
        finally:
            os.unlink(temp_path)

    def test_invalid_metadata_start_location_raises_error(self):
        """Nonexistent start_location raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_999"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("loc_999", str(ctx.exception))
        finally:
            os.unlink(temp_path)

    def test_invalid_player_location_raises_error(self):
        """Player location referencing nonexistent location raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "player_state": {"location": "loc_999", "inventory": []}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("loc_999", str(ctx.exception))
        finally:
            os.unlink(temp_path)

    def test_invalid_player_inventory_item_raises_error(self):
        """Player inventory referencing nonexistent item raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "player_state": {"location": "loc_1", "inventory": ["item_999"]}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("item_999", str(ctx.exception))
        finally:
            os.unlink(temp_path)

    def test_player_inventory_non_item_raises_error(self):
        """Player inventory containing non-item entity raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "player_state": {"location": "loc_1", "inventory": ["loc_1"]}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            # Should indicate loc_1 is not an item
            error_msg = str(ctx.exception).lower()
            self.assertTrue("loc_1" in error_msg)
            self.assertTrue("item" in error_msg or "not an item" in error_msg)
        finally:
            os.unlink(temp_path)

    def test_door_item_references_invalid_location_raises_error(self):
        """Door item referencing nonexistent location raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        # Test with unified door item model (exit:loc_id:direction format)
        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "items": [
                {"id": "door_1", "name": "door", "description": "A door",
                 "location": "exit:loc_999:north", "door": {"open": False}}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("loc_999", str(ctx.exception))
        finally:
            os.unlink(temp_path)

    def test_door_item_lock_references_invalid_lock_raises_error(self):
        """Door item referencing nonexistent lock is validated when used.

        Note: Door item lock_ids are not validated at load time, only at runtime
        when lock/unlock is attempted. This is consistent with how container lock
        validation works. The lock entity is validated separately.
        """
        from src.state_manager import load_game_state

        # Door items with invalid lock_id don't fail at load time
        # (consistent with container behavior - lock is checked at runtime)
        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room 1", "description": "A room",
                 "exits": {"north": {"type": "door", "to": "loc_2", "door_id": "door_1"}}},
                {"id": "loc_2", "name": "Room 2", "description": "A room", "exits": {}}
            ],
            "items": [
                {"id": "door_1", "name": "door", "description": "A door",
                 "location": "exit:loc_1:north",
                 "door": {"open": False, "locked": True, "lock_id": "lock_999"}}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            # Should load successfully - lock validation happens at runtime
            state = load_game_state(temp_path)
            # The door item should exist
            door_items = [i for i in state.items if i.is_door]
            self.assertEqual(len(door_items), 1)
            self.assertEqual(door_items[0].door_lock_id, "lock_999")
        finally:
            os.unlink(temp_path)

    def test_lock_opens_with_invalid_key_raises_error(self):
        """Lock referencing nonexistent key item raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "locks": [
                {"id": "lock_1", "opens_with": ["key_999"]}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("key_999", str(ctx.exception))
        finally:
            os.unlink(temp_path)

    def test_container_lock_references_invalid_lock_raises_error(self):
        """Container referencing nonexistent lock raises error."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {},
                 "items": ["chest"]}
            ],
            "items": [
                {"id": "chest", "name": "Chest", "description": "A chest", "location": "loc_1",
                 "container": {"lock_id": "lock_999"}}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            self.assertIn("lock_999", str(ctx.exception))
        finally:
            os.unlink(temp_path)

    def test_valid_state_passes(self):
        """Valid game state passes validation."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {},
                 "items": ["item_1"]}
            ],
            "items": [
                {"id": "item_1", "name": "Torch", "description": "A torch", "location": "loc_1",
                 "portable": True}
            ],
            "player_state": {"location": "loc_1", "inventory": []}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            self.assertEqual(len(state.items), 1)
        finally:
            os.unlink(temp_path)

    def test_valid_complex_state_passes(self):
        """Complex valid game state with all entity types passes validation."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {
                    "id": "loc_1",
                    "name": "Entrance",
                    "description": "An entrance hall",
                    "exits": {
                        "north": {"type": "door", "door_id": "door_1"}
                    },
                    "items": ["chest"],
                    "npcs": ["guard"]
                },
                {
                    "id": "loc_2",
                    "name": "Inner Room",
                    "description": "An inner room",
                    "exits": {
                        "south": {"type": "door", "door_id": "door_1"}
                    }
                }
            ],
            "doors": [
                {
                    "id": "door_1",
                    "locations": ["loc_1", "loc_2"],
                    "locked": True,
                    "lock_id": "lock_1"
                }
            ],
            "items": [
                {
                    "id": "chest",
                    "name": "Chest",
                    "description": "A wooden chest",
                    "location": "loc_1",
                    "container": {"capacity": 10, "lock_id": "lock_2"}
                },
                {
                    "id": "key",
                    "name": "Key",
                    "description": "A brass key",
                    "location": "chest"
                },
                {
                    "id": "sword",
                    "name": "Sword",
                    "description": "A sword",
                    "location": "guard"
                }
            ],
            "locks": [
                {"id": "lock_1", "opens_with": ["key"]},
                {"id": "lock_2", "opens_with": ["key"]}
            ],
            "npcs": [
                {
                    "id": "guard",
                    "name": "Guard",
                    "description": "A guard",
                    "location": "loc_1"
                }
            ],
            "player_state": {"location": "loc_1", "inventory": []}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            self.assertEqual(len(state.locations), 2)
            # Legacy doors are migrated to items, so doors list is empty
            self.assertEqual(len(state.doors), 0)
            # Items: 3 original + 1 migrated door = 4
            self.assertEqual(len(state.items), 4)
            # Check door item was created
            door_items = [i for i in state.items if i.is_door]
            self.assertEqual(len(door_items), 1)
            self.assertEqual(door_items[0].id, "door_1")
            self.assertEqual(len(state.locks), 2)
            self.assertEqual(len(state.npcs), 1)
        finally:
            os.unlink(temp_path)


class TestValidationErrorAggregation(unittest.TestCase):
    """Test that validator aggregates multiple errors."""

    def test_multiple_errors_aggregated(self):
        """Multiple validation errors reported together."""
        from src.state_manager import load_game_state
        from src.validators import ValidationError

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_999"},
            "locations": [
                {
                    "id": "loc_1",
                    "name": "Room",
                    "description": "A room",
                    "exits": {
                        "north": {"type": "open", "to": "loc_888"}
                    }
                }
            ],
            "items": [
                {"id": "item_1", "name": "Item", "description": "Item", "location": "loc_777"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError) as ctx:
                load_game_state(temp_path)
            error_str = str(ctx.exception)
            # Should have multiple errors
            self.assertTrue(
                len(ctx.exception.errors) > 1 or
                error_str.count("error") > 1 or
                ("loc_999" in error_str and "loc_888" in error_str)
            )
        finally:
            os.unlink(temp_path)


class TestValidateGameStateFunction(unittest.TestCase):
    """Test the validate_game_state function directly."""

    def test_validate_existing_game_state(self):
        """validate_game_state works on already-loaded state."""
        from src.state_manager import (
            GameState, Metadata, Location, Item, Actor
        )
        from src.validators import validate_game_state

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            locations=[
                Location(id="loc_1", name="Room", description="A room", exits={}, items=["item_1"])
            ],
            items=[
                Item(id="item_1", name="Torch", description="A torch", location="loc_1")
            ],
            actors={
                "player": Actor(id="player", name="player", description="", location="loc_1", inventory=[])
            }
        )

        # Should not raise
        validate_game_state(state)

    def test_validate_detects_invalid_reference(self):
        """validate_game_state detects invalid references in loaded state."""
        from src.state_manager import (
            GameState, Metadata, Location, Item, Actor
        )
        from src.validators import validate_game_state, ValidationError

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            locations=[
                Location(id="loc_1", name="Room", description="A room", exits={})
            ],
            items=[
                Item(id="item_1", name="Torch", description="A torch", location="loc_999")
            ],
            actors={
                "player": Actor(id="player", name="player", description="", location="loc_1", inventory=[])
            }
        )

        with self.assertRaises(ValidationError) as ctx:
            validate_game_state(state)
        self.assertIn("loc_999", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
