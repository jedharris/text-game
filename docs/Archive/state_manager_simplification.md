# State Manager Simplification Design

## Goals

1. **Simplicity** - Minimal core models with clear responsibilities
2. **Extensibility** - Game developers can add features without modifying state_manager
3. **Future-proofing** - New features don't require loader/serializer/validator changes

## Current Problems

Every new feature (e.g., `is_surface`, `pushable`) requires changes to:
- `models.py` - Add typed field
- `loader.py` - Parse the field
- `serializer.py` - Write the field
- `validators.py` - Validate references
- Tests for all of the above

This couples feature development to infrastructure code.

**Current size**: 1,316 lines across 6 files.

## Design Principle

**Separate structural data from feature data.**

- **Structural data**: What the engine needs to function (identity, location, connectivity)
- **Feature data**: What behaviors need to implement game mechanics

The state_manager handles structural data. Behaviors own their feature data.

---

## Core Models

### Entity Base Pattern

All entities share:
- `id: str` - Global unique identifier
- `name: str` - Display name
- `description: str` - Display description
- `properties: Dict[str, Any]` - All feature-specific data
- `behaviors: Dict[str, str]` - Event handlers

### Item

```python
@dataclass
class Item:
    """Item in the game world."""
    id: str
    name: str
    description: str
    location: str  # Structural: where this item exists
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: Dict[str, str] = field(default_factory=dict)
```

Properties previously typed as fields:
- `type` → `properties["type"]`
- `portable` → `properties["portable"]`
- `pushable` → `properties["pushable"]`
- `provides_light` → `properties["provides_light"]`
- `container` → `properties["container"]` (nested dict)
- `states` → `properties["states"]` (nested dict)

### Location

```python
@dataclass
class Location:
    """Location in the game world."""
    id: str
    name: str
    description: str
    exits: Dict[str, ExitDescriptor]  # Structural: connectivity
    items: List[str] = field(default_factory=list)  # Structural: containment
    npcs: List[str] = field(default_factory=list)   # Structural: containment
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: Dict[str, str] = field(default_factory=dict)
```

Properties:
- `tags` → `properties["tags"]`
- `llm_context` → `properties["llm_context"]`

### Door

```python
@dataclass
class Door:
    """Door connecting locations."""
    id: str
    locations: Tuple[str, ...]  # Structural: what it connects
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: Dict[str, str] = field(default_factory=dict)
```

Properties:
- `name` → `properties["name"]` (optional, defaults to "door")
- `description` → `properties["description"]`
- `open` → `properties["open"]`
- `locked` → `properties["locked"]`
- `lock_id` → `properties["lock_id"]`
- `one_way` → `properties["one_way"]`

Note: `name` and `description` move to properties for doors since they're optional display data.

### NPC

```python
@dataclass
class NPC:
    """Non-player character."""
    id: str
    name: str
    description: str
    location: str  # Structural: where this NPC exists
    inventory: List[str] = field(default_factory=list)  # Structural: containment
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: Dict[str, str] = field(default_factory=dict)
```

Properties:
- `dialogue` → `properties["dialogue"]`
- `states` → `properties["states"]`

### Lock

```python
@dataclass
class Lock:
    """Lock mechanism."""
    id: str
    properties: Dict[str, Any] = field(default_factory=dict)
```

Properties:
- `opens_with` → `properties["opens_with"]`
- `auto_unlock` → `properties["auto_unlock"]`
- `description` → `properties["description"]`
- `fail_message` → `properties["fail_message"]`

Note: Locks have no behaviors since they're passive data checked by door/container behaviors.

### ExitDescriptor

```python
@dataclass
class ExitDescriptor:
    """Exit descriptor for location connections."""
    type: str  # "open" or "door" - Structural: exit behavior
    to: Optional[str] = None  # Structural: connectivity
    door_id: Optional[str] = None  # Structural: door reference
    properties: Dict[str, Any] = field(default_factory=dict)
```

Properties:
- `description` → `properties["description"]`
- `hidden` → `properties["hidden"]`
- `conditions` → `properties["conditions"]`
- `on_fail` → `properties["on_fail"]`

### PlayerState

```python
@dataclass
class PlayerState:
    """Player state information."""
    location: str  # Structural
    inventory: List[str] = field(default_factory=list)  # Structural
    properties: Dict[str, Any] = field(default_factory=dict)
```

