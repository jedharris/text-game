# Weight System Extension Example

This example demonstrates how to extend the core `handle_take` with weight limits. It shows the StateAccessor pattern's support for semantic error context.

```python
from behaviors.core.utils import find_accessible_item, find_item_in_inventory

def handle_take(accessor, action):
    """Handle take command with weight limits."""
    obj_name = action.get("object")
    item = find_accessible_item(accessor, obj_name)
    if not item:
        return (False, "You don't see that here.")

    if not item.portable:
        return (False, "You can't take that.")

    actor = accessor.get_actor()
    weight = item.properties.get("weight", 1)
    current_weight = actor.properties.get("carried_weight", 0)
    max_weight = actor.properties.get("max_carry", 100)

    if current_weight + weight > max_weight:
        lightest = find_lightest_carried_item(accessor)
        if lightest:
            return (False, f"The {item.name} is too heavy. You could drop the {lightest.name} first.")
        return (False, f"The {item.name} is too heavy.")

    # Update with automatic on_take behavior invocation
    result = accessor.update(
        entity=item,
        changes={"location": accessor.actor_id},
        event="on_take"
    )

    if not result.success:
        return (False, result.message or "You can't take that.")

    # Update actor's inventory and carried weight
    accessor.append_to_list(actor, "inventory", item.id)
    new_weight = current_weight + weight
    accessor.update(
        entity=actor,
        changes={"properties.carried_weight": new_weight}
    )

    return (True, result.message or f"You take the {item.name}.")


def find_lightest_carried_item(accessor):
    """Find the lightest item in the actor's inventory."""
    actor = accessor.get_actor()
    lightest = None
    lightest_weight = float('inf')

    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item:
            weight = item.properties.get("weight", 1)
            if weight < lightest_weight:
                lightest = item
                lightest_weight = weight

    return lightest
```

## Notes

- This extends the core `handle_take` by adding weight tracking
- Requires items to have a `weight` property (defaults to 1)
- Requires actors to have `carried_weight` and `max_carry` properties
- The `find_lightest_carried_item` helper suggests what to drop
- To use this extension, load your module after the core modules so it overrides `handle_take`

## Required Game State Properties

**Items**:
```json
{
  "id": "item_sword",
  "name": "sword",
  "properties": {
    "portable": true,
    "weight": 5
  }
}
```

**Player/NPCs**:
```json
{
  "location": "room_start",
  "inventory": [],
  "properties": {
    "carried_weight": 0,
    "max_carry": 50
  }
}
```
