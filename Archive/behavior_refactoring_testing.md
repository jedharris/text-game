# Behavior Refactoring - Testing Strategy

This document specifies the testing strategy for the behavior refactoring described in [behavior_refactoring.md](behavior_refactoring.md).

## Overview

With StateAccessor, handlers are easily testable without mocking the state layer. Tests use real GameState objects and verify both handler return values and actual state changes.

## Test Setup Utilities

Tests require a helper function to create a minimal test state with common entities:

```python
def create_test_state():
    """
    Create a minimal GameState for testing with common test entities.

    Returns:
        GameState with:
        - Player at "location_room"
        - A portable sword (item_sword) in the room
        - A non-portable table (item_table) in the room
        - A magic lantern (item_lantern) in the room with light_sources behavior
        - An anvil (item_anvil) with weight=150 in the room
        - A feather (item_feather) with weight=1 in the room
    """
    from src.models import GameState, Actor, Location, Item

    # Create player
    player = Actor(
        id="player",
        location="location_room",
        inventory=[],
        properties={"max_carry_weight": 100}
    )

    # Create location
    room = Location(
        id="location_room",
        name="Test Room",
        description="A room for testing",
        exits={}
    )

    # Create test items
    sword = Item(
        id="item_sword",
        name="sword",
        description="A test sword",
        location="location_room",
        portable=True
    )

    table = Item(
        id="item_table",
        name="table",
        description="A heavy table",
        location="location_room",
        portable=False
    )

    lantern = Item(
        id="item_lantern",
        name="lantern",
        description="A magic lantern",
        location="location_room",
        portable=True,
        behaviors=["light_sources"],
        states={"lit": False}
    )

    anvil = Item(
        id="item_anvil",
        name="anvil",
        description="A very heavy anvil",
        location="location_room",
        portable=True,
        properties={"weight": 150}
    )

    feather = Item(
        id="item_feather",
        name="feather",
        description="A light feather",
        location="location_room",
        portable=True,
        properties={"weight": 1}
    )

    # Create and return game state
    state = GameState(
        actors={"player": player},
        locations={"location_room": room},
        items={
            "item_sword": sword,
            "item_table": table,
            "item_lantern": lantern,
            "item_anvil": anvil,
            "item_feather": feather
        },
        doors={},
        locks={}
    )

    return state
```

## Basic Handler Tests

With StateAccessor, handlers are easily testable without mocking. Tests use real state objects and verify both the handler's return value and the actual state changes:

```python
def test_handle_take_success():
    state = create_test_state()
    behavior_manager = BehaviorManager()
    accessor = StateAccessor(state, behavior_manager)

    action = {"actor_id": "player", "object": "sword"}
    result = handle_take(accessor, action)

    # Verify handler result
    assert result.success
    assert "sword" in result.message

    # Verify actual state changes
    assert state.get_item("item_sword").location == "player"
    assert "item_sword" in state.actors["player"].inventory

def test_handle_take_not_portable():
    state = create_test_state()
    behavior_manager = BehaviorManager()
    accessor = StateAccessor(state, behavior_manager)

    action = {"actor_id": "player", "object": "table"}
    result = handle_take(accessor, action)

    assert not result.success
    assert "can't take" in result.message.lower()

def test_handle_take_with_behavior():
    state = create_test_state()
    behavior_manager = BehaviorManager()
    # Load light_sources behavior module
    behavior_manager.load_module("behaviors.core.light_sources")
    accessor = StateAccessor(state, behavior_manager)

    action = {"actor_id": "player", "object": "lantern"}
    result = handle_take(accessor, action)

    assert result.success
    assert "runes flare to life" in result.message  # From on_take behavior
    assert state.get_item("item_lantern").states.get("lit") == True
```

## Critical: Testing Handler Load Order

The handler loading order is critical to the delegation mechanism. Tests must verify:

