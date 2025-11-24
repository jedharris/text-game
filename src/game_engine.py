"""Text adventure game engine with state management."""

import json
import sys
import tempfile
from pathlib import Path

# Add project root to path so we can import from src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.parser import Parser
from src.state_manager import load_game_state, save_game_state, GameState
from src.file_dialogs import get_save_filename, get_load_filename
from src.json_protocol import JSONProtocolHandler
from src.vocabulary_generator import extract_nouns_from_state, merge_vocabulary
from src.behavior_manager import BehaviorManager

# Default game state file location
DEFAULT_STATE_FILE = Path(__file__).parent.parent / "examples" / "simple_game_state.json"


def get_current_location(state: GameState):
    """Get the current location object."""
    for loc in state.locations:
        if loc.id == state.player.location:
            return loc
    return None


def get_item_by_name(state: GameState, name: str):
    """Find an item by its name field."""
    for item in state.items:
        if item.name == name:
            return item
    return None


def get_item_by_id(state: GameState, item_id: str):
    """Find an item by its ID."""
    for item in state.items:
        if item.id == item_id:
            return item
    return None


def get_door_by_id(state: GameState, door_id: str):
    """Find a door by its ID."""
    for door in state.doors:
        if door.id == door_id:
            return door
    return None


def get_door_in_current_room(state: GameState):
    """Get all doors in the current location."""
    loc = get_current_location(state)
    if not loc:
        return []

    doors_here = []
    for door in state.doors:
        if loc.id in door.locations:
            doors_here.append(door)
    return doors_here


def get_lock_by_id(state: GameState, lock_id: str):
    """Find a lock by its ID."""
    for lock in state.locks:
        if lock.id == lock_id:
            return lock
    return None


def player_has_key_for_door(state: GameState, door) -> tuple[bool, bool]:
    """
    Check if player has a key that fits the door's lock.

    Returns:
        (has_key, auto_unlock): Tuple where has_key is True if player has
        the correct key, and auto_unlock is True if the lock auto-unlocks.
    """
    lock_id = door.properties.get("lock_id")
    if not lock_id:
        return (False, False)

    lock = get_lock_by_id(state, lock_id)
    if not lock:
        return (False, False)

    # Check if player has any key that opens this lock
    opens_with = lock.properties.get("opens_with", [])
    has_key = any(key_id in state.player.inventory for key_id in opens_with)
    return (has_key, lock.properties.get("auto_unlock", False))


def describe_location(state: GameState):
    """Describe the current location."""
    loc = get_current_location(state)
    if loc:
        print(loc.description)

        # List items in location
        items_here = [item for item in state.items if item.location == loc.id]
        if items_here:
            item_names = [item.name for item in items_here]
            print("You see:", ", ".join(item_names))

        # List exits (including doors)
        if loc.exits:
            exit_descriptions = []
            for direction, exit_desc in loc.exits.items():
                if exit_desc.type == "door" and exit_desc.door_id:
                    # Find the door and include its state
                    door = get_door_by_id(state, exit_desc.door_id)
                    if door:
                        # Get a brief description from the door's description
                        # Extract first adjective or distinctive word
                        door_desc = door.properties.get("description", "")
                        desc_words = door_desc.lower().split()
                        adjective = next((word for word in desc_words
                                        if word in ["wooden", "iron", "heavy", "simple", "golden", "ancient"]),
                                       "door")

                        # Add state info
                        state_info = []
                        if door.properties.get("locked", False):
                            state_info.append("locked")
                        if door.properties.get("open", False):
                            state_info.append("open")
                        else:
                            state_info.append("closed")

                        if state_info:
                            exit_descriptions.append(f"{adjective} door ({', '.join(state_info)}) to the {direction}")
                        else:
                            exit_descriptions.append(f"{adjective} door to the {direction}")
                else:
                    # Regular open exit
                    exit_descriptions.append(f"passage to the {direction}")

            if exit_descriptions:
                print("Exits:", ", ".join(exit_descriptions))


def show_inventory(state: GameState):
    """Show player's inventory."""
    if state.player.inventory:
        items = [get_item_by_id(state, item_id).name for item_id in state.player.inventory]
        print("You are carrying:", ", ".join(items))
    else:
        print("You are not carrying anything.")


