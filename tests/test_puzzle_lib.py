"""Tests for puzzle_lib behavior modules."""

import unittest
from unittest.mock import Mock

from behavior_libraries.puzzle_lib import state_revealer, sequence_tracker, threshold_checker


class TestStateRevealer(unittest.TestCase):
    """Test state revelation utilities."""

    def test_reveal_item_unconditional(self):
        """Test unconditional item revelation."""
        # Setup
        accessor = Mock()
        item = Mock()
        item.states = {"hidden": True}
        accessor.get_item.return_value = item

        # Reveal item
        result = state_revealer.reveal_item(accessor, "item_key")

        # Verify
        self.assertTrue(result)  # Was hidden, now revealed
        self.assertFalse(item.states["hidden"])

    def test_reveal_item_already_visible(self):
        """Test revealing an already visible item."""
        # Setup
        accessor = Mock()
        item = Mock()
        item.states = {"hidden": False}
        accessor.get_item.return_value = item

        # Try to reveal
        result = state_revealer.reveal_item(accessor, "item_key")

        # Verify - returns False because it was already visible
        self.assertFalse(result)
        self.assertFalse(item.states["hidden"])

    def test_reveal_item_with_condition(self):
        """Test conditional item revelation."""
        # Setup
        accessor = Mock()
        item = Mock()
        item.states = {"hidden": True}
        accessor.get_item.return_value = item

        # Condition that passes
        def condition_pass(item, acc):
            return True

        result = state_revealer.reveal_item(accessor, "item_key", condition_pass)
        self.assertTrue(result)
        self.assertFalse(item.states["hidden"])

        # Reset
        item.states = {"hidden": True}

        # Condition that fails
        def condition_fail(item, acc):
            return False

        result = state_revealer.reveal_item(accessor, "item_key", condition_fail)
        self.assertFalse(result)
        self.assertTrue(item.states["hidden"])  # Still hidden

    def test_reveal_item_not_found(self):
        """Test revealing non-existent item."""
        accessor = Mock()
        accessor.get_item.return_value = None

        result = state_revealer.reveal_item(accessor, "item_missing")
        self.assertFalse(result)

    def test_get_progressive_description(self):
        """Test progressive descriptions based on state."""
        entity = Mock()
        entity.states = {}

        descriptions = [
            "First look",
            "Second look",
            "Third look",
            "Subsequent looks"
        ]

        # First examination
        msg = state_revealer.get_progressive_description(
            entity, "examine_count", descriptions
        )
        self.assertEqual(msg, "First look")
        self.assertEqual(entity.states["examine_count"], 1)

        # Second examination
        msg = state_revealer.get_progressive_description(
            entity, "examine_count", descriptions
        )
        self.assertEqual(msg, "Second look")
        self.assertEqual(entity.states["examine_count"], 2)

        # Third examination
        msg = state_revealer.get_progressive_description(
            entity, "examine_count", descriptions
        )
        self.assertEqual(msg, "Third look")

        # Fourth+ examinations (repeats last)
        msg = state_revealer.get_progressive_description(
            entity, "examine_count", descriptions
        )
        self.assertEqual(msg, "Subsequent looks")

    def test_get_progressive_description_no_increment(self):
        """Test getting description without incrementing counter."""
        entity = Mock()
        entity.states = {"examine_count": 1}

        descriptions = ["Zero", "One", "Two"]

        # Get without incrementing
        msg = state_revealer.get_progressive_description(
            entity, "examine_count", descriptions, increment=False
        )
        self.assertEqual(msg, "One")  # Count is 1, gets index 1
        self.assertEqual(entity.states["examine_count"], 1)  # Not incremented

    def test_check_state_threshold(self):
        """Test state threshold checking."""
        entity = Mock()
        entity.states = {"power_level": 5}

        # Below threshold
        self.assertFalse(state_revealer.check_state_threshold(entity, "power_level", 10))

        # At threshold
        self.assertTrue(state_revealer.check_state_threshold(entity, "power_level", 5))

        # Above threshold
        self.assertTrue(state_revealer.check_state_threshold(entity, "power_level", 3))

        # Missing state
        self.assertFalse(state_revealer.check_state_threshold(entity, "missing", 1))


