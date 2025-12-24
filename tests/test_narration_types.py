"""
Tests for narration_types module.

Validates TypedDict structures and HandlerResult changes.
"""

import unittest
from typing import get_type_hints

from src.narration_types import (
    ViewpointInfo,
    ScopeInfo,
    EntityState,
    EntityRef,
    MustMention,
    NarrationPlan,
    NarrationResult,
    ReactionRef,
)
from src.state_accessor import HandlerResult, EventResult


class TestViewpointInfo(unittest.TestCase):
    """Tests for ViewpointInfo TypedDict."""

    def test_ground_mode(self) -> None:
        """ViewpointInfo accepts ground mode."""
        viewpoint: ViewpointInfo = {
            "mode": "ground",
            "posture": None,
            "focus_name": None
        }
        self.assertEqual(viewpoint["mode"], "ground")

    def test_elevated_mode_with_posture(self) -> None:
        """ViewpointInfo accepts elevated mode with climbing posture."""
        viewpoint: ViewpointInfo = {
            "mode": "elevated",
            "posture": "climbing",
            "focus_name": "the oak tree"
        }
        self.assertEqual(viewpoint["mode"], "elevated")
        self.assertEqual(viewpoint["posture"], "climbing")
        self.assertEqual(viewpoint["focus_name"], "the oak tree")

    def test_concealed_mode(self) -> None:
        """ViewpointInfo accepts concealed mode."""
        viewpoint: ViewpointInfo = {
            "mode": "concealed",
            "posture": "behind_cover",
            "focus_name": "the boulder"
        }
        self.assertEqual(viewpoint["mode"], "concealed")
        self.assertEqual(viewpoint["posture"], "behind_cover")

    def test_minimal_viewpoint(self) -> None:
        """ViewpointInfo allows minimal fields (total=False)."""
        viewpoint: ViewpointInfo = {"mode": "ground"}
        self.assertEqual(viewpoint["mode"], "ground")


class TestScopeInfo(unittest.TestCase):
    """Tests for ScopeInfo TypedDict."""

    def test_location_entry_scope(self) -> None:
        """ScopeInfo accepts location_entry scene."""
        scope: ScopeInfo = {
            "scene_kind": "location_entry",
            "outcome": "success",
            "familiarity": "new"
        }
        self.assertEqual(scope["scene_kind"], "location_entry")
        self.assertEqual(scope["outcome"], "success")
        self.assertEqual(scope["familiarity"], "new")

    def test_look_scope(self) -> None:
        """ScopeInfo accepts look scene."""
        scope: ScopeInfo = {
            "scene_kind": "look",
            "outcome": "success",
            "familiarity": "familiar"
        }
        self.assertEqual(scope["scene_kind"], "look")
        self.assertEqual(scope["familiarity"], "familiar")

    def test_action_result_failure(self) -> None:
        """ScopeInfo accepts action_result with failure."""
        scope: ScopeInfo = {
            "scene_kind": "action_result",
            "outcome": "failure",
            "familiarity": "familiar"
        }
        self.assertEqual(scope["scene_kind"], "action_result")
        self.assertEqual(scope["outcome"], "failure")


class TestEntityState(unittest.TestCase):
    """Tests for EntityState TypedDict."""

    def test_open_container(self) -> None:
        """EntityState tracks open/closed state."""
        state: EntityState = {"open": True}
        self.assertTrue(state["open"])

    def test_locked_door(self) -> None:
        """EntityState tracks locked state."""
        state: EntityState = {"open": False, "locked": True}
        self.assertFalse(state["open"])
        self.assertTrue(state["locked"])

    def test_lit_item(self) -> None:
        """EntityState tracks lit state."""
        state: EntityState = {"lit": True}
        self.assertTrue(state["lit"])

    def test_empty_state(self) -> None:
        """EntityState allows empty dict (total=False)."""
        state: EntityState = {}
        self.assertEqual(len(state), 0)


