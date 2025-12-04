# Spatial Game Implementation Notes

## Overview
Implementation plan for examples/spatial_game, demonstrating spatial positioning mechanics.
Based on examples/extended_game with additional spatial library commands and modified crystal ball behavior.

## Design Documents Reviewed
- [docs/spatial_game_design.md](spatial_game_design.md) - Complete design specification
- [user_docs/game_authors.md](../user_docs/game_authors.md) - Tier calculation explanation (lines 722-773)
- [user_docs/engine_documentation.md](../user_docs/engine_documentation.md) - Developer tier details (lines 372-404)

## Key Design Insights

### Tier System (Directory Depth-Based)
- **Tier = Depth + 1** (depth = subdirectory levels below `behaviors/`)
- Symlinks use their position in game structure, not target's internal structure
- No engine API changes needed - existing `discover_modules()` handles everything

**Example Directory Structure:**
```
behaviors/
  magic_star.py              # Tier 1 (depth 0)
  crystal_ball.py            # Tier 1 (depth 0)
  lib/
    spatial/
      stand_sit.py           # Tier 2 (depth 1)
      look_out.py            # Tier 2 (depth 1)
    core/                    # Tier 3 (depth 2)
      -> ../../../../behaviors/core/
```

### Crystal Ball Design Change
**Original (extended_game):** Auto-positions player when peering into ball
**New (spatial_game):** Ball requires proximity but does NOT auto-position
- Must use `examine ball` or `examine stand` first to position near
- `peer into ball` checks `focused_on`, fails with helpful message if not near
- Demonstrates explicit positioning requirement

### Garden Puzzle Chain
Three-step sequence using posture and focused_on:
1. `stand on bench` → Sets posture "on_surface", focused_on bench
2. `climb tree` → Checks posture/focus, sets posture "climbing", focused_on tree
3. `take star` → Checks posture/focus, allows taking star from branches

## Existing Code Analysis

### Current Crystal Ball Location
From [examples/extended_game/game_state.json](../examples/extended_game/game_state.json):
- item_silver_stand: loc_library, container with is_surface: true
- item_crystal_ball: location is "item_silver_stand" (on stand)
- item_desk: also in loc_library, is_surface: true

### Positioning Helper Functions
From [utilities/positioning.py](../utilities/positioning.py):
- `try_implicit_positioning()` - Handles auto-positioning based on interaction_distance
- `find_and_position_item()` - Combined lookup + positioning
- `find_and_position_part()` - Part lookup + positioning
- `build_message_with_positioning()` - Formats messages with movement prefix

### Vocabulary System
From [src/vocabulary.json](../src/vocabulary.json):
- **Current prepositions:** with, to, in, on, under, behind, from, into, onto, through
- **Need to add:** "of" and "out" (or confirm "out" already exists)

## Implementation Tasks

### Phase 1: Setup and Structure
1. Copy examples/extended_game to examples/spatial_game
2. Create directory structure:
   - `behaviors/lib/spatial/` (new Tier 2 directory)
   - `behaviors/lib/core/` (symlink to ../../../../behaviors/core/)
3. Move existing behaviors to root:
   - Keep crystal_ball.py, magic_mat.py, magic_wand.py, spellbook.py at depth 0
   - Remove old core symlink at behaviors/core/

### Phase 2: Vocabulary Updates
1. Add "of" and "out" to src/vocabulary.json prepositions
   - Verify parser handles compound prepositions ("out of")

### Phase 3: New Tier 2 Library Commands

#### lib/spatial/stand_sit.py
**Vocabulary:**
- Verb: "stand" (synonyms: "get on"), indirect_object_required: True
- Verb: "sit", indirect_object_required: True

**Handler: handle_stand_on(accessor, action)**
- Get actor and indirect_object (surface name)
- Find surface using `find_accessible_item()`
- Check `container.is_surface` property
- Set actor.properties["focused_on"] = surface.id
- Set actor.properties["posture"] = "on_surface"
- Return success message

**Handler: handle_sit_on(accessor, action)**
- Same logic as stand_on (same posture result)

**Testing:**
- Test with bench (has is_surface)
- Test with non-surface (should fail)
- Test posture and focus set correctly