1. **Load order determines call order**: First-loaded handler is called first
2. **Handler list append behavior**: Handlers are appended to list in load order
3. **`get_handler()` returns first**: Returns `handlers[0]` (first loaded)
4. **`invoke_previous_handler()` walks forward**: Returns `handlers[1]`, then `handlers[2]`, etc.
5. **Conflict detection**: Multiple handlers from same source type raise ValueError

```python
def test_handler_conflict_detection():
    """Test that multiple handlers from same source type are detected."""
    from types import ModuleType
    behavior_manager = BehaviorManager()

    # Create two regular modules that both define handle_test
    first_module = ModuleType("first_module")
    def first_handle_test(accessor, action):
        return HandlerResult(success=True, message="first")
    first_module.handle_test = first_handle_test

    second_module = ModuleType("second_module")
    def second_handle_test(accessor, action):
        return HandlerResult(success=True, message="second")
    second_module.handle_test = second_handle_test

    # Load first module - should succeed
    behavior_manager.load_module(first_module, source_type="regular")

    # Load second module with same verb - should raise ValueError
    try:
        behavior_manager.load_module(second_module, source_type="regular")
        assert False, "Should have raised ValueError for duplicate handler"
    except ValueError as e:
        assert "Handler conflict" in str(e)
        assert "first_module" in str(e)
        assert "second_module" in str(e)
        assert "handle_test" in str(e)

def test_handler_override_allowed_across_source_types():
    """Test that same verb in regular and symlink modules is allowed (for chaining)."""
    from types import ModuleType
    behavior_manager = BehaviorManager()

    # Create a regular module
    game_module = ModuleType("game_module")
    def game_handle_test(accessor, action):
        return HandlerResult(success=True, message="game")
    game_module.handle_test = game_handle_test

    # Create a symlink module with same verb
    core_module = ModuleType("core_module")
    def core_handle_test(accessor, action):
        return HandlerResult(success=True, message="core")
    core_module.handle_test = core_handle_test

    # Load both - should succeed (different source types)
    behavior_manager.load_module(game_module, source_type="regular")
    behavior_manager.load_module(core_module, source_type="symlink")  # No error

    # Verify both are registered
    assert len(behavior_manager._handlers["test"]) == 2

def test_vocabulary_override_same_event_allowed():
    """Test that same verb → same event from regular and symlink is allowed."""
    from types import ModuleType
    behavior_manager = BehaviorManager()

    # Create regular module with vocabulary
    game_module = ModuleType("game_module")
    game_module.vocabulary = {
        "verbs": [
            {"word": "take", "event": "on_take", "synonyms": ["grab"]}
        ]
    }
    def game_handle_take(accessor, action):
        return HandlerResult(success=True, message="game take")
    game_module.handle_take = game_handle_take

    # Create symlink module with SAME verb → SAME event
    core_module = ModuleType("core_module")
    core_module.vocabulary = {
        "verbs": [
            {"word": "take", "event": "on_take", "synonyms": ["get"]}
        ]
    }
    def core_handle_take(accessor, action):
        return HandlerResult(success=True, message="core take")
    core_module.handle_take = core_handle_take

    # Load both - should succeed (same event, different source types)
    behavior_manager.load_module(game_module, source_type="regular")
    behavior_manager.load_module(core_module, source_type="symlink")  # No error

    # Verify vocabulary mapping exists (one of them wins, doesn't matter which)
    assert behavior_manager.get_event_for_verb("take") == "on_take"
    # Verify synonyms work
    assert behavior_manager.get_event_for_verb("grab") == "on_take"
    assert behavior_manager.get_event_for_verb("get") == "on_take"

def test_invoke_handler_unknown_verb():
    """Test that unknown verbs return appropriate error."""
    behavior_manager = BehaviorManager()
    state = create_test_state()
    accessor = StateAccessor(state, behavior_manager)

    # No modules loaded, invoke unknown verb
    result = behavior_manager.invoke_handler("nonexistent", accessor, {})

    assert not result.success
    assert "Unknown command" in result.message
    assert "nonexistent" in result.message

def test_handler_load_order():
    """Test that handlers are called in load order (first loaded = first called)."""
    behavior_manager = BehaviorManager()

    # Create mock module objects with handler functions
    from types import ModuleType

    first_module = ModuleType("first_module")
    def first_handle_test(accessor, action):
        return HandlerResult(success=True, message="first")
    first_module.handle_test = first_handle_test

    second_module = ModuleType("second_module")
    def second_handle_test(accessor, action):
        return HandlerResult(success=True, message="second")
    second_module.handle_test = second_handle_test

    # Load in order
    behavior_manager.load_module(first_module)
    behavior_manager.load_module(second_module)

    # Verify first loaded is returned by get_handler()
    handler = behavior_manager.get_handler("test")
    result = handler(None, {})
    assert result.success and result.message == "first", "First loaded handler should be called"

    # Verify handlers list is in load order
    assert len(behavior_manager._handlers["test"]) == 2
    result0 = behavior_manager._handlers["test"][0](None, {})
    result1 = behavior_manager._handlers["test"][1](None, {})
    assert result0.success and result0.message == "first"
    assert result1.success and result1.message == "second"

def test_invoke_previous_handler_walks_forward():
    """Test that invoke_previous_handler walks forward through load order."""
    from types import ModuleType
    behavior_manager = BehaviorManager()

    # Create mock modules
    game_module = ModuleType("game_module")
    def game_handle_test(accessor, action):
        # Game code delegates to next in chain
        return accessor.invoke_previous_handler("test", action)
    game_module.handle_test = game_handle_test

    core_module = ModuleType("core_module")
    def core_handle_test(accessor, action):
        return HandlerResult(success=True, message="core")
    core_module.handle_test = core_handle_test

    # Load: game first, core last
    behavior_manager.load_module(game_module)
    behavior_manager.load_module(core_module)

    # Create mock accessor
    state = create_test_state()
    accessor = StateAccessor(state, behavior_manager)

    # Call should go: game → core
    handler = behavior_manager.get_handler("test")
    result = handler(accessor, {})
    assert result.success
    assert result.message == "core", "Should delegate to core (second loaded)"

def test_handler_override_with_delegation():
    """Test game-specific handler can override and delegate to symlinked core."""
    from types import ModuleType
    behavior_manager = BehaviorManager()
    state = create_test_state()

    # Simulate loading order: game first, core last
    # Game handler adds weight check then delegates
    game_manipulation = ModuleType("game_manipulation")
    def game_handle_take(accessor, action):
        actor_id = action.get("actor_id", "player")
        # Weight check
        item = find_accessible_item(accessor, action.get("object"), actor_id)
        if item and item.properties.get("weight", 0) > 100:
            return HandlerResult(success=False, message="Too heavy")
        # Delegate to core
        return accessor.invoke_previous_handler("take", action)
    game_manipulation.handle_take = game_handle_take

    # Core handler does basic take
    core_manipulation = ModuleType("core_manipulation")
    def core_handle_take(accessor, action):
        return HandlerResult(success=True, message="Taken")
    core_manipulation.handle_take = core_handle_take

    behavior_manager.load_module(game_manipulation)
    behavior_manager.load_module(core_manipulation)
    accessor = StateAccessor(state, behavior_manager)

    # Heavy item rejected by game code
    action = {"actor_id": "player", "object": "anvil"}
    result = behavior_manager.get_handler("take")(accessor, action)
    assert not result.success
    assert "heavy" in result.message.lower()

    # Light item delegates to core
    action = {"actor_id": "player", "object": "feather"}
    result = behavior_manager.get_handler("take")(accessor, action)
    assert result.success
    assert result.message == "Taken"

def test_three_layer_handler_chain():
    """Test handler chaining through three layers: game → library → core."""
    from types import ModuleType
    behavior_manager = BehaviorManager()
    state = create_test_state()

    # Create three-layer chain
    game_module = ModuleType("game_module")
    def game_handle_test(accessor, action):
        # Game adds prefix and delegates
        result = accessor.invoke_previous_handler("test", action)
        if result.success:
            return HandlerResult(success=True, message=f"game:{result.message}")
        return result
    game_module.handle_test = game_handle_test

    library_module = ModuleType("library_module")
    def library_handle_test(accessor, action):
        # Library adds prefix and delegates
        result = accessor.invoke_previous_handler("test", action)
        if result.success:
            return HandlerResult(success=True, message=f"library:{result.message}")
        return result
    library_module.handle_test = library_handle_test

    core_module = ModuleType("core_module")
    def core_handle_test(accessor, action):
        # Core does actual work
        return HandlerResult(success=True, message="core")
    core_module.handle_test = core_handle_test

    # Load in order: game, library, core
    behavior_manager.load_module(game_module)
    behavior_manager.load_module(library_module)
    behavior_manager.load_module(core_module)

    accessor = StateAccessor(state, behavior_manager)

    # Call should flow: game → library → core, then unwind
    # BehaviorManager.invoke_handler() manages position list lifecycle
    result = behavior_manager.invoke_handler("test", accessor, {})
    assert result.success
    assert result.message == "game:library:core", f"Expected 'game:library:core' but got '{result.message}'"

def test_position_list_cleanup_on_handler_exception():
    """Test that position list is cleaned up even when handler raises exception."""
    from types import ModuleType
    behavior_manager = BehaviorManager()
    state = create_test_state()

    # Create handler that raises exception
    error_module = ModuleType("error_module")
    def error_handle_test(accessor, action):
        raise ValueError("Handler error for testing")
    error_module.handle_test = error_handle_test

    behavior_manager.load_module(error_module)
    accessor = StateAccessor(state, behavior_manager)

    # Invoke handler - should raise exception
    try:
        behavior_manager.invoke_handler("test", accessor, {})
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Handler error for testing" in str(e)

    # Verify position list was cleaned up despite exception
    assert behavior_manager._handler_position_list == [], \
        f"Position list should be empty after exception, got {behavior_manager._handler_position_list}"
```

