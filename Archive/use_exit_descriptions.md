# Making Exits First-Class Entities

## Motivation

We should always maximize:
- **Author capability** - Game authors can create rich, examinable exits with descriptions and traits
- **Code cleanliness** - Exits follow the same patterns as other entities
- **Player agency** - Players can examine exits directly, not just navigate through them

Exit descriptions were recently added (`llm_context` with traits and state_variants), but they're only visible to the narrator LLM during location queries. Players cannot directly examine exits like they can examine items, doors, or actors.

## Current State

### What Works
- Exits have `llm_context` with traits and state_variants in game state
- Location queries return exit `llm_context` to the narrator
- Narrator can use exit traits when describing movement or locations

### What Doesn't Work
- `examine stairs` → "You don't see any stairs here"
- `examine east exit` → Not recognized
- `examine up` → Parser may not recognize direction as examinable object
- Exits cannot be queried as individual entities

### Why It Doesn't Work

Exits are **structural connectors**, not first-class entities:

| Aspect | Items/Doors/Actors | Exits |
|--------|-------------------|-------|
| Has unique ID | Yes | No (keyed by direction) |
| Has `name` field | Yes | No |
| Has `description` field | Yes | No |
| Can be examined | Yes | No |
| Can be queried individually | Yes | No |
| Stored in | Top-level lists/dicts | Nested in `Location.exits` |

## Solution: Make Exits First-Class Entities

### Phase 1: Add Required Fields to ExitDescriptor

**File:** `src/state_manager.py`

Add `name` and `description` fields to `ExitDescriptor`:

```python
@dataclass
class ExitDescriptor:
    """Exit descriptor for location connections."""
    type: str  # "open" or "door"
    to: Optional[str] = None
    door_id: Optional[str] = None
    name: Optional[str] = None  # NEW: e.g., "spiral staircase", "stone archway"
    description: Optional[str] = None  # NEW: prose description for examine
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: List[str] = field(default_factory=list)
```

**Backward Compatibility:** Both fields are optional with `None` default. Existing game states without these fields will continue to work.

**Work Completed:** Added `name: Optional[str] = None` and `description: Optional[str] = None` fields to `ExitDescriptor` in `src/state_manager.py`. All 49 state manager tests pass.

### Phase 2: Add Exit Lookup Utility

**File:** `utilities/utils.py`

Create `find_exit_by_name()` function:

```python
def find_exit_by_name(
    accessor: StateAccessor,
    name: str,
    actor_id: str,
    adjective: Optional[str] = None
) -> Optional[Tuple[str, ExitDescriptor]]:
    """
    Find an exit by name or direction in current location.

    Searches:
    1. Direction names (north, south, up, down, etc.)
    2. Exit names (if exit.name is set)
    3. Keywords in exit llm_context traits

    Returns:
        Tuple of (direction, ExitDescriptor) if found, None otherwise
    """
```

Search strategy:
1. **Exact direction match**: "north", "up", "east" → direct lookup
2. **Exit name match**: "stairs", "archway" → search `exit.name` field
3. **Trait keyword match**: "spiral staircase" → search first trait or name-like traits
4. **Adjective + noun**: "east exit", "stone archway" → combine direction/adjective filtering

**Work Completed:** Added `find_exit_by_name()` function to `utilities/utils.py` with support for direction lookup (including abbreviations like "n", "u"), exit name matching, and partial name matching. Also added `DIRECTION_WORDS` and `DIRECTION_ABBREVIATIONS` constants.

### Phase 3: Extend handle_examine() for Exits

**File:** `behaviors/core/perception.py`

Modify `handle_examine()` to search exits after items and doors:

```python
def handle_examine(accessor, action):
    object_name = action.get("object")
    adjective = action.get("adjective")

    # 1. Try to find an item
    item = find_accessible_item(accessor, object_name, actor_id, adjective)
    if item:
        return examine_item_result(item)

    # 2. Try to find a door
    door = find_door_with_adjective(accessor, object_name, adjective, location.id)
    if door:
        return examine_door_result(door)

    # 3. NEW: Try to find an exit
    exit_result = find_exit_by_name(accessor, object_name, actor_id, adjective)
    if exit_result:
        direction, exit_desc = exit_result
        return examine_exit_result(direction, exit_desc)

    return HandlerResult(success=False, message=f"You don't see any {object_name} here.")
```

### Phase 4: Add Exit-Specific Result Formatting

**File:** `behaviors/core/perception.py`

Create `examine_exit_result()` function:

```python
def examine_exit_result(direction: str, exit_desc: ExitDescriptor) -> HandlerResult:
    """Format examine result for an exit."""
    # Build description from available data
    if exit_desc.description:
        desc = exit_desc.description
    elif exit_desc.name:
        desc = f"A {exit_desc.name} leads {direction}."
    else:
        desc = f"A passage leads {direction}."

    # Build data dict with llm_context for narrator
    data = {
        "exit_direction": direction,
        "exit_type": exit_desc.type
    }
    if exit_desc.llm_context:
        data["llm_context"] = exit_desc.llm_context
    if exit_desc.door_id:
        data["door_id"] = exit_desc.door_id

    return HandlerResult(
        success=True,
        message=desc,
        data=data
    )
```

