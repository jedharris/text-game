"""UC8: Broken Statue - Custom behaviors for construct repair and guard mechanics.

These behaviors demonstrate how game-specific code integrates with library modules.
They are NOT part of the library - they are custom behaviors for the test game.

Custom behaviors needed for UC8:
1. repair_handler - Restore health with repairs items matching body.form
2. functional_threshold - Set functional:true when health >= 80
3. guard_duty - Attack hostile actors entering guarded location

Library modules used:
- combat.py: get_attacks, execute_attack
- conditions.py: has_condition, apply_condition
"""

from typing import Optional, List


def can_repair(item, target) -> bool:
    """
    Check if item can repair target.

    Args:
        item: The repair Item
        target: The target Actor

    Returns:
        True if item can repair target
    """
    if not item or not target:
        return False

    repairs = item.properties.get("repairs", [])
    if not repairs:
        return False

    body = target.properties.get("body", {})
    form = body.get("form")

    return form in repairs


def get_repair_amount(item) -> int:
    """
    Get repair amount from item.

    Args:
        item: The repair Item

    Returns:
        Amount of health restored
    """
    if not item:
        return 0

    return item.properties.get("repair_amount", 10)


def apply_repair(accessor, item, target) -> str:
    """
    Apply repair to target.

    Args:
        accessor: StateAccessor for state queries
        item: The repair Item
        target: The target Actor

    Returns:
        Message describing the repair result
    """
    if not can_repair(item, target):
        body = target.properties.get("body", {}) if target else {}
        form = body.get("form", "unknown")
        return f"The {item.name if item else 'item'} can't repair {form}s."

    repair_amount = get_repair_amount(item)
    current_health = target.properties.get("health", 0)
    max_health = target.properties.get("max_health", 100)

    new_health = min(max_health, current_health + repair_amount)
    target.properties["health"] = new_health

    # Check functional threshold
    was_functional = target.properties.get("functional", False)
    now_functional = check_functional_threshold(target)

    messages = [f"You repair the {target.name}. Health restored to {new_health}/{max_health}."]

    if now_functional and not was_functional:
        messages.append(f"The {target.name} whirs to life!")

    return " ".join(messages)


def get_functional_threshold(actor) -> int:
    """
    Get the health threshold for becoming functional.

    Args:
        actor: The Actor

    Returns:
        Health threshold (default 80)
    """
    return actor.properties.get("functional_threshold", 80) if actor else 80


def check_functional_threshold(actor) -> bool:
    """
    Check if actor meets functional threshold and update functional status.

    Args:
        actor: The Actor to check

    Returns:
        True if now functional
    """
    if not actor:
        return False

    health = actor.properties.get("health", 0)
    threshold = get_functional_threshold(actor)

    if health >= threshold:
        actor.properties["functional"] = True
        return True
    else:
        actor.properties["functional"] = False
        return False


def is_functional(actor) -> bool:
    """
    Check if actor is functional.

    Args:
        actor: The Actor

    Returns:
        True if functional
    """
    if not actor:
        return False

    return actor.properties.get("functional", False)


def get_guarded_location(actor) -> Optional[str]:
    """
    Get the location this actor guards.

    Args:
        actor: The Actor

    Returns:
        Location ID if guarding, None otherwise
    """
    if not actor:
        return None

    return actor.properties.get("guarding")


def is_guarding(actor, location_id: str) -> bool:
    """
    Check if actor is guarding a specific location.

    Args:
        actor: The Actor
        location_id: The location to check

    Returns:
        True if guarding this location
    """
    guarded = get_guarded_location(actor)
    return guarded == location_id


def get_hostiles_in_location(accessor, guard, location_id: str) -> List:
    """
    Get hostile actors in a location.

    Args:
        accessor: StateAccessor for state queries
        guard: The guarding Actor
        location_id: Location to check

    Returns:
        List of hostile Actors
    """
    hostiles = []

    for actor_id, actor in accessor.game_state.actors.items():
        if actor_id == guard.id:
            continue

        if actor.location != location_id:
            continue

        # Check if hostile to guard
        disposition = actor.properties.get("disposition")
        if disposition == "hostile":
            hostiles.append(actor)

    return hostiles


def perform_guard_attack(accessor, guard, target) -> str:
    """
    Guard attacks a hostile target.

    Args:
        accessor: StateAccessor for state queries
        guard: The guarding Actor
        target: The target Actor

    Returns:
        Message describing the attack
    """
    from behaviors.actors.combat import get_attacks, execute_attack

    attacks = get_attacks(guard)
    if not attacks:
        return f"The {guard.name} has no attacks available."

    # Use first available attack
    attack = attacks[0]
    result = execute_attack(accessor, guard, target, attack)

    return result.message if result else f"The {guard.name} attacks {target.name}!"


def on_guard_duty(accessor, guard) -> List[str]:
    """
    Perform guard duty actions.

    Called during NPC action phase.

    Args:
        accessor: StateAccessor for state queries
        guard: The guarding Actor

    Returns:
        List of action messages
    """
    messages = []

    if not is_functional(guard):
        return messages

    guarded_location = get_guarded_location(guard)
    if not guarded_location:
        return messages

    hostiles = get_hostiles_in_location(accessor, guard, guarded_location)

    for hostile in hostiles:
        msg = perform_guard_attack(accessor, guard, hostile)
        messages.append(msg)

    return messages


def on_use_repair_item(entity, accessor, context) -> Optional:
    """
    Handle using repair item on construct.

    Args:
        entity: The Actor using the item
        accessor: StateAccessor for state queries
        context: Context with item_id and target_id

    Returns:
        EventResult with repair message
    """
    from src.state_accessor import EventResult

    item_id = context.get("item_id")
    target_id = context.get("target_id")

    if not item_id:
        return None

    item = accessor.get_item(item_id)
    if not item:
        return None

    # Check if item has repairs property
    if not item.properties.get("repairs"):
        return None

    target = accessor.get_actor(target_id) if target_id else None
    if not target:
        return EventResult(allow=False, message="Repair what?")

    if not can_repair(item, target):
        body = target.properties.get("body", {})
        form = body.get("form", "unknown")
        return EventResult(
            allow=False,
            message=f"The {item.name} can't repair {form}s."
        )

    msg = apply_repair(accessor, item, target)

    # Consume item if single-use
    if item.properties.get("consumable", False):
        if item_id in entity.inventory:
            entity.inventory.remove(item_id)

    return EventResult(allow=True, message=msg)


# Vocabulary extension for UC8-specific events
vocabulary = {
    "events": [
        {
            "event": "on_use_repair_item",
            "description": "Handle using repair item on construct (UC8 custom behavior)"
        },
        {
            "event": "on_guard_duty",
            "description": "Perform guard duty actions (UC8 custom behavior)"
        }
    ]
}
