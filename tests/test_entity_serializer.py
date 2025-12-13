"""Tests for entity serializer module.

Tests unified entity-to-dict conversion with llm_context handling.
"""
import unittest
from unittest.mock import patch

from src.state_manager import (
    Item, Location, Actor, ExitDescriptor, Lock, Metadata, GameState
)


class TestEntityToDictItem(unittest.TestCase):
    """Test entity_to_dict for Item entities."""

    def test_basic_item_serialization(self):
        """Test basic item fields are serialized."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_sword",
            name="sword",
            description="A rusty sword.",
            location="loc_room"
        )

        result = entity_to_dict(item)

        self.assertEqual(result["id"], "item_sword")
        self.assertEqual(result["name"], "sword")
        self.assertEqual(result["description"], "A rusty sword.")
        self.assertEqual(result["type"], "item")

    def test_item_with_llm_context(self):
        """Test item llm_context is included."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_sword",
            name="sword",
            description="A rusty sword.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["rusty", "ancient", "battle-worn"]
                }
            }
        )

        result = entity_to_dict(item)

        self.assertIn("llm_context", result)
        self.assertIn("traits", result["llm_context"])
        self.assertEqual(len(result["llm_context"]["traits"]), 3)

    def test_item_without_llm_context(self):
        """Test item without llm_context doesn't have key."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_rock",
            name="rock",
            description="A plain rock.",
            location="loc_room"
        )

        result = entity_to_dict(item)

        self.assertNotIn("llm_context", result)

    def test_door_item_serialization(self):
        """Test door item includes door-specific fields."""
        from utilities.entity_serializer import entity_to_dict

        door = Item(
            id="door_wooden",
            name="door",
            description="A wooden door.",
            location="exit:loc_room:north",
            properties={
                "door": {"open": False, "locked": True, "lock_id": "lock_1"}
            }
        )

        result = entity_to_dict(door)

        self.assertEqual(result["type"], "door")
        self.assertEqual(result["open"], False)
        self.assertEqual(result["locked"], True)

    def test_container_item_serialization(self):
        """Test container item includes container type."""
        from utilities.entity_serializer import entity_to_dict

        chest = Item(
            id="item_chest",
            name="chest",
            description="A wooden chest.",
            location="loc_room",
            properties={
                "container": {"is_surface": False, "open": False, "capacity": 5}
            }
        )

        result = entity_to_dict(chest)

        self.assertEqual(result["type"], "container")

    def test_light_source_item_serialization(self):
        """Test light source includes lit state and provides_light."""
        from utilities.entity_serializer import entity_to_dict

        lantern = Item(
            id="item_lantern",
            name="lantern",
            description="A brass lantern.",
            location="player",
            properties={
                "provides_light": True,
                "states": {"lit": True}
            }
        )

        result = entity_to_dict(lantern)

        self.assertTrue(result.get("provides_light"))
        self.assertTrue(result.get("lit"))


class TestEntityToDictLocation(unittest.TestCase):
    """Test entity_to_dict for Location entities."""

    def test_basic_location_serialization(self):
        """Test basic location fields are serialized."""
        from utilities.entity_serializer import entity_to_dict

        location = Location(
            id="loc_room",
            name="Small Room",
            description="A small dusty room."
        )

        result = entity_to_dict(location)

        self.assertEqual(result["id"], "loc_room")
        self.assertEqual(result["name"], "Small Room")
        self.assertEqual(result["description"], "A small dusty room.")

    def test_location_with_llm_context(self):
        """Test location llm_context is included."""
        from utilities.entity_serializer import entity_to_dict

        location = Location(
            id="loc_room",
            name="Small Room",
            description="A small dusty room.",
            properties={
                "llm_context": {
                    "traits": ["dusty", "cramped", "dimly lit"]
                }
            }
        )

        result = entity_to_dict(location)

        self.assertIn("llm_context", result)
        self.assertEqual(len(result["llm_context"]["traits"]), 3)


class TestEntityToDictActor(unittest.TestCase):
    """Test entity_to_dict for Actor entities."""

    def test_basic_actor_serialization(self):
        """Test basic actor fields are serialized."""
        from utilities.entity_serializer import entity_to_dict

        actor = Actor(
            id="npc_guard",
            name="Guard",
            description="A stern-looking guard.",
            location="loc_room",
            inventory=[]
        )

        result = entity_to_dict(actor)

        self.assertEqual(result["id"], "npc_guard")
        self.assertEqual(result["name"], "Guard")
        self.assertEqual(result["description"], "A stern-looking guard.")
        self.assertEqual(result["type"], "actor")

    def test_actor_with_llm_context(self):
        """Test actor llm_context is included."""
        from utilities.entity_serializer import entity_to_dict

        actor = Actor(
            id="npc_guard",
            name="Guard",
            description="A stern-looking guard.",
            location="loc_room",
            inventory=[],
            properties={
                "llm_context": {
                    "traits": ["vigilant", "armored", "suspicious"]
                }
            }
        )

        result = entity_to_dict(actor)

        self.assertIn("llm_context", result)
        self.assertEqual(len(result["llm_context"]["traits"]), 3)


class TestEntityToDictExitDescriptor(unittest.TestCase):
    """Test entity_to_dict for ExitDescriptor entities."""

    def test_basic_exit_serialization(self):
        """Test basic exit fields are serialized."""
        from utilities.entity_serializer import entity_to_dict

        exit_desc = ExitDescriptor(
            type="open",
            to="loc_hallway",
            name="stone archway",
            description="A worn stone archway leads north."
        )

        result = entity_to_dict(exit_desc)

        self.assertEqual(result["name"], "stone archway")
        self.assertEqual(result["description"], "A worn stone archway leads north.")

    def test_exit_with_llm_context(self):
        """Test exit llm_context is included."""
        from utilities.entity_serializer import entity_to_dict

        exit_desc = ExitDescriptor(
            type="open",
            to="loc_hallway",
            name="stone archway",
            description="A worn stone archway.",
            properties={
                "llm_context": {
                    "traits": ["ancient", "weathered", "mossy"]
                }
            }
        )

        result = entity_to_dict(exit_desc)

        self.assertIn("llm_context", result)
        self.assertEqual(len(result["llm_context"]["traits"]), 3)


class TestEntityToDictLock(unittest.TestCase):
    """Test entity_to_dict for Lock entities."""

    def test_basic_lock_serialization(self):
        """Test basic lock fields are serialized."""
        from utilities.entity_serializer import entity_to_dict

        lock = Lock(
            id="lock_iron",
            name="Iron Lock",
            description="An iron lock with intricate engravings.",
            properties={"opens_with": ["item_key"]}
        )

        result = entity_to_dict(lock)

        self.assertEqual(result["id"], "lock_iron")
        self.assertEqual(result["description"], "An iron lock with intricate engravings.")

    def test_lock_with_llm_context(self):
        """Test lock llm_context is included."""
        from utilities.entity_serializer import entity_to_dict

        lock = Lock(
            id="lock_iron",
            name="Iron Lock",
            description="An iron lock.",
            properties={
                "opens_with": ["item_key"],
                "llm_context": {
                    "traits": ["rusty", "ancient", "elaborate"]
                }
            }
        )

        result = entity_to_dict(lock)

        self.assertIn("llm_context", result)
        self.assertEqual(len(result["llm_context"]["traits"]), 3)


class TestMaxTraits(unittest.TestCase):
    """Test max_traits parameter for limiting trait count."""

    def test_max_traits_limits_trait_count(self):
        """Test that max_traits parameter limits the number of traits."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_sword",
            name="sword",
            description="A sword.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
                }
            }
        )

        result = entity_to_dict(item, max_traits=3)

        self.assertEqual(len(result["llm_context"]["traits"]), 3)

    def test_max_traits_none_returns_all_traits(self):
        """Test that max_traits=None returns all traits."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_sword",
            name="sword",
            description="A sword.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["a", "b", "c", "d", "e"]
                }
            }
        )

        result = entity_to_dict(item, max_traits=None)

        self.assertEqual(len(result["llm_context"]["traits"]), 5)

    def test_max_traits_larger_than_list_returns_all(self):
        """Test that max_traits larger than list returns all traits."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_sword",
            name="sword",
            description="A sword.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["a", "b", "c"]
                }
            }
        )

        result = entity_to_dict(item, max_traits=10)

        self.assertEqual(len(result["llm_context"]["traits"]), 3)

    def test_max_traits_zero_returns_empty_list(self):
        """Test that max_traits=0 returns empty traits list."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_sword",
            name="sword",
            description="A sword.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["a", "b", "c"]
                }
            }
        )

        result = entity_to_dict(item, max_traits=0)

        self.assertEqual(len(result["llm_context"]["traits"]), 0)

    def test_max_traits_preserves_other_llm_context_fields(self):
        """Test that max_traits doesn't affect other llm_context fields."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_sword",
            name="sword",
            description="A sword.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["a", "b", "c", "d", "e"],
                    "state_variants": {"broken": "shattered"},
                    "atmosphere": "tense"
                }
            }
        )

        result = entity_to_dict(item, max_traits=2)

        self.assertEqual(len(result["llm_context"]["traits"]), 2)
        self.assertEqual(result["llm_context"]["state_variants"]["broken"], "shattered")
        self.assertEqual(result["llm_context"]["atmosphere"], "tense")

    def test_max_traits_with_no_llm_context(self):
        """Test that max_traits doesn't break entities without llm_context."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_rock",
            name="rock",
            description="A plain rock.",
            location="loc_room"
        )

        result = entity_to_dict(item, max_traits=5)

        self.assertNotIn("llm_context", result)


class TestTraitRandomization(unittest.TestCase):
    """Test trait randomization in llm_context."""

    def test_traits_are_randomized(self):
        """Test that traits order is randomized."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_sword",
            name="sword",
            description="A sword.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["a", "b", "c", "d", "e", "f", "g", "h"]
                }
            }
        )

        # Run multiple times and check for different orderings
        orderings = set()
        for _ in range(20):
            result = entity_to_dict(item)
            ordering = tuple(result["llm_context"]["traits"])
            orderings.add(ordering)

        # With 8 traits and 20 iterations, we should see multiple orderings
        # (probability of all same is astronomically low)
        self.assertGreater(len(orderings), 1, "Traits should be randomized")

    def test_original_traits_not_mutated(self):
        """Test that original entity traits are not mutated."""
        from utilities.entity_serializer import entity_to_dict

        original_traits = ["a", "b", "c", "d", "e"]
        item = Item(
            id="item_sword",
            name="sword",
            description="A sword.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": original_traits.copy()
                }
            }
        )

        # Call multiple times
        for _ in range(10):
            entity_to_dict(item)

        # Original should be unchanged
        self.assertEqual(item.properties["llm_context"]["traits"], original_traits)

    def test_non_trait_llm_context_preserved(self):
        """Test that other llm_context fields are preserved."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_sword",
            name="sword",
            description="A sword.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["sharp", "ancient"],
                    "state_variants": {
                        "broken": "shattered blade",
                        "pristine": "gleaming edge"
                    },
                    "custom_field": "custom_value"
                }
            }
        )

        result = entity_to_dict(item)

        self.assertIn("state_variants", result["llm_context"])
        self.assertEqual(result["llm_context"]["state_variants"]["broken"], "shattered blade")
        self.assertEqual(result["llm_context"]["custom_field"], "custom_value")


class TestSerializeForHandlerResult(unittest.TestCase):
    """Test serialize_for_handler_result convenience function."""

    def test_serialize_for_handler_result(self):
        """Test convenience function includes llm_context."""
        from utilities.entity_serializer import serialize_for_handler_result

        item = Item(
            id="item_sword",
            name="sword",
            description="A sword.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["sharp"]
                }
            }
        )

        result = serialize_for_handler_result(item)

        self.assertIn("llm_context", result)
        self.assertEqual(result["id"], "item_sword")


class TestIncludeLlmContextFlag(unittest.TestCase):
    """Test include_llm_context parameter."""

    def test_exclude_llm_context(self):
        """Test llm_context can be excluded."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_sword",
            name="sword",
            description="A sword.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["sharp"]
                }
            }
        )

        result = entity_to_dict(item, include_llm_context=False)

        self.assertNotIn("llm_context", result)
        self.assertEqual(result["id"], "item_sword")


