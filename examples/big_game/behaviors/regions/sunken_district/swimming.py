"""Swimming skill teaching for Old Swimmer Jek.

Jek teaches basic_swimming when asked about swimming.
Grants player the skill needed to enter submerged passages.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult

vocabulary: Dict[str, Any] = {
    "events": []
}


def on_jek_teach(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle Jek teaching swimming skill.

    Called via dialog_reactions handler when player asks about swimming.

    Args:
        entity: The actor being spoken to (Jek)
        accessor: StateAccessor instance
        context: Context with keyword, topic_name

    Returns:
        EventResult with teaching result
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "old_swimmer_jek":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    # Check if already learned
    if player.properties.get("skills", {}).get("basic_swimming"):
        return EventResult(
            allow=True,
            feedback=(
                "'You already know the way of the water, friend. "
                "Trust your body — it remembers.'"
            ),
        )

    # Grant swimming skill
    if "skills" not in player.properties:
        player.properties["skills"] = {}
    player.properties["skills"]["basic_swimming"] = True

    state.extra["learned_swimming"] = True

    return EventResult(
        allow=True,
        feedback=(
            "Old Jek spends time teaching you the basics of swimming — "
            "how to hold your breath, move through currents, and stay calm "
            "when water closes over your head. 'The water isn't your enemy,' "
            "he says. 'It's just... indifferent. Respect that and you'll survive.'"
        ),
    )
