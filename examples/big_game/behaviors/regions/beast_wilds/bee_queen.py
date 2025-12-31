"""Bee Queen Trade Mechanics for Beast Wilds.

Implements the flower-for-honey trade with the Bee Queen.
No timer pressure - this is a peaceful cross-region collection.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import (
    apply_trust_change,
    transition_state,
)

# Vocabulary: wire hooks to events
# Note: Gift reactions (flower offers) are handled by infrastructure/gift_reactions.py
# Note: Take reactions are handled by infrastructure/take_reactions.py
# Bee Queen must have appropriate reaction configurations
vocabulary: Dict[str, Any] = {
    "events": [
        {
            "event": "on_receive_item",
            "hook": "entity_item_received",
            "description": "Handle flower offerings to Bee Queen"
        }
    ]
}

# Valid flower types and their sources
FLOWER_TYPES = {
    "moonpetal": "Civilized Remnants",
    "frost_lily": "Frozen Reaches",
    "water_bloom": "Sunken District",
}


def on_receive_item(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle offering flowers to the Bee Queen.

    Each flower type can be traded once for royal honey.
    Trading 3 types unlocks allied state.

    Args:
        entity: The bee queen receiving the item (when called via on_receive_item)
        accessor: StateAccessor instance
        context: Context with item, item_id, giver_id

    Returns:
        EventResult with trade result
    """
    # When called via on_receive_item, entity is the bee queen
    bee_queen = entity
    bee_queen_id = bee_queen.id if hasattr(bee_queen, "id") else str(bee_queen)

    # Check if this is the bee queen
    if bee_queen_id != "bee_queen":
        return EventResult(allow=True, feedback=None)

    # Check if item is a valid flower
    item = context.get("item")
    if not item:
        return EventResult(allow=True, feedback=None)

    item_id = item.id if hasattr(item, "id") else str(item)
    item_lower = item_id.lower()

    flower_type = None
    for flower in FLOWER_TYPES:
        if flower in item_lower:
            flower_type = flower
            break

    if not flower_type:
        # Not a valid flower - queen rejects
        return EventResult(
            allow=True,
            feedback=(
                "The Bee Queen examines the offering, antennae twitching. "
                "She backs away - this is not what she seeks."
            ),
        )

    state = accessor.game_state
    extra = state.extra

    # Track which flowers have been traded
    if "bee_queen_flowers_traded" not in extra:
        extra["bee_queen_flowers_traded"] = []

    traded = extra["bee_queen_flowers_traded"]

    # Check if this flower type already traded
    if flower_type in traded:
        return EventResult(
            allow=True,
            feedback=(
                f"The Bee Queen has already received a {flower_type}. "
                "She does not need another."
            ),
        )

    # Accept the flower
    traded.append(flower_type)

    # Give royal honey to player
    # (The actual item creation would be handled by the give system)
    extra["bee_queen_owes_honey"] = True
    extra["bee_queen_honey_count"] = extra.get("bee_queen_honey_count", 0) + 1

    # Update queen's state
    queen = state.actors.get("bee_queen")
    if queen:
        sm = queen.properties.get("state_machine")
        if sm:
            # Transition to trading if not already
            if sm.get("current", sm["initial"]) == "neutral":
                transition_state(sm, "trading")

            # Check for allied transition (3 unique flowers)
            if len(traded) >= 3:
                transition_state(sm, "allied")

        # Increase trust
        # Initialize trust_state if missing
        if "trust_state" not in queen.properties:
            queen.properties["trust_state"] = {"current": 0}

        apply_trust_change(entity=queen, delta=1)

    trade_count = len(traded)
    if trade_count >= 3:
        return EventResult(
            allow=True,
            feedback=(
                "The Bee Queen's wings fan in pleased recognition - this completes "
                "the exchange. She approaches, no longer a trader but an ally. "
                "The grove is now sanctuary."
            ),
        )

    remaining = 3 - trade_count
    return EventResult(
        allow=True,
        feedback=(
            f"The Bee Queen accepts the {flower_type}, antennae quivering with "
            f"appreciation. She moves toward the honey cache, offering a portion "
            f"in exchange. {remaining} more flower type(s) would complete the bond."
        ),
    )


