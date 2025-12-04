# Implicit Positioning Implementation Patterns

This document describes the common patterns and helper functions for adding implicit positioning to verb handlers.

## Overview

Implicit positioning automatically moves the player close to entities that require proximity for interaction. This is controlled by the `interaction_distance` property:
- `"any"` (default) - Can interact from anywhere in location, no movement
- `"near"` - Must be close to interact, triggers automatic movement

## Commands with Implicit Positioning

### Implemented (Implicit)
- **examine** - Sets focus, moves if "near"
- **look at \<object\>** - Redirects to examine (sets focus, moves if "near")
- **take** - Sets focus, moves if "near"
- **open** - Sets focus, moves if "near"
- **close** - Sets focus, moves if "near"

### Implemented (Explicit)
- **approach** - Always sets focus and moves (explicit positioning command)

### Posture Commands
- **take cover** - Sets focus, posture="cover", requires provides_cover property
- **hide** - Sets focus, posture="concealed", requires allows_concealment property
- **climb** - Sets focus, posture="climbing", requires climbable property
- **Posture clearing** - Automatically cleared when moving to different entity

### No Positioning
- **look** (no object) - Describes room, doesn't change focus

### Universal Surfaces
- **ceiling, floor, sky, walls** - Can be examined without explicit parts
- Returns default descriptions unless overridden by explicit Part entities
- Does not set focus or trigger positioning (no real entity)
- Synonyms supported (ground = floor)

## Helper Functions (utilities/positioning.py)

### Core Functions

#### `try_implicit_positioning(accessor, actor_id, target_entity)`
Low-level positioning logic. Use this when you already have the entity.

**Returns:** `(moved: bool, message: Optional[str])`
- Always sets `focused_on` to target entity
- Only generates movement message for "near" entities
- Clears posture when moving
- No repeated movement if already focused

#### `find_and_position_item(accessor, actor_id, object_name, adjective=None)`
Most common pattern - combines item finding with positioning.

**Returns:** `(item: Optional[Item], position_message: Optional[str])`
- Finds accessible item
- Applies implicit positioning
- Returns None if item not found

#### `find_and_position_part(accessor, actor_id, object_name, location_id)`
Same as above but for parts.

**Returns:** `(part: Optional[Part], position_message: Optional[str])`

#### `build_message_with_positioning(base_messages, position_message)`
Combines messages ensuring movement appears first.

**Args:**
- `base_messages: List[str]` - Action result messages
- `position_message: Optional[str]` - Movement message from positioning

**Returns:** `str` - Combined message with movement prefix if present

## Implementation Pattern for Verbs

### Pattern 1: Simple Item Interaction (take, open, close, use, etc.)

```python
from utilities.positioning import find_and_position_item, build_message_with_positioning

def handle_verb(accessor, action):
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    adjective = action.get("adjective")

    # Combined find + position
    item, move_msg = find_and_position_item(accessor, actor_id, object_name, adjective)

    if not item:
        return HandlerResult(success=False, message="You don't see that here.")

    # ... perform action checks and state updates ...

    # Build messages
    base_messages = ["You opened the chest."]
    # ... add more messages as needed ...

    # Combine with positioning
    message = build_message_with_positioning(base_messages, move_msg)

    return HandlerResult(success=True, message=message)
```

### Pattern 2: Item or Part (examine)

```python
from utilities.positioning import find_and_position_item, find_and_position_part

def handle_examine(accessor, action):
    actor_id = action.get("actor_id", "player")
    object_name = action.get("object")
    adjective = action.get("adjective")
    location = accessor.get_current_location(actor_id)

    # Try item first
    item, move_msg = find_and_position_item(accessor, actor_id, object_name, adjective)
    if item:
        message_parts = []
        if move_msg:
            message_parts.append(move_msg)
        message_parts.append(f"{item.name}: {item.description}")
        return HandlerResult(success=True, message="\n".join(message_parts))

    # Then try part
    part, move_msg = find_and_position_part(accessor, actor_id, object_name, location.id)
    if part:
        message_parts = []
        if move_msg:
            message_parts.append(move_msg)
        # ... add part messages ...
        return HandlerResult(success=True, message="\n".join(message_parts))

    # Not found
    return HandlerResult(success=False, message="You don't see that here.")
```

### Pattern 3: Manual Positioning (when entity is found differently)

```python
from utilities.positioning import try_implicit_positioning

def handle_special(accessor, action):
    # Custom entity finding logic...
    entity = some_custom_find_function()

    if not entity:
        return HandlerResult(success=False, message="Not found.")

    # Apply positioning manually
    moved, move_msg = try_implicit_positioning(accessor, actor_id, entity)

    message_parts = []
    if move_msg:
        message_parts.append(move_msg)
    # ... continue with action ...
```

## Test Pattern

### Standard Test Structure

```python
def test_verb_near_distance_moves_player(self):
    """Test verb with 'near' entity moves player."""
    player = self.accessor.get_actor("player")

    # Verify not focused initially
    self.assertIsNone(player.properties.get("focused_on"))

    action = make_action(verb="verb", object="desk")
    result = handle_verb(self.accessor, action)

    self.assertTrue(result.success)
    # Should include movement message
    self.assertIn("move", result.message.lower())
    # Should set focus
    self.assertEqual(player.properties.get("focused_on"), "item_desk")

def test_verb_already_focused_no_movement(self):
    """Test verb when already focused doesn't repeat movement."""
    player = self.accessor.get_actor("player")
    player.properties["focused_on"] = "item_desk"

    action = make_action(verb="verb", object="desk")
    result = handle_verb(self.accessor, action)

    self.assertTrue(result.success)
    # Should NOT include movement message
    self.assertNotIn("move", result.message.lower())

def test_verb_clears_posture_when_moving(self):
    """Test verb clears posture when moving to new entity."""
    player = self.accessor.get_actor("player")
    player.properties["focused_on"] = "item_other"
    player.properties["posture"] = "cover"

    action = make_action(verb="verb", object="desk")
    result = handle_verb(self.accessor, action)

    self.assertTrue(result.success)
    # Posture should be cleared
    self.assertIsNone(player.properties.get("posture"))
```

## Remaining Verbs for Phase 2

### handle_take
- Uses `find_and_position_item`
- Position before checking portability/weight
- Movement message before "You take the key."

### handle_drop
- Usually doesn't need positioning (dropping at current location)
- May want to position if dropping "on" something specific
- Consider: "drop key on desk" should position to desk

### handle_open / handle_close
- Uses `find_and_position_item` for containers
- Also check doors (may need special handling)
- Position before state check (already open/closed)

### Notes
- All handlers should update `focused_on` when interacting with entities
- Movement only happens for `interaction_distance: "near"` entities
- Posture clears only when actually moving, not just updating focus
- Movement messages always appear before action results
- No repeated movement if already at target entity
