"""Household Shrine puzzle behavior.

Demonstrates:
- Using offering_lib.offering_handler for altar offerings
- Using offering_lib.blessing_manager for applying effects
- Different items grant different blessings or curses
"""

from typing import Dict, Any, cast
from src.behavior_manager import EventResult
from src.types import ActorId

# Import library functions
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from behavior_libraries.offering_lib.blessing_manager import (
    apply_blessing, apply_curse, get_effect_description
)


def on_receive_offering(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Entity behavior for shrine altar receiving an offering.

    Different items grant different effects:
    - Food: blessing of health
    - Flowers: blessing of luck
    - Weapons: curse of weakness (inappropriate offering)
    - Treasure: curse of misfortune (greed)

    Args:
        entity: The altar
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb, offered_item, offered_item_id

    Returns:
        EventResult with allow and message
    """
    actor_id = cast(ActorId, context.get("actor_id") or ActorId("player"))
    offered_item = context.get("offered_item")

    if not offered_item:
        return EventResult(
            allow=False,
            message="The altar sits silent, waiting for an offering."
        )

    # Determine the type of offering
    item_type = offered_item.properties.get("type", "object") if hasattr(offered_item, 'properties') else "object"
    item_name = offered_item.name if hasattr(offered_item, 'name') else "item"

    # Process the offering
    if item_type == "food":
        # Food = proper offering = blessing of health
        apply_blessing(accessor, actor_id, "health", duration=10, value=2)
        response = (
            f"You place the {item_name} on the altar.\n"
            f"It vanishes in a soft golden light!\n\n"
            f"{get_effect_description('health', is_blessing=True)}\n"
            f"(Blessing of Health: 10 turns remaining)"
        )

    elif item_type in ["plant", "flower"]:
        # Flowers = offering of beauty = blessing of luck
        apply_blessing(accessor, actor_id, "luck", duration=15, value=1)
        response = (
            f"You place the {item_name} on the altar.\n"
            f"It glows and transforms into motes of light!\n\n"
            f"{get_effect_description('luck', is_blessing=True)}\n"
            f"(Blessing of Luck: 15 turns remaining)"
        )

    elif item_type == "weapon":
        # Weapon = inappropriate offering = curse of weakness
        apply_curse(accessor, actor_id, "weakness", duration=8, value=-1)
        response = (
            f"You place the {item_name} on the altar.\n"
            f"The altar rejects it! Dark energy lashes out!\n\n"
            f"{get_effect_description('weakness', is_blessing=False)}\n"
            f"(Curse of Weakness: 8 turns remaining)"
        )

    elif item_type == "treasure":
        # Treasure = greed = curse of misfortune
        apply_curse(accessor, actor_id, "misfortune", duration=12, value=-2)
        response = (
            f"You place the {item_name} on the altar.\n"
            f"The offering is consumed, but the altar grows cold...\n\n"
            f"{get_effect_description('misfortune', is_blessing=False)}\n"
            f"(Curse of Misfortune: 12 turns remaining)"
        )

    else:
        # Generic object = neutral response
        response = (
            f"You place the {item_name} on the altar.\n"
            f"It sits there for a moment, then fades away.\n"
            f"The altar seems indifferent to this offering."
        )

    return EventResult(allow=True, message=response)
