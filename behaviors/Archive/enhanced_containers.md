# Enhanced Containers - Design Document

## Status

**Not yet implemented** - Design document for future feature.

## Use Cases

### UC-1: Furniture that holds items
A stone pedestal in a tower holds a potion. The player can:
- Examine the pedestal and see the potion on it
- Take the potion from the pedestal
- Put other items on the pedestal
- Cannot take the pedestal itself

### UC-2: Moveable furniture
A heavy crate blocks a passage. The player can:
- Push the crate to move it aside
- Cannot take the crate (too heavy)
- The crate may hold items inside

### UC-3: Surface vs. enclosed containers
- A table has items "on" it (visible, accessible)
- A chest has items "in" it (hidden until opened)

### UC-4: Limited capacity
- A small shelf can hold 3 items
- A pedestal can hold 1 item
- Attempting to add more fails with appropriate message

## Goals

1. **Support non-portable containers** - Items that hold other items but cannot be taken
2. **Support "put" command** - Place items on/in containers
3. **Support "push" command** - Move heavy furniture
4. **Distinguish surface vs. enclosed** - Items on surfaces visible; items in containers hidden until opened
5. **Enforce capacity limits** - Containers have maximum item count

## Non-Goals

- Complex container nesting (containers in containers)
- Weight-based capacity (item count is sufficient)
- Automatic item transfer when pushing containers
- Container locking separate from door locking

## Data Model

### Enhanced Item Schema

```json
{
  "id": "item_pedestal",
  "name": "pedestal",
  "description": "A stone pedestal with a shallow depression on top.",
  "type": "furniture",
  "portable": false,
  "location": "loc_tower",
  "container": {
    "is_container": true,
    "is_surface": true,
    "capacity": 1
  },
  "pushable": true,
  "llm_context": {
    "traits": ["weathered stone", "ancient", "single slot on top"]
  }
}
```

The potion would have:
```json
{
  "id": "item_potion",
  "name": "potion",
  "location": "item_pedestal",
  ...
}
```

### Container Fields

| Field | Type | Description |
|-------|------|-------------|
| `is_container` | bool | True if this item can hold other items |
| `is_surface` | bool | True = items visible ("on"), False = items hidden ("in", requires open) |
| `open` | bool | For enclosed containers, whether currently open |
| `capacity` | int | Maximum number of items (0 = unlimited) |

Note: Items in containers have `location` set to the container's ID (e.g., `"item_pedestal"`). This keeps item location tracking consistent.

### New Item Field

| Field | Type | Description |
|-------|------|-------------|
| `pushable` | bool | Can be pushed to move it |

## Commands

### Put Command

**Syntax**: `put <item> on/in <container>`

**Pattern**: VERB + NOUN + PREP + NOUN

**Behavior**:
1. Item must be in player inventory
2. Container must be in current location
3. Container must have capacity
4. If enclosed container, must be open
5. Move item from inventory to container

**Result**:
```json
{
  "success": true,
  "action": "put",
  "entity": {"name": "potion", ...},
  "container": {"name": "pedestal", ...},
  "message": "You place the potion on the pedestal."
}
```

### Enhanced Take Command

When taking from a container:

**Syntax**: `take <item> from <container>`

**Pattern**: VERB + NOUN + PREP + NOUN (already supported)

**Behavior**:
1. Find item in specified container
2. If enclosed container, must be open
3. Move item to player inventory

When item is in a surface container, `take <item>` should also work (item is visible).

### Push Command

**Syntax**: `push <item>`

**Pattern**: VERB + NOUN

