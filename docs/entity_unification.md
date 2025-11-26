# Entity Unification Design: Items and Doors

## Problem Statement

The codebase has parallel handling for items and doors that share most characteristics but are treated as separate entity types. This has led to:

1. **Duplicated utility functions**: `find_accessible_item()` vs `find_door_with_adjective()`, separate handling in `gather_location_contents()`
2. **Inconsistent feature support**: Items have containers, doors don't; doors have locations tuple, items have single location
3. **Bug surface area**: Each feature (hidden, behaviors, properties) must be implemented twice
4. **API complexity**: `get_item()`, `get_door()`, separate search functions, different query patterns

The hidden item feature request highlights this: we'd need to implement hidden support for both items and doors separately, with parallel changes to multiple utility functions.

## Decision: Full Unification

After analysis, we're proceeding with **full unification** - a single `Item` type that encompasses both traditional items and doors. Breaking changes are acceptable in favor of the cleanest design.

### Core Insight: Doors Live in Exits

A door is ontologically located *in the exit*, not in either room it connects. This insight drives the design:

- A door item has a `location` like any item (the exit, a room, a container)
- When a door is referenced by an exit, it appears visible from both connected rooms
- A door can also exist without being in an exit (e.g., a decorative door on a wall, a door to nowhere)

## Unified Item Design

### Item Dataclass (Unchanged Structure)

```python
@dataclass
class Item:
    id: str
    name: str
    description: str
    location: str                              # Where the item physically is
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: List[str] = field(default_factory=list)
```

### Door-Specific Properties

Doors are items with `properties.door` defined:

```python
"properties": {
    "door": {
        "open": false,          # Is door open?
        "locked": false,        # Is door locked?
        "lock_id": "lock_xyz"   # Optional reference to lock
    },
    "portable": false,          # Doors are never portable
    "hidden": false             # Hidden doors (secret passages)
}
```

### Exit Descriptor (Minor Change)

Exits reference door items by ID:

```python
@dataclass
class ExitDescriptor:
    type: str                   # "open", "door", "blocked"
    to: Optional[str]           # Destination location ID
    door_id: Optional[str]      # ID of door ITEM (was separate Door entity)
```

### Example Game State

```json
{
  "items": [
    {
      "id": "item_wooden_door",
      "name": "door",
      "description": "A simple wooden door.",
      "location": "exit:loc_entrance:east",
      "properties": {
        "door": {"open": false, "locked": false},
        "portable": false
      }
    },
    {
      "id": "item_decorative_door",
      "name": "door",
      "description": "An ornate door set into the wall. It doesn't seem to lead anywhere.",
      "location": "loc_gallery",
      "properties": {
        "door": {"open": false, "locked": true},
        "portable": false
      }
    },
    {
      "id": "item_sword",
      "name": "sword",
      "description": "A gleaming steel sword.",
      "location": "loc_armory",
      "properties": {"portable": true}
    }
  ],
  "locations": [
    {
      "id": "loc_entrance",
      "name": "Entrance Hall",
      "exits": {
        "east": {
          "type": "door",
          "to": "loc_storage",
          "door_id": "item_wooden_door"
        }
      }
    }
  ]
}
```

## Location Semantics

### Standard Locations

Items can be located in:
- **Room**: `"location": "loc_entrance"` - item is in a room
- **Container**: `"location": "item_chest"` - item is inside another item
- **Actor inventory**: `"location": "player"` - item is carried
- **Exit**: `"location": "exit:loc_entrance:east"` - item is in an exit (primarily for doors)

### Exit Location Format

For doors in exits, the location uses a structured format:
```
exit:<location_id>:<direction>
```

Example: `"exit:loc_entrance:east"` means "in the east exit of loc_entrance"

This format:
- Makes the door's canonical location explicit
- Allows doors to be moved (e.g., a portable door panel)
- Supports queries like "what's in this exit?"

### Door Visibility

A door is visible from a location if:
1. Its location is that room (decorative door on wall), OR
2. Any exit in that room references it via `door_id`

```python
def is_item_visible_in_location(item, location_id: str, accessor) -> bool:
    """Check if item should be visible in a location."""
    # Direct location match
    if item.location == location_id:
        return True

    # For doors: check if any exit in this location references the door
    if item.properties.get("door"):
        location = accessor.get_location(location_id)
        if location:
            for exit_desc in location.exits.values():
                if exit_desc.door_id == item.id:
                    return True

    return False
```

## Removed Entities

