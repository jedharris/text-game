"""World events for The Shattered Meridian.

Handles cross-region events, deadlines, and cascading effects.

Uses timing_lib for scheduling. Event definitions stored in GameState.extra:
{
    "world_event_config": {
        "spore_spread_turn": 100,
        "cold_spread_turn": 150,
        "flood_deadline_turn": 50
    }
}

Usage:
    from big_game.behaviors.world_events import (
        initialize_world_events, check_world_state,
        trigger_spore_spread, trigger_cold_spread
    )
"""

from typing import Dict, List

from behavior_libraries.timing_lib.scheduled_events import (
    schedule_event, cancel_event, get_scheduled_events
)
from behaviors.regions import (
    corrupt_region, purify_region, is_region_purified,
    REGION_FUNGAL_DEPTHS, REGION_BEAST_WILDS, REGION_FROZEN_REACHES,
    REGION_CIVILIZED_REMNANTS
)
from src.behavior_manager import EventResult


# Event names
EVENT_SPORE_SPREAD = "world_spore_spread"
EVENT_COLD_SPREAD = "world_cold_spread"
EVENT_FLOOD_RISING = "world_flood_rising"
EVENT_MERIDIAN_COLLAPSE = "world_meridian_collapse"


def initialize_world_events(accessor) -> List[str]:
    """
    Set up initial scheduled events for the game.

    Call this when starting a new game.

    Args:
        accessor: StateAccessor instance

    Returns:
        List of messages about scheduled events
    """
    config = accessor.game_state.extra.get('world_event_config', {})
    messages = []

    # Schedule spore spread if not already purified
    spore_turn = config.get('spore_spread_turn', 100)
    if spore_turn and not is_region_purified(accessor, REGION_FUNGAL_DEPTHS):
        schedule_event(
            accessor,
            EVENT_SPORE_SPREAD,
            spore_turn,
            data={'corruption_type': 'spore', 'target_region': REGION_CIVILIZED_REMNANTS}
        )
        messages.append(f"Spore spread scheduled for turn {spore_turn}")

    # Schedule cold spread if observatory not repaired
    cold_turn = config.get('cold_spread_turn', 150)
    if cold_turn and not accessor.game_state.extra.get('flags', {}).get('observatory_repaired'):
        schedule_event(
            accessor,
            EVENT_COLD_SPREAD,
            cold_turn,
            data={'corruption_type': 'cold', 'target_region': REGION_BEAST_WILDS}
        )
        messages.append(f"Cold spread scheduled for turn {cold_turn}")

    return messages


def cancel_spore_spread(accessor) -> str:
    """
    Cancel the spore spread event (called when Spore Mother is healed).

    Args:
        accessor: StateAccessor instance

    Returns:
        Message about cancellation
    """
    if cancel_event(accessor, EVENT_SPORE_SPREAD):
        return "The spore threat has been contained."
    return ""


def cancel_cold_spread(accessor) -> str:
    """
    Cancel the cold spread event (called when observatory is repaired).

    Args:
        accessor: StateAccessor instance

    Returns:
        Message about cancellation
    """
    if cancel_event(accessor, EVENT_COLD_SPREAD):
        return "The cold no longer threatens to spread."
    return ""


def trigger_spore_spread(accessor) -> List[str]:
    """
    Trigger spore spread from Fungal Depths to other regions.

    Args:
        accessor: StateAccessor instance

    Returns:
        List of messages describing the spread
    """
    messages = ["The spore infection begins spreading beyond the Fungal Depths!"]

    # First wave: spread to town entrance
    messages.extend(corrupt_region(accessor, REGION_CIVILIZED_REMNANTS, 'spore'))

    # Mark NPCs as affected
    affected_npcs = ['npc_cr_gate_guard', 'npc_cr_patrol_guard']
    for npc_id in affected_npcs:
        npc = accessor.get_actor(npc_id)
        if npc:
            npc.properties['spore_exposed'] = True
            messages.append(f"{npc.name} begins coughing from the spores.")

    # Set global flag
    accessor.game_state.extra.setdefault('flags', {})['spore_spread_started'] = True

    return messages


def trigger_cold_spread(accessor) -> List[str]:
    """
    Trigger cold spread from Frozen Reaches to other regions.

    Args:
        accessor: StateAccessor instance

    Returns:
        List of messages describing the spread
    """
    messages = ["An unnatural cold begins spreading from the Frozen Reaches!"]

    # Spread to Beast Wilds
    messages.extend(corrupt_region(accessor, REGION_BEAST_WILDS, 'cold'))

    # Animals become sluggish
    beast_actors = ['creature_bw_alpha_wolf', 'creature_bw_wolf_pack']
    for actor_id in beast_actors:
        actor = accessor.get_actor(actor_id)
        if actor:
            actor.properties['cold_affected'] = True
            messages.append(f"The {actor.name} shivers in the unnatural cold.")

    # Set global flag
    accessor.game_state.extra.setdefault('flags', {})['cold_spread_started'] = True

    return messages