Properties:
- `flags` → `properties["flags"]`
- `stats` → `properties["stats"]`

### GameState

```python
@dataclass
class GameState:
    """Complete game state."""
    metadata: Metadata
    locations: List[Location] = field(default_factory=list)
    doors: List[Door] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    locks: List[Lock] = field(default_factory=list)
    npcs: List[NPC] = field(default_factory=list)
    player: Optional[PlayerState] = None
    extra: Dict[str, Any] = field(default_factory=dict)
```

---

## JSON Format

The JSON format stays mostly the same from a game developer's perspective. The loader interprets fields into the properties dict.

### Item Example

```json
{
    "id": "chest",
    "name": "Wooden Chest",
    "description": "A sturdy wooden chest with iron bands.",
    "location": "loc_1",
    "type": "container",
    "portable": false,
    "container": {
        "is_surface": false,
        "capacity": 10,
        "locked": true,
        "lock_id": "lock_1"
    },
    "behaviors": {
        "on_open": "core.containers:on_open_chest"
    }
}
```

After loading:
```python
item.id == "chest"
item.name == "Wooden Chest"
item.description == "A sturdy wooden chest with iron bands."
item.location == "loc_1"
item.properties == {
    "type": "container",
    "portable": False,
    "container": {
        "is_surface": False,
        "capacity": 10,
        "locked": True,
        "lock_id": "lock_1"
    }
}
item.behaviors == {"on_open": "core.containers:on_open_chest"}
```

---

## Generic Loader

The loader becomes simple and generic:

```python
def parse_item(raw: Dict[str, Any]) -> Item:
    """Parse item from JSON dict."""
    # Core structural fields
    core_fields = {'id', 'name', 'description', 'location', 'behaviors'}

    return Item(
        id=raw['id'],
        name=raw.get('name', ''),
        description=raw.get('description', ''),
        location=raw.get('location', ''),
        properties={k: v for k, v in raw.items() if k not in core_fields},
        behaviors=raw.get('behaviors', {})
    )
```

This loader never needs to change when new properties are added.

### Location Loader

```python
def parse_location(raw: Dict[str, Any]) -> Location:
    """Parse location from JSON dict."""
    core_fields = {'id', 'name', 'description', 'exits', 'items', 'npcs', 'behaviors'}

    # Parse exits (structural core + properties)
    exits = {}
    exit_core_fields = {'type', 'to', 'door_id'}
    for direction, exit_data in raw.get('exits', {}).items():
        exits[direction] = ExitDescriptor(
            type=exit_data.get('type', 'open'),
            to=exit_data.get('to'),
            door_id=exit_data.get('door_id'),
            properties={k: v for k, v in exit_data.items() if k not in exit_core_fields}
        )

    return Location(
        id=raw['id'],
        name=raw.get('name', ''),
        description=raw.get('description', ''),
        exits=exits,
        items=raw.get('items', []),
        npcs=raw.get('npcs', []),
        properties={k: v for k, v in raw.items() if k not in core_fields},
        behaviors=raw.get('behaviors', {})
    )
```

---

## Generic Serializer

```python
def serialize_item(item: Item) -> Dict[str, Any]:
    """Serialize item to JSON dict."""
    result = {
        'id': item.id,
        'name': item.name,
        'description': item.description,
        'location': item.location,
    }

    # Merge properties back to top level
    result.update(item.properties)

    if item.behaviors:
        result['behaviors'] = item.behaviors

    return result
```

This serializer never needs to change when new properties are added.

---

## Property Access Patterns

### Direct Access

```python
# Get with default
portable = item.properties.get("portable", False)
capacity = item.properties.get("container", {}).get("capacity", 0)

# Check existence
if "container" in item.properties:
    ...

# Modify
item.properties["portable"] = True
item.properties.setdefault("container", {})["locked"] = False
```

### Behavior-Provided Helpers

Property helpers belong in the behaviors that own those properties, not in state_manager:

```python
# behaviors/core/take.py
def is_portable(item: Item) -> bool:
    """Check if item can be picked up."""
    return item.properties.get("portable", False)

# behaviors/core/containers.py
def is_container(item: Item) -> bool:
    """Check if item is a container."""
    return "container" in item.properties

def get_capacity(item: Item) -> int:
    """Get container capacity (0 = unlimited)."""
    return item.properties.get("container", {}).get("capacity", 0)

def is_open(item: Item) -> bool:
    """Check if container is open."""
    return item.properties.get("container", {}).get("open", False)

# behaviors/core/locks.py
def is_locked(entity: Union[Item, Door]) -> bool:
    """Check if entity is locked."""
    if isinstance(entity, Door):
        return entity.properties.get("locked", False)
    return entity.properties.get("container", {}).get("locked", False)
```

