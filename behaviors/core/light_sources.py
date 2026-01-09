"""Light source behaviors - lanterns, torches, etc.

Entity behaviors for light-providing items that automatically
light when taken and extinguish when dropped.

Following narration architecture:
- Behaviors manage state (lit/unlit)
- Return structured data for narrator
- Item definitions provide narrative descriptions via state_variants
"""

from typing import Any, Dict

from src.behavior_manager import EventResult


def on_take(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Auto-light when taken.

    Changes the entity's lit state to True. The narrator will compose
    prose from the item's state_variants (lit vs unlit).

    Args:
        entity: The light source being taken
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb

    Returns:
        EventResult with allow and structured data (no feedback message)
    """
    from utilities.entity_serializer import serialize_for_handler_result

    # Update state
    entity.states['lit'] = True

    actor_id = context.get("actor_id")

    # Return structured data for narrator
    return EventResult(
        allow=True,
        feedback="",  # No pre-composed prose
        data={
            "light_source": serialize_for_handler_result(entity, accessor, actor_id),
            "state_change": "lit"
        }
    )


def on_drop(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Extinguish when dropped.

    Changes the entity's lit state to False. The narrator will compose
    prose from the item's state_variants (lit vs unlit).

    Args:
        entity: The light source being dropped
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb

    Returns:
        EventResult with allow and structured data (no feedback message)
    """
    from utilities.entity_serializer import serialize_for_handler_result

    # Update state
    entity.states['lit'] = False

    actor_id = context.get("actor_id")

    # Return structured data for narrator
    return EventResult(
        allow=True,
        feedback="",  # No pre-composed prose
        data={
            "light_source": serialize_for_handler_result(entity, accessor, actor_id),
            "state_change": "unlit"
        }
    )


def on_put(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """Extinguish when put down - delegates to on_drop."""
    return on_drop(entity, accessor, context)
