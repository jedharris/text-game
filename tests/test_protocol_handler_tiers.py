"""Tests for protocol handler tier system."""

import unittest
from unittest.mock import Mock
from src.behavior_manager import BehaviorManager
from src.state_accessor import HandlerResult


class TestProtocolHandlerTierStorage(unittest.TestCase):
    """Test storing and retrieving protocol handlers with tiers."""

    def setUp(self):
        self.manager = BehaviorManager()

    def test_register_handler_stores_tier(self):
        """Registering a handler stores tier along with handler."""
        verb = "take"
        tier = 2
        module_name = "test_module"

        def mock_handler(accessor, action):
            return HandlerResult(success=True, message="Test")

        # Register handler with tier
        self.manager._register_handler(verb, mock_handler, module_name, tier)

        # Check internal structure
        handlers = self.manager._handlers.get(verb)
        self.assertIsNotNone(handlers, "Should have handlers for verb")
        self.assertEqual(len(handlers), 1, "Should have one handler")
        self.assertEqual(handlers[0][0], tier, "Should store tier as first element")
        self.assertEqual(handlers[0][1], mock_handler, "Should store handler as second element")
        self.assertEqual(handlers[0][2], module_name, "Should store module name as third element")

    def test_register_handler_within_tier_conflict(self):
        """Registering same verb+tier with different handler raises error."""
        verb = "take"
        tier = 2
        module1 = "module1"
        module2 = "module2"

        def handler1(accessor, action):
            return HandlerResult(success=True, message="Handler 1")

        def handler2(accessor, action):
            return HandlerResult(success=True, message="Handler 2")

        # Register first handler
        self.manager._register_handler(verb, handler1, module1, tier)

        # Attempt to register conflicting handler (same verb+tier, different module)
        with self.assertRaises(ValueError) as cm:
            self.manager._register_handler(verb, handler2, module2, tier)

        error_msg = str(cm.exception)
        self.assertIn("take", error_msg, "Error should mention verb")
        self.assertIn("Tier 2", error_msg, "Error should mention tier")
        self.assertIn("conflict", error_msg.lower(), "Error should mention conflict")

    def test_register_handler_same_module_same_tier_allowed(self):
        """Registering same verb+tier+module is allowed (no error)."""
        verb = "take"
        tier = 2
        module_name = "test_module"

        def handler(accessor, action):
            return HandlerResult(success=True, message="Test")

        # Register first time
        self.manager._register_handler(verb, handler, module_name, tier)

        # Register same handler again (should not raise)
        self.manager._register_handler(verb, handler, module_name, tier)

        # Should only store once (no duplicates)
        handlers = self.manager._handlers.get(verb)
        self.assertEqual(len(handlers), 1, "Should not create duplicate entries")

    def test_register_handler_cross_tier_allowed(self):
        """Registering same verb in different tiers is allowed."""
        verb = "take"
        module1 = "module1"
        module2 = "module2"

        def handler1(accessor, action):
            return HandlerResult(success=True, message="Handler 1")

        def handler2(accessor, action):
            return HandlerResult(success=True, message="Handler 2")

        # Register in Tier 1
        self.manager._register_handler(verb, handler1, module1, tier=1)

        # Register in Tier 2 (should not raise)
        self.manager._register_handler(verb, handler2, module2, tier=2)

        # Should have both handlers
        handlers = self.manager._handlers.get(verb)
        self.assertEqual(len(handlers), 2, "Should have handlers from both tiers")

    def test_handlers_sorted_by_tier(self):
        """Handlers are stored sorted by tier (lowest first)."""
        verb = "take"

        def handler1(accessor, action):
            return HandlerResult(success=True, message="Tier 1")

        def handler2(accessor, action):
            return HandlerResult(success=True, message="Tier 2")

        def handler3(accessor, action):
            return HandlerResult(success=True, message="Tier 3")

        # Register in different order (Tier 3, then Tier 1, then Tier 2)
        self.manager._register_handler(verb, handler3, "module3", tier=3)
        self.manager._register_handler(verb, handler1, "module1", tier=1)
        self.manager._register_handler(verb, handler2, "module2", tier=2)

        # Get handlers
        handlers = self.manager._handlers.get(verb)

        # Should be sorted by tier (lowest/highest precedence first)
        self.assertEqual(len(handlers), 3, "Should have all three handlers")
        self.assertEqual(handlers[0][0], 1, "Tier 1 should be first")
        self.assertEqual(handlers[1][0], 2, "Tier 2 should be second")
        self.assertEqual(handlers[2][0], 3, "Tier 3 should be third")


class TestProtocolHandlerInvocation(unittest.TestCase):
    """Test invoking protocol handlers in tier order."""

    def setUp(self):
        self.manager = BehaviorManager()
        self.accessor = Mock()

    def test_invoke_handler_tier1_success_stops(self):
        """Tier 1 handler succeeds, doesn't try Tier 2."""
        verb = "take"

        def tier1_handler(accessor, action):
            return HandlerResult(success=True, message="Tier 1 success")

        def tier2_handler(accessor, action):
            # Should not be called
            raise AssertionError("Tier 2 should not be invoked")

        # Register both tiers
        self.manager._register_handler(verb, tier1_handler, "module1", tier=1)
        self.manager._register_handler(verb, tier2_handler, "module2", tier=2)

        # Invoke handler
        result = self.manager.invoke_handler(verb, self.accessor, {})

        # Should get Tier 1 result
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Tier 1 success")

    def test_invoke_handler_tier1_fails_tries_tier2(self):
        """Tier 1 handler fails, tries Tier 2."""
        verb = "take"

        def tier1_handler(accessor, action):
            return HandlerResult(success=False, message="Tier 1 failed")

        def tier2_handler(accessor, action):
            return HandlerResult(success=True, message="Tier 2 success")

        # Register both tiers
        self.manager._register_handler(verb, tier1_handler, "module1", tier=1)
        self.manager._register_handler(verb, tier2_handler, "module2", tier=2)

        # Invoke handler
        result = self.manager.invoke_handler(verb, self.accessor, {})

        # Should get Tier 2 result (Tier 1 failed)
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Tier 2 success")

    def test_invoke_handler_all_tiers_fail(self):
        """All tiers fail, returns last result."""
        verb = "take"

        def tier1_handler(accessor, action):
            return HandlerResult(success=False, message="Tier 1 failed")

        def tier2_handler(accessor, action):
            return HandlerResult(success=False, message="Tier 2 failed")

        # Register both tiers
        self.manager._register_handler(verb, tier1_handler, "module1", tier=1)
        self.manager._register_handler(verb, tier2_handler, "module2", tier=2)

        # Invoke handler
        result = self.manager.invoke_handler(verb, self.accessor, {})

        # Should get Tier 2 result (last one tried)
        self.assertIsNotNone(result)
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Tier 2 failed")

    def test_invoke_handler_no_handler_returns_none(self):
        """No handler registered, returns None."""
        result = self.manager.invoke_handler("unknown_verb", self.accessor, {})
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
