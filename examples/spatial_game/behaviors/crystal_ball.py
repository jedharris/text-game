"""Crystal ball behavior module.

Demonstrates:
- Adding a new verb (peer/gaze)
- Revealing hidden items through entity behavior
- Modifying game state from entity behavior
"""

from typing import Dict, Any, cast

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from src.types import ActorId
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
    "adjectives": []
}


def handle_peer(accessor, action: Dict) -> HandlerResult:
    """
    Handle the peer/gaze command.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, actor_id

    Returns:
        HandlerResult with success flag and structured data
    """
    from utilities.entity_serializer import serialize_for_handler_result

    actor_id = cast(ActorId, action.get("actor_id") or ActorId("player"))
    obj_name = action.get("object")
    adjective = action.get("adjective")

    if not obj_name:
        return HandlerResult(success=False, primary="Peer into what?")

    # Find item - check inventory first, then location
    item = find_item_in_inventory(accessor, obj_name, actor_id)
    if not item:
        item = find_accessible_item(accessor, obj_name, actor_id, adjective)

    if not item:
        return HandlerResult(success=False, primary=f"You don't see any {obj_name} here.")

    # Check if item can be peered into
    properties = item.properties if hasattr(item, 'properties') else {}
    if not properties.get("magical", False):
        return HandlerResult(
            success=False,
            primary=f"You stare at the {item.name}, but nothing happens."
        )

    # Check if item requires proximity (no auto-positioning!)
    interaction_distance = properties.get("interaction_distance", "any")
    if interaction_distance == "near":
        player = accessor.get_actor(actor_id)
        focused_on = player.properties.get("focused_on")

        # Check if focused on the item or its container
        if focused_on != item.id:
            # Check if focused on item's container
            if hasattr(item, 'location'):
                container = accessor.get_item(item.location)
                if not container or focused_on != container.id:
                    return HandlerResult(
                        success=False,
                        primary=f"You need to be closer to peer into the {item.name}. Try examining it first."
                    )

    # Invoke entity behavior via accessor.update() with verb
    result = accessor.update(item, {}, verb="peer", actor_id=actor_id)

    if not result.success:
        return HandlerResult(success=False, primary=result.detail)

    # Return structured data for narrator to compose
    data = {
        "crystal_ball": serialize_for_handler_result(item, accessor, actor_id)
    }

    # If behavior returned data (revealed key), include it
    if hasattr(result, 'data') and result.data:
        data.update(result.data)

    return HandlerResult(
        success=True,
        primary=f"You peer deeply into the {item.name}.",
        data=data
    )


def on_peer(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Entity behavior for being peered into.

    This is called when the crystal ball is gazed into.
    Reveals the hidden sanctum key by setting states.hidden = False
    and placing it on the same surface/container as the crystal ball.

    Returns structured data for narrator to compose revelation prose.

    Args:
        entity: The crystal ball
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb

    Returns:
        EventResult with allow and structured data (no feedback message)
    """
    from utilities.entity_serializer import serialize_for_handler_result

    actor_id = context.get("actor_id")

    # Find the sanctum key (hidden in the same location as the crystal ball)
    sanctum_key = accessor.get_item("item_sanctum_key")
    if not sanctum_key:
        # No key to reveal - return minimal feedback
        return EventResult(
            allow=True,
            feedback="",
            data={"revelation": "nothing"}
        )

    # Initialize states if needed
    if not hasattr(sanctum_key, 'states') or sanctum_key.states is None:
        sanctum_key.states = {}

    # Check if the key is still hidden
    if sanctum_key.states.get("hidden", False):
        # Reveal the hidden key by setting hidden to False
        sanctum_key.states["hidden"] = False

        # Place the key in the same location as the crystal ball
        crystal_ball_location = entity.location
        accessor.set_entity_where(sanctum_key.id, crystal_ball_location)

        # Determine location type for narrator context
        location_entity = accessor.get_entity(crystal_ball_location)
        location_type = "floor"
        if location_entity and hasattr(location_entity, 'properties'):
            container_props = location_entity.properties.get("container", {})
            if container_props.get("is_surface", False):
                location_type = "surface"
            elif container_props.get("is_container", False):
                location_type = "container"

        # Return structured data for narrator
        return EventResult(
            allow=True,
            feedback="",  # No pre-composed prose
            data={
                "revelation": "key_appears",
                "revealed_key": serialize_for_handler_result(sanctum_key, accessor, actor_id),
                "location_entity": serialize_for_handler_result(location_entity, accessor, actor_id) if location_entity else None,
                "location_type": location_type
            }
        )
    else:
        # Key already revealed - return status
        return EventResult(
            allow=True,
            feedback="",
            data={"revelation": "already_claimed"}
        )
