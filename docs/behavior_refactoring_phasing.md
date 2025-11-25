# Behavior Refactoring - Phasing Plan

This document describes the implementation plan for the behavior system refactoring described in [behavior_refactoring.md](behavior_refactoring.md).

**See also:**
- [behavior_refactoring.md](behavior_refactoring.md) - Design and architecture
- [behavior_refactoring_testing.md](behavior_refactoring_testing.md) - Testing strategy and test code library
- [behavior_refactoring_implementation.md](behavior_refactoring_implementation.md) - Implementation details and code examples

**How to use this document:**
- Each phase lists tasks and tests to write
- Reference line numbers point to [behavior_refactoring_testing.md](behavior_refactoring_testing.md) where you can copy actual test code
- Tests should be written FIRST (TDD), then implementation makes them pass
- This document is designed to be used by a fresh Claude session without additional context

## Principles

1. **Write tests first** - Each phase begins with writing failing tests, then implementing to make them pass (TDD)
2. **Each phase is independently testable** - Can run tests and verify progress at every step
3. **Small, focused phases** - Each phase should take hours to a day, not weeks
4. **Modified vertical slices** - Work on complete modules (manipulation, movement, etc.) rather than single commands
5. **NPC tests validate actor_id threading** - Every command handler must be tested with both player and NPC actor_id
6. **Design can evolve** - If we encounter issues, we can adjust the design or tests. Goals and use cases are last resort changes.
7. **No backward compatibility constraints** - All code and data are in this repository, so we can make any changes needed

## Approach: Modified Vertical Slices

We use "thick vertical slices" that implement complete command modules end-to-end:

- **Slice 1: Basic Manipulation** - `take`, `drop`, `put` (all share utilities and patterns)
- **Slice 2: Movement & Perception** - `go`, `look`, `examine`, `inventory` (different domain, validates infrastructure generalizes)
- **Slice 3: Interaction & Locks** - `open`, `close`, `unlock`, `lock` (entity behaviors on doors/locks)
- **Infrastructure & Cleanup** - Query handlers, error handling, remove old code
- **Example Behaviors** - Polish with real entity behavior modules

This groups related commands that share code and concepts, allowing us to:
- Get utilities right the first time for each domain
- Validate the infrastructure with diverse command types
- Keep clear "done" criteria for each slice (e.g., "manipulation module working end-to-end")

---

## Phase 0: Preparation & Infrastructure Setup

**Goal:** Set up basic scaffolding without touching existing game logic

**Duration:** ~1 hour

### Tasks

1. Create directory structure:
   ```
   behaviors/
   behaviors/core/
   utilities/
   tests/
   ```

2. Create `tests/conftest.py` with `create_test_state()` helper:
   - **Copy from:** [behavior_refactoring_testing.md](behavior_refactoring_testing.md) lines 14-106
   - This creates a minimal GameState with player, room, and test items
   - Already uses unified actor model: `actors={"player": player}`

3. Create empty `src/state_accessor.py`:
   - Define `EventResult` dataclass (fields: `allow: bool`, `message: Optional[str]`)
   - Define `UpdateResult` dataclass (fields: `success: bool`, `message: Optional[str]`)
   - Define `HandlerResult` dataclass (fields: `success: bool`, `message: str`)
   - Create empty `StateAccessor` class with `__init__(game_state, behavior_manager)`

4. Create empty `src/behavior_manager.py`:
   - Create empty `BehaviorManager` class with `__init__()`

5. Create empty `utilities/utils.py`:
   - Add module docstring: "Shared utility functions for behavior modules"

### Tests (write first)

```python
def test_imports():
    """Verify all new modules can be imported."""
    from src.state_accessor import EventResult, UpdateResult, HandlerResult, StateAccessor
    from src.behavior_manager import BehaviorManager
    import utilities.utils

def test_dataclass_structure():
    """Verify result dataclasses have expected fields."""
    from src.state_accessor import EventResult, UpdateResult, HandlerResult

    er = EventResult(allow=True, message="test")
    assert er.allow is True
    assert er.message == "test"

    ur = UpdateResult(success=True, message="test")
    assert ur.success is True

    hr = HandlerResult(success=True, message="test")
    assert hr.success is True
```

### Validation

- All imports work
- Tests pass
- Existing game functionality unaffected

---

## Phase 1: StateAccessor Core (Read-Only)

**Goal:** Build the query/getter side of StateAccessor

**Duration:** ~2-3 hours

### Tasks

1. Implement `StateAccessor.__init__(game_state, behavior_manager)`
2. Implement getter methods:
   - `get_item(item_id) -> Optional[Item]`
   - `get_actor(actor_id) -> Optional[Actor]`
   - `get_location(location_id) -> Optional[Location]`
   - `get_door(door_id) -> Optional[Door]`
   - `get_lock(lock_id) -> Optional[Lock]`
3. Implement collection methods:
   - `get_current_location(actor_id) -> Location`
   - `get_items_in_location(location_id) -> List[Item]`
   - `get_actors_in_location(location_id) -> List[Actor]`

### Tests (write first)

```python
def test_get_item_found():
    """Test retrieving an item that exists."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    item = accessor.get_item("item_sword")
    assert item is not None
    assert item.id == "item_sword"

def test_get_item_not_found():
    """Test retrieving an item that doesn't exist returns None."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    item = accessor.get_item("nonexistent")
    assert item is None

def test_get_actor_player():
    """Test retrieving the player actor."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    player = accessor.get_actor("player")
    assert player is not None
    assert player.id == "player"

def test_get_current_location():
    """Test getting actor's current location."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    location = accessor.get_current_location("player")
    assert location is not None
    assert location.id == "location_room"

def test_get_items_in_location():
    """Test retrieving items in a location."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    items = accessor.get_items_in_location("location_room")
    assert len(items) > 0
    assert any(item.id == "item_sword" for item in items)

def test_get_actors_in_location():
    """Test retrieving actors in a location."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    actors = accessor.get_actors_in_location("location_room")
    assert len(actors) > 0
    # Player should be in the location
    assert any(actor.id == "player" for actor in actors)
```

### Validation

