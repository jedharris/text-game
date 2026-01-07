"""Dialog command handlers.

Provides ask/talk commands. Pure hook dispatch - NO game logic.
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
            "word": "ask",
            "synonyms": ["inquire", "question"],
            "object_required": True,
            "preposition": "about"
        },
        {
            "word": "talk",
            "synonyms": ["speak", "converse", "chat"],
            "object_required": False,
            "preposition": "to"
        }
    ],
    "handlers": {
        "ask": "handle_ask",
        "talk": "handle_talk"
    }
}


def handle_ask(accessor, action: Dict) -> HandlerResult:
    """Handle 'ask <npc> about <topic>' command.

    Fires entity_dialog hook - ALL logic in reaction infrastructure.

    Args:
        accessor: StateAccessor with game_state and behavior_manager
        action: Parsed action dict with object (NPC) and indirect_object (topic)

    Returns:
        HandlerResult with feedback from dialog reaction or error message
    """
    actor_id = ActorId(action.get('actor_id', ActorId("player")))
    npc_name = action.get('object')
    topic = action.get('indirect_object') or action.get('raw_after_preposition', '')

    # Find NPC
    if not isinstance(npc_name, WordEntry):
        return HandlerResult(success=False, primary="Ask who?")

    npc = find_actor_by_name(accessor, npc_name, actor_id)
    if not npc:
        return HandlerResult(
            success=False,
            primary=f"You don't see any {get_display_name(npc_name)} here."
        )

    if not topic:
        return HandlerResult(success=False, primary=f"Ask {npc.name} about what?")

    # Fire hook (reaction infrastructure handles everything)
    topic_str = topic.word if isinstance(topic, WordEntry) else str(topic)
    context = {
        "keyword": topic_str,
        "dialog_text": topic_str,
        "speaker": actor_id
    }

    result = accessor.behavior_manager.invoke_behavior(
        npc, "entity_dialog", accessor, context
    )

    # Serialize NPC for narrator
    npc_data = serialize_for_handler_result(npc, accessor, actor_id)

    # Return result
    if result and result.feedback:
        return HandlerResult(
            success=result.allow,
            primary=result.feedback,
            data=npc_data
        )
    else:
        # No handler responded
        return HandlerResult(
            success=False,
            primary=f"{npc.name} doesn't seem interested in discussing that.",
            data=npc_data
        )


def handle_talk(accessor, action: Dict) -> HandlerResult:
    """Handle 'talk to <npc>' command.

    Fires entity_dialog hook with empty keyword (general conversation).

    Args:
        accessor: StateAccessor with game_state and behavior_manager
        action: Parsed action dict with indirect_object (NPC) or object (NPC)

    Returns:
        HandlerResult with feedback from dialog reaction or error message
    """
    actor_id = ActorId(action.get('actor_id', ActorId("player")))
    npc_name = action.get('indirect_object') or action.get('object')

    # Find NPC
    if not isinstance(npc_name, WordEntry):
        return HandlerResult(success=False, primary="Talk to whom?")

    npc = find_actor_by_name(accessor, npc_name, actor_id)
    if not npc:
        return HandlerResult(
            success=False,
            primary=f"You don't see any {get_display_name(npc_name)} here."
        )

    # Fire hook with empty keyword (general conversation)
    context = {
        "keyword": "",
        "dialog_text": "",
        "speaker": actor_id
    }

    result = accessor.behavior_manager.invoke_behavior(
        npc, "entity_dialog", accessor, context
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
            primary=f"{npc.name} doesn't seem interested in conversation.",
            data=npc_data
        )
