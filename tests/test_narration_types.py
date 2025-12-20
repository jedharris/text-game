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
)
from src.state_accessor import HandlerResult


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


if __name__ == "__main__":
    unittest.main()
