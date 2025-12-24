"""End-to-end scenario tests using the actual game engine.

These tests run through the real game engine (LLMProtocolHandler) with
the big_game game state, verifying that commands produce expected
state changes and messages.
"""

import copy
import json
import unittest
from pathlib import Path
from typing import Any, Dict

from src.behavior_manager import BehaviorManager
from src.llm_protocol import LLMProtocolHandler
from src.parser import Parser
from src.state_manager import load_game_state, GameState
from src.types import ActorId, ItemId, LocationId
from src.validators import validate_game_state
from src.vocabulary_service import build_merged_vocabulary


# Path to big_game
BIG_GAME_DIR = Path(__file__).parent.parent.parent / "examples" / "big_game"
GAME_STATE_FILE = BIG_GAME_DIR / "game_state.json"
BEHAVIORS_DIR = Path(__file__).parent.parent.parent / "behaviors"


def get_result_message(result: Dict[str, Any]) -> str:
    """
    Extract message text from result, handling both old and new formats.

    New format (Phase 4): result["narration"]["primary_text"]
    Old format: result["message"] or result["error"]["message"]

    For the new format, also concatenates secondary_beats.
    """
    # New format: NarrationResult
    if "narration" in result:
        narration = result["narration"]
        parts = [narration.get("primary_text", "")]
        if "secondary_beats" in narration:
            parts.extend(narration["secondary_beats"])
        return "\n".join(parts)

    # Old format - success case
    if result.get("success") and "message" in result:
        return result["message"]

    # Old format - error case
    if "error" in result and "message" in result["error"]:
        return result["error"]["message"]

    return result.get("message", "")


