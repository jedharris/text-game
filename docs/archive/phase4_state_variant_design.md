# Phase 4: State Variant Selection Design

**Date**: 2025-12-30
**Status**: Design Review

## Overview

Design for Context Builder to select location `state_variants` based on game state (quest flags, environmental spreads, visit history).

## Key Principle

**Context Builder makes ALL selection decisions.** Narration Model receives only the selected variant and generates prose.

## Data Sources

### 1. Location Properties (set by environmental spreads)
```python
location.properties = {
    "infection_present": true,  # Set by spore spread at milestone
    "spore_level": "low",       # Set by spore spread progression
    "temperature": "freezing"   # Set by cold spread (future)
}
```

### 2. Global Flags (set by quest completion)
```python
state.extra.flags = {
    "telescope_repaired": true,
    "spore_mother_healed": true,
    "water_receding": true,
    "guardian_active": true
}
```

### 3. Visit History (tracked per player)
```python
state.extra.visit_history = {
    "player": ["nexus_chamber", "town_gate", "market_square"]
}
```

## Selection Priority

**Priority 1: Location Properties** (highest)
- Checks: `location.properties[key]` matches variant key
- Reason: Environmental effects are immediate and visible
- Example: If `infection_present=true`, use "infection_present" variant

**Priority 2: Global Quest Flags**
- Checks: `state.extra.flags[key]` is true
- Reason: Quest completion changes world state
- Example: If `telescope_repaired=true`, use "telescope_repaired" variant

**Priority 3: Visit History**
- Checks: `location.id` in `visit_history[actor_id]`
- Variants: "first_visit" vs "revisit"
- Reason: Player familiarity affects description

**Priority 4: None** (fallback)
- No state_variant selected
- Use base traits + atmosphere only

## Selection Algorithm

```python
def _select_state_variant(
    llm_context: Dict[str, Any],
    location: Location,
    world_state: Dict[str, Any],
    actor_id: ActorId
) -> Optional[str]:
    """Select best matching state_variant based on world state.

    Args:
        llm_context: Location's llm_context with state_variants
        location: Location entity
        world_state: state.extra dict with flags, visit_history, etc.
        actor_id: Current actor for visit history

    Returns:
        Selected variant text or None
    """
    variants = llm_context.get('state_variants', {})
    if not variants:
        return None

    # Priority 1: Location properties (environmental spreads)
    location_props = location.properties if hasattr(location, 'properties') else {}

    # Check specific property keys
    for prop_key in ['infection_present', 'spore_level', 'temperature', 'flooded']:
        prop_value = location_props.get(prop_key)
        if prop_value:
            # For boolean: check if variant key exists
            if isinstance(prop_value, bool) and prop_value and prop_key in variants:
                return variants[prop_key]
            # For string: check if value matches a variant key
            if isinstance(prop_value, str) and prop_value in variants:
                return variants[prop_value]

    # Priority 2: Global quest flags
    flags = world_state.get('flags', {})

    # Define quest flag priority order (most specific first)
    quest_flags = [
        'telescope_repaired',
        'guardian_active',
        'water_receding',
        'spore_mother_healed',
        'golems_activated',
        'golems_commanded'
    ]

    for flag_name in quest_flags:
        if flags.get(flag_name) and flag_name in variants:
            return variants[flag_name]

    # Priority 3: Visit history
    visit_history = world_state.get('visit_history', {})
    actor_visits = visit_history.get(str(actor_id), [])

    if location.id not in actor_visits and 'first_visit' in variants:
        return variants['first_visit']

    if 'revisit' in variants:
        return variants['revisit']

    # Priority 4: No variant
    return None
```

## Integration Points

### 1. Visit History Tracking

Add visit tracking to movement system:

```python
# In movement handler or turn processing
def track_visit(state: GameState, actor_id: ActorId, location_id: LocationId):
    """Track that actor visited a location."""
    if 'visit_history' not in state.extra:
        state.extra['visit_history'] = {}

    actor_key = str(actor_id)
    if actor_key not in state.extra['visit_history']:
        state.extra['visit_history'][actor_key] = []

    if location_id not in state.extra['visit_history'][actor_key]:
        state.extra['visit_history'][actor_key].append(location_id)
```

### 2. Context Builder Enhancement

Modify `serialize_location_for_llm()`:

