# Observability Design

## Goal

Add a unified mechanism for controlling entity visibility via the `on_observe` behavior event. This allows game authors to create hidden items, secret doors, invisible NPCs, and hidden exits that can be revealed through gameplay.

## Use Cases

1. **Hidden item** - A key hidden under a rug, revealed when player searches
2. **Secret door** - A bookcase that's actually a door, hidden until examined closely
3. **Hidden exit** - A passage behind a waterfall, invisible until discovered
4. **Invisible NPC** - A ghost that only appears under certain conditions
5. **Conditional visibility** - Items visible only with special abilities (magic sight, etc.)

## Design

### Event: `on_observe`

A new behavior event invoked whenever any code attempts to detect/list an entity. The event handler decides whether the entity is currently observable.

**Signature:**
```python
def on_observe(entity, accessor, context) -> EventResult:
    """
    Called when something attempts to observe this entity.

    Args:
        entity: The entity being observed
        accessor: StateAccessor for querying game state
        context: Dict with:
            - actor_id: Who is attempting to observe
            - method: The verb triggering observation (e.g., "look", "examine", "search", "take")

    Returns:
        EventResult(allow=True) - entity is visible
        EventResult(allow=False) - entity is hidden
        EventResult(allow=True/False, message="...") - optional flavor text
    """
```

### Core Behavior: `behaviors/core/observability.py`

Provides the default `on_observe` implementation that checks `entity.states.get("hidden")`. This behavior is implicitly applied to all entities - game authors don't need to add it explicitly.

```python
def on_observe(entity, accessor, context) -> EventResult:
    """Default observability check - returns False if entity.states.hidden is True."""
    # Get states dict (handle entities that store states differently)
    states = getattr(entity, 'states', None)
    if states is None:
        states = entity.properties.get("states", {}) if hasattr(entity, 'properties') else {}

    if states.get("hidden", False):
        return EventResult(allow=False)

    return EventResult(allow=True)
```

### Helper Function: `is_observable()`

A utility function that invokes `on_observe` behaviors and returns the result.

```python
def is_observable(entity, accessor, behavior_manager, actor_id: str, method: str) -> tuple[bool, Optional[str]]:
    """
    Check if an entity is observable.

    Invokes on_observe behaviors on the entity. The core observability behavior
    is always invoked first (checking states.hidden), then any custom behaviors.

    Args:
        entity: Entity to check
        accessor: StateAccessor instance
        behavior_manager: BehaviorManager instance
        actor_id: Who is observing
        method: The verb/method of observation

    Returns:
        Tuple of (is_visible, message)
    """
```

### State Location

Hidden state is stored in `entity.states["hidden"]` (not `properties`), because:
- It's dynamic - can change during gameplay
- Behaviors modify it to reveal items: `entity.states["hidden"] = False`
- Consistent with other dynamic state like `lit`, `examine_count`, etc.

### Entity Support

All entity types support `on_observe`:

| Entity | Has `behaviors` | Has `states` | Changes Needed |
|--------|----------------|--------------|----------------|
| Item | Yes | Yes (via properties) | None |
| Actor | Yes | Yes (via properties) | None |
| Location | Yes | Yes (via properties) | None |
| ExitDescriptor | No | No | Add both |

### ExitDescriptor Changes

```python
@dataclass
class ExitDescriptor:
    """Exit descriptor for location connections."""
    type: str  # "open" or "door"
    to: Optional[str] = None
    door_id: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: List[str] = field(default_factory=list)  # NEW

    @property
    def states(self) -> Dict[str, Any]:  # NEW
        """Access states dict within properties."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return self.properties["states"]
```

### Integration Points

The `is_observable()` check replaces current `properties.hidden` checks at these locations:

1. **`_is_item_visible_in_location()`** - filters items when gathering location contents
2. **`find_accessible_item()`** - filters when searching for items by name
3. **`gather_location_contents()`** - filters actors, items in containers
4. **Exit listing** - filters exits when describing location or checking movement

### Implicit Core Behavior

The core observability behavior is invoked for all entities without requiring explicit registration. Implementation options:

**Option A: Check in `is_observable()` before invoking entity behaviors**
```python
def is_observable(entity, accessor, behavior_manager, actor_id, method):
    # Always check core observability first
    states = get_entity_states(entity)
    if states.get("hidden", False):
        return (False, None)

    # Then invoke any custom on_observe behaviors
    context = {"actor_id": actor_id, "method": method}
    result = behavior_manager.invoke_behavior(entity, "on_observe", accessor, context)
    ...
```

**Option B: Automatically prepend core behavior to all entities' behavior lists**

