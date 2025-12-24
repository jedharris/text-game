"""
Tests for narrator_helpers module.

Tests fragment selection helpers for the narrator system.
"""

import unittest
from unittest.mock import MagicMock

from src.narrator_helpers import (
    select_state_fragments,
    select_action_fragments,
    select_traits,
    build_reaction,
    RepetitionBuffer,
)


class TestRepetitionBuffer(unittest.TestCase):
    """Tests for RepetitionBuffer class."""

    def test_empty_buffer(self) -> None:
        """New buffer contains nothing."""
        buffer = RepetitionBuffer(size=5)
        self.assertFalse(buffer.contains("anything"))

    def test_add_and_contains(self) -> None:
        """Added fragments are found in buffer."""
        buffer = RepetitionBuffer(size=5)
        buffer.add("fragment1")
        buffer.add("fragment2")

        self.assertTrue(buffer.contains("fragment1"))
        self.assertTrue(buffer.contains("fragment2"))
        self.assertFalse(buffer.contains("fragment3"))

    def test_eviction_when_full(self) -> None:
        """Oldest fragments are evicted when buffer is full."""
        buffer = RepetitionBuffer(size=3)
        buffer.add("frag1")
        buffer.add("frag2")
        buffer.add("frag3")
        buffer.add("frag4")  # Should evict frag1

        self.assertFalse(buffer.contains("frag1"))
        self.assertTrue(buffer.contains("frag2"))
        self.assertTrue(buffer.contains("frag3"))
        self.assertTrue(buffer.contains("frag4"))

    def test_filter_pool(self) -> None:
        """Filter pool removes recently used fragments."""
        buffer = RepetitionBuffer(size=5)
        buffer.add("used1")
        buffer.add("used2")

        pool = ["used1", "fresh1", "used2", "fresh2"]
        filtered = buffer.filter_pool(pool)

        self.assertEqual(filtered, ["fresh1", "fresh2"])

    def test_filter_pool_empty_result(self) -> None:
        """Filter pool can return empty if all used."""
        buffer = RepetitionBuffer(size=5)
        buffer.add("a")
        buffer.add("b")

        pool = ["a", "b"]
        filtered = buffer.filter_pool(pool)

        self.assertEqual(filtered, [])

    def test_filter_pool_preserves_order(self) -> None:
        """Filter pool preserves original order of remaining items."""
        buffer = RepetitionBuffer(size=5)
        buffer.add("b")

        pool = ["a", "b", "c", "d"]
        filtered = buffer.filter_pool(pool)

        self.assertEqual(filtered, ["a", "c", "d"])


class TestSelectStateFragments(unittest.TestCase):
    """Tests for select_state_fragments function."""

    def test_select_from_state_fragments(self) -> None:
        """Selects fragments from llm_context.state_fragments[state]."""
        entity = MagicMock()
        entity.properties = {
            "llm_context": {
                "state_fragments": {
                    "hostile": ["hackles raised", "teeth bared", "growling"],
                    "friendly": ["tail wagging", "ears relaxed"]
                }
            }
        }

        fragments = select_state_fragments(entity, "hostile", max_count=2)

        self.assertLessEqual(len(fragments), 2)
        for frag in fragments:
            self.assertIn(frag, ["hackles raised", "teeth bared", "growling"])

    def test_select_respects_max_count(self) -> None:
        """Selection respects max_count limit."""
        entity = MagicMock()
        entity.properties = {
            "llm_context": {
                "state_fragments": {
                    "hostile": ["f1", "f2", "f3", "f4", "f5"]
                }
            }
        }

        fragments = select_state_fragments(entity, "hostile", max_count=2)
        self.assertLessEqual(len(fragments), 2)

    def test_missing_llm_context_returns_empty(self) -> None:
        """Missing llm_context returns empty list."""
        entity = MagicMock()
        entity.properties = {}

        fragments = select_state_fragments(entity, "hostile")
        self.assertEqual(fragments, [])

    def test_missing_state_returns_empty(self) -> None:
        """Missing state key returns empty list."""
        entity = MagicMock()
        entity.properties = {
            "llm_context": {
                "state_fragments": {
                    "friendly": ["tail wagging"]
                }
            }
        }

        fragments = select_state_fragments(entity, "hostile")
        self.assertEqual(fragments, [])

    def test_respects_repetition_buffer(self) -> None:
        """Fragments in repetition buffer are excluded."""
        entity = MagicMock()
        entity.properties = {
            "llm_context": {
                "state_fragments": {
                    "hostile": ["hackles raised", "teeth bared"]
                }
            }
        }

        buffer = RepetitionBuffer(size=5)
        buffer.add("hackles raised")

        fragments = select_state_fragments(
            entity, "hostile", max_count=2, repetition_buffer=buffer
        )

        self.assertNotIn("hackles raised", fragments)
        # Should get "teeth bared" if any
        if fragments:
            self.assertIn("teeth bared", fragments)


