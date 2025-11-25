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

    An item is accessible if it's either:
    - In the actor's current location
    - In the actor's inventory

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

    # Check inventory first
    item = find_item_in_inventory(accessor, name, actor_id)
    if item:
        return item

    # Check current location
    location = accessor.get_current_location(actor_id)
    if not location:
        return None

    items_in_location = accessor.get_items_in_location(location.id)
    for item in items_in_location:
        if item.name.lower() == name.lower():
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
