"""Descend command for exiting climbing posture.

Tier 2 library behavior - reusable across games.
"""

from typing import Dict, Any, cast

from src.state_accessor import HandlerResult
from src.types import ActorId


# Vocabulary extension
vocabulary = {
    "verbs": [
        {
            "word": "descend",
            "event": "on_descend",
            "synonyms": [],
            "object_required": False,
            "llm_context": {
                "traits": ["positioning", "climbing"],
                "usage": ["descend", "climb down", "get down"]
            }
        }
    ],
    "nouns": [],
    "adjectives": []
}


def handle_descend(accessor, action: Dict[str, Any]) -> HandlerResult:
    """
    Handle descend/climb down command.

    Clears climbing posture and returns player to normal standing state.
    """
    actor_id = cast(ActorId, action.get("actor_id") or ActorId("player"))

    # Get actor
    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            primary=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Check if currently climbing
    posture = actor.properties.get("posture")
    if posture != "climbing":
        return HandlerResult(
            success=False,
            primary="You're not climbing anything."
        )

    # Get what they were climbing for the message
    focused_on = actor.properties.get("focused_on")
    climbed_thing = None
    if focused_on:
        climbed_thing = accessor.get_item(focused_on)

    # Clear climbing state
    if "posture" in actor.properties:
        del actor.properties["posture"]
    if "focused_on" in actor.properties:
        del actor.properties["focused_on"]

    # Build message
    if climbed_thing:
        message = f"You carefully climb down from the {climbed_thing.name}."
    else:
        message = "You climb down."

    return HandlerResult(success=True, primary=message)
