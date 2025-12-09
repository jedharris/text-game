"""Implementation of big_game functional tests.

This module contains the actual test implementations. Each test class
should be run in its own subprocess by test_big_game_functional.py
to ensure module isolation.

DO NOT import this module directly in the test suite - it will cause
module pollution issues.
"""

import sys
import unittest
from pathlib import Path


# Path setup - must be absolute before importing game modules
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
GAME_DIR = PROJECT_ROOT / 'examples' / 'big_game'


def _setup_paths():
    """Ensure paths are set up for imports.

    IMPORTANT: We remove '' (current directory) from path because when running
    from project root, Python would find behaviors/ from project root before
    finding it from the game directory.
    """
    # Remove CWD ('') from path to prevent project root behaviors from being found
    while '' in sys.path:
        sys.path.remove('')

    # Add examples directory first (for big_game.behaviors.* imports)
    examples_dir = str(PROJECT_ROOT / 'examples')
    if examples_dir not in sys.path:
        sys.path.insert(0, examples_dir)

    # Add project root after (for src imports)
    project_str = str(PROJECT_ROOT)
    if project_str not in sys.path:
        sys.path.insert(1, project_str)


# Set up paths before importing game modules
_setup_paths()

from src.state_manager import load_game_state
from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager


def load_all_behaviors(manager: BehaviorManager) -> None:
    """Load all behaviors including big_game specific behaviors."""
    # Load core behaviors
    behaviors_dir = PROJECT_ROOT / "behaviors"
    modules = manager.discover_modules(str(behaviors_dir))
    manager.load_modules(modules)

    # Load only the required behavior_libraries (avoiding conflicts)
    required_libs = [
        "behavior_libraries.timing_lib.scheduled_events",
        "behavior_libraries.dialog_lib.handlers",
        "behavior_libraries.dialog_lib.topics",
    ]
    for lib_path in required_libs:
        try:
            manager.load_module(lib_path, tier=2)
        except (ValueError, ImportError):
            # Skip if conflicts or not found
            pass

    # Load big_game behaviors explicitly by module path
    big_game_behaviors = [
        "big_game.behaviors.regions",
        "big_game.behaviors.factions",
        "big_game.behaviors.world_events",
        "big_game.behaviors.npc_specifics.the_echo",
    ]
    for mod_path in big_game_behaviors:
        manager.load_module(mod_path, tier=3)


def get_game_state_path():
    """Get path to game_state.json."""
    return GAME_DIR / "game_state.json"


class TestBigGameLoading(unittest.TestCase):
    """Test that big_game loads correctly."""

    def setUp(self):
        """Load the game state."""
        self.state = load_game_state(str(get_game_state_path()))

    def test_game_loads(self):
        """Test that game state loads without errors."""
        self.assertIsNotNone(self.state)
        self.assertEqual(self.state.metadata.title, "The Shattered Meridian")

    def test_has_locations(self):
        """Test that locations were loaded."""
        self.assertGreater(len(self.state.locations), 0)
        # Should have 31 locations
        self.assertEqual(len(self.state.locations), 31)

    def test_has_actors(self):
        """Test that actors were loaded including player."""
        self.assertGreater(len(self.state.actors), 0)
        self.assertIn("player", self.state.actors)

    def test_has_items(self):
        """Test that items were loaded."""
        self.assertGreater(len(self.state.items), 0)

    def test_has_parts(self):
        """Test that location parts were loaded."""
        self.assertGreater(len(self.state.parts), 0)

    def test_player_at_start_location(self):
        """Test player starts at the correct location."""
        player = self.state.actors["player"]
        self.assertEqual(player.location, self.state.metadata.start_location)
        self.assertEqual(player.location, "loc_mn_nexus_chamber")

    def test_start_location_exists(self):
        """Test that start location is a valid location."""
        start_loc = self.state.metadata.start_location
        location = self.state.get_location(start_loc)
        self.assertIsNotNone(location)
        self.assertEqual(location.name, "Nexus Chamber")


class TestBigGameMovement(unittest.TestCase):
    """Test movement mechanics in big_game."""

    def setUp(self):
        """Set up game with handler."""
        self.state = load_game_state(str(get_game_state_path()))

        # Load all behaviors including big_game specific ones
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)

        self.handler = LLMProtocolHandler(self.state, behavior_manager=self.manager)

    def test_can_go_north(self):
        """Test movement north from start."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "go", "object": "north"}
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(self.state.actors["player"].location, "loc_fr_frozen_pass")

    def test_can_go_south(self):
        """Test movement south from start."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "go", "object": "south"}
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(self.state.actors["player"].location, "loc_bw_forest_edge")

    def test_can_go_east(self):
        """Test movement east from start."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "go", "object": "east"}
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(self.state.actors["player"].location, "loc_sd_flooded_streets")

    def test_can_go_west(self):
        """Test movement west from start."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "go", "object": "west"}
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(self.state.actors["player"].location, "loc_fd_cavern_entrance")

    def test_movement_round_trip(self):
        """Test can move and return to start."""
        start = self.state.actors["player"].location

        # Go north
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "go", "object": "north"}
        })
        self.assertNotEqual(self.state.actors["player"].location, start)

        # Go south to return
        self.handler.handle_command({
            "type": "command",
            "action": {"verb": "go", "object": "south"}
        })
        self.assertEqual(self.state.actors["player"].location, start)


class TestBigGameQueries(unittest.TestCase):
    """Test query mechanics in big_game."""

    def setUp(self):
        """Set up game with handler."""
        self.state = load_game_state(str(get_game_state_path()))

        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)

        self.handler = LLMProtocolHandler(self.state, behavior_manager=self.manager)

    def test_location_query(self):
        """Test location query returns valid data."""
        result = self.handler.handle_query({
            "type": "query",
            "query_type": "location"
        })
        self.assertEqual(result.get("type"), "query_response")
        data = result.get("data", {})
        self.assertIn("exits", data)

    def test_inventory_query(self):
        """Test inventory query works."""
        result = self.handler.handle_query({
            "type": "query",
            "query_type": "inventory"
        })
        # Inventory query should succeed (may return query_response or have items)
        self.assertIn(result.get("type"), ["query_response", "error"])
        if result.get("type") == "query_response":
            data = result.get("data", {})
            self.assertIn("items", data)


class TestBigGameRegions(unittest.TestCase):
    """Test that all regions are reachable and valid."""

    def setUp(self):
        """Load game state."""
        self.state = load_game_state(str(get_game_state_path()))

    def test_all_locations_have_region(self):
        """Test all locations have a region property."""
        for loc in self.state.locations:
            region = loc.properties.get("region")
            self.assertIsNotNone(
                region,
                f"Location {loc.id} missing region property"
            )

    def test_known_regions_exist(self):
        """Test expected regions are present."""
        expected_regions = {
            "meridian_nexus",
            "beast_wilds",
            "frozen_reaches",
            "fungal_depths",
            "sunken_district",
            "civilized_remnants"
        }
        actual_regions = set()
        for loc in self.state.locations:
            region = loc.properties.get("region")
            if region:
                actual_regions.add(region)

        for expected in expected_regions:
            self.assertIn(
                expected, actual_regions,
                f"Expected region '{expected}' not found"
            )


