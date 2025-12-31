"""Bear Cubs Healing Commitment for Beast Wilds.

Implements the commitment to heal the dire bear's sick cubs.
More forgiving timer (30 turns) compared to Sira.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_types import TurnNumber
from src.infrastructure_utils import (
    apply_trust_change,
    create_commitment,
    get_current_turn,
    transition_state,
)

# Vocabulary: wire hooks to events
# Note: Dialog reactions are handled by infrastructure/dialog_reactions.py
# Note: Item use reactions are handled by infrastructure/item_use_reactions.py
# Note: Commitment failure is handled by infrastructure/commitment_reactions.py
# Bear must have appropriate reaction configurations
vocabulary: Dict[str, Any] = {
    "events": []
}


def on_bear_encounter(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle first encounter with the dire bear.

    The bear is extremely hostile, protecting her sick cubs.
    This provides the initial hook for the healing commitment.

    Args:
        entity: The dire bear actor
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with encounter description
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "dire_bear":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    extra = state.extra

    # Check if already encountered
    if extra.get("bear_encountered"):
        return EventResult(allow=True, feedback=None)

    extra["bear_encountered"] = True

    # Get bear's current state
    bear = state.actors.get("dire_bear")
    if not bear:
        return EventResult(allow=True, feedback=None)

    sm = bear.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "hostile"))

    if current_state == "hostile":
        return EventResult(
            allow=True,
            feedback=(
                "A massive shape emerges from the darkness of the den - a dire bear, "
                "larger than any natural creature. She rears up with a thunderous roar, "
                "her eyes blazing with protective fury. Behind her, you glimpse two small "
                "forms huddled together, their breathing shallow and labored. The cubs are sick. "
                "The bear positions herself between you and her young, claws extended. "
                "She looks ready to attack, but there's desperation in her eyes alongside the rage."
            ),
        )

    return EventResult(allow=True, feedback=None)


# Keywords that trigger the commitment
COMMITMENT_KEYWORDS = [
    "heal",
    "help",
    "medicine",
    "save",
    "cubs",
    "promise",
    "herbs",
]


def on_bear_commitment(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Create bear cubs commitment when player promises to help.

    Unlike Sira, this commitment is explicitly triggered by
    player dialog, not by first encounter.

    Args:
        entity: The actor being spoken to (dire bear)
        accessor: StateAccessor instance
        context: Context with keyword, dialog_text

    Returns:
        EventResult with commitment creation result
    """
    # Check if this is the dire bear
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "dire_bear":
        return EventResult(allow=True, feedback=None)

    # Check if keyword matches commitment triggers
    keyword = context.get("keyword", "").lower()
    if not any(trigger in keyword for trigger in COMMITMENT_KEYWORDS):
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    extra = state.extra

    # Check if commitment already exists
    if extra.get("bear_cubs_commitment_created"):
        return EventResult(
            allow=True,
            feedback="You have already promised to help the cubs.",
        )

    # Create the commitment (config must exist in game state)
    # Config ID "commit_bear_cubs" should be defined in game_state.json
    current_turn = get_current_turn(state)
    create_commitment(
        state=state,
        config_id="commit_bear_cubs",
        current_turn=current_turn,
    )

    extra["bear_cubs_commitment_created"] = True
    extra["bear_cubs_commitment_turn"] = get_current_turn(state)

    # Bear calms slightly and gives hint
    bear = state.actors.get("dire_bear")
    if bear:
        # Reduce immediate hostility
        sm = bear.properties.get("state_machine")
        if sm:
            # Don't transition state yet, just note the commitment
            pass

    return EventResult(
        allow=True,
        feedback=(
            "The bear's aggression lessens slightly. She looks at her cubs, "
            "then pointedly toward the southern trail. The message is clear: "
            "what they need lies to the south."
        ),
    )


def on_cubs_healed(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle healing cubs with healing herbs.

    Using healing_herbs on the cubs fulfills the commitment
    and transitions the bear to grateful state.

    Args:
        entity: The item being used
        accessor: StateAccessor instance
        context: Context with target

    Returns:
        EventResult with healing result
    """
    # Check if item is healing herbs
    item_id = entity.id if hasattr(entity, "id") else str(entity)
    if "healing_herbs" not in item_id.lower():
        return EventResult(allow=True, feedback=None)

    # Check if target is cubs or bear (using on cubs affects them)
    target = context.get("target")
    target_id = target.id if target and hasattr(target, "id") else str(target) if target else ""

    # Accept targeting cubs directly or the bear
    valid_targets = ["bear_cub_1", "bear_cub_2", "dire_bear"]
    if target_id not in valid_targets:
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state

    # Mark cubs as healed
    state.extra["cubs_healed"] = True

    # Transition bear to grateful state
    bear = state.actors.get("dire_bear")
    if bear:
        sm = bear.properties.get("state_machine")
        if sm:
            transition_state(sm, "grateful")

        # Increase trust
        # Initialize trust_state if missing
        if "trust_state" not in bear.properties:
            bear.properties["trust_state"] = {"current": 0}

        apply_trust_change(entity=bear, delta=3)

    # Mark cubs as recovering
    for cub_id in ["bear_cub_1", "bear_cub_2"]:
        cub = state.actors.get(cub_id)
        if cub:
            cub.properties["recovering"] = True
            cub.properties["sick"] = False

    return EventResult(
        allow=True,
        feedback=(
            "The cubs eagerly consume the healing herbs. Within moments, "
            "their labored breathing eases. The dire bear approaches slowly, "
            "her massive head lowering in what can only be gratitude."
        ),
    )


def on_cubs_died(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle cubs dying from failed commitment.

    The bear becomes vengeful and will hunt the player.

    Args:
        entity: The commitment that failed
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult noting the consequence
    """
    commitment_id = context.get("commitment_id")
    if commitment_id != "commit_bear_cubs":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state

    # Transition bear to vengeful state
    bear = state.actors.get("dire_bear")
    if bear:
        sm = bear.properties.get("state_machine")
        if sm:
            transition_state(sm, "vengeful")

        # Set trust to minimum
        trust_state = bear.properties.get("trust_state", {"current": 0})
        trust_state["current"] = trust_state.get("floor", -5)
        bear.properties["trust_state"] = trust_state
        bear.properties["hunts_player"] = True

    # Mark cubs as dead
    for cub_id in ["bear_cub_1", "bear_cub_2"]:
        cub = state.actors.get(cub_id)
        if cub:
            cub.properties["dead"] = True

    state.extra["cubs_died"] = True

    return EventResult(
        allow=True,
        feedback=(
            "The cubs' breathing has stopped. The dire bear's grief-stricken "
            "roar echoes through the forest, transforming into something darker. "
            "She will remember your face."
        ),
    )
