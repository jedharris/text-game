"""Spatial behaviors - explicit positioning commands.

Vocabulary and handlers for spatial positioning and movement within a location.
"""

from typing import Dict, Any, Optional

from src.action_types import ActionDict
from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.entity_serializer import serialize_for_handler_result
from utilities.handler_utils import validate_actor_and_location


# Vocabulary extension - adds spatial positioning verbs and universal surfaces
vocabulary = {
    "verbs": [
        {
            "word": "approach",
            "event": "on_approach",
            "synonyms": ["go to", "move to", "walk to"],
            "object_required": True,
            "llm_context": {
                "traits": ["moves actor near object", "explicit positioning"],
                "usage": ["approach <object>", "go to <object>"]
            }
        },
        {
            "word": "cover",
            "event": "on_cover",
            "synonyms": ["take cover", "hide behind"],
            "indirect_object_required": True,
            "llm_context": {
                "traits": ["tactical positioning", "concealment", "combat"],
                "usage": ["take cover behind <object>", "hide behind <object>"]
            }
        },
        {
            "word": "hide",
            "event": "on_hide",
            "synonyms": ["conceal"],
            "indirect_object_required": True,
            "llm_context": {
                "traits": ["stealth", "concealment"],
                "usage": ["hide in <object>"]
            }
        },
        {
            "word": "climb",
            "event": "on_climb",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["vertical movement", "positioning"],
                "usage": ["climb <object>"]
            }
        },
        {
            "word": "down",
            "event": "on_down",
            "synonyms": [],
            "object_required": False,
            "llm_context": {
                "traits": ["return to ground level", "descend from elevated position"],
                "usage": ["down"]
            }
        },
        {
            "word": "up",
            "event": "on_up",
            "synonyms": [],
            "object_required": False,
            "llm_context": {
                "traits": ["return to ground level", "get down from elevated position"],
                "usage": ["up"]
            }
        }
    ],
    "nouns": [
        {
            "word": "ceiling",
            "synonyms": [],
            "properties": {
                "universal_surface": True,
                "default_description": "Nothing remarkable about the ceiling."
            }
        },
        {
            "word": "floor",
            "synonyms": ["ground"],
            "properties": {
                "universal_surface": True,
                "default_description": "Nothing remarkable about the floor."
            }
        },
        {
            "word": "sky",
            "synonyms": [],
            "properties": {
                "universal_surface": True,
                "default_description": "The sky stretches above you."
            }
        },
        {
            "word": "walls",
            "synonyms": [],
            "properties": {
                "universal_surface": True,
                "default_description": "The walls surround you."
            }
        }
    ],
    "adjectives": [],
    "directions": []
}


def _handle_positioning(accessor, action, object_field: str, required_property: Optional[str] = None,
                        posture: Optional[str] = None, verb_phrase: str = "move to",
                        failure_message_builder=None, invoke_behaviors: bool = False) -> HandlerResult:
    """
    Generic positioning handler for approach, cover, hide, climb operations.

    Args:
        accessor: StateAccessor instance
        action: Action dict with actor_id, object/indirect_object
        object_field: "object" or "indirect_object" - which field to read
        required_property: Optional property to validate (e.g., "climbable")
        posture: Optional posture to set ("climbing", "cover", "concealed", None)
        verb_phrase: Verb phrase for success message (e.g., "move to", "take cover behind")
        failure_message_builder: Optional function(property_name, target_name) for custom failure messages
        invoke_behaviors: Whether to invoke entity behaviors before positioning

    Returns:
        HandlerResult with success flag and message
    """
    # Validate actor and location
    require_object = (object_field == "object")
    require_indirect = (object_field == "indirect_object")
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=require_object, require_indirect_object=require_indirect
    )
    if error:
        return error
    assert actor is not None and location is not None  # Guaranteed by validate_actor_and_location

    object_name = action.get(object_field)
    adjective = action.get("adjective")

    # Find target entity in current location
    target = _find_entity_in_location(accessor, location.id, object_name, adjective)

    if not target:
        display_name = object_name.word if hasattr(object_name, 'word') else object_name
        return HandlerResult(
            success=False,
            message=f"You don't see any {display_name} here."
        )

    # Check if target is accessible
    if not _is_accessible(accessor, actor, target):
        return HandlerResult(
            success=False,
            message=f"You can't reach the {target.name} from here."
        )

    # Check required property if specified
    if required_property and not target.properties.get(required_property, False):
        if failure_message_builder:
            message = failure_message_builder(required_property, target.name)
        else:
            # Default failure message based on property
            if required_property == "provides_cover":
                message = f"The {target.name} doesn't provide cover."
            elif required_property == "allows_concealment":
                message = f"You can't hide in the {target.name}."
            elif required_property == "climbable":
                message = f"You can't climb the {target.name}."
            else:
                message = f"The {target.name} doesn't allow that."
        return HandlerResult(success=False, message=message)

    # Invoke entity behaviors if requested (e.g., for climb)
    behavior_message = None
    if invoke_behaviors:
        verb = action.get("verb", "interact")
        result = accessor.update(target, {}, verb=verb, actor_id=actor_id)
        if not result.success:
            return HandlerResult(success=False, message=result.message)
        behavior_message = result.message

    # Check if already positioned here (for approach-like operations without posture change)
    old_focus = actor.properties.get("focused_on")
    already_there = (old_focus == target.id and posture is None)

    # Set positioning state
    actor.properties["focused_on"] = target.id

    # Set or clear posture
    if posture:
        actor.properties["posture"] = posture
    elif "posture" in actor.properties:
        # Clear posture for simple movement
        del actor.properties["posture"]

    # Build message
    if already_there:
        message = f"You're already at the {target.name}."
    else:
        message = f"You {verb_phrase} the {target.name}."
        if behavior_message:
            message = f"{message}\n{behavior_message}"

    # Serialize target for LLM consumption
    data = serialize_for_handler_result(target)
    if posture:
        data["posture"] = posture

    return HandlerResult(success=True, message=message, data=data)