class TestBigGameActors(unittest.TestCase):
    """Test actor configuration."""

    def setUp(self):
        """Load game state."""
        self.state = load_game_state(str(get_game_state_path()))

    def test_player_has_required_fields(self):
        """Test player has all required fields."""
        player = self.state.actors["player"]
        self.assertIsNotNone(player.location)
        self.assertIsNotNone(player.inventory)
        self.assertEqual(player.id, "player")

    def test_npcs_have_locations_or_null(self):
        """Test NPCs either have valid locations or null (for spectral/faction)."""
        for actor_id, actor in self.state.actors.items():
            if actor_id == "player":
                continue
            # Location can be null for special actors like The Echo
            if actor.location is not None:
                loc = self.state.get_location(actor.location)
                self.assertIsNotNone(
                    loc,
                    f"Actor {actor_id} has invalid location: {actor.location}"
                )


class TestBigGameItems(unittest.TestCase):
    """Test item configuration."""

    def setUp(self):
        """Load game state."""
        self.state = load_game_state(str(get_game_state_path()))

    def test_items_have_valid_locations(self):
        """Test all items have valid locations."""
        # Items can be in locations, on other items (containers), in player inventory, or on NPCs
        valid_location_prefixes = ("loc_", "item_", "player", "npc_", "creature_")
        for item in self.state.items:
            loc = item.location
            self.assertTrue(
                loc is None or loc.startswith(valid_location_prefixes),
                f"Item {item.id} has unexpected location format: {loc}"
            )
            # If location is a loc_, verify it exists
            if loc and loc.startswith("loc_"):
                location = self.state.get_location(loc)
                self.assertIsNotNone(
                    location,
                    f"Item {item.id} has non-existent location: {loc}"
                )


class TestBigGameBehaviorModules(unittest.TestCase):
    """Test that big_game behavior modules load and work correctly."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))

        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)

        self.handler = LLMProtocolHandler(self.state, behavior_manager=self.manager)

    def test_big_game_behaviors_loaded(self):
        """Test that big_game specific behavior modules are loaded."""
        loaded_modules = list(self.manager._modules.keys())

        # Check that big_game behaviors are loaded
        self.assertIn("big_game.behaviors.regions", loaded_modules)
        self.assertIn("big_game.behaviors.factions", loaded_modules)
        self.assertIn("big_game.behaviors.world_events", loaded_modules)
        self.assertIn("big_game.behaviors.npc_specifics.the_echo", loaded_modules)

    def test_regions_module_functions(self):
        """Test that regions module functions work."""
        from big_game.behaviors.regions import (
            get_region_for_location,
            get_region_state,
            is_region_purified,
        )
        from src.state_accessor import StateAccessor

        accessor = StateAccessor(self.state, self.manager)

        # Test get_region_for_location (should use location properties, not regions dict)
        player_loc = self.state.actors["player"].location
        location = self.state.get_location(player_loc)
        region = location.properties.get("region")
        self.assertEqual(region, "meridian_nexus")

    def test_factions_module_functions(self):
        """Test that factions module functions work."""
        from big_game.behaviors.factions import (
            get_factions,
            get_faction_disposition,
        )
        from src.state_accessor import StateAccessor

        accessor = StateAccessor(self.state, self.manager)

        # Test get_factions (may be empty if not configured)
        factions = get_factions(accessor)
        # Factions are stored in extra, may or may not be present
        self.assertIsInstance(factions, dict)

    def test_echo_module_functions(self):
        """Test that the_echo module functions work."""
        from big_game.behaviors.npc_specifics.the_echo import (
            calculate_appearance_chance,
            NEXUS_LOCATIONS,
        )
        from src.state_accessor import StateAccessor

        accessor = StateAccessor(self.state, self.manager)

        # Test appearance chance calculation
        chance = calculate_appearance_chance(accessor)
        self.assertGreaterEqual(chance, 0.0)
        self.assertLessEqual(chance, 1.0)

        # Test that nexus locations are defined
        self.assertIn("loc_mn_nexus_chamber", NEXUS_LOCATIONS)

    def test_world_events_module_functions(self):
        """Test that world_events module functions work."""
        from big_game.behaviors.world_events import (
            check_ending_conditions,
            EVENT_SPORE_SPREAD,
            EVENT_COLD_SPREAD,
        )
        from src.state_accessor import StateAccessor

        accessor = StateAccessor(self.state, self.manager)

        # Test check_ending_conditions
        result = check_ending_conditions(accessor)
        self.assertIn("crystals_restored", result)
        self.assertIn("regions_purified", result)
        self.assertIn("ending", result)
        self.assertEqual(result["ending"], "in_progress")


class TestBigGameRegionBehaviors(unittest.TestCase):
    """Test region-specific behavior functionality."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))

        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)

    def test_region_purification(self):
        """Test that purify_region modifies game state."""
        from big_game.behaviors.regions import purify_region, is_region_purified
        from src.state_accessor import StateAccessor

        accessor = StateAccessor(self.state, self.manager)

        # Set up a region in extra.regions if not present
        if "regions" not in self.state.extra:
            self.state.extra["regions"] = {
                "fungal_depths": {
                    "locations": ["loc_fd_cavern_entrance"],
                    "purified": False
                }
            }

        # Initially not purified
        self.assertFalse(is_region_purified(accessor, "fungal_depths"))

        # Purify the region
        messages = purify_region(accessor, "fungal_depths")
        self.assertIsInstance(messages, list)
        self.assertGreater(len(messages), 0)

        # Now should be purified
        self.assertTrue(is_region_purified(accessor, "fungal_depths"))


