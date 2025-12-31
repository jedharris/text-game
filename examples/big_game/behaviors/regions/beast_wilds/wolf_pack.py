"""Wolf Pack Dynamics for Beast Wilds.

Implements pack behavior where followers mirror the alpha's state and location.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import (
    apply_trust_change,
    get_current_state,
    transition_state,
)
from src.narrator_helpers import select_state_fragments

# Vocabulary: wire hooks to events
# Note: Pack state mirroring is handled by infrastructure/pack_mirroring.py
# Note: Gift reactions are handled by infrastructure/gift_reactions.py
# Wolves must have:
#   - pack_behavior.pack_follows_leader_state=true for pack mirroring
#   - gift_reactions configuration for feeding mechanics
vocabulary: Dict[str, Any] = {
    "events": [
        {
            "event": "on_receive_item",
            "hook": "entity_item_received",
            "description": "Handle feeding wolves to build trust"
        }
    ]
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
    if not hasattr(entity, "id") or entity.id != "alpha_wolf":
        return EventResult(allow=True, feedback=None)

    # Get pack followers from entity properties
    pack_config = entity.properties.get("pack_behavior", {})
    if not pack_config.get("pack_follows_alpha_state", False):
        return EventResult(allow=True, feedback=None)

    followers = pack_config.get("followers", [])
    new_state = context.get("new_state")
    if not new_state or not followers:
        return EventResult(allow=True, feedback=None)

    # Mirror state to all followers
    state = accessor.game_state
    messages = []
    for follower_id in followers:
        follower = state.actors.get(follower_id)
        if follower and "state_machine" in follower.properties:
            sm = follower.properties["state_machine"]
            success, msg = transition_state(sm, new_state)
            if success:
                messages.append(f"{follower_id} mirrors alpha's state")

    if messages:
        return EventResult(allow=True, feedback="; ".join(messages))
    return EventResult(allow=True, feedback=None)


def on_receive_item(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle feeding wolves to build trust.

    Giving meat to the alpha wolf increases trust and may
    cause state transitions (hostile -> wary -> neutral -> friendly).

    Args:
        entity: The wolf receiving the item (when called via on_receive_item)
        accessor: StateAccessor instance
        context: Context with item, item_id, giver_id

    Returns:
        EventResult with feeding result message
    """
    # When called via on_receive_item, entity is the wolf
    wolf = entity
    wolf_id = wolf.id if hasattr(wolf, "id") else str(wolf)

    # Check if this is a wolf
    if "wolf" not in wolf_id.lower():
        return EventResult(allow=True, feedback=None)

    # Check if item is food (meat/venison)
    item = context.get("item")
    if not item:
        return EventResult(allow=True, feedback=None)

    item_id = item.id if hasattr(item, "id") else str(item)
    food_items = ["venison", "meat", "rabbit"]
    is_food = any(food in item_id.lower() for food in food_items)
    if not is_food:
        return EventResult(allow=True, feedback=None)

    # Get the alpha wolf (may be target or may need to find leader)
    state = accessor.game_state
    alpha = state.actors.get("alpha_wolf")
    if not alpha:
        return EventResult(allow=True, feedback=None)

    # Initialize trust_state if missing
    if "trust_state" not in alpha.properties:
        alpha.properties["trust_state"] = {"current": 0}

    # Increase trust with state transitions
    result = apply_trust_change(
        entity=alpha,
        delta=1,
        transitions={"1": "wary", "2": "neutral", "3": "friendly", "5": "allied"},
    )

    # Check for state transitions based on trust
    sm = alpha.properties.get("state_machine")
    if sm:
        if result["state_changed"]:
            new_state = result["new_state"]
            # Pack will mirror via on_wolf_state_change

            # Select fragments for the new state
            fragments = select_state_fragments(alpha, new_state, max_count=2)

            # Check if we should give the alpha_fang_fragment (at allied state)
            extra_feedback = ""
            if new_state == "allied" and not state.extra.get("alpha_fang_given"):
                state.extra["alpha_fang_given"] = True
                # Give the fragment to the player
                fang = state.get_item("alpha_fang_fragment")
                if fang:
                    fang.location = "player"
                    player = state.actors.get("player")
                    if player and fang.id not in player.inventory:
                        player.inventory.append(fang.id)
                extra_feedback = (
                    " The alpha approaches and, with deliberate care, places something "
                    "at your feet - a massive fang, freely given. A mark of pack bond."
                )

            # Get previous state for context
            prev_state = get_current_state(sm) if not result["state_changed"] else None
            # Since we just transitioned, the current state is new_state
            # But we don't have the old state anymore - this is a limitation

            return EventResult(
                allow=True,
                feedback=f"The wolf accepts the {item_id}. Its posture changes noticeably.{extra_feedback}",
                context={
                    "npc_state": {"current": new_state},
                    "communication": {"type": "body_language"}
                },
                hints=["trust-building", "tense"],
                fragments={"state": fragments},
            )

    # No state change, but still accepted food
    current_state = get_current_state(sm) if sm else "hostile"
    fragments = select_state_fragments(alpha, current_state, max_count=2)

    return EventResult(
        allow=True,
        feedback=f"The wolf accepts the {item_id}, watching you carefully.",
        context={"communication": {"type": "body_language"}},
        hints=["trust-building"],
        fragments={"state": fragments},
    )
