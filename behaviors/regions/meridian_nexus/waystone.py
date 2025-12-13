"""Waystone Repair Mechanics for Meridian Nexus.

Implements the central quest of collecting fragments
and repairing the waystone for different endings.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult

# Vocabulary: wire hooks to events
# Note: Item use reactions are handled by infrastructure/item_use_reactions.py
# Waystone must have item_use_reactions configuration for fragment placement
vocabulary: Dict[str, Any] = {
    "events": [
        {
            "event": "on_waystone_complete",
            "hook": "on_puzzle_solved",
            "description": "Handle waystone completion for ending",
        },
        {
            "event": "on_ending_check",
            "hook": "turn_phase_global",
            "description": "Check ending conditions each turn",
        },
    ]
}

# Required waystone fragments
WAYSTONE_FRAGMENTS = [
    "alpha_fang",      # Beast Wilds - wolf trust
    "spore_heart",     # Fungal Depths - heal Spore Mother
    "ice_shard",       # Frozen Reaches - ice caves
    "water_bloom",     # Sunken District - flooded areas
    "echo_essence",    # Meridian Nexus - Echo's gift
]


def on_fragment_place(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle placing a waystone fragment.

    Each fragment contributes to waystone repair.

    Args:
        entity: The item being placed
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with placement result
    """
    item_id = entity.id if hasattr(entity, "id") else str(entity)
    item_lower = item_id.lower()

    # Check if this is a fragment
    fragment_name = None
    for frag in WAYSTONE_FRAGMENTS:
        if frag.replace("_", "") in item_lower.replace("_", ""):
            fragment_name = frag
            break

    if not fragment_name:
        return EventResult(allow=True, message=None)

    # Check location is waystone
    target = context.get("target")
    target_id = target.id if target and hasattr(target, "id") else str(target) if target else ""
    if "waystone" not in target_id.lower():
        return EventResult(allow=True, message=None)

    state = accessor.state

    # Track placed fragments
    if "waystone_fragments" not in state.extra:
        state.extra["waystone_fragments"] = []

    fragments = state.extra["waystone_fragments"]
    if fragment_name in fragments:
        return EventResult(
            allow=True,
            message=f"This fragment ({fragment_name}) is already in place.",
        )

    fragments.append(fragment_name)

    # Check completion
    remaining = len(WAYSTONE_FRAGMENTS) - len(fragments)

    if remaining == 0:
        state.extra["waystone_complete"] = True
        return EventResult(
            allow=True,
            message=(
                "The final fragment clicks into place. The waystone blazes with "
                "brilliant light, its ancient power restored. The connection to "
                "distant places awakens. You have completed the primary restoration."
            ),
        )

    return EventResult(
        allow=True,
        message=(
            f"The {fragment_name} slots into place. The waystone pulses with "
            f"renewed energy. {remaining} fragment(s) remain to complete repair."
        ),
    )


def on_waystone_complete(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle waystone completion for ending calculation.

    Args:
        entity: The waystone
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with ending hint
    """
    puzzle_id = context.get("puzzle_id")
    if puzzle_id != "waystone_repair":
        return EventResult(allow=True, message=None)

    state = accessor.state
    state.extra["waystone_complete"] = True

    # Calculate ending factors
    ending_score = _calculate_ending_score(state)
    state.extra["ending_score"] = ending_score

    return EventResult(
        allow=True,
        message="The waystone is restored. Echo's presence strengthens.",
    )


def on_ending_check(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Check if game ending conditions are met.

    Called each turn to evaluate possible endings.

    Args:
        entity: None (global check)
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult (silent unless ending triggered)
    """
    state = accessor.state

    # Check for ending trigger (waystone complete + all threats resolved)
    if not state.extra.get("waystone_complete"):
        return EventResult(allow=True, message=None)

    if state.extra.get("ending_triggered"):
        return EventResult(allow=True, message=None)

    # Check ending conditions
    score = _calculate_ending_score(state)

    # Determine ending tier
    if score >= 90:
        ending = "triumphant"
    elif score >= 70:
        ending = "successful"
    elif score >= 50:
        ending = "bittersweet"
    elif score >= 30:
        ending = "surviving"
    else:
        ending = "pyrrhic"

    state.extra["ending_tier"] = ending
    state.extra["ending_score"] = score

    return EventResult(allow=True, message=None)


def _calculate_ending_score(state: Any) -> int:
    """Calculate ending score based on player choices."""
    score = 0
    extra = state.extra

    # Waystone completion (base requirement)
    if extra.get("waystone_complete"):
        score += 20

    # NPCs saved (up to 30 points)
    saved_npcs = [
        "sira_healed",
        "aldric_helped",
        "delvan_rescued",
        "garrett_rescued",
        "spore_mother_healed",
        "cubs_healed",
    ]
    for npc in saved_npcs:
        if extra.get(npc):
            score += 5

    # NPCs lost (penalty)
    lost_npcs = [
        "sira_died",
        "aldric_died",
        "delvan_died",
        "garrett_died",
        "spore_mother_dead",
        "cubs_died",
    ]
    for npc in lost_npcs:
        if extra.get(npc):
            score -= 5

    # Relationships built (up to 20 points)
    if extra.get("wolf_companion"):
        score += 5
    if extra.get("salamander_companion"):
        score += 5
    if extra.get("learned_mycology"):
        score += 5
    if extra.get("learned_tracking"):
        score += 5

    # Violence penalties
    if extra.get("has_killed_fungi"):
        score -= 10
    if extra.get("golem_protection_lost"):
        score -= 5
    if extra.get("bee_trade_destroyed"):
        score -= 5

    # Environmental threats resolved
    if extra.get("spore_mother_healed"):
        score += 10  # Prevents spore spread
    if extra.get("telescope_repaired"):
        score += 10  # Prevents cold spread

    return max(0, min(100, score))