class TestEntityRef(unittest.TestCase):
    """Tests for EntityRef TypedDict."""

    def test_item_entity_ref(self) -> None:
        """EntityRef represents an item with traits."""
        ref: EntityRef = {
            "name": "rusty sword",
            "type": "item",
            "traits": ["pitted blade", "leather-wrapped hilt"],
            "spatial_relation": "within_reach",
            "salience": "high"
        }
        self.assertEqual(ref["name"], "rusty sword")
        self.assertEqual(ref["type"], "item")
        self.assertEqual(len(ref["traits"]), 2)
        self.assertEqual(ref["salience"], "high")

    def test_container_with_state(self) -> None:
        """EntityRef represents a container with state."""
        ref: EntityRef = {
            "name": "wooden chest",
            "type": "container",
            "traits": ["iron bands", "dust-covered"],
            "state": {"open": True},
            "salience": "medium"
        }
        self.assertEqual(ref["type"], "container")
        self.assertTrue(ref["state"]["open"])

    def test_door_entity_ref(self) -> None:
        """EntityRef represents a door."""
        ref: EntityRef = {
            "name": "oak door",
            "type": "door",
            "traits": ["heavy", "iron-bound"],
            "state": {"open": False, "locked": True},
            "salience": "medium"
        }
        self.assertEqual(ref["type"], "door")
        self.assertTrue(ref["state"]["locked"])

    def test_spatial_relations(self) -> None:
        """EntityRef supports all spatial relations."""
        relations = ["within_reach", "below", "above", "nearby"]
        for relation in relations:
            ref: EntityRef = {
                "name": "test item",
                "type": "item",
                "spatial_relation": relation  # type: ignore[typeddict-item]
            }
            self.assertEqual(ref["spatial_relation"], relation)

    def test_minimal_entity_ref(self) -> None:
        """EntityRef allows minimal fields."""
        ref: EntityRef = {"name": "thing", "type": "item"}
        self.assertEqual(ref["name"], "thing")


class TestMustMention(unittest.TestCase):
    """Tests for MustMention TypedDict."""

    def test_exits_text(self) -> None:
        """MustMention contains exits description."""
        must: MustMention = {
            "exits_text": "Exits lead north to the corridor and east to the pantry."
        }
        self.assertIn("north", must["exits_text"])

    def test_empty_must_mention(self) -> None:
        """MustMention allows empty dict."""
        must: MustMention = {}
        self.assertEqual(len(must), 0)


class TestNarrationPlan(unittest.TestCase):
    """Tests for NarrationPlan TypedDict."""

    def test_simple_action_plan(self) -> None:
        """NarrationPlan for a simple action."""
        plan: NarrationPlan = {
            "primary_text": "You pick up the rusty sword.",
            "secondary_beats": ["Its pitted blade feels heavier than expected."],
            "scope": {
                "scene_kind": "action_result",
                "outcome": "success",
                "familiarity": "familiar"
            }
        }
        self.assertEqual(plan["primary_text"], "You pick up the rusty sword.")
        self.assertEqual(len(plan["secondary_beats"]), 1)

    def test_location_entry_plan(self) -> None:
        """NarrationPlan for entering a location."""
        plan: NarrationPlan = {
            "primary_text": "You enter the kitchen.",
            "secondary_beats": [],
            "viewpoint": {
                "mode": "ground",
                "posture": None,
                "focus_name": None
            },
            "scope": {
                "scene_kind": "location_entry",
                "outcome": "success",
                "familiarity": "new"
            },
            "entity_refs": {
                "item_knife": {
                    "name": "kitchen knife",
                    "type": "item",
                    "traits": ["sharp", "well-used"],
                    "salience": "medium"
                }
            },
            "must_mention": {
                "exits_text": "A door leads north to the dining room."
            }
        }
        self.assertEqual(plan["scope"]["scene_kind"], "location_entry")
        self.assertIn("item_knife", plan["entity_refs"])

    def test_elevated_viewpoint_plan(self) -> None:
        """NarrationPlan with elevated viewpoint."""
        plan: NarrationPlan = {
            "primary_text": "You look around from the tree.",
            "secondary_beats": ["The ground seems far below."],
            "viewpoint": {
                "mode": "elevated",
                "posture": "climbing",
                "focus_name": "the oak tree"
            },
            "scope": {
                "scene_kind": "look",
                "outcome": "success",
                "familiarity": "familiar"
            }
        }
        self.assertEqual(plan["viewpoint"]["mode"], "elevated")
        self.assertEqual(plan["viewpoint"]["posture"], "climbing")

    def test_minimal_plan(self) -> None:
        """NarrationPlan allows minimal fields."""
        plan: NarrationPlan = {
            "primary_text": "Done."
        }
        self.assertEqual(plan["primary_text"], "Done.")


