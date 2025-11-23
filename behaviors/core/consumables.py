"""Consumable items - drink and eat functionality.

Vocabulary and entity behaviors for consumable items like potions and food.
These behaviors handle the effects of consuming items.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult


# Vocabulary extension - adds eat and drink verbs
vocabulary = {
    "verbs": [
        {
            "word": "eat",
            "synonyms": ["consume"],
            "object_required": True,
            "llm_context": {
                "traits": ["consumes food", "may restore health", "destroys item"],
                "failure_narration": {
                    "not_edible": "cannot eat that",
                    "not_hungry": "not hungry"
                }
            }
        },
        {
            "word": "drink",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["consumes liquid", "may have effects", "usually destroys item"],
                "failure_narration": {
                    "not_drinkable": "cannot drink that",
                    "empty": "nothing left to drink"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}


def on_drink_health_potion(entity: Any, state: Any, context: Dict) -> EventResult:
    """
    Health potion drinking behavior.

    Heals the player and removes the potion from inventory.

    Args:
        entity: The potion being drunk
        state: GameState object
        context: Context dict with location, verb

    Returns:
        EventResult with allow and message
    """
    # Remove from inventory
    if entity.id in state.player.inventory:
        state.player.inventory.remove(entity.id)

    # Mark as consumed (empty location)
    entity.location = ""

    # Heal player
    current_health = state.player.stats.get("health", 100)
    max_health = state.player.stats.get("max_health", 100)
    heal_amount = 20

    new_health = min(current_health + heal_amount, max_health)
    state.player.stats["health"] = new_health

    return EventResult(
        allow=True,
        message="You drink the glowing red potion. Warmth spreads through your body as your wounds heal."
    )


def on_eat_food(entity: Any, state: Any, context: Dict) -> EventResult:
    """
    Generic food eating behavior.

    Removes the food from inventory and provides a satisfying message.

    Args:
        entity: The food being eaten
        state: GameState object
        context: Context dict with location, verb

    Returns:
        EventResult with allow and message
    """
    # Remove from inventory
    if entity.id in state.player.inventory:
        state.player.inventory.remove(entity.id)

    # Mark as consumed
    entity.location = ""

    return EventResult(
        allow=True,
        message="You eat the food. It's delicious and satisfying."
    )
