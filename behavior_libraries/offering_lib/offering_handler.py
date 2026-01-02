"""Offering handler for altar/shrine interactions.

This module provides an "offer" verb for making offerings to altars, shrines, wells, etc.
The semantics differ from "put" - offerings are consumed/transformed, not just placed.

NOTE: This is a library behavior pattern that could be useful to migrate to core
if offering-based puzzles become a common pattern across many games.
"""

from typing import Dict, Any, cast

from src.action_types import ActionDict
from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from src.types import ActorId
from utilities.utils import find_item_in_inventory, find_accessible_item
from utilities.handler_utils import get_display_name


# Vocabulary extension - adds "offer" verb
vocabulary = {
    "verbs": [
        {
            "word": "offer",
            "event": "on_receive_offering",
            "synonyms": ["sacrifice", "give"],
            "object_required": True,
            "preposition": "to"
        }
    ],
    "nouns": [],
    "adjectives": []
}


def handle_offer(accessor, action: Dict) -> HandlerResult:
    """
    Handle the offer command (offer <item> to <target>).

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, target, actor_id

    Returns:
        HandlerResult with success flag and message

    Example:
        > offer flower to shrine
        > offer weapon to well
    """
    actor_id = cast(ActorId, action.get("actor_id") or ActorId("player"))
    item_name = action.get("object")
    target_name = action.get("indirect_object") or action.get("target")

    if not item_name:
        return HandlerResult(success=False, primary="Offer what?")

    if not target_name:
        return HandlerResult(
            success=False,
            primary=f"Offer the {get_display_name(item_name)} to what?"
        )

    # Find the item - must be in inventory or accessible
    item = find_item_in_inventory(accessor, item_name, actor_id)
    if not item:
        item = find_accessible_item(accessor, item_name, actor_id)

    if not item:
        return HandlerResult(
            success=False,
            primary=f"You don't have any {get_display_name(item_name)} to offer."
        )

    # Find the target (altar, shrine, well, etc.)
    target = find_accessible_item(accessor, target_name, actor_id)

    if not target:
        return HandlerResult(
            success=False,
            primary=f"You don't see any {get_display_name(target_name)} here."
        )

    # Check if target accepts offerings (has on_receive_offering behavior)
    # We'll invoke the entity behavior and let it decide
    context = {
        "actor_id": actor_id,
        "verb": "offer",
        "offered_item": item,
        "offered_item_id": item.id
    }

    result = accessor.update(target, {}, verb="receive_offering", actor_id=actor_id, **context)

    if not result.success:
        # Target doesn't accept offerings or rejected this one
        default_msg = f"The {target.name} does not respond to your offering."
        return HandlerResult(success=False, primary=result.detail or default_msg)

    # Offering accepted - remove item from game (consumed by offering)
    # The target's behavior may have already handled this, but we'll ensure it
    if hasattr(item, 'location'):
        # Mark as consumed using proper removal state
        accessor.set_entity_where(item.id, f"__consumed_by_{actor_id}__")

    # Build response message
    base_message = f"You offer the {item.name} to the {target.name}."
    if result.detail:
        message = f"{base_message}\n{result.detail}"
    else:
        message = base_message

    return HandlerResult(success=True, primary=message)


def on_receive_offering(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Default entity behavior for receiving offerings.

    This is a helper function that game-specific behaviors can use as a base.
    Most altars/shrines/wells will override this with their own logic.

    Args:
        entity: The altar/shrine/well receiving the offering
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb, offered_item, offered_item_id

    Returns:
        EventResult with allow and message

    Example usage in game-specific behavior:
        from behavior_libraries.offering_lib.offering_handler import on_receive_offering as base_receive

        def on_receive_offering(entity, accessor, context):
            # Custom logic here
            if context["offered_item"].name == "flower":
                # Apply blessing
                return EventResult(allow=True, feedback="The shrine glows warmly!")
            else:
                # Fall back to default rejection
                return EventResult(allow=False, feedback="The shrine rejects your offering.")
    """
    # Default: reject all offerings
    return EventResult(
        allow=False,
        feedback=f"The {entity.name} does not accept offerings."
    )
