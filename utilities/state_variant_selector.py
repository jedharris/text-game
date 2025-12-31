"""State variant selection for location narration.

The Context Builder (game engine) uses this module to select appropriate
state_variants based on game state. The Narration Model (LLM) receives
only the selected variant text.

See: docs/phase4_state_variant_design.md for full design
"""
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.state_manager import Location
    from src.types import ActorId, LocationId


def select_state_variant(
    llm_context: Dict[str, Any],
    location: "Location",
    world_state: Dict[str, Any],
    actor_id: "ActorId"
) -> Optional[str]:
    """Select best matching state_variant based on world state.

    Priority order:
    1. Location properties (set by environmental spreads)
    2. Global quest flags
    3. Visit history (first_visit vs revisit)
    4. None (use base traits only)

    Args:
        llm_context: Location's llm_context with state_variants
        location: Location entity
        world_state: state.extra dict with flags, visit_history, etc.
        actor_id: Current actor for visit history

    Returns:
        Selected variant text or None
    """
    variants = llm_context.get('state_variants', {})
    if not variants:
        return None

    # Priority 1: Location properties (environmental spreads)
    selected = _check_location_properties(variants, location)
    if selected:
        return selected

    # Priority 2: Global quest flags
    selected = _check_quest_flags(variants, world_state)
    if selected:
        return selected

    # Priority 3: Visit history
    selected = _check_visit_history(variants, location, world_state, actor_id)
    if selected:
        return selected

    # Priority 4: No variant
    return None


def _check_location_properties(
    variants: Dict[str, str],
    location: "Location"
) -> Optional[str]:
    """Check location properties for matching variants.

    Environmental spreads set location properties like:
    - infection_present: true
    - spore_level: "low", "medium", "high"
    - temperature: "freezing", "cold", "normal"
    """
    location_props = location.properties if hasattr(location, 'properties') else {}

    # Property keys to check (in priority order)
    property_checks = [
        'infection_present',  # Spore spread
        'spore_level',        # Spore spread progression
        'temperature',        # Cold spread (future)
        'flooded',            # Water level
        'toxic',              # Air quality
    ]

    for prop_key in property_checks:
        prop_value = location_props.get(prop_key)
        if prop_value is None:
            continue

        # Boolean properties: check if variant key exists
        if isinstance(prop_value, bool):
            if prop_value and prop_key in variants:
                return variants[prop_key]

        # String properties: check if value matches a variant key
        elif isinstance(prop_value, str):
            if prop_value in variants:
                return variants[prop_value]

    return None


def _check_quest_flags(
    variants: Dict[str, str],
    world_state: Dict[str, Any]
) -> Optional[str]:
    """Check global quest flags for matching variants.

    Quest completion handlers set flags like:
    - telescope_repaired: true
    - guardian_active: true
    - water_receding: true
    """
    flags = world_state.get('flags', {})

    # Quest flags in priority order (most specific first)
    quest_flag_checks = [
        'telescope_repaired',
        'telescope_active',
        'guardian_active',
        'golems_commanded',
        'golems_activated',
        'water_receding',
        'water_drained',
        'spore_mother_healed',
        'corruption_cleansed',
        'heart_destroyed',
        'heart_weakened',
        'lights_restored',
        'council_restored',
        'trade_restored',
        'merchants_returning',
    ]

    for flag_name in quest_flag_checks:
        # Check if flag is true (bool flags) or non-zero (int flags)
        if flags.get(flag_name):
            if flag_name in variants:
                return variants[flag_name]

    return None


def _check_visit_history(
    variants: Dict[str, str],
    location: "Location",
    world_state: Dict[str, Any],
    actor_id: "ActorId"
) -> Optional[str]:
    """Check visit history for first_visit vs revisit.

    Visit history is tracked per actor in world_state['visit_history'].
    """
    visit_history = world_state.get('visit_history', {})
    actor_key = str(actor_id)
    actor_visits = visit_history.get(actor_key, [])

    # First visit to this location
    if location.id not in actor_visits:
        if 'first_visit' in variants:
            return variants['first_visit']

    # Returning to familiar location
    if 'revisit' in variants:
        return variants['revisit']

    return None


def track_location_visit(
    world_state: Dict[str, Any],
    actor_id: "ActorId",
    location_id: "LocationId"
) -> None:
    """Track that an actor visited a location.

    Updates world_state['visit_history'] to record the visit.
    Should be called when actor enters a new location.

    Args:
        world_state: state.extra dict (mutated)
        actor_id: Actor who is visiting
        location_id: Location being visited
    """
    if 'visit_history' not in world_state:
        world_state['visit_history'] = {}

    actor_key = str(actor_id)
    if actor_key not in world_state['visit_history']:
        world_state['visit_history'][actor_key] = []

    # Add location if not already visited
    if location_id not in world_state['visit_history'][actor_key]:
        world_state['visit_history'][actor_key].append(location_id)
