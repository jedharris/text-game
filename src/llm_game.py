#!/usr/bin/env python3
"""LLM-powered text adventure game.

This script provides a natural language interface to the text adventure game,
using an LLM to translate player input into game commands and narrate results.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path when run as script (not when imported as module)
if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.game_engine import GameEngine


def main(game_dir: Optional[str] = None, debug: bool = False, show_traits: bool = False):
    """Run the LLM-powered text adventure.

    Args:
        game_dir: Path to game directory containing game_state.json (required)
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

    if not game_dir:
        print("Error: game_dir is required")
        print("Usage: llm_game <game_dir>")
        return 1

    # Load API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY=sk-ant-...")
        return 1

    # Initialize game engine
    # Missing/invalid game files indicate authoring errors and should fail loudly
    engine = GameEngine(Path(game_dir))

    # Create narrator with game-specific prompt
    # Missing narrator protocol or files indicate authoring errors and should fail loudly
    narrator = engine.create_narrator(api_key, show_traits=show_traits)

    # Show title and opening
    print(f"\n{engine.game_state.metadata.title}")
    print("=" * len(engine.game_state.metadata.title))
    print()

    # Errors in opening narration indicate authoring/coding bugs and should fail loudly
    opening = narrator.get_opening()
    print(opening)

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

            # Errors processing turns indicate bugs in behaviors/handlers and should fail loudly
            response = narrator.process_turn(player_input)
            print(f"\n{response}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break

    return 0


def cli_main():
    """Entry point for console script."""
    parser = argparse.ArgumentParser(description='LLM-powered text adventure game')
    parser.add_argument('game_dir', help='Game name (from examples/) or full path to game directory')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug logging (shows API cache statistics)')
    parser.add_argument('--show-traits', '-t', action='store_true',
                        help='Print llm_context traits before each LLM narration')
    args = parser.parse_args()

    # If it's just a name (no path separators), prefix with examples/
    if '/' not in args.game_dir and not Path(args.game_dir).is_absolute():
        game_path = Path('examples') / args.game_dir
    else:
        game_path = Path(args.game_dir)

    sys.exit(main(game_dir=str(game_path), debug=args.debug, show_traits=args.show_traits))


if __name__ == "__main__":
    cli_main()
