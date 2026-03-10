"""Drowning System for Sunken District.

Implements held-breath mechanics for non-breathable underwater locations.

Turn phase hook checks player location each turn:
- Entering non-breathable location: start breath timer
- In non-breathable location: tick breath, warn, apply damage
- Leaving non-breathable location: reset breath, surface message

Players with a breathing_item in inventory are immune.
Air bladder can be used on self to reset breath timer (consumes a use).
"""

from typing import Any, Dict, List, Optional

from src.behavior_manager import EventResult

# Vocabulary: turn phase hook for per-turn drowning check
vocabulary: Dict[str, Any] = {
    "hook_definitions": [
        {
            "hook_id": "turn_drowning",
            "invocation": "turn_phase",
            "after": ["turn_commitments"],
            "description": "Check drowning state based on player location breathability"
        }
    ],
    "events": [
        {
            "event": "on_turn_drowning",
            "hook": "turn_drowning",
            "description": "Per-turn drowning check and breath tracking",
        }
    ]
}

# Drowning parameters
MAX_BREATH = 12
WARNING_THRESHOLD = 8
CRITICAL_THRESHOLD = 10
DROWN_DAMAGE = 20


def _has_breathing_item(state: Any, actor_id: str) -> bool:
    """Check if actor has an item with breathing_item property in inventory."""
    actor = state.actors.get(actor_id)
    if not actor:
        return False
    for item in state.items:
        if item.location == actor_id and item.properties.get("breathing_item"):
            return True
    return False


def _get_location_breathable(state: Any, location_id: str) -> bool:
    """Check if a location is breathable. Defaults to True if not specified."""
    location = next((loc for loc in state.locations if loc.id == location_id), None)
    if not location:
        return True
    return location.properties.get("breathable", True)


def on_turn_drowning(
    entity: None,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Per-turn drowning check.

    Detects water transitions and ticks breath counter.

    Args:
        entity: None (turn phase hook)
        accessor: StateAccessor instance
        context: Turn context

    Returns:
        EventResult with drowning/breathing messages
    """
    state = accessor.game_state
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    breathable = _get_location_breathable(state, player.location)
    was_underwater = player.properties.get("underwater", False)

    # Transition: entered breathable location from underwater
    if breathable and was_underwater:
        player.properties["underwater"] = False
        breath = player.properties.get("breath_state")
        if breath:
            breath["current"] = 0
        return EventResult(
            allow=True,
            feedback="You break the surface, gasping for air. Sweet oxygen fills your lungs.",
        )

    # Transition: entered non-breathable location
    if not breathable and not was_underwater:
        player.properties["underwater"] = True

        if _has_breathing_item(state, "player"):
            return EventResult(
                allow=True,
                feedback="You plunge into the flooded passage. Your breathing equipment keeps you safe.",
            )

        # Initialize breath state
        player.properties["breath_state"] = {
            "current": 0,
            "max": MAX_BREATH,
        }
        return EventResult(
            allow=True,
            feedback=(
                f"You plunge into the flooded passage. Hold your breath! "
                f"You have {MAX_BREATH} turns of air."
            ),
        )

    # Staying underwater: tick breath
    if not breathable and was_underwater:
        # Breathing item grants immunity
        if _has_breathing_item(state, "player"):
            return EventResult(allow=True, feedback=None)

        breath = player.properties.get("breath_state")
        if not breath:
            breath = {"current": 0, "max": MAX_BREATH}
            player.properties["breath_state"] = breath

        current = breath.get("current", 0) + 1
        breath["current"] = current

        if current >= MAX_BREATH:
            health = player.properties.get("health", 100)
            player.properties["health"] = max(0, health - DROWN_DAMAGE)
            return EventResult(
                allow=True,
                feedback=(
                    f"You're drowning! [{DROWN_DAMAGE} damage] "
                    "Your lungs scream for air. You must surface NOW."
                ),
            )

        if current >= CRITICAL_THRESHOLD:
            return EventResult(
                allow=True,
                feedback="You're suffocating! Find air immediately!",
            )

        if current >= WARNING_THRESHOLD:
            return EventResult(
                allow=True,
                feedback="Your lungs are burning. You need air soon.",
            )

    return EventResult(allow=True, feedback=None)


def on_breathe(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle using air bladder on self to reset breath timer.

    Called via item_use_reactions self-use on air_bladder.

    Args:
        entity: The air_bladder item
        accessor: StateAccessor instance
        context: Context with item, actor_id

    Returns:
        EventResult with breath reset message
    """
    state = accessor.game_state
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    # Decrement uses
    uses = entity.properties.get("uses", 0)
    if uses <= 0:
        return EventResult(
            allow=False,
            feedback="The air bladder is spent — no air remains.",
        )

    entity.properties["uses"] = uses - 1
    remaining = uses - 1

    # Reset breath timer
    breath = player.properties.get("breath_state")
    if breath:
        breath["current"] = 0

    if not player.properties.get("underwater"):
        return EventResult(
            allow=True,
            feedback=(
                f"You breathe from the air bladder, though you don't really need to here. "
                f"{remaining} use{'s' if remaining != 1 else ''} remaining."
            ),
        )

    return EventResult(
        allow=True,
        feedback=(
            f"You press the bladder to your face and breathe deeply. "
            f"Fresh air fills your burning lungs. "
            f"{remaining} use{'s' if remaining != 1 else ''} remaining."
        ),
    )
