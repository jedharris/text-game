"""Perception behaviors - examine/look.

Vocabulary and handlers for examining objects and surroundings.
"""

from typing import Dict, Any, cast

from src.action_types import ActionDict
from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from src.types import ActorId
from utilities.utils import (
    find_accessible_item,
    find_door_with_adjective,
    find_exit_by_name,
    find_lock_by_context,
    find_actor_by_name,
    format_inventory,
    describe_location,
    name_matches,
    is_observable,
)
from utilities.location_serializer import serialize_location_for_llm
from utilities.entity_serializer import serialize_for_handler_result
from utilities.positioning import (
    try_implicit_positioning,
    find_part_by_name,
    find_and_position_item,
    find_and_position_part,
    build_message_with_positioning
)
from utilities.handler_utils import get_display_name, validate_actor_and_location


# Vocabulary extension - adds perception verbs
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "entity_visibility_check",
            "invocation": "entity",
            "description": "Called to check if an entity is visible"
        }
    ],
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
            "narration_mode": "brief",
            "llm_context": {
                "traits": ["shows carried items", "personal status"]
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "events": [
        {
            "event": "on_observe",
            "hook": "entity_visibility_check",
            "description": "Called to check if entity is visible. "
                          "Return allow=False to hide entity."
        }
    ]
}