def handle_approach(accessor, action):
    """
    Handle approach command for explicit positioning.

    Moves actor to be focused on target entity (item, part, container, actor).
    Always sets focused_on and clears posture when moving.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of target entity (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    return _handle_positioning(accessor, action, object_field="object", verb_phrase="move to")


def handle_take_cover(accessor, action):
    """
    Handle take cover command for tactical positioning.

    Takes cover behind an object or part that provides cover.
    Sets actor's posture to "cover" and focuses on the cover entity.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - indirect_object: Name of cover entity (required)

    Returns:
        HandlerResult with success flag and message
    """
    # Check for missing indirect_object with custom message
    if not action.get("indirect_object"):
        return HandlerResult(
            success=False,
            message="Take cover behind what?"
        )

    return _handle_positioning(
        accessor, action,
        object_field="indirect_object",
        required_property="provides_cover",
        posture="cover",
        verb_phrase="take cover behind"
    )


def handle_hide_in(accessor, action):
    """
    Handle hide command for concealment.

    Hides inside a container or concealed space that allows concealment.
    Sets actor's posture to "concealed" and focuses on the hiding spot.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - indirect_object: Name of hiding spot (required)

    Returns:
        HandlerResult with success flag and message
    """
    # Check for missing indirect_object with custom message
    if not action.get("indirect_object"):
        return HandlerResult(
            success=False,
            message="Hide in what?"
        )

    return _handle_positioning(
        accessor, action,
        object_field="indirect_object",
        required_property="allows_concealment",
        posture="concealed",
        verb_phrase="hide in"
    )


def handle_climb(accessor, action):
    """
    Handle climb command for vertical positioning.

    Climbs on an object that is climbable.
    Sets actor's posture to "climbing" and focuses on the climbable object.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of climbable object (required)
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

    object_name = action.get("object")
    adjective = action.get("adjective")

    # Use find_accessible_item for climb to support adjectives properly
    from utilities.utils import find_accessible_item
    climbable = find_accessible_item(accessor, object_name, actor_id, adjective)

    if not climbable:
        # Not found - return failure so exits.py can try exit navigation
        display_name = object_name.word if hasattr(object_name, 'word') else object_name
        return HandlerResult(
            success=False,
            message=f"You don't see any {display_name} here."
        )

    # Check if entity is climbable
    if not climbable.properties.get("climbable", False):
        # Not climbable - return failure so exits.py can try exit navigation
        return HandlerResult(
            success=False,
            message=f"You can't climb the {climbable.name}."
        )

    # Check if target is accessible
    if not _is_accessible(accessor, actor, climbable):
        return HandlerResult(
            success=False,
            message=f"You can't reach the {climbable.name} from here."
        )

    # Invoke entity behaviors (on_climb) before allowing climb
    result = accessor.update(climbable, {}, verb="climb", actor_id=actor_id)

    if not result.success:
        # Entity behavior denied the climb
        return HandlerResult(success=False, message=result.message)

    # Set climbing state
    actor.properties["focused_on"] = climbable.id
    actor.properties["posture"] = "climbing"

    # Build message - include behavior message if present
    base_message = f"You climb the {climbable.name}."
    if result.message:
        message = f"{base_message}\n{result.message}"
    else:
        message = base_message

    # Serialize climbable object for LLM consumption
    data = serialize_for_handler_result(climbable)
    data["posture"] = "climbing"

    return HandlerResult(success=True, message=message, data=data)


def handle_down(accessor, action):
    """
    Handler for 'down' command to return to ground level.

    When actor has a posture (climbing, cover, concealed), this clears it
    and returns them to normal standing. When actor has no posture, this
    returns failure so exits.py can handle it as directional movement.

    Args:
        accessor: StateAccessor instance
        action: Action dict with actor_id

    Returns:
        HandlerResult with success flag and message, or failure if no posture
    """
    # Validate actor and location
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=False
    )
    if error:
        return error

    # Check if actor has a posture to clear
    current_posture = actor.properties.get("posture")

    if not current_posture:
        # No posture - return failure so exits.py can handle 'down' as direction
        return HandlerResult(
            success=False,
            message=""  # Empty message means "not handled, try next handler"
        )

    # Clear positioning state
    actor.properties.pop("posture", None)
    actor.properties.pop("focused_on", None)

    # Generate appropriate message based on previous posture
    posture_messages = {
        "climbing": "You climb down and return to ground level.",
        "cover": "You stand up from cover.",
        "concealed": "You emerge from hiding."
    }

    message = posture_messages.get(current_posture, "You return to ground level.")

    return HandlerResult(success=True, message=message)


