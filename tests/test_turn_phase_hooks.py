"""Tests for turn phase hook system (Phase 0 of Actor Interaction)."""

import unittest
from unittest.mock import Mock, MagicMock, patch, call

from src import hooks
from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager
from src.state_accessor import HandlerResult


class TestTurnPhaseHookConstants(unittest.TestCase):
    """Test that all turn phase hook constants exist."""

    def test_npc_action_hook_exists(self):
        """NPC_ACTION hook constant is defined."""
        self.assertTrue(hasattr(hooks, 'NPC_ACTION'))
        self.assertEqual(hooks.NPC_ACTION, "npc_action")

    def test_environmental_effect_hook_exists(self):
        """ENVIRONMENTAL_EFFECT hook constant is defined."""
        self.assertTrue(hasattr(hooks, 'ENVIRONMENTAL_EFFECT'))
        self.assertEqual(hooks.ENVIRONMENTAL_EFFECT, "environmental_effect")

    def test_condition_tick_hook_exists(self):
        """CONDITION_TICK hook constant is defined."""
        self.assertTrue(hasattr(hooks, 'CONDITION_TICK'))
        self.assertEqual(hooks.CONDITION_TICK, "condition_tick")

    def test_death_check_hook_exists(self):
        """DEATH_CHECK hook constant is defined."""
        self.assertTrue(hasattr(hooks, 'DEATH_CHECK'))
        self.assertEqual(hooks.DEATH_CHECK, "death_check")

    def test_all_turn_phase_hooks_are_unique(self):
        """All turn phase hook values are unique strings."""
        turn_phase_hooks = [
            hooks.NPC_ACTION,
            hooks.ENVIRONMENTAL_EFFECT,
            hooks.CONDITION_TICK,
            hooks.DEATH_CHECK,
        ]
        # All should be strings
        for hook in turn_phase_hooks:
            self.assertIsInstance(hook, str)
        # All should be unique
        self.assertEqual(len(turn_phase_hooks), len(set(turn_phase_hooks)))


class TestTurnPhaseFiring(unittest.TestCase):
    """Test that turn phases fire after successful commands."""

    def setUp(self):
        """Set up test fixtures with mocked state and behavior manager."""
        # Create mock state
        self.mock_state = Mock()
        self.mock_state.actors = {"player": Mock(location="loc_test")}
        self.mock_state.items = []
        self.mock_state.locations = []
        self.mock_state.locks = []
        # Mock metadata with extra_turn_phases (empty by default)
        self.mock_state.metadata = Mock()
        self.mock_state.metadata.extra_turn_phases = []

        # Create mock behavior manager
        self.mock_behavior_manager = Mock(spec=BehaviorManager)
        self.mock_behavior_manager.has_handler.return_value = True
        self.mock_behavior_manager.invoke_handler.return_value = HandlerResult(
            success=True, primary="Action succeeded"
        )
        # No events registered for hooks by default
        self.mock_behavior_manager.get_event_for_hook.return_value = None

        # Create handler
        self.handler = LLMProtocolHandler(
            self.mock_state,
            self.mock_behavior_manager
        )

    def test_turn_phases_fire_on_success(self):
        """Turn phase hooks are checked after successful command."""
        # Execute a successful command
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "look"}
        })

        self.assertTrue(result["success"])

        # Verify get_event_for_hook was called for each turn phase hook
        hook_calls = [
            call(hooks.NPC_ACTION),
            call(hooks.ENVIRONMENTAL_EFFECT),
            call(hooks.CONDITION_TICK),
            call(hooks.DEATH_CHECK),
        ]
        self.mock_behavior_manager.get_event_for_hook.assert_has_calls(
            hook_calls, any_order=False
        )

    def test_turn_phases_skip_on_failure(self):
        """Turn phase hooks do NOT fire after failed command."""
        # Make the command fail
        self.mock_behavior_manager.invoke_handler.return_value = HandlerResult(
            success=False, primary="Action failed"
        )

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "nonexistent"}
        })

        self.assertFalse(result["success"])

        # get_event_for_hook should NOT be called for turn phases
        self.mock_behavior_manager.get_event_for_hook.assert_not_called()

    def test_turn_phase_order(self):
        """Turn phases fire in correct order: NPC_ACTION, ENVIRONMENTAL_EFFECT, CONDITION_TICK, DEATH_CHECK."""
        # Track order of hook calls
        hook_call_order = []

        def track_hook_call(hook_name):
            hook_call_order.append(hook_name)
            return None  # No event registered

        self.mock_behavior_manager.get_event_for_hook.side_effect = track_hook_call

        # Execute successful command
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "look"}
        })

        # Verify order
        expected_order = [
            hooks.NPC_ACTION,
            hooks.ENVIRONMENTAL_EFFECT,
            hooks.CONDITION_TICK,
            hooks.DEATH_CHECK,
        ]
        self.assertEqual(hook_call_order, expected_order)

    def test_turn_phase_invokes_registered_event(self):
        """When a hook has a registered event, invoke_behavior is called."""
        # Register an event for NPC_ACTION hook
        def get_event(hook_name):
            if hook_name == hooks.NPC_ACTION:
                return "npc_take_action"
            return None

        self.mock_behavior_manager.get_event_for_hook.side_effect = get_event
        self.mock_behavior_manager.invoke_behavior.return_value = None

        # Execute successful command
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "look"}
        })

        # Verify get_event_for_hook was called for NPC_ACTION
        self.mock_behavior_manager.get_event_for_hook.assert_any_call(hooks.NPC_ACTION)

        # Verify invoke_behavior was called with the event name
        self.mock_behavior_manager.invoke_behavior.assert_called()
        # Check that one of the calls was for npc_take_action
        call_args = [call[0] for call in self.mock_behavior_manager.invoke_behavior.call_args_list]
        event_names = [args[1] if len(args) > 1 else None for args in call_args]
        self.assertIn("npc_take_action", event_names)

    def test_turn_phase_messages_collected(self):
        """Messages from turn phase handlers are collected and returned."""
        # Register events that produce messages
        def get_event(hook_name):
            if hook_name == hooks.CONDITION_TICK:
                return "on_condition_tick"
            return None

        self.mock_behavior_manager.get_event_for_hook.side_effect = get_event

        # Mock EventResult with message
        mock_event_result = Mock()
        mock_event_result.primary = "Poison deals 2 damage"
        mock_event_result.allow = True
        self.mock_behavior_manager.invoke_behavior.return_value = mock_event_result

        # Execute successful command
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "look"}
        })

        self.assertTrue(result["success"])
        # The turn phase message should be included in the result
        self.assertIn("turn_phase_messages", result)


