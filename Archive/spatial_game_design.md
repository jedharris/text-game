# Spatial Game Example - Design Document

## Overview

This document describes the design for a new example game (`examples/spatial_game`) that demonstrates the spatial positioning system. The game will be based on `examples/extended_game` but will add spatial mechanics to two locations:

1. **Garden**: Bench → Tree → Star (chained positioning requirements using "stand on bench")
2. **Wizard's Library**: Window (look out of) and Crystal Ball (requires proximity but no implicit positioning)

## Requirements

### Garden Mechanics
- Player must use `stand on bench` to position on the bench
- From bench, player can `climb tree` to set climbing posture
- While climbing tree, player can `take star` from branches
- Uses new `stand on <surface>` command (Tier 2 library)

### Library Mechanics
- Player can `look out of window` from anywhere (new command, Tier 2 library)
- Crystal ball requires proximity but does NOT auto-position player
- Player must first `examine ball` or `examine stand` to get near ball
- Then `peer into ball` works (checks focused_on, fails if not near)

## Architecture

### Tier Structure

The game uses a three-tier behavior system controlled by directory depth:

- **Tier 1**: Game-specific behaviors (depth 0)
- **Tier 2**: Reusable spatial library (depth 1)
- **Tier 3**: Core engine behaviors (depth 2, via symlink)

Tiers are calculated as: `tier = depth + 1` where depth is subdirectory levels below `behaviors/`.

### Directory Structure

```
examples/spatial_game/
├── game_state.json
├── run_game.py
├── behaviors/
│   ├── __init__.py
│   ├── magic_star.py        # Tier 1: Game-specific (depth 0)
│   ├── crystal_ball.py      # Tier 1: Modified for no implicit positioning
│   ├── magic_wand.py        # Tier 1: From extended_game
│   ├── magic_mat.py         # Tier 1: From extended_game
│   ├── spellbook.py         # Tier 1: From extended_game
│   ├── lib/                 # Directory
│   │   ├── spatial/         # Tier 2: Reusable library (depth 1)
│   │   │   ├── __init__.py
│   │   │   ├── stand_sit.py # NEW: stand on/sit on commands
│   │   │   └── look_out.py  # NEW: look out of command
│   │   └── core/            # Tier 3: Core behaviors (depth 2, symlink)
│   │       -> ../../../../behaviors/core/
```

**Key points:**
- Single `discover_modules("behaviors/")` call loads everything
- Symlink at `lib/core/` puts core behaviors at depth 2 → Tier 3
- Spatial library at `lib/spatial/` is at depth 1 → Tier 2
- Game files at root are at depth 0 → Tier 1

## Design Decisions

### Stand On Command (New)

**Why needed:** `approach bench` sets `focused_on` but doesn't establish "standing on" relationship needed for climbing tree.

**Implementation:**
- New verb: `stand on <surface>` (synonyms: `stand`, `get on`)
- Sets `posture: "on_surface"` and `focused_on` to the surface
- Checks for `container.is_surface: true` property on target
- Located in Tier 2 library (`lib/spatial/stand_sit.py`)

**Also include:** `sit on <surface>` with same posture (for future flexibility)

### Look Out Of Command (New)

**Why needed:** `examine window` describes the window object, not the view outside.

**Implementation:**
- New verb: `look out of <object>` (note: "out of" is the preposition phrase)
- Uses indirect_object from parser
- Checks if object allows looking out (any Part or Item can work by default)
- Simply displays object's description (which should describe the view)
- Located in Tier 2 library (`lib/spatial/look_out.py`)

**Parser considerations:**
- "out" already in prepositions, "of" needs to be added
- Parser handles compound prepositions naturally

### Crystal Ball - No Implicit Positioning

**Why:** User requested that `peer into ball` should FAIL if player not near, not auto-position them.

