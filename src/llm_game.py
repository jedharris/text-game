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

# Default game state file location
DEFAULT_STATE_FILE = Path(__file__).parent.parent / "examples" / "simple_game_state.json"


def main(state_file: str = None, debug: bool = False):
    """Run the LLM-powered text adventure.

    Args:
        state_file: Path to game state JSON file (uses default if not provided)
        debug: If True, enable debug logging (shows cache statistics)
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

    # Load game state
    if state_file:
        game_state_path = Path(state_file)
        # Try adding .json if file doesn't exist
        if not game_state_path.exists() and not state_file.endswith('.json'):
            game_state_path = Path(state_file + '.json')
    else:
        game_state_path = DEFAULT_STATE_FILE
    if not game_state_path.exists():
        print(f"Error: Game state file not found: {game_state_path}")
        return 1

    state = load_game_state(str(game_state_path))

    # Create behavior manager and load modules
    behavior_manager = BehaviorManager()
    behaviors_dir = project_root / "behaviors"
    modules = behavior_manager.discover_modules(str(behaviors_dir))
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
                           vocabulary=merged_vocab)

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
    parser.add_argument('state_file', nargs='?', help='Path to game state JSON file')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug logging (shows API cache statistics)')
    args = parser.parse_args()
    sys.exit(main(state_file=args.state_file, debug=args.debug))


if __name__ == "__main__":
    cli_main()
