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
    find_lock_by_context,
    find_actor_by_name,
    format_inventory,
    describe_location,
    name_matches,
    is_observable
)
from utilities.location_serializer import serialize_location_for_llm
from utilities.entity_serializer import serialize_for_handler_result


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
                "valid_objects": ["items", "doors", "exits", "locks", "actors"]
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

    # Serialize location for LLM consumption
    llm_data = serialize_location_for_llm(accessor, location, actor_id)

    return HandlerResult(
        success=True,
        message="\n".join(message_parts),
        data=llm_data
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

        # Use unified serializer for llm_context with trait randomization
        data = serialize_for_handler_result(item)

        return HandlerResult(
            success=True,
            message="\n".join(message_parts),
            data=data
        )

    # If no item found, try to find a door
    # Use direction as adjective if no explicit adjective provided (e.g., "examine east door")
    door_adjective = adjective or direction
    door = find_door_with_adjective(accessor, object_name, door_adjective, location.id)

    if door:
        # Use unified serializer for llm_context with trait randomization
        data = serialize_for_handler_result(door)

        return HandlerResult(
            success=True,
            message=f"{door.description}",
            data=data
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

        # Use unified serializer for llm_context with trait randomization
        data = serialize_for_handler_result(exit_desc)
        # Add exit-specific fields
        data["exit_direction"] = exit_direction
        data["exit_type"] = exit_desc.type
        if exit_desc.door_id:
            data["door_id"] = exit_desc.door_id

        return HandlerResult(
            success=True,
            message=desc,
            data=data
        )

    # If no exit found, try to find a lock
    # Check if object_name matches "lock" (using vocabulary synonym matching)
    if name_matches(object_name, "lock"):
        # Extract indirect_object for "examine lock in door" pattern
        indirect_object = action.get("indirect_object")
        indirect_adjective = action.get("indirect_adjective")

        lock = find_lock_by_context(
            accessor,
            location_id=location.id,
            direction=direction,
            door_name=indirect_object,
            door_adjective=indirect_adjective,
            actor_id=actor_id
        )

        if lock:
            # Build lock description
            desc = lock.description if hasattr(lock, 'description') and lock.description else "A lock."

            # Use unified serializer for llm_context with trait randomization
            data = serialize_for_handler_result(lock)

            return HandlerResult(
                success=True,
                message=desc,
                data=data
            )

        # Lock lookup failed - provide helpful error message
        if direction:
            return HandlerResult(
                success=False,
                message=f"There's no lock to the {direction}."
            )
        elif indirect_object:
            return HandlerResult(
                success=False,
                message=f"You don't see any lock on that."
            )
        else:
            return HandlerResult(
                success=False,
                message="You don't see any lock here."
            )

    # Special case: redirect "examine player" to use "self"/"me"
    # Check BEFORE actor search to ensure consistent behavior regardless of player.name
    if name_matches(object_name, "player"):
        return HandlerResult(
            success=False,
            message="To examine yourself, use 'examine self' or 'examine me'. To examine another player, use their name (e.g., 'examine Blake' or 'examine Ayomide')."
        )

    # Try to find an actor
    target_actor = find_actor_by_name(accessor, object_name, actor_id)

    if target_actor:
        # Check observability (handles invisible actors)
        visible, reason = is_observable(
            target_actor, accessor, accessor.behavior_manager,
            actor_id=actor_id, method="examine"
        )
        if visible:
            message_parts = []
            is_self = (target_actor.id == actor_id)

            # Build description
            if is_self:
                # Self-examination
                if target_actor.description:
                    message_parts.append(target_actor.description)
                else:
                    message_parts.append("You examine yourself.")
            else:
                # Other actor examination
                if target_actor.description:
                    message_parts.append(f"{target_actor.name}: {target_actor.description}")
                else:
                    message_parts.append(f"You see {target_actor.name}.")

            # Show inventory using shared helper
            inv_message, inv_data = format_inventory(accessor, target_actor, for_self=is_self)
            if inv_message:
                message_parts.append(inv_message)

            # Invoke actor behaviors (on_examine)
            result = accessor.update(target_actor, {}, verb="examine", actor_id=actor_id)
            if result.message:
                message_parts.append(result.message)

            # Use unified serializer for llm_context with trait randomization
            data = serialize_for_handler_result(target_actor)

            return HandlerResult(
                success=True,
                message="\n".join(message_parts),
                data=data
            )
        # Invisible actor - fall through to "not found" message

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

    # Use shared format_inventory helper
    message, items_data = format_inventory(accessor, actor, for_self=True)

    if not message:
        return HandlerResult(
            success=True,
            message="You are carrying nothing."
        )

    return HandlerResult(
        success=True,
        message=message,
        data={"items": items_data}
    )
