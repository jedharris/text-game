"""Exit behaviors - go, climb, traverse.

Vocabulary and handlers for moving through exits between locations.
Exits can be referenced by direction (north, up) or by structure name
(stairs, archway, corridor).
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item, find_exit_by_name, describe_location
from utilities.handler_utils import get_display_name
from utilities.entity_serializer import serialize_for_handler_result
from utilities.location_serializer import serialize_location_for_llm


# Vocabulary extension - adds exit-related verbs and nouns
vocabulary = {
    "verbs": [
        {
            "word": "go",
            "event": "on_go",
            "synonyms": ["walk", "move"],
            "object_required": True,
            "llm_context": {
                "traits": ["movement between locations", "requires direction"],
                "failure_narration": {
                    "no_exit": "can't go that way",
                    "blocked": "something blocks the path",
                    "door_closed": "the door is closed"
                }
            }
        },
        {
            "word": "climb",
            "event": "on_climb",
            "synonyms": ["scale", "ascend"],
            "object_required": True,
            "llm_context": {
                "traits": ["traverse exit by climbing", "requires exit structure name"],
                "failure_narration": {
                    "not_found": "can't find that to climb",
                    "not_climbable": "can't climb that"
                }
            }
        }
    ],
    "nouns": [
        # Exit structure nouns (single type)
        {"word": "exit", "synonyms": ["passage", "way", "path", "opening"]},
        {"word": "stairs", "synonyms": ["staircase", "stairway", "steps"]},
        {"word": "archway", "synonyms": ["arch"]},
        {"word": "corridor", "synonyms": ["hallway", "hall"]},
        {"word": "tunnel", "synonyms": ["passageway"]},

        # Direction nouns
        {"word": "north", "synonyms": ["n"]},
        {"word": "south", "synonyms": ["s"]},
        {"word": "east", "synonyms": ["e"]},
        {"word": "west", "synonyms": ["w"]},
        {"word": "up", "synonyms": ["u"]},
        {"word": "down", "synonyms": ["d"]},
        {"word": "northeast", "synonyms": ["ne"]},
        {"word": "northwest", "synonyms": ["nw"]},
        {"word": "southeast", "synonyms": ["se"]},
        {"word": "southwest", "synonyms": ["sw"]}
    ],
    "adjectives": [
        # Directions also work as adjectives (e.g., "north door")
        {"word": "north", "synonyms": []},
        {"word": "south", "synonyms": []},
        {"word": "east", "synonyms": []},
        {"word": "west", "synonyms": []},
        {"word": "up", "synonyms": []},
        {"word": "down", "synonyms": []},
        {"word": "northeast", "synonyms": []},
        {"word": "northwest", "synonyms": []},
        {"word": "southeast", "synonyms": []},
        {"word": "southwest", "synonyms": []}
    ],
    "directions": []
}


def handle_go(accessor, action):
    """
    Handle go/walk/move command.

    Supports:
    1. Direction-based: "go north", "go up"
    2. Exit name: "go archway", "go through archway"

    Uses unified action["object"] for both directions and exit names:
    - First tries to match object as a compass direction
    - If not a direction, tries to match as exit structure name
    - Preposition "through" is optional syntactic sugar

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Direction or exit name (WordEntry)
            - preposition: Optional (e.g., "through")
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")
    object_entry = action.get("object")  # Now a WordEntry, not just string
    preposition = action.get("preposition")
    adjective = action.get("adjective")

    # Get the actor
    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Get current location
    current_location = accessor.get_current_location(actor_id)
    if not current_location:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Cannot find location for actor {actor_id}"
        )

    # Extract object entry
    if not object_entry:
        return HandlerResult(
            success=False,
            message="Which direction do you want to go?"
        )

    # Get object name for error messages
    from src.word_entry import WordEntry
    if isinstance(object_entry, WordEntry):
        object_name = object_entry.word
    else:
        # Backward compatibility: if it's already a string
        object_name = object_entry

    # Determine exit: try as direction first, then as exit name
    exit_descriptor = None
    direction = None

    # If preposition "through" is used, skip direction check and go straight to exit name
    if preposition == "through":
        # Force exit name lookup when "through" is explicit
        # Pass WordEntry to preserve synonyms
        exit_result = find_exit_by_name(accessor, object_entry, actor_id, adjective)
        if not exit_result:
            return HandlerResult(
                success=False,
                message=f"You don't see any {object_name} here to go through."
            )
        direction, exit_descriptor = exit_result
    else:
        # Try to match as a compass direction first
        visible_exits = accessor.get_visible_exits(current_location.id, actor_id)
        if object_name in visible_exits:
            # It's a direction!
            direction = object_name
            exit_descriptor = visible_exits[direction]
        else:
            # Not a direction - try as exit structure name
            # Pass WordEntry to preserve synonyms
            exit_result = find_exit_by_name(accessor, object_entry, actor_id, adjective)
            if not exit_result:
                # Not found as direction or exit name
                return HandlerResult(
                    success=False,
                    message=f"You can't go {object_name} from here."
                )
            direction, exit_descriptor = exit_result

    # Handle both ExitDescriptor objects and plain strings (backward compatibility)
    if hasattr(exit_descriptor, 'to'):
        destination_id = exit_descriptor.to
        # Check for door blocking
        if exit_descriptor.type == 'door' and exit_descriptor.door_id:
            # Try door item first (unified model)
            door_item = accessor.get_door_item(exit_descriptor.door_id)
            if door_item:
                if not door_item.door_open:
                    return HandlerResult(
                        success=False,
                        message=f"The {door_item.name} is closed."
                    )
            else:
                # Fall back to old-style Door entity during migration
                door = accessor.get_door(exit_descriptor.door_id)
                if door and not door.open:
                    return HandlerResult(
                        success=False,
                        message=f"The {door.description or 'door'} is closed."
                    )
    else:
        # Plain string destination (backward compatibility)
        destination_id = exit_descriptor

    destination = accessor.get_location(destination_id)

    if not destination:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Destination {destination_id} not found"
        )

    # Update actor location
    result = accessor.update(actor, {"location": destination_id})

    if not result.success:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Failed to move actor: {result.message}"
        )

    # Invoke on_enter event if destination location has behaviors
    on_enter_message = None
    if hasattr(destination, 'behaviors') and destination.behaviors:
        context = {"actor_id": actor_id, "from_direction": direction}
        behavior_result = accessor.behavior_manager.invoke_behavior(
            destination, "on_enter", accessor, context
        )
        if behavior_result and behavior_result.message:
            on_enter_message = behavior_result.message

    # Build message with movement and auto-look
    message_parts = [f"You go {direction} to {destination.name}.\n"]

    # Add on_enter message if present
    if on_enter_message:
        message_parts.append(f"{on_enter_message}\n")

    # Add location description using shared utility
    message_parts.extend(describe_location(accessor, destination, actor_id))

    # Serialize location for LLM consumption
    llm_data = serialize_location_for_llm(accessor, destination, actor_id)

    return HandlerResult(
        success=True,
        message="\n".join(message_parts),
        data=llm_data
    )


