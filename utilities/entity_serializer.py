"""Entity serialization for LLM communication.

Provides unified entity-to-dict conversion with automatic llm_context
handling and trait randomization.

This module consolidates entity serialization that was previously scattered
across llm_protocol.py (_entity_to_dict, _door_to_dict, etc.) and behavior
handlers. All entity serialization for LLM communication should use these
functions.
"""
import random
from typing import Any, Dict, Optional, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from src.state_manager import Item, Location, Actor, ExitDescriptor, Lock
    from src.state_accessor import StateAccessor
    from src.types import ActorId


def entity_to_dict(entity: Any, include_llm_context: bool = True,
                   max_traits: Optional[int] = None,
                   player_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convert any entity to a dict suitable for LLM communication.

    Handles: Item, Location, Actor, ExitDescriptor, Lock

    Args:
        entity: Entity object to serialize
        include_llm_context: If True, include llm_context with randomized traits
        max_traits: If set, limit traits to this count (after randomization).
                   Use for brief verbosity mode to reduce LLM output length.
        player_context: If set, compute spatial_relation based on player's
                       posture and focus. Dict with posture, focused_on keys.

    Returns:
        Dict representation of entity
    """
    result = _serialize_core_fields(entity)

    if include_llm_context:
        _add_llm_context(result, entity, max_traits=max_traits,
                        player_context=player_context)

    # Add spatial_relation if player has non-null posture
    if player_context and player_context.get("posture"):
        spatial_relation = _compute_spatial_relation(entity, player_context)
        if spatial_relation:
            result["spatial_relation"] = spatial_relation

    return result


def _compute_spatial_relation(entity: Any, player_context: Dict[str, Any]) -> Optional[str]:
    """Compute spatial relation between entity and player's position.

    Args:
        entity: Entity to compute relation for
        player_context: Dict with posture, focused_on, focused_entity_id keys

    Returns:
        Spatial relation string or None if not applicable
    """
    posture = player_context.get("posture")
    focused_on = player_context.get("focused_on")

    if not posture:
        return None

    entity_id = getattr(entity, 'id', None)
    entity_location = getattr(entity, 'location', None)

    # Check if this IS the focused entity
    if entity_id and entity_id == focused_on:
        return "within_reach"

    # Check if item is ON the focused surface (location == focused_on)
    if entity_location and entity_location == focused_on:
        return "within_reach"

    # For elevated postures (on_surface, climbing), items on floor are "below"
    if posture in ("on_surface", "climbing"):
        # Items directly in a location (not in/on something) are on floor
        # But NOT items in player inventory - those are in hand, not below
        # Check if location looks like an actor ID (doesn't start with "loc_" or "item_")
        is_in_location = entity_location and entity_location.startswith("loc_")
        if is_in_location:
            return "below"

    # Default for positioned player
    return "nearby"


def _serialize_core_fields(entity: Any) -> Dict[str, Any]:
    """Serialize core fields based on entity type.

    Detects entity type by checking for characteristic attributes and
    serializes appropriately.
    """
    result: Dict[str, Any] = {}

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

    # Exit-specific fields (destination)
    if hasattr(entity, 'to') and entity.to:
        result["destination"] = entity.to

    return result


def _detect_entity_type(entity: Any) -> Optional[str]:
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


def _select_item_state_variant(
    llm_context: Dict[str, Any],
    entity: Any
) -> Optional[Any]:
    """Select state variant for an item based on its properties.

    Checks entity properties in priority order:
    1. Door state (open, closed_locked, closed_unlocked)
    2. Light state (lit, unlit)
    3. Container state (open, closed)
    4. Generic state properties (broken, active, etc.)

    Returns:
        - str: state_note text if variant is a string
        - dict: traits dict if variant is a dict with "traits"
        - None: if no matching variant

    Examples:
        # Door with string variant
        state_variants = {
            "open": "door swings wide revealing stairs beyond"
        }
        Returns: "door swings wide revealing stairs beyond"

        # Torch with dict variant
        state_variants = {
            "lit": {"traits": ["flames dancing", "warm glow"]}
        }
        Returns: {"traits": ["flames dancing", "warm glow"]}
    """
    variants = llm_context.get('state_variants', {})
    if not variants:
        return None

    # Priority 1: Door state
    if hasattr(entity, 'door_open') or hasattr(entity, 'door_locked'):
        state_key = _compute_door_state_key(entity)
        if state_key and state_key in variants:
            return variants[state_key]

    # Priority 2: Light state
    if hasattr(entity, 'states'):
        states = entity.states
        if isinstance(states, dict) and states.get('lit') is not None:
            state_key = "lit" if states['lit'] else "unlit"
            if state_key in variants:
                return variants[state_key]

    # Priority 3: Container state
    if hasattr(entity, 'container'):
        container = entity.container
        if isinstance(container, dict) and 'open' in container:
            state_key = "open" if container['open'] else "closed"
            if state_key in variants:
                return variants[state_key]

    # Priority 4: Generic properties
    # Check common state properties
    if hasattr(entity, 'properties'):
        props = entity.properties
        if isinstance(props, dict):
            for prop_name in ['broken', 'active', 'powered', 'sealed', 'restored', 'mat_state']:
                if prop_name in props:
                    # Boolean properties
                    if isinstance(props[prop_name], bool):
                        state_key = prop_name if props[prop_name] else f"not_{prop_name}"
                        if state_key in variants:
                            return variants[state_key]
                    # String properties (e.g., "damaged", "intact", "examined_once")
                    elif isinstance(props[prop_name], str):
                        if props[prop_name] in variants:
                            return variants[props[prop_name]]

    return None


def _compute_door_state_key(entity: Any) -> Optional[str]:
    """Compute door state key: open | closed_locked | closed_unlocked.

    Args:
        entity: Entity with door_open and door_locked attributes

    Returns:
        State key string or None if not a door
    """
    if not hasattr(entity, 'door_open'):
        return None

    if entity.door_open:
        return "open"
    elif hasattr(entity, 'door_locked') and entity.door_locked:
        return "closed_locked"
    else:
        return "closed_unlocked"


def _select_exit_state_variant(
    llm_context: Dict[str, Any],
    exit_entity: Any,
    accessor: Optional[Any]
) -> Optional[str]:
    """Select state variant for exit based on associated door state.

    If exit has door_id, checks door state and selects variant:
    - "door_open" if door is open
    - "door_closed" if door is closed or locked

    This allows exits (like stairs) to describe the door state at the far end.
    For example: "stairs descend to a closed door at the bottom"

    Args:
        llm_context: Exit's llm_context with state_variants
        exit_entity: Exit entity with door_id attribute
        accessor: Optional StateAccessor for door lookup

    Returns:
        State note string or None
    """
    variants = llm_context.get('state_variants', {})
    if not variants or not accessor:
        return None

    # Check if exit has associated door
    if hasattr(exit_entity, 'door_id') and exit_entity.door_id:
        try:
            door = accessor.get_door_item(exit_entity.door_id)
            state_key = "door_open" if door.door_open else "door_closed"
            if state_key in variants:
                return str(variants[state_key])
        except (KeyError, AttributeError):
            # Door doesn't exist or accessor missing method - fail gracefully
            pass

    return None


def _add_llm_context(result: Dict[str, Any], entity: Any,
                     max_traits: Optional[int] = None,
                     player_context: Optional[Dict[str, Any]] = None) -> None:
    """Add llm_context with trait randomization, state variant, and perspective variant selection.

    Randomizes trait order to encourage varied LLM narration.
    Copies the llm_context to avoid mutating the original entity.
    Selects state variant based on entity properties (door state, light state, etc.).
    Selects perspective variant based on player posture and focus.

    Args:
        result: Dict to add llm_context to
        entity: Entity to get llm_context from
        max_traits: If set, limit traits to this count after randomization
        player_context: If set, used for perspective_variants selection
    """
    llm_context = _get_llm_context(entity)

    if not llm_context:
        return

    # Copy to avoid mutation of original
    context_copy = dict(llm_context)

    # Select state variant for items (doors, lights, containers, etc.)
    state_variant = _select_item_state_variant(context_copy, entity)

    if state_variant:
        # Check if variant is string (state_note) or dict (trait replacement)
        if isinstance(state_variant, str):
            # String variant: Add as state_note, keep existing traits
            result['state_note'] = state_variant

            # Randomize existing traits
            if 'traits' in context_copy and isinstance(context_copy['traits'], list):
                traits_copy = list(context_copy['traits'])
                random.shuffle(traits_copy)
                if max_traits is not None:
                    traits_copy = traits_copy[:max_traits]
                context_copy['traits'] = traits_copy

        elif isinstance(state_variant, dict) and 'traits' in state_variant:
            # Dict variant: Replace traits entirely
            traits_copy = list(state_variant['traits'])
            random.shuffle(traits_copy)
            if max_traits is not None:
                traits_copy = traits_copy[:max_traits]
            context_copy['traits'] = traits_copy
    else:
        # No state variant: Use base traits
        if 'traits' in context_copy and isinstance(context_copy['traits'], list):
            traits_copy = list(context_copy['traits'])
            random.shuffle(traits_copy)
            if max_traits is not None:
                traits_copy = traits_copy[:max_traits]
            context_copy['traits'] = traits_copy

    # Select perspective variant if available
    perspective_note = _select_perspective_variant(context_copy, player_context)
    if perspective_note:
        result['perspective_note'] = perspective_note

    # Remove variant dicts from output - LLM should only see selected variants
    context_copy.pop('perspective_variants', None)
    context_copy.pop('state_variants', None)

    result['llm_context'] = context_copy


def _select_perspective_variant(llm_context: Dict[str, Any],
                                player_context: Optional[Dict[str, Any]]) -> Optional[str]:
    """Select best matching perspective variant based on player context.

    Looks for perspective_variants in llm_context and selects the best match:
    1. Try exact match: "<posture>:<focused_on>" (e.g., "on_surface:item_table")
    2. Try posture match: "<posture>" (e.g., "climbing")
    3. Fall back to "default" if present

    Args:
        llm_context: The entity's llm_context dict
        player_context: Player positioning context with posture and focused_on

    Returns:
        Selected perspective variant text, or None if no match
    """
    variants = llm_context.get('perspective_variants')
    if not variants or not isinstance(variants, dict):
        return None

    if not player_context:
        # No player context - try default only
        return cast(Optional[str], variants.get('default'))

    posture = player_context.get('posture')
    focused_on = player_context.get('focused_on')

    # 1. Try exact match: "posture:focused_on"
    if posture and focused_on:
        exact_key = f"{posture}:{focused_on}"
        if exact_key in variants:
            return cast(str, variants[exact_key])

    # 2. Try posture-only match
    if posture and posture in variants:
        return cast(str, variants[posture])

    # 3. Fall back to default
    return cast(Optional[str], variants.get('default'))


def _get_llm_context(entity: Any) -> Optional[Dict[str, Any]]:
    """Get llm_context from entity using appropriate accessor.

    Tries the llm_context property first (for Item, Location, ExitDescriptor
    which have property accessors), then falls back to properties dict,
    and finally checks traits dict for Exit entities.

    Args:
        entity: Entity to get llm_context from

    Returns:
        llm_context dict or None
    """
    # Try direct property accessor first (Item, Location, ExitDescriptor)
    # These have @property llm_context that accesses properties["llm_context"]
    if hasattr(entity, 'llm_context'):
        llm_context = cast(Optional[Dict[str, Any]], getattr(entity, 'llm_context'))
        if llm_context:
            return llm_context

    # Fall back to properties dict (for entities that might store it differently)
    if hasattr(entity, 'properties') and isinstance(entity.properties, dict):
        llm_context = entity.properties.get('llm_context')
        if llm_context:
            return cast(Dict[str, Any], llm_context)

    # For Exit entities, check traits dict
    if hasattr(entity, 'traits') and isinstance(entity.traits, dict):
        return cast(Optional[Dict[str, Any]], entity.traits.get('llm_context'))

    return None


def _build_player_context(accessor: "StateAccessor", actor_id: "ActorId") -> Dict[str, Any]:
    """Build player context dict from accessor and actor_id.

    Args:
        accessor: StateAccessor for state queries
        actor_id: ID of the actor

    Returns:
        Dict with posture and focused_on keys
    """
    actor = accessor.get_actor(actor_id)  # Raises KeyError if not found
    return {
        "posture": actor.properties.get("posture"),
        "focused_on": actor.properties.get("focused_on")
    }


def serialize_for_handler_result(
    entity: Any,
    accessor: Optional["StateAccessor"] = None,
    actor_id: Optional["ActorId"] = None
) -> Dict[str, Any]:
    """Serialize entity for inclusion in HandlerResult.data.

    Convenience function for behavior handlers. Always includes llm_context
    with randomized traits. When accessor and actor_id are provided, also
    computes spatial_relation and selects appropriate perspective_variant
    based on the actor's current posture.

    Args:
        entity: Entity to serialize
        accessor: Optional StateAccessor for player context
        actor_id: Optional actor ID for player context

    Returns:
        Dict suitable for HandlerResult.data
    """
    player_context = None
    if accessor is not None and actor_id is not None:
        player_context = _build_player_context(accessor, actor_id)

    return entity_to_dict(entity, include_llm_context=True, player_context=player_context)