This keeps property knowledge with the behaviors that define those properties.

---

## Validation Architecture

### Core Validators (in state_manager)

The state_manager validates only structural integrity:

1. **ID uniqueness** - All IDs globally unique
2. **Reserved IDs** - "player" is reserved
3. **Reference existence** - All referenced IDs exist
4. **Reference types** - References point to correct entity types
   - Exit `to` → location
   - Exit `door_id` → door
   - Door `locations` → locations
   - Item `location` → location, item, npc, or player
5. **Containment cycles** - No circular containment
6. **Metadata validity** - start_location exists

### Reference Validation in Properties

Some structural references live in properties (e.g., `lock_id` in doors and containers). The structural validator must validate these references even though they're in properties:

- Door `properties["lock_id"]` → must reference a lock
- Container `properties["container"]["lock_id"]` → must reference a lock
- Lock `properties["opens_with"]` → must reference items

This is acceptable because these are structural references (they define relationships between entities), even though the containing data is in properties.

---

## Benefits

### For Game Developers

- Add any property to any entity without engine changes
- Properties are self-documenting via behavior schemas
- No need to understand state_manager internals

### For Engine Development

- state_manager becomes stable infrastructure
- New features are localized to behavior modules
- Clear separation of concerns

### For Testing

- state_manager tests only test structural integrity
- Property tests live with their behavior modules
- Less coupling between test suites

---

## Example: Adding a New Feature

**Scenario**: Add "flammable" property for items that can catch fire.

### Before (Current Architecture)

1. Add `flammable: bool = False` to Item dataclass
2. Update loader to parse `flammable`
3. Update serializer to write `flammable`
4. Add validation if needed
5. Update test fixtures
6. Write tests for all of the above
7. Implement fire behavior

### After (New Architecture)

1. Create `behaviors/core/fire.py`:

```python
PROPERTY_SCHEMA = {
    "flammable": {
        "type": "bool",
        "default": False,
        "description": "Whether item can catch fire"
    },
    "on_fire": {
        "type": "bool",
        "default": False,
        "description": "Whether item is currently burning"
    }
}

VOCABULARY = {
    "verbs": [
        {"word": "ignite", "synonyms": ["light", "burn"]}
    ]
}

def on_ignite(event):
    item = event.game_state.get_item(event.direct_object)
    if not item.properties.get("flammable", False):
        return EventResult(allow=False, message="That won't burn.")
    item.properties["on_fire"] = True
    return EventResult(allow=True, message="It catches fire!")
```

2. Add to game state JSON:

```json
{
    "id": "torch",
    "name": "Wooden Torch",
    "description": "A torch wrapped in oil-soaked cloth.",
    "location": "loc_1",
    "flammable": true,
    "behaviors": {
        "on_ignite": "core.fire:on_ignite"
    }
}
```

**No changes to state_manager needed.**

---

## Considerations

### Type Safety

Moving to properties dict loses IDE autocomplete and type checking. Mitigations:

1. **Helper functions** provide typed access
2. **Property schemas** provide runtime validation
3. **Documentation** in behavior modules

### Performance

Dict access is slightly slower than attribute access. This is negligible for game state operations.

### Backward Compatibility

Existing game files work unchanged - the loader interprets old fields into properties.

---

## Module Consolidation

The simplified design allows significant consolidation of the state_manager modules.

### Current Structure (1,316 lines)

| Module | Lines | Purpose |
|--------|-------|---------|
| models.py | 271 | Dataclass definitions |
| loader.py | 359 | JSON parsing |
| serializer.py | 201 | JSON writing |
| validators.py | 422 | Validation rules |
| exceptions.py | 41 | Exception classes |
| __init__.py | 22 | Exports |

### Simplified Structure (~500 lines)

Consolidate into two files:

**`state_manager.py`** (~350 lines)
- Exceptions
- All dataclass models (minimal core fields)
- Generic loader
- Generic serializer
- GameState convenience methods

**`validators.py`** (~150 lines)
- Structural validation only
- Pluggable property validation (future)

### Benefits of Consolidation

