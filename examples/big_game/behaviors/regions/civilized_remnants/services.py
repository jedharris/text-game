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
TRADE_KEYWORDS = ["buy", "sell", "trade", "herbs", "potion", "supplies", "purchase"]
HERBALISM_KEYWORDS = ["herbalism", "teach", "training", "learn", "plants", "lesson"]


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

    # Elara - Healer and Confession
    if "elara" in actor_id.lower():
        # Check for Aldric topic
        if "aldric" in keyword:
            return _handle_elara_aldric_topic(entity, accessor)

        # Check for herbalism teaching
        if any(k in keyword for k in HERBALISM_KEYWORDS):
            return _handle_elara_herbalism_teaching(entity, accessor)

        # Check for confession first
        confession_keywords = ["confess", "admit", "tell you", "must know", "truth"]
        if any(k in keyword for k in confession_keywords):
            return on_confession(entity, accessor, context)

        if any(k in keyword for k in HEAL_KEYWORDS):
            return _handle_elara_healing(entity, accessor)

    # Maren - Herbalist/Trader
    if "maren" in actor_id.lower():
        if any(k in keyword for k in TRADE_KEYWORDS):
            return _handle_maren_trading(entity, accessor, context)

    return EventResult(allow=True, feedback=None)


def handle_gossip_for_services(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Update NPC trust based on received gossip.

    Gossip about player actions affects NPC relationships.
    Called by gossip_reactions infrastructure, not directly by behavior_manager.

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
            elara = state.actors.get("healer_elara")
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


def _handle_elara_aldric_topic(entity: Any, accessor: Any) -> EventResult:
    """Handle Elara's dialog about Aldric.

    If Aldric was rescued, grants a one-time trust bonus.
    """
    state = accessor.game_state
    elara = entity

    # Check if Aldric was saved
    aldric_saved = state.extra.get("aldric_saved", False)

    if not aldric_saved:
        return EventResult(
            allow=True,
            feedback=(
                "Elara's expression softens. 'Aldric? He's a scholar who was studying "
                "in the Fungal Depths. I worry about him... the spores down there are dangerous.'"
            ),
        )

    # Aldric was saved - check if bonus already applied
    bonus_applied = state.extra.get("elara_aldric_bonus_applied", False)

    if bonus_applied:
        return EventResult(
            allow=True,
            feedback=(
                "Elara smiles warmly. 'I'm still so grateful you helped Aldric. "
                "He's recovering well thanks to you.'"
            ),
        )

    # Apply trust bonus (one-time)
    if "trust_state" not in elara.properties:
        elara.properties["trust_state"] = {"current": 0}

    apply_trust_change(entity=elara, delta=1)
    state.extra["elara_aldric_bonus_applied"] = True

    return EventResult(
        allow=True,
        feedback=(
            "Elara's eyes light up. 'You saved Aldric! He told me what you did - "
            "braving those spore-filled tunnels to bring him back. I won't forget this.' "
            "Her demeanor warms noticeably toward you."
        ),
    )


def _handle_elara_herbalism_teaching(entity: Any, accessor: Any) -> EventResult:
    """Handle Elara's herbalism teaching service.

    Basic herbalism requires trust >= 2.
    Advanced herbalism requires trust >= 3 AND basic_herbalism skill.
    """
    state = accessor.game_state
    elara = entity
    player = state.actors.get("player")

    if not player:
        return EventResult(allow=True, feedback=None)

    # Get trust level
    trust_state = elara.properties.get("trust_state", {"current": 0})
    trust = trust_state.get("current", 0)

    # Get player skills
    skills = player.properties.get("skills", [])
    if skills is None:
        skills = []

    has_basic = "basic_herbalism" in skills
    has_advanced = "advanced_herbalism" in skills

    # Already has advanced - nothing more to teach
    if has_advanced:
        return EventResult(
            allow=True,
            feedback=(
                "Elara smiles proudly. 'You've already mastered everything I can teach you. "
                "Now it's about practice and experience - and perhaps finding rare specimens "
                "in the deeper wilds.'"
            ),
        )

    # Has basic, check if can learn advanced
    if has_basic:
        if trust < 3:
            return EventResult(
                allow=True,
                feedback=(
                    "Elara nods approvingly. 'You've learned the basics well. "
                    "Advanced techniques require deeper trust between us. "
                    "Continue helping the community, and perhaps...'"
                ),
            )

        # Can learn advanced
        if "skills" not in player.properties:
            player.properties["skills"] = []
        player.properties["skills"].append("advanced_herbalism")

        return EventResult(
            allow=True,
            feedback=(
                "Elara takes you deeper into her garden. 'Now for the advanced techniques - "
                "identifying rare specimens, proper extraction methods, creating compounds.' "
                "She spends hours teaching you the subtle arts of herbalism. "
                "'You have a gift for this,' she says finally. 'Use it wisely.'"
            ),
        )

    # No skills yet - check trust for basic
    if trust < 2:
        return EventResult(
            allow=True,
            feedback=(
                "Elara considers your request carefully. 'Teaching herbalism takes time "
                "and trust. Help me, help the community, and we can discuss lessons later.' "
                "She gestures to the various tasks around the sanctuary."
            ),
        )

    # Can learn basic
    if "skills" not in player.properties:
        player.properties["skills"] = []
    player.properties["skills"].append("basic_herbalism")

    return EventResult(
        allow=True,
        feedback=(
            "Elara nods slowly. 'Very well. I'll teach you the fundamentals.' "
            "She leads you through her herb garden, naming each plant. "
            "'This is silvermoss - excellent for wounds. And here, moonpetal - "
            "calms the nerves.' By the end, you've learned to identify and "
            "harvest the basic medicinal plants."
        ),
    )


def _handle_maren_trading(entity: Any, accessor: Any, context: dict[str, Any]) -> EventResult:
    """Handle Maren's trading service.

    Maren sells healing items with trust-based pricing.
    """
    state = accessor.game_state
    maren = entity
    player = state.actors.get("player")

    if not player:
        return EventResult(allow=True, feedback=None)

    trust_state = maren.properties.get("trust_state", {"current": 0})
    trust = trust_state.get("current", 0)

    # Base prices
    ITEMS_FOR_SALE = {
        "silvermoss": {"price": 50, "description": "potent healing moss"},
        "healing_herbs": {"price": 30, "description": "basic medicinal herbs"},
        "warm_cloak": {"price": 100, "description": "thick wool cloak"},
    }

    keyword = context.get("keyword", "").lower()

    # Check if player is asking about a specific item
    requested_item = None
    for item_id in ITEMS_FOR_SALE.keys():
        if item_id.replace("_", " ") in keyword or item_id in keyword:
            requested_item = item_id
            break

    if not requested_item:
        # Show shop menu
        items_list = []
        for item_id, info in ITEMS_FOR_SALE.items():
            base_price = info["price"]
            discount = min(trust * 0.1, 0.3)  # Max 30% discount at trust 3+
            final_price = int(base_price * (1.0 - discount))
            items_list.append(f"{info['description']} ({final_price} gold)")

        feedback = "Maren shows you her wares:\n" + "\n".join(f"  - {item}" for item in items_list)
        if trust >= 1:
            feedback += f"\n\nMaren smiles. 'For a friend, I offer a {int(discount * 100)}% discount.'"

        return EventResult(allow=True, feedback=feedback)

    # Handle specific item purchase
    item_info = ITEMS_FOR_SALE[requested_item]
    base_price = item_info["price"]
    discount = min(trust * 0.1, 0.3)
    final_price = int(base_price * (1.0 - discount))

    # Check player gold
    player_gold = player.properties.get("gold", 0)

    if player_gold < final_price:
        return EventResult(
            allow=True,
            feedback=f"Maren shakes her head. 'That'll be {final_price} gold. You don't have enough.'"
        )

    # Complete purchase
    player.properties["gold"] = player_gold - final_price

    # Create item instance
    item_template = next((item for item in state.items if item.id == requested_item), None)
    if not item_template:
        return EventResult(
            allow=True,
            feedback=f"[ERROR: Item {requested_item} not found in game state]"
        )

    # Add to player inventory
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
        feedback=f"Maren hands you the {item_info['description']}. 'That'll be {final_price} gold.'"
    )


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
        conditions = player.properties.get("conditions", {})
        healable = ["bleeding", "fungal_infection", "poison"]
        healed = []
        remaining = {}

        for cond_name, cond_data in conditions.items():
            if cond_name in healable:
                healed.append(cond_name)
            else:
                remaining[cond_name] = cond_data

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


