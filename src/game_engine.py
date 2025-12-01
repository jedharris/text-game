"""Game engine that manages state, behaviors, and vocabulary.

Provides a unified interface for initializing games, supporting both
text-based (parser-only) and LLM-augmented game modes.
"""

import json
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from src.state_manager import load_game_state, GameState
from src.behavior_manager import BehaviorManager
from src.llm_protocol import LLMProtocolHandler
from src.vocabulary_generator import extract_nouns_from_state, merge_vocabulary
from src.parser import Parser


class GameEngine:
    """Game engine that manages state, behaviors, and vocabulary.

    Encapsulates all game initialization logic for both text-based and
    LLM-augmented game modes.
    """

    def __init__(self, game_dir: Path):
        """Initialize the game engine.

        Args:
            game_dir: Path to game directory containing game_state.json

        Raises:
            FileNotFoundError: If game directory, game_state.json, or behaviors/ doesn't exist
            ValueError: If game_dir is not a directory, or game_state.json is invalid
        """
        # Validate game directory
        self.game_dir = Path(game_dir).absolute()
        if not self.game_dir.exists():
            raise FileNotFoundError(f"Game directory not found: {self.game_dir}")
        if not self.game_dir.is_dir():
            raise ValueError(f"Game directory path is not a directory: {self.game_dir}")

        # Validate game_state.json
        game_state_path = self.game_dir / "game_state.json"
        if not game_state_path.exists():
            raise FileNotFoundError(f"game_state.json not found in: {self.game_dir}")

        # Load game state
        try:
            self.game_state = load_game_state(str(game_state_path))
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid game_state.json: {e}")

        # Validate behaviors directory
        behaviors_dir = self.game_dir / "behaviors"
        if not behaviors_dir.exists() or not behaviors_dir.is_dir():
            raise FileNotFoundError(
                f"Game must have a behaviors/ directory: {behaviors_dir}\n"
                "Create one with at least a symlink to the engine's core behaviors."
            )

        # Initialize behavior manager and load modules
        self.behavior_manager = BehaviorManager()

        # Add game directory to sys.path so game-specific modules can be imported
        game_dir_str = str(self.game_dir)
        if game_dir_str not in sys.path:
            sys.path.insert(0, game_dir_str)

        # Load all behaviors from game directory (includes core via symlink)
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

        # Load and merge vocabulary
        vocab_path = Path(__file__).parent / 'vocabulary.json'
        with open(vocab_path, 'r') as f:
            base_vocab = json.load(f)

        extracted_nouns = extract_nouns_from_state(self.game_state)
        vocab_with_nouns = merge_vocabulary(base_vocab, extracted_nouns)
        self.merged_vocabulary = self.behavior_manager.get_merged_vocabulary(vocab_with_nouns)

        # Create JSON protocol handler
        self.json_handler = LLMProtocolHandler(self.game_state, behavior_manager=self.behavior_manager)

    def create_parser(self) -> Parser:
        """Create a Parser with merged vocabulary.

        Returns:
            Parser instance ready for command parsing
        """
        # Write merged vocabulary to temp file for Parser (it requires a file path)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.merged_vocabulary, f)
            vocab_path = f.name

        parser = Parser(vocab_path)
        Path(vocab_path).unlink()  # Clean up temp file
        return parser

    def create_narrator(self, api_key: str,
                       model: str = "claude-3-5-haiku-20241022",
                       show_traits: bool = False):
        """Create an LLMNarrator with game-specific configuration.

        Automatically loads narrator_prompt.txt from game directory.

        Args:
            api_key: Anthropic API key
            model: Model to use for generation
            show_traits: If True, print llm_context traits before narration

        Returns:
            LLMNarrator instance ready for natural language interaction

        Raises:
            ImportError: If anthropic library not installed
            FileNotFoundError: If narrator_prompt.txt not found in game directory
        """
        from src.llm_narrator import LLMNarrator

        # Check for narrator prompt in game directory
        prompt_path = self.game_dir / "narrator_prompt.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"narrator_prompt.txt not found in game directory: {self.game_dir}\n"
                "Each game must have its own narrator_prompt.txt file."
            )

        return LLMNarrator(
            api_key=api_key,
            json_handler=self.json_handler,
            model=model,
            prompt_file=prompt_path,
            behavior_manager=self.behavior_manager,
            vocabulary=self.merged_vocabulary,
            show_traits=show_traits
        )

    def reload_state(self, new_state: GameState) -> None:
        """Reload the game state (e.g., after loading a save file).

        Recreates the JSON handler with the new state while preserving
        behavior manager and vocabulary.

        Args:
            new_state: The new game state to use
        """
        self.game_state = new_state
        self.json_handler = LLMProtocolHandler(self.game_state, behavior_manager=self.behavior_manager)