def handle_climb(accessor, action):
    """
    Handle climb command.

    Allows an actor to climb a climbable object or exit (like stairs).

    Search order:
    1. Look for a climbable Item (property "climbable": true)
    2. Look for an exit by name (e.g., "stairs" matches "spiral staircase")
       - If exit found, move the actor to that destination

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item/exit to climb (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    adjective = action.get("adjective")
    verb = action.get("verb", "climb")

    if not object_name:
        return HandlerResult(
            success=False,
            message=f"What do you want to {verb}?"
        )

    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Try to find an exit by name
    # NOTE: This handler only handles exit navigation.
    # If the target isn't an exit, we return failure so other handlers can try.
    exit_result = find_exit_by_name(accessor, object_name, actor_id, adjective)
    if not exit_result:
        # Not an exit - return failure silently so other handlers can try
        return HandlerResult(
            success=False,
            message=""
        )

    if exit_result:
        direction, exit_descriptor = exit_result
        destination_id = exit_descriptor.to

        # Check for door blocking
        if exit_descriptor.type == 'door' and exit_descriptor.door_id:
            door_item = accessor.get_door_item(exit_descriptor.door_id)
            if door_item:
                if not door_item.door_open:
                    return HandlerResult(
                        success=False,
                        message=f"The {door_item.name} is closed."
                    )
            else:
                door = accessor.get_door(exit_descriptor.door_id)
                if door and not door.open:
                    return HandlerResult(
                        success=False,
                        message=f"The {door.description or 'door'} is closed."
                    )

        destination = accessor.get_location(destination_id)
        if not destination:
            return HandlerResult(
                success=False,
                message=f"INCONSISTENT STATE: Destination {destination_id} not found"
            )

        # Move the actor
        result = accessor.update(actor, {"location": destination_id})
        if not result.success:
            return HandlerResult(
                success=False,
                message=f"INCONSISTENT STATE: Failed to move actor: {result.message}"
            )

        # Invoke on_enter event if destination location has behaviors
        on_enter_message = None
        if hasattr(destination, 'behaviors') and destination.behaviors:
            context = {"actor_id": actor_id, "from_direction": direction}
            behavior_result = accessor.behavior_manager.invoke_behavior(
                destination, "on_enter", accessor, context
            )
            if behavior_result and behavior_result.message:
                on_enter_message = behavior_result.message

        # Build message with climb action and auto-look
        exit_name = exit_descriptor.name if exit_descriptor.name else direction
        message_parts = [f"You climb the {exit_name} to {destination.name}.\n"]

        # Add on_enter message if present
        if on_enter_message:
            message_parts.append(f"{on_enter_message}\n")

        message_parts.extend(describe_location(accessor, destination, actor_id))
        llm_data = serialize_location_for_llm(accessor, destination, actor_id)

        return HandlerResult(
            success=True,
            message="\n".join(message_parts),
            data=llm_data
        )

    # Neither climbable item nor exit found
    if item:
        # Found an item but it's not climbable
        return HandlerResult(
            success=False,
            message=f"You can't climb the {item.name}."
        )

    return HandlerResult(
        success=False,
        message=f"You don't see any {get_display_name(object_name)} here to climb."
    )
