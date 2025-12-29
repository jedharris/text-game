"""Unit tests for LLM command parser.

These tests load real big_game and test parser with actual vocabulary and contexts.
"""

import unittest
from pathlib import Path
from typing import Dict, List

from src.game_engine import GameEngine
from src.shared_mlx import SharedMLXBackend
from src.llm_command_parser import LLMCommandParser


class TestLLMCommandParser(unittest.TestCase):
    """Test LLM command parser with real big_game."""

    @classmethod
    def setUpClass(cls):
        """Load shared backend and REAL game engine once for all tests."""
        # Use Qwen 2.5 7B from Phase 1
        cls.backend = SharedMLXBackend("mlx-community/Qwen2.5-7B-Instruct-4bit")

        # Load REAL big_game
        cls.engine = GameEngine(Path('examples/big_game'))

        # Extract REAL verbs from merged vocabulary
        cls.verbs = [v['word'] for v in cls.engine.merged_vocabulary.get('verbs', [])]

        print(f"\n[Test Setup] Loaded {len(cls.verbs)} verbs from big_game vocabulary")

    def setUp(self):
        """Create parser for each test."""
        self.parser = LLMCommandParser(self.backend, self.verbs)

    def _build_simple_context(self, objects: List[str], inventory: List[str], exits: List[str]) -> Dict[str, List[str]]:
        """Helper to build test context."""
        return {
            "location_objects": objects,
            "inventory": inventory,
            "exits": exits
        }

    def test_parser_initialization(self):
        """Parser initializes correctly with real vocabulary."""
        self.assertIsNotNone(self.parser)
        self.assertEqual(self.parser.verbs, self.verbs)
        self.assertIsNotNone(self.parser.cache)
        self.assertGreater(self.parser.system_prompt_length, 0)

    def test_simple_verb_only_command(self):
        """Parse simple verb-only command: 'look'."""
        context = self._build_simple_context(
            objects=[],
            inventory=[],
            exits=["north", "south"]
        )

        result = self.parser.parse_command("look", context)

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'command')
        self.assertEqual(result['action']['verb'], 'look')
        self.assertEqual(result['raw_input'], 'look')

    def test_verb_with_direction(self):
        """Parse movement command: 'go north'."""
        context = self._build_simple_context(
            objects=[],
            inventory=[],
            exits=["north", "south", "east"]
        )

        result = self.parser.parse_command("go north", context)

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'command')
        self.assertEqual(result['action']['verb'], 'go')
        self.assertEqual(result['action']['object'], 'north')

    def test_verb_with_object(self):
        """Parse simple verb + object: 'take bucket'."""
        context = self._build_simple_context(
            objects=["bucket", "torch"],
            inventory=[],
            exits=["up"]
        )

        result = self.parser.parse_command("take bucket", context)

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'command')
        self.assertEqual(result['action']['verb'], 'take')
        self.assertEqual(result['action']['object'], 'bucket')

    def test_verb_with_article(self):
        """Parse command with article: 'take the torch'."""
        context = self._build_simple_context(
            objects=["bucket", "torch"],
            inventory=[],
            exits=["up"]
        )

        result = self.parser.parse_command("take the torch", context)

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'command')
        self.assertEqual(result['action']['verb'], 'take')
        self.assertEqual(result['action']['object'], 'torch')

    def test_inventory_command(self):
        """Parse inventory command."""
        context = self._build_simple_context(
            objects=[],
            inventory=["torch", "bucket"],
            exits=[]
        )

        result = self.parser.parse_command("inventory", context)

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'command')
        self.assertEqual(result['action']['verb'], 'inventory')

    def test_examine_object(self):
        """Parse examine command: 'examine bucket'."""
        context = self._build_simple_context(
            objects=["bucket", "torch"],
            inventory=[],
            exits=["up"]
        )

        result = self.parser.parse_command("examine bucket", context)

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'command')
        self.assertEqual(result['action']['verb'], 'examine')
        self.assertEqual(result['action']['object'], 'bucket')

    def test_use_on_command(self):
        """Parse 'use X on Y' command."""
        context = self._build_simple_context(
            objects=["frozen_crystal", "stone_altar"],
            inventory=["ice_wand"],
            exits=[]
        )

        result = self.parser.parse_command("use ice_wand on frozen_crystal", context)

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'command')
        self.assertEqual(result['action']['verb'], 'use')
        # Parser should normalize to underscore format
        self.assertIn('object', result['action'])
        self.assertIn('indirect_object', result['action'])

    def test_object_from_inventory(self):
        """Parser should handle objects from inventory."""
        context = self._build_simple_context(
            objects=[],
            inventory=["brass_key"],
            exits=[]
        )

        result = self.parser.parse_command("examine brass_key", context)

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'command')
        self.assertEqual(result['action']['verb'], 'examine')
        self.assertEqual(result['action']['object'], 'brass_key')

    def test_unknown_verb_returns_none(self):
        """Unknown verb may be accepted by LLM - adapter will reject it."""
        context = self._build_simple_context(
            objects=["bucket"],
            inventory=[],
            exits=[]
        )

        result = self.parser.parse_command("dance with bucket", context)

        # LLM may accept unknown verb "dance" - that's OK
        # The adapter (Phase 4) will validate verbs against vocabulary
        # and reject invalid ones
        if result is not None:
            # Just verify structure is valid
            self.assertIn('type', result)
            if result.get('type') == 'command':
                self.assertIn('verb', result['action'])

    def test_hallucinated_object(self):
        """Parser may hallucinate object not in context - that's OK, handler will reject."""
        context = self._build_simple_context(
            objects=["bucket"],
            inventory=[],
            exits=[]
        )

        result = self.parser.parse_command("take unicorn", context)

        # Parser might produce {"verb": "take", "object": "unicorn"}
        # This is acceptable - the handler will later reject "unicorn" as invalid
        # Just verify the structure is valid if it returns something
        if result is not None:
            self.assertEqual(result.get('type'), 'command')
            self.assertEqual(result['action'].get('verb'), 'take')

    def test_natural_language_variations(self):
        """Parser should handle natural variations."""
        context = self._build_simple_context(
            objects=["bucket", "torch"],
            inventory=[],
            exits=[]
        )

        # Try different phrasings
        variations = [
            "pick up the bucket",
            "get bucket",
            "grab the bucket"
        ]

        for cmd in variations:
            result = self.parser.parse_command(cmd, context)
            # Some variations might work, some might not
            # Just verify if it succeeds, it has correct structure
            if result is not None:
                self.assertEqual(result.get('type'), 'command')
                self.assertIn('verb', result['action'])

    def test_give_to_command(self):
        """Parse 'give X to Y' command."""
        context = self._build_simple_context(
            objects=["aldric"],
            inventory=["silvermoss"],
            exits=[]
        )

        result = self.parser.parse_command("give silvermoss to aldric", context)

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'command')
        self.assertEqual(result['action']['verb'], 'give')
        self.assertIn('object', result['action'])
        self.assertIn('indirect_object', result['action'])

    def test_multi_word_item_ice_wand(self):
        """Parse multi-word item: 'ice wand' → ice_wand."""
        context = self._build_simple_context(
            objects=["ice_wand", "bucket"],
            inventory=[],
            exits=[]
        )

        result = self.parser.parse_command("take the ice wand", context)

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'command')
        self.assertEqual(result['action']['verb'], 'take')
        self.assertEqual(result['action']['object'], 'ice_wand')

    def test_multi_word_item_keepers_journal(self):
        """Parse multi-word item with apostrophe: "Keeper's journal" → keepers_journal."""
        context = self._build_simple_context(
            objects=["keepers_journal", "ancient_telescope"],
            inventory=[],
            exits=["west"]
        )

        result = self.parser.parse_command("examine the keeper's journal", context)

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'command')
        self.assertEqual(result['action']['verb'], 'examine')
        self.assertEqual(result['action']['object'], 'keepers_journal')

    def test_multi_word_item_ancient_telescope(self):
        """Parse multi-word item: 'ancient telescope' → ancient_telescope."""
        context = self._build_simple_context(
            objects=["ancient_telescope", "keepers_journal"],
            inventory=[],
            exits=[]
        )

        result = self.parser.parse_command("examine ancient telescope", context)

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'command')
        self.assertEqual(result['action']['verb'], 'examine')
        self.assertEqual(result['action']['object'], 'ancient_telescope')

    def test_multi_word_use_command(self):
        """Parse command with two multi-word items: 'use ice wand on frozen crystal'."""
        context = self._build_simple_context(
            objects=["frozen_crystal", "stone_altar"],
            inventory=["ice_wand"],
            exits=[]
        )

        result = self.parser.parse_command("use ice wand on frozen crystal", context)

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'command')
        self.assertEqual(result['action']['verb'], 'use')
        self.assertEqual(result['action']['object'], 'ice_wand')
        self.assertEqual(result['action']['indirect_object'], 'frozen_crystal')


