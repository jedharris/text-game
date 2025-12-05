"""Spatial behaviors - explicit positioning commands.

Vocabulary and handlers for spatial positioning and movement within a location.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.entity_serializer import serialize_for_handler_result


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
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    adjective = action.get("adjective")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to approach?"
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

    # Find target entity in current location
    target = _find_entity_in_location(accessor, location.id, object_name, adjective)

    if not target:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Check if target is accessible
    if not _is_accessible(accessor, actor, target):
        return HandlerResult(
            success=False,
            message=f"You can't reach the {target.name} from here."
        )

    # Check if already focused on this entity
    old_focus = actor.properties.get("focused_on")
    already_there = (old_focus == target.id)

    # Update focus
    actor.properties["focused_on"] = target.id

    # Clear posture when moving (even if just confirming position)
    if "posture" in actor.properties:
        del actor.properties["posture"]

    # Build message
    if already_there:
        message = f"You're already at the {target.name}."
    else:
        message = f"You move to the {target.name}."

    # Serialize target for LLM consumption
    data = serialize_for_handler_result(target)

    return HandlerResult(success=True, message=message, data=data)


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
    actor_id = action.get("actor_id", "player")
    indirect_object = action.get("indirect_object")

    if not indirect_object:
        return HandlerResult(
            success=False,
            message="Take cover behind what?"
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

    # Find cover entity in current location
    cover = _find_entity_in_location(accessor, location.id, indirect_object)

    if not cover:
        return HandlerResult(
            success=False,
            message=f"You don't see any {indirect_object} here."
        )

    # Check if entity provides cover
    if not cover.properties.get("provides_cover", False):
        return HandlerResult(
            success=False,
            message=f"The {cover.name} doesn't provide cover."
        )

    # Check if target is accessible
    if not _is_accessible(accessor, actor, cover):
        return HandlerResult(
            success=False,
            message=f"You can't reach the {cover.name} from here."
        )

    # Set cover state
    actor.properties["focused_on"] = cover.id
    actor.properties["posture"] = "cover"

    message = f"You take cover behind the {cover.name}."

    # Serialize cover entity for LLM consumption
    data = serialize_for_handler_result(cover)
    data["posture"] = "cover"

    return HandlerResult(success=True, message=message, data=data)


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
    actor_id = action.get("actor_id", "player")
    indirect_object = action.get("indirect_object")

    if not indirect_object:
        return HandlerResult(
            success=False,
            message="Hide in what?"
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

    # Find hiding spot in current location
    hiding_spot = _find_entity_in_location(accessor, location.id, indirect_object)

    if not hiding_spot:
        return HandlerResult(
            success=False,
            message=f"You don't see any {indirect_object} here."
        )

    # Check if entity allows concealment
    if not hiding_spot.properties.get("allows_concealment", False):
        return HandlerResult(
            success=False,
            message=f"You can't hide in the {hiding_spot.name}."
        )

    # Check if target is accessible
    if not _is_accessible(accessor, actor, hiding_spot):
        return HandlerResult(
            success=False,
            message=f"You can't reach the {hiding_spot.name} from here."
        )

    # Set concealed state
    actor.properties["focused_on"] = hiding_spot.id
    actor.properties["posture"] = "concealed"

    message = f"You hide in the {hiding_spot.name}."

    # Serialize hiding spot for LLM consumption
    data = serialize_for_handler_result(hiding_spot)
    data["posture"] = "concealed"

    return HandlerResult(success=True, message=message, data=data)


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
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    adjective = action.get("adjective")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to climb?"
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

    # Find climbable entity in current location
    from utilities.utils import find_accessible_item
    climbable = find_accessible_item(accessor, object_name, actor_id, adjective)

    if not climbable:
        # Not found - return failure so exits.py can try exit navigation
        # Extract word from WordEntry for display
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
