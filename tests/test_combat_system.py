"""Tests for combat system (Phase 3 of Actor Interaction)."""

import unittest
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass

from src.state_manager import Actor, Part, Location, GameState, Metadata, Item
from src.state_accessor import StateAccessor
from src.state_accessor import IGNORE_EVENT


class TestGetAttacks(unittest.TestCase):
    """Test get_attacks function."""

    def test_get_attacks_returns_list(self):
        """get_attacks returns actor's attacks array."""
        from behavior_libraries.actor_lib.combat import get_attacks

        actor = Actor(
            id="npc_wolf",
            name="Wolf",
            description="A wolf",
            location="loc_test",
            inventory=[],
            properties={
                "attacks": [
                    {"name": "bite", "damage": 15, "type": "melee"},
                    {"name": "claw", "damage": 10, "type": "melee"}
                ]
            }
        )

        attacks = get_attacks(actor)

        self.assertEqual(len(attacks), 2)
        self.assertEqual(attacks[0]["name"], "bite")
        self.assertEqual(attacks[1]["name"], "claw")

    def test_get_attacks_empty_list(self):
        """get_attacks returns empty list if no attacks."""
        from behavior_libraries.actor_lib.combat import get_attacks

        actor = Actor(
            id="npc_scholar",
            name="Scholar",
            description="A peaceful scholar",
            location="loc_test",
            inventory=[],
            properties={}
        )

        attacks = get_attacks(actor)

        self.assertEqual(attacks, [])

    def test_get_attacks_none_actor(self):
        """get_attacks returns empty list for None actor."""
        from behavior_libraries.actor_lib.combat import get_attacks

        attacks = get_attacks(None)

        self.assertEqual(attacks, [])


class TestSelectAttack(unittest.TestCase):
    """Test select_attack function."""

    def setUp(self):
        """Create test attacker and target."""
        self.attacker = Actor(
            id="npc_wolf",
            name="Wolf",
            description="A wolf",
            location="loc_test",
            inventory=[],
            properties={
                "attacks": [
                    {"name": "bite", "damage": 15, "type": "melee"},
                    {"name": "knockdown_pounce", "damage": 8, "type": "melee", "effect": "knockdown"},
                    {"name": "poison_bite", "damage": 5, "type": "melee",
                     "applies_condition": {"name": "poison", "severity": 30}}
                ]
            }
        )

        self.target = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=[],
            properties={
                "health": 100,
                "max_health": 100
            }
        )

    def test_select_attack_prefers_knockdown_healthy_target(self):
        """Prefers knockdown attack against healthy target."""
        from behavior_libraries.actor_lib.combat import select_attack

        context = {}

        attack = select_attack(self.attacker, self.target, context)

        self.assertEqual(attack["name"], "knockdown_pounce")

    def test_select_attack_prefers_condition_not_present(self):
        """Prefers condition attack if target doesn't have it."""
        from behavior_libraries.actor_lib.combat import select_attack

        # Target is injured (below 50% health), so knockdown not preferred
        self.target.properties["health"] = 40

        context = {}

        attack = select_attack(self.attacker, self.target, context)

        self.assertEqual(attack["name"], "poison_bite")

    def test_select_attack_skips_condition_if_present(self):
        """Doesn't prefer condition attack if target already has it."""
        from behavior_libraries.actor_lib.combat import select_attack

        # Target is injured and already poisoned
        self.target.properties["health"] = 40
        self.target.properties["conditions"] = {"poison": {"severity": 50}}

        context = {}

        attack = select_attack(self.attacker, self.target, context)

        # Should fall back to highest damage
        self.assertEqual(attack["name"], "bite")

    def test_select_attack_falls_back_to_highest_damage(self):
        """Falls back to highest damage attack."""
        from behavior_libraries.actor_lib.combat import select_attack

        # Attacker with no special attacks
        simple_attacker = Actor(
            id="npc_rat",
            name="Rat",
            description="A rat",
            location="loc_test",
            inventory=[],
            properties={
                "attacks": [
                    {"name": "nibble", "damage": 2},
                    {"name": "bite", "damage": 5}
                ]
            }
        )

        attack = select_attack(simple_attacker, self.target, {})

        self.assertEqual(attack["name"], "bite")

    def test_select_attack_no_attacks(self):
        """Returns None if attacker has no attacks."""
        from behavior_libraries.actor_lib.combat import select_attack

        peaceful = Actor(
            id="npc_scholar",
            name="Scholar",
            description="A scholar",
            location="loc_test",
            inventory=[],
            properties={}
        )

        attack = select_attack(peaceful, self.target, {})

        self.assertIsNone(attack)


