"""Old Swimmer Jek - Swimming Lessons for Sunken District.

Jek teaches basic swimming skill for 5 gold OR a food item.
If Garrett is rescued, Jek teaches for free (favor fulfilled).
If Garrett died, Jek is bitter and refuses advanced lessons.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import get_current_turn

# Vocabulary: wire hooks to events
vocabulary: Dict[str, Any] = {
    "events": []
}

# Dialog keywords
SWIMMING_KEYWORDS = ["swimming", "swim", "lesson", "teach", "learn", "water"]
PRICE_KEYWORDS = ["price", "cost", "gold", "pay", "payment", "afford"]
FAVOR_KEYWORDS = ["favor", "free", "garrett", "apprentice", "deal"]
FINGERS_KEYWORDS = ["fingers", "webbed", "hands", "birth", "defect", "legendary"]

# Teaching cost
GOLD_COST = 5


def on_jek_dialog(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle dialog with Old Swimmer Jek.

    Args:
        entity: Jek NPC
        accessor: StateAccessor instance
        context: Context with keyword

    Returns:
        EventResult with dialog response
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "old_swimmer_jek":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    extra = state.extra
    keyword = context.get("keyword", "").lower()

    # Check Garrett's fate for bitter response
    garrett_died = extra.get("garrett_died", False)
    garrett_rescued = extra.get("garrett_rescued", False)

    # If Garrett died, Jek is bitter
    if garrett_died and not extra.get("jek_confronted_about_garrett"):
        extra["jek_confronted_about_garrett"] = True
        return EventResult(
            allow=True,
            feedback=(
                "Jek's weathered face hardens as he sees you. "
                "'You were there? You SPOKE to him? And you... left?' "
                "His voice cracks like old rope. 'Garrett was my apprentice. "
                "The best swimmer I ever trained. And now he's gone.' "
                "He turns away. 'I'll still teach you the basics. For gold. "
                "But the advanced techniques died with him.'"
            ),
        )

    # Check for webbed fingers/appearance keywords
    if any(kw in keyword for kw in FINGERS_KEYWORDS):
        return _handle_fingers_dialog(entity, accessor)

    # Check for favor keywords (Garrett connection)
    if any(kw in keyword for kw in FAVOR_KEYWORDS):
        return _handle_favor_dialog(entity, accessor, garrett_rescued, garrett_died)

    # Check for price keywords
    if any(kw in keyword for kw in PRICE_KEYWORDS):
        return _handle_price_dialog(entity, accessor, garrett_rescued)

    # Check for swimming keywords (main topic)
    if any(kw in keyword for kw in SWIMMING_KEYWORDS):
        return _handle_swimming_dialog(entity, accessor)

    # Default response
    return EventResult(
        allow=True,
        feedback=(
            "Old Swimmer Jek watches you with clouded eyes that still see clearly. "
            "'The water calls to everyone eventually. What brings you to me?'"
        ),
    )


def _handle_fingers_dialog(entity: Any, accessor: Any) -> EventResult:
    """Handle dialog about Jek's webbed fingers."""
    return EventResult(
        allow=True,
        feedback=(
            "Jek spreads his hands, revealing the webbing between his fingers - "
            "translucent membranes connecting each digit. 'Born this way,' he says. "
            "'Others called it a curse. I called it a gift.' He flexes them, "
            "the webbing catching the light. 'I could outswim anyone before I could walk. "
            "Made me legendary in these waters.' A hint of pride touches his weathered face. "
            "'Now I'm too old for the deep places, but I can still teach what I know.'"
        ),
    )


def _handle_favor_dialog(
    entity: Any, accessor: Any, garrett_rescued: bool, garrett_died: bool
) -> EventResult:
    """Handle dialog about the favor (Garrett connection)."""
    if garrett_died:
        return EventResult(
            allow=True,
            feedback=(
                "Jek's jaw tightens. 'There is no favor anymore. Garrett was the favor. "
                "He was going to teach the advanced techniques - the current-riding, "
                "the fish-dodging. Things I'm too old to demonstrate.' "
                "His voice drops to a whisper. 'That knowledge drowned with him.'"
            ),
        )

    if garrett_rescued:
        return EventResult(
            allow=True,
            feedback=(
                "Jek's clouded eyes brighten. 'You saved Garrett. My apprentice. "
                "My... he's like a son to me.' His weathered hand grips your arm. "
                "'The basic lessons are yours. No charge. You've earned that and more.' "
                "He pauses. 'When Garrett recovers, he can teach you the advanced techniques. "
                "Give him time - he's been through much.'"
            ),
        )

    # Garrett not yet encountered
    return EventResult(
        allow=True,
        feedback=(
            "Jek leans closer, his clouded eyes intense. 'Find Garrett. "
            "He was my apprentice - the best swimmer since me. He's trapped somewhere "
            "in the flooded district.' His webbed hand trembles. 'Bring him back alive, "
            "and I'll teach you everything I know. No gold. No food. Just his life.' "
            "He settles back. 'That's my favor.'"
        ),
    )