## Testing Principles

The StateAccessor design enables straightforward testing:

1. **No mocking required**: Tests use real GameState objects and real handlers
2. **Verify both sides**: Check both the HandlerResult and actual state mutations
3. **Isolated setup**: `create_test_state()` provides a clean starting point for each test
4. **Behavior testing**: Load real behavior modules to test entity behavior integration
5. **Load order testing**: Critical tests verify handler chaining works as designed

Tests should be written for:
- Each handler's success path
- Each handler's error conditions (missing items, invalid operations)
- Entity behavior integration (behaviors allow/deny actions)
- Handler override and delegation chains
- Edge cases in StateAccessor operations (invalid paths, type mismatches)
- **NPC actor tests** (critical for validating actor_id threading)

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

## Critical: Testing NPC Actions

**Why NPC tests are essential:** The design threads `actor_id` through all utility functions to support NPCs. Without NPC-specific tests, it's easy to accidentally hardcode `"player"` instead of using the `actor_id` variable, which would break NPC functionality silently.

**NPC Test Pattern:**

```python
def test_npc_can_take_item():
    """Test that NPCs can take items using the same handlers as players."""
    state = create_test_state()
    behavior_manager = BehaviorManager()
    accessor = StateAccessor(state, behavior_manager)

    # Add an NPC to the test state
    from src.models import Actor
    guard = Actor(
        id="npc_guard",
        name="guard",
        location="location_room",
        inventory=[],
        properties={}
    )
    state.actors["npc_guard"] = guard

    # NPC takes an item
    action = {"actor_id": "npc_guard", "object": "sword"}
    result = handle_take(accessor, action)

    # Verify success
    assert result.success, f"NPC take failed: {result.message}"

    # Verify item is in NPC's inventory, NOT player's
    assert "item_sword" in guard.inventory, "Item should be in NPC inventory"
    player = state.actors["player"]
    assert "item_sword" not in player.inventory, "Item should NOT be in player inventory"

    # Verify item location changed to NPC
    sword = state.get_item("item_sword")
    assert sword.location == "npc_guard", f"Item location should be 'npc_guard', got '{sword.location}'"

def test_npc_drop_item():
    """Test that NPCs can drop items."""
    state = create_test_state()
    behavior_manager = BehaviorManager()
    accessor = StateAccessor(state, behavior_manager)

    # Add NPC with item in inventory
    from src.models import Actor
    guard = Actor(
        id="npc_guard",
        name="guard",
        location="location_room",
        inventory=["item_sword"],
        properties={}
    )
    state.actors["npc_guard"] = guard

    # Set sword location to NPC
    sword = state.get_item("item_sword")
    sword.location = "npc_guard"

    # NPC drops the item
    action = {"actor_id": "npc_guard", "object": "sword"}
    result = handle_drop(accessor, action)

    assert result.success
    assert "item_sword" not in guard.inventory
    assert sword.location == "location_room"

def test_npc_give_to_player():
    """Test that NPCs can give items to the player."""
    state = create_test_state()
    behavior_manager = BehaviorManager()
    accessor = StateAccessor(state, behavior_manager)

    # Add NPC with item
    from src.models import Actor
    guard = Actor(
        id="npc_guard",
        name="guard",
        location="location_room",
        inventory=["item_sword"],
        properties={}
    )
    state.actors["npc_guard"] = guard

    sword = state.get_item("item_sword")
    sword.location = "npc_guard"

    # NPC gives item to player
    action = {"actor_id": "npc_guard", "object": "sword", "indirect_object": "player"}
    result = handle_give(accessor, action)

    assert result.success
    player = state.actors["player"]
    assert "item_sword" not in guard.inventory, "Item should be removed from NPC"
    assert "item_sword" in player.inventory, "Item should be in player inventory"
    assert sword.location == "player"
```

