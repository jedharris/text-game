#!/usr/bin/env python3
"""LLM-powered text adventure game.

This script provides a natural language interface to the text adventure game,
using an LLM to translate player input into game commands and narrate results.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.state_manager import load_game_state
from src.llm_protocol import JSONProtocolHandler
from src.llm_narrator import LLMNarrator
from src.behavior_manager import BehaviorManager
from src.vocabulary_generator import extract_nouns_from_state, merge_vocabulary

# Default game directory location
DEFAULT_GAME_DIR = Path(__file__).parent.parent / "examples" / "simple_game"


def main(game_dir: str = None, debug: bool = False, show_traits: bool = False):
    """Run the LLM-powered text adventure.

    Args:
        game_dir: Path to game directory containing game_state.json (uses default if not provided)
        debug: If True, enable debug logging (shows cache statistics)
        show_traits: If True, print llm_context traits before each LLM narration
    """
    # Configure logging
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='[DEBUG] %(name)s: %(message)s'
        )
    else:
        logging.basicConfig(level=logging.WARNING)
    # Load API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY=sk-ant-...")
        return 1

    # Resolve game directory
    if game_dir:
        game_dir_path = Path(game_dir).absolute()
    else:
        game_dir_path = DEFAULT_GAME_DIR

    if not game_dir_path.exists() or not game_dir_path.is_dir():
        print(f"Error: Game directory not found: {game_dir_path}")
        return 1

    # Load game state from game_state.json in the directory
    game_state_path = game_dir_path / "game_state.json"
    if not game_state_path.exists():
        print(f"Error: game_state.json not found in: {game_dir_path}")
        return 1

    state = load_game_state(str(game_state_path))

    # Create behavior manager and load modules
    # Game must have its own behaviors/ directory (with at least a symlink to core behaviors).
    behavior_manager = BehaviorManager()
    game_behaviors_dir = game_dir_path / "behaviors"
    if not game_behaviors_dir.exists() or not game_behaviors_dir.is_dir():
        print(f"Error: Game must have a behaviors/ directory: {game_behaviors_dir}")
        print("Create one with at least a symlink to the engine's core behaviors.")
        return 1

    # Add game directory to sys.path so game-specific modules can be imported
    if str(game_dir_path) not in sys.path:
        sys.path.insert(0, str(game_dir_path))

    # Load all behaviors from game directory (includes core via symlink)
    modules = behavior_manager.discover_modules(str(game_behaviors_dir))
    behavior_manager.load_modules(modules)

    # Load and merge vocabulary (same pattern as text_game.py)
    vocab_path = Path(__file__).parent / 'vocabulary.json'
    with open(vocab_path, 'r') as f:
        base_vocab = json.load(f)

    extracted_nouns = extract_nouns_from_state(state)
    vocab_with_nouns = merge_vocabulary(base_vocab, extracted_nouns)
    merged_vocab = behavior_manager.get_merged_vocabulary(vocab_with_nouns)

    # Create JSON handler with behavior manager
    json_handler = JSONProtocolHandler(state, behavior_manager=behavior_manager)

    # Create narrator with merged vocabulary for local parsing
    narrator = LLMNarrator(api_key, json_handler, behavior_manager=behavior_manager,
                           vocabulary=merged_vocab, show_traits=show_traits)

    # Show title and opening
    print(f"\n{state.metadata.title}")
    print("=" * len(state.metadata.title))
    print()

    try:
        opening = narrator.get_opening()
        print(opening)
    except Exception as e:
        print(f"[Error getting opening: {e}]")
        return 1

    # Game loop
    print("\n(Type 'quit' to exit)")

    while True:
        try:
            player_input = input("\n> ").strip()

            if not player_input:
                continue

            if player_input.lower() in ("quit", "exit", "q"):
                print("\nThanks for playing!")
                break

            response = narrator.process_turn(player_input)
            print(f"\n{response}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n[Error: {e}]")

    return 0


def cli_main():
    """Entry point for console script."""
    parser = argparse.ArgumentParser(description='LLM-powered text adventure game')
    parser.add_argument('game_dir', nargs='?', help='Path to game directory containing game_state.json')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug logging (shows API cache statistics)')
    parser.add_argument('--show-traits', '-t', action='store_true',
                        help='Print llm_context traits before each LLM narration')
    args = parser.parse_args()
    sys.exit(main(game_dir=args.game_dir, debug=args.debug, show_traits=args.show_traits))


if __name__ == "__main__":
    cli_main()