**Work Completed:** Modified `handle_examine()` in `behaviors/core/perception.py` to:
1. Import `find_exit_by_name` from utilities
2. Search for exits after items and doors fail
3. Build description from `exit_desc.description`, `exit_desc.name`, or fallback to generic "passage leads {direction}"
4. Include `llm_context`, `exit_direction`, `exit_type`, and `door_id` in response data

All 938 tests pass.

### Phase 5: Update Vocabulary

**File:** `behaviors/core/perception.py` vocabulary section

Add exit-related nouns to examine vocabulary:

```python
VOCABULARY = {
    "verbs": [
        {
            "word": "examine",
            "synonyms": ["x", "look at", "inspect", "study"],
            "object_required": True,
            "llm_context": {
                "traits": ["reveals details", "non-destructive"],
                "valid_objects": ["items", "doors", "exits", "actors"]  # ADD exits
            }
        }
    ]
}
```

**File:** `behaviors/core/exits.py`

Exit nouns are now defined in the exits behavior module (not in vocabulary.json):

```python
vocabulary = {
    "nouns": [
        {"word": "exit", "synonyms": ["passage", "way", "path", "opening"]},
        {"word": "stairs", "synonyms": ["staircase", "stairway", "steps"]},
        {"word": "archway", "synonyms": ["arch"]},
        {"word": "corridor", "synonyms": ["hallway", "hall"]},
        {"word": "tunnel", "synonyms": ["passageway"]}
    ],
    ...
}
```

**Work Completed:**
1. Updated `behaviors/core/perception.py` vocabulary to add `valid_objects: ["items", "doors", "exits"]` to examine verb
2. Exit-related nouns are now defined in `behaviors/core/exits.py` behavior module (migrated from vocabulary.json per architectural principle)

### Phase 6: Update Game State Examples

**File:** `examples/simple_game_state.json`

Add `name` and `description` to exits that have `llm_context`:

```json
{
  "up": {
    "type": "open",
    "to": "loc_tower",
    "name": "spiral staircase",
    "description": "A narrow spiral staircase carved from living rock winds upward into shadow.",
    "llm_context": {
      "traits": ["spiral staircase carved from living rock", ...],
      "state_variants": {...}
    }
  }
}
```

**Work Completed:** Updated `examples/simple_game_state.json`:
- Added `name: "spiral staircase"` and description to the "up" exit in loc_hallway
- Added `name: "grand archway"` and description to the "east" exit in loc_hallway

## Testing

### Unit Tests for Exit Lookup

**File:** `tests/utilities/test_exit_lookup.py`

```python
class TestFindExitByName(unittest.TestCase):

    def test_find_exit_by_direction(self):
        """Find exit using direction name."""
        # "examine north" finds the north exit

    def test_find_exit_by_name(self):
        """Find exit using exit.name field."""
        # "examine stairs" finds exit with name="spiral staircase"

    def test_find_exit_by_partial_name(self):
        """Find exit using partial name match."""
        # "examine staircase" matches "spiral staircase"

    def test_find_exit_with_adjective(self):
        """Find exit using adjective + noun."""
        # "examine east exit" finds the east exit
        # "examine spiral stairs" matches name

    def test_exit_not_found(self):
        """Return None when exit doesn't exist."""

    def test_hidden_exit_not_found(self):
        """Hidden exits should not be findable."""

    def test_exit_without_name_found_by_direction(self):
        """Exits without name field can still be found by direction."""
```

### Unit Tests for Examine Exit

**File:** `tests/behaviors/test_perception_exits.py`

```python
class TestExamineExit(unittest.TestCase):

    def test_examine_exit_by_direction(self):
        """Examine exit using direction returns description."""
        result = handle_examine(accessor, {"object": "north", "verb": "examine"})
        self.assertTrue(result.success)

    def test_examine_exit_by_name(self):
        """Examine exit using name returns description."""
        result = handle_examine(accessor, {"object": "stairs", "verb": "examine"})
        self.assertTrue(result.success)
        self.assertIn("spiral", result.message.lower())

    def test_examine_exit_returns_llm_context(self):
        """Examine exit includes llm_context in data."""
        result = handle_examine(accessor, {"object": "stairs", "verb": "examine"})
        self.assertIn("llm_context", result.data)

    def test_examine_exit_without_description(self):
        """Exit without description gets generated message."""
        # Exit has name but no description
        result = handle_examine(accessor, {"object": "passage", "verb": "examine"})
        self.assertTrue(result.success)
        self.assertIn("leads", result.message)

    def test_examine_exit_without_name_or_description(self):
        """Exit with only direction gets minimal message."""
        result = handle_examine(accessor, {"object": "west", "verb": "examine"})
        self.assertTrue(result.success)
        self.assertIn("west", result.message)

    def test_examine_prioritizes_items_over_exits(self):
        """If item and exit share name, item is examined."""
        # Item named "stairs" in room + exit named "stairs"
        # Should examine the item

    def test_examine_exit_with_door(self):
        """Examining exit with door mentions the door."""
        result = handle_examine(accessor, {"object": "east exit", "verb": "examine"})
        # Should include door_id in data for narrator context
```

