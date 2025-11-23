# Simplifying game_engine.py with Entity Behaviors

## Overview

This document analyzes which behaviors in `src/game_engine.py` can be moved to entity behaviors once the behavior system is implemented, and what design changes are needed to support them.

## Current Behaviors in game_engine.py

### Behaviors That Can Become Entity Behaviors

#### 1. Chest Opening Win Condition (Lines 364-366)
**Current code:**
```python
if item_name == "chest":
    print("You open the chest and find treasure! You win!")
    return "win"
```

**As entity behavior:**
```python
# behaviors/items/treasure_chest.py
def on_open(entity, state, context):
    def set_win_flag(state):
        state.player.flags["won"] = True

    return EventResult(
        allow=True,
        message="You open the chest and find treasure! You win!",
        side_effects=set_win_flag
    )
```

**Design change needed:** The engine needs to check for win condition via `state.player.flags["won"]` instead of special return value.

#### 2. Potion Drinking Effect (Lines 421-430)
**Current code:**
```python
if item_name == "potion":
    print("You drink the glowing red potion.")
    print("You feel refreshed and energized!")
    state.player.inventory.remove(item_in_inventory.id)
    return True
```

**As entity behavior:**
```python
# behaviors/items/health_potion.py
def on_drink(entity, state, context):
    def consume_potion(state):
        state.player.inventory.remove(entity.id)
        state.player.stats["health"] = state.player.stats.get("health", 100) + 20

    return EventResult(
        allow=True,
        message="You drink the glowing red potion. You feel refreshed and energized!",
        side_effects=consume_potion
    )
```

**Design change needed:** Need `on_drink` event for items (not currently in design).

#### 3. Door Auto-Unlock on Pass Through (Lines 194-198)
**Current code:**
```python
# Case 5: Door is closed and locked, have key with auto-unlock
case (True, True, True, True):
    print("You unlock the door with your key and pass through.")
    door.locked = False
    door.open = True
```

**As entity behavior:**
```python
# behaviors/doors/auto_unlock_door.py
def on_pass_through(entity, state, context):
    player = context["player"]

    if entity.locked:
        # Check for key
        lock = state.get_lock_by_id(entity.lock_id)
        has_key = any(k in player.inventory for k in lock.opens_with)

        if has_key and lock.auto_unlock:
            def unlock_and_open(state):
                entity.locked = False
                entity.open = True

            return EventResult(
                allow=True,
                message="You unlock the door with your key and pass through.",
                side_effects=unlock_and_open
            )
        elif has_key:
            return EventResult(
                allow=False,
                message="The door is locked. You have the key but need to unlock it first."
            )
        else:
            return EventResult(
                allow=False,
                message="The door is locked. You need a key."
            )

    if not entity.open:
        return EventResult(
            allow=False,
            message="The door is closed. You need to open it first."
        )

    return EventResult(allow=True)
```

**This is already in the design** - `on_pass_through` is documented for doors.

#### 4. Door Unlock on Open (Lines 341-351)
**Current code:**
```python
if door.locked:
    has_key, _ = player_has_key_for_door(state, door)
    if has_key:
        print("You unlock the door with your key.")
        door.locked = False
        door.open = True
        return True
    else:
        print("The door is locked. You need a key.")
        return False
```

**As entity behavior:** Same pattern as above but for `on_open` event.

### Behaviors That Should Stay in Engine

#### 1. Movement Logic (move_player, lines 151-212)
Core engine responsibility - determines if movement is valid and updates player location.

**However:** The door interaction logic within `move_player` (lines 174-203) can be moved to door behaviors via `on_pass_through`.

#### 2. Basic Item Operations
- `take_item` - Core engine: moves item to inventory
- `drop_item` - Core engine: moves item to location
- `examine_item` - Core engine: returns description

**However:** Behaviors can hook into these via `on_take`, `on_drop`, `on_examine` to add custom effects.

#### 3. Location Description (describe_location, lines 94-139)
Core engine responsibility - displays location info.

**However:** `on_enter` and `on_examine` (for location) behaviors can add custom messages.

#### 4. Inventory Display (show_inventory, lines 142-148)
Pure UI/engine function - no entity-specific behavior.

#### 5. Save/Load (lines 450-469)
Meta-commands - not entity behaviors.

## Summary of Convertible Behaviors

