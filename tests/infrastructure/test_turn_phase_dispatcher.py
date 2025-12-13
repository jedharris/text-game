"""Tests for turn_phase_dispatcher infrastructure dispatcher."""

import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from examples.big_game.behaviors.infrastructure.dispatcher_utils import clear_handler_cache
from examples.big_game.behaviors.infrastructure.turn_phase_dispatcher import on_regional_turn
from src.behavior_manager import EventResult


class MockEntity:
    """Mock entity for testing."""

    def __init__(self, entity_id: str, properties: dict | None = None) -> None:
        self.id = entity_id
        self.properties = properties or {}


class MockLocation:
    """Mock location for testing."""

    def __init__(self, loc_id: str, properties: dict | None = None) -> None:
        self.id = loc_id
        self.properties = properties or {}


class MockState:
    """Mock state for testing."""

    def __init__(self) -> None:
        self.extra: dict = {}
        self.actors: dict = {}
        self.locations: list = []


class MockAccessor:
    """Mock accessor for testing."""

    def __init__(self) -> None:
        self.state = MockState()


class TestTurnPhaseDispatcherBasic(unittest.TestCase):
    """Tests for basic turn phase dispatcher behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_no_player(self) -> None:
        """No player in state returns allow with no message."""
        context: dict[str, Any] = {}

        result = on_regional_turn(None, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.message)

    def test_player_with_no_location(self) -> None:
        """Player with no location returns allow with no message."""
        player = MockEntity("player", {})
        self.accessor.state.actors["player"] = player
        context: dict[str, Any] = {}

        result = on_regional_turn(None, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.message)

    def test_location_not_found(self) -> None:
        """Player location not in locations list returns allow with no message."""
        player = MockEntity("player", {"location": "loc_unknown"})
        self.accessor.state.actors["player"] = player
        self.accessor.state.locations = []
        context: dict[str, Any] = {}

        result = on_regional_turn(None, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.message)

    def test_location_without_turn_phase_effects(self) -> None:
        """Location without turn_phase_effects returns allow with no message."""
        player = MockEntity("player", {"location": "loc_cave"})
        location = MockLocation("loc_cave", {})
        self.accessor.state.actors["player"] = player
        self.accessor.state.locations = [location]
        context: dict[str, Any] = {}

        result = on_regional_turn(None, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.message)


class TestTurnPhaseDispatcherDataDriven(unittest.TestCase):
    """Tests for data-driven turn phase effects."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_location_with_turn_phase_effects(self) -> None:
        """Location with turn_phase_effects config is processed."""
        player = MockEntity("player", {"location": "loc_spore_cave"})
        location = MockLocation(
            "loc_spore_cave",
            {
                "turn_phase_effects": {
                    "spore_damage": 5,
                    "cold_damage": 0,
                }
            },
        )
        self.accessor.state.actors["player"] = player
        self.accessor.state.locations = [location]
        context: dict[str, Any] = {}

        # Currently _process_turn_effects is mostly placeholder
        # This test verifies the dispatcher finds the location and attempts processing
        result = on_regional_turn(None, self.accessor, context)

        self.assertTrue(result.allow)
        # The placeholder doesn't return messages, but dispatcher runs without error

    def test_player_conditions_processed(self) -> None:
        """Player conditions are checked during turn phase."""
        player = MockEntity(
            "player",
            {
                "location": "loc_cave",
                "conditions": [
                    {"type": "drowning", "turns_remaining": 3},
                    {"type": "hypothermia", "severity": 2},
                ],
            },
        )
        location = MockLocation("loc_cave", {})
        self.accessor.state.actors["player"] = player
        self.accessor.state.locations = [location]
        context: dict[str, Any] = {}

        # Currently _process_condition_turn is placeholder
        # This test verifies conditions are iterated without error
        result = on_regional_turn(None, self.accessor, context)

        self.assertTrue(result.allow)

    def test_conditions_non_dict_ignored(self) -> None:
        """Non-dict conditions are ignored."""
        player = MockEntity(
            "player",
            {
                "location": "loc_cave",
                "conditions": ["string_condition", 123, None],
            },
        )
        location = MockLocation("loc_cave", {})
        self.accessor.state.actors["player"] = player
        self.accessor.state.locations = [location]
        context: dict[str, Any] = {}

        # Should not raise
        result = on_regional_turn(None, self.accessor, context)

        self.assertTrue(result.allow)


class TestTurnPhaseDispatcherHandlerEscapeHatch(unittest.TestCase):
    """Tests for handler escape hatch in turn_phase_dispatcher."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_handler_called(self) -> None:
        """When location has handler, it is called."""
        player = MockEntity("player", {"location": "loc_spore_cave"})
        location = MockLocation(
            "loc_spore_cave",
            {
                "turn_phase_effects": {
                    "handler": "behaviors.regions.fungal_depths.spore_zones:on_turn_in_spore_zone"
                }
            },
        )
        self.accessor.state.actors["player"] = player
        self.accessor.state.locations = [location]
        context: dict[str, Any] = {}

        handler_result = EventResult(allow=True, message="Spores swirl around you.")
        mock_handler = MagicMock(return_value=handler_result)

        with patch(
            "examples.big_game.behaviors.infrastructure.turn_phase_dispatcher.load_handler",
            return_value=mock_handler,
        ):
            result = on_regional_turn(None, self.accessor, context)

        self.assertIn("Spores swirl around you.", result.message or "")
        mock_handler.assert_called_once_with(location, self.accessor, context)

    def test_handler_load_failure_falls_through(self) -> None:
        """When handler fails to load, data-driven processing continues."""
        player = MockEntity("player", {"location": "loc_spore_cave"})
        location = MockLocation(
            "loc_spore_cave",
            {
                "turn_phase_effects": {
                    "handler": "invalid.module:nonexistent",
                    "spore_damage": 5,
                }
            },
        )
        self.accessor.state.actors["player"] = player
        self.accessor.state.locations = [location]
        context: dict[str, Any] = {}

        # Should not raise, falls through to data-driven
        result = on_regional_turn(None, self.accessor, context)

        self.assertTrue(result.allow)


class TestTurnPhaseDispatcherMultipleLocations(unittest.TestCase):
    """Tests for location lookup with multiple locations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_correct_location_found(self) -> None:
        """Correct location is found among multiple."""
        player = MockEntity("player", {"location": "loc_target"})
        loc1 = MockLocation("loc_other1", {"turn_phase_effects": {"wrong": True}})
        loc2 = MockLocation(
            "loc_target",
            {
                "turn_phase_effects": {
                    "handler": "behaviors.test:on_turn"
                }
            },
        )
        loc3 = MockLocation("loc_other2", {"turn_phase_effects": {"also_wrong": True}})

        self.accessor.state.actors["player"] = player
        self.accessor.state.locations = [loc1, loc2, loc3]
        context: dict[str, Any] = {}

        handler_result = EventResult(allow=True, message="Correct location!")
        mock_handler = MagicMock(return_value=handler_result)

        with patch(
            "examples.big_game.behaviors.infrastructure.turn_phase_dispatcher.load_handler",
            return_value=mock_handler,
        ):
            result = on_regional_turn(None, self.accessor, context)

        # Verify the handler was called with loc2, not loc1 or loc3
        mock_handler.assert_called_once_with(loc2, self.accessor, context)
        self.assertIn("Correct location!", result.message or "")


if __name__ == "__main__":
    unittest.main()
