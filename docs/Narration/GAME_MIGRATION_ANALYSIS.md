# Game Migration Analysis for Behavior Refactoring

This document analyzes all example games to determine migration requirements for the behavior refactoring described in issue #412.

## Executive Summary

**Games Affected**: 2 out of 7 example games use core behaviors that will be refactored
- ✅ **simple_game** - Uses light_sources, already has proper state_variants
- ✅ **fancy_game** - Uses light_sources, already has proper state_variants

**Games Not Affected**: 5 games don't use any core behaviors being refactored
- spatial_game
- extended_game
- layered_game
- big_game
- actor_interaction_test

**Migration Impact**: **MINIMAL** - Both affected games already have the required state_variants defined correctly.

---

## Behaviors Being Refactored

### 1. behaviors.core.light_sources
**Current behavior**: Returns hard-coded prose like "As your hand closes around the lantern, the runes flare to life..."

**New behavior**: Will return structured data, narrator composes from state_variants

**Required migration**: Items must have state_variants with "lit" and "unlit" keys

### 2. behaviors.core.consumables (Not used by any game)
**Current behavior**: Returns hard-coded prose like "You drink the glowing red potion..."

**New behavior**: Will return structured data with effects_applied

**Required migration**: Items need effects properties and traits

### 3. behaviors.core.containers (Not used by any game)
**Current behavior**: Returns hard-coded victory message

**New behavior**: Will return structured data with victory flag

**Required migration**: Treasure chests need proper item properties

---

## Game-by-Game Analysis

### ✅ simple_game - READY (No Migration Needed)

**Uses**: behaviors.core.light_sources

**Item**: item_lantern (lines 241-270)

**Current Configuration**:
```json
{
  "id": "item_lantern",
  "properties": {
    "type": "object",
    "portable": true,
    "provides_light": true,
    "states": {
      "lit": false
    }
  },
  "llm_context": {
    "traits": [
      "hexagonal",
      "hammered copper",
      "rough runes around cap",
      "door on side",
      "wire loop handle"
    ],
    "state_variants": {
      "unlit": "dark and silent",
      "lit": "sheds a helpful light",
      "examined": "crudely made but functional"
    }
  },
  "behaviors": [
    "behaviors.core.light_sources"
  ]
}
```

**Migration Status**: ✅ Already compliant
- Has required "lit" and "unlit" state_variants
- Has proper traits for narrator grounding
- Has states.lit property for behavior to toggle

**Testing Required**: Verify narration quality after behavior refactor

---

### ✅ fancy_game - READY (No Migration Needed)

**Uses**: behaviors.core.light_sources

**Item**: item_lantern (lines 371-420)

**Current Configuration**:
```json
{
  "id": "item_lantern",
  "properties": {
    "type": "object",
    "portable": true,
    "provides_light": true,
    "states": {
      "lit": false
    }
  },
  "llm_context": {
    "traits": [
      "hexagonal",
      "hammered copper",
      "rough runes around cap",
      "door on side",
      "wire loop handle",
      "glass panes clouded with age",
      "oil reservoir half full",
      "wick trimmed and ready",
      ... (25 total traits for rich description)
    ],
    "state_variants": {
      "unlit": "dark and silent",
      "lit": "sheds a helpful light",
      "examined": "crudely made but functional"
    }
  },
  "behaviors": [
    "behaviors.core.light_sources"
  ]
}
```

**Migration Status**: ✅ Already compliant
- Has required "lit" and "unlit" state_variants
- Has extensive traits for rich narrator grounding
- Has states.lit property for behavior to toggle

**Testing Required**: Verify narration quality after behavior refactor (especially given the extensive trait list)

---

### ✅ spatial_game - Not Affected

**Uses**: No core behaviors being refactored
- Uses custom behaviors (crystal_ball, magic_mat, magic_staircase)
- Already fully compliant with narration architecture (A+ grade)

**Migration Status**: None required

---

### ✅ extended_game - Not Affected

**Uses**: No behaviors.core.* modules

**Migration Status**: None required

---

### ✅ layered_game - Not Affected

**Uses**: No behaviors.core.* modules

**Migration Status**: None required

---

### ✅ big_game - Not Affected

**Uses**: No behaviors.core.* modules

**Migration Status**: None required

---

### ✅ actor_interaction_test - Not Affected

**Uses**: No behaviors.core.* modules

**Migration Status**: None required

---

## Migration Strategy

### Phase 1: Refactor Core Behaviors
1. Refactor behaviors/core/light_sources.py to return structured data
2. Refactor behaviors/core/consumables.py to return structured data
3. Refactor behaviors/core/containers.py to return structured data

### Phase 2: Test Affected Games
1. Test simple_game with refactored light_sources behavior
   - Take lantern (should trigger on_take)
   - Drop lantern (should trigger on_drop)
   - Verify narrator composes proper prose from state_variants
2. Test fancy_game with refactored light_sources behavior
   - Same testing as simple_game
   - Pay special attention to how narrator uses extensive trait list

### Phase 3: Update Documentation
1. Update authoring guide with behavior usage patterns
2. Add examples showing how to use state_variants with behaviors
3. Document migration guide for future game authors

---

## Risk Assessment

**Risk Level**: ⚪ Very Low

**Reasons**:
1. Only 2 games affected (simple_game, fancy_game)
2. Both games already have required state_variants configured correctly
3. No game state JSON changes needed
4. Only behavior code changes required
5. Changes improve narration quality and flexibility

**Potential Issues**:
1. Narrator might compose differently than current hard-coded prose
   - **Mitigation**: Test thoroughly and adjust narrator prompts if needed
2. State variant descriptions might not cover all edge cases
   - **Mitigation**: Both games have good coverage ("lit", "unlit", "examined")

**Testing Priority**:
- 🔴 High: simple_game (simpler trait list, baseline test)
- 🟡 Medium: fancy_game (extensive traits, narrator composition test)

---

## Recommended Workflow

Following CLAUDE.md Workflow A (small to moderate changes):

1. ✅ Create issue #412 (DONE)
2. Add comment to issue describing migration analysis (this document)
3. Refactor behaviors using TDD:
   - Start with light_sources.py (affects 2 games)
   - Then consumables.py (no games affected, but high priority)
   - Finally containers.py (no games affected, medium priority)
4. Test each game after refactoring
5. Document results in issue comment
6. Close issue

---

## Conclusion

**The migration impact is minimal because both affected games already have proper state_variants configured.** This suggests the games were authored with awareness of state-dependent narration patterns, even though the behaviors themselves weren't yet compliant.

The refactoring will:
- ✅ Improve consistency with narration architecture
- ✅ Enable future game authors to customize light source descriptions
- ✅ Remove hard-coded prose from behavior code
- ✅ Maintain or improve narration quality in existing games

**No game_state.json changes are required for any game.**
