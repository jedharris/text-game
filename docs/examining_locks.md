# Design: Examining Locks

## Use Cases and Goals

**Use Cases:**
1. Player wants to examine a lock to learn about it (description, traits for LLM narration)
2. Player wants to identify which lock is on which door before attempting to unlock
3. Player in a location with multiple locked doors wants to examine a specific lock by direction

**Goals:**
- Enable examining locks as first-class entities with full LLM context support
- Use consistent patterns that work with the unified vocabulary system
- Support disambiguation when multiple locks are visible
- Follow existing entity lookup patterns (items → doors → exits → locks)

## Supported Command Patterns

| Pattern | Example | Parser Output |
|---------|---------|---------------|
| `VERB + NOUN` | "examine lock" | `verb=examine`, `object=lock` |
| `VERB + DIRECTION + NOUN` | "examine east lock" | `verb=examine`, `direction=east`, `object=lock` |
| `VERB + NOUN + PREP + NOUN` | "examine lock in door" | `verb=examine`, `object=lock`, `prep=in`, `indirect_object=door` |
| `VERB + NOUN + PREP + ADJ + NOUN` | "examine lock in iron door" | `verb=examine`, `object=lock`, `prep=in`, `indirect_adj=iron`, `indirect_object=door` |

All four patterns use existing parser patterns. No parser changes required.

## Design

### 1. Add "lock" to Vocabulary

**File:** `src/vocabulary_generator.py`

Extend `extract_nouns_from_state()` to extract lock names from `state.locks`:

```python
# Extract lock names
for lock in state.locks:
    name = getattr(lock, 'name', None) or 'lock'
    if name and name not in seen_words:
        nouns.append({"word": name})
        seen_words.add(name)
```

This follows the existing pattern for items and actors, using the unified vocabulary system.

### 2. Add Lock Lookup Utility

**File:** `utilities/utils.py`

Add a new function `find_lock_by_context()`:

```python
def find_lock_by_context(
    accessor,
    direction: Optional[str] = None,
    door_name: Optional[str] = None,
    door_adjective: Optional[str] = None,
    location_id: Optional[str] = None
) -> Optional[Any]:
    """
    Find a lock based on context (direction or door specification).

    Args:
        accessor: StateAccessor instance
        direction: Direction to find door with lock (e.g., "east")
        door_name: Name of door to find lock on
        door_adjective: Adjective to disambiguate door
        location_id: Current location ID

    Returns:
        Lock entity if found, None otherwise
    """
```

**Logic:**
1. If `direction` provided: Find exit in that direction → get door_id → get lock from door
2. If `door_name` provided: Find door by name (with optional adjective) → get lock_id → get lock
3. If neither: Find all visible doors with locks, return lock if exactly one, else None (ambiguous)

### 3. Extend handle_examine

**File:** `behaviors/core/perception.py`

After the exit lookup block, add lock lookup:

```python
# If no exit found, try to find a lock
if object_name matches "lock":
    lock = find_lock_by_context(
        accessor,
        direction=direction,
        door_name=indirect_object,
        door_adjective=indirect_adjective,
        location_id=location.id
    )

    if lock:
        data = {}
        if lock.llm_context:
            data["llm_context"] = lock.llm_context

        return HandlerResult(
            success=True,
            message=lock.description,
            data=data if data else None
        )
```

The `object_name matches "lock"` check uses the WordEntry's canonical form or synonyms, consistent with how items are matched.

### 4. Accessor Method for Lock Retrieval

**File:** `src/state_accessor.py`

Add method to retrieve lock by ID:

```python
def get_lock(self, lock_id: str) -> Optional[Lock]:
    """Get a lock by ID."""
    for lock in self.game_state.locks:
        if lock.id == lock_id:
            return lock
    return None
```

## Pattern Handling Details

### Pattern 1: "examine lock"

**Parsed as:** `verb=examine`, `object=lock`

**Handler behavior:**
1. `object_name` = "lock", no direction, no indirect_object
2. Call `find_lock_by_context(accessor, location_id=location.id)`
3. Function finds all visible doors with locks
4. If exactly one lock visible, return it
5. If multiple locks, return error: "Which lock do you mean?"
6. If no locks visible, return error: "You don't see any lock here."

### Pattern 2: "examine east lock"

**Parsed as:** `verb=examine`, `direction=east`, `object=lock`