**Behavior**:
1. Item must be in current location
2. Item must have `pushable: true`
3. Item must not be portable (can't push what you can carry)
4. Invoke `on_push` behavior if present

The actual effect of pushing depends on the entity behavior. Common patterns:
- Move to adjacent location
- Reveal hidden passage
- Trigger mechanism

**Result**:
```json
{
  "success": true,
  "action": "push",
  "entity": {"name": "crate", ...},
  "message": "You push the heavy crate aside, revealing a trapdoor."
}
```

## Visibility Rules

### Items on Surfaces
- Visible in room description
- Shown when examining the container
- Can be taken directly (`take potion`) or from container (`take potion from pedestal`)

### Items in Enclosed Containers
- Hidden until container is opened
- Shown when examining open container
- Must specify container to take (`take potion from chest`)

## Implementation Notes

### Vocabulary Extension

Add to `behaviors/core/containers.py`:

```python
vocabulary = {
    "verbs": [
        # ... existing open, close ...
        {
            "word": "put",
            "synonyms": ["place", "set"],
            "object_required": True,
            "llm_context": {
                "traits": ["places item in/on container"],
                "failure_narration": {
                    "no_capacity": "won't fit",
                    "not_container": "can't put things there",
                    "container_closed": "it's closed"
                }
            }
        }
    ]
}
```

### State Manager Changes

- Update `Item` dataclass to include `pushable` field
- Ensure container items list is loaded/saved

### JSON Protocol Changes

- Add `_cmd_put` handler
- Modify `_cmd_take` to check containers
- Add `_cmd_push` handler (currently exists as stub)
- Update `_find_accessible_item` to search containers on surfaces

### Room Description Changes

When describing a location, include visible items on surfaces:
- "A stone pedestal holds a glowing potion."
- "On the table you see a key and a letter."

## Behavior Integration

### on_put Event
Called when item is placed in container:
```python
def on_put(entity, state, context):
    # entity = the container
    # context["item"] = the item being placed
    pass
```

### on_push Event
Already defined in interaction.py. Specific behaviors determine effect:
```python
def on_push_crate(entity, state, context):
    # Move crate to adjacent room
    entity.location = "loc_hidden_passage"
    state.locations["loc_tower"].exits["down"] = {
        "type": "open",
        "to": "loc_hidden_passage"
    }
    return EventResult(
        allow=True,
        message="The crate slides aside, revealing a hidden trapdoor!"
    )
```

## Example: Tower Pedestal

### Game State

Pedestal:
```json
{
  "id": "item_pedestal",
  "name": "pedestal",
  "description": "A weathered stone pedestal.",
  "type": "furniture",
  "portable": false,
  "location": "loc_tower",
  "container": {
    "is_container": true,
    "is_surface": true,
    "capacity": 1
  },
  "llm_context": {
    "traits": ["ancient stone", "waist-high", "flat top with shallow depression"]
  }
}
```

Potion (on the pedestal):
```json
{
  "id": "item_potion",
  "name": "potion",
  "location": "item_pedestal",
  ...
}
```

### Player Interactions

```
> look
Tower Top
You are at the top of a tower. A stone pedestal holds a glowing red potion.

> examine pedestal
The pedestal is ancient stone, waist-high with a flat top. A glowing potion rests in the shallow depression.

> take potion
You take the potion from the pedestal.

> put key on pedestal
You place the key on the pedestal.
```

## Design Review

### Consistency Check

1. **Container model** - Reuses existing `container` field structure from chests
2. **Command patterns** - Uses existing VERB + NOUN + PREP + NOUN pattern
3. **Behavior system** - Uses standard `on_<verb>` event naming
4. **Vocabulary** - Extends existing containers.py module

### Simplicity Check

1. **No nested containers** - Keeps item location simple (location or container, not both)
2. **Count-based capacity** - Simpler than weight calculations
3. **Single pushable flag** - No complex physics simulation
4. **Surface vs enclosed** - Simple boolean, not multiple container types

### Potential Issues

1. **Item visibility** - Need clear rules for when surface items appear in room description
2. **Ambiguous take** - If item name appears in room and on surface, which takes precedence?
   - Resolution: Prioritize direct room items, then surface containers
3. **Push direction** - Current design doesn't specify direction
   - Resolution: Let behavior handle specifics; generic push just invokes behavior

## Migration Path

### Phase 1: Data Model
1. Add `pushable` field to Item dataclass
2. Ensure container.items list works for items

### Phase 2: Put Command
1. Add put verb to vocabulary
2. Implement `_cmd_put` handler
3. Add tests for put command

### Phase 3: Enhanced Take
1. Modify `_cmd_take` to search surface containers
2. Support `take X from Y` syntax
3. Add tests

### Phase 4: Push Command
1. Implement `_cmd_push` handler (beyond current stub)
2. Add tests

### Phase 5: Room Descriptions
1. Update location queries to include surface container items
2. Update LLM narrator prompt with container examples

## Summary

This design adds support for:
- Non-portable containers (pedestals, tables, crates)
- Put command to place items in/on containers
- Push command to move heavy furniture
- Surface containers with visible items vs. enclosed containers

The design maintains consistency with existing patterns and avoids unnecessary complexity by using simple boolean flags and count-based capacity.
