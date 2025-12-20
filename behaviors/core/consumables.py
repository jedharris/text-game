"""Consumable items - drink and eat functionality.

Vocabulary, handlers and entity behaviors for consumable items like potions and food.
"""

from typing import Any, Dict, Optional, cast

from src.action_types import ActionDict
from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from src.types import ActorId
from utilities.utils import find_item_in_inventory
from utilities.handler_utils import get_display_name, validate_actor_and_location


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
    "adjectives": []
}


def _handle_consume(accessor, action, property_name: str, verb: str) -> HandlerResult:
    """
    Generic consumable handler for drinkable/edible items.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, actor_id
        property_name: Property to check ("drinkable" or "edible")
        verb: Verb for messages ("drink" or "eat")

    Returns:
        HandlerResult with success flag and message
    """
    # Validate actor (location not needed for inventory-based action)
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error
    assert actor_id is not None  # Guaranteed by validate_actor_and_location

    object_name = action.get("object")

    item = find_item_in_inventory(accessor, object_name, cast(ActorId, actor_id))
    if not item:
        return HandlerResult(
            success=False,
            primary=f"You're not carrying any {get_display_name(object_name)}."
        )

    # Check if item has the required property
    if not item.properties.get(property_name, False):
        return HandlerResult(
            success=False,
            primary=f"You can't {verb} the {item.name}."
        )

    # Invoke entity behaviors - behaviors decide what happens
    result = accessor.update(item, {}, verb=verb, actor_id=actor_id)

    if not result.success:
        return HandlerResult(
            success=False,
            primary=result.detail or f"You can't {verb} the {item.name}."
        )

    # Build primary - include behavior message if present
    base_message = f"You {verb} the {item.name}."
    if result.detail:
        return HandlerResult(success=True, primary=f"{base_message} {result.detail}")

    return HandlerResult(success=True, primary=base_message)


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
    return _handle_consume(accessor, action, "drinkable", "drink")


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
    return _handle_consume(accessor, action, "edible", "eat")


def on_drink(entity: Any, state: Any, context: Dict) -> Optional[EventResult]:
    """
    Handle drink event for drinkable items.

    Heals the player and removes the item from inventory.
    Returns None for non-drinkable entities.

    Args:
        entity: The entity being drunk
        state: GameState object
        context: Context dict with location, verb

    Returns:
        EventResult if entity is drinkable, None otherwise
    """
    # Check if entity is drinkable
    if not entity.properties.get("drinkable", False):
        return None

    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback="No player found.")

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
        feedback="You drink the glowing red potion. Warmth spreads through your body as your wounds heal."
    )


def on_eat(entity: Any, state: Any, context: Dict) -> Optional[EventResult]:
    """
    Handle eat event for food items.

    Removes the food from inventory and provides a satisfying message.
    Returns None for non-food entities.

    Args:
        entity: The entity being eaten
        state: GameState object
        context: Context dict with location, verb

    Returns:
        EventResult if entity is edible, None otherwise
    """
    # Check if entity is edible
    if not entity.properties.get("edible", False):
        return None

    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback="No player found.")

    # Remove from inventory
    if entity.id in player.inventory:
        player.inventory.remove(entity.id)

    # Mark as consumed
    entity.location = ""

    return EventResult(
        allow=True,
        feedback="You eat the food. It's delicious and satisfying."
    )
