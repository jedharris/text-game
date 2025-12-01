"""Tests for behavior manager tier system."""

import unittest
from src.behavior_manager import BehaviorManager


class TestTierCalculation(unittest.TestCase):
    """Test tier calculation based on directory depth."""

    def setUp(self):
        self.manager = BehaviorManager()

    def test_calculate_tier_depth_zero(self):
        """Files in base directory are Tier 1 (depth 0)."""
        base_dir = "/game/behaviors"
        behavior_file = "/game/behaviors/consumables.py"

        tier = self.manager._calculate_tier(behavior_file, base_dir)

        self.assertEqual(tier, 1, "Base directory files should be Tier 1")

    def test_calculate_tier_depth_one(self):
        """Files in first subdirectory are Tier 2 (depth 1)."""
        base_dir = "/game/behaviors"
        behavior_file = "/game/behaviors/library/examine.py"

        tier = self.manager._calculate_tier(behavior_file, base_dir)

        self.assertEqual(tier, 2, "First subdirectory files should be Tier 2")

    def test_calculate_tier_depth_two(self):
        """Files in nested subdirectory are Tier 3 (depth 2)."""
        base_dir = "/game/behaviors"
        behavior_file = "/game/behaviors/library/core/basic.py"

        tier = self.manager._calculate_tier(behavior_file, base_dir)

        self.assertEqual(tier, 3, "Nested subdirectory files should be Tier 3")

    def test_calculate_tier_with_trailing_slash(self):
        """Tier calculation works with trailing slash in base_dir."""
        base_dir = "/game/behaviors/"
        behavior_file = "/game/behaviors/library/examine.py"

        tier = self.manager._calculate_tier(behavior_file, base_dir)

        self.assertEqual(tier, 2, "Should handle trailing slash correctly")

    def test_calculate_tier_absolute_paths(self):
        """Tier calculation works with different absolute path formats."""
        base_dir = "/Users/jed/game/behaviors"
        behavior_file = "/Users/jed/game/behaviors/library/locks.py"

        tier = self.manager._calculate_tier(behavior_file, base_dir)

        self.assertEqual(tier, 2, "Should work with different absolute paths")


class TestTierStorage(unittest.TestCase):
    """Test storing and retrieving tiered event mappings."""

    def setUp(self):
        self.manager = BehaviorManager()

    def test_register_verb_mapping_stores_tier(self):
        """Registering a verb mapping stores tier along with event."""
        verb = "examine"
        event = "on_examine"
        tier = 2
        module_name = "test_module"

        # Register the mapping with tier
        self.manager._register_verb_mapping(verb, event, module_name, tier)

        # Check internal structure
        events = self.manager.get_events_for_verb(verb)
        self.assertIsNotNone(events, "Should have events for verb")
        self.assertEqual(len(events), 1, "Should have one event")
        self.assertEqual(events[0], (tier, event), "Should store (tier, event) tuple")

    def test_register_verb_mapping_within_tier_conflict(self):
        """Registering same verb+tier with different event raises error."""
        verb = "examine"
        module1 = "module1"
        module2 = "module2"
        tier = 2

        # Register first mapping
        self.manager._register_verb_mapping(verb, "on_examine_mushroom", module1, tier)

        # Attempt to register conflicting mapping (same verb+tier, different event)
        with self.assertRaises(ValueError) as cm:
            self.manager._register_verb_mapping(verb, "on_examine_rock", module2, tier)

        error_msg = str(cm.exception)
        self.assertIn("examine", error_msg, "Error should mention verb")
        self.assertIn("Tier 2", error_msg, "Error should mention tier")
        self.assertIn("conflict", error_msg.lower(), "Error should mention conflict")

    def test_register_verb_mapping_same_event_same_tier_allowed(self):
        """Registering same verb+tier+event is allowed (no error)."""
        verb = "examine"
        event = "on_examine"
        tier = 2
        module1 = "module1"
        module2 = "module2"

        # Register first mapping
        self.manager._register_verb_mapping(verb, event, module1, tier)

        # Register same mapping again (should not raise)
        self.manager._register_verb_mapping(verb, event, module2, tier)

        # Should only store once (no duplicates)
        events = self.manager.get_events_for_verb(verb)
        self.assertEqual(len(events), 1, "Should not create duplicate entries")

    def test_register_verb_mapping_cross_tier_allowed(self):
        """Registering same verb in different tiers is allowed."""
        verb = "examine"
        module1 = "module1"
        module2 = "module2"

        # Register in Tier 1
        self.manager._register_verb_mapping(verb, "on_examine_mushroom", module1, tier=1)

        # Register in Tier 2 (should not raise)
        self.manager._register_verb_mapping(verb, "on_examine", module2, tier=2)

        # Should have both events
        events = self.manager.get_events_for_verb(verb)
        self.assertEqual(len(events), 2, "Should have events from both tiers")

    def test_get_events_for_verb_returns_sorted_list(self):
        """Getting events for a verb returns list sorted by tier (lowest first)."""
        verb = "examine"

        # Register in different order (Tier 3, then Tier 1, then Tier 2)
        self.manager._register_verb_mapping(verb, "on_examine_default", "module3", tier=3)
        self.manager._register_verb_mapping(verb, "on_examine_mushroom", "module1", tier=1)
        self.manager._register_verb_mapping(verb, "on_examine", "module2", tier=2)

        # Get events
        events = self.manager.get_events_for_verb(verb)

        # Should be sorted by tier (lowest/highest precedence first)
        self.assertEqual(len(events), 3, "Should have all three events")
        self.assertEqual(events[0], (1, "on_examine_mushroom"), "Tier 1 should be first")
        self.assertEqual(events[1], (2, "on_examine"), "Tier 2 should be second")
        self.assertEqual(events[2], (3, "on_examine_default"), "Tier 3 should be third")

    def test_get_events_for_verb_returns_none_when_not_found(self):
        """Getting events for unknown verb returns None."""
        events = self.manager.get_events_for_verb("unknown_verb")
        self.assertIsNone(events, "Should return None for unknown verb")


if __name__ == '__main__':
    unittest.main()
