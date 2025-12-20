"""Command handlers for dialog commands.

Handles 'ask' and 'talk' commands for NPC dialog.

Commands:
    ask <npc> about <topic>  - Ask NPC about specific topic
    talk to <npc>            - Show available topics

Usage:
    from behavior_libraries.dialog_lib.handlers import (
        handle_ask, handle_talk
    )
"""

from typing import Dict, Optional

from src.action_types import ActionDict
from src.state_accessor import HandlerResult
from src.word_entry import WordEntry
from src.types import ActorId
from utilities.utils import name_matches
from utilities.handler_utils import get_display_name
from behavior_libraries.dialog_lib.topics import handle_ask_about, handle_talk_to


# Vocabulary extension
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
    """
    Handle 'ask <npc> about <topic>' command.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, target, raw_input

    Returns:
        HandlerResult with success and message
    """
    actor_id = ActorId(action.get('actor_id', ActorId("player")))
    npc_name = action.get('object')
    topic = action.get('indirect_object') or action.get('raw_after_preposition', '')

    if not isinstance(npc_name, WordEntry):
        return HandlerResult(success=False, primary="Ask who?")

    if not topic:
        return HandlerResult(success=False, primary=f"Ask {get_display_name(npc_name)} about what?")

    # Find the NPC
    npc = find_accessible_actor(accessor, npc_name, actor_id)
    if not npc:
        return HandlerResult(success=False, primary=f"You don't see any {get_display_name(npc_name)} here.")

    # Check if NPC has dialog topics
    if 'dialog_topics' not in npc.properties:
        return HandlerResult(
            success=False,
            primary=f"{npc.name} doesn't seem interested in conversation."
        )

    # Handle the ask - convert topic to string if it's a WordEntry
    topic_str = topic.word if isinstance(topic, WordEntry) else str(topic)
    result = handle_ask_about(accessor, npc, topic_str)

    return HandlerResult(success=result.success, primary=result.response)


def handle_talk(accessor, action: Dict) -> HandlerResult:
    """
    Handle 'talk to <npc>' command.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, target

    Returns:
        HandlerResult with success and message
    """
    actor_id = ActorId(action.get('actor_id', ActorId("player")))
    # Try indirect_object first (from "talk to X"), then object
    npc_name = action.get('indirect_object') or action.get('object')

    if not isinstance(npc_name, WordEntry):
        return HandlerResult(success=False, primary="Talk to whom?")

    # Find the NPC
    npc = find_accessible_actor(accessor, npc_name, actor_id)
    if not npc:
        return HandlerResult(success=False, primary=f"You don't see any {get_display_name(npc_name)} here.")

    # Check if NPC has dialog topics
    if 'dialog_topics' not in npc.properties:
        return HandlerResult(
            success=False,
            primary=f"{npc.name} doesn't seem interested in conversation."
        )

    # Handle the talk
    result = handle_talk_to(accessor, npc)

    return HandlerResult(success=result.success, primary=result.response)


def find_accessible_actor(accessor, name: WordEntry, actor_id: ActorId = ActorId("player")):
    """
    Find an actor accessible to the specified actor.

    Args:
        accessor: StateAccessor instance
        name: WordEntry for actor to find
        actor_id: ID of actor doing the finding

    Returns:
        Actor object if found, None otherwise
    """
    actor = accessor.get_actor(actor_id)
    if not actor:
        return None

    location = actor.location

    # Search by ID first
    for aid, a in accessor.game_state.actors.items():
        if aid == actor_id:
            continue
        if a.location != location:
            continue
        if name_matches(name, aid):
            return a

    # Search by name
    for aid, a in accessor.game_state.actors.items():
        if aid == actor_id:
            continue
        if a.location != location:
            continue
        if name_matches(name, a.name):
            return a

    return None
