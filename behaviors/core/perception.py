"""Perception behaviors - examine/look.

Vocabulary and handlers for examining objects and surroundings.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import (
    find_accessible_item,
    find_door_with_adjective,
    find_exit_by_name,
    describe_location
)


# Vocabulary extension - adds perception verbs
vocabulary = {
    "verbs": [
        {
            "word": "look",
            "event": "on_look",
            "synonyms": ["l"],
            "object_required": "optional",
            "llm_context": {
                "traits": ["reveals details", "non-destructive", "provides information"],
                "without_object": "describes current surroundings",
                "state_variants": {
                    "detailed": "close inspection reveals hidden details",
                    "quick": "brief glance"
                }
            }
        },
        {
            "word": "examine",
            "event": "on_examine",
            "synonyms": ["inspect", "x"],
            "object_required": True,
            "llm_context": {
                "traits": ["reveals details", "non-destructive", "provides information"],
                "valid_objects": ["items", "doors", "exits"]
            }
        },
        {
            "word": "inventory",
            "event": "on_inventory",
            "synonyms": ["i", "inv"],
            "object_required": False,
            "llm_context": {
                "traits": ["shows carried items", "personal status"]
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}


def handle_look(accessor, action):
    """
    Handle look command.

    Shows the description of the current location and visible items.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")

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

    # Use shared utility to build location description
    message_parts = describe_location(accessor, location, actor_id)

    return HandlerResult(
        success=True,
        message="\n".join(message_parts)
    )


def handle_examine(accessor, action):
    """
    Handle examine command.

    Shows detailed description of an item or door.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to examine (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    adjective = action.get("adjective")
    # Direction can act as adjective (e.g., "examine east door")
    direction = action.get("direction")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to examine?"
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

    # Try to find an item first
    # Use direction as adjective if no explicit adjective (e.g., "examine east door")
    item_adjective = adjective or direction
    item = find_accessible_item(accessor, object_name, actor_id, item_adjective)

    if item:
        message_parts = [f"{item.name}: {item.description}"]

        # If item is a container, show its contents
        container_props = item.properties.get("container", {})
        if container_props:
            is_surface = container_props.get("is_surface", False)
            is_open = container_props.get("open", False)

            # Surface containers always show contents, enclosed only if open
            if is_surface or is_open:
                contents = []
                for other_item in accessor.game_state.items:
                    if other_item.location == item.id:
                        contents.append(other_item.name)

                if contents:
                    preposition = "On" if is_surface else "In"
                    message_parts.append(f"{preposition} the {item.name}: {', '.join(contents)}")
                elif is_surface:
                    message_parts.append(f"The {item.name} is empty.")
            elif not is_open and not is_surface:
                message_parts.append(f"The {item.name} is closed.")

        # Show light source state
        if item.properties.get("provides_light"):
            if item.states.get("lit"):
                message_parts.append("It is currently lit, casting a warm glow.")
            else:
                message_parts.append("It is currently unlit.")

        # Invoke entity behaviors (on_examine)
        result = accessor.update(item, {}, verb="examine", actor_id=actor_id)

        # Append behavior message if present
        if result.message:
            message_parts.append(result.message)

        # Include llm_context for LLM narration
        data = {}
        if item.llm_context:
            data["llm_context"] = item.llm_context

        return HandlerResult(
            success=True,
            message="\n".join(message_parts),
            data=data if data else None
        )

    # If no item found, try to find a door
    # Use direction as adjective if no explicit adjective provided (e.g., "examine east door")
    door_adjective = adjective or direction
    door = find_door_with_adjective(accessor, object_name, door_adjective, location.id)

    if door:
        # Include llm_context for doors too
        data = {}
        if door.llm_context:
            data["llm_context"] = door.llm_context

        return HandlerResult(
            success=True,
            message=f"{door.description}",
            data=data if data else None
        )

    # If no door found, try to find an exit
    # Use direction as adjective if no explicit adjective provided (e.g., "examine east exit")
    exit_adjective = adjective or direction
    exit_result = find_exit_by_name(accessor, object_name, actor_id, exit_adjective)

    if exit_result:
        exit_direction, exit_desc = exit_result

        # Build description from available fields
        if exit_desc.description:
            desc = exit_desc.description
        elif exit_desc.name:
            desc = f"A {exit_desc.name} leads {exit_direction}."
        else:
            desc = f"A passage leads {exit_direction}."

        # Include llm_context for exits
        data = {
            "exit_direction": exit_direction,
            "exit_type": exit_desc.type
        }
        if exit_desc.llm_context:
            data["llm_context"] = exit_desc.llm_context
        if exit_desc.door_id:
            data["door_id"] = exit_desc.door_id

        return HandlerResult(
            success=True,
            message=desc,
            data=data
        )

    return HandlerResult(
        success=False,
        message=f"You don't see any {object_name} here."
    )


def handle_inventory(accessor, action):
    """
    Handle inventory command.

    Shows items carried by the actor.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")

    # Get the actor
    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Get items in inventory
    if not actor.inventory:
        return HandlerResult(
            success=True,
            message="You are carrying nothing."
        )

    # Build list of item names
    item_names = []
    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item:
            item_names.append(item.name)

    if not item_names:
        return HandlerResult(
            success=True,
            message="Your inventory is empty."
        )

    return HandlerResult(
        success=True,
        message=f"You are carrying: {', '.join(item_names)}"
    )
