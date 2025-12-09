"""Manipulation behaviors - take and drop.

Vocabulary and handlers for basic item manipulation.
"""

from typing import Dict, Any, TYPE_CHECKING

from src.action_types import ActionDict
from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult

if TYPE_CHECKING:
    from src.state_accessor import StateAccessor
from utilities.utils import (
    find_accessible_item,
    find_item_in_inventory,
    find_container_with_adjective,
    find_item_in_container,
    name_matches,
)
from utilities.entity_serializer import serialize_for_handler_result
from utilities.positioning import try_implicit_positioning, build_message_with_positioning
from utilities.handler_utils import get_display_name, validate_actor_and_location


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
            "narration_mode": "brief",
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
            "fallback_event": "on_drop",
            "synonyms": ["set"],
            "object_required": True,
            "narration_mode": "brief",
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
    "adjectives": []
}


def handle_take(accessor: "StateAccessor", action: Dict[str, Any]) -> HandlerResult:
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
    # Validate actor and location
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    # Extract remaining action parameters and ensure WordEntry
    object_name = action.get("object")
    adjective = action.get("adjective")
    container_name = action.get("indirect_object")
    container_adjective = action.get("indirect_adjective")

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
                message=f"You don't see any {get_display_name(container_name)} here."
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
                message=f"You don't see any {get_display_name(object_name)} {preposition} the {container.name}."
            )
    else:
        # No container specified - find item anywhere accessible
        # Use adjective if provided for disambiguation
        item = find_accessible_item(accessor, object_name, actor_id, adjective)

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {get_display_name(object_name)} here."
        )

    # Apply implicit positioning
    # For container operations, position to container not item
    if container_name:
        moved, move_msg = try_implicit_positioning(accessor, actor_id, container)
    else:
        moved, move_msg = try_implicit_positioning(accessor, actor_id, item)

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
        # Behavior denied the action - this is normal, not an inconsistent state
        return HandlerResult(
            success=False,
            message=result.message
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
    base_messages = [f"You take the {item.name}."]
    if result.message:
        base_messages.append(result.message)

    # Combine with positioning message
    message = build_message_with_positioning(base_messages, move_msg)

    # Use unified serializer for llm_context with trait randomization
    data = serialize_for_handler_result(item)

    return HandlerResult(
        success=True,
        message=message,
        data=data
    )


def handle_drop(accessor: "StateAccessor", action: Dict[str, Any]) -> HandlerResult:
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
    # Validate actor and location
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    object_name = action.get("object")

    # Find the item in actor's inventory
    item = find_item_in_inventory(accessor, object_name, actor_id)

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't have any {get_display_name(object_name)}."
        )

    # Perform state changes
    # 1. Change item location to current room
    # 2. Remove item from actor's inventory
    # 3. Clear equipped state (item is no longer being carried)
    changes = {
        "location": location.id,
        "states.equipped": False
    }

    # Pass verb and actor_id to trigger entity behaviors (on_drop)
    result = accessor.update(item, changes, verb="drop", actor_id=actor_id)

    if not result.success:
        # Behavior denied the action - this is normal, not an inconsistent state
        return HandlerResult(
            success=False,
            message=result.message
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


def handle_give(accessor: "StateAccessor", action: Dict[str, Any]) -> HandlerResult:
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
    # Validate actor and location
    actor_id, giver, location, error = validate_actor_and_location(
        accessor, action, require_object=True, require_indirect_object=True
    )
    if error:
        return error

    object_name = action.get("object")
    recipient_name = action.get("indirect_object")

    # Find the item in giver's inventory
    item = find_item_in_inventory(accessor, object_name, actor_id)

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't have any {get_display_name(object_name)}."
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
            message=f"You don't see any {get_display_name(recipient_name)} here."
        )

    # Perform state changes
    # 1. Change item location to recipient
    # 2. Remove item from giver's inventory
    # 3. Add item to recipient's inventory
    # 4. Clear equipped state (item is changing hands)
    changes = {
        "location": recipient.id,
        "states.equipped": False
    }

    result = accessor.update(item, changes)

    if not result.success:
        # Behavior denied the action - this is normal, not an inconsistent state
        return HandlerResult(
            success=False,
            message=result.message
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

    # Build base message
    base_message = f"You give the {item.name} to {recipient.name}."

    # Invoke recipient's on_receive_item behavior (for trades/services)
    receive_context = {
        "item_id": item.id,
        "item": item,
        "giver_id": actor_id
    }
    receive_result = accessor.behavior_manager.invoke_behavior(
        recipient, "on_receive_item", accessor, receive_context
    )
    if receive_result and receive_result.message:
        message = f"{base_message}\n{receive_result.message}"
    else:
        message = base_message

    # Use unified serializer for llm_context with trait randomization
    data = serialize_for_handler_result(item)

    return HandlerResult(
        success=True,
        message=message,
        data=data
    )


def handle_put(accessor: "StateAccessor", action: Dict[str, Any]) -> HandlerResult:
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
    # Validate actor and location
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True, require_indirect_object=True
    )
    if error:
        return error

    object_name = action.get("object")
    container_name = action.get("indirect_object")

    # Find item in actor's inventory
    item = find_item_in_inventory(accessor, object_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't have the {get_display_name(object_name)}."
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
            message=f"You don't see any {get_display_name(container_name)} here."
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