**Handler behavior:**
1. `object_name` = "lock", `direction` = "east"
2. Call `find_lock_by_context(accessor, direction="east", location_id=location.id)`
3. Function finds exit in "east" direction
4. Gets door_id from exit, finds door
5. Gets lock_id from door, finds and returns lock
6. If no exit/door/lock in that direction, return error

### Pattern 3: "examine lock in door"

**Parsed as:** `verb=examine`, `object=lock`, `prep=in`, `indirect_object=door`

**Handler behavior:**
1. `object_name` = "lock", `indirect_object` = "door"
2. Call `find_lock_by_context(accessor, door_name="door", location_id=location.id)`
3. Function finds door by name
4. Gets lock_id from door, finds and returns lock
5. If door has no lock, return error: "The door has no lock."

### Pattern 4: "examine lock in iron door"

**Parsed as:** `verb=examine`, `object=lock`, `prep=in`, `indirect_adj=iron`, `indirect_object=door`

**Handler behavior:**
1. `object_name` = "lock", `indirect_object` = "door", `indirect_adjective` = "iron"
2. Call `find_lock_by_context(accessor, door_name="door", door_adjective="iron", location_id=location.id)`
3. Function finds door matching name and adjective
4. Gets lock_id from door, finds and returns lock

## Error Messages

| Condition | Message |
|-----------|---------|
| No locks visible in location | "You don't see any lock here." |
| Multiple locks, no disambiguation | "Which lock do you mean?" |
| Direction has no exit | "There's no exit to the {direction}." |
| Exit has no door | "There's no door to the {direction}." |
| Door has no lock | "The {door_name} has no lock." |
| Door not found by name | "You don't see any {door_name} here." |

## Testing Strategy

1. **Unit tests for `find_lock_by_context()`** - test each lookup path
2. **Unit tests for `handle_examine` with lock** - test all four patterns
3. **Integration tests** - test full command flow from parser through handler

Test file: `tests/test_examine_locks.py`

## Implementation Phases

### Phase 1: Infrastructure
- Add `get_lock()` to StateAccessor
- Add "lock" extraction to vocabulary_generator
- Add `find_lock_by_context()` utility function

### Phase 2: Handler Integration
- Extend `handle_examine` to check for locks after exits
- Extract indirect_object and indirect_adjective from action

### Phase 3: Testing
- Unit tests for utility function
- Integration tests for all four patterns
- Edge case tests (no lock, multiple locks, etc.)

---

## Implementation Notes

**Status: Completed**

### Files Modified

1. **`src/vocabulary_generator.py`** (lines 49-54)
   - Added lock name extraction from `state.locks`
   - Uses `getattr(lock, 'name', None) or 'lock'` to handle locks with or without explicit names

2. **`utilities/utils.py`** (lines 892-962)
   - Added `find_lock_by_context()` function with three search strategies:
     - Strategy 1: Find lock via direction (exit → door → lock)
     - Strategy 2: Find lock via door name (with optional adjective)
     - Strategy 3: Auto-select if exactly one visible door has a lock

3. **`behaviors/core/perception.py`** (lines 257-302)
   - Extended `handle_examine` with lock lookup after exit lookup
   - Uses `name_matches(object_name, "lock")` for vocabulary-aware matching
   - Extracts `indirect_object` and `indirect_adjective` from action for prepositional patterns
   - Includes `llm_context` in response data for LLM narration

4. **`src/state_accessor.py`** (lines 111-124)
   - `get_lock()` method already existed - no changes needed

### Tests Added

**`tests/test_examine_locks.py`** - 15 new tests:

- `TestExamineLockBasic` (2 tests): Basic "examine lock" with/without lock present
- `TestExamineLockWithDirection` (3 tests): "examine east lock" patterns
- `TestExamineLockPrepositional` (3 tests): "examine lock in door" patterns
- `TestExamineLockLLMContext` (1 test): Verify llm_context is included in response
- `TestFindLockByContext` (6 tests): Unit tests for the utility function

### Error Messages Implemented

| Condition | Message |
|-----------|---------|
| Direction with no lock | "There's no lock to the {direction}." |
| Door specified with no lock | "You don't see any lock on that." |
| No locks visible | "You don't see any lock here." |

### Test Results

All 1017 tests pass (15 new tests added for lock examination).