def move_player(state: GameState, direction: str):
    """Move player in a direction."""
    loc = get_current_location(state)
    if not loc:
        print("Error: current location not found!")
        return False

    if direction not in loc.exits:
        print(f"You can't go {direction} from here.")
        return False

    exit_desc = loc.exits[direction]

    # Check if exit goes through a door
    if exit_desc.type == "door" and exit_desc.door_id:
        door = get_door_by_id(state, exit_desc.door_id)
        if not door:
            print("Error: door not found!")
            return False

        # Handle door interactions using pattern matching
        has_key, auto_unlock = player_has_key_for_door(state, door)

        door_open = door.properties.get("open", False)
        door_locked = door.properties.get("locked", False)
        match (not door_open, door_locked, has_key, auto_unlock):
            # Case 1: Door is open
            case (False, _, _, _):
                print("You pass through the open door.")

            # Case 2: Door is closed but not locked
            case (True, False, _, _):
                print("The door is closed. You need to open it first. Try 'open door'.")
                return False

            # Case 3: Door is closed and locked, no key
            case (True, True, False, _):
                print("The door is locked. You need a key.")
                return False

            # Case 4: Door is closed and locked, have key, no auto-unlock
            case (True, True, True, False):
                print("The door is locked. You have the key but need to unlock it first. Try 'open door'.")
                return False

            # Case 5: Door is closed and locked, have key with auto-unlock
            case (True, True, True, True):
                print("You unlock the door with your key and pass through.")
                door.properties["locked"] = False
                door.properties["open"] = True

            # Case 6: Unexpected state
            case _:
                print("Error: Unexpected door state!")
                return False

    # Move to new location
    if exit_desc.to:
        state.player.location = exit_desc.to
        describe_location(state)
        return True
    else:
        print("Error: exit has no destination!")
        return False


def take_item(state: GameState, item_name: str, adjective: str = None, json_handler=None):
    """Take an item from current location."""
    if json_handler:
        # Use JSON protocol handler (supports behaviors)
        action = {"verb": "take", "object": item_name}
        if adjective:
            action["adjective"] = adjective
        result = json_handler.handle_command({"type": "command", "action": action})

        if result.get("success"):
            if adjective:
                print(f"You take the {adjective} {item_name}.")
            else:
                print(f"You take the {item_name}.")
            # Display behavior message if present
            if "message" in result:
                print(result["message"])
            return True
        else:
            error_msg = result.get("error", {}).get("message", f"You can't take the {item_name}.")
            print(error_msg)
            return False

    # Fallback: direct state manipulation (no behaviors)
    loc = get_current_location(state)
    if not loc:
        return False

    # Find item by name in current location
    item = None
    for i in state.items:
        if i.name == item_name and i.location == loc.id:
            item = i
            break

    if not item:
        print(f"There is no {item_name} here.")
        return False

    if not item.properties.get("portable", False):
        print(f"You can't take the {item_name}.")
        return False

    # Move item to player inventory
    item.location = "player"
    state.player.inventory.append(item.id)

    # Remove from location items list
    if item.id in loc.items:
        loc.items.remove(item.id)

    if adjective:
        print(f"You take the {adjective} {item_name}.")
    else:
        print(f"You take the {item_name}.")

    return True


def drop_item(state: GameState, item_name: str, json_handler=None):
    """Drop an item from inventory."""
    if json_handler:
        # Use JSON protocol handler (supports behaviors)
        result = json_handler.handle_command({
            "type": "command",
            "action": {"verb": "drop", "object": item_name}
        })

        if result.get("success"):
            print(f"You drop the {item_name}.")
            # Display behavior message if present
            if "message" in result:
                print(result["message"])
            return True
        else:
            error_msg = result.get("error", {}).get("message", f"You can't drop the {item_name}.")
            print(error_msg)
            return False

    # Fallback: direct state manipulation (no behaviors)
    loc = get_current_location(state)
    if not loc:
        return False

    # Find item in inventory
    item = None
    for item_id in state.player.inventory:
        i = get_item_by_id(state, item_id)
        if i and i.name == item_name:
            item = i
            break

    if not item:
        print(f"You are not carrying a {item_name}.")
        return False

    # Move item to location
    item.location = loc.id
    state.player.inventory.remove(item.id)
    loc.items.append(item.id)

    print(f"You drop the {item_name}.")
    return True