### Integration Tests

**File:** `tests/llm_interaction/test_json_protocol.py`

```python
class TestExitExamination(unittest.TestCase):

    def test_examine_exit_command_succeeds(self):
        """Full command flow for examining exit."""
        message = {
            "type": "command",
            "action": {"verb": "examine", "object": "stairs"}
        }
        result = handler.handle_message(message)
        self.assertTrue(result["success"])

    def test_examine_exit_includes_llm_context_in_response(self):
        """Response includes llm_context for narrator."""
        message = {
            "type": "command",
            "action": {"verb": "examine", "object": "up"}
        }
        result = handler.handle_message(message)
        self.assertIn("data", result)
        self.assertIn("llm_context", result["data"])
```

## Effort Estimate

### Scope

| Component | Files | Complexity |
|-----------|-------|------------|
| Add fields to ExitDescriptor | 1 | Low |
| Add find_exit_by_name utility | 1 | Medium |
| Extend handle_examine | 1 | Medium |
| Add examine_exit_result | 1 | Low |
| Update vocabulary | 2 | Low |
| Update example game state | 1 | Low |
| Unit tests | 2 new files | Medium |
| Integration tests | 1 | Low |

### Total Effort: Medium

- **Lines of code:** ~150-200 new lines
- **Test coverage:** ~15-20 new tests
- **Risk:** Low - additive changes, backward compatible
- **Dependencies:** None external

### Implementation Order

1. **Phase 1:** Add fields to ExitDescriptor (enables everything else)
2. **Phase 2:** Add find_exit_by_name utility (standalone, testable)
3. **Phase 3-4:** Extend handle_examine (depends on Phase 2)
4. **Phase 5:** Update vocabulary (independent)
5. **Phase 6:** Update example game state (independent)

Each phase can be implemented and tested independently.

## Files Modified

- `src/state_manager.py` - Add name/description to ExitDescriptor
- `utilities/utils.py` - Add find_exit_by_name function
- `behaviors/core/perception.py` - Extend handle_examine, add examine_exit_result
- `src/vocabulary.json` - Add exit-related nouns
- `examples/simple_game_state.json` - Add name/description to exits

## New Files

- `tests/test_examine_exits.py` - Tests for find_exit_by_name and exit examination (16 tests)

---

## Work Completed

### Summary

All 6 phases completed successfully. Exits are now first-class examinable entities.

### Implementation Details

1. **Phase 1:** Added `name` and `description` optional fields to `ExitDescriptor` in `src/state_manager.py`

2. **Phase 2:** Added `find_exit_by_name()` utility in `utilities/utils.py` with support for:
   - Direction lookup (north, up) and abbreviations (n, u)
   - Exit name matching (stairs → "spiral staircase")
   - Partial name matching (spiral → "spiral staircase")
   - Word matching (steps → "stone steps")
   - Adjective + exit pattern (north exit)
   - Generic exit terms (exit, passage, way) when only one exit exists

3. **Phase 3-4:** Extended `handle_examine()` in `behaviors/core/perception.py` to:
   - Search for exits after items and doors fail
   - Return description from `exit_desc.description`, `exit_desc.name`, or fallback
   - Include `llm_context`, `exit_direction`, `exit_type`, and `door_id` in response

4. **Phase 5:** Updated vocabulary:
   - Added `valid_objects: ["items", "doors", "exits"]` to examine verb
   - Exit nouns defined in `behaviors/core/exits.py`: exit, stairs, archway, corridor, tunnel (migrated from vocabulary.json)

5. **Phase 6:** Updated `examples/simple_game_state.json`:
   - Added name/description to "up" exit (spiral staircase)
   - Added name/description to "east" exit (grand archway)

### Test Results

- **18 new tests** in `tests/test_examine_exits.py`
- **956 total tests pass** (including 18 new)
- All tests cover:
  - Finding exits by direction, abbreviation, name, partial name
  - Examining exits with/without descriptions
  - Returning llm_context and direction info
  - Graceful handling of nonexistent exits
  - Generic "exit" term with single vs multiple exits

### Files Changed

| File | Change |
|------|--------|
| `src/state_manager.py` | Added `name`, `description` fields to ExitDescriptor |
| `utilities/utils.py` | Added `find_exit_by_name()`, `DIRECTION_WORDS`, `DIRECTION_ABBREVIATIONS` |
| `behaviors/core/perception.py` | Extended `handle_examine()`, imported `find_exit_by_name` |
| `behaviors/core/exits.py` | Exit-related nouns defined in behavior module vocabulary |
| `examples/simple_game_state.json` | Added exit names/descriptions |
| `tests/test_examine_exits.py` | New test file (18 tests) |
