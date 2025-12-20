"""Tests for treatment system (Phase 5 of Actor Interaction)."""

import unittest
from unittest.mock import Mock

from src.state_manager import Actor, Item, Location, GameState, Metadata
from src.state_accessor import StateAccessor


class TestGetTreatableConditions(unittest.TestCase):
    """Test get_treatable_conditions function."""

    def test_get_treatable_conditions_returns_list(self):
        """Returns list of conditions from cures property."""
        from behavior_libraries.actor_lib.treatment import get_treatable_conditions

        item = Item(
            id="item_antidote",
            name="Antidote",
            description="Cures poison",
            location="loc_test",
            properties={"cures": ["poison", "venom"]}
        )

        conditions = get_treatable_conditions(item)

        # Use set comparison since order is not guaranteed (implementation uses set)
        self.assertEqual(set(conditions), {"poison", "venom"})

    def test_get_treatable_conditions_empty(self):
        """Returns empty list if no cures property."""
        from behavior_libraries.actor_lib.treatment import get_treatable_conditions

        item = Item(
            id="item_sword",
            name="Sword",
            description="A sword",
            location="loc_test",
            properties={}
        )

        conditions = get_treatable_conditions(item)

        self.assertEqual(conditions, [])

    def test_get_treatable_conditions_none_item(self):
        """Returns empty list for None item."""
        from behavior_libraries.actor_lib.treatment import get_treatable_conditions

        conditions = get_treatable_conditions(None)

        self.assertEqual(conditions, [])


class TestCanTreat(unittest.TestCase):
    """Test can_treat function."""

    def test_can_treat_matching(self):
        """Returns True when item can treat condition."""
        from behavior_libraries.actor_lib.treatment import can_treat

        item = Item(
            id="item_antidote",
            name="Antidote",
            description="Cures poison",
            location="loc_test",
            properties={"cures": ["poison"]}
        )

        self.assertTrue(can_treat(item, "poison"))

    def test_can_treat_no_match(self):
        """Returns False when item cannot treat condition."""
        from behavior_libraries.actor_lib.treatment import can_treat

        item = Item(
            id="item_antidote",
            name="Antidote",
            description="Cures poison",
            location="loc_test",
            properties={"cures": ["poison"]}
        )

        self.assertFalse(can_treat(item, "bleeding"))

    def test_can_treat_no_cures(self):
        """Returns False when item has no cures property."""
        from behavior_libraries.actor_lib.treatment import can_treat

        item = Item(
            id="item_sword",
            name="Sword",
            description="A sword",
            location="loc_test",
            properties={}
        )

        self.assertFalse(can_treat(item, "poison"))


