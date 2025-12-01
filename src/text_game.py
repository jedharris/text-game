"""Text adventure game engine with state management.

This is a thin wrapper around the JSON protocol handler, converting text
input to JSON commands and formatting JSON responses as text output.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path so we can import from src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.parser import ParsedCommand
from src.state_manager import load_game_state, save_game_state, GameState
from src.file_dialogs import get_save_filename, get_load_filename
from src.game_engine import GameEngine


def parsed_to_json(result: ParsedCommand) -> Dict[str, Any]:
    """Convert ParsedCommand to JSON protocol format.

    Passes WordEntry objects for object/indirect_object to preserve
    vocabulary synonyms for entity matching. Verbs, directions, and
    adjectives use .word since they don't need synonym matching.
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


def format_location_query(response: Dict[str, Any]) -> str:
    """Format a location query response as text."""
    data = response.get("data", {})
    location = data.get("location", {})
    lines = []

    # Location name and description
    lines.append(location.get("name", "Unknown Location"))
    lines.append(location.get("description", ""))

    # Items - separate direct items from items on surfaces
    items = data.get("items", [])
    direct_items = []
    surface_items = {}  # container_name -> [item_names]

    for item in items:
        on_surface = item.get("on_surface")
        if on_surface:
            if on_surface not in surface_items:
                surface_items[on_surface] = []
            surface_items[on_surface].append(item.get("name", "item"))
        else:
            direct_items.append(item.get("name", "item"))

    if direct_items:
        lines.append(f"You see: {', '.join(direct_items)}")

    for container_name, item_names in surface_items.items():
        lines.append(f"On the {container_name}: {', '.join(item_names)}")

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


def format_item_query(response: Dict[str, Any]) -> str:
    """Format an entity query response for an item as text."""
    data = response.get("data", {})
    lines = []

    # Item description
    lines.append(data.get("description", "You see nothing special."))

    # Container contents
    contents = data.get("contents", [])
    if contents:
        container_props = data.get("container", {})
        is_surface = container_props.get("is_surface", False)
        preposition = "On" if is_surface else "Inside"
        item_names = [item.get("name", "item") for item in contents]
        lines.append(f"{preposition} the {data.get('name', 'container')}: {', '.join(item_names)}")
    elif data.get("container", {}).get("is_surface"):
        lines.append(f"The {data.get('name', 'surface')} is empty.")
    elif data.get("container") and not data.get("container", {}).get("open", True):
        lines.append(f"The {data.get('name', 'container')} is closed.")

    # Light source state
    if data.get("provides_light"):
        if data.get("lit"):
            lines.append("It is currently lit, casting a warm glow.")
        else:
            lines.append("It is currently unlit.")

    return "\n".join(lines)


def format_inventory_query(response: Dict[str, Any]) -> str:
    """Format an inventory query response as text."""
    data = response.get("data", {})
    items = data.get("items", [])

    if items:
        item_names = [item.get("name", "item") for item in items]
        return f"You are carrying: {', '.join(item_names)}"
    else:
        return "You are not carrying anything."


def format_command_result(response: Dict[str, Any]) -> str:
    """Format a command result as text."""
    if response.get("success"):
        return response.get("message", "Done.")
    else:
        error = response.get("error", {})
        return error.get("message", "That didn't work.")


def save_game(state: GameState, filename: str):
    """Save the game state to a file."""
    try:
        save_game_state(state, filename)
        print(f"Game saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving game: {e}")
        return False


def load_game(filename: str) -> Optional[GameState]:
    """Load a game state from a file."""
    try:
        state = load_game_state(filename)
        print(f"Game loaded from {filename}")
        return state
    except Exception as e:
        print(f"Error loading game: {e}")
        return None


