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
    Reveals the hidden sanctum key by setting states.hidden = False
    and placing it on the same surface/container as the crystal ball.

    Args:
        entity: The crystal ball
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb

    Returns:
        EventResult with allow and message
    """
    # Find the sanctum key (hidden in the same location as the crystal ball)
    sanctum_key = accessor.get_item("item_sanctum_key")
    if not sanctum_key:
        message = "The mists swirl mysteriously but reveal nothing."
        return EventResult(allow=True, message=message)

    # Initialize states if needed
    if not hasattr(sanctum_key, 'states') or sanctum_key.states is None:
        sanctum_key.states = {}

    # Check if the key is still hidden
    if sanctum_key.states.get("hidden", False):
        # Reveal the hidden key by setting hidden to False
        sanctum_key.states["hidden"] = False

        # Place the key in the same location as the crystal ball
        crystal_ball_location = entity.location
        sanctum_key.location = crystal_ball_location

        # Determine the appropriate message based on where the crystal ball is
        location_item = accessor.get_item(crystal_ball_location)
        if location_item and hasattr(location_item, 'properties'):
            container_props = location_item.properties.get("container", {})
            if container_props.get("is_surface", False):
                location_desc = f"on the {location_item.name}"
            elif container_props.get("is_container", False):
                location_desc = f"in the {location_item.name}"
            else:
                location_desc = "on the floor nearby"
        else:
            location_desc = "on the floor nearby"

        message = (
            "The mists within the crystal ball swirl and coalesce...\n"
            "A golden light pulses from within!\n"
            f"As you watch, a small golden key materializes {location_desc}!"
        )
    else:
        # Key already revealed
        message = (
            "The mists swirl and part, but the crystal ball is now empty.\n"
            "You've already claimed what was hidden within."
        )

    return EventResult(allow=True, message=message)
