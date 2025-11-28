"""Location serialization for LLM communication.

Provides unified location-to-dict conversion including all visible contents,
doors, exits, and actors. This consolidates the serialization logic that was
previously duplicated between _query_location() in llm_protocol.py and
gather_location_llm_context() in utils.py.

All location serialization for LLM communication should use this function.
"""
from typing import Any, Dict

from utilities.entity_serializer import entity_to_dict
from utilities.utils import gather_location_contents


def serialize_location_for_llm(accessor, location, actor_id: str) -> Dict[str, Any]:
    """Serialize a location and its visible contents for LLM consumption.

    Produces a consistent structure suitable for both protocol queries and
    behavior handler results. All entity serialization uses entity_to_dict()
    from entity_serializer for consistent llm_context handling.

    Args:
        accessor: StateAccessor instance
        location: Location object to serialize
        actor_id: ID of the actor viewing (affects visibility)

    Returns:
        Dict with structure:
        {
            "location": {"id": str, "name": str, "llm_context": {...}, ...},
            "items": [{"id": str, "name": str, ...}, ...],
            "doors": [{"id": str, "name": str, "direction": str, ...}, ...],
            "exits": {"north": {"type": str, "to": str, ...}, ...},
            "actors": [{"id": str, "name": str, ...}, ...]
        }
    """
    result = {}

    # Serialize location
    result["location"] = entity_to_dict(location)

    # Gather visible contents using shared utility
    contents = gather_location_contents(accessor, location.id, actor_id)

    # Serialize items
    items = []

    # Items directly in location
    for item in contents["items"]:
        items.append(entity_to_dict(item))

    # Items on surfaces - add with on_surface marker
    for container_name, container_items in contents["surface_items"].items():
        for item in container_items:
            item_dict = entity_to_dict(item)
            item_dict["on_surface"] = container_name
            items.append(item_dict)

    # Items in open containers - add with in_container marker
    for container_name, container_items in contents["open_container_items"].items():
        for item in container_items:
            item_dict = entity_to_dict(item)
            item_dict["in_container"] = container_name
            items.append(item_dict)

    result["items"] = items

    # Get visible exits once for both doors and exits
    visible_exits = accessor.get_visible_exits(location.id, actor_id)

    # Serialize doors
    doors = []
    seen_door_ids = set()
    for direction, exit_desc in visible_exits.items():
        # Handle both ExitDescriptor objects and plain strings (backward compatibility)
        if hasattr(exit_desc, 'door_id') and exit_desc.door_id:
            door = accessor.get_door_item(exit_desc.door_id)
            if door and exit_desc.door_id not in seen_door_ids:
                seen_door_ids.add(exit_desc.door_id)
                door_dict = entity_to_dict(door)
                door_dict["direction"] = direction
                doors.append(door_dict)
    result["doors"] = doors

    # Serialize exits
    exits = {}
    for direction, exit_desc in visible_exits.items():
        # Handle both ExitDescriptor objects and plain strings (backward compatibility)
        if isinstance(exit_desc, str):
            # Plain string destination
            exit_data = {
                "type": "passage",
                "to": exit_desc
            }
        else:
            # ExitDescriptor object
            exit_data = {
                "type": exit_desc.type,
                "to": exit_desc.to
            }
            if exit_desc.door_id:
                exit_data["door_id"] = exit_desc.door_id
            # Include llm_context if present
            if exit_desc.llm_context:
                exit_dict = entity_to_dict(exit_desc)
                if "llm_context" in exit_dict:
                    exit_data["llm_context"] = exit_dict["llm_context"]
        exits[direction] = exit_data
    result["exits"] = exits

    # Serialize actors
    actors = []
    for actor in contents["actors"]:
        actors.append(entity_to_dict(actor))
    result["actors"] = actors

    return result