- All getter tests pass
- Can query state through accessor
- Existing game still works (we're not using accessor yet)

---

## Phase 2: StateAccessor._set_path()

**Goal:** Build the low-level state mutation primitive

**Duration:** ~3-4 hours

### Tasks

1. Implement `_set_path(entity, path: str, value: Any) -> Optional[str]`
   - Handle simple field access: `"location"`
   - Handle nested dict access with dots: `"properties.container.open"`
   - Handle list append with `+` prefix: `"+inventory"`
   - Handle list remove with `-` prefix: `"-inventory"`
   - Return `None` on success, error string on failure

### Tests (write first)

```python
def test_set_path_simple_field():
    """Test setting a simple field."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    item = state.get_item("item_sword")
    error = accessor._set_path(item, "location", "new_location")

    assert error is None
    assert item.location == "new_location"

def test_set_path_nested_dict():
    """Test setting nested dict property."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    item = state.get_item("item_sword")
    error = accessor._set_path(item, "properties.health", 50)

    assert error is None
    assert item.properties.get("health") == 50

def test_set_path_deeply_nested():
    """Test setting deeply nested property."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    item = state.get_item("item_sword")
    error = accessor._set_path(item, "properties.container.open", True)

    assert error is None
    assert item.properties["container"]["open"] is True

def test_set_path_list_append():
    """Test appending to a list."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    actor = state.actors["player"]
    error = accessor._set_path(actor, "+inventory", "new_item")

    assert error is None
    assert "new_item" in actor.inventory

def test_set_path_list_remove():
    """Test removing from a list."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    actor = state.actors["player"]
    actor.inventory.append("item_to_remove")

    error = accessor._set_path(actor, "-inventory", "item_to_remove")

    assert error is None
    assert "item_to_remove" not in actor.inventory

def test_set_path_field_not_found():
    """Test error when field doesn't exist."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    item = state.get_item("item_sword")
    error = accessor._set_path(item, "nonexistent_field", "value")

    assert error is not None
    assert "not found" in error.lower()

def test_set_path_append_to_non_list():
    """Test error when trying to append to non-list."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    item = state.get_item("item_sword")
    error = accessor._set_path(item, "+location", "value")

    assert error is not None
    assert "non-list" in error.lower()

def test_set_path_remove_from_non_list():
    """Test error when trying to remove from non-list."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    item = state.get_item("item_sword")
    error = accessor._set_path(item, "-location", "value")

    assert error is not None
    assert "non-list" in error.lower()

def test_set_path_remove_missing_value():
    """Test error when removing value not in list."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    actor = state.actors["player"]
    error = accessor._set_path(actor, "-inventory", "not_in_list")

    assert error is not None
    assert "not in list" in error.lower()
```

### Validation

- All _set_path tests pass
- Can mutate state via _set_path
- Don't call it from game code yet (internal method)

---

## Phase 3: Unified Actor Model Refactoring

**Goal:** Convert GameState from player/npcs to unified actors dict

**Duration:** ~3-4 hours

### Tasks

1. Refactor `GameState` in `src/state_manager.py`:
   - Replace `self.player` with `self.actors: Dict[str, Actor]`
   - Remove `self.npcs` field
   - Initialize: `self.actors = {"player": Actor(id="player", ...)}`
   - Remove `get_npc()` method
   - Update serialization to save/load from unified actors dict

2. Change `behaviors` field type in ALL entity dataclasses:
   - Change from `behaviors: Dict[str, str]` to `behaviors: List[str]`
   - Update: `Item`, `Actor`, `Location`, `Door`, `Lock`
   - Default to empty list: `behaviors: List[str] = field(default_factory=list)`

3. Update StateAccessor getters to use unified model:
   - `get_actor()` uses `game_state.actors.get(actor_id)`
   - `get_actors_in_location()` returns all actors including player

4. Add migration for old save files (if any exist):
   - Convert old player/npcs structure to actors dict
   - Convert dict-type behaviors to list-type

### Tests (write first)

```python
def test_unified_actor_storage():
    """Test that player and NPCs are in same dict."""
    state = create_test_state()

    # Player should be in actors dict
    assert "player" in state.actors
    assert state.actors["player"].id == "player"

    # Add an NPC
    npc = Actor(id="npc_guard", name="guard", location="location_room", inventory=[])
    state.actors["npc_guard"] = npc

    # Should be able to retrieve both the same way
    player = state.actors["player"]
    guard = state.actors["npc_guard"]
    assert player is not None
    assert guard is not None

def test_get_actor_works_for_player_and_npcs():
    """Test get_actor() works for both player and NPCs."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    # Add NPC
    npc = Actor(id="npc_guard", name="guard", location="location_room", inventory=[])
    state.actors["npc_guard"] = npc

    # Both should be retrievable
    player = accessor.get_actor("player")
    guard = accessor.get_actor("npc_guard")

    assert player is not None
    assert player.id == "player"
    assert guard is not None
    assert guard.id == "npc_guard"

def test_get_actors_in_location_includes_player():
    """Test that get_actors_in_location includes player when present."""
    state = create_test_state()
    accessor = StateAccessor(state, None)

    actors = accessor.get_actors_in_location("location_room")

    # Player should be included
    assert any(actor.id == "player" for actor in actors)

def test_behaviors_field_is_list():
    """Test that behaviors field is a list, not dict."""
    state = create_test_state()

    item = state.get_item("item_sword")
    assert isinstance(item.behaviors, list)

    actor = state.actors["player"]
    assert isinstance(actor.behaviors, list)

def test_save_load_round_trip():
    """Test that save/load preserves unified actor structure."""
    # Create state with player and NPC
    state = create_test_state()
    npc = Actor(id="npc_guard", name="guard", location="location_room", inventory=["item_key"])
    state.actors["npc_guard"] = npc

    # Save to dict
    saved = state.to_dict()

    # Should have actors dict
    assert "actors" in saved
    assert "player" in saved["actors"]
    assert "npc_guard" in saved["actors"]

    # Load from dict
    loaded_state = GameState.from_dict(saved)

    # Verify structure preserved
    assert "player" in loaded_state.actors
    assert "npc_guard" in loaded_state.actors
    assert loaded_state.actors["npc_guard"].inventory == ["item_key"]
```

### Validation

- All unified actor tests pass
- Existing game works with unified model
- Save/load works correctly

---

## Phase 4: BehaviorManager - Module Loading & Vocabulary

**Goal:** Build module loading, vocabulary registration, handler registration (no invocation yet)

**Duration:** ~4-5 hours

### Tasks

1. Implement `BehaviorManager.__init__()`:
   - `self._handlers = {}`
   - `self._verb_events = {}`
   - `self._modules = {}`
   - `self._module_sources = {}`
   - `self._verb_event_sources = {}`
   - `self._handler_position_list = []`

2. Implement `load_module(module, source_type="regular")`:
   - Store `self._current_load_source = source_type`
   - Call `_validate_vocabulary(module, module_name)`
   - Discover and register handlers (`handle_*` functions)
   - Register verb-to-event mappings from vocabulary
   - Track module sources for conflict detection
   - Raise ValueError on conflicts

3. Implement `_validate_vocabulary(module, module_name)`:
   - Check vocabulary is dict
   - Check verbs is list
   - Check each verb spec structure
   - Raise ValueError with descriptive messages

4. Implement `get_event_for_verb(verb) -> Optional[str]`:
   - Return event name from `_verb_events`

5. Implement `get_handler(verb)`:
   - Return first handler from list

### Tests (write first)

**Reference:** [behavior_refactoring_testing.md](behavior_refactoring_testing.md) lines 166-443

**Copy these tests** (they're comprehensive and ready to use):
- Lines 166-193: `test_handler_conflict_detection()` - Verifies duplicate handler detection
- Lines 195-217: `test_handler_override_allowed_across_source_types()` - Verifies chaining is allowed
- Lines 219-254: `test_vocabulary_override_same_event_allowed()` - Verifies same verb→same event is OK
- Lines 256-267: `test_invoke_handler_unknown_verb()` - Verifies error for unknown verbs
- Lines 269-300: `test_handler_load_order()` - Critical: verifies first-loaded-first-called
- Lines 302-331: `test_invoke_previous_handler_walks_forward()` - Will be used in Phase 8, but shows the pattern
- Lines 374-416: `test_three_layer_handler_chain()` - Comprehensive chaining test for Phase 8
- Lines 418-442: `test_position_list_cleanup_on_handler_exception()` - For Phase 8

**For Phase 4, focus on:**

```python
def test_load_module_with_vocabulary():
    """Test loading a module with vocabulary."""
    from types import ModuleType
    behavior_manager = BehaviorManager()

    module = ModuleType("test_module")
    module.vocabulary = {
        "verbs": [
            {"word": "test", "synonyms": ["try"], "event": "on_test"}
        ]
    }

    behavior_manager.load_module(module)

    # Verify verb-to-event mapping
    assert behavior_manager.get_event_for_verb("test") == "on_test"
    assert behavior_manager.get_event_for_verb("try") == "on_test"

def test_load_module_with_handler():
    """Test loading a module with handler."""
    from types import ModuleType
    behavior_manager = BehaviorManager()

    module = ModuleType("test_module")
    def handle_test(accessor, action):
        return HandlerResult(success=True, message="test")
    module.handle_test = handle_test

    behavior_manager.load_module(module)

    # Verify handler registered
    handler = behavior_manager.get_handler("test")
    assert handler is not None
    assert callable(handler)

def test_vocabulary_validation_not_dict():
    """Test that vocabulary must be a dict."""
    from types import ModuleType
    behavior_manager = BehaviorManager()

    module = ModuleType("test_module")
    module.vocabulary = "not a dict"

    with pytest.raises(ValueError) as exc_info:
        behavior_manager.load_module(module)

    assert "must be a dict" in str(exc_info.value)

def test_vocabulary_validation_verbs_not_list():
    """Test that verbs must be a list."""
    from types import ModuleType
    behavior_manager = BehaviorManager()

    module = ModuleType("test_module")
    module.vocabulary = {"verbs": "not a list"}

    with pytest.raises(ValueError) as exc_info:
        behavior_manager.load_module(module)

    assert "must be a list" in str(exc_info.value)

def test_vocabulary_validation_missing_word():
    """Test that verb spec must have 'word' field."""
    from types import ModuleType
    behavior_manager = BehaviorManager()

    module = ModuleType("test_module")
    module.vocabulary = {
        "verbs": [
            {"synonyms": ["test"]}  # Missing 'word'
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        behavior_manager.load_module(module)

    assert "missing required field 'word'" in str(exc_info.value)

def test_handler_conflict_same_source_type():
    """Test that duplicate handlers from same source type raise error."""
    from types import ModuleType
    behavior_manager = BehaviorManager()

    # First module
    first_module = ModuleType("first_module")
    def first_handle_test(accessor, action):
        return HandlerResult(success=True, message="first")
    first_module.handle_test = first_handle_test

    # Second module with same verb
    second_module = ModuleType("second_module")
    def second_handle_test(accessor, action):
        return HandlerResult(success=True, message="second")
    second_module.handle_test = second_handle_test

    # Load first module
    behavior_manager.load_module(first_module, source_type="regular")

    # Load second module - should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        behavior_manager.load_module(second_module, source_type="regular")

    assert "Handler conflict" in str(exc_info.value)
    assert "first_module" in str(exc_info.value)
    assert "second_module" in str(exc_info.value)

def test_handler_no_conflict_different_source_types():
    """Test that same verb from different source types is allowed."""
    from types import ModuleType
    behavior_manager = BehaviorManager()

    # Regular module
    game_module = ModuleType("game_module")
    def game_handle_test(accessor, action):
        return HandlerResult(success=True, message="game")
    game_module.handle_test = game_handle_test

    # Symlink module
    core_module = ModuleType("core_module")
    def core_handle_test(accessor, action):
        return HandlerResult(success=True, message="core")
    core_module.handle_test = core_handle_test

    # Load both - should succeed
    behavior_manager.load_module(game_module, source_type="regular")
    behavior_manager.load_module(core_module, source_type="symlink")

    # Both should be registered
    assert len(behavior_manager._handlers["test"]) == 2

def test_vocabulary_conflict_different_events():
    """Test that same verb mapping to different events raises error."""
    from types import ModuleType
    behavior_manager = BehaviorManager()

    # First module maps "test" -> "on_test"
    first_module = ModuleType("first_module")
    first_module.vocabulary = {
        "verbs": [{"word": "test", "event": "on_test"}]
    }

    # Second module maps "test" -> "on_different"
    second_module = ModuleType("second_module")
    second_module.vocabulary = {
        "verbs": [{"word": "test", "event": "on_different"}]
    }

    behavior_manager.load_module(first_module)

    # Should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        behavior_manager.load_module(second_module)

    assert "Vocabulary conflict" in str(exc_info.value)
    assert "test" in str(exc_info.value)

def test_vocabulary_same_event_allowed():
    """Test that same verb mapping to same event is allowed."""
    from types import ModuleType
    behavior_manager = BehaviorManager()

    # First module maps "test" -> "on_test"
    first_module = ModuleType("first_module")
    first_module.vocabulary = {
        "verbs": [{"word": "test", "event": "on_test"}]
    }

    # Second module also maps "test" -> "on_test"
    second_module = ModuleType("second_module")
    second_module.vocabulary = {
        "verbs": [{"word": "test", "event": "on_test"}]
    }

    behavior_manager.load_module(first_module)
    behavior_manager.load_module(second_module)  # Should not raise

    # Mapping should work
    assert behavior_manager.get_event_for_verb("test") == "on_test"
```

### Validation

- All module loading tests pass
- Can load modules with vocabulary and handlers
- Conflict detection works correctly

---

## Phase 5: StateAccessor.update() - Without Behaviors

**Goal:** Wire up update() to _set_path, but skip behavior invocation initially

**Duration:** ~2 hours

### Tasks

1. Implement `update(entity, changes, verb=None, actor_id="player")`:
   - Loop through changes dict
   - Call `_set_path()` for each change
   - Return `UpdateResult` with success/message
   - Log errors to stderr if _set_path fails
   - Skip behavior invocation for now (just apply changes)

### Tests (write first)

```python
def test_update_simple_change():
    """Test update with a simple field change."""
    state = create_test_state()
    accessor = StateAccessor(state, BehaviorManager())

    item = state.get_item("item_sword")
    result = accessor.update(
        entity=item,
        changes={"location": "new_location"}
    )

    assert result.success
    assert item.location == "new_location"

def test_update_multiple_changes():
    """Test update with multiple changes."""
    state = create_test_state()
    accessor = StateAccessor(state, BehaviorManager())

    item = state.get_item("item_sword")
    result = accessor.update(
        entity=item,
        changes={
            "location": "new_location",
            "properties.weight": 10
        }
    )

    assert result.success
    assert item.location == "new_location"
    assert item.properties.get("weight") == 10

def test_update_with_error():
    """Test that update returns error from _set_path."""
    state = create_test_state()
    accessor = StateAccessor(state, BehaviorManager())

    item = state.get_item("item_sword")
    result = accessor.update(
        entity=item,
        changes={"nonexistent_field": "value"}
    )

    assert not result.success
    assert result.message is not None

def test_update_with_actor_id():
    """Test that update accepts actor_id parameter."""
    state = create_test_state()
    accessor = StateAccessor(state, BehaviorManager())

    item = state.get_item("item_sword")
    result = accessor.update(
        entity=item,
        changes={"location": "player"},
        verb="take",
        actor_id="player"
    )

    assert result.success
```

### Validation

- All update tests pass
- Can use accessor.update() to change state safely
- Errors are reported properly

---

## Phase 6: Utility Functions

**Goal:** Build the search/lookup and visibility helpers

**Duration:** ~4-5 hours

**CRITICAL:** Every utility function MUST accept `actor_id` parameter and use it correctly. NPC tests validate this.

### Tasks

1. Implement in `utilities/utils.py`:
   - `find_accessible_item(accessor, name, actor_id) -> Optional[Item]`
   - `find_item_in_inventory(accessor, name, actor_id) -> Optional[Item]`
   - `find_container_by_name(accessor, name, location_id) -> Optional[Item]`
   - `actor_has_key_for_door(accessor, actor_id, door) -> bool`
   - `get_visible_items_in_location(accessor, location_id, actor_id) -> List[Item]`
   - `get_visible_actors_in_location(accessor, location_id, actor_id) -> List[Actor]`
   - `get_doors_in_location(accessor, location_id, actor_id) -> List[Door]`

2. Add full type hints to all functions

3. Add docstrings with warnings about not hardcoding "player"
   - Example: "IMPORTANT: Do not hardcode 'player' - use the actor_id variable from action"

### Tests (write first)

**Reference:** [behavior_refactoring_testing.md](behavior_refactoring_testing.md) lines 463-686

**Critical NPC utility tests** - These validate actor_id threading BEFORE handlers exist:

```python
def test_find_accessible_item_in_location():
    """Test finding item in actor's current location."""
    state = create_test_state()
    accessor = StateAccessor(state, BehaviorManager())

    item = find_accessible_item(accessor, "sword", "player")

    assert item is not None
    assert item.id == "item_sword"

def test_find_accessible_item_in_inventory():
    """Test finding item in actor's inventory."""
    state = create_test_state()
    accessor = StateAccessor(state, BehaviorManager())

    # Put sword in player's inventory
    player = state.actors["player"]
    sword = state.get_item("item_sword")
    sword.location = "player"
    player.inventory.append("item_sword")

    item = find_accessible_item(accessor, "sword", "player")

    assert item is not None
    assert item.id == "item_sword"

def test_find_accessible_item_not_found():
    """Test that nonexistent item returns None."""
    state = create_test_state()
    accessor = StateAccessor(state, BehaviorManager())

    item = find_accessible_item(accessor, "nonexistent", "player")

    assert item is None

def test_find_accessible_item_for_npc():
    """Test finding item accessible to NPC, not player."""
    state = create_test_state()
    accessor = StateAccessor(state, BehaviorManager())

    # Create NPC in different location
    npc = Actor(id="npc_guard", name="guard", location="other_room", inventory=[])
    state.actors["npc_guard"] = npc

    # Create item in NPC's location
    key = Item(id="item_key", name="key", location="other_room", portable=True)
    state.items["item_key"] = key

    # NPC should find key in their location
    item = find_accessible_item(accessor, "key", "npc_guard")
    assert item is not None
    assert item.id == "item_key"

    # Player should NOT find key (it's in different location)
    item = find_accessible_item(accessor, "key", "player")
    assert item is None

def test_find_item_in_inventory_player():
    """Test finding item in player's inventory."""
    state = create_test_state()
    accessor = StateAccessor(state, BehaviorManager())

    player = state.actors["player"]
    player.inventory.append("item_sword")

    item = find_item_in_inventory(accessor, "sword", "player")

    assert item is not None
    assert item.id == "item_sword"

def test_find_item_in_inventory_npc():
    """Test finding item in NPC's inventory, not player's."""
    state = create_test_state()
    accessor = StateAccessor(state, BehaviorManager())

    # Create NPC with item
    npc = Actor(id="npc_guard", name="guard", location="location_room", inventory=["item_key"])
    state.actors["npc_guard"] = npc

    key = Item(id="item_key", name="key", location="npc_guard", portable=True)
    state.items["item_key"] = key

    # NPC should find key in their inventory
    item = find_item_in_inventory(accessor, "key", "npc_guard")
    assert item is not None
    assert item.id == "item_key"

    # Player should NOT find key
    item = find_item_in_inventory(accessor, "key", "player")
    assert item is None

def test_actor_has_key_for_door_player():
    """Test checking if player has key."""
    state = create_test_state()
    accessor = StateAccessor(state, BehaviorManager())

    # Create door with lock
    door = Door(id="door_main", locations=("room", "hall"), properties={"lock_id": "lock_main"})
    state.doors["door_main"] = door

    lock = Lock(id="lock_main", locked=True, properties={"opens_with": ["item_key"]})
    state.locks["lock_main"] = lock

    key = Item(id="item_key", name="key", location="player", portable=True)
    state.items["item_key"] = key

    player = state.actors["player"]
    player.inventory.append("item_key")

    # Player has key
    assert actor_has_key_for_door(accessor, "player", door)

def test_actor_has_key_for_door_npc():
    """Test checking if NPC has key, not player."""
    state = create_test_state()
    accessor = StateAccessor(state, BehaviorManager())

    # Create door with lock
    door = Door(id="door_main", locations=("room", "hall"), properties={"lock_id": "lock_main"})
    state.doors["door_main"] = door

    lock = Lock(id="lock_main", locked=True, properties={"opens_with": ["item_key"]})
    state.locks["lock_main"] = lock

    # Give key to NPC, not player
    npc = Actor(id="npc_guard", name="guard", location="location_room", inventory=["item_key"])
    state.actors["npc_guard"] = npc

    key = Item(id="item_key", name="key", location="npc_guard", portable=True)
    state.items["item_key"] = key

    # NPC has key
    assert actor_has_key_for_door(accessor, "npc_guard", door)

    # Player does NOT have key
    assert not actor_has_key_for_door(accessor, "player", door)

def test_get_visible_actors_excludes_self():
    """Test that get_visible_actors excludes the viewing actor."""
    state = create_test_state()
    accessor = StateAccessor(state, BehaviorManager())

    # Add NPC to same location
    npc = Actor(id="npc_guard", name="guard", location="location_room", inventory=[])
    state.actors["npc_guard"] = npc

    # Player's view should include NPC but not player
    actors = get_visible_actors_in_location(accessor, "location_room", "player")
    actor_ids = [a.id for a in actors]

    assert "npc_guard" in actor_ids
    assert "player" not in actor_ids

    # NPC's view should include player but not NPC
    actors = get_visible_actors_in_location(accessor, "location_room", "npc_guard")
    actor_ids = [a.id for a in actors]

    assert "player" in actor_ids
    assert "npc_guard" not in actor_ids

def test_utilities_handle_missing_entities():
    """Test that utilities handle missing entities gracefully."""
    state = create_test_state()
    accessor = StateAccessor(state, BehaviorManager())

    # Put non-existent item in inventory (simulates corruption)
    player = state.actors["player"]
    player.inventory.append("missing_item")

    # Should not crash, should skip missing item
    item = find_item_in_inventory(accessor, "sword", "player")
    # Function should complete without AttributeError
```

### Validation

- All utility tests pass
- Utilities work correctly for both player and NPCs
- Missing entities handled gracefully

---

## Slice 1: Basic Manipulation Module

This slice implements the complete manipulation module end-to-end: infrastructure, handlers, and entity behavior support.

---

## Phase 7: First Command Handler (handle_take)

**Goal:** Implement one complete command handler end-to-end

**Duration:** ~4-5 hours

**CRITICAL:** This is the first end-to-end test of the entire system. The NPC test is MANDATORY.

### Tasks

1. Create `behaviors/core/manipulation.py`:
   - Define vocabulary with "take" verb and event mapping: `{"word": "take", "event": "on_take", "synonyms": ["get", "grab"]}`
   - Implement `handle_take(accessor, action)`:
     - **Extract `actor_id` from action at the top:** `actor_id = action.get("actor_id", "player")`
     - Use `find_accessible_item(accessor, name, actor_id)` - pass actor_id!
     - Check `item.portable`
     - Use `accessor.update()` to change item location and actor inventory
     - Handle inconsistent state errors with "INCONSISTENT STATE:" prefix

2. Update `llm_protocol.py` (or create stub):
   - Wire up command routing to call `behavior_manager.invoke_handler()`
   - Return JSON response

### Tests (write first)

**Reference:** [behavior_refactoring_testing.md](behavior_refactoring_testing.md) lines 113-153 (basic tests), 573-605 (NPC test)

**Copy these tests verbatim:**

```python
def test_handle_take_success():
    """Test player taking an item."""
    state = create_test_state()
    behavior_manager = BehaviorManager()
    # Load manipulation module
    import behaviors.core.manipulation
    behavior_manager.load_module(behaviors.core.manipulation)
    accessor = StateAccessor(state, behavior_manager)

    action = {"actor_id": "player", "object": "sword"}
    result = handle_take(accessor, action)

    assert result.success
    assert "sword" in result.message.lower()

    # Verify state changes
    sword = state.get_item("item_sword")
    assert sword.location == "player"
    assert "item_sword" in state.actors["player"].inventory

def test_handle_take_not_portable():
    """Test that non-portable items can't be taken."""
    state = create_test_state()
    behavior_manager = BehaviorManager()
    import behaviors.core.manipulation
    behavior_manager.load_module(behaviors.core.manipulation)
    accessor = StateAccessor(state, behavior_manager)

    action = {"actor_id": "player", "object": "table"}
    result = handle_take(accessor, action)

    assert not result.success
    assert "can't take" in result.message.lower()

def test_handle_take_not_found():
    """Test taking item that doesn't exist."""
    state = create_test_state()
    behavior_manager = BehaviorManager()
    import behaviors.core.manipulation
    behavior_manager.load_module(behaviors.core.manipulation)
    accessor = StateAccessor(state, behavior_manager)

    action = {"actor_id": "player", "object": "nonexistent"}
    result = handle_take(accessor, action)

    assert not result.success
    assert "don't see" in result.message.lower()

def test_handle_take_npc():
    """Test NPC taking an item (critical for actor_id threading)."""
    state = create_test_state()
    behavior_manager = BehaviorManager()
    import behaviors.core.manipulation
    behavior_manager.load_module(behaviors.core.manipulation)
    accessor = StateAccessor(state, behavior_manager)

    # Add NPC to room
    npc = Actor(id="npc_guard", name="guard", location="location_room", inventory=[])
    state.actors["npc_guard"] = npc

    action = {"actor_id": "npc_guard", "object": "sword"}
    result = handle_take(accessor, action)

    assert result.success, f"NPC take failed: {result.message}"

    # Verify item went to NPC, not player
    sword = state.get_item("item_sword")
    assert sword.location == "npc_guard", f"Sword location should be npc_guard, got {sword.location}"
    assert "item_sword" in npc.inventory
    assert "item_sword" not in state.actors["player"].inventory

def test_handle_take_with_missing_actor():
    """Test that missing actor is handled gracefully."""
    state = create_test_state()
    behavior_manager = BehaviorManager()
    import behaviors.core.manipulation
    behavior_manager.load_module(behaviors.core.manipulation)
    accessor = StateAccessor(state, behavior_manager)

    action = {"actor_id": "nonexistent_npc", "object": "sword"}
    result = handle_take(accessor, action)

    # Should return HandlerResult with error, not crash
    assert not result.success
    assert isinstance(result, HandlerResult)
```

### Validation

- All handle_take tests pass
- "take" command works end-to-end through new system
- Works for both player and NPCs

---

## Phase 8: Handler Chaining Infrastructure

**Goal:** Implement invoke_handler() and invoke_previous_handler() with position list

**Duration:** ~3-4 hours

**KEY INSIGHT:** BehaviorManager owns the position list lifecycle. It initializes on invoke_handler(), cleans up in finally.

### Tasks

1. Implement `invoke_handler(verb, accessor, action)` in BehaviorManager:
   - Initialize `self._handler_position_list = [0]` before calling handler
   - Call first handler from `self._handlers[verb][0]`
   - Always clean up in finally block (set to `[]`)
   - This ensures cleanup even if handler raises exception

2. Implement `invoke_previous_handler(verb, accessor, action)` in BehaviorManager:
   - Check position list is initialized (raise RuntimeError if not)
   - Get current position from end of list: `current_pos = self._handler_position_list[-1]`
   - Calculate next: `next_pos = current_pos + 1`
   - Append next position to list
   - Call handler at next position
   - Pop position in finally block

3. Add `invoke_previous_handler(verb, action)` method to StateAccessor:
   - Delegates to `behavior_manager.invoke_previous_handler(verb, self, action)`
   - This allows handlers to call `accessor.invoke_previous_handler()` naturally

### Tests (write first)

**Reference:** [behavior_refactoring_testing.md](behavior_refactoring_testing.md) lines 302-442

**Copy these tests** - they're comprehensive and test the critical path:

```python
def test_invoke_handler_initializes_position_list():
    """Test that invoke_handler initializes position list."""
    from types import ModuleType
    behavior_manager = BehaviorManager()
    state = create_test_state()
    accessor = StateAccessor(state, behavior_manager)

    module = ModuleType("test_module")
    def handle_test(accessor, action):
        # Check position list is initialized
        assert len(behavior_manager._handler_position_list) > 0
        return HandlerResult(success=True, message="test")
    module.handle_test = handle_test

    behavior_manager.load_module(module)

    result = behavior_manager.invoke_handler("test", accessor, {})
    assert result.success

def test_invoke_handler_cleans_up_position_list():
    """Test that position list is cleaned up after handler."""
    from types import ModuleType
    behavior_manager = BehaviorManager()
    state = create_test_state()
    accessor = StateAccessor(state, behavior_manager)

    module = ModuleType("test_module")
    def handle_test(accessor, action):
        return HandlerResult(success=True, message="test")
    module.handle_test = handle_test

    behavior_manager.load_module(module)
    behavior_manager.invoke_handler("test", accessor, {})

    # Position list should be empty after return
    assert behavior_manager._handler_position_list == []

def test_invoke_handler_cleans_up_on_exception():
    """Test that position list is cleaned up even on exception."""
    from types import ModuleType
    behavior_manager = BehaviorManager()
    state = create_test_state()
    accessor = StateAccessor(state, behavior_manager)

    module = ModuleType("test_module")
    def handle_test(accessor, action):
        raise ValueError("Test error")
    module.handle_test = handle_test

    behavior_manager.load_module(module)

    try:
        behavior_manager.invoke_handler("test", accessor, {})
    except ValueError:
        pass

    # Position list should be cleaned up despite exception
    assert behavior_manager._handler_position_list == []

def test_invoke_previous_handler_walks_forward():
    """Test that invoke_previous_handler walks forward through list."""
    from types import ModuleType
    behavior_manager = BehaviorManager()
    state = create_test_state()
    accessor = StateAccessor(state, behavior_manager)

    # First handler delegates
    game_module = ModuleType("game_module")
    def game_handle_test(accessor, action):
        return accessor.invoke_previous_handler("test", action)
    game_module.handle_test = game_handle_test

    # Second handler does work
    core_module = ModuleType("core_module")
    def core_handle_test(accessor, action):
        return HandlerResult(success=True, message="core")
    core_module.handle_test = core_handle_test

    # Load in order
    behavior_manager.load_module(game_module)
    behavior_manager.load_module(core_module)

    result = behavior_manager.invoke_handler("test", accessor, {})

    assert result.success
    assert result.message == "core"

def test_three_layer_handler_chain():
    """Test handler chaining through three layers."""
    from types import ModuleType
    behavior_manager = BehaviorManager()
    state = create_test_state()
    accessor = StateAccessor(state, behavior_manager)

    # Game layer adds prefix
    game_module = ModuleType("game_module")
    def game_handle_test(accessor, action):
        result = accessor.invoke_previous_handler("test", action)
        if result.success:
            return HandlerResult(success=True, message=f"game:{result.message}")
        return result
    game_module.handle_test = game_handle_test

    # Library layer adds prefix
    library_module = ModuleType("library_module")
    def library_handle_test(accessor, action):
        result = accessor.invoke_previous_handler("test", action)
        if result.success:
            return HandlerResult(success=True, message=f"library:{result.message}")
        return result
    library_module.handle_test = library_handle_test

    # Core layer does work
    core_module = ModuleType("core_module")
    def core_handle_test(accessor, action):
        return HandlerResult(success=True, message="core")
    core_module.handle_test = core_handle_test

    # Load in order
    behavior_manager.load_module(game_module)
    behavior_manager.load_module(library_module)
    behavior_manager.load_module(core_module)

    result = behavior_manager.invoke_handler("test", accessor, {})

    assert result.success
    assert result.message == "game:library:core"

def test_invoke_previous_handler_runtime_error():
    """Test that calling invoke_previous_handler incorrectly raises RuntimeError."""
    from types import ModuleType
    behavior_manager = BehaviorManager()
    state = create_test_state()
    accessor = StateAccessor(state, behavior_manager)

    # Try to invoke without initialization
    with pytest.raises(RuntimeError) as exc_info:
        behavior_manager.invoke_previous_handler("test", accessor, {})

    assert "position list not initialized" in str(exc_info.value).lower()
```

### Validation

- All handler chaining tests pass
- Position list properly managed
- Can create custom handlers that delegate to core

---

## Phase 9: Entity Behaviors - Infrastructure

**Goal:** Wire up behavior invocation in update()

**Duration:** ~4-5 hours

**KEY DESIGN:** Multiple behaviors use AND logic (all must allow) and concatenate messages.

### Tasks

1. Implement `invoke_behavior(entity, event_name, accessor, context)` in BehaviorManager:
   - Check if entity has `behaviors` field (might be empty list)
   - For each behavior module name in `entity.behaviors`:
     - Look up module in `self._modules[behavior_name]`
     - Check if module has event handler function: `hasattr(module, event_name)`
     - Call handler: `handler(entity, accessor, context)`
     - Collect EventResult
   - Combine results:
     - `allow = all(r.allow for r in results)` - AND logic
     - `message = "\n".join(r.message for r in results if r.message)` - concatenate
   - Return combined EventResult or None if no behaviors

2. Wire into `update()` in StateAccessor:
   - Look up event name from verb using `behavior_manager.get_event_for_verb(verb)`
   - Build context dict: `{"actor_id": actor_id, "changes": changes, "verb": verb}`
   - Call `behavior_manager.invoke_behavior(entity, event_name, accessor, context)` BEFORE changes
   - If behavior returns EventResult with allow=False, return UpdateResult(success=False, message=...)
   - If behavior allows (or no behaviors), apply changes with `_set_path()`
   - Return UpdateResult with behavior's message if present

### Tests (write first)

**Reference:** [behavior_refactoring_testing.md](behavior_refactoring_testing.md) lines 697-854

**Copy these tests** - they validate the critical multiple-behavior composition logic:

```python
def test_entity_behavior_single():
    """Test invoking single entity behavior."""
    from types import ModuleType
    state = create_test_state()
    behavior_manager = BehaviorManager()

    # Create behavior module with on_take
    behavior_module = ModuleType("test_behavior")
    def on_take(entity, accessor, context):
        return EventResult(allow=False, message="Can't take this!")
    behavior_module.on_take = on_take

    behavior_manager.load_module(behavior_module)
    behavior_manager._modules["test_behavior"] = behavior_module

    accessor = StateAccessor(state, behavior_manager)

    # Create item with behavior
    item = Item(
        id="test_item",
        name="test item",
        location="location_room",
        portable=True,
        behaviors=["test_behavior"]
    )
    state.items["test_item"] = item

    # Invoke behavior
    context = {"actor_id": "player", "changes": {}, "verb": "take"}
    result = behavior_manager.invoke_behavior(item, "on_take", accessor, context)

    assert result is not None
    assert not result.allow
    assert "Can't take" in result.message

def test_entity_behavior_multiple():
    """Test that multiple behaviors are all invoked."""
    from types import ModuleType
    state = create_test_state()
    behavior_manager = BehaviorManager()

    # First behavior
    behavior1 = ModuleType("behavior1")
    def on_take_1(entity, accessor, context):
        return EventResult(allow=True, message="Message from behavior1")
    behavior1.on_take = on_take_1

    # Second behavior
    behavior2 = ModuleType("behavior2")
    def on_take_2(entity, accessor, context):
        return EventResult(allow=True, message="Message from behavior2")
    behavior2.on_take = on_take_2

    behavior_manager.load_module(behavior1)
    behavior_manager.load_module(behavior2)
    behavior_manager._modules["behavior1"] = behavior1
    behavior_manager._modules["behavior2"] = behavior2

    accessor = StateAccessor(state, behavior_manager)

    # Item with both behaviors
    item = Item(
        id="test_item",
        name="test item",
        location="location_room",
        portable=True,
        behaviors=["behavior1", "behavior2"]
    )
    state.items["test_item"] = item

    context = {"actor_id": "player", "changes": {}, "verb": "take"}
    result = behavior_manager.invoke_behavior(item, "on_take", accessor, context)

    assert result is not None
    assert result.allow
    # Both messages should be present
    assert "behavior1" in result.message
    assert "behavior2" in result.message

def test_entity_behavior_any_deny_wins():
    """Test that if any behavior denies, action is denied."""
    from types import ModuleType
    state = create_test_state()
    behavior_manager = BehaviorManager()

    # First behavior allows
    behavior1 = ModuleType("behavior1")
    def on_take_1(entity, accessor, context):
        return EventResult(allow=True, message="OK from behavior1")
    behavior1.on_take = on_take_1

    # Second behavior denies
    behavior2 = ModuleType("behavior2")
    def on_take_2(entity, accessor, context):
        return EventResult(allow=False, message="Denied by behavior2")
    behavior2.on_take = on_take_2

    behavior_manager.load_module(behavior1)
    behavior_manager.load_module(behavior2)
    behavior_manager._modules["behavior1"] = behavior1
    behavior_manager._modules["behavior2"] = behavior2

    accessor = StateAccessor(state, behavior_manager)

    item = Item(
        id="test_item",
        name="test item",
        location="location_room",
        portable=True,
        behaviors=["behavior1", "behavior2"]
    )
    state.items["test_item"] = item

    context = {"actor_id": "player", "changes": {}, "verb": "take"}
    result = behavior_manager.invoke_behavior(item, "on_take", accessor, context)

    assert result is not None
    assert not result.allow  # Denied

def test_update_invokes_behavior():
    """Test that update() invokes entity behaviors."""
    from types import ModuleType
    state = create_test_state()
    behavior_manager = BehaviorManager()

    # Create vocabulary mapping take -> on_take
    vocab_module = ModuleType("vocab_module")
    vocab_module.vocabulary = {
        "verbs": [{"word": "take", "event": "on_take"}]
    }
    behavior_manager.load_module(vocab_module)

    # Create behavior that denies
    behavior_module = ModuleType("test_behavior")
    def on_take(entity, accessor, context):
        return EventResult(allow=False, message="Behavior denies!")
    behavior_module.on_take = on_take

    behavior_manager.load_module(behavior_module)
    behavior_manager._modules["test_behavior"] = behavior_module

    accessor = StateAccessor(state, behavior_manager)

    # Item with behavior
    item = Item(
        id="test_item",
        name="test item",
        location="location_room",
        portable=True,
        behaviors=["test_behavior"]
    )
    state.items["test_item"] = item

    # Try to update with verb that triggers behavior
    result = accessor.update(
        entity=item,
        changes={"location": "player"},
        verb="take",
        actor_id="player"
    )

    # Should be denied by behavior
    assert not result.success
    assert "Behavior denies" in result.message

def test_entity_no_behaviors_allows():
    """Test that entity with no behaviors allows changes."""
    state = create_test_state()
    behavior_manager = BehaviorManager()
    accessor = StateAccessor(state, behavior_manager)

    # Item with no behaviors
    item = Item(
        id="test_item",
        name="test item",
        location="location_room",
        portable=True,
        behaviors=[]
    )
    state.items["test_item"] = item

    # Should succeed (no behaviors to block)
    result = accessor.update(
        entity=item,
        changes={"location": "player"},
        verb="take",
        actor_id="player"
    )

    assert result.success
```

### Validation

- All entity behavior tests pass
- accessor.update() invokes behaviors correctly
- Multiple behaviors work as designed (all invoked, AND logic)

---

## Phase 10: Complete Manipulation Handlers

**Goal:** Finish the manipulation module

**Duration:** ~4-6 hours

**CRITICAL:** Each handler needs NPC test. Use handle_take as the pattern.

### Tasks

1. Add to `behaviors/core/manipulation.py`:
   - Vocabulary for drop, put, give (with event mappings: "on_drop", "on_put", "on_give")
   - Implement `handle_drop()`:
     - Extract `actor_id` at top
     - Use `find_item_in_inventory(accessor, name, actor_id)`
     - Use `get_current_location(actor_id)` for destination
     - Handle inconsistent state
   - Implement `handle_put()`:
     - Extract `actor_id` at top
     - Find item in actor's inventory
     - Find container in actor's location
     - Check container is open/surface
     - Handle inconsistent state
   - Implement `handle_give()`:
     - Extract `actor_id` at top
     - Find item in giving actor's inventory
     - Find recipient in actor's location
     - Update both inventories
     - Handle inconsistent state

### Tests (write first)

**Reference:** [behavior_refactoring_testing.md](behavior_refactoring_testing.md) lines 606-664

**Pattern for each handler:**
1. Write success test with player
2. Write error condition tests
3. **Write NPC test (MANDATORY)** - Copy pattern from lines 606-664

**NPC test examples to copy:**
- Lines 606-633: `test_npc_drop_item()` - Shows NPC dropping works independently of player
- Lines 635-663: `test_npc_give_to_player()` - Shows bidirectional give (NPC→player)

### Validation

- All manipulation commands work for player and NPCs
- Full manipulation module complete
- End of Slice 1

---

## Slice 2: Movement & Perception

---

## Phase 11: Movement and Perception Handlers

**Goal:** Add different command types to validate infrastructure generalizes

**Duration:** ~6-8 hours

### Tasks

1. Create `behaviors/core/movement.py`:
   - Vocabulary for "go" with directions
   - Implement `handle_go(accessor, action)`
   - Handle doors, locked doors, invalid exits

2. Create `behaviors/core/perception.py`:
   - Vocabulary for look, examine, inventory
   - Implement `handle_look(accessor, action)`
   - Implement `handle_examine(accessor, action)`
   - Implement `handle_inventory(accessor, action)`
   - Use visibility utilities

### Tests (write first)

```python
def test_handle_go_success():
    """Test moving to adjacent location."""
    # ...

def test_handle_go_npc():
    """Test NPC movement."""
    # Critical test...

def test_handle_go_blocked_door():
    """Test that locked doors block movement."""
    # ...

def test_handle_look_lists_items():
    """Test that look shows visible items."""
    # ...

def test_handle_look_npc_perspective():
    """Test look from NPC perspective."""
    # Different location than player...

def test_handle_examine_item():
    """Test examining an item."""
    # ...

def test_handle_inventory_player():
    """Test player inventory."""
    # ...

def test_handle_inventory_npc():
    """Test NPC inventory."""
    # Should show NPC's items, not player's...
```

### Validation

- Movement works for player and NPCs
- Perception commands work from different actor perspectives
- Infrastructure handles different command types
- End of Slice 2

---

## Slice 3: Interaction & Locks

---

## Phase 12: Interaction and Lock Handlers

**Goal:** Add commands that interact with entity behaviors on doors/locks

**Duration:** ~6-8 hours

### Tasks

1. Create `behaviors/core/interaction.py`:
   - Vocabulary for open, close
   - Implement `handle_open(accessor, action)`
   - Implement `handle_close(accessor, action)`
   - Work with both items (containers) and doors

2. Create `behaviors/core/locks.py`:
   - Vocabulary for unlock, lock
   - Implement `handle_unlock(accessor, action)`
   - Implement `handle_lock(accessor, action)`
   - Check for keys in actor inventory

### Tests (write first)

```python
def test_handle_open_container():
    """Test opening a container."""
    # ...

def test_handle_open_door():
    """Test opening a door."""
    # ...

def test_handle_open_npc():
    """Test NPC opening something."""
    # Critical test...

def test_handle_unlock_with_key():
    """Test unlocking with correct key."""
    # ...

def test_handle_unlock_without_key():
    """Test that unlocking fails without key."""
    # ...

def test_handle_unlock_npc():
    """Test NPC unlocking with their key."""
    # NPC has key, player doesn't...
```

### Validation

- Interaction commands work
- Lock/unlock uses key from correct actor
- Different from item behaviors (tests behavior flexibility)
- End of Slice 3

---

## Infrastructure & Cleanup

---

## Phase 13: Query Handler Refactoring

**Goal:** Make llm_protocol queries use utility functions

**Duration:** ~3-4 hours

### Tasks

1. Refactor query handlers in llm_protocol.py:
   - `_query_location()` uses `get_visible_items_in_location()`, `get_visible_actors_in_location()`, `get_doors_in_location()`
   - `_query_inventory()` uses utilities
   - `_query_entity()` uses accessor getters
   - All queries pass actor_id to utilities

### Tests (write first)

```python
def test_query_location_shows_visible_items():
    """Test that location query shows visible items."""
    # ...

def test_query_location_actor_specific():
    """Test that location query is actor-specific."""
    # Different actors see different things...

def test_query_inventory_player():
    """Test inventory query for player."""
    # ...

def test_query_inventory_npc():
    """Test inventory query for NPC."""
    # Should return NPC's inventory...
```

### Validation

- Queries work correctly
- Queries use utilities (no game logic in llm_protocol)

---

## Phase 14: Inconsistent State Handling

**Goal:** Add infrastructure error detection and recovery

**Duration:** ~2-3 hours

### Tasks

1. Add to llm_protocol.py:
   - `self.state_corrupted = False` flag
   - Check for "INCONSISTENT STATE:" prefix in results
   - Implement `_handle_inconsistent_state()` method
   - Block non-meta commands after corruption
   - Log full error to stderr

### Tests (write first)

```python
def test_inconsistent_state_detected():
    """Test that inconsistent state is detected."""
    # Create handler that returns INCONSISTENT STATE message...

def test_inconsistent_state_blocks_commands():
    """Test that commands are blocked after corruption."""
    # ...

def test_inconsistent_state_allows_meta_commands():
    """Test that save/quit still work."""
    # ...

def test_inconsistent_state_logged():
    """Test that error details are logged to stderr."""
    # Capture stderr...
```

### Validation

- Inconsistent state handled gracefully
- User gets clean error, developer gets details

---

## Phase 15: Cleanup & Removal

**Goal:** Delete old code, finalize structure

**Duration:** ~2-3 hours

### Tasks

1. Remove old code:
   - Delete all `_cmd_*` methods from llm_protocol.py (or json_protocol.py)
   - Remove parallel implementations from game_engine.py
   - Remove old helper methods
   - Rename json_protocol.py to llm_protocol.py if not done yet

2. Update imports throughout codebase

3. Run full test suite

### Validation

- All tests pass
- No references to old code
- Full game playthrough works

---

## Phase 16: Example Entity Behaviors

**Goal:** Polish with real entity behavior modules

**Duration:** ~4-6 hours

### Tasks

1. Create example entity behavior modules:
   - `behaviors/examples/cursed_items.py` with `on_take` and `on_drop`
   - `behaviors/examples/light_sources.py` with `on_take` (lights up)
   - `behaviors/examples/lockable_containers.py` with `on_open`
   - `behaviors/examples/heavy_items.py` with `on_take` (weight check)

2. Add entities to game data that use these behaviors:
   - Cursed sword (can't drop)
   - Magic lantern (glows when taken)
   - Locked chest
   - Heavy anvil

3. Create test scenarios showcasing behavior composition:
   - Item with multiple behaviors
   - Behaviors that provide success messages
   - Behaviors that deny actions

### Tests (write first)

```python
def test_cursed_item_cant_drop():
    """Test that cursed items can't be dropped."""
    # ...

def test_magic_lantern_glows():
    """Test that lantern glows when taken."""
    # ...

def test_locked_container_blocks_open():
    """Test that locked container can't be opened."""
    # ...

def test_heavy_item_weight_check():
    """Test that heavy items check weight limit."""
    # ...

def test_multiple_behaviors_compose():
    """Test item with multiple behaviors."""
    # Item that is both heavy AND cursed...
```

### Validation

- Example behaviors work
- Can play with interesting interactive objects
- Demonstrates the value of the refactoring

---

## Summary

**Total Estimated Duration:** 8-12 days of focused work

**Key Milestones:**
- After Phase 6: Infrastructure complete, utilities work for player and NPCs
- After Phase 10: Manipulation module complete end-to-end (Slice 1 done)
- After Phase 11: Multiple command types validated (Slice 2 done)
- After Phase 12: Entity behaviors on different entity types (Slice 3 done)
- After Phase 15: Old code removed, clean architecture
- After Phase 16: Polish with example behaviors showing value

**Success Criteria:**
- All tests pass
- NPC tests validate actor_id threading throughout
- Full game playthrough works
- Example entity behaviors demonstrate extensibility
- llm_protocol.py contains no game logic
- Can add new commands by creating behavior modules

---

## Quick Reference: Testing Document Mapping

This table shows which sections of [behavior_refactoring_testing.md](behavior_refactoring_testing.md) are most relevant for each phase:

| Phase | Testing Doc Lines | What to Copy/Reference |
|-------|------------------|------------------------|
| 0 | 14-106 | `create_test_state()` helper - copy into `tests/conftest.py` |
| 1-2 | (inline) | Tests are inline in phasing doc |
| 3 | 93 | Unified actor model pattern: `actors={"player": player}` |
| 4 | 166-443 | Module loading, conflict detection, vocabulary validation tests |
| 5 | (inline) | Tests are inline in phasing doc |
| 6 | 463-686 | Utility functions with actor_id, NPC utility tests, None handling |
| 7 | 113-153, 573-605 | Basic handler tests + critical NPC test for handle_take |
| 8 | 302-442 | Position list lifecycle, handler chaining, three-layer chain |
| 9 | 697-854 | Multiple behaviors, AND logic, message concatenation |
| 10 | 606-664 | NPC tests for drop, give handlers |
| 11-12 | 573-686 | Adapt NPC test pattern for movement/perception/locks |
| 13 | (create new) | Query handler tests using utilities |
| 14 | (create new) | Inconsistent state detection tests |

**Testing Principles to Remember:**

1. **Always write tests FIRST** - This is TDD, tests drive implementation
2. **NPC tests are mandatory** for every handler - They catch hardcoded "player" bugs
3. **Copy tests from testing doc** - Don't rewrite, the tests are ready to use
4. **None handling tests** prevent AttributeError crashes
5. **Multiple behavior tests** validate composition logic (AND, message concat)

**Common Patterns in Testing Doc:**

- **Lines 14-106**: Test state setup - use this everywhere
- **Lines 573-605**: NPC test pattern - replicate for every handler
- **Lines 697-729**: Multiple behaviors - test any entity with 2+ behaviors
- **Lines 463-520**: None handling - test utilities and handlers

**When Starting a Phase:**
1. Read the phase tasks in this document
2. Jump to the referenced lines in behavior_refactoring_testing.md
3. Copy the test code into your test file
4. Run tests (they should fail - this is expected in TDD)
5. Implement features to make tests pass
6. Move to next phase

---

## Quick Reference: Implementation Code Examples

For implementation guidance, see [behavior_refactoring_implementation.md](behavior_refactoring_implementation.md):

| Topic | Implementation Doc Lines | What's There |
|-------|-------------------------|--------------|
| Module organization | 9-37 | Final directory structure, module responsibilities |
| Shared utilities | 39-168 | Complete implementations of utility functions with type hints |
| llm_protocol structure | 218-344 | Complete refactored llm_protocol.py with inconsistent state handling |
| manipulation.py example | 379-640 | Complete working example of all four manipulation handlers |
| Migration map | 642-683 | Old method names → new handler locations |
| StateAccessor details | 684-887 | Detailed implementation notes for Phase 2a (note: uses old phase numbering) |

**Key Code to Reference:**

- **Utility function signatures** (lines 87-168): Copy these exact signatures with type hints
- **handle_take example** (lines 426-470): The canonical pattern for all handlers
- **handle_give example** (lines 572-638): Shows complex multi-entity updates
- **llm_protocol._process_command** (lines 239-295): Shows how to wire up invoke_handler()
- **Inconsistent state handling** (lines 297-332): Shows _handle_inconsistent_state() implementation

**Usage Pattern:**
1. Look at phasing doc for WHAT to implement in this phase
2. Look at testing doc for TESTS to write first
3. Look at implementation doc for CODE EXAMPLES of how to implement
4. Run tests to verify your implementation matches the design
