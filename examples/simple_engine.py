
"""Simple game demonstrating state_manager usage."""

import os
from pathlib import Path
from src.parser import Parser
from src.state_manager import load_game_state, save_game_state, GameState


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


def get_lock_by_id(state: GameState, lock_id: str):
    """Find a lock by its ID."""
    for lock in state.locks:
        if lock.id == lock_id:
            return lock
    return None


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

        # Check if door is locked
        if door.locked:
            # Check if player has the key
            if door.lock_id:
                lock = get_lock_by_id(state, door.lock_id)
                if lock:
                    # Check if player has any of the items that open this lock
                    has_key = any(key_id in state.player.inventory for key_id in lock.opens_with)
                    if has_key:
                        if lock.auto_unlock:
                            print("You unlock the door with the key and enter.")
                            door.locked = False
                            door.open = True
                        else:
                            print("The door is locked. You need to unlock it first.")
                            return False
                    else:
                        print("The door is locked. You need a key.")
                        return False
                else:
                    print("The door is locked.")
                    return False
            else:
                print("The door is locked.")
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
    """Examine an item."""
    loc = get_current_location(state)

    # Check current location
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

    print(f"You don't see a {item_name} here.")
    return False


def open_item(state: GameState, item_name: str):
    """Open an item (e.g., chest)."""
    loc = get_current_location(state)

    # Find item in current location
    for item in state.items:
        if item.name == item_name and item.location == loc.id:
            if item_name == "chest":
                print("You open the chest and find treasure! You win!")
                return True
            else:
                print(f"You can't open the {item_name}.")
                return False

    print(f"There is no {item_name} here.")
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

        if command_text.lower() == 'quit':
            print("Thanks for playing!")
            break

        if command_text.lower() == 'inventory':
            show_inventory(state)
            continue

        if command_text.lower() == 'look':
            describe_location(state)
            continue

        # Handle save command
        if command_text.lower().startswith('save '):
            filename = command_text[5:].strip()
            if filename:
                save_game(state, filename)
            else:
                print("Please specify a filename: save <filename>")
            continue

        # Handle load command
        if command_text.lower().startswith('load '):
            filename = command_text[5:].strip()
            if filename:
                loaded_state = load_game(filename)
                if loaded_state:
                    state = loaded_state
                    describe_location(state)
            else:
                print("Please specify a filename: load <filename>")
            continue

        # Parse command
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

            # Handle "take" command
            case _ if result.verb and result.verb.word == "take" and result.direct_object:
                obj_name = result.direct_object.word
                adjective = result.direct_adjective.word if result.direct_adjective else None
                take_item(state, obj_name, adjective)

            # Handle "drop" command
            case _ if result.verb and result.verb.word == "drop" and result.direct_object:
                drop_item(state, result.direct_object.word)

            # Handle "examine" command
            case _ if result.verb and result.verb.word == "examine" and result.direct_object:
                examine_item(state, result.direct_object.word)

            # Handle "open" command
            case _ if result.verb and result.verb.word == "open" and result.direct_object:
                if open_item(state, result.direct_object.word):
                    break  # Win condition

            # Handle "go" with direction
            case _ if result.verb and result.verb.word == "go" and result.direction:
                move_player(state, result.direction.word)

            # Fallback for unhandled commands
            case _:
                print("I don't know how to do that.")


if __name__ == '__main__':
    main()