class TestNarrationResult(unittest.TestCase):
    """Tests for NarrationResult TypedDict."""

    def test_success_result(self) -> None:
        """NarrationResult for successful action."""
        result: NarrationResult = {
            "success": True,
            "verbosity": "full",
            "narration": {
                "primary_text": "You take the sword.",
                "secondary_beats": [],
                "scope": {
                    "scene_kind": "action_result",
                    "outcome": "success",
                    "familiarity": "new"
                }
            },
            "data": {"item_id": "item_sword"}
        }
        self.assertTrue(result["success"])
        self.assertEqual(result["verbosity"], "full")
        self.assertEqual(result["narration"]["primary_text"], "You take the sword.")

    def test_failure_result(self) -> None:
        """NarrationResult for failed action."""
        result: NarrationResult = {
            "success": False,
            "verbosity": "brief",
            "narration": {
                "primary_text": "The door is locked.",
                "scope": {
                    "scene_kind": "action_result",
                    "outcome": "failure",
                    "familiarity": "familiar"
                }
            },
            "data": {}
        }
        self.assertFalse(result["success"])
        self.assertEqual(result["narration"]["scope"]["outcome"], "failure")

    def test_brief_verbosity(self) -> None:
        """NarrationResult with brief verbosity."""
        result: NarrationResult = {
            "success": True,
            "verbosity": "brief",
            "narration": {
                "primary_text": "You go north."
            },
            "data": {}
        }
        self.assertEqual(result["verbosity"], "brief")


class TestHandlerResult(unittest.TestCase):
    """Tests for updated HandlerResult dataclass."""

    def test_simple_handler_result(self) -> None:
        """HandlerResult with primary text only."""
        result = HandlerResult(success=True, primary="You take the sword.")
        self.assertTrue(result.success)
        self.assertEqual(result.primary, "You take the sword.")
        self.assertEqual(result.beats, [])
        self.assertIsNone(result.data)

    def test_handler_result_with_beats(self) -> None:
        """HandlerResult with supplemental beats."""
        result = HandlerResult(
            success=True,
            primary="You pick up the sword.",
            beats=["You step down from the table."]
        )
        self.assertEqual(result.primary, "You pick up the sword.")
        self.assertEqual(len(result.beats), 1)
        self.assertEqual(result.beats[0], "You step down from the table.")

    def test_handler_result_with_data(self) -> None:
        """HandlerResult with extra data."""
        result = HandlerResult(
            success=True,
            primary="You examine the chest.",
            data={"llm_context": {"traits": ["ornate", "dusty"]}}
        )
        self.assertIsNotNone(result.data)
        assert result.data is not None  # Type guard for mypy
        self.assertIn("llm_context", result.data)

    def test_handler_result_failure(self) -> None:
        """HandlerResult for failed action."""
        result = HandlerResult(
            success=False,
            primary="The door is locked."
        )
        self.assertFalse(result.success)
        self.assertEqual(result.primary, "The door is locked.")

    def test_handler_result_multiple_beats(self) -> None:
        """HandlerResult with multiple beats."""
        result = HandlerResult(
            success=True,
            primary="You take the lantern.",
            beats=[
                "You step down from the shelf.",
                "The flame flickers briefly."
            ]
        )
        self.assertEqual(len(result.beats), 2)

    def test_handler_result_default_beats(self) -> None:
        """HandlerResult defaults to empty beats list."""
        result = HandlerResult(success=True, primary="Done.")
        self.assertIsInstance(result.beats, list)
        self.assertEqual(len(result.beats), 0)


class TestReactionRef(unittest.TestCase):
    """Tests for ReactionRef TypedDict (new for multi-entity reactions)."""

    def test_basic_reaction(self) -> None:
        """ReactionRef represents a single entity's reaction."""
        reaction: ReactionRef = {
            "entity": "npc_guard",
            "entity_name": "Town Guard",
            "state": "hostile",
            "fragments": ["hand moves to sword hilt", "steps forward"],
            "response": "confrontation"
        }
        self.assertEqual(reaction["entity"], "npc_guard")
        self.assertEqual(reaction["entity_name"], "Town Guard")
        self.assertEqual(reaction["state"], "hostile")
        self.assertEqual(len(reaction["fragments"]), 2)
        self.assertEqual(reaction["response"], "confrontation")

    def test_minimal_reaction(self) -> None:
        """ReactionRef allows minimal fields (total=False)."""
        reaction: ReactionRef = {
            "entity": "npc_villager",
            "entity_name": "Villager"
        }
        self.assertEqual(reaction["entity"], "npc_villager")
        self.assertNotIn("state", reaction)

    def test_empty_fragments(self) -> None:
        """ReactionRef can have empty fragments list."""
        reaction: ReactionRef = {
            "entity": "npc_merchant",
            "entity_name": "Merchant",
            "state": "nervous",
            "fragments": [],
            "response": "avoidance"
        }
        self.assertEqual(reaction["fragments"], [])


