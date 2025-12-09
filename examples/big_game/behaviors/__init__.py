"""Game-specific behaviors for The Shattered Meridian.

This package contains custom behaviors that are specific to this game
and don't belong in the shared behavior_libraries.

Modules:
- regions: Region management and area-wide effects
- factions: Faction reputation system
- world_events: Cross-region events and deadlines
- npc_specifics: Unique NPC behaviors (The Echo, etc.)
"""

from .regions import (
    get_region_for_location,
    get_region_state,
    purify_region,
    corrupt_region,
    is_region_purified,
)

from .factions import (
    get_faction_reputation,
    modify_faction_reputation,
    get_faction_for_actor,
    get_faction_disposition,
)

from .world_events import (
    initialize_world_events,
    check_ending_conditions,
    cancel_spore_spread,
    cancel_cold_spread,
)

__all__ = [
    # Regions
    'get_region_for_location',
    'get_region_state',
    'purify_region',
    'corrupt_region',
    'is_region_purified',
    # Factions
    'get_faction_reputation',
    'modify_faction_reputation',
    'get_faction_for_actor',
    'get_faction_disposition',
    # World events
    'initialize_world_events',
    'check_ending_conditions',
    'cancel_spore_spread',
    'cancel_cold_spread',
]
