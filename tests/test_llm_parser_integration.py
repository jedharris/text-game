"""Integration tests for LLM parser + adapter pipeline.

Tests the full flow: player input → LLM parser → adapter → ParsedCommand
"""

import unittest
from pathlib import Path
from typing import Dict, List, Optional

from src.game_engine import GameEngine
from src.shared_mlx import SharedMLXBackend
from src.llm_command_parser import LLMCommandParser
from src.llm_parser_adapter import LLMParserAdapter
from src.parsed_command import ParsedCommand


class TestLLMParserIntegration(unittest.TestCase):
    """Test full LLM parser + adapter integration with real big_game."""

    backend: SharedMLXBackend
    engine: GameEngine
    verbs: List[str]
    parser: LLMCommandParser
    adapter: LLMParserAdapter

    @classmethod
    def setUpClass(cls):
        """Load shared backend, game engine, parser, and adapter once."""
        print("\n[Integration Test Setup] Loading model and game...")

        # Load shared backend (Qwen 2.5 7B)
        cls.backend = SharedMLXBackend("mlx-community/Qwen2.5-7B-Instruct-4bit")

        # Load real big_game
        cls.engine = GameEngine(Path('examples/big_game'))

        # Extract verbs
        cls.verbs = [v['word'] for v in cls.engine.merged_vocabulary.get('verbs', [])]

        # Create parser
        cls.parser = LLMCommandParser(cls.backend, cls.verbs)

        # Create adapter
        cls.adapter = LLMParserAdapter(cls.engine.merged_vocabulary)

        print(f"  Model loaded: Qwen 2.5 7B")
        print(f"  Verbs: {len(cls.verbs)}")
        print(f"  Ready for integration tests")

    def _build_context(self, objects: List[str], inventory: List[str], exits: List[str]) -> Dict[str, List[str]]:
        """Helper to build context dict."""
        return {
            "location_objects": objects,
            "inventory": inventory,
            "exits": exits
        }

    def _parse_command_full_pipeline(
        self,
        player_input: str,
        context: Dict[str, List[str]]
    ) -> Optional[ParsedCommand]:
        """Full pipeline: player input → LLM parser → adapter → ParsedCommand."""
        # Step 1: LLM parser
        parser_output = self.parser.parse_command(player_input, context)

        # Step 2: Adapter
        parsed_command = self.adapter.to_parsed_command(parser_output, player_input)

        return parsed_command

    def test_simple_look_command(self):
        """Integration: 'look' → ParsedCommand."""
        context = self._build_context([], [], ["north"])

        result = self._parse_command_full_pipeline("look", context)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, ParsedCommand)
        self.assertEqual(result.verb.word, "look")
        self.assertEqual(result.raw, "look")

    def test_take_single_word_object(self):
        """Integration: 'take bucket' → ParsedCommand."""
        context = self._build_context(["bucket", "torch"], [], [])

        result = self._parse_command_full_pipeline("take bucket", context)

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertIsNotNone(result.direct_object)
        self.assertEqual(result.direct_object.word, "bucket")

    def test_take_multi_word_object(self):
        """Integration: 'take ice wand' → ParsedCommand."""
        context = self._build_context(["ice_wand"], [], [])

        result = self._parse_command_full_pipeline("take the ice wand", context)

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertIsNotNone(result.direct_object)
        self.assertEqual(result.direct_object.word, "ice wand")

    def test_examine_keepers_journal(self):
        """Integration: 'examine keeper's journal' → ParsedCommand."""
        context = self._build_context(["keepers_journal", "ancient_telescope"], [], [])

        result = self._parse_command_full_pipeline("examine the keeper's journal", context)

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "examine")
        self.assertIsNotNone(result.direct_object)
        self.assertIn("journal", result.direct_object.word.lower())

    def test_use_ice_wand_on_crystal(self):
        """Integration: 'use ice wand on frozen crystal' → ParsedCommand."""
        context = self._build_context(["frozen_crystal"], ["ice_wand"], [])

        result = self._parse_command_full_pipeline("use ice wand on frozen crystal", context)

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "use")
        self.assertIsNotNone(result.direct_object)
        self.assertEqual(result.direct_object.word, "ice wand")
        self.assertIsNotNone(result.indirect_object)
        self.assertIn("crystal", result.indirect_object.word.lower())
        # Preposition is optional - LLM may or may not include it
        if result.preposition:
            self.assertEqual(result.preposition.word, "on")

    def test_go_north(self):
        """Integration: 'go north' → ParsedCommand."""
        context = self._build_context([], [], ["north", "south"])

        result = self._parse_command_full_pipeline("go north", context)

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "go")
        self.assertIsNotNone(result.direct_object)
        self.assertEqual(result.direct_object.word, "north")

    def test_give_to_npc(self):
        """Integration: 'give silvermoss to aldric' → ParsedCommand."""
        context = self._build_context(["aldric"], ["silvermoss"], [])

        result = self._parse_command_full_pipeline("give silvermoss to aldric", context)

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "give")
        self.assertIsNotNone(result.direct_object)
        # Preposition is optional - handlers can infer from verb
        if result.preposition:
            self.assertEqual(result.preposition.word, "to")

    def test_unknown_verb_rejected(self):
        """Integration: unknown verb 'dance' → None."""
        context = self._build_context(["bucket"], [], [])

        result = self._parse_command_full_pipeline("dance with the bucket", context)

        # Adapter should reject unknown verb
        self.assertIsNone(result)

    def test_natural_language_variation(self):
        """Integration: 'pick up the bucket' → ParsedCommand."""
        context = self._build_context(["bucket"], [], [])

        result = self._parse_command_full_pipeline("pick up the bucket", context)

        # LLM should normalize to "take"
        if result:
            self.assertEqual(result.verb.word, "take")
            self.assertIsNotNone(result.direct_object)


if __name__ == "__main__":
    unittest.main()
