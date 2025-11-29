# Entity Behaviors Implementation Plan

## Overview

This document outlines the step-by-step implementation plan for the entity behaviors system. The implementation is organized to:
1. Build and test infrastructure first
2. Enable behavior modules with minimal engine changes
3. Only then migrate existing behaviors from the engine

## Implementation Phases

### Phase 1: Core Infrastructure

**Goal**: Create the BehaviorManager and EventResult classes, with tests proving they work.

#### 1.1 Create behavior_manager.py

Create `src/behavior_manager.py` with:
- `EventResult` dataclass (allow, message)
- `BehaviorManager` class with:
  - `_behavior_cache` for loaded behaviors
  - `_handlers` for registered command handlers
  - `_vocabulary_extensions` for vocabulary additions
  - `discover_modules()` - auto-discover modules in behaviors/ directory (follows symlinks)
  - `load_module()` - scan module for handle_* and vocabulary
  - `load_behavior()` - load specific module:function path
  - `invoke_behavior()` - call behavior with entity, state, context
  - `get_handler()` / `has_handler()` - check for registered handlers
  - `get_merged_vocabulary()` - merge extensions with base vocabulary
  - `clear_cache()` - for hot reload support
- `get_behavior_manager()` - global instance accessor

#### 1.2 Create tests for BehaviorManager

Create `tests/test_behavior_manager.py`:
- Test `load_module()` registers handlers and vocabulary
- Test `load_behavior()` loads and caches functions
- Test `invoke_behavior()` calls function with correct args
- Test `get_merged_vocabulary()` merges correctly
- Test error handling for missing modules/functions
- Test `EventResult` creation and defaults

#### 1.3 Create behaviors directory structure

```
behaviors/
├── __init__.py
├── core/
│   └── __init__.py
└── items/
    └── __init__.py
```

### Phase 2: Protocol Handler Integration

**Goal**: Modify JSONProtocolHandler to use BehaviorManager for command routing and behavior invocation.

#### 2.1 Update JSONProtocolHandler

Modify `src/json_protocol.py`:
- Add `behavior_manager` parameter to `__init__`
- Create `_builtin_handlers` dict mapping verbs to methods
- Modify `handle_command()` to:
  1. Check registered handlers first (`behavior_manager.get_handler()`)
  2. Fall back to builtin handlers
- Add `_apply_behavior()` method:
  - Build event name from verb (`on_{verb}`)
  - Build context with location
  - Call `behavior_manager.invoke_behavior()`
  - Handle EventResult (allow/message)
  - Remove `entity_obj` before returning
- Update all `_cmd_*` methods to include `entity_obj` in successful results

#### 2.2 Update handler method signatures

Built-in handlers need to include `entity_obj` for behaviors to be invoked:
```python
return {
    "type": "result",
    "success": True,
    "action": "take",
    "entity": self._entity_to_dict(item),
    "entity_obj": item  # ADD THIS
}
```

Methods to update:
- `_cmd_take`
- `_cmd_drop`
- `_cmd_examine`
- `_cmd_go`
- `_cmd_open`
- `_cmd_close`
- `_cmd_unlock`
- `_cmd_lock`
- `_cmd_drink`
- `_cmd_eat`
- `_cmd_attack`
- `_cmd_use`
- `_cmd_read`
- `_cmd_climb`
- `_cmd_pull`
- `_cmd_push`

#### 2.3 Create integration tests

Create `tests/test_protocol_behaviors.py`:
- Test registered handler takes precedence over builtin
- Test behavior invocation after successful command
- Test behavior can prevent action (allow=False)
- Test behavior message appears in result
- Test entity_obj is removed from final result
- Test context contains location

### Phase 3: Update Data Models

**Goal**: Add behaviors field to entity models and update loader.

#### 3.1 Update models

Modify `src/state_manager/models.py`:
- Add `behaviors: Dict[str, str] = field(default_factory=dict)` to:
  - `Item`
  - `NPC`
  - `Door`
  - `Location`

#### 3.2 Update loader

Modify `src/state_manager/loader.py`:
- Parse `behaviors` dict from JSON for each entity type
- Map to model's behaviors field

#### 3.3 Create tests for model updates

Create `tests/test_behaviors_loading.py`:
- Test loading game state with behaviors field
- Test behaviors field defaults to empty dict
- Test behaviors correctly mapped to entities

### Phase 4: Create First Behavior Module

**Goal**: Create a test behavior module to validate the complete flow.

#### 4.1 Create rubber duck example

Create `behaviors/items/rubber_duck.py`:
- `vocabulary` dict with "squeeze" verb
- `handle_squeeze()` command handler
- `on_squeeze()` entity behavior

This is a complete example from the design doc that exercises all features.

#### 4.2 Create test fixture

Create `tests/fixtures/test_game_with_behaviors.json`:
- Include rubber duck item with behaviors field
- Include other items without behaviors for comparison