Option A is simpler and recommended - the core check is hardcoded in `is_observable()`, custom behaviors can override.

### Custom Behavior Example

A hidden item that reveals itself when searched:

```python
# behaviors/game/hidden_key.py

def on_observe(entity, accessor, context) -> EventResult:
    """Reveal the key when player searches."""
    if entity.states.get("hidden", False):
        if context["method"] == "search":
            entity.states["hidden"] = False
            return EventResult(allow=True, message="You find a small key hidden in a crack!")
        return EventResult(allow=False)
    return EventResult(allow=True)
```

## Migration

### Code Changes

1. `utilities/utils.py` - Replace `properties.hidden` checks with `is_observable()` calls
2. `src/state_manager.py` - Add `behaviors` and `states` to ExitDescriptor, update parsing/serialization
3. `behaviors/core/observability.py` - New file with default handler (minimal, since check is in `is_observable()`)

### Test Changes

Update tests that use `properties.hidden` to use `states.hidden`:
- `tests/test_entity_unification.py`
- `tests/state_manager/test_simplified_models.py`

### Game File Changes

None required for existing visible entities. Only entities that need to be hidden require `states: {hidden: true}`.

## Implementation Phases

### Phase 1: ExitDescriptor Enhancement

**Goal:** Add `behaviors` and `states` support to ExitDescriptor.

**Tasks:**
1. Add `behaviors: List[str]` field to ExitDescriptor dataclass
2. Add `states` property to ExitDescriptor (like Item has)
3. Update `_parse_exit()` to parse behaviors and states from JSON
4. Update `_serialize_exit()` to serialize behaviors and states
5. Update tests in `test_simplified_models.py` to use `states.hidden` instead of `properties.hidden`

**Tests:**
- ExitDescriptor can have behaviors list
- ExitDescriptor states property works (get/set)
- Parsing exit with behaviors from JSON works
- Serializing exit with behaviors to JSON works
- Round-trip: parse -> serialize -> parse preserves behaviors and states

**Progress:**
- All tasks completed
- Added `behaviors: List[str]` field to ExitDescriptor
- Added `states` property to ExitDescriptor (accesses `properties["states"]`)
- Updated `_parse_exit()` to extract `behaviors` as core field
- Updated `_serialize_exit()` to include `behaviors` if present
- Updated tests to use `states.hidden` pattern instead of `properties.hidden`
- All 885 tests pass

**Issues:**
- None encountered

---

### Phase 2: is_observable() Helper

**Goal:** Create the helper function that checks observability via behavior invocation.

**Tasks:**
1. Create `is_observable()` function in `utilities/utils.py`
2. Function checks `states.hidden` directly (core behavior logic)
3. Function invokes `on_observe` behaviors on entity if any exist
4. Returns `(visible: bool, message: Optional[str])`

**Tests:**
- Entity without states.hidden returns (True, None)
- Entity with states.hidden=False returns (True, None)
- Entity with states.hidden=True returns (False, None)
- Entity with custom on_observe behavior that returns allow=False is not visible
- Entity with custom on_observe behavior that returns message includes message
- Custom behavior can override core hidden check (reveal on search)

**Progress:**
- All tasks completed
- Added `is_observable()` function to `utilities/utils.py`
- Added `_get_entity_states()` helper function
- Function first invokes on_observe behaviors if entity has any
- Falls back to core hidden state check when no behavior handles the event
- Created comprehensive test suite in `tests/test_observability.py` (14 tests)
- All 899 tests pass

**Issues:**
- None encountered

---

### Phase 3: Integration - Items

**Goal:** Replace `properties.hidden` checks with `is_observable()` for items.

**Tasks:**
1. Update `_is_item_visible_in_location()` to use `is_observable()`
2. Update `find_accessible_item()` inventory check to use `is_observable()`
3. Update `gather_location_contents()` container contents to use `is_observable()`
4. Update docstrings to reference `states.hidden`
5. Update `test_entity_unification.py` to use `states.hidden`

**Tests:**
- Hidden item (states.hidden=True) not visible in location
- Hidden item not found by find_accessible_item
- Hidden item in container not listed
- Item with states.hidden=False is visible
- Item without states.hidden is visible (default)
- Revealing item (setting states.hidden=False) makes it visible

