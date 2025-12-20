"""Container behaviors - chests, boxes, etc.

Vocabulary and entity behaviors for containers like treasure chests
that trigger special effects when opened.
"""

from typing import Any, Dict, Optional

from src.behavior_manager import EventResult


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


def on_open(entity: Any, state: Any, context: Dict) -> Optional[EventResult]:
    """
    Handle open event for treasure chest - win condition.

    Sets the 'won' flag in player flags to trigger game end.
    Returns None if entity is not a treasure chest, allowing other handlers.

    Args:
        entity: The entity being opened
        state: GameState object
        context: Context dict with location, verb

    Returns:
        EventResult if entity is treasure chest, None otherwise
    """
    # Only handle treasure chest
    if entity.id != "treasure_chest":
        return None

    player = state.actors.get("player")
    if player:
        player.flags["won"] = True

    return EventResult(
        allow=True,
        feedback="You open the chest and find glittering treasure! You win!"
    )