class TestEffectRegistry(unittest.TestCase):
    """Test effect string registry."""

    def test_all_standard_effects_registered(self):
        """All standard effect constants are in REGISTERED_EFFECTS."""
        from behavior_libraries.actor_lib import effects

        standard_effects = [
            effects.CANNOT_MOVE,
            effects.CANNOT_SWIM,
            effects.SLOWED,
            effects.CANNOT_ATTACK,
            effects.AGILITY_REDUCED,
            effects.STRENGTH_REDUCED,
            effects.BLINDED,
            effects.DEAFENED,
            effects.PARALYSIS,
            effects.ENTANGLED,
            effects.KNOCKDOWN,
        ]

        for effect in standard_effects:
            self.assertIn(effect, effects.REGISTERED_EFFECTS)

    def test_is_valid_effect_valid(self):
        """is_valid_effect returns True for registered effects."""
        from behavior_libraries.actor_lib.effects import is_valid_effect, CANNOT_MOVE

        self.assertTrue(is_valid_effect(CANNOT_MOVE))
        self.assertTrue(is_valid_effect("blinded"))

    def test_is_valid_effect_invalid(self):
        """is_valid_effect returns False for unregistered effects."""
        from behavior_libraries.actor_lib.effects import is_valid_effect

        self.assertFalse(is_valid_effect("flying"))
        self.assertFalse(is_valid_effect("super_strength"))
        self.assertFalse(is_valid_effect(""))

    def test_get_effects_from_actor(self):
        """get_effects returns all effect strings from actor conditions."""
        from behavior_libraries.actor_lib.effects import get_effects

        mock_actor = Mock()
        mock_actor.properties = {
            "conditions": {
                "poison": {"severity": 50, "effect": "agility_reduced"},
                "web": {"severity": 30, "effect": "cannot_move"},
                "fear": {"severity": 20}  # No effect
            }
        }

        effects_list = get_effects(mock_actor)

        self.assertEqual(len(effects_list), 2)
        self.assertIn("agility_reduced", effects_list)
        self.assertIn("cannot_move", effects_list)

    def test_get_effects_no_conditions(self):
        """get_effects returns empty list for actor with no conditions."""
        from behavior_libraries.actor_lib.effects import get_effects

        mock_actor = Mock()
        mock_actor.properties = {}

        effects_list = get_effects(mock_actor)

        self.assertEqual(effects_list, [])

    def test_get_effects_none_actor(self):
        """get_effects returns empty list for None actor."""
        from behavior_libraries.actor_lib.effects import get_effects

        effects_list = get_effects(None)

        self.assertEqual(effects_list, [])

    def test_has_effect_true(self):
        """has_effect returns True when actor has the effect."""
        from behavior_libraries.actor_lib.effects import has_effect

        mock_actor = Mock()
        mock_actor.properties = {
            "conditions": {
                "poison": {"effect": "cannot_move"}
            }
        }

        self.assertTrue(has_effect(mock_actor, "cannot_move"))

    def test_has_effect_false(self):
        """has_effect returns False when actor doesn't have the effect."""
        from behavior_libraries.actor_lib.effects import has_effect

        mock_actor = Mock()
        mock_actor.properties = {
            "conditions": {
                "poison": {"effect": "cannot_move"}
            }
        }

        self.assertFalse(has_effect(mock_actor, "blinded"))

    def test_validate_condition_effects_valid(self):
        """validate_condition_effects returns None for valid effects."""
        from behavior_libraries.actor_lib.effects import validate_condition_effects

        conditions = {
            "poison": {"effect": "agility_reduced"},
            "web": {"effect": "cannot_move"}
        }

        result = validate_condition_effects(conditions)

        self.assertIsNone(result)

    def test_validate_condition_effects_invalid(self):
        """validate_condition_effects returns error for invalid effects."""
        from behavior_libraries.actor_lib.effects import validate_condition_effects

        conditions = {
            "poison": {"effect": "agility_reduced"},
            "magic": {"effect": "flying"}  # Invalid
        }

        result = validate_condition_effects(conditions)

        self.assertIsNotNone(result)
        self.assertIn("flying", result)
        self.assertIn("magic", result)

    def test_vocabulary_has_effects_section(self):
        """Module exports vocabulary with effects documentation."""
        from behavior_libraries.actor_lib.effects import vocabulary

        self.assertIn("effects", vocabulary)
        self.assertTrue(len(vocabulary["effects"]) > 0)

        # Each effect should have effect and description
        for effect_doc in vocabulary["effects"]:
            self.assertIn("effect", effect_doc)
            self.assertIn("description", effect_doc)


