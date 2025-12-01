# Behavior Refactoring Design Review - Session 5 Summary

## Date: 2025-11-24

## Overview

Fifth review session of `behavior_refactoring.md` following the unified actor model refactoring. This session addressed issues #13-24, completing a comprehensive review of consistency, testing strategy, module organization, and implementation phases.

## Issues Identified and Resolved

### Issue #13-14: Multiple Behaviors Per Entity - Invocation Strategy

**Issue**: When an entity has multiple behaviors (e.g., `behaviors=["lockable", "cursed"]`) and both define the same event (`on_take`), should we:
- Option A: Invoke ALL behaviors and combine results with AND logic
- Option B: Invoke only FIRST matching behavior

**User Decision**: Option A - invoke all behaviors for complete player feedback

**Resolution**: Implemented comprehensive multi-behavior support:

1. **BehaviorManager.invoke_behavior()** updated to:
   - Iterate through ALL behaviors in entity.behaviors list
   - Invoke every behavior that defines the event
   - Collect all results and combine them

2. **Result combination logic**:
   - `allow = all(r.allow for r in results)` - ANY behavior can block
   - Messages from all behaviors are concatenated with newlines
   - Empty results list returns None (no behaviors matched)

3. **Added Design Rationale section** (lines 657-707) explaining:
   - **Complete player feedback**: Player sees all relevant constraints/effects
   - **Composable constraints**: Lockable + Cursed both enforced simultaneously
   - **Qualitative effects accumulate**: Multiple behaviors can describe different aspects
   - **Simple mental model**: All active behaviors participate in events

**Example**:
```python
# Chest has both lockable and cursed behaviors
chest.behaviors = ["lockable", "cursed"]

# Player tries to take chest
# Both on_take handlers are invoked:
# - lockable.on_take() returns EventResult(allow=False, "The chest is locked.")
# - cursed.on_take() returns EventResult(allow=False, "A dark aura prevents you from touching it.")

# Combined result:
# EventResult(allow=False, "The chest is locked.\nA dark aura prevents you from touching it.")
```

**Documentation Added**: Lines 1125-1174 (invoke_behavior implementation), Lines 657-707 (design rationale)

---

### Issue #15: Handler Chaining vs Entity Behaviors - Terminology Confusion

**Issue**: Documentation mixed up two distinct concepts:
- **Entity behaviors**: on_take, on_drop, etc. defined in behavior modules
- **Command handler chaining**: handlers delegating to previous handlers via invoke_previous_handler()

**Resolution**: Added comprehensive examples clarifying the distinction:

1. **Entity behaviors** (e.g., `lockable.py`):
   ```python
   def on_take(entity, accessor, context):
       """Invoked when StateAccessor.update() changes entity's location"""
       if is_locked(entity):
           return EventResult(allow=False, message="The chest is locked.")
   ```

2. **Command handler chaining** (e.g., `themed_items.py`):
   ```python
   def handle_take(verb, args, state, behavior_manager):
       """Override core take handler to add custom narration"""
       # First invoke previous handler (from core/manipulation.py)
       result = behavior_manager.invoke_previous_handler('take', verb, args, state)

       # Enhance result with theme-specific narration
       if result.success and args['item_id'] == 'magic_sword':
           result.message += "\nThe sword hums with ancient power."

       return result
   ```

**Key distinction**: Entity behaviors are invoked by StateAccessor during state changes. Command handler chaining allows behavior modules to extend/override other behavior modules' command handlers.

**Documentation Updated**: Lines 1421-1516 expanded examples

---

### Issue #16: TDD Workflow Contradictions in Phase 2a

**Issue**: Phase 2a had contradictory statements:
- Step 6 said "Write comprehensive tests (all will fail initially)"
- Step 7 said "Implement infrastructure"
- Step 8 said "Verify tests pass"

But other parts suggested implementing before testing.

**User Decision**: Go with strict TDD approach - write tests first

**Resolution**: Restructured Phase 2a to clear 3-step TDD workflow:

