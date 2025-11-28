# Exit LLM Context Support

## Overview

This document describes adding optional `llm_context` support to exits, allowing authors to provide descriptive traits and state variants for open passages, not just doors.

## Goals

1. Allow authors to describe open exits (passages, stairs, archways) with the same richness as doors and items
2. For door exits, support merging exit-level traits with door-level traits
3. Maintain full backward compatibility - existing game files work unchanged

## Design

### Exit llm_context Structure

Exits can have an optional `llm_context` field in their properties, following the same structure as items and doors:

```json
{
  "up": {
    "type": "open",
    "to": "loc_tower",
    "llm_context": {
      "traits": [
        "worn stone steps",
        "spiraling upward",
        "narrow passage",
        "cold draft from above"
      ],
      "state_variants": {
        "first_visit": "The stairs beckon upward into darkness.",
        "revisit": "The familiar winding staircase."
      }
    }
  }
}
```

### Trait Merging for Door Exits

When an exit has a door (`type: "door"` with `door_id`), the narrator can use traits from both sources:

1. **Exit traits**: Describe the passage/opening itself
2. **Door traits**: Describe the physical door object

Example in game state:
```json
{
  "east": {
    "type": "door",
    "to": "loc_treasure",
    "door_id": "door_treasure",
    "llm_context": {
      "traits": [
        "grand archway",
        "carved stone frame",
        "runes along lintel"
      ]
    }
  }
}
```

The door item (`door_treasure`) already has its own `llm_context` with door-specific traits. The LLM narrator can combine these for richer descriptions.

### Backward Compatibility

- The `llm_context` field is entirely optional
- Exits without `llm_context` work exactly as before
- Existing game files require no changes
- The narrator handles missing `llm_context` gracefully (uses door traits only, or no traits)

## Code Impact Analysis

### Files Requiring Changes

#### 1. `src/state_manager.py`

**Changes needed:**
- Add `llm_context` property accessor to `ExitDescriptor` class (similar to existing pattern on `Item` and `Location`)

```python
@dataclass
class ExitDescriptor:
    """Exit descriptor for location connections."""
    type: str  # "open" or "door"
    to: Optional[str] = None
    door_id: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: List[str] = field(default_factory=list)

    # ADD: property accessor
    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return self.properties.get("llm_context")

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value
```

**Impact:** Minimal - adds convenience accessor, no behavioral change

#### 2. `src/llm_protocol.py`

**Changes needed:**
- Update `_query_location()` to include exit `llm_context` in response
- Add helper method to merge exit and door traits when building location query response

In `_query_location()`, modify the exits section:
```python
if "exits" in include or not include:
    exits = {}
    for direction, exit_desc in visible_exits.items():
        exit_data = {
            "type": exit_desc.type,
            "to": exit_desc.to
        }
        if exit_desc.door_id:
            exit_data["door_id"] = exit_desc.door_id
        # ADD: Include llm_context if present
        if exit_desc.properties.get("llm_context"):
            exit_data["llm_context"] = exit_desc.properties["llm_context"]
        exits[direction] = exit_data
    data["exits"] = exits
```

**Impact:** Small - adds optional field to query response

#### 3. `src/validators.py`

