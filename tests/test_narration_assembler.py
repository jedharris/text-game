"""
Tests for NarrationAssembler module.

Tests the assembly of NarrationPlan from HandlerResult and game state context.
"""

import unittest
from typing import Any, Dict

from src.state_manager import (
    GameState, Location, Item, Actor, Metadata, ExitDescriptor
)
from src.behavior_manager import BehaviorManager
from src.state_accessor import StateAccessor, HandlerResult
from src.types import ActorId, ItemId, LocationId
from src.narration_assembler import NarrationAssembler, LOCATION_ENTRY_VERBS, LOOK_VERBS


def create_test_state_with_exits() -> GameState:
    """Create a GameState with exits for testing."""
    metadata = Metadata(
        title="Test Game",
        version="1.0",
        description="A test game",
        start_location="location_room"
    )

    player = Actor(
        id=ActorId("player"),
        name="Adventurer",
        description="The player character",
        location=LocationId("location_room"),
        inventory=[],
        properties={},
        behaviors=[]
    )

    # Create second location for exit destination
    kitchen = Location(
        id=LocationId("location_kitchen"),
        name="Kitchen",
        description="A kitchen",
        exits={},
        items=[],
        properties={},
        behaviors=[]
    )

    # Create main room with exits
    room = Location(
        id=LocationId("location_room"),
        name="Test Room",
        description="A room for testing",
        exits={
            "north": ExitDescriptor(
                type="open",
                to=LocationId("location_kitchen"),
                _direction="north",
                _location_id=LocationId("location_room")
            ),
            "east": ExitDescriptor(
                type="door",
                to=LocationId("location_garden"),
                name="garden door",
                _direction="east",
                _location_id=LocationId("location_room")
            )
        },
        items=[ItemId("item_sword")],
        properties={},
        behaviors=[]
    )

    garden = Location(
        id=LocationId("location_garden"),
        name="Garden",
        description="A garden",
        exits={},
        items=[],
        properties={},
        behaviors=[]
    )

    sword = Item(
        id=ItemId("item_sword"),
        name="sword",
        description="A test sword",
        location="location_room",
        properties={
            "portable": True,
            "llm_context": {"traits": ["shiny", "sharp", "well-balanced"]}
        },
        behaviors=[]
    )

    tree = Item(
        id=ItemId("item_tree"),
        name="oak tree",
        description="A large oak tree",
        location="location_room",
        properties={
            "portable": False,
            "climbable": True
        },
        behaviors=[]
    )

    state = GameState(
        metadata=metadata,
        locations=[room, kitchen, garden],
        items=[sword, tree],
        locks=[],
        actors={ActorId("player"): player},
        extra={}
    )

    return state


class TestNarrationAssemblerViewpoint(unittest.TestCase):
    """Tests for viewpoint building."""

    def setUp(self) -> None:
        """Set up test state and assembler."""
        self.state = create_test_state_with_exits()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)
        self.assembler = NarrationAssembler(
            self.accessor, ActorId("player")
        )

    def test_ground_viewpoint_default(self) -> None:
        """Default viewpoint is ground mode."""
        result = HandlerResult(success=True, primary="Done.")
        plan = self.assembler.assemble(result, "take", "brief", "new")

        self.assertEqual(plan["viewpoint"]["mode"], "ground")

    def test_elevated_viewpoint_climbing(self) -> None:
        """Climbing posture produces elevated viewpoint."""
        player = self.accessor.get_actor(ActorId("player"))
        assert player is not None
        player.properties["posture"] = "climbing"
        player.properties["focused_on"] = "item_tree"

        result = HandlerResult(success=True, primary="You look around.")
        plan = self.assembler.assemble(result, "look", "full", "familiar")

        self.assertEqual(plan["viewpoint"]["mode"], "elevated")
        self.assertEqual(plan["viewpoint"]["posture"], "climbing")
        self.assertEqual(plan["viewpoint"]["focus_name"], "oak tree")

    def test_elevated_viewpoint_on_surface(self) -> None:
        """On_surface posture produces elevated viewpoint."""
        player = self.accessor.get_actor(ActorId("player"))
        assert player is not None
        player.properties["posture"] = "on_surface"
        player.properties["focused_on"] = "item_tree"

        result = HandlerResult(success=True, primary="You stand on the tree.")
        plan = self.assembler.assemble(result, "look", "full", "familiar")

        self.assertEqual(plan["viewpoint"]["mode"], "elevated")
        self.assertEqual(plan["viewpoint"]["posture"], "on_surface")

    def test_concealed_viewpoint_behind_cover(self) -> None:
        """Behind_cover posture produces concealed viewpoint."""
        player = self.accessor.get_actor(ActorId("player"))
        assert player is not None
        player.properties["posture"] = "behind_cover"
        player.properties["focused_on"] = "item_tree"

        result = HandlerResult(success=True, primary="You peer out.")
        plan = self.assembler.assemble(result, "look", "full", "familiar")

        self.assertEqual(plan["viewpoint"]["mode"], "concealed")
        self.assertEqual(plan["viewpoint"]["posture"], "behind_cover")

    def test_concealed_viewpoint_cover_alias(self) -> None:
        """Cover posture is normalized to behind_cover."""
        player = self.accessor.get_actor(ActorId("player"))
        assert player is not None
        player.properties["posture"] = "cover"
        player.properties["focused_on"] = "item_tree"

        result = HandlerResult(success=True, primary="You hide.")
        plan = self.assembler.assemble(result, "look", "full", "familiar")

        self.assertEqual(plan["viewpoint"]["mode"], "concealed")
        self.assertEqual(plan["viewpoint"]["posture"], "behind_cover")