```python
def serialize_location_for_llm(
    accessor,
    location,
    actor_id: ActorId
) -> Dict[str, Any]:
    """Serialize location with state-aware variant selection."""

    result: Dict[str, Any] = {}

    # ... existing player_context code ...

    # Serialize location
    location_dict = entity_to_dict(location)

    # NEW: Select state variant based on world state
    if 'llm_context' in location_dict:
        state = accessor.game_state
        state_note = _select_state_variant(
            location_dict['llm_context'],
            location,
            state.extra,
            actor_id
        )

        if state_note:
            location_dict['state_note'] = state_note

        # Remove state_variants from output (like perspective_variants)
        location_dict['llm_context'].pop('state_variants', None)

    result["location"] = location_dict

    # ... rest of existing code ...
```

### 3. NPC State Variants (Future Enhancement)

Similar pattern could apply to NPC state variants based on NPC state machines:

```python
# In entity_serializer.py for actors
if actor.properties.get('state_machine'):
    current_state = get_current_state(actor.properties['state_machine'])
    # Could use state_fragments[current_state] as "state_note"
    # This already works via existing state_fragments selection
```

## Testing Strategy

### Unit Tests

```python
def test_state_variant_selection_priority():
    """Test that location properties override flags."""
    # Setup location with infection_present property
    # Setup flags with telescope_repaired
    # Verify infection_present variant is selected (higher priority)

def test_visit_history_first_vs_revisit():
    """Test first_visit vs revisit selection."""
    # Setup location with both variants
    # Test with empty visit history → first_visit
    # Test with location in history → revisit

def test_environmental_spread_integration():
    """Test that spread-set properties trigger variants."""
    # Setup spread that sets infection_present
    # Run to milestone
    # Verify location gets infection_present variant
```

### Integration Tests

```python
def test_spore_spread_narration():
    """Test that spore spread changes location narration."""
    # Visit market_square before turn 150 → normal
    # Advance to turn 150 (spread milestone)
    # Visit market_square again → infection variant

def test_quest_completion_narration():
    """Test that quest flags change narration."""
    # Visit observatory before telescope repair → broken variant
    # Repair telescope (sets flag)
    # Visit observatory again → repaired variant
```

### Walkthrough Tests

```
# Test environmental spread narration
go to market square
> "The abandoned marketplace, forever frozen in flight."

advance turns 150

go to town gate
go to market square
> "Sickly bioluminescent fungi sprout from cracks in cobblestones..."

# Test quest flag narration
go to nexus
go north
go to observatory platform
> "The empty telescope mount and celestial charts suggest..."

repair telescope with lens and bracket

go to observatory platform
> "The restored telescope gleams in its mount, ready to pierce..."
```

## Risks & Mitigations

**Risk 1**: Performance impact of checking many properties/flags
- **Mitigation**: Selection is O(n) where n is small (~10 checks), negligible
- **Mitigation**: Only runs once per location visit, not per action

**Risk 2**: Conflicting variants (multiple conditions true)
- **Mitigation**: Clear priority order documented and enforced
- **Mitigation**: Most specific conditions checked first

**Risk 3**: Authors forget to update both spread config and variants
- **Mitigation**: Validation pass in Phase 5 checks variant keys match spread property names
- **Mitigation**: Documentation clearly maps spread properties → variant keys

**Risk 4**: Visit history grows unbounded
- **Mitigation**: Only stores location IDs (small strings), not full state
- **Mitigation**: Could add max size limit or prune old visits if needed (future)

## Open Questions

1. **Visit history persistence**: Should visit_history be saved in save files?
   - **Answer**: Yes - it's part of player progress, should persist across sessions

2. **Multiple actors**: Do we track visit history per actor or just player?
   - **Answer**: Per actor for generality, but initially only player uses it

3. **Variant authoring guidelines**: How do we ensure authors create compatible variants?
   - **Answer**: Phase 5 validation, plus documentation of common patterns

## Success Criteria

- [ ] Context Builder selects variants based on location properties
- [ ] Context Builder selects variants based on quest flags
- [ ] Context Builder tracks and uses visit history
- [ ] Environmental spreads trigger narration changes
- [ ] Quest completion triggers narration changes
- [ ] All tests pass
- [ ] Walkthrough demonstrates working system

## Next Steps

1. Implement `_select_state_variant()` in new module
2. Add visit history tracking
3. Enhance `serialize_location_for_llm()`
4. Write unit tests
5. Write integration tests
6. Create walkthrough
7. Verify with environmental spreads
