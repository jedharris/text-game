# Spatial Game Example - Design Document

## Overview

This document describes the design for a new example game (`examples/spatial_game`) that demonstrates the spatial positioning system. The game will be based on `examples/extended_game` but will add spatial mechanics to two locations:

1. **Garden**: Bench → Tree → Star (chained positioning requirements)
2. **Wizard's Library**: Window (examine from anywhere) and Crystal Ball (requires proximity)

## Architecture

### Tier Structure

The game will use a three-tier behavior system:

- **Tier 1**: Game-specific behaviors (highest precedence)
- **Tier 2**: Reusable spatial library behaviors
- **Tier 3**: Core engine behaviors (lowest precedence)

This structure allows:
- Game behaviors to override library behaviors when needed
- Library behaviors to provide reusable spatial patterns
- Core behaviors to provide fallback functionality

### Directory Structure

```
examples/spatial_game/
├── game_state.json           # Game entities and properties
├── run_game.py               # Game launcher (modified to load spatial library)
├── behaviors/                # Game-specific behaviors (Tier 1)
│   ├── __init__.py
│   ├── core -> ../../behaviors/core/  # Symlink to core behaviors
│   ├── magic_wand.py        # From extended_game
│   ├── magic_mat.py         # From extended_game
│   ├── spellbook.py         # From extended_game
│   ├── crystal_ball.py      # Modified for proximity requirement
│   └── magic_star.py        # NEW: Star that requires climbing tree
└── behavior_libraries/
    └── spatial/              # Reusable spatial library (Tier 2)
        ├── __init__.py
        └── conditional_take.py  # NEW: Take handler with positioning requirements
```

## Design Problems and Solutions

### Problem 1: Tier Loading for Libraries

**Issue**: The current `run_game.py` uses `discover_modules()` which automatically assigns tiers based on directory depth. We need to load behaviors from two separate locations with specific tiers:
- `behaviors/` → Tier 1 (game-specific)
- `behavior_libraries/spatial/` → Tier 2 (library)
- `behaviors/core/` → Tier 3 (core, via symlink)

**Current behavior_manager tier assignment** (from line 60):
```python
depth = len(relative_path.parts) - 1  # -1 to exclude filename
return depth + 1  # Tier = depth + 1
```

This means:
- `behaviors/magic_star.py` → depth 0 → Tier 1 ✓
- `behaviors/core/spatial.py` → depth 1 → Tier 2 ✗ (should be Tier 3)
- `behavior_libraries/spatial/conditional_take.py` → depth 1 → Tier 2 ✓

**Solution**: The symlink approach already gives us what we need! But we need to adjust our understanding:
- Game behaviors at `behaviors/*.py` → Tier 1
- Core behaviors at `behaviors/core/*.py` → Tier 2 (via symlink)
- Library behaviors need a different approach

**Actually, this reveals a design issue**: We can't easily load two different behavior directories with controlled tiers using the current `discover_modules()` approach.

**Proposed Solution**:
1. Keep game behaviors in `behaviors/` → auto Tier 1
2. Put spatial library in `behaviors/spatial_lib/` → auto Tier 2
3. Keep core symlink at `behaviors/core/` → auto Tier 2

This means spatial library and core will both be Tier 2, which is fine since:
- They handle different verbs (no conflicts)
- Library can have game-specific positioning logic
- Core provides general spatial commands

**Wait, this is still problematic** because we want core to be Tier 3 (lowest precedence), not Tier 2.

**Better Solution**: Modify `run_game.py` to explicitly control tier assignment:
1. Discover modules from `behaviors/` (excluding `core/`)
2. Load them with default tier calculation (game behaviors = Tier 1, spatial_lib = Tier 2)
3. Discover modules from `behaviors/core/`
4. Override their tier to 3 before loading

However, looking at `load_modules()`, it calculates tier internally. We'd need to add a parameter to override tier calculation.

**Actually, let's check the current approach more carefully**:

