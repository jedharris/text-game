# Code Path Consolidation Implementation Plan

**Created:** 2025-12-05
**Status:** Planning

## Goals and Use Cases

### Primary Goals
1. **Reduce code duplication** - Eliminate 600-800 lines of repeated logic across handlers
2. **Improve maintainability** - Centralize common patterns so changes happen in one place
3. **Enhance consistency** - Ensure all handlers follow identical patterns for validation, positioning, etc.
4. **Reduce testing burden** - Common utilities tested once, not 20+ times
5. **Improve extensibility** - New handlers can easily reuse established patterns

### Use Cases
- Game authors adding new verb handlers can follow clear patterns
- Developers fixing bugs in validation only need to update one function
- Testing teams can verify core patterns once instead of per-handler
- Code reviewers can quickly identify deviations from standard patterns

## Architecture

### New Utility Modules

All new utilities will be added to existing modules in `utilities/`:

```
utilities/
├── handler_utils.py (EXISTING - will be enhanced)
│   ├── validate_actor_and_location()  # NEW - Phase 1
│   ├── validate_container_access()    # NEW - Phase 4
│   └── build_handler_result()         # NEW - Phase 9
├── positioning.py (EXISTING - no changes)
├── lock_utils.py                      # NEW - Phase 3
│   ├── validate_lock_operation()
│   └── perform_lock_operation()
├── exit_utils.py                      # NEW - Phase 5
│   ├── check_door_blocking()
│   └── perform_exit_movement()
└── utils.py (EXISTING - will be enhanced)
```

### Consolidation Strategy

**Principle:** Extract common patterns into utilities first (TDD), then migrate handlers incrementally.

**Each phase follows this workflow:**
1. Write comprehensive tests for new utility function
2. Implement utility to pass tests
3. Migrate one handler to use utility (verify tests still pass)
4. Migrate remaining handlers one at a time
5. Remove old duplicated code
6. Verify all tests still pass

---

## Phase 1: Actor & Location Validation Helper

**Goal:** Create `validate_actor_and_location()` utility and migrate all 21 handlers

**Estimated Effort:** 2-3 days
**Code Savings:** 400-500 lines
**Risk:** Medium - touches all handlers, but changes are mechanical

### 1.1: Design and Test Utility Function

**Create:** `utilities/handler_utils.py` enhancement

**New function signature:**
```python
def validate_actor_and_location(
    accessor: StateAccessor,
    action: Dict[str, Any],
    require_object: bool = True,
    require_direction: bool = False,
    require_indirect_object: bool = False
) -> Tuple[Optional[str], Optional[Any], Optional[Any], Optional[HandlerResult]]:
    """
    Standard handler preamble: validates actor, location, and required action fields.

    Args:
        accessor: StateAccessor instance
        action: Action dictionary from parser
        require_object: If True, validates 'object' field is present
        require_direction: If True, validates 'direction' field is present
        require_indirect_object: If True, validates 'indirect_object' field is present

    Returns:
        Tuple of (actor_id, actor, location, error_result):
        - If valid: (actor_id, actor, location, None)
        - If error: (None, None, None, HandlerResult with error message)

    Example:
        actor_id, actor, location, error = validate_actor_and_location(
            accessor, action, require_object=True
        )
        if error:
            return error

        # Continue with handler logic using actor_id, actor, location
    """
```

**Tests to write:** `tests/test_handler_utils.py`

```python
class TestValidateActorAndLocation(unittest.TestCase):
    def setUp(self):
        self.state = create_test_state()
        self.accessor = StateAccessor(self.state, None)

    def test_valid_action_with_object(self):
        """Should return actor, location, no error for valid action"""
        action = {"actor_id": "player", "verb": "take", "object": "sword"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action, require_object=True
        )

        self.assertIsNone(error)
        self.assertEqual(actor_id, "player")
        self.assertIsNotNone(actor)
        self.assertIsNotNone(location)

    def test_missing_object_when_required(self):
        """Should return error when object is required but missing"""
        action = {"actor_id": "player", "verb": "take"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action, require_object=True
        )

        self.assertIsNone(actor_id)
        self.assertIsNone(actor)
        self.assertIsNone(location)
        self.assertIsNotNone(error)
        self.assertFalse(error.success)
        self.assertIn("What do you want to", error.message)

    def test_missing_actor_id_defaults_to_player(self):
        """Should default to 'player' when actor_id not in action"""
        action = {"verb": "take", "object": "sword"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action, require_object=True
        )

        self.assertIsNone(error)
        self.assertEqual(actor_id, "player")

    def test_nonexistent_actor(self):
        """Should return INCONSISTENT STATE error for missing actor"""
        action = {"actor_id": "ghost", "verb": "take", "object": "sword"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action, require_object=True
        )

        self.assertIsNone(actor_id)
        self.assertIsNotNone(error)
        self.assertIn("INCONSISTENT STATE", error.message)
        self.assertIn("Actor ghost not found", error.message)

    def test_actor_without_location(self):
        """Should return INCONSISTENT STATE error when location not found"""
        # Create actor with invalid location
        self.state.actors["orphan"] = Actor(
            id="orphan", name="Orphan", description="Lost",
            location="nowhere", inventory=[]
        )

        action = {"actor_id": "orphan", "verb": "take", "object": "sword"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action, require_object=True
        )

        self.assertIsNone(actor_id)
        self.assertIsNotNone(error)
        self.assertIn("INCONSISTENT STATE", error.message)
        self.assertIn("Cannot find location", error.message)

    def test_require_direction_present(self):
        """Should validate direction field when required"""
        action = {"actor_id": "player", "verb": "go", "direction": "north"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action, require_direction=True
        )

        self.assertIsNone(error)

    def test_require_direction_missing(self):
        """Should return error when direction required but missing"""
        action = {"actor_id": "player", "verb": "go"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action, require_direction=True
        )

        self.assertIsNotNone(error)
        self.assertIn("Which direction", error.message)

    def test_require_indirect_object_present(self):
        """Should validate indirect_object field when required"""
        action = {
            "actor_id": "player",
            "verb": "unlock",
            "object": "door",
            "indirect_object": "key"
        }
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action,
            require_object=True,
            require_indirect_object=True
        )

        self.assertIsNone(error)

    def test_require_indirect_object_missing(self):
        """Should return error when indirect_object required but missing"""
        action = {"actor_id": "player", "verb": "unlock", "object": "door"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action,
            require_object=True,
            require_indirect_object=True
        )

        self.assertIsNotNone(error)
        self.assertIn("What do you want to unlock it with", error.message)

    def test_no_requirements(self):
        """Should work with no field requirements (like 'look')"""
        action = {"actor_id": "player", "verb": "look"}
        actor_id, actor, location, error = validate_actor_and_location(
            self.accessor, action,
            require_object=False,
            require_direction=False
        )

        self.assertIsNone(error)
        self.assertIsNotNone(actor)
        self.assertIsNotNone(location)
```