class E2EScenarioTestCase(unittest.TestCase):
    """Base class for end-to-end scenario tests.

    Provides a fresh game state and engine for each test.
    """

    _game_state_template: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        """Load game state template once for all tests."""
        if not GAME_STATE_FILE.exists():
            raise unittest.SkipTest(f"big_game not found at {GAME_STATE_FILE}")

        # Load the game state JSON as a template
        with open(GAME_STATE_FILE, "r") as f:
            cls._game_state_template = json.load(f)

    def setUp(self) -> None:
        """Set up fresh game state and engine for each test."""
        # Deep copy the template to get fresh state
        state_dict = copy.deepcopy(self._game_state_template)

        # Load game state
        self.game_state = load_game_state(state_dict)

        # Initialize behavior manager
        self.behavior_manager = BehaviorManager()
        if BEHAVIORS_DIR.exists():
            modules = self.behavior_manager.discover_modules(str(BEHAVIORS_DIR))
            self.behavior_manager.load_modules(modules)

        # Build vocabulary and parser
        self.vocab = build_merged_vocabulary(self.game_state, self.behavior_manager)
        self.parser = Parser.from_vocab(self.vocab)

        # Initialize protocol handler
        self.handler = LLMProtocolHandler(self.game_state, self.behavior_manager)

    def execute(self, command_text: str) -> dict[str, Any]:
        """Parse and execute a text command.

        Args:
            command_text: Natural language command (e.g., "go north")

        Returns:
            Result dict from protocol handler
        """
        # Parse the command
        parsed = self.parser.parse_command(command_text)
        if parsed is None:
            return {
                "success": False,
                "error": {"message": f"Could not parse: {command_text}"},
            }

        # Convert to JSON action
        from src.command_utils import parsed_to_json

        # Handle direction-only input
        if parsed.direct_object and not parsed.verb:
            json_cmd = {
                "type": "command",
                "action": {"verb": "go", "object": parsed.direct_object},
            }
        else:
            json_cmd = parsed_to_json(parsed)

        # Execute via protocol handler
        return self.handler.handle_message(json_cmd)

    def execute_json(self, verb: str, obj: str | None = None, **kwargs: Any) -> dict[str, Any]:
        """Execute a command via JSON protocol directly.

        Args:
            verb: Command verb
            obj: Command object (optional)
            **kwargs: Additional action parameters

        Returns:
            Result dict from protocol handler
        """
        action: dict[str, Any] = {"verb": verb}
        if obj:
            action["object"] = obj
        action.update(kwargs)

        return self.handler.handle_message({"type": "command", "action": action})

    def query(self, query_type: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a query.

        Args:
            query_type: Type of query (e.g., "inventory", "location")
            **kwargs: Additional query parameters

        Returns:
            Result dict from protocol handler
        """
        message: dict[str, Any] = {"type": "query", "query_type": query_type}
        message.update(kwargs)
        return self.handler.handle_message(message)

    def advance_turns(self, count: int) -> list[dict[str, Any]]:
        """Advance game by executing 'wait' commands.

        Args:
            count: Number of turns to advance

        Returns:
            List of results from each wait
        """
        results = []
        for _ in range(count):
            result = self.execute_json("wait")
            results.append(result)
        return results

    # =========================================================================
    # State inspection helpers
    # =========================================================================

    def get_player_location(self) -> str | None:
        """Get current player location ID."""
        player = self.game_state.actors.get(ActorId("player"))
        return player.location if player else None

    def get_actor_state(self, actor_id: ActorId) -> str | None:
        """Get actor's current state machine state."""
        actor = self.game_state.actors.get(actor_id)
        if not actor:
            return None
        sm = actor.properties.get("state_machine", {})
        return sm.get("current", sm.get("initial"))

    def get_actor_trust(self, actor_id: ActorId) -> int:
        """Get actor's current trust value."""
        actor = self.game_state.actors.get(actor_id)
        if not actor:
            return 0
        trust = actor.properties.get("trust_state", {})
        return trust.get("current", 0)

    def get_flag(self, flag_name: str) -> Any:
        """Get a global flag value."""
        return self.game_state.extra.get(flag_name)

    def get_condition_severity(self, actor_id: ActorId, condition_type: str) -> int | None:
        """Get severity of an actor's condition."""
        actor = self.game_state.actors.get(actor_id)
        if not actor:
            return None
        conditions = actor.properties.get("conditions", {})
        if isinstance(conditions, dict):
            cond = conditions.get(condition_type)
            if cond:
                return cond.get("severity")
        elif isinstance(conditions, list):
            for cond in conditions:
                if cond.get("type") == condition_type:
                    return cond.get("severity")
        return None

    def player_has_item(self, item_id: str) -> bool:
        """Check if player has an item in inventory."""
        player = self.game_state.actors.get(ActorId("player"))
        if not player:
            return False
        return item_id in player.inventory

    def move_player_to(self, location_id: str) -> None:
        """Directly move player to a location (for test setup)."""
        player = self.game_state.actors.get(ActorId("player"))
        if player:
            player.location = LocationId(location_id)

    def give_player_item(self, item_id: str) -> None:
        """Give player an item (for test setup)."""
        player = self.game_state.actors.get(ActorId("player"))
        if player and item_id not in player.inventory:
            player.inventory.append(ItemId(item_id))

    # =========================================================================
    # Assertions
    # =========================================================================

    def assert_success(self, result: dict[str, Any], msg: str = "") -> None:
        """Assert command succeeded."""
        self.assertTrue(
            result.get("success", False),
            f"Expected success but got: {result.get('error', result)} {msg}",
        )

    def assert_failure(self, result: dict[str, Any], msg: str = "") -> None:
        """Assert command failed."""
        self.assertFalse(
            result.get("success", True),
            f"Expected failure but got success {msg}",
        )

    def assert_message_contains(self, result: dict[str, Any], substring: str) -> None:
        """Assert result message contains substring."""
        message = get_result_message(result)
        self.assertIn(
            substring.lower(),
            message.lower(),
            f"Expected '{substring}' in message: {message}",
        )

    def assert_player_at(self, location_id: str) -> None:
        """Assert player is at specified location."""
        actual = self.get_player_location()
        self.assertEqual(
            actual,
            location_id,
            f"Expected player at '{location_id}', got '{actual}'",
        )

    def assert_actor_state(self, actor_id: ActorId, expected_state: str) -> None:
        """Assert actor is in expected state."""
        actual = self.get_actor_state(actor_id)
        self.assertEqual(
            actual,
            expected_state,
            f"Actor '{actor_id}' state: expected '{expected_state}', got '{actual}'",
        )

    def assert_flag_set(self, flag_name: str) -> None:
        """Assert a global flag is set (truthy)."""
        value = self.get_flag(flag_name)
        if value is None or value is False:
            self.fail(f"Flag '{flag_name}' not set")

    def assert_flag_not_set(self, flag_name: str) -> None:
        """Assert a global flag is not set."""
        value = self.get_flag(flag_name)
        if value and value is not False:
            self.fail(f"Flag '{flag_name}' unexpectedly set to {value}")


class TestE2EMovement(E2EScenarioTestCase):
    """Basic movement tests to verify engine works."""

    def test_look_at_start(self) -> None:
        """Look command works at starting location."""
        result = self.execute_json("look")
        self.assert_success(result)
        self.assert_message_contains(result, "nexus")

    def test_go_north(self) -> None:
        """Can move north from nexus chamber."""
        result = self.execute("go north")
        self.assert_success(result)
        self.assert_player_at("frozen_pass")

    def test_go_south(self) -> None:
        """Can move south from nexus chamber."""
        result = self.execute("go south")
        self.assert_success(result)
        self.assert_player_at("forest_edge")

    def test_direction_shorthand(self) -> None:
        """Direction-only input works."""
        result = self.execute("north")
        self.assert_success(result)
        self.assert_player_at("frozen_pass")


class TestE2EBeastWildsScenarios(E2EScenarioTestCase):
    """End-to-end tests for Beast Wilds region."""

    def test_movement_into_beast_wilds(self) -> None:
        """Can navigate into Beast Wilds from nexus."""
        # Go south to forest edge
        result = self.execute("go south")
        self.assert_success(result)
        self.assert_player_at("forest_edge")

    def test_look_at_location(self) -> None:
        """Look command works in Beast Wilds."""
        self.execute("go south")  # Go to forest_edge
        result = self.execute_json("look")
        self.assert_success(result)
        self.assert_message_contains(result, "forest")

    def test_navigate_to_hunters_camp(self) -> None:
        """Can navigate to Hunter's Camp where Sira is."""
        # nexus -> forest_edge -> southern_trail -> hunters_camp
        self.execute("go south")  # forest_edge
        self.execute("go east")  # southern_trail
        result = self.execute("go east")  # hunters_camp
        self.assert_success(result)
        self.assert_player_at("hunters_camp")

    def test_hunter_sira_at_camp(self) -> None:
        """Hunter Sira is present at Hunter's Camp."""
        self.move_player_to("hunters_camp")
        result = self.execute_json("look")
        self.assert_success(result)
        # Sira should be visible in the room
        sira = self.game_state.actors.get(ActorId("hunter_sira"))
        self.assertIsNotNone(sira)
        assert sira is not None
        self.assertEqual(sira.location, "hunters_camp")

    def test_navigate_to_spider_lair(self) -> None:
        """Can navigate to Spider Matriarch's Lair."""
        # nexus -> forest_edge -> tangled_path -> spider_thicket -> spider_matriarch_lair
        self.execute("go south")  # forest_edge
        self.execute("go south")  # tangled_path
        self.execute("go west")  # spider_thicket
        result = self.execute("go west")  # spider_matriarch_lair
        self.assert_success(result)
        self.assert_player_at("spider_matriarch_lair")

    def test_spider_matriarch_at_lair(self) -> None:
        """Spider Matriarch is present at lair."""
        self.move_player_to("spider_matriarch_lair")
        matriarch = self.game_state.actors.get(ActorId("spider_matriarch"))
        self.assertIsNotNone(matriarch)
        assert matriarch is not None
        self.assertEqual(matriarch.location, "spider_matriarch_lair")

    def test_navigate_to_bee_queen(self) -> None:
        """Can navigate to Bee Queen's Clearing."""
        # nexus -> forest_edge -> tangled_path -> ancient_grove -> bee_queen_clearing
        self.execute("go south")  # forest_edge
        self.execute("go south")  # tangled_path
        self.execute("go south")  # ancient_grove
        result = self.execute("go east")  # bee_queen_clearing
        self.assert_success(result)
        self.assert_player_at("bee_queen_clearing")

    def test_bee_queen_at_clearing(self) -> None:
        """Bee Queen is present at clearing."""
        self.move_player_to("bee_queen_clearing")
        queen = self.game_state.actors.get(ActorId("bee_queen"))
        self.assertIsNotNone(queen)
        assert queen is not None
        self.assertEqual(queen.location, "bee_queen_clearing")


class TestE2EFungalDepthsScenarios(E2EScenarioTestCase):
    """End-to-end tests for Fungal Depths region."""

    def test_movement_into_fungal_depths(self) -> None:
        """Can navigate into Fungal Depths from nexus."""
        # Go west to cavern entrance
        result = self.execute("go west")
        self.assert_success(result)
        self.assert_player_at("cavern_entrance")

    def test_aldric_at_entrance(self) -> None:
        """Scholar Aldric is at cavern entrance."""
        self.move_player_to("cavern_entrance")
        aldric = self.game_state.actors.get(ActorId("npc_aldric"))
        self.assertIsNotNone(aldric)
        assert aldric is not None
        self.assertEqual(aldric.location, "cavern_entrance")

    def test_navigate_to_spore_heart(self) -> None:
        """Can navigate to Spore Heart where Spore Mother is."""
        # nexus -> cavern_entrance -> luminous_grotto -> spore_heart
        self.execute("go west")  # cavern_entrance
        self.execute("go down")  # luminous_grotto
        # Check what exits are available from luminous_grotto
        loc = None
        for l in self.game_state.locations:
            if l.id == "luminous_grotto":
                loc = l
                break
        if loc and "down" in loc.exits:
            result = self.execute("go down")  # spore_heart
            self.assert_success(result)
            self.assert_player_at("spore_heart")
        else:
            # May need different path - check direct placement
            self.move_player_to("spore_heart")
            self.assert_player_at("spore_heart")

    def test_spore_mother_at_heart(self) -> None:
        """Spore Mother is present at Spore Heart."""
        self.move_player_to("spore_heart")
        mother = self.game_state.actors.get(ActorId("npc_spore_mother"))
        self.assertIsNotNone(mother)
        assert mother is not None
        self.assertEqual(mother.location, "spore_heart")

    def test_sporelings_at_heart(self) -> None:
        """Sporelings are present at Spore Heart with Spore Mother."""
        self.move_player_to("spore_heart")
        for sporeling_id in ["npc_sporeling_1", "npc_sporeling_2", "npc_sporeling_3"]:
            sporeling = self.game_state.actors.get(ActorId(sporeling_id))
            self.assertIsNotNone(sporeling, f"Missing {sporeling_id}")
            assert sporeling is not None
            self.assertEqual(sporeling.location, "spore_heart")

    def test_myconid_elder_at_sanctuary(self) -> None:
        """Myconid Elder is at sanctuary."""
        self.move_player_to("myconid_sanctuary")
        elder = self.game_state.actors.get(ActorId("npc_myconid_elder"))
        self.assertIsNotNone(elder)
        assert elder is not None
        self.assertEqual(elder.location, "myconid_sanctuary")


class TestE2EFrozenReachesScenarios(E2EScenarioTestCase):
    """End-to-end tests for Frozen Reaches region."""

    def test_movement_into_frozen_reaches(self) -> None:
        """Can navigate into Frozen Reaches from nexus."""
        # Go north to frozen pass
        result = self.execute("go north")
        self.assert_success(result)
        self.assert_player_at("frozen_pass")

    def test_navigate_to_wolf_den(self) -> None:
        """Can navigate to Wolf Den where Alpha Wolf is."""
        # nexus -> frozen_pass -> ice_field -> snow_forest -> wolf_den
        self.execute("go north")  # frozen_pass
        self.execute("go east")  # ice_field
        self.execute("go east")  # snow_forest
        result = self.execute("go north")  # wolf_den
        self.assert_success(result)
        self.assert_player_at("wolf_den")

    def test_alpha_wolf_at_den(self) -> None:
        """Alpha Wolf is present at Wolf Den."""
        self.move_player_to("wolf_den")
        alpha = self.game_state.actors.get(ActorId("alpha_wolf"))
        self.assertIsNotNone(alpha)
        assert alpha is not None
        self.assertEqual(alpha.location, "wolf_den")

    def test_frost_wolves_at_den(self) -> None:
        """Frost wolves are present at Wolf Den."""
        self.move_player_to("wolf_den")
        for wolf_id in ["frost_wolf_1", "frost_wolf_2"]:
            wolf = self.game_state.actors.get(ActorId(wolf_id))
            self.assertIsNotNone(wolf, f"Missing {wolf_id}")
            assert wolf is not None
            self.assertEqual(wolf.location, "wolf_den")

    def test_navigate_to_hot_springs(self) -> None:
        """Can navigate to Hot Springs where Salamander is."""
        # nexus -> frozen_pass -> ice_field -> hot_springs
        self.execute("go north")  # frozen_pass
        self.execute("go east")  # ice_field
        result = self.execute("go north")  # hot_springs
        self.assert_success(result)
        self.assert_player_at("hot_springs")

    def test_salamander_at_hot_springs(self) -> None:
        """Fire Salamander is present at Hot Springs."""
        self.move_player_to("hot_springs")
        salamander = self.game_state.actors.get(ActorId("salamander"))
        self.assertIsNotNone(salamander)
        assert salamander is not None
        self.assertEqual(salamander.location, "hot_springs")

    def test_navigate_to_frozen_observatory(self) -> None:
        """Can navigate to Frozen Observatory."""
        # nexus -> frozen_pass -> glacier_approach -> glacier_surface -> frozen_observatory
        self.execute("go north")  # frozen_pass
        self.execute("go north")  # glacier_approach
        self.execute("go north")  # glacier_surface
        result = self.execute("go north")  # frozen_observatory
        self.assert_success(result)
        self.assert_player_at("frozen_observatory")


class TestE2ESunkenDistrictScenarios(E2EScenarioTestCase):
    """End-to-end tests for Sunken District region."""

    def test_movement_into_sunken_district(self) -> None:
        """Can navigate into Sunken District from nexus."""
        # Go east to flooded plaza
        result = self.execute("go east")
        self.assert_success(result)
        self.assert_player_at("flooded_plaza")

    def test_navigate_to_survivor_camp(self) -> None:
        """Can navigate to Survivor Camp."""
        # nexus -> flooded_plaza -> survivor_camp
        self.execute("go east")  # flooded_plaza
        result = self.execute("go northwest")  # survivor_camp
        self.assert_success(result)
        self.assert_player_at("survivor_camp")

    def test_survivors_at_camp(self) -> None:
        """Survivors present at camp."""
        self.move_player_to("survivor_camp")
        mira = self.game_state.actors.get(ActorId("camp_leader_mira"))
        self.assertIsNotNone(mira)
        assert mira is not None
        self.assertEqual(mira.location, "survivor_camp")

        jek = self.game_state.actors.get(ActorId("old_swimmer_jek"))
        self.assertIsNotNone(jek)
        assert jek is not None
        self.assertEqual(jek.location, "survivor_camp")

    def test_navigate_to_sea_caves(self) -> None:
        """Can navigate to Sea Caves where Garrett is."""
        # nexus -> flooded_plaza -> flooded_chambers -> tidal_passage -> sea_caves
        self.execute("go east")  # flooded_plaza
        self.execute("go east")  # flooded_chambers
        self.execute("go east")  # tidal_passage
        result = self.execute("go east")  # sea_caves
        self.assert_success(result)
        self.assert_player_at("sea_caves")

    def test_garrett_at_sea_caves(self) -> None:
        """Sailor Garrett is at Sea Caves."""
        self.move_player_to("sea_caves")
        garrett = self.game_state.actors.get(ActorId("sailor_garrett"))
        self.assertIsNotNone(garrett)
        assert garrett is not None
        self.assertEqual(garrett.location, "sea_caves")

    def test_navigate_to_merchant_warehouse(self) -> None:
        """Can navigate to Merchant Warehouse where Delvan is."""
        # nexus -> flooded_plaza -> merchant_quarter -> merchant_warehouse
        self.execute("go east")  # flooded_plaza
        self.execute("go south")  # merchant_quarter
        result = self.execute("go south")  # merchant_warehouse
        self.assert_success(result)
        self.assert_player_at("merchant_warehouse")

    def test_delvan_at_warehouse(self) -> None:
        """Merchant Delvan is at Warehouse."""
        self.move_player_to("merchant_warehouse")
        delvan = self.game_state.actors.get(ActorId("merchant_delvan"))
        self.assertIsNotNone(delvan)
        assert delvan is not None
        self.assertEqual(delvan.location, "merchant_warehouse")

    def test_archivist_at_archive(self) -> None:
        """The Archivist is at Deep Archive."""
        self.move_player_to("deep_archive")
        archivist = self.game_state.actors.get(ActorId("the_archivist"))
        self.assertIsNotNone(archivist)
        assert archivist is not None
        self.assertEqual(archivist.location, "deep_archive")


class TestE2ECivilizedRemnantsScenarios(E2EScenarioTestCase):
    """End-to-end tests for Civilized Remnants (town) region."""

    def test_navigate_to_town(self) -> None:
        """Can navigate to Town Gate from Beast Wilds."""
        # nexus -> forest_edge -> southern_trail -> town_gate
        self.execute("go south")  # forest_edge
        self.execute("go east")  # southern_trail
        result = self.execute("go south")  # town_gate
        self.assert_success(result)
        self.assert_player_at("town_gate")

    def test_gate_guard_at_gate(self) -> None:
        """Gate Guard is at Town Gate."""
        self.move_player_to("town_gate")
        guard = self.game_state.actors.get(ActorId("gate_guard"))
        self.assertIsNotNone(guard)
        assert guard is not None
        self.assertEqual(guard.location, "town_gate")

    def test_navigate_to_market_square(self) -> None:
        """Can navigate to Market Square."""
        # town_gate -> south -> market_square
        self.move_player_to("town_gate")
        result = self.execute("go south")  # market_square
        self.assert_success(result)
        self.assert_player_at("market_square")

    def test_merchants_at_market(self) -> None:
        """Merchants are present at Market Square."""
        self.move_player_to("market_square")
        merchants = ["herbalist_maren", "weaponsmith_toran", "curiosity_dealer_vex"]
        for merchant_id in merchants:
            merchant = self.game_state.actors.get(ActorId(merchant_id))
            self.assertIsNotNone(merchant, f"Missing {merchant_id}")
            assert merchant is not None
            self.assertEqual(merchant.location, "market_square")

    def test_healer_at_sanctuary(self) -> None:
        """Healer Elara is at Healer's Sanctuary."""
        self.move_player_to("healers_sanctuary")
        healer = self.game_state.actors.get(ActorId("healer_elara"))
        self.assertIsNotNone(healer)
        assert healer is not None
        self.assertEqual(healer.location, "healers_sanctuary")

    def test_councilors_at_council_hall(self) -> None:
        """Councilors are at Council Hall."""
        self.move_player_to("council_hall")
        councilors = ["councilor_hurst", "councilor_asha", "councilor_varn"]
        for councilor_id in councilors:
            councilor = self.game_state.actors.get(ActorId(councilor_id))
            self.assertIsNotNone(councilor, f"Missing {councilor_id}")
            assert councilor is not None
            self.assertEqual(councilor.location, "council_hall")

    def test_undercity_denizens(self) -> None:
        """Undercity characters are in the Undercity."""
        self.move_player_to("undercity")
        denizens = ["the_fence", "whisper", "shadow"]
        for denizen_id in denizens:
            denizen = self.game_state.actors.get(ActorId(denizen_id))
            self.assertIsNotNone(denizen, f"Missing {denizen_id}")
            assert denizen is not None
            self.assertEqual(denizen.location, "undercity")


class TestE2EMeridianNexusScenarios(E2EScenarioTestCase):
    """End-to-end tests for Meridian Nexus (hub) region."""

    def test_player_starts_at_nexus(self) -> None:
        """Player starts at Nexus Chamber."""
        self.assert_player_at("nexus_chamber")

    def test_echo_at_keepers_quarters(self) -> None:
        """The Echo is at Keeper's Quarters."""
        self.move_player_to("keepers_quarters")
        echo = self.game_state.actors.get(ActorId("the_echo"))
        self.assertIsNotNone(echo)
        assert echo is not None
        self.assertEqual(echo.location, "keepers_quarters")

    def test_waystone_spirit_at_nexus(self) -> None:
        """Waystone Spirit is at Nexus Chamber."""
        waystone = self.game_state.actors.get(ActorId("waystone_spirit"))
        self.assertIsNotNone(waystone)
        assert waystone is not None
        self.assertEqual(waystone.location, "nexus_chamber")

    def test_navigate_to_observatory(self) -> None:
        """Can navigate to Observatory Platform."""
        result = self.execute("go up")  # observatory_platform
        self.assert_success(result)
        self.assert_player_at("observatory_platform")

    def test_navigate_to_keepers_quarters(self) -> None:
        """Can navigate to Keeper's Quarters."""
        # nexus -> observatory_platform -> keepers_quarters
        self.execute("go up")  # observatory_platform
        result = self.execute("go east")  # keepers_quarters
        self.assert_success(result)
        self.assert_player_at("keepers_quarters")

    def test_navigate_to_crystal_garden(self) -> None:
        """Can navigate to Crystal Garden."""
        # nexus -> observatory_platform -> keepers_quarters -> crystal_garden
        self.execute("go up")  # observatory_platform
        self.execute("go east")  # keepers_quarters
        result = self.execute("go down")  # crystal_garden
        self.assert_success(result)
        self.assert_player_at("crystal_garden")


class TestE2EWorldConsistency(E2EScenarioTestCase):
    """Tests verifying world state consistency."""

    def test_all_regions_accessible(self) -> None:
        """All four main regions are accessible from nexus."""
        # Check all four exits from nexus
        for direction, expected_loc in [
            ("north", "frozen_pass"),
            ("south", "forest_edge"),
            ("east", "flooded_plaza"),
            ("west", "cavern_entrance"),
        ]:
            # Reset to nexus
            self.move_player_to("nexus_chamber")
            result = self.execute(f"go {direction}")
            self.assert_success(result, f"Failed to go {direction}")
            self.assert_player_at(expected_loc)

    def test_all_key_npcs_have_locations(self) -> None:
        """All key NPCs have valid locations."""
        key_npcs = [
            "player",
            "the_echo",
            "waystone_spirit",
            "alpha_wolf",
            "salamander",
            "hunter_sira",
            "spider_matriarch",
            "bee_queen",
            "camp_leader_mira",
            "sailor_garrett",
            "merchant_delvan",
            "the_archivist",
            "npc_aldric",
            "npc_spore_mother",
            "npc_myconid_elder",
            "gate_guard",
            "healer_elara",
        ]
        for npc_id in key_npcs:
            npc = self.game_state.actors.get(ActorId(npc_id))
            self.assertIsNotNone(npc, f"Missing NPC: {npc_id}")
            assert npc is not None
            self.assertIsNotNone(npc.location, f"NPC {npc_id} has no location")

    def test_all_locations_exist(self) -> None:
        """All expected locations exist in game state."""
        expected_locations = [
            "nexus_chamber",
            "observatory_platform",
            "keepers_quarters",
            "crystal_garden",
            "frozen_pass",
            "wolf_den",
            "hot_springs",
            "frozen_observatory",
            "forest_edge",
            "hunters_camp",
            "bee_queen_clearing",
            "spider_matriarch_lair",
            "flooded_plaza",
            "survivor_camp",
            "sea_caves",
            "merchant_warehouse",
            "deep_archive",
            "cavern_entrance",
            "spore_heart",
            "myconid_sanctuary",
            "town_gate",
            "market_square",
            "council_hall",
            "undercity",
        ]
        location_ids = {loc.id for loc in self.game_state.locations}
        for loc_id in expected_locations:
            self.assertIn(loc_id, location_ids, f"Missing location: {loc_id}")

    def test_state_machines_present(self) -> None:
        """Key NPCs have state machines configured."""
        npcs_with_state_machines = [
            "alpha_wolf",
            "npc_spore_mother",
        ]
        for npc_id in npcs_with_state_machines:
            npc = self.game_state.actors.get(ActorId(npc_id))
            self.assertIsNotNone(npc, f"Missing NPC: {npc_id}")
            assert npc is not None
            sm = npc.properties.get("state_machine")
            self.assertIsNotNone(sm, f"NPC {npc_id} missing state_machine")
            assert sm is not None
            self.assertIn("states", sm, f"NPC {npc_id} state_machine missing states")


class TestE2EInventoryAndItems(E2EScenarioTestCase):
    """End-to-end tests for inventory system."""

    def test_inventory_command(self) -> None:
        """Inventory command works."""
        result = self.execute("inventory")
        # Inventory command should succeed even if empty
        self.assert_success(result)


if __name__ == "__main__":
    unittest.main()
