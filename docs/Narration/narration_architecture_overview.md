# Narration Architecture Overview

## Core Principle: Engine Manages State, LLM Narrates

The fundamental architectural principle is **separation of concerns**:
- **Game Engine**: Executes commands, manages state changes, tracks game world
- **LLM Narrator**: Composes natural language prose from structured data

This separation ensures:
- Engine logic remains testable and deterministic
- Narrative quality improves through LLM capabilities
- Content authors have full control over what information reaches the narrator
- No "narrative leakage" where story elements affect game mechanics

## Data Flow Architecture

```
User Command
    ↓
Parser (extracts intent)
    ↓
Handler (executes state change, returns structured data)
    ↓
NarrationAssembler (gathers context, builds NarrationPlan)
    ↓
Narrator LLM (composes prose from structured data)
    ↓
Player sees natural language output
```

## Key Design Patterns

### 1. Handlers Return Structured Data, Not Prose

**Anti-pattern (what we avoid):**
```python
# Handler concatenating strings - BAD
state_note = "revealing stairs beyond"
primary = f"You open the door. {state_note.capitalize()}"
```

**Correct pattern:**
```python
# Handler returns structured data - GOOD
return HandlerResult(
    success=True,
    primary="You open the door.",
    data={
        "door": serialize_for_handler_result(door),
        "_context_changed": {"exits": True}
    }
)
```

The handler:
- Executes the state change
- Returns minimal primary message (action acknowledgment)
- Includes serialized entity data with descriptive fields
- Signals when context needs re-evaluation

### 2. Entity Serialization Provides Narrative Building Blocks

Entities are converted to dictionaries with narrative-relevant fields:

```python
{
    "id": "door_sanctum",
    "name": "ornate door",
    "type": "door",
    "llm_context": {
        "traits": ["carved wood", "ancient", "iron hinges"],
        "material": "oak",
        "notes": ["bears mystical symbols"]
    },
    "state_note": "door swings wide, revealing narrow stone stairs",
    "spatial_relation": "nearby"
}
```

**Key fields:**
- `traits`: Physical characteristics (randomized order for variety)
- `state_note`: State-dependent description (from state_variants)
- `perspective_note`: Player-position-dependent description (from perspective_variants)
- `spatial_relation`: Player's positional relationship (within_reach, nearby, below)
- `passage`: Physical passage description (for exits)

### 3. State-Dependent Narration via Variants

Entities can have different descriptions based on current state:

```json
{
    "llm_context": {
        "traits": ["carved wood", "ancient"],
        "state_variants": {
            "open": "door swings wide, revealing narrow stone stairs ascending into shadow",
            "closed_locked": "door is firmly locked, iron bolt engaged",
            "closed_unlocked": "door stands closed but unlatched"
        }
    }
}
```

**State variant selection priority:**
1. Door state (open, closed_locked, closed_unlocked)
2. Light state (lit, unlit)
3. Container state (open, closed)
4. Generic properties (broken, active, powered, etc.)

**Two variant formats:**
- **String variant**: Adds `state_note`, keeps existing traits
- **Dict variant with traits**: Replaces traits entirely for that state

### 4. Perspective-Aware Narration

Items can have different descriptions based on player position:

```json
{
    "llm_context": {
        "traits": ["leather-bound", "gilt edges"],
        "perspective_variants": {
            "on_surface:item_table": "book lies open before you, text clearly visible",
            "on_surface": "book rests on the surface within easy reach",
            "climbing": "book sits on the floor far below",
            "default": "book rests nearby"
        }
    }
}
```

**Selection logic:**
1. Try exact match: `"<posture>:<focused_on>"` (e.g., `"on_surface:item_table"`)
2. Try posture-only: `"<posture>"` (e.g., `"climbing"`)
3. Fall back to `"default"`

### 5. Context Change Signals

When actions change what's visible or accessible, handlers signal this:

```python
data["_context_changed"] = {"exits": True}
```

NarrationAssembler detects the signal and:
1. Re-serializes the location to get updated context
2. Adds newly-visible entities to entity_refs
3. Narrator weaves action and revelation together

**Example:** Opening a door reveals stairs beyond:
- Handler signals `exits` changed
- Location re-serialized, stairs now in visible_exits
- Narrator receives both door (with state_note) and exit (with passage)
- Narrator composes: "You open the ornate door. It swings wide, revealing narrow stone stairs spiraling upward into shadow."

### 6. Passage Visibility Rules

Exits with both `passage` and `door_id` represent passages BEYOND doors:

