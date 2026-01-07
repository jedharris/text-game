"""Tests for unified reaction interpreter."""

import unittest
from unittest.mock import Mock

from behaviors.shared.infrastructure.reaction_interpreter import process_reaction
from behaviors.shared.infrastructure.reaction_specs import ReactionSpec
from behaviors.shared.infrastructure.match_strategies import NoMatchStrategy
from src.behavior_manager import EventResult


class TestReactionInterpreter(unittest.TestCase):
    """Test core interpreter functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_accessor = Mock()
        self.mock_state = Mock()
        self.mock_state.extra = {}
        self.mock_accessor.game_state = self.mock_state

        self.mock_entity = Mock()
        self.mock_entity.properties = {
            "trust_state": {"current": 0, "floor": -5, "ceiling": 5},
            "state_machine": {"current": "neutral", "states": ["hostile", "neutral", "friendly"]}
        }

        self.test_spec = ReactionSpec(
            reaction_type="test",
            message_key="message",
            fallback_message_key="fallback",
            match_strategy=NoMatchStrategy(),
            context_enrichment=lambda ctx, cfg: ctx
        )

    def test_condition_passes_effects_applied(self):
        """Conditions pass → effects applied → feedback returned."""
        config = {
            "requires_flags": {"test_flag": True},
            "set_flags": {"result_flag": True},
            "message": "Success"
        }
        self.mock_state.extra = {"test_flag": True}

        result = process_reaction(
            self.mock_entity, config, self.mock_accessor, {}, self.test_spec
        )

        self.assertTrue(result.allow)
        self.assertEqual(result.feedback, "Success")
        self.assertTrue(self.mock_state.extra.get("result_flag"))

    def test_condition_fails_effects_skipped(self):
        """Condition fails → effects skipped → failure message returned."""
        config = {
            "requires_flags": {"missing_flag": True},
            "set_flags": {"should_not_set": True},
            "failure_message": "Condition not met"
        }
        self.mock_state.extra = {}

        result = process_reaction(
            self.mock_entity, config, self.mock_accessor, {}, self.test_spec
        )

        self.assertTrue(result.allow)
        self.assertEqual(result.feedback, "Condition not met")
        self.assertNotIn("should_not_set", self.mock_state.extra)

    def test_trust_delta_and_transitions(self):
        """Trust delta applies and triggers transition at threshold."""
        config = {
            "trust_delta": 3,
            "trust_transitions": {"3": "friendly"},
            "message": "Trust increased"
        }

        result = process_reaction(
            self.mock_entity, config, self.mock_accessor, {}, self.test_spec
        )

        self.assertEqual(self.mock_entity.properties["trust_state"]["current"], 3)
        self.assertEqual(self.mock_entity.properties["state_machine"]["current"], "friendly")

    def test_template_substitution(self):
        """Message templates substitute context variables."""
        config = {
            "message": "You give {item} to {target}"
        }
        context = {"item": "sword", "target": "knight"}

        result = process_reaction(
            self.mock_entity, config, self.mock_accessor, context, self.test_spec
        )

        self.assertEqual(result.feedback, "You give sword to knight")

    def test_multiple_conditions_all_must_pass(self):
        """Multiple conditions - all must pass."""
        config = {
            "requires_flags": {"flag1": True},
            "requires_state": ["neutral"],
            "set_flags": {"result": True},
            "message": "Success"
        }
        self.mock_state.extra = {"flag1": True}

        result = process_reaction(
            self.mock_entity, config, self.mock_accessor, {}, self.test_spec
        )

        self.assertTrue(result.allow)
        self.assertTrue(self.mock_state.extra.get("result"))


class TestPropertyModification(unittest.TestCase):
    """Test modify_property (Tier 1 primitive)."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_accessor = Mock()
        self.mock_state = Mock()
        self.mock_state.extra = {}
        self.mock_accessor.game_state = self.mock_state

        self.mock_entity = Mock()
        self.mock_entity.properties = {"health": 50, "max_health": 100}

        self.test_spec = ReactionSpec(
            reaction_type="test",
            message_key="message",
            fallback_message_key="fallback",
            match_strategy=NoMatchStrategy(),
            context_enrichment=lambda ctx, cfg: ctx
        )

    def test_property_delta(self):
        """modify_property with delta adds to numeric value."""
        config = {
            "modify_property": {"path": "health", "delta": 20}
        }

        process_reaction(self.mock_entity, config, self.mock_accessor, {}, self.test_spec)

        self.assertEqual(self.mock_entity.properties["health"], 70)

    def test_property_set(self):
        """modify_property with set replaces value."""
        config = {
            "modify_property": {"path": "health", "set": 100}
        }

        process_reaction(self.mock_entity, config, self.mock_accessor, {}, self.test_spec)

        self.assertEqual(self.mock_entity.properties["health"], 100)

    def test_property_append(self):
        """modify_property with append adds to list."""
        self.mock_entity.properties["knowledge"] = ["item1"]
        config = {
            "modify_property": {"path": "knowledge", "append": ["item2", "item3"]}
        }

        process_reaction(self.mock_entity, config, self.mock_accessor, {}, self.test_spec)

        self.assertEqual(self.mock_entity.properties["knowledge"], ["item1", "item2", "item3"])


class TestPropertyConditions(unittest.TestCase):
    """Test require_property (Tier 1 primitive)."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_accessor = Mock()
        self.mock_state = Mock()
        self.mock_state.extra = {}
        self.mock_accessor.game_state = self.mock_state

        self.mock_entity = Mock()
        self.mock_entity.properties = {
            "trust_state": {"current": 3},
            "sanity": 75
        }

        self.test_spec = ReactionSpec(
            reaction_type="test",
            message_key="message",
            fallback_message_key="fallback",
            match_strategy=NoMatchStrategy(),
            context_enrichment=lambda ctx, cfg: ctx
        )

    def test_property_min_passes(self):
        """require_property with min passes when value >= min."""
        config = {
            "require_property": {"path": "trust_state.current", "min": 2},
            "set_flags": {"success": True}
        }

        result = process_reaction(self.mock_entity, config, self.mock_accessor, {}, self.test_spec)

        self.assertTrue(self.mock_state.extra.get("success"))

    def test_property_min_fails(self):
        """require_property with min fails when value < min."""
        config = {
            "require_property": {"path": "trust_state.current", "min": 5},
            "set_flags": {"should_not_set": True},
            "failure_message": "Insufficient trust"
        }

        result = process_reaction(self.mock_entity, config, self.mock_accessor, {}, self.test_spec)

        self.assertEqual(result.feedback, "Insufficient trust")
        self.assertNotIn("should_not_set", self.mock_state.extra)

    def test_property_range(self):
        """require_property with min and max checks range."""
        config = {
            "require_property": {"path": "sanity", "min": 50, "max": 100},
            "set_flags": {"sane": True}
        }

        result = process_reaction(self.mock_entity, config, self.mock_accessor, {}, self.test_spec)

        self.assertTrue(self.mock_state.extra.get("sane"))


if __name__ == "__main__":
    unittest.main()
