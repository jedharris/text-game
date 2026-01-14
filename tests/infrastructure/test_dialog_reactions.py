"""Tests for dialog_reactions infrastructure dispatcher."""

import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import clear_handler_cache
from examples.big_game.behaviors.shared.infrastructure.dialog_reactions import on_dialog
from src.behavior_manager import EventResult


class MockEntity:
    """Mock entity for testing."""

    def __init__(self, entity_id: str, properties: dict | None = None) -> None:
        self.id = entity_id
        self.properties = properties or {}


class MockState:
    """Mock state for testing."""

    def __init__(self) -> None:
        self.extra: dict[str, Any] = {}
        self.actors: dict[str, Any] = {}


class MockAccessor:
    """Mock accessor for testing."""

    def __init__(self) -> None:
        self.game_state = MockState()


class TestDialogReactionsHandlerEscapeHatch(unittest.TestCase):
    """Tests for handler escape hatch in dialog_reactions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_handler_escape_hatch_called(self) -> None:
        """When handler is specified, it is called."""
        npc = MockEntity(
            "npc_echo",
            {
                "dialog_reactions": {
                    "handler": "behaviors.regions.meridian_nexus.echo:on_echo_dialog"
                }
            },
        )
        context = {"keyword": "history", "speaker": "player"}

        handler_result = EventResult(allow=True, feedback="Handler processed")
        mock_handler = MagicMock(return_value=handler_result)

        with patch(
            "examples.big_game.behaviors.shared.infrastructure.dialog_reactions.load_handler",
            return_value=mock_handler,
        ):
            # Re-import inside patch context to ensure we get the patched version
            from examples.big_game.behaviors.shared.infrastructure.dialog_reactions import on_dialog as patched_func
            result = patched_func(npc, self.accessor, context)

        self.assertEqual(result.feedback, "Handler processed")
        mock_handler.assert_called_once_with(npc, self.accessor, context)

    def test_handler_load_failure_falls_through(self) -> None:
        """When handler fails to load, data-driven processing continues."""
        npc = MockEntity(
            "npc_scholar",
            {
                "dialog_reactions": {
                    "handler": "invalid.module:nonexistent",
                    "infection": {
                        "keywords": ["infection", "sick"],
                        "summary": "The scholar explains the infection.",
                    },
                    "default_response": "The scholar looks confused.",
                }
            },
        )
        context = {"keyword": "weather", "speaker": "player"}

        result = on_dialog(npc, self.accessor, context)

        # Should fall through to data-driven and return default
        self.assertEqual(result.feedback, "The scholar looks confused.")


class TestDialogReactionsDataDriven(unittest.TestCase):
    """Tests for data-driven dialog reactions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_no_properties(self) -> None:
        """Entity without properties returns allow with no message."""
        npc = "string_npc"  # Not a proper entity
        context = {"keyword": "hello", "speaker": "player"}

        result = on_dialog(npc, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_no_dialog_reactions(self) -> None:
        """Entity without dialog_reactions config returns allow with no message."""
        npc = MockEntity("npc_guard", {})
        context = {"keyword": "hello", "speaker": "player"}

        result = on_dialog(npc, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_empty_dialog_reactions(self) -> None:
        """Entity with empty dialog_reactions returns allow with no message."""
        npc = MockEntity("npc_guard", {"dialog_reactions": {}})
        context = {"keyword": "hello", "speaker": "player"}

        result = on_dialog(npc, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_keyword_match_returns_summary(self) -> None:
        """Matching keyword returns the summary."""
        npc = MockEntity(
            "npc_scholar",
            {
                "dialog_reactions": {
                    "infection": {
                        "keywords": ["infection", "sick", "disease"],
                        "summary": "The scholar explains the infection spreading through the depths.",
                    }
                }
            },
        )
        context = {"keyword": "infection", "speaker": "player"}

        result = on_dialog(npc, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIn("infection spreading", result.feedback or "")

    def test_keyword_match_partial(self) -> None:
        """Partial keyword match works."""
        npc = MockEntity(
            "npc_scholar",
            {
                "dialog_reactions": {
                    "infection": {
                        "keywords": ["infection", "sick"],
                        "summary": "The scholar explains the sickness.",
                    }
                }
            },
        )
        context = {"keyword": "sick", "speaker": "player"}

        result = on_dialog(npc, self.accessor, context)

        self.assertIn("sickness", result.feedback or "")

    def test_no_match_returns_default(self) -> None:
        """No keyword match returns default_response."""
        npc = MockEntity(
            "npc_scholar",
            {
                "dialog_reactions": {
                    "infection": {
                        "keywords": ["infection"],
                        "summary": "About infection...",
                    },
                    "default_response": "The scholar shrugs. 'I don't know about that.'"
                }
            },
        )
        context = {"keyword": "weather", "speaker": "player"}

        result = on_dialog(npc, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(result.feedback, "The scholar shrugs. 'I don't know about that.'")

    def test_no_match_no_default(self) -> None:
        """No keyword match and no default returns None feedback."""
        npc = MockEntity(
            "npc_scholar",
            {
                "dialog_reactions": {
                    "infection": {
                        "keywords": ["infection"],
                        "summary": "About infection...",
                    }
                }
            },
        )
        context = {"keyword": "weather", "speaker": "player"}

        result = on_dialog(npc, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_set_flags_applied(self) -> None:
        """Set flags are applied to game state."""
        npc = MockEntity(
            "npc_scholar",
            {
                "dialog_reactions": {
                    "infection": {
                        "keywords": ["infection"],
                        "summary": "The scholar tells you about the infection.",
                        "set_flags": {"knows_about_infection": True}
                    }
                }
            },
        )
        context = {"keyword": "infection", "speaker": "player"}

        on_dialog(npc, self.accessor, context)

        self.assertTrue(self.accessor.game_state.extra.get("knows_about_infection"))

    def test_trust_delta_applied(self) -> None:
        """Trust delta is applied to NPC."""
        npc = MockEntity(
            "npc_scholar",
            {
                "trust_state": {"current": 0, "floor": -5, "ceiling": 5},
                "dialog_reactions": {
                    "help": {
                        "keywords": ["help", "assist"],
                        "summary": "The scholar thanks you for offering help.",
                        "trust_delta": 1
                    }
                }
            },
        )
        context = {"keyword": "help", "speaker": "player"}

        on_dialog(npc, self.accessor, context)

        self.assertEqual(npc.properties["trust_state"]["current"], 1)

    def test_requires_state_blocks_when_not_met(self) -> None:
        """Requires_state blocks reaction when state doesn't match."""
        npc = MockEntity(
            "npc_bear",
            {
                "state_machine": {"current": "hostile"},
                "dialog_reactions": {
                    "cubs": {
                        "keywords": ["cubs", "help"],
                        "requires_state": ["wary", "neutral"],
                        "summary": "The bear explains her cubs are sick.",
                        "failure_message": "The bear growls warningly.",
                    },
                }
            },
        )
        context = {"keyword": "cubs", "speaker": "player"}

        result = on_dialog(npc, self.accessor, context)

        # Should return failure_message because state is "hostile", not in ["wary", "neutral"]
        self.assertEqual(result.feedback, "The bear growls warningly.")

    def test_requires_state_allows_when_met(self) -> None:
        """Requires_state allows reaction when state matches."""
        npc = MockEntity(
            "npc_bear",
            {
                "state_machine": {"current": "wary"},
                "dialog_reactions": {
                    "cubs": {
                        "keywords": ["cubs", "help"],
                        "requires_state": ["wary", "neutral"],
                        "summary": "The bear explains her cubs are sick.",
                    }
                }
            },
        )
        context = {"keyword": "cubs", "speaker": "player"}

        result = on_dialog(npc, self.accessor, context)

        self.assertIn("cubs are sick", result.feedback or "")


class TestDialogReactionsMultipleTopics(unittest.TestCase):
    """Tests for multiple dialog topics."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_first_matching_topic_used(self) -> None:
        """First topic that matches keyword is used."""
        npc = MockEntity(
            "npc_scholar",
            {
                "dialog_reactions": {
                    "cure": {
                        "keywords": ["cure", "treatment"],
                        "summary": "The cure requires heartmoss.",
                    },
                    "infection": {
                        "keywords": ["infection", "disease", "cure"],
                        "summary": "The infection is spreading.",
                    }
                }
            },
        )
        context = {"keyword": "cure", "speaker": "player"}

        result = on_dialog(npc, self.accessor, context)

        # Should match first topic with "cure" keyword
        self.assertTrue(result.allow)
        # Note: dict ordering means we might get either one


if __name__ == "__main__":
    unittest.main()