Looking at the extended_game structure, it uses a symlink `behaviors/core -> ../../behaviors/core`. This means:
- `behaviors/magic_wand.py` → `behaviors/magic_wand` → depth 0 → Tier 1
- `behaviors/core/spatial.py` → `behaviors/core/spatial` → depth 1 → Tier 2

**The real solution**: Don't use the symlink approach. Instead:

```
examples/spatial_game/
├── behaviors/                    # Tier 1 (game-specific)
│   ├── magic_star.py
│   └── crystal_ball.py (modified)
├── behavior_libraries/
│   └── spatial/                  # Tier 2 (reusable library)
│       └── conditional_take.py
└── run_game.py (loads both directories with explicit tier control)
```

Then modify `run_game.py` to:
1. Load `behavior_libraries/spatial/` and manually adjust tiers to 2
2. Load `behaviors/` with default tier calculation (Tier 1)
3. Load core behaviors from engine with tier 3

But this requires API changes to `BehaviorManager`.

**CLEANEST SOLUTION**: Use the directory depth approach, but structure directories to get the right tiers:

```
examples/spatial_game/
├── behaviors/
│   ├── game/                      # Tier 1 (depth 0 from behaviors/)
│   │   ├── magic_star.py
│   │   └── crystal_ball.py
│   ├── lib/                       # Tier 2 (depth 1 from behaviors/)
│   │   └── spatial/
│   │       └── conditional_take.py
│   └── core/                      # Tier 3 (depth 1 from behaviors/)
│       -> ../../../behaviors/core/  # Symlink
```

Wait, that still gives lib and core the same tier (2).

**ACTUAL CLEANEST SOLUTION**: The directory depth calculation is from the base directory passed to `discover_modules()`. So:

```
behaviors/magic_star.py         → relative to behaviors/ → parts=['magic_star.py'] → depth 0 → Tier 1
behaviors/spatial/conditional.py → relative to behaviors/ → parts=['spatial', 'conditional.py'] → depth 1 → Tier 2
behaviors/core/spatial.py       → relative to behaviors/ → parts=['core', 'spatial.py'] → depth 1 → Tier 2
```

**This means we can't have different tiers for library vs core using a single discover_modules() call.**

**FINAL SOLUTION**: Accept that we need to modify the BehaviorManager API slightly. Add an optional `tier_override` parameter to `load_modules()`:

```python
def load_modules(self, modules: List[Tuple[str, str]], tier_override: Optional[int] = None):
    """Load behavior modules with optional tier override."""
```

Then in `run_game.py`:
```python
# Load core behaviors at Tier 3
core_modules = behavior_manager.discover_modules('../../behaviors/core')
behavior_manager.load_modules(core_modules, tier_override=3)

# Load spatial library at Tier 2
lib_modules = behavior_manager.discover_modules('./behavior_libraries/spatial')
behavior_manager.load_modules(lib_modules, tier_override=2)

# Load game behaviors at Tier 1 (default tier calculation)
game_modules = behavior_manager.discover_modules('./behaviors')
behavior_manager.load_modules(game_modules)
```

**WAIT - Simpler approach**: Just use the existing depth-based approach correctly:

```
examples/spatial_game/
├── behaviors/
│   ├── magic_star.py              # Tier 1
│   ├── crystal_ball.py            # Tier 1
│   ├── spatial/                   # Tier 2
│   │   └── conditional_take.py
│   └── core/                      # Tier 2
│       -> ../../../behaviors/core/
```

But have the spatial library check if an entity allows taking *before* checking positioning. This way:
- Tier 1 game behaviors handle game-specific logic first (can override anything)
- Tier 2 spatial library handles conditional take (only for entities that need positioning checks)
- Tier 2 core handles standard take (for all other entities)

The order within Tier 2 doesn't matter because of positive testing: conditional_take checks if entity has positioning requirements and fails if not, allowing standard take to handle it.

**Actually, I just realized the real issue**: We want:
1. Tier 1: Game-specific behaviors
2. Tier 2: Spatial library (reusable)
3. Tier 3: Core behaviors

