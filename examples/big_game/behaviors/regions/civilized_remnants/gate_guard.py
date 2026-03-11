"""Gate Guard encounter and inspection for Civilized Remnants.

Handles:
- Infection detection when player enters town_gate
- State transitions based on reputation
- Companion entry warnings
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import transition_state


vocabulary: Dict[str, Any] = {
    "events": []
}


def on_gate_encounter(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle player encounter with gate guard.

    Checks for infection and companions. Updates guard state
    based on player reputation.

    Args:
        entity: The gate guard actor
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with inspection result
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "gate_guard":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    guard = state.actors.get("gate_guard")
    if not guard:
        return EventResult(allow=True, feedback=None)

    sm = guard.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "suspicious"))

    messages = []

    # Check for infection
    conditions = player.properties.get("conditions", {})
    if "fungal_infection" in conditions:
        messages.append(
            "The guard recoils, eyes widening. 'You're infected! I can see "
            "the spore marks on your skin. Can't let you in like that — "
            "healer's orders. Get yourself cured first.'"
        )
        state.extra["guard_detected_infection"] = True
        return EventResult(allow=True, feedback="\n".join(messages))

    # Check for beast companions (pack followers in player's location)
    companion_warnings = _check_companions(state, player)
    if companion_warnings:
        messages.append(companion_warnings)

    # Update state based on reputation/flags
    if current_state == "suspicious":
        # Check for reputation or good deeds
        if (state.extra.get("mira_quest_completed")
                or state.extra.get("delvan_rescued")
                or state.extra.get("garrett_rescued")):
            transition_state(sm, "neutral")
            messages.append(
                "The guard's posture relaxes as he recognizes you. "
                "'Word's gotten around about what you did. You're alright. "
                "Welcome to town.'"
            )
        else:
            messages.append(
                "The guard looks you over with obvious suspicion. "
                "'Another stranger. State your business.'"
            )
    elif current_state == "neutral":
        messages.append(
            "The guard nods in recognition. 'Welcome back.'"
        )
    elif current_state == "friendly":
        messages.append(
            "The guard grins. 'Good to see you again! Head on in.'"
        )

    feedback = "\n".join(messages) if messages else None
    return EventResult(allow=True, feedback=feedback)


def _check_companions(state: Any, player: Any) -> str | None:
    """Check if player has beast companions in their location."""
    player_loc = player.location
    warnings = []

    for actor_id, actor in state.actors.items():
        if actor_id == "player":
            continue
        if actor.location != player_loc:
            continue

        # Check for pack followers that follow the player
        pack = actor.properties.get("pack_behavior", {})
        if pack.get("leader") == "player" or pack.get("role") == "companion":
            name = actor.name
            # Check creature type for appropriate reaction
            if "wolf" in actor_id.lower():
                warnings.append(
                    f"The guard's hand goes to his weapon. 'A wolf?! "
                    f"Absolutely not. That thing stays outside the walls.'"
                )
            elif "spider" in actor_id.lower():
                warnings.append(
                    f"The guard stumbles backward. 'A giant spider?! "
                    f"Are you mad? Keep that thing away from the gate!'"
                )
            elif "sporeling" in actor_id.lower() or "myconid" in actor_id.lower():
                warnings.append(
                    f"The guard looks horrified. 'A spore creature? Inside "
                    f"the walls? Absolutely not — we have enough infection "
                    f"problems already.'"
                )
            elif "salamander" in actor_id.lower():
                warnings.append(
                    f"The guard eyes the {name} warily. 'A fire creature? "
                    f"If it burns anything, you're responsible. And I mean "
                    f"personally responsible.'"
                )

    return "\n".join(warnings) if warnings else None