### Door Dataclass (Removed)

The `Door` dataclass is eliminated. All functionality moves to items with door properties.

**Before:**
```python
@dataclass
class Door:
    id: str
    locations: Tuple[str, ...]
    properties: Dict[str, Any]
    behaviors: List[str]
```

**After:** Doors are items.

### Lock Consideration

Locks remain as a separate entity type for now. They represent abstract mechanisms, not physical objects. A future iteration could unify locks as items too (a physical padlock), but this is out of scope.

## API Changes

### StateAccessor

```python
class StateAccessor:
    # REMOVED
    # def get_door(self, door_id: str) -> Optional[Door]

    # UNCHANGED - get_item now returns door-items too
    def get_item(self, item_id: str) -> Optional[Item]

    # NEW - convenience method
    def get_door_item(self, door_id: str) -> Optional[Item]:
        """Get a door item by ID. Returns None if not found or not a door."""
        item = self.get_item(door_id)
        if item and item.properties.get("door"):
            return item
        return None

    # NEW - for exit-based door lookup
    def get_door_for_exit(self, location_id: str, direction: str) -> Optional[Item]:
        """Get the door item for an exit, if any."""
        location = self.get_location(location_id)
        if not location:
            return None
        exit_desc = location.exits.get(direction)
        if not exit_desc or not exit_desc.door_id:
            return None
        return self.get_door_item(exit_desc.door_id)
```

### GameState

```python
@dataclass
class GameState:
    metadata: Metadata
    locations: List[Location]
    items: List[Item]           # Now includes doors
    locks: List[Lock]
    actors: Dict[str, Actor]
    # REMOVED: doors: List[Door]

    # REMOVED
    # def get_door(self, door_id: str) -> Door
```

### Utility Functions

```python
# REMOVED - functionality merged into find_accessible_item
# find_door_with_adjective()

# REMOVED - doors included in standard item gathering
# get_doors_in_location()

# MODIFIED - now includes door items
def find_accessible_item(accessor, name: str, actor_id: str, adjective: Optional[str] = None):
    """Find any accessible item including doors."""
    # ... existing logic ...
    # Now also checks exit-referenced doors

def gather_location_contents(accessor, location_id: str, actor_id: str) -> dict:
    """Gather all visible items including doors."""
    # ... returns doors in items list ...
```

## Property Helpers

The Item dataclass gains door-related property accessors:

```python
@dataclass
class Item:
    # ... existing fields ...

    @property
    def is_door(self) -> bool:
        """Check if this item is a door."""
        return "door" in self.properties

    @property
    def door_open(self) -> bool:
        """Get door open state. Returns False if not a door."""
        door_props = self.properties.get("door", {})
        return door_props.get("open", False)

    @door_open.setter
    def door_open(self, value: bool) -> None:
        """Set door open state."""
        if "door" not in self.properties:
            self.properties["door"] = {}
        self.properties["door"]["open"] = value

    @property
    def door_locked(self) -> bool:
        """Get door locked state. Returns False if not a door."""
        door_props = self.properties.get("door", {})
        return door_props.get("locked", False)

    @door_locked.setter
    def door_locked(self, value: bool) -> None:
        """Set door locked state."""
        if "door" not in self.properties:
            self.properties["door"] = {}
        self.properties["door"]["locked"] = value

    @property
    def door_lock_id(self) -> Optional[str]:
        """Get door's lock ID. Returns None if not a door or no lock."""
        door_props = self.properties.get("door", {})
        return door_props.get("lock_id")
```

## Hidden Items (Now Unified)

With unification, hidden support is simple:

```python
def gather_location_contents(accessor, location_id: str, actor_id: str) -> dict:
    items_here = []

    for item in accessor.game_state.items:
        # Skip hidden items
        if item.properties.get("hidden", False):
            continue

        # Check visibility (handles both regular items and doors)
        if is_item_visible_in_location(item, location_id, accessor):
            items_here.append(item)

    # ... rest of function (surfaces, open containers, actors) ...
```

One implementation handles regular items, doors, and hidden doors (secret passages).

## Testing Strategy

This is a significant refactoring. We use TDD with comprehensive test coverage.

### Phase 1: New Infrastructure Tests (Write First)

Write tests for the new unified behavior before changing any implementation.

#### 1.1 Item Door Properties

