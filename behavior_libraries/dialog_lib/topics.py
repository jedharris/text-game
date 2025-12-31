"""Topic management for NPC dialog.

Manages dialog topics, prerequisites, and state changes when topics are discussed.

NPC configuration (in actor.properties):
{
    "dialog_topics": {
        "infection": {
            "keywords": ["infection", "sick", "illness"],
            "summary": "The scholar explains the infection.",
            "unlocks_topics": ["cure"],
            "sets_flags": {"knows_about_infection": true},
            "requires_flags": {},
            "requires_items": [],
            "requires_trust": 2,  // Requires NPC trust >= 2
            "requires_state": "friendly",  // Requires NPC in this state
            "grants_items": [],
            "one_time": false
        }
    },
    "unlocked_topics": [],
    "default_topic_summary": "The NPC doesn't know about that."
}

Usage:
    from behavior_libraries.dialog_lib.topics import (
        get_available_topics, get_topic_hints,
        handle_ask_about, handle_talk_to
    )
"""
from src.types import ActorId
from src.infrastructure_utils import apply_trust_change

import importlib
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Cache for loaded handler functions
_topic_handler_cache: dict[str, Callable[..., Any]] = {}


def _load_topic_handler(handler_path: str) -> Callable[..., Any] | None:
    """Load a handler function from a module:function path.

    Args:
        handler_path: Path like "module.path:function_name"

    Returns:
        The handler function, or None if loading fails
    """
    if handler_path in _topic_handler_cache:
        return _topic_handler_cache[handler_path]

    try:
        if ":" not in handler_path:
            logger.warning(f"Invalid handler path (missing ':'): {handler_path}")
            return None

        module_path, func_name = handler_path.rsplit(":", 1)
        module = importlib.import_module(module_path)
        handler = getattr(module, func_name)
        _topic_handler_cache[handler_path] = handler
        return handler
    except (ValueError, ImportError, AttributeError) as e:
        logger.warning(f"Failed to load topic handler {handler_path}: {e}")
        return None


def clear_topic_handler_cache() -> None:
    """Clear the handler cache. Useful for testing."""
    _topic_handler_cache.clear()


@dataclass
class DialogResult:
    """Result of a dialog interaction.

    Fields:
        response: The NPC's response text.
                  Semantic type: ResponseText
    """
    success: bool
    response: str
    topic_name: Optional[str] = None


def get_available_topics(accessor, npc) -> List[str]:
    """
    Get topics the NPC can currently discuss.

    Filters topics based on:
    - Required flags being set
    - Required items in player inventory
    - Topic not being one_time and already discussed
    - Topic being unlocked (if unlocking is required)

    Args:
        accessor: StateAccessor instance
        npc: Actor object (the NPC)

    Returns:
        List of available topic names
    """
    player = accessor.get_actor(ActorId('player'))
    if not player:
        return []

    topics = npc.properties.get('dialog_topics', {})
    player_flags = player.properties.get('flags', {})
    player_inventory = player.inventory
    unlocked = npc.properties.get('unlocked_topics', [])
    discussed = npc.properties.get('discussed_topics', [])

    available = []
    for topic_name, topic in topics.items():
        # Skip non-dict entries (e.g., "handler" key)
        if not isinstance(topic, dict):
            continue

        # Check required flags
        required_flags = topic.get('requires_flags', {})
        flags_met = all(
            player_flags.get(flag) == value
            for flag, value in required_flags.items()
        )
        if not flags_met:
            continue

        # Check required items
        required_items = topic.get('requires_items', [])
        items_met = all(item in player_inventory for item in required_items)
        if not items_met:
            continue

        # Check one_time topics
        if topic.get('one_time') and topic_name in discussed:
            continue

        # Check requires_state (NPC state machine gating)
        requires_state = topic.get('requires_state')
        if requires_state is not None:
            state_machine = npc.properties.get('state_machine')
            if not state_machine:
                # Topic requires state but NPC has no state machine
                continue
            current_state = state_machine.get('current')
            # Support both single string and list of states
            if isinstance(requires_state, str):
                if current_state != requires_state:
                    continue
            elif isinstance(requires_state, list):
                if current_state not in requires_state:
                    continue

        # Check requires_trust (NPC trust level gating)
        requires_trust = topic.get('requires_trust')
        if requires_trust is not None:
            trust_state = npc.properties.get('trust_state', {})
            current_trust = trust_state.get('current', 0)
            if current_trust < requires_trust:
                continue

        available.append(topic_name)

    return available


def get_topic_hints(accessor, npc) -> List[str]:
    """
    Get hint keywords for available topics.

    Returns the first keyword of each available topic.

    Args:
        accessor: StateAccessor instance
        npc: Actor object (the NPC)

    Returns:
        List of hint keywords
    """
    available = get_available_topics(accessor, npc)
    topics = npc.properties.get('dialog_topics', {})

    hints = []
    for topic_name in available:
        topic = topics.get(topic_name, {})
        keywords = topic.get('keywords', [])
        if keywords:
            hints.append(keywords[0])

    return hints