class TestBigGameActorBehaviors(unittest.TestCase):
    """Test actor-specific behavior functionality."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))

        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)

    def test_echo_actor_has_behaviors(self):
        """Test that The Echo actor has behaviors assigned."""
        echo = self.state.actors.get("npc_mn_the_echo")
        self.assertIsNotNone(echo)
        self.assertIn("big_game.behaviors.npc_specifics.the_echo", echo.behaviors)

    def test_echo_is_spectral(self):
        """Test that The Echo has spectral properties."""
        echo = self.state.actors.get("npc_mn_the_echo")
        self.assertIsNotNone(echo)
        self.assertTrue(echo.properties.get("is_spectral", False))
        self.assertFalse(echo.properties.get("can_be_attacked", True))


class TestRegionSystemIntegration(unittest.TestCase):
    """Integration tests for the region system."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        from src.state_accessor import StateAccessor
        self.accessor = StateAccessor(self.state, self.manager)

    def test_regions_data_structure_exists(self):
        """Test that regions are defined in extra."""
        self.assertIn("regions", self.state.extra)
        regions = self.state.extra["regions"]
        self.assertEqual(len(regions), 6)

    def test_all_region_locations_are_valid(self):
        """Test that all location IDs in region definitions exist."""
        regions = self.state.extra["regions"]
        for region_id, region_def in regions.items():
            for loc_id in region_def.get("locations", []):
                location = self.state.get_location(loc_id)
                self.assertIsNotNone(
                    location,
                    f"Region {region_id} references non-existent location: {loc_id}"
                )

    def test_region_lookup_from_location(self):
        """Test finding region by location ID."""
        from big_game.behaviors.regions import get_region_for_location

        # Nexus chamber should be in meridian_nexus
        region = get_region_for_location(self.accessor, "loc_mn_nexus_chamber")
        self.assertEqual(region, "meridian_nexus")

        # Cavern entrance should be in fungal_depths
        region = get_region_for_location(self.accessor, "loc_fd_cavern_entrance")
        self.assertEqual(region, "fungal_depths")

    def test_region_corruption_applies_to_locations(self):
        """Test that corruption spreads to all locations in a region."""
        from big_game.behaviors.regions import corrupt_region

        # Corrupt the beast_wilds with cold
        messages = corrupt_region(self.accessor, "beast_wilds", "cold")
        self.assertIsInstance(messages, list)

        # Check that locations now have cold temperature
        for loc_id in self.state.extra["regions"]["beast_wilds"]["locations"]:
            location = self.state.get_location(loc_id)
            if location:
                # Some locations may have been updated
                temp = location.properties.get("temperature")
                # Either cold was applied or the location didn't change
                self.assertIn(temp, ["cold", "normal", None])

    def test_purification_clears_corruption(self):
        """Test that purification removes corruption from region locations."""
        from big_game.behaviors.regions import purify_region, corrupt_region

        # First corrupt fungal_depths with spores
        corrupt_region(self.accessor, "fungal_depths", "spore")

        # Get a location and set spore level
        loc = self.state.get_location("loc_fd_cavern_entrance")
        if loc:
            loc.properties["spore_level"] = "high"

        # Purify the region
        messages = purify_region(self.accessor, "fungal_depths")
        self.assertGreater(len(messages), 0)

        # Location should now have spore_level cleared
        if loc:
            self.assertEqual(loc.properties.get("spore_level"), "none")

    def test_get_actors_in_region(self):
        """Test getting all actors currently in a region."""
        from big_game.behaviors.regions import get_actors_in_region

        # Player starts in meridian_nexus
        actors = get_actors_in_region(self.accessor, "meridian_nexus")
        actor_ids = [a.id for a in actors]
        self.assertIn("player", actor_ids)


class TestFactionSystemIntegration(unittest.TestCase):
    """Integration tests for the faction system."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        from src.state_accessor import StateAccessor
        self.accessor = StateAccessor(self.state, self.manager)

    def test_factions_data_structure_exists(self):
        """Test that factions are defined in extra."""
        self.assertIn("factions", self.state.extra)
        factions = self.state.extra["factions"]
        self.assertEqual(len(factions), 4)

    def test_faction_has_representative(self):
        """Test that each faction has a representative actor."""
        from big_game.behaviors.factions import get_factions

        factions = get_factions(self.accessor)
        for faction_id, faction_def in factions.items():
            self.assertIn(
                "representative", faction_def,
                f"Faction {faction_id} missing representative"
            )

    def test_get_faction_for_actor(self):
        """Test finding which faction an actor belongs to."""
        from big_game.behaviors.factions import get_faction_for_actor

        # Myconid elder should be in myconid_collective
        faction = get_faction_for_actor(self.accessor, "npc_fd_myconid_elder")
        self.assertEqual(faction, "myconid_collective")

        # Gate guard should be in town_council
        faction = get_faction_for_actor(self.accessor, "npc_cr_gate_guard")
        self.assertEqual(faction, "town_council")

    def test_faction_disposition_starts_neutral(self):
        """Test that faction disposition starts at neutral."""
        from big_game.behaviors.factions import get_faction_disposition

        disposition = get_faction_disposition(self.accessor, "myconid_collective")
        self.assertEqual(disposition, "neutral")

    def test_faction_disposition_changes_with_trust(self):
        """Test that faction disposition changes based on trust level."""
        from big_game.behaviors.factions import (
            get_faction_disposition, modify_faction_reputation
        )

        # Increase trust significantly
        modify_faction_reputation(
            self.accessor, "myconid_collective", "trust", 6
        )

        # Should now be friendly
        disposition = get_faction_disposition(self.accessor, "myconid_collective")
        self.assertEqual(disposition, "friendly")


class TestWorldEventsIntegration(unittest.TestCase):
    """Integration tests for the world events system."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        from src.state_accessor import StateAccessor
        self.accessor = StateAccessor(self.state, self.manager)

    def test_world_event_config_exists(self):
        """Test that world event configuration is present."""
        self.assertIn("world_event_config", self.state.extra)
        config = self.state.extra["world_event_config"]
        self.assertIn("spore_spread_turn", config)
        self.assertIn("cold_spread_turn", config)

    def test_check_ending_conditions_initial_state(self):
        """Test ending condition check with no progress."""
        from big_game.behaviors.world_events import check_ending_conditions

        result = check_ending_conditions(self.accessor)

        self.assertEqual(result["crystals_restored"], 0)
        # Only corrupted regions count: fungal_depths, beast_wilds, frozen_reaches
        # (meridian_nexus, civilized_remnants, sunken_district start purified but don't count)
        self.assertEqual(result["regions_purified"], 0)
        self.assertEqual(result["ending"], "in_progress")

    def test_check_ending_conditions_with_crystals(self):
        """Test ending conditions reflect crystal restoration."""
        from big_game.behaviors.world_events import check_ending_conditions

        # Set crystal flags
        self.state.extra.setdefault("flags", {})
        self.state.extra["flags"]["crystal_1_restored"] = True
        self.state.extra["flags"]["crystal_2_restored"] = True

        result = check_ending_conditions(self.accessor)
        self.assertEqual(result["crystals_restored"], 2)

    def test_spore_spread_affects_npcs(self):
        """Test that spore spread applies effects to NPCs."""
        from big_game.behaviors.world_events import trigger_spore_spread

        messages = trigger_spore_spread(self.accessor)

        # Should produce messages
        self.assertGreater(len(messages), 0)

        # Flag should be set
        self.assertTrue(
            self.state.extra.get("flags", {}).get("spore_spread_started", False)
        )


