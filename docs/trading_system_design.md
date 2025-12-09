# Trading System Design

## Problem

NPCs in Big Game have dialog topics mentioning trade (buy/sell/wares), but there's no mechanism to actually execute trades. The `give` command transfers items but doesn't invoke any behavior on the recipient to respond with a counter-trade.

## Existing Infrastructure

**Good news:** Most of the infrastructure already exists in `behaviors/actors/services.py`:

- `on_receive_for_service(entity, accessor, context)` - checks if received item is payment for a service
- Threshold logic: if amount too low, accepts but explains insufficiency
- If sufficient: automatically executes the service
- Trust-based discounts (trust >= 3 gives 50% off)

**The gap:** `handle_give` in `manipulation.py` doesn't invoke `on_receive_for_service` after transferring the item.

## Goals

1. Allow players to trade items with NPCs using natural commands like `give silvermoss to Maren`
2. NPCs respond appropriately - accepting desired items and giving something in return
3. Minimal changes - hook existing `on_receive_for_service` into `give` handler
4. Support both item-for-item barter and item-for-service exchanges

## Non-Goals

- Full currency system (gold coins as inventory items)
- Complex pricing/haggling mechanics
- NPC-to-NPC trading

## NPCs Requiring Trade Support

### Need new `trades` config:
1. **Herbalist Maren** - sells healing herbs/antidotes, buys silvermoss/ice crystals
2. **Myconid Elder** - sells spore lanterns/masks, buys healing items/minerals

### Already have `services` config (just need `give` to trigger them):
3. **Healer Elara** - services for items or gold (format needs alignment)
4. **Myconid Healer** - healing for gold or healing herbs (already correct format)
5. **Temple Keeper** - services for trust
6. **Swimmer Jek** - teaching/guiding for gold or salvage
7. **Archivist Construct** - information for scholarly proof

## Design

### 1. Modify `handle_give` to invoke recipient behavior

After successful item transfer, invoke `on_receive_item` event on the recipient:

```python
# In handle_give, after successful transfer:
context = {
    "item_id": item.id,
    "item": item,
    "giver_id": actor_id
}
receive_result = accessor.invoke_behavior(recipient, "on_receive_item", context)
if receive_result and receive_result.message:
    # Append NPC's response to the give message
    message = f"{base_message}\n{receive_result.message}"
```

### 2. Create `on_receive_item` behavior handler

In `behaviors/actors/trading.py`:

```python
def on_receive_item(entity, accessor, context) -> EventResult:
    """
    Handle NPC receiving an item - check for trades or service payment.

    Checks:
    1. Does NPC have a trade defined for this item?
    2. Does NPC have a service that accepts this item?

    If trade found: give counter-item to giver
    If service found: execute service (existing logic handles threshold)
    Otherwise: generic acceptance
    """
    item = context.get("item")
    giver_id = context.get("giver_id")

    if not item or not giver_id:
        return EventResult(allow=True, message="")

    # Check for direct trade
    trades = entity.properties.get("trades", {})
    if item.id in trades:
        trade = trades[item.id]
        return execute_trade(accessor, entity, giver_id, item, trade)

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
```

### 3. Add `trades` config to NPC properties

For barter-focused NPCs like the Herbalist:

```json
{
  "trades": {
    "item_fd_silvermoss": {
      "gives": "item_cr_healing_herbs",
      "message": "'Silvermoss! Excellent. Here, take these healing herbs in trade.'"
    },
    "item_fd_ice_crystal": {
      "gives": "item_cr_antidote",
      "message": "'Ice crystals from the north! These will make fine remedies. Take this antidote.'"
    }
  }
}
```

### 4. Update Big Game NPC data

Add `trades` config to Herbalist Maren:
```json
"trades": {
  "item_fd_silvermoss": {
    "gives": "item_cr_healing_herbs",
    "message": "'Silvermoss! This is exactly what I need. Here, take these healing herbs - fair trade.'"
  }
}
```

Add `trades` config to Myconid Elder:
```json
"trades": {
  "item_fd_healing_herb": {
    "gives": "item_fd_spore_lantern",
    "message": "*Spores form images of exchange* 'Healing gift accepted. Light gift given.'"
  },
  "item_fd_rare_mineral": {
    "gives": "item_fd_breathing_mask",
    "message": "*Spores shimmer with approval* 'Deep earth treasure for deep earth protection.'"
  }
}
```

## Implementation Steps

1. **Create `behaviors/actors/trading.py`** with:
   - `on_receive_item` event handler
   - `execute_trade` helper function
   - Vocabulary extension registering the event

2. **Modify `behaviors/core/manipulation.py`**:
   - Add behavior invocation after successful give

3. **Update `examples/big_game/game_state.json`**:
   - Add `trades` config to Herbalist Maren
   - Add `trades` config to Myconid Elder
   - Load trading behavior module

4. **Tests**:
   - Test give triggers on_receive_item
   - Test trade execution (item exchange)
   - Test service payment via give
   - Test generic acceptance for non-trade items

## Example Gameplay

```
> give silvermoss to Maren
You give the silvermoss to Herbalist Maren.
'Silvermoss! This is exactly what I need. Here, take these healing herbs - fair trade.'

> inventory
You are carrying:
  healing herbs
```

## Exchange Rates

The barter system uses 1:1 item exchanges. Each trade involves a single item given in exchange for a single item received.

**Herbalist Maren:**
- silvermoss → healing herbs (1:1)
- ice crystal → antidote (1:1)

**Myconid Elder:**
- healing herb → spore lantern (1:1)
- rare mineral → breathing mask (1:1)

These rates reflect the difficulty of obtaining the items:
- Silvermoss and ice crystals require traveling to dangerous regions
- The trade goods (herbs, antidotes, lanterns, masks) are useful but obtainable through other means

## Implementation Notes

**Dialog text updates:** References to "pay" and "coin" have been changed to "trade" for consistency since Big Game uses barter, not currency. The treasure chest item still mentions gold coins but that's a descriptive/narrative element, not a functional currency.

**Item locations:** Trade items (spore lantern, breathing mask) have been moved to NPC inventories so they can be given in trades. Items the player finds (silvermoss, ice crystal, healing herb, rare mineral) remain in their original locations.

## Alternative Considered

**Separate `trade` verb**: e.g., `trade silvermoss for herbs with Maren`

Rejected because:
- More complex parser requirements
- `give` already handles the item transfer semantics
- NPCs responding to gifts is more natural/immersive
