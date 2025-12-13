"""Tests for item_use_reactions infrastructure dispatcher."""

import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from examples.big_game.behaviors.infrastructure.dispatcher_utils import clear_handler_cache
from examples.big_game.behaviors.infrastructure.item_use_reactions import on_item_used
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
        self.state = MockState()


class TestItemUseReactionsBasic(unittest.TestCase):
    """Tests for basic item use reaction behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_no_target_no_item_config(self) -> None:
        """No target and no item config returns allow with no message."""
        item = MockEntity("item_rock", {})
        context: dict[str, Any] = {}

        result = on_item_used(item, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.message)

    def test_target_without_properties(self) -> None:
        """Target without properties returns allow with no message."""
        item = MockEntity("item_potion", {})
        context = {"target": "string_target"}

        result = on_item_used(item, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.message)

    def test_target_without_item_use_reactions(self) -> None:
        """Target without item_use_reactions returns allow with no message."""
        item = MockEntity("item_potion", {})
        target = MockEntity("npc_guard", {})
        context = {"target": target}

        result = on_item_used(item, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.message)


class TestItemUseReactionsTargetDataDriven(unittest.TestCase):
    """Tests for data-driven item use reactions on target."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_accepted_item_returns_response(self) -> None:
        """Using accepted item on target returns response."""
        item = MockEntity("item_silvermoss", {})
        target = MockEntity(
            "npc_aldric",
            {
                "item_use_reactions": {
                    "healing": {
                        "accepted_items": ["silvermoss", "healing_potion"],
                        "response": "The medicine takes effect...",
                    }
                }
            },
        )
        context = {"target": target}

        result = on_item_used(item, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(result.message, "The medicine takes effect...")

    def test_item_pattern_matching(self) -> None:
        """Item matching uses substring matching."""
        item = MockEntity("item_red_healing_potion", {})
        target = MockEntity(
            "npc_aldric",
            {
                "item_use_reactions": {
                    "healing": {
                        "accepted_items": ["healing_potion"],
                        "response": "Healed!",
                    }
                }
            },
        )
        context = {"target": target}

        result = on_item_used(item, self.accessor, context)

        self.assertEqual(result.message, "Healed!")

    def test_non_accepted_item_no_response(self) -> None:
        """Non-accepted item returns no message."""
        item = MockEntity("item_rock", {})
        target = MockEntity(
            "npc_aldric",
            {
                "item_use_reactions": {
                    "healing": {
                        "accepted_items": ["silvermoss", "healing_potion"],
                        "response": "The medicine takes effect...",
                    }
                }
            },
        )
        context = {"target": target}

        result = on_item_used(item, self.accessor, context)

        self.assertIsNone(result.message)

    def test_set_flags(self) -> None:
        """Item use reaction sets flags."""
        item = MockEntity("item_silvermoss", {})
        target = MockEntity(
            "npc_aldric",
            {
                "item_use_reactions": {
                    "healing": {
                        "accepted_items": ["silvermoss"],
                        "response": "Healed!",
                        "set_flags": {"aldric_healed": True},
                    }
                }
            },
        )
        context = {"target": target}

        on_item_used(item, self.accessor, context)

        self.assertTrue(self.accessor.state.extra.get("aldric_healed"))

    def test_trust_delta(self) -> None:
        """Item use reaction applies trust delta."""
        item = MockEntity("item_silvermoss", {})
        target = MockEntity(
            "npc_aldric",
            {
                "trust_state": {"current": 0, "floor": -5, "ceiling": 5},
                "item_use_reactions": {
                    "healing": {
                        "accepted_items": ["silvermoss"],
                        "response": "Healed!",
                        "trust_delta": 2,
                    }
                },
            },
        )
        context = {"target": target}

        on_item_used(item, self.accessor, context)

        self.assertEqual(target.properties["trust_state"]["current"], 2)

    def test_state_transition(self) -> None:
        """Item use reaction triggers state transition."""
        item = MockEntity("item_silvermoss", {})
        target = MockEntity(
            "npc_aldric",
            {
                "state_machine": {
                    "initial": "critical",
                    "current": "critical",
                    "states": ["critical", "stabilized"],
                },
                "item_use_reactions": {
                    "healing": {
                        "accepted_items": ["silvermoss"],
                        "response": "Stabilized!",
                        "transition_to": "stabilized",
                    }
                },
            },
        )
        context = {"target": target}

        on_item_used(item, self.accessor, context)

        self.assertEqual(target.properties["state_machine"]["current"], "stabilized")

    def test_requires_flags_met(self) -> None:
        """Reaction fires when requires_flags are met."""
        self.accessor.state.extra["aldric_found"] = True

        item = MockEntity("item_silvermoss", {})
        target = MockEntity(
            "npc_aldric",
            {
                "item_use_reactions": {
                    "healing": {
                        "accepted_items": ["silvermoss"],
                        "requires_flags": {"aldric_found": True},
                        "response": "Healed!",
                    }
                }
            },
        )
        context = {"target": target}

        result = on_item_used(item, self.accessor, context)

        self.assertEqual(result.message, "Healed!")

    def test_requires_flags_not_met(self) -> None:
        """Reaction doesn't fire when requires_flags not met."""
        item = MockEntity("item_silvermoss", {})
        target = MockEntity(
            "npc_aldric",
            {
                "item_use_reactions": {
                    "healing": {
                        "accepted_items": ["silvermoss"],
                        "requires_flags": {"aldric_found": True},
                        "response": "Healed!",
                    }
                }
            },
        )
        context = {"target": target}

        result = on_item_used(item, self.accessor, context)

        self.assertIsNone(result.message)


class TestItemUseReactionsItemSelfReactions(unittest.TestCase):
    """Tests for item self-reactions (item config, not target config)."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_item_self_reaction(self) -> None:
        """Item can have reactions when used on certain targets."""
        item = MockEntity(
            "item_bucket_water",
            {
                "item_use_reactions": {
                    "watering": {
                        "target_types": ["plant", "fire"],
                        "response": "You pour water from the bucket.",
                    }
                }
            },
        )
        target = MockEntity("item_plant_pot", {})
        context = {"target": target}

        result = on_item_used(item, self.accessor, context)

        self.assertEqual(result.message, "You pour water from the bucket.")

    def test_item_self_reaction_wrong_target(self) -> None:
        """Item self-reaction doesn't fire on wrong target type."""
        item = MockEntity(
            "item_bucket_water",
            {
                "item_use_reactions": {
                    "watering": {
                        "target_types": ["plant", "fire"],
                        "response": "You pour water from the bucket.",
                    }
                }
            },
        )
        target = MockEntity("npc_guard", {})
        context = {"target": target}

        result = on_item_used(item, self.accessor, context)

        self.assertIsNone(result.message)


class TestItemUseReactionsHandlerEscapeHatch(unittest.TestCase):
    """Tests for handler escape hatch in item_use_reactions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_target_handler_called(self) -> None:
        """When target has handler, it is called."""
        item = MockEntity("item_silvermoss", {})
        target = MockEntity(
            "npc_aldric",
            {
                "item_use_reactions": {
                    "handler": "behaviors.regions.fungal_depths.aldric_rescue:on_aldric_heal"
                }
            },
        )
        context = {"target": target}

        handler_result = EventResult(allow=True, message="Handler response")
        mock_handler = MagicMock(return_value=handler_result)

        with patch(
            "examples.big_game.behaviors.infrastructure.item_use_reactions.load_handler",
            return_value=mock_handler,
        ):
            result = on_item_used(item, self.accessor, context)

        self.assertEqual(result.message, "Handler response")
        mock_handler.assert_called_once_with(item, self.accessor, context)

    def test_item_handler_called(self) -> None:
        """When item has handler, it is called."""
        item = MockEntity(
            "item_magic_wand",
            {
                "item_use_reactions": {
                    "handler": "behaviors.magic:on_wand_use"
                }
            },
        )
        target = MockEntity("npc_guard", {})
        context = {"target": target}

        handler_result = EventResult(allow=True, message="Magic!")
        mock_handler = MagicMock(return_value=handler_result)

        with patch(
            "examples.big_game.behaviors.infrastructure.item_use_reactions.load_handler",
            return_value=mock_handler,
        ):
            result = on_item_used(item, self.accessor, context)

        self.assertEqual(result.message, "Magic!")

    def test_target_handler_takes_precedence(self) -> None:
        """Target handler is checked before item handler."""
        item = MockEntity(
            "item_silvermoss",
            {
                "item_use_reactions": {
                    "handler": "behaviors.item:on_item_use"
                }
            },
        )
        target = MockEntity(
            "npc_aldric",
            {
                "item_use_reactions": {
                    "handler": "behaviors.target:on_target_use"
                }
            },
        )
        context = {"target": target}

        target_result = EventResult(allow=True, message="Target handler")
        mock_handler = MagicMock(return_value=target_result)

        with patch(
            "examples.big_game.behaviors.infrastructure.item_use_reactions.load_handler",
            return_value=mock_handler,
        ):
            result = on_item_used(item, self.accessor, context)

        self.assertEqual(result.message, "Target handler")

    def test_handler_load_failure_falls_through(self) -> None:
        """When handler fails to load, data-driven processing continues."""
        item = MockEntity("item_silvermoss", {})
        target = MockEntity(
            "npc_aldric",
            {
                "item_use_reactions": {
                    "handler": "invalid.module:nonexistent",
                    "healing": {
                        "accepted_items": ["silvermoss"],
                        "response": "Fallback response.",
                    },
                }
            },
        )
        context = {"target": target}

        result = on_item_used(item, self.accessor, context)

        self.assertEqual(result.message, "Fallback response.")


if __name__ == "__main__":
    unittest.main()
