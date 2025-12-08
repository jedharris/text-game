"""NPC-specific behaviors for The Shattered Meridian."""

from behaviors.npc_specifics.the_echo import (
    on_turn_end_echo_appearance,
    get_echo_message,
    vocabulary
)

__all__ = [
    'on_turn_end_echo_appearance',
    'get_echo_message',
    'vocabulary'
]
