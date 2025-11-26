"""
Shared utility functions for behavior modules.

This module contains helper functions used by command handlers and query handlers.
Functions in this module should be generic and reusable across different behavior modules.

IMPORTANT: All utility functions that operate on entities should accept an actor_id
parameter and use it correctly. Never hardcode "player" - use the actor_id variable.
"""
from typing import Optional, List


def find_accessible_item(accessor, name: str, actor_id: str):
    """
    Find an item that is accessible to the actor.

    Search order (first match wins):
    1. Items in actor's current location
    2. Items in actor's inventory
    3. Items on surface containers in location
    4. Items in open enclosed containers in location

    IMPORTANT: Do not hardcode 'player' - use the actor_id parameter.

    Args:
        accessor: StateAccessor instance
        name: Item name to search for
        actor_id: ID of the actor looking for the item

    Returns:
        Item if found, None otherwise
    """
    actor = accessor.get_actor(actor_id)
    if not actor:
        return None

    # Get current location
    location = accessor.get_current_location(actor_id)
    if not location:
        return None

    name_lower = name.lower()

    # Check items directly in location first
    items_in_location = accessor.get_items_in_location(location.id)
    for item in items_in_location:
        if item.name.lower() == name_lower:
            return item

    # Check inventory
    item = find_item_in_inventory(accessor, name, actor_id)
    if item:
        return item

    # Check containers in location
    for container in items_in_location:
        container_info = container.properties.get("container", {})
        if not container_info:
            continue

        is_surface = container_info.get("is_surface", False)
        is_open = container_info.get("open", False)

        # Surface containers are always accessible
        # Enclosed containers must be open
        if is_surface or is_open:
            # Get items inside this container
            items_in_container = accessor.get_items_in_location(container.id)
            for item in items_in_container:
                if item.name.lower() == name_lower:
                    return item

    return None


def find_item_in_inventory(accessor, name: str, actor_id: str):
    """
    Find an item in the actor's inventory.

    IMPORTANT: Do not hardcode 'player' - use the actor_id parameter.

    Args:
        accessor: StateAccessor instance
        name: Item name to search for
        actor_id: ID of the actor whose inventory to search

    Returns:
        Item if found in inventory, None otherwise
    """
    actor = accessor.get_actor(actor_id)
    if not actor:
        return None

    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item and item.name.lower() == name.lower():
            return item

    return None


def find_container_by_name(accessor, name: str, location_id: str):
    """
    Find a container item in a location.

    A container is an item with properties.is_container == True.

    Args:
        accessor: StateAccessor instance
        name: Container name to search for
        location_id: ID of the location to search in

    Returns:
        Item if found and is a container, None otherwise
    """
    items = accessor.get_items_in_location(location_id)

    for item in items:
        if item.name.lower() == name.lower():
            # Check if it's a container
            if hasattr(item, 'properties') and isinstance(item.properties, dict):
                if item.properties.get('is_container'):
                    return item

    return None


def actor_has_key_for_door(accessor, actor_id: str, door) -> bool:
    """
    Check if actor has a key that can unlock the door.

    IMPORTANT: Do not hardcode 'player' - use the actor_id parameter.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of the actor to check
        door: Door object to check

    Returns:
        True if actor has a key for the door, False otherwise
    """
    # Get the lock for this door
    if not hasattr(door, 'lock_id'):
        return False

    lock = accessor.get_lock(door.lock_id)
    if not lock:
        return False

    # Get list of keys that open this lock
    if not hasattr(lock, 'opens_with'):
        return False

    key_ids = lock.opens_with
    if not key_ids:
        return False

    # Check if actor has any of these keys
    actor = accessor.get_actor(actor_id)
    if not actor:
        return False

    for key_id in key_ids:
        if key_id in actor.inventory:
            return True

    return False


