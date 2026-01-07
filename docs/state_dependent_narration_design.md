# State-Dependent Narration Design

**Created**: 2026-01-06
**Status**: Design Review
**Issue**: State-dependent narration for doors, passages, and general entities

---

## Problem Statement

Current narration issues:

1. **Door states not reflected in narration**: Doors are locked, unlocked, or open, but narration doesn't change based on state
2. **Passages behind closed doors are visible**: When door is closed, passage/stairs beyond are narrated, breaking immersion
3. **Door spatial relationships unclear**: From top of stairs, door at bottom isn't clearly located in narration
4. **No general state-variant support for items**: Only locations have `state_variants` via `state_variant_selector.py`, items don't

---

## Goals

1. **Door state narration**: Doors show different traits/descriptions when locked, unlocked, or open
2. **Passage visibility**: Passages behind closed doors are hidden from narration and movement
3. **Spatial door relationships**: Doors referenced by passages show clear spatial positioning
4. **General item state variants**: Any item can have state-dependent narration keyed by property values
5. **Flexible authoring**: Support both shared traits (all states) and state-specific traits
6. **No breaking changes**: Existing games work unchanged, new features are opt-in

---

## Architecture Overview

### Current State (Locations Only)

**Locations** already have state-dependent narration:
- `utilities/state_variant_selector.py` - Selection logic
- `utilities/location_serializer.py:87-102` - Integration point
- Priority: location properties > quest flags > visit history

**Process**:
1. Location serialized with `entity_to_dict(location)`
2. `select_state_variant()` chooses best match from `llm_context.state_variants`
3. Selected variant added as `state_note`
4. `state_variants` dict removed from output (narrator sees only selected variant)

### Proposed Extension (All Entities)

**Items, Exits, Doors** get same capability:
- Reuse `state_variant_selector.py` logic pattern
- Add item-specific selection in `entity_serializer.py`
- State keys based on entity properties (door: open/closed/locked, light: lit/unlit, etc.)

---

## Design Details

### 1. State Variant Structure

#### 1.1 Shared Traits + State Variants (Flexible Authoring)

Entities can have:
- **Common traits**: Always present regardless of state
- **State-specific variants**: Additional or replacement descriptions for specific states

```json
{
  "id": "door_sanctum",
  "name": "door",
  "llm_context": {
    "traits": [
      "ornate carved wood",
      "ancient craftsmanship",
      "pulsing with magical energy"
    ],
    "state_variants": {
      "closed_locked": "glowing arcane runes form a seal across the door, pulsing with protective magic",
      "closed_unlocked": "arcane runes dim but still visible, protective seal broken",
      "open": "door swings wide, revealing narrow stone stairs ascending into darkness"
    }
  }
}
```

**Narration assembly**:
- Narrator receives `traits` array (always present)
- Narrator receives `state_note` string (selected variant)
- Narrator weaves both into prose

**Benefit**: Authors don't duplicate unchanging traits, only add state-specific details

#### 1.2 State-Only Traits (Alternative)

For entities where traits change completely by state:

```json
{
  "id": "item_torch",
  "llm_context": {
    "state_variants": {
      "unlit": {
        "traits": [
          "wooden shaft wrapped in pitch-soaked cloth",
          "unlit but ready for flame",
          "smell of pitch strong"
        ]
      },
      "lit": {
        "traits": [
          "wooden shaft wrapped in burning cloth",
          "flames dancing steadily",
          "smoke trailing upward",
          "warm glow illuminating surroundings"
        ]
      }
    }
  }
}
```

**Narration assembly**:
- Narrator receives `traits` array from selected state variant
- No separate `state_note`

**Benefit**: Complete control over traits per state, useful for dramatic state changes

### 2. State Selection Keys

#### 2.1 Door States

Three primary states based on `door` property:

```python
# Door item properties
{
  "door": {
    "open": bool,
    "locked": bool
  }
}

# State key computation
if door.door_open:
    state_key = "open"
elif door.door_locked:
    state_key = "closed_locked"  # or just "locked"
else:
    state_key = "closed_unlocked"  # or just "closed"
```

