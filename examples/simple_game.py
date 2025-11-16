"""Simple game demonstrating parser usage."""

from src.parser import Parser


def main():
    # Initialize parser
    parser = Parser('data/vocabulary.json')

    # Game state
    inventory = []
    location = "start"
    game_state = {
        'start': {
            'description': "You are in a small room. There is a rusty sword on the ground and a wooden door to the north.",
            'items': ['sword'],
            'exits': {'north': 'hallway'}
        },
        'hallway': {
            'description': "You are in a long hallway. There is a locked door to the east and stairs going up.",
            'items': ['key'],
            'exits': {'south': 'start', 'up': 'tower', 'east': 'locked_room'}
        },
        'tower': {
            'description': "You are at the top of a tower. You can see for miles. Stairs lead down.",
            'items': ['potion'],
            'exits': {'down': 'hallway'}
        },
        'locked_room': {
            'description': "You are in a treasure room. There is a golden chest here.",
            'items': ['chest'],
            'exits': {'west': 'hallway'},
            'locked': True
        }
    }

    print("Welcome to the Simple Adventure!")
    print("Type 'quit' to exit, 'inventory' to see your items, 'look' to examine your surroundings.")
    print()
    print(game_state[location]['description'])
    print()

    while True:
        # Get user input
        command_text = input("> ").strip()

        if command_text.lower() == 'quit':
            print("Thanks for playing!")
            break

        if command_text.lower() == 'inventory':
            if inventory:
                print("You are carrying:", ", ".join(inventory))
            else:
                print("You are not carrying anything.")
            continue

        if command_text.lower() == 'look':
            print(game_state[location]['description'])
            if game_state[location]['items']:
                print("You see:", ", ".join(game_state[location]['items']))
            continue

        # Parse command
        result = parser.parse_command(command_text)

        # Handle errors
        if result is None:
            print("I don't understand that command.")
            continue

        # Process command based on type
        current_room = game_state[location]

        # Handle movement
        if result.direction:
            direction = result.direction.word
            if direction in current_room.get('exits', {}):
                new_location = current_room['exits'][direction]
                # Check if door is locked
                if game_state[new_location].get('locked', False):
                    if 'key' in inventory:
                        print("You unlock the door with the key and enter.")
                        game_state[new_location]['locked'] = False
                        location = new_location
                        print(game_state[location]['description'])
                    else:
                        print("The door is locked. You need a key.")
                else:
                    location = new_location
                    print(game_state[location]['description'])
            else:
                print(f"You can't go {direction} from here.")

        # Handle taking items
        elif result.verb and result.verb.word == "take":
            if result.direct_object:
                obj_name = result.direct_object.word
                if result.direct_adjective:
                    # For adjectives, just use the base object name
                    obj_name = result.direct_object.word

                if obj_name in current_room['items']:
                    current_room['items'].remove(obj_name)
                    inventory.append(obj_name)
                    if result.direct_adjective:
                        print(f"You take the {result.direct_adjective.word} {obj_name}.")
                    else:
                        print(f"You take the {obj_name}.")
                else:
                    print(f"There is no {obj_name} here.")

        # Handle dropping items
        elif result.verb and result.verb.word == "drop":
            if result.direct_object:
                obj_name = result.direct_object.word
                if obj_name in inventory:
                    inventory.remove(obj_name)
                    current_room['items'].append(obj_name)
                    print(f"You drop the {obj_name}.")
                else:
                    print(f"You are not carrying a {obj_name}.")

        # Handle examining
        elif result.verb and result.verb.word == "examine":
            if result.direct_object:
                obj_name = result.direct_object.word
                if obj_name in current_room['items']:
                    descriptions = {
                        'sword': "A rusty but serviceable sword.",
                        'key': "An iron key.",
                        'potion': "A red potion that glows faintly.",
                        'chest': "A large golden chest. It looks valuable!",
                        'door': "A wooden door."
                    }
                    print(descriptions.get(obj_name, f"You see nothing special about the {obj_name}."))
                elif obj_name in inventory:
                    print(f"You examine the {obj_name} in your inventory.")
                else:
                    print(f"You don't see a {obj_name} here.")

        # Handle opening
        elif result.verb and result.verb.word == "open":
            if result.direct_object and result.direct_object.word == "chest":
                if "chest" in current_room['items']:
                    print("You open the chest and find treasure! You win!")
                    break
                else:
                    print("There is no chest here.")

        # Handle going with direction
        elif result.verb and result.verb.word == "go" and result.direction:
            direction = result.direction.word
            if direction in current_room.get('exits', {}):
                location = current_room['exits'][direction]
                print(game_state[location]['description'])
            else:
                print(f"You can't go {direction} from here.")

        else:
            print("I don't know how to do that.")


if __name__ == '__main__':
    main()
