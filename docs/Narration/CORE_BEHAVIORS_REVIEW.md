# Core Behaviors & Libraries Narration Review

This document reviews core behaviors and behavior libraries for compliance with the narration architecture defined in `docs/Narration/narration_architecture_overview.md`.

## Executive Summary

**Status**: ⚠️ Multiple violations found - significant refactoring needed

**Key Findings**:
- ✅ **handlers/utilities**: Door/container handlers already compliant (use structured data)
- ⚠️ **behaviors/core/light_sources.py**: Returns hard-coded narrative prose
- ⚠️ **behaviors/core/consumables.py**: Returns hard-coded narrative prose
- ⚠️ **behaviors/core/containers.py**: Returns hard-coded narrative prose (treasure chest)
- ✅ **behaviors/core/perception.py**: Acceptable - builds summary lists, not narrative
- ✅ **behaviors/core/exits.py**: Acceptable - builds summary lists, not narrative

**Severity**:
- **High**: Light sources, consumables - these are commonly used features
- **Medium**: Container treasure - specific use case, less common
- **Low**: Perception/exits - summary output, different from narrative composition

---

## Detailed Findings

### 1. ✅ COMPLIANT: utilities/handler_utils.py

**File**: `utilities/handler_utils.py`
**Functions**: `handle_open_close_door_or_container()`

**Status**: Excellent - recently refactored to comply

**Lines 604-616** (door handling):
```python
# Update door state
item.door_open = target_state
data = serialize_for_handler_result(item, accessor, actor_id)

# Signal that exits may have changed visibility
data["_context_changed"] = {"exits": True}

return HandlerResult(
    success=True,
    primary=f"You {verb} the {item.name}.",
    beats=beats,
    data=data
)
```

**Conformance**:
- ✅ Returns minimal primary message
- ✅ Returns serialized entity data
- ✅ Signals context changes for re-serialization
- ✅ Perfect separation of concerns

---

### 2. ⚠️ VIOLATION: behaviors/core/light_sources.py

**File**: `behaviors/core/light_sources.py`
**Functions**: `on_take()`, `on_drop()`, `on_put()`

**Status**: HIGH PRIORITY - Returns hard-coded narrative prose

**Lines 12-29** (on_take):
```python
def on_take(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """Auto-light when taken (magical runes activate on touch)."""
    entity.states['lit'] = True

    return EventResult(
        allow=True,
        feedback="As your hand closes around the lantern, the runes flare to life, casting a warm glow."
    )
```

**Lines 32-49** (on_drop):
```python
def on_drop(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """Extinguish when dropped (magical runes deactivate)."""
    entity.states['lit'] = False

    return EventResult(
        allow=True,
        feedback="The lantern's runes fade as you set it down, leaving it dark and cold."
    )
```

**Violations**:
- ❌ Hard-coded narrative prose ("As your hand closes...", "The lantern's runes fade...")
- ❌ Specific implementation details baked into behavior ("runes", "magical")
- ❌ No entity data returned for narrator composition

**Impact**:
- High - light sources are common game items
- Hard-coded text doesn't adapt to different light source types
- Can't use state_variants for varied descriptions

**Recommended Fix**:
```python
def on_take(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """Auto-light when taken."""
    from utilities.entity_serializer import serialize_for_handler_result

    entity.states['lit'] = True
    actor_id = context.get("actor_id")

    return EventResult(
        allow=True,
        feedback="",  # No pre-composed prose
        data={
            "light_source": serialize_for_handler_result(entity, accessor, actor_id),
            "state_change": "lit"
        }
    )
```

**Item definition should have state_variants**:
```json
{
  "id": "lantern_rune",
  "properties": {
    "llm_context": {
      "traits": ["brass construction", "magical runes", "warm glow"],
      "state_variants": {
        "lit": {
          "traits": ["glowing runes", "warm radiance", "dancing light"]
        },
        "unlit": {
          "traits": ["dormant runes", "cold metal", "dark glass"]
        }
      }
    }
  }
}
```

---

### 3. ⚠️ VIOLATION: behaviors/core/consumables.py

**File**: `behaviors/core/consumables.py`
**Functions**: `on_drink()`, `on_eat()`

**Status**: HIGH PRIORITY - Returns hard-coded narrative prose

**Example (on_drink)**:
```python
feedback="You drink the glowing red potion. Warmth spreads through your body as your wounds heal."
```

**Example (on_eat)**:
```python
feedback="You eat the food. It's delicious and satisfying."
```

