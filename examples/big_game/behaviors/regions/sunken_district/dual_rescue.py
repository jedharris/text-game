"""Dual Rescue Mechanics for Sunken District.

Implements the competing urgent rescues of Delvan and Garrett.
This creates the designed impossible choice.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_types import GossipId
from src.types import ActorId
from src.infrastructure_utils import (
    create_commitment,
    create_gossip,
    get_current_turn,
)

# Vocabulary: wire hooks to events
# Note: Death reactions are handled by infrastructure/death_reactions.py
# Note: First encounter reactions are handled by infrastructure/encounter_reactions.py
# Note: Room entry reactions are handled by infrastructure/location_reactions.py
# Note: Condition removal is handled by infrastructure/condition_reactions.py
# NPCs must have appropriate reaction configurations
vocabulary: Dict[str, Any] = {
    "events": []
}


# Dialog keywords for Delvan
UNDERCITY_KEYWORDS = ["undercity", "underground", "black market", "connections", "contacts", "smuggler", "fence"]
TRADE_KEYWORDS = ["trade", "buy", "sell", "goods", "supplies", "business"]


def on_delvan_dialog(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle dialog with Delvan.

    Post-rescue, Delvan can reveal undercity entrance as alternative to Vex.

    Args:
        entity: Delvan NPC
        accessor: StateAccessor instance
        context: Context with keyword

    Returns:
        EventResult with dialog response
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "merchant_delvan":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    extra = state.extra
    keyword = context.get("keyword", "").lower()

    # Get Delvan's current state
    sm = entity.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "trapped"))

    # If still trapped, limited dialog
    if current_state == "trapped":
        return EventResult(
            allow=True,
            feedback=(
                "Delvan gasps between pained breaths. 'Please... help me first... "
                "we can talk later...'"
            ),
        )

    # Check for undercity/connections keywords (only available if rescued)
    if any(kw in keyword for kw in UNDERCITY_KEYWORDS):
        if not extra.get("delvan_rescued"):
            return EventResult(
                allow=True,
                feedback="Delvan shakes his head. 'I don't know what you mean.'",
            )

        # Reveal undercity entrance
        if not extra.get("knows_undercity_entrance"):
            extra["knows_undercity_entrance"] = True
            return EventResult(
                allow=True,
                feedback=(
                    "Delvan lowers his voice conspiratorially. 'You saved my life, so I'll "
                    "share something valuable. The Undercity - there's a hidden entrance "
                    "in the old cistern. Look for the drainage grate with the merchant's mark.' "
                    "He traces a symbol in the dust. 'This gets you in without dealing with Vex.'"
                ),
            )
        else:
            return EventResult(
                allow=True,
                feedback=(
                    "Delvan nods. 'The cistern entrance - you remember the symbol I showed you? "
                    "That's your way in. Be careful down there.'"
                ),
            )

    # Check for trade keywords (only if rescued)
    if any(kw in keyword for kw in TRADE_KEYWORDS):
        if not extra.get("delvan_rescued"):
            return EventResult(
                allow=True,
                feedback="Delvan is in no condition to discuss business.",
            )

        return EventResult(
            allow=True,
            feedback=(
                "Delvan's merchant instincts return despite his ordeal. 'Once I recover, "
                "I'll be back in business. Good salvage from the flooded areas, if you "
                "can get it to me. I pay fair prices - better than most.'"
            ),
        )

    # Default post-rescue dialog
    if extra.get("delvan_rescued"):
        return EventResult(
            allow=True,
            feedback=(
                "Delvan regards you with genuine gratitude. 'I owe you my life. "
                "If there's anything I can help you with - information, connections - "
                "just ask.'"
            ),
        )

    return EventResult(
        allow=True,
        feedback="Delvan seems preoccupied with his injuries.",
    )


def on_delvan_encounter(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Start Delvan rescue commitment on first encounter.

    Delvan is trapped and bleeding - timer starts immediately.

    Args:
        entity: The actor (Delvan)
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with encounter narration
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "merchant_delvan":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    extra = state.extra

    if extra.get("delvan_commitment_created"):
        return EventResult(allow=True, feedback=None)

    # Create commitment (config must exist in game state)
    current_turn = get_current_turn(state)
    create_commitment(
        state=state,
        config_id="commit_delvan_rescue",
        current_turn=current_turn,
    )

    extra["delvan_commitment_created"] = True
    extra["delvan_encounter_turn"] = current_turn

    return EventResult(
        allow=True,
        feedback=(
            "You find Delvan pinned beneath fallen debris, blood seeping from "
            "a gash on his arm. He taps frantically on a pipe - Morse code. "
            "SOS. He's been signaling for help. Without treatment, he won't last long."
        ),
    )


def on_garrett_encounter(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Start Garrett rescue timer when entering his location.

    Garrett is in rising water - timer starts on room entry.

    Args:
        entity: The location being entered
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with encounter narration
    """
    loc_id = entity.id if hasattr(entity, "id") else None
    if "garrett" not in (loc_id or "").lower() and "rising_water" not in (loc_id or "").lower():
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    extra = state.extra

    if extra.get("garrett_commitment_created"):
        return EventResult(allow=True, feedback=None)

    # Create commitment (config must exist in game state)
    current_turn = get_current_turn(state)
    create_commitment(
        state=state,
        config_id="commit_garrett_rescue",
        current_turn=current_turn,
    )

    extra["garrett_commitment_created"] = True
    extra["garrett_encounter_turn"] = current_turn

    return EventResult(
        allow=True,
        feedback=(
            "The chamber is filling with water. Garrett clings to debris, "
            "head barely above the rising tide. 'Help! Please!' "
            "The water is rising fast - he has minutes, not hours."
        ),
    )


