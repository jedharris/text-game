"""Spider Nest Mechanics for Beast Wilds.

The spider nest is the combat-only contrast - no diplomatic path.
Features web hazards, darkness, and respawning spiders.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_types import TurnNumber
from src.infrastructure_utils import get_current_turn

# Vocabulary: wire hooks to events
# Note: Death reactions are handled by infrastructure/death_reactions.py
# Note: Turn phase events are handled by infrastructure/turn_phase_dispatcher.py
# Note: Movement events are handled by infrastructure/movement_reactions.py
# Spider queen must have death_reactions; locations have turn_phase and movement effects
vocabulary: Dict[str, Any] = {
    "events": []
}

# Turns between spider respawns
RESPAWN_INTERVAL = 10


def on_spider_respawn_check(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Check if spiders should respawn in the nest.

    Every 10 turns while the queen lives, 2 giant spiders respawn.

    Args:
        entity: None (regional check)
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with respawn message if applicable
    """
    state = accessor.game_state
    extra = state.extra

    # Check if queen is alive
    queen = state.actors.get("spider_matriarch")
    if not queen:
        return EventResult(allow=True, feedback=None)

    queen_sm = queen.properties.get("state_machine", {})
    if queen_sm.get("current") == "dead":
        return EventResult(allow=True, feedback=None)

    # Check respawn timing
    current_turn = get_current_turn(state)
    last_respawn = extra.get("spider_last_respawn", 0)

    if current_turn - last_respawn < RESPAWN_INTERVAL:
        return EventResult(allow=True, feedback=None)

    # Count living spiders
    living_spiders = 0
    for actor_id, actor in state.actors.items():
        if "giant_spider" in actor_id:
            actor_sm = actor.properties.get("state_machine", {})
            if actor_sm.get("current") != "dead":
                living_spiders += 1

    # Respawn up to 2 if fewer than 2 living
    if living_spiders >= 2:
        extra["spider_last_respawn"] = current_turn
        return EventResult(allow=True, feedback=None)

    # Respawn spiders
    respawned = 0
    for i in range(1, 10):  # Support up to spider_9
        spider_id = f"giant_spider_{i}"
        spider = state.actors.get(spider_id)
        if spider:
            spider_sm = spider.properties.get("state_machine", {})
            if spider_sm.get("current") == "dead":
                spider_sm["current"] = "hostile"
                spider.properties["location"] = "spider_thicket"
                respawned += 1
                if living_spiders + respawned >= 2:
                    break

    extra["spider_last_respawn"] = current_turn

    if respawned > 0:
        return EventResult(
            allow=True,
            feedback=f"The darkness stirs - {respawned} spider(s) emerge from deeper tunnels.",
        )

    return EventResult(allow=True, feedback=None)


def on_web_movement(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Apply web slow effect when moving in spider gallery.

    Movement through webs costs 2 turns instead of 1.

    Args:
        entity: The player entity
        accessor: StateAccessor instance
        context: Context with destination

    Returns:
        EventResult with web effect message
    """
    destination = context.get("destination")
    dest_id = destination.id if destination and hasattr(destination, "id") else str(destination) if destination else ""

    if "spider_nest" not in dest_id.lower():
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state

    # Check for web effects - find location by id in list
    dest_loc = None
    for loc in getattr(state, "locations", []):
        if hasattr(loc, "id") and loc.id == dest_id:
            dest_loc = loc
            break

    if dest_loc and dest_loc.properties.get("web_effects"):
        # Double movement cost handled by engine based on property
        return EventResult(
            allow=True,
            feedback=(
                "Thick webs cling to everything, slowing your progress. "
                "You can feel vibrations traveling through them..."
            ),
        )

    return EventResult(allow=True, feedback=None)


def on_spider_queen_death(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle spider queen death - stop future respawns.

    Remaining spiders fight to death but no more will spawn.

    Args:
        entity: The actor who died
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with consequence message
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "spider_matriarch":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    state.extra["spider_queen_dead"] = True

    return EventResult(
        allow=True,
        feedback=(
            "The Spider Queen falls, her death scream echoing through the gallery. "
            "The remaining spiders shriek in confused fury, but no more will emerge "
            "from the depths. The nest is broken."
        ),
    )
