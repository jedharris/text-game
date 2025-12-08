"""Tests for relationship tracking system (Phase 7 of Actor Interaction)."""

import unittest
from unittest.mock import Mock

from src.state_manager import Actor, Location, GameState, Metadata
from src.state_accessor import StateAccessor


class TestGetRelationship(unittest.TestCase):
    """Test get_relationship function."""

    def test_get_relationship_existing(self):
        """Returns existing relationship values."""
        from behaviors.actors.relationships import get_relationship

        actor = Actor(
            id="npc_healer",
            name="Healer",
            description="A healer",
            location="loc_test",
            inventory=[],
            properties={
                "relationships": {
                    "player": {"trust": 5, "gratitude": 2, "fear": 0}
                }
            }
        )

        rel = get_relationship(actor, "player")

        self.assertEqual(rel["trust"], 5)
        self.assertEqual(rel["gratitude"], 2)
        self.assertEqual(rel["fear"], 0)

    def test_get_relationship_new(self):
        """Creates default relationship entry if missing."""
        from behaviors.actors.relationships import get_relationship

        actor = Actor(
            id="npc_healer",
            name="Healer",
            description="A healer",
            location="loc_test",
            inventory=[],
            properties={}
        )

        rel = get_relationship(actor, "player")

        # Should return default values
        self.assertEqual(rel.get("trust", 0), 0)
        self.assertEqual(rel.get("gratitude", 0), 0)
        self.assertEqual(rel.get("fear", 0), 0)

    def test_get_relationship_none_actor(self):
        """Returns empty dict for None actor."""
        from behaviors.actors.relationships import get_relationship

        rel = get_relationship(None, "player")

        self.assertEqual(rel, {})


