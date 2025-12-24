"""
Narrator Helpers - Fragment selection utilities for narration.

This module provides helper functions for selecting fragments from entity
llm_context pools. These are used by handlers and infrastructure code
to populate fragments for the narrator.

Usage:
    from src.narrator_helpers import select_state_fragments, build_reaction

    # In a handler:
    fragments = select_state_fragments(entity, "hostile", max_count=2)

    # For multi-entity reactions:
    reaction = build_reaction(entity, "hostile", "confrontation")
"""

import random
from typing import Any, Dict, List, Optional


class RepetitionBuffer:
    """
    Track recently used fragments to avoid repetition.

    Maintains a ring buffer of recently-used fragment keys.
    When selecting new fragments, those in the buffer can be excluded.
    """

    def __init__(self, size: int = 10):
        """
        Initialize RepetitionBuffer.

        Args:
            size: Maximum number of fragments to remember
        """
        self.buffer: List[str] = []
        self.size = size

    def add(self, fragment: str) -> None:
        """
        Add a fragment to the buffer.

        If buffer is full, oldest fragment is evicted.

        Args:
            fragment: Fragment string to remember
        """
        if len(self.buffer) >= self.size:
            self.buffer.pop(0)  # Remove oldest
        self.buffer.append(fragment)

    def contains(self, fragment: str) -> bool:
        """
        Check if fragment was recently used.

        Args:
            fragment: Fragment string to check

        Returns:
            True if fragment is in buffer
        """
        return fragment in self.buffer

    def filter_pool(self, pool: List[str]) -> List[str]:
        """
        Return pool with recently-used fragments removed.

        Preserves order of remaining items.

        Args:
            pool: List of fragments to filter

        Returns:
            Filtered list with recently-used fragments removed
        """
        return [f for f in pool if f not in self.buffer]


def _get_llm_context(entity: Any) -> Dict[str, Any]:
    """
    Get llm_context from entity properties.

    Args:
        entity: Entity with properties dict

    Returns:
        llm_context dict or empty dict if not found
    """
    if not hasattr(entity, "properties"):
        return {}
    properties = entity.properties
    if not isinstance(properties, dict):
        return {}
    llm_context = properties.get("llm_context", {})
    if not isinstance(llm_context, dict):
        return {}
    return llm_context


def select_state_fragments(
    entity: Any,
    state: str,
    max_count: int = 2,
    repetition_buffer: Optional[RepetitionBuffer] = None
) -> List[str]:
    """
    Select fragments from entity's llm_context.state_fragments[state].

    Args:
        entity: Entity with properties.llm_context.state_fragments
        state: Current state name (e.g., 'hostile', 'friendly')
        max_count: Maximum fragments to select
        repetition_buffer: Recently used fragments to avoid

    Returns:
        List of selected fragment strings (may be empty)
    """
    llm_context = _get_llm_context(entity)
    state_fragments = llm_context.get("state_fragments", {})

    if not isinstance(state_fragments, dict):
        return []

    pool = state_fragments.get(state, [])
    if not isinstance(pool, list):
        return []

    # Filter out recently used
    if repetition_buffer:
        pool = repetition_buffer.filter_pool(pool)

    if not pool:
        return []

    # Random selection
    selected = list(pool)
    random.shuffle(selected)
    result = selected[:max_count]

    # Add selected to buffer
    if repetition_buffer:
        for frag in result:
            repetition_buffer.add(frag)

    return result


def select_action_fragments(
    entity: Any,
    verb: str,
    verbosity: str = "full",
    repetition_buffer: Optional[RepetitionBuffer] = None
) -> Dict[str, Any]:
    """
    Select fragments from entity's llm_context.action_fragments[verb].

    Args:
        entity: Entity with properties.llm_context.action_fragments
        verb: Action verb (e.g., 'unlock', 'open', 'give')
        verbosity: 'brief' or 'full'
        repetition_buffer: Recently used fragments to avoid

    Returns:
        Dict with 'action_core' (str) and 'action_color' (list[str])
        Empty dict if no fragments found
    """
    llm_context = _get_llm_context(entity)
    action_fragments = llm_context.get("action_fragments", {})

    if not isinstance(action_fragments, dict):
        return {}

    verb_fragments = action_fragments.get(verb, {})
    if not isinstance(verb_fragments, dict):
        return {}

    result: Dict[str, Any] = {}

    # Select core fragment (always 1)
    core_pool = verb_fragments.get("core", [])
    if isinstance(core_pool, list) and core_pool:
        if repetition_buffer:
            core_pool = repetition_buffer.filter_pool(core_pool)
        if core_pool:
            selected_core = random.choice(core_pool)
            result["action_core"] = selected_core
            if repetition_buffer:
                repetition_buffer.add(selected_core)

    # Select color fragments (0 for brief, 1-2 for full)
    if verbosity == "full":
        color_pool = verb_fragments.get("color", [])
        if isinstance(color_pool, list) and color_pool:
            if repetition_buffer:
                color_pool = repetition_buffer.filter_pool(color_pool)
            if color_pool:
                shuffled = list(color_pool)
                random.shuffle(shuffled)
                # Select 1-2 color fragments
                count = min(2, len(shuffled))
                result["action_color"] = shuffled[:count]
                if repetition_buffer:
                    for frag in result["action_color"]:
                        repetition_buffer.add(frag)
            else:
                result["action_color"] = []
        else:
            result["action_color"] = []
    else:
        # Brief: no color
        result["action_color"] = []

    # Only return non-empty result with actual content
    if "action_core" not in result:
        return {}
    return result


def select_traits(
    entity: Any,
    max_count: int = 2,
    repetition_buffer: Optional[RepetitionBuffer] = None
) -> List[str]:
    """
    Select traits from entity's llm_context.traits pool.

    Args:
        entity: Entity with properties.llm_context.traits
        max_count: Maximum traits to select
        repetition_buffer: Recently used fragments to avoid

    Returns:
        List of selected trait strings (may be empty)
    """
    llm_context = _get_llm_context(entity)
    traits = llm_context.get("traits", [])

    if not isinstance(traits, list):
        return []

    pool = list(traits)

    # Filter out recently used
    if repetition_buffer:
        pool = repetition_buffer.filter_pool(pool)

    if not pool:
        return []

    # Random selection
    random.shuffle(pool)
    result = pool[:max_count]

    # Add selected to buffer
    if repetition_buffer:
        for trait in result:
            repetition_buffer.add(trait)

    return result


def build_reaction(
    entity: Any,
    state: str,
    response: str,
    max_fragments: int = 2
) -> Dict[str, Any]:
    """
    Build a reaction dict for multi-entity scenes.

    This is a convenience function for building the reaction structure
    expected by EventResult.context["reaction"] or HandlerResult.reactions.

    Args:
        entity: Entity that is reacting
        state: Current state (e.g., "hostile", "nervous")
        response: Response type (e.g., "confrontation", "avoidance")
        max_fragments: Maximum fragments to include

    Returns:
        Dict suitable for EventResult.context["reaction"]
    """
    # Get entity ID and name
    entity_id = getattr(entity, "id", "unknown")
    entity_name = getattr(entity, "name", "Unknown")

    # Select fragments for this state
    fragments = select_state_fragments(entity, state, max_count=max_fragments)

    return {
        "entity": entity_id,
        "entity_name": entity_name,
        "state": state,
        "fragments": fragments,
        "response": response
    }
