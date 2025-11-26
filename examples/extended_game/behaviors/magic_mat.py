"""Magic mat behavior module.

Demonstrates:
- Reacting to standard verbs (examine) with custom behavior
- Simple state tracking
"""

from typing import Dict, Any

from src.behavior_manager import EventResult


def on_examine(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Entity behavior for being examined.

    The mat has a hidden message that becomes clearer each time you examine it.

    Args:
        entity: The mat
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb

    Returns:
        EventResult with allow and message
    """
    # Track examination count
    if not hasattr(entity, 'states') or entity.states is None:
        entity.states = {}

    examine_count = entity.states.get("examine_count", 0) + 1
    entity.states["examine_count"] = examine_count

    # Progressively reveal the hidden message
    if examine_count == 1:
        message = (
            "You look more closely at the faded mat.\n"
            "The words 'Speak Friend' are barely visible, worn by countless feet."
        )
    elif examine_count == 2:
        message = (
            "You bend down to examine the mat more carefully.\n"
            "Wait - there's something underneath! You lift the corner..."
        )
    elif examine_count == 3:
        message = (
            "Under the mat, you find words scratched into the stone:\n"
            "'The crystal holds the key to the sanctum.'"
        )
    else:
        message = (
            "You've examined the mat thoroughly.\n"
            "The message 'The crystal holds the key to the sanctum' is still there."
        )

    return EventResult(allow=True, message=message)
