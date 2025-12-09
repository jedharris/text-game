"""
Tests for handler utility functions.

Tests the validate_actor_and_location() utility that provides
standard preamble for all handlers.
"""

import unittest
from tests.conftest import BaseTestCase
from src.state_manager import Actor
from src.word_entry import WordEntry, WordType
from utilities.handler_utils import validate_actor_and_location


def make_word(word: str) -> WordEntry:
    """Helper to create WordEntry for tests."""
    return WordEntry(word=word, synonyms=[], word_type=WordType.NOUN)


class TestValidateActorAndLocation(BaseTestCase):
    """Tests for validate_actor_and_location utility function."""

    def test_valid_action_with_object(self):
        """Should return actor, location, no error for valid action"""
        action = {"actor_id": "player", "verb": "take", "object": make_word("sword")}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action, require_object=True
        )

        self.assertIsNone(error)
        self.assertEqual(actor_id, "player")
        self.assertIsNotNone(actor)
        self.assertEqual(actor.id, "player")
        self.assertIsNotNone(location)

    def test_missing_object_when_required(self):
        """Should return error when object is required but missing"""
        action = {"actor_id": "player", "verb": "take"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action, require_object=True
        )

        self.assertIsNone(actor_id)
        self.assertIsNone(actor)
        self.assertIsNone(location)
        self.assertIsNotNone(error)
        self.assertFalse(error.success)
        self.assertIn("What do you want to", error.message)

    def test_missing_actor_id_defaults_to_player(self):
        """Should default to 'player' when actor_id not in action"""
        action = {"verb": "take", "object": "sword"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action, require_object=True
        )

        self.assertIsNone(error)
        self.assertEqual(actor_id, "player")
        self.assertIsNotNone(actor)
        self.assertEqual(actor.id, "player")

    def test_nonexistent_actor(self):
        """Should return INCONSISTENT STATE error for missing actor"""
        action = {"actor_id": "ghost", "verb": "take", "object": "sword"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action, require_object=True
        )

        self.assertIsNone(actor_id)
        self.assertIsNone(actor)
        self.assertIsNone(location)
        self.assertIsNotNone(error)
        self.assertIn("INCONSISTENT STATE", error.message)
        self.assertIn("Actor ghost not found", error.message)

    def test_actor_without_location(self):
        """Should return INCONSISTENT STATE error when location not found"""
        # Create actor with invalid location
        self.state.actors["orphan"] = Actor(
            id="orphan", name="Orphan", description="Lost",
            location="nowhere", inventory=[]
        )

        action = {"actor_id": "orphan", "verb": "take", "object": "sword"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action, require_object=True
        )

        self.assertIsNone(actor_id)
        self.assertIsNone(actor)
        self.assertIsNone(location)
        self.assertIsNotNone(error)
        self.assertIn("INCONSISTENT STATE", error.message)
        self.assertIn("Cannot find location", error.message)

    def test_require_direction_present(self):
        """Should validate direction field when required"""
        action = {"actor_id": "player", "verb": "go", "direction": "north"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action, require_direction=True, require_object=False
        )

        self.assertIsNone(error)
        self.assertEqual(actor_id, "player")
        self.assertIsNotNone(actor)
        self.assertIsNotNone(location)

    def test_require_direction_missing(self):
        """Should return error when direction required but missing"""
        action = {"actor_id": "player", "verb": "go"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action, require_direction=True, require_object=False
        )

        self.assertIsNone(actor_id)
        self.assertIsNone(actor)
        self.assertIsNone(location)
        self.assertIsNotNone(error)
        self.assertIn("Which direction", error.message)

    def test_require_indirect_object_present(self):
        """Should validate indirect_object field when required"""
        action = {
            "actor_id": "player",
            "verb": "unlock",
            "object": "door",
            "indirect_object": "key"
        }
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action,
            require_object=True,
            require_indirect_object=True
        )

        self.assertIsNone(error)
        self.assertEqual(actor_id, "player")
        self.assertIsNotNone(actor)
        self.assertIsNotNone(location)

    def test_require_indirect_object_missing(self):
        """Should return error when indirect_object required but missing"""
        action = {"actor_id": "player", "verb": "unlock", "object": make_word("door")}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action,
            require_object=True,
            require_indirect_object=True
        )

        self.assertIsNone(actor_id)
        self.assertIsNone(actor)
        self.assertIsNone(location)
        self.assertIsNotNone(error)
        self.assertIn("What do you want to", error.message)
        self.assertIn("with", error.message)

    def test_no_requirements(self):
        """Should work with no field requirements (like 'look')"""
        action = {"actor_id": "player", "verb": "look"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action,
            require_object=False,
            require_direction=False
        )

        self.assertIsNone(error)
        self.assertEqual(actor_id, "player")
        self.assertIsNotNone(actor)
        self.assertIsNotNone(location)


if __name__ == '__main__':
    unittest.main()