1. **Step 6: Write tests first (TDD)** - all will fail initially
2. **Step 7: Implement infrastructure** to make tests pass
3. **Step 8: Implementation checkpoint** - verify ALL tests pass before Phase 2b

Removed all contradictory statements suggesting implementation before tests.

**Documentation Updated**: Lines 2299-2402 (Phase 2a restructured)

---

### Issue #17: Entities Without Behaviors Field

**Issue**: Only Item entities had `behaviors` field. What about Actor, Location, Door, Lock?

Options:
- A: All entities support behaviors (add field to all dataclasses)
- B: Only Items support behaviors (document limitation)

**User Decision**: Option A - any kind of entity could have behaviors

**Rationale**: Maximum flexibility for game content:
- **Actors**: Could have status effects (poisoned, blessed, invisible)
- **Locations**: Could have traps, magical wards, environmental hazards
- **Doors**: Could have magical locks, security systems, curses
- **Locks**: Could have puzzle mechanics, magical protections

**Resolution**: Updated all entity dataclasses to include behaviors field:

```python
@dataclass
class Item:
    id: str
    name: str
    behaviors: List[str] = field(default_factory=list)
    # ... other fields

@dataclass
class Actor:
    id: str
    name: str
    behaviors: List[str] = field(default_factory=list)
    location: str
    inventory: List[str]
    # ... other fields

@dataclass
class Location:
    id: str
    name: str
    behaviors: List[str] = field(default_factory=list)
    # ... other fields

@dataclass
class Door:
    id: str
    name: str
    behaviors: List[str] = field(default_factory=list)
    # ... other fields

@dataclass
class Lock:
    id: str
    behaviors: List[str] = field(default_factory=list)
    # ... other fields
```

**Documentation Updated**: Lines 1056-1103 (all entity dataclasses)

---

### Issue #18: Unified Actor Model Consistency Check

**Issue**: After eliminating PlayerState and NPC types in favor of unified Actor, document had inconsistent references.

**Inconsistencies found and fixed**:
1. `Union[PlayerState, NPC]` → `Actor`
2. Imports still showing `from state_manager import PlayerState, NPC`
3. `state.player.inventory` → `state.actors["player"].inventory`
4. `GameState.actors: Dict[str, Union[PlayerState, NPC]]` → `Dict[str, Actor]`

**Resolution**: Systematic search and replace across entire document ensuring all references conform to unified Actor model.

**Documentation Updated**: Multiple locations throughout document

---

### Issue #19: Vocabulary Generation Testing

**Issue**: Phase 2a didn't specify comprehensive tests for vocabulary_generator.py

**Resolution**: Added detailed test coverage specification:

```python
# Test noun extraction from entities
test_extract_nouns_from_items()
test_extract_nouns_from_actors()
test_extract_nouns_from_locations()
test_extract_nouns_from_doors()

# Test verb registration from behaviors
test_register_verbs_from_behavior_module()
test_register_verbs_from_multiple_modules()
test_verb_override_precedence()

# Test parser vocabulary integration
test_parser_receives_complete_vocabulary()
test_parser_handles_noun_verb_ambiguity()

# Test edge cases
test_empty_behavior_modules()
test_entities_without_names()
test_duplicate_nouns_across_entity_types()
```

**Documentation Updated**: Lines 2297-2314 (Phase 2a test plan)

---

### Issue #20: Behavior Module Dependencies

**Issue**: Design didn't clearly specify what behavior modules can import.

**Clarification**: Behavior modules can import from `utilities/`, NOT from other behavior modules.

**Architecture**:
```
behaviors/           # Behavior modules (define handlers, events, vocabularies)
  core/
    manipulation.py  # Can import from utilities/utils.py
    movement.py      # Can import from utilities/utils.py
utilities/           # Utility modules (helper functions only, NO handlers/events)
  utils.py          # Search, lookup, visibility functions
```

**Inter-behavior-module dependencies** documented as explicitly out of scope (would require dependency graph, circular dependency detection, etc.).

**Documentation Updated**: Lines 1626-1662 (module organization), Lines 3383-3387 (deferred items)

