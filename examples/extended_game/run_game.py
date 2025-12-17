from src.types import ActorId
#!/usr/bin/env python3
"""
Extended Game Runner - Demonstrates extending the text game engine.

This script shows how a game developer would use the text-game engine
to build their own game with custom behaviors and vocabulary.

Usage:
    python examples/extended_game/run_game.py

From the project root directory.
"""

import sys
from pathlib import Path

# Add project root to path for imports
# This is the key step - game developers need to add the engine to their path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Also add the extended_game directory so our custom behaviors can be found
extended_game_dir = Path(__file__).parent
sys.path.insert(0, str(extended_game_dir))

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


def format_inventory_query(response: dict) -> str:
    """Format an inventory query response as text."""
    data = response.get("data", {})
    items = data.get("items", [])

    if items:
        item_names = [item.get("name", "item") for item in items]
        return f"You are carrying: {', '.join(item_names)}"
    else:
        return "You are not carrying anything."


def format_command_result(response: dict) -> str:
    """Format a command result as text."""
    if response.get("success"):
        return response.get("message", "Done.")
    else:
        error = response.get("error", {})
        return error.get("message", "That didn't work.")


def main():
    """Run the extended game."""
    print("=" * 60)
    print("Extended Game Example - Testing Engine Extensibility")
    print("=" * 60)
    print()

    # Step 1: Load game state
    print("Loading game state...")
    state = load_game_state(str(GAME_STATE_FILE))

    # Step 2: Initialize behavior manager
    print("Initializing behavior manager...")
    behavior_manager = BehaviorManager()

    # Step 3: Load behaviors from our game's behaviors directory
    # This includes core behaviors via symlink (behaviors/core -> engine's behaviors/core)
    # The symlink approach lets game developers use core behaviors without path issues
    if CUSTOM_BEHAVIORS_DIR.exists():
        print(f"Loading behaviors from {CUSTOM_BEHAVIORS_DIR}...")
        modules = behavior_manager.discover_modules(str(CUSTOM_BEHAVIORS_DIR))
        print(f"  Found {len(modules)} behavior modules")
        for module_path, source_type in modules:
            print(f"    - {module_path} ({source_type})")
        behavior_manager.load_modules(modules)
    else:
        print("WARNING: Behaviors directory not found!")

    # Step 4: Validate behavior references in game state
    # This catches typos/mismatches in behavior module paths early
    print("Validating behavior references...")
    validate_game_state(state, behavior_manager.get_loaded_modules())

    # Step 5: Load and merge vocabulary
    print("Building vocabulary...")
    merged_vocab = build_merged_vocabulary(state, behavior_manager)

    # Initialize parser directly from in-memory vocabulary
    parser = Parser.from_vocab(merged_vocab)

    # Show what verbs are available
    verb_words = [v["word"] for v in merged_vocab.get("verbs", [])]
    print(f"  Available verbs: {', '.join(sorted(verb_words))}")

    # Step 6: Initialize JSON protocol handler
    print("Initializing protocol handler...")
    json_handler = LLMProtocolHandler(state, behavior_manager=behavior_manager)

    print()
    print("=" * 60)
    print(f"Welcome to {state.metadata.title}!")
    print("=" * 60)
    print()
    print("Type 'quit' to exit, 'help' for commands.")
    print("Try: read, peer, wave, examine")
    print()

    # Show initial location via look command
    response = json_handler.handle_message({
        "type": "command",
        "action": {"verb": "look"}
    })
    print(format_command_result(response))
    print()

    # Main game loop
    while True:
        try:
            command_text = input("> ").strip()
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nThanks for playing!")
            break

        if not command_text:
            continue

        # Parse text command
        result = parser.parse_command(command_text)

        if result is None:
            print("I don't understand that command.")
            continue

        # Handle special commands
        if result.verb:
            verb = result.verb.word

            # Help
            if verb == "help":
                print("Available commands:")
                print("  Movement: north, south, east, west, up, down")
                print("  Actions: take, drop, open, close, unlock, examine, look")
                print("  Custom: read, peer/gaze, wave")
                print("  Other: inventory, quit, help")
                continue

            # Look without object -> use command handler
            if verb in ("look", "examine") and not result.direct_object:
                response = json_handler.handle_message({
                    "type": "command",
                    "action": {"verb": "look"}
                })
                print(format_command_result(response))
                continue

            # Inventory
            if verb == "inventory":
                response = json_handler.handle_message({
                    "type": "query",
                    "query_type": "inventory"
                })
                print(format_inventory_query(response))
                continue

        # Handle direction-only input
        # Directions are now in direct_object as nouns
        if result.direct_object and not result.verb:
            json_cmd = {"type": "command", "action": {"verb": "go", "object": result.direct_object}}
        else:
            json_cmd = parsed_to_json(result)

        # Execute via JSON protocol
        response = json_handler.handle_message(json_cmd)

        # Check for meta command signals (quit, save, load)
        if response.get("success") and response.get("data", {}).get("signal"):
            signal = response["data"]["signal"]

            if signal == "quit":
                print(response.get("message", "Thanks for playing!"))
                break

            # Note: extended_game doesn't have save/load functionality
            # If needed in future, add signal handling here

        # Normal command result
        print(format_command_result(response))

        # Check for win condition (getting to sanctum with the wand)
        if response.get("success"):
            actor = state.actors.get(ActorId("player"))
            if actor and actor.location == "loc_sanctum":
                # Check if player has the wand
                wand = None
                for item in state.items:
                    if item.id == "item_magic_wand" and item.location == "player":
                        wand = item
                        break
                if wand:
                    print()
                    print("=" * 60)
                    print("CONGRATULATIONS!")
                    print("You've claimed the wizard's wand and reached the sanctum!")
                    print("The tower's magic is now yours to command.")
                    print("=" * 60)
                    break


if __name__ == '__main__':
    main()
