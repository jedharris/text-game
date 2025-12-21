# Perspective-Aware Narration

## Problem Statement

When the LLM narrates game results, it often describes actions inappropriately for the player's actual perspective. For example, when examining a staircase from ground level, the narration might describe climbing it, even though the player hasn't moved.

The engine needs to provide perspective context to the LLM so narration matches the player's actual position and posture.

## Goals

1. Provide player positioning context to the LLM narrator
2. Enable position-aware item descriptions
3. Support authored perspective-specific text variants
4. Maintain backward compatibility with existing games

## Use Cases

1. **Ground-level examination**: Player examines stairs from below - narration describes looking up at them, not climbing
2. **Surface positioning**: Player stands on a table - narration describes being elevated, looking down
3. **Climbing context**: Player is climbing a ladder - items are described relative to climbing position
4. **Container focus**: Player is inside a wardrobe - narration reflects enclosed perspective

## Existing Infrastructure

### Actor Properties (already implemented)

- `posture`: Current positioning state
  - `null` - normal standing
  - `"on_surface"` - standing/sitting on something
  - `"climbing"` - actively climbing
  - `"cover"` - behind cover
  - `"concealed"` - hidden inside something

- `focused_on`: Entity ID the player is positioned at/on/in

### Relevant Code

- `behaviors/core/spatial.py` - Sets posture for climb, cover, hide
- `examples/spatial_game/behaviors/lib/spatial/stand_sit.py` - Sets posture for stand/sit on surfaces
- `utilities/location_serializer.py` - Serializes locations for LLM
- `utilities/entity_serializer.py` - Serializes entities for LLM

## Design

### 1. Player Context Structure

Add `player_context` to location serialization output:

```python
"player_context": {
    "posture": "on_surface",      # from actor.properties["posture"]
    "focused_on": "wooden_table", # from actor.properties["focused_on"]
    "focused_entity_name": "wooden table"  # resolved name for LLM
}
```

### 2. Spatial Relation for Items

Add computed `spatial_relation` to item serialization when player has non-null posture:

```python
"spatial_relation": "below"  # "within_reach", "below", "above", "nearby"
```

Computed based on:
- If item IS the focused entity: `"within_reach"`
- If item is ON the focused surface: `"within_reach"`
- If player is on elevated surface and item is on floor: `"below"`
- Otherwise: `"nearby"`

### 3. Perspective Variants in llm_context

Authors can add `perspective_variants` to entity `llm_context`:

```json
{
  "llm_context": {
    "traits": ["worn stone steps", "spiral design"],
    "perspective_variants": {
      "default": "A spiral staircase rises through the tower",
      "climbing": "The worn steps continue above and below you",
      "on_surface:wooden_table": "The staircase is visible across the room"
    }
  }
}
```

Keys can be:
- `"default"` - used when no specific match
- `"<posture>"` - matches any focus with that posture
- `"<posture>:<entity_id>"` - matches specific posture + focus combination

### 4. Prompt Updates

Update narrator prompts to use `player_context`:

```
## Player Perspective

The "player_context" field tells you the player's current position:
- "posture": How the player is positioned (null=standing normally, "climbing"=on ladder/stairs, "on_surface"=standing on something)
- "focused_on": What the player is positioned at/on/in

Always narrate from this perspective. If the player is climbing, describe things relative to that. If examining something while standing normally, don't describe moving to or using it.
```

## Implementation Phases

### Phase 1: Add player_context to location serialization

**Files**: `utilities/location_serializer.py`

**Changes**:
- Modify `serialize_location_for_llm()` to accept actor object (not just actor_id)
- Add `player_context` dict to output with posture, focused_on, focused_entity_name
- Resolve focused_entity_name from focused_on ID

**Tests**: New tests in `tests/test_location_serializer.py`

### Phase 2: Add spatial_relation to item serialization

**Files**: `utilities/entity_serializer.py`

**Changes**:
- Add optional `player_context` parameter to `entity_to_dict()`
- Add optional `focused_entity_id` parameter
- When player has non-null posture, compute and add `spatial_relation`

**Tests**: New tests in `tests/test_entity_serializer.py`

### Phase 3: Add perspective_variants support

**Files**: `utilities/entity_serializer.py`

**Changes**:
- In `_add_llm_context()`, check for `perspective_variants`
- Select best matching variant based on player_context
- Add selected variant as `perspective_note` in output

**Tests**: Extend tests in `tests/test_entity_serializer.py`

### Phase 4: Thread player_context through serialization

**Files**:
- `utilities/location_serializer.py`
- `src/llm_protocol.py` (if it calls serializers directly)

**Changes**:
- Pass player_context to item serialization calls
- Ensure all paths that serialize for LLM include perspective info

**Tests**: Integration tests

### Phase 5: Update narrator prompts

**Files**:
- `src/narrator_protocol.txt`
- `src/llm_narrator.py` (Anthropic prompt)
- `src/mlx_narrator.py` (if it has its own prompt)

**Changes**:
- Add player perspective section to prompts
- Document how to use player_context fields

**Tests**: Manual testing with spatial_game

### Phase 6: Documentation

**Files**:
- `user_docs/authoring_manual/07_spatial.md`
- `user_docs/authoring_manual/11_advanced.md`

**Changes**:
- Document `perspective_variants` in llm_context
- Explain how perspective narration works

## Files Affected Summary

| File | Change Type |
|------|-------------|
| `utilities/location_serializer.py` | Modify |
| `utilities/entity_serializer.py` | Modify |
| `src/narrator_protocol.txt` | Modify |
| `src/llm_narrator.py` | Modify |
| `src/mlx_narrator.py` | Check/Modify |
| `tests/test_location_serializer.py` | Create |
| `tests/test_entity_serializer.py` | Create |
| `user_docs/authoring_manual/07_spatial.md` | Modify |
| `user_docs/authoring_manual/11_advanced.md` | Modify |

## Backward Compatibility

- `player_context` is additive - existing games work unchanged
- `spatial_relation` only added when posture is non-null
- `perspective_variants` is optional - entities without it narrate normally
- No changes to game state format
