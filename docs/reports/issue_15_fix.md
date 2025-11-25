# Issue #15 Fix: Error Handling for get_* Methods Returning None

## Issue Summary

**Issue #15: Missing error handling for get_* methods returning None**
- **Location:** StateAccessor get methods (behavior_refactoring.md lines 340-364)
- **Problem:** Methods return `Optional[Entity]` but handling isn't consistently documented
- **Impact:** Code examples don't check for None, teaching developers to write buggy code
- **Severity:** HIGH - Examples are teaching material that will be copied

## Root Cause Analysis

The design document contains multiple code examples showing usage of `get_*` methods:

### Examples That Check for None (Correct ✓)
1. Line 148-149: `lock = accessor.get_lock(lock_id); key_hint = lock.properties.get("hint", "a key") if lock else "a key"`
2. Line 1453-1454: `lock = accessor.get_lock(lock_id); if lock and lock.locked:`
3. Line 1682-1684: `item = accessor.get_item(item_id); if item: total += item.properties.get("weight", 0)`

### Examples That Don't Check (Buggy ✗)
1. **Lines 189-195** (brewing example):
   ```python
   actor = accessor.get_actor(actor_id)
   for ingredient_id in recipe.properties.get("ingredients", []):
       if ingredient_id not in actor.inventory:  # ✗ Crash if actor is None
   ```

2. **Line 194** (brewing example):
   ```python
   ingredient = accessor.get_item(ingredient_id)
   messages.append(f"Missing ingredient: {ingredient.name}")  # ✗ Crash if ingredient is None
   ```

3. **Line 1667-1669** (weight checking example):
   ```python
   actor = accessor.get_actor(actor_id)
   current_weight = calculate_inventory_weight(accessor, actor)  # ✗ Passes None
   ```

4. **Line 1987** (doors visibility example):
   ```python
   location = accessor.get_location(location_id)
   for direction, exit_desc in location.exits.items():  # ✗ Crash if location is None
   ```

5. **Line 2018** (hidden doors example):
   ```python
   actor = accessor.get_actor(actor_id)
   if actor.properties.get("detect_hidden", False):  # ✗ Crash if actor is None
   ```

## Risk Assessment

### Risk Categories

#### 1. Low Risk: Infrastructure-Provided IDs
- `get_actor(actor_id)` where actor_id comes from action dict (passed by llm_protocol)
- `get_location(location_id)` where location_id comes from `actor.location` field
- **Should never be None** if game state is consistent
- **Defensive checking still recommended** for robustness

#### 2. Medium Risk: Entity Property References
- `get_lock(lock_id)` where lock_id comes from `entity.properties.get("lock_id")`
- `get_door(door_id)` where door_id comes from `exit_desc.door_id`
- `get_item(item_id)` where item_id comes from `actor.inventory`
- **Can be None** due to data corruption or incomplete setup
- **Must check for None**

#### 3. High Risk: User Input or Computed IDs
- Any IDs derived from user input
- Any computed IDs from game logic
- **Very likely to be None** during normal gameplay
- **Must check for None**

## Proposed Fix

### 1. Add New Documentation Section

Add after StateAccessor Core API section (~line 555 in behavior_refactoring.md):

```markdown
### Error Handling: None Returns from get_* Methods

**Type Contract:** All `get_*` methods return `Optional[Entity]`, meaning they return `None` when the requested entity doesn't exist.

**When None occurs:**
1. **Malformed game data** - Entity references non-existent entity (developer error)
2. **Corrupted state** - Previous operation left dangling references (implementation bug)
3. **Race conditions** - Entity was deleted while being referenced (future multi-user scenarios)

Handlers must treat None returns as error conditions and return appropriate HandlerResult messages.

#### When to Check for None

**ALWAYS check when the ID comes from:**
- Entity properties: `entity.properties.get("lock_id")`
- External references: `exit_desc.door_id`, items from `actor.inventory`
- Computed values or loops
- User input or search results

```python
# Correct pattern for property references
lock_id = container.properties.get("lock_id")
if lock_id:
    lock = accessor.get_lock(lock_id)
    if lock and lock.properties.get("locked", False):
        return HandlerResult(success=False, message="It's locked.")
