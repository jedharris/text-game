"""Companion library - companion following mechanics.

Allows domesticated creatures and befriended NPCs to follow the player
between locations, with support for location/terrain restrictions.
"""

from .following import (
    get_companions,
    make_companion,
    dismiss_companion,
    check_can_follow,
    on_player_move_companions_follow,
)

__all__ = [
    'get_companions',
    'make_companion',
    'dismiss_companion',
    'check_can_follow',
    'on_player_move_companions_follow',
]