class TestCalculateDamage(unittest.TestCase):
    """Test calculate_damage function."""

    def setUp(self):
        """Create test actors."""
        self.attacker = Actor(
            id="npc_wolf",
            name="Wolf",
            description="A wolf",
            location="loc_test",
            inventory=[],
            properties={}
        )

        self.target = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=[],
            properties={"health": 100}
        )

    def test_calculate_damage_base(self):
        """Base damage is applied correctly."""
        from behavior_libraries.actor_lib.combat import calculate_damage

        attack = {"name": "bite", "damage": 15}
        context = {}

        damage = calculate_damage(attack, self.attacker, self.target, context)

        self.assertEqual(damage, 15)

    def test_calculate_damage_armor_reduces(self):
        """Armor reduces damage."""
        from behavior_libraries.actor_lib.combat import calculate_damage

        attack = {"name": "bite", "damage": 15}
        self.target.properties["armor"] = 5
        context = {}

        damage = calculate_damage(attack, self.attacker, self.target, context)

        self.assertEqual(damage, 10)

    def test_calculate_damage_armor_minimum_zero(self):
        """Damage can't go below zero from armor."""
        from behavior_libraries.actor_lib.combat import calculate_damage

        attack = {"name": "nibble", "damage": 2}
        self.target.properties["armor"] = 10
        context = {}

        damage = calculate_damage(attack, self.attacker, self.target, context)

        self.assertEqual(damage, 0)

    def test_calculate_damage_with_cover(self):
        """Cover reduces damage by percentage."""
        from behavior_libraries.actor_lib.combat import calculate_damage

        attack = {"name": "bite", "damage": 20}

        # Target is in cover
        self.target.properties["posture"] = "cover"

        # Cover value of 50 reduces damage by 50%
        context = {"cover_value": 50}

        damage = calculate_damage(attack, self.attacker, self.target, context)

        self.assertEqual(damage, 10)

    def test_calculate_damage_cover_and_armor(self):
        """Cover and armor both apply."""
        from behavior_libraries.actor_lib.combat import calculate_damage

        attack = {"name": "bite", "damage": 20}
        self.target.properties["armor"] = 5
        self.target.properties["posture"] = "cover"
        context = {"cover_value": 50}

        # Armor first: 20 - 5 = 15
        # Then cover: 15 * 0.5 = 7.5 -> 7
        damage = calculate_damage(attack, self.attacker, self.target, context)

        self.assertEqual(damage, 7)