- **~65% code reduction** (1,316 → ~500 lines)
- **Single import** for most use cases: `from src.state_manager import GameState, load_game_state, save_game_state`
- **Clear separation** between IO and validation
- **No modification needed** when adding new properties

### Combined Module Structure

```python
"""
Game state management - models, loading, and serialization.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, IO

# === Exceptions ===

class StateManagerError(Exception):
    """Base exception for state manager errors."""
    pass

class FileLoadError(StateManagerError):
    """Error loading file."""
    pass

class SchemaError(StateManagerError):
    """Invalid JSON schema."""
    pass

class ValidationError(StateManagerError):
    """Validation failed."""
    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.errors = errors or []

# === Models ===

@dataclass
class Metadata:
    title: str
    author: str = ""
    version: str = "1.0"
    description: str = ""
    start_location: str = ""

@dataclass
class ExitDescriptor:
    type: str
    to: Optional[str] = None
    door_id: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Location:
    id: str
    name: str
    description: str
    exits: Dict[str, ExitDescriptor] = field(default_factory=dict)
    items: List[str] = field(default_factory=list)
    npcs: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: Dict[str, str] = field(default_factory=dict)

@dataclass
class Door:
    id: str
    locations: Tuple[str, ...]
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: Dict[str, str] = field(default_factory=dict)

@dataclass
class Item:
    id: str
    name: str
    description: str
    location: str
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: Dict[str, str] = field(default_factory=dict)

@dataclass
class Lock:
    id: str
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NPC:
    id: str
    name: str
    description: str
    location: str
    inventory: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: Dict[str, str] = field(default_factory=dict)

@dataclass
class PlayerState:
    location: str
    inventory: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GameState:
    metadata: Metadata
    locations: List[Location] = field(default_factory=list)
    doors: List[Door] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    locks: List[Lock] = field(default_factory=list)
    npcs: List[NPC] = field(default_factory=list)
    player: Optional[PlayerState] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    # Convenience methods (get_item, get_location, move_item, etc.)
    ...

# === Generic Loader ===

def load_game_state(source: Union[str, Path, IO, Dict]) -> GameState:
    """Load game state from file path, file-like object, or dict."""
    ...

def _parse_entity(raw: Dict, core_fields: set) -> Tuple[Dict, Dict, Dict]:
    """Extract core fields, properties, and behaviors from raw dict."""
    core = {k: raw.get(k) for k in core_fields if k in raw}
    behaviors = raw.get('behaviors', {})
    properties = {k: v for k, v in raw.items()
                  if k not in core_fields and k != 'behaviors'}
    return core, properties, behaviors

# === Generic Serializer ===

def save_game_state(state: GameState, destination: Union[str, Path, IO], ...):
    """Save game state to file."""
    ...

def _serialize_entity(entity, core_fields: List[str]) -> Dict:
    """Serialize entity: core fields + properties merged."""
    result = {f: getattr(entity, f) for f in core_fields}
    result.update(entity.properties)
    if entity.behaviors:
        result['behaviors'] = entity.behaviors
    return result
```

---

## Summary