#### 4.3 Create end-to-end tests

Create `tests/test_behavior_end_to_end.py`:
- Test loading game with behaviors
- Test squeeze command reaches handler
- Test handler invokes entity behavior
- Test behavior modifies entity state
- Test behavior message in result

### Phase 5: Migrate Core Behaviors

**Goal**: Move hardcoded behaviors from engine to behavior modules.

#### 5.1 Create consumables.py

Create `behaviors/core/consumables.py`:
- `handle_drink()` - command handler
- `handle_eat()` - command handler
- `on_drink_health_potion()` - entity behavior

Current hardcoded behavior in `game_engine.py` lines 404-447:
- Potion drinking effect
- Removes item from inventory
- Could add health restoration

Tests:
- Test drink command finds item in inventory
- Test behavior removes item and updates stats
- Test non-drinkable items fail gracefully

#### 5.2 Create light_sources.py

Create `behaviors/core/light_sources.py`:
- `on_take()` - auto-light behavior
- `on_drop()` - auto-extinguish behavior

Current hardcoded behavior in `json_protocol.py` lines 147-149, 192-194:
- Auto-light lantern on take
- Extinguish on drop

Tests:
- Test taking lantern sets lit=True
- Test dropping lantern sets lit=False
- Test non-light items unaffected

#### 5.3 Create containers.py

Create `behaviors/core/containers.py`:
- `on_open_treasure_chest()` - win condition behavior

Current hardcoded behavior in `game_engine.py` lines 364-366:
- Check for chest name
- Set won flag
- Return win message

Tests:
- Test opening chest sets won flag
- Test win condition checking after command

#### 5.4 Update game state files

Update `examples/simple_game_state.json`:
- Add behaviors field to potion with `on_drink`
- Add behaviors field to lantern with `on_take` and `on_drop`
- Add behaviors field to chest with `on_open`

Update `tests/llm_interaction/fixtures/test_game_state.json`:
- Same behavior additions

### Phase 6: Remove Hardcoded Logic

**Goal**: Clean up engine after behaviors are migrated.

#### 6.1 Clean json_protocol.py

Remove from `_cmd_take`:
- Lines 147-149: auto-light logic (now in behavior)

Remove from `_cmd_drop`:
- Lines 192-194: extinguish logic (now in behavior)

The drink/eat handlers in json_protocol.py can stay as they're already simple (just find item, return result). The actual consumption logic will be in behaviors.

#### 6.2 Clean game_engine.py (temporary)

Remove from `drink_item`:
- Lines 423-429: potion-specific logic

Remove from `open_item`:
- Lines 364-366: chest win condition

These are temporary removals before the full refactoring in 6.4.

#### 6.3 Add win condition checking

Update game loop in `game_engine.py` to check flags:
```python
if state.player.flags.get("won"):
    print("\nCongratulations! You win!")
    break
```

#### 6.4 Refactor game_engine.py to use JSONProtocolHandler

Refactor the text-based engine to use JSONProtocolHandler as the single source of truth:

**Remove duplicate functions**:
- `move_player()` - use `_cmd_go`
- `take_item()` - use `_cmd_take`
- `drop_item()` - use `_cmd_drop`
- `examine_item()` - use `_cmd_examine`
- `open_item()` - use `_cmd_open`
- `close_door()` - use `_cmd_close`
- `drink_item()` - use `_cmd_drink`

**Keep UI formatting functions**:
- `describe_location()` - format location for text display
- `show_inventory()` - format inventory for text display

**Add result formatting**:
- `_format_result()` - convert JSON result to text output
- Handle success messages from behaviors
- Handle error messages

**Update main loop**:
```python
# Convert parsed command to JSON action
action = {"verb": result.verb.word}
if result.direct_object:
    action["object"] = result.direct_object.word
if result.direction:
    action["direction"] = result.direction.word

# Process through JSON handler
json_result = json_handler.handle_command({"type": "command", "action": action})

# Format and display result
print(_format_result(json_result))
```

**Tests**:
- Test text commands produce same results as JSON commands
- Test behavior messages appear in text output
- Test win/lose conditions work correctly

### Phase 7: Documentation and Polish

**Goal**: Complete documentation and examples.

#### 7.1 Update design document

Review `docs/entity_behaviors.md`:
- Ensure all examples match implementation
- Add any discovered edge cases
- Update migration path to "Complete"

#### 7.2 Create behavior authoring guide

Create `docs/behavior_authoring_guide.md`:
- Step-by-step guide for creating behaviors
- Template for new behavior modules
- Common patterns and pitfalls
- Testing recommendations

#### 7.3 Update example game state

Ensure `examples/simple_game_state.json` demonstrates:
- Items with behaviors
- Items without behaviors
- Multiple behaviors on same entity

## Behavior Modules to Create

