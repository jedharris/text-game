"""UC3: Hungry Wolf Pack - Custom behaviors for feeding, morale, and domestication.

These behaviors demonstrate how game-specific code integrates with library modules.
They are NOT part of the library - they are custom behaviors for the test game.

Custom behaviors needed for UC3:
1. check_feeding - Check if item satisfies actor needs, update disposition
2. directed_flee - Override random flee to use flee_destination property
3. on_feed_wolf - Handle giving food to wolf, build gratitude relationship

Library modules used:
- packs.py: sync_pack_disposition, get_alpha, is_alpha
- morale.py: get_morale, check_flee_condition, attempt_flee
- relationships.py: modify_relationship, check_threshold
"""

from typing import Optional, List


def get_satisfiable_needs(item, actor) -> List[str]:
    """
    Get list of actor needs that an item can satisfy.

    Args:
        item: The Item object with satisfies property
        actor: The Actor with needs property

    Returns:
        List of need names that match between item.satisfies and actor.needs
    """
    if not item or not actor:
        return []

    item_satisfies = item.properties.get("satisfies", [])
    actor_needs = actor.properties.get("needs", [])

    return [need for need in item_satisfies if need in actor_needs]


def apply_feeding(accessor, item, actor) -> Optional[str]:
    """
    Apply feeding effect when giving food to an actor.

    If item satisfies any of actor's needs:
    1. Mark need as satisfied (remove from needs list)
    2. If actor is pack alpha, change disposition to neutral
    3. Sync pack disposition
    4. Consume item if consumable
    5. Build gratitude relationship with player

    Args:
        accessor: StateAccessor for state queries
        item: The Item being given
        actor: The Actor receiving the item

    Returns:
        Message describing what happened, or None if no feeding effect
    """
    from behaviors.actors.packs import sync_pack_disposition, is_alpha
    from behaviors.actors.relationships import modify_relationship

    satisfiable = get_satisfiable_needs(item, actor)
    if not satisfiable:
        return None

    messages = []

    # Mark needs as satisfied
    for need in satisfiable:
        if need in actor.properties.get("needs", []):
            actor.properties["needs"].remove(need)
            messages.append(f"{actor.name} devours the {item.name}, satisfying its {need}.")

    # If alpha, change disposition to neutral and sync pack
    if is_alpha(actor):
        old_disposition = actor.properties.get("disposition")
        if old_disposition == "hostile":
            actor.properties["disposition"] = "neutral"
            messages.append(f"{actor.name} relaxes, no longer hostile.")

            # Sync pack
            pack_id = actor.properties.get("pack_id")
            if pack_id:
                changed = sync_pack_disposition(accessor, pack_id)
                if changed:
                    messages.append("The pack follows the alpha's lead and calms down.")

    # Build gratitude relationship with player
    result = modify_relationship(accessor, actor, "player", "gratitude", 1)
    if result.threshold_crossed == "domestication":
        messages.append(f"{actor.name} has become domesticated!")
        actor.properties["disposition"] = "friendly"

    # Consume item if consumable
    if item.properties.get("consumable", False):
        # Remove from location or inventory
        for actor_id, other in accessor.game_state.actors.items():
            if item.id in other.inventory:
                other.inventory.remove(item.id)
                break

    return "\n".join(messages) if messages else None


def directed_flee(accessor, actor) -> Optional[str]:
    """
    Flee to a specific destination instead of random exit.

    If actor has flee_destination property, move there directly.
    Otherwise falls back to random flee behavior.

    Args:
        accessor: StateAccessor for state queries
        actor: The Actor attempting to flee

    Returns:
        Message describing what happened
    """
    from behaviors.actors.morale import check_flee_condition

    if not check_flee_condition(accessor, actor):
        return None

    flee_dest = actor.properties.get("flee_destination")
    if flee_dest:
        # Direct flee to specified destination
        old_location = actor.location
        actor.location = flee_dest
        return f"{actor.name} flees to safety!"

    # Fall back to library's random flee
    from behaviors.actors.morale import attempt_flee
    result = attempt_flee(accessor, actor, force_success=True)
    return result.message


def update_morale_on_damage(accessor, actor, damage: int) -> Optional[str]:
    """
    Check morale after actor takes damage.

    If morale drops below flee_threshold, attempt directed flee.

    Args:
        accessor: StateAccessor for state queries
        actor: The Actor that took damage
        damage: Amount of damage taken

    Returns:
        Message if fled, None otherwise
    """
    from behaviors.actors.morale import check_flee_condition

    if check_flee_condition(accessor, actor):
        return directed_flee(accessor, actor)

    return None


def check_domestication(actor, target_id: str = "player") -> bool:
    """
    Check if actor is domesticated toward target.

    Domestication occurs when gratitude >= 3.

    Args:
        actor: The Actor to check
        target_id: ID of the target (default: player)

    Returns:
        True if domesticated, False otherwise
    """
    from behaviors.actors.relationships import check_threshold

    return check_threshold(actor, target_id, "gratitude", 3)


def on_give_food(entity, accessor, context) -> Optional:
    """
    Handle giving food item to an actor.

    Called when player gives an item to an NPC. If the item satisfies
    actor needs, applies feeding behavior.

    Args:
        entity: The Actor receiving the item
        accessor: StateAccessor for state queries
        context: Context dict with item_id

    Returns:
        EventResult if feeding occurred, None otherwise
    """
    from src.state_accessor import EventResult

    item_id = context.get("item_id")
    if not item_id:
        return None

    item = accessor.get_item(item_id)
    if not item:
        return None

    # Check if item can satisfy any needs
    satisfiable = get_satisfiable_needs(item, entity)
    if not satisfiable:
        return None

    # Apply feeding
    message = apply_feeding(accessor, item, entity)
    if message:
        return EventResult(allow=True, message=message)

    return None


# Vocabulary extension for UC3-specific events
vocabulary = {
    "events": [
        {
            "event": "on_give_food",
            "description": "Handle giving food to satisfy actor needs (UC3 custom behavior)"
        }
    ]
}
