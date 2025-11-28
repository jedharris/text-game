"""Entity serialization for LLM communication.

Provides unified entity-to-dict conversion with automatic llm_context
handling and trait randomization.

This module consolidates entity serialization that was previously scattered
across llm_protocol.py (_entity_to_dict, _door_to_dict, etc.) and behavior
handlers. All entity serialization for LLM communication should use these
functions.
"""
import random
from typing import Any, Dict, Optional


def entity_to_dict(entity, include_llm_context: bool = True) -> Dict[str, Any]:
    """Convert any entity to a dict suitable for LLM communication.

    Handles: Item, Location, Actor, ExitDescriptor, Lock

    Args:
        entity: Entity object to serialize
        include_llm_context: If True, include llm_context with randomized traits

    Returns:
        Dict representation of entity
    """
    result = _serialize_core_fields(entity)

    if include_llm_context:
        _add_llm_context(result, entity)

    return result


def _serialize_core_fields(entity) -> Dict[str, Any]:
    """Serialize core fields based on entity type.

    Detects entity type by checking for characteristic attributes and
    serializes appropriately.
    """
    result = {}

    # All entities have id (except maybe ExitDescriptor)
    if hasattr(entity, 'id') and entity.id:
        result["id"] = entity.id

    # Most entities have name
    if hasattr(entity, 'name') and entity.name:
        result["name"] = entity.name

    # Most entities have description
    if hasattr(entity, 'description') and entity.description:
        result["description"] = entity.description

    # Determine entity type and add type-specific fields
    entity_type = _detect_entity_type(entity)
    if entity_type:
        result["type"] = entity_type

    # Door-specific fields (unified Item/Door model)
    if hasattr(entity, 'is_door') and entity.is_door:
        result["open"] = entity.door_open
        result["locked"] = entity.door_locked

    # Light source state
    if hasattr(entity, 'states'):
        states = entity.states
        if isinstance(states, dict) and states.get('lit'):
            result["lit"] = states['lit']

    # Provides light property
    if hasattr(entity, 'provides_light') and entity.provides_light:
        result["provides_light"] = True

    return result


def _detect_entity_type(entity) -> Optional[str]:
    """Detect entity type from its attributes.

    Returns:
        String type identifier or None if type is unclear
    """
    # Door item (unified model) - check before container since doors might have both
    if hasattr(entity, 'is_door') and entity.is_door:
        return "door"

    # Container item
    if hasattr(entity, 'container') and entity.container:
        return "container"

    # Actor (has inventory)
    if hasattr(entity, 'inventory'):
        return "actor"

    # Regular item (has portable attribute)
    if hasattr(entity, 'portable'):
        return "item"

    # Location (has exits)
    if hasattr(entity, 'exits'):
        return "location"

    # Lock (has opens_with)
    if hasattr(entity, 'opens_with'):
        return "lock"

    # ExitDescriptor (has 'to' and 'type' but not as entity type)
    if hasattr(entity, 'to') and hasattr(entity, 'type'):
        return "exit"

    return None


def _add_llm_context(result: Dict, entity) -> None:
    """Add llm_context with randomized traits.

    Randomizes trait order to encourage varied LLM narration.
    Copies the llm_context to avoid mutating the original entity.

    Args:
        result: Dict to add llm_context to
        entity: Entity to get llm_context from
    """
    llm_context = _get_llm_context(entity)

    if not llm_context:
        return

    # Copy to avoid mutation of original
    context_copy = dict(llm_context)

    # Randomize traits if present
    if 'traits' in context_copy and isinstance(context_copy['traits'], list):
        traits_copy = list(context_copy['traits'])
        random.shuffle(traits_copy)
        context_copy['traits'] = traits_copy

    result['llm_context'] = context_copy


def _get_llm_context(entity) -> Optional[Dict[str, Any]]:
    """Get llm_context from entity using appropriate accessor.

    Tries the llm_context property first (for Item, Location, ExitDescriptor
    which have property accessors), then falls back to properties dict.

    Args:
        entity: Entity to get llm_context from

    Returns:
        llm_context dict or None
    """
    # Try direct property accessor first (Item, Location, ExitDescriptor)
    # These have @property llm_context that accesses properties["llm_context"]
    if hasattr(entity, 'llm_context'):
        llm_context = entity.llm_context
        if llm_context:
            return llm_context

    # Fall back to properties dict (for entities that might store it differently)
    if hasattr(entity, 'properties') and isinstance(entity.properties, dict):
        return entity.properties.get('llm_context')

    return None


def serialize_for_handler_result(entity) -> Dict[str, Any]:
    """Serialize entity for inclusion in HandlerResult.data.

    Convenience function for behavior handlers. Always includes llm_context
    with randomized traits.

    Args:
        entity: Entity to serialize

    Returns:
        Dict suitable for HandlerResult.data
    """
    return entity_to_dict(entity, include_llm_context=True)
