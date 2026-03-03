"""Service NPCs for Civilized Remnants.

Implements healer, shopkeeper, and other service providers
with trust-gated access.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import apply_trust_change

# Vocabulary: wire hooks to events
# Note: Dialog reactions are handled by infrastructure/dialog_reactions.py
# Note: Gossip reactions are handled by infrastructure/gossip_reactions.py
# Service NPCs must have appropriate reaction configurations
vocabulary: Dict[str, Any] = {
    "events": []
}

# Service keywords
HEAL_KEYWORDS = ["heal", "cure", "medicine", "treatment", "help"]


def on_service_request(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle service requests to NPCs.

    Different NPCs provide different services with trust gates.

    Args:
        entity: The NPC being asked
        accessor: StateAccessor instance
        context: Context with keyword

    Returns:
        EventResult with service response
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if not actor_id:
        return EventResult(allow=True, feedback=None)

    keyword = context.get("keyword", "").lower()

    # Elara - Healer
    if "elara" in actor_id.lower():
        if any(k in keyword for k in HEAL_KEYWORDS):
            return _handle_elara_healing(entity, accessor)

    return EventResult(allow=True, feedback=None)


def on_gossip_received(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Update NPC trust based on received gossip.

    Gossip about player actions affects NPC relationships.

    Args:
        entity: The NPC who received gossip
        accessor: StateAccessor instance
        context: Context with gossip content

    Returns:
        EventResult noting trust change
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    gossip_content = context.get("content", "").lower()

    if not actor_id:
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    npc = state.actors.get(actor_id)
    if not npc:
        return EventResult(allow=True, feedback=None)

    trust_change = 0
    message = None

    # Check gossip content for trust-affecting events
    if "sira" in gossip_content and "died" in gossip_content:
        if "elara" in actor_id.lower():
            # Sira's death affects Elara (healer_elara or npc_healer_elara)
            if state.extra.get("player_confessed_sira"):
                trust_change = -1  # Confessed first
                message = "Elara nods grimly. 'At least you told me yourself.'"
            else:
                trust_change = -2  # Gossip arrived first
                message = "'You were there when she died? And you didn't tell me?'"

    if "abandoned" in gossip_content:
        trust_change = -2
        message = f"The news reaches {entity.name if hasattr(entity, 'name') else 'them'}. Trust is lost."

    if trust_change != 0:
        # Initialize trust_state if missing
        if "trust_state" not in npc.properties:
            npc.properties["trust_state"] = {"current": 0}

        # Apply unified trust change
        apply_trust_change(
            entity=npc,
            delta=trust_change,
        )

    if message:
        return EventResult(allow=True, feedback=message)

    return EventResult(allow=True, feedback=None)


def on_confession(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle player confessing before gossip arrives.

    Confessing reduces trust penalty from gossip.

    Args:
        entity: The NPC being confessed to
        accessor: StateAccessor instance
        context: Context with keyword

    Returns:
        EventResult with confession response
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    keyword = context.get("keyword", "").lower()

    confession_keywords = ["confess", "admit", "tell you", "must know", "truth"]
    if not any(k in keyword for k in confession_keywords):
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state

    # Check for Sira confession to Elara
    if "elara" in (actor_id or "").lower():
        if state.extra.get("sira_died_with_player"):
            state.extra["player_confessed_sira"] = True

            # Apply reduced penalty
            elara = state.actors.get("npc_healer_elara")
            if elara:
                # Initialize trust_state if missing
                if "trust_state" not in elara.properties:
                    elara.properties["trust_state"] = {"current": 0}

                apply_trust_change(entity=elara, delta=-1)  # Reduced from -2

            return EventResult(
                allow=True,
                feedback=(
                    "Elara's face falls as you tell her about Sira. "
                    "'Thank you for telling me yourself. That takes courage.' "
                    "Her voice is heavy with grief, but not anger."
                ),
            )

    return EventResult(allow=True, feedback=None)


def _handle_elara_healing(entity: Any, accessor: Any) -> EventResult:
    """Handle Elara's healing service."""
    state = accessor.game_state
    elara = entity

    trust_state = elara.properties.get("trust_state", {"current": 0})
    trust = trust_state.get("current", 0)

    if trust < -2:
        return EventResult(
            allow=True,
            feedback=(
                "Elara turns away. 'I can't help someone I don't trust. "
                "Perhaps you should think about the choices that brought you here.'"
            ),
        )

    # Healing available
    player = state.actors.get("player")
    if player:
        # Clear negative conditions
        conditions = player.properties.get("conditions", [])
        healable = ["bleeding", "fungal_infection", "poison"]
        healed = []
        remaining = []

        for cond in conditions:
            if cond.get("type") in healable:
                healed.append(cond.get("type"))
            else:
                remaining.append(cond)

        player.properties["conditions"] = remaining

        if healed:
            return EventResult(
                allow=True,
                feedback=(
                    f"Elara tends to your wounds with practiced care. "
                    f"'{', '.join(healed)}' - treated successfully."
                ),
            )

    return EventResult(
        allow=True,
        feedback="Elara examines you. 'You seem well. Come back if you need healing.'",
    )


