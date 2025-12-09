"""Trading behavior for NPC item exchanges.

Handles NPCs receiving items and responding with trades or services.

Configuration in NPC properties:
{
    "trades": {
        "item_fd_silvermoss": {
            "gives": "item_cr_healing_herbs",
            "message": "'Silvermoss! Here, take these healing herbs in trade.'"
        }
    }
}

This module integrates with:
- services.py: For service-based exchanges (healing, teaching)
- manipulation.py: handle_give invokes on_receive_item after transfer
"""

from typing import Any, Dict, Optional

from src.behavior_manager import EventResult


def on_receive_item(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Handle NPC receiving an item - check for trades or service payment.

    Called by handle_give after successful item transfer.

    Checks:
    1. Does NPC have a trade defined for this item?
    2. Does NPC have a service that accepts this item?

    If trade found: give counter-item to giver
    If service found: execute service (existing logic handles threshold)
    Otherwise: generic acceptance

    Args:
        entity: The NPC receiving the item
        accessor: StateAccessor instance
        context: Context dict with:
            - item_id: str - the item ID
            - item: Item - the item object
            - giver_id: str - the actor giving the item

    Returns:
        EventResult with message about NPC's response
    """
    item = context.get("item")
    item_id = context.get("item_id")
    giver_id = context.get("giver_id")

    if not item or not giver_id:
        return EventResult(allow=True, message="")

    # Check for direct trade
    trades = entity.properties.get("trades", {})
    if item_id in trades:
        trade = trades[item_id]
        return _execute_trade(accessor, entity, giver_id, item, trade)

    # Also check by item name for more flexible matching
    item_name_key = item.name.lower().replace(" ", "_")
    for trade_key, trade in trades.items():
        # Support matching by item name pattern
        if item_name_key in trade_key.lower():
            return _execute_trade(accessor, entity, giver_id, item, trade)

    # Check for service payment (delegate to existing services.py)
    from behaviors.actors.services import on_receive_for_service
    service_result = on_receive_for_service(entity, accessor, context)
    if service_result:
        return service_result

    # No trade or service - generic acceptance
    return EventResult(
        allow=True,
        message=f"{entity.name} accepts the {item.name}."
    )


def _execute_trade(
    accessor: Any,
    npc: Any,
    giver_id: str,
    given_item: Any,
    trade: Dict
) -> EventResult:
    """
    Execute a trade - give counter-item to giver.

    Args:
        accessor: StateAccessor instance
        npc: The NPC executing the trade
        giver_id: ID of the actor who gave the item
        given_item: The item that was given
        trade: Trade config dict with 'gives' and optional 'message'

    Returns:
        EventResult with trade outcome
    """
    gives_item_id = trade.get("gives")
    message = trade.get("message", f"{npc.name} gives you something in return.")

    if not gives_item_id:
        # Trade config is incomplete - just accept
        return EventResult(allow=True, message=message)

    # Find the item to give (must be in NPC's inventory)
    gives_item = None
    for inv_item_id in npc.inventory:
        if inv_item_id == gives_item_id:
            gives_item = accessor.get_item(inv_item_id)
            break

    if not gives_item:
        # NPC doesn't have the item to trade - apologize
        return EventResult(
            allow=True,
            message=f"{npc.name} accepts the {given_item.name} but seems unable to provide anything in return right now."
        )

    # Get giver actor
    giver = accessor.get_actor(giver_id)
    if not giver:
        return EventResult(allow=True, message=message)

    # Transfer item from NPC to giver
    # 1. Change item location
    gives_item.location = giver_id

    # 2. Remove from NPC inventory
    if gives_item_id in npc.inventory:
        npc.inventory.remove(gives_item_id)

    # 3. Add to giver inventory
    if gives_item_id not in giver.inventory:
        giver.inventory.append(gives_item_id)

    return EventResult(allow=True, message=message)


# Vocabulary extension - registers receive event
vocabulary = {
    "events": [
        {
            "event": "on_receive_item",
            "description": "Called when an NPC receives an item via give command. "
                          "Checks for trades and service payments."
        }
    ]
}