```python
class TestItemDoorProperties:
    """Test door-related properties on Item dataclass."""

    def test_is_door_true_when_door_properties_present(self):
        """Item with properties.door is recognized as door."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room",
            properties={"door": {"open": False}}
        )
        assert item.is_door is True

    def test_is_door_false_for_regular_item(self):
        """Regular item is not a door."""
        item = Item(
            id="sword", name="sword", description="A sword",
            location="loc_room",
            properties={"portable": True}
        )
        assert item.is_door is False

    def test_door_open_getter(self):
        """door_open returns door's open state."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room",
            properties={"door": {"open": True}}
        )
        assert item.door_open is True

    def test_door_open_false_when_not_door(self):
        """door_open returns False for non-doors."""
        item = Item(
            id="sword", name="sword", description="A sword",
            location="loc_room", properties={}
        )
        assert item.door_open is False

    def test_door_open_setter(self):
        """door_open setter updates door state."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room",
            properties={"door": {"open": False}}
        )
        item.door_open = True
        assert item.properties["door"]["open"] is True

    def test_door_open_setter_creates_door_dict(self):
        """door_open setter creates door dict if missing."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room", properties={}
        )
        item.door_open = True
        assert item.properties["door"]["open"] is True

    def test_door_locked_getter(self):
        """door_locked returns door's locked state."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room",
            properties={"door": {"locked": True}}
        )
        assert item.door_locked is True

    def test_door_lock_id_getter(self):
        """door_lock_id returns lock reference."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room",
            properties={"door": {"lock_id": "lock_1"}}
        )
        assert item.door_lock_id == "lock_1"

    def test_door_lock_id_none_when_no_lock(self):
        """door_lock_id returns None when no lock."""
        item = Item(
            id="door_1", name="door", description="A door",
            location="loc_room",
            properties={"door": {"open": False}}
        )
        assert item.door_lock_id is None
```

#### 1.2 Door Visibility

```python
class TestDoorVisibility:
    """Test door visibility from connected locations."""

    def setup_method(self):
        """Create test state with door connecting two rooms."""
        self.state = load_game_state({
            "metadata": {"title": "Test"},
            "locations": [
                {
                    "id": "loc_room1",
                    "name": "Room 1",
                    "exits": {
                        "east": {"type": "door", "to": "loc_room2", "door_id": "door_connecting"}
                    }
                },
                {
                    "id": "loc_room2",
                    "name": "Room 2",
                    "exits": {
                        "west": {"type": "door", "to": "loc_room1", "door_id": "door_connecting"}
                    }
                }
            ],
            "items": [
                {
                    "id": "door_connecting",
                    "name": "door",
                    "description": "A wooden door.",
                    "location": "exit:loc_room1:east",
                    "properties": {"door": {"open": False}}
                }
            ],
            "actors": {"player": {"id": "player", "location": "loc_room1"}}
        })
        self.accessor = StateAccessor(self.state, BehaviorManager())

    def test_door_visible_from_first_room(self):
        """Door is visible from room1 (has exit referencing it)."""
        contents = gather_location_contents(self.accessor, "loc_room1", "player")
        door_ids = [item.id for item in contents["items"]]
        assert "door_connecting" in door_ids

    def test_door_visible_from_second_room(self):
        """Door is visible from room2 (has exit referencing it)."""
        contents = gather_location_contents(self.accessor, "loc_room2", "player")
        door_ids = [item.id for item in contents["items"]]
        assert "door_connecting" in door_ids

    def test_door_not_visible_from_unconnected_room(self):
        """Door not visible from room with no exit to it."""
        # Add a third room with no connection to the door
        self.state.locations.append(Location(
            id="loc_room3", name="Room 3", description="", exits={}
        ))
        contents = gather_location_contents(self.accessor, "loc_room3", "player")
        door_ids = [item.id for item in contents["items"]]
        assert "door_connecting" not in door_ids

    def test_decorative_door_visible_only_in_its_location(self):
        """Door without exit reference visible only in its location."""
        # Add decorative door directly in room3
        self.state.items.append(Item(
            id="door_decorative",
            name="door",
            description="An ornate door on the wall.",
            location="loc_room1",
            properties={"door": {"open": False}}
        ))

        # Visible in room1 where it's located
        contents = gather_location_contents(self.accessor, "loc_room1", "player")
        door_ids = [item.id for item in contents["items"]]
        assert "door_decorative" in door_ids

        # Not visible in room2 (no exit references it)
        contents = gather_location_contents(self.accessor, "loc_room2", "player")
        door_ids = [item.id for item in contents["items"]]
        assert "door_decorative" not in door_ids
```

