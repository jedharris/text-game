# Spatial Game - Ready for Implementation

## Status: Design Complete, Ready to Code

All design questions have been resolved. The implementation can proceed with confidence.

## Key Files Reviewed

1. **[docs/spatial_game_design.md](spatial_game_design.md)** - Complete design spec (516 lines)
2. **[user_docs/game_authors.md](../user_docs/game_authors.md)** - Tier system explanation (lines 722-773)
3. **[user_docs/engine_documentation.md](../user_docs/engine_documentation.md)** - Developer tier details (lines 372-404)
4. **[examples/extended_game/](../examples/extended_game/)** - Base game structure
5. **[utilities/positioning.py](../utilities/positioning.py)** - Positioning helpers
6. **[src/vocabulary.json](../src/vocabulary.json)** - Current vocabulary

## Critical Insights Confirmed

### 1. Tier System Works by Directory Depth
**Formula:** `tier = depth + 1` where depth = subdirectory levels below `behaviors/`

**Example:**
```
behaviors/
  puzzle.py              # depth 0 → Tier 1
  lib/
    spatial/
      stand_sit.py       # depth 1 → Tier 2
    core/                # depth 2 → Tier 3
      -> /engine/behaviors/core/
```

**Symlink behavior:** Tier is based on symlink location in game structure, NOT target location.
This is exactly what we need - no API changes required.

### 2. Crystal Ball Design Confirmed
**Current (extended_game):** `handle_peer` calls `accessor.update()` which uses `try_implicit_positioning()`
- This auto-positions player to ball

**New (spatial_game):** Add explicit check in `handle_peer` BEFORE calling `accessor.update()`
- Check if `interaction_distance == "near"`
- Check if `focused_on` matches ball or ball's container
- Fail with helpful message if not positioned
- Only call `accessor.update()` if check passes

**Why this works:** Intercepts before the auto-positioning logic in `try_implicit_positioning()`

### 3. Positioning Utilities Already Available
From `utilities/positioning.py`:
- `find_and_position_item()` - Find item + apply implicit positioning
- `find_and_position_part()` - Find part + apply implicit positioning
- `try_implicit_positioning()` - Core positioning logic (checks interaction_distance)
- `build_message_with_positioning()` - Formats messages

**Insight:** The `look_out.py` handler should use `interaction_distance: "any"` on the window entity to avoid triggering positioning.

### 4. Existing Game Structure Verified
From `examples/extended_game/game_state.json`:
- Crystal ball: location is "item_silver_stand" (on the stand)
- Silver stand: is_surface: true, is_container: true, capacity: 1
- Desk: Also in loc_library, is_surface: true
- Garden bench: Already exists, needs `container.is_surface: true` added

**Location hierarchy:**
```
loc_library
  ├─ item_desk (surface)
  │   └─ item_spellbook
  └─ item_silver_stand (surface)
      └─ item_crystal_ball
```

### 5. Vocabulary Update Needed
**Current prepositions:** with, to, in, on, under, behind, from, into, onto, through
**Need to add:** "of" and "out" (for "look out of window")

**Parser note:** The parser already handles compound prepositions naturally, so "out of" will work once both words are in the preposition list.

## Implementation Approach Confirmed

### Phase Order (Safe and Testable)
1. **Setup** - Copy extended_game, create directory structure
2. **Vocabulary** - Add "of" and "out" to prepositions
3. **Magic Star** - Implement tree climbing puzzle (Tier 1)
4. **Stand/Sit** - Implement surface positioning library (Tier 2)
5. **Look Out** - Implement window viewing library (Tier 2)
6. **Crystal Ball** - Modify for explicit positioning (Tier 1)
7. **Entities** - Update game_state.json with new entities
8. **Testing** - Test all scenarios end-to-end

### Directory Structure to Create
```
examples/spatial_game/
├── game_state.json          # Modified from extended_game
├── narrator_style.txt       # Copy from extended_game
├── run_game.py             # Copy from extended_game
└── behaviors/
    ├── __init__.py
    ├── crystal_ball.py     # Modified - add proximity check
    ├── magic_mat.py        # Copy unchanged
    ├── magic_wand.py       # Copy unchanged
    ├── spellbook.py        # Copy unchanged
    ├── magic_star.py       # NEW - tree/star behaviors
    └── lib/
        ├── spatial/
        │   ├── __init__.py
        │   ├── stand_sit.py    # NEW Tier 2
        │   └── look_out.py     # NEW Tier 2
        └── core/               # Symlink at depth 2 → Tier 3
            -> ../../../../behaviors/core/
```