```

**Optional (but recommended) when the ID comes from:**
- Infrastructure-provided `actor_id` (from action dict passed by llm_protocol)
- Entity location fields: `actor.location`

These *should* never be None if game state is consistent, but defensive checking improves robustness:

```python
# Defensive style (recommended for production code)
actor = accessor.get_actor(actor_id)
if not actor:
    return HandlerResult(success=False, message="Actor not found.")
# Proceed with actor operations

# Trust-based style (acceptable for infrastructure-provided IDs in development)
actor = accessor.get_actor(actor_id)
# Proceed assuming actor is not None
# Will raise AttributeError if assumption is violated (fast failure)
```

#### Anti-Patterns

**DO NOT do this:**
```python
# ✗ BAD: No None check before accessing attributes
actor = accessor.get_actor(actor_id)
for item_id in actor.inventory:  # Crashes with AttributeError if actor is None
    ...

# ✗ BAD: No None check with property reference
lock_id = door.properties.get("lock_id")
lock = accessor.get_lock(lock_id)
if lock.locked:  # Crashes with AttributeError if lock is None
    ...

# ✗ BAD: Assuming get_item always returns an item
ingredient = accessor.get_item(ingredient_id)
messages.append(f"Missing: {ingredient.name}")  # Crashes if ingredient is None
```

**DO this instead:**
```python
# ✓ GOOD: Check before use
actor = accessor.get_actor(actor_id)
if not actor:
    return HandlerResult(success=False, message="Actor not found.")
for item_id in actor.inventory:
    ...

# ✓ GOOD: Check lock exists before checking locked state
lock_id = door.properties.get("lock_id")
if lock_id:
    lock = accessor.get_lock(lock_id)
    if lock and lock.properties.get("locked", False):
        return HandlerResult(success=False, message="The door is locked.")

# ✓ GOOD: Handle missing item gracefully
ingredient = accessor.get_item(ingredient_id)
if not ingredient:
    messages.append(f"Error: Missing ingredient {ingredient_id}")
    continue
messages.append(f"Missing: {ingredient.name}")
```

#### Development vs Production Trade-offs

**Development/Testing:** Trust-based style can be acceptable for infrastructure-provided IDs because:
- Failures produce clear AttributeError tracebacks
- Bugs are caught immediately during testing
- Less defensive code is easier to read

**Production:** Defensive style is strongly recommended because:
- Graceful error messages are better than crashes
- Helps diagnose state corruption issues
- Provides better user experience when data is malformed

**Recommendation:** Start with defensive style by default. Only relax checking for infrastructure-provided IDs after thorough testing proves it's safe.
```

### 2. Fix All Code Examples

#### Fix: Brewing Example (Lines 186-228)

**Before (BUGGY):**
```python
def handle_brew(accessor, action):
    actor_id = action.get("actor_id", "player")
    recipe_name = action.get("object")
    recipe = find_accessible_item(accessor, recipe_name)
    actor = accessor.get_actor(actor_id)  # ✗ No None check
    messages = []

    for ingredient_id in recipe.properties.get("ingredients", []):
        if ingredient_id not in actor.inventory:  # ✗ Crash if actor is None
            ingredient = accessor.get_item(ingredient_id)  # ✗ No None check
            messages.append(f"Missing ingredient: {ingredient.name}")  # ✗ Crash if ingredient is None
            continue

        ingredient = accessor.get_item(ingredient_id)  # ✗ No None check
        accessor.update(
            entity=ingredient,
            changes={"location": "consumed"},
            verb="consume",
            actor_id=actor_id
        )
        accessor.update(
            entity=actor,
            changes={"-inventory": ingredient_id}
        )
        messages.append(f"Added {ingredient.name} to the cauldron.")

    result_id = recipe.properties.get("creates")
    result_item = accessor.get_item(result_id)  # ✗ No None check
    accessor.update(
        entity=result_item,
        changes={"location": actor_id}
    )
```