### 1.2: Implement Utility Function

**Implementation in utilities/handler_utils.py:**

```python
from typing import Dict, Any, Optional, Tuple
from src.state_accessor import StateAccessor
from src.models import HandlerResult

def validate_actor_and_location(
    accessor: StateAccessor,
    action: Dict[str, Any],
    require_object: bool = True,
    require_direction: bool = False,
    require_indirect_object: bool = False
) -> Tuple[Optional[str], Optional[Any], Optional[Any], Optional[HandlerResult]]:
    """Standard handler preamble: validates actor, location, and required action fields."""

    # Extract actor_id with default
    actor_id = action.get("actor_id", "player")

    # Validate required fields
    verb = action.get("verb", "do something")

    if require_object and not action.get("object"):
        return None, None, None, HandlerResult(
            success=False,
            message=f"What do you want to {verb}?"
        )

    if require_direction and not action.get("direction"):
        return None, None, None, HandlerResult(
            success=False,
            message="Which direction do you want to go?"
        )

    if require_indirect_object and not action.get("indirect_object"):
        obj_name = action.get("object", "it")
        return None, None, None, HandlerResult(
            success=False,
            message=f"What do you want to {verb} {obj_name} with?"
        )

    # Validate actor exists
    actor = accessor.get_actor(actor_id)
    if not actor:
        return None, None, None, HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Validate location exists
    location = accessor.get_current_location(actor_id)
    if not location:
        return None, None, None, HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Cannot find location for actor {actor_id}"
        )

    return actor_id, actor, location, None
```

**TDD Steps:**
1. Write all tests (should fail)
2. Implement function
3. Run tests (should pass)
4. Verify coverage: `python -m coverage run -m unittest tests.test_handler_utils.TestValidateActorAndLocation`

### 1.3: Migrate First Handler (handle_take)

**Update:** `behaviors/core/manipulation.py` lines 107-134

**Before:**
```python
def handle_take(accessor, action):
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")

    if not object_name:
        return HandlerResult(success=False, message="What do you want to take?")

    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    location = accessor.get_current_location(actor_id)
    if not location:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Cannot find location for actor {actor_id}"
        )

    # Rest of handler...
```

**After:**
```python
from utilities.handler_utils import validate_actor_and_location

def handle_take(accessor, action):
    # Validate actor and location
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    object_name = action.get("object")

    # Rest of handler...
```

**Verification:**
1. Run existing tests: `python -m unittest tests.test_phase1 -v`
2. Ensure all handle_take tests still pass
3. Check that error messages are identical

### 1.4: Migrate Remaining 20 Handlers

**Files to update:**
- `behaviors/core/manipulation.py`: handle_drop (269-301), handle_give (367-406), handle_put (489-527)
- `behaviors/core/exits.py`: handle_go (112-133), handle_climb (276-293)
- `behaviors/core/spatial.py`: handle_approach (113-137), handle_take_cover (194-217), handle_hide_in (271-294), handle_climb (349-373)
- `behaviors/core/perception.py`: handle_examine (149-176), handle_inventory (454-463)
- `behaviors/core/interaction.py`: handle_open, handle_close, handle_use (308-324), handle_read, handle_pull, handle_push
- `behaviors/core/locks.py`: handle_unlock, handle_lock
- `behaviors/core/consumables.py`: handle_drink (63-77), handle_eat (124-138)
- `behaviors/core/combat.py`: handle_attack (54-78)

**For each handler:**
1. Update to use `validate_actor_and_location()`
2. Run that handler's tests
3. Verify all pass
4. Move to next handler

**Note:** Some handlers need different parameters:
- `handle_go`, `handle_climb`: `require_direction=True, require_object=False`
- `handle_look`: `require_object=False, require_direction=False`
- `handle_unlock`, `handle_lock`: May need `require_indirect_object=True`

### 1.5: Phase 1 Success Criteria

- [ ] All 11 tests for `validate_actor_and_location()` pass
- [ ] All 21 handlers migrated to use utility
- [ ] All existing handler tests still pass (990+ tests)
- [ ] Code reduction: 400-500 lines removed
- [ ] No behavioral changes - all error messages identical

---

## Phase 2: Consumables Handler Consolidation

**Goal:** Merge handle_drink and handle_eat into shared implementation

**Estimated Effort:** 0.5 days
**Code Savings:** 50-60 lines
**Risk:** Low - only 2 handlers, well-isolated

### 2.1: Create Generic Consume Handler

**Tests:** `tests/test_consumables.py` (enhance existing)

```python
class TestConsumeHelper(unittest.TestCase):
    """Tests for the generic handle_consume helper"""

    def test_consume_drinkable_item(self):
        """Should handle drinking a drinkable item"""
        # Test the helper function directly
        result = handle_consume(
            self.accessor,
            {"actor_id": "player", "verb": "drink", "object": "water"},
            property_name="drinkable",
            verb="drink"
        )
        self.assertTrue(result.success)

    def test_consume_edible_item(self):
        """Should handle eating an edible item"""
        result = handle_consume(
            self.accessor,
            {"actor_id": "player", "verb": "eat", "object": "apple"},
            property_name="edible",
            verb="eat"
        )
        self.assertTrue(result.success)

    def test_consume_non_consumable_property(self):
        """Should reject items without the required property"""
        result = handle_consume(
            self.accessor,
            {"actor_id": "player", "verb": "eat", "object": "sword"},
            property_name="edible",
            verb="eat"
        )
        self.assertFalse(result.success)
        self.assertIn("can't eat", result.message.lower())

    def test_consume_removes_from_inventory(self):
        """Should remove consumed item from inventory"""
        # Put item in inventory first
        # ... test setup ...

        result = handle_consume(
            self.accessor,
            {"actor_id": "player", "verb": "drink", "object": "potion"},
            property_name="drinkable",
            verb="drink"
        )

        actor = self.accessor.get_actor("player")
        self.assertNotIn("item_potion", actor.inventory)
```

### 2.2: Implement Shared Handler

**In:** `behaviors/core/consumables.py`

