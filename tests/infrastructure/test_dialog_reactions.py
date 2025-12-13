"""Tests for dialog_reactions infrastructure dispatcher."""

import unittest
from unittest.mock import MagicMock, patch

from examples.big_game.behaviors.infrastructure.dispatcher_utils import clear_handler_cache
from examples.big_game.behaviors.infrastructure.dialog_reactions import on_dialog_received
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


class TestDialogReactionsBasic(unittest.TestCase):
    """Tests for basic dialog reaction behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_entity_without_properties(self) -> None:
        """Entity without properties returns allow with no message."""
        entity = "string_entity"  # Not a proper entity
        context = {"keyword": "hello"}

        result = on_dialog_received(entity, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.message)

    def test_entity_without_dialog_reactions(self) -> None:
        """Entity without dialog_reactions config returns allow with no message."""
        entity = MockEntity("npc_guard", {})
        context = {"keyword": "hello"}

        result = on_dialog_received(entity, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.message)

    def test_no_matching_trigger(self) -> None:
        """No matching trigger returns allow with no message."""
        entity = MockEntity(
            "npc_scholar",
            {
                "dialog_reactions": {
                    "help_request": {
                        "triggers": ["help", "save"],
                        "response": "I can help you.",
                    }
                }
            },
        )
        context = {"keyword": "weather", "dialog_text": ""}

        result = on_dialog_received(entity, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertIsNone(result.message)


class TestDialogReactionsDataDriven(unittest.TestCase):
    """Tests for data-driven dialog reactions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_trigger_match_returns_response(self) -> None:
        """Matching trigger returns configured response."""
        entity = MockEntity(
            "npc_scholar",
            {
                "dialog_reactions": {
                    "help_request": {
                        "triggers": ["help", "save", "please"],
                        "response": "I can help you find the cure.",
                    }
                }
            },
        )
        context = {"keyword": "help", "dialog_text": ""}

        result = on_dialog_received(entity, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(result.message, "I can help you find the cure.")

    def test_trigger_in_dialog_text(self) -> None:
        """Trigger can match in dialog_text, not just keyword."""
        entity = MockEntity(
            "npc_scholar",
            {
                "dialog_reactions": {
                    "help_request": {
                        "triggers": ["cure"],
                        "response": "The cure is in the cave.",
                    }
                }
            },
        )
        context = {"keyword": "tell", "dialog_text": "me about the cure"}

        result = on_dialog_received(entity, self.accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual(result.message, "The cure is in the cave.")

    def test_set_flags(self) -> None:
        """Dialog reaction sets flags in game state."""
        entity = MockEntity(
            "npc_scholar",
            {
                "dialog_reactions": {
                    "help_request": {
                        "triggers": ["help"],
                        "response": "I'll help.",
                        "set_flags": {"asked_for_help": True, "scholar_met": True},
                    }
                }
            },
        )
        context = {"keyword": "help", "dialog_text": ""}

        on_dialog_received(entity, self.accessor, context)

        self.assertTrue(self.accessor.state.extra.get("asked_for_help"))
        self.assertTrue(self.accessor.state.extra.get("scholar_met"))

    def test_trust_delta(self) -> None:
        """Dialog reaction applies trust delta."""
        entity = MockEntity(
            "npc_scholar",
            {
                "trust_state": {"current": 0, "floor": -5, "ceiling": 5},
                "dialog_reactions": {
                    "compliment": {
                        "triggers": ["wise", "smart"],
                        "response": "Thank you!",
                        "trust_delta": 1,
                    }
                },
            },
        )
        context = {"keyword": "you're wise", "dialog_text": ""}

        on_dialog_received(entity, self.accessor, context)

        self.assertEqual(entity.properties["trust_state"]["current"], 1)

    def test_state_transition(self) -> None:
        """Dialog reaction triggers state transition."""
        entity = MockEntity(
            "npc_scholar",
            {
                "state_machine": {
                    "initial": "neutral",
                    "current": "neutral",
                    "states": ["neutral", "helpful"],
                },
                "dialog_reactions": {
                    "befriend": {
                        "triggers": ["friend"],
                        "response": "We are friends now.",
                        "transition_to": "helpful",
                    }
                },
            },
        )
        context = {"keyword": "be my friend", "dialog_text": ""}

        on_dialog_received(entity, self.accessor, context)

        self.assertEqual(entity.properties["state_machine"]["current"], "helpful")

    def test_requires_state_met(self) -> None:
        """Reaction fires when requires_state is met."""
        entity = MockEntity(
            "npc_aldric",
            {
                "state_machine": {
                    "initial": "critical",
                    "current": "critical",
                    "states": ["critical", "stable"],
                },
                "dialog_reactions": {
                    "plea": {
                        "triggers": ["help"],
                        "requires_state": "critical",
                        "response": "Please... help me...",
                    }
                },
            },
        )
        context = {"keyword": "help", "dialog_text": ""}

        result = on_dialog_received(entity, self.accessor, context)

        self.assertEqual(result.message, "Please... help me...")

    def test_requires_state_not_met(self) -> None:
        """Reaction doesn't fire when requires_state is not met."""
        entity = MockEntity(
            "npc_aldric",
            {
                "state_machine": {
                    "initial": "critical",
                    "current": "stable",
                    "states": ["critical", "stable"],
                },
                "dialog_reactions": {
                    "plea": {
                        "triggers": ["help"],
                        "requires_state": "critical",
                        "response": "Please... help me...",
                    }
                },
            },
        )
        context = {"keyword": "help", "dialog_text": ""}

        result = on_dialog_received(entity, self.accessor, context)

        self.assertIsNone(result.message)

    def test_requires_flags_met(self) -> None:
        """Reaction fires when requires_flags are met."""
        self.accessor.state.extra["knows_secret"] = True

        entity = MockEntity(
            "npc_spy",
            {
                "dialog_reactions": {
                    "secret": {
                        "triggers": ["secret"],
                        "requires_flags": {"knows_secret": True},
                        "response": "The password is 'moonlight'.",
                    }
                }
            },
        )
        context = {"keyword": "secret", "dialog_text": ""}

        result = on_dialog_received(entity, self.accessor, context)

        self.assertEqual(result.message, "The password is 'moonlight'.")

    def test_requires_flags_not_met(self) -> None:
        """Reaction doesn't fire when requires_flags are not met."""
        entity = MockEntity(
            "npc_spy",
            {
                "dialog_reactions": {
                    "secret": {
                        "triggers": ["secret"],
                        "requires_flags": {"knows_secret": True},
                        "response": "The password is 'moonlight'.",
                    }
                }
            },
        )
        context = {"keyword": "secret", "dialog_text": ""}

        result = on_dialog_received(entity, self.accessor, context)

        self.assertIsNone(result.message)

    def test_forbidden_flags_blocks(self) -> None:
        """Reaction doesn't fire when forbidden_flags are set."""
        self.accessor.state.extra["already_told"] = True

        entity = MockEntity(
            "npc_spy",
            {
                "dialog_reactions": {
                    "secret": {
                        "triggers": ["secret"],
                        "forbidden_flags": ["already_told"],
                        "response": "The password is 'moonlight'.",
                    }
                }
            },
        )
        context = {"keyword": "secret", "dialog_text": ""}

        result = on_dialog_received(entity, self.accessor, context)

        self.assertIsNone(result.message)


class TestDialogReactionsHandlerEscapeHatch(unittest.TestCase):
    """Tests for handler escape hatch in dialog_reactions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.accessor = MockAccessor()

    def test_handler_called(self) -> None:
        """When handler is specified, it is called."""
        entity = MockEntity(
            "npc_aldric",
            {
                "dialog_reactions": {
                    "handler": "behaviors.regions.fungal_depths.aldric_rescue:on_aldric_commitment"
                }
            },
        )
        context = {"keyword": "help", "dialog_text": ""}

        handler_result = EventResult(allow=True, message="Handler response")
        mock_handler = MagicMock(return_value=handler_result)

        with patch(
            "examples.big_game.behaviors.infrastructure.dialog_reactions.load_handler",
            return_value=mock_handler,
        ):
            result = on_dialog_received(entity, self.accessor, context)

        self.assertEqual(result.message, "Handler response")
        mock_handler.assert_called_once_with(entity, self.accessor, context)

    def test_handler_load_failure_falls_through(self) -> None:
        """When handler fails to load, data-driven processing continues."""
        entity = MockEntity(
            "npc_aldric",
            {
                "dialog_reactions": {
                    "handler": "invalid.module:nonexistent",
                    "help_request": {
                        "triggers": ["help"],
                        "response": "Fallback response.",
                    },
                }
            },
        )
        context = {"keyword": "help", "dialog_text": ""}

        result = on_dialog_received(entity, self.accessor, context)

        self.assertEqual(result.message, "Fallback response.")


if __name__ == "__main__":
    unittest.main()