**No changes required.** The existing validation handles `properties` on `ExitDescriptor` generically. No specific validation needed for `llm_context` structure (it's author-defined content).

#### 4. `src/state_accessor.py`

**No changes required.** Exit descriptors are accessed through locations, which already work with the property-based model.

### Files Not Requiring Changes

- `src/parser.py` - Parsing is unrelated to LLM context
- `src/text_game.py` - Text game doesn't use LLM context
- `src/llm_narrator.py` - Already handles `llm_context` generically in query results
- `src/llm_game.py` - No direct exit handling
- `behaviors/core/*.py` - Behaviors don't access exit `llm_context` directly

## Test Impact Analysis

### Existing Tests

The following test files reference `ExitDescriptor`:

| File | Impact | Reason |
|------|--------|--------|
| `tests/state_manager/test_simplified_models.py` | None | Tests `ExitDescriptor` with `properties` dict - already supports arbitrary properties including `llm_context` |
| `tests/state_manager/test_simplified_validators.py` | None | Validates structural references, not `llm_context` content |
| `tests/test_entity_unification.py` | None | Tests door/item unification, not exit descriptions |
| `tests/test_examine_doors.py` | None | Tests door examination, exit traits would be additive |
| `tests/test_phase6_utility_functions.py` | None | Tests utility functions, not exit content |
| `tests/test_phase12_interaction_locks.py` | None | Tests lock mechanics, not descriptions |

**All existing tests should pass unchanged.** The design is purely additive.

### New Tests Needed

Add tests to `tests/state_manager/test_simplified_models.py`:

```python
def test_exit_descriptor_with_llm_context(self):
    """ExitDescriptor can have llm_context in properties."""
    from src.state_manager import ExitDescriptor

    exit_desc = ExitDescriptor(
        type="open",
        to="loc_2",
        properties={
            "llm_context": {
                "traits": ["worn steps", "cold draft"],
                "state_variants": {
                    "first_visit": "Stairs lead upward."
                }
            }
        }
    )

    self.assertIsNotNone(exit_desc.llm_context)
    self.assertIn("worn steps", exit_desc.llm_context["traits"])

def test_exit_descriptor_llm_context_property_accessor(self):
    """ExitDescriptor llm_context property provides convenient access."""
    from src.state_manager import ExitDescriptor

    exit_desc = ExitDescriptor(type="open", to="loc_2")

    # Initially None
    self.assertIsNone(exit_desc.llm_context)

    # Can set via property
    exit_desc.llm_context = {"traits": ["narrow passage"]}
    self.assertEqual(exit_desc.llm_context["traits"], ["narrow passage"])

    # Stored in properties
    self.assertEqual(
        exit_desc.properties["llm_context"]["traits"],
        ["narrow passage"]
    )
```

Add tests to `tests/llm_interaction/test_json_protocol.py`:

```python
def test_location_query_includes_exit_llm_context(self):
    """Location query includes llm_context for exits that have it."""
    # Setup: Create state with exit that has llm_context
    # Query location
    # Verify exit data includes llm_context
    pass

def test_location_query_omits_exit_llm_context_when_missing(self):
    """Location query omits llm_context for exits without it."""
    # Setup: Create state with exit without llm_context
    # Query location
    # Verify exit data has no llm_context key
    pass
```

### Test Fixture Updates

Update `tests/llm_interaction/fixtures/test_game_state.json` to include one exit with `llm_context` for integration testing:

```json
{
  "exits": {
    "up": {
      "type": "open",
      "to": "loc_tower",
      "llm_context": {
        "traits": ["spiral staircase", "worn stone steps"],
        "state_variants": {
          "first_visit": "A winding stair leads upward."
        }
      }
    }
  }
}
```

## Implementation Order

1. Add `llm_context` property accessor to `ExitDescriptor` in `state_manager.py`
2. Add unit tests for the new property accessor
3. Update `_query_location()` in `llm_protocol.py` to include exit `llm_context`
4. Add integration tests for location query with exit `llm_context`
5. Update one test fixture with exit `llm_context` for integration testing
6. (Optional) Update example game files to demonstrate the feature

## Summary

This is a small, purely additive change that:
- Adds ~10 lines to `state_manager.py` (property accessor)
- Adds ~5 lines to `llm_protocol.py` (include in query response)
- Requires ~4 new test cases
- Updates 1 test fixture

Existing tests pass unchanged. Authors who don't want the additional descriptive capability simply don't add `llm_context` to their exits - the behavior is identical to current.

## Implementation Summary

**Completed:** All changes implemented and tested.

### Code Changes
- `src/state_manager.py`: Added `llm_context` property accessor to `ExitDescriptor` (lines 84-92)
- `src/llm_protocol.py`: Updated `_query_location()` to include exit `llm_context` in response (lines 310-312)

### Test Changes
- `tests/state_manager/test_simplified_models.py`: Added `test_exit_descriptor_with_llm_context` and `test_exit_descriptor_llm_context_property_accessor`
- `tests/llm_interaction/test_json_protocol.py`: Added `test_location_query_includes_exit_llm_context` and `test_location_query_omits_exit_llm_context_when_missing`

### Example Content
Added `llm_context` with 25 traits each to two exits in `examples/simple_game_state.json`:

1. **Stairs up** (doorless exit from Long Hallway to Tower Top):
   - Traits: spiral staircase carved from living rock, worn treads, iron handrail, moss, arrow slits, dripping water echo, lichen, spider webs, torch sconce holders, etc.
   - Atmosphere: "vertical, ancient, slightly vertiginous"
   - State variants for first visit, revisit, from tower, and carrying light

2. **East archway** (door exit from Long Hallway to Treasure Room):
   - Traits: grand archway, carved lintel, geometric patterns, runes of warding, gargoyle faces, prayer stones, brass fixtures, crystalline deposits, etc.
   - Atmosphere: "imposing, mysterious, guarded"
   - State variants for door locked/unlocked/open, first visit, and revisit

3. **South exit** left undescribed to demonstrate backward compatibility

### Test Results
All 930 tests pass. The implementation is purely additive with no breaking changes.

### GitHub Issue
Closes #18 "Give exits descriptions"
