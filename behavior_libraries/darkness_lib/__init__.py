"""Darkness library - visibility and light source mechanics.

Implements darkness mechanics where certain locations require light to see/interact.
"""

from behavior_libraries.darkness_lib.visibility import (
    check_visibility,
    get_light_sources,
    get_darkness_description,
    on_visibility_check,
)

__all__ = [
    'check_visibility',
    'get_light_sources',
    'get_darkness_description',
    'on_visibility_check',
]