```python
def handle_consume(
    accessor,
    action: Dict[str, Any],
    property_name: str,
    verb: str
) -> HandlerResult:
    """
    Generic consumable handler for drinkable/edible items.

    Args:
        accessor: StateAccessor instance
        action: Action dict from parser
        property_name: Property to check ("drinkable" or "edible")
        verb: Verb for messages ("drink" or "eat")
    """
    # Use Phase 1 utility
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    object_name = action.get("object")

    # Find item in inventory
    item = find_item_in_inventory(accessor, object_name, actor_id)
    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't have any {object_name}."
        )

    # Check if item has the required property
    if not item.properties.get(property_name, False):
        return HandlerResult(
            success=False,
            message=f"You can't {verb} the {item.name}."
        )

    # Apply implicit positioning (items in hand don't need positioning)
    moved, move_msg = try_implicit_positioning(accessor, actor_id, item)

    # Invoke behaviors
    result = accessor.update(item, {}, verb=verb, actor_id=actor_id)

    if not result.success:
        return HandlerResult(success=False, message=result.message)

    # Remove from inventory and set location to "consumed"
    accessor.update(
        entity=item,
        changes={"location": "consumed"}
    )
    accessor.update(
        entity=actor,
        changes={"-inventory": item.id}
    )

    # Build response message
    base_message = f"You {verb} the {item.name}."
    if result.message:
        message = f"{base_message} {result.message}"
    else:
        message = base_message

    data = serialize_for_handler_result(item)
    return HandlerResult(success=True, message=message, data=data)


def handle_drink(accessor, action):
    """Handle drinking liquids."""
    return handle_consume(accessor, action, property_name="drinkable", verb="drink")


def handle_eat(accessor, action):
    """Handle eating food."""
    return handle_consume(accessor, action, property_name="edible", verb="eat")
```

### 2.3: Verify and Clean Up

1. Run all consumables tests: `python -m unittest tests.test_consumables -v`
2. Verify handle_drink and handle_eat still work identically
3. Remove old implementations
4. Verify line count reduction (~50-60 lines)

### 2.4: Phase 2 Success Criteria

- [ ] Generic `handle_consume()` implemented and tested
- [ ] Both handle_drink and handle_eat use shared implementation
- [ ] All existing consumables tests pass
- [ ] Code reduced by 50-60 lines

---

## Phase 3: Lock Operation Consolidation

**Goal:** Create shared lock/unlock validation and state management

**Estimated Effort:** 1-1.5 days
**Code Savings:** 80-100 lines
**Risk:** Medium - locks are complex with door items vs containers

### 3.1: Create Lock Utilities Module

**Create:** `utilities/lock_utils.py`

**Tests:** `tests/test_lock_utils.py`

```python
class TestValidateLockOperation(unittest.TestCase):
    def test_unlock_door_item_with_key(self):
        """Should validate unlocking a locked door with correct key"""
        # Test setup: locked door, player has key
        valid, error_msg, lock = validate_lock_operation(
            accessor=self.accessor,
            entity=self.door_item,
            actor_id="player",
            operation="unlock"
        )

        self.assertTrue(valid)
        self.assertIsNone(error_msg)
        self.assertIsNotNone(lock)

    def test_unlock_already_unlocked(self):
        """Should return error when door is already unlocked"""
        valid, error_msg, lock = validate_lock_operation(
            accessor=self.accessor,
            entity=self.unlocked_door,
            actor_id="player",
            operation="unlock"
        )

        self.assertFalse(valid)
        self.assertIn("isn't locked", error_msg)

    def test_lock_without_key(self):
        """Should return error when actor doesn't have key"""
        valid, error_msg, lock = validate_lock_operation(
            accessor=self.accessor,
            entity=self.door_item,
            actor_id="player",
            operation="lock"
        )

        self.assertFalse(valid)
        self.assertIn("don't have the key", error_msg)

    def test_container_lock_operation(self):
        """Should validate locking a container"""
        valid, error_msg, lock = validate_lock_operation(
            accessor=self.accessor,
            entity=self.chest,
            actor_id="player",
            operation="lock"
        )

        # Test based on whether player has key

    def test_entity_without_lock(self):
        """Should return error for entity with no lock"""
        valid, error_msg, lock = validate_lock_operation(
            accessor=self.accessor,
            entity=self.table,  # Regular item, no lock
            actor_id="player",
            operation="unlock"
        )

        self.assertFalse(valid)
        self.assertIn("has no lock", error_msg)


class TestPerformLockOperation(unittest.TestCase):
    def test_perform_unlock_door_item(self):
        """Should unlock a door item"""
        success, message = perform_lock_operation(
            accessor=self.accessor,
            entity=self.locked_door,
            lock=self.lock,
            operation="unlock"
        )

        self.assertTrue(success)
        self.assertFalse(self.locked_door.door_locked)

    def test_perform_lock_container(self):
        """Should lock a container"""
        success, message = perform_lock_operation(
            accessor=self.accessor,
            entity=self.chest,
            lock=self.lock,
            operation="lock"
        )

        self.assertTrue(success)
        self.assertTrue(self.chest.container["locked"])
```

### 3.2: Implement Lock Utilities

**Implementation:**

```python
from typing import Tuple, Optional, Any
from src.models import HandlerResult

def validate_lock_operation(
    accessor,
    entity: Any,
    actor_id: str,
    operation: str  # "lock" or "unlock"
) -> Tuple[bool, Optional[str], Optional[Any]]:
    """
    Validates that a lock operation can be performed.

    Returns:
        Tuple of (valid, error_message, lock):
        - If valid: (True, None, Lock)
        - If invalid: (False, error_message, None)
    """
    actor = accessor.get_actor(actor_id)

    # Check if entity is a door item
    if hasattr(entity, 'is_door') and entity.is_door:
        # Check current state
        currently_locked = entity.door_locked

        if operation == "unlock" and not currently_locked:
            return False, f"The {entity.name} isn't locked.", None
        if operation == "lock" and currently_locked:
            return False, f"The {entity.name} is already locked.", None

        # Check for lock
        if not entity.door_lock_id:
            return False, f"The {entity.name} has no lock.", None

        lock = accessor.get_lock(entity.door_lock_id)
        if not lock:
            return False, f"INCONSISTENT STATE: Lock {entity.door_lock_id} not found", None

        # Check for key
        has_key = any(key_id in actor.inventory for key_id in lock.opens_with)
        if not has_key:
            key_names = [accessor.get_item(kid).name for kid in lock.opens_with if accessor.get_item(kid)]
            if key_names:
                return False, f"You don't have the key. You need: {', '.join(key_names)}", None
            else:
                return False, "You don't have the key.", None

        return True, None, lock

    # Check if entity is a container
    elif entity.properties.get("container"):
        container = entity.container
        currently_locked = container.get("locked", False)

        if operation == "unlock" and not currently_locked:
            return False, f"The {entity.name} isn't locked.", None
        if operation == "lock" and currently_locked:
            return False, f"The {entity.name} is already locked.", None

        # Check for lock
        lock_id = container.get("lock_id")
        if not lock_id:
            return False, f"The {entity.name} has no lock.", None

        lock = accessor.get_lock(lock_id)
        if not lock:
            return False, f"INCONSISTENT STATE: Lock {lock_id} not found", None

        # Check for key
        has_key = any(key_id in actor.inventory for key_id in lock.opens_with)
        if not has_key:
            return False, "You don't have the key.", None

        return True, None, lock

    else:
        return False, f"The {entity.name} has no lock.", None


def perform_lock_operation(
    accessor,
    entity: Any,
    lock: Any,
    operation: str
) -> Tuple[bool, str]:
    """
    Performs the lock operation (changes state).

    Returns:
        Tuple of (success, message)
    """
    new_state = (operation == "lock")

    # Update door item
    if hasattr(entity, 'is_door') and entity.is_door:
        old_state = entity.door_locked
        entity.door_locked = new_state

        # Verify state changed
        if entity.door_locked == old_state:
            return False, "Failed to change lock state"

        action_word = "lock" if new_state else "unlock"
        return True, f"You {action_word} the {entity.name}."

    # Update container
    elif entity.properties.get("container"):
        entity.container["locked"] = new_state
        action_word = "lock" if new_state else "unlock"
        return True, f"You {action_word} the {entity.name}."

    return False, "Cannot perform lock operation"
```

