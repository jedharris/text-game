"""Tests for the event registry system."""

import unittest
from unittest.mock import Mock, MagicMock
from types import ModuleType

from src.behavior_manager import BehaviorManager, EventInfo


class TestEventRegistryBasics(unittest.TestCase):
    """Test basic event registry functionality."""

    def setUp(self):
        self.manager = BehaviorManager()

    def test_register_event_from_verb(self):
        """Events from verb specs are registered."""
        vocabulary = {
            "verbs": [
                {"word": "take", "event": "on_take", "synonyms": ["get"]}
            ]
        }
        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        self.assertTrue(self.manager.has_event("on_take"))
        events = self.manager.get_registered_events()
        self.assertIn("on_take", events)

    def test_register_event_from_events_section(self):
        """Events from explicit events section are registered."""
        vocabulary = {
            "events": [
                {"event": "on_enter", "description": "Called when entering"}
            ]
        }
        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        self.assertTrue(self.manager.has_event("on_enter"))
        info = self.manager.get_event_info("on_enter")
        self.assertIsNotNone(info)
        self.assertEqual(info.event_name, "on_enter")
        self.assertEqual(info.description, "Called when entering")

    def test_event_tracks_registering_modules(self):
        """Event info tracks which modules registered it."""
        vocabulary1 = {"verbs": [{"word": "take", "event": "on_take"}]}
        vocabulary2 = {"verbs": [{"word": "grab", "event": "on_take"}]}

        self.manager._register_vocabulary(vocabulary1, "module1", tier=1)
        self.manager._register_vocabulary(vocabulary2, "module2", tier=2)

        info = self.manager.get_event_info("on_take")
        self.assertIn("module1", info.registered_by)
        self.assertIn("module2", info.registered_by)

    def test_first_description_wins(self):
        """First registered description is kept."""
        vocabulary1 = {
            "events": [{"event": "on_enter", "description": "First description"}]
        }
        vocabulary2 = {
            "events": [{"event": "on_enter", "description": "Second description"}]
        }

        self.manager._register_vocabulary(vocabulary1, "module1", tier=1)
        self.manager._register_vocabulary(vocabulary2, "module2", tier=2)

        info = self.manager.get_event_info("on_enter")
        self.assertEqual(info.description, "First description")

    def test_get_event_info_returns_none_for_unknown(self):
        """get_event_info returns None for unregistered events."""
        info = self.manager.get_event_info("on_unknown")
        self.assertIsNone(info)

    def test_has_event_returns_false_for_unknown(self):
        """has_event returns False for unregistered events."""
        self.assertFalse(self.manager.has_event("on_unknown"))


class TestEventFallbacks(unittest.TestCase):
    """Test event fallback functionality."""

    def setUp(self):
        self.manager = BehaviorManager()

    def test_register_fallback_event(self):
        """fallback_event in verb spec is registered."""
        vocabulary = {
            "verbs": [
                {"word": "put", "event": "on_put", "fallback_event": "on_drop"},
                {"word": "drop", "event": "on_drop"}
            ]
        }
        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        fallback = self.manager.get_fallback_event("on_put")
        self.assertEqual(fallback, "on_drop")

    def test_no_fallback_returns_none(self):
        """get_fallback_event returns None when no fallback registered."""
        vocabulary = {
            "verbs": [{"word": "take", "event": "on_take"}]
        }
        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        fallback = self.manager.get_fallback_event("on_take")
        self.assertIsNone(fallback)


