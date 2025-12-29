"""Test GameEngine integration with LLM parser."""

import unittest
from pathlib import Path

from src.game_engine import GameEngine
from src.shared_mlx import SharedMLXBackend


class TestGameEngineLLMParser(unittest.TestCase):
    """Test that GameEngine can create and use LLM parser."""

    @classmethod
    def setUpClass(cls):
        """Load game engine and shared backend once."""
        cls.engine = GameEngine(Path('examples/big_game'))
        cls.backend = SharedMLXBackend("mlx-community/Qwen2.5-7B-Instruct-4bit")

        print("\n[GameEngine Integration Test] Loaded engine and backend")

    def test_create_llm_parser(self):
        """GameEngine can create LLM parser and adapter."""
        parser, adapter = self.engine.create_llm_parser(self.backend)

        self.assertIsNotNone(parser)
        self.assertIsNotNone(adapter)

    def test_build_parser_context(self):
        """GameEngine can build parser context from game state."""
        context = self.engine.build_parser_context("player")

        self.assertIn("location_objects", context)
        self.assertIn("inventory", context)
        self.assertIn("exits", context)
        self.assertIsInstance(context["location_objects"], list)
        self.assertIsInstance(context["inventory"], list)
        self.assertIsInstance(context["exits"], list)

    def test_full_pipeline_via_game_engine(self):
        """Full pipeline: GameEngine → parser → adapter → ParsedCommand."""
        # Create parser and adapter via GameEngine
        parser, adapter = self.engine.create_llm_parser(self.backend)

        # Build context from game state
        context = self.engine.build_parser_context("player")

        # Parse a command
        player_input = "look"
        parser_output = parser.parse_command(player_input, context)
        parsed_command = adapter.to_parsed_command(parser_output, player_input)

        self.assertIsNotNone(parsed_command)
        self.assertEqual(parsed_command.verb.word, "look")
        self.assertEqual(parsed_command.raw, "look")

    def test_context_has_real_objects(self):
        """Context built from game state has actual objects."""
        context = self.engine.build_parser_context("player")

        # Player starts in nexus_chamber which has exits
        self.assertGreater(len(context["exits"]), 0)

    def test_parse_with_real_game_context(self):
        """Parse command using real game context."""
        parser, adapter = self.engine.create_llm_parser(self.backend)
        context = self.engine.build_parser_context("player")

        # Player starts in nexus_chamber with exits to north, south, east
        player_input = "go north"
        parser_output = parser.parse_command(player_input, context)
        parsed_command = adapter.to_parsed_command(parser_output, player_input)

        self.assertIsNotNone(parsed_command)
        self.assertEqual(parsed_command.verb.word, "go")
        self.assertIsNotNone(parsed_command.direct_object)
        self.assertEqual(parsed_command.direct_object.word, "north")


if __name__ == "__main__":
    unittest.main()
