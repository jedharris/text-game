"""Exit behaviors - go, climb, traverse.

Vocabulary and handlers for moving through exits between locations.
Exits can be referenced by direction (north, up) or by structure name
(stairs, archway, corridor).
"""

from typing import Dict, Any, cast

from src.action_types import ActionDict
from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from src.hooks import LOCATION_ENTERED
from src.types import ActorId
from utilities.utils import find_accessible_item, find_exit_by_name, describe_location
from utilities.handler_utils import get_display_name, validate_actor_and_location
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
        },
        # Direction verbs - bare directions like "north" invoke these handlers
        {"word": "north", "synonyms": ["n"], "object_required": False},
        {"word": "south", "synonyms": ["s"], "object_required": False},
        {"word": "east", "synonyms": ["e"], "object_required": False},
        {"word": "west", "synonyms": ["w"], "object_required": False},
        {"word": "up", "synonyms": ["u"], "object_required": False},
        {"word": "down", "synonyms": ["d"], "object_required": False},
        {"word": "northeast", "synonyms": ["ne"], "object_required": False},
        {"word": "northwest", "synonyms": ["nw"], "object_required": False},
        {"word": "southeast", "synonyms": ["se"], "object_required": False},
        {"word": "southwest", "synonyms": ["sw"], "object_required": False},
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
    "events": [
        {
            "event": "on_enter",
            "hook": "location_entered",
            "description": "Called when an actor enters a location. "
                          "Context includes actor_id and from_direction."
        }
    ]
}


def _build_movement_message(
    exit_descriptor,
    direction: str,
    destination_name: str,
    source_location_id: str,
    verb_phrase: str
) -> str:
    """Build the movement message for exit traversal.

    Handles three cases:
    1. Simple exit (no passage): "You climb the spiral staircase to Tower Room."
    2. Door + passage, door at source: "You go through the ornate door and
       climb the narrow stairs to the Sanctum."
    3. Door + passage, door at destination: "You descend the narrow stairs
       and go through the ornate door to the Library."

    Args:
        exit_descriptor: ExitDescriptor object (or plain string for backward compat)
        direction: Direction being traveled (e.g., "up", "north")
        destination_name: Name of destination location
        source_location_id: ID of location being left
        verb_phrase: Verb phrase from handler (e.g., "go up", "climb the")

    Returns:
        Movement message string
    """
    # Handle plain string destination (backward compatibility)
    if not hasattr(exit_descriptor, 'name'):
        return f"You go {direction} to {destination_name}."

    exit_name = exit_descriptor.name or direction
    passage = getattr(exit_descriptor, 'passage', None)
    door_at = getattr(exit_descriptor, 'door_at', None)

    # Case 1: No passage - simple exit
    if not passage:
        # For door-type exits, say "go through"; for open exits, use verb_phrase
        if exit_descriptor.type == "door":
            return f"You go through the {exit_name} to {destination_name}."
        else:
            return f"You {verb_phrase} {exit_name} to {destination_name}."

    # Case 2 & 3: Door + passage
    # Determine traversal verb based on direction
    if direction in ("up",):
        passage_verb = "climb"
    elif direction in ("down",):
        passage_verb = "descend"
    else:
        passage_verb = "traverse"

    if door_at == source_location_id:
        # Door at source: door first, then passage
        return (
            f"You go through the {exit_name} and {passage_verb} the {passage} "
            f"to {destination_name}."
        )
    else:
        # Door at destination: passage first, then door
        return (
            f"You {passage_verb} the {passage} and go through the {exit_name} "
            f"to {destination_name}."
        )


def _perform_exit_movement(accessor, actor, actor_id: ActorId, exit_descriptor, direction: str, verb_phrase: str) -> HandlerResult:
    """
    Generic exit movement handler for go, climb, and similar movement verbs.

    Args:
        accessor: StateAccessor instance
        actor: Actor entity
        actor_id: Actor ID string
        exit_descriptor: ExitDescriptor object describing the exit
        direction: Direction or exit name for messages
        verb_phrase: Verb phrase for message (e.g., "go", "climb the")

    Returns:
        HandlerResult with success flag and message
    """
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
                        primary=f"The {door_item.name} is closed."
                    )
            else:
                # Fall back to old-style Door entity during migration
                door = accessor.get_door(exit_descriptor.door_id)
                if door and not door.open:
                    return HandlerResult(
                        success=False,
                        primary=f"The {door.description or 'door'} is closed."
                    )
    else:
        # Plain string destination (backward compatibility)
        destination_id = exit_descriptor

    destination = accessor.get_location(destination_id)

    if not destination:
        return HandlerResult(
            success=False,
            primary=f"INCONSISTENT STATE: Destination {destination_id} not found"
        )

    # Capture source location before updating
    source_location_id = actor.location

    # Update actor location
    result = accessor.update(actor, {"location": destination_id})

    if not result.success:
        return HandlerResult(
            success=False,
            primary=f"INCONSISTENT STATE: Failed to move actor: {result.detail}"
        )

    # Invoke location_entered hook if destination location has behaviors
    on_enter_message = None
    event = accessor.behavior_manager.get_event_for_hook(LOCATION_ENTERED)
    if event and hasattr(destination, 'behaviors') and destination.behaviors:
        context = {"actor_id": actor_id, "from_direction": direction}
        behavior_result = accessor.behavior_manager.invoke_behavior(
            destination, event, accessor, context
        )
        if behavior_result and behavior_result.feedback:
            on_enter_message = behavior_result.feedback

    # Build message with movement and auto-look
    movement_msg = _build_movement_message(
        exit_descriptor, direction, destination.name, source_location_id, verb_phrase
    )
    message_parts = [f"{movement_msg}\n"]

    # Add on_enter message if present
    if on_enter_message:
        message_parts.append(f"{on_enter_message}\n")

    # Add location description using shared utility
    message_parts.extend(describe_location(accessor, destination, actor_id))

    # Serialize location for LLM consumption
    llm_data = serialize_location_for_llm(accessor, destination, actor_id)

    return HandlerResult(
        success=True,
        primary="\n".join(message_parts),
        data=llm_data
    )


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
    # Validate actor and location
    actor_id, actor, current_location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    # Extract action parameters
    object_entry = action.get("object")  # Now a WordEntry, not just string
    preposition = action.get("preposition")
    adjective = action.get("adjective")

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
                primary=f"You don't see any {get_display_name(object_entry)} here to go through."
            )
        direction, exit_descriptor = exit_result
        # Check for ambiguity
        if direction is None and isinstance(exit_descriptor, list):
            exit_names = exit_descriptor
            names_str = " or ".join(f'"{name}"' for name in exit_names)
            return HandlerResult(
                success=False,
                primary=f"Which {object_name} do you mean: {names_str}?"
            )
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
                    primary=f"You can't go {get_display_name(object_entry)} from here."
                )
            direction, exit_descriptor = exit_result
            # Check for ambiguity
            if direction is None and isinstance(exit_descriptor, list):
                exit_names = exit_descriptor
                names_str = " or ".join(f'"{name}"' for name in exit_names)
                return HandlerResult(
                    success=False,
                    primary=f"Which {object_name} do you mean: {names_str}?"
                )

    # Perform the movement using shared helper
    return _perform_exit_movement(accessor, actor, actor_id, exit_descriptor, direction, f"go {direction}")