def get_visible_items_in_location(accessor, location_id: str, actor_id: str) -> List:
    """
    Get all visible items in a location.

    Currently returns all items in the location. Future versions may
    implement visibility rules.

    Args:
        accessor: StateAccessor instance
        location_id: ID of the location
        actor_id: ID of the actor viewing (for future visibility rules)

    Returns:
        List of visible Item objects
    """
    return accessor.get_items_in_location(location_id)


def get_visible_actors_in_location(accessor, location_id: str, actor_id: str) -> List:
    """
    Get all visible actors in a location, excluding the viewing actor.

    IMPORTANT: Excludes the actor specified by actor_id from the results.

    Args:
        accessor: StateAccessor instance
        location_id: ID of the location
        actor_id: ID of the actor viewing (excluded from results)

    Returns:
        List of visible Actor objects (excluding actor_id)
    """
    all_actors = accessor.get_actors_in_location(location_id)

    # Filter out the viewing actor
    return [actor for actor in all_actors if actor.id != actor_id]


def get_doors_in_location(accessor, location_id: str, actor_id: str) -> List:
    """
    Get all doors in a location.

    Args:
        accessor: StateAccessor instance
        location_id: ID of the location
        actor_id: ID of the actor viewing (for future visibility rules)

    Returns:
        List of Door objects connected to this location
    """
    all_doors = accessor.game_state.doors
    doors_in_location = []

    for door in all_doors:
        if hasattr(door, 'locations') and location_id in door.locations:
            doors_in_location.append(door)

    return doors_in_location


def _matches_adjective(adjective: str, entity) -> bool:
    """
    Check if an adjective matches an entity's id or description.

    Matching is case-insensitive and looks for the adjective as a word
    in the entity's id or description.

    Args:
        adjective: The adjective to match
        entity: Entity with id and description attributes

    Returns:
        True if adjective matches, False otherwise
    """
    adj_lower = adjective.lower()

    # Check if adjective appears in ID
    if adj_lower in entity.id.lower():
        return True

    # Check if adjective appears in description
    description = getattr(entity, 'description', '') or ''
    if adj_lower in description.lower():
        return True

    return False


def find_accessible_item_with_adjective(
    accessor, name: str, adjective: Optional[str], actor_id: str
):
    """
    Find an item that is accessible to the actor, optionally filtered by adjective.

    If adjective is provided, only returns items whose id or description
    contains the adjective. If no adjective or empty adjective, returns
    first matching item by name.

    IMPORTANT: Do not hardcode 'player' - use the actor_id parameter.

    Args:
        accessor: StateAccessor instance
        name: Item name to search for
        adjective: Optional adjective to filter by (or None/empty for first match)
        actor_id: ID of the actor looking for the item

    Returns:
        Item if found, None otherwise
    """
    actor = accessor.get_actor(actor_id)
    if not actor:
        return None

    # Get current location
    location = accessor.get_current_location(actor_id)
    if not location:
        return None

    name_lower = name.lower()
    has_adjective = adjective and adjective.strip()

    # Collect all accessible items matching name
    matching_items = []

    # Check items directly in location first
    items_in_location = accessor.get_items_in_location(location.id)
    for item in items_in_location:
        if item.name.lower() == name_lower:
            matching_items.append(item)

    # Check inventory
    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item and item.name.lower() == name_lower:
            matching_items.append(item)

    # Check containers in location
    for container in items_in_location:
        container_info = container.properties.get("container", {})
        if not container_info:
            continue

        is_surface = container_info.get("is_surface", False)
        is_open = container_info.get("open", False)

        if is_surface or is_open:
            items_in_container = accessor.get_items_in_location(container.id)
            for item in items_in_container:
                if item.name.lower() == name_lower:
                    matching_items.append(item)

    # If no matches, return None
    if not matching_items:
        return None

    # If no adjective, return first match
    if not has_adjective:
        return matching_items[0]

    # Filter by adjective
    for item in matching_items:
        if _matches_adjective(adjective, item):
            return item

    # No match with adjective
    return None


