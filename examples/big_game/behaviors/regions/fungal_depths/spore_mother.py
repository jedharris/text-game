"""Spore Mother Mechanics for Fungal Depths.

Implements the heal-or-kill choice with the Spore Mother
and sporeling pack dynamics.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_types import GossipId
from src.types import ActorId
from src.infrastructure_utils import (
    create_gossip,
    get_current_turn,
    transition_state,
)

# Vocabulary: wire hooks to events
# Note: Pack state mirroring is handled by infrastructure/pack_mirroring.py
# Note: Item use reactions are handled by infrastructure/item_use_reactions.py
# Note: Death reactions are handled by infrastructure/death_reactions.py
# Note: Turn phase events are handled by infrastructure/turn_phase_dispatcher.py
# Spore Mother must have pack_behavior, item_use_reactions, death_reactions config
vocabulary: Dict[str, Any] = {
    "events": [],
    # Add "spore" as adjective so "ask about spore mother" parses correctly
    "adjectives": [{"word": "spore", "synonyms": []}]
}


def on_spore_mother_presence(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Track player presence in Spore Heart for wary transition.

    After 3 turns without attacking, Spore Mother becomes wary.

    Args:
        entity: None (regional check)
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with state change message if applicable
    """
    state = accessor.game_state

    # Check if player is in Spore Heart
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    player_loc = player.properties.get("location")
    if player_loc != "spore_heart":
        # Reset counter if not in spore heart
        state.extra["spore_mother_presence_turns"] = 0
        return EventResult(allow=True, feedback=None)

    # Get Spore Mother
    mother = state.actors.get("npc_spore_mother")
    if not mother:
        return EventResult(allow=True, feedback=None)

    sm = mother.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "hostile"))

    # Only track for hostile state
    if current_state != "hostile":
        return EventResult(allow=True, feedback=None)

    # Check if player attacked this turn
    if state.extra.get("player_attacked_this_turn"):
        state.extra["spore_mother_presence_turns"] = 0
        state.extra["player_attacked_this_turn"] = False
        return EventResult(allow=True, feedback=None)

    # Increment presence counter
    turns = state.extra.get("spore_mother_presence_turns", 0) + 1
    state.extra["spore_mother_presence_turns"] = turns

    if turns >= 3:
        # Transition to wary
        transition_state(sm, "wary")
        state.extra["spore_mother_presence_turns"] = 0

        return EventResult(
            allow=True,
            feedback=(
                "The Spore Mother's hostility fades to watchful curiosity. "
                "Through empathic spores, you sense... questions. Confusion. "
                "Why didn't you attack? The sporelings hesitate, mirroring her uncertainty."
            ),
        )

    return EventResult(allow=True, feedback=None)