**After (CORRECT):**
```python
def handle_brew(accessor, action):
    actor_id = action.get("actor_id", "player")
    recipe_name = action.get("object")
    recipe = find_accessible_item(accessor, recipe_name, actor_id)
    if not recipe:
        return HandlerResult(success=False, message="You don't see that recipe here.")

    actor = accessor.get_actor(actor_id)
    if not actor:  # ✓ Check for None
        return HandlerResult(success=False, message="Actor not found.")

    messages = []

    for ingredient_id in recipe.properties.get("ingredients", []):
        if ingredient_id not in actor.inventory:
            ingredient = accessor.get_item(ingredient_id)
            if not ingredient:  # ✓ Check for None
                messages.append(f"Missing ingredient: {ingredient_id} (not found in game)")
                continue
            messages.append(f"Missing ingredient: {ingredient.name}")
            continue

        ingredient = accessor.get_item(ingredient_id)
        if not ingredient:  # ✓ Check for None
            messages.append(f"Error: Ingredient {ingredient_id} not found")
            continue

        # Update ingredient location
        accessor.update(
            entity=ingredient,
            changes={"location": "consumed"},
            verb="consume",
            actor_id=actor_id
        )
        # Update actor inventory
        accessor.update(
            entity=actor,
            changes={"-inventory": ingredient_id}
        )
        messages.append(f"Added {ingredient.name} to the cauldron.")

    if any("Missing" in m or "Error" in m for m in messages):
        return HandlerResult(success=False, message="\n".join(messages))

    result_id = recipe.properties.get("creates")
    result_item = accessor.get_item(result_id)
    if not result_item:  # ✓ Check for None
        return HandlerResult(success=False, message="Recipe result item not found in game data.")

    # Update result item location
    accessor.update(
        entity=result_item,
        changes={"location": actor_id}
    )
    # Update actor inventory
    accessor.update(
        entity=actor,
        changes={"+inventory": result_id}
    )
    messages.append(f"Success! You created a {result_item.name}.")

    return HandlerResult(success=True, message="\n".join(messages))
```

#### Fix: Weight Checking Example (Lines 1664-1685)

**Before (BUGGY):**
```python
def handle_take(accessor, action):
    actor_id = action.get("actor_id", "player")
    item_name = action.get("object")

    item = find_accessible_item(accessor, item_name)
    if item:
        actor = accessor.get_actor(actor_id)  # ✗ No None check
        current_weight = calculate_inventory_weight(accessor, actor)  # ✗ Passes potentially None actor
        item_weight = item.properties.get("weight", 0)
        max_weight = actor.properties.get("max_carry_weight", 100)  # ✗ Crash if actor is None

        if current_weight + item_weight > max_weight:
            return HandlerResult(success=False, message="That would be too heavy to carry.")

    return accessor.invoke_previous_handler("take", action)

def calculate_inventory_weight(accessor, actor):
    """Helper to sum weight of all items in inventory."""
    total = 0
    for item_id in actor.inventory:  # ✗ Crash if actor is None
        item = accessor.get_item(item_id)  # ✗ No None check
        if item:
            total += item.properties.get("weight", 0)
    return total
```

**After (CORRECT):**
```python
def handle_take(accessor, action):
    actor_id = action.get("actor_id", "player")
    item_name = action.get("object")

    item = find_accessible_item(accessor, item_name, actor_id)
    if item:
        actor = accessor.get_actor(actor_id)
        if not actor:  # ✓ Check for None
            return HandlerResult(success=False, message="Actor not found.")

        current_weight = calculate_inventory_weight(accessor, actor)
        item_weight = item.properties.get("weight", 0)
        max_weight = actor.properties.get("max_carry_weight", 100)

        if current_weight + item_weight > max_weight:
            return HandlerResult(success=False, message="That would be too heavy to carry.")

    return accessor.invoke_previous_handler("take", action)

def calculate_inventory_weight(accessor, actor):
    """Helper to sum weight of all items in inventory."""
    if not actor:  # ✓ Defensive check
        return 0

    total = 0
    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item:  # ✓ Already checks for None (correct)
            total += item.properties.get("weight", 0)
    return total
```

#### Fix: Doors Visibility Example (Lines 1984-2004)

**Before (BUGGY):**
```python
def get_doors_in_location(
    accessor: StateAccessor,
    location_id: str = None,
    actor_id: str = "player"
) -> List[Tuple[Door, str]]:
    if location_id is None:
        location_id = accessor.get_current_location(actor_id).id  # ✗ Crash if None

    location = accessor.get_location(location_id)  # ✗ No None check
    doors_with_direction = []

    for direction, exit_desc in location.exits.items():  # ✗ Crash if location is None
        if exit_desc.door_id:
            door = accessor.get_door(exit_desc.door_id)
            if door:  # ✓ Already checks (correct)
                # Apply door visibility rules...
```

