"""Curiosity Dealer Vex - Rare item trader and information broker.

Vex buys unusual items at high prices and sells rare equipment.
Also sells valuable information for gold (trust-gated).
"""

from typing import Any, Dict

from src.behavior_manager import EventResult

# Vocabulary: wire hooks to events
vocabulary: Dict[str, Any] = {
    "events": []
}


def on_vex_dialog(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle dialog with Vex for trading and information.

    Args:
        entity: Vex NPC
        accessor: StateAccessor instance
        context: Context with keyword

    Returns:
        EventResult with trading/info response
    """
    state = accessor.game_state
    vex = entity
    player = state.actors.get("player")

    if not player:
        return EventResult(allow=True, feedback=None)

    trust_state = vex.properties.get("trust_state", {"current": 0})
    trust = trust_state.get("current", 0)

    keyword = context.get("keyword", "").lower()

    # Trade keywords
    if any(word in keyword for word in ["trade", "buy", "sell", "rare", "unusual"]):
        return _handle_vex_trading(vex, accessor, context)

    # Information broker keywords
    if any(word in keyword for word in ["information", "secrets", "gossip", "news", "know"]):
        return _handle_vex_information(vex, accessor, trust)

    # Curiosities keywords
    if any(word in keyword for word in ["curious", "strange", "artifact", "mystery"]):
        return EventResult(
            allow=True,
            feedback=(
                "Vex's eyes gleam with interest. 'I collect the strange and unusual. "
                "If you find anything... peculiar, bring it to me. I pay well.'"
            )
        )

    # Default response based on trust
    if trust < 1:
        return EventResult(
            allow=True,
            feedback="Vex regards you with guarded suspicion. 'Looking for something specific?'"
        )
    else:
        return EventResult(
            allow=True,
            feedback=(
                "Vex nods in recognition. 'Good to see you again. "
                "I have rare items for sale, and I always buy curiosities.'"
            )
        )


def on_vex_gift(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle gifts to Vex (curiosities increase trust).

    Args:
        entity: Vex NPC
        accessor: StateAccessor instance
        context: Context with item

    Returns:
        EventResult with gift response
    """
    from src.infrastructure_utils import apply_trust_change

    state = accessor.game_state
    vex = entity
    item_context = context.get("item")

    if not item_context:
        return EventResult(allow=True, feedback=None)

    item_id = item_context.id if hasattr(item_context, "id") else str(item_context)

    # Curiosities that Vex values
    CURIOSITIES = {
        "strange_artifact": {"trust": 2, "response": "Fascinating! I've never seen anything like this."},
        "mysterious_object": {"trust": 1, "response": "Intriguing. I'll study this carefully."},
        "ancient_tool": {"trust": 1, "response": "Pre-Collapse technology! Excellent find."},
    }

    curiosity = CURIOSITIES.get(item_id)

    if curiosity:
        # Apply trust change
        apply_trust_change(entity=vex, delta=curiosity["trust"])

        # Remove item from player
        player = state.actors.get("player")
        if player and item_id in player.inventory:
            from src.types import ItemId
            player.inventory.remove(ItemId(item_id))

        # Update item location
        for item in state.items:
            if item.id == item_id:
                item.location = "curiosity_dealer_vex"
                break

        return EventResult(
            allow=True,
            feedback=f"Vex examines the {item_id.replace('_', ' ')} with intense interest. '{curiosity['response']}'"
        )

    return EventResult(
        allow=True,
        feedback="Vex glances at it. 'Not what I'm looking for. I deal in curiosities, not common goods.'"
    )


def _handle_vex_trading(vex: Any, accessor: Any, context: dict[str, Any]) -> EventResult:
    """Handle Vex's rare item trading."""
    state = accessor.game_state
    player = state.actors.get("player")

    if not player:
        return EventResult(allow=True, feedback=None)

    trust_state = vex.properties.get("trust_state", {"current": 0})
    trust = trust_state.get("current", 0)

    # Items Vex sells (trust-gated)
    ITEMS_FOR_SALE = {
        "command_orb": {"price": 200, "trust_required": 2, "description": "ancient command orb"},
        "ancient_tools": {"price": 150, "trust_required": 1, "description": "pre-collapse tools"},
    }

    keyword = context.get("keyword", "").lower()

    # Check for specific item request
    requested_item = None
    for item_id in ITEMS_FOR_SALE.keys():
        if item_id.replace("_", " ") in keyword or item_id in keyword:
            requested_item = item_id
            break

    if not requested_item:
        # Show shop menu
        items_list = []
        for item_id, info in ITEMS_FOR_SALE.items():
            if trust >= info["trust_required"]:
                items_list.append(f"{info['description']} ({info['price']} gold)")
            else:
                items_list.append(f"[LOCKED - Requires more trust]")

        feedback = "Vex gestures to a locked cabinet:\n" + "\n".join(f"  - {item}" for item in items_list)

        if trust < 2:
            feedback += "\n\nVex watches you carefully. 'Some items are only for trusted clients.'"

        return EventResult(allow=True, feedback=feedback)

    # Handle specific purchase
    item_info = ITEMS_FOR_SALE.get(requested_item)

    if not item_info:
        return EventResult(
            allow=True,
            feedback="Vex shakes his head. 'I don't have that in stock.'"
        )

    # Check trust gate
    if trust < item_info["trust_required"]:
        return EventResult(
            allow=True,
            feedback=f"Vex's eyes narrow. 'That item is not for sale to just anyone. Earn my trust first.'"
        )

    # Check player gold
    player_gold = player.properties.get("gold", 0)
    price = item_info["price"]

    if player_gold < price:
        return EventResult(
            allow=True,
            feedback=f"Vex names his price: {price} gold. You don't have enough."
        )

    # Complete purchase
    player.properties["gold"] = player_gold - price

    # Add item to player inventory
    from src.types import ItemId
    if ItemId(requested_item) not in player.inventory:
        player.inventory.append(ItemId(requested_item))

    # Update item location
    for item in state.items:
        if item.id == requested_item:
            item.location = "player"
            break

    return EventResult(
        allow=True,
        feedback=f"Vex carefully hands you the {item_info['description']}. '{price} gold. Handle it carefully.'"
    )


def _handle_vex_information(vex: Any, accessor: Any, trust: int) -> EventResult:
    """Handle Vex's information broker service."""
    state = accessor.game_state
    player = state.actors.get("player")

    if not player:
        return EventResult(allow=True, feedback=None)

    # Information requires trust
    if trust < 2:
        return EventResult(
            allow=True,
            feedback="Vex smiles thinly. 'Information is valuable. Come back when we're better acquainted.'"
        )

    # Information costs gold
    INFO_PRICE = 100
    player_gold = player.properties.get("gold", 0)

    # Check available secrets (based on game flags)
    secrets_available = []

    if not state.extra.get("vex_info_golem_weakness"):
        secrets_available.append("golem_weakness")

    if not state.extra.get("vex_info_spore_mother"):
        secrets_available.append("spore_mother_location")

    if not state.extra.get("vex_info_frozen_shortcut"):
        secrets_available.append("frozen_reaches_shortcut")

    if not secrets_available:
        return EventResult(
            allow=True,
            feedback="Vex shrugs. 'I have nothing new for you at the moment. Check back later.'"
        )

    if player_gold < INFO_PRICE:
        return EventResult(
            allow=True,
            feedback=f"Vex leans in. 'Information costs {INFO_PRICE} gold. You lack the funds.'"
        )

    # Sell first available secret
    secret = secrets_available[0]

    player.properties["gold"] = player_gold - INFO_PRICE
    state.extra[f"vex_info_{secret}"] = True

    # Add knowledge to player
    if "knowledge" not in player.properties:
        player.properties["knowledge"] = []

    player.properties["knowledge"].append(secret)

    SECRET_MESSAGES = {
        "golem_weakness": "The stone golems in the frozen reaches... they're vulnerable to thermal shock. Hit them with extreme temperature changes.",
        "spore_mother_location": "The spore mother in the fungal depths can be... reasoned with. Bring her something alive, she craves it.",
        "frozen_reaches_shortcut": "There's a hidden passage in the ice caves that bypasses the golem chamber. Look for the false wall near the frozen waterfall.",
    }

    return EventResult(
        allow=True,
        feedback=f"Vex leans in conspiratorially. '{SECRET_MESSAGES[secret]}' ({INFO_PRICE} gold)"
    )
