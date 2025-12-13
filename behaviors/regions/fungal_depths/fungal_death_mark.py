"""Fungal Death Mark System for Fungal Depths.

Killing any fungal creature sets a permanent mark that
Myconids can sense, affecting trust.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult

# Vocabulary: wire hooks to events
# Note: Death reactions are handled by infrastructure/death_reactions.py
# Note: First encounter reactions are handled by infrastructure/encounter_reactions.py
# Entities must have appropriate reaction configurations
vocabulary: Dict[str, Any] = {
    "events": []
}


def on_fungal_kill(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Mark player when they kill a fungal creature.

    The spore network instantly knows about the death,
    leaving a mystical mark on the player.

    Args:
        entity: The actor who died
        accessor: StateAccessor instance
        context: Context dict with killer info

    Returns:
        EventResult allowing the death
    """
    # Check if killed entity is fungal
    props = entity.properties if hasattr(entity, "properties") else {}
    if not props.get("fungal", False):
        return EventResult(allow=True, message=None)

    # Check if player did the killing
    killer = context.get("killer")
    if not killer or (hasattr(killer, "id") and killer.id != "player"):
        return EventResult(allow=True, message=None)

    state = accessor.state

    # Set the death mark
    state.extra["has_killed_fungi"] = True

    entity_name = entity.name if hasattr(entity, "name") else "creature"

    return EventResult(
        allow=True,
        message=(
            f"As the {entity_name} dies, you feel a ripple through the air - "
            "as if every fungus in these depths just learned what you did."
        ),
    )


def on_myconid_first_meeting(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Detect death mark when first meeting Myconid Elder.

    If player has killed fungi, Myconid trust starts at -3.

    Args:
        entity: The Myconid being encountered
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with detection message
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "npc_myconid_elder":
        return EventResult(allow=True, message=None)

    state = accessor.state

    # Check for death mark
    if not state.extra.get("has_killed_fungi"):
        return EventResult(allow=True, message=None)

    # Apply trust penalty
    myconid = state.actors.get("npc_myconid_elder")
    if myconid:
        trust_state = myconid.properties.get("trust_state", {"current": 0})
        trust_state["current"] = -3  # Starts at -3 with death mark
        myconid.properties["trust_state"] = trust_state
        state.extra["myconid_detected_death_mark"] = True

    return EventResult(
        allow=True,
        message=(
            "The Myconid Elder recoils as you approach. Its spores shift to "
            "deep crimson. 'You carry the death of our kin upon you. We sense it.'"
        ),
    )
