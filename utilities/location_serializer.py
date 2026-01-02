"""Location serialization for LLM communication.

Provides unified location-to-dict conversion including all visible contents,
doors, exits, and actors. This consolidates the serialization logic that was
previously duplicated between _query_location() in llm_protocol.py and
gather_location_llm_context() in utils.py.

All location serialization for LLM communication should use this function.
"""
from typing import Any, Dict, Optional

from src.types import ActorId
from utilities.entity_serializer import entity_to_dict
from utilities.state_variant_selector import select_state_variant
from utilities.utils import gather_location_contents


def _build_player_context(accessor, actor_id: ActorId) -> Dict[str, Any]:
    """Build player_context dict from actor's posture and focus.

    Returns a dict with the player's current positioning state for
    perspective-aware LLM narration.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of actor to get context for

    Returns:
        Dict with posture, focused_on, and optionally focused_entity_name
    """
    actor = accessor.get_actor(actor_id)  # Raises KeyError if not found
    properties = actor.properties if hasattr(actor, 'properties') else {}
    posture = properties.get("posture")
    focused_on = properties.get("focused_on")

    context: Dict[str, Any] = {
        "posture": posture,
        "focused_on": focused_on
    }

    # Resolve focused entity name if we have a focus
    if focused_on:
        # Try to find the focused entity to get its name
        focused_entity = accessor.get_item(focused_on)
        if focused_entity and hasattr(focused_entity, 'name'):
            context["focused_entity_name"] = focused_entity.name

    return context


def serialize_location_for_llm(accessor, location, actor_id: ActorId) -> Dict[str, Any]:
    """Serialize a location and its visible contents for LLM consumption.

    Produces a consistent structure suitable for both protocol queries and
    behavior handler results. All entity serialization uses entity_to_dict()
    from entity_serializer for consistent llm_context handling.

    Exit entities are serialized with type computed from door_id:
    - If exit.door_id is present, type is "door"
    - If exit.door_id is None, type is "open"

    Args:
        accessor: StateAccessor instance
        location: Location object to serialize
        actor_id: ID of the actor viewing (affects visibility)

    Returns:
        Dict with structure:
        {
            "player_context": {"posture": str|None, "focused_on": str|None, ...},
            "location": {"id": str, "name": str, "llm_context": {...}, ...},
            "items": [{"id": str, "name": str, ...}, ...],
            "doors": [{"id": str, "name": str, "direction": str, ...}, ...],
            "exits": {"north": {"type": "door"|"open", "to": str, "door_id": str?, ...}, ...},
            "actors": [{"id": str, "name": str, ...}, ...]
        }
    """
    result: Dict[str, Any] = {}

    # Build player context for perspective-aware narration
    player_context = _build_player_context(accessor, actor_id)
    result["player_context"] = player_context

    # Serialize location
    location_dict = entity_to_dict(location)

    # Select state variant based on world state (Context Builder logic)
    if 'llm_context' in location_dict:
        state = accessor.game_state
        state_note = select_state_variant(
            location_dict['llm_context'],
            location,
            state.extra,
            actor_id
        )

        if state_note:
            location_dict['state_note'] = state_note

        # Remove state_variants from output - Narration Model should only see selected variant
        # (same pattern as perspective_variants for items)
        location_dict['llm_context'].pop('state_variants', None)

    result["location"] = location_dict

    # Gather visible contents using shared utility
    contents = gather_location_contents(accessor, location.id, actor_id)

    # Serialize items - pass player_context for spatial_relation and perspective_variants
    items = []

    # Items directly in location
    for item in contents["items"]:
        items.append(entity_to_dict(item, player_context=player_context))

    # Items on surfaces - add with on_surface marker
    for container_name, container_items in contents["surface_items"].items():
        for item in container_items:
            item_dict = entity_to_dict(item, player_context=player_context)
            item_dict["on_surface"] = container_name
            items.append(item_dict)

    # Items in open containers - add with in_container marker
    for container_name, container_items in contents["open_container_items"].items():
        for item in container_items:
            item_dict = entity_to_dict(item, player_context=player_context)
            item_dict["in_container"] = container_name
            items.append(item_dict)

    result["items"] = items

    # Get visible exits once for both doors and exits
    visible_exits = accessor.get_visible_exits(location.id, actor_id)

    # Serialize doors - pass player_context for perspective_variants
    doors = []
    seen_door_ids = set()
    for direction, exit_entity in visible_exits.items():
        # Check if exit has a door (door_id is direct attribute)
        if exit_entity.door_id:
            door = accessor.get_door_item(exit_entity.door_id)
            if door and exit_entity.door_id not in seen_door_ids:
                seen_door_ids.add(exit_entity.door_id)
                door_dict = entity_to_dict(door, player_context=player_context)
                door_dict["direction"] = direction
                doors.append(door_dict)
    result["doors"] = doors

    # Serialize exits - pass player_context for perspective_variants
    exits = {}
    for direction, exit_entity in visible_exits.items():
        # Get destination by traversing connections
        destination_id = None
        if exit_entity.connections:
            connected_exit_id = exit_entity.connections[0]
            try:
                connected_exit = accessor.game_state.get_exit(connected_exit_id)
                destination_id = connected_exit.location
            except KeyError:
                pass

        # Compute exit type from door_id (not stored in properties)
        exit_type = "door" if exit_entity.door_id else "open"

        exit_data = {
            "type": exit_type,
            "to": destination_id
        }
        # Include name and description for LLM narration
        if exit_entity.name:
            exit_data["name"] = exit_entity.name
        if exit_entity.description:
            exit_data["description"] = exit_entity.description
        # Include door_id if present (direct attribute)
        if exit_entity.door_id:
            exit_data["door_id"] = exit_entity.door_id
        # Include llm_context if present in traits - pass player_context for perspective_variants
        if "llm_context" in exit_entity.traits:
            exit_dict = entity_to_dict(exit_entity, player_context=player_context)
            if "llm_context" in exit_dict:
                exit_data["llm_context"] = exit_dict["llm_context"]
            # Also include perspective_note if present
            if "perspective_note" in exit_dict:
                exit_data["perspective_note"] = exit_dict["perspective_note"]
        exits[direction] = exit_data
    result["exits"] = exits

    # Serialize actors (don't need player_context - spatial_relation is for items)
    actors = []
    for actor in contents["actors"]:
        actors.append(entity_to_dict(actor))
    result["actors"] = actors

    return result
