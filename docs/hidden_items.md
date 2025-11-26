# Hidden Items Design

## Overview

This document explores adding support for hidden items (and potentially doors) to the text game engine. Hidden items are not visible to players until explicitly revealed through gameplay actions.

## Use Cases

1. **Items hidden inside other objects** - A key hidden inside a crystal ball, revealed when the player peers into it
2. **Items requiring search** - A coin under a rug, found when the player searches the area
3. **Puzzle reveals** - Items that appear after solving a puzzle or performing specific actions
4. **Secret passages** - Doors that only become visible after discovering them

## Design Questions

### 1. Property vs Behavior

**Question:** Should "hidden" be a property on items/doors, or handled through behaviors?

**Recommendation: Property with optional behavior hooks**

A property is the right choice because:
- Hidden/visible is a fundamental visibility state, not conditional logic
- The engine needs to filter hidden items at multiple points (`gather_location_contents`, `find_accessible_item`, `describe_location`)
- Consistent with other boolean states like `portable`, `locked`, `open`
- Behaviors can still hook into reveal events via `on_reveal` callback

The property approach in game state:
```json
{
  "id": "item_sanctum_key",
  "name": "key",
  "description": "A golden key that glows faintly with magic.",
  "location": "loc_library",
  "properties": {
    "hidden": true,
    "portable": true
  }
}
```

### 2. Reveal Mechanisms

**Question:** What should reveal hidden items?

**Recommendation: Multiple mechanisms, all explicit**

| Mechanism | Description | Use Case |
|-----------|-------------|----------|
| Behavior-triggered | Entity behaviors call `accessor.reveal_item(item)` | Crystal ball revealing a key when peered into |
| Search command | New `search` verb reveals hidden items in target | Finding a coin under a rug |
| Examine with property | Optional `reveal_on_examine: true` property | Simple hidden items found by close inspection |

Example behavior-triggered reveal (crystal ball):
```python
def on_peer(entity, accessor, context):
    sanctum_key = accessor.get_item("item_sanctum_key")
    if sanctum_key and sanctum_key.properties.get("hidden"):
        accessor.reveal_item(sanctum_key)
        return EventResult(
            allow=True,
            message="A golden key materializes and falls to the floor!"
        )
```

### 3. Visibility Semantics

**Question:** How invisible should hidden items be?

**Recommendation: Completely invisible until revealed**

- Hidden items are excluded from `look` output
- Hidden items are excluded from `examine` (unless `reveal_on_examine` is set)
- Hidden items cannot be found by `find_accessible_item`
- Players cannot interact with hidden items even if they know the name
- Once revealed (`hidden: false`), the item behaves normally

This approach:
- Avoids "guess the hidden item name" gameplay
- Is consistent with classic adventure game conventions
- Keeps the mechanic simple and predictable

**Alternative considered but rejected:** Items hidden from `look` but findable with `examine`. This creates ambiguity about what "hidden" means and encourages players to examine everything.

## Implementation

### Changes to utilities/utils.py

#### gather_location_contents()

Filter hidden items from all returned collections:

```python
def gather_location_contents(accessor, location_id: str, actor_id: str) -> dict:
    # ... existing code ...

    # Filter: exclude hidden items
    items_here = [item for item in items_here
                  if not item.properties.get("hidden", False)]
```

#### find_accessible_item()

Skip hidden items during search:

```python
def find_accessible_item(accessor, name: str, actor_id: str, adjective: Optional[str] = None):
    # ... existing code ...

    for item in items_in_location:
        # Skip hidden items
        if item.properties.get("hidden", False):
            continue
        if item.name.lower() == name_lower:
            matching_items.append(item)
```

#### find_item_in_container()

Skip hidden items:

```python
def find_item_in_container(accessor, item_name: str, container_id: str, adjective: Optional[str] = None):
    # ... existing code ...

    for item in items_in_container:
        # Skip hidden items
        if item.properties.get("hidden", False):
            continue
        if item.name.lower() == name_lower:
            matching_items.append(item)
```

### Changes to src/state_accessor.py

Add reveal method:

```python
def reveal_item(self, item) -> None:
    """
    Reveal a hidden item, making it visible and interactable.

    Args:
        item: Item to reveal (by object or ID)
    """
    if isinstance(item, str):
        item = self.get_item(item)
    if item:
        item.properties["hidden"] = False
```

### Optional: Search Command

Add to `behaviors/core/perception.py`:

```python
vocabulary = {
    "verbs": [
        # ... existing verbs ...
        {
            "word": "search",
            "event": "on_search",
            "synonyms": ["look in", "look under"],
            "object_required": "optional"
        }
    ]
}

def handle_search(accessor, action):
    """Search a container or location for hidden items."""
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

    # Determine search target
    if object_name:
        # Search specific container
        target = find_container(accessor, object_name, actor_id)
        if not target:
            return HandlerResult(False, f"You can't search the {object_name}.")
        search_location = target.id
    else:
        # Search current location
        location = accessor.get_current_location(actor_id)
        search_location = location.id

    # Find hidden items in search location
    revealed = []
    for item in accessor.game_state.items:
        if item.location == search_location and item.properties.get("hidden"):
            accessor.reveal_item(item)
            revealed.append(item.name)

    if revealed:
        return HandlerResult(True, f"You find: {', '.join(revealed)}")
    else:
        return HandlerResult(True, "You don't find anything hidden.")
```

## Hidden Doors

The same pattern can apply to doors for secret passages:

```json
{
  "id": "door_secret",
  "locations": ["loc_library", "loc_hidden_room"],
  "description": "A hidden door behind the bookshelf.",
  "properties": {
    "hidden": true,
    "open": false
  }
}
```

Changes needed:
- `get_doors_in_location()` filters hidden doors
- `find_door_with_adjective()` skips hidden doors
- Add `reveal_door()` method to StateAccessor

## Migration Path

Existing games are unaffected:
- Items without `hidden` property default to `hidden: false` (visible)
- No breaking changes to game state format
- New functionality is opt-in

## Testing Strategy

1. **Unit tests for visibility filtering**
   - Hidden items excluded from `gather_location_contents`
   - Hidden items not found by `find_accessible_item`
   - Hidden items in containers not found

2. **Unit tests for reveal mechanism**
   - `reveal_item()` sets `hidden: false`
   - Revealed items appear in subsequent lookups

3. **Integration tests**
   - Search command reveals hidden items
   - Behavior-triggered reveal works
   - `reveal_on_examine` property works

4. **End-to-end test**
   - Update extended_game example to use hidden key instead of workaround