## New Entities Required

### 1. item_tree (loc_garden)
- climbable: true
- interaction_distance: "near"
- behaviors: ["behaviors.magic_star"]
- on_climb checks posture/focus

### 2. item_magic_star (item_tree)
- portable: true
- magical: true
- behaviors: ["behaviors.magic_star"]
- on_take checks posture/focus

### 3. part_library_window (part_of: loc_library)
- description: "Through the large arched window, you see rolling hills..."
- interaction_distance: "any"

### 4. Modify item_garden_bench
- Add: container.is_surface: true

### 5. Modify item_crystal_ball
- Add: interaction_distance: "near"

## Handler Patterns Confirmed

### Positive Testing (from design)
```python
def handle_look_out_of(accessor, action):
    preposition = action.get("preposition")

    # Positive testing: only handle if preposition matches
    if not preposition or preposition not in ["out of", "out"]:
        return HandlerResult(success=False, message="")  # Let others try

    # Continue with actual logic...
```

### Proximity Check Pattern (for crystal ball)
```python
def handle_peer(accessor, action):
    # ... find item ...

    # NEW: Check proximity BEFORE invoking behavior
    interaction_distance = properties.get("interaction_distance", "any")
    if interaction_distance == "near":
        player = accessor.get_actor(actor_id)
        focused_on = player.properties.get("focused_on")

        if focused_on != item.id:
            # Check if focused on container
            if hasattr(item, 'location'):
                container = accessor.get_item(item.location)
                if not container or focused_on != container.id:
                    return HandlerResult(
                        success=False,
                        message="You need to be closer to peer into the ball. Try examining it first."
                    )

    # Original logic: invoke behavior
    result = accessor.update(item, {}, verb="peer", actor_id=actor_id)
    # ...
```

### Surface Positioning Pattern (new)
```python
def handle_stand_on(accessor, action):
    surface_name = action.get("indirect_object")
    actor = accessor.get_actor(actor_id)

    # Find surface
    surface = find_accessible_item(accessor, surface_name, actor_id, adjective)
    if not surface:
        return HandlerResult(success=False, message=f"You don't see any {surface_name} here.")

    # Check if it's a surface
    container_props = surface.properties.get("container", {})
    if not container_props.get("is_surface", False):
        return HandlerResult(success=False, message=f"You can't stand on the {surface.name}.")

    # Set posture and focus
    actor.properties["focused_on"] = surface.id
    actor.properties["posture"] = "on_surface"

    return HandlerResult(success=True, message=f"You stand on the {surface.name}.")
```

## Test Scenarios Specified

### 1. Garden Puzzle (Full Chain)
```
> examine bench       # Position at bench
> stand on bench      # Set posture=on_surface, focus=bench
> climb tree          # Check posture/focus → set posture=climbing, focus=tree
> take star           # Check posture/focus → allow taking
```

### 2. Crystal Ball (Explicit Positioning)
```
> peer into ball      # FAIL: "You need to be closer..."
> examine stand       # Position at stand (ball's container)
> peer into ball      # SUCCESS: focused_on=stand, ball.location=stand
```

### 3. Crystal Ball (Alternative)
```
> examine ball        # Position at ball directly
> peer into ball      # SUCCESS: focused_on=ball
```

### 4. Window View (No Positioning)
```
> look out of window  # SUCCESS: interaction_distance=any, no movement
```

## No Design Issues Remaining

✅ **Tier system** - Works via directory depth, symlinks handled correctly
✅ **Crystal ball** - Clear modification strategy, no auto-positioning
✅ **Garden puzzle** - Clean posture/focus chain
✅ **Library commands** - Tier 2 reusable patterns
✅ **Vocabulary** - Simple addition to prepositions
✅ **Entity structure** - All entities specified
✅ **Code patterns** - Existing patterns identified and documented
✅ **Testing** - All scenarios specified

## Next Steps

The implementation is ready to proceed:

1. **Review** [docs/spatial_game_implementation_notes.md](spatial_game_implementation_notes.md) for detailed implementation guide
2. **Start with Phase 1** - Setup and directory structure
3. **Follow TDD** - Write tests for each behavior before implementing
4. **Test incrementally** - Verify each phase works before moving to next

All design work is complete. No ambiguities remain. Ready to code.