| Behavior | Current Location | Entity Type | Event | Status |
|----------|-----------------|-------------|-------|--------|
| Chest win condition | open_item() | item | on_open | Can convert |
| Potion drinking | drink_item() | item | on_drink | **Needs new event** |
| Door auto-unlock on pass | move_player() | door | on_pass_through | Can convert |
| Door unlock on open | open_item() | door | on_open | Can convert |
| Door state messages | move_player() | door | on_pass_through | Can convert |

**Total: 5 behaviors can be moved to entity behaviors**

## Design Changes Required

### 1. Add `on_drink` Event for Items

Currently not in the entity_behaviors.md design. Add to Item Events:

```markdown
#### Item Events
- `on_drink` - When player drinks the item
- `on_eat` - When player eats the item
```

### 2. Add `on_eat` Event for Items

For consistency, also add eating behavior support.

### 3. Add Win Condition Checking

The engine needs a way to check for game-ending conditions. Options:

**Option A: Flag-based (Recommended)**
```python
# After processing any command
if state.player.flags.get("won"):
    print("\nYou win!")
    break
```

**Option B: Event-based**
Add `on_win` event that behaviors can trigger.

### 4. Item Consumption Pattern

Behaviors that consume items (potions, food) need a standard pattern:

```python
def on_drink(entity, state, context):
    def consume(state):
        state.player.inventory.remove(entity.id)
        # Item still exists in state.items but location is now empty
        entity.location = ""  # Or mark as consumed

    return EventResult(
        allow=True,
        message="...",
        side_effects=consume
    )
```

Consider adding a helper or standard pattern for this.

### 5. Lock/Key Access from Behaviors

Behaviors need access to locks and key checking:

```python
# Need state methods like:
state.get_lock_by_id(lock_id)
state.player_has_key_for_lock(lock_id)
```

Or pass lock info in context for door events.

### 6. Context Enhancement for Door Events

For `on_open` and `on_pass_through` on doors, include lock info in context:

```python
context = {
    "player": state.player,
    "location": current_location,
    "lock": lock,  # Lock object if door has one
    "has_key": has_key,  # Whether player has matching key
    "auto_unlock": auto_unlock  # Whether lock auto-unlocks
}
```

This prevents behaviors from needing to look up lock information themselves.

## Recommended Implementation Order

### Phase 1: Core Events
1. Add `on_drink` and `on_eat` to Item Events in design
2. Implement BehaviorManager
3. Add `behaviors` field to entity models and loader

### Phase 2: Simple Conversions
1. Convert chest win condition to behavior
2. Convert potion drinking to behavior
3. Add flag-based win condition checking to engine

### Phase 3: Door Behaviors
1. Add lock/key info to door event context
2. Convert door unlock-on-open to behavior
3. Convert door auto-unlock-on-pass to behavior

### Phase 4: Cleanup
1. Remove hardcoded item-specific logic from engine
2. Simplify `move_player()` to delegate door handling to behaviors
3. Simplify `open_item()` to delegate to behaviors

## Benefits of Conversion

1. **Data-driven behavior**: Game authors can add new items with custom behaviors without modifying engine code
2. **Testability**: Each behavior can be unit tested independently
3. **Maintainability**: Behaviors are localized to specific entities
4. **Flexibility**: Same engine supports many different game types

## What Remains in Engine After Conversion

The game_engine.py would be simplified to:

- **State management**: Moving items, updating locations
- **Command routing**: Parse command → find entity → invoke behavior → apply result
- **Default behaviors**: Standard take/drop/examine for entities without custom behaviors
- **Meta-commands**: Save/load/quit/inventory
- **Win/lose condition checking**: Check flags after each command

The engine becomes a generic command processor that delegates all entity-specific logic to behaviors.

## Estimated Code Reduction

| Function | Current Lines | After Conversion |
|----------|--------------|-----------------|
| move_player() | 62 | ~30 (door logic moved) |
| open_item() | 58 | ~20 (chest/door logic moved) |
| drink_item() | 44 | ~15 (potion logic moved) |
| **Total** | 164 | ~65 |

Approximately **100 lines** of entity-specific logic can move to behaviors.

## Conclusion

The entity_behaviors design can handle most of the custom behaviors currently hardcoded in game_engine.py. The main additions needed are:

1. **`on_drink` and `on_eat` events** for items
2. **Lock/key context** for door events
3. **Win condition flag checking** in engine

With these changes, 5 specific behaviors can be moved out of the engine, reducing approximately 100 lines of entity-specific code and making the engine truly generic.
