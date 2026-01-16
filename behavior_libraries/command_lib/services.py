"""Service command handlers.

Provides learn/train commands for NPC teaching services.
Fires entity_service hook - reaction infrastructure handles logic.
"""

from typing import Any, Dict

from src.state_accessor import HandlerResult
from src.word_entry import WordEntry
from src.types import ActorId
from utilities.utils import find_actor_by_name
from utilities.handler_utils import get_display_name
from utilities.entity_serializer import serialize_for_handler_result

vocabulary = {
    "verbs": [
        {
            "word": "learn",
            "synonyms": ["study", "train"],
            "object_required": False,
            "preposition": "from"
        }
    ],
    "handlers": {
        "learn": "handle_learn"
    }
}


def handle_learn(accessor, action: Dict) -> HandlerResult:
    """Handle 'learn from <npc>' command.

    Fires entity_service hook - reaction infrastructure handles logic.

    Args:
        accessor: StateAccessor with game_state and behavior_manager
        action: Parsed action dict with indirect_object (NPC)

    Returns:
        HandlerResult with feedback from service handler or error message
    """
    actor_id = ActorId(action.get("actor_id", "player"))
    npc_name = action.get("indirect_object") or action.get("object")

    # Find NPC
    if not isinstance(npc_name, WordEntry):
        return HandlerResult(success=False, primary="Learn from whom?")

    npc = find_actor_by_name(accessor, npc_name, actor_id)
    if not npc:
        return HandlerResult(
            success=False,
            primary=f"You don't see any {get_display_name(npc_name)} here."
        )

    # Check if NPC has services defined
    services = npc.properties.get("services", {})
    if not services:
        return HandlerResult(
            success=False,
            primary=f"{npc.name} doesn't teach anything.",
        )

    # Fire service hook
    context = {
        "service_type": "teach",
        "requester": actor_id,
    }

    result = accessor.behavior_manager.invoke_behavior(
        npc, "on_service", accessor, context
    )

    npc_data = serialize_for_handler_result(npc, accessor, actor_id)

    if result and result.feedback:
        return HandlerResult(
            success=result.allow,
            primary=result.feedback,
            data=npc_data
        )
    else:
        return HandlerResult(
            success=False,
            primary=f"{npc.name} doesn't respond to your request.",
            data=npc_data
        )