def on_spore_mother_heal(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle healing Spore Mother with heartmoss.

    This can work even mid-combat, transitioning to allied state.

    Args:
        entity: The item being used
        accessor: StateAccessor instance
        context: Context with target

    Returns:
        EventResult with healing result
    """
    item_id = entity.id if hasattr(entity, "id") else str(entity)
    if "heartmoss" not in item_id.lower():
        return EventResult(allow=True, feedback=None)

    target = context.get("target")
    target_id = target.id if target and hasattr(target, "id") else str(target) if target else ""
    if target_id != "npc_spore_mother":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    mother = state.actors.get("npc_spore_mother")
    if not mother:
        return EventResult(allow=True, feedback=None)

    # Transition to allied
    sm = mother.properties.get("state_machine", {})
    transition_state(sm, "allied")

    # Clear her blight condition
    conditions = mother.properties.get("conditions", {})
    if "fungal_blight" in conditions:
        del conditions["fungal_blight"]

    # Set flags
    state.extra["spore_mother_healed"] = True
    state.extra["has_spore_heart"] = True  # She gifts the waystone fragment

    # Give the spore_heart_fragment to the player
    spore_heart = state.get_item("spore_heart_fragment")
    if spore_heart:
        # Set item location and add to player inventory
        spore_heart.location = "player"
        player = state.actors.get("player")
        if player and spore_heart.id not in player.inventory:
            player.inventory.append(spore_heart.id)

    # Clear all spore levels in the region
    for loc in getattr(state, "locations", []):
        if hasattr(loc, "properties"):
            if loc.properties.get("spore_level"):
                loc.properties["spore_level"] = "none"

    # Create positive gossip
    create_gossip(
        state=state,
        content="The Spore Mother has been healed",
        source_npc=ActorId("spore_network"),
        target_npcs=[ActorId("npc_myconid_elder"), ActorId("echo")],
        delay_turns=1,
        gossip_id=GossipId("gossip_spore_mother_healed"),
    )

    # Mirror state to sporelings
    _update_sporeling_states(state, "allied")

    return EventResult(
        allow=True,
        feedback=(
            "As the heartmoss touches the Spore Mother, a wave of relief floods "
            "through the empathic connection. The dark blight veins fade, replaced "
            "by healthy bioluminescence. She pulses with gratitude - and gently "
            "releases something into your hands: a crystallized spore heart, "
            "warm with her thanks. The spore haze throughout the depths begins to clear."
        ),
    )


def on_spore_mother_death(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle Spore Mother death consequences.

    Killing her has severe reputation consequences and
    permanently affects the region.

    Args:
        entity: The actor who died
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with consequence message
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "npc_spore_mother":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state

    # Set death flags
    state.extra["spore_mother_dead"] = True
    state.extra["has_killed_fungi"] = True  # Also sets death mark

    # Drop trophy instead of waystone fragment
    state.extra["has_mother_heart"] = True  # The negative trophy

    # Create negative gossip
    create_gossip(
        state=state,
        content="The Spore Mother has been killed",
        source_npc=ActorId("spore_network"),
        target_npcs=[ActorId("npc_myconid_elder"), ActorId("echo")],
        delay_turns=1,
        gossip_id=GossipId("gossip_spore_mother_killed"),
    )

    # Myconid trust -5
    myconid = state.actors.get("npc_myconid_elder")
    if myconid:
        trust_state = myconid.properties.get("trust_state", {"current": 0})
        trust_state["current"] = trust_state.get("current", 0) - 5
        myconid.properties["trust_state"] = trust_state

    # Sporelings become confused
    _update_sporeling_states(state, "confused")

    return EventResult(
        allow=True,
        feedback=(
            "The Spore Mother's death cry echoes through your mind - raw pain, "
            "then emptiness. The organic walls shudder and begin to decay. "
            "The sporelings wander aimlessly, confused. You sense a ripple of "
            "horror spreading through every fungus in the depths. "
            "The spore haze will persist indefinitely now."
        ),
    )


def on_spore_mother_state_change(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Mirror Spore Mother state changes to sporelings.

    Args:
        entity: The Spore Mother
        accessor: StateAccessor instance
        context: Context with new_state

    Returns:
        EventResult allowing the change
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "npc_spore_mother":
        return EventResult(allow=True, feedback=None)

    new_state = context.get("new_state")
    if not new_state:
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    _update_sporeling_states(state, new_state)

    return EventResult(allow=True, feedback=None)


def on_spore_mother_talk(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle talk/ask commands directed at Spore Mother.

    The Spore Mother communicates through empathic spores, not words.
    Her communication vocabulary (from design Section 1.5):
    - Pain spike: sharp sensation through spore contact
    - Waves of need: desperate grasping sensation, seeking help
    - Gentle probing: curiosity, attention focusing on player
    - Warmth flood: gratitude, relief, connection established
    - Pressure surge: hostility, threat, spore burst incoming
    - Weakening pulse: her illness, dying, needs heartmoss

    Args:
        entity: The Spore Mother actor
        accessor: StateAccessor instance
        context: Context with keyword (topic) if ask command

    Returns:
        EventResult with empathic communication description
    """
    state = accessor.game_state
    mother = state.actors.get("npc_spore_mother")
    if not mother:
        return EventResult(allow=True, feedback=None)

    sm = mother.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "hostile"))

    # Get keyword if this is an "ask about" command
    keyword = context.get("keyword", "")

    # Generate empathic response based on current state
    if current_state == "hostile":
        feedback = (
            "The Spore Mother's massive cap turns toward you. A pressure surge "
            "builds in your chest - hostility, warning. Through the spore haze, "
            "you sense pain spike after pain spike, her suffering mixed with "
            "threat. Waves of desperate need wash over you, but underneath "
            "pulses something darker: she will defend herself. "
            "The sporelings bristle, mirroring her aggression."
        )
    elif current_state == "wary":
        feedback = (
            "The Spore Mother regards you with cautious attention. Gentle probing "
            "tendrils of sensation reach toward your mind - curiosity, questions. "
            "Underneath, you feel her weakening pulse, the illness that consumes her. "
            "Waves of need flow through the connection: she seeks something, "
            "desperately. The sensation of dying roots, of blight spreading... "
            "The sporelings watch, uncertain."
        )
    elif current_state == "allied":
        feedback = (
            "Warmth floods through the empathic connection as the Spore Mother "
            "acknowledges you. Gentle probing becomes welcoming embrace. You sense "
            "her gratitude - deep, ancient, patient. The spore-song hums with "
            "peaceful contentment. Through her, you feel the health of the fungal "
            "network, the slow pulse of life through miles of mycelium. "
            "The sporelings dance lazily around her, at peace."
        )
    elif current_state == "dead":
        feedback = (
            "There is nothing here but silence and decay. The empathic connection "
            "that once filled this chamber is gone, replaced by hollow emptiness. "
            "The organic walls are still. The sporelings wander aimlessly."
        )
    elif current_state == "confused":
        feedback = (
            "Erratic pulses of sensation wash over you - confusion, loss, "
            "searching. The Spore Mother's connection feels fractured, uncertain. "
            "The sporelings twitch and wander, reflecting her disorientation."
        )
    else:
        feedback = (
            "The Spore Mother's presence fills the chamber. Through the thick "
            "spore haze, you sense her awareness turning toward you."
        )

    return EventResult(allow=True, feedback=feedback)


def _update_sporeling_states(state: Any, new_state: str) -> None:
    """Update all sporeling states to match Mother."""
    sporeling_ids = ["npc_sporeling_1", "npc_sporeling_2", "npc_sporeling_3"]

    for sporeling_id in sporeling_ids:
        sporeling = state.actors.get(sporeling_id)
        if sporeling:
            sm = sporeling.properties.get("state_machine", {})
            if sm:
                # Add confused state if needed
                if new_state == "confused" and "confused" not in sm.get("states", []):
                    sm["states"] = sm.get("states", []) + ["confused"]
                transition_state(sm, new_state)