**After (CORRECT):**
```python
def get_doors_in_location(
    accessor: StateAccessor,
    location_id: str = None,
    actor_id: str = "player"
) -> List[Tuple[Door, str]]:
    if location_id is None:
        current_location = accessor.get_current_location(actor_id)
        if not current_location:  # ✓ Check for None
            return []  # No location = no doors
        location_id = current_location.id

    location = accessor.get_location(location_id)
    if not location:  # ✓ Check for None
        return []  # Location not found = no doors

    doors_with_direction = []

    for direction, exit_desc in location.exits.items():
        if exit_desc.door_id:
            door = accessor.get_door(exit_desc.door_id)
            if door:  # ✓ Already checks (correct)
                # Apply door visibility rules via behaviors (if any)
                if door.behaviors:
                    context = {"actor_id": actor_id, "location_id": location_id, "direction": direction}
                    visibility_result = accessor.behavior_manager.invoke_behavior(
                        door, "on_query_visibility", accessor, context
                    )
                    if visibility_result and not visibility_result.allow:
                        continue  # Door is hidden from this actor

                doors_with_direction.append((door, direction))

    return doors_with_direction
```

#### Fix: Hidden Doors Example (Lines 2015-2025)

**Before (BUGGY):**
```python
def on_query_visibility(door, accessor, context):
    """Hide doors from actors without detection ability."""
    actor_id = context.get("actor_id")
    actor = accessor.get_actor(actor_id)  # ✗ No None check

    if door.properties.get("hidden", False):
        if not actor.properties.get("detect_hidden", False):  # ✗ Crash if actor is None
            return EventResult(allow=False)

    return EventResult(allow=True)
```

**After (CORRECT):**
```python
def on_query_visibility(door, accessor, context):
    """Hide doors from actors without detection ability."""
    actor_id = context.get("actor_id")
    actor = accessor.get_actor(actor_id)
    if not actor:  # ✓ Check for None
        # No actor = show door by default (shouldn't happen in practice)
        return EventResult(allow=True)

    if door.properties.get("hidden", False):
        if not actor.properties.get("detect_hidden", False):
            return EventResult(allow=False)  # Door is hidden from this actor

    return EventResult(allow=True)  # Show the door
```

### 3. Add Testing Requirements

Add to behavior_refactoring_testing.md after line 385:

```markdown
## Testing None Returns from get_* Methods

Every handler and utility function that uses `get_*` methods must have tests verifying correct None handling.

### Test Pattern for None Returns

```python
def test_handle_unlock_with_missing_lock():
    """Verify graceful handling when lock_id references non-existent lock."""
    state = create_test_state()
    behavior_manager = BehaviorManager()
    accessor = StateAccessor(state, behavior_manager)

    # Create door with lock_id that doesn't exist in state
    door = Door(
        id="door_broken",
        locations=("room", "hall"),
        properties={"lock_id": "missing_lock"}  # This lock doesn't exist
    )
    state.doors["door_broken"] = door

    action = {"actor_id": "player", "object": "broken door"}
    result = handle_unlock(accessor, action)

    # Should fail gracefully, not crash
    assert not result.success
    assert "not found" in result.message.lower() or "no lock" in result.message.lower()

def test_utility_with_missing_item():
    """Verify utilities handle missing items gracefully."""
    state = create_test_state()
    behavior_manager = BehaviorManager()
    accessor = StateAccessor(state, behavior_manager)

    # Put non-existent item ID in actor's inventory (simulates corruption)
    player = state.actors["player"]
    player.inventory.append("missing_item_id")

    # Utility should handle missing item gracefully
    result = calculate_inventory_weight(accessor, player)

    # Should not crash, should skip missing item
    assert isinstance(result, (int, float))

