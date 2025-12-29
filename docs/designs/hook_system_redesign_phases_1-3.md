# Hook System Redesign - Phases 1-3 Implementation Plan

## Overview

This document describes the re-implementation of Phases 1-3 from GH issue #307 (Hook System Redesign), which were completed but reverted due to being uncommitted work.

**Parent Issue:** #307 - Hook System Redesign: Vocabulary-Based Hook Definitions
**Reference Plan:** /Users/jed/.claude/plans/declarative-petting-thunder.md
**Current Baseline:** 2039 tests, ALL PASSING ✅

## Context

The hook system redesign addresses these problems:
1. Authors must reference src/hooks.py for hook names
2. Hook names don't indicate invocation pattern (turn phase vs entity-specific)
3. Limited validation - authoring errors only caught at runtime
4. No dependency ordering for turn phases
5. Core field misuse (actor.properties['location']) silently fails

**Solution:** Vocabulary-based hook definitions with validation and runtime protection.

## Lessons from Previous Attempt

The previous implementation of Phases 1-3 was completed successfully but reverted due to:

1. **Uncommitted work got lost** - Work was done but never committed
2. **No cleanup plan** - After Phase 3 caught 838 test errors, there was no systematic plan to fix them
3. **LibCST tool issues** - The refactoring tool had bugs (double-underscore `__properties`, too broad scope)
4. **Confusion about baseline** - Unclear what the correct baseline was after changes

**This plan addresses these issues:**

### 1. Commit Strategy
- **Commit after each phase completes with all tests passing**
- Phase 1: Commit infrastructure (no test breakage expected)
- Phase 2: Commit validation (no test breakage expected)
- Phase 3: Commit only after ALL test fixes complete
- Use git branches for safety: `feature/hook-system-phase-1`, etc.

### 2. Phase 3 Cleanup Plan (Detailed Below)
- Step-by-step approach to fixing 838+ expected test errors
- Automated refactoring with verification
- Manual fix patterns documented
- Clear "done" criteria for each step

### 3. LibCST Tool Improvements
- Add visit_Call/leave_Call tracking to target only specific constructors
- Test transformer on small file first before running on entire codebase
- Manual review of dry-run output before applying
- Avoid sed for any fixes (use Edit tool or manual edits)

### 4. Baseline Tracking
- Document test count and status before each phase
- Document test count and status after each phase
- Never proceed to next phase with failing tests

## Phase 1: Core Infrastructure - Hook Definition Storage

### Goal
Add hook definition storage to BehaviorManager (temporary, for later handoff to turn_executor)

### Data Structure

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class HookDefinition:
    """Definition of a hook from a behavior module vocabulary."""
    hook: str                      # Hook name (e.g., "turn_environmental_effect")
    invocation: str                # "turn_phase" or "entity"
    after: List[str]               # Dependencies (for turn phases only)
    description: str               # Human-readable description
    defined_by: str                # Module that defined it (for error messages)
```

### BehaviorManager Changes

Add to `src/behavior_manager.py`:

```python
class BehaviorManager:
    def __init__(self):
        # Existing fields...
        self._hook_definitions: Dict[str, HookDefinition] = {}

    def _register_hook_definition(self, hook_def: Dict[str, Any], module_path: str) -> None:
        """Register a hook definition from a vocabulary.

        Args:
            hook_def: Hook definition dict from vocabulary
            module_path: Path of module defining this hook (for error messages)

        Raises:
            ValueError: If hook already defined by different module
        """
        hook_name = hook_def['hook']

        # Check for duplicates
        if hook_name in self._hook_definitions:
            existing = self._hook_definitions[hook_name]
            if existing.defined_by != module_path:
                raise ValueError(
                    f"Hook '{hook_name}' defined multiple times:\n"
                    f"  1. {existing.defined_by}\n"
                    f"  2. {module_path}"
                )
            # Same module re-defining - just skip
            return

        # Store hook definition
        self._hook_definitions[hook_name] = HookDefinition(
            hook=hook_name,
            invocation=hook_def['invocation'],
            after=hook_def.get('after', []),
            description=hook_def.get('description', ''),
            defined_by=module_path
        )

    def _register_vocabulary(self, module_path: str, vocabulary: Dict[str, Any]) -> None:
        """Register vocabulary from a behavior module.

        Existing method - add hook_definitions processing.
        """
        # Existing code for verbs, events, etc...

        # NEW: Process hook definitions
        if 'hook_definitions' in vocabulary:
            for hook_def in vocabulary['hook_definitions']:
                self._register_hook_definition(hook_def, module_path)