def on_garden_herb_take(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle taking herbs from Elara's garden.

    Requires appropriate herbalism skill to harvest safely.
    - healing_herbs: basic_herbalism
    - nightshade: advanced_herbalism
    - moonpetal: no skill required (for Bee Queen quest)

    Args:
        entity: The item being taken
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult allowing or blocking the take action
    """
    item_id = entity.id if hasattr(entity, "id") else None
    if not item_id:
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    player = state.actors.get("player")

    if not player:
        return EventResult(allow=True, feedback=None)

    # Get player skills
    skills = player.properties.get("skills", [])
    if skills is None:
        skills = []

    # Get required skill from item properties
    required_skill = entity.properties.get("requires_herbalism")

    if not required_skill:
        # No skill required
        return EventResult(allow=True, feedback=None)

    # Map skill level to skill name
    skill_map = {
        "basic": "basic_herbalism",
        "advanced": "advanced_herbalism"
    }
    required_skill_name = skill_map.get(required_skill, required_skill)

    # Check if player has the required skill
    has_skill = required_skill_name in skills

    # For advanced items, also accept if they have advanced (supersedes basic)
    if required_skill == "basic" and "advanced_herbalism" in skills:
        has_skill = True

    if not has_skill:
        item_name = entity.name if hasattr(entity, "name") else "this plant"

        if required_skill == "basic":
            return EventResult(
                allow=False,
                feedback=(
                    f"You reach for the {item_name}, but hesitate. Without proper training, "
                    "you might damage the plant or take the wrong parts. "
                    "Perhaps Elara could teach you herbalism basics first."
                ),
            )
        elif required_skill == "advanced":
            return EventResult(
                allow=False,
                feedback=(
                    f"The {item_name} is clearly dangerous - you recognize the warning signs. "
                    "Handling it without advanced training could be fatal. "
                    "You'll need to master advanced herbalism before attempting this."
                ),
            )

    # Player has the required skill
    return EventResult(allow=True, feedback=None)


