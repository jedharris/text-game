"""Camp Leader Mira - Quest and Commitment System.

Mira offers time-limited rescue quests for survivors.
Success unlocks camp services and alliance.
Failure results in disappointment and lost trust.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_types import CommitmentState, TurnNumber
from src.infrastructure_utils import (
    apply_trust_change,
    get_current_turn,
    transition_state,
)
from src.state_manager import Commitment
from src.types import CommitmentId

# Vocabulary: wire hooks to events
vocabulary: Dict[str, Any] = {
    "events": []
}

# Quest keywords
QUEST_KEYWORDS = ["help", "quest", "survivors", "mission", "task", "assist"]
PROGRESS_KEYWORDS = ["progress", "update", "status", "how"]


def on_mira_dialog(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle dialog with Mira including quest offers and updates.

    Args:
        entity: Mira NPC
        accessor: StateAccessor instance
        context: Context with keyword

    Returns:
        EventResult with dialog response
    """
    state = accessor.game_state
    mira = entity

    if not hasattr(mira, "id") or mira.id != "camp_leader_mira":
        return EventResult(allow=True, feedback=None)

    keyword = context.get("keyword", "").lower()

    # Get Mira's current state and trust
    sm = mira.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "neutral"))
    trust_state = mira.properties.get("trust_state", {"current": 0})
    trust = trust_state.get("current", 0)

    # Check for quest-related keywords
    if any(kw in keyword for kw in QUEST_KEYWORDS):
        return _handle_quest_offer(mira, accessor, current_state, trust)

    # Check for progress update keywords
    if any(kw in keyword for kw in PROGRESS_KEYWORDS):
        return _handle_quest_status(mira, accessor)

    # Default responses based on state
    if current_state == "neutral":
        return EventResult(
            allow=True,
            feedback=(
                "Mira surveys the camp with weary eyes. 'We're holding together, "
                "but barely. Too many people, not enough supplies. If you're looking "
                "to help, I have tasks that need doing.'"
            )
        )
    elif current_state == "friendly":
        return EventResult(
            allow=True,
            feedback=(
                "Mira nods in recognition. 'You've proven yourself reliable. "
                "That counts for a lot in times like these.'"
            )
        )
    elif current_state == "allied":
        return EventResult(
            allow=True,
            feedback=(
                "Mira clasps your shoulder firmly. 'You're one of us now. "
                "This camp stands because of people like you.'"
            )
        )
    elif current_state == "disappointed":
        return EventResult(
            allow=True,
            feedback=(
                "Mira's expression hardens. 'I gave you a task, and you failed. "
                "People are counting on me to make good decisions. You've proven "
                "you're not someone I can trust.'"
            )
        )

    return EventResult(
        allow=True,
        feedback="Mira tends to the camp's needs, her face lined with exhaustion."
    )


def _handle_quest_offer(mira: Any, accessor: Any, current_state: str, trust: int) -> EventResult:
    """Handle quest offer from Mira."""
    state = accessor.game_state
    extra = state.extra

    # Check if quest already active or completed
    if extra.get("mira_quest_active"):
        return EventResult(
            allow=True,
            feedback="Mira shakes her head. 'You already have a task from me. Complete it first.'"
        )

    if extra.get("mira_quest_completed"):
        return EventResult(
            allow=True,
            feedback="Mira smiles wearily. 'You've already helped us immensely. We're in your debt.'"
        )

    if extra.get("mira_quest_failed"):
        return EventResult(
            allow=True,
            feedback="Mira's jaw tightens. 'I gave you a chance once. I won't make that mistake again.'"
        )

    # Check state requirements
    if current_state == "disappointed":
        return EventResult(
            allow=True,
            feedback="Mira turns away. 'I don't have time for those who let me down.'"
        )

    # Offer the quest
    if current_state == "neutral" and trust >= 0:
        # Create commitment entity
        current_turn = get_current_turn(state)

        commitment = Commitment(
            id=CommitmentId("commit_mira_rescue"),
            name="Rescue Trapped Survivors",
            description="Save survivors from the storage district before time runs out",
            behaviors=["behaviors.shared.infrastructure.commitments"]
        )
        commitment.properties["state"] = CommitmentState.ACTIVE
        commitment.properties["target_actor"] = "camp_leader_mira"
        commitment.properties["made_at_turn"] = current_turn
        commitment.properties["deadline_turn"] = TurnNumber(current_turn + 20)
        commitment.properties["hope_applied"] = False

        state.commitments.append(commitment)

        extra["mira_quest_active"] = True
        extra["mira_quest_offered_turn"] = current_turn

        return EventResult(
            allow=True,
            feedback=(
                "Mira's expression grows grave. 'We have survivors trapped in the "
                "old storage district. Fungal growth has them cut off. I need someone "
                "to get them out.' She meets your eyes. 'You have 20 turns. After that...' "
                "She doesn't finish the sentence. 'Can you do this?'"
            )
        )

    return EventResult(
        allow=True,
        feedback="Mira studies you for a moment, then shakes her head. 'I need to know I can trust you first.'"
    )


