"""Environmental Spread Turn Phase Handler.

Checks environmental spread milestones each turn.
Applies location property changes when milestones are reached.
"""

from typing import Any

from src.behavior_manager import EventResult
from src.infrastructure_types import TurnNumber
from src.infrastructure_utils import (
    check_spread_halt_flag,
    get_current_turn,
    get_due_milestones,
    get_environmental_spreads,
    mark_milestone_reached,
)

# Vocabulary: wire hook to event
vocabulary = {
    "events": [
        {
            "event": "on_spread_check",
            "hook": "turn_phase_spread",
            "description": "Check environmental spread milestones each turn",
        }
    ]
}


def on_spread_check(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Check environmental spread milestones and apply effects.

    This is called once per turn as part of the turn phase sequence.
    For each active spread:
    - Check if halt flag is set (spread stops)
    - Find milestones that have been reached
    - Apply milestone effects to locations

    Args:
        entity: None (game-wide handler)
        accessor: StateAccessor instance
        context: Context dict with current_turn

    Returns:
        EventResult with messages about spread changes
    """
    state = accessor.state
    current_turn = get_current_turn(state)
    spreads = get_environmental_spreads(state)

    messages = []

    for spread_id, spread in spreads.items():
        # Check if spread is halted
        if check_spread_halt_flag(state, spread_id):
            continue

        # Check if spread is active
        if not spread.get("active", False):
            continue

        # Get milestones that are now due
        due_milestones = get_due_milestones(state, spread_id, current_turn)

        for milestone in due_milestones:
            turn = milestone.get("turn")
            effects = milestone.get("effects", [])

            # Apply effects to locations
            for effect in effects:
                location_patterns = effect.get("locations", [])
                prop_name = effect.get("property_name")
                prop_value = effect.get("property_value")

                # Apply to matching locations
                for loc in state.locations:
                    if _location_matches_patterns(loc.id, location_patterns):
                        loc.properties[prop_name] = prop_value

            # Mark milestone as reached
            mark_milestone_reached(state, spread_id, TurnNumber(turn))

            # Add message for narration
            messages.append(f"Environmental change: {spread_id} milestone {turn}")

    if not messages:
        return EventResult(allow=True, message=None)

    return EventResult(
        allow=True,
        message="\n".join(messages),
    )


def _location_matches_patterns(location_id: str, patterns: list[str]) -> bool:
    """Check if a location ID matches any of the given glob patterns.

    Simple pattern matching:
    - "region/*" matches all locations with that region property
    - Exact ID matches the location

    Args:
        location_id: Location ID to check
        patterns: List of patterns to match against

    Returns:
        True if location matches any pattern
    """
    import fnmatch

    for pattern in patterns:
        if fnmatch.fnmatch(location_id, pattern):
            return True
    return False