def find_container_with_adjective(
    accessor, name: str, adjective: Optional[str], location_id: str
):
    """
    Find a container item in a location, optionally filtered by adjective.

    A container is an item with properties.container dict defined.

    Args:
        accessor: StateAccessor instance
        name: Container name to search for
        adjective: Optional adjective to filter by
        location_id: ID of the location to search in

    Returns:
        Item if found and is a container, None otherwise
    """
    name_lower = name.lower()
    has_adjective = adjective and adjective.strip()

    # Collect all containers in location matching name
    matching_containers = []

    items = accessor.get_items_in_location(location_id)
    for item in items:
        if item.name.lower() != name_lower:
            continue

        # Check if it's a container
        container_info = item.properties.get("container", {})
        if container_info:
            matching_containers.append(item)

    # If no matches, return None
    if not matching_containers:
        return None

    # If no adjective, return first match
    if not has_adjective:
        return matching_containers[0]

    # Filter by adjective
    for container in matching_containers:
        if _matches_adjective(adjective, container):
            return container

    # No match with adjective
    return None


def find_item_in_container(accessor, item_name: str, container_id: str, adjective: Optional[str] = None):
    """
    Find an item inside a specific container.

    Args:
        accessor: StateAccessor instance
        item_name: Name of item to find
        container_id: ID of the container to search in
        adjective: Optional adjective to filter items by

    Returns:
        Item if found in container, None otherwise
    """
    name_lower = item_name.lower()
    has_adjective = adjective and adjective.strip()

    # Get items in this container
    items_in_container = accessor.get_items_in_location(container_id)

    matching_items = []
    for item in items_in_container:
        if item.name.lower() == name_lower:
            matching_items.append(item)

    if not matching_items:
        return None

    if not has_adjective:
        return matching_items[0]

    # Filter by adjective
    for item in matching_items:
        if _matches_adjective(adjective, item):
            return item

    return None


def find_door_with_adjective(
    accessor, name: str, adjective: Optional[str], location_id: str,
    actor_id: Optional[str] = None, verb: Optional[str] = None
):
    """
    Find a door in a location, optionally filtered by adjective.

    If adjective is provided, only returns doors whose id or description
    contains the adjective. If no adjective, uses smart selection based on
    the verb being performed:
    - For "unlock": prefer locked doors that the actor has a key for
    - For "open": prefer closed unlocked doors, then closed locked doors
    - For "close": prefer open doors
    - Otherwise: prefer closed/locked doors over open ones

    Args:
        accessor: StateAccessor instance
        name: Door name to search for (often just "door")
        adjective: Optional adjective to filter by (or None/empty for smart selection)
        location_id: ID of the location
        actor_id: Optional actor ID for key checking (defaults to "player")
        verb: Optional verb being performed for smart selection

    Returns:
        Door if found, None otherwise
    """
    name_lower = name.lower()
    has_adjective = adjective and adjective.strip()
    actor_id = actor_id or "player"

    # Collect all doors in location matching name
    matching_doors = []

    for door in accessor.game_state.doors:
        if not hasattr(door, 'locations') or location_id not in door.locations:
            continue

        # Check if name matches id or description
        if name_lower in door.id.lower() or name_lower in door.description.lower():
            matching_doors.append(door)

    # If no matches, return None
    if not matching_doors:
        return None

    # If adjective provided, filter by it
    if has_adjective:
        for door in matching_doors:
            if _matches_adjective(adjective, door):
                return door
        # No match with adjective
        return None

    # Smart selection when no adjective
    if len(matching_doors) == 1:
        return matching_doors[0]

    # Multiple doors - apply smart selection based on verb
    if verb == "unlock":
        # Prefer locked doors that actor has key for
        for door in matching_doors:
            if door.locked and actor_has_key_for_door(accessor, actor_id, door):
                return door
        # Fall back to any locked door
        for door in matching_doors:
            if door.locked:
                return door

    elif verb == "open":
        # Prefer closed unlocked doors (immediately actionable)
        for door in matching_doors:
            if not door.open and not door.locked:
                return door
        # Fall back to closed locked doors
        for door in matching_doors:
            if not door.open:
                return door

    elif verb == "close":
        # Prefer open doors
        for door in matching_doors:
            if door.open:
                return door

    elif verb == "lock":
        # Prefer closed unlocked doors that actor has key for
        for door in matching_doors:
            if not door.open and not door.locked and actor_has_key_for_door(accessor, actor_id, door):
                return door
        # Fall back to any closed unlocked door with a lock
        for door in matching_doors:
            if not door.open and not door.locked and hasattr(door, 'lock_id') and door.lock_id:
                return door

    # Default: prefer locked/closed doors over open ones
    for door in matching_doors:
        if door.locked or not door.open:
            return door

    return matching_doors[0]