class TestNarrationAssemblerScope(unittest.TestCase):
    """Tests for scope building."""

    def setUp(self) -> None:
        """Set up test state and assembler."""
        self.state = create_test_state_with_exits()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)
        self.assembler = NarrationAssembler(
            self.accessor, ActorId("player")
        )

    def test_location_entry_verbs(self) -> None:
        """Movement verbs produce location_entry scene_kind."""
        for verb in ["go", "north", "n", "south", "east", "west", "up", "down"]:
            result = HandlerResult(success=True, primary="You go north.")
            plan = self.assembler.assemble(result, verb, "full", "new")
            self.assertEqual(
                plan["scope"]["scene_kind"], "location_entry",
                f"Verb '{verb}' should produce location_entry"
            )

    def test_look_verbs(self) -> None:
        """Look/examine verbs produce look scene_kind."""
        for verb in ["look", "l", "examine", "x", "inspect"]:
            result = HandlerResult(success=True, primary="You look.")
            plan = self.assembler.assemble(result, verb, "full", "familiar")
            self.assertEqual(
                plan["scope"]["scene_kind"], "look",
                f"Verb '{verb}' should produce look"
            )

    def test_action_result_verbs(self) -> None:
        """Other verbs produce action_result scene_kind."""
        for verb in ["take", "drop", "open", "close", "use", "attack"]:
            result = HandlerResult(success=True, primary="Done.")
            plan = self.assembler.assemble(result, verb, "full", "familiar")
            self.assertEqual(
                plan["scope"]["scene_kind"], "action_result",
                f"Verb '{verb}' should produce action_result"
            )

    def test_success_outcome(self) -> None:
        """Successful action produces success outcome."""
        result = HandlerResult(success=True, primary="You take the sword.")
        plan = self.assembler.assemble(result, "take", "full", "new")

        self.assertEqual(plan["scope"]["outcome"], "success")

    def test_failure_outcome(self) -> None:
        """Failed action produces failure outcome."""
        result = HandlerResult(success=False, primary="The door is locked.")
        plan = self.assembler.assemble(result, "open", "full", "familiar")

        self.assertEqual(plan["scope"]["outcome"], "failure")

    def test_familiarity_new(self) -> None:
        """Familiarity 'new' is preserved."""
        result = HandlerResult(success=True, primary="You enter the room.")
        plan = self.assembler.assemble(result, "go", "full", "new")

        self.assertEqual(plan["scope"]["familiarity"], "new")

    def test_familiarity_familiar(self) -> None:
        """Familiarity 'familiar' is preserved."""
        result = HandlerResult(success=True, primary="You look around.")
        plan = self.assembler.assemble(result, "look", "full", "familiar")

        self.assertEqual(plan["scope"]["familiarity"], "familiar")


