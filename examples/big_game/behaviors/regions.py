"""Region management for The Shattered Meridian.

Handles region-wide state changes like purification and corruption spreading.

Region definitions are stored in GameState.extra['regions']:
{
    "fungal_depths": {
        "locations": ["loc_fd_cavern_entrance", "loc_fd_luminous_grotto", ...],
        "default_spore_level": "medium",
        "purified": false
    },
    "beast_wilds": {
        "locations": ["loc_bw_forest_edge", ...],
        "purified": false
    },
    ...
}

Usage:
    from big_game.behaviors.regions import (
        get_region_for_location, get_region_state,
        purify_region, corrupt_region,
        apply_region_effect_to_location
    )
"""

from typing import Dict, List, Optional

from src.behavior_manager import EventResult


# Region IDs for reference
REGION_FUNGAL_DEPTHS = "fungal_depths"
REGION_BEAST_WILDS = "beast_wilds"
REGION_FROZEN_REACHES = "frozen_reaches"
REGION_SUNKEN_DISTRICT = "sunken_district"
REGION_MERIDIAN_NEXUS = "meridian_nexus"
REGION_CIVILIZED_REMNANTS = "civilized_remnants"


def get_regions(accessor) -> Dict:
    """
    Get all region definitions.

    Args:
        accessor: StateAccessor instance

    Returns:
        Dict of region_id -> region definition
    """
    return accessor.game_state.extra.get('regions', {})


def get_region_for_location(accessor, location_id: str) -> Optional[str]:
    """
    Find which region a location belongs to.

    Args:
        accessor: StateAccessor instance
        location_id: ID of the location

    Returns:
        Region ID if found, None otherwise
    """
    regions = get_regions(accessor)

    for region_id, region_def in regions.items():
        if location_id in region_def.get('locations', []):
            return region_id

    return None


def get_region_state(accessor, region_id: str) -> Dict:
    """
    Get current state of a region.

    Args:
        accessor: StateAccessor instance
        region_id: ID of the region

    Returns:
        Region state dict, or empty dict if region not found
    """
    regions = get_regions(accessor)
    return regions.get(region_id, {})


def is_region_purified(accessor, region_id: str) -> bool:
    """
    Check if a region has been purified.

    Args:
        accessor: StateAccessor instance
        region_id: ID of the region

    Returns:
        True if purified, False otherwise
    """
    state = get_region_state(accessor, region_id)
    return state.get('purified', False)


def purify_region(accessor, region_id: str) -> List[str]:
    """
    Purify a region, removing corruption from all locations.

    Args:
        accessor: StateAccessor instance
        region_id: ID of the region to purify

    Returns:
        List of messages describing what changed
    """
    regions = accessor.game_state.extra.get('regions', {})
    region_def = regions.get(region_id)

    if not region_def:
        return [f"Unknown region: {region_id}"]

    messages = []

    # Mark region as purified
    region_def['purified'] = True

    # Apply purification to all locations in region
    for loc_id in region_def.get('locations', []):
        location = accessor.get_location(loc_id)
        if location:
            # Clear corruption effects based on region type
            if region_id == REGION_FUNGAL_DEPTHS:
                old_level = location.properties.get('spore_level', 'none')
                if old_level != 'none':
                    location.properties['spore_level'] = 'none'
                    messages.append(f"The spores in {location.name} dissipate.")

            elif region_id == REGION_FROZEN_REACHES:
                old_temp = location.properties.get('temperature', 'normal')
                if old_temp in ('cold', 'freezing'):
                    location.properties['temperature'] = 'normal'
                    messages.append(f"Warmth returns to {location.name}.")

            # Mark location itself as purified
            location.properties['purified'] = True

    # Set global flag
    flag_name = f"{region_id}_purified"
    accessor.game_state.extra.setdefault('flags', {})[flag_name] = True

    if not messages:
        messages.append(f"The {region_id.replace('_', ' ')} has been purified.")

    return messages


def corrupt_region(accessor, region_id: str, corruption_type: str) -> List[str]:
    """
    Apply corruption to a region.

    Args:
        accessor: StateAccessor instance
        region_id: ID of the region to corrupt
        corruption_type: Type of corruption ('spore', 'cold', 'flood')

    Returns:
        List of messages describing what changed
    """
    regions = accessor.game_state.extra.get('regions', {})
    region_def = regions.get(region_id)

    if not region_def:
        return [f"Unknown region: {region_id}"]

    messages = []

    # Apply corruption to all locations in region
    for loc_id in region_def.get('locations', []):
        location = accessor.get_location(loc_id)
        if location:
            if corruption_type == 'spore':
                old_level = location.properties.get('spore_level', 'none')
                if old_level == 'none':
                    location.properties['spore_level'] = 'low'
                    messages.append(f"Spores begin to spread into {location.name}.")

            elif corruption_type == 'cold':
                old_temp = location.properties.get('temperature', 'normal')
                if old_temp == 'normal':
                    location.properties['temperature'] = 'cold'
                    messages.append(f"An unnatural chill settles over {location.name}.")

            elif corruption_type == 'flood':
                old_level = location.properties.get('water_level', 'none')
                if old_level == 'none':
                    location.properties['water_level'] = 'shallow'
                    messages.append(f"Water begins seeping into {location.name}.")

    return messages


def get_locations_in_region(accessor, region_id: str) -> List:
    """
    Get all location objects in a region.

    Args:
        accessor: StateAccessor instance
        region_id: ID of the region

    Returns:
        List of Location objects
    """
    region_def = get_region_state(accessor, region_id)
    locations = []

    for loc_id in region_def.get('locations', []):
        location = accessor.get_location(loc_id)
        if location:
            locations.append(location)

    return locations


def get_actors_in_region(accessor, region_id: str) -> List:
    """
    Get all actors currently in a region.

    Args:
        accessor: StateAccessor instance
        region_id: ID of the region

    Returns:
        List of Actor objects
    """
    region_def = get_region_state(accessor, region_id)
    location_ids = set(region_def.get('locations', []))

    actors = []
    for actor_id, actor in accessor.game_state.actors.items():
        if actor.location in location_ids:
            actors.append(actor)

    return actors


def on_region_purified(entity, accessor, context: dict) -> EventResult:
    """
    Event handler for when a region is purified.

    Triggered by game logic when a major quest objective is completed
    (e.g., healing the Spore Mother).

    Args:
        entity: Ignored
        accessor: StateAccessor instance
        context: Must contain 'region_id'

    Returns:
        EventResult with purification messages
    """
    region_id = context.get('region_id')
    if not region_id:
        return EventResult(allow=True, message='')

    messages = purify_region(accessor, region_id)
    return EventResult(allow=True, message='\n'.join(messages))


def on_corruption_spread(entity, accessor, context: dict) -> EventResult:
    """
    Event handler for corruption spreading to a region.

    Triggered by scheduled events when deadlines pass.

    Args:
        entity: Ignored
        accessor: StateAccessor instance
        context: Must contain 'region_id' and 'corruption_type'

    Returns:
        EventResult with spread messages
    """
    region_id = context.get('region_id')
    corruption_type = context.get('corruption_type', 'spore')

    if not region_id:
        return EventResult(allow=True, message='')

    messages = corrupt_region(accessor, region_id, corruption_type)
    return EventResult(allow=True, message='\n'.join(messages))


# Vocabulary extension
vocabulary = {
    "events": [
        {
            "event": "on_region_purified",
            "description": "Called when a region is purified"
        },
        {
            "event": "on_corruption_spread",
            "description": "Called when corruption spreads to a region"
        }
    ]
}
