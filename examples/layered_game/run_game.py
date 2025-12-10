#!/usr/bin/env python3
"""
Run the Layered Game - Three-Tier Behavior Demonstration.

This game demonstrates a three-tier behavior hierarchy:
- Tier 1: Game-specific behaviors (local to this game)
- Tier 2: Shared library behaviors (puzzle_lib and offering_lib)
- Tier 3: Core behaviors (foundational game mechanics)

Usage:
    python examples/layered_game/run_game.py

From the project root directory.
"""

import json
import sys
import tempfile
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Also add the layered_game directory so our custom behaviors can be found
layered_game_dir = Path(__file__).parent
sys.path.insert(0, str(layered_game_dir))

# Now we can import from the engine
from src.command_utils import parsed_to_json
from src.parser import Parser
from src.state_manager import load_game_state, save_game_state, GameState
from src.llm_protocol import LLMProtocolHandler
from src.vocabulary_service import build_merged_vocabulary
from src.behavior_manager import BehaviorManager
from src.validators import validate_game_state

# Game-specific paths
GAME_STATE_FILE = Path(__file__).parent / "game_state.json"
CUSTOM_BEHAVIORS_DIR = Path(__file__).parent / "behaviors"


def main():
    """Run the layered game."""
    print("=" * 60)
    print("THE CAVERN OF TRIALS")
    print("A Three-Tier Behavior Demonstration")
    print("=" * 60)
    print()
    print("This game demonstrates:")
    print("  - Tier 1: Game-specific puzzle behaviors")
    print("  - Tier 2: Shared library behaviors (puzzle_lib, offering_lib)")
    print("  - Tier 3: Core foundational behaviors")
    print()
    print("=" * 60)
    print()

    # Load game state
    game_state = load_game_state(GAME_STATE_FILE)

    # Validate
    validate_game_state(game_state)

    # Initialize behavior manager
    behavior_manager = BehaviorManager()

    # Load behaviors from the game's behaviors directory (three-tier)
    if CUSTOM_BEHAVIORS_DIR.exists():
        modules = behavior_manager.discover_modules(str(CUSTOM_BEHAVIORS_DIR))
        behavior_manager.load_modules(modules)

    # Load base vocabulary
    vocab_path = Path(__file__).parent.parent.parent / "src" / "vocabulary.json"
    with open(vocab_path) as f:
        base_vocab = json.load(f)

    # Build merged vocabulary (base + nouns + behaviors)
    merged_vocab = build_merged_vocabulary(game_state, behavior_manager, base_vocab=base_vocab)

    # Initialize parser and protocol handler directly from in-memory vocabulary
    parser = Parser(merged_vocab)
    protocol_handler = LLMProtocolHandler(game_state, behavior_manager=behavior_manager)

    # Main game loop
    print("Welcome to the Cavern of Trials!")
    print("Type 'help' for commands, 'quit' to exit.\n")

    while True:
        try:
            # Get player input
            command = input("> ").strip()

            if not command:
                continue

            if command.lower() in ["quit", "exit", "q"]:
                print("Thanks for playing!")
                break

            if command.lower() == "help":
                print("Available commands:")
                print("  - Movement: go [direction], north, south, east, west, up, down")
                print("  - Interaction: examine/look [object], take [object], drop [object]")
                print("  - Puzzles: water [mushroom], play [stalactite], check [pedestal]")
                print("  - Offerings: offer [item] to [altar/well/shrine], toss [item] into [well]")
                print("  - Inventory: inventory/i")
                print("  - Save/Load: save, load")
                print("  - quit - Exit the game")
                continue

            if command.lower() == "save":
                save_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
                save_game_state(game_state, save_file.name)
                print(f"Game saved to {save_file.name}")
                continue

            # Parse the command
            parse_result = parser.parse_command(command)

            if not parse_result.verb:
                print("I don't understand that command.")
                continue

            # Convert to JSON protocol and execute via JSON handler
            message = parsed_to_json(parse_result)
            response = protocol_handler.handle_message(message)

            if response.get("type") == "error":
                print(f"Error: {response.get('message', 'Unknown error')}")
                continue

            if response.get("success"):
                msg = response.get("message") or "Done."
                print(msg)
            else:
                error_msg = response.get("error", {}).get("message", "You can't do that.")
                print(error_msg)

        except KeyboardInterrupt:
            print("\nThanks for playing!")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
