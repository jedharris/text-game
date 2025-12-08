"""Tests for environmental effects system (Phase 2 of Actor Interaction)."""

import unittest
from unittest.mock import Mock, MagicMock

from src.state_manager import Actor, Part, Location, GameState, Metadata
from src.state_accessor import StateAccessor


class TestNeedsBreath(unittest.TestCase):
    """Test needs_breath function."""

    def test_needs_breath_normal_actor(self):
        """Normal actors need to breathe."""
        from behaviors.library.actors.environment import needs_breath

        actor = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=[],
            properties={}
        )

        self.assertTrue(needs_breath(actor))

    def test_needs_breath_construct(self):
        """Constructs don't need to breathe."""
        from behaviors.library.actors.environment import needs_breath

        actor = Actor(
            id="golem",
            name="Stone Golem",
            description="A golem",
            location="loc_test",
            inventory=[],
            properties={"body": {"form": "construct"}}
        )

        self.assertFalse(needs_breath(actor))

    def test_needs_breath_none_actor(self):
        """None actor returns False."""
        from behaviors.library.actors.environment import needs_breath

        self.assertFalse(needs_breath(None))


class TestCheckBreath(unittest.TestCase):
    """Test check_breath function."""

    def setUp(self):
        """Create test actors and parts."""
        self.actor = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_flooded",
            inventory=[],
            properties={
                "health": 100,
                "breath": 60,
                "max_breath": 60
            }
        )

        self.breathable_part = Part(
            id="part_air",
            name="air pocket",
            part_of="loc_flooded",
            properties={"breathable": True}
        )

        self.underwater_part = Part(
            id="part_underwater",
            name="underwater",
            part_of="loc_flooded",
            properties={"breathable": False}
        )

    def test_check_breath_breathable_restores(self):
        """Breath restores to max in breathable area."""
        from behaviors.library.actors.environment import check_breath

        self.actor.properties["breath"] = 30

        result = check_breath(self.actor, self.breathable_part)

        self.assertEqual(self.actor.properties["breath"], 60)
        self.assertIsNone(result)  # No message when just restoring

    def test_check_breath_underwater_decreases(self):
        """Breath decreases by 10 in non-breathable area."""
        from behaviors.library.actors.environment import check_breath

        result = check_breath(self.actor, self.underwater_part)

        self.assertEqual(self.actor.properties["breath"], 50)
        self.assertIsNotNone(result)
        self.assertIn("breath", result.lower())

    def test_check_breath_depleted_causes_damage(self):
        """When breath depleted, take drowning damage."""
        from behaviors.library.actors.environment import check_breath

        self.actor.properties["breath"] = 5

        result = check_breath(self.actor, self.underwater_part)

        # Breath should be 0 or below
        self.assertLessEqual(self.actor.properties["breath"], 0)
        # Should take 10 drowning damage
        self.assertEqual(self.actor.properties["health"], 90)
        self.assertIn("drowning", result.lower())

    def test_check_breath_already_depleted(self):
        """Actor with zero breath continues taking damage."""
        from behaviors.library.actors.environment import check_breath

        self.actor.properties["breath"] = 0

        result = check_breath(self.actor, self.underwater_part)

        self.assertEqual(self.actor.properties["health"], 90)
        self.assertIn("drowning", result.lower())

    def test_check_breath_construct_immune(self):
        """Constructs don't need to track breath."""
        from behaviors.library.actors.environment import check_breath

        construct = Actor(
            id="golem",
            name="Golem",
            description="A golem",
            location="loc_flooded",
            inventory=[],
            properties={"body": {"form": "construct"}}
        )

        result = check_breath(construct, self.underwater_part)

        self.assertIsNone(result)

    def test_check_breath_with_breathing_item(self):
        """Actor with breathing item doesn't lose breath."""
        from behaviors.library.actors.environment import check_breath

        # Give actor a breathing reed
        self.actor.inventory = ["item_reed"]

        # Mock accessor with the item
        mock_accessor = Mock()
        breathing_item = Mock()
        breathing_item.properties = {"provides_breathing": True}
        mock_accessor.get_item.return_value = breathing_item

        result = check_breath(self.actor, self.underwater_part, mock_accessor)

        # Breath should not decrease
        self.assertEqual(self.actor.properties["breath"], 60)
        self.assertIsNone(result)

    def test_check_breath_breathing_item_blocked(self):
        """Breathing item doesn't work if part blocks it."""
        from behaviors.library.actors.environment import check_breath

        self.actor.inventory = ["item_reed"]

        # Part that blocks breathing items (deep water)
        deep_water = Part(
            id="part_deep",
            name="deep water",
            part_of="loc_flooded",
            properties={"breathable": False, "breathing_item_works": False}
        )

        mock_accessor = Mock()
        breathing_item = Mock()
        breathing_item.properties = {"provides_breathing": True}
        mock_accessor.get_item.return_value = breathing_item

        result = check_breath(self.actor, deep_water, mock_accessor)

        # Breath should decrease despite having breathing item
        self.assertEqual(self.actor.properties["breath"], 50)

    def test_check_breath_no_breath_property(self):
        """Actor without breath property gets default max_breath."""
        from behaviors.library.actors.environment import check_breath

        actor = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=[],
            properties={"health": 100}
        )

        result = check_breath(actor, self.underwater_part)

        # Should have initialized breath and decreased it
        self.assertIn("breath", actor.properties)
        self.assertEqual(actor.properties["breath"], 50)


