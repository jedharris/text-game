"""Crystal ball behavior module.

Demonstrates:
- Adding a new verb (peer/gaze)
- Revealing hidden items through entity behavior
- Modifying game state from entity behavior
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_item_in_inventory, find_accessible_item


# Vocabulary extension - adds "peer" and "gaze" verbs
vocabulary = {
    "verbs": [
        {
            "word": "peer",
            "event": "on_peer",
            "synonyms": ["gaze", "scry"],
            "object_required": True
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}


def handle_peer(accessor, action: Dict) -> HandlerResult:
    """
    Handle the peer/gaze command.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, actor_id

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = action.get("actor_id", "player")
    obj_name = action.get("object")
    adjective = action.get("adjective")

    if not obj_name:
        return HandlerResult(success=False, message="Peer into what?")

    # Find item - check inventory first, then location
    item = find_item_in_inventory(accessor, obj_name, actor_id)
    if not item:
        item = find_accessible_item(accessor, obj_name, actor_id, adjective)

    if not item:
        return HandlerResult(success=False, message=f"You don't see any {obj_name} here.")

    # Check if item can be peered into
    properties = item.properties if hasattr(item, 'properties') else {}
    if not properties.get("magical", False):
        return HandlerResult(
            success=False,
            message=f"You stare at the {item.name}, but nothing happens."
        )

    # Invoke entity behavior via accessor.update() with verb
    result = accessor.update(item, {}, verb="peer", actor_id=actor_id)

    if not result.success:
        return HandlerResult(success=False, message=result.message)

    # Build response message
    base_message = f"You peer deeply into the {item.name}..."
    if result.message:
        message = f"{base_message}\n{result.message}"
    else:
        message = base_message

    return HandlerResult(success=True, message=message)


def on_peer(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Entity behavior for being peered into.

    This is called when the crystal ball is gazed into.

    Args:
        entity: The crystal ball
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb

    Returns:
        EventResult with allow and message
    """
    # Track if the key has been revealed
    if not hasattr(entity, 'states') or entity.states is None:
        entity.states = {}

    if entity.states.get("key_revealed", False):
        # Key already revealed
        message = (
            "The mists swirl and part, but the crystal ball is now empty.\n"
            "You've already claimed what was hidden within."
        )
        return EventResult(allow=True, message=message)

    # First time - reveal the hidden key
    entity.states["key_revealed"] = True

    # Move the sanctum key from its hidden location to the player's current location
    # We need to find the key and move it
    sanctum_key = accessor.get_item("item_sanctum_key")
    if sanctum_key:
        # Get the actor's current location
        actor_id = context.get("actor_id", "player")
        actor = accessor.get_actor(actor_id)
        if actor:
            # Move the key to the actor's location
            sanctum_key.location = actor.location
            message = (
                "The mists within the crystal ball swirl and coalesce...\n"
                "A golden light pulses from within!\n"
                "As you watch, a small golden key materializes and falls to the floor!"
            )
        else:
            message = "The mists swirl but nothing happens."
    else:
        message = "The mists swirl mysteriously but reveal nothing."

    return EventResult(allow=True, message=message)
