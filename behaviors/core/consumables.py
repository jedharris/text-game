"""Consumable items - drink and eat functionality.

Vocabulary, handlers and entity behaviors for consumable items like potions and food.
"""

from typing import Any, Dict

from src.action_types import ActionDict
from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult, IGNORE_EVENT
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

    item = find_item_in_inventory(accessor, object_name, actor_id)
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


def on_drink(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Handle drink event for drinkable items.

    Applies effects (healing, buffs, etc.) and removes the item from inventory.
    Returns structured data for narrator composition.
    Returns IGNORE_EVENT for non-drinkable entities.

    Following narration architecture:
    - Behavior manages state (applies effects, removes item)
    - Returns structured data for narrator
    - Item definitions provide narrative descriptions via traits

    Args:
        entity: The entity being drunk
        accessor: StateAccessor instance
        context: Context dict with location, verb

    Returns:
        EventResult if entity is drinkable, IGNORE_EVENT otherwise
    """
    from utilities.entity_serializer import serialize_for_handler_result

    # Check if entity is drinkable
    if not entity.properties.get("drinkable", False):
        return IGNORE_EVENT

    actor_id = context.get("actor_id", "player")
    player = accessor.get_actor(actor_id)
    if not player:
        return EventResult(allow=True, feedback="No player found.")

    # Remove from inventory
    if entity.id in player.inventory:
        player.inventory.remove(entity.id)

    # Mark as consumed
    accessor.set_entity_where(entity.id, "__consumed_by_player__")

    # Apply effects
    effects = entity.properties.get("effects", {})
    effects_applied = {}

    if "heal" in effects:
        heal_amount = effects["heal"]
        current_health = player.stats.get("health", 100)
        max_health = player.stats.get("max_health", 100)
        new_health = min(current_health + heal_amount, max_health)
        player.stats["health"] = new_health
        effects_applied["heal"] = heal_amount

    # Return structured data for narrator
    return EventResult(
        allow=True,
        feedback="",  # No pre-composed prose
        data={
            "consumable": serialize_for_handler_result(entity, accessor, actor_id),
            "action": "drink",
            "effects_applied": effects_applied
        }
    )


def on_eat(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Handle eat event for food items.

    Removes the food from inventory and applies any effects.
    Returns structured data for narrator composition.
    Returns IGNORE_EVENT for non-food entities.

    Following narration architecture:
    - Behavior manages state (removes item, applies effects)
    - Returns structured data for narrator
    - Item definitions provide narrative descriptions via traits

    Args:
        entity: The entity being eaten
        accessor: StateAccessor instance
        context: Context dict with location, verb

    Returns:
        EventResult if entity is edible, IGNORE_EVENT otherwise
    """
    from utilities.entity_serializer import serialize_for_handler_result

    # Check if entity is edible
    if not entity.properties.get("edible", False):
        return IGNORE_EVENT

    actor_id = context.get("actor_id", "player")
    player = accessor.get_actor(actor_id)
    if not player:
        return EventResult(allow=True, feedback="No player found.")

    # Remove from inventory
    if entity.id in player.inventory:
        player.inventory.remove(entity.id)

    # Mark as consumed
    accessor.set_entity_where(entity.id, "__consumed_by_player__")

    # Apply effects if any
    effects = entity.properties.get("effects", {})
    effects_applied = {}

    if "heal" in effects:
        heal_amount = effects["heal"]
        current_health = player.stats.get("health", 100)
        max_health = player.stats.get("max_health", 100)
        new_health = min(current_health + heal_amount, max_health)
        player.stats["health"] = new_health
        effects_applied["heal"] = heal_amount

    # Return structured data for narrator
    return EventResult(
        allow=True,
        feedback="",  # No pre-composed prose
        data={
            "consumable": serialize_for_handler_result(entity, accessor, actor_id),
            "action": "eat",
            "effects_applied": effects_applied
        }
    )