### Core Behaviors (behaviors/core/)

| Module | Handlers | Entity Behaviors | Current Location |
|--------|----------|------------------|------------------|
| consumables.py | handle_drink, handle_eat | on_drink_health_potion | game_engine.py drink_item |
| light_sources.py | (none) | on_take, on_drop | json_protocol.py _cmd_take/drop |
| containers.py | (none) | on_open_treasure_chest | game_engine.py open_item |

### Example Behaviors (behaviors/items/)

| Module | Handlers | Entity Behaviors | Purpose |
|--------|----------|------------------|---------|
| rubber_duck.py | handle_squeeze | on_squeeze | Complete example from design |

## Testing Strategy

### Unit Tests

Each module should have corresponding tests:
- `test_behavior_manager.py` - BehaviorManager class
- `test_protocol_behaviors.py` - Protocol handler integration
- `test_behaviors_loading.py` - Model and loader updates
- `test_consumables.py` - Consumables behavior module
- `test_light_sources.py` - Light sources behavior module
- `test_containers.py` - Containers behavior module
- `test_rubber_duck.py` - Example behavior module

### Integration Tests

- `test_behavior_end_to_end.py` - Full flow from command to result

### Coverage Goals

- 80% coverage on new code
- All behavior functions tested
- All handler functions tested
- Error paths tested

## Dependencies Between Phases

```
Phase 1 (Infrastructure)
    ↓
Phase 2 (Protocol Integration)
    ↓
Phase 3 (Data Models)
    ↓
Phase 4 (First Module)
    ↓
Phase 5 (Migrate Behaviors)
    ↓
Phase 6 (Remove Hardcoded)
    ↓
Phase 7 (Documentation)
```

Phases must be completed in order. Within each phase, items can be done in parallel where noted.

## Estimated Line Changes

| File | Additions | Removals | Net |
|------|-----------|----------|-----|
| src/behavior_manager.py | ~150 | 0 | +150 |
| src/json_protocol.py | ~80 | ~10 | +70 |
| src/state_manager/models.py | ~8 | 0 | +8 |
| src/state_manager/loader.py | ~20 | 0 | +20 |
| behaviors/core/consumables.py | ~70 | 0 | +70 |
| behaviors/core/light_sources.py | ~30 | 0 | +30 |
| behaviors/core/containers.py | ~20 | 0 | +20 |
| behaviors/items/rubber_duck.py | ~60 | 0 | +60 |
| game_engine.py | ~80 | ~350 | -270 |
| **Total** | ~518 | ~360 | +158 |

Plus ~500 lines of tests (including game_engine refactoring tests).

## Design Decisions

### Module Discovery

Behavior modules are auto-discovered by scanning the `behaviors/` directory. This approach:
- Requires no explicit configuration
- Automatically finds all `*.py` files in subdirectories
- Follows symlinks, enabling shared core behaviors across multiple games

For per-game behaviors with shared core, use symlinks:
```
my_game/
├── behaviors/
│   ├── core -> /path/to/engine/behaviors/core/  # symlink to shared
│   └── items/
│       └── game_specific.py
└── game_state.json
```

### game_engine.py Refactoring

The text-based game engine (`game_engine.py`) will be refactored to use `JSONProtocolHandler` internally, eliminating duplicate logic. This keeps JSONProtocolHandler as the single source of truth for game state changes.

**Approach**:
1. game_engine.py becomes a text UI wrapper around JSONProtocolHandler
2. Parser converts text commands to JSON action dicts
3. JSONProtocolHandler processes actions and returns results
4. game_engine.py formats results for text display

**Changes to game_engine.py**:
- Remove duplicate functions: `move_player()`, `take_item()`, `drop_item()`, `examine_item()`, `open_item()`, `close_door()`, `drink_item()`
- Keep: `describe_location()`, `show_inventory()` (UI formatting)
- Keep: `save_game()`, `load_game()` (file operations)
- Add: `_format_result()` to convert JSON results to text output

**Command flow after refactoring**:
```
User input → Parser → JSON action dict → JSONProtocolHandler → JSON result → text output
```

**Benefits**:
- Single implementation of game logic
- Behaviors work identically in both text and LLM modes
- Easier to maintain and test

**Implementation**: Add as Phase 6.4 after removing hardcoded logic

## Open Questions

1. **Behavior hot reload**: During development, should there be a command to reload behaviors without restarting?

## Success Criteria

- [ ] BehaviorManager loads modules and invokes behaviors
- [ ] Protocol handler uses registered handlers and invokes behaviors
- [ ] Entity models support behaviors field
- [ ] At least one new verb (squeeze) works end-to-end
- [ ] All three core behaviors migrated (consumables, light, containers)
- [ ] Hardcoded logic removed from engine
- [ ] All tests pass with 80% coverage on new code
- [ ] Documentation updated