def handle_climb(accessor, action):
    """
    Handle climb command.

    Allows an actor to climb a climbable object or exit (like stairs).

    Search order:
    1. Look for an exit by name (e.g., "stairs" matches "spiral staircase")
       - If exit found, move the actor to that destination
    2. If not an exit, return empty failure so other handlers can try
       (e.g., spatial.py handles climbable items)

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item/exit to climb (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    # Validate actor and location
    actor_id, actor, current_location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    object_name = action.get("object")
    adjective = action.get("adjective")

    # Try to find an exit by name
    # NOTE: This handler only handles exit navigation.
    # If the target isn't an exit, we return failure so other handlers can try.
    exit_result = find_exit_by_name(accessor, object_name, actor_id, adjective)

    if not exit_result:
        # Not an exit - return failure silently so other handlers can try
        return HandlerResult(
            success=False,
            primary=""
        )

    # Check for ambiguity - exit_result is (None, list_of_names) when ambiguous
    direction, exit_descriptor = exit_result
    if direction is None and isinstance(exit_descriptor, list):
        # Ambiguous - multiple exits match
        exit_names = exit_descriptor
        names_str = " or ".join(f'"{name}"' for name in exit_names)
        return HandlerResult(
            success=False,
            primary=f"Which stairs do you mean: {names_str}?"
        )

    # Perform the movement using shared helper
    return _perform_exit_movement(accessor, actor, actor_id, exit_descriptor, direction, "climb the")


# Direction handlers - each delegates to shared helper
def _handle_direction(accessor, action, direction: str) -> HandlerResult:
    """
    Shared helper for direction movement commands.

    Handles bare direction commands like "north", "up", etc.
    Looks up the exit in that direction and performs movement if found.

    Args:
        accessor: StateAccessor instance
        action: Action dict with actor_id
        direction: The direction to move (e.g., "north", "up")

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = cast(ActorId, action.get("actor_id") or ActorId("player"))
    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(success=False, primary="No actor found.")

    location = accessor.get_location(actor.location)
    if not location:
        return HandlerResult(success=False, primary="Actor has no location.")

    visible_exits = accessor.get_visible_exits(location.id, actor_id)
    if direction not in visible_exits:
        return HandlerResult(
            success=False,
            primary=f"You can't go {direction} from here."
        )

    exit_descriptor = visible_exits[direction]
    return _perform_exit_movement(accessor, actor, actor_id, exit_descriptor, direction, f"go {direction}")


def handle_north(accessor, action):
    """Handle bare 'north' command."""
    return _handle_direction(accessor, action, "north")


def handle_south(accessor, action):
    """Handle bare 'south' command."""
    return _handle_direction(accessor, action, "south")


def handle_east(accessor, action):
    """Handle bare 'east' command."""
    return _handle_direction(accessor, action, "east")


def handle_west(accessor, action):
    """Handle bare 'west' command."""
    return _handle_direction(accessor, action, "west")


def handle_up(accessor, action):
    """Handle bare 'up' command."""
    return _handle_direction(accessor, action, "up")


def handle_down(accessor, action):
    """Handle bare 'down' command."""
    return _handle_direction(accessor, action, "down")


def handle_northeast(accessor, action):
    """Handle bare 'northeast' command."""
    return _handle_direction(accessor, action, "northeast")


def handle_northwest(accessor, action):
    """Handle bare 'northwest' command."""
    return _handle_direction(accessor, action, "northwest")


def handle_southeast(accessor, action):
    """Handle bare 'southeast' command."""
    return _handle_direction(accessor, action, "southeast")


def handle_southwest(accessor, action):
    """Handle bare 'southwest' command."""
    return _handle_direction(accessor, action, "southwest")