class TestNarrationAssemblerSecondaryBeats(unittest.TestCase):
    """Tests for secondary_beats building."""

    def setUp(self) -> None:
        """Set up test state and assembler."""
        self.state = create_test_state_with_exits()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)
        self.assembler = NarrationAssembler(
            self.accessor, ActorId("player")
        )

    def test_handler_beats_included(self) -> None:
        """Handler-provided beats are included."""
        result = HandlerResult(
            success=True,
            primary="You take the sword.",
            beats=["You step down from the table."]
        )
        plan = self.assembler.assemble(result, "take", "full", "new")

        self.assertIn("You step down from the table.", plan["secondary_beats"])

    def test_multiple_handler_beats(self) -> None:
        """Multiple handler beats are all included."""
        result = HandlerResult(
            success=True,
            primary="You take the lantern.",
            beats=["You step down.", "The flame flickers."]
        )
        plan = self.assembler.assemble(result, "take", "full", "new")

        self.assertEqual(len(plan["secondary_beats"]), 2)
        self.assertIn("You step down.", plan["secondary_beats"])
        self.assertIn("The flame flickers.", plan["secondary_beats"])

    def test_trait_beats_extracted_full_verbosity(self) -> None:
        """Trait beats are extracted from llm_context in full verbosity."""
        result = HandlerResult(
            success=True,
            primary="You examine the sword.",
            data={
                "llm_context": {"traits": ["shiny", "sharp", "well-balanced"]}
            }
        )
        plan = self.assembler.assemble(result, "examine", "full", "new")

        # Should have some trait beats (up to 2 by default)
        # Since traits are randomized, we check that some are included
        trait_beats = [b for b in plan["secondary_beats"]
                      if b in ["shiny", "sharp", "well-balanced"]]
        self.assertTrue(len(trait_beats) <= 2)

    def test_no_trait_beats_brief_verbosity(self) -> None:
        """No trait beats in brief verbosity (only handler beats)."""
        result = HandlerResult(
            success=True,
            primary="You take the sword.",
            beats=["Handler beat."],
            data={
                "llm_context": {"traits": ["shiny", "sharp"]}
            }
        )
        plan = self.assembler.assemble(result, "take", "brief", "new")

        # Only handler beat should be present
        self.assertEqual(plan["secondary_beats"], ["Handler beat."])

    def test_empty_beats_when_none(self) -> None:
        """Empty beats list when no beats provided."""
        result = HandlerResult(success=True, primary="Done.")
        plan = self.assembler.assemble(result, "take", "brief", "new")

        self.assertEqual(plan["secondary_beats"], [])


class TestNarrationAssemblerEntityRefs(unittest.TestCase):
    """Tests for entity_refs building."""

    def setUp(self) -> None:
        """Set up test state and assembler."""
        self.state = create_test_state_with_exits()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)
        self.assembler = NarrationAssembler(
            self.accessor, ActorId("player")
        )

    def test_entity_ref_from_data(self) -> None:
        """Entity ref is built from handler data."""
        result = HandlerResult(
            success=True,
            primary="You examine the sword.",
            data={
                "id": "item_sword",
                "name": "sword",
                "type": "item",
                "llm_context": {"traits": ["shiny"]}
            }
        )
        plan = self.assembler.assemble(result, "examine", "full", "new")

        self.assertIn("item_sword", plan["entity_refs"])
        ref = plan["entity_refs"]["item_sword"]
        self.assertEqual(ref["name"], "sword")
        self.assertEqual(ref["type"], "item")

    def test_entity_ref_includes_traits(self) -> None:
        """Entity ref includes traits from llm_context."""
        result = HandlerResult(
            success=True,
            primary="You examine the sword.",
            data={
                "id": "item_sword",
                "name": "sword",
                "type": "item",
                "llm_context": {"traits": ["shiny", "sharp"]}
            }
        )
        plan = self.assembler.assemble(result, "examine", "full", "new")

        ref = plan["entity_refs"]["item_sword"]
        self.assertIn("traits", ref)
        self.assertIn("shiny", ref["traits"])

    def test_entity_ref_includes_state(self) -> None:
        """Entity ref includes state flags."""
        result = HandlerResult(
            success=True,
            primary="You examine the door.",
            data={
                "id": "door_1",
                "name": "oak door",
                "type": "door",
                "open": False,
                "locked": True
            }
        )
        plan = self.assembler.assemble(result, "examine", "full", "new")

        ref = plan["entity_refs"]["door_1"]
        self.assertFalse(ref["state"]["open"])
        self.assertTrue(ref["state"]["locked"])

    def test_no_entity_refs_brief_action(self) -> None:
        """No entity refs in brief verbosity for action_result."""
        result = HandlerResult(
            success=True,
            primary="Done.",
            data={"id": "item_sword", "name": "sword", "type": "item"}
        )
        plan = self.assembler.assemble(result, "take", "brief", "new")

        self.assertEqual(plan["entity_refs"], {})

    def test_entity_refs_for_look_even_brief(self) -> None:
        """Entity refs included for look even in brief mode."""
        result = HandlerResult(
            success=True,
            primary="You look around.",
            data={"id": "item_sword", "name": "sword", "type": "item"}
        )
        plan = self.assembler.assemble(result, "look", "brief", "new")

        # Look scene_kind should include entity_refs even in brief
        self.assertIn("item_sword", plan["entity_refs"])


