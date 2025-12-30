"""Manipulation behaviors - take and drop.

Vocabulary and handlers for basic item manipulation.
"""

from src.state_accessor import HandlerResult
from src.word_entry import WordEntry
from utilities.utils import (
    find_accessible_item,
    find_item_in_inventory,
    find_item_in_container,
    name_matches,
)
from utilities.positioning import try_implicit_positioning
from utilities.handler_utils import (
    get_display_name,
    validate_actor_and_location,
    transfer_item_to_actor,
    transfer_item_from_actor,
    find_and_validate_container,
    build_action_result,
)


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
        },
        {
            "word": "remove",
            "event": "on_remove",
            "synonyms": ["take off", "doff", "put down", "put away", "unequip"],
            "object_required": True,
            "narration_mode": "brief",
            "llm_context": {
                "traits": ["unequips equipped item", "removes worn/wielded gear"],
                "failure_narration": {
                    "not_equipped": "not currently equipped",
                    "not_holding": "not carrying that"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": []
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
    # Validate actor and location
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    # Extract remaining action parameters
    object_name = action.get("object")
    if not isinstance(object_name, WordEntry):
        return HandlerResult(success=False, primary="I didn't understand what to drop.")
    if not isinstance(object_name, WordEntry):
        return HandlerResult(success=False, primary="I didn't understand what to take.")
    adjective = action.get("adjective")
    container_name = action.get("indirect_object")
    if container_name is not None and not isinstance(container_name, WordEntry):
        return HandlerResult(
            success=False,
            primary="I didn't understand which container you meant."
        )
    container_adjective = action.get("indirect_adjective")

    # If container specified, validate it and search only within it
    container = None
    if container_name:
        container, error = find_and_validate_container(
            accessor, container_name, container_adjective, location.id, "take from"
        )
        if error:
            return error

        # Find item in this specific container
        container_info = container.properties.get("container", {})
        is_surface = container_info.get("is_surface", False)
        item = find_item_in_container(accessor, object_name, container.id, adjective)
        if not item:
            preposition = "on" if is_surface else "in"
            return HandlerResult(
                success=False,
                primary=f"You don't see any {get_display_name(object_name)} {preposition} the {container.name}."
            )
    else:
        # No container specified - find item anywhere accessible
        item = find_accessible_item(accessor, object_name, actor_id, adjective)

    if not item:
        return HandlerResult(
            success=False,
            primary=f"You don't see any {get_display_name(object_name)} here."
        )

    # Apply implicit positioning (to container if specified, else to item)
    target_for_positioning = container if container_name else item
    moved, move_msg = try_implicit_positioning(accessor, actor_id, target_for_positioning)

    # Check if item is already in actor's inventory
    if item.location == actor_id:
        return HandlerResult(
            success=True,
            primary=f"You already have the {item.name}."
        )

    # Check if item is portable
    if not item.portable:
        return HandlerResult(
            success=False,
            primary=f"You can't take the {item.name}."
        )

    # Transfer item to actor's inventory
    result, error = transfer_item_to_actor(
        accessor, item, actor, actor_id, "take",
        {"location": actor_id},
        location.id
    )
    if error:
        return error

    return build_action_result(
        item,
        f"You take the {item.name}.",
        beats=[move_msg, result.detail],
        accessor=accessor,
        actor_id=actor_id
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
            primary=f"You don't have any {get_display_name(object_name)}."
        )

    # Transfer item from actor's inventory to location
    result, error = transfer_item_from_actor(
        accessor, item, actor, actor_id, "drop",
        {"location": location.id, "states.equipped": False}
    )
    if error:
        return error

    # Build and return result
    beats = [result.detail] if result.detail else None
    return build_action_result(
        item,
        f"You drop the {item.name}.",
        beats=beats,
        accessor=accessor,
        actor_id=actor_id
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
    # Validate actor and location
    actor_id, giver, location, error = validate_actor_and_location(
        accessor, action, require_object=True, require_indirect_object=True
    )
    if error:
        return error

    object_name = action.get("object")
    if not isinstance(object_name, WordEntry):
        return HandlerResult(success=False, primary="I didn't understand what to give.")
    recipient_name = action.get("indirect_object")
    if not isinstance(recipient_name, WordEntry):
        return HandlerResult(success=False, primary="I didn't catch who should receive it.")

    # Find the item in giver's inventory
    item = find_item_in_inventory(accessor, object_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            primary=f"You don't have any {get_display_name(object_name)}."
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
            primary=f"You don't see any {get_display_name(recipient_name)} here."
        )

    # Step 1: Transfer item from giver's inventory
    # Note: We use give verb here but changes go to recipient location
    result, error = transfer_item_from_actor(
        accessor, item, giver, actor_id, "give",
        {"location": recipient.id, "states.equipped": False}
    )
    if error:
        return error

    # Step 2: Add to recipient's inventory
    add_result = accessor.update(recipient, {"+inventory": item.id})
    if not add_result.success:
        # Rollback: put item back in giver's inventory
        accessor.update(giver, {"+inventory": item.id})
        accessor.update(item, {"location": actor_id})
        return HandlerResult(
            success=False,
            primary=f"INCONSISTENT STATE: Failed to add item to recipient inventory: {add_result.detail}"
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

    # Build beats from behavior messages
    return build_action_result(
        item,
        base_message,
        beats=[result.detail, receive_result.feedback if receive_result else None],
        accessor=accessor,
        actor_id=actor_id
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
    # Validate actor and location
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True, require_indirect_object=True
    )
    if error:
        return error

    object_name = action.get("object")
    if not isinstance(object_name, WordEntry):
        return HandlerResult(success=False, primary="I didn't understand what to put.")
    container_name = action.get("indirect_object")
    if not isinstance(container_name, WordEntry):
        return HandlerResult(success=False, primary="I didn't catch where to put it.")
    container_adjective = action.get("indirect_adjective")

    # Find item in actor's inventory
    item = find_item_in_inventory(accessor, object_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            primary=f"You don't have the {get_display_name(object_name)}."
        )

    # Find and validate container
    container, error = find_and_validate_container(
        accessor, container_name, container_adjective, location.id, "put in"
    )
    if error:
        return error

    container_props = container.properties.get("container")

    # Check capacity
    is_surface = container_props.get("is_surface", False)
    capacity = container_props.get("capacity", 0)
    if capacity > 0:
        current_count = sum(1 for i in accessor.game_state.items
                          if i.location == container.id)
        if current_count >= capacity:
            return HandlerResult(
                success=False,
                primary=f"The {container.name} is full."
            )

    # Transfer item from actor's inventory to container
    result, error = transfer_item_from_actor(
        accessor, item, actor, actor_id, "put",
        {"location": container.id}
    )
    if error:
        return error

    # Build message based on container type
    preposition = "on" if is_surface else "in"
    beats = [result.detail] if result.detail else None
    return build_action_result(
        item,
        f"You put the {item.name} {preposition} the {container.name}.",
        beats=beats,
        accessor=accessor,
        actor_id=actor_id
    )


def handle_remove(accessor, action):
    """
    Handle remove/unequip command.

    Allows an actor to unequip an equipped item from their inventory.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item to remove (required)

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
    if not isinstance(object_name, WordEntry):
        return HandlerResult(success=False, primary="I didn't understand what to remove.")

    # Find the item in actor's inventory
    item = find_item_in_inventory(accessor, object_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            primary=f"You don't have any {get_display_name(object_name)}."
        )

    # Check if item is equippable (can't remove non-equippable items)
    if not item.properties.get("equippable", False):
        return HandlerResult(
            success=False,
            primary=f"The {item.name} is not something you can unequip."
        )

    # Check if item is equipped
    is_equipped = item.states.get("equipped", False)
    if not is_equipped:
        return HandlerResult(
            success=True,
            primary=f"The {item.name} is not currently equipped."
        )

    # Unequip the item
    result = accessor.update(item, {"states.equipped": False})
    if not result.success:
        return HandlerResult(
            success=False,
            primary=f"Failed to unequip the {item.name}: {result.detail}"
        )

    # Build and return result
    beats = [result.detail] if result.detail else None
    return build_action_result(
        item,
        f"You unequip the {item.name}.",
        beats=beats,
        accessor=accessor,
        actor_id=actor_id
    )
