"""Manipulation behaviors - take and drop.

Vocabulary and handlers for basic item manipulation.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import (
    find_accessible_item,
    find_item_in_inventory,
    find_container_with_adjective,
    find_item_in_container,
    name_matches
)
from utilities.entity_serializer import serialize_for_handler_result


# Vocabulary extension - adds take and drop verbs
vocabulary = {
    "verbs": [
        {
            "word": "take",
            "event": "on_take",
            "synonyms": ["get", "grab", "pick"],
            "object_required": True,
            "llm_context": {
                "traits": ["physical action", "transfers possession", "requires reachable object"],
                "failure_narration": {
                    "not_found": "cannot find the object",
                    "too_heavy": "too heavy to lift",
                    "fixed": "firmly attached"
                }
            }
        },
        {
            "word": "drop",
            "event": "on_drop",
            "synonyms": ["place"],
            "object_required": True,
            "llm_context": {
                "traits": ["releases held object", "places in current location"],
                "failure_narration": {
                    "not_holding": "not carrying that"
                }
            }
        },
        {
            "word": "give",
            "event": "on_give",
            "synonyms": ["hand", "offer"],
            "object_required": True,
            "llm_context": {
                "traits": ["transfers possession", "requires recipient present"],
                "failure_narration": {
                    "not_holding": "not carrying that",
                    "no_recipient": "no one here by that name"
                }
            }
        },
        {
            "word": "put",
            "event": "on_put",
            "synonyms": ["set"],
            "object_required": True,
            "llm_context": {
                "traits": ["places item in/on container", "requires container target"],
                "failure_narration": {
                    "not_holding": "not carrying that",
                    "not_container": "cannot put things there",
                    "closed": "container is closed",
                    "full": "container is full"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}


def handle_take(accessor, action):
    """
    Handle take/get/grab command.

    Allows an actor to pick up an item from their current location.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item to take (required)
            - adjective: Optional adjective for item disambiguation
            - indirect_object: Optional container name ("take X from Y")
            - indirect_adjective: Optional adjective for container

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    adjective = action.get("adjective")
    container_name = action.get("indirect_object")
    container_adjective = action.get("indirect_adjective")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to take?"
        )

    # Get the actor
    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Get current location
    location = accessor.get_current_location(actor_id)
    if not location:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Cannot find location for actor {actor_id}"
        )

    # If container specified, validate it and search only within it
    if container_name:
        # Find the container in the location
        container = find_container_with_adjective(
            accessor, container_name, container_adjective, location.id
        )

        if not container:
            # Check if item exists but isn't a container
            for item in accessor.get_items_in_location(location.id):
                if name_matches(container_name, item.name):
                    return HandlerResult(
                        success=False,
                        message=f"The {item.name} is not a container."
                    )
            return HandlerResult(
                success=False,
                message=f"You don't see any {container_name} here."
            )

        # Check if enclosed container is open
        container_info = container.properties.get("container", {})
        is_surface = container_info.get("is_surface", False)
        if not is_surface and not container_info.get("open", False):
            return HandlerResult(
                success=False,
                message=f"The {container.name} is closed."
            )

        # Find item in this specific container
        item = find_item_in_container(accessor, object_name, container.id, adjective)
        if not item:
            preposition = "on" if is_surface else "in"
            return HandlerResult(
                success=False,
                message=f"You don't see any {object_name} {preposition} the {container.name}."
            )
    else:
        # No container specified - find item anywhere accessible
        # Use adjective if provided for disambiguation
        item = find_accessible_item(accessor, object_name, actor_id, adjective)

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Check if item is already in actor's inventory
    if item.location == actor_id:
        return HandlerResult(
            success=True,
            message=f"You already have the {item.name}."
        )

    # Check if item is portable
    if not item.portable:
        return HandlerResult(
            success=False,
            message=f"You can't take the {item.name}."
        )

    # Perform state changes
    # 1. Change item location to actor
    # 2. Add item to actor's inventory
    changes = {
        "location": actor_id
    }

    # Pass verb and actor_id to trigger entity behaviors (on_take)
    result = accessor.update(item, changes, verb="take", actor_id=actor_id)

    if not result.success:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Failed to update item location: {result.message}"
        )

    # Add to inventory
    inventory_result = accessor.update(actor, {"+inventory": item.id})

    if not inventory_result.success:
        # Try to rollback item location change
        accessor.update(item, {"location": accessor.get_current_location(actor_id).id})
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Failed to add item to inventory: {inventory_result.message}"
        )

    # Build message - include behavior message if present
    base_message = f"You take the {item.name}."
    if result.message:
        message = f"{base_message} {result.message}"
    else:
        message = base_message

    # Use unified serializer for llm_context with trait randomization
    data = serialize_for_handler_result(item)

    return HandlerResult(
        success=True,
        message=message,
        data=data
    )


