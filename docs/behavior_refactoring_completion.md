# Behavior Refactoring - Completion Plan

This document describes the remaining work to complete the behavior system refactoring.

**Prerequisites:**
- Phases 0-12 complete (behavior handlers, utilities, infrastructure)
- Cleanup phases C-1 through C-8 complete

**Related documents:**
- [behavior_refactoring_phasing.md](behavior_refactoring_phasing.md) - Original phases 0-12
- [behavior_refactoring_cleanup.md](behavior_refactoring_cleanup.md) - Cleanup phases C-1 through C-8
- [behavior_refactoring.md](behavior_refactoring.md) - Design and architecture
- [behavior_refactoring_testing.md](behavior_refactoring_testing.md) - Testing strategy

---

## Current Status

### What's Complete

**Infrastructure (Phases 0-12):**
- StateAccessor with getters, `_set_path()`, and `update()` with behavior invocation
- BehaviorManager with module loading, vocabulary registration, handler chaining
- Unified Actor model (player and NPCs in single `actors` dict)
- Utility functions with strict `actor_id` threading
- Entity behaviors with AND logic and message concatenation

**Command Handlers:**
- Manipulation: `take`, `drop`, `give`, `put`
- Movement: `go`
- Perception: `look`, `examine`, `inventory`
- Interaction: `open`, `close`
- Locks: `unlock`, `lock`
- Consumption: `drink`, `eat`
- Combat: `attack`
- Other: `use`, `read`, `climb`, `pull`, `push`, `squeeze`

**Cleanup (Phases C-1 through C-8):**
- Game state converted to new format (list behaviors, properties dict)
- All `_cmd_*` methods removed from `llm_protocol.py`
- Old helper methods removed
- Union types removed from `behaviors` field (now `List[str]` only)
- File renamed: `json_protocol.py` → `llm_protocol.py`
- All stub commands migrated to behavior handlers

**Test Status:**
- 778 tests passing
- 0 tests skipped

### What Remains

From the original phasing plan (Phases 13-16), some items were completed during cleanup:

| Original Phase | Status | Notes |
|----------------|--------|-------|
| Phase 13: Query Handler Refactoring | Partially complete | Queries use utilities but could be improved |
| Phase 14: Inconsistent State Handling | Complete | Done in cleanup |
| Phase 15: Cleanup & Removal | Complete | Done in cleanup C-3 through C-6 |
| Phase 16: Example Entity Behaviors | Not started | Optional polish |

**Deferred Features (from cleanup):**
1. ~~Adjective-based disambiguation (5 skipped tests)~~ - **DONE (Phase 14)**
2. ~~Take-from-container validation (1 skipped test)~~ - **DONE (Phase 15)**

---

## Remaining Phases

### Phase 13.5: Consumable Property Validation

**Goal:** Prevent nonsensical actions like "eat key" by requiring `edible`/`drinkable` properties

**Duration:** ~30 minutes

**Motivation:** Currently `handle_eat` and `handle_drink` succeed for any item. A rock or key can be eaten because nothing vetoes the action. Handlers should enforce basic sanity checks via properties, matching the pattern used by `portable` for `take`.

**Design Decision:** Handlers enforce basic constraints via properties; behaviors add special effects. An apple needs `edible: true` to be eaten. A magic potion needs both `drinkable: true` AND a behavior for its healing effect.

#### Tasks

1. **Update `handle_eat` in `behaviors/core/consumables.py`:**
   ```python
   # After finding item, before consuming:
   if not item.properties.get("edible", False):
       return HandlerResult(
           success=False,
           message=f"You can't eat the {item.name}."
       )
   ```

2. **Update `handle_drink` in `behaviors/core/consumables.py`:**
   ```python
   # After finding item, before consuming:
   if not item.properties.get("drinkable", False):
       return HandlerResult(
           success=False,
           message=f"You can't drink the {item.name}."
       )
   ```

3. **Update game state items** (if any food/drink items exist):
   - Add `"edible": true` to food items
   - Add `"drinkable": true` to potion/drink items

#### Tests (write first)

Create `tests/test_consumable_properties.py`:

