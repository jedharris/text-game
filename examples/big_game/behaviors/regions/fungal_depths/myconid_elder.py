"""Myconid Elder dialog and services for Fungal Depths.

Handles dialog topics and barter-based services:
- Cure infection in exchange for ice_crystal or gold_nugget
- Teach spore resistance at trust >= 2
- Information about Spore Mother, ice crystals, etc.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import transition_state


vocabulary: Dict[str, Any] = {
    "events": []
}


# Payment items the Elder accepts for curing infection
# frost_lily (frozen reaches), warm_coal (hot springs), spring_water (hot springs)
CURE_PAYMENT_ITEMS = ["frost_lily", "warm_coal", "spring_water"]


def on_elder_dialog(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle all dialog with Myconid Elder.

    Routes by keyword to appropriate topic handler.

    Args:
        entity: The Myconid Elder actor
        accessor: StateAccessor instance
        context: Context with keyword (topic)

    Returns:
        EventResult with dialog response
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "npc_myconid_elder":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    keyword = context.get("keyword", "").lower()

    # Check elder's current state
    elder = state.actors.get("npc_myconid_elder")
    if not elder:
        return EventResult(allow=True, feedback=None)

    sm = elder.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "neutral"))

    # Route by keyword
    if keyword in ("cure", "infection", "heal", "sickness", "fungal"):
        return _handle_cure_topic(entity, accessor, context, current_state)
    elif keyword in ("resistance", "spores", "protect", "immunity"):
        return _handle_resistance_topic(entity, accessor, context, current_state)
    elif keyword in ("spore mother", "mother", "heart", "great one"):
        return _handle_spore_mother_topic(state)
    elif keyword in ("cold", "ice", "crystal", "frozen"):
        return _handle_ice_topic()
    elif keyword in ("hello", "greetings", "speak", "talk"):
        return _handle_greeting()
    else:
        return EventResult(
            allow=True,
            feedback=(
                "The Elder's spores drift in muted colors. The meaning is unclear — "
                "perhaps try asking about something specific."
            ),
        )


def _handle_greeting() -> EventResult:
    """Initial greeting."""
    return EventResult(
        allow=True,
        feedback=(
            "A cloud of blue spores drifts from the Elder's cap. Somehow, you "
            "understand: 'Soft-flesh comes to the Still Place. Why?'"
        ),
    )


def _handle_cure_topic(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
    current_state: str,
) -> EventResult:
    """Handle cure infection request.

    If player has a payment item and is infected, cure them.
    Otherwise, explain what's needed.
    """
    state = accessor.game_state
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    # Check if player has infection
    conditions = player.properties.get("conditions", {})
    has_infection = "fungal_infection" in conditions

    # Check for payment item
    payment_item = None
    payment_item_name = None
    for item_id in player.inventory:
        if item_id in CURE_PAYMENT_ITEMS:
            item = state.get_item(item_id)
            payment_item = item_id
            payment_item_name = item.name if item else item_id
            break

    if not has_infection:
        return EventResult(
            allow=True,
            feedback=(
                "Green spores pulse gently. 'The rot-within is not upon you, "
                "soft-flesh. You are clean. But if the spores take hold... "
                "bring frost-flower or warm-stone, and I will cleanse you.'"
            ),
        )

    if not payment_item:
        return EventResult(
            allow=True,
            feedback=(
                "Green spores pulse with concern. 'The rot-within grows in you. "
                "I can cleanse it — but the cleansing costs. Bring frost-flower "
                "from the frozen heights, or warm-stone from the hot waters. "
                "An exchange.'"
            ),
        )

    # Cure the infection — remove condition and consume payment
    from behavior_libraries.actor_lib.conditions import remove_condition
    remove_condition(player, "fungal_infection", accessor)

    # Remove payment item from inventory
    if payment_item in player.inventory:
        player.inventory.remove(payment_item)

    state.extra["elder_cured_player"] = True

    return EventResult(
        allow=True,
        feedback=(
            f"The Elder takes the {payment_item_name} reverently. Green and gold "
            "spores swirl around you in a dense cloud. You feel the infection "
            "receding — the burning in your lungs fades, the dark veins on your "
            "skin lighten and disappear. 'The rot-within is cleansed. Walk "
            "carefully among the spores, soft-flesh.'"
        ),
    )


def _handle_resistance_topic(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
    current_state: str,
) -> EventResult:
    """Handle spore resistance teaching.

    Requires trust >= 2 with the Elder.
    """
    state = accessor.game_state
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    elder = state.actors.get("npc_myconid_elder")
    if not elder:
        return EventResult(allow=True, feedback=None)

    trust = elder.properties.get("trust_state", {}).get("current", 0)

    # Already learned
    if player.properties.get("skills", {}).get("spore_resistance"):
        return EventResult(
            allow=True,
            feedback=(
                "Warm amber spores drift lazily. 'You already breathe with the "
                "spores, soft-flesh. The teaching lives in you.'"
            ),
        )

    # Need more trust
    if trust < 2:
        return EventResult(
            allow=True,
            feedback=(
                "Purple spores swirl thoughtfully. 'To walk among spores without "
                "harm... this can be taught. But teaching requires trust. Trust "
                "requires time.' The Elder's meaning is clear — you must earn "
                "more goodwill before this knowledge is shared."
            ),
        )

    # Grant resistance
    if "skills" not in player.properties:
        player.properties["skills"] = {}
    player.properties["skills"]["spore_resistance"] = True
    state.extra["learned_spore_resistance"] = True

    return EventResult(
        allow=True,
        feedback=(
            "The Elder's cap opens wide, releasing a dense cloud of shimmering "
            "purple spores. They settle on your skin, into your lungs — but "
            "instead of burning, they feel cool, almost pleasant. 'Breathe with "
            "them, not against them,' the Elder communicates. 'The spores will "
            "know you now. You are part of the network.' You feel a subtle "
            "change — the constant itch of spore exposure fades to nothing."
        ),
    )


def _handle_spore_mother_topic(state: Any) -> EventResult:
    """Information about the Spore Mother."""
    state.extra["knows_spore_mother_sick"] = True
    return EventResult(
        allow=True,
        feedback=(
            "The spores turn a deep, sorrowful amber. 'The Mother suffers. The "
            "corruption spreads from her wound. If she falls... we all fall. "
            "Heartmoss from the deep roots — only this can heal her. But the "
            "deep roots are dangerous, and the heartmoss rare.'"
        ),
    )


def _handle_ice_topic() -> EventResult:
    """Information about cold items for curing."""
    return EventResult(
        allow=True,
        feedback=(
            "Silver spores glitter. 'Cold things cool the cure-making. Without "
            "cold, the cleansing burns too fierce. The frost-flower from the "
            "frozen heights, or warm-stone from the hot waters — these carry "
            "the balance we need.'"
        ),
    )
