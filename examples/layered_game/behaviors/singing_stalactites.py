"""Singing Stalactites puzzle behavior.

Demonstrates:
- Custom verb (strike) for puzzle interaction
- Using puzzle_lib.sequence_tracker for musical sequence validation
- Using puzzle_lib.state_revealer for revealing reward
"""

from typing import Dict, Any
from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item

# Import library functions
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from behavior_libraries.puzzle_lib.sequence_tracker import (
    track_action, check_sequence, reset_sequence, get_sequence_progress
)
from behavior_libraries.puzzle_lib.state_revealer import reveal_item


# Vocabulary extension - adds "play" verb
vocabulary = {
    "verbs": [
        {
            "word": "play",
            "event": "on_play",
            "synonyms": ["ring"],
            "object_required": True
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}


# The correct musical sequence
CORRECT_SEQUENCE = ["do", "re", "mi", "fa", "sol"]


def handle_play(accessor, action: Dict) -> HandlerResult:
    """
    Handle the play command.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, actor_id

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = action.get("actor_id", "player")
    obj_name = action.get("object")
    adjective = action.get("adjective")

    if not obj_name:
        return HandlerResult(success=False, message="Play what?")

    # Find the target (stalactite)
    target = find_accessible_item(accessor, obj_name, actor_id, adjective)

    if not target:
        return HandlerResult(success=False, message=f"You don't see any {obj_name} here.")

    # Invoke entity behavior
    result = accessor.update(target, {}, verb="play", actor_id=actor_id)

    if not result.success:
        return HandlerResult(success=False, message=result.message)

    # Build response message
    if result.message:
        message = result.message
    else:
        message = f"You strike the {target.name}."

    return HandlerResult(success=True, message=message)


def on_play(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Entity behavior for stalactite being played.

    Tracks the sequence of notes played. When correct sequence is played,
    reveals the crystal cache.

    Args:
        entity: The stalactite being struck
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb

    Returns:
        EventResult with allow and message
    """
    # Get the note this stalactite produces
    note = entity.properties.get("note", "unknown")

    # Get the puzzle tracker (stored on the location)
    location = accessor.get_location("loc_stalactites")
    if not hasattr(location, 'states') or location.states is None:
        location.states = {}

    # Track this note in the sequence
    sequence = track_action(location, note, max_length=10)

    # Check progress
    progress = get_sequence_progress(location, CORRECT_SEQUENCE)

    # Check if sequence is complete and correct
    if check_sequence(location, CORRECT_SEQUENCE, exact=True):
        # Success! Reveal the crystals
        reveal_item(accessor, "item_crystal_cache")

        message = (
            f"You play the stalactite.\n"
            f"It rings with a clear '{note.upper()}' note!\n\n"
            f"The five notes resonate in perfect harmony!\n"
            f"The stalactites shatter, raining crystal shards down from the ceiling!"
        )

        # Reset for potential replay
        reset_sequence(location)

    elif len(sequence) > len(CORRECT_SEQUENCE):
        # Too many notes - sequence failed
        reset_sequence(location)
        message = (
            f"You play the stalactite.\n"
            f"It rings with a '{note.upper()}' note.\n\n"
            f"The sequence becomes discordant and fades away.\n"
            f"You'll need to start over."
        )

    elif progress < len(sequence):
        # Wrong note in sequence
        reset_sequence(location)
        message = (
            f"You play the stalactite.\n"
            f"It rings with a '{note.upper()}' note.\n\n"
            f"That doesn't sound right. The notes clash and fade.\n"
            f"You'll need to start over."
        )

    else:
        # Correct so far, keep going
        notes_left = len(CORRECT_SEQUENCE) - len(sequence)

        if notes_left > 0:
            message = (
                f"You play the stalactite.\n"
                f"It rings with a clear '{note.upper()}' note!\n"
                f"The sound resonates beautifully. {notes_left} more note(s) needed..."
            )
        else:
            message = (
                f"You play the stalactite.\n"
                f"It rings with a '{note.upper()}' note."
            )

    return EventResult(allow=True, message=message)