### 3.3: Migrate Lock Handlers

**Update:** `behaviors/core/locks.py`

**Before:** Lines 76-155 (handle_unlock), 182-272 (handle_lock) - very long and duplicated

**After:**
```python
from utilities.lock_utils import validate_lock_operation, perform_lock_operation
from utilities.handler_utils import validate_actor_and_location

def handle_unlock(accessor, action):
    """Handle unlocking locks."""
    # Standard validation
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    object_name = action.get("object")

    # Find the entity
    item, position_msg = find_and_position_item(
        accessor, actor_id, object_name
    )

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Validate lock operation
    valid, error_msg, lock = validate_lock_operation(
        accessor, item, actor_id, operation="unlock"
    )

    if not valid:
        return HandlerResult(success=False, message=error_msg)

    # Perform the operation
    success, message = perform_lock_operation(
        accessor, item, lock, operation="unlock"
    )

    if not success:
        return HandlerResult(success=False, message=message)

    # Build final message with positioning
    final_message = build_message_with_positioning([message], position_msg)

    data = serialize_for_handler_result(item)
    return HandlerResult(success=True, message=final_message, data=data)


def handle_lock(accessor, action):
    """Handle locking locks."""
    # Nearly identical to handle_unlock, just pass operation="lock"
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    object_name = action.get("object")

    item, position_msg = find_and_position_item(
        accessor, actor_id, object_name
    )

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    valid, error_msg, lock = validate_lock_operation(
        accessor, item, actor_id, operation="lock"
    )

    if not valid:
        return HandlerResult(success=False, message=error_msg)

    success, message = perform_lock_operation(
        accessor, item, lock, operation="lock"
    )

    if not success:
        return HandlerResult(success=False, message=message)

    final_message = build_message_with_positioning([message], position_msg)

    data = serialize_for_handler_result(item)
    return HandlerResult(success=True, message=final_message, data=data)
```

### 3.4: Phase 3 Success Criteria

- [ ] `lock_utils.py` created with 2 functions
- [ ] 20+ tests for lock utilities pass
- [ ] Both lock handlers migrated and simplified
- [ ] All existing lock tests pass
- [ ] Code reduced by 80-100 lines

---

## Phase 4: Container Validation Helper

**Goal:** Standardize container finding and validation

**Estimated Effort:** 0.5-1 day
**Code Savings:** 40-50 lines
**Risk:** Low - well-defined pattern

### 4.1: Create Container Utility

**Add to:** `utilities/handler_utils.py`

**Tests:** `tests/test_handler_utils.py`

```python
class TestValidateContainerAccess(unittest.TestCase):
    def test_find_valid_container(self):
        """Should find and validate accessible container"""
        container, error = validate_container_access(
            accessor=self.accessor,
            container_name="chest",
            container_adjective=None,
            location_id="loc_room",
            must_be_open=True
        )

        self.assertIsNotNone(container)
        self.assertIsNone(error)

    def test_container_is_closed(self):
        """Should return error when container is closed and must be open"""
        container, error = validate_container_access(
            accessor=self.accessor,
            container_name="chest",
            container_adjective=None,
            location_id="loc_room",
            must_be_open=True
        )

        self.assertIsNone(container)
        self.assertIn("closed", error)

    def test_item_exists_but_not_container(self):
        """Should return specific error when item exists but isn't a container"""
        container, error = validate_container_access(
            accessor=self.accessor,
            container_name="sword",  # Not a container
            container_adjective=None,
            location_id="loc_room",
            must_be_open=False
        )

        self.assertIsNone(container)
        self.assertIn("not a container", error)

    def test_surface_doesnt_require_open(self):
        """Should allow access to surface even when 'closed'"""
        container, error = validate_container_access(
            accessor=self.accessor,
            container_name="table",  # is_surface=True
            container_adjective=None,
            location_id="loc_room",
            must_be_open=True
        )

        self.assertIsNotNone(container)
        self.assertIsNone(error)
```

**Implementation:**

```python
def validate_container_access(
    accessor,
    container_name: str,
    container_adjective: Optional[str],
    location_id: str,
    must_be_open: bool = True
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Find and validate container access.

    Returns:
        Tuple of (container, error_message):
        - If valid: (container, None)
        - If invalid: (None, error_message)
    """
    from utilities.utils import find_container_with_adjective, name_matches

    # Try to find as container
    container = find_container_with_adjective(
        accessor, container_name, container_adjective, location_id
    )

    if not container:
        # Check if item exists but isn't a container
        location = accessor.get_location(location_id)
        if location:
            for item_id in location.items:
                item = accessor.get_item(item_id)
                if item and name_matches(container_name, item.name):
                    return None, f"The {item.name} is not a container."

        return None, f"You don't see any {container_name} here."

    # Check if container must be open
    container_info = container.properties.get("container", {})
    is_surface = container_info.get("is_surface", False)

    if must_be_open and not is_surface:
        if not container_info.get("open", False):
            return None, f"The {container.name} is closed."

    return container, None
```

### 4.2: Migrate Container Usage

**Update:** `behaviors/core/manipulation.py`
- Lines 136-173 in handle_take
- Lines 529-567 in handle_put