def test_get_actor_with_invalid_id():
    """Verify handler handles missing actor gracefully."""
    state = create_test_state()
    behavior_manager = BehaviorManager()
    accessor = StateAccessor(state, behavior_manager)

    # Try to perform action with non-existent actor
    action = {"actor_id": "nonexistent_npc", "object": "sword"}
    result = handle_take(accessor, action)

    # Should fail gracefully with clear message
    assert not result.success
    assert "actor" in result.message.lower() or "not found" in result.message.lower()
```

### Test Coverage Requirements

For each handler and utility function:

1. **Test with missing entity from property reference:**
   - Create entity with reference to non-existent entity (e.g., `lock_id` pointing to missing lock)
   - Verify graceful failure with appropriate error message

2. **Test with corrupted inventory:**
   - Add non-existent item ID to actor's inventory
   - Verify utility skips missing items without crashing

3. **Test with invalid actor_id:**
   - Call handler with non-existent actor_id
   - Verify graceful failure (for handlers that use infrastructure-provided IDs)

4. **Test with None propagation:**
   - Verify that utilities receiving None parameters either:
     - Check for None and return safe default (e.g., empty list, 0)
     - OR are only called after caller has checked for None

### Common Mistake Tests

These tests catch common developer mistakes:

```python
def test_forgot_to_check_actor():
    """This test should FAIL if developer forgot to check for None."""
    state = create_test_state()
    behavior_manager = BehaviorManager()
    accessor = StateAccessor(state, behavior_manager)

    # Remove player from actors dict (simulates severe corruption)
    del state.actors["player"]

    action = {"actor_id": "player", "object": "sword"}
    result = handle_take(accessor, action)

    # Handler MUST return HandlerResult with success=False
    # Should NOT raise AttributeError
    assert isinstance(result, HandlerResult)
    assert not result.success
```

Add these test requirements to Phase 2a step 6 in implementation guide.
```

### 4. Update Implementation Guide

Add to behavior_refactoring_implementation.md after line 738:

```markdown
   - **Test None returns from get_* methods** - verify handlers handle missing entities:
     - Test handler with lock_id pointing to non-existent lock
     - Test handler with item_id in inventory that doesn't exist (simulates corruption)
     - Test handler with invalid actor_id
     - Test utilities receiving None parameters handle gracefully
     - Verify no AttributeError exceptions are raised (must return HandlerResult instead)
```

Update step 916 checklist:

```markdown
4. **Code review checklist:**
   - [ ] All handlers extract `actor_id` at the top
   - [ ] No string literal `"player"` appears in utility calls
   - [ ] All utility calls pass `actor_id` variable
   - [ ] Type hints match utility function signatures
   - [ ] NPC tests pass for all manipulation commands
   - [ ] **All get_* calls have appropriate None checks**
   - [ ] **Tests verify graceful handling of None returns**
```

## Implementation Checklist

- [ ] Add "Error Handling: None Returns" section to behavior_refactoring.md (~line 555)
- [ ] Fix brewing example (lines 186-228)
- [ ] Fix weight checking example (lines 1664-1685)
- [ ] Fix doors visibility example (lines 1984-2004)
- [ ] Fix hidden doors example (lines 2015-2025)
- [ ] Add testing section to behavior_refactoring_testing.md (after line 385)
- [ ] Update Phase 2a testing requirements in behavior_refactoring_implementation.md (line 738)
- [ ] Update Phase 2b code review checklist (line 916)
- [ ] Review ALL other code examples in behavior_refactoring.md for None checking
- [ ] Mark Issue #15 as FIXED in review document

## Verification

After implementing fixes, verify:

1. **All code examples are correct:**
   - Search for `accessor.get_` in behavior_refactoring.md
   - Verify each usage either checks for None or is documented as safe to skip

2. **Documentation is clear:**
   - Review new "Error Handling: None Returns" section
   - Ensure guidelines distinguish between must-check and optional-check scenarios

3. **Tests are comprehensive:**
   - Review testing requirements in behavior_refactoring_testing.md
   - Ensure test patterns cover all risk categories

4. **Implementation guide is updated:**
   - Phase 2a includes None-handling tests
   - Phase 2b includes None-checking in code review checklist

## Related Issues

This fix addresses:
- Issue #15: Missing error handling for get_* methods returning None
- Partially addresses Issue #34: No tests for utility functions with malformed entities
- Improves Issue #37: No tests for handler return value validation (handlers should return HandlerResult even on errors)
