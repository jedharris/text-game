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
from utilities.entity_serializer import serialize_for_handler_result
from behavior_libraries.dialog_lib.topics import (
    get_topic_hints,
    handle_ask_about,
    handle_talk_to,
)

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
            "synonyms": ["speak", "converse", "chat", "tell", "say"],
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
    Handle 'ask <npc> about <topic>' or 'ask about <topic>' command.

    If no NPC is specified (e.g., "ask about infection") and there's exactly
    one NPC with dialog_topics in the location, that NPC is used automatically.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, target, raw_input

    Returns:
        HandlerResult with success and message
    """
    actor_id = ActorId(action.get('actor_id', ActorId("player")))
    npc_name = action.get('object')
    topic = action.get('indirect_object') or action.get('raw_after_preposition', '')

    # Handle "ask about X" (no NPC specified, topic is in object position)
    # In this case, object might be the topic, not the NPC
    if isinstance(npc_name, WordEntry) and not topic:
        # "ask about X" parses as object=X with no indirect_object
        # Check if there's a single NPC we can target
        npc = find_only_npc_in_location(accessor, actor_id)
        if npc:
            # Use the object as the topic
            topic = npc_name
            npc_name = None
        else:
            return HandlerResult(success=False, primary=f"Ask {get_display_name(npc_name)} about what?")

    if not isinstance(npc_name, WordEntry):
        # No NPC specified - try to find the only NPC in the location
        npc = find_only_npc_in_location(accessor, actor_id)
        if not npc:
            return HandlerResult(success=False, primary="Ask who?")
    else:
        # Find the named NPC
        npc = find_accessible_actor(accessor, npc_name, actor_id)
        if not npc:
            return HandlerResult(success=False, primary=f"You don't see any {get_display_name(npc_name)} here.")

    if not topic:
        return HandlerResult(success=False, primary=f"Ask {npc.name} about what?")

    # Serialize NPC for narrator context (even for failures, narrator needs context)
    npc_data = serialize_for_handler_result(npc, accessor, actor_id)

    # Check if NPC has dialog topics
    if 'dialog_topics' not in npc.properties:
        return HandlerResult(
            success=False,
            primary=f"{npc.name} doesn't seem interested in conversation.",
            data=npc_data
        )

    dialog_topics = npc.properties['dialog_topics']

    # Note: For 'ask' commands, we do NOT include available_topics in npc_data
    # because the player is asking about a specific topic, not asking for a list.
    # Only 'talk' commands show the topic list.

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
            return HandlerResult(success=result.allow, primary=feedback, data=npc_data)
        else:
            logger.warning(f"Dialog handler failed to load for {npc.id}: {handler_path}")

    # Handle the ask - convert topic to string if it's a WordEntry
    topic_str = topic.word if isinstance(topic, WordEntry) else str(topic)
    result = handle_ask_about(accessor, npc, topic_str)

    return HandlerResult(success=result.success, primary=result.response, data=npc_data)


def handle_talk(accessor, action: Dict) -> HandlerResult:
    """
    Handle 'talk to <npc>' command.

    If no NPC is specified and there's exactly one NPC with dialog_topics
    in the location, that NPC is used automatically.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, target

    Returns:
        HandlerResult with success and message
    """
    actor_id = ActorId(action.get('actor_id', ActorId("player")))
    # Try indirect_object first (from "talk to X"), then object
    npc_name = action.get('indirect_object') or action.get('object')

    # If no NPC specified, try to find the only NPC in the location
    if not isinstance(npc_name, WordEntry):
        npc = find_only_npc_in_location(accessor, actor_id)
        if not npc:
            return HandlerResult(success=False, primary="Talk to whom?")
    else:
        # Find the named NPC
        npc = find_accessible_actor(accessor, npc_name, actor_id)
        if not npc:
            return HandlerResult(success=False, primary=f"You don't see any {get_display_name(npc_name)} here.")

    # Serialize NPC for narrator context (even for failures, narrator needs context)
    npc_data = serialize_for_handler_result(npc, accessor, actor_id)

    # Check if NPC has dialog topics
    if 'dialog_topics' not in npc.properties:
        return HandlerResult(
            success=False,
            primary=f"{npc.name} doesn't seem interested in conversation.",
            data=npc_data
        )

    dialog_topics = npc.properties['dialog_topics']

    # Get available topic hints for narrator context
    available_topics = get_topic_hints(accessor, npc)
    if available_topics:
        npc_data["available_topics"] = available_topics

    # Check for handler escape hatch
    handler_path = dialog_topics.get('handler')
    if handler_path:
        handler = _load_handler(handler_path)
        if handler:
            # Call handler with empty keyword for general talk
            context = {"keyword": "", "dialog_text": ""}
            result = handler(npc, accessor, context)
            # If handler returns feedback, use it; otherwise fall through to data-driven topics
            if result.feedback:
                return HandlerResult(success=result.allow, primary=result.feedback, data=npc_data)
            # Handler returned no feedback - fall through to data-driven topic listing
        else:
            logger.warning(f"Dialog handler failed to load for {npc.id}: {handler_path}")

    # Handle the talk - list available topics from data-driven config
    result = handle_talk_to(accessor, npc)

    return HandlerResult(success=result.success, primary=result.response, data=npc_data)


def find_only_npc_in_location(accessor, actor_id: ActorId = ActorId("player")):
    """
    Find the only NPC in the player's location (for implicit targeting).

    Args:
        accessor: StateAccessor instance
        actor_id: ID of actor doing the finding

    Returns:
        Actor object if exactly one NPC in location, None otherwise
    """
    actor = accessor.get_actor(actor_id)
    if not actor:
        return None

    location = actor.location
    npcs = []

    for aid, a in accessor.game_state.actors.items():
        if aid == actor_id:
            continue
        if a.location != location:
            continue
        # Only include NPCs with dialog_topics
        if 'dialog_topics' in a.properties:
            npcs.append(a)

    # Return the NPC only if there's exactly one
    if len(npcs) == 1:
        return npcs[0]
    return None


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