```

### Tests

Create `tests/test_hook_definitions.py`:

```python
class TestHookDefinitionStorage(unittest.TestCase):
    """Test Phase 1: Hook definition storage in BehaviorManager."""

    def test_register_turn_phase_hook(self):
        """Test registering a turn phase hook definition."""
        # Vocabulary with turn phase hook
        # BehaviorManager loads it
        # Assert hook stored correctly

    def test_register_entity_hook(self):
        """Test registering an entity hook definition."""
        # Vocabulary with entity hook
        # Assert stored with correct invocation type

    def test_duplicate_hook_different_modules_raises(self):
        """Test that same hook from different modules raises error."""
        # Module A defines "turn_foo"
        # Module B defines "turn_foo"
        # Should raise ValueError with both module names

    def test_duplicate_hook_same_module_allowed(self):
        """Test that same hook from same module is idempotent."""
        # Module A defines "turn_foo" in multiple events
        # Should not raise - first definition wins

    def test_hook_with_dependencies(self):
        """Test storing hook with 'after' dependencies."""
        # Hook with after: ["turn_other", "turn_another"]
        # Assert dependencies stored correctly
```

### Success Criteria
- ✅ BehaviorManager can load hook definitions from vocabularies
- ✅ Duplicate detection works correctly
- ✅ All hook definition fields stored properly
- ✅ Tests pass

### Files Modified
- `src/behavior_manager.py` - Add HookDefinition class and storage
- `tests/test_hook_definitions.py` - New test file

---

## Phase 2: Validation Suite

### Goal
Add 6 validation methods that catch 90%+ of authoring errors at load time.

### Validation Methods

All methods added to `src/behavior_manager.py`:

#### 1. validate_hook_prefixes()

```python
def validate_hook_prefixes(self) -> None:
    """Validate all hooks use correct prefixes (turn_* or entity_*).

    Raises:
        ValueError: If hook doesn't use required prefix
    """
    for hook_name, hook_def in self._hook_definitions.items():
        if hook_def.invocation == "turn_phase":
            if not hook_name.startswith("turn_"):
                raise ValueError(
                    f"Turn phase hook '{hook_name}' must start with 'turn_' prefix\n"
                    f"  Defined in: {hook_def.defined_by}"
                )
        elif hook_def.invocation == "entity":
            if not hook_name.startswith("entity_"):
                raise ValueError(
                    f"Entity hook '{hook_name}' must start with 'entity_' prefix\n"
                    f"  Defined in: {hook_def.defined_by}"
                )
        else:
            raise ValueError(
                f"Hook '{hook_name}' has invalid invocation type '{hook_def.invocation}'\n"
                f"  Must be 'turn_phase' or 'entity'\n"
                f"  Defined in: {hook_def.defined_by}"
            )
```

#### 2. validate_turn_phase_dependencies()

```python
def validate_turn_phase_dependencies(self) -> None:
    """Validate turn phase 'after' dependencies reference defined hooks.

    Raises:
        ValueError: If dependency references undefined hook
    """
    for hook_name, hook_def in self._hook_definitions.items():
        if hook_def.invocation != "turn_phase":
            continue

        for dep in hook_def.after:
            if dep not in self._hook_definitions:
                raise ValueError(
                    f"Turn phase '{hook_name}' depends on undefined hook '{dep}'\n"
                    f"  Defined in: {hook_def.defined_by}"
                )

            # Dependency must also be a turn phase
            dep_def = self._hook_definitions[dep]
            if dep_def.invocation != "turn_phase":
                raise ValueError(
                    f"Turn phase '{hook_name}' depends on '{dep}' which is not a turn phase\n"
                    f"  '{dep}' is invocation type: {dep_def.invocation}\n"
                    f"  Defined in: {hook_def.defined_by}"
                )