| Component | Responsibility |
|-----------|----------------|
| **state_manager.py** | Models, exceptions, generic load/save |
| **validators.py** | Structural integrity validation |
| **behaviors/** | Property schemas, vocabulary, event handlers |

This architecture:
- Reduces state_manager from 1,316 to ~500 lines
- Makes state_manager a stable foundation that rarely needs modification
- Allows unlimited extension through behavior modules
- Provides single-import convenience for consumers

---

## Implementation Plan

### Overview

The implementation follows test-driven development: write tests first, then implement to pass the tests. Each phase builds on the previous, maintaining a working system throughout.

### Phase 1: Create New Simplified Module (Tests First)

**Goal**: Create `state_manager_v2.py` with properties-based models alongside existing code.

#### 1.1 Tests Written

Tests are in `tests/state_manager/test_simplified_models.py`:

- `TestSimplifiedItem` - Core fields only, properties from JSON, container as property
- `TestSimplifiedLocation` - Core fields, tags as property
- `TestSimplifiedDoor` - Core fields (id, locations), state in properties
- `TestSimplifiedNPC` - Core fields, dialogue/states as properties
- `TestSimplifiedLock` - Minimal core (id only), opens_with in properties
- `TestSimplifiedPlayerState` - Core fields (location, inventory), flags/stats in properties
- `TestGenericLoader` - Loading items, doors, containers with properties
- `TestGenericSerializer` - Merging properties to top level, round-trip preservation
- `TestGameStateConvenienceMethods` - get_item, move_item
- `TestBackwardCompatibility` - Loading valid_world.json fixture

#### 1.2 Implement New Module

After tests are written, implement `src/state_manager/state_manager_v2.py` to pass all tests.

**Implementation tasks**:
1. Define exceptions
2. Define dataclasses with properties field
3. Implement generic `_parse_entity()` helper
4. Implement `load_game_state()` using generic parsing
5. Implement generic `_serialize_entity()` helper
6. Implement `game_state_to_dict()` and `save_game_state()`
7. Implement GameState convenience methods

---

### Phase 2: Structural Validators

**Goal**: Implement validators that check only structural integrity.

#### 2.1 Tests Written

Tests are in `tests/state_manager/test_simplified_validators.py`:

- `TestStructuralValidation` - 26 test cases covering:
  - Duplicate ID detection (across types and within same type)
  - Reserved "player" ID detection
  - Invalid exit references (locations, doors, missing door_id)
  - Invalid item locations (nonexistent, wrong type, valid player/container/NPC)
  - Container cycle detection (2-item and 3-item cycles)
  - Invalid metadata start_location
  - Invalid player state (location, inventory)
  - Invalid door/lock references
  - Valid simple and complex states
- `TestValidationErrorAggregation` - Multiple errors reported together
- `TestValidateGameStateFunction` - Direct validation of loaded state

#### 2.2 Implement Validators

Create `src/state_manager/validators_v2.py` (~150 lines) with:
- `build_global_id_registry()`
- `validate_references()`
- `validate_item_locations()`
- `validate_container_cycles()`
- `validate_metadata()`
- `validate_player_state()`
- `validate_game_state()`

---

### Phase 3: Integration and Migration

**Goal**: Replace old state_manager with new implementation.

#### 3.1 Migration Tests

Migration tests are included in `tests/state_manager/test_simplified_models.py`:

- `TestBackwardCompatibility.test_load_valid_world_fixture` - Loads existing fixture, verifies properties populated
- `TestBackwardCompatibility.test_serialized_output_matches_input` - Round-trip preserves all data

#### 3.2 Update Imports

1. Rename `state_manager_v2.py` to `state_manager.py`
2. Rename `validators_v2.py` to `validators.py`
3. Update `__init__.py` exports
4. Delete old modules (models.py, loader.py, serializer.py, exceptions.py)

#### 3.3 Update Consumers

Update all code that accesses typed fields to use properties:

```python
# game_engine.py, json_protocol.py, behaviors/*.py

# Before
if item.portable:

# After
if item.properties.get("portable", False):

# Or import from the behavior that owns the property
from src.behaviors.core.take import is_portable
if is_portable(item):
```

---

### Phase 4: Update Existing Tests

**Goal**: Modify existing tests to work with new structure.

#### 4.1 Test Updates Required

| Test File | Changes Needed |
|-----------|----------------|
| test_models.py | Remove ContainerInfo tests, update to use properties |
| test_loader.py | Update assertions to check properties |
| test_serializer.py | Update assertions |
| test_validators.py | Minor updates for new validator module |
| test_regressions.py | Should mostly work as-is |

#### 4.2 Example Test Updates

```python
# test_models.py - OLD
def test_TM002_container_info_structure(self):
    container = ContainerInfo(locked=True, capacity=10)
    item = Item(..., container=container)
    self.assertTrue(item.container.locked)

# test_models.py - NEW
def test_TM002_container_in_properties(self):
    item = Item(
        id="chest", name="Chest", description="A chest", location="loc_1",
        properties={"container": {"locked": True, "capacity": 10}}
    )
    self.assertTrue(item.properties["container"]["locked"])
```

---

### Implementation Timeline

| Phase | Description | Test Files | Implementation Files |
|-------|-------------|------------|---------------------|
| 1 | New models + loader/serializer | test_simplified_models.py | state_manager_v2.py |
| 2 | Structural validators | test_simplified_validators.py | validators_v2.py |
| 3 | Integration | test migration cases | rename files, update imports |
| 4 | Update tests | modify existing tests | - |

### Success Criteria

1. All new tests pass
2. All existing tests pass (after updates)
3. Game runs correctly with existing game state files
4. No typed field access in state_manager (properties accessed via dict)
5. Total state_manager code < 600 lines