def handle_drop(accessor, action):
    """
    Handle drop command.

    Allows an actor to drop an item from their inventory to their current location.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item to drop (required)

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to drop?"
        )

    # Get the actor
    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Find the item in actor's inventory
    item = find_item_in_inventory(accessor, object_name, actor_id)

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't have any {object_name}."
        )

    # Get current location
    location = accessor.get_current_location(actor_id)
    if not location:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Cannot find location for actor {actor_id}"
        )

    # Perform state changes
    # 1. Change item location to current room
    # 2. Remove item from actor's inventory
    changes = {
        "location": location.id
    }

    # Pass verb and actor_id to trigger entity behaviors (on_drop)
    result = accessor.update(item, changes, verb="drop", actor_id=actor_id)

    if not result.success:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Failed to update item location: {result.message}"
        )

    # Remove from inventory
    inventory_result = accessor.update(actor, {"-inventory": item.id})

    if not inventory_result.success:
        # Try to rollback item location change
        accessor.update(item, {"location": actor_id})
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Failed to remove item from inventory: {inventory_result.message}"
        )

    # Build message - include behavior message if present
    base_message = f"You drop the {item.name}."
    if result.message:
        message = f"{base_message} {result.message}"
    else:
        message = base_message

    # Use unified serializer for llm_context with trait randomization
    data = serialize_for_handler_result(item)

    return HandlerResult(
        success=True,
        message=message,
        data=data
    )


def handle_give(accessor, action):
    """
    Handle give command.

    Allows an actor to give an item from their inventory to another actor.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item to give (required)
            - indirect_object: Name of recipient actor (required)

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    recipient_name = action.get("indirect_object")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to give?"
        )

    if not recipient_name:
        return HandlerResult(
            success=False,
            message="Give it to whom?"
        )

    # Get the giver actor
    giver = accessor.get_actor(actor_id)
    if not giver:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Find the item in giver's inventory
    item = find_item_in_inventory(accessor, object_name, actor_id)

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't have any {object_name}."
        )

    # Find recipient actor in same location
    location = accessor.get_current_location(actor_id)
    if not location:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Cannot find location for actor {actor_id}"
        )

    # Search for recipient in current location
    recipient = None
    for other_actor_id, other_actor in accessor.game_state.actors.items():
        if other_actor.location == location.id and name_matches(recipient_name, other_actor.name):
            recipient = other_actor
            break

    if not recipient:
        return HandlerResult(
            success=False,
            message=f"You don't see any {recipient_name} here."
        )

    # Perform state changes
    # 1. Change item location to recipient
    # 2. Remove item from giver's inventory
    # 3. Add item to recipient's inventory
    changes = {
        "location": recipient.id
    }

    result = accessor.update(item, changes)

    if not result.success:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Failed to update item location: {result.message}"
        )

    # Remove from giver's inventory
    remove_result = accessor.update(giver, {"-inventory": item.id})

    if not remove_result.success:
        # Try to rollback
        accessor.update(item, {"location": actor_id})
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Failed to remove item from inventory: {remove_result.message}"
        )

    # Add to recipient's inventory
    add_result = accessor.update(recipient, {"+inventory": item.id})

    if not add_result.success:
        # Try to rollback
        accessor.update(giver, {"+inventory": item.id})
        accessor.update(item, {"location": actor_id})
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Failed to add item to recipient inventory: {add_result.message}"
        )

    # Use unified serializer for llm_context with trait randomization
    data = serialize_for_handler_result(item)

    return HandlerResult(
        success=True,
        message=f"You give the {item.name} to {recipient.name}.",
        data=data
    )


def handle_put(accessor, action):
    """
    Handle put/place command.

    Allows an actor to put an item from their inventory into/onto a container.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item to put (required)
            - indirect_object: Name of container (required)

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    container_name = action.get("indirect_object")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to put?"
        )

    if not container_name:
        return HandlerResult(
            success=False,
            message="Where do you want to put it?"
        )

    # Get the actor
    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Find item in actor's inventory
    item = find_item_in_inventory(accessor, object_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't have the {object_name}."
        )

    # Find container in current location
    location = accessor.get_current_location(actor_id)
    if not location:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Cannot find location for actor {actor_id}"
        )

    # Search for container
    container = None
    for i in accessor.game_state.items:
        if name_matches(container_name, i.name) and i.location == location.id:
            container = i
            break

    if not container:
        return HandlerResult(
            success=False,
            message=f"You don't see any {container_name} here."
        )

    # Check if target is a container
    container_props = container.properties.get("container")
    if not container_props:
        return HandlerResult(
            success=False,
            message=f"You can't put things in the {container.name}."
        )

    # Check if enclosed container is open
    is_surface = container_props.get("is_surface", False)
    if not is_surface and not container_props.get("open", False):
        return HandlerResult(
            success=False,
            message=f"The {container.name} is closed."
        )

    # Check capacity
    capacity = container_props.get("capacity", 0)
    if capacity > 0:
        current_count = sum(1 for i in accessor.game_state.items
                          if i.location == container.id)
        if current_count >= capacity:
            return HandlerResult(
                success=False,
                message=f"The {container.name} is full."
            )

    # Move item from inventory to container
    result = accessor.update(item, {"location": container.id}, verb="put", actor_id=actor_id)
    if not result.success:
        return HandlerResult(
            success=False,
            message=result.message or f"You can't put the {item.name} there."
        )

    # Remove from inventory
    if item.id in actor.inventory:
        actor.inventory.remove(item.id)

    # Build message based on container type
    preposition = "on" if is_surface else "in"
    base_message = f"You put the {item.name} {preposition} the {container.name}."

    # Use unified serializer for llm_context with trait randomization
    data = serialize_for_handler_result(item)

    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}", data=data)

    return HandlerResult(success=True, message=base_message, data=data)