```

#### 3. validate_hooks_are_defined()

```python
def validate_hooks_are_defined(self) -> None:
    """Validate all event hook references point to defined hooks.

    Raises:
        ValueError: If event references undefined hook
    """
    for event_name, event_spec in self._event_specs.items():
        hook_name = event_spec.hook

        if hook_name and hook_name not in self._hook_definitions:
            raise ValueError(
                f"Event '{event_name}' references undefined hook '{hook_name}'\n"
                f"  Event defined in: {event_spec.module_path}\n"
                f"  Available hooks: {sorted(self._hook_definitions.keys())}"
            )
```

#### 4. validate_turn_phase_not_in_entity_behaviors()

```python
def validate_turn_phase_not_in_entity_behaviors(self, game_state: GameState) -> None:
    """Validate turn phase behaviors not attached to entities.

    Turn phases should only be in global behaviors, not entity behaviors lists.

    Args:
        game_state: Loaded game state to validate

    Raises:
        ValueError: If turn phase behavior attached to entity
    """
    # Get all turn phase module paths
    turn_phase_modules = set()
    for hook_def in self._hook_definitions.values():
        if hook_def.invocation == "turn_phase":
            turn_phase_modules.add(hook_def.defined_by)

    # Check all entities
    for actor in game_state.actors.values():
        for behavior in actor.behaviors:
            if behavior in turn_phase_modules:
                raise ValueError(
                    f"Actor '{actor.id}' has turn phase behavior '{behavior}' in behaviors list\n"
                    f"  Turn phases should not be attached to entities"
                )

    for item in game_state.items:
        for behavior in item.behaviors:
            if behavior in turn_phase_modules:
                raise ValueError(
                    f"Item '{item.id}' has turn phase behavior '{behavior}' in behaviors list\n"
                    f"  Turn phases should not be attached to entities"
                )

    for location in game_state.locations.values():
        for behavior in location.behaviors:
            if behavior in turn_phase_modules:
                raise ValueError(
                    f"Location '{location.id}' has turn phase behavior '{behavior}' in behaviors list\n"
                    f"  Turn phases should not be attached to entities"
                )
```

#### 5. validate_hook_invocation_consistency()

```python
def validate_hook_invocation_consistency(self) -> None:
    """Validate each hook used consistently (not as both turn_phase and entity).

    Raises:
        ValueError: If hook defined with conflicting invocation types
    """
    # This is already enforced by duplicate detection in _register_hook_definition
    # But we keep this as explicit validation pass for clarity

    hook_invocations: Dict[str, Tuple[str, str]] = {}  # hook -> (invocation, module)

    for hook_name, hook_def in self._hook_definitions.items():
        if hook_name in hook_invocations:
            prev_inv, prev_mod = hook_invocations[hook_name]
            if prev_inv != hook_def.invocation:
                raise ValueError(
                    f"Hook '{hook_name}' used with conflicting invocation types:\n"
                    f"  1. {prev_mod}: {prev_inv}\n"
                    f"  2. {hook_def.defined_by}: {hook_def.invocation}"
                )
        else:
            hook_invocations[hook_name] = (hook_def.invocation, hook_def.defined_by)
```

#### 6. validate_no_core_fields_in_properties()

**Note:** This validation is **NOT** implemented in Phase 2. Instead, it's handled by runtime protection in Phase 3 via CoreFieldProtectingDict. The original design had this as Phase 2 validation, but the actual implementation used runtime protection instead.

### Validation Call Site

```python
def finalize_loading(self, game_state: GameState) -> None:
    """Call after all vocabularies loaded to run validations.

    Args:
        game_state: Loaded game state (for entity behavior validation)

    Raises:
        ValueError: If any validation fails
    """
    # Run all validations
    self.validate_hook_prefixes()
    self.validate_turn_phase_dependencies()
    self.validate_hooks_are_defined()
    self.validate_hook_invocation_consistency()
    self.validate_turn_phase_not_in_entity_behaviors(game_state)