class TestEventResultExtensions(unittest.TestCase):
    """Tests for new EventResult fields (context, hints, fragments)."""

    def test_event_result_basic(self) -> None:
        """EventResult still works with just allow and feedback."""
        result = EventResult(allow=True, feedback="The door creaks open.")
        self.assertTrue(result.allow)
        self.assertEqual(result.feedback, "The door creaks open.")

    def test_event_result_with_context(self) -> None:
        """EventResult accepts author-defined context."""
        result = EventResult(
            allow=True,
            feedback="The wolf sniffs the offering.",
            context={
                "npc_state": {"previous": "hostile", "current": "wary"},
                "communication": {"type": "body_language", "signal": "accepting"}
            }
        )
        self.assertTrue(result.allow)
        self.assertIsNotNone(result.context)
        assert result.context is not None  # Type guard
        self.assertEqual(result.context["npc_state"]["current"], "wary")

    def test_event_result_with_hints(self) -> None:
        """EventResult accepts hints list."""
        result = EventResult(
            allow=True,
            feedback="Relief floods his features.",
            hints=["rescue", "urgent", "trust-building"]
        )
        self.assertEqual(len(result.hints), 3)
        self.assertIn("rescue", result.hints)

    def test_event_result_with_fragments(self) -> None:
        """EventResult accepts pre-selected fragments."""
        result = EventResult(
            allow=True,
            feedback="Aldric accepts the silvermoss.",
            fragments={
                "state": ["trembling hands", "labored breathing"],
                "action": ["accepts with gratitude"]
            }
        )
        self.assertIsNotNone(result.fragments)
        assert result.fragments is not None  # Type guard
        self.assertEqual(len(result.fragments["state"]), 2)

    def test_event_result_defaults(self) -> None:
        """EventResult new fields have sensible defaults."""
        result = EventResult(allow=True)
        self.assertIsNone(result.context)
        self.assertEqual(result.hints, [])
        self.assertIsNone(result.fragments)

    def test_event_result_with_reaction(self) -> None:
        """EventResult can include reaction context for multi-entity scenes."""
        result = EventResult(
            allow=True,
            context={
                "reaction": {
                    "entity": "npc_guard",
                    "entity_name": "Town Guard",
                    "state": "hostile",
                    "fragments": ["hand moves to sword"],
                    "response": "confrontation"
                }
            }
        )
        assert result.context is not None
        self.assertIn("reaction", result.context)
        self.assertEqual(result.context["reaction"]["state"], "hostile")


class TestHandlerResultExtensions(unittest.TestCase):
    """Tests for new HandlerResult fields (context, hints, fragments, reactions)."""

    def test_handler_result_basic(self) -> None:
        """HandlerResult still works with original fields."""
        result = HandlerResult(
            success=True,
            primary="You unlock the door.",
            beats=["The lock clicks."],
            data={"item_id": "door_sanctum"}
        )
        self.assertTrue(result.success)
        self.assertEqual(result.primary, "You unlock the door.")

    def test_handler_result_with_context(self) -> None:
        """HandlerResult accepts author-defined context."""
        result = HandlerResult(
            success=True,
            primary="You give the silvermoss to Aldric.",
            context={
                "npc_state": {"previous": "critical", "current": "stabilized"},
                "urgency": {"level": "critical"}
            }
        )
        self.assertIsNotNone(result.context)
        assert result.context is not None  # Type guard
        self.assertEqual(result.context["npc_state"]["current"], "stabilized")

    def test_handler_result_with_hints(self) -> None:
        """HandlerResult accepts hints list."""
        result = HandlerResult(
            success=True,
            primary="You apply the bandages.",
            hints=["rescue", "urgent"]
        )
        self.assertEqual(len(result.hints), 2)
        self.assertIn("urgent", result.hints)

    def test_handler_result_with_fragments(self) -> None:
        """HandlerResult accepts pre-selected fragments."""
        result = HandlerResult(
            success=True,
            primary="You unlock the door.",
            fragments={
                "action_core": "the lock clicks open",
                "action_color": ["runes flicker momentarily"],
                "traits": ["glowing runes", "heavy iron"]
            }
        )
        self.assertIsNotNone(result.fragments)
        assert result.fragments is not None  # Type guard
        self.assertEqual(result.fragments["action_core"], "the lock clicks open")

    def test_handler_result_with_reactions(self) -> None:
        """HandlerResult accepts reactions list for multi-entity scenes."""
        result = HandlerResult(
            success=True,
            primary="You enter the market square with your wolf.",
            reactions=[
                {
                    "entity": "npc_guard",
                    "entity_name": "Town Guard",
                    "state": "hostile",
                    "fragments": ["hand moves to sword hilt"],
                    "response": "confrontation"
                },
                {
                    "entity": "npc_merchant",
                    "entity_name": "Merchant",
                    "state": "nervous",
                    "fragments": ["backs away"],
                    "response": "avoidance"
                }
            ]
        )
        self.assertIsNotNone(result.reactions)
        assert result.reactions is not None  # Type guard
        self.assertEqual(len(result.reactions), 2)
        self.assertEqual(result.reactions[0]["state"], "hostile")
        self.assertEqual(result.reactions[1]["response"], "avoidance")

    def test_handler_result_defaults(self) -> None:
        """HandlerResult new fields have sensible defaults."""
        result = HandlerResult(success=True, primary="Done.")
        self.assertIsNone(result.context)
        self.assertEqual(result.hints, [])
        self.assertIsNone(result.fragments)
        self.assertIsNone(result.reactions)