---

### Issue #21: Changes Dict Format - String Keys vs Nested Dicts

**Issue**: StateAccessor.update() documentation showed both string keys with dots AND nested dict examples:
- `{"properties.container.open": True}` (string with dots)
- `{"properties": {"container": {"open": True}}}` (nested dicts)

**User Decision**: Use ONLY string keys with dot notation, never nested dicts

**Resolution**: Standardized all examples and documentation:

```python
# CORRECT - string keys with dot notation
changes = {
    "location": "room1",              # Simple field
    "properties.health": 50,          # Nested dict field
    "+inventory": "sword",            # Append to list
    "-inventory": "shield",           # Remove from list
    "properties.container.open": True # Deeply nested
}

# INCORRECT - never use nested dicts
changes = {
    "properties": {
        "container": {
            "open": True
        }
    }
}
```

**Rationale**:
- Simpler API - single format for all updates
- Easier to read - clear path to field being updated
- Consistent with list prefix syntax (`"+inventory"`)
- No ambiguity about merge vs replace semantics

**Documentation Updated**: Lines 372-394 (StateAccessor.update() docstring), all examples throughout document

---

### Issue #22: _set_path() Test Coverage for Nested Dict Access

**Issue**: Phase 2a test plan didn't explicitly cover nested dict access with dot notation.

**Resolution**: Expanded test coverage specification:

```python
# Simple field access
test_set_path_simple_field()  # "location" → item.location

# Nested dict access with dots
test_set_path_nested_dict()  # "properties.container.open" → item.properties["container"]["open"]
test_set_path_creates_intermediate_dicts()  # Creates missing intermediate dicts

# List operations
test_set_path_list_append()  # "+inventory"
test_set_path_list_remove()  # "-inventory"
test_set_path_nested_list()  # "+properties.tags"

# Error cases
test_set_path_invalid_field()  # Field doesn't exist
test_set_path_append_to_non_list()  # "+location" when location is string
test_set_path_invalid_entity()  # Entity missing expected structure
```

**Documentation Updated**: Lines 2304-2324 (Phase 2a test plan)

---

### Issue #23: visibility.py vs utils.py - Module Duplication

**Issue**: Design had both `utilities/visibility.py` and `utilities/utils.py` with overlapping purposes:
- `utils.py`: Search/lookup functions (find_accessible_item)
- `visibility.py`: Enumeration functions (get_visible_items_in_location)

Both are "utilities that help handlers determine what entities are accessible/visible."

**Resolution**: Merged into single `utilities/utils.py` containing:

1. **Search/lookup functions**:
   - `find_accessible_item(state, actor_id, item_name)` → Item or None
   - `find_accessible_door(state, actor_id, door_name)` → Door or None
   - `find_accessible_actor(state, actor_id, actor_name)` → Actor or None

2. **Visibility/enumeration functions**:
   - `get_visible_items_in_location(state, location_id, actor_id)` → List[Item]
   - `get_visible_actors_in_location(state, location_id, actor_id)` → List[Actor]
   - `get_visible_exits(state, location_id, actor_id)` → List[str]
   - `get_inventory_items(state, actor_id)` → List[Item]

**Rationale**: Both serve the same purpose (determining entity visibility/accessibility), splitting them creates artificial separation and confusion.

**Documentation Updated**: Lines 1626-1662 (merged into single utilities/utils.py)

---

### Issue #24: Entity Behaviors Optional in Phase 2b

**Issue**: Phase 2b creates command handler modules (manipulation.py, movement.py) but doesn't specify when/how to create entity behavior modules (on_take, on_drop, etc.).

This created confusion: Should handlers be tested with or without entity behaviors?

**User Decision**: Option A - handlers work with or without entity behaviors, test both cases

**Resolution**: Added clarification to Phase 2b:

```
**Entity behaviors are optional:** Command handlers in this phase work with or
without entity behaviors. Handlers can be tested with simple entities (no behaviors)
and entity behavior modules can be added incrementally as game content requires them.
```

