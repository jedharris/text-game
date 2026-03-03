"""Magic mat behavior module.

Demonstrates:
- Reacting to standard verbs (examine) with custom behavior
- State-dependent narration via state_variants
- Progressive revelation through state changes
"""

from typing import Dict, Any

from src.behavior_manager import EventResult


def on_examine(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Entity behavior for being examined.

    The mat progressively reveals its hidden message through state changes.
    State variants in the item definition provide the narrative descriptions.

    Args:
        entity: The mat
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb

    Returns:
        EventResult with allow and no message (state_variant provides description)
    """
    # Get current examine count from properties
    properties = entity.properties if hasattr(entity, 'properties') else {}
    examine_count = properties.get("examine_count", 0)

    # Increment count and update state property
    examine_count += 1
    if not hasattr(entity, 'properties'):
        entity.properties = {}
    entity.properties["examine_count"] = examine_count

    # Map count to state key for state_variant selection
    if examine_count == 1:
        state_key = "examined_once"
    elif examine_count == 2:
        state_key = "examined_twice"
    elif examine_count >= 3:
        state_key = "fully_examined"
    else:
        state_key = "unexamined"

    # Store current state for state_variant selector
    # The selector will use this to choose the appropriate variant
    entity.properties["mat_state"] = state_key

    # Return success with no message - let narrator compose from state_variant
    # The entity serializer will select the appropriate state_variant based on mat_state
    return EventResult(allow=True, feedback="")
