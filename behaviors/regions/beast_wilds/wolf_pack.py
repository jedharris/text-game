"""Wolf Pack Dynamics for Beast Wilds.

Implements pack behavior where followers mirror the alpha's state and location.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import (
    get_current_state,
    modify_trust,
    transition_state,
)

# Vocabulary: wire hooks to events
# Note: Pack state mirroring is handled by infrastructure/pack_mirroring.py
# Note: Gift reactions are handled by infrastructure/gift_reactions.py
# Wolves must have:
#   - pack_behavior.pack_follows_leader_state=true for pack mirroring
#   - gift_reactions configuration for feeding mechanics
vocabulary: Dict[str, Any] = {
    "events": []
}


def on_wolf_state_change(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Mirror alpha wolf state changes to pack members.

    When the alpha wolf's state machine transitions, all pack
    followers should mirror that state.

    Args:
        entity: The actor whose state changed
        accessor: StateAccessor instance
        context: Context with old_state, new_state

    Returns:
        EventResult allowing the change
    """
    # Check if this is the alpha wolf
    if not hasattr(entity, "id") or entity.id != "npc_alpha_wolf":
        return EventResult(allow=True, message=None)

    # Get pack followers from entity properties
    pack_config = entity.properties.get("pack_behavior", {})
    if not pack_config.get("pack_follows_alpha_state", False):
        return EventResult(allow=True, message=None)

    followers = pack_config.get("followers", [])
    new_state = context.get("new_state")
    if not new_state or not followers:
        return EventResult(allow=True, message=None)

    # Mirror state to all followers
    state = accessor.state
    messages = []
    for follower_id in followers:
        follower = state.actors.get(follower_id)
        if follower and "state_machine" in follower.properties:
            sm = follower.properties["state_machine"]
            success, msg = transition_state(sm, new_state)
            if success:
                messages.append(f"{follower_id} mirrors alpha's state")

    if messages:
        return EventResult(allow=True, message="; ".join(messages))
    return EventResult(allow=True, message=None)


def on_wolf_feed(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle feeding wolves to build trust.

    Giving meat to the alpha wolf increases trust and may
    cause state transitions (hostile -> wary -> neutral -> friendly).

    Args:
        entity: The item being given
        accessor: StateAccessor instance
        context: Context with target_actor, item

    Returns:
        EventResult with feeding result message
    """
    target = context.get("target_actor")
    if not target:
        return EventResult(allow=True, message=None)

    # Check if target is a wolf
    target_id = target.id if hasattr(target, "id") else str(target)
    if not target_id.startswith("npc_") or "wolf" not in target_id:
        return EventResult(allow=True, message=None)

    # Check if item is food (meat/venison)
    item = context.get("item") or entity
    item_id = item.id if hasattr(item, "id") else str(item)
    food_items = ["venison", "meat", "rabbit"]
    is_food = any(food in item_id.lower() for food in food_items)
    if not is_food:
        return EventResult(allow=True, message=None)

    # Get the alpha wolf (may be target or may need to find leader)
    state = accessor.state
    alpha = state.actors.get("npc_alpha_wolf")
    if not alpha:
        return EventResult(allow=True, message=None)

    # Increase trust
    trust_state = alpha.properties.get("trust_state", {"current": 0})
    old_trust = trust_state.get("current", 0)
    new_trust = modify_trust(
        current=old_trust,
        delta=1,
        floor=trust_state.get("floor", -3),
        ceiling=trust_state.get("ceiling", 6),
    )
    trust_state["current"] = new_trust
    alpha.properties["trust_state"] = trust_state

    # Check for state transitions based on trust
    sm = alpha.properties.get("state_machine")
    if sm:
        current_state = get_current_state(sm)
        new_state = None

        if current_state == "hostile" and new_trust >= 1:
            new_state = "wary"
        elif current_state == "wary" and new_trust >= 2:
            new_state = "neutral"
        elif current_state == "neutral" and new_trust >= 3:
            new_state = "friendly"

        if new_state:
            transition_state(sm, new_state)
            # Pack will mirror via on_wolf_state_change

    return EventResult(
        allow=True,
        message=f"The wolf accepts the {item_id}, watching you with less hostility.",
    )
