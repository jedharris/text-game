"""
Tests for Phase 1/2.5: Hook definition storage in BehaviorManager.

Tests the basic infrastructure for storing hook definitions loaded from
behavior module vocabularies, including typed hook IDs (Phase 2.5).
"""

import unittest
from src.behavior_manager import BehaviorManager, HookDefinition
from src.types import TurnHookId, EntityHookId


class TestHookDefinitionStorage(unittest.TestCase):
    """Test Phase 1: Hook definition storage in BehaviorManager."""

    def setUp(self):
        """Create a fresh BehaviorManager for each test."""
        self.manager = BehaviorManager()

    def test_register_turn_phase_hook(self):
        """Test registering a turn phase hook definition."""
        vocabulary = {
            "hook_definitions": [
                {
                    "hook_id": "turn_environmental_effect",
                    "invocation": "turn_phase",
                    "after": ["turn_npc_action"],
                    "description": "Apply environmental hazards"
                }
            ]
        }

        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        # Verify hook was stored
        self.assertIn("turn_environmental_effect", self.manager._hook_definitions)
        hook_def = self.manager._hook_definitions["turn_environmental_effect"]

        # Verify all fields
        self.assertEqual(hook_def.hook_id, "turn_environmental_effect")
        self.assertEqual(hook_def.invocation, "turn_phase")
        self.assertEqual(hook_def.after, ["turn_npc_action"])
        self.assertEqual(hook_def.description, "Apply environmental hazards")
        self.assertEqual(hook_def.defined_by, "test_module")

    def test_register_entity_hook(self):
        """Test registering an entity hook definition."""
        vocabulary = {
            "hook_definitions": [
                {
                    "hook_id": "entity_entered_location",
                    "invocation": "entity",
                    "description": "Called when an actor enters a new location"
                }
            ]
        }

        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        # Verify hook was stored
        self.assertIn("entity_entered_location", self.manager._hook_definitions)
        hook_def = self.manager._hook_definitions["entity_entered_location"]

        # Verify fields
        self.assertEqual(hook_def.hook_id, "entity_entered_location")
        self.assertEqual(hook_def.invocation, "entity")
        self.assertEqual(hook_def.after, [])  # No dependencies for entity hooks
        self.assertEqual(hook_def.description, "Called when an actor enters a new location")
        self.assertEqual(hook_def.defined_by, "test_module")

    def test_duplicate_hook_different_modules_raises(self):
        """Test that same hook from different modules raises error."""
        vocab_a = {
            "hook_definitions": [
                {
                    "hook_id": "turn_foo",
                    "invocation": "turn_phase"
                }
            ]
        }

        vocab_b = {
            "hook_definitions": [
                {
                    "hook_id": "turn_foo",
                    "invocation": "turn_phase"
                }
            ]
        }

        # First registration should succeed
        self.manager._register_vocabulary(vocab_a, "module_a", tier=1)

        # Second registration from different module should raise
        with self.assertRaises(ValueError) as cm:
            self.manager._register_vocabulary(vocab_b, "module_b", tier=1)

        error_msg = str(cm.exception)
        self.assertIn("turn_foo", error_msg)
        self.assertIn("defined multiple times", error_msg)
        self.assertIn("module_a", error_msg)
        self.assertIn("module_b", error_msg)

    def test_duplicate_hook_same_module_allowed(self):
        """Test that same hook from same module is idempotent."""
        vocabulary = {
            "hook_definitions": [
                {
                    "hook_id": "turn_foo",
                    "invocation": "turn_phase",
                    "after": [],
                    "description": "First definition"
                }
            ]
        }

        # First registration
        self.manager._register_vocabulary(vocabulary, "module_a", tier=1)
        first_def = self.manager._hook_definitions["turn_foo"]

        # Second registration from same module
        self.manager._register_vocabulary(vocabulary, "module_a", tier=1)
        second_def = self.manager._hook_definitions["turn_foo"]

        # Should be the same object (first definition wins)
        self.assertIs(first_def, second_def)
        self.assertEqual(second_def.description, "First definition")

    def test_hook_with_dependencies(self):
        """Test storing hook with 'after' dependencies."""
        vocabulary = {
            "hook_definitions": [
                {
                    "hook_id": "turn_condition_tick",
                    "invocation": "turn_phase",
                    "after": ["turn_environmental_effect", "turn_npc_action"],
                    "description": "Update conditions on actors"
                }
            ]
        }

        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        hook_def = self.manager._hook_definitions["turn_condition_tick"]
        self.assertEqual(hook_def.after, ["turn_environmental_effect", "turn_npc_action"])

    def test_hook_with_empty_dependencies(self):
        """Test that omitted 'after' field defaults to empty list."""
        vocabulary = {
            "hook_definitions": [
                {
                    "hook_id": "turn_first_phase",
                    "invocation": "turn_phase"
                    # No 'after' field
                }
            ]
        }

        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        hook_def = self.manager._hook_definitions["turn_first_phase"]
        self.assertEqual(hook_def.after, [])

    def test_hook_with_empty_description(self):
        """Test that omitted 'description' field defaults to empty string."""
        vocabulary = {
            "hook_definitions": [
                {
                    "hook_id": "entity_custom_hook",
                    "invocation": "entity"
                    # No 'description' field
                }
            ]
        }

        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        hook_def = self.manager._hook_definitions["entity_custom_hook"]
        self.assertEqual(hook_def.description, "")

    def test_multiple_hooks_from_same_vocabulary(self):
        """Test registering multiple hooks from one vocabulary."""
        vocabulary = {
            "hook_definitions": [
                {
                    "hook_id": "turn_phase_one",
                    "invocation": "turn_phase",
                    "after": []
                },
                {
                    "hook_id": "turn_phase_two",
                    "invocation": "turn_phase",
                    "after": ["turn_phase_one"]
                },
                {
                    "hook_id": "entity_custom",
                    "invocation": "entity"
                }
            ]
        }

        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        # Verify all three hooks stored
        self.assertEqual(len(self.manager._hook_definitions), 3)
        self.assertIn("turn_phase_one", self.manager._hook_definitions)
        self.assertIn("turn_phase_two", self.manager._hook_definitions)
        self.assertIn("entity_custom", self.manager._hook_definitions)

    def test_vocabulary_without_hook_definitions(self):
        """Test that vocabularies without hook_definitions work normally."""
        vocabulary = {
            "verbs": [
                {
                    "word": "test",
                    "event": "on_test"
                }
            ],
            "events": [
                {
                    "event": "on_test"
                }
            ]
            # No hook_definitions
        }

        # Should not raise
        self.manager._register_vocabulary(vocabulary, "test_module", tier=1)

        # No hooks should be registered
        self.assertEqual(len(self.manager._hook_definitions), 0)

    def test_hook_definition_dataclass_fields(self):
        """Test that HookDefinition dataclass has correct fields (Phase 2.5: typed IDs)."""
        hook_def = HookDefinition(
            hook_id=EntityHookId("entity_test_hook"),
            invocation="entity",
            after=[TurnHookId("turn_other_hook")],
            description="Test description",
            defined_by="test_module"
        )

        self.assertEqual(hook_def.hook_id, EntityHookId("entity_test_hook"))
        self.assertEqual(hook_def.invocation, "entity")
        self.assertEqual(hook_def.after, [TurnHookId("turn_other_hook")])
        self.assertEqual(hook_def.description, "Test description")
        self.assertEqual(hook_def.defined_by, "test_module")


if __name__ == '__main__':
    unittest.main()
