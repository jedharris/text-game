"""The Echo - spectral guide NPC behavior.

The Echo is the remnant of the last Meridian Keeper. It appears intermittently
in Nexus locations, with appearance probability increasing as the player
restores the Meridian.

Actor configuration (in npc_mn_the_echo.properties):
{
    "is_spectral": true,
    "can_be_attacked": false,
    "appearance_chance": 0.1,
    "restoration_bonus": 0.15
}

The Echo only appears in Nexus locations. Its appearance chance increases
based on how many restoration tasks the player has completed.

Usage:
    from big_game.behaviors.npc_specifics.the_echo import (
        on_turn_end_echo_appearance,
        get_echo_message
    )
"""

import random
from typing import Optional

from src.behavior_manager import EventResult


# Locations where The Echo can appear
NEXUS_LOCATIONS = [
    "loc_mn_nexus_chamber",
    "loc_mn_observatory_platform",
    "loc_mn_keepers_quarters",
    "loc_mn_crystal_garden"
]

# Restoration flags that increase appearance chance
RESTORATION_FLAGS = [
    "waystone_repaired",
    "crystal_1_restored",
    "crystal_2_restored",
    "crystal_3_restored",
    "telescope_functional",
    "spore_mother_healed",
    "observatory_repaired"
]

# Messages The Echo delivers based on game state
ECHO_MESSAGES = {
    "greeting_first": [
        "A translucent figure flickers into view, watching you with ancient eyes. 'A visitor... how long has it been?'",
        "Reality shimmers, and a spectral form coalesces from the air itself. 'You can see me. How unexpected.'",
    ],
    "greeting_returning": [
        "The Echo materializes, its form slightly more solid than before. 'You return.'",
        "A familiar shimmer heralds The Echo's appearance. 'I sense your progress.'",
    ],
    "progress_crystals_1": [
        "'One crystal restored. The Meridian stirs in its long sleep.'",
    ],
    "progress_crystals_2": [
        "'Two crystals now. I can feel the ley lines beginning to remember their purpose.'",
    ],
    "progress_crystals_3": [
        "'All three crystals blaze with power. The restoration... it is truly possible.'",
    ],
    "warning_spores": [
        "'The spores spread. Without intervention, they will reach the settlement.'",
    ],
    "warning_cold": [
        "'The cold advances. The observatory... it was meant to stabilize temperatures.'",
    ],
    "encouragement": [
        "'Do not lose hope. Even fragments can be made whole again.'",
        "'The world remembers what it was. Help it remember again.'",
    ],
    "farewell": [
        "The Echo's form begins to fade, its voice growing distant. 'I cannot stay long...'",
        "The spectral figure flickers and dims. 'The effort to manifest... drains what remains of me.'",
    ],
}


def calculate_appearance_chance(accessor) -> float:
    """
    Calculate The Echo's appearance probability.

    Base chance is 10%, increased by 15% for each restoration task completed.

    Args:
        accessor: StateAccessor instance

    Returns:
        Probability between 0.0 and 1.0
    """
    echo = accessor.get_actor('npc_mn_the_echo')
    if not echo:
        return 0.0

    base_chance = echo.properties.get('appearance_chance', 0.1)
    restoration_bonus = echo.properties.get('restoration_bonus', 0.15)

    flags = accessor.game_state.extra.get('flags', {})

    # Count completed restoration tasks
    restoration_count = sum(
        1 for flag in RESTORATION_FLAGS
        if flags.get(flag, False)
    )

    # Calculate final chance (capped at 85%)
    final_chance = base_chance + (restoration_count * restoration_bonus)
    return min(0.85, final_chance)


def get_echo_message(accessor) -> Optional[str]:
    """
    Get an appropriate message from The Echo based on game state.

    Args:
        accessor: StateAccessor instance

    Returns:
        A contextual message, or None
    """
    flags = accessor.game_state.extra.get('flags', {})
    messages = []

    # Check if first meeting
    if not flags.get('met_the_echo'):
        return random.choice(ECHO_MESSAGES['greeting_first'])

    # Otherwise, returning greeting
    messages.append(random.choice(ECHO_MESSAGES['greeting_returning']))

    # Add progress message based on crystal count
    crystals_restored = sum([
        flags.get('crystal_1_restored', False),
        flags.get('crystal_2_restored', False),
        flags.get('crystal_3_restored', False),
    ])

    if crystals_restored == 1:
        messages.append(random.choice(ECHO_MESSAGES['progress_crystals_1']))
    elif crystals_restored == 2:
        messages.append(random.choice(ECHO_MESSAGES['progress_crystals_2']))
    elif crystals_restored == 3:
        messages.append(random.choice(ECHO_MESSAGES['progress_crystals_3']))

    # Add warnings if applicable
    if flags.get('spore_spread_started') and not flags.get('spore_mother_healed'):
        messages.append(random.choice(ECHO_MESSAGES['warning_spores']))

    if flags.get('cold_spread_started') and not flags.get('observatory_repaired'):
        messages.append(random.choice(ECHO_MESSAGES['warning_cold']))

    # Add encouragement or farewell
    if len(messages) < 3:
        messages.append(random.choice(ECHO_MESSAGES['encouragement']))

    messages.append(random.choice(ECHO_MESSAGES['farewell']))

    return '\n\n'.join(messages)


def on_turn_end_echo_appearance(entity, accessor, context: dict) -> EventResult:
    """
    Hook handler - The Echo appears intermittently in Nexus locations.

    This should be registered for the NPC_ACTION hook.

    Args:
        entity: Ignored (entity is None for turn phase hooks)
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with appearance message if Echo appears
    """
    player = accessor.get_actor('player')
    echo = accessor.get_actor('npc_mn_the_echo')

    if not player or not echo:
        return EventResult(allow=True, message='')

    # Only appear in Nexus locations
    if player.location not in NEXUS_LOCATIONS:
        # If Echo was visible, hide it
        if echo.location is not None:
            echo.location = None
        return EventResult(allow=True, message='')

    # Calculate appearance chance
    chance = calculate_appearance_chance(accessor)

    # Roll for appearance
    if random.random() < chance:
        # Echo appears!
        old_location = echo.location
        echo.location = player.location

        # Set flag for first meeting
        flags = accessor.game_state.extra.setdefault('flags', {})
        first_meeting = not flags.get('met_the_echo', False)
        flags['met_the_echo'] = True

        # Get appropriate message
        message = get_echo_message(accessor)

        return EventResult(allow=True, message=message or '')

    else:
        # Echo doesn't appear (or disappears if was present)
        if echo.location is not None:
            echo.location = None
            return EventResult(
                allow=True,
                message="The Echo's form flickers and fades from view."
            )

    return EventResult(allow=True, message='')


# Vocabulary extension
vocabulary = {
    "events": [
        {
            "event": "on_turn_end_echo_appearance",
            "hook": "npc_action",
            "description": "The Echo appears intermittently in Nexus locations"
        }
    ]
}
