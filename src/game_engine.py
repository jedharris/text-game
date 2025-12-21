"""Game engine that manages state, behaviors, and vocabulary.

Provides a unified interface for initializing games, supporting both
text-based (parser-only) and LLM-augmented game modes.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union

from src.state_manager import load_game_state, GameState
from src.behavior_manager import BehaviorManager
from src.llm_protocol import LLMProtocolHandler
from src.vocabulary_service import build_merged_vocabulary
from src.parser import Parser


class GameEngine:
    """Game engine that manages state, behaviors, and vocabulary.

    Encapsulates all game initialization logic for both text-based and
    LLM-augmented game modes.
    """

    def __init__(self, game_dir: Union[str, Path]):
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

        # Add project root to sys.path so behavior_libraries can be imported
        # This is needed when running via installed package (llm-game command)
        project_root = Path(__file__).parent.parent
        project_root_str = str(project_root)
        if project_root_str not in sys.path:
            sys.path.append(project_root_str)

        # Add game directory to sys.path FIRST so game-specific behaviors take precedence
        # This is critical because both game dir and project root have behaviors/ packages
        game_dir_str = str(self.game_dir)
        if game_dir_str not in sys.path:
            sys.path.insert(0, game_dir_str)

        # Load all behaviors from game directory (includes core via symlink)
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

        # Load and merge vocabulary
        self.merged_vocabulary = build_merged_vocabulary(
            game_state=self.game_state,
            behavior_manager=self.behavior_manager
        )

        # Create JSON protocol handler
        self.json_handler = LLMProtocolHandler(self.game_state, behavior_manager=self.behavior_manager)

    def create_parser(self) -> Parser:
        """Create a Parser with merged vocabulary.

        Returns:
            Parser instance ready for command parsing
        """
        return Parser.from_vocab(self.merged_vocabulary)

    def create_narrator(self, api_key: str,
                       model: str = "claude-3-5-haiku-20241022",
                       show_traits: bool = False):
        """Create an LLMNarrator with game-specific configuration.

        Automatically loads narrator_style.txt from game directory and combines
        it with the protocol template from src/narrator_protocol.txt.

        Args:
            api_key: Anthropic API key
            model: Model to use for generation
            show_traits: If True, print llm_context traits before narration

        Returns:
            LLMNarrator instance ready for natural language interaction

        Raises:
            ImportError: If anthropic library not installed
            FileNotFoundError: If narrator_style.txt not found in game directory
        """
        from src.llm_narrator import LLMNarrator

        # Check for narrator style in game directory
        style_path = self.game_dir / "narrator_style.txt"
        if not style_path.exists():
            raise FileNotFoundError(
                f"narrator_style.txt not found in game directory: {self.game_dir}\n"
                "Each game must have its own narrator_style.txt file.\n"
                "This file contains game-specific narration style and examples.\n"
                "The protocol specification is automatically loaded from src/narrator_protocol.txt."
            )

        return LLMNarrator(
            api_key=api_key,
            json_handler=self.json_handler,
            model=model,
            prompt_file=style_path,
            behavior_manager=self.behavior_manager,
            vocabulary=self.merged_vocabulary,
            show_traits=show_traits
        )

    def create_mlx_narrator(self,
                            model: str = "mlx-community/Llama-3.2-3B-Instruct-4bit",
                            show_traits: bool = False,
                            temperature: float = 0.8,
                            max_tokens: int = 300):
        """Create an MLXNarrator with game-specific configuration.

        Uses Apple's MLX framework for native Metal GPU acceleration.
        Automatically loads narrator_style.txt from game directory.

        Args:
            model: MLX model path (HuggingFace format)
            show_traits: If True, print llm_context traits before narration
            temperature: Temperature for generation (0.0-2.0)
            max_tokens: Max tokens to generate

        Returns:
            MLXNarrator instance ready for natural language interaction

        Raises:
            ImportError: If mlx-lm library not installed
            FileNotFoundError: If narrator_style.txt not found in game directory
        """
        from src.mlx_narrator import MLXNarrator

        # Check for narrator style in game directory
        style_path = self.game_dir / "narrator_style.txt"
        if not style_path.exists():
            raise FileNotFoundError(
                f"narrator_style.txt not found in game directory: {self.game_dir}\n"
                "Each game must have its own narrator_style.txt file.\n"
                "This file contains game-specific narration style and examples.\n"
                "The protocol specification is automatically loaded from src/narrator_protocol.txt."
            )

        return MLXNarrator(
            json_handler=self.json_handler,
            model=model,
            prompt_file=style_path,
            behavior_manager=self.behavior_manager,
            vocabulary=self.merged_vocabulary,
            show_traits=show_traits,
            temperature=temperature,
            max_tokens=max_tokens
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
