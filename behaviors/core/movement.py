"""Movement behaviors - go, walk, move.

Vocabulary for movement between locations.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult


# Vocabulary extension - adds movement verbs
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
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}


def handle_go(accessor, action):
    """
    Handle go/walk/move command.

    Allows an actor to move between locations via exits.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - direction: Direction to go (required)

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")
    direction = action.get("direction")

    if not direction:
        return HandlerResult(
            success=False,
            message="Which direction do you want to go?"
        )

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

    # Check if exit exists
    if direction not in current_location.exits:
        return HandlerResult(
            success=False,
            message=f"You can't go {direction} from here."
        )

    # Get destination
    destination_id = current_location.exits[direction]
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

    return HandlerResult(
        success=True,
        message=f"You go {direction} to {destination.name}."
    )