def handle_up(accessor, action):
    """Alias for handle_down - 'up' also works to get down from elevated positions."""
    return handle_down(accessor, action)


def _find_entity_in_location(accessor, location_id: str, object_name, adjective=None):
    """
    Find entity matching object_name in given location.

    Searches items, parts, and actors in the location.
    Uses vocabulary system for matching.

    Args:
        accessor: StateAccessor instance
        location_id: Location ID to search in
        object_name: WordEntry or string name to search for
        adjective: Optional adjective for disambiguation

    Returns:
        Matching entity or None if not found
    """
    from utilities.utils import name_matches
    from utilities.positioning import find_part_by_name

    # Try to find as item in the location
    for item in accessor.game_state.items:
        if item.location == location_id:
            if name_matches(object_name, item.name):
                # Check adjective if provided
                if adjective:
                    # Compare adjective against item properties or description
                    # For now, just match without adjective filtering
                    # (full adjective support would need more context)
                    pass
                return item

    # Try to find as part
    part = find_part_by_name(accessor, object_name, location_id)
    if part:
        return part

    # Try to find as actor in same location
    for actor_id, actor in accessor.game_state.actors.items():
        if actor.location == location_id and actor_id != "player":
            if name_matches(object_name, actor.name):
                return actor

    return None


def _is_accessible(accessor, actor, target):
    """
    Check if target entity is accessible from actor's location.

    Returns True if target is in same location or is a part whose parent
    is in same location.

    Args:
        accessor: StateAccessor instance
        actor: Actor attempting to access
        target: Entity being accessed

    Returns:
        bool: True if accessible, False otherwise
    """
    actor_location = actor.location

    # If target is an item/actor, check same location
    if hasattr(target, 'location'):
        return target.location == actor_location

    # If target is a part, check parent is in same location
    if hasattr(target, 'part_of'):
        parent = accessor.get_entity(target.part_of)
        if parent:
            # If parent is a location, check actor is in that location
            if hasattr(parent, 'exits'):  # It's a Location
                return parent.id == actor_location
            # If parent is an item/actor, check parent's location
            if hasattr(parent, 'location'):
                return parent.location == actor_location

    return False


# Universal Surface Support
# These functions provide fallback behavior for common spatial elements
# (ceiling, floor, walls, sky) that exist in every location but don't
# require explicit Part entities unless authors want custom descriptions.

def get_universal_surface_nouns():
    """
    Return list of universal surface noun words.

    Universal surfaces are common room features that exist in every location
    without requiring explicit Part entities.

    Returns:
        list[str]: List of universal surface words (e.g., ["ceiling", "floor", ...])
    """
    return [entry["word"] for entry in vocabulary["nouns"]
            if entry.get("properties", {}).get("universal_surface")]


def is_universal_surface(word_entry):
    """
    Check if word entry refers to a universal surface.

    Universal surfaces include: ceiling, floor (ground), sky, walls

    Args:
        word_entry: WordEntry or string to check

    Returns:
        bool: True if the word refers to a universal surface
    """
    # Handle string input
    if isinstance(word_entry, str):
        search_word = word_entry.lower()
    else:
        # WordEntry or object with 'word' attribute
        search_word = getattr(word_entry, 'word', str(word_entry)).lower()

    universal_words = get_universal_surface_nouns()

    # Check primary word
    if search_word in universal_words:
        return True

    # Check synonyms
    for entry in vocabulary["nouns"]:
        if entry.get("properties", {}).get("universal_surface"):
            synonyms = [syn.lower() for syn in entry.get("synonyms", [])]
            if search_word in synonyms:
                return True

    return False


def get_default_description(word_entry):
    """
    Get default description for universal surface.

    Args:
        word_entry: WordEntry or string for the surface

    Returns:
        str: Default description for the surface
    """
    # Handle string input
    if isinstance(word_entry, str):
        search_word = word_entry.lower()
    else:
        # WordEntry or object with 'word' attribute
        search_word = getattr(word_entry, 'word', str(word_entry)).lower()

    # Check primary word match
    for entry in vocabulary["nouns"]:
        if entry["word"].lower() == search_word:
            return entry.get("properties", {}).get("default_description",
                                                   f"Nothing remarkable about the {search_word}.")

    # Check synonym match
    for entry in vocabulary["nouns"]:
        synonyms = [syn.lower() for syn in entry.get("synonyms", [])]
        if search_word in synonyms:
            return entry.get("properties", {}).get("default_description",
                                                   f"Nothing remarkable about the {search_word}.")

    return f"Nothing remarkable about the {search_word}."
