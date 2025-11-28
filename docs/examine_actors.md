# Design: Examining Actors

## Issue

GitHub Issue #36: Add support for examining actors (self and NPCs)

## Problem

Currently "examine player" fails with "You don't see any player here" because `handle_examine` in `behaviors/core/perception.py` only searches:
1. Items (`find_accessible_item`)
2. Doors (`find_door_with_adjective`)
3. Exits (`find_exit_by_name`)
4. Locks (`find_lock_by_context`)

Actors are never searched, even though the infrastructure exists:
- `Actor` class has `llm_context` property (state_manager.py:330-338)
- `entity_serializer.py` detects actors via `inventory` attribute and serializes them
- `accessor.get_actors_in_location()` exists
- Game state files can have `llm_context` on actors (fancy_game_state.json does)

## Design Goals

1. Enable examining self ("examine self", "examine me")
2. Enable examining NPCs in same location ("examine guard")
3. Provide helpful message for "examine player" (guide toward "self"/"me")
4. **No code duplication** - reuse existing patterns and utilities
5. **Prefer restructuring for consistency** - restructuring is preferable if it improves consistency and simplifies the codebase

## Approach

### 1. Add Self-Reference Nouns via Vocabulary

Add "self" noun with "me" synonym in a new `behaviors/core/actors.py` module:

```python
vocabulary = {
    "verbs": [],
    "nouns": [
        {
            "word": "self",
            "synonyms": ["me", "myself"],
            "llm_context": {
                "traits": ["self-reference", "the acting character"]
            }
        }
    ],
    "adjectives": [],
    "directions": []
}
```

**Rationale**: Using the vocabulary system ensures "self" and "me" are recognized by the parser and passed as the `object` field in actions. This follows the established pattern where behavior modules extend vocabulary.

**Why not "player"**: "player" is ambiguous in multiplayer scenarios and refers to the entity ID, not a self-reference concept. Using "self"/"me" is clearer semantically.

### 2. Add Helper Function for Actor Lookup

Add `find_actor_by_name` to `utilities/utils.py` following the pattern of `find_accessible_item`:

```python
def find_actor_by_name(
    accessor,
    name: Union[WordEntry, str],
    actor_id: str
) -> Optional[Actor]:
    """
    Find an actor accessible to the examining actor.

    Handles special cases:
    - "self"/"me"/"myself" -> returns the acting actor
    - Other names -> searches actors in same location

    Args:
        accessor: StateAccessor instance
        name: Actor name or self-reference word
        actor_id: ID of the actor doing the examining

    Returns:
        Actor if found, None otherwise
    """
    actor = accessor.get_actor(actor_id)
    if not actor:
        return None

    # Handle self-reference
    if name_matches(name, "self"):
        return actor

    # Search actors in same location
    location = accessor.get_current_location(actor_id)
    if not location:
        return None

    for other_actor in accessor.get_actors_in_location(location.id):
        # Don't return self when searching by name
        if other_actor.id == actor_id:
            continue
        if name_matches(name, other_actor.name):
            return other_actor

    return None
```

**Reuse**: Uses existing `name_matches()` for synonym handling, `accessor.get_actor()`, `accessor.get_current_location()`, and `accessor.get_actors_in_location()`.

### 3. Extend handle_examine in perception.py

Add actor search **after** existing lock search, **before** the final "not found" message. This placement ensures items/doors/exits/locks take precedence (avoiding conflicts if an item is named "me" or similar).

```python
# After lock handling (around line 301), before final return:

# Special case: redirect "examine player" to use "self"/"me"
# Check BEFORE actor search to ensure consistent behavior regardless of player.name
if name_matches(object_name, "player"):
    return HandlerResult(
        success=False,
        message="To examine yourself, use 'examine self' or 'examine me'. To examine another player, use their name (e.g., 'examine Blake' or 'examine Ayomide')."
    )

# Try to find an actor
target_actor = find_actor_by_name(accessor, object_name, actor_id)

if target_actor:
    # Check observability (handles invisible actors)
    visible, reason = is_observable(
        target_actor, accessor, accessor.behavior_manager,
        actor_id=actor_id, method="examine"
    )
    if not visible:
        # Invisible actor - fail silently (don't reveal existence)
        # Fall through to "not found" message
        pass
    else:
        message_parts = []
        is_self = (target_actor.id == actor_id)

        # Build description
        if is_self:
            # Self-examination
            if target_actor.description:
                message_parts.append(target_actor.description)
            else:
                message_parts.append("You examine yourself.")
        else:
            # Other actor examination
            if target_actor.description:
                message_parts.append(f"{target_actor.name}: {target_actor.description}")
            else:
                message_parts.append(f"You see {target_actor.name}.")

        # Show inventory using shared helper
        inv_message, inv_data = format_inventory(accessor, target_actor, for_self=is_self)
        if inv_message:
            message_parts.append(inv_message)

        # Invoke actor behaviors (on_examine)
        result = accessor.update(target_actor, {}, verb="examine", actor_id=actor_id)
        if result.message:
            message_parts.append(result.message)

        # Use unified serializer for llm_context with trait randomization
        data = serialize_for_handler_result(target_actor)

        return HandlerResult(
            success=True,
            message="\n".join(message_parts),
            data=data
        )

return HandlerResult(
    success=False,
    message=f"You don't see any {object_name} here."
)
```