def put_item(state: GameState, item_name: str, container_name: str, json_handler=None):
    """Put an item on/in a container."""
    if json_handler:
        # Use JSON protocol handler (supports behaviors)
        result = json_handler.handle_command({
            "type": "command",
            "action": {"verb": "put", "object": item_name, "indirect_object": container_name}
        })

        if result.get("success"):
            container = result.get("container", {})
            container_props = container.get("container", {})
            preposition = "on" if container_props.get("is_surface", False) else "in"
            print(f"You put the {item_name} {preposition} the {container_name}.")
            # Display behavior message if present
            if "message" in result:
                print(result["message"])
            return True
        else:
            error_msg = result.get("error", {}).get("message", f"You can't put the {item_name} there.")
            print(error_msg)
            return False

    # Fallback: no json_handler provided
    print("Put command requires json_handler.")
    return False


def examine_item(state: GameState, item_name: str):
    """Examine an item, door, or current location."""
    loc = get_current_location(state)

    def _print_item_details(item):
        """Print item description and lit state if applicable."""
        print(item.description)
        # Show lit state for light sources
        if item.properties.get("provides_light", False):
            states = item.properties.get("states", {})
            if states.get('lit'):
                print("It is currently lit, casting a warm glow.")
            else:
                print("It is currently unlit.")

    # Check current location for items
    for item in state.items:
        if item.name == item_name and item.location == loc.id:
            _print_item_details(item)
            return True

    # Check items on surface containers in current location
    for container in state.items:
        container_props = container.properties.get("container")
        if container.location == loc.id and container_props:
            if container_props.get("is_surface", False):
                # Search items on this surface
                for item in state.items:
                    if item.name == item_name and item.location == container.id:
                        _print_item_details(item)
                        return True

    # Check inventory
    for item_id in state.player.inventory:
        item = get_item_by_id(state, item_id)
        if item and item.name == item_name:
            _print_item_details(item)
            return True

    # Check for doors (accept "door" as the name)
    if item_name == "door":
        doors = get_door_in_current_room(state)
        if doors:
            # Show all doors in the room
            for door in doors:
                print(door.properties.get("description", "A door."))
                if door.properties.get("locked", False):
                    print("  The door is locked.")
                elif door.properties.get("open", False):
                    print("  The door is open.")
                else:
                    print("  The door is closed.")
            return True

    print(f"You don't see a {item_name} here.")
    return False


def open_item(state: GameState, item_name: str):
    """Open an item (e.g., chest) or door.

    Returns:
        "win" - Player won the game (opened chest)
        True - Successfully opened something
        False - Failed to open
    """
    loc = get_current_location(state)

    # Check if trying to open a door
    if item_name == "door":
        doors = get_door_in_current_room(state)
        if not doors:
            print("There is no door here.")
            return False

        # Prioritize closed/locked doors over open ones
        door = None
        for d in doors:
            if not d.properties.get("open", False):
                door = d
                break
        if not door:
            door = doors[0]  # All doors are open, just pick the first

        if door.properties.get("locked", False):
            # Check if player has a key
            has_key, _ = player_has_key_for_door(state, door)
            if has_key:
                print("You unlock the door with your key.")
                door.properties["locked"] = False
                door.properties["open"] = True
                return True
            else:
                print("The door is locked. You need a key.")
                return False

        if door.properties.get("open", False):
            print("The door is already open.")
            return False

        door.properties["open"] = True
        print("You open the door.")
        return True

    # Find item in current location
    for item in state.items:
        if item.name == item_name and item.location == loc.id:
            if item_name == "chest":
                print("You open the chest and find treasure! You win!")
                return "win"  # Special return value for winning
            else:
                print(f"You can't open the {item_name}.")
                return False

    print(f"There is no {item_name} here.")
    return False


def close_door(state: GameState, item_name: str):
    """Close a door."""
    if item_name != "door":
        print(f"You can't close the {item_name}.")
        return False

    doors = get_door_in_current_room(state)
    if not doors:
        print("There is no door here.")
        return False

    # Prioritize open doors over closed ones
    door = None
    for d in doors:
        if d.properties.get("open", False):
            door = d
            break
    if not door:
        door = doors[0]  # All doors are closed, just pick the first

    if not door.properties.get("open", False):
        print("The door is already closed.")
        return False

    door.properties["open"] = False
    print("You close the door.")
    return True


