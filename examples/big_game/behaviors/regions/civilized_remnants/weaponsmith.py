"""Weaponsmith Toran barter and dialog for Civilized Remnants.

Toran trades equipment for raw materials the player brings from the wilds.
No currency system — pure barter using existing portable items.
"""

from typing import Any, Dict, List, Optional, Tuple

from src.behavior_manager import EventResult


vocabulary: Dict[str, Any] = {
    "events": []
}


# Barter trades: (payment_item_id, reward_item_id, reward_name, toran_dialog)
TRADES: List[Tuple[str, str, str, str]] = [
    (
        "spider_silk",
        "silk_armor",
        "silk armor",
        "Toran examines the spider silk with professional respect. "
        "'Fine material. Strong as steel, light as cloth.' He works quickly, "
        "and hands you armor woven from the silk.",
    ),
    (
        "venom_sac",
        "venom_blade",
        "venom blade",
        "Toran handles the venom sac carefully. 'Dangerous stuff. But coat a "
        "blade right and it hits twice as hard.' He coats a dagger with the "
        "venom and hands it back, gleaming and deadly.",
    ),
    (
        "crystal_lens",
        "crystal_shield",
        "crystal shield",
        "Toran turns the crystal lens in his hands, watching light refract "
        "through it. 'Unusual material. But I can work with unusual.' He "
        "mounts it in a frame and hands you a shield that gleams with "
        "refracted light.",
    ),
]

# Items Toran creates (must also be added to game_state.json items list)
TRADE_ITEM_IDS = [t[1] for t in TRADES]


def on_toran_dialog(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle all dialog with Weaponsmith Toran.

    Args:
        entity: Toran actor
        accessor: StateAccessor instance
        context: Context with keyword

    Returns:
        EventResult with dialog response
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "weaponsmith_toran":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    keyword = context.get("keyword", "").lower()

    if keyword in ("trade", "buy", "sell", "equipment", "weapons", "armor", "forge"):
        return _handle_trade_topic(player, state)
    elif keyword in ("repair", "fix", "mend"):
        return _handle_repair_topic()
    elif keyword in ("town", "council", "news"):
        return _handle_town_topic()
    else:
        # Check if player has any tradeable items — mention it
        tradeable = _find_tradeable_item(player)
        if tradeable:
            payment_id, _, reward_name, _ = tradeable
            item = state.get_item(payment_id)
            item_name = item.name if item else payment_id
            return EventResult(
                allow=True,
                feedback=(
                    f"Toran eyes the {item_name} you're carrying. "
                    f"'That's good material. I could make you {reward_name} "
                    f"from that. Ask me about a trade if you're interested.'"
                ),
            )
        return EventResult(
            allow=True,
            feedback=(
                "Toran looks up from his anvil. 'Need something forged? "
                "Bring me materials from the wilds — spider silk, venom, "
                "good crystal — and I'll make something worth carrying.'"
            ),
        )


def _handle_trade_topic(player: Any, state: Any) -> EventResult:
    """Handle trade request — find tradeable item and execute."""
    tradeable = _find_tradeable_item(player)

    if not tradeable:
        return EventResult(
            allow=True,
            feedback=(
                "Toran shakes his head. 'Got nothing I can work with there. "
                "Bring me spider silk, venom sac, or a crystal lens — "
                "raw materials from the wilds. Then we'll talk.'"
            ),
        )

    payment_id, reward_id, reward_name, dialog = tradeable

    # Check if reward item already exists and has been given before
    if reward_id in player.inventory:
        return EventResult(
            allow=True,
            feedback=(
                f"Toran nods at the {reward_name} you already carry. "
                "'Already made you one of those. Anything else?'"
            ),
        )

    # Execute the trade
    # Remove payment from inventory
    if payment_id in player.inventory:
        player.inventory.remove(payment_id)

    # Create reward — set location to player and add to inventory
    reward_item = state.get_item(reward_id)
    if reward_item:
        player.inventory.append(reward_id)
    else:
        # Item doesn't exist in game state — just add to inventory
        player.inventory.append(reward_id)

    state.extra[f"toran_traded_{reward_id}"] = True

    return EventResult(allow=True, feedback=dialog)


def _handle_repair_topic() -> EventResult:
    """Handle repair request."""
    return EventResult(
        allow=True,
        feedback=(
            "Toran looks over his tools. 'Bring me what needs fixing. "
            "I can mend most things, given time and materials. Nothing fancy — "
            "but it'll hold.'"
        ),
    )


def _handle_town_topic() -> EventResult:
    """Handle town gossip."""
    return EventResult(
        allow=True,
        feedback=(
            "Toran grunts. 'Council argues while the walls need reinforcing. "
            "Asha wants to help everyone. Hurst wants to lock the gates. "
            "Varn just wants his cut. Same as always.' He hammers a nail "
            "with unnecessary force."
        ),
    )


def _find_tradeable_item(
    player: Any,
) -> Optional[Tuple[str, str, str, str]]:
    """Find the first tradeable item in player inventory."""
    for trade in TRADES:
        payment_id = trade[0]
        if payment_id in player.inventory:
            return trade
    return None