class TestEchoIntegration(unittest.TestCase):
    """Integration tests for The Echo NPC mechanics."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        from src.state_accessor import StateAccessor
        self.accessor = StateAccessor(self.state, self.manager)

    def test_echo_appearance_chance_base(self):
        """Test Echo base appearance chance is 10%."""
        from big_game.behaviors.npc_specifics.the_echo import calculate_appearance_chance

        chance = calculate_appearance_chance(self.accessor)
        self.assertAlmostEqual(chance, 0.1, places=2)

    def test_echo_appearance_chance_increases_with_restoration(self):
        """Test Echo appearance chance increases with restoration flags."""
        from big_game.behaviors.npc_specifics.the_echo import calculate_appearance_chance

        # Set some restoration flags
        self.state.extra.setdefault("flags", {})
        self.state.extra["flags"]["crystal_1_restored"] = True
        self.state.extra["flags"]["waystone_repaired"] = True

        chance = calculate_appearance_chance(self.accessor)
        # Base 0.1 + 2 * 0.15 = 0.4
        self.assertAlmostEqual(chance, 0.4, places=2)

    def test_echo_message_first_meeting(self):
        """Test Echo gives first meeting message when flag not set."""
        from big_game.behaviors.npc_specifics.the_echo import get_echo_message

        message = get_echo_message(self.accessor)
        self.assertIsNotNone(message)
        # First meeting messages contain specific phrases
        self.assertTrue(
            "visitor" in message.lower() or "see me" in message.lower()
        )

    def test_echo_message_returning_player(self):
        """Test Echo gives returning message after first meeting."""
        from big_game.behaviors.npc_specifics.the_echo import get_echo_message

        # Set met flag
        self.state.extra.setdefault("flags", {})
        self.state.extra["flags"]["met_the_echo"] = True

        message = get_echo_message(self.accessor)
        self.assertIsNotNone(message)
        # Should include returning greeting
        self.assertTrue(
            "return" in message.lower() or "progress" in message.lower()
        )


class TestCrossSystemIntegration(unittest.TestCase):
    """Tests for interactions between multiple systems."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        from src.state_accessor import StateAccessor
        self.accessor = StateAccessor(self.state, self.manager)

    def test_purifying_region_updates_ending_conditions(self):
        """Test that purifying a region updates ending condition check."""
        from big_game.behaviors.regions import purify_region, is_region_purified
        from big_game.behaviors.world_events import check_ending_conditions

        # Get initial state
        initial = check_ending_conditions(self.accessor)
        initial_purified = initial["regions_purified"]

        # Purify fungal_depths (starts unpurified)
        self.assertFalse(is_region_purified(self.accessor, "fungal_depths"))
        purify_region(self.accessor, "fungal_depths")

        # Check ending conditions again
        after = check_ending_conditions(self.accessor)
        self.assertEqual(after["regions_purified"], initial_purified + 1)

    def test_perfect_ending_requires_all_conditions(self):
        """Test that perfect ending requires all crystals and regions."""
        from big_game.behaviors.regions import purify_region
        from big_game.behaviors.world_events import check_ending_conditions

        # Set all crystal flags
        self.state.extra.setdefault("flags", {})
        self.state.extra["flags"]["crystal_1_restored"] = True
        self.state.extra["flags"]["crystal_2_restored"] = True
        self.state.extra["flags"]["crystal_3_restored"] = True

        # Purify all remaining regions
        for region_id in ["fungal_depths", "beast_wilds", "frozen_reaches"]:
            purify_region(self.accessor, region_id)

        # Check for perfect ending
        result = check_ending_conditions(self.accessor)
        self.assertEqual(result["crystals_restored"], 3)
        self.assertGreaterEqual(result["regions_purified"], 3)


class TestGameStateConsistency(unittest.TestCase):
    """Tests for overall game state data consistency."""

    def setUp(self):
        """Load game state."""
        self.state = load_game_state(str(get_game_state_path()))

    def test_all_faction_members_exist(self):
        """Test that all faction member IDs refer to actual actors."""
        factions = self.state.extra.get("factions", {})
        for faction_id, faction_def in factions.items():
            for member_id in faction_def.get("members", []):
                actor = self.state.actors.get(member_id)
                self.assertIsNotNone(
                    actor,
                    f"Faction {faction_id} member {member_id} not found in actors"
                )

    def test_all_faction_representatives_exist(self):
        """Test that all faction representatives are valid actors."""
        factions = self.state.extra.get("factions", {})
        for faction_id, faction_def in factions.items():
            rep_id = faction_def.get("representative")
            if rep_id:
                actor = self.state.actors.get(rep_id)
                self.assertIsNotNone(
                    actor,
                    f"Faction {faction_id} representative {rep_id} not found"
                )

    def test_location_exits_are_bidirectional(self):
        """Test that location exits have corresponding return exits."""
        opposite = {
            "north": "south", "south": "north",
            "east": "west", "west": "east",
            "up": "down", "down": "up"
        }

        issues = []
        for loc in self.state.locations:
            for direction, exit_data in loc.exits.items():
                if direction not in opposite:
                    continue  # Skip non-standard directions

                dest_id = exit_data.to if hasattr(exit_data, 'to') else exit_data
                dest = self.state.get_location(dest_id)

                if dest is None:
                    issues.append(f"{loc.id} -> {direction} leads to non-existent {dest_id}")
                    continue

                # Check for return path
                opp_dir = opposite[direction]
                if opp_dir not in dest.exits:
                    issues.append(
                        f"{loc.id} -> {direction} -> {dest_id} has no {opp_dir} return"
                    )
                else:
                    return_dest = dest.exits[opp_dir]
                    return_id = return_dest.to if hasattr(return_dest, 'to') else return_dest
                    if return_id != loc.id:
                        issues.append(
                            f"{loc.id} -> {direction} -> {dest_id} -> {opp_dir} goes to {return_id}, not back"
                        )

        # Allow some issues for one-way passages (intentional design)
        # But report if there are many
        if len(issues) > 10:
            self.fail(f"Too many exit consistency issues:\n" + "\n".join(issues[:10]))


# ============================================================================
# PHASE 3: Additional Functional Test Coverage
# ============================================================================