#### 1.3 find_accessible_item with Doors

```python
class TestFindAccessibleItemWithDoors:
    """Test that find_accessible_item finds door items."""

    def setup_method(self):
        """Create state with doors and regular items."""
        self.state = load_game_state({
            "metadata": {"title": "Test"},
            "locations": [
                {
                    "id": "loc_room",
                    "name": "Room",
                    "exits": {
                        "north": {"type": "door", "to": "loc_other", "door_id": "door_iron"},
                        "south": {"type": "door", "to": "loc_other2", "door_id": "door_wooden"}
                    }
                }
            ],
            "items": [
                {
                    "id": "door_iron",
                    "name": "door",
                    "description": "A heavy iron door.",
                    "location": "exit:loc_room:north",
                    "properties": {"door": {"open": False}}
                },
                {
                    "id": "door_wooden",
                    "name": "door",
                    "description": "A wooden door.",
                    "location": "exit:loc_room:south",
                    "properties": {"door": {"open": False}}
                },
                {
                    "id": "item_key",
                    "name": "key",
                    "description": "A small key.",
                    "location": "loc_room",
                    "properties": {"portable": True}
                }
            ],
            "actors": {"player": {"id": "player", "location": "loc_room"}}
        })
        self.accessor = StateAccessor(self.state, BehaviorManager())

    def test_find_door_by_name(self):
        """find_accessible_item finds door by name 'door'."""
        item = find_accessible_item(self.accessor, "door", "player")
        assert item is not None
        assert item.is_door

    def test_find_door_with_adjective(self):
        """find_accessible_item finds specific door with adjective."""
        item = find_accessible_item(self.accessor, "door", "player", "iron")
        assert item is not None
        assert item.id == "door_iron"

    def test_find_door_with_different_adjective(self):
        """find_accessible_item finds wooden door with adjective."""
        item = find_accessible_item(self.accessor, "door", "player", "wooden")
        assert item is not None
        assert item.id == "door_wooden"

    def test_find_regular_item_still_works(self):
        """find_accessible_item still finds regular items."""
        item = find_accessible_item(self.accessor, "key", "player")
        assert item is not None
        assert item.id == "item_key"
```

#### 1.4 Hidden Door Support

```python
class TestHiddenDoors:
    """Test hidden door (secret passage) support."""

    def setup_method(self):
        """Create state with hidden and visible doors."""
        self.state = load_game_state({
            "metadata": {"title": "Test"},
            "locations": [
                {
                    "id": "loc_library",
                    "name": "Library",
                    "exits": {
                        "north": {"type": "door", "to": "loc_study", "door_id": "door_visible"},
                        "east": {"type": "door", "to": "loc_secret", "door_id": "door_secret"}
                    }
                }
            ],
            "items": [
                {
                    "id": "door_visible",
                    "name": "door",
                    "description": "A normal door.",
                    "location": "exit:loc_library:north",
                    "properties": {"door": {"open": False}}
                },
                {
                    "id": "door_secret",
                    "name": "door",
                    "description": "A hidden door behind the bookshelf.",
                    "location": "exit:loc_library:east",
                    "properties": {"door": {"open": False}, "hidden": True}
                }
            ],
            "actors": {"player": {"id": "player", "location": "loc_library"}}
        })
        self.accessor = StateAccessor(self.state, BehaviorManager())

    def test_hidden_door_not_in_location_contents(self):
        """Hidden door excluded from gather_location_contents."""
        contents = gather_location_contents(self.accessor, "loc_library", "player")
        door_ids = [item.id for item in contents["items"]]
        assert "door_visible" in door_ids
        assert "door_secret" not in door_ids

    def test_hidden_door_not_found_by_find_accessible_item(self):
        """Hidden door not found by find_accessible_item."""
        # Should find the visible door, not the hidden one
        item = find_accessible_item(self.accessor, "door", "player")
        assert item.id == "door_visible"

    def test_revealed_door_becomes_visible(self):
        """Door becomes visible after hidden=False."""
        secret_door = self.accessor.get_item("door_secret")
        secret_door.properties["hidden"] = False

        contents = gather_location_contents(self.accessor, "loc_library", "player")
        door_ids = [item.id for item in contents["items"]]
        assert "door_secret" in door_ids
```

#### 1.5 StateAccessor Door Methods