```

### Tests

Create `tests/test_validation.py`:

```python
class TestHookValidation(unittest.TestCase):
    """Test Phase 2: Hook validation methods."""

    # Test validate_hook_prefixes()
    def test_turn_phase_without_prefix_raises(self):
        """Turn phase hook without 'turn_' prefix should raise."""

    def test_entity_hook_without_prefix_raises(self):
        """Entity hook without 'entity_' prefix should raise."""

    def test_valid_prefixes_pass(self):
        """Hooks with correct prefixes should not raise."""

    def test_invalid_invocation_type_raises(self):
        """Hook with invocation='foo' should raise."""

    # Test validate_turn_phase_dependencies()
    def test_dependency_on_undefined_hook_raises(self):
        """Turn phase depending on non-existent hook should raise."""

    def test_dependency_on_entity_hook_raises(self):
        """Turn phase depending on entity hook should raise."""

    def test_valid_dependencies_pass(self):
        """Turn phases with valid dependencies should not raise."""

    # Test validate_hooks_are_defined()
    def test_event_references_undefined_hook_raises(self):
        """Event with hook='turn_foo' when turn_foo not defined should raise."""

    def test_all_events_reference_defined_hooks_passes(self):
        """All events referencing defined hooks should not raise."""

    # Test validate_turn_phase_not_in_entity_behaviors()
    def test_turn_phase_on_actor_raises(self):
        """Actor with turn phase in behaviors list should raise."""

    def test_turn_phase_on_item_raises(self):
        """Item with turn phase in behaviors list should raise."""

    def test_turn_phase_on_location_raises(self):
        """Location with turn phase in behaviors list should raise."""

    def test_entity_behaviors_on_entities_allowed(self):
        """Entity with entity hooks in behaviors list should not raise."""

    # Test validate_hook_invocation_consistency()
    def test_hook_as_both_turn_and_entity_raises(self):
        """Same hook defined as both turn_phase and entity should raise."""

    def test_consistent_invocation_passes(self):
        """Hook always used with same invocation type should not raise."""
```

### Success Criteria
- ✅ All 5 validation methods implemented
- ✅ Validation called during finalization
- ✅ Comprehensive test coverage for valid and invalid cases
- ✅ Clear error messages guide authors to fixes
- ✅ All tests pass

### Files Modified
- `src/behavior_manager.py` - Add 5 validation methods + finalize_loading()
- `tests/test_validation.py` - New test file (26+ test cases)

---

## Phase 3: Core Field Protection

### Goal
Add runtime protection to prevent core field access via properties dict.

### Design

**Problem:** Test code (and potentially game behaviors) can incorrectly access core fields:
```python
# WRONG - silently fails or causes bugs:
actor.properties['location'] = LocationId('cave')
actor.properties.get('location')

# CORRECT:
actor.location = LocationId('cave')
actor.location
```

**Solution:** Wrap the properties dict to raise clear errors on core field access.

### Implementation

#### CoreFieldProtectingDict Class

Add to `src/state_manager.py`:

```python
class CoreFieldProtectingDict(dict):
    """Dict wrapper that prevents modification of core entity fields.

    Raises TypeError if attempting to set fields that exist as direct attributes
    (location, id, name, inventory, behaviors, description).
    """

    def __init__(self, core_fields: Set[str], *args, **kwargs):
        """Initialize with set of protected field names.

        Args:
            core_fields: Set of field names that cannot be set via dict
            *args, **kwargs: Passed to dict.__init__
        """
        super().__init__(*args, **kwargs)
        self._core_fields = core_fields

    def __setitem__(self, key: str, value: Any) -> None:
        """Prevent setting core fields via dict access.

        Raises:
            TypeError: If key is a core field
        """
        if key in self._core_fields:
            raise TypeError(
                f"Cannot set core field '{key}' via properties dict. "
                f"Use direct attribute access instead (e.g., entity.{key} = value)"
            )
        super().__setitem__(key, value)

    def setdefault(self, key: str, default: Any = None) -> Any:
        """Prevent setting core fields via setdefault.

        Raises:
            TypeError: If key is a core field
        """
        if key in self._core_fields:
            raise TypeError(
                f"Cannot set core field '{key}' via properties dict. "
                f"Use direct attribute access instead (e.g., entity.{key})"
            )
        return super().setdefault(key, default)

    def update(self, *args, **kwargs) -> None:
        """Prevent setting core fields via update.

        Raises:
            TypeError: If any key is a core field
        """
        # Check all keys first before updating
        updates = dict(*args, **kwargs) if args else kwargs
        for key in updates:
            if key in self._core_fields:
                raise TypeError(
                    f"Cannot set core field '{key}' via properties dict. "
                    f"Use direct attribute access instead (e.g., entity.{key} = value)"
                )
        super().update(updates)