def on_rescue_success(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle successful rescue of either NPC.

    Args:
        entity: The NPC being rescued
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with success message
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    condition_type = context.get("condition_type")

    state = accessor.game_state

    if actor_id == "merchant_delvan" and condition_type == "bleeding":
        state.extra["delvan_rescued"] = True
        return EventResult(
            allow=True,
            feedback=(
                "You stop Delvan's bleeding. He grasps your hand. "
                "'You came. I wasn't sure anyone would.' His tapping stops - "
                "he doesn't need to signal anymore."
            ),
        )

    if actor_id == "sailor_garrett" and condition_type == "drowning":
        state.extra["garrett_rescued"] = True
        return EventResult(
            allow=True,
            feedback=(
                "You pull Garrett from the rising water. He coughs, sputters, "
                "then laughs with relief. 'I thought I was dead. Thank you.'"
            ),
        )

    return EventResult(allow=True, feedback=None)


def on_npc_death(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle rescue failure when NPC dies.

    Creates gossip and affects ending calculations.

    Args:
        entity: The NPC who died
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with failure message
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    state = accessor.game_state

    if actor_id == "merchant_delvan":
        state.extra["delvan_died"] = True

        create_gossip(
            state=state,
            content="Delvan died in the Sunken District",
            source_npc=ActorId("survivors"),
            target_npcs=[ActorId("echo"), ActorId("healer_elara")],
            delay_turns=15,
            gossip_id=GossipId("gossip_delvan_death"),
        )

        return EventResult(
            allow=True,
            feedback=(
                "The tapping stops. Delvan's hand falls still. "
                "You were too late."
            ),
        )

    if actor_id == "sailor_garrett":
        state.extra["garrett_died"] = True

        create_gossip(
            state=state,
            content="Garrett drowned in the Sunken District",
            source_npc=ActorId("survivors"),
            target_npcs=[ActorId("echo")],
            delay_turns=10,
            gossip_id=GossipId("gossip_garrett_death"),
        )

        return EventResult(
            allow=True,
            feedback=(
                "The water closes over Garrett's head. His struggles cease. "
                "You chose, and someone paid the price."
            ),
        )

    return EventResult(allow=True, feedback=None)