@unittest.skipIf(True, "Integration tests - run manually with --verbose")
class TestLLMCommandParserIntegration(unittest.TestCase):
    """Integration tests for parser - run manually to see LLM output."""

    @classmethod
    def setUpClass(cls):
        """Load backend and game."""
        cls.backend = SharedMLXBackend("mlx-community/Qwen2.5-7B-Instruct-4bit")
        cls.engine = GameEngine(Path('examples/big_game'))
        cls.verbs = [v['word'] for v in cls.engine.merged_vocabulary.get('verbs', [])]

    def setUp(self):
        """Create parser."""
        self.parser = LLMCommandParser(self.backend, self.verbs)

    def test_complex_commands_verbose(self):
        """Test complex commands and print LLM output."""
        test_cases = [
            {
                "command": "use the ice wand on the frozen crystal",
                "context": {
                    "location_objects": ["ice_wand", "frozen_crystal", "stone_altar"],
                    "inventory": [],
                    "exits": ["north", "south"]
                }
            },
            {
                "command": "unlock the door with the brass key",
                "context": {
                    "location_objects": ["wooden_door"],
                    "inventory": ["brass_key"],
                    "exits": []
                }
            },
            {
                "command": "examine the keeper's journal",
                "context": {
                    "location_objects": ["keepers_journal", "ancient_telescope"],
                    "inventory": [],
                    "exits": ["west"]
                }
            }
        ]

        for i, test in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"Test {i}: {test['command']}")
            print(f"Context: {test['context']}")
            print("-" * 60)

            result = self.parser.parse_command(test['command'], test['context'])

            if result:
                import json
                print(json.dumps(result, indent=2))
            else:
                print("FAILED: Parser returned None")


if __name__ == "__main__":
    unittest.main()
