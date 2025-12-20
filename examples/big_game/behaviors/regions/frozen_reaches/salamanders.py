"""Salamander Befriending for Frozen Reaches.

Implements trust-building through fire item gifts
and companion recruitment mechanics.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import (
    modify_trust,
    transition_state,
)

# Vocabulary: wire hooks to events
# Note: Pack state mirroring is handled by infrastructure/pack_mirroring.py
# Note: Gift reactions are handled by infrastructure/gift_reactions.py
# Salamanders must have:
#   - pack_behavior.pack_follows_leader_state=true for pack mirroring
#   - gift_reactions configuration for fire gift mechanics
vocabulary: Dict[str, Any] = {
    "events": []
}

# Fire items salamanders accept
FIRE_ITEMS = [
    "torch",
    "fire_crystal",
    "warm_coal",
    "heated_stone",
    "fire",
    "flame",
]


def on_fire_gift(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle giving fire items to salamanders.

    Fire-aspected gifts increase gratitude and may
    transition salamanders to friendly/companion state.

    Args:
        entity: The item being given
        accessor: StateAccessor instance
        context: Context with target_actor

    Returns:
        EventResult with gift result
    """
    target = context.get("target_actor")
    if not target:
        return EventResult(allow=True, feedback=None)

    # Check if target is a salamander
    target_id = target.id if hasattr(target, "id") else str(target)
    if "salamander" not in target_id.lower():
        return EventResult(allow=True, feedback=None)

    # Check if item is fire-aspected
    item = context.get("item") or entity
    item_id = item.id if hasattr(item, "id") else str(item)
    item_lower = item_id.lower()

    is_fire_item = any(fire in item_lower for fire in FIRE_ITEMS)
    if not is_fire_item:
        return EventResult(
            allow=True,
            feedback=(
                "The salamander sniffs at the offering, then backs away, "
                "shaking its head. Its flame dims with disappointment."
            ),
        )

    state = accessor.state

    # Find lead salamander (all trust changes apply to lead)
    lead = state.actors.get("salamander")
    if not lead:
        lead = target  # Use target if lead not found

    # Increase trust/gratitude
    trust_state = lead.properties.get("trust_state", {"current": 0})
    old_trust = trust_state.get("current", 0)
    new_trust = modify_trust(
        current=old_trust,
        delta=1,
        floor=0,
        ceiling=5,
    )
    trust_state["current"] = new_trust
    lead.properties["trust_state"] = trust_state

    # Check for state transitions
    sm = lead.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "neutral"))

    if current_state == "neutral" and new_trust >= 1:
        transition_state(sm, "friendly")
        _mirror_salamander_state(state, "friendly")

        return EventResult(
            allow=True,
            feedback=(
                "The salamander's flame brightens with delight as it accepts the "
                f"{item_id}. It approaches cautiously, curling near you with a "
                "contented crackle. The other salamanders watch with interest."
            ),
        )

    if current_state == "friendly" and new_trust >= 3:
        # Ready for companion - but needs invitation
        return EventResult(
            allow=True,
            feedback=(
                "The lead salamander's flame burns bright and steady. It nuzzles "
                f"against you after accepting the {item_id}, clearly comfortable "
                "in your presence. It seems willing to follow if you ask."
            ),
        )

    return EventResult(
        allow=True,
        feedback=(
            f"The salamander accepts the {item_id}, its flame flickering with "
            "gratitude. A pleasant crackle sounds as it moves closer."
        ),
    )


def on_salamander_state_change(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Mirror lead salamander state to followers.

    Salamanders 2 and 3 follow the lead's disposition.

    Args:
        entity: The lead salamander
        accessor: StateAccessor instance
        context: Context with new_state

    Returns:
        EventResult allowing the change
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "salamander":
        return EventResult(allow=True, feedback=None)

    new_state = context.get("new_state")
    if not new_state:
        return EventResult(allow=True, feedback=None)

    state = accessor.state
    _mirror_salamander_state(state, new_state)

    return EventResult(allow=True, feedback=None)


def _mirror_salamander_state(state: Any, new_state: str) -> None:
    """Update follower salamander states to match lead.

    Note: Currently only one salamander exists in game state.
    This function is a no-op until additional salamanders are added.
    """
    # No follower salamanders defined in current game state
    # If salamander followers are added later, list their IDs here
    pass