class TestNarrationAssemblerMustMention(unittest.TestCase):
    """Tests for must_mention building."""

    def setUp(self) -> None:
        """Set up test state and assembler."""
        self.state = create_test_state_with_exits()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)
        self.assembler = NarrationAssembler(
            self.accessor, ActorId("player")
        )

    def test_exits_text_for_location_entry(self) -> None:
        """Exits text is included for location_entry scene."""
        result = HandlerResult(success=True, primary="You enter the room.")
        plan = self.assembler.assemble(result, "go", "full", "new")

        self.assertIn("must_mention", plan)
        self.assertIn("exits_text", plan["must_mention"])
        exits_text = plan["must_mention"]["exits_text"]
        self.assertIn("north", exits_text)
        self.assertIn("Kitchen", exits_text)

    def test_exits_text_for_look(self) -> None:
        """Exits text is included for look scene."""
        result = HandlerResult(success=True, primary="You look around.")
        plan = self.assembler.assemble(result, "look", "full", "familiar")

        self.assertIn("must_mention", plan)
        exits_text = plan["must_mention"]["exits_text"]
        self.assertIn("north", exits_text)

    def test_no_exits_text_for_action(self) -> None:
        """No exits text for action_result scene."""
        result = HandlerResult(success=True, primary="You take the sword.")
        plan = self.assembler.assemble(result, "take", "full", "new")

        # must_mention should not be present or should be empty
        if "must_mention" in plan:
            self.assertNotIn("exits_text", plan["must_mention"])

    def test_exits_text_includes_named_exits(self) -> None:
        """Named exits are described in exits text."""
        result = HandlerResult(success=True, primary="You look around.")
        plan = self.assembler.assemble(result, "look", "full", "new")

        exits_text = plan["must_mention"]["exits_text"]
        # Should include the named exit "garden door"
        self.assertIn("east", exits_text)

    def test_single_exit_format(self) -> None:
        """Single exit uses different format."""
        # Modify state to have only one exit
        location = self.accessor.get_location(LocationId("location_room"))
        assert location is not None
        del location.exits["east"]

        result = HandlerResult(success=True, primary="You look around.")
        plan = self.assembler.assemble(result, "look", "full", "new")

        exits_text = plan["must_mention"]["exits_text"]
        self.assertIn("There is an exit", exits_text)


class TestNarrationAssemblerPrimaryText(unittest.TestCase):
    """Tests for primary_text handling."""

    def setUp(self) -> None:
        """Set up test state and assembler."""
        self.state = create_test_state_with_exits()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)
        self.assembler = NarrationAssembler(
            self.accessor, ActorId("player")
        )

    def test_primary_text_from_handler(self) -> None:
        """Primary text comes directly from handler result."""
        result = HandlerResult(
            success=True,
            primary="You pick up the rusty sword."
        )
        plan = self.assembler.assemble(result, "take", "full", "new")

        self.assertEqual(plan["primary_text"], "You pick up the rusty sword.")

    def test_primary_text_failure(self) -> None:
        """Primary text for failure is preserved."""
        result = HandlerResult(
            success=False,
            primary="The door is locked."
        )
        plan = self.assembler.assemble(result, "open", "full", "familiar")

        self.assertEqual(plan["primary_text"], "The door is locked.")


class TestNarrationAssemblerFullAssembly(unittest.TestCase):
    """Integration tests for full plan assembly."""

    def setUp(self) -> None:
        """Set up test state and assembler."""
        self.state = create_test_state_with_exits()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)
        self.assembler = NarrationAssembler(
            self.accessor, ActorId("player")
        )

    def test_complete_location_entry_plan(self) -> None:
        """Full plan for location entry has all required fields."""
        result = HandlerResult(
            success=True,
            primary="You enter the kitchen."
        )
        plan = self.assembler.assemble(result, "go", "full", "new")

        # Check all required fields
        self.assertIn("primary_text", plan)
        self.assertIn("secondary_beats", plan)
        self.assertIn("viewpoint", plan)
        self.assertIn("scope", plan)
        self.assertIn("entity_refs", plan)
        self.assertIn("must_mention", plan)

        # Check scope values
        self.assertEqual(plan["scope"]["scene_kind"], "location_entry")
        self.assertEqual(plan["scope"]["outcome"], "success")
        self.assertEqual(plan["scope"]["familiarity"], "new")

    def test_complete_examine_plan(self) -> None:
        """Full plan for examine has correct structure."""
        result = HandlerResult(
            success=True,
            primary="You examine the sword.",
            data={
                "id": "item_sword",
                "name": "sword",
                "type": "item",
                "llm_context": {"traits": ["shiny", "sharp"]}
            }
        )
        plan = self.assembler.assemble(result, "examine", "full", "new")

        self.assertEqual(plan["scope"]["scene_kind"], "look")
        self.assertIn("item_sword", plan["entity_refs"])
        self.assertIn("must_mention", plan)

    def test_brief_action_plan_minimal(self) -> None:
        """Brief action plan is minimal."""
        result = HandlerResult(success=True, primary="Done.")
        plan = self.assembler.assemble(result, "take", "brief", "familiar")

        self.assertEqual(plan["primary_text"], "Done.")
        self.assertEqual(plan["secondary_beats"], [])
        self.assertEqual(plan["scope"]["scene_kind"], "action_result")
        self.assertEqual(plan["entity_refs"], {})
        self.assertNotIn("must_mention", plan)


if __name__ == "__main__":
    unittest.main()