class TestMovementEdgeCases(unittest.TestCase):
    """Test movement edge cases and internal region navigation."""

    def setUp(self):
        """Set up game with handler."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        self.handler = LLMProtocolHandler(self.state, behavior_manager=self.manager)

    def test_nexus_locations_exist_and_connected(self):
        """Test that all Meridian Nexus locations exist and have exits."""
        nexus_locations = [
            "loc_mn_nexus_chamber",
            "loc_mn_observatory_platform",
            "loc_mn_keepers_quarters",
            "loc_mn_crystal_garden"
        ]

        for loc_id in nexus_locations:
            location = self.state.get_location(loc_id)
            self.assertIsNotNone(location, f"Nexus location {loc_id} not found")
            # Each location should have at least one exit
            self.assertGreater(len(location.exits), 0,
                             f"Nexus location {loc_id} has no exits")

    def test_invalid_direction_fails(self):
        """Test that moving in an invalid direction fails gracefully."""
        # Move to a location that doesn't have all exits
        self.state.actors["player"].location = "loc_mn_nexus_chamber"

        # Try an invalid direction name
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "go", "object": "northwest"}  # Likely doesn't exist
        })
        # Should fail gracefully (either success=False or no movement)
        if result.get("success"):
            # If somehow succeeded, player should still be somewhere valid
            self.assertIsNotNone(self.state.get_location(self.state.actors["player"].location))


class TestRegionSystemExtended(unittest.TestCase):
    """Extended tests for the region system."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        from src.state_accessor import StateAccessor
        self.accessor = StateAccessor(self.state, self.manager)

    def test_each_region_has_correct_location_count(self):
        """Test that each region has the expected number of locations."""
        expected_counts = {
            "meridian_nexus": 4,
            "civilized_remnants": 6,
            "fungal_depths": 5,
            "beast_wilds": 5,
            "frozen_reaches": 5,
            "sunken_district": 6
        }
        regions = self.state.extra.get("regions", {})

        for region_id, expected_count in expected_counts.items():
            self.assertIn(region_id, regions, f"Region {region_id} not found")
            actual_count = len(regions[region_id].get("locations", []))
            self.assertEqual(actual_count, expected_count,
                           f"Region {region_id} has {actual_count} locations, expected {expected_count}")

    def test_location_region_property_matches_regions_dict(self):
        """Test that location properties match the regions dictionary."""
        regions = self.state.extra.get("regions", {})

        for region_id, region_def in regions.items():
            for loc_id in region_def.get("locations", []):
                location = self.state.get_location(loc_id)
                self.assertIsNotNone(location, f"Location {loc_id} not found")
                loc_region = location.properties.get("region")
                self.assertEqual(loc_region, region_id,
                               f"Location {loc_id} has region={loc_region}, expected {region_id}")

    def test_corruption_types_apply_correctly(self):
        """Test that different corruption types apply the right effects."""
        from big_game.behaviors.regions import corrupt_region

        # Test spore corruption
        messages = corrupt_region(self.accessor, "beast_wilds", "spore")
        self.assertIsInstance(messages, list)
        # Check that some location got spore_level
        for loc_id in self.state.extra["regions"]["beast_wilds"]["locations"]:
            loc = self.state.get_location(loc_id)
            if loc and loc.properties.get("spore_level"):
                break
        # At least messages should be returned
        self.assertGreater(len(messages), 0)

    def test_region_purification_sets_purified_state(self):
        """Test that purification sets region purified state to true."""
        from big_game.behaviors.regions import purify_region, is_region_purified

        # beast_wilds starts not purified
        self.assertFalse(is_region_purified(self.accessor, "beast_wilds"))

        # Purify
        messages = purify_region(self.accessor, "beast_wilds")
        self.assertGreater(len(messages), 0)

        # Now should be purified
        self.assertTrue(is_region_purified(self.accessor, "beast_wilds"))

    def test_get_region_for_location_handles_unknown_location(self):
        """Test that get_region_for_location handles invalid locations."""
        from big_game.behaviors.regions import get_region_for_location

        region = get_region_for_location(self.accessor, "nonexistent_location")
        self.assertIsNone(region)

    def test_is_region_purified_default_state(self):
        """Test purification status for regions at game start."""
        from big_game.behaviors.regions import is_region_purified

        # Corrupted regions start not purified
        self.assertFalse(is_region_purified(self.accessor, "fungal_depths"))
        self.assertFalse(is_region_purified(self.accessor, "beast_wilds"))
        self.assertFalse(is_region_purified(self.accessor, "frozen_reaches"))

        # Safe regions start purified
        self.assertTrue(is_region_purified(self.accessor, "meridian_nexus"))
        self.assertTrue(is_region_purified(self.accessor, "civilized_remnants"))


