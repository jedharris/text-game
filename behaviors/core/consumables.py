"""Consumable items - drink and eat functionality.

Vocabulary, handlers and entity behaviors for consumable items like potions and food.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_item_in_inventory


# Vocabulary extension - adds eat and drink verbs
vocabulary = {
    "verbs": [
        {
            "word": "eat",
            "event": "on_eat",
            "synonyms": ["consume", "devour", "munch"],
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
            "event": "on_drink",
            "synonyms": ["quaff", "sip", "gulp"],
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


def handle_drink(accessor, action):
    """
    Handle drink command.

    Allows an actor to drink an item from their inventory.
    Entity behaviors (on_drink) determine what happens.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, actor_id

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to drink?"
        )

    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    item = find_item_in_inventory(accessor, object_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            message=f"You're not carrying any {object_name}."
        )

    # Check if item is drinkable
    if not item.properties.get("drinkable", False):
        return HandlerResult(
            success=False,
            message=f"You can't drink the {item.name}."
        )

    # Invoke entity behaviors (on_drink) - behaviors decide what happens
    result = accessor.update(item, {}, verb="drink", actor_id=actor_id)

    if not result.success:
        return HandlerResult(
            success=False,
            message=result.message or f"You can't drink the {item.name}."
        )

    # Build message - include behavior message if present
    base_message = f"You drink the {item.name}."
    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}")

    return HandlerResult(success=True, message=base_message)


def handle_eat(accessor, action):
    """
    Handle eat command.

    Allows an actor to eat an item from their inventory.
    Entity behaviors (on_eat) determine what happens.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, actor_id

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

    if not object_name:
        return HandlerResult(
            success=False,
            message="What do you want to eat?"
        )

    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    item = find_item_in_inventory(accessor, object_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            message=f"You're not carrying any {object_name}."
        )

    # Check if item is edible
    if not item.properties.get("edible", False):
        return HandlerResult(
            success=False,
            message=f"You can't eat the {item.name}."
        )

    # Invoke entity behaviors (on_eat) - behaviors decide what happens
    result = accessor.update(item, {}, verb="eat", actor_id=actor_id)

    if not result.success:
        return HandlerResult(
            success=False,
            message=result.message or f"You can't eat the {item.name}."
        )

    # Build message - include behavior message if present
    base_message = f"You eat the {item.name}."
    if result.message:
        return HandlerResult(success=True, message=f"{base_message} {result.message}")

    return HandlerResult(success=True, message=base_message)


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
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=False, message="No player found.")

    # Remove from inventory
    if entity.id in player.inventory:
        player.inventory.remove(entity.id)

    # Mark as consumed (empty location)
    entity.location = ""

    # Heal player
    current_health = player.stats.get("health", 100)
    max_health = player.stats.get("max_health", 100)
    heal_amount = 20

    new_health = min(current_health + heal_amount, max_health)
    player.stats["health"] = new_health

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
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=False, message="No player found.")

    # Remove from inventory
    if entity.id in player.inventory:
        player.inventory.remove(entity.id)

    # Mark as consumed
    entity.location = ""

    return EventResult(
        allow=True,
        message="You eat the food. It's delicious and satisfying."
    )
