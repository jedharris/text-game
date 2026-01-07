"""Treatment command handler.

Provides treat command. Pure hook dispatch - NO game logic.
"""

from typing import Dict
from src.state_accessor import HandlerResult
from src.word_entry import WordEntry
from src.types import ActorId
from utilities.utils import find_actor_by_name, find_item_in_inventory
from utilities.handler_utils import get_display_name
from utilities.entity_serializer import serialize_for_handler_result

vocabulary = {
    "verbs": [
        {
            "word": "treat",
            "synonyms": ["bandage", "heal"],
            "object_required": True,
            "preposition": "with"
        }
    ],
    "handlers": {
        "treat": "handle_treat"
    }
}


def handle_treat(accessor, action: Dict) -> HandlerResult:
    """Handle 'treat <target> with <item>' command.

    Fires on_use_treatment event - ALL logic in treatment system.

    Args:
        accessor: StateAccessor with game_state and behavior_manager
        action: Parsed action dict with object (target) and indirect_object (treatment item)

    Returns:
        HandlerResult with feedback from treatment system or error message
    """
    actor_id = ActorId(action.get('actor_id', ActorId("player")))
    target_name = action.get('object')
    item_name = action.get('indirect_object')

    # Find target
    if not isinstance(target_name, WordEntry):
        return HandlerResult(success=False, primary="Treat who?")

    target = find_actor_by_name(accessor, target_name, actor_id)
    if not target:
        return HandlerResult(
            success=False,
            primary=f"You don't see any {get_display_name(target_name)} here."
        )

    # Find treatment item in inventory
    if not isinstance(item_name, WordEntry):
        return HandlerResult(success=False, primary="Treat with what?")

    item = find_item_in_inventory(accessor, item_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            primary=f"You don't have any {get_display_name(item_name)}."
        )

    # Fire on_use_treatment event (treatment system handles everything)
    context = {
        "treatment": item,
        "treatment_id": item.id,
        "target": target,
        "target_id": target.id,
        "actor_id": actor_id
    }

    # Fire event on the treatment item
    result = accessor.behavior_manager.invoke_behavior(
        item, "on_use_treatment", accessor, context
    )

    # Serialize item and target for narrator
    item_data = serialize_for_handler_result(item, accessor, actor_id)
    target_data = serialize_for_handler_result(target, accessor, actor_id)
    item_data["target"] = target_data

    # Return result
    if result and result.feedback:
        return HandlerResult(
            success=result.allow,
            primary=result.feedback,
            data=item_data
        )
    else:
        # No treatment handler responded
        return HandlerResult(
            success=False,
            primary=f"The {item.name} doesn't seem to help the {target.name}.",
            data=item_data
        )
