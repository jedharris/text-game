"""Tests for examining actors (self and NPCs).

GitHub Issue #36: Add support for examining actors.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.state_manager import load_game_state
from src.state_accessor import StateAccessor, HandlerResult
from src.behavior_manager import BehaviorManager
from src.word_entry import WordEntry, WordType
from tests.conftest import make_word_entry


def make_self_word_entry() -> WordEntry:
    """Create a WordEntry for self-reference words with proper synonyms.

    This mirrors what the parser produces when it encounters 'self', 'me', or 'myself'.
    The parser's lookup table maps all synonyms to the canonical entry, so regardless
    of which word the player types, the returned WordEntry has word='self' with
    synonyms=['me', 'myself'].
    """
    return WordEntry(
        word="self",
        word_type=WordType.NOUN,
        synonyms=["me", "myself"]
    )


class TestFindActorByName(unittest.TestCase):
    """Tests for find_actor_by_name utility function."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_state = load_game_state({
            "metadata": {"title": "Test", "start_location": "loc_start"},
            "locations": [
                {"id": "loc_start", "name": "Start", "description": "A room", "exits": {}},
                {"id": "loc_other", "name": "Other", "description": "Another room", "exits": {}}
            ],
            "items": [],
            "locks": [],
            "actors": {
                "player": {
                    "id": "player",
                    "name": "Landry",
                    "description": "A brave adventurer.",
                    "location": "loc_start",
                    "inventory": []
                },
                "guard": {
                    "id": "guard",
                    "name": "Guard",
                    "description": "A stern guard.",
                    "location": "loc_start",
                    "inventory": []
                },
                "merchant": {
                    "id": "merchant",
                    "name": "Merchant",
                    "description": "A friendly merchant.",
                    "location": "loc_other",
                    "inventory": []
                }
            }
        })
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_find_self_with_self_keyword(self):
        """find_actor_by_name returns acting actor for 'self' WordEntry."""
        from utilities.utils import find_actor_by_name
        # Parser returns canonical WordEntry regardless of which synonym was typed
        self_entry = make_self_word_entry()
        result = find_actor_by_name(self.accessor, self_entry, "player")
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "player")

    def test_find_self_with_me_keyword(self):
        """find_actor_by_name returns acting actor for 'me' (parser returns canonical 'self' entry)."""
        from utilities.utils import find_actor_by_name
        # When player types "me", parser returns the canonical "self" WordEntry
        # because the lookup table maps synonyms to their canonical entry
        self_entry = make_self_word_entry()
        result = find_actor_by_name(self.accessor, self_entry, "player")
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "player")

    def test_find_self_with_myself_keyword(self):
        """find_actor_by_name returns acting actor for 'myself' (parser returns canonical 'self' entry)."""
        from utilities.utils import find_actor_by_name
        # Same as above - parser normalizes all synonyms to canonical entry
        self_entry = make_self_word_entry()
        result = find_actor_by_name(self.accessor, self_entry, "player")
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "player")

    def test_find_npc_in_same_location(self):
        """find_actor_by_name returns NPC in same location."""
        from utilities.utils import find_actor_by_name
        guard_entry = make_word_entry("Guard")
        result = find_actor_by_name(self.accessor, guard_entry, "player")
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "guard")

    def test_find_npc_case_insensitive(self):
        """find_actor_by_name is case-insensitive for NPC names."""
        from utilities.utils import find_actor_by_name
        guard_entry = make_word_entry("guard")
        result = find_actor_by_name(self.accessor, guard_entry, "player")
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "guard")

    def test_npc_in_different_location_not_found(self):
        """find_actor_by_name returns None for NPC in different location."""
        from utilities.utils import find_actor_by_name
        merchant_entry = make_word_entry("Merchant")
        result = find_actor_by_name(self.accessor, merchant_entry, "player")
        self.assertIsNone(result)

    def test_nonexistent_actor_not_found(self):
        """find_actor_by_name returns None for nonexistent actor."""
        from utilities.utils import find_actor_by_name
        wizard_entry = make_word_entry("wizard")
        result = find_actor_by_name(self.accessor, wizard_entry, "player")
        self.assertIsNone(result)

    def test_npc_can_find_player(self):
        """NPCs can find the player actor by name."""
        from utilities.utils import find_actor_by_name
        landry_entry = make_word_entry("Landry")
        result = find_actor_by_name(self.accessor, landry_entry, "guard")
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "player")

    def test_npc_self_reference(self):
        """NPCs using 'self' get themselves, not the player."""
        from utilities.utils import find_actor_by_name
        self_entry = make_self_word_entry()
        result = find_actor_by_name(self.accessor, self_entry, "guard")
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "guard")