class TestSelectActionFragments(unittest.TestCase):
    """Tests for select_action_fragments function."""

    def test_select_action_fragments_full(self) -> None:
        """Full verbosity selects core + color."""
        entity = MagicMock()
        entity.properties = {
            "llm_context": {
                "action_fragments": {
                    "unlock": {
                        "core": ["the lock clicks open", "the mechanism releases"],
                        "color": ["runes flicker", "dust falls", "hinges creak"]
                    }
                }
            }
        }

        result = select_action_fragments(entity, "unlock", verbosity="full")

        self.assertIn("action_core", result)
        self.assertIn("action_color", result)
        self.assertIsInstance(result["action_core"], str)
        self.assertIsInstance(result["action_color"], list)

    def test_select_action_fragments_brief(self) -> None:
        """Brief verbosity selects core only."""
        entity = MagicMock()
        entity.properties = {
            "llm_context": {
                "action_fragments": {
                    "unlock": {
                        "core": ["the lock clicks open"],
                        "color": ["runes flicker", "dust falls"]
                    }
                }
            }
        }

        result = select_action_fragments(entity, "unlock", verbosity="brief")

        self.assertIn("action_core", result)
        # Brief should have empty or no color
        self.assertEqual(result.get("action_color", []), [])

    def test_missing_verb_returns_empty(self) -> None:
        """Missing verb key returns empty dict."""
        entity = MagicMock()
        entity.properties = {
            "llm_context": {
                "action_fragments": {
                    "open": {"core": ["door swings"]}
                }
            }
        }

        result = select_action_fragments(entity, "unlock")
        self.assertEqual(result, {})

    def test_missing_llm_context_returns_empty(self) -> None:
        """Missing llm_context returns empty dict."""
        entity = MagicMock()
        entity.properties = {}

        result = select_action_fragments(entity, "unlock")
        self.assertEqual(result, {})


class TestSelectTraits(unittest.TestCase):
    """Tests for select_traits function."""

    def test_select_traits(self) -> None:
        """Selects traits from llm_context.traits."""
        entity = MagicMock()
        entity.properties = {
            "llm_context": {
                "traits": ["massive", "grey-furred", "amber eyes", "scarred"]
            }
        }

        traits = select_traits(entity, max_count=2)

        self.assertLessEqual(len(traits), 2)
        for trait in traits:
            self.assertIn(trait, ["massive", "grey-furred", "amber eyes", "scarred"])

    def test_missing_traits_returns_empty(self) -> None:
        """Missing traits returns empty list."""
        entity = MagicMock()
        entity.properties = {"llm_context": {}}

        traits = select_traits(entity)
        self.assertEqual(traits, [])

    def test_respects_repetition_buffer(self) -> None:
        """Traits in repetition buffer are excluded."""
        entity = MagicMock()
        entity.properties = {
            "llm_context": {
                "traits": ["massive", "grey-furred"]
            }
        }

        buffer = RepetitionBuffer(size=5)
        buffer.add("massive")

        traits = select_traits(entity, max_count=2, repetition_buffer=buffer)

        self.assertNotIn("massive", traits)


class TestBuildReaction(unittest.TestCase):
    """Tests for build_reaction function."""

    def test_build_basic_reaction(self) -> None:
        """Builds reaction dict from entity and state."""
        entity = MagicMock()
        entity.id = "npc_guard"
        entity.name = "Town Guard"
        entity.properties = {
            "llm_context": {
                "state_fragments": {
                    "hostile": ["hand on sword", "blocking path"]
                }
            }
        }

        reaction = build_reaction(entity, "hostile", "confrontation")

        self.assertEqual(reaction["entity"], "npc_guard")
        self.assertEqual(reaction["entity_name"], "Town Guard")
        self.assertEqual(reaction["state"], "hostile")
        self.assertEqual(reaction["response"], "confrontation")
        self.assertIn("fragments", reaction)

    def test_build_reaction_respects_max_fragments(self) -> None:
        """Reaction fragment count respects max_fragments."""
        entity = MagicMock()
        entity.id = "npc_guard"
        entity.name = "Guard"
        entity.properties = {
            "llm_context": {
                "state_fragments": {
                    "hostile": ["f1", "f2", "f3", "f4", "f5"]
                }
            }
        }

        reaction = build_reaction(entity, "hostile", "confrontation", max_fragments=2)

        self.assertLessEqual(len(reaction["fragments"]), 2)

    def test_build_reaction_missing_fragments(self) -> None:
        """Reaction with missing fragments has empty list."""
        entity = MagicMock()
        entity.id = "npc_villager"
        entity.name = "Villager"
        entity.properties = {}

        reaction = build_reaction(entity, "nervous", "avoidance")

        self.assertEqual(reaction["entity"], "npc_villager")
        self.assertEqual(reaction["fragments"], [])


if __name__ == "__main__":
    unittest.main()