class TestSequenceTracker(unittest.TestCase):
    """Test sequence tracking utilities."""

    def test_track_action(self):
        """Test tracking actions in sequence."""
        entity = Mock()
        entity.states = {}

        # Track first action
        seq = sequence_tracker.track_action(entity, "note_c")
        self.assertEqual(seq, ["note_c"])

        # Track second action
        seq = sequence_tracker.track_action(entity, "note_e")
        self.assertEqual(seq, ["note_c", "note_e"])

        # Track third action
        seq = sequence_tracker.track_action(entity, "note_g")
        self.assertEqual(seq, ["note_c", "note_e", "note_g"])

    def test_track_action_max_length(self):
        """Test sequence is trimmed to max length."""
        entity = Mock()
        entity.states = {}

        # Add 25 actions with max_length=20
        for i in range(25):
            sequence_tracker.track_action(entity, f"action_{i}", max_length=20)

        # Should only have last 20
        seq = sequence_tracker.get_sequence(entity)
        self.assertEqual(len(seq), 20)
        self.assertEqual(seq[0], "action_5")  # First 5 trimmed
        self.assertEqual(seq[-1], "action_24")

    def test_check_sequence_exact(self):
        """Test exact sequence matching."""
        entity = Mock()
        entity.states = {"action_sequence": ["red", "blue", "green"]}

        # Exact match
        self.assertTrue(sequence_tracker.check_sequence(
            entity, ["red", "blue", "green"], exact=True
        ))

        # Wrong sequence
        self.assertFalse(sequence_tracker.check_sequence(
            entity, ["red", "green", "blue"], exact=True
        ))

        # Partial match (not allowed in exact mode)
        self.assertFalse(sequence_tracker.check_sequence(
            entity, ["blue", "green"], exact=True
        ))

    def test_check_sequence_partial(self):
        """Test partial sequence matching (suffix)."""
        entity = Mock()
        entity.states = {"action_sequence": ["red", "blue", "green"]}

        # Last two match
        self.assertTrue(sequence_tracker.check_sequence(
            entity, ["blue", "green"], exact=False
        ))

        # Last one matches
        self.assertTrue(sequence_tracker.check_sequence(
            entity, ["green"], exact=False
        ))

        # All three match
        self.assertTrue(sequence_tracker.check_sequence(
            entity, ["red", "blue", "green"], exact=False
        ))

        # Wrong suffix
        self.assertFalse(sequence_tracker.check_sequence(
            entity, ["red", "blue"], exact=False
        ))

    def test_reset_sequence(self):
        """Test resetting sequence."""
        entity = Mock()
        entity.states = {"action_sequence": ["a", "b", "c"]}

        sequence_tracker.reset_sequence(entity)

        self.assertEqual(entity.states["action_sequence"], [])

    def test_get_sequence_progress(self):
        """Test getting sequence progress."""
        entity = Mock()
        entity.states = {}

        expected = ["do", "re", "mi", "fa", "sol"]

        # No actions yet
        progress = sequence_tracker.get_sequence_progress(entity, expected)
        self.assertEqual(progress, 0)

        # First action correct
        sequence_tracker.track_action(entity, "do")
        progress = sequence_tracker.get_sequence_progress(entity, expected)
        self.assertEqual(progress, 1)

        # Second action correct
        sequence_tracker.track_action(entity, "re")
        progress = sequence_tracker.get_sequence_progress(entity, expected)
        self.assertEqual(progress, 2)

        # Third action wrong - breaks sequence
        sequence_tracker.track_action(entity, "la")
        progress = sequence_tracker.get_sequence_progress(entity, expected)
        self.assertEqual(progress, 2)  # Still matches first 2, but broke at position 3