```python
import unittest
from tests.conftest import create_test_state
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.state_manager import Item
from behaviors.core.consumables import handle_eat, handle_drink


class TestConsumableProperties(unittest.TestCase):
    """Test that eat/drink require edible/drinkable properties."""

    def test_eat_non_edible_item_fails(self):
        """Test that eating a non-edible item fails."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        accessor = StateAccessor(state, behavior_manager)

        # Sword is not edible (no edible property)
        sword = state.get_item("item_sword")
        sword.location = "player"
        state.actors["player"].inventory.append("item_sword")

        action = {"actor_id": "player", "object": "sword"}
        result = handle_eat(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't eat", result.message.lower())

    def test_eat_edible_item_succeeds(self):
        """Test that eating an edible item succeeds."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        accessor = StateAccessor(state, behavior_manager)

        # Create edible apple
        apple = Item(
            id="item_apple",
            name="apple",
            description="A red apple",
            location="player",
            properties={"edible": True}
        )
        state.items["item_apple"] = apple
        state.actors["player"].inventory.append("item_apple")

        action = {"actor_id": "player", "object": "apple"}
        result = handle_eat(accessor, action)

        self.assertTrue(result.success)

    def test_drink_non_drinkable_item_fails(self):
        """Test that drinking a non-drinkable item fails."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        accessor = StateAccessor(state, behavior_manager)

        # Sword is not drinkable
        sword = state.get_item("item_sword")
        sword.location = "player"
        state.actors["player"].inventory.append("item_sword")

        action = {"actor_id": "player", "object": "sword"}
        result = handle_drink(accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't drink", result.message.lower())

    def test_drink_drinkable_item_succeeds(self):
        """Test that drinking a drinkable item succeeds."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        accessor = StateAccessor(state, behavior_manager)

        # Create drinkable potion
        potion = Item(
            id="item_potion",
            name="potion",
            description="A healing potion",
            location="player",
            properties={"drinkable": True}
        )
        state.items["item_potion"] = potion
        state.actors["player"].inventory.append("item_potion")

        action = {"actor_id": "player", "object": "potion"}
        result = handle_drink(accessor, action)

        self.assertTrue(result.success)


if __name__ == '__main__':
    unittest.main()
```

#### Validation

- All new tests pass
- Existing tests still pass
- "eat key" now fails with sensible message

#### Implementation Notes (Phase 13.5 Complete)

**Date:** 2025-01-25

**Work Done:**
1. Created `tests/test_consumable_properties.py` with 6 tests (TDD)
2. Ran tests - 4 failed as expected (red phase) - non-edible/non-drinkable items were being consumed
3. Updated `behaviors/core/consumables.py`:
   - Added `edible` property check to `handle_eat()` (line 147-152)
   - Added `drinkable` property check to `handle_drink()` (line 86-91)
4. Updated test fixtures to add `edible`/`drinkable` properties:
   - `tests/fixtures/test_game_with_core_behaviors.json` - potion, bread, water
   - `tests/test_hardcoded_removal.py` - inline fixture for potion, water
   - `tests/test_protocol_behaviors.py` - inline fixture for potion

**Design Decision Implemented:**
- Handlers enforce basic constraints via properties (like `portable` for take)
- Behaviors add special effects (healing, messages, etc.)
- Items need BOTH the property AND a behavior for special effects

**Test Results:**
- All 755 tests pass (6 skipped)
- New tests: 6 added for consumable property validation

**Duration:** ~20 minutes

**Files Modified:**
- `behaviors/core/consumables.py` - Added property checks
- `tests/test_consumable_properties.py` - New test file
- `tests/fixtures/test_game_with_core_behaviors.json` - Added drinkable/edible
- `tests/test_hardcoded_removal.py` - Added drinkable to inline fixture
- `tests/test_protocol_behaviors.py` - Added drinkable to inline fixture

---

### Phase 14: Adjective-Based Disambiguation

**Goal:** Enable commands to select specific entities using adjectives (e.g., "iron door" vs "wooden door")

**Duration:** ~2-3 hours

**Motivation:** Currently, when multiple entities match a name, handlers return the first match and ignore any adjective in the action. This breaks scenarios with multiple similar items or doors.

#### Tasks

1. **Add utility functions in `utilities/utils.py`:**

   ```python
   def find_door_by_name_and_adjective(
       accessor, name: str, adjective: Optional[str], location_id: str
   ) -> Optional[Door]:
       """
       Find door by name, optionally filtered by adjective.

       If adjective provided, matches against door.id or door description.
       If no adjective, returns first matching door.
       """

   def find_item_by_name_and_adjective(
       accessor, name: str, adjective: Optional[str], actor_id: str
   ) -> Optional[Item]:
       """
       Find item by name, optionally filtered by adjective.

       Searches actor's inventory and current location.
       If adjective provided, matches against item.id, description, or properties.
       """
   ```