class TestPerspectiveVariants(unittest.TestCase):
    """Test perspective_variants selection based on player_context."""

    def test_no_perspective_note_without_variants(self):
        """Test that no perspective_note is added when no variants exist."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_stairs",
            name="stairs",
            description="A spiral staircase.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["worn", "ancient"]
                }
            }
        )

        player_context = {"posture": "climbing", "focused_on": "item_stairs"}
        result = entity_to_dict(item, player_context=player_context)

        self.assertNotIn("perspective_note", result)

    def test_no_perspective_note_without_player_context_and_no_default(self):
        """Test no perspective_note when no player_context and no default variant."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_stairs",
            name="stairs",
            description="A spiral staircase.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["worn"],
                    "perspective_variants": {
                        "climbing": "The worn steps continue above and below you"
                    }
                }
            }
        )

        result = entity_to_dict(item)  # No player_context

        self.assertNotIn("perspective_note", result)

    def test_default_variant_without_player_context(self):
        """Test that default variant is used when no player_context."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_stairs",
            name="stairs",
            description="A spiral staircase.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["worn"],
                    "perspective_variants": {
                        "default": "A spiral staircase rises through the tower",
                        "climbing": "The worn steps continue above and below you"
                    }
                }
            }
        )

        result = entity_to_dict(item)  # No player_context

        self.assertEqual(result["perspective_note"],
                        "A spiral staircase rises through the tower")

    def test_posture_match_selected(self):
        """Test that posture-only variant is selected when matching."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_stairs",
            name="stairs",
            description="A spiral staircase.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["worn"],
                    "perspective_variants": {
                        "default": "A spiral staircase rises through the tower",
                        "climbing": "The worn steps continue above and below you"
                    }
                }
            }
        )

        player_context = {"posture": "climbing", "focused_on": "item_stairs"}
        result = entity_to_dict(item, player_context=player_context)

        self.assertEqual(result["perspective_note"],
                        "The worn steps continue above and below you")

    def test_exact_match_takes_precedence(self):
        """Test that exact posture:focus match takes precedence over posture."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_stairs",
            name="stairs",
            description="A spiral staircase.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["worn"],
                    "perspective_variants": {
                        "default": "A spiral staircase rises through the tower",
                        "climbing": "Generic climbing description",
                        "climbing:item_stairs": "You cling to the worn spiral steps"
                    }
                }
            }
        )

        player_context = {"posture": "climbing", "focused_on": "item_stairs"}
        result = entity_to_dict(item, player_context=player_context)

        self.assertEqual(result["perspective_note"],
                        "You cling to the worn spiral steps")

    def test_fallback_to_default_when_no_posture_match(self):
        """Test fallback to default when posture doesn't match."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_stairs",
            name="stairs",
            description="A spiral staircase.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["worn"],
                    "perspective_variants": {
                        "default": "A spiral staircase rises through the tower",
                        "climbing": "The worn steps continue above and below you"
                    }
                }
            }
        )

        player_context = {"posture": "on_surface", "focused_on": "item_table"}
        result = entity_to_dict(item, player_context=player_context)

        self.assertEqual(result["perspective_note"],
                        "A spiral staircase rises through the tower")

    def test_no_perspective_note_when_no_match_and_no_default(self):
        """Test no perspective_note when posture doesn't match and no default."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_stairs",
            name="stairs",
            description="A spiral staircase.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["worn"],
                    "perspective_variants": {
                        "climbing": "The worn steps continue above and below you"
                    }
                }
            }
        )

        player_context = {"posture": "on_surface", "focused_on": "item_table"}
        result = entity_to_dict(item, player_context=player_context)

        self.assertNotIn("perspective_note", result)

    def test_perspective_note_separate_from_llm_context(self):
        """Test that perspective_note is at top level, not inside llm_context."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_stairs",
            name="stairs",
            description="A spiral staircase.",
            location="loc_room",
            properties={
                "llm_context": {
                    "traits": ["worn"],
                    "perspective_variants": {
                        "default": "A spiral staircase rises through the tower"
                    }
                }
            }
        )

        result = entity_to_dict(item)

        # perspective_note should be at top level
        self.assertIn("perspective_note", result)
        # llm_context should still exist and have traits
        self.assertIn("llm_context", result)
        self.assertIn("traits", result["llm_context"])


