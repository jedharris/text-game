"""Tests for unified dialog_topics system via dialog_lib."""

import unittest
from unittest.mock import MagicMock, patch

from behavior_libraries.dialog_lib.handlers import (
    clear_dialog_handler_cache,
    handle_ask,
    handle_talk,
)
from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from src.word_entry import WordEntry, WordType


class MockActor:
    """Mock actor for testing."""

    def __init__(
        self,
        actor_id: str,
        name: str = "Test Actor",
        location: str = "test_room",
        properties: dict | None = None,
        inventory: list | None = None,
    ) -> None:
        self.id = actor_id
        self.name = name
        self.location = location
        self.properties = properties or {}
        self.inventory = inventory or []


class MockGameState:
    """Mock game state for testing."""

    def __init__(self) -> None:
        self.actors: dict = {}
        self.extra: dict = {}


class MockAccessor:
    """Mock accessor for testing."""

    def __init__(self) -> None:
        self.game_state = MockGameState()

    def get_actor(self, actor_id):
        return self.game_state.actors.get(actor_id)


def make_word_entry(word: str) -> WordEntry:
    """Create a WordEntry for testing."""
    return WordEntry(
        word=word,
        word_type=WordType.NOUN,
        synonyms=[],
    )


class TestDialogHandlerEscapeHatch(unittest.TestCase):
    """Tests for handler escape hatch in dialog_topics."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_dialog_handler_cache()
        self.accessor = MockAccessor()

        # Create player and NPC in same location
        self.player = MockActor("player", "Player", "test_room")
        self.npc = MockActor(
            "the_echo",
            "Echo",
            "test_room",
            properties={
                "dialog_topics": {
                    "handler": "examples.big_game.behaviors.regions.meridian_nexus.echo:on_echo_dialog"
                }
            },
        )
        self.accessor.game_state.actors["player"] = self.player
        self.accessor.game_state.actors["the_echo"] = self.npc

    def test_ask_calls_handler(self) -> None:
        """When handler is specified, ask command calls it."""
        handler_result = EventResult(allow=True, feedback="Handler response")
        mock_handler = MagicMock(return_value=handler_result)

        with patch(
            "behavior_libraries.dialog_lib.handlers._load_handler",
            return_value=mock_handler,
        ):
            action = {
                "verb": "ask",
                "object": make_word_entry("echo"),
                "indirect_object": make_word_entry("waystone"),
            }
            result = handle_ask(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(result.primary, "Handler response")
        mock_handler.assert_called_once()

        # Check context passed to handler
        call_args = mock_handler.call_args
        context = call_args[0][2]
        self.assertEqual(context["keyword"], "waystone")

    def test_talk_calls_handler(self) -> None:
        """When handler is specified, talk command calls it."""
        handler_result = EventResult(allow=True, feedback="Hello there!")
        mock_handler = MagicMock(return_value=handler_result)

        with patch(
            "behavior_libraries.dialog_lib.handlers._load_handler",
            return_value=mock_handler,
        ):
            action = {
                "verb": "talk",
                "indirect_object": make_word_entry("echo"),
            }
            result = handle_talk(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(result.primary, "Hello there!")
        mock_handler.assert_called_once()

        # Check context passed to handler - empty keyword for talk
        call_args = mock_handler.call_args
        context = call_args[0][2]
        self.assertEqual(context["keyword"], "")

    def test_handler_returns_none_feedback(self) -> None:
        """When handler returns None feedback, default message is used."""
        handler_result = EventResult(allow=True, feedback=None)
        mock_handler = MagicMock(return_value=handler_result)

        with patch(
            "behavior_libraries.dialog_lib.handlers._load_handler",
            return_value=mock_handler,
        ):
            action = {
                "verb": "ask",
                "object": make_word_entry("echo"),
                "indirect_object": make_word_entry("nothing"),
            }
            result = handle_ask(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("nothing to say", result.primary)


class TestDialogDataDriven(unittest.TestCase):
    """Tests for data-driven dialog_topics."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_dialog_handler_cache()
        self.accessor = MockAccessor()

        # Create player and NPC with data-driven topics
        self.player = MockActor(
            "player", "Player", "test_room", properties={"flags": {}}
        )
        self.npc = MockActor(
            "scholar",
            "The Scholar",
            "test_room",
            properties={
                "dialog_topics": {
                    "infection": {
                        "keywords": ["infection", "sick", "illness"],
                        "summary": "'The infection spreads from the caves...'",
                    },
                    "cure": {
                        "keywords": ["cure", "remedy"],
                        "summary": "'You'll need the moonflower.'",
                        "requires_flags": {"knows_about_infection": True},
                    },
                },
                "default_topic_summary": "The scholar shakes their head.",
            },
        )
        self.accessor.game_state.actors["player"] = self.player
        self.accessor.game_state.actors["scholar"] = self.npc

    def test_ask_matches_keyword(self) -> None:
        """Ask command matches keyword and returns summary."""
        action = {
            "verb": "ask",
            "object": make_word_entry("scholar"),
            "indirect_object": make_word_entry("infection"),
        }
        result = handle_ask(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("caves", result.primary)

    def test_ask_unknown_topic(self) -> None:
        """Ask about unknown topic returns default response."""
        action = {
            "verb": "ask",
            "object": make_word_entry("scholar"),
            "indirect_object": make_word_entry("weather"),
        }
        result = handle_ask(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("shakes", result.primary)

    def test_talk_lists_topics(self) -> None:
        """Talk command lists available topic hints."""
        action = {
            "verb": "talk",
            "indirect_object": make_word_entry("scholar"),
        }
        result = handle_talk(self.accessor, action)

        self.assertTrue(result.success)
        # Should mention infection (first keyword), not cure (requires flag)
        self.assertIn("infection", result.primary)


class TestDialogNoTopics(unittest.TestCase):
    """Tests for NPCs without dialog_topics."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_dialog_handler_cache()
        self.accessor = MockAccessor()

        self.player = MockActor("player", "Player", "test_room")
        self.npc = MockActor("guard", "Guard", "test_room", properties={})
        self.accessor.game_state.actors["player"] = self.player
        self.accessor.game_state.actors["guard"] = self.npc

    def test_ask_npc_without_topics(self) -> None:
        """Ask NPC without dialog_topics returns not interested."""
        action = {
            "verb": "ask",
            "object": make_word_entry("guard"),
            "indirect_object": make_word_entry("anything"),
        }
        result = handle_ask(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("interested in conversation", result.primary)

    def test_talk_npc_without_topics(self) -> None:
        """Talk to NPC without dialog_topics returns not interested."""
        action = {
            "verb": "talk",
            "indirect_object": make_word_entry("guard"),
        }
        result = handle_talk(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("interested in conversation", result.primary)

    def test_talk_npc_without_topics_includes_entity_context(self) -> None:
        """Talk failure still includes NPC data for narrator context."""
        action = {
            "verb": "talk",
            "indirect_object": make_word_entry("guard"),
        }
        result = handle_talk(self.accessor, action)

        self.assertFalse(result.success)
        # Even failures should include entity data so narrator doesn't hallucinate
        self.assertIsNotNone(result.data)
        assert result.data is not None
        self.assertEqual(result.data["id"], "guard")
        self.assertEqual(result.data["name"], "Guard")

    def test_ask_npc_without_topics_includes_entity_context(self) -> None:
        """Ask failure still includes NPC data for narrator context."""
        action = {
            "verb": "ask",
            "object": make_word_entry("guard"),
            "indirect_object": make_word_entry("weather"),
        }
        result = handle_ask(self.accessor, action)

        self.assertFalse(result.success)
        # Even failures should include entity data so narrator doesn't hallucinate
        self.assertIsNotNone(result.data)
        assert result.data is not None
        self.assertEqual(result.data["id"], "guard")
        self.assertEqual(result.data["name"], "Guard")


class TestDialogNpcNotFound(unittest.TestCase):
    """Tests for NPC not in location."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_dialog_handler_cache()
        self.accessor = MockAccessor()

        self.player = MockActor("player", "Player", "test_room")
        self.npc = MockActor("scholar", "Scholar", "other_room")  # Different location
        self.accessor.game_state.actors["player"] = self.player
        self.accessor.game_state.actors["scholar"] = self.npc

    def test_ask_npc_not_here(self) -> None:
        """Ask NPC in different location returns not found."""
        action = {
            "verb": "ask",
            "object": make_word_entry("scholar"),
            "indirect_object": make_word_entry("anything"),
        }
        result = handle_ask(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.primary)


class TestDialogSingleNpcDefault(unittest.TestCase):
    """Tests for defaulting to single NPC in location."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_dialog_handler_cache()
        self.accessor = MockAccessor()

        # Create player and single NPC with dialog topics
        self.player = MockActor(
            "player", "Player", "test_room", properties={"flags": {}}
        )
        self.npc = MockActor(
            "scholar",
            "The Scholar",
            "test_room",
            properties={
                "dialog_topics": {
                    "infection": {
                        "keywords": ["infection"],
                        "summary": "'The infection spreads.'",
                    },
                },
            },
        )
        self.accessor.game_state.actors["player"] = self.player
        self.accessor.game_state.actors["scholar"] = self.npc

    def test_talk_without_npc_uses_single_npc(self) -> None:
        """'talk' without NPC name targets the only NPC in location."""
        action = {
            "verb": "talk",
            # No object or indirect_object - just "talk"
        }
        result = handle_talk(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("Scholar", result.primary)

    def test_ask_about_without_npc_uses_single_npc(self) -> None:
        """'ask about X' without NPC name targets the only NPC in location."""
        action = {
            "verb": "ask",
            "object": make_word_entry("infection"),
            # No indirect_object - simulates "ask about infection"
        }
        result = handle_ask(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("infection spreads", result.primary.lower())

    def test_talk_without_npc_fails_when_multiple_npcs(self) -> None:
        """'talk' without NPC name fails when multiple NPCs present."""
        # Add a second NPC
        self.accessor.game_state.actors["guard"] = MockActor(
            "guard",
            "Guard",
            "test_room",
            properties={
                "dialog_topics": {
                    "patrol": {"keywords": ["patrol"], "summary": "I patrol."},
                },
            },
        )

        action = {"verb": "talk"}
        result = handle_talk(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("whom", result.primary.lower())


class TestDialogHandlerResultData(unittest.TestCase):
    """Tests that dialog handlers include NPC entity data for narration context."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_dialog_handler_cache()
        self.accessor = MockAccessor()

        # Create player and NPC with dialog topics
        self.player = MockActor(
            "player", "Player", "test_room", properties={"flags": {}}
        )
        self.npc = MockActor(
            "scholar",
            "The Scholar",
            "test_room",
            properties={
                "dialog_topics": {
                    "infection": {
                        "keywords": ["infection"],
                        "summary": "'The infection spreads.'",
                    },
                },
            },
        )
        self.accessor.game_state.actors["player"] = self.player
        self.accessor.game_state.actors["scholar"] = self.npc

    def test_ask_includes_npc_data(self) -> None:
        """Ask command result includes NPC entity data for narrator context."""
        action = {
            "verb": "ask",
            "object": make_word_entry("scholar"),
            "indirect_object": make_word_entry("infection"),
        }
        result = handle_ask(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        assert result.data is not None
        self.assertEqual(result.data["id"], "scholar")
        self.assertEqual(result.data["name"], "The Scholar")
        self.assertEqual(result.data["type"], "actor")

    def test_talk_includes_npc_data(self) -> None:
        """Talk command result includes NPC entity data for narrator context."""
        action = {
            "verb": "talk",
            "indirect_object": make_word_entry("scholar"),
        }
        result = handle_talk(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        assert result.data is not None
        self.assertEqual(result.data["id"], "scholar")
        self.assertEqual(result.data["name"], "The Scholar")
        self.assertEqual(result.data["type"], "actor")

    def test_ask_with_handler_includes_npc_data(self) -> None:
        """Ask with escape hatch handler still includes NPC data."""
        # Set up NPC with handler
        self.npc.properties["dialog_topics"]["handler"] = "some.module:handler"
        handler_result = EventResult(allow=True, feedback="Custom response")
        mock_handler = MagicMock(return_value=handler_result)

        with patch(
            "behavior_libraries.dialog_lib.handlers._load_handler",
            return_value=mock_handler,
        ):
            action = {
                "verb": "ask",
                "object": make_word_entry("scholar"),
                "indirect_object": make_word_entry("anything"),
            }
            result = handle_ask(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        assert result.data is not None
        self.assertEqual(result.data["id"], "scholar")

    def test_talk_includes_available_topics(self) -> None:
        """Talk command result includes available_topics for narrator."""
        action = {
            "verb": "talk",
            "indirect_object": make_word_entry("scholar"),
        }
        result = handle_talk(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        assert result.data is not None
        self.assertIn("available_topics", result.data)
        # The topic's first keyword should be in available_topics
        self.assertIn("infection", result.data["available_topics"])

    def test_ask_includes_available_topics(self) -> None:
        """Ask command result includes available_topics for narrator."""
        action = {
            "verb": "ask",
            "object": make_word_entry("scholar"),
            "indirect_object": make_word_entry("infection"),
        }
        result = handle_ask(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        assert result.data is not None
        self.assertIn("available_topics", result.data)


if __name__ == "__main__":
    unittest.main()
