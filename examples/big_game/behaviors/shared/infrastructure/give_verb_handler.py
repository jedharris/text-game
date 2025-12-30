"""Give Verb Handler.

Wires the 'give' verb to invoke entity_gift_given hook so that
gift_reactions infrastructure can process gift giving.

This is a workaround until the engine natively supports this.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult

# Vocabulary: wire give verb to handler
vocabulary: Dict[str, Any] = {
    "verbs": [
        {
            "word": "give",
            "synonyms": ["offer", "present"],
            "object_required": True,
            "preposition": "to",
        }
    ],
    "events": [
        {
            "event": "on_give_item",
            "hook": "before_action",
            "description": "Handle giving items to actors"
        }
    ]
}


def on_give_item(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle give command by invoking entity_gift_given hook.

    This allows gift_reactions infrastructure to process the gift.

    Args:
        entity: The actor performing the action (player)
        accessor: StateAccessor instance
        context: Context with verb, target, item info

    Returns:
        EventResult allowing the action
    """
    # Check if this is a give command
    verb = context.get("verb", "")
    if verb not in ["give", "offer", "present"]:
        return EventResult(allow=True, feedback=None)

    # Get target actor (who is receiving the gift)
    target = context.get("target")
    if not target:
        return EventResult(allow=True, feedback=None)

    # Check if target is an actor (not an item or location)
    if not hasattr(target, "properties"):
        return EventResult(allow=True, feedback=None)

    # Get the item being given
    item = context.get("object")
    if not item:
        return EventResult(allow=True, feedback=None)

    # Invoke entity_gift_given hook on the target
    # This allows gift_reactions to process the gift
    gift_context = {
        **context,
        "target_actor": target,
        "item": item,
        "giver": entity,
    }

    result = accessor.invoke_hook(
        hook_id="entity_gift_given",
        entity=target,
        context=gift_context
    )

    # If gift reaction provided feedback, use it
    # Otherwise allow the default give action to proceed
    if result and result.feedback:
        return result

    return EventResult(allow=True, feedback=None)
