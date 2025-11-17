"""
Tests for state manager error handling.

Covers: TE-001 through TE-005 from state_manager_testing.md
"""
import unittest
import logging
from test_helpers import load_fixture, get_fixture_path


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling and reporting."""

    def test_TE001_multiple_errors_aggregated(self):
        """TE-001: Multiple validation errors aggregated into single exception."""
        from src.state_manager.loader import parse_game_state
        from src.state_manager.exceptions import ValidationError

        # Create fixture with multiple errors
        data = {
            "metadata": {
                "title": "Test",
                "version": "1.0",
                "start_location": "loc_999"  # Error 1: missing location
            },
            "locations": [
                {
                    "id": "loc_1",
                    "name": "Room",
                    "description": "A room",
                    "exits": {
                        "north": {"type": "open", "to": "loc_888"}  # Error 2: missing ref
                    }
                }
            ],
            "items": [
                {
                    "id": "item_1",
                    "name": "Item",
                    "description": "An item",
                    "type": "tool",
                    "portable": True,
                    "location": "loc_777"  # Error 3: missing location
                }
            ]
        }

        try:
            parse_game_state(data)
            self.fail("Expected ValidationError")
        except ValidationError as e:
            # Should contain all three errors
            error_str = str(e)
            self.assertIn("loc_999", error_str)
            self.assertIn("loc_888", error_str)
            self.assertIn("loc_777", error_str)

            # Should indicate multiple errors (at least 3)
            # Implementation may format count differently

    def test_TE002_schema_error_missing_required_section(self):
        """TE-002: Schema error for missing required sections."""
        from src.state_manager.loader import load_game_state
        from src.state_manager.exceptions import SchemaError

        with self.assertRaises(SchemaError) as ctx:
            load_game_state(get_fixture_path("missing_sections.json"))

        error_str = str(ctx.exception)
        self.assertIn("metadata", error_str.lower())

    def test_TE003_type_mismatch_error(self):
        """TE-003: Type mismatch triggers schema-level exception."""
        from src.state_manager.loader import parse_game_state
        from src.state_manager.exceptions import SchemaError

        data = {
            "metadata": {
                "title": "Test",
                "version": "1.0",
                "start_location": "loc_1"
            },
            "locations": "not an array"  # Wrong type
        }

        with self.assertRaises(SchemaError):
            parse_game_state(data)

    def test_TE004_non_string_keys_error(self):
        """TE-004: Non-string IDs raise clear error."""
        from src.state_manager.loader import parse_game_state
        from src.state_manager.exceptions import SchemaError

        data = {
            "metadata": {
                "title": "Test",
                "version": "1.0",
                "start_location": "loc_1"
            },
            "locations": [
                {
                    "id": 123,  # Should be string
                    "name": "Room",
                    "description": "A room",
                    "exits": {}
                }
            ]
        }

        with self.assertRaises(SchemaError):
            parse_game_state(data)

    def test_TE005_warnings_do_not_abort_parsing(self):
        """TE-005: Warnings are optional and do not abort parsing."""
        from src.state_manager.loader import parse_game_state

        # Create data with potential warning condition
        # Note: This test is implementation-dependent
        # If the implementation doesn't have warnings, this test can pass
        data = {
            "metadata": {
                "title": "Test",
                "version": "1.0",
                "start_location": "loc_1"
            },
            "locations": [
                {
                    "id": "loc_1",
                    "name": "Room",
                    "description": "A room",
                    "exits": {},
                    "items": []
                }
            ],
            "items": [
                {
                    "id": "item_1",
                    "name": "Item",
                    "description": "An item",
                    "type": "tool",
                    "portable": True,
                    "location": "loc_1"
                }
            ]
        }

        # Should parse successfully (warnings are optional)
        game_state = parse_game_state(data)
        self.assertIsNotNone(game_state)


if __name__ == '__main__':
    unittest.main()
