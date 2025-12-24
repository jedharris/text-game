"""Sira Rescue Mechanics for Beast Wilds.

Implements the time-sensitive commitment to save Hunter Sira.
Timer starts on first encounter, not on explicit commitment.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_types import CommitmentId, GossipId, TurnNumber
from src.types import ActorId
from src.infrastructure_utils import (
    create_commitment,
    create_gossip,
    get_current_turn,
)

# Vocabulary: wire hooks to events
# Note: Death reactions are handled by infrastructure/death_reactions.py
# Note: First encounter reactions are handled by infrastructure/encounter_reactions.py
# Note: Condition removal is handled by infrastructure/condition_reactions.py
# Sira must have appropriate reaction configurations
vocabulary: Dict[str, Any] = {
    "events": []
}


def on_sira_encounter(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Start Sira rescue commitment on first encounter.

    The timer starts immediately when player finds Sira, not when
    they explicitly promise to help. This is the designed "trap" -
    players who explore elsewhere will fail.

    Args:
        entity: The actor being encountered (Sira)
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with encounter narration
    """
    # Check if this is Sira
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "npc_hunter_sira":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    extra = state.extra

    # Check if commitment already exists
    if extra.get("sira_commitment_created"):
        return EventResult(allow=True, feedback=None)

    # Create the commitment (config must exist in game state)
    # Config ID "commit_sira_rescue" should be defined in game_state.json
    current_turn = get_current_turn(state)
    create_commitment(
        state=state,
        config_id="commit_sira_rescue",
        current_turn=current_turn,
    )

    extra["sira_commitment_created"] = True
    extra["sira_first_encounter_turn"] = get_current_turn(state)

    return EventResult(
        allow=True,
        feedback=(
            "Sira's condition is critical - the clock is now ticking. "
            "She needs bandages and medical care urgently."
        ),
    )


def on_sira_death(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Create gossip to Elara when Sira dies.

    If player was present (commitment exists), gossip reaches Elara
    in 12 turns. This affects trust with Elara.

    Args:
        entity: The actor who died (Sira)
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult allowing the death
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "npc_hunter_sira":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state

    # Check if player was involved (commitment existed)
    if state.extra.get("sira_commitment_created"):
        # Create gossip to Elara
        create_gossip(
            state=state,
            content="Someone was with Sira when she died",
            source_npc=ActorId("traveler"),
            target_npcs=[ActorId("npc_healer_elara")],
            delay_turns=12,
            confession_window=12,
            gossip_id=GossipId("gossip_sira_death"),
        )

        # Set flag for Elara trust impact
        state.extra["sira_died_with_player"] = True

    return EventResult(
        allow=True,
        feedback="Sira's struggle has ended. News will travel south in time.",
    )


def on_sira_healed(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Track Sira's healing progress.

    Stopping bleeding and healing leg are separate steps.
    Both must be completed to fulfill the commitment.

    Args:
        entity: The actor being healed (Sira)
        accessor: StateAccessor instance
        context: Context with condition_type, treatment

    Returns:
        EventResult with healing result
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "npc_hunter_sira":
        return EventResult(allow=True, feedback=None)

    condition_type = context.get("condition_type")
    state = accessor.game_state

    if condition_type == "bleeding":
        state.extra["sira_bleeding_stopped"] = True
        return EventResult(
            allow=True,
            feedback="The bleeding stops. Sira's color improves slightly.",
        )

    if condition_type == "leg_injury":
        state.extra["sira_leg_healed"] = True

        # Check if fully healed
        if state.extra.get("sira_bleeding_stopped"):
            state.extra["sira_healed"] = True
            # Fulfill commitment will be handled by commitment system
            return EventResult(
                allow=True,
                feedback=(
                    "Sira's leg is mended. She tests it carefully, then looks "
                    "at you with gratitude. 'You saved my life. I won't forget this.'"
                ),
            )

        return EventResult(
            allow=True,
            feedback="The leg is splinted, but the bleeding must also be stopped.",
        )

    return EventResult(allow=True, feedback=None)
