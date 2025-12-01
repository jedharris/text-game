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
from src.parser import Parser, ParsedCommand
from src.state_manager import load_game_state, save_game_state, GameState
from src.llm_protocol import LLMProtocolHandler
from src.vocabulary_generator import extract_nouns_from_state, merge_vocabulary
from src.behavior_manager import BehaviorManager
from src.validators import validate_game_state

# Game-specific paths
GAME_STATE_FILE = Path(__file__).parent / "game_state.json"
CUSTOM_BEHAVIORS_DIR = Path(__file__).parent / "behaviors"


def parsed_to_json(result: ParsedCommand) -> dict:
    """Convert ParsedCommand to JSON protocol format.

    Passes WordEntry objects for object/indirect_object to preserve
    vocabulary synonyms for entity matching.
    """
    action = {"verb": result.verb.word}
    if result.direct_object:
        action["object"] = result.direct_object
    if result.indirect_object:
        action["target"] = result.indirect_object
    if result.preposition:
        action["preposition"] = result.preposition
    if result.direct_adjective:
        action["adjective"] = result.direct_adjective.word
    return action


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

    # Extract nouns from game state and merge
    extracted_nouns = extract_nouns_from_state(game_state)
    vocab_with_nouns = merge_vocabulary(base_vocab, extracted_nouns)

    # Merge with behavior vocabulary extensions
    merged_vocab = behavior_manager.get_merged_vocabulary(vocab_with_nouns)

    # Write merged vocabulary to temp file for parser
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(merged_vocab, f)
        merged_vocab_path = f.name

    # Initialize parser and protocol handler
    parser = Parser(merged_vocab_path)
    Path(merged_vocab_path).unlink()  # Clean up temp file
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

            # Convert to JSON protocol
            action = parsed_to_json(parse_result)
            action["actor_id"] = "player"

            # Execute via behavior manager
            result = behavior_manager.handle_action(game_state.accessor, action)

            if result.message:
                print(result.message)
            elif not result.success:
                print("You can't do that.")

        except KeyboardInterrupt:
            print("\nThanks for playing!")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
