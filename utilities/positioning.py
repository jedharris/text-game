"""
Positioning utilities for spatial structure.

Handles implicit positioning (automatic movement to entities).
Provides helper functions to reduce code duplication across handlers.
"""
from typing import Any, Optional, Tuple, List

from src.types import ActorId


def try_implicit_positioning(accessor, actor_id: ActorId, target_entity) -> Tuple[bool, Optional[str]]:
    """
    Handle implicit positioning for entity interaction.

    Always sets focused_on to target entity. If entity requires "near"
    interaction distance and actor is not already focused on it, also
    moves actor and returns movement message.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of actor attempting interaction
        target_entity: The entity being interacted with

    Returns:
        Tuple of (moved: bool, message: Optional[str])
        - moved: True if actor was moved (implicit movement occurred)
        - message: Movement message if moved, None otherwise

    Side effects:
        - Always sets actor.properties["focused_on"] to target entity ID
        - Clears actor.properties["posture"] if moving (not just focusing)
    """
    if not target_entity:
        return (False, None)

    # Get actor
    actor = accessor.get_actor(actor_id)  # Raises KeyError if not found

    # Check if already focused on this entity or its container
    current_focus = actor.properties.get("focused_on")
    already_focused = (current_focus == target_entity.id)

    # Also check if focused on the target's container (e.g., taking item from tree while climbing tree)
    focused_on_container = False
    if hasattr(target_entity, 'location') and current_focus == target_entity.location:
        focused_on_container = True

    # Get interaction distance (defaults to "any")
    distance = target_entity.properties.get("interaction_distance", "any")

    # If entity doesn't require "near", just update focus without movement
    # UNLESS we're focused on its container - then keep container focus
    if distance != "near":
        if not focused_on_container:
            # Update focus (even if same - keeps state consistent)
            actor.properties["focused_on"] = target_entity.id
        return (False, None)

    # Entity requires "near" - check if movement needed
    if already_focused:
        # Already positioned at this entity, no movement needed
        return (False, None)

    # Move actor to entity
    actor.properties["focused_on"] = target_entity.id

    # Clear posture when moving
    if "posture" in actor.properties:
        del actor.properties["posture"]

    # Generate movement message
    entity_name = target_entity.name if hasattr(target_entity, 'name') else "it"
    message = f"(You move closer to the {entity_name}.)"

    return (True, message)


def find_part_by_name(accessor, part_name, location_id: str):
    """
    Find part by name in a location.

    Searches for parts belonging to the location or items in the location.
    Supports WordEntry objects and vocabulary matching.

    Args:
        accessor: StateAccessor instance
        part_name: WordEntry or string name to search for
        location_id: Current location ID

    Returns:
        Part if found, None otherwise
    """
    from utilities.utils import name_matches
    from src.word_entry import WordEntry, WordType

    # Convert string to WordEntry if needed (parts are nouns)
    if isinstance(part_name, str):
        part_name = WordEntry(word=part_name, word_type=WordType.NOUN, synonyms=[])

    # Extract search string for fallback matching
    search_str = part_name.word if hasattr(part_name, 'word') else str(part_name)

    # Get all parts in location (parts of location itself)
    location_parts = accessor.get_parts_of(location_id)

    # Try matching with name_matches (handles synonyms and phrase matching by default)
    for part in location_parts:
        if name_matches(part_name, part.name):
            return part

    # Fallback: exact case-insensitive string match for multi-word phrases
    for part in location_parts:
        if part.name.lower() == search_str.lower():
            return part

    # Get all items in location (by checking item.location property)
    items_in_location = [item for item in accessor.game_state.items
                         if item.location == location_id]

    for item in items_in_location:
        # Check parts of each item
        item_parts = accessor.get_parts_of(item.id)

        for part in item_parts:
            if name_matches(part_name, part.name):
                return part

        # Fallback: exact case-insensitive string match
        for part in item_parts:
            if part.name.lower() == search_str.lower():
                return part

    return None


def find_and_position_item(accessor, actor_id: ActorId, object_name, adjective: Optional[str] = None) -> Tuple[Optional[Any], Optional[str]]:
    """
    Find accessible item and apply implicit positioning.

    Combines item lookup with positioning logic - the most common pattern
    across handlers (take, open, close, use, etc.).

    Args:
        accessor: StateAccessor instance
        actor_id: ID of actor attempting interaction
        object_name: WordEntry or string name of object
        adjective: Optional adjective for disambiguation

    Returns:
        Tuple of (item, position_message)
        - item: Found item or None
        - position_message: Movement message if positioned, None otherwise

    Example:
        item, move_msg = find_and_position_item(accessor, actor_id, object_name, adjective)
        if not item:
            return HandlerResult(success=False, primary="You don't see that here.")

        message_parts = []
        if move_msg:
            message_parts.append(move_msg)
        # ... continue with action
    """
    from utilities.utils import find_accessible_item

    # Find the item
    item = find_accessible_item(accessor, object_name, actor_id, adjective)
    if not item:
        return (None, None)

    # Apply implicit positioning
    moved, move_message = try_implicit_positioning(accessor, actor_id, item)

    return (item, move_message)


def find_and_position_part(accessor, actor_id: ActorId, object_name, location_id: str) -> Tuple[Optional[Any], Optional[str]]:
    """
    Find part and apply implicit positioning.

    Similar to find_and_position_item but for parts.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of actor attempting interaction
        object_name: WordEntry or string name of part
        location_id: Current location ID

    Returns:
        Tuple of (part, position_message)
        - part: Found part or None
        - position_message: Movement message if positioned, None otherwise
    """
    # Find the part
    part = find_part_by_name(accessor, object_name, location_id)
    if not part:
        return (None, None)

    # Apply implicit positioning
    moved, move_message = try_implicit_positioning(accessor, actor_id, part)

    return (part, move_message)


def build_message_with_positioning(
    base_messages: List[str],
    position_message: Optional[str]
) -> Tuple[str, List[str]]:
    """
    Build primary message and beats from action messages and positioning.

    Separates the core action statement (primary) from supplemental
    information (beats) for the narrator to weave together.

    Args:
        base_messages: List of message parts from the action.
                      First message is the primary action statement.
                      Additional messages are supplemental beats.
        position_message: Optional movement message from implicit positioning

    Returns:
        Tuple of (primary, beats):
        - primary: The core action statement (first base message)
        - beats: List of supplemental sentences (positioning + extra messages)

    Example:
        primary, beats = build_message_with_positioning(
            ["You picked up the key.", "It's cold to the touch."],
            "(You move closer to the desk.)"
        )
        # Returns: ("You picked up the key.", ["(You move closer to the desk.)", "It's cold to the touch."])
    """
    if not base_messages:
        return ("", [])

    primary = base_messages[0]
    beats: List[str] = []

    if position_message:
        beats.append(position_message)

    # Additional base messages become beats
    if len(base_messages) > 1:
        beats.extend(base_messages[1:])

    return (primary, beats)
