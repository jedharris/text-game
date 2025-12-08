"""Tests for the condition system (Phase 1 of Actor Interaction)."""

import unittest
from unittest.mock import Mock

from src.state_manager import Actor


class TestApplyCondition(unittest.TestCase):
    """Test apply_condition function."""

    def setUp(self):
        """Create a test actor."""
        self.actor = Actor(
            id="player",
            name="Player",
            description="Test player",
            location="loc_test",
            inventory=[],
            properties={"health": 100, "max_health": 100}
        )

    def test_apply_condition_new(self):
        """Apply a new condition to an actor."""
        from behaviors.library.actors.conditions import apply_condition

        message = apply_condition(self.actor, "poison", {
            "severity": 50,
            "damage_per_turn": 2,
            "effect": "agility_reduced"
        })

        self.assertIn("conditions", self.actor.properties)
        self.assertIn("poison", self.actor.properties["conditions"])
        self.assertEqual(self.actor.properties["conditions"]["poison"]["severity"], 50)
        self.assertIn("poison", message.lower())

    def test_apply_condition_stack(self):
        """Applying existing condition increases severity."""
        from behaviors.library.actors.conditions import apply_condition

        # Apply first time
        apply_condition(self.actor, "poison", {"severity": 30})

        # Apply second time - severity should stack
        apply_condition(self.actor, "poison", {"severity": 20})

        self.assertEqual(self.actor.properties["conditions"]["poison"]["severity"], 50)

    def test_apply_condition_immune_array(self):
        """Actor with immunity in array rejects condition."""
        from behaviors.library.actors.conditions import apply_condition

        self.actor.properties["immunities"] = ["poison", "disease"]

        message = apply_condition(self.actor, "poison", {"severity": 50})

        # Condition should not be applied
        conditions = self.actor.properties.get("conditions", {})
        self.assertNotIn("poison", conditions)
        self.assertIn("immune", message.lower())

    def test_apply_condition_immune_construct(self):
        """Constructs are immune to disease and poison."""
        from behaviors.library.actors.conditions import apply_condition

        self.actor.properties["body"] = {"form": "construct"}

        message = apply_condition(self.actor, "disease", {"severity": 50})

        conditions = self.actor.properties.get("conditions", {})
        self.assertNotIn("disease", conditions)
        self.assertIn("immune", message.lower())

    def test_apply_condition_preserves_other_fields(self):
        """Stacking preserves non-severity fields from original."""
        from behaviors.library.actors.conditions import apply_condition

        apply_condition(self.actor, "poison", {
            "severity": 30,
            "damage_per_turn": 2,
            "duration": 10,
            "effect": "agility_reduced"
        })

        # Stack more severity
        apply_condition(self.actor, "poison", {"severity": 20})

        condition = self.actor.properties["conditions"]["poison"]
        self.assertEqual(condition["severity"], 50)
        self.assertEqual(condition["damage_per_turn"], 2)
        self.assertEqual(condition["duration"], 10)
        self.assertEqual(condition["effect"], "agility_reduced")


class TestTickConditions(unittest.TestCase):
    """Test tick_conditions function."""

    def setUp(self):
        """Create a test actor with conditions."""
        self.actor = Actor(
            id="player",
            name="Player",
            description="Test player",
            location="loc_test",
            inventory=[],
            properties={
                "health": 100,
                "max_health": 100,
                "conditions": {}
            }
        )

    def test_tick_conditions_damage(self):
        """Damage per turn is applied to health."""
        from behaviors.library.actors.conditions import tick_conditions

        self.actor.properties["conditions"]["poison"] = {
            "severity": 50,
            "damage_per_turn": 5
        }

        messages = tick_conditions(self.actor)

        self.assertEqual(self.actor.properties["health"], 95)
        self.assertTrue(len(messages) > 0)

    def test_tick_conditions_duration_decrements(self):
        """Duration decrements each tick."""
        from behaviors.library.actors.conditions import tick_conditions

        self.actor.properties["conditions"]["stun"] = {
            "severity": 30,
            "duration": 3
        }

        tick_conditions(self.actor)

        self.assertEqual(self.actor.properties["conditions"]["stun"]["duration"], 2)

    def test_tick_conditions_duration_removes(self):
        """Condition removed when duration reaches zero."""
        from behaviors.library.actors.conditions import tick_conditions

        self.actor.properties["conditions"]["stun"] = {
            "severity": 30,
            "duration": 1
        }

        messages = tick_conditions(self.actor)

        self.assertNotIn("stun", self.actor.properties["conditions"])
        # Should have message about condition ending
        self.assertTrue(any("stun" in m.lower() for m in messages))

    def test_tick_conditions_progression_rate(self):
        """Severity increases by progression_rate."""
        from behaviors.library.actors.conditions import tick_conditions

        self.actor.properties["conditions"]["infection"] = {
            "severity": 20,
            "progression_rate": 5
        }

        tick_conditions(self.actor)

        self.assertEqual(self.actor.properties["conditions"]["infection"]["severity"], 25)

    def test_tick_conditions_no_conditions(self):
        """No error when actor has no conditions."""
        from behaviors.library.actors.conditions import tick_conditions

        self.actor.properties["conditions"] = {}

        messages = tick_conditions(self.actor)

        self.assertEqual(messages, [])

    def test_tick_conditions_multiple(self):
        """Multiple conditions all tick."""
        from behaviors.library.actors.conditions import tick_conditions

        self.actor.properties["conditions"] = {
            "poison": {"severity": 50, "damage_per_turn": 2},
            "bleeding": {"severity": 30, "damage_per_turn": 3}
        }

        tick_conditions(self.actor)

        # 100 - 2 - 3 = 95
        self.assertEqual(self.actor.properties["health"], 95)