def check_ending_conditions(accessor) -> Dict:
    """
    Check which ending conditions have been met.

    Args:
        accessor: StateAccessor instance

    Returns:
        Dict with ending status information
    """
    flags = accessor.game_state.extra.get('flags', {})

    result = {
        'crystals_restored': sum([
            flags.get('crystal_1_restored', False),
            flags.get('crystal_2_restored', False),
            flags.get('crystal_3_restored', False),
        ]),
        'regions_purified': sum([
            is_region_purified(accessor, REGION_FUNGAL_DEPTHS),
            is_region_purified(accessor, REGION_BEAST_WILDS),
            is_region_purified(accessor, REGION_FROZEN_REACHES),
        ]),
        'spore_spread': flags.get('spore_spread_started', False),
        'cold_spread': flags.get('cold_spread_started', False),
        'aldric_dead': flags.get('aldric_dead', False),
        'aldric_cured': flags.get('aldric_cured', False),
        'observatory_repaired': flags.get('observatory_repaired', False),
    }

    # Determine potential ending
    if result['crystals_restored'] == 3 and result['regions_purified'] == 3:
        result['ending'] = 'perfect'
    elif result['crystals_restored'] == 3:
        result['ending'] = 'partial_restoration'
    elif result['spore_spread'] and result['cold_spread']:
        result['ending'] = 'catastrophe'
    else:
        result['ending'] = 'in_progress'

    return result


def on_world_event_check(entity, accessor, context: dict) -> EventResult:
    """
    Hook handler to process scheduled world events.

    This integrates with timing_lib - when a scheduled event fires,
    this handler determines what actually happens.

    Args:
        entity: Ignored
        accessor: StateAccessor instance
        context: Contains 'event_name' and 'data' from scheduled event

    Returns:
        EventResult with event messages
    """
    event_name = context.get('event_name', '')
    data = context.get('data', {})

    messages = []

    if event_name == EVENT_SPORE_SPREAD:
        # Check if player has prevented this
        if not is_region_purified(accessor, REGION_FUNGAL_DEPTHS):
            messages.extend(trigger_spore_spread(accessor))
        else:
            messages.append("The Fungal Depths purification holds - the spores cannot spread.")

    elif event_name == EVENT_COLD_SPREAD:
        flags = accessor.game_state.extra.get('flags', {})
        if not flags.get('observatory_repaired'):
            messages.extend(trigger_cold_spread(accessor))
        else:
            messages.append("The repaired observatory stabilizes the temperature.")

    elif event_name == EVENT_FLOOD_RISING:
        # Sunken district flooding continues
        messages.append("The water level rises in the Sunken District...")

    elif event_name == EVENT_MERIDIAN_COLLAPSE:
        # Ultimate bad ending trigger
        messages.append("The Meridian begins to collapse! Time is running out!")

    return EventResult(allow=True, message='\n'.join(messages))


def on_quest_complete(entity, accessor, context: dict) -> EventResult:
    """
    Hook handler for quest completions that affect world state.

    Args:
        entity: Quest-related entity
        accessor: StateAccessor instance
        context: Contains 'quest_id'

    Returns:
        EventResult with world state changes
    """
    quest_id = context.get('quest_id', '')
    messages = []

    if quest_id == 'heal_spore_mother':
        # Purify Fungal Depths and cancel spore spread
        messages.extend(purify_region(accessor, REGION_FUNGAL_DEPTHS))
        cancel_msg = cancel_spore_spread(accessor)
        if cancel_msg:
            messages.append(cancel_msg)
        accessor.game_state.extra.setdefault('flags', {})['spore_mother_healed'] = True

    elif quest_id == 'repair_observatory':
        # Cancel cold spread
        cancel_msg = cancel_cold_spread(accessor)
        if cancel_msg:
            messages.append(cancel_msg)
        accessor.game_state.extra.setdefault('flags', {})['observatory_repaired'] = True
        messages.append("The observatory hums back to life, stabilizing the region's temperature.")

    elif quest_id == 'cure_aldric':
        accessor.game_state.extra.setdefault('flags', {})['aldric_cured'] = True
        messages.append("Scholar Aldric's infection is cured. He can now help you fully.")

    elif quest_id.startswith('restore_crystal_'):
        crystal_num = quest_id[-1]
        accessor.game_state.extra.setdefault('flags', {})[f'crystal_{crystal_num}_restored'] = True
        messages.append(f"Crystal {crystal_num} pulses with renewed energy.")

        # Check if all crystals restored
        ending_state = check_ending_conditions(accessor)
        if ending_state['crystals_restored'] == 3:
            messages.append("All three crystals are restored! The Meridian's power awakens!")

    return EventResult(allow=True, message='\n'.join(messages))


# Vocabulary extension
vocabulary = {
    "events": [
        {
            "event": "on_world_event_check",
            "description": "Process scheduled world events"
        },
        {
            "event": "on_quest_complete",
            "description": "Handle quest completion world effects"
        }
    ]
}
