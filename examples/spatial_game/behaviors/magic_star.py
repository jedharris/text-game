"""Magic star behavior module.

Demonstrates:
- Chained positioning requirements (bench → tree → star)
- Posture-based access control
- Using focused_on and posture properties
"""

from typing import Dict, Any

from src.behavior_manager import EventResult


def on_climb(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Tree climb behavior - checks if player is standing on bench.

    entity: The tree
    context: {actor_id, verb}
    """
    actor_id = context.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)

    posture = actor.properties.get("posture")
    focused = actor.properties.get("focused_on")

    if posture != "on_surface" or focused != "item_garden_bench":
        return EventResult(
            allow=False,
            message="The tree is too tall to climb from the ground. You need something to stand on."
        )

    return EventResult(allow=True, message="")


def on_take(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Star take behavior - checks if player is climbing tree.

    entity: The star
    context: {actor_id, verb}
    """
    actor_id = context.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)

    posture = actor.properties.get("posture")
    focused = actor.properties.get("focused_on")

    if posture != "climbing" or focused != "item_tree":
        return EventResult(
            allow=False,
            message="The star is too high up in the tree branches. You'll need to climb the tree to reach it."
        )

    return EventResult(allow=True, message="")