def _handle_price_dialog(entity: Any, accessor: Any, garrett_rescued: bool) -> EventResult:
    """Handle dialog about teaching price."""
    if garrett_rescued:
        return EventResult(
            allow=True,
            feedback=(
                "Jek waves his webbed hand dismissively. 'No price. Not for you. "
                "You brought Garrett back.' His voice softens. 'Just say the word "
                "and I'll teach you to swim. Consider it a gift.'"
            ),
        )

    return EventResult(
        allow=True,
        feedback=(
            f"Jek counts on his webbed fingers. 'Five gold for the basics. "
            "Or bring me something to eat - I'm not picky.' "
            "He gestures at the flooded areas. 'Swimming could save your life down there. "
            f"The price is fair.' He pauses. 'Or... find my apprentice Garrett. "
            "Bring him back safe, and the lessons are free.'"
        ),
    )


def _handle_swimming_dialog(entity: Any, accessor: Any) -> EventResult:
    """Handle general swimming dialog."""
    state = accessor.game_state
    player = state.actors.get("player")

    # Check if player already knows basic swimming
    if player:
        skills = player.properties.get("skills", {})
        if skills.get("basic_swimming"):
            return EventResult(
                allow=True,
                feedback=(
                    "Jek nods approvingly. 'You already know the basics. "
                    "Your breathing is good, your form is passable.' "
                    "He gestures toward the deeper waters. 'For the advanced techniques - "
                    "reading currents, avoiding predators - you'll need Garrett. "
                    "If he's recovered, he can teach you what I no longer can.'"
                ),
            )

    return EventResult(
        allow=True,
        feedback=(
            "Jek's clouded eyes seem to look through you. 'The water isn't your enemy. "
            "It's your element - if you learn its ways.' He demonstrates with his hands, "
            "mimicking swimming motions. 'I can teach you to hold your breath longer, "
            "move through the water without fighting it. The basics.' "
            "He holds up five webbed fingers. 'Five gold. Or food. Or... a favor.'"
        ),
    )


def on_jek_teach(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle the actual teaching service.

    Called when player explicitly requests to learn swimming.
    Checks payment (gold, food, or favor) and grants skill.

    Args:
        entity: Jek NPC
        accessor: StateAccessor instance
        context: Context with service request

    Returns:
        EventResult with teaching result
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "old_swimmer_jek":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    extra = state.extra
    player = state.actors.get("player")

    if not player:
        return EventResult(allow=True, feedback=None)

    # Check if player already has skill
    skills = player.properties.get("skills", {})
    if skills.get("basic_swimming"):
        return EventResult(
            allow=True,
            feedback="Jek shakes his head. 'You already know what I can teach you.'",
        )

    garrett_rescued = extra.get("garrett_rescued", False)
    garrett_died = extra.get("garrett_died", False)

    # Check payment method
    payment_method = None
    payment_item = None

    # Method 1: Garrett rescued = free
    if garrett_rescued:
        payment_method = "favor"

    # Method 2: Gold payment
    if not payment_method:
        player_gold = player.properties.get("gold", 0)
        if player_gold >= GOLD_COST:
            payment_method = "gold"

    # Method 3: Food item payment
    if not payment_method:
        for item_id in player.inventory:
            item = state.get_item(item_id)
            if item and item.properties.get("food"):
                payment_method = "food"
                payment_item = item
                break

    # No payment available
    if not payment_method:
        return EventResult(
            allow=True,
            feedback=(
                f"Jek spreads his webbed hands. 'I'd teach you, but I need something in return. "
                f"Five gold, or food, or...' He trails off. 'Find Garrett. "
                "That's the other way.'"
            ),
        )

    # Process payment
    if payment_method == "gold":
        player.properties["gold"] = player.properties.get("gold", 0) - GOLD_COST
    elif payment_method == "food":
        # Remove food item from inventory
        if payment_item:
            player.inventory.remove(payment_item.id)
            payment_item.location = "consumed"

    # Grant skill
    if "skills" not in player.properties:
        player.properties["skills"] = {}
    player.properties["skills"]["basic_swimming"] = {
        "learned_from": "old_swimmer_jek",
        "learned_turn": get_current_turn(state),
        "breath_bonus": 5,  # Extends breath from base 10 to 15
    }

    extra["jek_taught_swimming"] = True

    # Response varies by payment method
    if payment_method == "favor":
        return EventResult(
            allow=True,
            feedback=(
                "Jek guides you to the water's edge. 'For Garrett's life, I give you this.' "
                "For the next hour, he teaches you the rhythm of breathing, the art of "
                "floating, the kick that propels without exhausting. 'The water is your friend now,' "
                "he says at last. 'You can hold your breath longer, move without panic. "
                "The deep places are open to you.' He clasps your shoulder with his webbed hand. "
                "'Thank you. For bringing him back.'"
            ),
        )
    elif payment_method == "gold":
        return EventResult(
            allow=True,
            feedback=(
                f"Jek accepts the {GOLD_COST} gold, tucking it away. 'Fair exchange.' "
                "He leads you to the water's edge and spends the next hour teaching you "
                "the fundamentals - how to breathe, how to float, how to move through water "
                "without fighting it. 'Your breath will hold longer now,' he says at last. "
                "'The flooded passages are less deadly to you. But be careful still - "
                "the fish don't care how well you swim.'"
            ),
        )
    else:  # food
        food_name = payment_item.name if payment_item else "food"
        return EventResult(
            allow=True,
            feedback=(
                f"Jek's eyes light up at the {food_name}. 'A fair trade.' "
                "He eats quickly, then leads you to the water's edge. For the next hour, "
                "he teaches you the swimmer's art - breathing deep, floating easy, "
                "moving with the current instead of against it. "
                "'You'll live longer in the water now,' he says. 'Your breath holds better, "
                "your movements waste less air. The basics are yours.'"
            ),
        )