class TestExecuteAttack(unittest.TestCase):
    """Test execute_attack function."""

    def setUp(self):
        """Create test actors and mock accessor."""
        from behavior_libraries.actor_lib.combat import on_damage

        self.attacker = Actor(
            id="npc_wolf",
            name="Wolf",
            description="A wolf",
            location="loc_test",
            inventory=[],
            properties={
                "attacks": [
                    {"name": "bite", "damage": 15}
                ]
            }
        )

        self.target = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=[],
            properties={"health": 100, "max_health": 100}
        )

        # Create mock accessor that calls real on_damage handler
        self.mock_accessor = Mock()
        self.mock_accessor.behavior_manager = Mock()
        # Mock invoke_behavior to call actual on_damage function when on_damage event is triggered
        def mock_invoke(entity, event, accessor, context):
            if event == "on_damage":
                return on_damage(entity, accessor, context)
            return IGNORE_EVENT
        self.mock_accessor.behavior_manager.invoke_behavior.side_effect = mock_invoke

    def test_execute_attack_applies_damage(self):
        """Attack applies damage to target."""
        from behavior_libraries.actor_lib.combat import execute_attack

        attack = {"name": "bite", "damage": 15}

        result = execute_attack(self.mock_accessor, self.attacker, self.target, attack)

        self.assertTrue(result.success)
        self.assertEqual(result.damage, 15)
        self.assertEqual(self.target.properties["health"], 85)

    def test_execute_attack_armor_reduces_damage(self):
        """Armor reduces damage in attack execution."""
        from behavior_libraries.actor_lib.combat import execute_attack

        attack = {"name": "bite", "damage": 15}
        self.target.properties["armor"] = 5

        result = execute_attack(self.mock_accessor, self.attacker, self.target, attack)

        self.assertEqual(result.damage, 10)
        self.assertEqual(self.target.properties["health"], 90)

    def test_execute_attack_applies_condition(self):
        """Attack with condition applies it to target."""
        from behavior_libraries.actor_lib.combat import execute_attack

        attack = {
            "name": "poison_bite",
            "damage": 5,
            "applies_condition": {"name": "poison", "severity": 30}
        }

        result = execute_attack(self.mock_accessor, self.attacker, self.target, attack)

        self.assertIn("poison", result.conditions_applied)
        self.assertIn("poison", self.target.properties.get("conditions", {}))
        self.assertEqual(
            self.target.properties["conditions"]["poison"]["severity"],
            30
        )

    def test_execute_attack_returns_message(self):
        """Attack returns descriptive message."""
        from behavior_libraries.actor_lib.combat import execute_attack

        attack = {"name": "bite", "damage": 15}

        result = execute_attack(self.mock_accessor, self.attacker, self.target, attack)

        self.assertIn("Wolf", result.narration)
        self.assertIn("bite", result.narration)
        self.assertIn("15", result.narration)

    def test_execute_attack_fires_on_damage_behavior(self):
        """Attack applies damage via on_damage handler."""
        from behavior_libraries.actor_lib.combat import execute_attack

        attack = {"name": "bite", "damage": 15}

        # Verify target starts with full health
        self.assertEqual(self.target.properties["health"], 100)

        execute_attack(self.mock_accessor, self.attacker, self.target, attack)

        # on_damage handler should have applied damage (15 damage to 100 health = 85)
        self.assertEqual(self.target.properties["health"], 85)

    def test_execute_attack_with_cover(self):
        """Attack respects target's cover."""
        from behavior_libraries.actor_lib.combat import execute_attack

        attack = {"name": "bite", "damage": 20}
        self.target.properties["posture"] = "cover"
        self.target.properties["focused_on"] = "item_crate"

        # Mock the cover item
        cover_item = Mock()
        cover_item.properties = {"cover_value": 50}
        self.mock_accessor.get_item.return_value = cover_item

        result = execute_attack(self.mock_accessor, self.attacker, self.target, attack)

        self.assertEqual(result.damage, 10)
        self.assertEqual(self.target.properties["health"], 90)


