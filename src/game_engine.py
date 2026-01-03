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
from src.types import ActorId


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
        # JSONDecodeError or ValueError here indicates invalid game_state.json (authoring error)
        self.game_state = load_game_state(str(game_state_path))

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

        # Validate all loaded modules and game state
        # Catches authoring errors early (hook typos, invalid behaviors, etc.)
        self.behavior_manager.finalize_loading(self.game_state)

        # Initialize turn executor with hook definitions
        from src import turn_executor
        turn_executor.initialize(self.behavior_manager._hook_definitions)

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

    def create_llm_parser(self, shared_backend):
        """Create an LLM parser with adapter.

        Args:
            shared_backend: SharedMLXBackend instance (shared with narrator)

        Returns:
            Tuple of (LLMCommandParser, LLMParserAdapter) ready for command parsing
        """
        from src.llm_command_parser import LLMCommandParser
        from src.llm_parser_adapter import LLMParserAdapter

        # Extract verbs for parser (including multi-type words from other sections)
        verbs = []

        # Get verbs from verbs section
        for v in self.merged_vocabulary.get('verbs', []):
            verbs.append(v['word'])

        # Get multi-type words with verb type from nouns and adjectives sections
        for section in ['nouns', 'adjectives']:
            for entry in self.merged_vocabulary.get(section, []):
                word_type = entry.get('word_type')
                # Check if this entry has verb type
                if isinstance(word_type, list) and 'verb' in word_type:
                    if entry['word'] not in verbs:
                        verbs.append(entry['word'])

        # Create parser and adapter
        parser = LLMCommandParser(shared_backend, verbs)
        adapter = LLMParserAdapter(self.merged_vocabulary)

        return parser, adapter

    def build_parser_context(self, actor_id: ActorId = ActorId("player")):
        """Build context dict for LLM parser from current game state.

        Args:
            actor_id: ID of actor whose context to build (default: "player")

        Returns:
            Dict with keys: location_objects, inventory, exits
        """
        from typing import List, Dict
        from src.state_accessor import StateAccessor

        actor = self.game_state.actors.get(actor_id)
        if not actor:
            return {"location_objects": [], "inventory": [], "exits": []}

        location_id = actor.location
        if not location_id:
            return {"location_objects": [], "inventory": [], "exits": []}

        location = next((loc for loc in self.game_state.locations if loc.id == location_id), None)
        if not location:
            return {"location_objects": [], "inventory": [], "exits": []}

        # Create temporary accessor for queries
        accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Get location objects using index (fixes Myconid Sanctuary bug)
        location_objects: List[str] = []

        # Get items at location
        items_here = accessor.get_entities_at(location_id, entity_type="item")
        for item in items_here:
            item_name = getattr(item, 'name', item.id)
            location_objects.append(item_name)

        # Get actors at location (excluding self)
        actors_here = accessor.get_entities_at(location_id, entity_type="actor")
        for other_actor in actors_here:
            if other_actor.id != actor_id:
                actor_name = getattr(other_actor, 'name', other_actor.id)
                location_objects.append(actor_name)

        # Get actor inventory (query index, not actor.inventory list)
        inventory: List[str] = []
        inventory_items = accessor.get_entities_at(actor_id, entity_type="item")
        for item in inventory_items:
            item_name = getattr(item, 'name', item.id)
            inventory.append(item_name)

        # Get exits using index
        exits: List[str] = []
        exits_here = accessor.get_exits_from_location(location_id)
        for exit_entity in exits_here:
            if exit_entity.direction:
                exits.append(exit_entity.direction)

        # Get dialogue topics (unchanged)
        topics: List[str] = []
        for other_actor in actors_here:
            if other_actor.id != actor_id:
                dialogue_topics = getattr(other_actor, 'dialogue_topics', None)
                if dialogue_topics:
                    topics.extend(dialogue_topics)

        return {
            "location_objects": location_objects,
            "inventory": inventory,
            "exits": exits,
            "topics": topics
        }

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
                            max_tokens: int = 300,
                            shared_backend=None):
        """Create an MLXNarrator with game-specific configuration.

        Uses Apple's MLX framework for native Metal GPU acceleration.
        Automatically loads narrator_style.txt from game directory.

        Args:
            model: MLX model path (HuggingFace format) - only used if shared_backend is None
            show_traits: If True, print llm_context traits before narration
            temperature: Temperature for generation (0.0-2.0)
            max_tokens: Max tokens to generate
            shared_backend: Optional SharedMLXBackend instance (saves ~4-6GB memory)

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
            max_tokens=max_tokens,
            shared_backend=shared_backend
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
