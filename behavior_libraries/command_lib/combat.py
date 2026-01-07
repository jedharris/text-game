"""Combat command handler.

Provides attack command. Pure hook dispatch - NO game logic.
"""

from typing import Dict
from src.state_accessor import HandlerResult
from src.word_entry import WordEntry
from src.types import ActorId
from utilities.utils import find_actor_by_name
from utilities.handler_utils import get_display_name
from utilities.entity_serializer import serialize_for_handler_result

vocabulary = {
    "verbs": [
        {
            "word": "attack",
            "synonyms": ["hit", "strike", "fight"],
            "object_required": True
        }
    ],
    "handlers": {
        "attack": "handle_attack"
    }
}


def handle_attack(accessor, action: Dict) -> HandlerResult:
    """Handle 'attack <target>' command.

    Fires on_attack event - ALL logic in combat system.

    Args:
        accessor: StateAccessor with game_state and behavior_manager
        action: Parsed action dict with object (target)

    Returns:
        HandlerResult with feedback from combat system or error message
    """
    actor_id = ActorId(action.get('actor_id', ActorId("player")))
    target_name = action.get('object')

    # Get attacker
    state = accessor.game_state
    attacker = state.get_actor(actor_id)

    # Find target
    if not isinstance(target_name, WordEntry):
        return HandlerResult(success=False, primary="Attack who?")

    target = find_actor_by_name(accessor, target_name, actor_id)
    if not target:
        return HandlerResult(
            success=False,
            primary=f"You don't see any {get_display_name(target_name)} here."
        )

    if target.id == actor_id:
        return HandlerResult(
            success=False,
            primary="You can't attack yourself."
        )

    # Fire on_attack event (combat system handles everything)
    context = {
        "target_id": target.id,
        "actor_id": actor_id
    }

    result = accessor.behavior_manager.invoke_behavior(
        attacker, "on_attack", accessor, context
    )

    # Serialize attacker and target for narrator
    attacker_data = serialize_for_handler_result(attacker, accessor, actor_id)
    target_data = serialize_for_handler_result(target, accessor, actor_id)
    attacker_data["target"] = target_data

    # Return result
    if result and result.feedback:
        return HandlerResult(
            success=result.allow,
            primary=result.feedback,
            data=attacker_data
        )
    else:
        # No combat handler responded
        return HandlerResult(
            success=False,
            primary=f"You don't know how to attack the {target.name}.",
            data=attacker_data
        )