```

#### Update Entity Classes

**Apply to:** Actor, Item, Location, Part

**Example for Actor:**

```python
@dataclass
class Actor:
    id: ActorId
    name: str
    description: str
    location: LocationId
    inventory: List[ItemId] = field(default_factory=list)
    _properties: Dict[str, Any] = field(default_factory=dict)  # Changed to _properties
    behaviors: List[str] = field(default_factory=list)

    @property
    def properties(self) -> Dict[str, Any]:
        """Return properties dict with core field protection."""
        if not isinstance(self._properties, CoreFieldProtectingDict):
            core_fields = {'id', 'name', 'description', 'location', 'inventory', 'behaviors'}
            self._properties = CoreFieldProtectingDict(core_fields, self._properties)
        return self._properties
```

**Core fields by entity type:**
- **Actor**: id, name, description, location, inventory, behaviors
- **Item**: id, name, description, location, inventory, behaviors
- **Location**: id, name, description, exits, items, behaviors
- **Part**: id, name, description, part_of, behaviors

**Do NOT apply to:** Lock, ExitDescriptor, Commitment, ScheduledEvent, Gossip, Spread
(These are infrastructure types without core field issues)

#### Update Entity Parsers

Update the JSON parsing functions in `src/state_manager.py` to handle `_properties`:

```python
def actor_from_dict(data: Dict[str, Any]) -> Actor:
    """Parse Actor from JSON dict."""
    return Actor(
        id=ActorId(data['id']),
        name=data['name'],
        description=data.get('description', ''),
        location=LocationId(data['location']),
        inventory=[ItemId(i) for i in data.get('inventory', [])],
        _properties=data.get('properties', {}),  # Changed to _properties
        behaviors=data.get('behaviors', [])
    )
```

**Apply same change to:** item_from_dict, location_from_dict, part_from_dict

#### Update Test Code

**Use LibCST refactoring tool** to update all test files:

```python
# In tools/refactor_using_LibCST, configure:
RenameKeywordArgInConstructors(
    class_names=['Actor', 'Item', 'Location', 'Part'],
    old_arg='properties',
    new_arg='_properties'
)
```

**Run with dry-run first:**
```bash
python tools/refactor_using_LibCST tests/ --dry-run
```

**Manual fixes needed:**
- Any direct `entity.properties['core_field']` access → `entity.core_field`
- Any `entity.properties.get('core_field')` → `entity.core_field`

### Tests

Create `tests/test_core_field_protection.py`:

```python
class TestCoreFieldProtection(unittest.TestCase):
    """Test Phase 3: CoreFieldProtectingDict prevents core field access."""

    def test_actor_can_set_custom_property(self):
        """Actors should be able to set non-core properties."""
        actor = Actor(id=ActorId('test'), name='Test', location=LocationId('start'))
        actor.properties['health'] = 100  # Should work
        self.assertEqual(actor.properties['health'], 100)

    def test_actor_cannot_set_location_via_properties(self):
        """Setting location via properties should raise TypeError."""
        actor = Actor(id=ActorId('test'), name='Test', location=LocationId('start'))
        with self.assertRaises(TypeError) as cm:
            actor.properties['location'] = LocationId('cave')
        self.assertIn('Cannot set core field', str(cm.exception))
        self.assertIn('location', str(cm.exception))

    def test_actor_cannot_set_id_via_properties(self):
        """Setting id via properties should raise TypeError."""
        actor = Actor(id=ActorId('test'), name='Test', location=LocationId('start'))
        with self.assertRaises(TypeError):
            actor.properties['id'] = ActorId('other')

    def test_item_core_field_protection(self):
        """Items should have same protection as Actors."""
        item = Item(id=ItemId('sword'), name='Sword', location=LocationId('start'))
        with self.assertRaises(TypeError):
            item.properties['name'] = 'Dagger'

    def test_location_core_field_protection(self):
        """Locations should protect exits and items fields."""
        loc = Location(id=LocationId('cave'), name='Cave')
        with self.assertRaises(TypeError):
            loc.properties['exits'] = {}

    def test_part_core_field_protection(self):
        """Parts should protect part_of field."""
        part = Part(id=PartId('blade'), name='Blade', part_of=ItemId('sword'))
        with self.assertRaises(TypeError):
            part.properties['part_of'] = ItemId('axe')

    def test_setdefault_on_core_field_raises(self):
        """Using setdefault on core field should raise."""
        actor = Actor(id=ActorId('test'), name='Test', location=LocationId('start'))
        with self.assertRaises(TypeError):
            actor.properties.setdefault('location', LocationId('cave'))

    def test_update_with_core_field_raises(self):
        """Using update with core field should raise."""
        actor = Actor(id=ActorId('test'), name='Test', location=LocationId('start'))
        with self.assertRaises(TypeError):
            actor.properties.update({'health': 100, 'location': LocationId('cave')})

    def test_error_message_includes_correct_usage(self):
        """Error message should guide user to correct syntax."""
        actor = Actor(id=ActorId('test'), name='Test', location=LocationId('start'))
        with self.assertRaises(TypeError) as cm:
            actor.properties['location'] = LocationId('cave')
        self.assertIn('entity.location = value', str(cm.exception))