```python
class TestStateAccessorDoorMethods:
    """Test StateAccessor door-related methods."""

    def setup_method(self):
        """Create state with door."""
        self.state = load_game_state({
            "metadata": {"title": "Test"},
            "locations": [
                {
                    "id": "loc_room",
                    "name": "Room",
                    "exits": {
                        "north": {"type": "door", "to": "loc_other", "door_id": "door_1"}
                    }
                }
            ],
            "items": [
                {
                    "id": "door_1",
                    "name": "door",
                    "description": "A door.",
                    "location": "exit:loc_room:north",
                    "properties": {"door": {"open": False}}
                },
                {
                    "id": "item_sword",
                    "name": "sword",
                    "description": "A sword.",
                    "location": "loc_room",
                    "properties": {}
                }
            ],
            "actors": {"player": {"id": "player", "location": "loc_room"}}
        })
        self.accessor = StateAccessor(self.state, BehaviorManager())

    def test_get_door_item_returns_door(self):
        """get_door_item returns door item."""
        door = self.accessor.get_door_item("door_1")
        assert door is not None
        assert door.id == "door_1"
        assert door.is_door

    def test_get_door_item_returns_none_for_regular_item(self):
        """get_door_item returns None for non-door items."""
        result = self.accessor.get_door_item("item_sword")
        assert result is None

    def test_get_door_item_returns_none_for_missing(self):
        """get_door_item returns None for missing ID."""
        result = self.accessor.get_door_item("nonexistent")
        assert result is None

    def test_get_door_for_exit_returns_door(self):
        """get_door_for_exit returns door for exit with door."""
        door = self.accessor.get_door_for_exit("loc_room", "north")
        assert door is not None
        assert door.id == "door_1"

    def test_get_door_for_exit_returns_none_for_open_exit(self):
        """get_door_for_exit returns None for exit without door."""
        # Add open exit
        self.state.locations[0].exits["south"] = ExitDescriptor(
            type="open", to="loc_south"
        )
        result = self.accessor.get_door_for_exit("loc_room", "south")
        assert result is None

    def test_get_door_for_exit_returns_none_for_invalid_direction(self):
        """get_door_for_exit returns None for invalid direction."""
        result = self.accessor.get_door_for_exit("loc_room", "west")
        assert result is None
```

#### 1.6 Game State Loading/Saving

```python
class TestDoorItemSerialization:
    """Test loading and saving door items."""

    def test_load_door_item_from_json(self):
        """Door item loads correctly from JSON."""
        state = load_game_state({
            "metadata": {"title": "Test"},
            "locations": [],
            "items": [
                {
                    "id": "door_1",
                    "name": "door",
                    "description": "A wooden door.",
                    "location": "exit:loc_room:north",
                    "properties": {
                        "door": {"open": False, "locked": True, "lock_id": "lock_1"}
                    }
                }
            ],
            "actors": {}
        })

        door = state.get_item("door_1")
        assert door is not None
        assert door.is_door
        assert door.door_open is False
        assert door.door_locked is True
        assert door.door_lock_id == "lock_1"

    def test_save_door_item_to_dict(self):
        """Door item serializes correctly."""
        item = Item(
            id="door_1",
            name="door",
            description="A door.",
            location="exit:loc_room:north",
            properties={"door": {"open": True, "locked": False}}
        )

        result = _serialize_item(item)

        assert result["id"] == "door_1"
        assert result["door"]["open"] is True
        assert result["door"]["locked"] is False

    def test_load_state_without_doors_field(self):
        """State without 'doors' field loads correctly."""
        # New format: no doors field, doors are items
        state = load_game_state({
            "metadata": {"title": "Test"},
            "locations": [],
            "items": [],
            "actors": {}
        })
        # Should not have doors attribute or it should be empty
        assert not hasattr(state, 'doors') or len(state.doors) == 0
```

### Phase 2: Behavior Handler Tests

Test that command handlers work with door items.

#### 2.1 Open/Close Door Commands