class TestModifyRelationship(unittest.TestCase):
    """Test modify_relationship function."""

    def setUp(self):
        """Create test actor."""
        self.actor = Actor(
            id="npc_healer",
            name="Healer",
            description="A healer",
            location="loc_test",
            inventory=[],
            properties={}
        )

        self.location = Location(
            id="loc_test",
            name="Test",
            description="Test"
        )

    def test_modify_relationship_increase(self):
        """Increases metric value."""
        from behaviors.actors.relationships import modify_relationship

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[],
            actors={"npc_healer": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = modify_relationship(accessor, self.actor, "player", "trust", 2)

        self.assertEqual(result.old_value, 0)
        self.assertEqual(result.new_value, 2)
        self.assertEqual(
            self.actor.properties["relationships"]["player"]["trust"],
            2
        )

    def test_modify_relationship_decrease(self):
        """Decreases metric value."""
        from behaviors.actors.relationships import modify_relationship

        self.actor.properties["relationships"] = {
            "player": {"trust": 5, "gratitude": 0, "fear": 0}
        }

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[],
            actors={"npc_healer": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = modify_relationship(accessor, self.actor, "player", "trust", -2)

        self.assertEqual(result.old_value, 5)
        self.assertEqual(result.new_value, 3)

    def test_modify_relationship_bounds_max(self):
        """Values clamped at maximum 10."""
        from behaviors.actors.relationships import modify_relationship

        self.actor.properties["relationships"] = {
            "player": {"trust": 9, "gratitude": 0, "fear": 0}
        }

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[],
            actors={"npc_healer": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = modify_relationship(accessor, self.actor, "player", "trust", 5)

        self.assertEqual(result.new_value, 10)  # Clamped at 10

    def test_modify_relationship_bounds_min(self):
        """Values clamped at minimum 0."""
        from behaviors.actors.relationships import modify_relationship

        self.actor.properties["relationships"] = {
            "player": {"trust": 2, "gratitude": 0, "fear": 0}
        }

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[],
            actors={"npc_healer": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = modify_relationship(accessor, self.actor, "player", "trust", -5)

        self.assertEqual(result.new_value, 0)  # Clamped at 0


class TestThresholdCrossing(unittest.TestCase):
    """Test threshold crossing detection."""

    def setUp(self):
        """Create test actor."""
        self.actor = Actor(
            id="npc_healer",
            name="Healer",
            description="A healer",
            location="loc_test",
            inventory=[],
            properties={}
        )

        self.location = Location(
            id="loc_test",
            name="Test",
            description="Test"
        )

    def test_threshold_domestication(self):
        """Gratitude >= 3 triggers domestication threshold."""
        from behaviors.actors.relationships import modify_relationship

        self.actor.properties["relationships"] = {
            "player": {"trust": 0, "gratitude": 2, "fear": 0}
        }

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[],
            actors={"npc_healer": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = modify_relationship(accessor, self.actor, "player", "gratitude", 1)

        self.assertEqual(result.threshold_crossed, "domestication")

    def test_threshold_discount(self):
        """Trust >= 3 triggers discount threshold."""
        from behaviors.actors.relationships import modify_relationship

        self.actor.properties["relationships"] = {
            "player": {"trust": 2, "gratitude": 0, "fear": 0}
        }

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[],
            actors={"npc_healer": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = modify_relationship(accessor, self.actor, "player", "trust", 1)

        self.assertEqual(result.threshold_crossed, "discount")

    def test_threshold_loyalty(self):
        """Trust >= 5 triggers loyalty threshold."""
        from behaviors.actors.relationships import modify_relationship

        self.actor.properties["relationships"] = {
            "player": {"trust": 4, "gratitude": 0, "fear": 0}
        }

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[],
            actors={"npc_healer": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = modify_relationship(accessor, self.actor, "player", "trust", 1)

        self.assertEqual(result.threshold_crossed, "loyalty")

    def test_threshold_intimidation(self):
        """Fear >= 5 triggers intimidation threshold."""
        from behaviors.actors.relationships import modify_relationship

        self.actor.properties["relationships"] = {
            "player": {"trust": 0, "gratitude": 0, "fear": 4}
        }

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[],
            actors={"npc_healer": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = modify_relationship(accessor, self.actor, "player", "fear", 1)

        self.assertEqual(result.threshold_crossed, "intimidation")

    def test_no_threshold_crossing(self):
        """No threshold crossed when staying below."""
        from behaviors.actors.relationships import modify_relationship

        self.actor.properties["relationships"] = {
            "player": {"trust": 0, "gratitude": 0, "fear": 0}
        }

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[],
            actors={"npc_healer": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = modify_relationship(accessor, self.actor, "player", "trust", 1)

        self.assertIsNone(result.threshold_crossed)

    def test_threshold_not_recrossed(self):
        """Threshold not reported when already above."""
        from behaviors.actors.relationships import modify_relationship

        # Already at trust 5
        self.actor.properties["relationships"] = {
            "player": {"trust": 5, "gratitude": 0, "fear": 0}
        }

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[],
            actors={"npc_healer": self.actor},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = modify_relationship(accessor, self.actor, "player", "trust", 1)

        # Should not report loyalty threshold again
        self.assertIsNone(result.threshold_crossed)


class TestCheckThreshold(unittest.TestCase):
    """Test check_threshold function."""

    def test_check_threshold_met(self):
        """Returns True when threshold is met."""
        from behaviors.actors.relationships import check_threshold

        actor = Actor(
            id="npc_healer",
            name="Healer",
            description="A healer",
            location="loc_test",
            inventory=[],
            properties={
                "relationships": {
                    "player": {"trust": 5, "gratitude": 0, "fear": 0}
                }
            }
        )

        self.assertTrue(check_threshold(actor, "player", "trust", 3))
        self.assertTrue(check_threshold(actor, "player", "trust", 5))

    def test_check_threshold_not_met(self):
        """Returns False when threshold is not met."""
        from behaviors.actors.relationships import check_threshold

        actor = Actor(
            id="npc_healer",
            name="Healer",
            description="A healer",
            location="loc_test",
            inventory=[],
            properties={
                "relationships": {
                    "player": {"trust": 2, "gratitude": 0, "fear": 0}
                }
            }
        )

        self.assertFalse(check_threshold(actor, "player", "trust", 3))

    def test_check_threshold_no_relationship(self):
        """Returns False when no relationship exists."""
        from behaviors.actors.relationships import check_threshold

        actor = Actor(
            id="npc_healer",
            name="Healer",
            description="A healer",
            location="loc_test",
            inventory=[],
            properties={}
        )

        self.assertFalse(check_threshold(actor, "player", "trust", 3))


class TestGetDispositionFromRelationships(unittest.TestCase):
    """Test get_disposition_from_relationships function."""

    def test_disposition_hostile_from_fear(self):
        """High fear makes NPC hostile."""
        from behaviors.actors.relationships import get_disposition_from_relationships

        actor = Actor(
            id="npc_guard",
            name="Guard",
            description="A guard",
            location="loc_test",
            inventory=[],
            properties={
                "relationships": {
                    "player": {"trust": 0, "gratitude": 0, "fear": 7}
                }
            }
        )

        disposition = get_disposition_from_relationships(actor, "player")

        # High fear without trust leads to hostile
        self.assertEqual(disposition, "hostile")

    def test_disposition_friendly_from_trust(self):
        """High trust makes NPC friendly."""
        from behaviors.actors.relationships import get_disposition_from_relationships

        actor = Actor(
            id="npc_healer",
            name="Healer",
            description="A healer",
            location="loc_test",
            inventory=[],
            properties={
                "relationships": {
                    "player": {"trust": 5, "gratitude": 3, "fear": 0}
                }
            }
        )

        disposition = get_disposition_from_relationships(actor, "player")

        self.assertEqual(disposition, "friendly")

    def test_disposition_neutral_default(self):
        """Low values default to neutral."""
        from behaviors.actors.relationships import get_disposition_from_relationships

        actor = Actor(
            id="npc_merchant",
            name="Merchant",
            description="A merchant",
            location="loc_test",
            inventory=[],
            properties={
                "relationships": {
                    "player": {"trust": 1, "gratitude": 1, "fear": 1}
                }
            }
        )

        disposition = get_disposition_from_relationships(actor, "player")

        self.assertEqual(disposition, "neutral")

    def test_disposition_no_relationship(self):
        """No relationship defaults to neutral."""
        from behaviors.actors.relationships import get_disposition_from_relationships

        actor = Actor(
            id="npc_stranger",
            name="Stranger",
            description="A stranger",
            location="loc_test",
            inventory=[],
            properties={}
        )

        disposition = get_disposition_from_relationships(actor, "player")

        self.assertEqual(disposition, "neutral")


class TestRelationshipResult(unittest.TestCase):
    """Test RelationshipResult dataclass."""

    def test_relationship_result_creation(self):
        """RelationshipResult can be created with all fields."""
        from behaviors.actors.relationships import RelationshipResult

        result = RelationshipResult(
            old_value=2,
            new_value=3,
            threshold_crossed="discount"
        )

        self.assertEqual(result.old_value, 2)
        self.assertEqual(result.new_value, 3)
        self.assertEqual(result.threshold_crossed, "discount")


class TestRelationshipsVocabulary(unittest.TestCase):
    """Test relationships vocabulary exports."""

    def test_vocabulary_has_events(self):
        """Vocabulary exports events."""
        from behaviors.actors.relationships import vocabulary

        self.assertIn("events", vocabulary)


if __name__ == '__main__':
    unittest.main()