class TestCheckSpores(unittest.TestCase):
    """Test check_spores function."""

    def setUp(self):
        """Create test actor and parts."""
        self.actor = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_basement",
            inventory=[],
            properties={"health": 100}
        )

    def test_check_spores_none(self):
        """No spores means no effect."""
        from behaviors.library.actors.environment import check_spores

        part = Part(
            id="part_safe",
            name="safe area",
            part_of="loc_basement",
            properties={"spore_level": "none"}
        )

        result = check_spores(self.actor, part)

        self.assertIsNone(result)
        self.assertNotIn("conditions", self.actor.properties)

    def test_check_spores_low(self):
        """Low spores apply/increase fungal_infection by 5."""
        from behaviors.library.actors.environment import check_spores

        part = Part(
            id="part_low",
            name="low spore area",
            part_of="loc_basement",
            properties={"spore_level": "low"}
        )

        result = check_spores(self.actor, part)

        self.assertIsNotNone(result)
        self.assertIn("conditions", self.actor.properties)
        self.assertEqual(
            self.actor.properties["conditions"]["fungal_infection"]["severity"],
            5
        )

    def test_check_spores_medium(self):
        """Medium spores apply/increase fungal_infection by 15."""
        from behaviors.library.actors.environment import check_spores

        part = Part(
            id="part_med",
            name="medium spore area",
            part_of="loc_basement",
            properties={"spore_level": "medium"}
        )

        result = check_spores(self.actor, part)

        self.assertEqual(
            self.actor.properties["conditions"]["fungal_infection"]["severity"],
            15
        )

    def test_check_spores_high(self):
        """High spores apply/increase fungal_infection by 30."""
        from behaviors.library.actors.environment import check_spores

        part = Part(
            id="part_high",
            name="high spore area",
            part_of="loc_basement",
            properties={"spore_level": "high"}
        )

        result = check_spores(self.actor, part)

        self.assertEqual(
            self.actor.properties["conditions"]["fungal_infection"]["severity"],
            30
        )

    def test_check_spores_stacks(self):
        """Spore exposure stacks on existing infection."""
        from behaviors.library.actors.environment import check_spores

        # Already infected
        self.actor.properties["conditions"] = {
            "fungal_infection": {"severity": 20}
        }

        part = Part(
            id="part_low",
            name="low spore area",
            part_of="loc_basement",
            properties={"spore_level": "low"}
        )

        result = check_spores(self.actor, part)

        self.assertEqual(
            self.actor.properties["conditions"]["fungal_infection"]["severity"],
            25  # 20 + 5
        )

    def test_check_spores_construct_immune(self):
        """Constructs are immune to spores."""
        from behaviors.library.actors.environment import check_spores

        construct = Actor(
            id="golem",
            name="Golem",
            description="A golem",
            location="loc_basement",
            inventory=[],
            properties={"body": {"form": "construct"}}
        )

        part = Part(
            id="part_high",
            name="high spore area",
            part_of="loc_basement",
            properties={"spore_level": "high"}
        )

        result = check_spores(construct, part)

        self.assertIsNone(result)
        self.assertNotIn("conditions", construct.properties)

    def test_check_spores_no_level_property(self):
        """Part without spore_level has no effect."""
        from behaviors.library.actors.environment import check_spores

        part = Part(
            id="part_normal",
            name="normal area",
            part_of="loc_basement",
            properties={}
        )

        result = check_spores(self.actor, part)

        self.assertIsNone(result)


