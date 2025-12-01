# Cleanup and Trait Randomization

## Issue Reference
GitHub Issue #15: Randomize trait lists when passing to narrator

## Problem Statement

### Narration Diversity
Currently, entities have ~25 traits in `llm_context.traits`. These are passed verbatim to the narrator LLM, which tends to pick from the same positions (likely the beginning), leading to repetitive narration even with rich trait data.

### Code Duplication
Four `_*_to_dict` methods in `llm_protocol.py` share common logic for adding `llm_context`:
- `_entity_to_dict()` - items
- `_door_to_dict()` - doors
- `_location_to_dict()` - locations
- `_actor_to_dict()` - actors

Additionally, `_query_location()` handles exit `llm_context` inline.

## Solution

### 1. Extract Common Helper

Create `_add_llm_context(result: Dict, entity) -> None` that:
- Checks if entity has `properties.llm_context`
- If traits list exists, creates a shuffled copy
- Adds the (potentially shuffled) llm_context to result dict

```python
def _add_llm_context(self, result: Dict, properties: Dict) -> None:
    """Add llm_context to result dict, randomizing traits for narration variety."""
    llm_context = properties.get('llm_context')
    if not llm_context:
        return

    # Make a copy to avoid mutating original
    context_copy = dict(llm_context)

    # Shuffle traits if present
    if 'traits' in context_copy and isinstance(context_copy['traits'], list):
        traits_copy = list(context_copy['traits'])
        random.shuffle(traits_copy)
        context_copy['traits'] = traits_copy

    result['llm_context'] = context_copy
```

### 2. Refactor _*_to_dict Methods

Each method calls the helper instead of duplicating llm_context logic:

```python
def _location_to_dict(self, loc) -> Dict:
    result = {
        "id": loc.id,
        "name": loc.name,
        "description": loc.description
    }
    self._add_llm_context(result, loc.properties)
    return result
```

### 3. Handle Exit llm_context

In `_query_location()`, apply the same randomization when building exit data:

```python
if exit_desc.llm_context:
    exits[direction]["llm_context"] = self._randomize_llm_context(exit_desc.llm_context)
```

### 4. Update Narrator Prompt

Add guidance to select traits from different aspects:
- Different sensory modes (visual, auditory, olfactory, tactile)
- Different commentary types (physical details, atmosphere, evidence of events)

## Testing

### Unit Tests for Randomization

```python
class TestTraitRandomization(unittest.TestCase):

    def test_traits_are_shuffled(self):
        """Verify traits list is shuffled (not in original order)."""
        # Run multiple times to ensure randomization occurs

    def test_original_traits_not_mutated(self):
        """Verify original entity traits are not modified."""

    def test_state_variants_preserved(self):
        """Verify state_variants are included unchanged."""

    def test_no_llm_context_handled(self):
        """Verify entities without llm_context work correctly."""
```

### Integration Tests

Verify that location queries, examine commands, etc. still return valid llm_context with shuffled traits.

## Files Modified

- `src/llm_protocol.py` - Add helper, refactor _*_to_dict methods
- `examples/narrator_prompt.txt` - Add trait diversity guidance
- `tests/llm_interaction/test_json_protocol.py` - Add randomization tests

---

## Work Completed

### Implementation Summary

1. **Added `_add_llm_context` helper method** to `LLMProtocolHandler` in [llm_protocol.py](../src/llm_protocol.py#L592-L611)
   - Extracts common llm_context handling logic
   - Shuffles traits list using `random.shuffle()` on a copy
   - Preserves original traits in game state (no mutation)
   - Preserves `state_variants` and other llm_context fields unchanged

2. **Refactored all `_*_to_dict` methods** to use the helper:
   - `_entity_to_dict()` - items
   - `_door_to_dict()` - doors
   - `_location_to_dict()` - locations
   - `_actor_to_dict()` - actors
   - Reduced code duplication across 4 methods

3. **Applied randomization to exit llm_context** in `_query_location()` method

4. **Updated narrator prompt** ([narrator_prompt.txt](../examples/narrator_prompt.txt#L27-L30)) with guidance for trait diversity:
   - Different senses: visual details, sounds, smells, textures
   - Different focus areas: architecture, atmosphere, signs of inhabitants, evidence of past events
   - Different scales: overall impression, specific details, small touches

5. **Added comprehensive test suite** `TestTraitRandomization` with 8 tests:
   - `test_traits_are_shuffled` - verifies randomization occurs
   - `test_original_traits_not_mutated` - verifies no mutation of source data
   - `test_state_variants_preserved` - verifies other llm_context fields unchanged
   - `test_no_llm_context_handled` - verifies entities without llm_context work
   - `test_empty_traits_handled` - verifies empty traits list works
   - `test_llm_context_without_traits_preserved` - verifies llm_context without traits key works
   - `test_exit_traits_randomized` - verifies exit traits are also randomized
   - `test_all_traits_present_after_shuffle` - verifies no traits lost during shuffle

### Test Results

All 73 tests in `test_json_protocol.py` pass, including the 8 new randomization tests.