2. **Update handlers to use adjective:**
   - `handle_unlock` in `behaviors/core/locks.py`
   - `handle_lock` in `behaviors/core/locks.py`
   - `handle_open` in `behaviors/core/interaction.py`
   - `handle_close` in `behaviors/core/interaction.py`
   - `handle_take` in `behaviors/core/manipulation.py`

3. **Pattern for handler updates:**
   ```python
   def handle_unlock(accessor, action):
       actor_id = action.get("actor_id", "player")
       object_name = action.get("object")
       adjective = action.get("adjective")  # NEW: Extract adjective

       # Use new finder with adjective support
       door = find_door_by_name_and_adjective(
           accessor, object_name, adjective, current_location_id
       )
   ```

#### Tests (write first)

Create `tests/test_adjective_disambiguation.py`:

```python
def test_find_door_with_adjective():
    """Test finding specific door when multiple present."""
    state = create_test_state()
    # Add two doors with different adjectives
    iron_door = Door(id="door_iron", locations=("room", "hall"),
                     properties={"description": "iron door"})
    wooden_door = Door(id="door_wooden", locations=("room", "kitchen"),
                       properties={"description": "wooden door"})
    state.doors["door_iron"] = iron_door
    state.doors["door_wooden"] = wooden_door

    accessor = StateAccessor(state, BehaviorManager())

    # With adjective, finds specific door
    door = find_door_by_name_and_adjective(accessor, "door", "iron", "room")
    assert door.id == "door_iron"

    door = find_door_by_name_and_adjective(accessor, "door", "wooden", "room")
    assert door.id == "door_wooden"

def test_unlock_with_adjective():
    """Test unlocking specific door using adjective."""
    # Setup: two doors, two keys, player has iron key
    # Action: unlock "iron door"
    # Result: iron door unlocked, not wooden door

def test_take_item_with_adjective():
    """Test taking specific item using adjective."""
    # Setup: brass key and iron key in room
    # Action: take "brass key"
    # Result: brass key taken, not iron key
```

#### Unskip Tests

After implementation, unskip these tests:
- `tests/llm_interaction/test_json_protocol.py::test_take_key_unlock_door_sequence`
- `tests/llm_interaction/test_json_protocol.py::test_disambiguation_with_adjective`
- `tests/llm_interaction/test_json_protocol.py::test_failed_action_then_retry`
- `tests/llm_interaction/test_llm_narrator.py::test_unlock_and_open_door`
- `tests/test_unknown_adjectives.py::test_different_adjective_selects_other_item`

#### Validation

- All new adjective tests pass
- All previously skipped tests pass
- Existing tests still pass

#### Implementation Notes (Phase 14 Complete)

**Date:** 2025-01-25

**Work Done:**
1. Created `tests/test_adjective_disambiguation.py` with 15 tests (TDD)
2. Added utility functions in `utilities/utils.py`:
   - `_matches_adjective()` - helper to check if adjective matches entity id/description
   - `find_accessible_item_with_adjective()` - find item with optional adjective filter
   - `find_door_with_adjective()` - find door with optional adjective filter
3. Updated handlers to use adjective parameter:
   - `handle_take` in `behaviors/core/manipulation.py`
   - `handle_open` in `behaviors/core/interaction.py`
   - `handle_close` in `behaviors/core/interaction.py`
   - `handle_unlock` in `behaviors/core/locks.py`
   - `handle_lock` in `behaviors/core/locks.py`
4. Unskipped 5 previously skipped tests and fixed them:
   - Fixed tests that tried to open locked doors without unlocking first
   - Added adjective to mock LLM responses

**Design Decision Implemented:**
- Adjective matching is case-insensitive and checks both entity ID and description
- If no adjective provided (or empty), returns first match (backward compatible)
- If adjective provided but nothing matches, returns None (not first match)

**Test Results:**
- All 770 tests pass (1 skipped - Phase 15)
- New tests: 15 added for adjective disambiguation

**Duration:** ~1.5 hours

