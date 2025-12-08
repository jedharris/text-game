"""Text adventure game engine with state management.

This is a thin wrapper around the JSON protocol handler, converting text
input to JSON commands and formatting JSON responses as text output.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path when run as script (not when imported as module)
if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.parser import ParsedCommand
from src.state_manager import load_game_state, save_game_state, GameState
from src.file_dialogs import get_save_filename, get_load_filename
from src.game_engine import GameEngine


def parsed_to_json(result: ParsedCommand) -> Dict[str, Any]:
    """Convert ParsedCommand to JSON protocol format.

    Passes WordEntry objects for object/indirect_object to preserve
    vocabulary synonyms for entity matching. Verbs and adjectives use
    .word since they don't need synonym matching.
    """
    action = {"verb": result.verb.word}

    if result.direct_object:
        # Pass full WordEntry to preserve synonyms for entity matching
        action["object"] = result.direct_object
    if result.direct_adjective:
        action["adjective"] = result.direct_adjective.word
    if result.indirect_object:
        # Pass full WordEntry to preserve synonyms for entity matching
        action["indirect_object"] = result.indirect_object
    if result.indirect_adjective:
        action["indirect_adjective"] = result.indirect_adjective.word

    return {"type": "command", "action": action}


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

    # Show initial location via look command
    response = engine.json_handler.handle_message({
        "type": "command",
        "action": {"verb": "look"}
    })
    print(format_command_result(response))
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

            # Examine/look/inventory -> use command handler
            # (handle_look calls describe_location which includes all visible exits)
            if verb in ("examine", "look", "inventory"):
                json_cmd = parsed_to_json(result)
                response = engine.json_handler.handle_message(json_cmd)
                print(format_command_result(response))
                continue

        # Convert parsed command to JSON
        json_cmd = parsed_to_json(result)

        # Execute via JSON protocol
        response = engine.json_handler.handle_message(json_cmd)

        # Check for meta command signals (quit, save, load)
        if response.get("success") and response.get("data", {}).get("signal"):
            signal = response["data"]["signal"]

            if signal == "quit":
                print(response.get("message", "Thanks for playing!"))
                break

            elif signal == "save":
                filename = response["data"].get("filename")
                if not filename:
                    # Prompt for filename using file dialog
                    filename = get_save_filename(default_dir=save_load_dir,
                                                default_filename="savegame.json")
                if filename:
                    save_game(engine.game_state, filename)
                    print(f"Game saved to {filename}")
                else:
                    print("Save canceled.")
                continue

            elif signal == "load":
                filename = response["data"].get("filename")
                if not filename:
                    # Prompt for filename using file dialog
                    filename = get_load_filename(default_dir=save_load_dir)
                if filename:
                    loaded_state = load_game(filename)
                    if loaded_state:
                        # Reload state in engine
                        engine.reload_state(loaded_state)
                        # Show new location
                        response = engine.json_handler.handle_message({
                            "type": "command",
                            "action": {"verb": "look"}
                        })
                        print(format_command_result(response))
                    else:
                        print(f"Failed to load {filename}")
                else:
                    print("Load canceled.")
                continue

        # Normal command result
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
    parser.add_argument('game_dir', help='Game name (from examples/) or full path to game directory')
    args = parser.parse_args()

    # If it's just a name (no path separators), prefix with examples/
    if '/' not in args.game_dir and not Path(args.game_dir).is_absolute():
        game_path = Path('examples') / args.game_dir
    else:
        game_path = Path(args.game_dir)

    sys.exit(main(game_dir=str(game_path)) or 0)


if __name__ == '__main__':
    cli_main()
