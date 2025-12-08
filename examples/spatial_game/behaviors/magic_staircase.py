"""Magic staircase behavior module.

The spiral staircase in the tower entrance is invisible until
the player carries the magic star from the tree in the garden.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult


def on_observe(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Visibility check for the magic staircase.

    The staircase is only visible when the player is carrying
    the magic star.

    entity: The exit descriptor for the staircase
    context: {actor_id, method}
    """
    actor_id = context.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)

    if not actor:
        return EventResult(allow=False, message="")

    # Check if player has the magic star in inventory
    inventory = actor.inventory or []
    has_star = "item_magic_star" in inventory

    if has_star:
        return EventResult(allow=True, message="")
    else:
        return EventResult(allow=False, message="")