class TestNarrationPlanExtensions(unittest.TestCase):
    """Tests for new NarrationPlan fields (context, hints, fragments, reactions)."""

    def test_narration_plan_with_context(self) -> None:
        """NarrationPlan accepts author-defined context."""
        plan: NarrationPlan = {
            "primary_text": "You give the silvermoss to Aldric.",
            "context": {
                "npc_state": {"previous": "critical", "current": "stabilized"},
                "relationship": {"trust_level": "grateful"}
            }
        }
        self.assertIn("context", plan)
        self.assertEqual(plan["context"]["npc_state"]["current"], "stabilized")

    def test_narration_plan_with_hints(self) -> None:
        """NarrationPlan accepts hints list."""
        plan: NarrationPlan = {
            "primary_text": "You apply the bandages to Sira.",
            "hints": ["rescue", "urgent", "trust-building"]
        }
        self.assertIn("hints", plan)
        self.assertEqual(len(plan["hints"]), 3)

    def test_narration_plan_with_fragments(self) -> None:
        """NarrationPlan accepts pre-selected fragments."""
        plan: NarrationPlan = {
            "primary_text": "You unlock the door.",
            "fragments": {
                "action_core": "the lock clicks open",
                "action_color": ["runes flicker"],
                "traits": ["glowing runes", "heavy iron"]
            }
        }
        self.assertIn("fragments", plan)
        self.assertEqual(plan["fragments"]["action_core"], "the lock clicks open")

    def test_narration_plan_with_reactions(self) -> None:
        """NarrationPlan accepts reactions list."""
        plan: NarrationPlan = {
            "primary_text": "You enter with the wolf.",
            "reactions": [
                {
                    "entity": "npc_guard",
                    "entity_name": "Guard",
                    "state": "hostile",
                    "fragments": ["draws sword"],
                    "response": "confrontation"
                }
            ]
        }
        self.assertIn("reactions", plan)
        self.assertEqual(len(plan["reactions"]), 1)

    def test_narration_plan_full_new_structure(self) -> None:
        """NarrationPlan with all new fields for complex scene."""
        plan: NarrationPlan = {
            "action_verb": "give",
            "primary_text": "You offer the venison to the wolf.",
            "secondary_beats": [],
            "context": {
                "npc_state": {"previous": "hostile", "current": "wary"},
                "communication": {"type": "body_language", "signal": "accepting"}
            },
            "hints": ["trust-building", "tense"],
            "fragments": {
                "action_core": "the wolf sniffs the meat",
                "action_color": ["its posture relaxes slightly"],
                "traits": ["massive", "grey-furred"]
            },
            "reactions": [
                {
                    "entity": "npc_alpha_wolf",
                    "entity_name": "Alpha Wolf",
                    "state": "wary",
                    "fragments": ["ears prick forward"],
                    "response": "cautious_acceptance"
                }
            ]
        }
        self.assertEqual(plan["action_verb"], "give")
        self.assertEqual(plan["context"]["npc_state"]["current"], "wary")
        self.assertIn("trust-building", plan["hints"])
        self.assertEqual(plan["fragments"]["action_core"], "the wolf sniffs the meat")
        self.assertEqual(len(plan["reactions"]), 1)


if __name__ == "__main__":
    unittest.main()