class TestSpatialRelation(unittest.TestCase):
    """Test spatial_relation computation based on player_context."""

    def test_no_spatial_relation_without_player_context(self):
        """Test that no spatial_relation is added without player_context."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_sword",
            name="sword",
            description="A sword.",
            location="loc_room"
        )

        result = entity_to_dict(item)

        self.assertNotIn("spatial_relation", result)

    def test_no_spatial_relation_with_null_posture(self):
        """Test that no spatial_relation is added when posture is None."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_sword",
            name="sword",
            description="A sword.",
            location="loc_room"
        )

        player_context = {"posture": None, "focused_on": None}
        result = entity_to_dict(item, player_context=player_context)

        self.assertNotIn("spatial_relation", result)

    def test_within_reach_for_focused_entity(self):
        """Test that focused entity has within_reach relation."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_table",
            name="table",
            description="A wooden table.",
            location="loc_room"
        )

        player_context = {"posture": "on_surface", "focused_on": "item_table"}
        result = entity_to_dict(item, player_context=player_context)

        self.assertEqual(result["spatial_relation"], "within_reach")

    def test_within_reach_for_item_on_focused_surface(self):
        """Test that items on focused surface have within_reach relation."""
        from utilities.entity_serializer import entity_to_dict

        # Item is ON the table (location = item_table)
        item = Item(
            id="item_cup",
            name="cup",
            description="A ceramic cup.",
            location="item_table"  # Item is on the table
        )

        player_context = {"posture": "on_surface", "focused_on": "item_table"}
        result = entity_to_dict(item, player_context=player_context)

        self.assertEqual(result["spatial_relation"], "within_reach")

    def test_below_for_floor_items_when_elevated(self):
        """Test that floor items are 'below' when player is elevated."""
        from utilities.entity_serializer import entity_to_dict

        # Item is on the floor (location = location id)
        item = Item(
            id="item_sword",
            name="sword",
            description="A sword.",
            location="loc_room"  # On the floor
        )

        player_context = {"posture": "on_surface", "focused_on": "item_table"}
        result = entity_to_dict(item, player_context=player_context)

        self.assertEqual(result["spatial_relation"], "below")

    def test_below_for_floor_items_when_climbing(self):
        """Test that floor items are 'below' when player is climbing."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_rock",
            name="rock",
            description="A rock.",
            location="loc_room"
        )

        player_context = {"posture": "climbing", "focused_on": "item_ladder"}
        result = entity_to_dict(item, player_context=player_context)

        self.assertEqual(result["spatial_relation"], "below")

    def test_nearby_for_other_postures(self):
        """Test that non-elevated postures result in 'nearby'."""
        from utilities.entity_serializer import entity_to_dict

        item = Item(
            id="item_sword",
            name="sword",
            description="A sword.",
            location="loc_room"
        )

        # Cover posture - not elevated, so items are nearby
        player_context = {"posture": "cover", "focused_on": "item_barricade"}
        result = entity_to_dict(item, player_context=player_context)

        self.assertEqual(result["spatial_relation"], "nearby")

    def test_nearby_for_items_in_containers_when_elevated(self):
        """Test that items in containers are 'nearby' even when player is elevated."""
        from utilities.entity_serializer import entity_to_dict

        # Item is IN a container (location starts with item_)
        item = Item(
            id="item_key",
            name="key",
            description="A brass key.",
            location="item_chest"  # In a container
        )

        player_context = {"posture": "on_surface", "focused_on": "item_table"}
        result = entity_to_dict(item, player_context=player_context)

        # Container items aren't "on floor" so they're nearby, not below
        self.assertEqual(result["spatial_relation"], "nearby")


if __name__ == '__main__':
    unittest.main()
