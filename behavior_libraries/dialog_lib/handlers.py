"""Command handlers for dialog commands.

Handles 'ask' and 'talk' commands for NPC dialog.

Commands:
    ask <npc> about <topic>  - Ask NPC about specific topic
    talk to <npc>            - Show available topics

Supports two modes:
1. Data-driven: NPC has dialog_topics with keywords and responses
2. Handler escape hatch: NPC has dialog_topics with "handler" key pointing
   to a Python function that handles all dialog for that NPC

Usage:
    from behavior_libraries.dialog_lib.handlers import (
        handle_ask, handle_talk
    )
"""

from typing import Any, Callable, Dict

from src.state_accessor import HandlerResult
from src.word_entry import WordEntry
from src.types import ActorId
from utilities.utils import name_matches
from utilities.handler_utils import get_display_name
from behavior_libraries.dialog_lib.topics import handle_ask_about, handle_talk_to

# Import handler loading utility
import importlib
import logging

logger = logging.getLogger(__name__)

# Cache for loaded handler functions
_handler_cache: dict[str, Callable[..., Any]] = {}


def _load_handler(handler_path: str) -> Callable[..., Any] | None:
    """Load a handler function from a module:function path.

    Args:
        handler_path: Path like "module.path:function_name"

    Returns:
        The handler function, or None if loading fails
    """
    if handler_path in _handler_cache:
        return _handler_cache[handler_path]

    try:
        if ":" not in handler_path:
            logger.warning(f"Invalid handler path (missing ':'): {handler_path}")
            return None

        module_path, func_name = handler_path.rsplit(":", 1)
        module = importlib.import_module(module_path)
        handler = getattr(module, func_name)
        _handler_cache[handler_path] = handler
        return handler
    except (ValueError, ImportError, AttributeError) as e:
        logger.warning(f"Failed to load dialog handler {handler_path}: {e}")
        return None


def clear_dialog_handler_cache() -> None:
    """Clear the handler cache. Useful for testing."""
    _handler_cache.clear()


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

    dialog_topics = npc.properties['dialog_topics']

    # Check for handler escape hatch
    handler_path = dialog_topics.get('handler')
    if handler_path:
        handler = _load_handler(handler_path)
        if handler:
            # Call handler with context - handlers return EventResult
            topic_str = topic.word if isinstance(topic, WordEntry) else str(topic)
            context = {"keyword": topic_str, "dialog_text": topic_str}
            result = handler(npc, accessor, context)
            # Convert EventResult to HandlerResult
            feedback = result.feedback if result.feedback else f"{npc.name} has nothing to say about that."
            return HandlerResult(success=result.allow, primary=feedback)
        else:
            logger.warning(f"Dialog handler failed to load for {npc.id}: {handler_path}")

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

    dialog_topics = npc.properties['dialog_topics']

    # Check for handler escape hatch
    handler_path = dialog_topics.get('handler')
    if handler_path:
        handler = _load_handler(handler_path)
        if handler:
            # Call handler with empty keyword for general talk
            context = {"keyword": "", "dialog_text": ""}
            result = handler(npc, accessor, context)
            # Convert EventResult to HandlerResult
            feedback = result.feedback if result.feedback else f"{npc.name} has nothing to say right now."
            return HandlerResult(success=result.allow, primary=feedback)
        else:
            logger.warning(f"Dialog handler failed to load for {npc.id}: {handler_path}")

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