But core behaviors are part of the engine, not the game. The extended_game uses a symlink to include them.

**Re-reading the user's request**: "Add a library to behavior_libraries for any reusable spatial behavior that you create, and have the game load that library as tier 2, with core as tier 3."

This tells me the user wants:
- `behavior_libraries/` to be separate from `behaviors/`
- Library loaded as Tier 2
- Core loaded as Tier 3

This DOES require API changes or a more sophisticated loading approach.

### Problem 2: Chained Positioning Requirements (Bench → Tree → Star)

**Requirement**: Player must stand on bench to climb tree, must climb tree to take star.

**Design Options**:

**Option A**: Use posture requirements
- Star requires `posture: "climbing"` AND `focused_on: "item_tree"`
- Tree requires `focused_on: "item_bench"`

**Issue with Option A**: The `climb` command in spatial.py doesn't check focused_on. It only checks if the entity is climbable and accessible.

**Option B**: Add game-specific `on_climb` behavior to tree
- Tree's `on_climb` behavior checks if player is focused on bench
- Returns failure if not

**Option C**: Add positioning requirements to entity properties
- Tree has `requires_focused_on: "item_bench"`
- Star has conditional take that checks posture and focused_on

**Recommendation**: Use Option C with Option B for clear error messages.

**Implementation**:
1. Bench has `climbable: false` but `allows_standing: true` (or just use `approach bench`)
2. Tree has `climbable: true` and behavior checks focused_on bench
3. Star has `portable: true` but game behavior checks posture=climbing and focused_on=tree

### Problem 3: Proximity Requirement for Crystal Ball

**Requirement**: "gaze into ball" should require player to be near the ball.

**Current State**: crystal_ball.py has `handle_peer` which handles the "peer/gaze" verb and calls the entity's `on_peer` behavior.

**Design Options**:

**Option A**: Modify `handle_peer` to check `interaction_distance: "near"` and use implicit positioning
- Add to crystal_ball.py: Check ball's `interaction_distance` property
- If "near", call `try_implicit_positioning()` before invoking behavior

**Option B**: Move `handle_peer` to Tier 2 library and make it positioning-aware
- Library version checks interaction_distance
- Game's crystal_ball.py only provides the `on_peer` behavior

**Option C**: Use core `examine` command pattern - add interaction_distance to ball
- Set ball's `interaction_distance: "near"`
- Don't modify handle_peer, just ensure player is near ball before they can peer
- This requires handle_peer to respect focused_on or positioning

**Recommendation**: Option A - modify handle_peer to be positioning-aware.

**Implementation**:
1. Add `interaction_distance: "near"` to crystal ball entity
2. Modify `handle_peer` in crystal_ball.py to call `try_implicit_positioning()` if interaction_distance is "near"
3. This follows the same pattern as examine/take/open/close

### Problem 4: Window Interaction

**Requirement**: Player can "look out window" from anywhere in library.

**Design**:
1. Add a Part entity for window in library
2. Window has no special properties (default interaction_distance: "any")
3. No custom behavior needed - standard examine will work
4. Window description includes view: "You gaze out the window at the countryside below..."

## Behavior Specifications

### Tier 1: Game Behaviors (behaviors/)

#### magic_star.py (NEW)
```python
vocabulary = {
    "verbs": []  # No new verbs
}

def on_take(entity, accessor, context):
    """
    Star can only be taken while climbing the tree.

    Checks:
    - Actor has posture="climbing"
    - Actor's focused_on="item_tree"

    Returns failure with helpful message if requirements not met.
    """
```

#### crystal_ball.py (MODIFIED)
Existing `handle_peer` modified to:
1. Check if ball has `interaction_distance: "near"`
2. If yes, use `try_implicit_positioning()` to move player
3. Then invoke `on_peer` behavior as before

No new verbs, no new behaviors - just positioning awareness.

### Tier 2: Spatial Library (behavior_libraries/spatial/)

