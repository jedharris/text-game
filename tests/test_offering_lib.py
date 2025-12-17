"""Tests for offering_lib behavior modules."""

import unittest
from unittest.mock import Mock, MagicMock

from behavior_libraries.offering_lib import offering_handler, blessing_manager, alignment_tracker
from src.types import ActorId
from src.word_entry import WordEntry, WordType


def make_word(word: str) -> WordEntry:
    """Helper to create WordEntry for tests."""
    return WordEntry(word=word, synonyms=[], word_type=WordType.NOUN)


class TestOfferingHandler(unittest.TestCase):
    """Test offering handler."""

    def test_handle_offer_missing_item(self):
        """Test offering without specifying item."""
        accessor = Mock()
        action = {"actor_id": ActorId("player")}

        result = offering_handler.handle_offer(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what", result.message.lower())

    def test_handle_offer_missing_target(self):
        """Test offering without specifying target."""
        accessor = Mock()
        action = {
            "actor_id": ActorId("player"),
            "object": make_word("flower")
        }

        result = offering_handler.handle_offer(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("to what", result.message.lower())

    def test_on_receive_offering_default(self):
        """Test default offering receiver rejects."""
        entity = Mock()
        entity.name = "altar"
        accessor = Mock()
        context = {"offered_item": Mock(), "actor_id": ActorId("player")}

        result = offering_handler.on_receive_offering(entity, accessor, context)

        self.assertFalse(result.allow)
        self.assertIn("does not accept", result.message)


class TestBlessingManager(unittest.TestCase):
    """Test blessing and curse management."""

    def test_apply_blessing(self):
        """Test applying a blessing."""
        accessor = Mock()
        actor = Mock()
        actor.states = {}
        accessor.get_actor.return_value = actor

        result = blessing_manager.apply_blessing(
            accessor, ActorId("player"), "strength", duration=10, value=2
        )

        self.assertTrue(result)
        self.assertEqual(len(actor.states["effects"]), 1)

        effect = actor.states["effects"][0]
        self.assertEqual(effect["type"], "strength")
        self.assertTrue(effect["is_blessing"])
        self.assertEqual(effect["duration"], 10)
        self.assertEqual(effect["value"], 2)

    def test_apply_curse(self):
        """Test applying a curse."""
        accessor = Mock()
        actor = Mock()
        actor.states = {}
        accessor.get_actor.return_value = actor

        result = blessing_manager.apply_curse(
            accessor, ActorId("player"), "weakness", duration=5, value=-1
        )

        self.assertTrue(result)
        self.assertEqual(len(actor.states["effects"]), 1)

        effect = actor.states["effects"][0]
        self.assertEqual(effect["type"], "weakness")
        self.assertFalse(effect["is_blessing"])
        self.assertEqual(effect["duration"], 5)
        self.assertEqual(effect["value"], -1)

    def test_get_active_effects(self):
        """Test getting active effects."""
        accessor = Mock()
        actor = Mock()
        actor.states = {
            "effects": [
                {"type": "strength", "duration": 5},
                {"type": "luck", "duration": 10}
            ]
        }
        accessor.get_actor.return_value = actor

        effects = blessing_manager.get_active_effects(accessor, ActorId("player"))

        self.assertEqual(len(effects), 2)
        self.assertEqual(effects[0]["type"], "strength")
        self.assertEqual(effects[1]["type"], "luck")

    def test_has_effect(self):
        """Test checking for specific effect."""
        accessor = Mock()
        actor = Mock()
        actor.states = {
            "effects": [
                {"type": "strength", "duration": 5}
            ]
        }
        accessor.get_actor.return_value = actor

        self.assertTrue(blessing_manager.has_effect(accessor, ActorId("player"), "strength"))
        self.assertFalse(blessing_manager.has_effect(accessor, ActorId("player"), "luck"))

    def test_remove_effect(self):
        """Test removing an effect."""
        accessor = Mock()
        actor = Mock()
        actor.states = {
            "effects": [
                {"type": "strength", "duration": 5},
                {"type": "luck", "duration": 10}
            ]
        }
        accessor.get_actor.return_value = actor

        result = blessing_manager.remove_effect(accessor, ActorId("player"), "strength")

        self.assertTrue(result)
        self.assertEqual(len(actor.states["effects"]), 1)
        self.assertEqual(actor.states["effects"][0]["type"], "luck")

    def test_tick_effects(self):
        """Test effect duration ticking."""
        accessor = Mock()
        actor = Mock()
        actor.states = {
            "effects": [
                {"type": "strength", "duration": 3},
                {"type": "luck", "duration": 2},
                {"type": "protection", "duration": -1}  # Permanent
            ]
        }
        accessor.get_actor.return_value = actor

        # First tick - both decrement
        expired = blessing_manager.tick_effects(accessor, ActorId("player"))
        self.assertEqual(len(expired), 0)
        self.assertEqual(len(actor.states["effects"]), 3)
        self.assertEqual(actor.states["effects"][0]["duration"], 2)
        self.assertEqual(actor.states["effects"][1]["duration"], 1)

        # Second tick - luck expires (1 -> 0)
        expired = blessing_manager.tick_effects(accessor, ActorId("player"))
        self.assertEqual(len(expired), 1)
        self.assertIn("luck", expired)
        self.assertEqual(len(actor.states["effects"]), 2)
        self.assertEqual(actor.states["effects"][0]["duration"], 1)

        # Third tick - strength expires (1 -> 0)
        expired = blessing_manager.tick_effects(accessor, ActorId("player"))
        self.assertEqual(len(expired), 1)
        self.assertIn("strength", expired)
        self.assertEqual(len(actor.states["effects"]), 1)
        self.assertEqual(actor.states["effects"][0]["type"], "protection")

    def test_get_effect_description(self):
        """Test effect descriptions."""
        desc = blessing_manager.get_effect_description("strength", is_blessing=True)
        self.assertIn("stronger", desc.lower())

        desc = blessing_manager.get_effect_description("weakness", is_blessing=False)
        self.assertIn("weak", desc.lower())

        # Unknown effect should get generic description
        desc = blessing_manager.get_effect_description("unknown", is_blessing=True)
        self.assertIn("blessed", desc.lower())


class TestAlignmentTracker(unittest.TestCase):
    """Test alignment tracking."""

    def test_record_choice_good(self):
        """Test recording a good choice."""
        accessor = Mock()
        actor = Mock()
        actor.states = {}
        accessor.get_actor.return_value = actor

        result = alignment_tracker.record_choice(accessor, ActorId("player"), "good", weight=2.0)

        self.assertTrue(result)
        self.assertEqual(actor.states["alignment"], 2.0)

        # Record another good choice
        alignment_tracker.record_choice(accessor, ActorId("player"), "good", weight=1.5)
        self.assertEqual(actor.states["alignment"], 3.5)

    def test_record_choice_evil(self):
        """Test recording an evil choice."""
        accessor = Mock()
        actor = Mock()
        actor.states = {}
        accessor.get_actor.return_value = actor

        result = alignment_tracker.record_choice(accessor, ActorId("player"), "evil", weight=1.0)

        self.assertTrue(result)
        self.assertEqual(actor.states["alignment"], -1.0)

    def test_record_choice_neutral(self):
        """Test recording a neutral choice."""
        accessor = Mock()
        actor = Mock()
        actor.states = {"alignment": 2.0}
        accessor.get_actor.return_value = actor

        alignment_tracker.record_choice(accessor, ActorId("player"), "neutral", weight=1.0)

        # Neutral choices don't change alignment
        self.assertEqual(actor.states["alignment"], 2.0)

    def test_alignment_clamping(self):
        """Test alignment is clamped to -10 to +10."""
        accessor = Mock()
        actor = Mock()
        actor.states = {"alignment": 9.0}
        accessor.get_actor.return_value = actor

        # Try to exceed +10
        alignment_tracker.record_choice(accessor, ActorId("player"), "good", weight=5.0)
        self.assertEqual(actor.states["alignment"], 10.0)

        # Try to go below -10
        actor.states["alignment"] = -9.0
        alignment_tracker.record_choice(accessor, ActorId("player"), "evil", weight=5.0)
        self.assertEqual(actor.states["alignment"], -10.0)

    def test_get_alignment(self):
        """Test getting alignment score."""
        accessor = Mock()
        actor = Mock()
        actor.states = {"alignment": 5.5}
        accessor.get_actor.return_value = actor

        alignment = alignment_tracker.get_alignment(accessor, ActorId("player"))
        self.assertEqual(alignment, 5.5)

    def test_get_alignment_descriptor(self):
        """Test alignment descriptors."""
        self.assertEqual(alignment_tracker.get_alignment_descriptor(8.0), "Saintly")
        self.assertEqual(alignment_tracker.get_alignment_descriptor(5.0), "Virtuous")
        self.assertEqual(alignment_tracker.get_alignment_descriptor(2.0), "Good")
        self.assertEqual(alignment_tracker.get_alignment_descriptor(0.0), "Neutral")
        self.assertEqual(alignment_tracker.get_alignment_descriptor(-2.0), "Questionable")
        self.assertEqual(alignment_tracker.get_alignment_descriptor(-5.0), "Wicked")
        self.assertEqual(alignment_tracker.get_alignment_descriptor(-8.0), "Malevolent")

    def test_get_alignment_category(self):
        """Test alignment categories."""
        self.assertEqual(alignment_tracker.get_alignment_category(5.0), "good")
        self.assertEqual(alignment_tracker.get_alignment_category(0.0), "neutral")
        self.assertEqual(alignment_tracker.get_alignment_category(-5.0), "evil")

    def test_reset_alignment(self):
        """Test resetting alignment."""
        accessor = Mock()
        actor = Mock()
        actor.states = {"alignment": 7.0}
        accessor.get_actor.return_value = actor

        result = alignment_tracker.reset_alignment(accessor, ActorId("player"))

        self.assertTrue(result)
        self.assertEqual(actor.states["alignment"], 0.0)

    def test_get_alignment_effects(self):
        """Test alignment effect suggestions."""
        # Good alignment
        effects = alignment_tracker.get_alignment_effects(8.0)
        self.assertGreater(effects["good_npc_reaction"], 0)
        self.assertLess(effects["evil_npc_reaction"], 0)
        self.assertGreater(effects["holy_power_bonus"], 0)

        # Evil alignment
        effects = alignment_tracker.get_alignment_effects(-8.0)
        self.assertLess(effects["good_npc_reaction"], 0)
        self.assertGreater(effects["evil_npc_reaction"], 0)
        self.assertGreater(effects["dark_power_bonus"], 0)

        # Neutral alignment
        effects = alignment_tracker.get_alignment_effects(0.0)
        self.assertEqual(effects["good_npc_reaction"], 0)
        self.assertEqual(effects["evil_npc_reaction"], 0)


if __name__ == '__main__':
    unittest.main()