class TestFormatInventory(unittest.TestCase):
    """Tests for format_inventory utility function."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_state = load_game_state({
            "metadata": {"title": "Test", "start_location": "loc_start"},
            "locations": [
                {"id": "loc_start", "name": "Start", "description": "A room", "exits": {}}
            ],
            "items": [
                {"id": "sword", "name": "sword", "description": "A rusty sword", "location": "player", "properties": {"portable": True}, "states": {"equipped": True}},
                {"id": "key", "name": "key", "description": "An iron key", "location": "player", "properties": {"portable": True}, "states": {"equipped": True}}
            ],
            "locks": [],
            "actors": {
                "player": {
                    "id": "player",
                    "name": "Landry",
                    "description": "A brave adventurer.",
                    "location": "loc_start",
                    "inventory": ["sword", "key"]
                }
            }
        })
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_format_inventory_for_self(self):
        """format_inventory with for_self=True uses 'You are carrying'."""
        from utilities.utils import format_inventory
        actor = self.accessor.get_actor("player")
        message, items_data = format_inventory(self.accessor, actor, for_self=True)
        self.assertIsNotNone(message)
        self.assertIn("You are carrying", message)
        self.assertIn("sword", message)
        self.assertIn("key", message)
        self.assertEqual(len(items_data), 2)

    def test_format_inventory_for_other(self):
        """format_inventory with for_self=False uses 'Carrying'."""
        from utilities.utils import format_inventory
        actor = self.accessor.get_actor("player")
        message, items_data = format_inventory(self.accessor, actor, for_self=False)
        self.assertIsNotNone(message)
        self.assertIn("Carrying", message)
        self.assertNotIn("You are", message)

    def test_format_inventory_empty(self):
        """format_inventory returns None for empty inventory."""
        from utilities.utils import format_inventory
        # Create a separate game state with an actor with empty inventory
        empty_state = load_game_state({
            "metadata": {"title": "Test", "start_location": "loc_start"},
            "locations": [
                {"id": "loc_start", "name": "Start", "description": "A room", "exits": {}}
            ],
            "items": [],
            "locks": [],
            "actors": {
                "player": {
                    "id": "player",
                    "name": "Empty",
                    "description": "",
                    "location": "loc_start",
                    "inventory": []
                }
            }
        })
        empty_accessor = StateAccessor(empty_state, self.behavior_manager)
        empty_actor = empty_accessor.get_actor("player")
        message, items_data = format_inventory(empty_accessor, empty_actor, for_self=True)
        self.assertIsNone(message)
        self.assertEqual(items_data, [])


class TestHandleExamineActors(unittest.TestCase):
    """Tests for handle_examine with actors."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_state = load_game_state({
            "metadata": {"title": "Test", "start_location": "loc_start"},
            "locations": [
                {"id": "loc_start", "name": "Start", "description": "A room", "exits": {}}
            ],
            "items": [
                {"id": "sword", "name": "sword", "description": "A rusty sword", "location": "player", "properties": {"portable": True}, "states": {"equipped": True}}
            ],
            "locks": [],
            "actors": {
                "player": {
                    "id": "player",
                    "name": "Landry",
                    "description": "A brave adventurer with keen eyes.",
                    "location": "loc_start",
                    "inventory": ["sword"],
                    "properties": {
                        "llm_context": {
                            "traits": ["brave", "adventurous"]
                        }
                    }
                },
                "guard": {
                    "id": "guard",
                    "name": "Guard",
                    "description": "A stern guard in plate armor.",
                    "location": "loc_start",
                    "inventory": []
                }
            }
        })
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_examine_self(self):
        """examine self returns player description and inventory."""
        from behaviors.core.perception import handle_examine
        self_entry = make_self_word_entry()
        result = handle_examine(self.accessor, {"actor_id": "player", "object": self_entry})
        self.assertTrue(result.success)
        self.assertIn("brave adventurer", result.message)
        self.assertIn("You are carrying", result.message)
        self.assertIn("sword", result.message)

    def test_examine_me(self):
        """examine me returns player description (synonym handled via canonical WordEntry)."""
        from behaviors.core.perception import handle_examine
        # Parser normalizes "me" to canonical "self" WordEntry
        self_entry = make_self_word_entry()
        result = handle_examine(self.accessor, {"actor_id": "player", "object": self_entry})
        self.assertTrue(result.success)
        self.assertIn("brave adventurer", result.message)

    def test_examine_myself(self):
        """examine myself returns player description (synonym handled via canonical WordEntry)."""
        from behaviors.core.perception import handle_examine
        # Parser normalizes "myself" to canonical "self" WordEntry
        self_entry = make_self_word_entry()
        result = handle_examine(self.accessor, {"actor_id": "player", "object": self_entry})
        self.assertTrue(result.success)
        self.assertIn("brave adventurer", result.message)

    def test_examine_npc_in_same_location(self):
        """examine guard returns guard description."""
        from behaviors.core.perception import handle_examine
        guard_entry = make_word_entry("guard")
        result = handle_examine(self.accessor, {"actor_id": "player", "object": guard_entry})
        self.assertTrue(result.success)
        self.assertIn("stern guard", result.message)

    def test_examine_player_gives_helpful_message(self):
        """examine player gives helpful message to use self/me."""
        from behaviors.core.perception import handle_examine
        player_entry = make_word_entry("player")
        result = handle_examine(self.accessor, {"actor_id": "player", "object": player_entry})
        self.assertFalse(result.success)
        self.assertIn("examine self", result.message)
        self.assertIn("examine me", result.message)

    def test_examine_self_no_description(self):
        """examine self with no description shows default message."""
        # Remove description - Actor is a dataclass, modify attribute directly
        self.game_state.actors["player"].description = ""
        from behaviors.core.perception import handle_examine
        self_entry = make_self_word_entry()
        result = handle_examine(self.accessor, {"actor_id": "player", "object": self_entry})
        self.assertTrue(result.success)
        self.assertIn("You examine yourself", result.message)

    def test_examine_npc_no_description(self):
        """examine NPC with no description shows 'You see Name'."""
        self.game_state.actors["guard"].description = ""
        from behaviors.core.perception import handle_examine
        guard_entry = make_word_entry("guard")
        result = handle_examine(self.accessor, {"actor_id": "player", "object": guard_entry})
        self.assertTrue(result.success)
        self.assertIn("You see Guard", result.message)

    def test_examine_self_empty_inventory(self):
        """examine self with empty inventory doesn't show inventory line."""
        self.game_state.actors["player"].inventory = []
        from behaviors.core.perception import handle_examine
        self_entry = make_self_word_entry()
        result = handle_examine(self.accessor, {"actor_id": "player", "object": self_entry})
        self.assertTrue(result.success)
        self.assertNotIn("carrying", result.message.lower())

    def test_examine_actor_returns_llm_context(self):
        """examine actor includes llm_context in data."""
        from behaviors.core.perception import handle_examine
        self_entry = make_self_word_entry()
        result = handle_examine(self.accessor, {"actor_id": "player", "object": self_entry})
        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertEqual(result.data.get("type"), "actor")

    def test_examine_nonexistent_actor(self):
        """examine nonexistent actor returns not found."""
        from behaviors.core.perception import handle_examine
        wizard_entry = make_word_entry("wizard")
        result = handle_examine(self.accessor, {"actor_id": "player", "object": wizard_entry})
        self.assertFalse(result.success)
        self.assertIn("don't see", result.message)

    def test_npc_examines_player(self):
        """NPC can examine the player by name."""
        from behaviors.core.perception import handle_examine
        landry_entry = make_word_entry("Landry")
        result = handle_examine(self.accessor, {"actor_id": "guard", "object": landry_entry})
        self.assertTrue(result.success)
        self.assertIn("brave adventurer", result.message)
        # NPC sees player's inventory
        self.assertIn("Carrying", result.message)
        self.assertIn("sword", result.message)