def main(game_dir: str = None):
    """Run the game.

    Args:
        game_dir: Path to game directory containing game_state.json (required)
    """
    if not game_dir:
        print("Error: game_dir is required")
        print("Usage: text_game <game_dir>")
        return 1

    # Initialize game engine
    try:
        engine = GameEngine(Path(game_dir))
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return 1

    # Use the game directory for save/load dialogs
    save_load_dir = str(engine.game_dir)

    # Create parser
    parser = engine.create_parser()

    print(f"Welcome to {engine.game_state.metadata.title}!")
    print("Type 'quit' to exit, 'help' for commands.")
    print()

    # Show initial location via query
    response = engine.json_handler.handle_message({
        "type": "query",
        "query_type": "location",
        "include": ["items", "doors"]
    })
    print(format_location_query(response))
    print()

    while True:
        command_text = input("> ").strip()
        if not command_text:
            continue

        # Handle raw JSON input
        if command_text.startswith("{"):
            try:
                message = json.loads(command_text)
                result_json = engine.json_handler.handle_message(message)
                print(json.dumps(result_json, indent=2))
            except json.JSONDecodeError as e:
                print(f"Invalid JSON: {e}")
            continue

        # Parse text command
        result = parser.parse_command(command_text)

        if result is None:
            print("I don't understand that command.")
            continue

        # Handle special commands that need local processing
        if result.verb:
            verb = result.verb.word

            # Quit
            if verb == "quit":
                print("Thanks for playing!")
                break

            # Save (needs file dialog support)
            if verb == "save":
                if result.direct_object:
                    save_game(engine.game_state, result.direct_object.word)
                elif result.object_missing:
                    parts = result.raw.split(maxsplit=1)
                    if len(parts) > 1:
                        save_game(engine.game_state, parts[1].strip())
                    else:
                        filename = get_save_filename(default_dir=save_load_dir, default_filename="savegame.json")
                        if filename:
                            save_game(engine.game_state, filename)
                        else:
                            print("Save canceled.")
                continue

            # Load (needs file dialog support and state replacement)
            if verb == "load":
                filename = None
                if result.direct_object:
                    filename = result.direct_object.word
                elif result.object_missing:
                    parts = result.raw.split(maxsplit=1)
                    if len(parts) > 1:
                        filename = parts[1].strip()
                    else:
                        filename = get_load_filename(default_dir=save_load_dir)

                if filename:
                    loaded_state = load_game(filename)
                    if loaded_state:
                        # Reload state in engine
                        engine.reload_state(loaded_state)
                        response = engine.json_handler.handle_message({
                            "type": "query",
                            "query_type": "location",
                            "include": ["items", "doors"]
                        })
                        print(format_location_query(response))
                else:
                    print("Load canceled.")
                continue

            # Look/examine without object -> location query
            if verb in ("look", "examine") and not result.direct_object:
                response = engine.json_handler.handle_message({
                    "type": "query",
                    "query_type": "location",
                    "include": ["items", "doors"]
                })
                print(format_location_query(response))
                continue

            # Examine/look with object -> use command (handlers find by name)
            if verb in ("examine", "look") and result.direct_object:
                json_cmd = parsed_to_json(result)
                response = engine.json_handler.handle_message(json_cmd)
                print(format_command_result(response))
                continue

            # Inventory -> inventory query
            if verb == "inventory":
                response = engine.json_handler.handle_message({
                    "type": "query",
                    "query_type": "inventory"
                })
                print(format_inventory_query(response))
                continue

        # Handle direction-only input (bare "north", etc.)
        if result.direction and not result.verb:
            json_cmd = {"type": "command", "action": {"verb": "go", "direction": result.direction.word}}
        else:
            # Convert parsed command to JSON
            json_cmd = parsed_to_json(result)

        # Execute via JSON protocol
        response = engine.json_handler.handle_message(json_cmd)
        print(format_command_result(response))

        # Check for win condition
        if (response.get("success") and
            response.get("action") == "open" and
            "chest" in response.get("message", "").lower() and
            "treasure" in response.get("message", "").lower()):
            break


def cli_main():
    """Entry point for console script."""
    parser = argparse.ArgumentParser(description='Text adventure game')
    parser.add_argument('game_dir', nargs='?', help='Path to game directory containing game_state.json')
    args = parser.parse_args()
    sys.exit(main(game_dir=args.game_dir) or 0)


if __name__ == '__main__':
    cli_main()