**Common Mistakes These Tests Catch:**

1. **Hardcoded "player" string:**
```python
# BUG - this would pass player tests but fail NPC tests
item = find_accessible_item(accessor, obj_name, "player")  # ❌ Always uses player
```

2. **Using wrong variable:**
```python
# BUG - typo in variable name
item = find_accessible_item(accessor, obj_name, actor)  # ❌ Should be actor_id
```

3. **Forgetting to pass actor_id:**
```python
# BUG - missing parameter (caught by TypeError)
item = find_accessible_item(accessor, obj_name)  # ❌ Missing actor_id
```

**Test Coverage Requirement:** Every manipulation command handler (`take`, `drop`, `put`, `give`) should have at least one NPC test to verify the `actor_id` is correctly threaded through all utility calls.

## Critical: Testing Multiple Behaviors Per Entity

When an entity references multiple behavior modules, all matching event handlers must be invoked and their results combined correctly.

**Why these tests are essential:** The design allows entities like `behaviors=["lockable", "cursed"]` where both modules define the same event (e.g., `on_take`). Without tests, it's easy to accidentally return after the first behavior, breaking the composability guarantee.

**Multiple Behavior Test Pattern:**

```python
def test_multiple_behaviors_all_invoked():
    """Test that all matching behaviors are invoked, not just the first."""
    state = create_test_state()
    behavior_manager = BehaviorManager()

    # Load two behavior modules that both define on_take
    behavior_manager.load_module("behaviors.cursed_items")
    behavior_manager.load_module("behaviors.lockable_containers")

    accessor = StateAccessor(state, behavior_manager)

    # Create item with both behaviors
    from src.models import Item
    cursed_chest = Item(
        id="cursed_chest",
        name="cursed chest",
        location="location_room",
        portable=True,
        behaviors=["cursed_items", "lockable_containers"],
        properties={
            "cursed": True,
            "lock_id": "lock_chest_01"
        }
    )
    state.items["cursed_chest"] = cursed_chest

    action = {"actor_id": "player", "object": "cursed chest"}
    result = handle_take(accessor, action)

    # Should be denied (both behaviors say no)
    assert not result.success

    # CRITICAL: Message should contain feedback from BOTH behaviors
    assert "cursed" in result.message.lower() or "dark energy" in result.message.lower()
    assert "locked" in result.message.lower()

def test_multiple_behaviors_any_deny_wins():
    """Test that if any behavior denies, the action is denied (AND logic)."""
    state = create_test_state()
    behavior_manager = BehaviorManager()

    behavior_manager.load_module("behaviors.cursed_items")
    behavior_manager.load_module("behaviors.weight_limits")

    accessor = StateAccessor(state, behavior_manager)

    # Create item that is cursed (deny) but within weight limit (allow)
    from src.models import Item
    cursed_feather = Item(
        id="cursed_feather",
        name="cursed feather",
        location="location_room",
        portable=True,
        behaviors=["cursed_items", "weight_limits"],
        properties={
            "cursed": True,
            "weight": 1  # Very light, weight check would allow
        }
    )
    state.items["cursed_feather"] = cursed_feather

    action = {"actor_id": "player", "object": "cursed feather"}
    result = handle_take(accessor, action)

    # Should be denied because cursed_items.on_take returns allow=False
    # even though weight_limits.on_take would return allow=True
    assert not result.success
    assert "cursed" in result.message.lower() or "dark energy" in result.message.lower()

def test_multiple_behaviors_all_allow():
    """Test that action succeeds when all behaviors allow."""
    state = create_test_state()
    behavior_manager = BehaviorManager()

    behavior_manager.load_module("behaviors.light_sources")
    behavior_manager.load_module("behaviors.weight_limits")

    accessor = StateAccessor(state, behavior_manager)

    # Create item with two behaviors that both provide success messages
    from src.models import Item
    magic_lantern = Item(
        id="magic_lantern",
        name="magic lantern",
        location="location_room",
        portable=True,
        behaviors=["light_sources", "weight_limits"],
        properties={"weight": 5},
        states={"lit": False}
    )
    state.items["magic_lantern"] = magic_lantern

    action = {"actor_id": "player", "object": "magic lantern"}
    result = handle_take(accessor, action)

    # Should succeed
    assert result.success

    # Message should include effects from both behaviors
    # (e.g., "The runes flare to life" from light_sources AND weight confirmation)
    # Exact text depends on behavior implementation

def test_multiple_behaviors_invocation_order():
    """Test that behaviors are invoked in the order listed."""
    state = create_test_state()
    behavior_manager = BehaviorManager()

    behavior_manager.load_module("behaviors.behavior_a")
    behavior_manager.load_module("behaviors.behavior_b")

    accessor = StateAccessor(state, behavior_manager)

    # Create item with behaviors=["behavior_a", "behavior_b"]
    from src.models import Item
    test_item = Item(
        id="test_item",
        name="test item",
        location="location_room",
        portable=True,
        behaviors=["behavior_a", "behavior_b"]
    )
    state.items["test_item"] = test_item

    action = {"actor_id": "player", "object": "test item"}
    result = handle_take(accessor, action)

    # If both behaviors provide messages, they should appear in order:
    # behavior_a message first, then behavior_b message
    # (Implementation detail: messages joined with \n)
    lines = result.message.split("\n")
    assert "message from behavior_a" in lines[0]
    assert "message from behavior_b" in lines[1]
```

**Common Mistakes These Tests Catch:**

1. **Returning after first behavior:**
```python
# BUG - only invokes first matching behavior
for behavior_module_name in entity.behaviors:
    if hasattr(module, event_name):
        return handler(entity, accessor, context)  # ❌ Returns immediately
```

2. **Not combining messages:**
```python
# BUG - only returns last message, loses information from earlier behaviors
final_message = results[-1].message  # ❌ Should concatenate all messages
```

3. **Wrong combination logic:**
```python
# BUG - uses OR instead of AND (action allowed if ANY behavior allows)
final_allow = any(r.allow for r in results)  # ❌ Should be all()
```

**Test Coverage Requirement:** Any entity with 2+ behaviors in its `behaviors` list should have a test verifying all behaviors are invoked and results are combined correctly.