**From door_at location (where door physically is):**
- Door closed: passage NOT visible (can't see through door)
- Door open: passage IS visible
- Door item: ALWAYS visible (door itself is present)

**From opposite location:**
- Passage: ALWAYS visible (stairs don't disappear)
- Exit state_variants describe door state at far end

```json
{
    "state_variants": {
        "door_open": "stairs descend to an open doorway below",
        "door_closed": "stairs descend into shadow, ending at a closed door below"
    }
}
```

## Narration Assembly Process

### Step 1: Handler Execution
Handler executes command, returns HandlerResult with:
- `success`: bool
- `primary`: minimal action message
- `beats`: optional list of sub-events
- `data`: serialized entities and signals

### Step 2: Context Change Detection
If `_context_changed` in data:
- Re-serialize affected context (location, exits, etc.)
- Add updated entities to entity_refs

### Step 3: Entity Reference Building
For each entity in handler data:
- Extract narrative fields (traits, state_note, perspective_note, passage)
- Compute spatial_relation based on player posture
- Build EntityRef dict

### Step 4: NarrationPlan Construction
Assemble NarrationPlan with:
- `primary`: handler's action message
- `beats`: sub-events list
- `entity_refs`: dict of all referenced entities
- `location_context`: current location serialization
- `additional_context`: special narrative instructions

### Step 5: Narrator Composition
Narrator LLM receives NarrationPlan and:
- Weaves entities into natural prose
- Uses traits for physical descriptions
- Incorporates state_note for state-dependent narrative
- Applies perspective_note for position-aware descriptions
- Composes unified narrative from action + revelation

## Validation and Error Prevention

### Entity Trait Warnings
Physical entities (items, doors, furniture) should have traits for material grounding:

```python
# Warns if missing traits - prevents hallucination
if entity_type in ("item", "door", "furniture") and not traits:
    warn(f"Entity '{name}' has no traits. Narrator may hallucinate.")
```

**Exceptions:**
- Locations: Described via location.llm_context
- Exits: Directional/navigational, use passage field
- Actors: May be described dynamically

### State Variant Validation
Authors should test all state variants actually get triggered:
- Test door open/closed/locked states
- Test light lit/unlit states
- Test container open/closed states
- Verify state_note appears in output

## Authoring Guidelines

### For Items with States

Use state_variants to describe state-dependent appearance:

```json
{
    "id": "torch_wall",
    "name": "torch",
    "llm_context": {
        "traits": ["iron sconce", "resinous wood"],
        "state_variants": {
            "lit": {
                "traits": ["dancing flames", "warm glow", "flickering light"]
            },
            "unlit": "torch sits cold and dark in its sconce"
        }
    }
}
```

### For Doors with Passages

Door item describes door + revelation; exit describes passage:

```json
{
    "id": "door_sanctum",
    "llm_context": {
        "traits": ["carved oak", "ancient", "mystical symbols"],
        "state_variants": {
            "open": "door swings wide, revealing narrow stone stairs ascending"
        }
    }
}

// Separate exit entity
{
    "id": "exit_library_up",
    "passage": "narrow stone stairs",
    "door_id": "door_sanctum",
    "door_at": "loc_library",
    "traits": {
        "llm_context": {
            "traits": ["worn grey stone", "spiral design"]
        }
    }
}
```

### For Position-Dependent Items

Use perspective_variants for items player can interact with from different positions:

```json
{
    "id": "item_book",
    "llm_context": {
        "traits": ["leather-bound", "gilt edges"],
        "perspective_variants": {
            "on_surface:item_table": "book lies open, text at eye level",
            "climbing": "book rests on floor far below"
        }
    }
}
```

## Testing Approach

### Unit Tests
- Test state variant selection (all priorities, both formats)
- Test perspective variant selection (exact, posture, default)
- Test passage visibility rules (door_at vs opposite)
- Test spatial_relation computation

### Integration Tests
- Test handler → assembler → narrator flow
- Test context change detection and re-serialization
- Verify no string concatenation in handlers
- Verify traits warnings work correctly

### Walkthrough Tests
- Test actual game scenarios end-to-end
- Verify narration quality and coherence
- Check state-dependent descriptions appear correctly
- Validate perspective-aware narration

## Implementation Files

**Core Components:**
- `src/narration_assembler.py`: Builds NarrationPlan from handler results
- `utilities/entity_serializer.py`: Converts entities to LLM-consumable dicts
- `utilities/location_serializer.py`: Serializes locations with all visible contents
- `utilities/handler_utils.py`: Common handler patterns

**State Logic:**
- `src/state_accessor.py`: Visibility logic (exits, items, observability)
- `utilities/state_variant_selector.py`: Location-level state variant selection

**Documentation:**
- `docs/Narration/unified_narrator_prompt_revised_api.md`: Narrator API spec
- `docs/state_dependent_narration_design.md`: Implementation design doc

## Common Pitfalls to Avoid

1. **String concatenation in handlers** - Return structured data instead
2. **Hardcoding narrative logic** - Use state_variants and perspective_variants
3. **Missing traits on physical items** - Always provide material descriptions
4. **Confusing exits vs doors** - Exits are navigational, doors are physical items
5. **Ignoring player position** - Use spatial_relation and perspective_variants
6. **Not testing all states** - Verify every state_variant key is reachable

## Future Considerations

### Potential Extensions
- Time-dependent variants (day/night, seasons)
- NPC-dependent variants (different NPCs see different things)
- History-dependent variants (descriptions change based on past actions)
- Dynamic trait generation (procedural descriptions)

### Compatibility
- State variant structure is extensible (new state types can be added)
- Perspective variant keys follow composable pattern (can add new postures)
- Entity serialization is backward compatible (new fields are optional)