def handle_look(accessor, action):
    """
    Handle look command.

    If object is provided, redirects to examine behavior.
    Otherwise, shows the description of the current location and visible items.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Optional object to look at (redirects to examine)

    Returns:
        HandlerResult with success flag and message
    """
    # If object specified, redirect to examine
    object_name = action.get("object")
    if object_name:
        return handle_examine(accessor, action)

    # Validate actor and location
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=False
    )
    if error:
        return error

    # Use shared utility to build location description
    message_parts = describe_location(accessor, location, actor_id)

    # Serialize location for LLM consumption
    llm_data = serialize_location_for_llm(accessor, location, actor_id)

    return HandlerResult(
        success=True,
        primary="\n".join(message_parts),
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
    # Validate actor and location
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error
    verb = action.get("verb", "examine")

    object_name = action.get("object")
    adjective = action.get("adjective")
    # Direction can act as adjective (e.g., "examine east door")
    direction = action.get("direction")

    # Try to find an item first
    # Use direction as adjective if no explicit adjective (e.g., "examine east door")
    item_adjective = adjective or direction
    item = find_accessible_item(accessor, object_name, actor_id, item_adjective)

    if item:
        # Special handling for doors: use exit description if available
        if item.is_door:
            from utilities.utils import find_exit_for_door
            exit_entity = find_exit_for_door(accessor, item.id, location.id, actor_id)

            if exit_entity:
                # CRITICAL: Closed doors should NOT reveal what's beyond them
                # Only open doors can show passage information
                if item.door_open:
                    # Open door - describe the door AND the passage beyond
                    passage = exit_entity.passage if hasattr(exit_entity, 'passage') and exit_entity.passage else None
                    if passage:
                        # Combine door description + passage description
                        desc = f"{item.description} Beyond it, {passage}."
                    else:
                        # No passage info, just use exit description
                        desc = exit_entity.description if exit_entity.description else item.description
                else:
                    # Closed door - use only the door's description (player can't see through it)
                    desc = item.description

                data = serialize_for_handler_result(exit_entity, accessor, actor_id)
                # Add door state as context for testing/debugging
                context = {
                    "is_door": True,
                    "door_state": {
                        "open": item.door_open,
                        "locked": item.door_locked
                    }
                }

                return HandlerResult(
                    success=True,
                    primary=desc,
                    data=data,
                    context=context
                )

        # Normal item handling (non-doors or doors not part of exits)
        # Try implicit positioning
        moved, move_message = try_implicit_positioning(accessor, actor_id, item)

        message_parts = []
        if move_message:
            message_parts.append(move_message)

        # Don't include item name in primary text - it's already in entity_refs
        # Including it creates redundancy that leads to "ball ball" type errors
        message_parts.append(item.description)

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
        if result.detail:
            message_parts.append(result.detail)

        # Check for examine_reactions handler in item properties
        examine_reactions = item.properties.get("examine_reactions", {})
        handler_path = examine_reactions.get("handler")
        if handler_path:
            handler = accessor.behavior_manager.load_behavior(handler_path)
            if handler:
                context = {"target": item}
                reaction_result = handler(item, accessor, context)
                if reaction_result.feedback:
                    message_parts.append(reaction_result.feedback)

        # Use unified serializer for llm_context with trait randomization
        data = serialize_for_handler_result(item, accessor, actor_id)

        # If player has a posture (on_surface, climbing, etc.), include that entity too
        # so narrator has context about player's position
        posture = actor.properties.get("posture")
        posture_entity_id = actor.properties.get("posture_entity")
        if posture and posture_entity_id and posture_entity_id != item.id:
            # Include the posture entity (bench, tree, etc.) in entity_refs
            posture_entity = accessor.get_item(posture_entity_id)
            if posture_entity:
                # Add as additional entity in nested structure
                if "items" not in data:
                    data["items"] = []
                posture_data = serialize_for_handler_result(posture_entity, accessor, actor_id)
                data["items"].append(posture_data)

        return HandlerResult(
            success=True,
            primary="\n".join(message_parts),
            data=data
        )

    # If no item found, try to find a part
    part = find_part_by_name(accessor, object_name, location.id)

    if part:
        # Try implicit positioning
        moved, move_message = try_implicit_positioning(accessor, actor_id, part)

        message_parts = []
        if move_message:
            message_parts.append(move_message)

        # Add part description
        part_desc = part.properties.get("description", f"A {part.name}.")
        message_parts.append(f"{part.name}: {part_desc}")

        # List items at this part
        items_at_part = accessor.get_items_at_part(part.id)
        if items_at_part:
            item_names = [item.name for item in items_at_part]
            message_parts.append(f"On the {part.name}: {', '.join(item_names)}")

        # Invoke part behaviors (on_examine)
        result = accessor.update(part, {}, verb="examine", actor_id=actor_id)
        if result.detail:
            message_parts.append(result.detail)

        # Check for examine_reactions handler in part properties
        examine_reactions = part.properties.get("examine_reactions", {})
        handler_path = examine_reactions.get("handler")
        if handler_path:
            handler = accessor.behavior_manager.load_behavior(handler_path)
            if handler:
                context = {"target": part}
                reaction_result = handler(part, accessor, context)
                if reaction_result.feedback:
                    message_parts.append(reaction_result.feedback)

        # Use unified serializer for llm_context
        data = serialize_for_handler_result(part, accessor, actor_id)

        return HandlerResult(
            success=True,
            primary="\n".join(message_parts),
            data=data
        )

    # If no item or part found, try to find a door
    # Use direction as adjective if no explicit adjective provided (e.g., "examine east door")
    door_adjective = adjective or direction
    door = find_door_with_adjective(accessor, object_name, door_adjective, location.id, actor_id, verb=verb)

    if door:
        # Check if this door is part of a visible exit
        # If so, use the exit's perspective-aware description instead of the door's generic one
        from utilities.utils import find_exit_for_door
        exit_entity = find_exit_for_door(accessor, door.id, location.id, actor_id)

        if exit_entity:
            # CRITICAL: Closed doors should NOT reveal what's beyond them
            # Only open doors can show passage information
            if door.door_open:
                # Open door - describe the door AND the passage beyond
                passage = exit_entity.passage if hasattr(exit_entity, 'passage') and exit_entity.passage else None
                if passage:
                    # Combine door description + passage description
                    desc = f"{door.description} Beyond it, {passage}."
                else:
                    # No passage info, just use exit description
                    desc = exit_entity.description if exit_entity.description else door.description
            else:
                # Closed door - use only the door's description (player can't see through it)
                desc = door.description

            # Serialize the exit to get perspective variants and spatial context
            data = serialize_for_handler_result(exit_entity, accessor, actor_id)
            # Add door state as context for testing/debugging
            context = {
                "is_door": True,
                "door_state": {
                    "open": door.door_open,
                    "locked": door.door_locked
                }
            }
        else:
            # Fallback to door's generic description (not part of an exit)
            desc = door.description
            data = serialize_for_handler_result(door, accessor, actor_id)
            context = None

        return HandlerResult(
            success=True,
            primary=desc,
            data=data,
            context=context
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
        data = serialize_for_handler_result(exit_desc, accessor, actor_id)
        # Add exit-specific fields
        data["exit_direction"] = exit_direction
        data["exit_type"] = "door" if exit_desc.door_id else "open"
        if exit_desc.door_id:
            data["door_id"] = exit_desc.door_id

        return HandlerResult(
            success=True,
            primary=desc,
            data=data
        )

    # If no exit found, try to find a lock
    # Check if object_name matches "lock" (using vocabulary synonym matching)
    if name_matches(object_name, "lock"):
        # Extract indirect_object for "examine lock in door" pattern
        indirect_object = action.get("indirect_object")
        indirect_adjective = action.get("indirect_adjective")

        # Use adjective as direction if no explicit direction (e.g., "examine east lock")
        lock_direction = adjective or direction

        lock = find_lock_by_context(
            accessor,
            location_id=location.id,
            direction=lock_direction,
            door_name=indirect_object,
            door_adjective=indirect_adjective,
            actor_id=actor_id
        )

        if lock:
            # Build lock description
            desc = lock.description if hasattr(lock, 'description') and lock.description else "A lock."

            # Use unified serializer for llm_context with trait randomization
            data = serialize_for_handler_result(lock, accessor, actor_id)

            return HandlerResult(
                success=True,
                primary=desc,
                data=data
            )

        # Lock lookup failed - provide helpful error message
        if lock_direction:
            return HandlerResult(
                success=False,
                primary=f"There's no lock to the {lock_direction}."
            )
        elif indirect_object:
            return HandlerResult(
                success=False,
                primary=f"You don't see any lock on that."
            )
        else:
            return HandlerResult(
                success=False,
                primary="You don't see any lock here."
            )

    # Special case: redirect "examine player" to use "self"/"me"
    # Check BEFORE actor search to ensure consistent behavior regardless of player.name
    if name_matches(object_name, "player"):
        return HandlerResult(
            success=False,
            primary="To examine yourself, use 'examine self' or 'examine me'. To examine another player, use their name (e.g., 'examine Blake' or 'examine Ayomide')."
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
            inv_message, inv_data = format_inventory(accessor, target_actor, for_self=is_self, observer_actor_id=actor_id)
            if inv_message:
                message_parts.append(inv_message)

            # Invoke actor behaviors (on_examine)
            result = accessor.update(target_actor, {}, verb="examine", actor_id=actor_id)
            if result.detail:
                message_parts.append(result.detail)

            # Use unified serializer for llm_context with trait randomization
            data = serialize_for_handler_result(target_actor, accessor, actor_id)

            return HandlerResult(
                success=True,
                primary="\n".join(message_parts),
                data=data
            )
        # Invisible actor - fall through to "not found" message

    # Try universal surface fallback
    # Universal surfaces (ceiling, floor, walls, sky) don't require explicit parts
    from behaviors.core.spatial import is_universal_surface, get_default_description

    if is_universal_surface(object_name):
        description = get_default_description(object_name)
        return HandlerResult(
            success=True,
            primary=description
        )

    return HandlerResult(
        success=False,
        primary=f"You don't see any {get_display_name(object_name)} here."
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
    # Validate actor (location not needed for inventory)
    actor_id = cast(ActorId, action.get("actor_id") or ActorId("player"))
    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            primary=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Use shared format_inventory helper
    message, items_data = format_inventory(accessor, actor, for_self=True, observer_actor_id=actor_id)

    if not message:
        return HandlerResult(
            success=True,
            primary="You are carrying nothing."
        )

    return HandlerResult(
        success=True,
        primary=message,
        data={"items": items_data}
    )