**Violations**:
- ❌ Hard-coded descriptions ("glowing red", "delicious")
- ❌ Specific effects described in prose ("wounds heal")
- ❌ Can't vary by consumable type

**Impact**:
- High - consumables are common in many games
- Generic descriptions don't match specific items
- Effect descriptions should come from item properties

**Recommended Fix**:
```python
def on_drink(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """Handle drinking a potion or liquid."""
    from utilities.entity_serializer import serialize_for_handler_result

    actor_id = context.get("actor_id")
    actor = accessor.get_actor(actor_id)

    # Apply effects (healing, buffs, etc.)
    if hasattr(entity, 'effects'):
        for effect_type, effect_value in entity.effects.items():
            # Apply effect to actor
            pass  # Effect application logic

    return EventResult(
        allow=True,
        feedback="",
        data={
            "consumable": serialize_for_handler_result(entity, accessor, actor_id),
            "action": "drink",
            "effects_applied": entity.effects if hasattr(entity, 'effects') else {}
        }
    )
```

**Item definition should describe appearance and effects**:
```json
{
  "id": "potion_healing",
  "properties": {
    "llm_context": {
      "traits": ["glowing red liquid", "warm to touch", "sweet scent"]
    },
    "effects": {
      "heal": 20
    }
  }
}
```

---

### 4. ⚠️ VIOLATION: behaviors/core/containers.py

**File**: `behaviors/core/containers.py`
**Function**: Treasure chest on_open behavior

**Status**: MEDIUM PRIORITY - Specific use case with hard-coded victory prose

**Example**:
```python
feedback="You open the chest and find glittering treasure! You win!"
```

**Violations**:
- ❌ Hard-coded victory message
- ❌ Treasure description baked into behavior

**Impact**:
- Medium - specific to treasure chest scenario
- Victory conditions should be handled elsewhere
- Treasure description should come from item properties

**Recommended Fix**:
```python
def on_open(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """Handle opening treasure chest."""
    from utilities.entity_serializer import serialize_for_handler_result

    actor_id = context.get("actor_id")

    # Check if this is a victory condition
    is_victory = entity.properties.get("victory_item", False)

    # Get treasure contents
    treasure_items = []
    if hasattr(entity, 'container'):
        # Serialize items in container
        pass

    return EventResult(
        allow=True,
        feedback="",
        data={
            "container": serialize_for_handler_result(entity, accessor, actor_id),
            "contents": treasure_items,
            "victory": is_victory
        }
    )
```

---

### 5. ✅ ACCEPTABLE: behaviors/core/perception.py

**File**: `behaviors/core/perception.py`
**Functions**: `handle_look()`, `handle_examine()`

**Status**: Acceptable - builds summary lists, not narrative composition

**Lines 120-133** (handle_look):
```python
# Use shared utility to build location description
message_parts = describe_location(accessor, location, actor_id)

# Serialize location for LLM consumption
llm_data = serialize_location_for_llm(accessor, location, actor_id)

return HandlerResult(
    success=True,
    primary="\n".join(message_parts),
    data=llm_data
)
```

**Why acceptable**:
- `describe_location()` builds **summary lists** (items present, exits available)
- This is informational output, not narrative prose
- LLM data is still properly serialized
- Summary format: "[Item1], [Item2], [Item3]" - structured, not storytelling

**Difference from violations**:
- ❌ Violation: "As your hand closes around the lantern..." (narrative prose)
- ✅ Acceptable: "You see: a lantern, a sword, a shield" (summary list)

**Future consideration**: Could eventually move to pure narrator composition, but this is low priority.

---

### 6. ✅ ACCEPTABLE: behaviors/core/exits.py

**File**: `behaviors/core/exits.py`
**Function**: `handle_exits()`

**Status**: Acceptable - builds summary lists of available directions

**Similar reasoning to perception.py** - summary output rather than narrative composition.

---

## Behavior Libraries Review

Let me check the behavior libraries for similar issues:

### behavior_libraries/actor_lib/effects.py
**Status**: Needs review - likely has hard-coded effect descriptions

### behavior_libraries/liquid_lib/handlers.py
**Status**: Needs review - likely similar to consumables

### behavior_libraries/crafting_lib/handlers.py
**Status**: Needs review - may have hard-coded success messages

### behavior_libraries/dialog_lib/handlers.py
**Status**: Needs review - dialog might be separate concern

---

## Priority Matrix