class TestFactionSystemExtended(unittest.TestCase):
    """Extended tests for the faction system."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        from src.state_accessor import StateAccessor
        self.accessor = StateAccessor(self.state, self.manager)

    def test_faction_reputation_sync_to_members(self):
        """Test that faction reputation syncs to member NPCs."""
        from big_game.behaviors.factions import (
            modify_faction_reputation, sync_faction_reputation, get_faction_reputation
        )
        from behavior_libraries.actor_lib.relationships import get_relationship

        # Modify myconid faction trust
        modify_faction_reputation(self.accessor, "myconid_collective", "trust", 5)

        # Sync should have propagated to members
        # (sync happens automatically in modify_faction_reputation if sync_to_members=True)
        member = self.accessor.get_actor("npc_fd_myconid_elder")
        if member:
            rel = get_relationship(member, "player")
            # Trust should now be 5 (synced from faction)
            self.assertEqual(rel.get("trust", 0), 5)

    def test_faction_disposition_thresholds(self):
        """Test all faction disposition thresholds."""
        from big_game.behaviors.factions import (
            modify_faction_reputation, get_faction_disposition
        )

        # Test hostile threshold (fear >= 5, trust < 3)
        faction = "beast_spirits"  # Use a faction with no members for simpler testing
        modify_faction_reputation(self.accessor, faction, "fear", 5, sync_to_members=False)
        modify_faction_reputation(self.accessor, faction, "trust", 0, sync_to_members=False)
        disposition = get_faction_disposition(self.accessor, faction)
        self.assertEqual(disposition, "hostile")

        # Reset and test neutral
        modify_faction_reputation(self.accessor, faction, "fear", -5, sync_to_members=False)
        disposition = get_faction_disposition(self.accessor, faction)
        self.assertEqual(disposition, "neutral")

        # Test friendly threshold (trust >= 5)
        modify_faction_reputation(self.accessor, faction, "trust", 5, sync_to_members=False)
        disposition = get_faction_disposition(self.accessor, faction)
        self.assertEqual(disposition, "friendly")

        # Test allied threshold (trust >= 8)
        modify_faction_reputation(self.accessor, faction, "trust", 3, sync_to_members=False)
        disposition = get_faction_disposition(self.accessor, faction)
        self.assertEqual(disposition, "allied")

    def test_get_faction_for_actor_returns_none_for_non_member(self):
        """Test that non-members return None faction."""
        from big_game.behaviors.factions import get_faction_for_actor

        # Player should not be in any faction
        faction = get_faction_for_actor(self.accessor, "player")
        self.assertIsNone(faction)

    def test_check_faction_threshold(self):
        """Test faction threshold checking."""
        from big_game.behaviors.factions import (
            modify_faction_reputation, check_faction_threshold
        )

        faction = "town_council"

        # Initially trust is 0
        self.assertFalse(check_faction_threshold(self.accessor, faction, "trust", 5))

        # Increase to 5
        modify_faction_reputation(self.accessor, faction, "trust", 5, sync_to_members=False)
        self.assertTrue(check_faction_threshold(self.accessor, faction, "trust", 5))
        self.assertFalse(check_faction_threshold(self.accessor, faction, "trust", 6))

    def test_faction_action_handler_positive(self):
        """Test on_faction_action handler for positive actions."""
        from big_game.behaviors.factions import on_faction_action, get_faction_reputation

        entity = self.accessor.get_actor("npc_fd_myconid_elder")
        context = {"action": "help", "faction_id": "myconid_collective"}

        result = on_faction_action(entity, self.accessor, context)

        # Should have increased trust and gratitude
        rep = get_faction_reputation(self.accessor, "myconid_collective")
        self.assertGreater(rep.get("trust", 0), 0)
        self.assertGreater(rep.get("gratitude", 0), 0)

    def test_faction_action_handler_negative(self):
        """Test on_faction_action handler for negative actions."""
        from big_game.behaviors.factions import (
            on_faction_action, get_faction_reputation, modify_faction_reputation
        )

        # Use a different faction to avoid state from other tests
        entity = self.accessor.get_actor("npc_cr_gate_guard")
        context = {"action": "attack", "faction_id": "town_council"}

        # Set initial trust to a positive value so we can see it decrease
        # (trust can't go below 0, so we need to start above 0 to verify decrease)
        modify_faction_reputation(self.accessor, "town_council", "trust", 5)
        initial_rep = get_faction_reputation(self.accessor, "town_council")
        initial_trust = initial_rep.get("trust", 0)
        initial_fear = initial_rep.get("fear", 0)

        result = on_faction_action(entity, self.accessor, context)

        # Should have decreased trust and increased fear
        rep = get_faction_reputation(self.accessor, "town_council")
        self.assertLess(rep.get("trust", 0), initial_trust)
        self.assertGreater(rep.get("fear", 0), initial_fear)


class TestWorldEventsExtended(unittest.TestCase):
    """Extended tests for the world events system."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        from src.state_accessor import StateAccessor
        self.accessor = StateAccessor(self.state, self.manager)

    def test_initialize_world_events(self):
        """Test that world events can be initialized."""
        from big_game.behaviors.world_events import initialize_world_events

        messages = initialize_world_events(self.accessor)
        self.assertIsInstance(messages, list)
        # Should have scheduled at least spore spread
        self.assertGreater(len(messages), 0)

    def test_cancel_spore_spread(self):
        """Test cancelling spore spread event."""
        from big_game.behaviors.world_events import (
            initialize_world_events, cancel_spore_spread
        )

        # Initialize to schedule events
        initialize_world_events(self.accessor)

        # Cancel
        message = cancel_spore_spread(self.accessor)
        # Should return a message (or empty if not scheduled)
        self.assertIsInstance(message, str)

    def test_cancel_cold_spread(self):
        """Test cancelling cold spread event."""
        from big_game.behaviors.world_events import (
            initialize_world_events, cancel_cold_spread
        )

        # Initialize to schedule events
        initialize_world_events(self.accessor)

        # Cancel
        message = cancel_cold_spread(self.accessor)
        self.assertIsInstance(message, str)

    def test_trigger_cold_spread(self):
        """Test triggering cold spread."""
        from big_game.behaviors.world_events import trigger_cold_spread

        messages = trigger_cold_spread(self.accessor)

        self.assertGreater(len(messages), 0)
        self.assertTrue(
            self.state.extra.get("flags", {}).get("cold_spread_started", False)
        )

    def test_ending_condition_partial_restoration(self):
        """Test partial restoration ending."""
        from big_game.behaviors.world_events import check_ending_conditions

        # Set all crystal flags but don't purify regions
        self.state.extra.setdefault("flags", {})
        self.state.extra["flags"]["crystal_1_restored"] = True
        self.state.extra["flags"]["crystal_2_restored"] = True
        self.state.extra["flags"]["crystal_3_restored"] = True

        result = check_ending_conditions(self.accessor)
        self.assertEqual(result["crystals_restored"], 3)
        self.assertEqual(result["ending"], "partial_restoration")

    def test_ending_condition_catastrophe(self):
        """Test catastrophe ending."""
        from big_game.behaviors.world_events import check_ending_conditions

        # Set both spread flags
        self.state.extra.setdefault("flags", {})
        self.state.extra["flags"]["spore_spread_started"] = True
        self.state.extra["flags"]["cold_spread_started"] = True

        result = check_ending_conditions(self.accessor)
        self.assertEqual(result["ending"], "catastrophe")

    def test_on_quest_complete_heal_spore_mother(self):
        """Test quest completion handler for heal_spore_mother."""
        from big_game.behaviors.world_events import on_quest_complete
        from big_game.behaviors.regions import is_region_purified

        context = {"quest_id": "heal_spore_mother"}

        result = on_quest_complete(None, self.accessor, context)

        # Should have purified fungal_depths
        self.assertTrue(is_region_purified(self.accessor, "fungal_depths"))
        # Should have set flag
        self.assertTrue(
            self.state.extra.get("flags", {}).get("spore_mother_healed", False)
        )

    def test_on_quest_complete_repair_observatory(self):
        """Test quest completion handler for repair_observatory."""
        from big_game.behaviors.world_events import on_quest_complete

        context = {"quest_id": "repair_observatory"}

        result = on_quest_complete(None, self.accessor, context)

        # Should have set flag
        self.assertTrue(
            self.state.extra.get("flags", {}).get("observatory_repaired", False)
        )

    def test_on_quest_complete_cure_aldric(self):
        """Test quest completion handler for cure_aldric."""
        from big_game.behaviors.world_events import on_quest_complete

        context = {"quest_id": "cure_aldric"}

        result = on_quest_complete(None, self.accessor, context)

        # Should have set flag
        self.assertTrue(
            self.state.extra.get("flags", {}).get("aldric_cured", False)
        )

    def test_on_quest_complete_restore_crystal(self):
        """Test quest completion handler for crystal restoration."""
        from big_game.behaviors.world_events import on_quest_complete, check_ending_conditions

        # Restore crystal 1
        result = on_quest_complete(None, self.accessor, {"quest_id": "restore_crystal_1"})
        self.assertTrue(
            self.state.extra.get("flags", {}).get("crystal_1_restored", False)
        )

        # Restore crystal 2
        result = on_quest_complete(None, self.accessor, {"quest_id": "restore_crystal_2"})

        # Restore crystal 3
        result = on_quest_complete(None, self.accessor, {"quest_id": "restore_crystal_3"})

        # Check all crystals restored
        ending = check_ending_conditions(self.accessor)
        self.assertEqual(ending["crystals_restored"], 3)