class TestCheckTemperature(unittest.TestCase):
    """Test check_temperature function."""

    def setUp(self):
        """Create test actor."""
        self.actor = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=[],
            properties={"health": 100}
        )

    def test_check_temperature_normal(self):
        """Normal temperature has no effect."""
        from behaviors.library.actors.environment import check_temperature

        part = Part(
            id="part_normal",
            name="normal area",
            part_of="loc_test",
            properties={"temperature": "normal"}
        )

        result = check_temperature(self.actor, part)

        self.assertIsNone(result)

    def test_check_temperature_freezing(self):
        """Freezing temperature applies hypothermia."""
        from behaviors.library.actors.environment import check_temperature

        part = Part(
            id="part_cold",
            name="cold area",
            part_of="loc_test",
            properties={"temperature": "freezing"}
        )

        result = check_temperature(self.actor, part)

        self.assertIsNotNone(result)
        self.assertIn("conditions", self.actor.properties)
        self.assertIn("hypothermia", self.actor.properties["conditions"])

    def test_check_temperature_burning(self):
        """Burning temperature applies burning condition."""
        from behaviors.library.actors.environment import check_temperature

        part = Part(
            id="part_hot",
            name="hot area",
            part_of="loc_test",
            properties={"temperature": "burning"}
        )

        result = check_temperature(self.actor, part)

        self.assertIn("burning", self.actor.properties["conditions"])

    def test_check_temperature_construct_immune_to_cold(self):
        """Constructs are immune to temperature effects."""
        from behaviors.library.actors.environment import check_temperature

        construct = Actor(
            id="golem",
            name="Golem",
            description="A golem",
            location="loc_test",
            inventory=[],
            properties={"body": {"form": "construct"}}
        )

        part = Part(
            id="part_cold",
            name="cold area",
            part_of="loc_test",
            properties={"temperature": "freezing"}
        )

        result = check_temperature(construct, part)

        self.assertIsNone(result)

    def test_check_temperature_no_property(self):
        """Part without temperature property has no effect."""
        from behaviors.library.actors.environment import check_temperature

        part = Part(
            id="part_normal",
            name="normal area",
            part_of="loc_test",
            properties={}
        )

        result = check_temperature(self.actor, part)

        self.assertIsNone(result)


class TestApplyEnvironmentalEffects(unittest.TestCase):
    """Test apply_environmental_effects function."""

    def setUp(self):
        """Create test actor and part with multiple hazards."""
        self.actor = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_hazard",
            inventory=[],
            properties={
                "health": 100,
                "breath": 60,
                "max_breath": 60
            }
        )

        self.hazardous_part = Part(
            id="part_hazard",
            name="hazardous area",
            part_of="loc_hazard",
            properties={
                "breathable": False,
                "spore_level": "medium",
                "temperature": "freezing"
            }
        )

    def test_apply_all_effects(self):
        """All environmental effects are applied."""
        from behaviors.library.actors.environment import apply_environmental_effects

        messages = apply_environmental_effects(self.actor, self.hazardous_part)

        # Should have breath, spore, and temperature messages
        self.assertTrue(len(messages) >= 3)

        # Breath should have decreased
        self.assertEqual(self.actor.properties["breath"], 50)

        # Should have conditions
        self.assertIn("fungal_infection", self.actor.properties.get("conditions", {}))
        self.assertIn("hypothermia", self.actor.properties.get("conditions", {}))

    def test_apply_effects_none_actor(self):
        """None actor returns empty list."""
        from behaviors.library.actors.environment import apply_environmental_effects

        messages = apply_environmental_effects(None, self.hazardous_part)

        self.assertEqual(messages, [])

    def test_apply_effects_none_part(self):
        """None part returns empty list."""
        from behaviors.library.actors.environment import apply_environmental_effects

        messages = apply_environmental_effects(self.actor, None)

        self.assertEqual(messages, [])