```

### Success Criteria
- ✅ CoreFieldProtectingDict implemented with all dict methods protected
- ✅ Actor, Item, Location, Part use `_properties` with @property wrapper
- ✅ JSON parsers handle `_properties` correctly
- ✅ LibCST refactoring updates all test constructors
- ✅ Test suite catches ~838 instances of core field misuse (from GH #311)
- ✅ All test code fixed (automatically or manually)
- ✅ All 2039+ tests pass
- ✅ New protection tests verify behavior

### Files Modified
- `src/state_manager.py` - Add CoreFieldProtectingDict, update 4 entity classes, update 4 parsers
- `tests/**/*.py` - Update ~70 test files via LibCST refactoring
- `tests/test_core_field_protection.py` - New test file (18+ test cases)

### Phase 3 Cleanup Plan

This phase WILL cause ~838 test failures (catching real bugs). Here's the systematic cleanup approach:

#### Step 1: Implement Core Field Protection (Expected: 0 failures)
1. Add CoreFieldProtectingDict class to state_manager.py
2. Write tests in test_core_field_protection.py
3. Run tests: `python -m unittest tests/test_core_field_protection.py`
4. **Verify:** 18 new tests pass, no other test failures
5. **Commit:** `git commit -m "Phase 3: Add CoreFieldProtectingDict class and tests"`

#### Step 2: Update Entity Classes (Expected: 0 failures)
1. Update Actor, Item, Location, Part in state_manager.py:
   - Change `properties:` to `_properties:`
   - Add `@property def properties()` wrapper
2. Update parsers: actor_from_dict, item_from_dict, location_from_dict, part_from_dict
3. Run core protection tests: `python -m unittest tests/test_core_field_protection.py`
4. **Verify:** Protection tests still pass
5. **Do NOT run full test suite yet** - expect massive failures
6. **Commit:** `git commit -m "Phase 3: Update entity classes to use _properties with protection"`

#### Step 3: Fix LibCST Refactoring Tool (Expected: Tool works correctly)
1. Edit `tools/refactor_using_LibCST`:
   - Update `RenameKeywordArgInConstructors` class to add `_in_target_call` tracking
   - Add `visit_Call()` method to set flag when in target constructor
   - Add `leave_Call()` method to clear flag
   - Update `leave_Arg()` to only rename if `_in_target_call == True`
2. Test on single file first:
   ```bash
   python tools/refactor_using_LibCST tests/test_actor.py --dry-run
   ```
3. **Verify:** Output shows ONLY `Actor(properties=` → `Actor(_properties=`, nothing else
4. **If problems:** Debug transformer, retest on single file
5. **Commit:** `git commit -m "Phase 3: Fix LibCST transformer to target only specific constructors"`

#### Step 4: Run LibCST on All Tests (Expected: ~70 files modified)
1. Create backup branch: `git checkout -b backup/before-libcst`
2. Return to main branch: `git checkout feature/hook-system-phase-3`
3. Run refactoring in dry-run mode on all tests:
   ```bash
   python tools/refactor_using_LibCST tests/ --dry-run > /tmp/refactor_preview.txt
   ```
4. **Review `/tmp/refactor_preview.txt`:**
   - Check that ONLY `Actor/Item/Location/Part(properties=` → `_properties=` changes
   - Look for any `__properties` (double underscore) - should be NONE
   - Count files to be modified (expect ~70)
5. **If looks good, apply changes:**
   ```bash
   python tools/refactor_using_LibCST tests/
   ```
6. **Verify changes:**
   ```bash
   git diff tests/ | grep "^+" | grep "_properties" | head -20
   ```
7. **Check for double-underscore bug:**
   ```bash
   grep -r "__properties" tests/
   ```
   - Should return NOTHING
8. **Commit:** `git commit -m "Phase 3: Refactor test code to use _properties parameter"`

#### Step 5: Run Tests and Analyze Failures (Expected: ~838 errors)
1. Run full test suite:
   ```bash
   python -m unittest discover tests/ 2>&1 | tee /tmp/test_output.txt
   ```
2. **Expected result:** ~838 errors with TypeError messages like:
   ```
   TypeError: Cannot set core field 'location' via properties dict.
   Use direct attribute access instead (e.g., entity.location = value)
   ```
3. **Analyze error patterns:**
   ```bash
   grep "Cannot set core field" /tmp/test_output.txt | cut -d"'" -f2 | sort | uniq -c
   ```
4. **Document error breakdown** in `/tmp/error_analysis.txt`:
   - Count by field name (location, id, name, inventory, etc.)
   - Count by entity type (Actor, Item, Location, Part)
   - Identify most common patterns
5. **DO NOT COMMIT** - tests are failing

#### Step 6: Fix Test Code Systematically (Expected: Reduce errors to 0)

**Pattern 1: Constructor calls (should be fixed by LibCST)**
- Already fixed in Step 4
- If any remain, fix manually

**Pattern 2: Direct property assignment to core fields (MANUAL FIX)**
```python
# WRONG:
actor.properties['location'] = LocationId('cave')

# CORRECT:
actor.location = LocationId('cave')
```

Search and fix:
```bash
grep -r "\.properties\['location'\]" tests/ | grep "="
```
- For each occurrence, change to direct attribute access
- Repeat for: 'id', 'name', 'inventory', 'behaviors', 'description'

**Pattern 3: Property reads via .get() (MANUAL FIX)**
```python
# WRONG:
loc = actor.properties.get('location')

# CORRECT:
loc = actor.location
```

Search and fix:
```bash
grep -r "\.properties\.get('location')" tests/
```
- Change to direct attribute access
- Repeat for other core fields

**Pattern 4: Nested dict access (MANUAL FIX)**
```python
# WRONG (if 'relationships' field was incorrectly used as core field):
actor.properties['relationships'][player_id] = {...}

# CORRECT (if actually custom property):
if 'relationships' not in actor.properties:
    actor.properties['relationships'] = {}
actor.properties['relationships'][player_id] = {...}
```

**Fix Strategy:**
1. Start with most common error (likely 'location')
2. Fix all occurrences in one test file
3. Run that test file to verify fixes
4. Move to next file
5. After fixing ~20 files, run full suite to check progress
6. Continue until all errors resolved

**Checkpoint commits every ~10 files:**
```bash
git add tests/test_file1.py tests/test_file2.py ...
git commit -m "Phase 3: Fix core field access in test files (batch 1)"
```

#### Step 7: Verify All Tests Pass (Expected: 2039+ tests pass)
1. Run full test suite:
   ```bash
   python -m unittest discover tests/
   ```
2. **Expected:** All tests pass, no errors
3. **Actual test count may be higher** than 2039 (added test_core_field_protection.py tests)
4. **If any failures remain:**
   - Analyze failure messages
   - Fix remaining issues
   - Rerun tests
   - Repeat until clean
5. **Final commit:**
   ```bash
   git commit -m "Phase 3: Complete - all test code fixed, all tests passing"
   ```

#### Step 8: Verify Big Game Still Works (Expected: Game loads and plays)
1. Run big game:
   ```bash
   python -m examples.big_game.game
   ```
2. **Test basic commands:**
   - `look`
   - `inventory`
   - `examine [object]`
   - `go [direction]`
3. **Load existing save file** (if available)
4. **Verify:** Game works normally, no errors
5. **If errors:** Fix and retest

#### Step 9: Final Documentation and Cleanup
1. Update [docs/entity_properties_analysis.md](docs/entity_properties_analysis.md):
   - Document Phase 3 completion
   - Record final test count
   - Note any issues encountered
2. Delete backup branch:
   ```bash
   git branch -D backup/before-libcst
   ```
3. Final commit:
   ```bash
   git add docs/
   git commit -m "Phase 3: Documentation complete"
   ```

#### Rollback Plan (If Things Go Wrong)

If at any point the cleanup becomes unmanageable:

1. **Identify what went wrong:**
   - LibCST created double-underscores?
   - Too many manual fixes needed?
   - Unclear error messages?

2. **Rollback to last good state:**
   ```bash
   git reset --hard backup/before-libcst
   ```

3. **Fix the root cause:**
   - Improve LibCST transformer
   - Add better error messages to CoreFieldProtectingDict
   - Create helper script for common fix patterns

4. **Try again with improved tools**

#### Success Criteria for Phase 3 Cleanup

- ✅ CoreFieldProtectingDict class implemented and tested
- ✅ Entity classes updated to use _properties
- ✅ LibCST tool targets ONLY specific constructors (no double-underscores)
- ✅ All ~838 test errors identified and categorized
- ✅ All test code fixed (constructor calls + core field access)
- ✅ Full test suite passes: 2039+ tests, 0 failures, 0 errors
- ✅ Big game loads and plays normally
- ✅ All changes committed incrementally
- ✅ Documentation updated

#### Estimated Effort

Based on GH #311 experience:
- Steps 1-4: 1-2 hours (infrastructure and tool fixes)
- Step 5: 30 minutes (analysis)
- Step 6: 3-5 hours (fixing 838 errors across ~70 files)
- Steps 7-9: 1 hour (verification and docs)

**Total: 5-8 hours of focused work**

**Key to success:** Systematic approach, frequent commits, clear done criteria for each step.

---

## Implementation Workflow

Per CLAUDE.md Workflow B for large changes:

1. **Issue #307 is the top-level issue** (already exists)
2. **This document is the design** (replaces lost hook_system_redesign.md)
3. **Create Phase 1 issue (#308 - reopen it)**
   - Implement Phase 1 using TDD
   - Comment on issue when complete
4. **Create Phase 2 issue (#309 - reopen it)**
   - Implement Phase 2 using TDD
   - Comment on issue when complete
5. **Create Phase 3 issue (#310 - reopen it)**
   - Implement Phase 3 using TDD
   - Run LibCST refactoring
   - Fix remaining test code manually
   - Comment on issue when complete
6. **Comment on #307 referencing this design doc**

## Risk Assessment

### Risk: LibCST refactoring too broad
**Mitigation:** Run with --dry-run first, manually review changes, use tightly scoped transformer

### Risk: Many test failures in Phase 3
**Expected:** GH #311 showed 838 errors caught by protection
**Mitigation:** This is GOOD - these are real bugs being caught. Fix systematically.

### Risk: Performance impact of @property wrapper
**Assessment:** Negligible - wrapper created once, cached in `_properties`
**Evidence:** GH #311 showed no performance issues

### Risk: Breaking game save compatibility
**Assessment:** No impact - JSON still has `"properties": {...}`, parsers map to `_properties`
**Mitigation:** Test with existing big_game save files

## Success Metrics

After all 3 phases complete:

- ✅ BehaviorManager stores hook definitions
- ✅ 5 validation methods catch authoring errors at load time
- ✅ Core field protection prevents `actor.properties['location']` bugs
- ✅ All 2039+ tests passing
- ✅ No regression in existing functionality
- ✅ Clear error messages guide authors
- ✅ Ready for Phase 4 (adding actual hook definitions to behavior modules)

## Next Steps After Phase 3

Once Phases 1-3 complete:
- **Phase 4:** Add hook_definitions to core behavior modules
- **Phase 5:** Add hook_definitions to infrastructure behaviors
- **Phase 6:** Migrate big_game to new hook system
- **Phase 7:** Create turn_executor module
- **Phase 8:** Delete src/hooks.py and legacy code
- **Phase 9:** Update documentation

Each phase will have its own issue and implementation plan.