#### conditional_take.py (NEW)
```python
vocabulary = {
    "verbs": []  # Uses existing "take" verb
}

def handle_take(accessor, action):
    """
    Enhanced take handler that checks positioning requirements.

    Uses positive testing:
    1. Find the target item
    2. Check if it has positioning requirements (custom property)
    3. If yes, validate requirements
    4. If no requirements or validation passes, return failure (let core handle it)
    5. If validation fails, return failure with helpful message

    This is Tier 2, so it's tried after game behaviors (Tier 1)
    but before core behaviors (Tier 3).
    """
```

**WAIT - This doesn't make sense**. If we validate positioning and it passes, we should succeed, not return failure.

Let me reconsider...

**Actually, the take command should work like this**:
1. Tier 1 game behavior (`on_take` on star) checks positioning
2. If positioning wrong, returns failure with message
3. If positioning right, returns success (allow=True) - lets standard take proceed
4. Core take (Tier 3) actually moves the item

So we don't need a library behavior for conditional take. The game behavior handles it via entity behaviors.

**Revised**: No Tier 2 library behaviors needed for this example.

The spatial library concept is good for future reusable patterns, but for this example:
- Star uses entity `on_take` behavior (checks posture/focused_on)
- Tree uses entity `on_climb` behavior (checks focused_on bench)
- Crystal ball modifies its `handle_peer` to use positioning

All are game-specific, belong in Tier 1.

### Tier 3: Core Behaviors

Standard core behaviors handle:
- Basic take (after entity behavior allows)
- Climb (spatial.py)
- Examine (perception.py)
- Approach (spatial.py)

## Revised Architecture (Simpler)

Given the analysis above, here's the cleaner design:

### Directory Structure
```
examples/spatial_game/
├── game_state.json
├── run_game.py (modified to load core behaviors explicitly)
├── behaviors/
│   ├── __init__.py
│   ├── magic_wand.py      (unchanged from extended_game)
│   ├── magic_mat.py       (unchanged from extended_game)
│   ├── spellbook.py       (unchanged from extended_game)
│   ├── crystal_ball.py    (modified for positioning)
│   └── magic_star.py      (NEW: positioning checks)
```

No behavior_libraries needed for this example. Core behaviors loaded from engine.

### Loading Approach

Modify `run_game.py`:
```python
# Load core behaviors from engine (Tier 3)
core_path = project_root / 'behaviors' / 'core'
core_modules = behavior_manager.discover_modules(str(core_path))
# Need to override tier to 3 - requires API change

# Load game behaviors (Tier 1 automatically)
game_modules = behavior_manager.discover_modules(str(CUSTOM_BEHAVIORS_DIR))
behavior_manager.load_modules(game_modules)
```

**This reveals we DO need the tier_override API change.**

## API Changes Required

### behavior_manager.py

Add optional `base_tier` parameter to `load_modules()`:

```python
def load_modules(self, modules: List[Tuple[str, str]], base_tier: Optional[int] = None):
    """
    Load behavior modules from discovered module list.

    Args:
        modules: List of (module_path, source_type) tuples from discover_modules()
        base_tier: Optional base tier for all modules. If None, tier calculated from depth.
                   If provided, tier = base_tier + depth (depth 0 gets base_tier)
    """
```

This allows:
```python
# Core behaviors: base_tier=3 means behaviors/core/*.py get tier 3
behavior_manager.load_modules(core_modules, base_tier=3)

# Game behaviors: base_tier=1 means behaviors/*.py get tier 1, behaviors/lib/*.py get tier 2
behavior_manager.load_modules(game_modules, base_tier=1)
```

## Entity Specifications

### Garden Entities