**Before (handle_put, lines 529-567):**
```python
# Find container
container = find_container_with_adjective(accessor, container_name, container_adjective, location.id)

if not container:
    # Check if item exists but isn't a container
    for item in accessor.get_items_in_location(location.id):
        if name_matches(container_name, item.name):
            return HandlerResult(
                success=False,
                message=f"The {item.name} is not a container."
            )
    return HandlerResult(
        success=False,
        message=f"You don't see any {container_name} here."
    )

# Check if container is open
container_info = container.properties.get("container", {})
is_surface = container_info.get("is_surface", False)

if not is_surface and not container_info.get("open", False):
    return HandlerResult(
        success=False,
        message=f"The {container.name} is closed."
    )
```

**After:**
```python
from utilities.handler_utils import validate_container_access

# Find and validate container
container, error_msg = validate_container_access(
    accessor, container_name, container_adjective, location.id, must_be_open=True
)

if not container:
    return HandlerResult(success=False, message=error_msg)
```

### 4.3: Phase 4 Success Criteria

- [ ] `validate_container_access()` implemented and tested
- [ ] handle_take and handle_put migrated
- [ ] All manipulation tests pass
- [ ] Code reduced by 40-50 lines

---

## Phase 5: Exit Movement Consolidation

**Goal:** Extract common exit movement logic

**Estimated Effort:** 1 day
**Code Savings:** 60-80 lines
**Risk:** Medium - movement is complex with door checking

### 5.1: Create Exit Utilities

**Create:** `utilities/exit_utils.py`

**Tests:** `tests/test_exit_utils.py`

```python
class TestCheckDoorBlocking(unittest.TestCase):
    def test_no_door(self):
        """Should pass when exit has no door"""
        blocked, message = check_door_blocking(
            accessor=self.accessor,
            exit_descriptor=self.open_exit
        )

        self.assertFalse(blocked)
        self.assertIsNone(message)

    def test_open_door(self):
        """Should pass when door is open"""
        blocked, message = check_door_blocking(
            accessor=self.accessor,
            exit_descriptor=self.exit_with_open_door
        )

        self.assertFalse(blocked)
        self.assertIsNone(message)

    def test_closed_door(self):
        """Should block when door is closed"""
        blocked, message = check_door_blocking(
            accessor=self.accessor,
            exit_descriptor=self.exit_with_closed_door
        )

        self.assertTrue(blocked)
        self.assertIn("closed", message)


class TestPerformExitMovement(unittest.TestCase):
    def test_basic_movement(self):
        """Should move actor and invoke on_enter behaviors"""
        result = perform_exit_movement(
            accessor=self.accessor,
            actor=self.actor,
            destination_id="loc_forest",
            direction_name="north",
            exit_descriptor=self.exit,
            verb="go"
        )

        self.assertTrue(result.success)
        self.assertEqual(self.actor.location, "loc_forest")

    def test_movement_clears_posture(self):
        """Should clear actor posture when moving"""
        self.actor.properties["posture"] = "climbing"

        result = perform_exit_movement(
            accessor=self.accessor,
            actor=self.actor,
            destination_id="loc_forest",
            direction_name="north",
            exit_descriptor=self.exit,
            verb="go"
        )

        self.assertIsNone(self.actor.properties.get("posture"))

    def test_on_enter_behaviors_invoked(self):
        """Should invoke on_enter behaviors on destination"""
        # Create destination with on_enter behavior
        # Verify behavior gets called
```

**Implementation:**

```python
from typing import Tuple, Optional, Any
from src.models import HandlerResult

def check_door_blocking(
    accessor,
    exit_descriptor: Any
) -> Tuple[bool, Optional[str]]:
    """
    Check if a door is blocking the exit.

    Returns:
        Tuple of (is_blocked, error_message):
        - If not blocked: (False, None)
        - If blocked: (True, error_message)
    """
    if exit_descriptor.type != 'door' or not exit_descriptor.door_id:
        return False, None

    # Try new-style door item first
    door_item = accessor.get_door_item(exit_descriptor.door_id)
    if door_item:
        if not door_item.door_open:
            return True, f"The {door_item.name} is closed."
        return False, None

    # Fall back to old-style Door entity
    door = accessor.get_door(exit_descriptor.door_id)
    if door and not door.open:
        return True, f"The {door.description or 'door'} is closed."

    return False, None


def perform_exit_movement(
    accessor,
    actor: Any,
    destination_id: str,
    direction_name: str,
    exit_descriptor: Any,
    verb: str  # "go" or "climb"
) -> HandlerResult:
    """
    Perform actor movement through an exit.

    Handles:
    - Moving actor to destination
    - Clearing posture
    - Invoking on_enter behaviors
    - Building result message with auto-look
    """
    from utilities.utils import serialize_for_handler_result

    # Get destination
    destination = accessor.get_location(destination_id)
    if not destination:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Destination {destination_id} not found"
        )

    # Move actor
    old_location = actor.location
    actor.location = destination_id

    # Clear posture
    if "posture" in actor.properties:
        actor.properties["posture"] = None

    # Invoke on_enter behaviors for the exit
    on_enter_result = accessor.invoke_behavior(
        "on_enter",
        exit_descriptor,
        actor.id
    )

    behavior_message = ""
    if on_enter_result and on_enter_result.message:
        behavior_message = on_enter_result.message + " "

    # Build message
    verb_past = "climbed" if verb == "climb" else "went"
    message = f"{behavior_message}You {verb_past} {direction_name}."

    # Serialize new location for auto-look
    data = serialize_for_handler_result(destination)

    return HandlerResult(success=True, message=message, data=data)
```

### 5.2: Migrate Exit Handlers

**Update:** `behaviors/core/exits.py`

**Before:** Lines 86-252 (handle_go), 255-379 (handle_climb)

**After (handle_go):**
```python
from utilities.exit_utils import check_door_blocking, perform_exit_movement
from utilities.handler_utils import validate_actor_and_location

def handle_go(accessor, action):
    """Handle movement between locations."""
    # Validate actor and direction
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_direction=True, require_object=False
    )
    if error:
        return error

    direction = action.get("direction")
    direction_name = direction.word if hasattr(direction, 'word') else str(direction)

    # Find exit
    exit_descriptor = find_exit(accessor, location, direction_name)
    if not exit_descriptor:
        return HandlerResult(
            success=False,
            message=f"You can't go {direction_name} from here."
        )

    # Check for door blocking
    blocked, block_message = check_door_blocking(accessor, exit_descriptor)
    if blocked:
        return HandlerResult(success=False, message=block_message)

    # Perform movement
    return perform_exit_movement(
        accessor, actor, exit_descriptor.to, direction_name, exit_descriptor, "go"
    )
```

**Similar changes for handle_climb**