class TestHookRegistration(unittest.TestCase):
    """Test hook registration and lookup."""

    def setUp(self):
        self.manager = BehaviorManager()

    def test_register_hook(self):
        """Events with hooks are registered in hook mapping."""
        vocabulary = {
            "events": [
                {"event": "on_enter", "hook": "location_entered"}
            ]
        }
        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        event = self.manager.get_event_for_hook("location_entered")
        self.assertEqual(event, "on_enter")

    def test_get_hooks_returns_all_hooks(self):
        """get_hooks returns all registered hook names."""
        vocabulary = {
            "events": [
                {"event": "on_enter", "hook": "location_entered"},
                {"event": "on_observe", "hook": "visibility_check"}
            ]
        }
        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        hooks = self.manager.get_hooks()
        self.assertIn("location_entered", hooks)
        self.assertIn("visibility_check", hooks)

    def test_unregistered_hook_returns_none(self):
        """get_event_for_hook returns None for unregistered hooks."""
        event = self.manager.get_event_for_hook("unknown_hook")
        self.assertIsNone(event)


class TestHookConflicts(unittest.TestCase):
    """Test hook conflict detection and tier-based resolution."""

    def setUp(self):
        self.manager = BehaviorManager()

    def test_same_hook_same_event_allowed(self):
        """Same hook with same event from multiple modules is allowed."""
        vocabulary1 = {
            "events": [{"event": "on_enter", "hook": "location_entered"}]
        }
        vocabulary2 = {
            "events": [{"event": "on_enter", "hook": "location_entered"}]
        }

        self.manager._register_vocabulary(vocabulary1, "module1", tier=1)
        # Should not raise
        self.manager._register_vocabulary(vocabulary2, "module2", tier=2)

        event = self.manager.get_event_for_hook("location_entered")
        self.assertEqual(event, "on_enter")

    def test_same_hook_different_event_same_tier_errors(self):
        """Same hook with different events at same tier raises error."""
        vocabulary1 = {
            "events": [{"event": "on_enter", "hook": "location_entered"}]
        }
        vocabulary2 = {
            "events": [{"event": "on_arrive", "hook": "location_entered"}]
        }

        self.manager._register_vocabulary(vocabulary1, "module1", tier=2)

        with self.assertRaises(ValueError) as cm:
            self.manager._register_vocabulary(vocabulary2, "module2", tier=2)

        error_msg = str(cm.exception)
        self.assertIn("location_entered", error_msg)
        self.assertIn("conflict", error_msg.lower())

    def test_higher_precedence_tier_wins(self):
        """Lower tier number (higher precedence) wins hook mapping."""
        # Register tier 2 first
        vocabulary2 = {
            "events": [{"event": "on_enter_basic", "hook": "location_entered"}]
        }
        self.manager._register_vocabulary(vocabulary2, "library", tier=2)

        # Then register tier 1 (higher precedence)
        vocabulary1 = {
            "events": [{"event": "on_enter_fancy", "hook": "location_entered"}]
        }
        self.manager._register_vocabulary(vocabulary1, "game", tier=1)

        # Tier 1 should win
        event = self.manager.get_event_for_hook("location_entered")
        self.assertEqual(event, "on_enter_fancy")

    def test_lower_precedence_tier_does_not_override(self):
        """Higher tier number (lower precedence) does not override."""
        # Register tier 1 first
        vocabulary1 = {
            "events": [{"event": "on_enter_fancy", "hook": "location_entered"}]
        }
        self.manager._register_vocabulary(vocabulary1, "game", tier=1)

        # Then register tier 2 (lower precedence)
        vocabulary2 = {
            "events": [{"event": "on_enter_basic", "hook": "location_entered"}]
        }
        self.manager._register_vocabulary(vocabulary2, "library", tier=2)

        # Tier 1 should still be active
        event = self.manager.get_event_for_hook("location_entered")
        self.assertEqual(event, "on_enter_fancy")