**Reuse**:
- `is_observable()` - existing observability check used for items
- `serialize_for_handler_result()` - already handles actors
- `accessor.update()` with verb - existing behavior invocation pattern

### 4. Update Vocabulary llm_context

In `behaviors/core/perception.py`, update the examine verb's `llm_context`:

```python
{
    "word": "examine",
    "event": "on_examine",
    "synonyms": ["inspect", "x"],
    "object_required": True,
    "llm_context": {
        "traits": ["reveals details", "non-destructive", "provides information"],
        "valid_objects": ["items", "doors", "exits", "locks", "actors"]  # Add "actors"
    }
}
```

## File Changes

| File | Change |
|------|--------|
| `behaviors/core/actors.py` | **New file** - vocabulary with "self" noun |
| `utilities/utils.py` | Add `find_actor_by_name()` and `format_inventory()` functions |
| `behaviors/core/perception.py` | Extend `handle_examine` to search actors; refactor `handle_inventory` to use `format_inventory()` |
| `src/validators.py` | Add `_validate_actor_names()` for prohibited names |
| `tests/test_examine_actors.py` | **New file** - test suite |
| `examples/*.json` | Rename player.name from "player" to "hero" |

## Entity Search Order in handle_examine

After this change, `handle_examine` searches in this order:
1. Items (`find_accessible_item`)
2. Doors (`find_door_with_adjective`)
3. Exits (`find_exit_by_name`)
4. Locks (`find_lock_by_context`)
5. Special case: "player" -> helpful message - NEW
6. **Actors** (`find_actor_by_name`) - NEW
7. Not found error

This order ensures:
- Existing behavior unchanged for items/doors/exits/locks
- "player" always redirects to "self"/"me" (regardless of player.name field)
- No conflicts if an item happens to be named "self" (item wins)

## Test Cases

### Self-examination
- `examine self` -> returns player's description, inventory, and llm_context
- `examine me` -> same as above (synonym)
- `examine myself` -> same as above (synonym)
- Self-examine with items in inventory -> shows "You are carrying: sword, key"
- Self-examine with empty inventory -> no inventory line shown

### NPC examination
- `examine guard` when guard is in same location -> returns guard's info and inventory
- `examine guard` when guard is elsewhere -> "You don't see any guard here."
- NPC with items -> shows "Carrying: sword, shield"

### Observability (invisible actors)
- `examine self` when player is invisible -> "You don't see any self here."
- `examine guard` when guard is invisible -> "You don't see any guard here."
- Invisible actor not revealed by error message (same message as non-existent)

### Behaviors
- Examining actor with on_examine behavior -> behavior is invoked
- Behavior message appended to description

### Edge cases
- `examine player` -> helpful message suggesting "self" or "me"
- Player examining self when no description -> "You examine yourself."
- NPC with no description -> "You see Guard."
- NPC with no llm_context -> works without traits (serializer handles this)

### Validator
- Actor named "player" -> validation error
- Actor named "Player" (uppercase) -> validation error (case-insensitive)
- Actor named "NPC" -> validation error
- Actor named "self" -> validation error
- Actor named "me" -> validation error
- Actor named "myself" -> validation error
- Actor with ID "player" but name "hero" -> valid (ID can be "player")
- Actor named "guard" -> valid

### No regression
- All existing examine tests still pass
- Items/doors/exits/locks still found before actors
- All existing validation tests still pass

## Implementation Notes

1. **No actors.py handler needed**: We're extending perception's `handle_examine`, not adding a new verb. The actors.py module only contributes vocabulary.

2. **entity_serializer already works**: The `serialize_for_handler_result()` function detects actors via `hasattr(entity, 'inventory')` and returns `type: "actor"`.

3. **name_matches handles synonyms**: When the parser sees "me", it looks up the vocabulary noun "self" with synonyms ["me", "myself"]. The action's `object` field gets the WordEntry, which `name_matches()` handles correctly.

4. **get_actors_in_location exists**: No need to write new accessor methods.

5. **is_observable for actors**: Confirmed - `is_observable()` explicitly documents support for Actor entities in its docstring: `entity: Entity to check (Item, Actor, ExitDescriptor, etc.)`.

6. **accessor.update for actors**: Confirmed - `accessor.update()` explicitly documents support for Actor entities: `entity: The entity to modify (Item, Actor, Location, etc.)`. Actors have a `behaviors` field so behavior invocation will work.

## Alternatives Considered

### A. Add actor search to find_accessible_item
Rejected: Would conflate item and actor search. Cleaner to have separate `find_actor_by_name`.

### B. Create new "examine_self" verb
Rejected: Over-engineering. "examine" already handles multiple entity types; actors are just another type.

### C. Allow "player" as self-reference
Rejected per requirements: Ambiguous with multiplayer. "self"/"me" is semantically clearer.

## Design Decisions (Confirmed)

1. **NPCs can examine the player**: Yes, via `find_actor_by_name`. Symmetrical capability.