class TestTreatCondition(unittest.TestCase):
    """Test treat_condition function."""

    def setUp(self):
        """Create a test actor with a condition."""
        self.actor = Actor(
            id="player",
            name="Player",
            description="Test player",
            location="loc_test",
            inventory=[],
            properties={
                "health": 80,
                "max_health": 100,
                "conditions": {
                    "poison": {"severity": 50, "damage_per_turn": 2}
                }
            }
        )

    def test_treat_condition_reduce(self):
        """Treatment reduces severity."""
        from behaviors.library.actors.conditions import treat_condition

        message = treat_condition(self.actor, "poison", 30)

        self.assertEqual(self.actor.properties["conditions"]["poison"]["severity"], 20)
        self.assertIn("poison", message.lower())

    def test_treat_condition_remove_at_zero(self):
        """Condition removed when severity drops to zero or below."""
        from behaviors.library.actors.conditions import treat_condition

        message = treat_condition(self.actor, "poison", 60)

        self.assertNotIn("poison", self.actor.properties["conditions"])
        self.assertIn("cured", message.lower())

    def test_treat_condition_nonexistent(self):
        """Treating nonexistent condition returns appropriate message."""
        from behaviors.library.actors.conditions import treat_condition

        message = treat_condition(self.actor, "bleeding", 30)

        self.assertIn("not", message.lower())


class TestRemoveCondition(unittest.TestCase):
    """Test remove_condition function."""

    def setUp(self):
        """Create a test actor with a condition."""
        self.actor = Actor(
            id="player",
            name="Player",
            description="Test player",
            location="loc_test",
            inventory=[],
            properties={
                "conditions": {
                    "poison": {"severity": 50}
                }
            }
        )

    def test_remove_condition(self):
        """Condition is completely removed."""
        from behaviors.library.actors.conditions import remove_condition

        message = remove_condition(self.actor, "poison")

        self.assertNotIn("poison", self.actor.properties["conditions"])
        self.assertIn("poison", message.lower())

    def test_remove_condition_nonexistent(self):
        """Removing nonexistent condition is safe."""
        from behaviors.library.actors.conditions import remove_condition

        message = remove_condition(self.actor, "bleeding")

        # Should not raise, should return appropriate message
        self.assertIsNotNone(message)