def _find_topic_by_keyword(npc, query: str) -> Optional[str]:
    """
    Find a topic that matches the query keyword.

    Args:
        npc: Actor object
        query: Search text from player

    Returns:
        Topic name if found, None otherwise
    """
    topics = npc.properties.get('dialog_topics', {})
    query_lower = query.lower()

    for topic_name, topic in topics.items():
        # Skip non-dict entries (e.g., "handler" key)
        if not isinstance(topic, dict):
            continue
        keywords = topic.get('keywords', [])
        for keyword in keywords:
            if keyword.lower() in query_lower or query_lower in keyword.lower():
                return topic_name

    return None


def handle_ask_about(accessor, npc, topic_text: str) -> DialogResult:
    """
    Handle asking NPC about a topic.

    Args:
        accessor: StateAccessor instance
        npc: Actor object (the NPC)
        topic_text: The topic text from player's question

    Returns:
        DialogResult with success and message
    """
    player = accessor.get_actor(ActorId('player'))
    if not player:
        return DialogResult(success=False, response="No player found.")

    # Find matching topic
    topic_name = _find_topic_by_keyword(npc, topic_text)

    if not topic_name:
        # Use default response
        default_msg = npc.properties.get(
            'default_topic_summary',
            f"{npc.name} doesn't know about that."
        )
        return DialogResult(success=True, response=default_msg)

    topics = npc.properties.get('dialog_topics', {})
    topic = topics.get(topic_name, {})

    # Check if topic is available
    available = get_available_topics(accessor, npc)
    if topic_name not in available:
        default_msg = npc.properties.get(
            'default_topic_summary',
            f"{npc.name} doesn't know about that."
        )
        return DialogResult(success=True, response=default_msg)

    # Topic found and available - process it

    # Check for per-topic handler
    handler_path = topic.get('handler')
    if handler_path:
        handler = _load_topic_handler(handler_path)
        if handler:
            # Call handler with context
            context = {
                "keyword": topic_text,
                "topic_name": topic_name,
                "dialog_text": topic_text
            }
            result = handler(npc, accessor, context)
            # If handler returns feedback, use it
            if result.feedback:
                return DialogResult(
                    success=result.allow,
                    response=result.feedback,
                    topic_name=topic_name
                )
            # Handler returned no feedback - fall through to summary and effects
        else:
            logger.warning(f"Topic handler failed to load for {npc.id}.{topic_name}: {handler_path}")

    # Set flags
    sets_flags = topic.get('sets_flags', {})
    if 'flags' not in player.properties:
        player.properties['flags'] = {}
    for flag, value in sets_flags.items():
        player.properties['flags'][flag] = value

    # Unlock new topics
    unlocks = topic.get('unlocks_topics', [])
    if unlocks:
        if 'unlocked_topics' not in npc.properties:
            npc.properties['unlocked_topics'] = []
        for unlock_topic in unlocks:
            if unlock_topic not in npc.properties['unlocked_topics']:
                npc.properties['unlocked_topics'].append(unlock_topic)

    # Grant items
    grants_items = topic.get('grants_items', [])
    for item_id in grants_items:
        if item_id not in player.inventory:
            player.inventory.append(item_id)

    # Mark as discussed (for one_time topics)
    if topic.get('one_time'):
        if 'discussed_topics' not in npc.properties:
            npc.properties['discussed_topics'] = []
        if topic_name not in npc.properties['discussed_topics']:
            npc.properties['discussed_topics'].append(topic_name)

    # Apply trust_delta
    trust_delta = topic.get('trust_delta')
    if trust_delta is not None and trust_delta != 0:
        # Initialize trust_state if missing
        if 'trust_state' not in npc.properties:
            npc.properties['trust_state'] = {'current': 0}

        # Apply trust change using unified utility
        transitions = topic.get('trust_transitions', {})
        apply_trust_change(
            entity=npc,
            delta=trust_delta,
            transitions=transitions,
        )

    # Return summary
    summary = topic.get('summary', f"{npc.name} discusses {topic_name}.")
    return DialogResult(success=True, response=summary, topic_name=topic_name)


def handle_talk_to(accessor, npc) -> DialogResult:
    """
    Handle general talk - shows available topics.

    Args:
        accessor: StateAccessor instance
        npc: Actor object (the NPC)

    Returns:
        DialogResult listing available topics
    """
    hints = get_topic_hints(accessor, npc)

    if not hints:
        return DialogResult(
            success=True,
            response=f"{npc.name} has nothing to discuss right now."
        )

    topic_list = ', '.join(hints)
    return DialogResult(
        success=True,
        response=f"You could ask {npc.name} about: {topic_list}"
    )
