"""
Handler utility functions.

Provides shared preamble utilities for item-targeting handlers.
"""

from typing import Tuple, Optional, Dict, Any, List, Union, cast

from src.types import ActorId
from src.state_accessor import HandlerResult, StateAccessor, UpdateResult
from src.state_manager import Entity, Item, Actor, Lock
from src.word_entry import WordEntry
from utilities.utils import find_accessible_item, find_door_with_adjective
from utilities.entity_serializer import serialize_for_handler_result
from utilities.positioning import build_message_with_positioning


def validate_actor_and_location(
    accessor: StateAccessor,
    action: Dict[str, Any],
    require_object: bool = True,
    require_direction: bool = False,
    require_indirect_object: bool = False
) -> Tuple[Optional[ActorId], Optional[Any], Optional[Any], Optional[HandlerResult]]:
    """
    Standard handler preamble: validates actor, location, and required action fields.

    Args:
        accessor: StateAccessor instance
        action: Action dictionary from parser
        require_object: If True, validates 'object' field is present
        require_direction: If True, validates 'direction' field is present
        require_indirect_object: If True, validates 'indirect_object' field is present

    Returns:
        Tuple of (actor_id, actor, location, error_result):
        - If valid: (actor_id, actor, location, None)
        - If error: (None, None, None, HandlerResult with error message)

    Example:
        actor_id, actor, location, error = validate_actor_and_location(
            accessor, action, require_object=True
        )
        if error:
            return error

        # Continue with handler logic using actor_id, actor, location
    """
    # Extract actor_id with default
    actor_id = cast(ActorId, action.get("actor_id") or ActorId("player"))

    # Validate required fields
    verb = action.get("verb", "do something")

    if require_object and not action.get("object"):
        return None, None, None, HandlerResult(
            success=False,
            primary=f"What do you want to {verb}?"
        )

    if require_direction and not action.get("direction"):
        return None, None, None, HandlerResult(
            success=False,
            primary="Which direction do you want to go?"
        )

    if require_indirect_object and not action.get("indirect_object"):
        # Context-specific message based on verb
        if verb == "put":
            return None, None, None, HandlerResult(
                success=False,
                primary="Where do you want to put it?"
            )
        elif verb == "give":
            return None, None, None, HandlerResult(
                success=False,
                primary="Give it to whom?"
            )
        else:
            obj_name = get_display_name(action.get("object"))
            return None, None, None, HandlerResult(
                success=False,
                primary=f"What do you want to {verb} {obj_name} with?"
            )

    # Validate actor exists
    actor = accessor.get_actor(actor_id)
    if not actor:
        return None, None, None, HandlerResult(
            success=False,
            primary=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Validate location exists
    location = accessor.get_current_location(actor_id)
    if not location:
        return None, None, None, HandlerResult(
            success=False,
            primary=f"INCONSISTENT STATE: Cannot find location for actor {actor_id}"
        )

    return actor_id, actor, location, None


def get_object_word(object_name: Optional[WordEntry]) -> Optional[str]:
    """
    Extract the word string from a WordEntry.

    Args:
        object_name: WordEntry or None (from action.get("object"))

    Returns:
        The lowercase word string, or None if object_name is None
    """
    if object_name is None:
        return None
    return object_name.word.lower()


def get_display_name(object_name: Optional[WordEntry]) -> str:
    """
    Extract a display-friendly name from a WordEntry.

    Args:
        object_name: WordEntry or None (from action.get("object"))

    Returns:
        The word string suitable for display in messages
    """
    if object_name is None:
        return "something"
    return object_name.word


def find_action_target(
    accessor,
    action: Dict[str, Any]
) -> Tuple[Optional[Any], Optional[HandlerResult]]:
    """
    Standard preamble for item-targeting handlers.

    Extracts actor_id, object, adjective from action.
    Validates actor exists.
    Finds accessible item using adjective for disambiguation.

    The verb in action["verb"] is used for error messages and is the
    canonical form from the parser/vocabulary.

    Args:
        accessor: StateAccessor instance
        action: Action dict containing:
            - verb: Canonical verb from parser (required for messages)
            - actor_id: Actor performing action (default: "player")
            - object: Name of target object
            - adjective: Optional adjective for disambiguation

    Returns:
        Tuple of (item, error_result):
        - If item found: (item, None)
        - If error: (None, HandlerResult with error message)
    """
    actor_id = cast(ActorId, action.get("actor_id") or ActorId("player"))
    object_name = action.get("object")
    adjective = action.get("adjective")
    verb = action.get("verb", "interact with")

    if not object_name:
        return None, HandlerResult(
            success=False,
            primary=f"What do you want to {verb}?"
        )

    actor = accessor.get_actor(actor_id)
    if not actor:
        return None, HandlerResult(
            success=False,
            primary=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    item = find_accessible_item(accessor, object_name, actor_id, adjective)
    if not item:
        return None, HandlerResult(
            success=False,
            primary=f"You don't see any {get_display_name(object_name)} here."
        )

    return item, None


def find_openable_target(
    accessor,
    action: Dict[str, Any],
    verb: str
) -> Tuple[Optional[Any], Optional[ActorId], Optional[HandlerResult]]:
    """
    Shared preamble for door/container handlers (open, close, lock, unlock).

    Extracts actor_id, object, adjective from action.
    Validates actor exists.
    Performs smart door selection when object_word == "door".
    Falls back to general item search.

    Args:
        accessor: StateAccessor instance
        action: Action dict containing:
            - actor_id: Actor performing action (default: "player")
            - object: Name of target object
            - adjective: Optional adjective for disambiguation
        verb: The verb being performed (e.g., "open", "close", "lock", "unlock")
              Used for error messages and smart door selection.

    Returns:
        Tuple of (item, actor_id, error_result):
        - If item found: (item, actor_id, None)
        - If error: (None, actor_id, HandlerResult with error message)
    """
    actor_id = cast(ActorId, action.get("actor_id") or ActorId("player"))
    object_name = action.get("object")
    adjective = action.get("adjective")

    if not object_name:
        return None, actor_id, HandlerResult(
            success=False,
            primary=f"What do you want to {verb}?"
        )

    actor = accessor.get_actor(actor_id)
    if not actor:
        return None, actor_id, HandlerResult(
            success=False,
            primary=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Get current location for door searches
    location = accessor.get_current_location(actor_id)
    location_id = location.id if location else None

    # For door-related searches, use smart door selection
    item = None
    object_word = get_object_word(object_name)
    if object_word == "door" and location_id:
        item = find_door_with_adjective(
            accessor, object_name, adjective, location_id,
            actor_id=actor_id, verb=verb
        )

    # Fall back to general item search
    if not item:
        item = find_accessible_item(accessor, object_name, actor_id, adjective)

    if not item:
        return None, actor_id, HandlerResult(
            success=False,
            primary=f"You don't see any {get_display_name(object_name)} here."
        )

    return item, actor_id, None


# =============================================================================
# Action Execution Helpers
# =============================================================================

def execute_entity_action(
    accessor: StateAccessor,
    entity: Entity,
    changes: Dict[str, Any],
    verb: str,
    actor_id: ActorId,
    base_message: str,
    positioning_msg: Optional[str] = None,
    failure_message: Optional[str] = None
) -> HandlerResult:
    """
    Execute an action on an entity with behavior invocation and message building.

    This helper handles the common pattern of:
    1. Calling accessor.update() with verb/actor_id to invoke behaviors
    2. Checking for failure and returning appropriate error
    3. Building success message with behavior result appended
    4. Building beats from positioning and behavior messages
    5. Serializing entity for llm_context

    Args:
        accessor: StateAccessor instance
        entity: The entity to act upon (Item, Actor, Part, etc.)
        changes: Dict of state changes to apply (can be empty {} for behavior-only)
        verb: The verb for behavior invocation (e.g., "examine", "open")
        actor_id: ID of actor performing the action
        base_message: Success message (e.g., "You open the chest.")
        positioning_msg: Optional positioning message to add to beats
        failure_message: Optional custom failure message (defaults to behavior message)

    Returns:
        HandlerResult with primary, beats, and serialized data
    """
    result = accessor.update(entity, changes, verb=verb, actor_id=actor_id)

    if not result.success:
        msg = failure_message or result.detail or f"You can't {verb} the {getattr(entity, 'name', 'that')}."
        return HandlerResult(success=False, primary=msg)

    # Build primary and beats
    base_messages = [base_message]
    if result.detail:
        base_messages.append(result.detail)

    primary, beats = build_message_with_positioning(base_messages, positioning_msg)
    data = serialize_for_handler_result(entity)

    return HandlerResult(success=True, primary=primary, beats=beats, data=data)


# =============================================================================
# Inventory Transfer Helpers
# =============================================================================

def transfer_item_to_actor(
    accessor: StateAccessor,
    item: Item,
    actor: Actor,
    actor_id: ActorId,
    verb: str,
    item_changes: Dict[str, Any],
    rollback_location: str
) -> Tuple[Optional[UpdateResult], Optional[HandlerResult]]:
    """
    Transfer an item to an actor's inventory with rollback on failure.

    Handles:
    - Update item with changes (triggers behaviors via verb)
    - Add item to actor's inventory
    - Rollback item location if inventory update fails

    Args:
        accessor: StateAccessor instance
        item: The item to transfer
        actor: The actor receiving the item
        actor_id: ID of the actor (for behavior context)
        verb: The verb for behavior invocation (e.g., "take")
        item_changes: Changes to apply to item (typically {"location": actor_id})
        rollback_location: Location to restore item to if inventory update fails

    Returns:
        Tuple of (update_result, error):
        - On success: (UpdateResult with behavior message, None)
        - On failure: (None, HandlerResult with error)
    """
    # Update item (triggers behaviors)
    result = accessor.update(item, item_changes, verb=verb, actor_id=actor_id)

    if not result.success:
        return None, HandlerResult(success=False, primary=result.detail or f"Cannot {verb} the {item.name}.")

    # Add to inventory
    inv_result = accessor.update(actor, {"+inventory": item.id})

    if not inv_result.success:
        # Rollback item location
        accessor.update(item, {"location": rollback_location})
        return None, HandlerResult(
            success=False,
            primary=f"INCONSISTENT STATE: Failed to add item to inventory: {inv_result.detail}"
        )

    return result, None


def transfer_item_from_actor(
    accessor: StateAccessor,
    item: Item,
    actor: Actor,
    actor_id: ActorId,
    verb: str,
    item_changes: Dict[str, Any]
) -> Tuple[Optional[UpdateResult], Optional[HandlerResult]]:
    """
    Transfer an item from an actor's inventory with rollback on failure.

    Handles:
    - Update item with changes (triggers behaviors via verb)
    - Remove item from actor's inventory
    - Rollback item location if inventory update fails

    Args:
        accessor: StateAccessor instance
        item: The item to transfer
        actor: The actor giving up the item
        actor_id: ID of the actor (for behavior context)
        verb: The verb for behavior invocation (e.g., "drop", "put")
        item_changes: Changes to apply to item (typically {"location": new_location})

    Returns:
        Tuple of (update_result, error):
        - On success: (UpdateResult with behavior message, None)
        - On failure: (None, HandlerResult with error)
    """
    # Update item (triggers behaviors)
    result = accessor.update(item, item_changes, verb=verb, actor_id=actor_id)

    if not result.success:
        return None, HandlerResult(success=False, primary=result.detail or f"Cannot {verb} the {item.name}.")

    # Remove from inventory
    inv_result = accessor.update(actor, {"-inventory": item.id})

    if not inv_result.success:
        # Rollback item location
        accessor.update(item, {"location": actor_id})
        return None, HandlerResult(
            success=False,
            primary=f"INCONSISTENT STATE: Failed to remove item from inventory: {inv_result.detail}"
        )

    return result, None


# =============================================================================
# Validation Helpers
# =============================================================================

def validate_container_accessible(
    container: Item,
    verb: str
) -> Optional[HandlerResult]:
    """
    Validate that a container can be accessed (is open or is a surface).

    Args:
        container: The container item to check
        verb: The verb for error messages (e.g., "take from", "put in")

    Returns:
        None if accessible, HandlerResult error if container is closed
    """
    container_info = container.properties.get("container", {})
    is_surface = container_info.get("is_surface", False)

    if not is_surface and not container_info.get("open", False):
        return HandlerResult(
            success=False,
            primary=f"The {container.name} is closed."
        )

    return None


def check_actor_has_key(
    actor: Actor,
    lock: Lock,
    item_name: str,
    verb: str
) -> Optional[HandlerResult]:
    """
    Check if actor has a key that opens the given lock.

    Args:
        actor: The actor to check inventory of
        lock: The lock to check keys for
        item_name: Name of the locked item (for error message)
        verb: The verb being performed (for error message)

    Returns:
        None if actor has a valid key, HandlerResult error if not
    """
    opens_with = lock.properties.get("opens_with", [])
    has_key = any(key_id in actor.inventory for key_id in opens_with)

    if not has_key:
        return HandlerResult(
            success=False,
            primary=f"You don't have the right key to {verb} the {item_name}."
        )

    return None


# =============================================================================
# Message Building Helpers
# =============================================================================

def build_action_result(
    item: Item,
    primary: str,
    beats: Optional[List[str]] = None,
    data: Optional[Dict[str, Any]] = None
) -> HandlerResult:
    """
    Build a successful HandlerResult with primary message, beats, and entity data.

    Args:
        item: The item to serialize for llm_context
        primary: The core action statement (e.g., "You pick up the sword.")
        beats: Optional list of supplemental sentences
               (e.g., ["You step down from the table.", "It's cold to the touch."])
        data: Optional extra data. If not provided, serializes the item.

    Returns:
        HandlerResult with primary, beats, and serialized data
    """
    return HandlerResult(
        success=True,
        primary=primary,
        beats=beats or [],
        data=data if data is not None else serialize_for_handler_result(item)
    )
