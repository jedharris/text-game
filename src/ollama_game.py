#!/usr/bin/env python3
"""Ollama-powered text adventure game.

This script provides a natural language interface to the text adventure game,
using a local Ollama server to translate player input into game commands and narrate results.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path when run as script (not when imported as module)
if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.game_engine import GameEngine


def main(game_dir: str | None = None,
         debug: bool = False,
         show_traits: bool = False,
         model: str = "mistral:7b-instruct-q8_0",
         ollama_url: str = "http://localhost:11434") -> int:
    """Run the Ollama-powered text adventure.

    Args:
        game_dir: Path to game directory containing game_state.json (required)
        debug: If True, enable debug logging
        show_traits: If True, print llm_context traits before each LLM narration
        model: Ollama model to use
        ollama_url: Base URL for Ollama server

    Returns:
        Exit code (0 for success, non-zero for error)
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
        print("Usage: ollama_game <game_dir>")
        return 1

    # Initialize game engine
    try:
        engine = GameEngine(Path(game_dir))
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return 1

    # Create narrator using Ollama
    try:
        narrator = engine.create_ollama_narrator(
            model=model,
            ollama_url=ollama_url,
            show_traits=show_traits
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    # Check Ollama connection
    if not narrator.check_connection():
        print(f"Error: Cannot connect to Ollama at {ollama_url}")
        print("Make sure Ollama is running: ollama serve")
        print(f"And the model is available: ollama pull {model}")
        return 1

    # Show title and opening
    print(f"\n{engine.game_state.metadata.title}")
    print("=" * len(engine.game_state.metadata.title))
    print(f"[Using Ollama model: {model}]")
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


def cli_main() -> None:
    """Entry point for console script."""
    parser = argparse.ArgumentParser(description='Ollama-powered text adventure game')
    parser.add_argument('game_dir', help='Game name (from examples/) or full path to game directory')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--show-traits', '-t', action='store_true',
                        help='Print llm_context traits before each LLM narration')
    parser.add_argument('--model', '-m', default='mistral:7b-instruct-q8_0',
                        help='Ollama model to use (default: mistral:7b-instruct-q8_0)')
    parser.add_argument('--ollama-url', '-u', default='http://localhost:11434',
                        help='Ollama server URL (default: http://localhost:11434)')
    args = parser.parse_args()

    # If it's just a name (no path separators), prefix with examples/
    if '/' not in args.game_dir and not Path(args.game_dir).is_absolute():
        game_path = Path('examples') / args.game_dir
    else:
        game_path = Path(args.game_dir)

    sys.exit(main(
        game_dir=str(game_path),
        debug=args.debug,
        show_traits=args.show_traits,
        model=args.model,
        ollama_url=args.ollama_url
    ))


if __name__ == "__main__":
    cli_main()
