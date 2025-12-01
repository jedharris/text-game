# Enhanced Containers - Implementation Plan

## Overview

Implementation of the enhanced containers feature as specified in [enhanced_containers.md](enhanced_containers.md).

## Phase 1: Data Model Updates

### 1.1 Update Item Dataclass

**File**: `src/state_manager.py`

Add `pushable` field to Item:
```python
@dataclass
class Item:
    # ... existing fields ...
    pushable: bool = False
```

Update `ContainerInfo` to include `is_surface`:
```python
@dataclass
class ContainerInfo:
    is_container: bool = True
    is_surface: bool = False  # True = items visible on top
    open: bool = False
    capacity: int = 0  # 0 = unlimited
```

### 1.2 Update State Loading

**File**: `src/state_manager.py`

Ensure `load_game_state` handles:
- `pushable` field on items
- `is_surface` field in container info

### 1.3 Tests

- Test loading item with `pushable: true`
- Test loading container with `is_surface: true`
- Test item with `location` pointing to container ID

## Phase 2: Put Command

### 2.1 Vocabulary

**File**: `behaviors/core/containers.py`

Add put verb:
```python
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
```

### 2.2 Command Handler

**File**: `src/json_protocol.py`

Implement `_cmd_put`:
1. Parse action for object and target (indirect_object)
2. Find item in player inventory
3. Find container in current location
4. Validate:
   - Item exists in inventory
   - Container exists and is_container
   - Container has capacity (count items with location = container.id)
   - If not is_surface, container must be open
5. Move item: set `item.location = container.id`
6. Remove from player inventory
7. Return result with entity and container

### 2.3 Tests

- Put item on surface container
- Put item in enclosed container (open)
- Fail: put in closed container
- Fail: put when at capacity
- Fail: put on non-container
- Fail: put item not in inventory

## Phase 3: Enhanced Take Command

### 3.1 Update _find_accessible_item

**File**: `src/json_protocol.py`

Modify to search surface containers:
1. Check player inventory
2. Check current location
3. Check surface containers in current location
4. Return item and its container (if any)

### 3.2 Update _cmd_take

**File**: `src/json_protocol.py`

Handle taking from containers:
1. If item is in a container:
   - If enclosed container, must be open
   - Set item.location to player location temporarily (then to inventory)
2. Support `take X from Y` syntax using indirect_object

### 3.3 Tests

- Take item from surface (visible)
- Take item from open enclosed container
- Fail: take from closed container
- Take with explicit "from container" syntax

## Phase 4: Push Command

### 4.1 Command Handler

**File**: `src/json_protocol.py`

Implement `_cmd_push`:
1. Find item in current location
2. Validate:
   - Item exists
   - Item has `pushable: true`
   - Item is not portable (can't push what you can carry)
3. Return result with entity_obj for behavior invocation

Note: Actual push effects are handled by entity behaviors.

### 4.2 Tests

- Push pushable item (invokes behavior)
- Fail: push non-pushable item
- Fail: push portable item
- Fail: push item not in location

## Phase 5: Game State Updates

### 5.1 Add Pedestal to Tower

**File**: `examples/simple_game_state.json`

Add pedestal item:
```json
{
  "id": "item_pedestal",
  "name": "pedestal",
  "description": "A weathered stone pedestal with a shallow depression on top.",
  "type": "furniture",
  "portable": false,
  "location": "loc_tower",
  "container": {
    "is_container": true,
    "is_surface": true,
    "capacity": 1
  },
  "llm_context": {
    "traits": ["ancient stone", "waist-high", "flat top"],
    "state_variants": {
      "empty": "stands empty, waiting",
      "holding_item": "holds something on its surface"
    }
  }
}
```

Update potion location:
```json
{
  "id": "item_potion",
  "location": "item_pedestal",
  ...
}
```

Update tower location description to not mention pedestal (it's now an item):
- Remove "pedestal" from description
- Update state_variants

### 5.2 Add Table to Hallway

**File**: `examples/simple_game_state.json`

Add table item:
```json
{
  "id": "item_table",
  "name": "table",
  "description": "A sturdy wooden table against the wall.",
  "type": "furniture",
  "portable": false,
  "location": "loc_hallway",
  "container": {
    "is_container": true,
    "is_surface": true,
    "capacity": 5
  },
  "llm_context": {
    "traits": ["oak wood", "worn surface", "sturdy legs"],
    "state_variants": {
      "empty": "its surface bare",
      "holding_items": "holds various items"
    }
  }
}
```

Update lantern location:
```json
{
  "id": "item_lantern",
  "location": "item_table",
  ...
}
```

Update hallway description to not mention lantern directly (it's on the table).

### 5.3 Update Location Descriptions

Remove direct item mentions that are now on furniture:
- loc_tower: remove pedestal/potion mentions
- loc_hallway: remove lantern mention

## Phase 6: Room Description Updates

### 6.1 Update Location Queries

**File**: `src/json_protocol.py`

When querying location, include items on surface containers:
1. Get items directly in location
2. Get surface containers in location
3. For each surface container, get items inside
4. Format appropriately: "On the table: lantern, key"

### 6.2 Update _location_to_dict

Include surface container contents in location data for LLM narrator.

### 6.3 Tests

- Location query includes items on surfaces
- Enclosed container contents not shown until opened

## Phase 7: Narrator Prompt Updates

### 7.1 Update Examples

**File**: `examples/narrator_prompt.txt`

Add examples for:
- Put command
- Taking from container
- Room with furniture holding items

### 7.2 Container Description Guidelines

Add guidance for describing:
- Items on surfaces vs. in containers
- Furniture in room descriptions

## Implementation Order

1. **Phase 1**: Data model (foundation for everything)
2. **Phase 3**: Enhanced take (most impactful for gameplay)
3. **Phase 5**: Game state updates (can test take from containers)
4. **Phase 6**: Room descriptions (visibility of items on surfaces)
5. **Phase 2**: Put command (requires container infrastructure)
6. **Phase 4**: Push command (least critical)
7. **Phase 7**: Narrator updates (polish)

## Testing Strategy

### Unit Tests

Each phase includes unit tests for:
- Success cases
- Failure cases with appropriate errors
- Edge cases

### Integration Tests

After Phase 5:
- Full gameplay test: enter hallway, take lantern from table, behaviors work
- Full gameplay test: enter tower, take potion from pedestal
- Put item back on furniture

### LLM Game Test

Manual testing with llm_game to verify:
- Room descriptions mention furniture and items
- Take/put commands narrated correctly
- Behavior messages still work (lantern lighting)

## Estimated Effort

- Phase 1: Small (data model changes)
- Phase 2: Medium (new command handler)
- Phase 3: Medium (modify existing take logic)
- Phase 4: Small (simple handler, behaviors do work)
- Phase 5: Small (JSON edits)
- Phase 6: Medium (room description logic)
- Phase 7: Small (documentation)

Total: ~200-300 lines of code + tests

## Risks and Mitigations

### Risk: Breaking existing take behavior
**Mitigation**: Extensive tests for existing take scenarios before modifying

### Risk: Item location ambiguity
**Mitigation**: Clear convention that location is always a single ID (room or container)

### Risk: Room descriptions become cluttered
**Mitigation**: Smart formatting, show surface items naturally ("On the table you see...")

## Success Criteria

1. Can take lantern from table in hallway
2. Lantern still lights when taken (behavior works)
3. Can take potion from pedestal in tower
4. Can put items on pedestal/table
5. Room descriptions show items on furniture
6. All existing tests pass
7. 439+ tests (new tests added)