#### lib/spatial/look_out.py
**Vocabulary:**
- Verb: "look" (for "look out of"), indirect_object_required: True

**Handler: handle_look_out_of(accessor, action)**
- **Positive testing:** Check preposition is "out of" or "out", return failure if not
- Get indirect_object (window/opening name)
- Try finding as Part first using `find_and_position_part()`
- If not found, try as Item using `find_and_position_item()`
- Note: Uses interaction_distance: "any" (no proximity needed)
- Display entity's description property (the view)
- Return success with description

**Testing:**
- Test with window part
- Test with wrong preposition (should fail, let other handlers try)
- Test description displayed correctly

### Phase 4: Game-Specific Behaviors (Tier 1)

#### behaviors/magic_star.py (NEW)
**Entity behaviors:**

**on_climb(entity, accessor, context)**
- Entity: tree
- Check actor posture == "on_surface"
- Check actor focused_on == "item_garden_bench"
- Fail with message if not standing on bench
- Success: Set actor posture = "climbing", focused_on = "item_tree"

**on_take(entity, accessor, context)**
- Entity: star
- Check actor posture == "climbing"
- Check actor focused_on == "item_tree"
- Fail with message if not climbing tree
- Success: Allow taking star

**Testing:**
- Test climb tree without standing on bench (should fail)
- Test climb tree from bench (should succeed)
- Test take star without climbing (should fail)
- Test take star while climbing (should succeed)

#### behaviors/crystal_ball.py (MODIFIED)
**Modify handle_peer:**
- Add interaction distance check BEFORE invoking behavior
- If `interaction_distance == "near"`:
  - Get player's focused_on property
  - Check if focused_on == item.id OR focused_on == item.location (container)
  - If not focused: Return failure "You need to be closer to peer into the ball. Try examining it first."
- Otherwise continue with existing logic (invoke on_peer behavior)

**Keep on_peer unchanged:**
- Existing sanctum key revelation logic works fine

**Testing:**
- Test peer without examining first (should fail)
- Test examine stand then peer (should succeed)
- Test examine ball then peer (should succeed)
- Test key revelation still works

### Phase 5: Entity Updates (game_state.json)

#### item_garden_bench (MODIFY)
```json
{
  "id": "item_garden_bench",
  "name": "bench",
  "description": "A weathered stone bench, covered in moss. It looks sturdy enough to stand on.",
  "location": "loc_garden",
  "properties": {
    "type": "furniture",
    "portable": false,
    "container": {
      "is_surface": true
    }
  }
}
```

#### item_tree (NEW)
```json
{
  "id": "item_tree",
  "name": "tree",
  "description": "An old oak tree with thick branches. You might be able to climb it if you had something to stand on.",
  "location": "loc_garden",
  "properties": {
    "type": "object",
    "portable": false,
    "climbable": true,
    "interaction_distance": "near"
  },
  "behaviors": ["behaviors.magic_star"]
}
```

#### item_magic_star (NEW)
```json
{
  "id": "item_magic_star",
  "name": "star",
  "description": "A crystalline star that glows with inner light, nestled in the tree branches.",
  "location": "item_tree",
  "properties": {
    "type": "object",
    "portable": true,
    "magical": true
  },
  "behaviors": ["behaviors.magic_star"]
}
```

#### part_library_window (NEW Part)
```json
{
  "id": "part_library_window",
  "name": "window",
  "part_of": "loc_library",
  "properties": {
    "description": "Through the large arched window, you see rolling hills and distant forests stretching to the horizon. Birds circle lazily in the clear sky.",
    "interaction_distance": "any"
  }
}
```

#### item_crystal_ball (MODIFY)
Add interaction_distance property:
```json
{
  "id": "item_crystal_ball",
  "name": "ball",
  "description": "A crystal ball. Mist swirls within its depths.",
  "location": "item_silver_stand",
  "properties": {
    "type": "object",
    "portable": true,
    "magical": true,
    "interaction_distance": "near"
  },
  "behaviors": ["behaviors.crystal_ball"]
}
```

