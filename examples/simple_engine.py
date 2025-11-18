
"""Simple game demonstrating state_manager usage."""

import os
import sys
from pathlib import Path

# Add project root to path so we can import from src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.parser import Parser
from src.state_manager import load_game_state, save_game_state, GameState
from src.file_dialogs import get_save_filename, get_load_filename


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
    if not door.lock_id:
        return (False, False)

    lock = get_lock_by_id(state, door.lock_id)
    if not lock:
        return (False, False)

    # Check if player has any key that opens this lock
    has_key = any(key_id in state.player.inventory for key_id in lock.opens_with)
    return (has_key, lock.auto_unlock)


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

        match (not door.open, door.locked, has_key, auto_unlock):
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
                door.locked = False
                door.open = True

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


def take_item(state: GameState, item_name: str, adjective: str = None):
    """Take an item from current location."""
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

    if not item.portable:
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


def drop_item(state: GameState, item_name: str):
    """Drop an item from inventory."""
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


def examine_item(state: GameState, item_name: str):
    """Examine an item, door, or current location."""
    loc = get_current_location(state)

    # Check current location for items
    for item in state.items:
        if item.name == item_name and item.location == loc.id:
            print(item.description)
            return True

    # Check inventory
    for item_id in state.player.inventory:
        item = get_item_by_id(state, item_id)
        if item and item.name == item_name:
            print(item.description)
            return True

    # Check for doors (accept "door" as the name)
    if item_name == "door":
        doors = get_door_in_current_room(state)
        if doors:
            # Show all doors in the room
            for door in doors:
                print(door.description)
                if door.locked:
                    print("  The door is locked.")
                elif door.open:
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
            if not d.open:
                door = d
                break
        if not door:
            door = doors[0]  # All doors are open, just pick the first

        if door.locked:
            # Check if player has a key
            has_key, _ = player_has_key_for_door(state, door)
            if has_key:
                print("You unlock the door with your key.")
                door.locked = False
                door.open = True
                return True
            else:
                print("The door is locked. You need a key.")
                return False

        if door.open:
            print("The door is already open.")
            return False

        door.open = True
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
        if d.open:
            door = d
            break
    if not door:
        door = doors[0]  # All doors are closed, just pick the first

    if not door.open:
        print("The door is already closed.")
        return False

    door.open = False
    print("You close the door.")
    return True


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


def main():
    # Get the directory of this script
    script_dir = Path(__file__).parent

    # Initialize parser
    parser = Parser('data/vocabulary.json')

    # Load initial game state
    state_file = script_dir / "simple_game_state.json"
    state = load_game_state(str(state_file))

    print(f"Welcome to {state.metadata.title}!")
    print("Type 'quit' to exit, 'inventory' to see your items, 'look' to examine your surroundings.")
    print("Type 'save <filename>' to save your game, 'load <filename>' to load a saved game.")
    print()
    describe_location(state)
    print()

    while True:
        # Get user input
        command_text = input("> ").strip()

        # Parse command - now handles all verbs including quit, save, load, inventory
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
                        filename = get_save_filename(default_dir=".", default_filename="savegame.json")
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
                        filename = get_load_filename(default_dir=".")
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
                take_item(state, obj_name, adjective)

            # Handle "drop" command (object required)
            case _ if result.verb and result.verb.word == "drop" and result.direct_object:
                drop_item(state, result.direct_object.word)

            # Handle "open" command (object required)
            case _ if result.verb and result.verb.word == "open" and result.direct_object:
                open_result = open_item(state, result.direct_object.word)
                if open_result == "win":
                    break  # Win condition - opened the chest!

            # Handle "close" command (object required)
            case _ if result.verb and result.verb.word == "close" and result.direct_object:
                close_door(state, result.direct_object.word)

            # Handle "go" with direction
            case _ if result.verb and result.verb.word == "go" and result.direction:
                move_player(state, result.direction.word)

            # Fallback for unhandled commands
            case _:
                print("I don't know how to do that.")


if __name__ == '__main__':
    main()