class TestThresholdChecker(unittest.TestCase):
    """Test threshold checking utilities."""

    def test_check_threshold_exact(self):
        """Test exact threshold with tolerance."""
        # Within tolerance
        self.assertTrue(threshold_checker.check_threshold(3.6, 3.5, tolerance=0.2, mode="exact"))
        self.assertTrue(threshold_checker.check_threshold(3.4, 3.5, tolerance=0.2, mode="exact"))
        self.assertTrue(threshold_checker.check_threshold(3.5, 3.5, tolerance=0.2, mode="exact"))

        # Outside tolerance
        self.assertFalse(threshold_checker.check_threshold(3.8, 3.5, tolerance=0.2, mode="exact"))
        self.assertFalse(threshold_checker.check_threshold(3.2, 3.5, tolerance=0.2, mode="exact"))

    def test_check_threshold_min(self):
        """Test minimum threshold."""
        # Above threshold
        self.assertTrue(threshold_checker.check_threshold(12, 10, mode="min"))
        self.assertTrue(threshold_checker.check_threshold(10, 10, mode="min"))

        # Below threshold
        self.assertFalse(threshold_checker.check_threshold(9, 10, mode="min"))

    def test_check_threshold_max(self):
        """Test maximum threshold."""
        # Below threshold
        self.assertTrue(threshold_checker.check_threshold(95, 100, mode="max"))
        self.assertTrue(threshold_checker.check_threshold(100, 100, mode="max"))

        # Above threshold
        self.assertFalse(threshold_checker.check_threshold(105, 100, mode="max"))

    def test_get_threshold_feedback(self):
        """Test threshold feedback messages."""
        # Exact match
        msg = threshold_checker.get_threshold_feedback(3.5, 3.5, tolerance=0.2)
        self.assertIn("Perfect", msg)

        # Within tolerance (exact)
        msg = threshold_checker.get_threshold_feedback(3.6, 3.5, tolerance=0.2)
        self.assertIn("Perfect", msg)  # 3.6 is within 0.2 of 3.5

        # Very close (just outside tolerance, within 2x tolerance)
        msg = threshold_checker.get_threshold_feedback(3.75, 3.5, tolerance=0.2)
        self.assertIn("close", msg.lower())

        # Too low
        msg = threshold_checker.get_threshold_feedback(3.0, 3.5, tolerance=0.2)
        self.assertIn("low", msg.lower())

        # Too high
        msg = threshold_checker.get_threshold_feedback(4.0, 3.5, tolerance=0.2)
        self.assertIn("high", msg.lower())

    def test_get_threshold_feedback_custom_labels(self):
        """Test custom feedback labels."""
        labels = {
            "too_low": "Add more weight",
            "too_high": "Remove some weight",
            "close": "Nearly there!",
            "exact": "Balanced!"
        }

        msg = threshold_checker.get_threshold_feedback(3.0, 3.5, tolerance=0.2, labels=labels)
        self.assertEqual(msg, "Add more weight")

        msg = threshold_checker.get_threshold_feedback(3.5, 3.5, tolerance=0.2, labels=labels)
        self.assertEqual(msg, "Balanced!")

    def test_calculate_item_weight(self):
        """Test calculating total item weight."""
        accessor = Mock()

        # Create mock items
        rock = Mock()
        rock.properties = {"weight": 2.5}
        book = Mock()
        book.properties = {"weight": 1.0}
        coin = Mock()
        coin.properties = {"weight": 0.01}

        def get_item_mock(item_id):
            items = {
                "item_rock": rock,
                "item_book": book,
                "item_coin": coin
            }
            return items.get(item_id)

        accessor.get_item = get_item_mock

        # Calculate total weight
        total = threshold_checker.calculate_item_weight(
            accessor, ["item_rock", "item_book", "item_coin"]
        )
        self.assertAlmostEqual(total, 3.51, places=2)

    def test_get_items_in_location(self):
        """Test getting items in a location."""
        accessor = Mock()

        # Create mock items
        item1 = Mock()
        item1.id = "item_rock"
        item1.location = "item_pedestal"

        item2 = Mock()
        item2.id = "item_book"
        item2.location = "item_pedestal"

        item3 = Mock()
        item3.id = "item_coin"
        item3.location = "loc_floor"

        accessor.get_all_items.return_value = [item1, item2, item3]

        # Get items on pedestal
        items = threshold_checker.get_items_in_location(accessor, "item_pedestal")
        self.assertEqual(set(items), {"item_rock", "item_book"})

        # Get items on floor
        items = threshold_checker.get_items_in_location(accessor, "loc_floor")
        self.assertEqual(items, ["item_coin"])


if __name__ == '__main__':
    unittest.main()