**Progress:**
- All tasks completed
- Updated `_is_item_visible_in_location()` to call `is_observable()` - added `actor_id` and `method` parameters
- Updated `find_accessible_item()` to use `is_observable()` for location items, inventory items, and container contents
- Updated `gather_location_contents()` to use `is_observable()` for items and container contents
- Updated `get_doors_in_location()` and `find_door_with_adjective()` to pass `actor_id` and `method`
- Updated docstrings to reference `states.hidden` and `is_observable()`
- Updated `test_entity_unification.py` TestHiddenDoors to use `states.hidden` instead of `properties.hidden`
- Added 4 integration tests in `tests/test_observability.py` (TestObservabilityIntegration class)
- All 903 tests pass

**Issues:**
- None encountered

---

### Phase 4: Integration - Actors

**Goal:** Add observability filtering for actors/NPCs.

**Tasks:**
1. Update `gather_location_contents()` actor loop to use `is_observable()`
2. Update `get_visible_actors_in_location()` if it exists and needs change

**Tests:**
- Hidden actor (states.hidden=True) not listed in location
- Actor with states.hidden=False is visible
- Actor without states.hidden is visible (default)

**Progress:**
- All tasks completed
- Added `states` property to Actor class (consistent with Item and ExitDescriptor)
- Updated `gather_location_contents()` actor loop to use `is_observable()` check
- Updated `get_visible_actors_in_location()` to use `is_observable()` check
- Added 6 actor-specific integration tests in `tests/test_observability.py`:
  - `test_hidden_actor_not_in_location_contents`
  - `test_visible_actor_in_location_contents`
  - `test_revealed_actor_becomes_visible`
  - `test_hidden_actor_not_in_get_visible_actors`
  - `test_actor_with_states_hidden_false_is_visible`
- All 908 tests pass

**Issues:**
- None encountered

---

### Phase 5: Integration - Exits

**Goal:** Add observability filtering for exits.

**Tasks:**
1. Identify where exits are listed (describe_location, movement code, llm_protocol)
2. Add `is_observable()` check when iterating exits
3. Handle the fact that ExitDescriptor doesn't have an `id` field (may need to pass direction as identifier)

**Tests:**
- Hidden exit (states.hidden=True) not shown in location description
- Hidden exit blocks movement (can't go that direction)
- Exit with states.hidden=False is visible
- Exit without states.hidden is visible (default)
- Revealing exit makes it visible and usable

**Progress:**
- All tasks completed
- Created `StateAccessor.get_visible_exits()` helper method that filters exits using `is_observable()`:
  - Central location for exit visibility filtering
  - Returns dict of direction -> ExitDescriptor for visible exits only
- Updated `llm_protocol.py:_query_location()` to use `get_visible_exits()`:
  - Single call to get visible exits, used by both doors and exits sections
  - Removed redundant inline `is_observable()` checks
- Updated `behaviors/core/exits.py:handle_go()` to use `get_visible_exits()`:
  - Checks `direction not in visible_exits` instead of accessing `location.exits` directly
  - Hidden exits appear as if they don't exist to the movement handler
- Added 6 integration tests in `tests/test_observability.py` (TestHiddenExitsIntegration class):
  - `test_hidden_exit_not_in_query_response`
  - `test_visible_exit_in_query_response`
  - `test_hidden_exit_blocks_movement`
  - `test_visible_exit_allows_movement`
  - `test_revealed_exit_becomes_usable`
  - `test_exit_without_hidden_state_is_visible`
- All 914 tests pass

**Issues:**
- None encountered

---

### Phase 6: Documentation and Cleanup

**Goal:** Document the feature and clean up any remaining issues.

**Tasks:**
1. Update relevant docs (entity_behaviors.md, etc.)
2. Add example hidden item to example game
3. Remove any obsolete `properties.hidden` references from documentation
   - Note: Source code (`src/`, `utilities/`, `behaviors/`) already clean as of Phase 3
   - Documentation files still reference old pattern: `docs/hidden_items.md`, `docs/entity_unification.md`, `docs/behavior_refactoring.md`
4. Verify all tests pass

**Tests:**
- Full integration test: hidden item revealed by search behavior

**Progress:**
- All tasks completed
- Updated `docs/entity_unification.md` - changed `properties["hidden"]` to `states["hidden"]` in code examples
- Updated `docs/hidden_items.md` - comprehensive update to use `states.hidden` pattern throughout:
  - Updated JSON examples to show `states: {hidden: true}` inside `properties`
  - Updated code examples to use `item.states.get("hidden")` and `item.states["hidden"] = False`
  - Updated reveal mechanism to use `states` instead of `properties`
  - Updated testing strategy to reference actual test file
- Added hidden item example to `examples/simple_game_state.json`:
  - `item_hidden_gem` - a ruby concealed beneath the chest in the treasure room
  - Demonstrates proper `states.hidden` usage in game data
- All 914 tests pass

**Issues:**
- None encountered
