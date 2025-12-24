"""Tests for gift_reactions infrastructure dispatcher."""

import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import clear_handler_cache
from examples.big_game.behaviors.shared.infrastructure.gift_reactions import on_gift_given
from src.behavior_manager import EventResult


class MockEntity:
    """Mock entity for testing."""

    def __init__(self, entity_id: str, properties: dict | None = None) -> None:
        self.id = entity_id
        self.properties = properties or {}


class MockState:
    """Mock state for testing."""

    def __init__(self) -> None:
        self.extra: dict = {}
        self.actors: dict = {}


class MockAccessor:
    """Mock accessor for testing."""

    def __init__(self) -> None:
        self.game_state = MockState()


class TestGiftReactionsHandlerEscapeHatch(unittest.TestCase):
    """Tests for handler escape hatch in gift_reactions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_handler_escape_hatch_called(self) -> None:
        """When handler is specified, it is called."""
        target = MockEntity(
            "npc_bee_queen",
            {
                "gift_reactions": {
                    "handler": "examples.big_game.behaviors.regions.beast_wilds.bee_queen:on_flower_offer"
                }
            },
        )
        item = MockEntity("item_moonpetal")
        context = {"target_actor": target, "item": item}

        handler_result = EventResult(allow=True, feedback="Handler processed")
        mock_handler = MagicMock(return_value=handler_result)

        with patch(
            "examples.big_game.behaviors.shared.infrastructure.gift_reactions.load_handler",
            return_value=mock_handler,
        ):
            result = on_gift_given(item, self.accessor, context)

        self.assertEqual(result.feedback, "Handler processed")
        mock_handler.assert_called_once()

    def test_handler_load_failure_falls_through(self) -> None:
        """When handler fails to load, data-driven processing continues."""
        target = MockEntity(
            "npc_wolf",
            {
                "gift_reactions": {
                    "handler": "invalid.module:nonexistent",
                    "food": {
                        "accepted_items": ["venison", "meat"],
                        "accept_message": "The wolf accepts the {item}.",
                    },
                }
            },
        )
        item = MockEntity("item_venison")
        context = {"target_actor": target, "item": item}

        result = on_gift_given(item, self.accessor, context)

        # Should fall through to data-driven and process the gift
        self.assertIn("venison", (result.feedback or "").lower())


class TestGiftReactionsDataDriven(unittest.TestCase):
    """Tests for data-driven gift reactions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_no_target_actor(self) -> None:
        """No target_actor returns allow with no message."""
        item = MockEntity("item_flower")
        context: dict[str, Any] = {}

        result = on_gift_given(item, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_target_without_properties(self) -> None:
        """Target without properties returns allow with no message."""
        target = "string_target"  # Not a proper entity
        item = MockEntity("item_flower")
        context = {"target_actor": target}

        result = on_gift_given(item, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_target_without_gift_reactions(self) -> None:
        """Target without gift_reactions config returns allow with no message."""
        target = MockEntity("npc_guard", {})
        item = MockEntity("item_flower")
        context = {"target_actor": target, "item": item}

        result = on_gift_given(item, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_accepted_item_returns_message(self) -> None:
        """Accepted item triggers accept_message."""
        target = MockEntity(
            "npc_wolf",
            {
                "gift_reactions": {
                    "food": {
                        "accepted_items": ["venison", "meat", "rabbit"],
                        "accept_message": "The wolf accepts the {item}.",
                    }
                }
            },
        )
        item = MockEntity("item_venison")
        context = {"target_actor": target, "item": item}

        result = on_gift_given(item, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIn("wolf accepts", (result.feedback or "").lower())

    def test_rejected_item_returns_reject_message(self) -> None:
        """Rejected item triggers reject_message."""
        target = MockEntity(
            "npc_wolf",
            {
                "gift_reactions": {
                    "food": {
                        "accepted_items": ["venison", "meat"],
                        "accept_message": "Accepted!",
                    },
                    "reject_message": "The wolf ignores the offering.",
                }
            },
        )
        item = MockEntity("item_rock")
        context = {"target_actor": target, "item": item}

        result = on_gift_given(item, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(result.feedback, "The wolf ignores the offering.")

    def test_trust_delta_applied(self) -> None:
        """Trust delta is applied to target."""
        target = MockEntity(
            "npc_wolf",
            {
                "trust_state": {"current": 0, "floor": -5, "ceiling": 5},
                "gift_reactions": {
                    "food": {
                        "accepted_items": ["venison"],
                        "trust_delta": 2,
                        "accept_message": "Accepted!",
                    }
                },
            },
        )
        item = MockEntity("item_venison")
        context = {"target_actor": target, "item": item}

        on_gift_given(item, self.accessor, context)

        self.assertEqual(target.properties["trust_state"]["current"], 2)

    def test_set_flags_applied(self) -> None:
        """Set flags are applied to game state."""
        target = MockEntity(
            "npc_wolf",
            {
                "gift_reactions": {
                    "food": {
                        "accepted_items": ["venison"],
                        "set_flags": {"wolf_fed": True},
                        "accept_message": "Accepted!",
                    }
                }
            },
        )
        item = MockEntity("item_venison")
        context = {"target_actor": target, "item": item}

        on_gift_given(item, self.accessor, context)

        self.assertTrue(self.accessor.game_state.extra.get("wolf_fed"))

    def test_track_items_key(self) -> None:
        """Track items key appends item to list."""
        target = MockEntity(
            "npc_queen",
            {
                "gift_reactions": {
                    "flowers": {
                        "accepted_items": ["moonpetal", "frost_lily"],
                        "track_items_key": "flowers_given",
                        "accept_message": "Accepted!",
                    }
                }
            },
        )
        item = MockEntity("item_moonpetal")
        context = {"target_actor": target, "item": item}

        on_gift_given(item, self.accessor, context)

        tracked = self.accessor.game_state.extra.get("flowers_given", [])
        self.assertIn("moonpetal", tracked)


if __name__ == "__main__":
    unittest.main()
