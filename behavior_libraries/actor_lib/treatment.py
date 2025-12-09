"""Treatment system for actor interaction.

Handles using items to treat/cure conditions on actors:
- Items with `cures` or `treats` property can treat matching conditions
- `treats` is an author-friendly alias for `cures`
- `cure_amount` controls severity reduction (default: full cure)
- Consumable items are removed after use

Item treatment properties:
{
    "cures": ["poison", "disease"],  # Conditions this item treats
    "treats": ["bleeding"],          # Alias for cures (author convenience)
    "cure_amount": 100,              # Severity reduction (default: full cure)
    "consumable": True               # Whether item is consumed on use
}

Usage:
    from behavior_libraries.actor_lib.treatment import (
        can_treat, get_treatable_conditions, apply_treatment,
        TreatmentResult
    )
"""

from dataclasses import dataclass
from typing import Any, List, Optional

from behavior_libraries.actor_lib.conditions import treat_condition


@dataclass
class TreatmentResult:
    """Result of applying treatment."""
    success: bool
    conditions_treated: List[str]
    item_consumed: bool
    message: str


def get_treatable_conditions(item) -> List[str]:
    """
    Get list of conditions this item can treat.

    Checks both `cures` and `treats` properties (treats is an alias for cures).

    Args:
        item: The Item object

    Returns:
        List of condition names, or empty list if item has no treatment properties
    """
    if not item:
        return []
    # Combine both cures and treats (treats is an alias)
    cures = item.properties.get("cures", [])
    treats = item.properties.get("treats", [])
    # Return combined list, avoiding duplicates
    return list(set(cures + treats))


def can_treat(item, condition_name: str) -> bool:
    """
    Check if an item can treat a specific condition.

    Args:
        item: The Item object
        condition_name: Name of the condition to check

    Returns:
        True if item can treat the condition
    """
    return condition_name in get_treatable_conditions(item)


def apply_treatment(
    accessor,
    item,
    target_actor,
    condition_name: Optional[str] = None
) -> TreatmentResult:
    """
    Use an item to treat conditions on an actor.

    If condition_name is provided, only that condition is treated.
    Otherwise, all matching conditions are treated.

    Args:
        accessor: StateAccessor for state queries
        item: The Item to use for treatment
        target_actor: The Actor to treat
        condition_name: Optional specific condition to treat

    Returns:
        TreatmentResult with outcome details
    """
    treatable = get_treatable_conditions(item)
    if not treatable:
        return TreatmentResult(
            success=False,
            conditions_treated=[],
            item_consumed=False,
            message=f"{item.name} cannot treat any conditions."
        )

    cure_amount = item.properties.get("cure_amount", 100)
    conditions_treated = []

    target_conditions = target_actor.properties.get("conditions", {})

    for cond_name in treatable:
        # Skip if we're treating a specific condition and this isn't it
        if condition_name and cond_name != condition_name:
            continue

        if cond_name in target_conditions:
            # Use the condition system's treat_condition function
            msg = treat_condition(target_actor, cond_name, cure_amount)
            conditions_treated.append(cond_name)

    if not conditions_treated:
        return TreatmentResult(
            success=False,
            conditions_treated=[],
            item_consumed=False,
            message=f"{target_actor.name} doesn't have any conditions {item.name} can treat."
        )

    # Consume item if consumable
    item_consumed = False
    if item.properties.get("consumable", False):
        item_consumed = True
        # Remove from actor's inventory if present
        if item.id in target_actor.inventory:
            target_actor.inventory.remove(item.id)
        # Check other actor inventories (like player giving to NPC)
        for actor_id, actor in accessor.game_state.actors.items():
            if item.id in actor.inventory:
                actor.inventory.remove(item.id)
                break

    treated_list = ", ".join(conditions_treated)
    return TreatmentResult(
        success=True,
        conditions_treated=conditions_treated,
        item_consumed=item_consumed,
        message=f"Treated {treated_list} on {target_actor.name}."
    )


def on_receive_treatment(entity, accessor, context) -> Optional[Any]:
    """
    Auto-apply treatment when receiving curative item.

    Called when an actor receives an item. If the item has cures
    matching any of the actor's conditions, automatically apply treatment.

    Args:
        entity: The Actor receiving the item
        accessor: StateAccessor for state queries
        context: Context dict with item_id

    Returns:
        EventResult with treatment message, or None if no treatment applied
    """
    from src.state_accessor import EventResult

    item_id = context.get("item_id")
    if not item_id:
        return None

    item = accessor.get_item(item_id)
    if not item:
        return None

    treatable = get_treatable_conditions(item)
    if not treatable:
        return None

    # Check if entity has any matching conditions
    conditions = entity.properties.get("conditions", {})
    matching = [c for c in treatable if c in conditions]

    if not matching:
        return None

    # Apply treatment
    result = apply_treatment(accessor, item, entity)
    if result.success:
        return EventResult(allow=True, message=result.message)

    return None


def on_use_treatment(entity, accessor, context) -> Optional[Any]:
    """
    Handle using a treatment item on a target actor.

    Called for "use X on Y" commands where X is a treatment item.
    Applies treatment from the item to the target.

    Args:
        entity: The Actor using the item (typically player)
        accessor: StateAccessor for state queries
        context: Context dict with:
            - item_id: str - the treatment item
            - target_id: str - the actor to treat

    Returns:
        EventResult with treatment message, or None if not applicable
    """
    from src.state_accessor import EventResult

    item_id = context.get("item_id")
    target_id = context.get("target_id")

    if not item_id or not target_id:
        return None

    item = accessor.get_item(item_id)
    if not item:
        return None

    # Check if item can treat anything
    treatable = get_treatable_conditions(item)
    if not treatable:
        return None

    target = accessor.get_actor(target_id)
    if not target:
        return None

    # Apply treatment
    result = apply_treatment(accessor, item, target)
    return EventResult(allow=result.success, message=result.message)


# Vocabulary extension - registers treatment events and verbs
vocabulary = {
    "events": [
        {
            "event": "on_receive_treatment",
            "description": "Called when an actor receives a curative item. "
                          "Auto-applies treatment if item cures matching conditions."
        },
        {
            "event": "on_use_treatment",
            "description": "Called for 'use X on Y' commands where X is a treatment item."
        }
    ],
    "verbs": [
        {
            "word": "treat",
            "event": "on_use_treatment",
            "synonyms": ["bandage", "heal"],
            "object_required": True,
            "indirect_object_required": True,
            "description": "Use a treatment item on a target (e.g., 'treat merchant with bandages')"
        }
    ]
}
