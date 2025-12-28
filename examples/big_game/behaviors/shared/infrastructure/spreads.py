"""Environmental Spread Turn Phase Handler.

Checks environmental spread milestones each turn.
Applies location property changes when milestones are reached.
"""

from typing import Any

from src.behavior_manager import EventResult
from src.state_manager import Spread
from src.infrastructure_utils import get_bool_flag

# Vocabulary: wire hook to event
vocabulary = {
    "events": [
        {
            "event": "on_turn_spread",
            "hook": "turn_phase_spread",
            "description": "Check spread milestone if reached (per-entity)",
        }
    ]
}


def on_turn_spread(
    entity: Spread,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Check if this spread has reached a milestone (per-entity handler).

    Called once per spread per turn as part of the turn phase sequence.
    For each active spread:
    - Check if halt flag is set (spread stops)
    - Find milestones that have been reached
    - Apply milestone effects to locations

    Args:
        entity: The Spread entity being checked
        accessor: StateAccessor instance
        context: Context dict with current_turn

    Returns:
        EventResult with message about spread changes if milestone reached
    """
    state = accessor.game_state
    current_turn = context.get("current_turn", 0)

    # Check if spread is active
    if not entity.properties.get("active", False):
        return EventResult(allow=True, feedback=None)

    # Check if halt flag is set
    halt_flag = entity.properties.get("halt_flag")
    if halt_flag:
        flags = state.extra.get("flags", {})
        if get_bool_flag(flags, halt_flag):
            return EventResult(allow=True, feedback=None)

    # Get milestones and check which ones are due
    milestones = entity.properties.get("milestones", [])
    reached_milestones = entity.properties.get("reached_milestones", [])

    messages = []

    for milestone in milestones:
        milestone_turn = milestone.get("turn")
        if not milestone_turn or current_turn < milestone_turn:
            continue

        # Skip if already reached
        if milestone_turn in reached_milestones:
            continue

        # Milestone is now due - apply effects
        effects = milestone.get("effects", [])

        for effect in effects:
            location_patterns = effect.get("locations", [])
            prop_name = effect.get("property_name")
            prop_value = effect.get("property_value")

            if not prop_name:
                continue

            # Apply to matching locations
            for loc in state.locations:
                if _location_matches_patterns(loc.id, location_patterns):
                    loc.properties[prop_name] = prop_value

        # Mark milestone as reached
        if "reached_milestones" not in entity.properties:
            entity.properties["reached_milestones"] = []
        entity.properties["reached_milestones"].append(milestone_turn)

        # Add message for narration
        messages.append(f"Environmental change: {entity.name} milestone {milestone_turn}")

    if not messages:
        return EventResult(allow=True, feedback=None)

    return EventResult(allow=True, feedback="\n".join(messages))


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