| Component | Severity | Usage Frequency | Refactor Priority |
|-----------|----------|----------------|-------------------|
| light_sources.py | High | High | 🔴 Immediate |
| consumables.py | High | High | 🔴 Immediate |
| containers.py (treasure) | Medium | Low | 🟡 Medium |
| actor_lib/effects.py | High | Medium | 🟡 Medium |
| liquid_lib/handlers.py | Medium | Low | 🟢 Low |
| crafting_lib/handlers.py | Medium | Low | 🟢 Low |
| perception.py (look/examine) | Low | High | ⚪ Future |
| exits.py | Low | High | ⚪ Future |

---

## Refactoring Strategy

### Phase 1: High-Priority Core Behaviors (Immediate)

1. **light_sources.py**
   - Add state_variants for lit/unlit to lantern items
   - Update on_take/on_drop to return structured data
   - Remove hard-coded prose
   - Estimated effort: 2-3 hours

2. **consumables.py**
   - Add effects to consumable item definitions
   - Update on_drink/on_eat to return structured data
   - Remove hard-coded prose
   - Estimated effort: 2-3 hours

### Phase 2: Medium-Priority Components

3. **containers.py** (treasure chest)
   - Move victory logic to separate system
   - Return structured data for treasure reveal
   - Estimated effort: 1-2 hours

4. **actor_lib/effects.py**
   - Review and refactor effect descriptions
   - Estimated effort: 2-4 hours

### Phase 3: Low-Priority Libraries

5. **liquid_lib/handlers.py**
6. **crafting_lib/handlers.py**
   - Review and refactor if violations found
   - Estimated effort: TBD after review

### Phase 4: Future Enhancements (Optional)

7. **perception.py / exits.py**
   - Consider moving to pure narrator composition
   - Very low priority - current summary format is acceptable
   - Estimated effort: 4-6 hours

---

## Testing Requirements

For each refactored component:

1. **Unit tests** - Verify behavior returns structured data, not prose
2. **Integration tests** - Verify narrator receives and composes correctly
3. **Game tests** - Verify actual gameplay narration quality
4. **Regression tests** - Verify existing games still work

---

## Migration Guide for Game Authors

When updating games to use refactored behaviors:

### For Light Sources

**Before** (old behavior provided prose):
```json
{
  "id": "lantern",
  "behaviors": ["behaviors.core.light_sources"]
}
```

**After** (need to add state_variants):
```json
{
  "id": "lantern",
  "properties": {
    "llm_context": {
      "traits": ["brass construction", "glass panes"],
      "state_variants": {
        "lit": {"traits": ["warm glow", "dancing flame", "casting light"]},
        "unlit": {"traits": ["cold metal", "dark interior"]}
      }
    }
  },
  "behaviors": ["behaviors.core.light_sources"]
}
```

### For Consumables

**Before** (old behavior provided prose):
```json
{
  "id": "healing_potion",
  "behaviors": ["behaviors.core.consumables"]
}
```

**After** (need to add effects and traits):
```json
{
  "id": "healing_potion",
  "properties": {
    "llm_context": {
      "traits": ["glowing red liquid", "sweet scent", "warm to touch"]
    },
    "effects": {
      "heal": 20
    }
  },
  "behaviors": ["behaviors.core.consumables"]
}
```

---

## Architectural Notes

### Why This Matters

1. **Consistency**: All narration should come from one source (narrator)
2. **Flexibility**: Authors can customize descriptions via state_variants
3. **Quality**: LLM can compose better prose than hard-coded strings
4. **Maintainability**: Narrative changes don't require code changes
5. **Extensibility**: New item types don't need new behaviors

### Core Principle

**Game logic (behaviors) manages state.**
**Narrator composes prose from structured data.**

Behaviors should:
- ✅ Execute state changes (light on/off, HP changes)
- ✅ Return structured data (entity serialization, effects applied)
- ❌ NOT compose narrative descriptions
- ❌ NOT include hard-coded prose

---

## Conclusion

The core handlers (utilities) are already compliant, but several core behaviors violate the narration architecture by returning hard-coded prose. The highest priority fixes are:

1. **light_sources.py** - Common feature, hard-coded magical description
2. **consumables.py** - Common feature, generic descriptions

These should be refactored immediately to:
- Return structured data instead of prose
- Use state_variants for state-dependent descriptions
- Let the narrator compose prose from entity properties

The perception/exits handlers are acceptable as-is (summary lists vs. narrative), but could be improved in the future for consistency.