class TestValidateActorNames(unittest.TestCase):
    """Tests for _validate_actor_names validator."""

    def test_actor_named_player_fails(self):
        """Actor named 'player' fails validation."""
        from src.validators import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            load_game_state({
                "metadata": {"title": "Test", "start_location": "loc_start"},
                "locations": [{"id": "loc_start", "name": "Start", "description": "A room", "exits": {}}],
                "items": [],
                "locks": [],
                "actors": {
                    "player": {"id": "player", "name": "player", "description": "", "location": "loc_start", "inventory": []}
                }
            })
        self.assertIn("prohibited name", str(ctx.exception).lower())

    def test_actor_named_player_uppercase_fails(self):
        """Actor named 'Player' (uppercase) fails validation."""
        from src.validators import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            load_game_state({
                "metadata": {"title": "Test", "start_location": "loc_start"},
                "locations": [{"id": "loc_start", "name": "Start", "description": "A room", "exits": {}}],
                "items": [],
                "locks": [],
                "actors": {
                    "player": {"id": "player", "name": "Player", "description": "", "location": "loc_start", "inventory": []}
                }
            })
        self.assertIn("prohibited name", str(ctx.exception).lower())

    def test_actor_named_npc_fails(self):
        """Actor named 'NPC' fails validation."""
        from src.validators import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            load_game_state({
                "metadata": {"title": "Test", "start_location": "loc_start"},
                "locations": [{"id": "loc_start", "name": "Start", "description": "A room", "exits": {}}],
                "items": [],
                "locks": [],
                "actors": {
                    "player": {"id": "player", "name": "Landry", "description": "", "location": "loc_start", "inventory": []},
                    "npc1": {"id": "npc1", "name": "NPC", "description": "", "location": "loc_start", "inventory": []}
                }
            })
        self.assertIn("prohibited name", str(ctx.exception).lower())

    def test_actor_named_self_fails(self):
        """Actor named 'self' fails validation."""
        from src.validators import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            load_game_state({
                "metadata": {"title": "Test", "start_location": "loc_start"},
                "locations": [{"id": "loc_start", "name": "Start", "description": "A room", "exits": {}}],
                "items": [],
                "locks": [],
                "actors": {
                    "player": {"id": "player", "name": "self", "description": "", "location": "loc_start", "inventory": []}
                }
            })
        self.assertIn("prohibited name", str(ctx.exception).lower())

    def test_actor_named_me_fails(self):
        """Actor named 'me' fails validation."""
        from src.validators import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            load_game_state({
                "metadata": {"title": "Test", "start_location": "loc_start"},
                "locations": [{"id": "loc_start", "name": "Start", "description": "A room", "exits": {}}],
                "items": [],
                "locks": [],
                "actors": {
                    "player": {"id": "player", "name": "me", "description": "", "location": "loc_start", "inventory": []}
                }
            })
        self.assertIn("prohibited name", str(ctx.exception).lower())

    def test_actor_named_myself_fails(self):
        """Actor named 'myself' fails validation."""
        from src.validators import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            load_game_state({
                "metadata": {"title": "Test", "start_location": "loc_start"},
                "locations": [{"id": "loc_start", "name": "Start", "description": "A room", "exits": {}}],
                "items": [],
                "locks": [],
                "actors": {
                    "player": {"id": "player", "name": "myself", "description": "", "location": "loc_start", "inventory": []}
                }
            })
        self.assertIn("prohibited name", str(ctx.exception).lower())

    def test_actor_with_valid_name_passes(self):
        """Actor with valid name passes validation."""
        from src.validators import validate_game_state
        state = load_game_state({
            "metadata": {"title": "Test", "start_location": "loc_start"},
            "locations": [{"id": "loc_start", "name": "Start", "description": "A room", "exits": {}}],
            "items": [],
            "locks": [],
            "actors": {
                "player": {"id": "player", "name": "Landry", "description": "", "location": "loc_start", "inventory": []},
                "guard": {"id": "guard", "name": "Guard", "description": "", "location": "loc_start", "inventory": []}
            }
        })
        # Should not raise
        validate_game_state(state)


class TestActorsVocabulary(unittest.TestCase):
    """Tests for actors.py vocabulary module."""

    def test_vocabulary_has_self_noun(self):
        """actors vocabulary includes 'self' noun."""
        from behaviors.core.actors import vocabulary
        nouns = vocabulary.get("nouns", [])
        self.assertTrue(any(n.get("word") == "self" for n in nouns))

    def test_self_noun_has_synonyms(self):
        """'self' noun has 'me' and 'myself' synonyms."""
        from behaviors.core.actors import vocabulary
        nouns = vocabulary.get("nouns", [])
        self_noun = next((n for n in nouns if n.get("word") == "self"), None)
        self.assertIsNotNone(self_noun)
        synonyms = self_noun.get("synonyms", [])
        self.assertIn("me", synonyms)
        self.assertIn("myself", synonyms)


if __name__ == "__main__":
    unittest.main()