```python
class TestOpenCloseDoorItems:
    """Test open/close commands work with door items."""

    def setup_method(self):
        """Create state with door item."""
        self.state = load_game_state({
            "metadata": {"title": "Test"},
            "locations": [
                {
                    "id": "loc_room",
                    "name": "Room",
                    "exits": {
                        "north": {"type": "door", "to": "loc_other", "door_id": "door_1"}
                    }
                }
            ],
            "items": [
                {
                    "id": "door_1",
                    "name": "door",
                    "description": "A wooden door.",
                    "location": "exit:loc_room:north",
                    "properties": {"door": {"open": False, "locked": False}}
                }
            ],
            "actors": {"player": {"id": "player", "location": "loc_room"}}
        })
        self.behavior_manager = BehaviorManager()
        # Load behaviors...
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_open_door_item(self):
        """open command works on door items."""
        action = {"verb": "open", "object": "door", "actor_id": "player"}
        result = handle_open(self.accessor, action)

        assert result.success
        door = self.accessor.get_item("door_1")
        assert door.door_open is True

    def test_close_door_item(self):
        """close command works on door items."""
        # First open the door
        door = self.accessor.get_item("door_1")
        door.door_open = True

        action = {"verb": "close", "object": "door", "actor_id": "player"}
        result = handle_close(self.accessor, action)

        assert result.success
        assert door.door_open is False

    def test_open_locked_door_fails(self):
        """Cannot open locked door item."""
        door = self.accessor.get_item("door_1")
        door.door_locked = True

        action = {"verb": "open", "object": "door", "actor_id": "player"}
        result = handle_open(self.accessor, action)

        assert not result.success
        assert "locked" in result.message.lower()
```

#### 2.2 Lock/Unlock Door Commands

```python
class TestLockUnlockDoorItems:
    """Test lock/unlock commands work with door items."""

    def setup_method(self):
        """Create state with lockable door."""
        self.state = load_game_state({
            "metadata": {"title": "Test"},
            "locations": [
                {
                    "id": "loc_room",
                    "name": "Room",
                    "exits": {
                        "north": {"type": "door", "to": "loc_other", "door_id": "door_1"}
                    }
                }
            ],
            "items": [
                {
                    "id": "door_1",
                    "name": "door",
                    "description": "An iron door.",
                    "location": "exit:loc_room:north",
                    "properties": {
                        "door": {"open": False, "locked": True, "lock_id": "lock_1"}
                    }
                },
                {
                    "id": "item_key",
                    "name": "key",
                    "description": "An iron key.",
                    "location": "player",
                    "properties": {"portable": True}
                }
            ],
            "locks": [
                {"id": "lock_1", "properties": {"opens_with": ["item_key"]}}
            ],
            "actors": {"player": {"id": "player", "location": "loc_room", "inventory": ["item_key"]}}
        })
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_unlock_door_with_key(self):
        """unlock command works with key in inventory."""
        action = {"verb": "unlock", "object": "door", "actor_id": "player"}
        result = handle_unlock(self.accessor, action)

        assert result.success
        door = self.accessor.get_item("door_1")
        assert door.door_locked is False

    def test_unlock_door_without_key_fails(self):
        """unlock command fails without correct key."""
        # Remove key from inventory
        player = self.accessor.get_actor("player")
        player.inventory.remove("item_key")

        action = {"verb": "unlock", "object": "door", "actor_id": "player"}
        result = handle_unlock(self.accessor, action)

        assert not result.success
```

#### 2.3 Movement Through Doors

```python
class TestMovementThroughDoorItems:
    """Test movement through door items."""

    def setup_method(self):
        """Create state with door between rooms."""
        self.state = load_game_state({
            "metadata": {"title": "Test"},
            "locations": [
                {
                    "id": "loc_room1",
                    "name": "Room 1",
                    "exits": {
                        "north": {"type": "door", "to": "loc_room2", "door_id": "door_1"}
                    }
                },
                {
                    "id": "loc_room2",
                    "name": "Room 2",
                    "exits": {
                        "south": {"type": "door", "to": "loc_room1", "door_id": "door_1"}
                    }
                }
            ],
            "items": [
                {
                    "id": "door_1",
                    "name": "door",
                    "description": "A door.",
                    "location": "exit:loc_room1:north",
                    "properties": {"door": {"open": False, "locked": False}}
                }
            ],
            "actors": {"player": {"id": "player", "location": "loc_room1"}}
        })
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_cannot_go_through_closed_door(self):
        """Movement blocked by closed door."""
        action = {"verb": "go", "direction": "north", "actor_id": "player"}
        result = handle_go(self.accessor, action)

        assert not result.success
        assert "closed" in result.message.lower() or "door" in result.message.lower()

    def test_can_go_through_open_door(self):
        """Movement allowed through open door."""
        door = self.accessor.get_item("door_1")
        door.door_open = True

        action = {"verb": "go", "direction": "north", "actor_id": "player"}
        result = handle_go(self.accessor, action)

        assert result.success
        player = self.accessor.get_actor("player")
        assert player.location == "loc_room2"

    def test_cannot_go_through_locked_door_even_if_open(self):
        """Movement blocked by locked door."""
        door = self.accessor.get_item("door_1")
        door.door_locked = True
        # Note: A locked door shouldn't be open, but test the check

        action = {"verb": "go", "direction": "north", "actor_id": "player"}
        result = handle_go(self.accessor, action)

        assert not result.success
```