### 5.3: Phase 5 Success Criteria

- [ ] `exit_utils.py` created with 2 functions
- [ ] 15+ tests for exit utilities pass
- [ ] Both exit handlers migrated and simplified
- [ ] All existing exit tests pass
- [ ] Code reduced by 60-80 lines

---

## Phase 6: Interaction Handler Quartet

**Goal:** Consolidate use/pull/push/read handlers

**Estimated Effort:** 0.5-1 day
**Code Savings:** 40-50 lines
**Risk:** Low - handlers are very similar

### 6.1: Create Generic Interaction Handler

**Update:** `behaviors/core/interaction.py`

**Tests:** Enhance `tests/test_phase9_entity_behaviors.py`

```python
class TestGenericInteraction(unittest.TestCase):
    def test_use_item(self):
        """Should handle generic 'use' action"""
        result = handle_simple_interaction(
            self.accessor,
            {"actor_id": "player", "verb": "use", "object": "wand"},
            verb="use"
        )
        self.assertTrue(result.success)

    def test_pull_item(self):
        """Should handle generic 'pull' action"""
        result = handle_simple_interaction(
            self.accessor,
            {"actor_id": "player", "verb": "pull", "object": "lever"},
            verb="pull"
        )
        self.assertTrue(result.success)

    def test_push_item(self):
        """Should handle generic 'push' action"""
        result = handle_simple_interaction(
            self.accessor,
            {"actor_id": "player", "verb": "push", "object": "button"},
            verb="push"
        )
        self.assertTrue(result.success)
```

**Implementation:**

```python
def handle_simple_interaction(accessor, action, verb: str) -> HandlerResult:
    """
    Generic handler for simple interactions (use, pull, push).

    Args:
        accessor: StateAccessor instance
        action: Action dict
        verb: The verb being performed
    """
    from utilities.handler_utils import validate_actor_and_location
    from utilities.positioning import find_and_position_item
    from utilities.utils import serialize_for_handler_result

    # Validate
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    object_name = action.get("object")

    # Find and position
    item, position_msg = find_and_position_item(accessor, actor_id, object_name)

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Invoke behaviors
    result = accessor.update(item, {}, verb=verb, actor_id=actor_id)

    if not result.success:
        return HandlerResult(success=False, message=result.message)

    # Build message
    base_message = f"You {verb} the {item.name}."
    message_parts = [base_message]

    if result.message:
        message_parts.append(result.message)

    final_message = build_message_with_positioning(message_parts, position_msg)

    data = serialize_for_handler_result(item)
    return HandlerResult(success=True, message=final_message, data=data)


def handle_use(accessor, action):
    """Handle using items."""
    return handle_simple_interaction(accessor, action, "use")


def handle_pull(accessor, action):
    """Handle pulling items."""
    return handle_simple_interaction(accessor, action, "pull")


def handle_push(accessor, action):
    """Handle pushing items."""
    return handle_simple_interaction(accessor, action, "push")


def handle_read(accessor, action):
    """Handle reading items - has custom logic for text property."""
    from utilities.handler_utils import validate_actor_and_location
    from utilities.positioning import find_and_position_item
    from utilities.utils import serialize_for_handler_result

    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    object_name = action.get("object")
    item, position_msg = find_and_position_item(accessor, actor_id, object_name)

    if not item:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Check if readable
    if not item.properties.get("readable", False):
        return HandlerResult(
            success=False,
            message=f"The {item.name} has nothing to read."
        )

    # Get text content
    text = item.properties.get("text", "")
    if not text:
        return HandlerResult(
            success=False,
            message=f"The {item.name} is blank."
        )

    # Invoke behaviors
    result = accessor.update(item, {}, verb="read", actor_id=actor_id)

    # Build message with text
    message_parts = [f'You read the {item.name}: "{text}"']
    if result.message:
        message_parts.append(result.message)

    final_message = build_message_with_positioning(message_parts, position_msg)

    data = serialize_for_handler_result(item)
    return HandlerResult(success=True, message=final_message, data=data)
```

### 6.2: Phase 6 Success Criteria

- [ ] `handle_simple_interaction()` implemented
- [ ] use/pull/push handlers use shared implementation
- [ ] read handler simplified with custom logic
- [ ] All interaction tests pass
- [ ] Code reduced by 40-50 lines

---

## Phase 7: Spatial Positioning Handler Pattern

**Goal:** Extract common positioning handler pattern

**Estimated Effort:** 1.5-2 days
**Code Savings:** 150-200 lines
**Risk:** Medium-High - spatial handlers have variations

### 7.1: Analyze Spatial Handler Patterns

All four handlers (approach, take_cover, hide_in, climb) follow this pattern:
1. Validate actor/location
2. Find target entity (items, parts, or both)
3. Check property requirements
4. Check accessibility
5. Set focused_on and posture
6. Return result

**Differences:**
- **approach**: No property check, no posture, finds items/parts/actors
- **take_cover**: Requires `provides_cover=true`, sets `posture="cover"`
- **hide_in**: Requires `allows_concealment=true`, sets `posture="concealed"`
- **climb**: Requires `climbable=true`, sets `posture="climbing"`

### 7.2: Create Positioning Utility

**Add to:** `utilities/positioning.py`

**Tests:** `tests/test_positioning_helpers.py`

```python
class TestHandlePositioningAction(unittest.TestCase):
    def test_approach_item(self):
        """Should handle approach with no property check"""
        result = handle_positioning_action(
            accessor=self.accessor,
            action={"actor_id": "player", "verb": "approach", "object": "table"},
            property_check=None,
            posture=None
        )

        self.assertTrue(result.success)
        actor = self.accessor.get_actor("player")
        self.assertEqual(actor.properties.get("focused_on"), "item_table")
        self.assertIsNone(actor.properties.get("posture"))

    def test_take_cover_with_property(self):
        """Should require provides_cover property"""
        result = handle_positioning_action(
            accessor=self.accessor,
            action={"actor_id": "player", "verb": "hide", "object": "wall"},
            property_check="provides_cover",
            posture="cover"
        )

        self.assertTrue(result.success)
        actor = self.accessor.get_actor("player")
        self.assertEqual(actor.properties.get("posture"), "cover")

    def test_missing_required_property(self):
        """Should reject when property check fails"""
        result = handle_positioning_action(
            accessor=self.accessor,
            action={"actor_id": "player", "verb": "hide", "object": "chair"},
            property_check="provides_cover",  # chair doesn't have this
            posture="cover"
        )

        self.assertFalse(result.success)
        self.assertIn("can't", result.message.lower())
```

**Implementation:**