**Files Modified:**
- `utilities/utils.py` - Added adjective-aware finder functions
- `behaviors/core/manipulation.py` - Updated handle_take
- `behaviors/core/interaction.py` - Updated handle_open, handle_close
- `behaviors/core/locks.py` - Updated handle_unlock, handle_lock
- `tests/test_adjective_disambiguation.py` - New test file
- `tests/test_unknown_adjectives.py` - Unskipped test
- `tests/llm_interaction/test_json_protocol.py` - Unskipped and fixed tests
- `tests/llm_interaction/test_llm_narrator.py` - Unskipped and fixed test

---

### Phase 15: Take-From-Container Validation

**Goal:** Validate container exists when taking items "from" a specific container

**Duration:** ~1 hour

**Motivation:** Currently "take X from Y" ignores the container name and finds X anywhere accessible. This can confuse players when the container they named doesn't exist.

#### Tasks

1. **Update `handle_take` in `behaviors/core/manipulation.py`:**

   ```python
   def handle_take(accessor, action):
       actor_id = action.get("actor_id", "player")
       object_name = action.get("object")
       indirect_object = action.get("indirect_object")  # Container name
       adjective = action.get("adjective")

       if indirect_object:
           # Validate container exists
           container = find_container_by_name(accessor, indirect_object, location_id)
           if not container:
               return HandlerResult(
                   success=False,
                   message=f"You don't see any {indirect_object} here."
               )
           # Search only within that container
           item = find_item_in_container(accessor, object_name, container)
       else:
           # Normal search
           item = find_accessible_item(accessor, object_name, actor_id)
   ```

2. **Add utility function (if needed):**
   ```python
   def find_item_in_container(
       accessor, item_name: str, container: Item
   ) -> Optional[Item]:
       """Find item specifically within a container."""
   ```

#### Tests (write first)

```python
def test_take_from_nonexistent_container():
    """Test that 'take X from Y' fails if Y doesn't exist."""
    state = create_test_state()
    # Item exists in room but no container named "shelf"
    accessor = StateAccessor(state, BehaviorManager())

    action = {
        "actor_id": "player",
        "object": "key",
        "indirect_object": "shelf"  # No shelf exists
    }
    result = handle_take(accessor, action)

    assert not result.success
    assert "shelf" in result.message.lower()

def test_take_from_valid_container():
    """Test that 'take X from Y' works when Y exists."""
    # Setup: chest container with key inside
    # Action: take key from chest
    # Result: success
```

#### Unskip Tests

After implementation, unskip:
- `tests/test_enhanced_containers.py::test_take_from_nonexistent_container_fails`

#### Validation

- New tests pass
- Previously skipped test passes
- Existing container tests still pass

#### Implementation Notes (Phase 15 Complete)

**Date:** 2025-01-25

**Work Done:**
1. Created `tests/test_take_from_container_validation.py` with 8 tests (TDD)
2. Added utility functions in `utilities/utils.py`:
   - `find_container_with_adjective()` - find container in location with adjective filter
   - `find_item_in_container()` - find item inside a specific container
3. Updated `handle_take` in `behaviors/core/manipulation.py`:
   - Extracts `indirect_object` and `indirect_adjective` from action
   - When `indirect_object` provided:
     - Validates container exists in location
     - Validates container is actually a container (has container property)
     - Validates enclosed containers are open
     - Searches only within that specific container
   - When no `indirect_object`, searches anywhere accessible (backward compatible)
4. Unskipped `test_take_from_nonexistent_container_fails` in `test_enhanced_containers.py`

**Design Decision Implemented:**
- "take X from Y" now validates Y exists and is a container
- If Y is not a container, returns "The Y is not a container."
- If Y doesn't exist, returns "You don't see any Y here."
- If enclosed container Y is closed, returns "The Y is closed."
- If X not found in Y, returns "You don't see any X in/on the Y."
- Supports `indirect_adjective` for container disambiguation

**Test Results:**
- All 778 tests pass (0 skipped)
- New tests: 8 added for take-from-container validation

**Duration:** ~30 minutes

**Files Modified:**
- `utilities/utils.py` - Added container/item finder functions
- `behaviors/core/manipulation.py` - Updated handle_take with indirect_object validation
- `tests/test_take_from_container_validation.py` - New test file
- `tests/test_enhanced_containers.py` - Unskipped test

---

### Phase 16: Example Entity Behaviors (Optional)

**Goal:** Create polished example behaviors demonstrating the system's capabilities

