"""Tests for item state variant selection in entity_serializer.

Tests the state-dependent narration system for items including doors,
lights, containers, and custom state properties.
"""
import unittest
from unittest.mock import Mock
from utilities.entity_serializer import (
    _select_item_state_variant,
    _compute_door_state_key,
    entity_to_dict
)


class TestDoorStateVariants(unittest.TestCase):
    """Tests for door state variant selection."""

    def test_door_state_open(self):
        """Door in open state selects 'open' variant."""
        entity = Mock()
        entity.door_open = True
        entity.door_locked = False

        llm_context = {
            "state_variants": {
                "open": "door swings wide",
                "closed_locked": "door is locked",
                "closed_unlocked": "door is closed"
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertEqual(result, "door swings wide")

    def test_door_state_closed_locked(self):
        """Door in closed and locked state selects 'closed_locked' variant."""
        entity = Mock()
        entity.door_open = False
        entity.door_locked = True

        llm_context = {
            "state_variants": {
                "open": "door swings wide",
                "closed_locked": "door is locked shut",
                "closed_unlocked": "door is closed"
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertEqual(result, "door is locked shut")

    def test_door_state_closed_unlocked(self):
        """Door in closed but unlocked state selects 'closed_unlocked' variant."""
        entity = Mock()
        entity.door_open = False
        entity.door_locked = False

        llm_context = {
            "state_variants": {
                "open": "door swings wide",
                "closed_locked": "door is locked",
                "closed_unlocked": "door is closed but unlatched"
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertEqual(result, "door is closed but unlatched")

    def test_compute_door_state_key_open(self):
        """_compute_door_state_key returns 'open' for open door."""
        entity = Mock()
        entity.door_open = True
        entity.door_locked = False

        result = _compute_door_state_key(entity)
        self.assertEqual(result, "open")

    def test_compute_door_state_key_closed_locked(self):
        """_compute_door_state_key returns 'closed_locked' for locked door."""
        entity = Mock()
        entity.door_open = False
        entity.door_locked = True

        result = _compute_door_state_key(entity)
        self.assertEqual(result, "closed_locked")

    def test_compute_door_state_key_closed_unlocked(self):
        """_compute_door_state_key returns 'closed_unlocked' for unlocked closed door."""
        entity = Mock()
        entity.door_open = False
        entity.door_locked = False

        result = _compute_door_state_key(entity)
        self.assertEqual(result, "closed_unlocked")

    def test_compute_door_state_key_not_door(self):
        """_compute_door_state_key returns None for non-door entity."""
        entity = Mock(spec=[])  # No door attributes

        result = _compute_door_state_key(entity)
        self.assertIsNone(result)


class TestLightStateVariants(unittest.TestCase):
    """Tests for light source state variant selection."""

    def test_light_lit(self):
        """Light in lit state selects 'lit' variant."""
        entity = Mock()
        entity.states = {"lit": True}

        llm_context = {
            "state_variants": {
                "lit": "flames dancing brightly",
                "unlit": "unlit and cold"
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertEqual(result, "flames dancing brightly")

    def test_light_unlit(self):
        """Light in unlit state selects 'unlit' variant."""
        entity = Mock()
        entity.states = {"lit": False}

        llm_context = {
            "state_variants": {
                "lit": "flames dancing",
                "unlit": "cold and dark"
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertEqual(result, "cold and dark")


class TestContainerStateVariants(unittest.TestCase):
    """Tests for container state variant selection."""

    def test_container_open(self):
        """Container in open state selects 'open' variant."""
        entity = Mock()
        entity.container = {"open": True}

        llm_context = {
            "state_variants": {
                "open": "lid stands open, contents visible",
                "closed": "lid is closed tight"
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertEqual(result, "lid stands open, contents visible")

    def test_container_closed(self):
        """Container in closed state selects 'closed' variant."""
        entity = Mock(spec=['container'])  # Only has container attribute
        entity.container = {"open": False}

        llm_context = {
            "state_variants": {
                "open": "lid stands open",
                "closed": "lid is shut tight"
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertEqual(result, "lid is shut tight")


class TestGenericStateVariants(unittest.TestCase):
    """Tests for generic property-based state variants."""

    def test_broken_state_true(self):
        """Entity with broken=True selects 'broken' variant."""
        entity = Mock()
        entity.properties = {"broken": True}

        llm_context = {
            "state_variants": {
                "broken": "shattered and useless",
                "not_broken": "intact and functional"
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertEqual(result, "shattered and useless")

    def test_broken_state_false(self):
        """Entity with broken=False selects 'not_broken' variant."""
        entity = Mock()
        entity.properties = {"broken": False}

        llm_context = {
            "state_variants": {
                "broken": "shattered",
                "not_broken": "intact and whole"
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertEqual(result, "intact and whole")

    def test_string_property_state(self):
        """Entity with string property selects matching variant."""
        entity = Mock()
        # Use 'active' which is in the checked properties list, but as a string value
        entity.properties = {"active": "damaged"}

        llm_context = {
            "state_variants": {
                "damaged": "cracked and worn",
                "pristine": "perfect condition"
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertEqual(result, "cracked and worn")


class TestStateVariantTraitReplacement(unittest.TestCase):
    """Tests for state variants that replace traits entirely."""

    def test_dict_variant_replaces_traits(self):
        """State variant dict with traits replaces base traits."""
        entity = Mock()
        entity.states = {"lit": True}

        llm_context = {
            "traits": ["wooden shaft", "pitch-soaked"],
            "state_variants": {
                "lit": {
                    "traits": ["flames dancing", "smoke rising", "warm glow"]
                },
                "unlit": {
                    "traits": ["cold wick", "pitch ready"]
                }
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertIsInstance(result, dict)
        self.assertIn("traits", result)
        self.assertEqual(set(result["traits"]), {"flames dancing", "smoke rising", "warm glow"})

    def test_string_variant_keeps_traits(self):
        """String state variant is added as state_note, traits remain."""
        entity = Mock()
        entity.door_open = True

        llm_context = {
            "traits": ["ornate carved wood", "ancient"],
            "state_variants": {
                "open": "door stands wide open"
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertIsInstance(result, str)
        self.assertEqual(result, "door stands wide open")


class TestStatePriority(unittest.TestCase):
    """Tests for state variant selection priority."""

    def test_door_state_takes_priority_over_generic(self):
        """Door state checked before generic properties."""
        entity = Mock()
        entity.door_open = True
        entity.door_locked = False
        entity.properties = {"broken": True}

        llm_context = {
            "state_variants": {
                "open": "door is open",
                "broken": "door is broken"
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertEqual(result, "door is open")

    def test_light_state_takes_priority_over_container(self):
        """Light state checked before container state."""
        entity = Mock(spec=['states', 'container'])  # Has both attributes
        entity.states = {"lit": True}
        entity.container = {"open": True}

        llm_context = {
            "state_variants": {
                "lit": "flames burning",
                "open": "container open"
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertEqual(result, "flames burning")


class TestNoStateVariants(unittest.TestCase):
    """Tests for entities without state variants."""

    def test_no_state_variants_returns_none(self):
        """Entity without state_variants returns None."""
        entity = Mock()
        entity.door_open = True

        llm_context = {
            "traits": ["wooden door", "simple"]
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertIsNone(result)

    def test_empty_state_variants_returns_none(self):
        """Entity with empty state_variants dict returns None."""
        entity = Mock()
        entity.door_open = True

        llm_context = {
            "traits": ["wooden door"],
            "state_variants": {}
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertIsNone(result)

    def test_missing_state_key_returns_none(self):
        """Entity state not in variants dict returns None."""
        entity = Mock()
        entity.door_open = True
        entity.door_locked = False
        entity.properties = {}  # Empty dict so property check doesn't fail

        llm_context = {
            "state_variants": {
                "closed_locked": "locked tight",
                "closed_unlocked": "closed but unlocked"
                # No "open" variant
            }
        }

        result = _select_item_state_variant(llm_context, entity)
        self.assertIsNone(result)


class TestEntityToDictIntegration(unittest.TestCase):
    """Integration tests for entity_to_dict with state variants."""

    def test_entity_to_dict_includes_state_note(self):
        """entity_to_dict includes state_note for door with state variant."""
        entity = Mock()
        entity.id = "door_test"
        entity.name = "wooden door"
        entity.description = "A simple door"
        entity.door_open = True
        entity.door_locked = False
        entity.llm_context = {
            "traits": ["wooden", "simple"],
            "state_variants": {
                "open": "door swings wide"
            }
        }

        result = entity_to_dict(entity, include_llm_context=True)

        self.assertIn("state_note", result)
        self.assertEqual(result["state_note"], "door swings wide")
        self.assertIn("llm_context", result)
        self.assertNotIn("state_variants", result["llm_context"])  # Should be removed

    def test_entity_to_dict_replaces_traits(self):
        """entity_to_dict replaces traits when variant is dict."""
        entity = Mock()
        entity.id = "torch_test"
        entity.name = "torch"
        entity.states = {"lit": True}
        entity.llm_context = {
            "traits": ["wooden shaft"],
            "state_variants": {
                "lit": {"traits": ["flames dancing", "warm glow"]},
                "unlit": {"traits": ["cold wick"]}
            }
        }

        result = entity_to_dict(entity, include_llm_context=True)

        self.assertNotIn("state_note", result)
        self.assertIn("llm_context", result)
        self.assertIn("traits", result["llm_context"])
        # Traits should be from "lit" variant, not base traits
        self.assertEqual(set(result["llm_context"]["traits"]), {"flames dancing", "warm glow"})


if __name__ == '__main__':
    unittest.main()
