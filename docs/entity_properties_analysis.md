# Entity Properties Analysis

## Current State (Baseline)

**Test Status:** 2039 tests, ALL PASSING ✅, 0 failures, 0 errors, 5 skipped

**Git Status:** Clean working tree except for documentation changes

## Understanding What Happened

### Phase 3/3.5 Was Completed But Reverted

From GH issue #311, Phase 3 and 3.5 were **completed successfully**:

**Phase 3:** Implemented CoreFieldProtectingDict
- Added protection to Actor, Item, Location, Part entities
- Changed entity constructors to use `_properties=` parameter
- Added `@property` wrapper returning CoreFieldProtectingDict
- Caught 838+ test code bugs where tests incorrectly accessed core fields via properties dict

**Phase 3.5:** Fixed all 838+ test code bugs
- Created `RenameKeywordArgInConstructors` LibCST transformer
- Fixed 70 test files automatically
- Manual fixes for edge cases
- Final result: All tests passing, core field protection working correctly

**Current State:** All Phase 3/3.5 work was reverted (uncommitted)
- Current codebase has NO CoreFieldProtectingDict class
- All entities use plain `properties: Dict[str, Any] = field(default_factory=dict)`
- All 2039 tests passing
- This is the state BEFORE Phase 3 was implemented

## What Phase 3 Implementation Looked Like

Based on GH issue #311 comments, the completed Phase 3 implementation included:

### 1. CoreFieldProtectingDict Class

A dict wrapper that prevents accidental modification of core fields via the properties dict:

```python
class CoreFieldProtectingDict(dict):
    """Dict that prevents modification of core entity fields via properties."""

    def __init__(self, core_fields: Set[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._core_fields = core_fields

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self._core_fields:
            raise TypeError(
                f"Cannot set core field '{key}' via properties dict. "
                f"Use direct attribute access instead."
            )
        super().__setitem__(key, value)

    def setdefault(self, key: str, default: Any = None) -> Any:
        if key in self._core_fields:
            raise TypeError(
                f"Cannot set core field '{key}' via properties dict. "
                f"Use direct attribute access instead."
            )
        return super().setdefault(key, default)
```

### 2. Entity Changes (Example: Actor)

**Before Phase 3:**
```python
@dataclass
class Actor:
    id: ActorId
    name: str
    description: str
    location: LocationId
    inventory: List[ItemId] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: List[str] = field(default_factory=list)
```

**After Phase 3:**
```python
@dataclass
class Actor:
    id: ActorId
    name: str
    description: str
    location: LocationId
    inventory: List[ItemId] = field(default_factory=list)
    _properties: Dict[str, Any] = field(default_factory=dict)  # Underscore prefix
    behaviors: List[str] = field(default_factory=list)

    @property
    def properties(self) -> Dict[str, Any]:
        """Return properties dict with core field protection."""
        if not isinstance(self._properties, CoreFieldProtectingDict):
            core_fields = {'id', 'name', 'description', 'location', 'inventory', 'behaviors'}
            self._properties = CoreFieldProtectingDict(core_fields, self._properties)
        return self._properties
```

### 3. Entities That Received Protection

According to the issue, these entities were updated:
- Actor
- Item
- Location
- Part

These entities were NOT updated (used plain `properties:`):
- Lock
- ExitDescriptor
- Commitment
- ScheduledEvent
- Gossip
- Spread

### 4. Test Code Changes

The LibCST transformer changed test code from:
```python
# Before:
actor = Actor(
    id=ActorId('player'),
    name="Player",
    location=LocationId('start'),
    properties={'health': 100}
)

# After:
actor = Actor(
    id=ActorId('player'),
    name="Player",
    location=LocationId('start'),
    _properties={'health': 100}  # Changed to _properties
)
```

## Why Phase 3/3.5 Work Was Valuable

Phase 3 caught **838 real bugs** in test code where tests were incorrectly accessing core fields:

**Bug Pattern 1:** Direct assignment to core fields
```python
# WRONG (caught by Phase 3):
actor.properties['location'] = LocationId('cave')

# CORRECT:
actor.location = LocationId('cave')
```

**Bug Pattern 2:** Reading core fields via properties
```python
# WRONG (caught by Phase 3):
loc = actor.properties.get('location')

# CORRECT:
loc = actor.location
```

These bugs were lurking in the test suite but not causing failures. Phase 3's protection made them visible and forcible to fix.

## Re-Implementation Plan

To restore Phase 3/3.5 work, we need to:

1. **Restore CoreFieldProtectingDict class** - Create the protection wrapper
2. **Update entity classes** - Add `_properties` + `@property` wrapper to Actor, Item, Location, Part
3. **Update entity parsers** - Handle `_properties` in JSON parsing
4. **Run LibCST refactoring** - Transform test code from `properties=` to `_properties=`
5. **Verify tests pass** - Ensure all 2039+ tests still pass

## Questions to Resolve

1. **Should Lock and ExitDescriptor get protection too?**
   - Phase 3 only protected Actor/Item/Location/Part
   - User previously said "Yes, make Lock & ExitDescriptor consistent"
   - Should we expand Phase 3 scope or stay with original design?

2. **Where should CoreFieldProtectingDict class live?**
   - In state_manager.py with the entity classes?
   - In a separate utilities file?

3. **Should we proceed with re-implementation?**
   - Or was Phase 3 abandoned for a reason?
   - Need user confirmation before starting work