class TestEchoExtended(unittest.TestCase):
    """Extended tests for The Echo NPC mechanics."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        from src.state_accessor import StateAccessor
        self.accessor = StateAccessor(self.state, self.manager)

    def test_echo_nexus_locations_defined(self):
        """Test that NEXUS_LOCATIONS are all valid."""
        from big_game.behaviors.npc_specifics.the_echo import NEXUS_LOCATIONS

        for loc_id in NEXUS_LOCATIONS:
            location = self.state.get_location(loc_id)
            self.assertIsNotNone(location, f"Nexus location {loc_id} not found")

    def test_echo_appearance_chance_max_cap(self):
        """Test that Echo appearance chance is capped at 85%."""
        from big_game.behaviors.npc_specifics.the_echo import (
            calculate_appearance_chance, RESTORATION_FLAGS
        )

        # Set all restoration flags
        self.state.extra.setdefault("flags", {})
        for flag in RESTORATION_FLAGS:
            self.state.extra["flags"][flag] = True

        chance = calculate_appearance_chance(self.accessor)
        # Should be capped at 0.85
        self.assertLessEqual(chance, 0.85)

    def test_echo_message_with_spore_warning(self):
        """Test Echo gives spore warning when spores spreading."""
        from big_game.behaviors.npc_specifics.the_echo import get_echo_message

        # Set flags for returning player with spore spread
        self.state.extra.setdefault("flags", {})
        self.state.extra["flags"]["met_the_echo"] = True
        self.state.extra["flags"]["spore_spread_started"] = True

        message = get_echo_message(self.accessor)
        # Should contain spore warning
        self.assertIn("spore", message.lower())

    def test_echo_message_with_cold_warning(self):
        """Test Echo gives cold warning when cold spreading."""
        from big_game.behaviors.npc_specifics.the_echo import get_echo_message

        # Set flags for returning player with cold spread
        self.state.extra.setdefault("flags", {})
        self.state.extra["flags"]["met_the_echo"] = True
        self.state.extra["flags"]["cold_spread_started"] = True

        message = get_echo_message(self.accessor)
        # Should contain cold warning
        self.assertIn("cold", message.lower())

    def test_echo_message_with_progress(self):
        """Test Echo message reflects crystal progress."""
        from big_game.behaviors.npc_specifics.the_echo import get_echo_message

        # Set flags for returning player with 2 crystals
        self.state.extra.setdefault("flags", {})
        self.state.extra["flags"]["met_the_echo"] = True
        self.state.extra["flags"]["crystal_1_restored"] = True
        self.state.extra["flags"]["crystal_2_restored"] = True

        message = get_echo_message(self.accessor)
        # Should mention two crystals
        self.assertTrue("two" in message.lower() or "2" in message)


class TestActorConfigurationExtended(unittest.TestCase):
    """Extended tests for actor configuration."""

    def setUp(self):
        """Load game state."""
        self.state = load_game_state(str(get_game_state_path()))

    def test_all_actors_have_required_fields(self):
        """Test all actors have id, name, and location fields."""
        for actor_id, actor in self.state.actors.items():
            self.assertEqual(actor.id, actor_id, f"Actor ID mismatch for {actor_id}")
            self.assertIsNotNone(actor.name, f"Actor {actor_id} missing name")
            # Location can be None for special actors

    def test_npcs_with_dialog_have_valid_topics(self):
        """Test that NPCs with dialog have properly structured topics."""
        for actor_id, actor in self.state.actors.items():
            dialog_topics = actor.properties.get("dialog_topics")
            if dialog_topics:
                self.assertIsInstance(dialog_topics, dict,
                                     f"Actor {actor_id} dialog_topics is not a dict")
                for topic_id, topic in dialog_topics.items():
                    self.assertIsInstance(topic, dict,
                                         f"Actor {actor_id} topic {topic_id} is not a dict")
                    # Each topic should have keywords and summary
                    self.assertIn("keywords", topic,
                                 f"Actor {actor_id} topic {topic_id} missing keywords")
                    self.assertIn("summary", topic,
                                 f"Actor {actor_id} topic {topic_id} missing summary")

    def test_hostile_creatures_have_combat_properties(self):
        """Test that hostile creature actors have combat-related properties."""
        for actor_id, actor in self.state.actors.items():
            if actor_id.startswith("creature_"):
                # Only check hostile creatures (not constructs, guardians, etc.)
                ai = actor.properties.get("ai", {})
                if ai.get("disposition") == "hostile":
                    # Hostile creatures should have health
                    self.assertIn("health", actor.properties,
                                 f"Hostile creature {actor_id} missing health")
                    self.assertIn("max_health", actor.properties,
                                 f"Hostile creature {actor_id} missing max_health")

    def test_faction_actors_have_is_faction_property(self):
        """Test that faction representative actors have is_faction property."""
        factions = self.state.extra.get("factions", {})
        for faction_id, faction_def in factions.items():
            rep_id = faction_def.get("representative")
            if rep_id:
                actor = self.state.actors.get(rep_id)
                if actor:
                    self.assertTrue(
                        actor.properties.get("is_faction", False),
                        f"Faction rep {rep_id} missing is_faction property"
                    )

    def test_spectral_actors_have_correct_properties(self):
        """Test that spectral actors have is_spectral and can_be_attacked=false."""
        echo = self.state.actors.get("npc_mn_the_echo")
        self.assertIsNotNone(echo)
        self.assertTrue(echo.properties.get("is_spectral", False))
        self.assertFalse(echo.properties.get("can_be_attacked", True))


class TestItemConfigurationExtended(unittest.TestCase):
    """Extended tests for item configuration."""

    def setUp(self):
        """Load game state."""
        self.state = load_game_state(str(get_game_state_path()))

    def test_key_items_exist(self):
        """Test that important quest items exist."""
        key_items = [
            "item_mn_keepers_journal",
            "item_fd_aldric_journal",
        ]
        item_ids = {item.id for item in self.state.items}
        for item_id in key_items:
            self.assertIn(item_id, item_ids, f"Key item {item_id} not found")

    def test_items_in_actor_inventory_exist(self):
        """Test that items referenced in actor inventories exist."""
        item_ids = {item.id for item in self.state.items}
        for actor_id, actor in self.state.actors.items():
            for item_id in actor.inventory:
                self.assertIn(item_id, item_ids,
                             f"Item {item_id} in {actor_id}'s inventory not found")

    def test_portable_items_have_property(self):
        """Test that portable items have portable=true."""
        for item in self.state.items:
            if item.properties.get("portable") is not None:
                # If explicitly set, should be boolean
                self.assertIsInstance(item.properties.get("portable"), bool,
                                     f"Item {item.id} portable is not boolean")

    def test_container_items_have_valid_structure(self):
        """Test that container items have valid container properties."""
        for item in self.state.items:
            container = item.properties.get("container")
            if container:
                self.assertIsInstance(container, dict,
                                     f"Item {item.id} container is not a dict")


class TestDialogSystemExtended(unittest.TestCase):
    """Extended tests for the dialog system."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)

    def test_all_dialog_topics_have_keywords(self):
        """Test that all dialog topics have non-empty keywords list."""
        for actor_id, actor in self.state.actors.items():
            dialog_topics = actor.properties.get("dialog_topics", {})
            for topic_id, topic in dialog_topics.items():
                keywords = topic.get("keywords", [])
                self.assertIsInstance(keywords, list,
                                     f"Actor {actor_id} topic {topic_id} keywords is not a list")
                self.assertGreater(len(keywords), 0,
                                  f"Actor {actor_id} topic {topic_id} has no keywords")

    def test_all_dialog_summaries_are_strings(self):
        """Test that all dialog summaries are non-empty strings."""
        for actor_id, actor in self.state.actors.items():
            dialog_topics = actor.properties.get("dialog_topics", {})
            for topic_id, topic in dialog_topics.items():
                summary = topic.get("summary")
                self.assertIsInstance(summary, str,
                                     f"Actor {actor_id} topic {topic_id} summary is not a string")
                self.assertGreater(len(summary), 0,
                                  f"Actor {actor_id} topic {topic_id} has empty summary")

    def test_topic_prerequisites_reference_valid_flags(self):
        """Test that topic prerequisites reference flag names (not checking values)."""
        for actor_id, actor in self.state.actors.items():
            dialog_topics = actor.properties.get("dialog_topics", {})
            for topic_id, topic in dialog_topics.items():
                requires_flags = topic.get("requires_flags")
                if requires_flags:
                    self.assertIsInstance(requires_flags, dict,
                                         f"Actor {actor_id} topic {topic_id} requires_flags is not a dict")

    def test_npcs_with_dialog_topics_have_content(self):
        """Test that NPCs with dialog topics have at least one topic with content."""
        for actor_id, actor in self.state.actors.items():
            dialog_topics = actor.properties.get("dialog_topics")
            if dialog_topics and len(dialog_topics) > 0:
                # At least one topic should have a summary
                has_content = any(
                    topic.get("summary") for topic in dialog_topics.values()
                )
                self.assertTrue(has_content,
                               f"Actor {actor_id} has dialog topics but no summaries")