class TestEventInfoDataclass(unittest.TestCase):
    """Test EventInfo dataclass."""

    def test_eventinfo_creation(self):
        """EventInfo can be created with all fields."""
        info = EventInfo(
            event_name="on_take",
            registered_by=["module1", "module2"],
            description="Take an item",
            hook="item_taken"
        )
        self.assertEqual(info.event_name, "on_take")
        self.assertEqual(info.registered_by, ["module1", "module2"])
        self.assertEqual(info.description, "Take an item")
        self.assertEqual(info.hook, "item_taken")

    def test_eventinfo_optional_fields(self):
        """EventInfo works with optional fields as None."""
        info = EventInfo(
            event_name="on_take",
            registered_by=["module1"]
        )
        self.assertIsNone(info.description)
        self.assertIsNone(info.hook)


class TestValidateOnPrefixUsage(unittest.TestCase):
    """Test the on_* prefix validation."""

    def setUp(self):
        self.manager = BehaviorManager()

    def test_valid_on_function_passes(self):
        """Module with on_* function for registered event passes."""
        # Register event
        vocabulary = {"verbs": [{"word": "take", "event": "on_take"}]}
        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        # Create module with matching on_take function
        mock_module = ModuleType("test_module")
        mock_module.on_take = lambda entity, accessor, context: None
        self.manager._modules["test_module"] = mock_module

        # Should not raise
        self.manager.validate_on_prefix_usage()

    def test_unregistered_on_function_fails(self):
        """Module with on_* function for unregistered event fails."""
        # Don't register any events

        # Create module with on_* function
        mock_module = ModuleType("test_module")
        mock_module.on_unregistered = lambda entity, accessor, context: None
        self.manager._modules["test_module"] = mock_module

        with self.assertRaises(ValueError) as context:
            self.manager.validate_on_prefix_usage()

        self.assertIn("on_unregistered", str(context.exception))
        self.assertIn("test_module", str(context.exception))
        self.assertIn("not registered", str(context.exception))

    def test_typo_in_event_name_caught(self):
        """Typo like on_tke instead of on_take is caught."""
        # Register correct event
        vocabulary = {"verbs": [{"word": "take", "event": "on_take"}]}
        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        # Create module with typo
        mock_module = ModuleType("test_module")
        mock_module.on_tke = lambda entity, accessor, context: None  # Typo!
        self.manager._modules["test_module"] = mock_module

        with self.assertRaises(ValueError) as context:
            self.manager.validate_on_prefix_usage()

        self.assertIn("on_tke", str(context.exception))

    def test_non_on_functions_ignored(self):
        """Functions not starting with on_ are ignored."""
        # No events registered

        # Create module with regular functions
        mock_module = ModuleType("test_module")
        mock_module.handle_take = lambda accessor, action: None
        mock_module.helper_function = lambda: None
        self.manager._modules["test_module"] = mock_module

        # Should not raise (no on_* functions to validate)
        self.manager.validate_on_prefix_usage()

    def test_multiple_modules_validated(self):
        """All loaded modules are validated."""
        # Register one event
        vocabulary = {"verbs": [{"word": "take", "event": "on_take"}]}
        self.manager._register_vocabulary(vocabulary, "module1", tier=1)

        # Module 1: valid on_take
        mock_module1 = ModuleType("module1")
        mock_module1.on_take = lambda entity, accessor, context: None
        self.manager._modules["module1"] = mock_module1

        # Module 2: invalid on_invalid
        mock_module2 = ModuleType("module2")
        mock_module2.on_invalid = lambda entity, accessor, context: None
        self.manager._modules["module2"] = mock_module2

        with self.assertRaises(ValueError) as context:
            self.manager.validate_on_prefix_usage()

        self.assertIn("module2", str(context.exception))
        self.assertIn("on_invalid", str(context.exception))

    def test_non_callable_on_attrs_ignored(self):
        """Non-callable attributes starting with on_ are ignored."""
        # Create module with non-callable on_* attribute
        mock_module = ModuleType("test_module")
        mock_module.on_some_value = "not a function"
        self.manager._modules["test_module"] = mock_module

        # Should not raise (non-callable ignored)
        self.manager.validate_on_prefix_usage()


if __name__ == '__main__':
    unittest.main()
