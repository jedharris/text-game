"""UC4: Healer and Garden - Custom behaviors for toxic plants and knowledge gates.

These behaviors demonstrate how game-specific code integrates with library modules.
They are NOT part of the library - they are custom behaviors for the test game.

Custom behaviors needed for UC4:
1. toxic_touch - Apply condition when touching toxic plant
2. knowledge_gate - Gate descriptions based on knows array
3. service_handlers - Helper functions for healer services

Library modules used:
- conditions.py: apply_condition, has_condition
- services.py: get_available_services, get_service_cost, execute_service
"""

from typing import Any, Optional


def check_toxic_touch(item, actor) -> bool:
    """
    Check if an item is toxic to touch.

    Args:
        item: The Item being touched/taken
        actor: The Actor touching the item

    Returns:
        True if item is toxic to touch, False otherwise
    """
    if not item:
        return False

    return item.properties.get("toxic_to_touch", False)


def apply_toxic_effect(item, actor) -> Optional[str]:
    """
    Apply toxic effect from touching a toxic item.

    Args:
        item: The toxic Item
        actor: The Actor being affected

    Returns:
        Message describing the effect, or None if item not toxic
    """
    from behaviors.actor_lib.conditions import apply_condition

    if not check_toxic_touch(item, actor):
        return None

    # Get condition data from item
    applies_condition = item.properties.get("applies_condition")
    if not applies_condition:
        return f"You feel a strange sensation from touching the {item.name}."

    condition_name = applies_condition.get("name", "poison")

    # Apply the condition
    msg = apply_condition(actor, condition_name, applies_condition)
    return f"The {item.name}'s toxic oils burn your skin! {msg}"


def has_knowledge(actor, knowledge: str) -> bool:
    """
    Check if actor has specific knowledge.

    Args:
        actor: The Actor to check
        knowledge: Name of the knowledge (e.g., "herbalism")

    Returns:
        True if actor has the knowledge, False otherwise
    """
    if not actor:
        return False

    knows = actor.properties.get("knows", [])
    return knowledge in knows


def get_knowledge_description(item, actor) -> str:
    """
    Get item description based on actor's knowledge.

    If actor has herbalism knowledge and item has description_with_herbalism,
    return that. Otherwise return normal description.

    Args:
        item: The Item to describe
        actor: The Actor viewing the item

    Returns:
        Appropriate description string
    """
    if not item:
        return ""

    # Check for knowledge-gated description (stored in properties)
    if has_knowledge(actor, "herbalism"):
        herbalism_desc = item.properties.get("description_with_herbalism")
        if herbalism_desc:
            return herbalism_desc

    return item.description


def grant_knowledge(actor, knowledge: str) -> str:
    """
    Grant knowledge to an actor.

    Args:
        actor: The Actor receiving knowledge
        knowledge: Name of the knowledge to grant

    Returns:
        Message describing what was learned
    """
    if not actor:
        return "No one to teach."

    knows = actor.properties.setdefault("knows", [])
    if knowledge in knows:
        return f"You already know {knowledge}."

    knows.append(knowledge)
    return f"You have learned {knowledge}!"


def on_take_toxic(entity, accessor, context) -> Optional[Any]:
    """
    Handle taking a toxic item.

    Called when an actor takes an item. If the item is toxic to touch,
    applies the toxic effect.

    Args:
        entity: The Actor taking the item (typically player)
        accessor: StateAccessor for state queries
        context: Context dict with item_id

    Returns:
        EventResult with toxic effect message, or None if not toxic
    """
    from src.state_accessor import EventResult

    item_id = context.get("item_id")
    if not item_id:
        return None

    item = accessor.get_item(item_id)
    if not item:
        return None

    if not check_toxic_touch(item, entity):
        return None

    message = apply_toxic_effect(item, entity)
    if message:
        # Still allow taking the item, but with consequences
        return EventResult(allow=True, feedback=message)

    return None


def on_examine_with_knowledge(entity, accessor, context) -> Optional[Any]:
    """
    Handle examining an item with knowledge-gated description.

    Called when an actor examines an item. Returns enhanced description
    if actor has relevant knowledge.

    Args:
        entity: The Actor examining (typically player)
        accessor: StateAccessor for state queries
        context: Context dict with item_id

    Returns:
        EventResult with knowledge description, or None if no special description
    """
    from src.state_accessor import EventResult

    item_id = context.get("item_id")
    if not item_id:
        return None

    item = accessor.get_item(item_id)
    if not item:
        return None

    # Check if item has herbalism description and player knows herbalism
    if has_knowledge(entity, "herbalism"):
        herbalism_desc = item.properties.get("description_with_herbalism")
        if herbalism_desc:
            return EventResult(allow=True, feedback=herbalism_desc)

    return None


def get_service_with_discount(npc, service_name: str, customer) -> dict:
    """
    Get service info including effective cost with trust discount.

    Args:
        npc: The NPC offering the service
        customer: The customer Actor

    Returns:
        Dict with service info and effective cost
    """
    from behaviors.actor_lib.services import get_available_services, get_service_cost

    services = get_available_services(npc)
    service = services.get(service_name, {})

    if not service:
        return {}

    effective_cost = get_service_cost(npc, service_name, customer)
    base_cost = service.get("amount_required", 0)

    return {
        "service": service,
        "base_cost": base_cost,
        "effective_cost": effective_cost,
        "has_discount": effective_cost < base_cost
    }


# Vocabulary extension for UC4-specific events
vocabulary = {
    "events": [
        {
            "event": "on_take_toxic",
            "description": "Handle taking toxic item (UC4 custom behavior)"
        },
        {
            "event": "on_examine_with_knowledge",
            "description": "Handle examining with knowledge gates (UC4 custom behavior)"
        }
    ]
}