class TestOnDeathCheck(unittest.TestCase):
    """Test on_death_check handler."""

    def setUp(self):
        """Create test actor."""
        self.actor = Actor(
            id="npc_wolf",
            name="Wolf",
            description="A wolf",
            location="loc_test",
            inventory=[],
            properties={"health": 10, "max_health": 50}
        )

    def test_death_check_triggers_at_zero(self):
        """Death check triggers on_death when health <= 0."""
        from behavior_libraries.actor_lib.combat import on_death_check

        self.actor.properties["health"] = 0

        mock_accessor = Mock()
        mock_accessor.game_state = Mock()
        mock_accessor.game_state.actors = {self.actor.id: self.actor}
        mock_accessor.behavior_manager = Mock()
        mock_accessor.behavior_manager.invoke_behavior.return_value = None
        context = {}

        result = on_death_check(self.actor, mock_accessor, context)

        # Should return message about death
        self.assertIsNotNone(result)
        self.assertIn("slain", result.feedback.lower())

    def test_death_check_triggers_negative_health(self):
        """Death check triggers when health is negative."""
        from behavior_libraries.actor_lib.combat import on_death_check

        self.actor.properties["health"] = -10

        mock_accessor = Mock()
        mock_accessor.game_state = Mock()
        mock_accessor.game_state.actors = {self.actor.id: self.actor}
        mock_accessor.behavior_manager = Mock()
        mock_accessor.behavior_manager.invoke_behavior.return_value = None

        result = on_death_check(self.actor, mock_accessor, {})

        self.assertIsNotNone(result)

    def test_death_check_skips_alive(self):
        """Death check skips actors with health > 0."""
        from behavior_libraries.actor_lib.combat import on_death_check

        self.actor.properties["health"] = 10

        mock_accessor = Mock()
        mock_accessor.behavior_manager = Mock()

        result = on_death_check(self.actor, mock_accessor, {})

        self.assertEqual(result, IGNORE_EVENT)
        mock_accessor.behavior_manager.invoke_behavior.assert_not_called()

    def test_death_check_skips_no_health(self):
        """Death check skips actors without health property."""
        from behavior_libraries.actor_lib.combat import on_death_check

        actor = Actor(
            id="item_statue",
            name="Statue",
            description="A statue",
            location="loc_test",
            inventory=[],
            properties={}  # No health
        )

        mock_accessor = Mock()

        result = on_death_check(actor, mock_accessor, {})

        self.assertEqual(result, IGNORE_EVENT)

    def test_death_check_uses_default_message(self):
        """Death check uses default death message."""
        from behavior_libraries.actor_lib.combat import on_death_check

        self.actor.properties["health"] = 0

        mock_accessor = Mock()
        mock_accessor.game_state = Mock()
        mock_accessor.game_state.actors = {self.actor.id: self.actor}

        result = on_death_check(self.actor, mock_accessor, {})

        self.assertIn("slain", result.feedback.lower())


class TestOnDeathCheckAll(unittest.TestCase):
    """Test on_death_check_all turn phase handler."""

    def test_death_check_all_checks_all_actors(self):
        """on_death_check_all checks all actors."""
        from behavior_libraries.actor_lib.combat import on_death_check_all
        from src.state_accessor import StateAccessor

        alive_actor = Actor(
            id="npc_guard",
            name="Guard",
            description="A guard",
            location="loc_test",
            inventory=[],
            properties={"health": 50}
        )

        dead_actor = Actor(
            id="npc_wolf",
            name="Wolf",
            description="A wolf",
            location="loc_test",
            inventory=[],
            properties={"health": 0}
        )

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[Location(id="loc_test", name="Test", description="Test")],
            items=[],
            actors={"npc_guard": alive_actor, "npc_wolf": dead_actor},
            locks=[],
            parts=[]
        )

        mock_behavior_manager = Mock()
        mock_behavior_manager.invoke_behavior.return_value = None

        accessor = StateAccessor(game_state, mock_behavior_manager)
        context = {"hook": "death_check"}

        result = on_death_check_all(None, accessor, context)

        # Should have a message about the dead wolf
        self.assertIsNotNone(result)
        self.assertIn("Wolf", result.feedback)


class TestAttackResult(unittest.TestCase):
    """Test AttackResult dataclass."""

    def test_attack_result_creation(self):
        """AttackResult can be created with all fields."""
        from behavior_libraries.actor_lib.combat import AttackResult

        result = AttackResult(
            success=True,
            damage=15,
            conditions_applied=["poison"],
            narration="Wolf bites Player for 15 damage"
        )

        self.assertTrue(result.success)
        self.assertEqual(result.damage, 15)
        self.assertEqual(result.conditions_applied, ["poison"])
        self.assertIn("15", result.narration)


class TestCombatVocabulary(unittest.TestCase):
    """Test combat vocabulary exports."""

    def test_vocabulary_has_events(self):
        """Vocabulary exports events."""
        from behavior_libraries.actor_lib.combat import vocabulary

        self.assertIn("events", vocabulary)

    def test_vocabulary_registers_death_hook(self):
        """Vocabulary registers on_death_check_all with death_check hook."""
        from behavior_libraries.actor_lib.combat import vocabulary

        events = vocabulary["events"]

        death_event = None
        for event in events:
            if event.get("event") == "on_death_check_all":
                death_event = event
                break

        self.assertIsNotNone(death_event)
        self.assertEqual(death_event["hook"], "death_check")


if __name__ == '__main__':
    unittest.main()
