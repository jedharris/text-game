"""Perception behaviors - examine/look.

Vocabulary and handlers for examining objects and surroundings.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item


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
                "traits": ["reveals details", "non-destructive", "provides information"]
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

    # Build description
    message_parts = [f"{location.name}\n{location.description}"]

    # List items in location
    items_here = []
    for item in accessor.game_state.items:
        if item.location == location.id:
            items_here.append(item)

    if items_here:
        item_names = ", ".join([item.name for item in items_here])
        message_parts.append(f"\nYou see: {item_names}")

    # List other actors in location
    actors_here = []
    for other_actor_id, other_actor in accessor.game_state.actors.items():
        if other_actor.location == location.id and other_actor_id != actor_id:
            actors_here.append(other_actor)

    if actors_here:
        actor_names = ", ".join([a.name for a in actors_here])
        message_parts.append(f"\nAlso here: {actor_names}")

    return HandlerResult(
        success=True,
        message="\n".join(message_parts)
    )


def handle_examine(accessor, action):
    """
    Handle examine command.

    Shows detailed description of an item.

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item to examine (required)

    Returns:
        HandlerResult with success flag and message
    """
    # CRITICAL: Extract actor_id at the top
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

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

    # Find the item
    item = find_accessible_item(accessor, object_name, actor_id)

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    return HandlerResult(
        success=True,
        message=f"{item.name}: {item.description}"
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