**Duration:** ~2-3 hours

**Note:** This is optional polish. The system is functional without it.

#### Tasks

1. **Create `behaviors/examples/cursed_items.py`:**
   ```python
   def on_drop(entity, accessor, context):
       """Cursed items can't be dropped."""
       if entity.properties.get("cursed"):
           return EventResult(
               allow=False,
               message="Dark magic binds the item to your hand!"
           )
       return EventResult(allow=True)
   ```

2. **Create `behaviors/examples/heavy_items.py`:**
   ```python
   def on_take(entity, accessor, context):
       """Check if actor can carry item weight."""
       actor_id = context.get("actor_id")
       actor = accessor.get_actor(actor_id)
       weight = entity.properties.get("weight", 0)
       max_weight = actor.properties.get("max_carry_weight", 100)
       current_weight = calculate_inventory_weight(accessor, actor)

       if current_weight + weight > max_weight:
           return EventResult(
               allow=False,
               message=f"The {entity.name} is too heavy to carry."
           )
       return EventResult(allow=True)
   ```

3. **Create `behaviors/examples/fragile_items.py`:**
   ```python
   def on_drop(entity, accessor, context):
       """Fragile items may break when dropped."""
       if entity.properties.get("fragile"):
           # Mark as broken
           entity.properties["broken"] = True
           return EventResult(
               allow=True,
               message=f"The {entity.name} shatters as it hits the ground!"
           )
       return EventResult(allow=True)
   ```

4. **Add example items to game state:**
   - Cursed amulet (behaviors: ["behaviors/examples/cursed_items"])
   - Heavy anvil (behaviors: ["behaviors/examples/heavy_items"])
   - Glass vase (behaviors: ["behaviors/examples/fragile_items"])

#### Tests

```python
def test_cursed_item_prevents_drop():
    """Test that cursed items can't be dropped."""
    # Setup: player has cursed amulet
    # Action: drop amulet
    # Result: failure with curse message

def test_heavy_item_weight_limit():
    """Test that heavy items respect weight limit."""
    # Setup: player near max carry weight, heavy anvil in room
    # Action: take anvil
    # Result: failure with weight message

def test_fragile_item_breaks_on_drop():
    """Test that fragile items break when dropped."""
    # Setup: player has glass vase
    # Action: drop vase
    # Result: success, vase now has broken=True

def test_behavior_composition():
    """Test item with multiple behaviors."""
    # Setup: item that is both heavy AND cursed
    # Test: both behaviors are invoked, all must allow
```

#### Validation

- Example behaviors work
- Multiple behaviors compose correctly
- Demonstrates system extensibility

---

## Summary

| Phase | Goal | Duration | Priority |
|-------|------|----------|----------|
| 13.5 | Consumable property validation | ~30 min | High |
| 14 | Adjective-based disambiguation | ~2-3 hours | High |
| 15 | Take-from-container validation | ~1 hour | Medium |
| 16 | Example entity behaviors | ~2-3 hours | Low (optional) |

**Total estimated duration:** 4-5 hours (core), +2-3 hours (optional)

**Key Principles:**
1. **TDD**: Write tests first, then implement
2. **Incremental**: Each phase is independently valuable
3. **Verify**: Run full test suite after each phase
4. **Unskip**: Remove skip decorators from tests as features are implemented

---

## Success Criteria

After completing all phases:

- [x] All tests pass (778 tests, 0 skipped)
- [x] Game state uses new format (list behaviors, properties dict)
- [x] No `_cmd_*` methods in llm_protocol.py
- [x] No old helper methods
- [x] `behaviors` field is `List[str]` only
- [x] File renamed to `llm_protocol.py`
- [x] llm_protocol.py contains NO game logic (only routing and serialization)
- [x] Consumable commands require edible/drinkable properties (Phase 13.5)
- [x] Adjective-based disambiguation works (Phase 14)
- [x] Take-from-container validation works (Phase 15)
- [ ] Example behaviors demonstrate extensibility (Phase 16, optional)
- [ ] Full game playthrough works (manual verification)

---

## Quick Commands

```bash
# Run all tests
python -m unittest discover tests/

# Run specific test file
python -m unittest tests/test_adjective_disambiguation.py -v

# Count skipped tests
python -m unittest discover tests/ 2>&1 | grep -E "skipped"

# Find skipped tests
grep -r "@unittest.skip" tests/
```