```python
def handle_positioning_action(
    accessor,
    action: Dict[str, Any],
    property_check: Optional[str],
    posture: Optional[str],
    verb: Optional[str] = None
) -> HandlerResult:
    """
    Generic positioning action handler.

    Args:
        accessor: StateAccessor
        action: Action dict
        property_check: Property name to validate (e.g., "provides_cover"), or None
        posture: Posture to set (e.g., "cover"), or None
        verb: Override verb (defaults to action["verb"])
    """
    from utilities.handler_utils import validate_actor_and_location
    from behaviors.core.spatial import _find_entity_in_location
    from utilities.utils import serialize_for_handler_result

    # Validate
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    object_name = action.get("object")
    verb = verb or action.get("verb", "approach")

    # Find entity
    entity = _find_entity_in_location(
        accessor, object_name, location.id, actor_id
    )

    if not entity:
        return HandlerResult(
            success=False,
            message=f"You don't see any {object_name} here."
        )

    # Check property requirement if specified
    if property_check:
        if not entity.properties.get(property_check, False):
            return HandlerResult(
                success=False,
                message=f"You can't {verb} the {entity.name}."
            )

    # Check accessibility (for items)
    if hasattr(entity, 'location'):
        from utilities.utils import is_item_accessible
        if not is_item_accessible(accessor, entity, location.id, actor.inventory):
            return HandlerResult(
                success=False,
                message=f"The {entity.name} is out of reach."
            )

    # Set focused_on
    old_focus = actor.properties.get("focused_on")
    actor.properties["focused_on"] = entity.id

    # Set posture if specified
    if posture:
        actor.properties["posture"] = posture
    elif "posture" in actor.properties and old_focus != entity.id:
        # Clear posture when changing focus (unless we're setting a new one)
        actor.properties["posture"] = None

    # Build message
    if posture == "cover":
        message = f"You take cover behind the {entity.name}."
    elif posture == "concealed":
        message = f"You hide in the {entity.name}."
    elif posture == "climbing":
        message = f"You climb the {entity.name}."
    else:
        message = f"You approach the {entity.name}."

    data = serialize_for_handler_result(entity)
    return HandlerResult(success=True, message=message, data=data)
```

### 7.3: Migrate Spatial Handlers

**Update:** `behaviors/core/spatial.py`

**Before:** Lines 96-425 (4 handlers, ~330 lines total)

**After:**
```python
from utilities.positioning import handle_positioning_action

def handle_approach(accessor, action):
    """Handle approaching an entity."""
    return handle_positioning_action(
        accessor, action,
        property_check=None,
        posture=None
    )

def handle_take_cover(accessor, action):
    """Handle taking cover behind an entity."""
    return handle_positioning_action(
        accessor, action,
        property_check="provides_cover",
        posture="cover",
        verb="take cover behind"
    )

def handle_hide_in(accessor, action):
    """Handle hiding in/behind an entity."""
    # Map hide_in to hide for property check
    action_copy = dict(action)
    action_copy["verb"] = "hide"

    return handle_positioning_action(
        accessor, action_copy,
        property_check="allows_concealment",
        posture="concealed",
        verb="hide in"
    )

def handle_climb(accessor, action):
    """Handle climbing an entity."""
    return handle_positioning_action(
        accessor, action,
        property_check="climbable",
        posture="climbing"
    )

# Keep _find_entity_in_location helper (used by positioning utility)
```

### 7.4: Phase 7 Success Criteria

- [ ] `handle_positioning_action()` utility implemented
- [ ] All 4 spatial handlers migrated (approach, take_cover, hide_in, climb)
- [ ] All spatial tests pass (40+ tests)
- [ ] Code reduced by 150-200 lines
- [ ] `_find_entity_in_location` remains as helper

---

## Phase 8: Implicit Positioning Consistency

**Goal:** Ensure all handlers use positioning utilities consistently

**Estimated Effort:** 0.5 days
**Code Savings:** 60-80 lines
**Risk:** Low - utilities already exist

### 8.1: Audit Handler Usage

Review all handlers for patterns like:
```python
item = find_accessible_item(accessor, object_name, actor_id)
moved, move_msg = try_implicit_positioning(accessor, actor_id, item)
```

Should be replaced with:
```python
item, move_msg = find_and_position_item(accessor, actor_id, object_name)
```

**Handlers to check:**
- manipulation.py: handle_take, handle_drop, handle_put
- interaction.py: handle_open, handle_close
- perception.py: handle_examine

### 8.2: Update Inconsistent Handlers

**Tests:** Run existing tests for each handler after change

**Changes:** Mechanical replacement of find + position with combined utility

### 8.3: Phase 8 Success Criteria

- [ ] All handlers use `find_and_position_item()` or `find_and_position_part()`
- [ ] No manual calls to `try_implicit_positioning()` in handlers
- [ ] All tests pass
- [ ] Code reduced by 60-80 lines

---

## Phase 9: Message Building Helper

**Goal:** Standardize behavior result message assembly

**Estimated Effort:** 0.5 days
**Code Savings:** 50-70 lines
**Risk:** Low - simple pattern

### 9.1: Create Message Building Utility

**Add to:** `utilities/handler_utils.py`

**Tests:** `tests/test_handler_utils.py`

```python
class TestBuildHandlerResult(unittest.TestCase):
    def test_base_message_only(self):
        """Should return base message when no behavior message"""
        result = build_handler_result(
            base_message="You take the sword.",
            behavior_result=UpdateResult(success=True, message=None),
            data={"id": "item_sword"}
        )

        self.assertTrue(result.success)
        self.assertEqual(result.message, "You take the sword.")
        self.assertEqual(result.data, {"id": "item_sword"})

    def test_base_plus_behavior_message(self):
        """Should combine base and behavior messages"""
        result = build_handler_result(
            base_message="You take the sword.",
            behavior_result=UpdateResult(success=True, message="It glows faintly."),
            data={"id": "item_sword"}
        )

        self.assertEqual(result.message, "You take the sword. It glows faintly.")

    def test_behavior_failure(self):
        """Should return failure when behavior fails"""
        result = build_handler_result(
            base_message="You take the sword.",
            behavior_result=UpdateResult(success=False, message="It's too hot!"),
            data=None
        )

        self.assertFalse(result.success)
        self.assertEqual(result.message, "It's too hot!")

    def test_no_data(self):
        """Should work without data"""
        result = build_handler_result(
            base_message="You pull the lever.",
            behavior_result=UpdateResult(success=True, message="Click!"),
            data=None
        )

        self.assertTrue(result.success)
        self.assertIsNone(result.data)
```

**Implementation:**

