"""
Tests for handler utility functions.

Tests the validate_actor_and_location() utility that provides
standard preamble for all handlers, plus new consolidation helpers.
"""
from src.types import ActorId

import unittest
from unittest.mock import Mock, MagicMock, patch
from tests.conftest import BaseTestCase
from src.state_manager import Actor, Item, Lock
from src.state_accessor import UpdateResult
from src.word_entry import WordEntry, WordType
from utilities.handler_utils import (
    validate_actor_and_location,
    execute_entity_action,
    transfer_item_to_actor,
    transfer_item_from_actor,
    validate_container_accessible,
    check_actor_has_key,
    build_action_result
)


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
        self.assertIn("What do you want to", error.primary)

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
        self.assertIn("INCONSISTENT STATE", error.primary)
        self.assertIn("Actor ghost not found", error.primary)

    def test_actor_without_location(self):
        """Should return INCONSISTENT STATE error when location not found"""
        # Create actor with invalid location
        self.state.actors[ActorId("orphan")] = Actor(
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
        self.assertIn("INCONSISTENT STATE", error.primary)
        self.assertIn("Cannot find location", error.primary)

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
        self.assertIn("Which direction", error.primary)

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
        self.assertIn("What do you want to", error.primary)
        self.assertIn("with", error.primary)

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


class TestExecuteEntityAction(BaseTestCase):
    """Tests for execute_entity_action helper."""

    def test_success_basic(self):
        """Should return success with message and serialized entity"""
        item = self.state.get_item("item_sword")
        result = execute_entity_action(
            self.accessor,
            item,
            {},  # No changes
            "examine",
            "player",
            "You examine the sword."
        )

        self.assertTrue(result.success)
        self.assertIn("examine the sword", result.primary)
        self.assertIsNotNone(result.data)
        self.assertIn("id", result.data)
        self.assertEqual(result.data["id"], "item_sword")

    def test_success_with_behavior_message(self):
        """Should include behavior message in beats"""
        # Mock accessor.update to return a message
        item = self.state.get_item("item_sword")
        original_update = self.accessor.update

        def mock_update(entity, changes, verb=None, actor_id=None):
            return UpdateResult(success=True, detail="The sword glows!")

        self.accessor.update = mock_update
        try:
            result = execute_entity_action(
                self.accessor,
                item,
                {},
                "examine",
                "player",
                "You examine the sword."
            )

            self.assertTrue(result.success)
            self.assertEqual(result.primary, "You examine the sword.")
            self.assertEqual(result.beats, ["The sword glows!"])
        finally:
            self.accessor.update = original_update

    def test_success_with_positioning_message(self):
        """Should include positioning message in beats"""
        item = self.state.get_item("item_sword")
        result = execute_entity_action(
            self.accessor,
            item,
            {},
            "examine",
            "player",
            "You examine the sword.",
            positioning_msg="You move closer."
        )

        self.assertTrue(result.success)
        self.assertEqual(result.primary, "You examine the sword.")
        self.assertIn("You move closer.", result.beats)

    def test_failure_from_behavior(self):
        """Should return failure when behavior denies action"""
        item = self.state.get_item("item_sword")
        original_update = self.accessor.update

        def mock_update(entity, changes, verb=None, actor_id=None):
            return UpdateResult(success=False, detail="The sword resists!")

        self.accessor.update = mock_update
        try:
            result = execute_entity_action(
                self.accessor,
                item,
                {},
                "take",
                "player",
                "You take the sword."
            )

            self.assertFalse(result.success)
            self.assertIn("resists", result.primary)
        finally:
            self.accessor.update = original_update


class TestTransferItemToActor(BaseTestCase):
    """Tests for transfer_item_to_actor helper."""

    def test_success(self):
        """Should transfer item to actor inventory"""
        item = self.state.get_item("item_sword")
        actor = self.state.actors[ActorId("player")]
        location = self.accessor.get_current_location("player")

        result, error = transfer_item_to_actor(
            self.accessor,
            item,
            actor,
            "player",
            "take",
            {"location": "player"},
            location.id
        )

        self.assertIsNone(error)
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(item.location, "player")
        self.assertIn("item_sword", actor.inventory)

    def test_behavior_denies(self):
        """Should return error when behavior denies"""
        item = self.state.get_item("item_sword")
        actor = self.state.actors[ActorId("player")]
        location = self.accessor.get_current_location("player")

        original_update = self.accessor.update

        def mock_update(entity, changes, verb=None, actor_id=None):
            if hasattr(entity, 'location'):  # Item update
                return UpdateResult(success=False, detail="Cannot take that.")
            return original_update(entity, changes, verb, actor_id)

        self.accessor.update = mock_update
        try:
            result, error = transfer_item_to_actor(
                self.accessor,
                item,
                actor,
                "player",
                "take",
                {"location": "player"},
                location.id
            )

            self.assertIsNone(result)
            self.assertIsNotNone(error)
            self.assertFalse(error.success)
            self.assertIn("Cannot take", error.primary)
        finally:
            self.accessor.update = original_update


class TestTransferItemFromActor(BaseTestCase):
    """Tests for transfer_item_from_actor helper."""

    def test_success(self):
        """Should transfer item from actor inventory"""
        # Setup: put sword in inventory
        item = self.state.get_item("item_sword")
        actor = self.state.actors[ActorId("player")]
        location = self.accessor.get_current_location("player")
        actor.inventory.append("item_sword")
        item.location = "player"

        result, error = transfer_item_from_actor(
            self.accessor,
            item,
            actor,
            "player",
            "drop",
            {"location": location.id}
        )

        self.assertIsNone(error)
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(item.location, location.id)
        self.assertNotIn("item_sword", actor.inventory)

    def test_behavior_denies(self):
        """Should return error when behavior denies"""
        item = self.state.get_item("item_sword")
        actor = self.state.actors[ActorId("player")]
        location = self.accessor.get_current_location("player")
        actor.inventory.append("item_sword")
        item.location = "player"

        original_update = self.accessor.update

        def mock_update(entity, changes, verb=None, actor_id=None):
            if hasattr(entity, 'location') and entity.id == "item_sword":
                return UpdateResult(success=False, detail="Cannot drop that.")
            return original_update(entity, changes, verb, actor_id)

        self.accessor.update = mock_update
        try:
            result, error = transfer_item_from_actor(
                self.accessor,
                item,
                actor,
                "player",
                "drop",
                {"location": location.id}
            )

            self.assertIsNone(result)
            self.assertIsNotNone(error)
            self.assertFalse(error.success)
            self.assertIn("Cannot drop", error.primary)
        finally:
            self.accessor.update = original_update


class TestValidateContainerAccessible(BaseTestCase):
    """Tests for validate_container_accessible helper."""

    def test_open_container_accessible(self):
        """Should return None for open container"""
        item = Mock()
        item.name = "chest"
        item.properties = {"container": {"open": True}}

        result = validate_container_accessible(item, "take from")
        self.assertIsNone(result)

    def test_surface_always_accessible(self):
        """Should return None for surfaces regardless of open state"""
        item = Mock()
        item.name = "table"
        item.properties = {"container": {"is_surface": True, "open": False}}

        result = validate_container_accessible(item, "take from")
        self.assertIsNone(result)

    def test_closed_container_not_accessible(self):
        """Should return error for closed container"""
        item = Mock()
        item.name = "chest"
        item.properties = {"container": {"open": False}}

        result = validate_container_accessible(item, "take from")
        self.assertIsNotNone(result)
        self.assertFalse(result.success)
        self.assertIn("chest is closed", result.primary)


class TestCheckActorHasKey(BaseTestCase):
    """Tests for check_actor_has_key helper."""

    def test_has_matching_key(self):
        """Should return None when actor has key"""
        actor = Mock()
        actor.inventory = ["gold_key", "silver_key"]

        lock = Mock()
        lock.properties = {"opens_with": ["gold_key"]}

        result = check_actor_has_key(actor, lock, "chest", "unlock")
        self.assertIsNone(result)

    def test_no_matching_key(self):
        """Should return error when actor doesn't have key"""
        actor = Mock()
        actor.inventory = ["bronze_key"]

        lock = Mock()
        lock.properties = {"opens_with": ["gold_key"]}

        result = check_actor_has_key(actor, lock, "chest", "unlock")
        self.assertIsNotNone(result)
        self.assertFalse(result.success)
        self.assertIn("don't have the right key", result.primary)
        self.assertIn("unlock", result.primary)
        self.assertIn("chest", result.primary)

    def test_empty_inventory(self):
        """Should return error when inventory is empty"""
        actor = Mock()
        actor.inventory = []

        lock = Mock()
        lock.properties = {"opens_with": ["gold_key"]}

        result = check_actor_has_key(actor, lock, "door", "lock")
        self.assertIsNotNone(result)
        self.assertFalse(result.success)


class TestBuildActionResult(BaseTestCase):
    """Tests for build_action_result helper."""

    def test_basic_message(self):
        """Should build result with just base message"""
        item = self.state.get_item("item_sword")
        result = build_action_result(item, "You take the sword.")

        self.assertTrue(result.success)
        self.assertEqual(result.primary, "You take the sword.")
        self.assertIsNotNone(result.data)
        self.assertIn("id", result.data)
        self.assertEqual(result.data["id"], "item_sword")

    def test_with_beats(self):
        """Should include beats in result"""
        item = self.state.get_item("item_sword")
        result = build_action_result(
            item,
            "You take the sword.",
            beats=["It feels warm."]
        )

        self.assertTrue(result.success)
        self.assertEqual(result.primary, "You take the sword.")
        self.assertEqual(result.beats, ["It feels warm."])

    def test_with_multiple_beats(self):
        """Should include multiple beats from positioning and behavior"""
        item = self.state.get_item("item_sword")
        result = build_action_result(
            item,
            "You take the sword.",
            beats=["You step closer.", "It feels warm."]
        )

        self.assertTrue(result.success)
        self.assertEqual(result.primary, "You take the sword.")
        self.assertEqual(len(result.beats), 2)
        self.assertIn("step closer", result.beats[0])
        self.assertIn("feels warm", result.beats[1])


if __name__ == '__main__':
    unittest.main()