def drink_item(state: GameState, item_name: str):
    """
    Drink an item (e.g., potion).

    Returns:
        True if item was drunk successfully, False otherwise
    """
    loc = get_current_location(state)

    # Check if item is in inventory
    item_in_inventory = None
    for item_id in state.player.inventory:
        item = next((i for i in state.items if i.id == item_id), None)
        if item and item.name == item_name:
            item_in_inventory = item
            break

    if item_in_inventory:
        # Handle specific drinkable items
        if item_name == "potion":
            print("You drink the glowing red potion.")
            print("You feel refreshed and energized!")
            # Remove potion from inventory
            state.player.inventory.remove(item_in_inventory.id)
            # Could add health restoration or other effects here
            # state.player.stats["health"] = state.player.stats.get("health", 100) + 20
            return True
        else:
            print(f"You can't drink the {item_name}.")
            return False
    else:
        # Check if item is in the room
        item_in_room = None
        for item in state.items:
            if item.name == item_name and item.location == loc.id:
                item_in_room = item
                break

        if item_in_room:
            print(f"You need to take the {item_name} first.")
            return False
        else:
            print(f"You don't see a {item_name} here.")
            return False


def save_game(state: GameState, filename: str):
    """Save the game state to a file."""
    try:
        save_game_state(state, filename)
        print(f"Game saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving game: {e}")
        return False


def load_game(filename: str):
    """Load a game state from a file."""
    try:
        state = load_game_state(filename)
        print(f"Game loaded from {filename}")
        return state
    except Exception as e:
        print(f"Error loading game: {e}")
        return None