```python
def build_handler_result(
    base_message: str,
    behavior_result: Any,  # UpdateResult
    data: Optional[Dict[str, Any]] = None
) -> HandlerResult:
    """
    Build HandlerResult from base message and behavior result.

    Args:
        base_message: Main action message (e.g., "You take the sword.")
        behavior_result: UpdateResult from accessor.update()
        data: Optional serialized entity data

    Returns:
        HandlerResult with combined messages
    """
    # Check if behavior blocked the action
    if not behavior_result.success:
        return HandlerResult(success=False, message=behavior_result.message)

    # Combine messages
    if behavior_result.message:
        message = f"{base_message} {behavior_result.message}"
    else:
        message = base_message

    return HandlerResult(success=True, message=message, data=data)
```

### 9.2: Migrate Message Building

**Update handlers that currently do:**
```python
if result.message:
    return HandlerResult(success=True, message=f"{base_message} {result.message}", data=data)
return HandlerResult(success=True, message=base_message, data=data)
```

**To:**
```python
return build_handler_result(base_message, result, data)
```

**Files to update:**
- manipulation.py: handle_take, handle_drop
- interaction.py: use, pull, push, read
- consumables.py: drink, eat
- 10+ locations total

### 9.3: Phase 9 Success Criteria

- [ ] `build_handler_result()` utility implemented
- [ ] 10+ handlers migrated
- [ ] All tests pass
- [ ] Code reduced by 50-70 lines

---

## Phase 10: Test Setup Consolidation (Optional)

**Goal:** Reduce test fixture duplication

**Estimated Effort:** 1-2 days
**Code Savings:** Could reduce 1000+ lines, but test code
**Risk:** Medium - many tests to update
**Priority:** Low - test code is less critical

### 10.1: Create Base Test Classes

**Create:** `tests/base_test.py`

```python
import unittest
from pathlib import Path
from src.state_manager import load_game_state
from src.behavior_manager import BehaviorManager
from src.json_protocol import JSONProtocolHandler

class BaseHandlerTest(unittest.TestCase):
    """Base class for handler tests with common setup."""

    fixture_name = "test_game.json"  # Override in subclasses

    def setUp(self):
        fixture_path = Path(__file__).parent / "fixtures" / self.fixture_name
        self.state = load_game_state(fixture_path)

        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        self.handler = JSONProtocolHandler(self.state, behavior_manager=self.manager)
        self.accessor = self.handler.state_accessor


class BaseIntegrationTest(unittest.TestCase):
    """Base class for integration tests."""

    fixture_name = "extended_game.json"

    def setUp(self):
        # Similar setup for integration tests
        pass
```

### 10.2: Migrate Test Classes

**Example migration:**

**Before:**
```python
class TestHandleTake(unittest.TestCase):
    def setUp(self):
        fixture_path = Path(__file__).parent / "fixtures" / "test_game.json"
        self.state = load_game_state(fixture_path)
        # ... 20 more lines ...
```

**After:**
```python
from tests.base_test import BaseHandlerTest

class TestHandleTake(BaseHandlerTest):
    fixture_name = "test_game.json"

    # setUp is inherited, no need to define
```

### 10.3: Phase 10 Success Criteria (If Implemented)

- [ ] Base test classes created
- [ ] 30+ test classes migrated
- [ ] All tests still pass
- [ ] Test code reduced by 1000+ lines

---

## Summary: Effort Estimates

| Phase | Description | Effort | Code Savings | Risk | Priority |
|-------|-------------|--------|--------------|------|----------|
| 1 | Actor & Location Validation | 2-3 days | 400-500 lines | Medium | HIGH |
| 2 | Consumables Consolidation | 0.5 days | 50-60 lines | Low | HIGH |
| 3 | Lock Operation Consolidation | 1-1.5 days | 80-100 lines | Medium | HIGH |
| 4 | Container Validation | 0.5-1 day | 40-50 lines | Low | MEDIUM |
| 5 | Exit Movement Consolidation | 1 day | 60-80 lines | Medium | MEDIUM |
| 6 | Interaction Quartet | 0.5-1 day | 40-50 lines | Low | MEDIUM |
| 7 | Spatial Positioning Pattern | 1.5-2 days | 150-200 lines | Med-High | MEDIUM |
| 8 | Implicit Positioning Consistency | 0.5 days | 60-80 lines | Low | LOW |
| 9 | Message Building Helper | 0.5 days | 50-70 lines | Low | LOW |
| 10 | Test Setup (Optional) | 1-2 days | 1000+ lines | Medium | LOW |
| **TOTAL** | **All Phases** | **8.5-13 days** | **930-1190 lines** | | |
| **HIGH+MEDIUM** | **Phases 1-7** | **7-10 days** | **820-1040 lines** | | |

## Phasing Strategy

### Recommended Approach: Incremental with High-Value First

**Week 1: High-Priority Phases (5-6.5 days)**
- Phase 1: Actor & Location Validation (biggest impact)
- Phase 2: Consumables Consolidation (quick win)
- Phase 3: Lock Operation Consolidation (complex but valuable)

**Week 2: Medium-Priority Phases (3.5-5 days)**
- Phase 4: Container Validation
- Phase 5: Exit Movement
- Phase 6: Interaction Quartet
- Phase 7: Spatial Positioning

**Optional Later: Low-Priority Phases (1.5 days)**
- Phase 8: Positioning Consistency
- Phase 9: Message Building

**Optional Future: Test Consolidation (1-2 days)**
- Phase 10: Test Setup (if test maintenance becomes burden)

### Alternative: Big Bang (Not Recommended)

Could do all phases at once, but risks:
- Merge conflicts if working across many files
- Harder to isolate failures
- Testing becomes complex

## Risk Mitigation

1. **Test First**: Every phase starts with comprehensive tests
2. **One Handler at a Time**: Migrate incrementally within each phase
3. **Verify After Each Migration**: Run tests after every handler change
4. **Keep Old Code Temporarily**: Comment out old code before deleting
5. **Git Branches**: Use feature branches for each phase
6. **Rollback Plan**: Can revert individual phases if issues arise

## Success Metrics

1. **Code Reduction**: Target 800+ lines removed (excluding tests)
2. **Test Coverage**: Maintain 80%+ coverage throughout
3. **Test Pass Rate**: 100% of existing tests must pass after each phase
4. **Behavioral Preservation**: No changes to user-facing behavior
5. **Performance**: No significant performance regression
6. **Documentation**: Update authoring manual with new patterns

## Next Steps

1. Review and approve this plan
2. Create tracking issue for overall consolidation work
3. Create sub-issues for each phase
4. Begin Phase 1 implementation with TDD
5. Update plan with progress and any discoveries

---

**End of Implementation Plan**