2. **Inventory displayed on examine**: Yes, for both self and other actors. Shows what they're carrying.

3. **Actor behaviors triggered**: Yes, examining an actor invokes `on_examine` behaviors via `accessor.update()`, same as items.

4. **Invisible actors**: Examining an invisible actor fails, including examining self when invisible. Uses existing `is_observable()` check for consistency with item visibility.

## Review Notes

### RESOLVED: "examine player" special case ordering

**Original issue**: The special case for "examine player" came after the actor search, so if player.name was "player", the actor would be found first.

**Resolution**: Moved "player" check before actor search. Now "examine player" always gives the helpful message regardless of what the player's `name` field contains.

### RESOLVED: Inventory display consolidation

The inventory display code in actor examination was similar to `handle_inventory`. Per goal 5 (prefer restructuring), extract a `format_inventory()` helper.

**Resolution**: Add `format_inventory()` to `utilities/utils.py`:

```python
def format_inventory(
    accessor,
    actor,
    for_self: bool = True
) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    """
    Format an actor's inventory for display.

    Args:
        accessor: StateAccessor instance
        actor: Actor whose inventory to format
        for_self: If True, use "You are carrying"; if False, use "Carrying"

    Returns:
        Tuple of (message string or None if empty, list of serialized items)
    """
    if not actor.inventory:
        return None, []

    item_names = []
    items_data = []
    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item:
            item_names.append(item.name)
            items_data.append(serialize_for_handler_result(item))

    if not item_names:
        return None, []

    prefix = "You are carrying" if for_self else "Carrying"
    return f"{prefix}: {', '.join(item_names)}", items_data
```

Both `handle_inventory` and actor examination will use this shared function.

### RESOLVED: Actor name ambiguity

**Issue**: If an actor's `name` field is "player", it could be found by `find_actor_by_name` before the "examine player" special case has a chance to guide users.

**Resolution**: Prohibit certain actor names via validation. Add `_validate_actor_names()` to `src/validators.py`:

```python
# Prohibited actor names (case-insensitive)
PROHIBITED_ACTOR_NAMES = {"player", "npc", "self", "me", "myself"}

def _validate_actor_names(state: "GameState", errors: List[str]) -> None:
    """Validate that actors don't have prohibited names."""
    for actor_id, actor in state.actors.items():
        if actor.name and actor.name.lower() in PROHIBITED_ACTOR_NAMES:
            errors.append(
                f"Actor '{actor_id}' has prohibited name '{actor.name}' "
                f"(reserved words: {', '.join(sorted(PROHIBITED_ACTOR_NAMES))})"
            )
```

**Rationale**:
- "player" and "npc" are ambiguous terms in multiplayer and general contexts
- "self", "me", "myself" are vocabulary synonyms for self-reference
- Actor IDs can still be "player" (the ID, not the display name)
- Case-insensitive to prevent "Player", "SELF", etc.

**Migration**: Rename player.name from "player" to "Landry" in example game states.

## Implementation Results

Implementation completed successfully on 2025-11-28.

### Files Modified

| File | Changes |
|------|---------|
| `behaviors/core/actors.py` | **New file** - vocabulary with "self" noun and synonyms "me", "myself" |
| `utilities/utils.py` | Added `find_actor_by_name()` and `format_inventory()` functions |
| `behaviors/core/perception.py` | Extended `handle_examine` to search actors; updated imports; refactored `handle_inventory` to use `format_inventory()` |
| `src/validators.py` | Added `PROHIBITED_ACTOR_NAMES` constant and `_validate_actor_names()` function |
| `src/state_manager.py` | Updated default player name to "Adventurer" (not prohibited "player") in `_parse_actor()` and default player creation |
| `tests/test_examine_actors.py` | **New file** - 32 tests for actor examination feature |
| `examples/fancy_game_state.json` | Changed player.name from "player" to "Landry" |
| `examples/simple_game_state.json` | Changed player.name from "player" to "Landry" |
| Multiple test files & fixtures | Updated player.name from "player" to "Adventurer" to comply with validation |

### Test Results

- All 1085 tests pass (1 skipped)
- 32 new tests added in `test_examine_actors.py`:
  - TestFindActorByName: 9 tests
  - TestFormatInventory: 3 tests
  - TestHandleExamineActors: 12 tests
  - TestValidateActorNames: 7 tests
  - TestActorsVocabulary: 2 tests

### Implementation Notes

1. **Self-reference handling**: The `find_actor_by_name()` function explicitly checks for the self-reference words {"self", "me", "myself"} rather than relying on vocabulary lookup, because plain strings passed directly to the function don't carry synonym information.

2. **Default player name**: Changed from "player" to "Adventurer" in two places:
   - `_parse_actor()` - when no name is provided in actor data
   - Default player creation in `load_game_state()` - when no player data exists

3. **Validation enforcement**: Validation happens during `load_game_state()`, so tests that create game states with invalid actor names now fail during loading rather than during explicit validation calls. Test patterns updated accordingly.

4. **Test fixture updates**: Multiple JSON fixtures and test helper functions updated to use "Adventurer" instead of "player" for the player.name field.