#### Update loc_garden items array
Add "item_tree" to items list (star is in tree, not location)

### Phase 6: Testing Scenarios

#### Scenario 1: Garden Puzzle
```
> examine bench
(Should describe bench, position near it)
> stand on bench
(Should set posture on_surface, focus bench)
> climb tree
(Should check posture/focus, set climbing, focus tree)
> take star
(Should check posture/focus, allow taking)
```

#### Scenario 2: Crystal Ball (No Auto-Position)
```
> peer into ball
(Should fail: "You need to be closer...")
> examine stand
(Should position at stand, which contains ball)
> peer into ball
(Should succeed: checks focused_on includes ball's container)
```

#### Scenario 3: Window View
```
> look out of window
(Should display window description/view, no movement)
```

#### Scenario 4: Alternative Crystal Ball Approach
```
> examine ball
(Should position at ball)
> peer into ball
(Should succeed: focused_on ball directly)
```

## Code Patterns from Existing System

### Handler Pattern (from crystal_ball.py)
```python
def handle_verb(accessor, action: Dict) -> HandlerResult:
    actor_id = action.get("actor_id", "player")
    obj_name = action.get("object")
    adjective = action.get("adjective")

    if not obj_name:
        return HandlerResult(success=False, message="Verb what?")

    # Find entity
    item = find_item_in_inventory(accessor, obj_name, actor_id)
    if not item:
        item = find_accessible_item(accessor, obj_name, actor_id, adjective)

    if not item:
        return HandlerResult(success=False, message=f"You don't see any {obj_name} here.")

    # Check preconditions...

    # Invoke behavior if present
    result = accessor.update(item, {}, verb="verb", actor_id=actor_id)

    return HandlerResult(success=result.success, message=result.message)
```

### Entity Behavior Pattern
```python
def on_event(entity: Any, accessor: Any, context: Dict) -> EventResult:
    actor_id = context.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)

    # Check conditions
    if not condition:
        return EventResult(allow=False, message="Failure message")

    # Update state if needed
    entity.states["some_state"] = value

    return EventResult(allow=True, message="Success message")
```

### Positive Testing Pattern (from design)
```python
def handle_look_out_of(accessor, action: Dict[str, Any]) -> HandlerResult:
    preposition = action.get("preposition")

    # Positive testing: only handle if preposition matches
    if not preposition or preposition not in ["out of", "out"]:
        return HandlerResult(success=False, message="")  # Let other handlers try

    # Continue with actual logic...
```

## Implementation Order

1. **Setup** (Phase 1) - Copy and create structure
2. **Vocabulary** (Phase 2) - Add "of" and "out"
3. **Magic Star** (Phase 4.1) - Game-specific tree/star logic
4. **Stand/Sit** (Phase 3.1) - Library surface positioning
5. **Look Out** (Phase 3.2) - Library window viewing
6. **Crystal Ball** (Phase 4.2) - Modify for no auto-position
7. **Entities** (Phase 5) - Update game_state.json
8. **Testing** (Phase 6) - Test all scenarios

## Key Testing Checkpoints

- [ ] Tree climb fails without bench positioning
- [ ] Tree climb succeeds from bench
- [ ] Star take fails without climbing
- [ ] Star take succeeds while climbing
- [ ] Crystal ball peer fails without positioning
- [ ] Crystal ball peer succeeds after examine stand
- [ ] Crystal ball peer succeeds after examine ball
- [ ] Look out of window works from anywhere
- [ ] Stand on bench sets correct posture and focus
- [ ] Tier system working (game overrides library overrides core)

## Notes for Development

- Follow TDD: Write tests for each behavior before implementing
- Use existing patterns from extended_game behaviors
- Test each phase independently before moving to next
- Verify tier precedence by checking handler order
- Use --debug flag to verify module loading and tiers
- Check focused_on and posture properties at each step

## Success Criteria

1. All tier assignments correct (1, 2, 3)
2. Garden puzzle fully functional (bench → tree → star)
3. Crystal ball requires explicit positioning
4. Look out of window works without positioning
5. All game mechanics work with clean separation of concerns
6. No core behavior modifications needed
7. Library behaviors are truly reusable