def main(save_load_dir=None):
    """
    Run the game.

    Args:
        save_load_dir: Default directory for save/load file dialogs.
                      If None, uses current directory.
    """
    # Set default directory for save/load operations
    if save_load_dir is None:
        save_load_dir = "."

    # Load initial game state from examples directory
    state = load_game_state(str(DEFAULT_STATE_FILE))

    # Initialize behavior manager and load behavior modules first
    # (needed for vocabulary extensions)
    behavior_manager = BehaviorManager()
    behaviors_dir = Path(__file__).parent.parent / "behaviors"
    modules = behavior_manager.discover_modules(str(behaviors_dir))
    behavior_manager.load_modules(modules)

    # Load base vocabulary
    vocab_path = Path(__file__).parent.parent / 'data' / 'vocabulary.json'
    with open(vocab_path, 'r') as f:
        base_vocab = json.load(f)

    # Merge nouns from game state
    extracted_nouns = extract_nouns_from_state(state)
    vocab_with_nouns = merge_vocabulary(base_vocab, extracted_nouns)

    # Merge verbs and other vocabulary from behavior modules
    merged_vocab = behavior_manager.get_merged_vocabulary(vocab_with_nouns)

    # Write merged vocabulary to temp file for parser
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(merged_vocab, f)
        merged_vocab_path = f.name

    # Initialize parser with merged vocabulary
    parser = Parser(merged_vocab_path)

    # Clean up temp file
    Path(merged_vocab_path).unlink()

    # Initialize JSON protocol handler with behavior manager
    json_handler = JSONProtocolHandler(state, behavior_manager=behavior_manager)

    print(f"Welcome to {state.metadata.title}!")
    print("Type 'quit' to exit, 'inventory' to see your items, 'look' to examine your surroundings.")
    print("Type 'save <filename>' to save your game, 'load <filename>' to load a saved game.")
    print("JSON commands are also supported (input starting with '{').")
    print()
    describe_location(state)
    print()

    while True:
        # Get user input
        command_text = input("> ").strip()

        # Check if input is JSON (per spec: starts with '{')
        if command_text.startswith("{"):
            try:
                message = json.loads(command_text)
                result_json = json_handler.handle_message(message)
                print(json.dumps(result_json, indent=2))

                # Check for win condition in JSON result
                if (result_json.get("type") == "result" and
                    result_json.get("success") and
                    result_json.get("action") == "open" and
                    result_json.get("entity", {}).get("name") == "chest"):
                    print("\nYou win!")
                    break
                continue
            except json.JSONDecodeError as e:
                print(json.dumps({
                    "type": "error",
                    "message": f"Invalid JSON: {e}"
                }, indent=2))
                continue

        # Parse text command - handles all verbs including quit, save, load, inventory
        result = parser.parse_command(command_text)

        # Handle errors
        if result is None:
            print("I don't understand that command.")
            continue

        # Process command based on type
        match result:
            # Handle movement (direction only, no verb)
            case _ if result.direction and not result.verb:
                move_player(state, result.direction.word)

            # Handle "quit" command (no object required)
            case _ if result.verb and result.verb.word == "quit":
                print("Thanks for playing!")
                break

            # Handle "inventory" command (no object required)
            case _ if result.verb and result.verb.word == "inventory":
                show_inventory(state)

            # Handle "examine" / "look" without object (examine room)
            case _ if result.verb and result.verb.word == "examine" and result.object_missing:
                describe_location(state)

            # Handle "examine" with object
            case _ if result.verb and result.verb.word == "examine" and result.direct_object:
                examine_item(state, result.direct_object.word)

            # Handle "save" command (optional object)
            case _ if result.verb and result.verb.word == "save":
                if result.direct_object:
                    # User provided filename as a noun (e.g., treating it like an object)
                    save_game(state, result.direct_object.word)
                elif result.object_missing:
                    # "save" alone - extract filename from raw input after the verb
                    parts = result.raw.split(maxsplit=1)
                    if len(parts) > 1:
                        filename = parts[1].strip()
                        save_game(state, filename)
                    else:
                        # No filename provided - open file dialog
                        filename = get_save_filename(default_dir=save_load_dir, default_filename="savegame.json")
                        if filename:
                            save_game(state, filename)
                        else:
                            print("Save canceled.")

            # Handle "load" command (optional object)
            case _ if result.verb and result.verb.word == "load":
                if result.direct_object:
                    # User provided filename as a noun
                    loaded_state = load_game(result.direct_object.word)
                    if loaded_state:
                        state = loaded_state
                        describe_location(state)
                elif result.object_missing:
                    # "load" alone - extract filename from raw input after the verb
                    parts = result.raw.split(maxsplit=1)
                    if len(parts) > 1:
                        filename = parts[1].strip()
                        loaded_state = load_game(filename)
                        if loaded_state:
                            state = loaded_state
                            describe_location(state)
                    else:
                        # No filename provided - open file dialog
                        filename = get_load_filename(default_dir=save_load_dir)
                        if filename:
                            loaded_state = load_game(filename)
                            if loaded_state:
                                state = loaded_state
                                describe_location(state)
                        else:
                            print("Load canceled.")

            # Handle "take" command (object required)
            case _ if result.verb and result.verb.word == "take" and result.direct_object:
                obj_name = result.direct_object.word
                adjective = result.direct_adjective.word if result.direct_adjective else None
                take_item(state, obj_name, adjective, json_handler)

            # Handle "drop" command (object required)
            case _ if result.verb and result.verb.word == "drop" and result.direct_object:
                drop_item(state, result.direct_object.word, json_handler)

            # Handle "put" command (object and indirect object required)
            case _ if result.verb and result.verb.word == "put" and result.direct_object and result.indirect_object:
                put_item(state, result.direct_object.word, result.indirect_object.word, json_handler)

            # Handle "open" command (object required)
            case _ if result.verb and result.verb.word == "open" and result.direct_object:
                open_result = open_item(state, result.direct_object.word)
                if open_result == "win":
                    break  # Win condition - opened the chest!

            # Handle "close" command (object required)
            case _ if result.verb and result.verb.word == "close" and result.direct_object:
                close_door(state, result.direct_object.word)

            # Handle "drink" command (object required)
            case _ if result.verb and result.verb.word == "drink" and result.direct_object:
                drink_item(state, result.direct_object.word)

            # Handle "go" with direction
            case _ if result.verb and result.verb.word == "go" and result.direction:
                move_player(state, result.direction.word)

            # Fallback for unhandled commands
            case _:
                print("I don't know how to do that.")


if __name__ == '__main__':
    main()
