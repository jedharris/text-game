"""Equipment system behavior.

Handles equipping and unequipping wearable/equippable items via the use command.
Items with wearable or equippable properties can be used (with no target) to equip them.
Equipment is stored in player.properties["equipment"] as a slot-based dict.
"""

from typing import Any, Optional

from src.state_accessor import EventResult, StateAccessor

# Vocabulary: reuse the same hook as item_use_reactions
vocabulary = {
    "events": [
        {
            "event": "on_item_used",
            "hook": "entity_item_used",
            "description": "Handle equipping wearable/equippable items",
        },
    ]
}

# Slot inference from item id patterns
_SLOT_PATTERNS: dict[str, str] = {
    "mask": "face",
    "cloak": "body",
    "gear": "body",
    "armor": "body",
    "sword": "weapon",
    "wand": "weapon",
    "shield": "off_hand",
    "helmet": "head",
    "hat": "head",
}


def _infer_slot(item: Any) -> str:
    """Determine equipment slot from item properties or id patterns."""
    slot = item.properties.get("slot")
    if slot:
        return str(slot)

    # Check filters_toxic_air for face slot
    if item.properties.get("filters_toxic_air"):
        return "face"

    # Pattern match on item id
    item_id = item.id
    for pattern, slot_name in _SLOT_PATTERNS.items():
        if pattern in item_id:
            return slot_name

    return "body"


def on_item_used(
    entity: Any,
    accessor: StateAccessor,
    context: dict[str, Any],
) -> Optional[EventResult]:
    """Handle using a wearable/equippable item to equip it.

    Only triggers for self-use (no target) on items with wearable/equippable property.
    Returns None (via EventResult with no feedback) to let other handlers proceed
    if this item isn't wearable.
    """
    item = context.get("item", entity)
    target = context.get("target")

    # Only handle self-use (no target)
    if target is not None:
        return EventResult(allow=True, feedback=None)

    # Check if item is wearable or equippable
    wearable = item.properties.get("wearable", False)
    equippable = item.properties.get("equippable", False)

    if not wearable and not equippable:
        return EventResult(allow=True, feedback=None)

    # Determine slot
    slot = _infer_slot(item)

    # Get or create equipment dict
    actor_id = context.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)
    equipment: dict[str, str] = actor.properties.get("equipment", {})

    # Toggle: if already equipped in this slot, unequip
    if equipment.get(slot) == item.id:
        del equipment[slot]
        actor.properties["equipment"] = equipment
        return EventResult(
            allow=True,
            feedback=f"You remove the {item.name}."
        )

    # Equip (replace if something else in slot)
    old_item_id = equipment.get(slot)
    equipment[slot] = item.id
    actor.properties["equipment"] = equipment

    if old_item_id:
        old_item = accessor.get_item(old_item_id)
        old_name = old_item.name if old_item else old_item_id
        return EventResult(
            allow=True,
            feedback=f"You remove the {old_name} and put on the {item.name}."
        )

    return EventResult(
        allow=True,
        feedback=f"You put on the {item.name}."
    )