**Variant key options**:

**Option A: Explicit (Recommended)**
- `"open"`, `"closed_locked"`, `"closed_unlocked"`
- Clear intent, supports all scenarios
- Authors can omit `closed_unlocked` if same as `closed_locked`

**Option B: Simplified**
- `"open"`, `"locked"`, `"closed"`
- Shorter keys
- Assumes locked doors are closed (reasonable)

**Decision: Use Option A** - More explicit, easier to understand authoring

#### 2.2 Other Common States

```python
# Light sources
states.get("lit") -> "lit" | "unlit"

# Containers
container.open -> "open" | "closed"

# General item state
properties.get("broken") -> "broken" | "intact"
properties.get("active") -> "active" | "inactive"

# Location/item position
properties.get("posture") -> "standing" | "sitting" | "climbing"
```

### 3. Passage Visibility Behind Doors

#### 3.1 Problem

In spatial_game:
- `exit_loc_library_up` has `passage="narrow stone stairs"` and `door_id="door_sanctum"`
- When door is closed, the stairs should not be mentioned in narration
- Currently, exit appears in `get_visible_exits()` regardless of door state

#### 3.2 Solution: Door-Aware Exit Filtering

Extend `StateAccessor.get_visible_exits()` to filter door-blocked passages:

```python
def get_visible_exits(self, location_id: LocationId, actor_id: ActorId) -> Dict[str, "Exit"]:
    """Get visible exits, filtering hidden exits and door-blocked passages.

    Exits are hidden if:
    1. Exit has states.hidden = true (observability check)
    2. Exit has passage AND door_id AND we're at door_at location AND door is closed

    An exit with passage and door_id represents a passage BEYOND a door.

    Visibility rules:
    - From door_at location (where door physically is):
      * If door closed: passage beyond is NOT visible (can't see through door)
      * If door open: passage beyond IS visible
    - From non-door_at location (other end of passage):
      * Passage is ALWAYS visible (the stairs/passage itself doesn't disappear)
      * Use state_variants to describe door state at far end
    """
    location = self.get_location(location_id)
    visible = {}

    for exit_entity in self.game_state.exits:
        if exit_entity.location != location_id:
            continue

        # Check 1: Observable (existing logic)
        if not is_observable(exit_entity, self, actor_id):
            continue

        # Check 2: Passage behind closed door (only at door_at location)
        if exit_entity.passage and exit_entity.door_id and exit_entity.door_at:
            # Only hide if we're AT the door location and door is closed
            if exit_entity.door_at == location_id:
                door = self.get_door_item(exit_entity.door_id)
                if door and not door.door_open:
                    # We're at the door location and it's closed - can't see passage beyond
                    continue

        # Exit is visible
        if exit_entity.direction:
            visible[exit_entity.direction] = exit_entity

    return visible
```

