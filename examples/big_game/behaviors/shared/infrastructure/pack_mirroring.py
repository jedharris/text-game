"""Pack State Mirroring Infrastructure.

Provides generic leader/follower state mirroring for any entity
that has pack_behavior configuration.

Supports two modes:
1. Data-driven: Entity pack_behavior defines followers list, mirroring enabled
2. Handler escape hatch: Entity pack_behavior specifies a Python function to call

Example data-driven config:
    "pack_behavior": {
        "pack_follows_leader_state": true,
        "followers": ["npc_wolf_beta", "npc_wolf_gamma"]
    }

Example handler escape hatch:
    "pack_behavior": {
        "handler": "behaviors.regions.beast_wilds.wolf_pack:on_alpha_state_change"
    }
"""

from typing import Any

from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult
from src.infrastructure_utils import transition_state

# Vocabulary: wire hooks to events
vocabulary = {
    "events": [
        {
            "event": "on_leader_state_change",
            "hook": "after_actor_state_change",
            "description": "Mirror leader state changes to pack followers",
        },
    ]
}


def on_leader_state_change(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Mirror leader state changes to pack followers.

    Checks if the entity has pack_behavior configuration.
    If config has "handler" key, calls that Python function.
    Otherwise, processes the data-driven config.

    Works for wolves, salamanders, sporelings, or any future
    pack-based entity.

    Args:
        entity: The actor whose state changed
        accessor: StateAccessor instance
        context: Context with old_state, new_state

    Returns:
        EventResult allowing the change
    """
    if not hasattr(entity, "properties"):
        return EventResult(allow=True, feedback=None)

    # Check for pack_behavior configuration
    pack_config = entity.properties.get("pack_behavior", {})
    if not pack_config:
        return EventResult(allow=True, feedback=None)

    # Check for handler escape hatch first
    handler_path = pack_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)
        # Handler failed to load - fall through to data-driven

    # Data-driven processing
    # Must be configured to mirror states
    # Support both generic and legacy property names
    follows_leader = pack_config.get("pack_follows_leader_state", False)
    follows_alpha = pack_config.get("pack_follows_alpha_state", False)
    if not follows_leader and not follows_alpha:
        return EventResult(allow=True, feedback=None)

    followers = pack_config.get("followers", [])
    new_state = context.get("new_state")
    if not new_state or not followers:
        return EventResult(allow=True, feedback=None)

    # Mirror state to all followers
    state = accessor.game_state
    for follower_id in followers:
        follower = state.actors.get(follower_id)
        if follower and "state_machine" in follower.properties:
            sm = follower.properties["state_machine"]
            # Add the state if it doesn't exist (for dynamic states like "confused")
            states = sm.get("states", [])
            if new_state not in states:
                sm["states"] = states + [new_state]
            transition_state(sm, new_state)

    return EventResult(allow=True, feedback=None)