def _handle_quest_status(mira: Any, accessor: Any) -> EventResult:
    """Handle quest status inquiry."""
    state = accessor.game_state
    extra = state.extra

    if not extra.get("mira_quest_active"):
        if extra.get("mira_quest_completed"):
            return EventResult(
                allow=True,
                feedback="Mira nods. 'You brought them back safely. The camp is stronger for it.'"
            )
        elif extra.get("mira_quest_failed"):
            return EventResult(
                allow=True,
                feedback="Mira's face darkens. 'They didn't make it. Because you took too long.'"
            )
        else:
            return EventResult(
                allow=True,
                feedback="Mira looks puzzled. 'I haven't given you any tasks yet.'"
            )

    # Quest is active - check time remaining
    current_turn = get_current_turn(state)
    offered_turn = extra.get("mira_quest_offered_turn", current_turn)
    turns_elapsed = current_turn - offered_turn
    turns_remaining = 20 - turns_elapsed

    if turns_remaining <= 0:
        return EventResult(
            allow=True,
            feedback="Mira's face is grim. 'Time's run out. I hope you move faster next time.'"
        )

    return EventResult(
        allow=True,
        feedback=f"Mira checks the sun's position. 'You have about {turns_remaining} turns left. Hurry.'"
    )


def on_quest_complete(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle successful completion of Mira's rescue quest.

    This should be called when the player successfully rescues survivors.

    Args:
        entity: Mira NPC
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with success response
    """
    state = accessor.game_state
    extra = state.extra

    if not hasattr(entity, "id") or entity.id != "camp_leader_mira":
        return EventResult(allow=True, feedback=None)

    # Check quest is active
    if not extra.get("mira_quest_active"):
        return EventResult(allow=True, feedback=None)

    # Mark quest complete
    extra["mira_quest_active"] = False
    extra["mira_quest_completed"] = True

    # Update Mira's state and trust
    mira = state.actors.get("camp_leader_mira")
    if mira:
        transition_state(mira, "allied")
        apply_trust_change(entity=mira, delta=2)

    # Unlock camp services
    extra["camp_services_unlocked"] = True

    return EventResult(
        allow=True,
        feedback=(
            "Mira's exhausted face breaks into a genuine smile as the survivors "
            "stumble into camp. 'You did it. You actually did it.' She clasps your hand firmly. "
            "'This camp is your home now, if you want it. You've earned that and more.'"
        )
    )


def on_quest_failed(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle failure of Mira's rescue quest (time ran out).

    Called when the commitment expires without completion.

    Args:
        entity: Mira NPC
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with failure response
    """
    state = accessor.game_state
    extra = state.extra

    if not hasattr(entity, "id") or entity.id != "camp_leader_mira":
        return EventResult(allow=True, feedback=None)

    # Check quest is active
    if not extra.get("mira_quest_active"):
        return EventResult(allow=True, feedback=None)

    # Mark quest failed
    extra["mira_quest_active"] = False
    extra["mira_quest_failed"] = True

    # Update Mira's state and trust
    mira = state.actors.get("camp_leader_mira")
    if mira:
        transition_state(mira, "disappointed")
        apply_trust_change(entity=mira, delta=-3)

    return EventResult(
        allow=True,
        feedback=(
            "Word arrives that the trapped survivors didn't make it. The fungal growth "
            "consumed them before rescue arrived. Mira's face goes pale, then hardens. "
            "'I trusted you with their lives. I won't make that mistake again.'"
        )
    )