def on_honey_theft(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle taking honey without permission.

    This makes the swarm hostile and destroys future trade.

    Args:
        entity: The item being taken (honey)
        accessor: StateAccessor instance
        context: Context with location

    Returns:
        EventResult with consequence
    """
    # Check if item is honey
    item_id = entity.id if hasattr(entity, "id") else str(entity)
    if "honey" not in item_id.lower():
        return EventResult(allow=True, feedback=None)

    # Check if in bee grove
    location = context.get("location")
    loc_id = location.id if location and hasattr(location, "id") else str(location) if location else ""
    if "beehive" not in loc_id.lower():
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state

    # Check if queen is allied (theft allowed when allied)
    queen = state.actors.get("bee_queen")
    if queen:
        sm = queen.properties.get("state_machine")
        if sm and sm.get("current") == "allied":
            return EventResult(allow=True, feedback=None)

        # Not allied - this is theft
        if sm:
            transition_state(sm, "hostile")

        # Permanent consequence
        state.extra["bee_grove_hostile"] = True
        state.extra["bee_trade_destroyed"] = True

    return EventResult(
        allow=True,
        feedback=(
            "The moment you touch the honey, the air erupts with furious buzzing. "
            "The Bee Queen's compound eyes fix on you with unmistakable hatred. "
            "The trade relationship is destroyed forever."
        ),
    )


def on_bee_queen_talk(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle talk/ask commands directed at the Bee Queen.

    The Bee Queen communicates through body language, not words.
    Her communication vocabulary (from design Section 1.5):
    - Antennae: twitching = interest, still = waiting, rapid = agitation
    - Wings: folded = calm, buzzing = warning, slow fan = pleased
    - Positioning: toward honey = offering trade, hovering over flowers = interested,
                   backing away = rejection, approaching = acceptance

    Args:
        entity: The Bee Queen actor
        accessor: StateAccessor instance
        context: Context with keyword (topic) if ask command

    Returns:
        EventResult with non-verbal communication description
    """
    state = accessor.game_state
    queen = state.actors.get("bee_queen")
    if not queen:
        return EventResult(allow=True, feedback=None)

    sm = queen.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "defensive"))

    # Check what flowers have been traded
    traded = state.extra.get("bee_queen_flowers_traded", [])
    trade_count = len(traded)

    # Generate non-verbal response based on current state
    if current_state == "hostile":
        feedback = (
            "The Bee Queen's wings blur with furious buzzing. Her antennae "
            "snap back and forth in rapid, aggressive patterns. The swarm "
            "around her thickens, a living wall of stingers. Her compound "
            "eyes track your every movement with cold hatred. There is "
            "no trade here, not anymore. Only threat."
        )
    elif current_state == "defensive":
        feedback = (
            "The Bee Queen regards you with still antennae, waiting. Her wings "
            "remain folded against her golden-furred body, but the swarm hovers "
            "close, watchful. She seems to be... expecting something. Her gaze "
            "drifts briefly toward the flowers blooming at the grove's edge, "
            "then back to you. An offering, perhaps? Something beautiful, "
            "something from far away?"
        )
    elif current_state == "neutral":
        feedback = (
            "The Bee Queen's antennae twitch with interest as you approach. "
            "Her wings give a slow, welcoming fan. She hovers near the honey "
            "cache, glancing between you and the golden combs. The message "
            "is clear enough: she has something you want. What can you bring "
            "her in return? Her gaze lingers on the colorful plants of the grove."
        )
    elif current_state == "trading":
        remaining = 3 - trade_count
        flower_hint = ""
        if "moonpetal" not in traded:
            flower_hint = "moonpetal"
        elif "frost_lily" not in traded:
            flower_hint = "frost lily"
        elif "water_bloom" not in traded:
            flower_hint = "water bloom"

        feedback = (
            f"The Bee Queen's antennae quiver with pleased recognition. Her wings "
            f"fan slowly, contentedly. She moves toward the honey cache, then back "
            f"toward you - the dance of trade, of fair exchange. {remaining} more "
            f"flower type(s) would complete the bond. "
        )
        if flower_hint:
            feedback += f"Perhaps a {flower_hint} would please her?"
    elif current_state == "allied":
        feedback = (
            "The Bee Queen approaches with a warm, slow buzz of recognition. "
            "Her antennae reach toward you in greeting, almost touching. "
            "The swarm parts to let you pass, no longer guards but escorts. "
            "She fans her wings in lazy contentment - the grove is yours "
            "as much as hers now. The honey cache stands open, freely given "
            "to a friend of the hive."
        )
    else:
        feedback = (
            "The Bee Queen's compound eyes fix on you. Her antennae wave "
            "in patterns you cannot quite read. She waits, patient and ancient."
        )

    return EventResult(allow=True, feedback=feedback)
