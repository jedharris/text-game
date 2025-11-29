#!/usr/bin/env python3
"""
Extended Game Runner - Demonstrates extending the text game engine.

This script shows how a game developer would use the text-game engine
to build their own game with custom behaviors and vocabulary.

Usage:
    python examples/extended_game/run_game.py

From the project root directory.
"""

import json
import sys
import tempfile
from pathlib import Path

# Add project root to path for imports
# This is the key step - game developers need to add the engine to their path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Also add the extended_game directory so our custom behaviors can be found
extended_game_dir = Path(__file__).parent
sys.path.insert(0, str(extended_game_dir))

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
        # Pass full WordEntry to preserve synonyms for entity matching
        action["object"] = result.direct_object
    if result.direct_adjective:
        action["adjective"] = result.direct_adjective.word
    if result.direction:
        action["direction"] = result.direction.word
    if result.indirect_object:
        # Pass full WordEntry to preserve synonyms for entity matching
        action["indirect_object"] = result.indirect_object
    if result.indirect_adjective:
        action["indirect_adjective"] = result.indirect_adjective.word

    return {"type": "command", "action": action}


def format_location_query(response: dict) -> str:
    """Format a location query response as text."""
    data = response.get("data", {})
    location = data.get("location", {})
    lines = []

    lines.append(location.get("name", "Unknown Location"))
    lines.append(location.get("description", ""))

    # Items - separate direct items from items on surfaces/in containers
    items = data.get("items", [])
    direct_items = []
    surface_items = {}
    contained_items = {}

    for item in items:
        on_surface = item.get("on_surface")
        in_container = item.get("in_container")
        if on_surface:
            if on_surface not in surface_items:
                surface_items[on_surface] = []
            surface_items[on_surface].append(item.get("name", "item"))
        elif in_container:
            if in_container not in contained_items:
                contained_items[in_container] = []
            contained_items[in_container].append(item.get("name", "item"))
        else:
            direct_items.append(item.get("name", "item"))

    if direct_items:
        lines.append(f"You see: {', '.join(direct_items)}")

    for container_name, item_names in surface_items.items():
        lines.append(f"On the {container_name}: {', '.join(item_names)}")

    for container_name, item_names in contained_items.items():
        lines.append(f"In the {container_name}: {', '.join(item_names)}")

    # Doors with state
    doors = data.get("doors", [])
    if doors:
        door_descriptions = []
        for door in doors:
            direction = door.get("direction", "")
            state_parts = []
            if door.get("locked"):
                state_parts.append("locked")
            if door.get("open"):
                state_parts.append("open")
            else:
                state_parts.append("closed")
            state_str = ", ".join(state_parts)
            door_descriptions.append(f"door ({state_str}) to the {direction}")
        lines.append(f"Exits: {', '.join(door_descriptions)}")

    return "\n".join(lines)


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
    vocab_path = project_root / 'src' / 'vocabulary.json'
    with open(vocab_path, 'r') as f:
        base_vocab = json.load(f)

    # Extract nouns from our game state
    extracted_nouns = extract_nouns_from_state(state)
    vocab_with_nouns = merge_vocabulary(base_vocab, extracted_nouns)

    # Merge with behavior vocabulary extensions
    merged_vocab = behavior_manager.get_merged_vocabulary(vocab_with_nouns)

    # Write merged vocabulary to temp file for parser
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(merged_vocab, f)
        merged_vocab_path = f.name

    parser = Parser(merged_vocab_path)
    Path(merged_vocab_path).unlink()

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

    # Show initial location
    response = json_handler.handle_message({
        "type": "query",
        "query_type": "location",
        "include": ["items", "doors"]
    })
    print(format_location_query(response))
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

            # Quit
            if verb == "quit":
                print("Thanks for playing!")
                break

            # Help
            if verb == "help":
                print("Available commands:")
                print("  Movement: north, south, east, west, up, down")
                print("  Actions: take, drop, open, close, unlock, examine, look")
                print("  Custom: read, peer/gaze, wave")
                print("  Other: inventory, quit, help")
                continue

            # Look without object -> location query
            if verb in ("look", "examine") and not result.direct_object:
                response = json_handler.handle_message({
                    "type": "query",
                    "query_type": "location",
                    "include": ["items", "doors"]
                })
                print(format_location_query(response))
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
        if result.direction and not result.verb:
            json_cmd = {"type": "command", "action": {"verb": "go", "direction": result.direction.word}}
        else:
            json_cmd = parsed_to_json(result)

        # Execute via JSON protocol
        response = json_handler.handle_message(json_cmd)
        print(format_command_result(response))

        # Check for win condition (getting to sanctum with the wand)
        if response.get("success"):
            actor = state.actors.get("player")
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
