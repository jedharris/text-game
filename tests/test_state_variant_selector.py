"""Tests for state variant selection (Context Builder logic).

Tests that the Context Builder correctly selects location state_variants
based on game state (environmental spreads, quest flags, visit history).
"""
import unittest
from types import SimpleNamespace
from typing import Any, Dict, Optional

from src.types import ActorId, LocationId
from utilities.state_variant_selector import (
    select_state_variant,
    track_location_visit,
)


class TestStateVariantSelection(unittest.TestCase):
    """Test state variant selection priority and logic."""

    def _make_location(self, properties: Optional[Dict[str, Any]] = None) -> Any:
        """Helper to create mock location."""
        loc = SimpleNamespace()
        loc.id = LocationId("test_location")
        loc.properties = properties or {}
        return loc

    def test_no_variants_returns_none(self):
        """Test that missing state_variants returns None."""
        llm_context = {"traits": ["trait1", "trait2"]}
        location = self._make_location()
        world_state = {}
        actor_id = ActorId("player")

        result = select_state_variant(llm_context, location, world_state, actor_id)
        self.assertIsNone(result)

    def test_empty_variants_returns_none(self):
        """Test that empty state_variants dict returns None."""
        llm_context = {"traits": ["trait1"], "state_variants": {}}
        location = self._make_location()
        world_state = {}
        actor_id = ActorId("player")

        result = select_state_variant(llm_context, location, world_state, actor_id)
        self.assertIsNone(result)

    def test_location_property_bool_match(self):
        """Test that boolean location property matches variant."""
        llm_context = {
            "state_variants": {
                "infection_present": "Fungi sprouting everywhere",
                "revisit": "Familiar location"
            }
        }
        location = self._make_location({"infection_present": True})
        world_state = {}
        actor_id = ActorId("player")

        result = select_state_variant(llm_context, location, world_state, actor_id)
        self.assertEqual(result, "Fungi sprouting everywhere")

    def test_location_property_string_match(self):
        """Test that string location property value matches variant."""
        llm_context = {
            "state_variants": {
                "low": "Faint spore presence",
                "medium": "Moderate spore growth",
                "high": "Thick spore coverage"
            }
        }
        location = self._make_location({"spore_level": "medium"})
        world_state = {}
        actor_id = ActorId("player")

        result = select_state_variant(llm_context, location, world_state, actor_id)
        self.assertEqual(result, "Moderate spore growth")

    def test_location_property_false_skipped(self):
        """Test that false boolean property doesn't match."""
        llm_context = {
            "state_variants": {
                "infection_present": "Fungi sprouting",
                "revisit": "Familiar location"
            }
        }
        location = self._make_location({"infection_present": False})
        world_state = {"visit_history": {"player": ["test_location"]}}
        actor_id = ActorId("player")

        result = select_state_variant(llm_context, location, world_state, actor_id)
        # Should skip false property and use revisit
        self.assertEqual(result, "Familiar location")

    def test_quest_flag_match(self):
        """Test that quest flag matches variant."""
        llm_context = {
            "state_variants": {
                "telescope_repaired": "The telescope gleams",
                "revisit": "Familiar platform"
            }
        }
        location = self._make_location()
        world_state = {
            "flags": {"telescope_repaired": True},
            "visit_history": {"player": ["test_location"]}
        }
        actor_id = ActorId("player")

        result = select_state_variant(llm_context, location, world_state, actor_id)
        self.assertEqual(result, "The telescope gleams")

    def test_first_visit_match(self):
        """Test that first visit is detected."""
        llm_context = {
            "state_variants": {
                "first_visit": "You've never been here before",
                "revisit": "This place is familiar"
            }
        }
        location = self._make_location()
        world_state = {"visit_history": {"player": []}}
        actor_id = ActorId("player")

        result = select_state_variant(llm_context, location, world_state, actor_id)
        self.assertEqual(result, "You've never been here before")

    def test_revisit_match(self):
        """Test that revisit is detected."""
        llm_context = {
            "state_variants": {
                "first_visit": "You've never been here before",
                "revisit": "This place is familiar"
            }
        }
        location = self._make_location()
        world_state = {"visit_history": {"player": ["test_location"]}}
        actor_id = ActorId("player")

        result = select_state_variant(llm_context, location, world_state, actor_id)
        self.assertEqual(result, "This place is familiar")

    def test_priority_location_over_flags(self):
        """Test that location properties have priority over quest flags."""
        llm_context = {
            "state_variants": {
                "infection_present": "Infected location",
                "telescope_repaired": "Telescope repaired",
                "revisit": "Familiar"
            }
        }
        location = self._make_location({"infection_present": True})
        world_state = {
            "flags": {"telescope_repaired": True},
            "visit_history": {"player": ["test_location"]}
        }
        actor_id = ActorId("player")

        result = select_state_variant(llm_context, location, world_state, actor_id)
        # Should choose infection_present (highest priority)
        self.assertEqual(result, "Infected location")

    def test_priority_flags_over_visit(self):
        """Test that quest flags have priority over visit history."""
        llm_context = {
            "state_variants": {
                "telescope_repaired": "Telescope repaired",
                "revisit": "Familiar"
            }
        }
        location = self._make_location()
        world_state = {
            "flags": {"telescope_repaired": True},
            "visit_history": {"player": ["test_location"]}
        }
        actor_id = ActorId("player")

        result = select_state_variant(llm_context, location, world_state, actor_id)
        # Should choose telescope_repaired (higher priority than visit)
        self.assertEqual(result, "Telescope repaired")

    def test_fallback_to_none(self):
        """Test that no matching variant returns None."""
        llm_context = {
            "state_variants": {
                "infection_present": "Infected",
                "first_visit": "New place"
            }
        }
        location = self._make_location({"infection_present": False})
        world_state = {"visit_history": {"player": ["test_location"]}}
        actor_id = ActorId("player")

        result = select_state_variant(llm_context, location, world_state, actor_id)
        # No matching variant (infection false, already visited)
        self.assertIsNone(result)