**Test strategy**:
1. Test handlers with simple entities (no behaviors field or empty list)
2. Test handlers with entity behaviors where behaviors add constraints
3. This validates handlers correctly invoke entity behaviors when present but don't break when absent

**Example**:
```python
# Test take handler without entity behaviors
def test_handle_take_simple():
    sword = Item(id="sword", name="sword", behaviors=[])
    # Should work - no entity behaviors to invoke

# Test take handler WITH entity behaviors
def test_handle_take_locked_item():
    chest = Item(id="chest", name="chest", behaviors=["lockable"])
    # Should invoke lockable.on_take() and respect result
```

**Documentation Updated**: Lines 2418-2420 (Phase 2b clarification)

---

### Issue #25: Module Loading Error Handling Specification

**Issue**: Design didn't specify how to handle errors during module loading:
- Module syntax errors (SyntaxError)
- Module import failures (ImportError, ModuleNotFoundError)
- Malformed vocabulary (already handled by _validate_vocabulary)
- Handler conflicts (already handled by load_module)
- Handler function signature errors

**User Decision**: All are developer errors that should be checked at load time if possible and reported via stderr. No recovery needed - fail fast during development.

**Resolution**: Added comprehensive "Design Rationale: Module Loading Error Handling" section specifying:

1. **Philosophy: Fail fast during development**
   - Detect errors at load time when possible
   - Report via stderr with technical details for developers
   - Fail loudly - make errors impossible to ignore
   - Provide actionable messages with context

2. **Error categories and handling:**
   - **Syntax errors (SyntaxError)**: Caught during import, logged with filename and line number
   - **Import failures (ImportError)**: Caught during import, logged with module name and missing dependency
   - **Malformed vocabulary (ValueError)**: Already handled by _validate_vocabulary()
   - **Handler/vocabulary conflicts (ValueError)**: Already handled by load_module()
   - **Handler signature errors**: NOT checked at load time (unreliable), deferred to runtime TypeError

3. **Module loading code pattern:**
   ```python
   try:
       module = importlib.import_module(module_name)
       behavior_manager.load_module(module, source_type=source_type)
   except SyntaxError as e:
       print(f"ERROR loading module {module_name}: SyntaxError: {e.msg} ({e.filename}, line {e.lineno})", file=sys.stderr)
   except (ImportError, ModuleNotFoundError) as e:
       print(f"ERROR loading module {module_name}: {type(e).__name__}: {e}", file=sys.stderr)
   except ValueError as e:
       print(f"ERROR loading module {module_name}: {e}", file=sys.stderr)
   ```

4. **Key design decisions:**
   - **Continue loading after errors**: If one module fails, continue loading others (see all errors at once)
   - **No signature validation**: Runtime TypeErrors give better debugging info than load-time checks
   - **No event name validation**: Can't validate event names at load time (modules loaded dynamically)
   - **stderr for all errors**: Always developer errors, never user-facing
   - **Technical messages**: Include full module names, exception types, file/line numbers

5. **Testing approach:**
   - Test syntax errors are caught during import
   - Test import errors are caught and reported
   - Test malformed vocabulary raises ValueError
   - Test handler signature errors NOT caught at load (succeed), but raise TypeError at runtime
   - Test continue-on-error (load multiple modules, some invalid, verify valid ones load)

**Documentation Added:**
- Lines 725-898: "Design Rationale: Module Loading Error Handling" section
- Lines 79-85: Updated error handling convention to reference new section
- Lines 89-108: Updated stderr output examples to include module loading errors
- Lines 2573-2597: Added module loading error handling tests to Phase 2a test plan

**Rationale**: Developer errors should fail fast with clear technical messages. No recovery needed - developers fix bugs during development/testing, not at runtime.

---

## Summary of Session 5 Work

Addressed issues #13-25, focusing on:

1. **Multi-behavior invocation strategy** (#13-14): All behaviors invoked, AND logic for combining
2. **Handler chaining vs entity behaviors** (#15): Clarified distinct concepts with examples
3. **TDD workflow** (#16): Strict write-tests-first approach
4. **Universal behavior support** (#17): All entity types have behaviors field
5. **Unified actor model consistency** (#18): Eliminated all PlayerState/NPC references
6. **Vocabulary generation testing** (#19): Comprehensive test coverage
7. **Module dependencies** (#20): Behaviors import from utilities, not each other
8. **Changes dict format** (#21): String keys only, dots for nesting
9. **_set_path() testing** (#22): Coverage for nested dict access
10. **Module consolidation** (#23): Merged visibility.py into utils.py
11. **Optional entity behaviors** (#24): Handlers work with or without behaviors
12. **Module loading error handling** (#25): Comprehensive error handling specification for load-time errors

## Design Completeness

The design document now includes:

- **Clear architectural boundaries**: behaviors/ vs utilities/ directories
- **Consistent data model**: Unified Actor type, all entities support behaviors
- **Unambiguous APIs**: String-only keys in changes dict, dot notation for nesting
- **Comprehensive testing strategy**: TDD workflow, entity behavior testing, error handling tests
- **Complete examples**: Multi-behavior invocation, handler chaining, all major patterns
- **Design rationales**: Multi-behavior invocation, StateAccessor coupling, error messages, noun vocabulary, module loading error handling

## Files Modified

- `/Users/jed/Development/text-game/docs/behavior_refactoring.md` - Multiple sections updated:
  - Lines 79-85: Updated error handling convention to reference module loading section
  - Lines 89-108: Updated stderr output examples (module loading errors)
  - Lines 372-394: StateAccessor.update() docstring (string-only keys)
  - Lines 657-707: Design rationale for multi-behavior invocation
  - Lines 725-898: Design rationale for module loading error handling (NEW)
  - Lines 1056-1103: All entity dataclasses with behaviors field
  - Lines 1125-1174: BehaviorManager.invoke_behavior() implementation
  - Lines 1421-1516: Handler chaining examples
  - Lines 1626-1662: Module organization (merged visibility.py into utils.py)
  - Lines 2297-2402: Phase 2a test plan (TDD workflow, comprehensive coverage)
  - Lines 2418-2420: Phase 2b entity behaviors optional
  - Lines 2573-2597: Module loading error handling tests (NEW)
  - Multiple locations: Unified Actor model consistency fixes

## Current Status

**All design review issues resolved.** The behavior refactoring design is complete and ready for implementation:

- All 25 identified issues addressed across 5 review sessions
- No outstanding design holes or inconsistencies
- Clear rationale documented for all design decisions
- Comprehensive migration path with testing strategy
- Complete examples for all major patterns
- Full error handling specification for all failure modes

## Next Steps

The design is ready for implementation. Recommended approach:

1. **Phase 2a**: Implement StateAccessor and utilities with full test coverage
2. **Phase 2b validation**: Implement one complete handler (e.g., `handle_take`) end-to-end to validate design
3. **Phase 2b completion**: Only proceed with remaining handlers after first handler proves the design works
4. **Entity behaviors**: Add entity behavior modules (on_take, on_drop, etc.) incrementally as game content requires

## Review Session History

1. **Review 1** (2025-11-23): Initial comprehensive review, fixed terminology (#4) and test structure (#7)
2. **Review 2** (2025-11-23): Fixed handler loading order (#1), handler chaining (#2), removed related_changes
3. **Review 3** (2025-11-24): Fixed actor_id threading (#3), imports (#5), conflict detection (#6), query handling (#5)
4. **Review 4** (2025-11-24): Addressed coupling (#8), actor_id in visibility (#9), noun vocabulary (#10), error messages (#11), verified migration path (#12)
5. **Review 5** (2025-11-24): Multi-behavior invocation (#13-14), handler chaining clarification (#15), TDD workflow (#16), universal behaviors (#17), unified actor consistency (#18), vocabulary testing (#19), module dependencies (#20), changes dict format (#21), _set_path testing (#22), module consolidation (#23), optional entity behaviors (#24), module loading error handling (#25)

All review sessions complete. Design validated and ready for implementation.