### Phase 3: Migration Tests

Test conversion from old Door format to new Item format.

```python
class TestDoorMigration:
    """Test migrating old Door entities to Item format."""

    def test_load_legacy_doors_format(self):
        """Old 'doors' field is converted to items."""
        # Legacy format with separate doors field
        legacy_state = {
            "metadata": {"title": "Test"},
            "locations": [
                {
                    "id": "loc_room",
                    "name": "Room",
                    "exits": {
                        "north": {"type": "door", "to": "loc_other", "door_id": "door_1"}
                    }
                }
            ],
            "items": [],
            "doors": [
                {
                    "id": "door_1",
                    "locations": ["loc_room", "loc_other"],
                    "description": "A wooden door.",
                    "properties": {"open": False, "locked": False}
                }
            ],
            "actors": {"player": {"id": "player", "location": "loc_room"}}
        }

        state = load_game_state(legacy_state)

        # Door should be converted to item
        door_item = state.get_item("door_1")
        assert door_item is not None
        assert door_item.is_door
        assert door_item.name == "door"  # Default name
        assert door_item.description == "A wooden door."
        assert door_item.door_open is False
        assert door_item.door_locked is False

    def test_legacy_door_gets_exit_location(self):
        """Migrated door gets exit:location:direction format."""
        legacy_state = {
            "metadata": {"title": "Test"},
            "locations": [
                {
                    "id": "loc_room1",
                    "exits": {"east": {"type": "door", "to": "loc_room2", "door_id": "door_1"}}
                },
                {
                    "id": "loc_room2",
                    "exits": {"west": {"type": "door", "to": "loc_room1", "door_id": "door_1"}}
                }
            ],
            "items": [],
            "doors": [
                {
                    "id": "door_1",
                    "locations": ["loc_room1", "loc_room2"],
                    "description": "A door."
                }
            ],
            "actors": {}
        }

        state = load_game_state(legacy_state)
        door = state.get_item("door_1")

        # Location should reference first exit found
        assert door.location.startswith("exit:")
```

### Phase 4: Integration Tests

End-to-end tests with the full system.

```python
class TestDoorItemIntegration:
    """Integration tests for door items."""

    def test_full_door_interaction_sequence(self):
        """Test complete door interaction: examine, unlock, open, go through."""
        state = load_game_state({
            "metadata": {"title": "Test"},
            "locations": [
                {"id": "loc_a", "exits": {"north": {"type": "door", "to": "loc_b", "door_id": "door_1"}}},
                {"id": "loc_b", "exits": {"south": {"type": "door", "to": "loc_a", "door_id": "door_1"}}}
            ],
            "items": [
                {
                    "id": "door_1", "name": "door", "description": "A locked door.",
                    "location": "exit:loc_a:north",
                    "properties": {"door": {"open": False, "locked": True, "lock_id": "lock_1"}}
                },
                {"id": "key_1", "name": "key", "description": "A key.", "location": "loc_a", "properties": {"portable": True}}
            ],
            "locks": [{"id": "lock_1", "properties": {"opens_with": ["key_1"]}}],
            "actors": {"player": {"id": "player", "location": "loc_a", "inventory": []}}
        })

        handler = JSONProtocolHandler(state, behavior_manager=setup_behaviors())

        # Examine door
        response = handler.handle_message({"type": "command", "action": {"verb": "examine", "object": "door"}})
        assert response["success"]
        assert "locked" in response["message"].lower()

        # Try to open (should fail - locked)
        response = handler.handle_message({"type": "command", "action": {"verb": "open", "object": "door"}})
        assert not response["success"]

        # Take key
        response = handler.handle_message({"type": "command", "action": {"verb": "take", "object": "key"}})
        assert response["success"]

        # Unlock door
        response = handler.handle_message({"type": "command", "action": {"verb": "unlock", "object": "door"}})
        assert response["success"]

        # Open door
        response = handler.handle_message({"type": "command", "action": {"verb": "open", "object": "door"}})
        assert response["success"]

        # Go through
        response = handler.handle_message({"type": "command", "action": {"verb": "go", "direction": "north"}})
        assert response["success"]
        assert state.actors["player"].location == "loc_b"

    def test_secret_door_reveal_sequence(self):
        """Test hidden door: invisible until revealed."""
        state = load_game_state({
            "metadata": {"title": "Test"},
            "locations": [
                {"id": "loc_library", "exits": {"east": {"type": "door", "to": "loc_secret", "door_id": "door_secret"}}}
            ],
            "items": [
                {
                    "id": "door_secret", "name": "door",
                    "description": "A concealed door.",
                    "location": "exit:loc_library:east",
                    "properties": {"door": {"open": False}, "hidden": True}
                }
            ],
            "actors": {"player": {"id": "player", "location": "loc_library"}}
        })

        handler = JSONProtocolHandler(state, behavior_manager=setup_behaviors())

        # Query location - door should not appear
        response = handler.handle_message({"type": "query", "query_type": "location"})
        item_ids = [item["id"] for item in response["data"].get("items", [])]
        assert "door_secret" not in item_ids

        # Try to open - should fail (can't see it)
        response = handler.handle_message({"type": "command", "action": {"verb": "open", "object": "door"}})
        assert not response["success"]

        # Reveal the door (simulating a behavior trigger)
        state.get_item("door_secret").properties["hidden"] = False

        # Now query shows door
        response = handler.handle_message({"type": "query", "query_type": "location"})
        item_ids = [item["id"] for item in response["data"].get("items", [])]
        assert "door_secret" in item_ids

        # Can now open it
        response = handler.handle_message({"type": "command", "action": {"verb": "open", "object": "door"}})
        assert response["success"]
```

