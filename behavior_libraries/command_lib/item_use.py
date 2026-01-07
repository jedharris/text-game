"""Item use command handler.

Provides use command. Pure hook dispatch - NO game logic.
"""

from typing import Dict, Optional
from src.state_accessor import HandlerResult
from src.word_entry import WordEntry
from src.types import ActorId
from utilities.utils import find_item_in_inventory
from utilities.handler_utils import get_display_name, find_action_target
from utilities.entity_serializer import serialize_for_handler_result

vocabulary = {
    "verbs": [
        {
            "word": "use",
            "synonyms": ["apply", "employ"],
            "object_required": True,
            "preposition": "on"
        }
    ],
    "handlers": {
        "use": "handle_use"
    }
}


def handle_use(accessor, action: Dict) -> HandlerResult:
    """Handle 'use <item> on <target>' command.

    Fires entity_item_use hook - ALL logic in reaction infrastructure.

    Args:
        accessor: StateAccessor with game_state and behavior_manager
        action: Parsed action dict with object (item) and indirect_object (target)

    Returns:
        HandlerResult with feedback from item_use reaction or error message
    """
    actor_id = ActorId(action.get('actor_id', ActorId("player")))
    item_name = action.get('object')
    target_name = action.get('indirect_object')

    # Find item in inventory
    if not isinstance(item_name, WordEntry):
        return HandlerResult(success=False, primary="Use what?")

    item = find_item_in_inventory(accessor, item_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            primary=f"You don't have any {get_display_name(item_name)}."
        )

    # Find target (can be actor, item, or location feature)
    target = None
    target_data = None

    if target_name and isinstance(target_name, WordEntry):
        # Try to find target using find_action_target
        target, error = find_action_target(accessor, action)
        if error:
            return error
        target_data = serialize_for_handler_result(target, accessor, actor_id)
    else:
        # No target specified - some items can be used without target
        pass

    # Fire hook (reaction infrastructure handles everything)
    context = {
        "item": item,
        "item_id": item.id,
        "target": target,
        "target_id": target.id if target else None,
        "actor_id": actor_id
    }

    result = accessor.behavior_manager.invoke_behavior(
        item, "entity_item_use", accessor, context
    )

    # Serialize item for narrator
    item_data = serialize_for_handler_result(item, accessor, actor_id)
    # Combine item and target data if both exist
    if target_data:
        item_data.update({"target": target_data})

    # Return result
    if result and result.feedback:
        return HandlerResult(
            success=result.allow,
            primary=result.feedback,
            data=item_data
        )
    else:
        # No handler responded
        if target:
            msg = f"You can't use the {item.name} on the {target.name}."
        else:
            msg = f"You can't use the {item.name} like that."
        return HandlerResult(
            success=False,
            primary=msg,
            data=item_data
        )
