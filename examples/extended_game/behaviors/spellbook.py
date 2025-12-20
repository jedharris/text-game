"""Spellbook behavior module.

Demonstrates:
- Entity behavior (on_read) reacting to core read handler
- Tracking state in entity properties

Note: We don't need to define handle_read because the core interaction module
already has a read handler that invokes entity behaviors. We just define
the on_read entity behavior that gets called when our spellbook is read.

If you wanted to completely override the read handler, you could define
handle_read here - it would take precedence over the core handler because
game-specific (regular) handlers override core (symlink) handlers.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult


def on_read(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Entity behavior for being read.

    This is called when the spellbook is read (by the core read handler).

    Args:
        entity: The item being read
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb

    Returns:
        EventResult with allow and message
    """
    # Track how many times the book has been read
    if not hasattr(entity, 'states') or entity.states is None:
        entity.states = {}

    if "times_read" not in entity.states:
        entity.states["times_read"] = 0

    entity.states["times_read"] += 1
    times_read = entity.states["times_read"]

    # Generate different messages based on read count
    if times_read == 1:
        message = (
            "The pages glow as you open the book. You learn a spell of illumination!\n"
            "(Hint: Try 'wave wand' when you find it.)"
        )
    elif times_read == 2:
        message = (
            "You find a passage about crystal balls:\n"
            "'To reveal what is hidden, gaze deeply and speak the word of seeing.'"
        )
    elif times_read == 3:
        message = (
            "A note falls out! It reads:\n"
            "'The sanctum key lies within the crystal. Peer into its depths.'"
        )
    else:
        message = "You've read this book many times. The words begin to blur."

    return EventResult(allow=True, feedback=message)