class TestIsImmune(unittest.TestCase):
    """Test is_immune function."""

    def setUp(self):
        """Create a test actor."""
        self.actor = Actor(
            id="npc_golem",
            name="Stone Golem",
            description="A stone golem",
            location="loc_test",
            inventory=[],
            properties={}
        )

    def test_is_immune_array_match(self):
        """Actor with condition in immunities array is immune."""
        from behaviors.library.actors.conditions import is_immune

        self.actor.properties["immunities"] = ["poison", "disease"]

        self.assertTrue(is_immune(self.actor, "poison"))
        self.assertTrue(is_immune(self.actor, "disease"))
        self.assertFalse(is_immune(self.actor, "bleeding"))

    def test_is_immune_construct_disease(self):
        """Constructs are immune to disease."""
        from behaviors.library.actors.conditions import is_immune

        self.actor.properties["body"] = {"form": "construct"}

        self.assertTrue(is_immune(self.actor, "disease"))

    def test_is_immune_construct_poison(self):
        """Constructs are immune to poison."""
        from behaviors.library.actors.conditions import is_immune

        self.actor.properties["body"] = {"form": "construct"}

        self.assertTrue(is_immune(self.actor, "poison"))

    def test_is_immune_construct_not_bleeding(self):
        """Constructs are NOT immune to bleeding (mechanical damage)."""
        from behaviors.library.actors.conditions import is_immune

        self.actor.properties["body"] = {"form": "construct"}

        self.assertFalse(is_immune(self.actor, "bleeding"))

    def test_is_immune_no_immunities(self):
        """Actor without immunities is not immune."""
        from behaviors.library.actors.conditions import is_immune

        self.assertFalse(is_immune(self.actor, "poison"))

    def test_is_immune_none_actor(self):
        """None actor returns False."""
        from behaviors.library.actors.conditions import is_immune

        self.assertFalse(is_immune(None, "poison"))


class TestGetConditions(unittest.TestCase):
    """Test get_conditions helper function."""

    def test_get_conditions_returns_dict(self):
        """get_conditions returns conditions dict."""
        from behaviors.library.actors.conditions import get_conditions

        actor = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=[],
            properties={"conditions": {"poison": {"severity": 50}}}
        )

        conditions = get_conditions(actor)

        self.assertEqual(conditions, {"poison": {"severity": 50}})

    def test_get_conditions_empty(self):
        """get_conditions returns empty dict when no conditions."""
        from behaviors.library.actors.conditions import get_conditions

        actor = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=[],
            properties={}
        )

        conditions = get_conditions(actor)

        self.assertEqual(conditions, {})

    def test_get_conditions_none_actor(self):
        """get_conditions returns empty dict for None actor."""
        from behaviors.library.actors.conditions import get_conditions

        conditions = get_conditions(None)

        self.assertEqual(conditions, {})


class TestHasCondition(unittest.TestCase):
    """Test has_condition helper function."""

    def test_has_condition_true(self):
        """has_condition returns True when actor has condition."""
        from behaviors.library.actors.conditions import has_condition

        actor = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=[],
            properties={"conditions": {"poison": {"severity": 50}}}
        )

        self.assertTrue(has_condition(actor, "poison"))

    def test_has_condition_false(self):
        """has_condition returns False when actor doesn't have condition."""
        from behaviors.library.actors.conditions import has_condition

        actor = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=[],
            properties={"conditions": {"poison": {"severity": 50}}}
        )

        self.assertFalse(has_condition(actor, "bleeding"))


class TestOnConditionTickHandler(unittest.TestCase):
    """Test on_condition_tick turn phase handler."""

    def test_on_condition_tick_ticks_all_actors(self):
        """on_condition_tick processes conditions on all actors."""
        from behaviors.library.actors.conditions import on_condition_tick
        from src.state_manager import GameState, Metadata, Location
        from src.state_accessor import StateAccessor

        player = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=[],
            properties={
                "health": 100,
                "conditions": {"poison": {"severity": 50, "damage_per_turn": 5}}
            }
        )

        npc = Actor(
            id="npc_guard",
            name="Guard",
            description="A guard",
            location="loc_test",
            inventory=[],
            properties={
                "health": 80,
                "conditions": {"bleeding": {"severity": 30, "damage_per_turn": 3}}
            }
        )

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[Location(id="loc_test", name="Test", description="Test")],
            items=[],
            actors={"player": player, "npc_guard": npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)
        context = {"hook": "condition_tick", "actor_id": "player"}

        result = on_condition_tick(None, accessor, context)

        # Both actors should have taken damage
        self.assertEqual(player.properties["health"], 95)  # 100 - 5
        self.assertEqual(npc.properties["health"], 77)     # 80 - 3

        # Result should have messages
        self.assertIsNotNone(result)
        self.assertTrue(result.allow)

    def test_vocabulary_registers_hook(self):
        """Vocabulary registers on_condition_tick with condition_tick hook."""
        from behaviors.library.actors.conditions import vocabulary

        self.assertIn("events", vocabulary)
        events = vocabulary["events"]

        # Find the on_condition_tick event
        tick_event = None
        for event in events:
            if event.get("event") == "on_condition_tick":
                tick_event = event
                break

        self.assertIsNotNone(tick_event)
        self.assertEqual(tick_event["hook"], "condition_tick")


if __name__ == '__main__':
    unittest.main()
