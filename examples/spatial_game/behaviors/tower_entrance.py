"""Tower entrance location behavior.

Provides dynamic description that includes the staircase
when the player has the magic star.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult


def on_examine(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Add dynamic description elements to the tower entrance.

    When the player has the magic star, mention the staircase
    that has now become visible.

    entity: The tower entrance location
    context: {actor_id}
    """
    actor_id = context.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)

    if not actor:
        return EventResult(allow=True, message="")

    # Check if player has the magic star
    inventory = actor.inventory or []
    has_star = "item_magic_star" in inventory

    if has_star:
        # Add the staircase to the description
        return EventResult(
            allow=True,
            message="The magic star pulses warmly in your possession, and you notice a spiral staircase leading upward that you hadn't seen before."
        )

    return EventResult(allow=True, message="")