#### item_garden_bench (MODIFIED)
```json
{
  "id": "item_garden_bench",
  "name": "bench",
  "description": "A weathered stone bench, covered in moss. It looks sturdy enough to stand on.",
  "location": "loc_garden",
  "properties": {
    "type": "furniture",
    "portable": false,
    "provides_cover": false
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

**NOTE**: Tree needs behavior that checks focused_on bench before allowing climb.

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

### Library Entities

#### part_library_window (NEW Part)
```json
{
  "id": "part_library_window",
  "name": "window",
  "part_of": "loc_library",
  "properties": {
    "description": "A large arched window overlooking the countryside. Rolling hills and distant forests stretch to the horizon.",
    "interaction_distance": "any"
  }
}
```

#### item_crystal_ball (MODIFIED)
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

## Behavior Implementation Details

### behaviors/magic_star.py

```python
def on_climb(entity, accessor, context):
    """
    Tree climb behavior - checks if player is on bench.

    entity: The tree
    context: {actor_id, verb}
    """
    actor_id = context.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)

    focused = actor.properties.get("focused_on")

    if focused != "item_garden_bench":
        return EventResult(
            allow=False,
            message="The tree is too tall to climb from the ground. You need something to stand on."
        )

    return EventResult(allow=True, message="")

def on_take(entity, accessor, context):
    """
    Star take behavior - checks if player is climbing tree.

    entity: The star
    context: {actor_id, verb}
    """
    actor_id = context.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)

    posture = actor.properties.get("posture")
    focused = actor.properties.get("focused_on")

    if posture != "climbing" or focused != "item_tree":
        return EventResult(
            allow=False,
            message="The star is too high up in the tree branches. You'll need to climb the tree to reach it."
        )

    return EventResult(allow=True, message="")
```

### behaviors/crystal_ball.py (MODIFIED)

Modify `handle_peer`:
```python
def handle_peer(accessor, action: Dict) -> HandlerResult:
    """Handle the peer/gaze command with positioning."""
    actor_id = action.get("actor_id", "player")
    obj_name = action.get("object")
    adjective = action.get("adjective")

    if not obj_name:
        return HandlerResult(success=False, message="Peer into what?")

    # Find item
    item = find_item_in_inventory(accessor, obj_name, actor_id)
    if not item:
        item = find_accessible_item(accessor, obj_name, actor_id, adjective)

    if not item:
        return HandlerResult(success=False, message=f"You don't see any {obj_name} here.")

    # Check if item requires proximity
    properties = item.properties if hasattr(item, 'properties') else {}
    interaction_distance = properties.get("interaction_distance", "any")

    if interaction_distance == "near":
        # Use implicit positioning
        from utilities.positioning import try_implicit_positioning, build_message_with_positioning

        positioning_result = try_implicit_positioning(accessor, item, actor_id)
        if not positioning_result["success"]:
            return HandlerResult(success=False, message=positioning_result["message"])

    # Check if item can be peered into
    if not properties.get("magical", False):
        return HandlerResult(
            success=False,
            message=f"You stare at the {item.name}, but nothing happens."
        )

    # Invoke entity behavior
    result = accessor.update(item, {}, verb="peer", actor_id=actor_id)

    if not result.success:
        return HandlerResult(success=False, message=result.message)

    # Build response message (include positioning message if any)
    base_message = f"You peer deeply into the {item.name}..."

    if interaction_distance == "near":
        message = build_message_with_positioning(
            positioning_result,
            f"{base_message}\n{result.message}" if result.message else base_message
        )
    else:
        message = f"{base_message}\n{result.message}" if result.message else base_message

    return HandlerResult(success=True, message=message)
```

## Summary

### Clean Design
- No behavior_libraries needed for this example (all behaviors are game-specific)
- Core behaviors loaded separately at Tier 3
- Game behaviors at Tier 1
- Simple entity behaviors handle positioning checks

### API Change Required
Add `base_tier` parameter to `BehaviorManager.load_modules()` to allow explicit tier control.

### No Design Problems
The current spatial system handles all requirements cleanly:
- Chained positioning: Entity behaviors check posture/focused_on
- Proximity requirements: Use `interaction_distance` property + `try_implicit_positioning()`
- Universal interactions: Parts with default properties

All behaviors use positive testing and follow separation of concerns.