class TestTreatCondition(unittest.TestCase):
    """Test treat_condition function."""

    def setUp(self):
        """Create test actors and items."""
        self.actor = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=["item_antidote"],
            properties={
                "health": 80,
                "conditions": {
                    "poison": {"severity": 50, "damage_per_turn": 2}
                }
            }
        )

        self.antidote = Item(
            id="item_antidote",
            name="Antidote",
            description="Cures poison",
            location="loc_test",
            properties={"cures": ["poison"], "consumable": True}
        )

        self.location = Location(
            id="loc_test",
            name="Test",
            description="Test"
        )

    def test_treat_removes_condition(self):
        """Treatment removes condition completely."""
        from behavior_libraries.actor_lib.treatment import apply_treatment

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[self.antidote],
            actors={"player": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = apply_treatment(accessor, self.antidote, self.actor)

        self.assertTrue(result.success)
        self.assertIn("poison", result.conditions_treated)
        # Condition should be removed
        self.assertNotIn("poison", self.actor.properties.get("conditions", {}))

    def test_treat_reduces_severity(self):
        """Partial cure reduces severity."""
        from behavior_libraries.actor_lib.treatment import apply_treatment

        # Item with partial cure
        weak_antidote = Item(
            id="item_weak_antidote",
            name="Weak Antidote",
            description="Partially cures poison",
            location="loc_test",
            properties={"cures": ["poison"], "cure_amount": 30}
        )

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[weak_antidote],
            actors={"player": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = apply_treatment(accessor, weak_antidote, self.actor)

        self.assertTrue(result.success)
        # Severity should be reduced but not removed (50 - 30 = 20)
        self.assertIn("poison", self.actor.properties["conditions"])
        self.assertEqual(
            self.actor.properties["conditions"]["poison"]["severity"],
            20
        )

    def test_treat_consumes_item(self):
        """Consumable items are consumed after use."""
        from behavior_libraries.actor_lib.treatment import apply_treatment

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[self.antidote],
            actors={"player": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = apply_treatment(accessor, self.antidote, self.actor)

        self.assertTrue(result.success)
        self.assertTrue(result.item_consumed)
        # Item should be removed from inventory
        self.assertNotIn("item_antidote", self.actor.inventory)

    def test_treat_non_consumable_not_consumed(self):
        """Non-consumable items are not consumed."""
        from behavior_libraries.actor_lib.treatment import apply_treatment

        healing_staff = Item(
            id="item_staff",
            name="Healing Staff",
            description="A reusable healing staff",
            location="loc_test",
            properties={"cures": ["poison"], "consumable": False}
        )

        self.actor.inventory = ["item_staff"]

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[healing_staff],
            actors={"player": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = apply_treatment(accessor, healing_staff, self.actor)

        self.assertTrue(result.success)
        self.assertFalse(result.item_consumed)
        # Item should still be in inventory
        self.assertIn("item_staff", self.actor.inventory)

    def test_treat_no_matching_condition(self):
        """Treatment fails if actor doesn't have treatable condition."""
        from behavior_libraries.actor_lib.treatment import apply_treatment

        # Actor with different condition
        self.actor.properties["conditions"] = {
            "bleeding": {"severity": 30}
        }

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[self.antidote],
            actors={"player": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = apply_treatment(accessor, self.antidote, self.actor)

        self.assertFalse(result.success)
        # Item should not be consumed
        self.assertIn("item_antidote", self.actor.inventory)

    def test_treat_specific_condition(self):
        """Can specify which condition to treat."""
        from behavior_libraries.actor_lib.treatment import apply_treatment

        # Actor with multiple conditions
        self.actor.properties["conditions"] = {
            "poison": {"severity": 50},
            "disease": {"severity": 30}
        }

        # Item that cures both
        universal_cure = Item(
            id="item_cure_all",
            name="Panacea",
            description="Cures everything",
            location="loc_test",
            properties={"cures": ["poison", "disease"]}
        )

        self.actor.inventory = ["item_cure_all"]

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[universal_cure],
            actors={"player": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        # Only treat poison
        result = apply_treatment(accessor, universal_cure, self.actor, "poison")

        self.assertTrue(result.success)
        # Poison should be removed
        self.assertNotIn("poison", self.actor.properties["conditions"])
        # Disease should remain
        self.assertIn("disease", self.actor.properties["conditions"])

    def test_treat_multiple_conditions(self):
        """Item can treat multiple conditions at once."""
        from behavior_libraries.actor_lib.treatment import apply_treatment

        # Actor with multiple conditions
        self.actor.properties["conditions"] = {
            "poison": {"severity": 50},
            "disease": {"severity": 30}
        }

        # Item that cures both
        universal_cure = Item(
            id="item_cure_all",
            name="Panacea",
            description="Cures everything",
            location="loc_test",
            properties={"cures": ["poison", "disease"], "consumable": True}
        )

        self.actor.inventory = ["item_cure_all"]

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[universal_cure],
            actors={"player": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = apply_treatment(accessor, universal_cure, self.actor)

        self.assertTrue(result.success)
        self.assertEqual(len(result.conditions_treated), 2)
        self.assertIn("poison", result.conditions_treated)
        self.assertIn("disease", result.conditions_treated)


class TestTreatmentResult(unittest.TestCase):
    """Test TreatmentResult dataclass."""

    def test_treatment_result_creation(self):
        """TreatmentResult can be created with all fields."""
        from behavior_libraries.actor_lib.treatment import TreatmentResult

        result = TreatmentResult(
            success=True,
            conditions_treated=["poison"],
            item_consumed=True,
            effect="Treated poison"
        )

        self.assertTrue(result.success)
        self.assertEqual(result.conditions_treated, ["poison"])
        self.assertTrue(result.item_consumed)


class TestOnReceiveTreatment(unittest.TestCase):
    """Test on_receive_treatment behavior."""

    def test_on_receive_auto_treats(self):
        """Receiving curative item auto-treats matching condition."""
        from behavior_libraries.actor_lib.treatment import on_receive_treatment
        from src.state_accessor import EventResult

        actor = Actor(
            id="npc_scholar",
            name="Scholar",
            description="An infected scholar",
            location="loc_test",
            inventory=[],
            properties={
                "conditions": {
                    "fungal_infection": {"severity": 30}
                }
            }
        )

        antifungal = Item(
            id="item_antifungal",
            name="Antifungal Herb",
            description="Cures fungal infections",
            location="loc_test",
            properties={"cures": ["fungal_infection"], "consumable": True}
        )

        location = Location(id="loc_test", name="Test", description="Test")

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[location],
            items=[antifungal],
            actors={"npc_scholar": actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)
        context = {"item_id": "item_antifungal"}

        result = on_receive_treatment(actor, accessor, context)

        self.assertIsNotNone(result)
        # Condition should be cured
        self.assertNotIn("fungal_infection", actor.properties.get("conditions", {}))

    def test_on_receive_no_matching_condition(self):
        """No auto-treatment if actor doesn't have matching condition."""
        from behavior_libraries.actor_lib.treatment import on_receive_treatment

        actor = Actor(
            id="player",
            name="Player",
            description="Healthy player",
            location="loc_test",
            inventory=[],
            properties={}  # No conditions
        )

        antidote = Item(
            id="item_antidote",
            name="Antidote",
            description="Cures poison",
            location="loc_test",
            properties={"cures": ["poison"]}
        )

        location = Location(id="loc_test", name="Test", description="Test")

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[location],
            items=[antidote],
            actors={"player": actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)
        context = {"item_id": "item_antidote"}

        result = on_receive_treatment(actor, accessor, context)

        # No treatment applied
        self.assertIsNone(result)

    def test_on_receive_non_curative_item(self):
        """No auto-treatment for non-curative items."""
        from behavior_libraries.actor_lib.treatment import on_receive_treatment

        actor = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=[],
            properties={
                "conditions": {"poison": {"severity": 50}}
            }
        )

        sword = Item(
            id="item_sword",
            name="Sword",
            description="A sword",
            location="loc_test",
            properties={}  # No cures
        )

        location = Location(id="loc_test", name="Test", description="Test")

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[location],
            items=[sword],
            actors={"player": actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)
        context = {"item_id": "item_sword"}

        result = on_receive_treatment(actor, accessor, context)

        self.assertIsNone(result)


class TestTreatmentVocabulary(unittest.TestCase):
    """Test treatment vocabulary exports."""

    def test_vocabulary_has_events(self):
        """Vocabulary exports events."""
        from behavior_libraries.actor_lib.treatment import vocabulary

        self.assertIn("events", vocabulary)

    def test_vocabulary_has_on_receive_event(self):
        """Vocabulary includes on_receive_treatment event."""
        from behavior_libraries.actor_lib.treatment import vocabulary

        events = vocabulary["events"]
        event_names = [e["event"] for e in events]

        self.assertIn("on_receive_treatment", event_names)


if __name__ == '__main__':
    unittest.main()
