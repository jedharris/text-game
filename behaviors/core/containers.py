"""Container behaviors - chests, boxes, etc.

Vocabulary and entity behaviors for containers like treasure chests
that trigger special effects when opened.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.state_accessor import IGNORE_EVENT


# Vocabulary extension - adds open and close verbs
vocabulary = {
    "verbs": [
        {
            "word": "open",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["reveals contents", "changes state to open"],
                "failure_narration": {
                    "locked": "locked and won't budge",
                    "already_open": "already open",
                    "cannot_open": "cannot be opened"
                }
            }
        },
        {
            "word": "close",
            "synonyms": ["shut"],
            "object_required": True,
            "narration_mode": "brief",
            "llm_context": {
                "traits": ["conceals contents", "changes state to closed"],
                "failure_narration": {
                    "already_closed": "already closed",
                    "cannot_close": "cannot be closed"
                }
            }
        },
        {
            "word": "put",
            "synonyms": ["place", "set"],
            "object_required": True,
            "indirect_object_required": True,
            "narration_mode": "brief",
            "llm_context": {
                "traits": ["places item in/on container", "requires indirect_object"],
                "failure_narration": {
                    "no_capacity": "won't fit",
                    "not_container": "can't put things there",
                    "container_closed": "it's closed"
                }
            }
        },
        {
            "word": "push",
            "synonyms": ["shove", "move"],
            "object_required": True,
            "llm_context": {
                "traits": ["moves heavy objects", "may reveal hidden areas"],
                "failure_narration": {
                    "not_pushable": "won't budge",
                    "portable": "could just pick it up"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": []
}


def on_open(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Handle open event for treasure chest - win condition.

    Sets the 'won' flag in player flags to trigger game end.
    Returns structured data for narrator composition.
    Returns IGNORE_EVENT if entity is not a treasure chest, allowing other handlers.

    Following narration architecture:
    - Behavior manages state (sets won flag)
    - Returns structured data for narrator
    - Item definitions provide narrative descriptions via traits

    Args:
        entity: The entity being opened
        accessor: StateAccessor instance
        context: Context dict with location, verb

    Returns:
        EventResult if entity is treasure chest, IGNORE_EVENT otherwise
    """
    from utilities.entity_serializer import serialize_for_handler_result

    # Only handle treasure chest
    if entity.id != "treasure_chest":
        return IGNORE_EVENT

    actor_id = context.get("actor_id", "player")
    player = accessor.get_actor(actor_id)
    if player:
        player.flags["won"] = True

    # Check if this is a victory item
    is_victory = entity.properties.get("victory_item", False)

    # Get treasure contents if container
    treasure_items = []
    if hasattr(entity, 'container') and entity.container:
        for item_id in entity.container.items:
            item = accessor.get_item(item_id)
            if item:
                treasure_items.append(serialize_for_handler_result(item, accessor, actor_id))

    # Return structured data for narrator
    return EventResult(
        allow=True,
        feedback="",  # No pre-composed prose
        data={
            "container": serialize_for_handler_result(entity, accessor, actor_id),
            "contents": treasure_items,
            "victory": is_victory
        }
    )