**Implementation:**
- Ball has `interaction_distance: "near"` property
- `handle_peer` checks if `focused_on` matches ball (or ball's container)
- Returns failure with message "You need to be closer to peer into the ball" if not near
- Player must use `examine ball` or `examine stand` first to get near
- Modified `handle_peer` stays in Tier 1 (game-specific behavior)

### Tree Climbing - Chained Requirements

**Implementation:**
- Bench has `container.is_surface: true` (allows standing)
- Tree has `climbable: true` and `on_climb` behavior
- Tree's `on_climb` checks if player has `posture: "on_surface"` AND `focused_on: "item_garden_bench"`
- Star's `on_take` checks if player has `posture: "climbing"` AND `focused_on: "item_tree"`
- All checks in game-specific behaviors (Tier 1)

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

### Library Entities

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

## Behavior Implementations

### Tier 1: Game Behaviors

#### behaviors/magic_star.py (NEW)

```python
"""Magic star behavior - requires climbing tree to take."""

from src.behavior_manager import EventResult

def on_climb(entity, accessor, context):
    """
    Tree climb behavior - checks if player is standing on bench.

    entity: The tree
    context: {actor_id, verb}
    """
    actor_id = context.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)

    posture = actor.properties.get("posture")
    focused = actor.properties.get("focused_on")

    if posture != "on_surface" or focused != "item_garden_bench":
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

#### behaviors/crystal_ball.py (MODIFIED)

Modify `handle_peer` to check positioning without auto-positioning:

```python
def handle_peer(accessor, action: Dict) -> HandlerResult:
    """Handle the peer/gaze command - requires proximity but no auto-positioning."""
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

    # Check if item can be peered into
    properties = item.properties if hasattr(item, 'properties') else {}
    if not properties.get("magical", False):
        return HandlerResult(
            success=False,
            message=f"You stare at the {item.name}, but nothing happens."
        )

    # Check if item requires proximity (no auto-positioning!)
    interaction_distance = properties.get("interaction_distance", "any")
    if interaction_distance == "near":
        player = accessor.get_actor(actor_id)
        focused_on = player.properties.get("focused_on")

        # Check if focused on the item or its container
        if focused_on != item.id:
            # Check if focused on item's container
            if hasattr(item, 'location'):
                container = accessor.get_item(item.location)
                if not container or focused_on != container.id:
                    return HandlerResult(
                        success=False,
                        message=f"You need to be closer to peer into the {item.name}. Try examining it first."
                    )

    # Invoke entity behavior
    result = accessor.update(item, {}, verb="peer", actor_id=actor_id)

    if not result.success:
        return HandlerResult(success=False, message=result.message)

    # Build response message
    base_message = f"You peer deeply into the {item.name}..."
    message = f"{base_message}\n{result.message}" if result.message else base_message

    return HandlerResult(success=True, message=message)
```

### Tier 2: Spatial Library

#### lib/spatial/stand_sit.py (NEW)

```python
"""Stand on and sit on commands for surface positioning."""

from typing import Dict, Any
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item

vocabulary = {
    "verbs": [
        {
            "word": "stand",
            "event": "on_stand",
            "synonyms": ["get on"],
            "indirect_object_required": True,
            "llm_context": {
                "traits": ["positioning", "surface interaction"],
                "usage": ["stand on <surface>", "get on <surface>"]
            }
        },
        {
            "word": "sit",
            "event": "on_sit",
            "synonyms": [],
            "indirect_object_required": True,
            "llm_context": {
                "traits": ["positioning", "surface interaction"],
                "usage": ["sit on <surface>"]
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}

def handle_stand_on(accessor, action: Dict[str, Any]) -> HandlerResult:
    """Handle 'stand on <surface>' command."""
    return _handle_surface_action(accessor, action, "stand on", "on_surface")

def handle_sit_on(accessor, action: Dict[str, Any]) -> HandlerResult:
    """Handle 'sit on <surface>' command."""
    return _handle_surface_action(accessor, action, "sit on", "on_surface")

def _handle_surface_action(accessor, action: Dict[str, Any], action_verb: str,
                           posture: str) -> HandlerResult:
    """Common logic for stand/sit on surface."""
    actor_id = action.get("actor_id", "player")
    surface_name = action.get("indirect_object")
    adjective = action.get("adjective")

    if not surface_name:
        return HandlerResult(success=False, message=f"What do you want to {action_verb}?")

    # Get actor
    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Find surface
    surface = find_accessible_item(accessor, surface_name, actor_id, adjective)
    if not surface:
        return HandlerResult(
            success=False,
            message=f"You don't see any {surface_name} here."
        )

    # Check if it's a surface
    properties = surface.properties if hasattr(surface, 'properties') else {}
    container_props = properties.get("container", {})
    if not container_props.get("is_surface", False):
        return HandlerResult(
            success=False,
            message=f"You can't {action_verb} the {surface.name}."
        )

    # Set posture and focus
    actor.properties["focused_on"] = surface.id
    actor.properties["posture"] = posture

    message = f"You {action_verb} the {surface.name}."

    return HandlerResult(success=True, message=message)
```

#### lib/spatial/look_out.py (NEW)

```python
"""Look out of command for windows and openings."""

from typing import Dict, Any
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item

vocabulary = {
    "verbs": [
        {
            "word": "look",
            "event": "on_look_out",
            "synonyms": [],
            "indirect_object_required": True,
            "llm_context": {
                "traits": ["observation", "distant viewing"],
                "usage": ["look out of <window>"]
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}

def handle_look_out_of(accessor, action: Dict[str, Any]) -> HandlerResult:
    """
    Handle 'look out of <object>' command.

    Used for windows, doors, archways - anything with a view beyond.
    Uses positive testing: only handles if preposition is "out of" or "out".
    """
    actor_id = action.get("actor_id", "player")
    object_name = action.get("indirect_object")
    preposition = action.get("preposition")

    # Positive testing: only handle "look out of X" or "look out X"
    if not preposition or preposition not in ["out of", "out"]:
        return HandlerResult(success=False, message="")  # Let other handlers try

    if not object_name:
        return HandlerResult(success=False, message="Look out of what?")

    # Find the object (can be Item or Part)
    from utilities.positioning import find_and_position_item, find_and_position_part

    # Try finding as part first (windows are often parts)
    result = find_and_position_part(accessor, object_name, actor_id)
    if result["success"]:
        target = result["entity"]
    else:
        # Try as item
        result = find_and_position_item(accessor, object_name, actor_id, interaction_distance="any")
        if result["success"]:
            target = result["entity"]
        else:
            return HandlerResult(
                success=False,
                message=f"You don't see any {object_name} here."
            )

    # Get description (the view)
    properties = target.properties if hasattr(target, 'properties') else {}
    description = properties.get("description", f"Nothing special to see through the {target.name}.")

    return HandlerResult(success=True, message=description)
```

### Tier 3: Core Behaviors

Standard core behaviors (via symlink at `lib/core/`):
- Climb (spatial.py) - handles climbable items
- Take (manipulation.py) - handles item pickup
- Examine (perception.py) - handles implicit positioning
- Approach (spatial.py) - explicit positioning

## Gameplay Flow Examples

### Getting the Star

1. Player: `examine bench` → positions at bench
2. Player: `stand on bench` → sets posture "on_surface", focused_on bench
3. Player: `climb tree` → tree's on_climb checks posture/focus, succeeds
4. Player: `take star` → star's on_take checks posture "climbing" and focused_on tree, succeeds

### Using the Crystal Ball

1. Player: `peer into ball` → FAILS "You need to be closer"
2. Player: `examine stand` → positions at stand (ball's container), sets focused_on stand
3. Player: `peer into ball` → handle_peer checks focused_on, sees it's on ball's container, succeeds

### Looking Out Window

1. Player: `look out of window` → displays window's description (the view)
   - Works from anywhere in library (no proximity needed)

## Summary

### Clean Design
- Three-tier structure via directory depth (no API changes needed)
- Symlinks work naturally based on their position in game structure
- New library commands at Tier 2 for reusability
- Game-specific positioning checks at Tier 1
- Core behaviors at Tier 3 via nested symlink

### No Design Problems
- Tiers controlled by directory structure
- Symlinks respect game's structure, not target's structure
- All requirements met with clean separation of concerns
- Positive testing throughout (handlers check what they CAN handle)
