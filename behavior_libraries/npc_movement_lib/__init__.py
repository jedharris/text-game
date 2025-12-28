"""NPC Movement library - patrol and wandering mechanics.

Allows NPCs to move between locations on their own schedule.
"""

from .patrol import (
    patrol_step,
    set_patrol_route,
    on_npc_movement,
)
from .wander import (
    wander_step,
    set_wander_area,
)

__all__ = [
    'patrol_step',
    'set_patrol_route',
    'on_npc_movement',
    'wander_step',
    'set_wander_area',
]
