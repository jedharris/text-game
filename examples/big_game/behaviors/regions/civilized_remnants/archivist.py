"""The Archivist - Lore Trading and Knowledge System.

The Archivist is a spectral guardian of the deep archives.
Trades artifacts for knowledge and requires proving worth.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import apply_trust_change, transition_state

# Vocabulary
vocabulary: Dict[str, Any] = {
    "events": []
}


def on_archivist_dialog(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle dialog with the Archivist."""
    state = accessor.game_state
    archivist = entity

    if not hasattr(archivist, "id") or archivist.id != "the_archivist":
        return EventResult(allow=True, feedback=None)

    keyword = context.get("keyword", "").lower()
    sm = archivist.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "guardian"))

    # Lore/knowledge trading
    if any(kw in keyword for kw in ["lore", "knowledge", "trade", "artifact"]):
        return _handle_lore_trade(archivist, accessor, current_state, context)

    # Proving worth
    if any(kw in keyword for kw in ["prove", "worth", "test", "trial"]):
        return _handle_prove_worth(archivist, accessor, current_state)

    # State-based responses
    if current_state == "guardian":
        return EventResult(
            allow=True,
            feedback=(
                "The Archivist's spectral form shimmers with protective magic. "
                "'The deep archive holds knowledge too dangerous for the unworthy. "
                "Prove yourself, and perhaps I will share its secrets.'"
            )
        )
    elif current_state == "helpful":
        return EventResult(
            allow=True,
            feedback=(
                "The Archivist gestures toward ancient texts. "
                "'You have proven yourself a worthy seeker. Ask, and I shall teach.'"
            )
        )
    elif current_state == "allied":
        return EventResult(
            allow=True,
            feedback=(
                "The Archivist regards you as an equal. "
                "'Together we preserve what was lost. What do you seek to learn?'"
            )
        )

    return EventResult(allow=True, feedback=None)


def on_archivist_gift(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle artifact gifts to Archivist."""
    state = accessor.game_state
    archivist = entity
    item_context = context.get("item")

    if not item_context:
        return EventResult(allow=True, feedback=None)

    item_id = item_context.id if hasattr(item_context, "id") else str(item_context)

    # Artifacts the Archivist values
    ARTIFACTS = {
        "alpha_fang_fragment": {"trust": 2, "knowledge": "beast_wild_secrets"},
        "spore_heart_fragment": {"trust": 2, "knowledge": "fungal_depths_lore"},
        "waystone_fragment": {"trust": 3, "knowledge": "meridian_nexus_knowledge"},
    }

    artifact = ARTIFACTS.get(item_id)

    if artifact:
        # Check current state - gifts help prove worth
        sm = archivist.properties.get("state_machine", {})
        current_state = sm.get("current", sm.get("initial", "guardian"))

        # Apply trust
        apply_trust_change(entity=archivist, delta=artifact["trust"])

        # Transition states
        if current_state == "guardian" and archivist.properties.get("trust_state", {}).get("current", 0) >= 2:
            transition_state(archivist, "helpful")
        elif current_state == "helpful" and archivist.properties.get("trust_state", {}).get("current", 0) >= 4:
            transition_state(archivist, "allied")

        # Grant knowledge
        player = state.actors.get("player")
        if player:
            if "knowledge" not in player.properties:
                player.properties["knowledge"] = []
            player.properties["knowledge"].append(artifact["knowledge"])

            # Remove item from player
            from src.types import ItemId
            if ItemId(item_id) in player.inventory:
                player.inventory.remove(ItemId(item_id))

            # Update item location
            for item in state.items:
                if item.id == item_id:
                    item.location = "the_archivist"
                    break

        return EventResult(
            allow=True,
            feedback=(
                f"The Archivist's eyes widen with recognition. 'A {item_id.replace('_', ' ')}! "
                f"Such artifacts are rare indeed.' The spectral form brightens. "
                f"'In exchange, let me share what I know...'"
            )
        )

    return EventResult(
        allow=True,
        feedback="The Archivist examines it briefly. 'Interesting, but not what I seek.'"
    )


def _handle_lore_trade(archivist: Any, accessor: Any, current_state: str, context: dict[str, Any]) -> EventResult:
    """Handle lore trading requests."""
    if current_state == "guardian":
        return EventResult(
            allow=True,
            feedback=(
                "The Archivist shakes their head. 'Knowledge must be earned. "
                "Bring me fragments of power - artifacts from the wild lands. "
                "Only then will I deem you worthy.'"
            )
        )

    # In helpful or allied state, explain what's needed
    return EventResult(
        allow=True,
        feedback=(
            "The Archivist gestures to ancient shelves. 'I trade knowledge for artifacts. "
            "Bring me fragments of power: alpha fangs, spore hearts, waystone shards. "
            "Each holds secrets worth preserving.'"
        )
    )


def _handle_prove_worth(archivist: Any, accessor: Any, current_state: str) -> EventResult:
    """Handle prove worth dialog."""
    state = accessor.game_state

    if current_state != "guardian":
        return EventResult(
            allow=True,
            feedback="The Archivist nods. 'You have already proven yourself worthy.'"
        )

    # Check if player has any artifacts
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    has_artifacts = any(
        item_id in player.inventory
        for item_id in ["alpha_fang_fragment", "spore_heart_fragment", "waystone_fragment"]
    )

    if has_artifacts:
        return EventResult(
            allow=True,
            feedback=(
                "The Archivist's gaze sharpens. 'I sense you carry fragments of power. "
                "Give them to me, and I shall judge your worth.'"
            )
        )

    return EventResult(
        allow=True,
        feedback=(
            "The Archivist studies you. 'Venture into the wild lands. Face the beasts, "
            "the spores, the nexus. Return with proof of your trials, and we shall speak again.'"
        )
    )