**Key insight**: `door_at` field indicates which location the door is physically at. From that location, a closed door blocks view of the passage beyond. From the other end, the passage itself is always visible (stairs don't disappear), but state_variants describe the door state at the far end.

#### 3.3 Door Visibility Rules

**From door_at location (where door physically is)**:
- Exit with passage: HIDDEN when door closed (can't see through door)
- Exit with passage: VISIBLE when door open (can see passage beyond)
- **Door ITEM: ALWAYS visible** (door is present even when passage beyond is hidden)
- Door item's state_variant describes passage when "open" ("revealing narrow stone stairs ascending")

**From non-door_at location (other end of passage)**:
- Exit/passage: ALWAYS visible (the physical structure doesn't disappear)
- Door item: ALWAYS visible (associated with exit at this location)
- Exit state_variants describe door state at far end ("closed door at bottom" vs "open door at bottom")

#### 3.4 Example: Ornate Door with Stairs

**Location setup**:
- `loc_library` (bottom) has `exit_loc_library_up` to `loc_sanctum` (top)
- `loc_sanctum` (top) has `exit_loc_sanctum_down` to `loc_library` (bottom)
- Both exits have `door_id="door_sanctum"` and `passage="narrow stone stairs"`
- Exit has `door_at="loc_library"` (door is at bottom)

**From loc_library (door location) - door CLOSED**:
```json
{
  "exits": {
    "up": {
      "type": "door",
      "name": "ornate door",
      "door_id": "door_sanctum"
    }
  },
  "doors": [
    {
      "id": "door_sanctum",
      "name": "door",
      "llm_context": {
        "traits": ["ornate carved wood", "ancient craftsmanship"],
        "state_note": "glowing arcane runes form a seal, door firmly closed"
      }
    }
  ]
}
```
**Narration**: "An ornate door of carved wood blocks the way upward, glowing runes sealing it shut."

**From loc_library (door location) - door OPEN**:
```json
{
  "exits": {
    "up": {
      "type": "open",
      "name": "ornate door",
      "door_id": "door_sanctum"
    }
  },
  "doors": [
    {
      "id": "door_sanctum",
      "name": "door",
      "llm_context": {
        "traits": ["ornate carved wood", "ancient craftsmanship"],
        "state_note": "door swings wide, revealing narrow stone stairs ascending into darkness"
      }
    }
  ]
}
```
**Narration**: "An ornate door stands open, narrow stone stairs visible beyond, spiraling upward."

**From loc_sanctum (opposite end) - door CLOSED**:
```json
{
  "exits": {
    "down": {
      "type": "open",
      "name": "spiral staircase",
      "llm_context": {
        "traits": ["worn grey stone", "spiral design", "descending"],
        "state_note": "stairs descend into shadow, ending at a closed door below"
      }
    }
  }
}
```
**Passage is ALWAYS VISIBLE** - stairs don't disappear. State variant describes closed door at bottom.

**From loc_sanctum (opposite end) - door OPEN**:
```json
{
  "exits": {
    "down": {
      "type": "open",
      "name": "spiral staircase",
      "llm_context": {
        "traits": ["worn grey stone", "spiral design", "descending"],
        "state_note": "stairs descend to an ornate door standing open at the bottom"
      }
    }
  }
}
```
**Narration**: "Narrow stone stairs spiral downward, ending at an ornate door standing open below."

### 4. Door State Variants for Passage Information

Door items use `state_variants` to describe passage when open:

```json
{
  "id": "door_sanctum",
  "name": "door",
  "location": "exit:loc_library:up",
  "llm_context": {
    "traits": [
      "ornate carved wood",
      "ancient craftsmanship",
      "faint magical aura"
    ],
    "state_variants": {
      "closed_locked": "glowing arcane runes seal the door shut, pulsing with protective magic",
      "closed_unlocked": "arcane runes have faded to dim outlines, seal broken but door remains closed",
      "open": "door stands open wide, narrow stone stairs visible beyond ascending into shadow"
    }
  }
}
```

**Key point**: The "open" variant mentions the passage. This is where passage description lives for door's location side.

### 5. Exit State Variants for Door Location

Exit entities can optionally have state variants to describe door at far end:

```json
{
  "id": "exit_loc_sanctum_down",
  "name": "spiral staircase",
  "location": "loc_sanctum",
  "door_id": "door_sanctum",
  "passage": "narrow stone stairs",
  "door_at": "loc_library",
  "traits": {
    "llm_context": {
      "traits": [
        "worn grey stone",
        "spiral design",
        "narrow passage"
      ],
      "state_variants": {
        "door_open": "stairs descend to an ornate door standing open at the bottom",
        "door_closed": "stairs descend into darkness, ending at a closed door below"
      }
    }
  }
}
```

**State key**: Computed from associated door's state
- If `exit.door_id` exists, look up door and check `door.door_open`
- State key: `"door_open"` or `"door_closed"`

**Note**: This is OPTIONAL. If exit doesn't have state_variants, it just doesn't mention the door.

---

## Implementation Plan

### Phase 1: Core State Variant Infrastructure for Items

**Goal**: Extend state variant selection from locations to all entities

#### 1.1 Add item state variant selection to entity_serializer.py

**File**: `utilities/entity_serializer.py`

Add function similar to `select_state_variant` but for items:

```python
def _select_item_state_variant(
    llm_context: Dict[str, Any],
    entity: Any
) -> Optional[Union[str, Dict[str, Any]]]:
    """Select state variant for an item based on its properties.

    Checks entity properties in priority order:
    1. Door state (open, closed_locked, closed_unlocked)
    2. Light state (lit, unlit)
    3. Container state (open, closed)
    4. Generic state properties (broken, active, etc.)

    Returns:
        - str: state_note text if variant is a string
        - dict: traits dict if variant is a dict with "traits"
        - None: if no matching variant
    """
    variants = llm_context.get('state_variants', {})
    if not variants:
        return None

    # Priority 1: Door state
    if hasattr(entity, 'door_open') or hasattr(entity, 'door_locked'):
        state_key = _compute_door_state_key(entity)
        if state_key and state_key in variants:
            return variants[state_key]

    # Priority 2: Light state
    if hasattr(entity, 'states'):
        states = entity.states
        if isinstance(states, dict):
            if states.get('lit') is not None:
                state_key = "lit" if states['lit'] else "unlit"
                if state_key in variants:
                    return variants[state_key]

    # Priority 3: Container state
    if hasattr(entity, 'container'):
        container = entity.container
        if isinstance(container, dict) and 'open' in container:
            state_key = "open" if container['open'] else "closed"
            if state_key in variants:
                return variants[state_key]

    # Priority 4: Generic properties
    # Check common state properties
    if hasattr(entity, 'properties'):
        props = entity.properties
        for prop_name in ['broken', 'active', 'powered', 'sealed']:
            if prop_name in props:
                # Boolean properties
                if isinstance(props[prop_name], bool):
                    state_key = prop_name if props[prop_name] else f"not_{prop_name}"
                    if state_key in variants:
                        return variants[state_key]
                # String properties (e.g., "damaged", "intact")
                elif isinstance(props[prop_name], str):
                    if props[prop_name] in variants:
                        return variants[props[prop_name]]

    return None


def _compute_door_state_key(entity: Any) -> Optional[str]:
    """Compute door state key: open | closed_locked | closed_unlocked."""
    if not hasattr(entity, 'door_open'):
        return None

    if entity.door_open:
        return "open"
    elif hasattr(entity, 'door_locked') and entity.door_locked:
        return "closed_locked"
    else:
        return "closed_unlocked"
```

#### 1.2 Integrate state variant selection in _add_llm_context

Update `_add_llm_context()` to call item state variant selector:

```python
def _add_llm_context(result: Dict[str, Any], entity: Any,
                     max_traits: Optional[int] = None,
                     player_context: Optional[Dict[str, Any]] = None) -> None:
    """Add llm_context with trait randomization and state variant selection."""
    llm_context = _get_llm_context(entity)
    if not llm_context:
        return

    context_copy = dict(llm_context)

    # Select state variant for items (NEW)
    state_variant = _select_item_state_variant(context_copy, entity)

    if state_variant:
        # Check if variant is string (state_note) or dict (trait replacement)
        if isinstance(state_variant, str):
            # String variant: Add as state_note, keep existing traits
            result['state_note'] = state_variant

            # Randomize existing traits
            if 'traits' in context_copy and isinstance(context_copy['traits'], list):
                traits_copy = list(context_copy['traits'])
                random.shuffle(traits_copy)
                if max_traits is not None:
                    traits_copy = traits_copy[:max_traits]
                context_copy['traits'] = traits_copy

        elif isinstance(state_variant, dict) and 'traits' in state_variant:
            # Dict variant: Replace traits entirely
            traits_copy = list(state_variant['traits'])
            random.shuffle(traits_copy)
            if max_traits is not None:
                traits_copy = traits_copy[:max_traits]
            context_copy['traits'] = traits_copy
    else:
        # No state variant: Use base traits
        if 'traits' in context_copy and isinstance(context_copy['traits'], list):
            traits_copy = list(context_copy['traits'])
            random.shuffle(traits_copy)
            if max_traits is not None:
                traits_copy = traits_copy[:max_traits]
            context_copy['traits'] = traits_copy

    # Select perspective variant (existing code)
    perspective_note = _select_perspective_variant(context_copy, player_context)
    if perspective_note:
        result['perspective_note'] = perspective_note

    # Remove variant dicts from output
    context_copy.pop('perspective_variants', None)
    context_copy.pop('state_variants', None)

    result['llm_context'] = context_copy
```

#### 1.3 Testing

**File**: `tests/test_entity_serializer.py` (new or extend existing)

```python
def test_door_state_variant_selection():
    """Door shows different state_note based on open/locked state."""

def test_door_state_variant_with_traits():
    """Door combines shared traits with state-specific note."""

def test_light_state_variant():
    """Torch shows different traits when lit vs unlit."""

def test_state_variant_dict_replaces_traits():
    """State variant with traits dict replaces base traits."""

def test_no_state_variant_uses_base_traits():
    """Entity without state_variants uses base traits only."""
```

**Estimated effort**: 3-4 hours

---

### Phase 2: Passage Visibility Filtering

**Goal**: Hide passages behind closed doors from narration and movement

#### 2.1 Update get_visible_exits() for door filtering

**File**: `src/state_accessor.py`

```python
def get_visible_exits(self, location_id: LocationId, actor_id: ActorId) -> Dict[str, "Exit"]:
    """Get visible exits, filtering hidden and door-blocked passages.

    An exit with both passage and door_id represents a structure beyond a door.
    When the door is closed, the passage is not visible.

    Returns:
        Dict of direction -> Exit for visible exits only
    """
    from utilities.utils import is_observable

    location = self.get_location(location_id)
    visible: Dict[str, "Exit"] = {}

    for exit_entity in self.game_state.exits:
        if exit_entity.location != location_id:
            continue

        # Filter 1: Observability check (existing)
        if not is_observable(exit_entity, self, actor_id):
            continue

        # Filter 2: Passage behind closed door (NEW)
        if exit_entity.passage and exit_entity.door_id:
            # This exit represents a passage beyond a door
            # Check if door is open
            try:
                door = self.get_door_item(exit_entity.door_id)
                if not door.door_open:
                    # Door closed - passage not visible
                    continue
            except KeyError:
                # Door doesn't exist - treat as open (fail gracefully)
                pass

        # Exit is visible - add to result
        if exit_entity.direction:
            visible[exit_entity.direction] = exit_entity

    return visible
```

#### 2.2 Update exit type computation

**File**: `utilities/location_serializer.py:163`

When door is closed, exit type should still be "door" (not "open"):

```python
# Compute exit type from door_id
if exit_entity.door_id:
    exit_type = "door"
    # Check if door is open to determine accessibility
    try:
        door = accessor.get_door_item(exit_entity.door_id)
        # If passage exists and door is open, type becomes "open"
        if exit_entity.passage and door.door_open:
            exit_type = "open"
    except KeyError:
        pass
else:
    exit_type = "open"
```

Actually, on reflection: **If passage is hidden when door is closed** (Phase 2.1), then the exit won't appear in this loop at all. So this change may not be needed.

#### 2.3 Testing

**File**: `tests/test_passage_visibility.py` (new)

```python
def test_passage_hidden_from_door_location_when_closed():
    """Exit with passage is hidden from door_at location when door is closed."""

def test_passage_visible_from_door_location_when_open():
    """Exit with passage is visible from door_at location when door is open."""

def test_passage_always_visible_from_opposite_location():
    """Exit with passage is always visible from non-door_at location, regardless of door state."""

def test_exit_without_passage_always_visible():
    """Exit with door_id but no passage is always visible (it's just a door)."""

def test_passage_without_door_always_visible():
    """Exit with passage but no door_id is always visible (open passage)."""

def test_movement_blocked_when_door_closed():
    """Cannot move through door when it is closed, regardless of location."""

def test_movement_allowed_when_door_open():
    """Can move through door when it is open."""
```

**Estimated effort**: 2-3 hours

---

### Phase 3: Exit State Variants for Door References

**Goal**: Exits can describe doors at far end using state variants

#### 3.1 Add exit state variant selection

**File**: `utilities/entity_serializer.py`

Add to `_select_item_state_variant` (or create separate `_select_exit_state_variant`):

```python
def _select_exit_state_variant(
    llm_context: Dict[str, Any],
    exit_entity: "Exit",
    accessor: Optional["StateAccessor"]
) -> Optional[str]:
    """Select state variant for exit based on associated door state.

    If exit has door_id, checks door state and selects variant:
    - "door_open" if door is open
    - "door_closed" if door is closed or locked

    Returns:
        State note string or None
    """
    variants = llm_context.get('state_variants', {})
    if not variants or not accessor:
        return None

    # Check if exit has associated door
    if hasattr(exit_entity, 'door_id') and exit_entity.door_id:
        try:
            door = accessor.get_door_item(exit_entity.door_id)
            state_key = "door_open" if door.door_open else "door_closed"
            if state_key in variants:
                return variants[state_key]
        except KeyError:
            pass

    return None
```

#### 3.2 Integrate in location_serializer

**File**: `utilities/location_serializer.py:177-184`

Update exit serialization to include state variant selection:

```python
# Include llm_context if present in traits - pass player_context for perspective_variants
if "llm_context" in exit_entity.traits:
    exit_dict = entity_to_dict(exit_entity, player_context=player_context)

    # NEW: Check for exit-specific state variants based on door state
    if "llm_context" in exit_dict:
        state_note = _select_exit_state_variant(
            exit_dict['llm_context'],
            exit_entity,
            accessor
        )
        if state_note:
            exit_dict['state_note'] = state_note

    if "llm_context" in exit_dict:
        exit_data["llm_context"] = exit_dict["llm_context"]
    # Also include perspective_note and state_note if present
    if "perspective_note" in exit_dict:
        exit_data["perspective_note"] = exit_dict["perspective_note"]
    if "state_note" in exit_dict:
        exit_data["state_note"] = exit_dict["state_note"]
```

#### 3.3 Testing

**File**: `tests/test_exit_state_variants.py` (new)

```python
def test_exit_state_variant_door_open():
    """Exit shows 'door_open' variant when associated door is open."""

def test_exit_state_variant_door_closed():
    """Exit shows 'door_closed' variant when associated door is closed."""

def test_exit_without_state_variants():
    """Exit without state_variants works normally."""
```

**Estimated effort**: 2 hours

---

### Phase 4: Narrator Prompt Update

**Goal**: Ensure narrator knows how to use state_note and state-based traits

#### 4.1 Update narrator prompt

**File**: `docs/Narration/unified_narrator_prompt_revised_api.md`

Add section explaining state_note usage:

```markdown
## Using Entity References

Entity references provide descriptive information about entities in the scene:

### Traits
The `traits` array contains permanent characteristics:
- Use traits to add sensory detail
- Weave them naturally into prose
- Don't list them mechanically

### State Notes
The `state_note` field provides state-dependent description:
- Describes current state of entity (e.g., door open/closed, light lit/unlit)
- Should be integrated with traits for complete picture
- Often describes relationships (e.g., "door open revealing stairs beyond")

### Example:
```json
{
  "entity_refs": {
    "door_sanctum": {
      "name": "door",
      "traits": ["ornate carved wood", "ancient craftsmanship"],
      "state_note": "door stands open, narrow stairs visible beyond"
    }
  }
}
```

Good narration: "An ornate door of ancient carved wood stands open before you, revealing narrow stone stairs ascending into darkness."

Bad narration: "You see an ornate door. It is made of carved wood and shows ancient craftsmanship. The door stands open, narrow stairs visible beyond." (Too mechanical, lists traits)
```

**Estimated effort**: 30 minutes

---

### Phase 5: Re-author Spatial Game

**Goal**: Add state variants to spatial_game doors and exits

#### 5.1 Update door_storage

**File**: `examples/spatial_game/game_state.json`

```json
{
  "id": "door_storage",
  "name": "door",
  "description": "A simple wooden door.",
  "location": "exit:loc_tower_entrance:east",
  "door": {
    "open": false,
    "locked": false
  },
  "properties": {
    "llm_context": {
      "traits": [
        "simple wooden construction",
        "plain surface",
        "iron handle",
        "slightly weathered"
      ],
      "state_variants": {
        "closed_locked": "door is closed and secured with an iron latch",
        "closed_unlocked": "door is closed but the latch is unlatched",
        "open": "door stands open, storage room visible beyond"
      }
    }
  }
}
```

#### 5.2 Update door_sanctum

```json
{
  "id": "door_sanctum",
  "name": "door",
  "description": "An ornate door.",
  "location": "exit:loc_library:up",
  "door": {
    "open": false,
    "locked": true,
    "lock_id": "lock_sanctum"
  },
  "properties": {
    "llm_context": {
      "traits": [
        "ornate carved wood",
        "ancient craftsmanship",
        "faint magical aura"
      ],
      "state_variants": {
        "closed_locked": "glowing arcane runes seal the door shut, pulsing with protective magic",
        "closed_unlocked": "arcane runes have dimmed to faint outlines, seal broken but door remains closed",
        "open": "door swings wide, revealing narrow stone stairs ascending into shadow"
      }
    }
  }
}
```

#### 5.3 Update exit_loc_sanctum_down (optional)

Add state variants to describe door at bottom:

```json
{
  "id": "exit_loc_sanctum_down",
  "name": "ornate door",
  "location": "loc_sanctum",
  "connections": ["exit_loc_library_up"],
  "direction": "down",
  "description": "An ornate door.",
  "door_id": "door_sanctum",
  "passage": "narrow stone stairs",
  "door_at": "loc_library",
  "traits": {
    "llm_context": {
      "traits": [
        "worn grey stone steps",
        "spiral descent",
        "narrow passage"
      ],
      "state_variants": {
        "door_open": "stairs descend to an ornate door standing open at the bottom",
        "door_closed": "stairs descend into shadow, ending at a closed door below"
      }
    }
  }
}
```

**Estimated effort**: 1 hour

---

### Phase 6: Testing & Validation

**Goal**: Comprehensive testing of all state-dependent narration features

#### 6.1 Create walkthrough test

**File**: `walkthroughs/state_dependent_narration.txt`

```
# Test door state variants and passage visibility

# Start in library, door is closed and locked
look
# Should show ornate door, NO mention of stairs
# Door should show locked state

examine door
# Should show locked state variant

unlock door with key
look
# Door should show unlocked state variant
# Still no stairs visible (door closed)

open door
look
# Door should show open state variant mentioning stairs
# Stairs should now be visible as exit

up
# Should successfully move to sanctum

look
# From top, should see stairs going down
# Should mention door at bottom (if exit has state_variant)

close door
look
# Stairs should disappear from view (passage hidden)

down
# Should fail - passage not visible

open door
look
# Stairs reappear

down
# Should succeed
```

#### 6.2 Run comprehensive tests

```bash
# Unit tests
python -m pytest tests/test_entity_serializer.py -v
python -m pytest tests/test_passage_visibility.py -v
python -m pytest tests/test_exit_state_variants.py -v

# Integration tests
python -m pytest tests/test_doors.py -v

# Walkthrough tests
python tools/walkthrough.py examples/spatial_game --file walkthroughs/state_dependent_narration.txt

# All tests
make test
```

#### 6.3 Manual testing

Play through spatial_game scenarios:
- Lock/unlock door, verify narration changes
- Open/close door with passage, verify stairs appear/disappear
- Test from both sides of passage
- Test "look at door" vs "look at stairs" vs "look"

**Estimated effort**: 3-4 hours

---

### Phase 7: Extend to Other Games

**Goal**: Add state variants to other example games as appropriate

#### 7.1 big_game

Doors with state variants:
- Search for doors in big_game
- Add appropriate state_variants to each

Passage exits:
- Find exits with both door_id and passage
- Ensure proper state variants

#### 7.2 other example games

Review each game for:
- Doors (add state variants)
- Light sources (add lit/unlit variants)
- Containers (add open/closed variants if meaningful)

**Estimated effort**: 2-3 hours per game

---

## Summary of Changes

### Code Changes

1. **utilities/entity_serializer.py**
   - Add `_select_item_state_variant()` function
   - Add `_compute_door_state_key()` helper
   - Add `_select_exit_state_variant()` function
   - Update `_add_llm_context()` to call state variant selectors
   - Support both string state_notes and dict trait replacement

2. **src/state_accessor.py**
   - Update `get_visible_exits()` to filter door-blocked passages (only from door_at location)

3. **utilities/location_serializer.py**
   - Integrate exit state variant selection in exit serialization

4. **docs/Narration/unified_narrator_prompt_revised_api.md**
   - Add state_note usage documentation

5. **src/validators.py** (new functionality)
   - Add validation for state_variant keys
   - Warn about unknown state keys to catch typos

### Authoring Changes

1. **examples/spatial_game/game_state.json**
   - Add state_variants to door_storage
   - Add state_variants to door_sanctum
   - Optionally add state_variants to exit_loc_sanctum_down

2. **Other example games**
   - Add state_variants to doors, lights, containers as appropriate

### Testing Changes

1. **New test files**:
   - `tests/test_entity_serializer.py` (or extend existing)
   - `tests/test_passage_visibility.py`
   - `tests/test_exit_state_variants.py`

2. **New walkthrough**:
   - `walkthroughs/state_dependent_narration.txt`

---

## Total Estimated Effort

- Phase 1: 3-4 hours
- Phase 2: 2-3 hours
- Phase 3: 2 hours
- Phase 4: 0.5 hours
- Phase 5: 1 hour
- Phase 6: 3-4 hours
- Phase 7: 2-3 hours per game

**Total: 14-18 hours** for complete implementation and testing

---

## Open Questions & Discussion Points

1. **State variant key naming**: Prefer `closed_locked`/`closed_unlocked` or `locked`/`unlocked`/`closed`?
   - Recommendation: `closed_locked`/`closed_unlocked`/`open` for clarity

2. **Shared vs state-specific traits**: Should we support both patterns or standardize?
   - Recommendation: Support both, use shared+state_note for most cases, full replacement for dramatic changes

3. **Exit state variant necessity**: Is it essential for exits to have door state variants?
   - Recommendation: Make it optional, valuable for "door at bottom of stairs" case

4. **Fallback behavior**: If state key not found in variants, use base traits or error?
   - Recommendation: Use base traits (graceful degradation)

5. **State variant validation**: Should we validate state keys at load time?
   - Recommendation: Add validator warnings for unknown state keys (help authors catch typos)

---

## Success Criteria

- [ ] Doors show different narration when locked vs unlocked vs open
- [ ] Passages behind closed doors are hidden from narration
- [ ] Passages behind closed doors cannot be traversed
- [ ] Opening door reveals passage in narration
- [ ] Door spatial relationships clear from both sides
- [ ] Existing games work unchanged (no breaking changes)
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Walkthrough test achieves 100% expected results
- [ ] Manual testing shows correct behavior in spatial_game
- [ ] Implementation is general enough for other use cases (lights, containers, etc.)