class TestOnEnvironmentalEffect(unittest.TestCase):
    """Test on_environmental_effect turn phase handler."""

    def test_on_environmental_effect_applies_to_all_actors(self):
        """Environmental effects apply to all actors in appropriate parts."""
        from behaviors.library.actors.environment import on_environmental_effect
        from src.state_accessor import StateAccessor

        # Create actors
        player = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_flooded",
            inventory=[],
            properties={
                "health": 100,
                "breath": 60,
                "max_breath": 60,
                "focused_on": "part_underwater"
            }
        )

        npc = Actor(
            id="npc_sailor",
            name="Sailor",
            description="A sailor",
            location="loc_flooded",
            inventory=[],
            properties={
                "health": 80,
                "breath": 30,
                "max_breath": 60,
                "focused_on": "part_underwater"
            }
        )

        underwater_part = Part(
            id="part_underwater",
            name="underwater",
            part_of="loc_flooded",
            properties={"breathable": False}
        )

        location = Location(
            id="loc_flooded",
            name="Flooded Tunnel",
            description="A flooded tunnel",
            properties={"default_part": "part_underwater"}
        )

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_flooded"),
            locations=[location],
            items=[],
            actors={"player": player, "npc_sailor": npc},
            locks=[],
            parts=[underwater_part]
        )

        accessor = StateAccessor(game_state, None)
        context = {"hook": "environmental_effect", "actor_id": "player"}

        result = on_environmental_effect(None, accessor, context)

        # Both actors should have lost breath
        self.assertEqual(player.properties["breath"], 50)
        self.assertEqual(npc.properties["breath"], 20)

        # Result should exist
        self.assertIsNotNone(result)
        self.assertTrue(result.allow)

    def test_on_environmental_effect_actor_not_in_spatial_location(self):
        """Actors not in spatial locations are skipped."""
        from behaviors.library.actors.environment import on_environmental_effect
        from src.state_accessor import StateAccessor

        player = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_room",
            inventory=[],
            properties={"health": 100, "breath": 60}
        )

        # Non-spatial location (no parts)
        location = Location(
            id="loc_room",
            name="Room",
            description="A simple room"
        )

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_room"),
            locations=[location],
            items=[],
            actors={"player": player},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)
        context = {"hook": "environmental_effect", "actor_id": "player"}

        result = on_environmental_effect(None, accessor, context)

        # Breath should be unchanged
        self.assertEqual(player.properties["breath"], 60)

    def test_vocabulary_registers_hook(self):
        """Vocabulary registers on_environmental_effect with environmental_effect hook."""
        from behaviors.library.actors.environment import vocabulary

        self.assertIn("events", vocabulary)
        events = vocabulary["events"]

        # Find the on_environmental_effect event
        env_event = None
        for event in events:
            if event.get("event") == "on_environmental_effect":
                env_event = event
                break

        self.assertIsNotNone(env_event)
        self.assertEqual(env_event["hook"], "environmental_effect")


class TestSporeLevelValues(unittest.TestCase):
    """Test spore level value mappings."""

    def test_spore_level_values(self):
        """Verify spore level severity values."""
        from behaviors.library.actors.environment import SPORE_LEVEL_SEVERITY

        self.assertEqual(SPORE_LEVEL_SEVERITY.get("none", 0), 0)
        self.assertEqual(SPORE_LEVEL_SEVERITY.get("low"), 5)
        self.assertEqual(SPORE_LEVEL_SEVERITY.get("medium"), 15)
        self.assertEqual(SPORE_LEVEL_SEVERITY.get("high"), 30)


class TestTemperatureConditions(unittest.TestCase):
    """Test temperature to condition mappings."""

    def test_temperature_conditions(self):
        """Verify temperature to condition mappings."""
        from behaviors.library.actors.environment import TEMPERATURE_CONDITIONS

        self.assertIn("freezing", TEMPERATURE_CONDITIONS)
        self.assertIn("burning", TEMPERATURE_CONDITIONS)
        self.assertEqual(TEMPERATURE_CONDITIONS["freezing"], "hypothermia")
        self.assertEqual(TEMPERATURE_CONDITIONS["burning"], "burning")


if __name__ == '__main__':
    unittest.main()