class TestVisitTracking(unittest.TestCase):
    """Test visit history tracking."""

    def test_track_first_visit(self):
        """Test tracking first visit to a location."""
        world_state: Dict[str, Any] = {}
        actor_id = ActorId("player")
        location_id = LocationId("market_square")

        track_location_visit(world_state, actor_id, location_id)

        self.assertIn("visit_history", world_state)
        self.assertIn("player", world_state["visit_history"])
        self.assertIn("market_square", world_state["visit_history"]["player"])

    def test_track_multiple_locations(self):
        """Test tracking visits to multiple locations."""
        world_state: Dict[str, Any] = {}
        actor_id = ActorId("player")

        track_location_visit(world_state, actor_id, LocationId("loc1"))
        track_location_visit(world_state, actor_id, LocationId("loc2"))
        track_location_visit(world_state, actor_id, LocationId("loc3"))

        visits = world_state["visit_history"]["player"]
        self.assertEqual(len(visits), 3)
        self.assertIn("loc1", visits)
        self.assertIn("loc2", visits)
        self.assertIn("loc3", visits)

    def test_no_duplicate_tracking(self):
        """Test that revisiting doesn't add duplicates."""
        world_state: Dict[str, Any] = {}
        actor_id = ActorId("player")
        location_id = LocationId("market_square")

        track_location_visit(world_state, actor_id, location_id)
        track_location_visit(world_state, actor_id, location_id)
        track_location_visit(world_state, actor_id, location_id)

        visits = world_state["visit_history"]["player"]
        self.assertEqual(len(visits), 1)
        self.assertEqual(visits[0], "market_square")

    def test_track_multiple_actors(self):
        """Test tracking different actors independently."""
        world_state: Dict[str, Any] = {}

        track_location_visit(world_state, ActorId("player"), LocationId("loc1"))
        track_location_visit(world_state, ActorId("npc1"), LocationId("loc2"))
        track_location_visit(world_state, ActorId("player"), LocationId("loc3"))

        self.assertEqual(len(world_state["visit_history"]["player"]), 2)
        self.assertEqual(len(world_state["visit_history"]["npc1"]), 1)
        self.assertIn("loc1", world_state["visit_history"]["player"])
        self.assertIn("loc3", world_state["visit_history"]["player"])
        self.assertIn("loc2", world_state["visit_history"]["npc1"])


if __name__ == '__main__':
    unittest.main()
