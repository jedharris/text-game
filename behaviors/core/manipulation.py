"""Manipulation behaviors - take and drop.

Vocabulary and handlers for basic item manipulation.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item, find_item_in_inventory


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

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

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

    # Find the item (uses actor_id to search actor's location and inventory)
    item = find_accessible_item(accessor, object_name, actor_id)

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

    result = accessor.update(item, changes)

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

    return HandlerResult(
        success=True,
        message=f"You take the {item.name}."
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

    result = accessor.update(item, changes)

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

    return HandlerResult(
        success=True,
        message=f"You drop the {item.name}."
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
        if other_actor.location == location.id and other_actor.name.lower() == recipient_name.lower():
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

    return HandlerResult(
        success=True,
        message=f"You give the {item.name} to {recipient.name}."
    )