class TestGetActorPart(unittest.TestCase):
    """Test StateAccessor.get_actor_part() method."""

    def setUp(self):
        """Set up test fixtures with actors and parts."""
        from src.state_manager import GameState, Metadata, Location, Actor, Part

        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Room",
            description="A test room"
        )

        # A spatial location with parts
        self.spatial_location = Location(
            id="loc_gallery",
            name="Gallery",
            description="A gallery with walls",
            properties={"default_part": "part_gallery_center"}
        )

        self.part_center = Part(
            id="part_gallery_center",
            name="center of gallery",
            part_of="loc_gallery"
        )

        self.part_north_wall = Part(
            id="part_gallery_north_wall",
            name="north wall",
            part_of="loc_gallery"
        )

        # Player in non-spatial location
        self.player = Actor(
            id="player",
            name="Player",
            description="The player",
            location="loc_room",
            inventory=[]
        )

        # NPC in spatial location focused on a part
        self.npc = Actor(
            id="npc_guard",
            name="Guard",
            description="A guard",
            location="loc_gallery",
            inventory=[],
            properties={"focused_on": "part_gallery_north_wall"}
        )

        # NPC in spatial location without focus
        self.npc2 = Actor(
            id="npc_visitor",
            name="Visitor",
            description="A visitor",
            location="loc_gallery",
            inventory=[]
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location, self.spatial_location],
            items=[],
            actors={
                "player": self.player,
                "npc_guard": self.npc,
                "npc_visitor": self.npc2
            },
            locks=[],
            parts=[self.part_center, self.part_north_wall]
        )

        self.behavior_manager = None  # Not needed for these tests
        from src.state_accessor import StateAccessor
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_get_actor_part_focused(self):
        """Returns the part the actor is focused on."""
        part = self.accessor.get_actor_part(self.npc)

        self.assertIsNotNone(part)
        self.assertEqual(part.id, "part_gallery_north_wall")

    def test_get_actor_part_default(self):
        """Returns default part when actor has no focus in spatial location."""
        part = self.accessor.get_actor_part(self.npc2)

        self.assertIsNotNone(part)
        self.assertEqual(part.id, "part_gallery_center")

    def test_get_actor_part_non_spatial_location(self):
        """Returns None for actor in non-spatial location."""
        part = self.accessor.get_actor_part(self.player)

        self.assertIsNone(part)

    def test_get_actor_part_none_actor(self):
        """Returns None when actor is None."""
        part = self.accessor.get_actor_part(None)

        self.assertIsNone(part)

    def test_get_actor_part_focused_on_non_part(self):
        """Returns default part if focused on non-part entity."""
        # Focus on an item instead of a part
        self.npc.properties["focused_on"] = "item_nonexistent"

        part = self.accessor.get_actor_part(self.npc)

        # Should fall back to default part
        self.assertIsNotNone(part)
        self.assertEqual(part.id, "part_gallery_center")


if __name__ == '__main__':
    unittest.main()