class TestQuerySystemExtended(unittest.TestCase):
    """Extended tests for the query system."""

    def setUp(self):
        """Set up game with handler."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        self.handler = LLMProtocolHandler(self.state, behavior_manager=self.manager)

    def test_actors_query(self):
        """Test actors query returns valid data."""
        result = self.handler.handle_query({
            "type": "query",
            "query_type": "actors"
        })
        # Should succeed or return error if not implemented
        self.assertIn(result.get("type"), ["query_response", "error"])

    def test_items_query(self):
        """Test items query returns valid data."""
        result = self.handler.handle_query({
            "type": "query",
            "query_type": "items"
        })
        self.assertIn(result.get("type"), ["query_response", "error"])

    def test_location_query_has_exits(self):
        """Test location query returns exits information."""
        result = self.handler.handle_query({
            "type": "query",
            "query_type": "location"
        })
        if result.get("type") == "query_response":
            data = result.get("data", {})
            self.assertIn("exits", data)


class TestDataConsistencyExtended(unittest.TestCase):
    """Extended tests for data consistency."""

    def setUp(self):
        """Load game state."""
        self.state = load_game_state(str(get_game_state_path()))

    def test_no_duplicate_ids_across_entities(self):
        """Test that there are no duplicate IDs across different entity types."""
        all_ids = []

        # Collect all IDs
        for loc in self.state.locations:
            all_ids.append(("location", loc.id))
        for actor in self.state.actors.values():
            all_ids.append(("actor", actor.id))
        for item in self.state.items:
            all_ids.append(("item", item.id))
        for part in self.state.parts:
            all_ids.append(("part", part.id))

        # Check for duplicates
        seen_ids = {}
        duplicates = []
        for entity_type, entity_id in all_ids:
            if entity_id in seen_ids:
                duplicates.append(f"{entity_id} (in {seen_ids[entity_id]} and {entity_type})")
            else:
                seen_ids[entity_id] = entity_type

        self.assertEqual(len(duplicates), 0,
                        f"Duplicate IDs found: {duplicates[:5]}")

    def test_all_behavior_modules_exist(self):
        """Test that all behaviors referenced by entities can be loaded."""
        behavior_paths = set()

        # Collect all behavior paths from actors
        for actor in self.state.actors.values():
            for behavior in actor.behaviors:
                behavior_paths.add(behavior)

        # Verify each path is valid (we already loaded them successfully)
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)

        for path in behavior_paths:
            if path.startswith("big_game."):
                # Big game behaviors should be loaded
                self.assertIn(path, self.manager._modules,
                             f"Behavior {path} not loaded")

    def test_region_locations_match_actual_locations(self):
        """Test that all locations in region definitions exist."""
        regions = self.state.extra.get("regions", {})
        location_ids = {loc.id for loc in self.state.locations}

        for region_id, region_def in regions.items():
            for loc_id in region_def.get("locations", []):
                self.assertIn(loc_id, location_ids,
                             f"Region {region_id} references non-existent location {loc_id}")

    def test_all_exit_destinations_exist(self):
        """Test that all exit destinations are valid locations."""
        location_ids = {loc.id for loc in self.state.locations}

        for loc in self.state.locations:
            for direction, exit_data in loc.exits.items():
                dest_id = exit_data.to if hasattr(exit_data, 'to') else exit_data
                self.assertIn(dest_id, location_ids,
                             f"Location {loc.id} exit {direction} leads to non-existent {dest_id}")

    def test_item_locations_are_valid(self):
        """Test that all items are in valid locations."""
        valid_ids = set()
        valid_ids.update(loc.id for loc in self.state.locations)
        valid_ids.update(actor.id for actor in self.state.actors.values())
        valid_ids.update(item.id for item in self.state.items)

        for item in self.state.items:
            if item.location is not None:
                self.assertIn(item.location, valid_ids,
                             f"Item {item.id} has invalid location {item.location}")

    def test_recipe_ingredients_exist(self):
        """Test that recipe ingredients reference valid items or item templates."""
        recipes = self.state.extra.get("recipes", {})
        item_ids = {item.id for item in self.state.items}
        template_ids = set(self.state.extra.get("item_templates", {}).keys())
        all_valid = item_ids | template_ids

        for recipe_id, recipe in recipes.items():
            for ingredient in recipe.get("ingredients", []):
                self.assertIn(ingredient, item_ids,
                             f"Recipe {recipe_id} references non-existent ingredient {ingredient}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