def gather_location_contents(accessor, location_id: str, actor_id: str) -> dict:
    """
    Gather all visible contents of a location.

    This is the single source of truth for what's visible in a location.
    Used by both text formatting (describe_location) and JSON queries (_query_location).

    Args:
        accessor: StateAccessor instance
        location_id: ID of location to gather contents for
        actor_id: ID of the actor viewing (excluded from actor list)

    Returns:
        Dict with keys:
            - items: List of items directly in location
            - surface_items: Dict of container_name -> list of items on that surface
            - open_container_items: Dict of container_name -> list of items in open containers
            - actors: List of other actors in location
    """
    # Collect items directly in location
    items_here = []
    for item in accessor.game_state.items:
        if item.location == location_id:
            items_here.append(item)

    # Collect items on surfaces and in open containers
    surface_items = {}  # container_name -> [items]
    open_container_items = {}  # container_name -> [items]

    for container in items_here:
        container_props = container.properties.get("container", {})
        if not container_props:
            continue

        is_surface = container_props.get("is_surface", False)
        is_open = container_props.get("open", False)

        if is_surface or is_open:
            items_in_container = []
            for item in accessor.game_state.items:
                if item.location == container.id:
                    items_in_container.append(item)

            if items_in_container:
                if is_surface:
                    surface_items[container.name] = items_in_container
                else:
                    open_container_items[container.name] = items_in_container

    # Collect other actors
    actors_here = []
    for other_actor_id, other_actor in accessor.game_state.actors.items():
        if other_actor.location == location_id and other_actor_id != actor_id:
            actors_here.append(other_actor)

    return {
        "items": items_here,
        "surface_items": surface_items,
        "open_container_items": open_container_items,
        "actors": actors_here
    }


def describe_location(accessor, location, actor_id: str) -> List[str]:
    """
    Build a text description of a location including items and actors.

    Uses gather_location_contents for data, then formats as text.

    Args:
        accessor: StateAccessor instance
        location: Location object to describe
        actor_id: ID of the actor viewing (excluded from actor list)

    Returns:
        List of strings that can be joined to form the description
    """
    message_parts = [f"{location.name}\n{location.description}"]

    contents = gather_location_contents(accessor, location.id, actor_id)

    if contents["items"]:
        item_names = ", ".join([item.name for item in contents["items"]])
        message_parts.append(f"\nYou see: {item_names}")

    for container_name, items in contents["surface_items"].items():
        item_names = ", ".join([item.name for item in items])
        message_parts.append(f"On the {container_name}: {item_names}")

    for container_name, items in contents["open_container_items"].items():
        item_names = ", ".join([item.name for item in items])
        message_parts.append(f"In the {container_name}: {item_names}")

    if contents["actors"]:
        actor_names = ", ".join([a.name for a in contents["actors"]])
        message_parts.append(f"\nAlso here: {actor_names}")

    return message_parts