### Phase 5: Regression Tests

Ensure existing functionality isn't broken.

```python
class TestNoRegressions:
    """Verify existing item functionality still works."""

    def test_regular_items_unchanged(self):
        """Regular items (non-doors) work as before."""
        # ... test take, drop, examine, containers, etc. ...

    def test_container_items_unchanged(self):
        """Container items still work (put, take from, open/close)."""
        # ... test container functionality ...

    def test_actor_inventory_unchanged(self):
        """Actor inventory operations work as before."""
        # ... test inventory operations ...

    def test_location_queries_include_doors(self):
        """Location queries now include door items."""
        # ... verify backwards-compatible query responses ...
```

## Implementation Order

1. **Write Phase 1 tests** (door properties, visibility, find_accessible_item)
2. **Implement Item property accessors** (is_door, door_open, etc.)
3. **Write Phase 2 tests** (behavior handlers)
4. **Modify utility functions** (gather_location_contents, find_accessible_item)
5. **Modify behavior handlers** (handle_open, handle_close, handle_lock, handle_unlock, handle_go)
6. **Write Phase 3 tests** (migration)
7. **Implement migration in load_game_state**
8. **Write Phase 4 & 5 tests** (integration, regression)
9. **Remove Door dataclass and old code**
10. **Update validators**
11. **Migrate extended_game example**

## Files to Modify

| File | Changes |
|------|---------|
| `src/state_manager.py` | Remove Door dataclass, add Item door properties, migration logic |
| `src/state_accessor.py` | Remove get_door, add get_door_item, get_door_for_exit |
| `src/validators.py` | Update door validation to check items |
| `utilities/utils.py` | Modify gather_location_contents, find_accessible_item; remove door-specific functions |
| `behaviors/core/interaction.py` | Update handle_open, handle_close for door items |
| `behaviors/core/locks.py` | Update handle_lock, handle_unlock for door items |
| `behaviors/core/movement.py` | Update handle_go for door items |
| `behaviors/core/perception.py` | Update examine to handle door items naturally |
| `src/llm_protocol.py` | Remove door-specific query handling |
| `examples/extended_game/game_state.json` | Convert doors to items |

## Backwards Compatibility

### Game State Files

- **Legacy format**: `"doors": [...]` field with Door objects
- **New format**: No doors field, doors are items with `properties.door`
- **Migration**: `load_game_state()` converts legacy format automatically

### API

- `get_door()` removed - use `get_item()` or `get_door_item()`
- `find_door_with_adjective()` removed - use `find_accessible_item()`
- Query responses unchanged - doors appear in items list

## Success Criteria

1. All existing tests pass (with modifications for API changes)
2. Doors are visible from both connected locations
3. Hidden doors work for both exit-doors and decorative doors
4. Open/close/lock/unlock commands work with door items
5. Movement respects door open/locked state
6. Legacy game states load correctly via migration
7. Extended game example works with converted state
