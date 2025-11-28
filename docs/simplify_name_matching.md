# Design: Unified Name Matching with Vocabulary Synonyms

## Problem Statement

The vocabulary system correctly defines synonyms (e.g., `{"word": "stairs", "synonyms": ["staircase", "stairway", "steps"]}`), and the parser correctly normalizes input so that both "stairs" and "staircase" resolve to the same `WordEntry`. However, this synonym information is lost when matching player input against game world entities.

**Example failure**: In the Long Hallway, an exit named "spiral staircase" cannot be found with "examine stairs" because:
1. Parser returns `WordEntry(word="stairs", synonyms=["staircase", ...])`
2. Action dict receives only `action["object"] = "stairs"` (the canonical word)
3. `find_exit_by_name()` tries to match "stairs" against "spiral staircase" using string operations
4. Match fails because "stairs" ≠ "staircase"

## Goals

1. Enable all finders to match against vocabulary synonyms
2. Consolidate duplicate name-matching code into a single helper
3. Maintain uniform matching behavior across all entity types (items, doors, exits, actors)
4. Keep the solution simple and avoid over-engineering

## Design

### Core Helper Function

Add a `name_matches()` function to `utilities/utils.py`:

```python
from typing import Union
from src.word_entry import WordEntry

def name_matches(
    search_term: Union[WordEntry, str],
    target_name: str,
    match_in_phrase: bool = False
) -> bool:
    """
    Check if search_term matches target_name, considering synonyms.

    Args:
        search_term: WordEntry (with synonyms) or plain string
        target_name: The entity's name field to match against
        match_in_phrase: If True, also match if any search word appears
                        as a word within target_name (for multi-word names
                        like "spiral staircase")

    Returns:
        True if any form of search_term matches target_name
    """
    # Extract all words to check (canonical + synonyms)
    if isinstance(search_term, WordEntry):
        match_words = [search_term.word] + search_term.synonyms
    else:
        match_words = [search_term]

    target_lower = target_name.lower()
    target_words = target_lower.split()

    for word in match_words:
        word_lower = word.lower()
        # Exact match (entire name)
        if target_lower == word_lower:
            return True
        # Word appears as complete word in multi-word name
        if match_in_phrase and word_lower in target_words:
            return True

    return False
```

### Action Dict Change

Modify action construction to pass `WordEntry` instead of just the word string:

```python
# Before (text_game.py, llm_narrator.py, run_game.py)
action["object"] = result.direct_object.word

# After
action["object"] = result.direct_object  # Full WordEntry
```

Similarly for `indirect_object` and `adjective`.

### Handler Changes

Handlers that extract object names will receive `WordEntry` objects:

```python
# Before
object_name = action.get("object")  # str
item = find_accessible_item(accessor, object_name, actor_id)

# After
object_name = action.get("object")  # WordEntry or str
item = find_accessible_item(accessor, object_name, actor_id)
```

### Finder Changes

Each finder will use `name_matches()` instead of inline string comparison:

```python
# Before (repeated in every finder)
name_lower = name.lower()
if item.name.lower() == name_lower:

# After
if name_matches(name, item.name):
```

For exits and other entities with multi-word names:
```python
if name_matches(name, exit_desc.name, match_in_phrase=True):
```

## Code Consolidation Opportunities

### 1. Finders in `utilities/utils.py`

| Function | Current Pattern | After |
|----------|----------------|-------|
| `find_accessible_item` (lines 143, 149, 175) | `item.name.lower() == name_lower` | `name_matches(name, item.name)` |
| `find_item_in_inventory` (line 224) | `item.name.lower() == name.lower()` | `name_matches(name, item.name)` |
| `find_container_by_name` (line 247) | `item.name.lower() == name.lower()` | `name_matches(name, item.name)` |
| `find_container_with_adjective` (line 456) | `item.name.lower() != name_lower` | `not name_matches(name, item.name)` |
| `find_item_in_container` (line 502) | `item.name.lower() == name_lower` | `name_matches(name, item.name)` |
| `find_door_with_adjective` (line 569) | `name_lower in item.name.lower()` | `name_matches(name, item.name, match_in_phrase=True)` |
| `find_exit_by_name` (lines 888-897) | Multiple checks | `name_matches(name, exit_desc.name, match_in_phrase=True)` |

### 2. Behavior Handlers

| File | Function | Current Pattern |
|------|----------|----------------|
| `behaviors/core/combat.py:83` | `handle_attack` | `actor.name.lower() == target_name.lower()` |
| `behaviors/core/manipulation.py:141` | `handle_take` | `item.name.lower() == container_name.lower()` |
| `behaviors/core/manipulation.py:388` | `handle_give` | `other_actor.name.lower() == recipient_name.lower()` |
| `behaviors/core/manipulation.py:504` | `handle_put` | `i.name.lower() == container_name.lower()` |

### 3. Action Construction Sites

These files construct action dicts and need to pass `WordEntry` instead of `.word`:

| File | Line | Field |
|------|------|-------|
| `src/text_game.py` | 34 | `action["object"]` |
| `src/text_game.py` | 40 | `action["indirect_object"]` |
| `src/llm_narrator.py` | 47 | `action["object"]` |
| `src/llm_narrator.py` | 53 | `action["indirect_object"]` |
| `examples/extended_game/run_game.py` | 46 | `action["object"]` |
| `examples/extended_game/run_game.py` | 52 | `action["indirect_object"]` |

### 4. Handlers Receiving Object Names

These handlers use `action.get("object")` and pass to finders (no code change needed if finders accept WordEntry):

- `behaviors/core/perception.py:125` - `handle_examine`
- `behaviors/core/manipulation.py:104` - `handle_take`
- `behaviors/core/manipulation.py:252` - `handle_drop`
- `behaviors/core/manipulation.py:345` - `handle_give`
- `behaviors/core/manipulation.py:462` - `handle_put`
- `behaviors/core/interaction.py:135` - `handle_open`
- `behaviors/core/interaction.py:286` - `handle_close`
- `behaviors/core/interaction.py:407` - `handle_use`
- `behaviors/core/interaction.py:457` - `handle_read`
- `behaviors/core/interaction.py:520` - `handle_climb`
- `behaviors/core/interaction.py:577` - `handle_pull`
- `behaviors/core/interaction.py:627` - `handle_push`
- `behaviors/core/locks.py:71` - `handle_unlock`
- `behaviors/core/locks.py:253` - `handle_lock`
- `behaviors/core/combat.py:55` - `handle_attack`
- `behaviors/core/consumables.py:64` - `handle_eat`
- `behaviors/core/consumables.py:125` - `handle_drink`

### 5. Eliminated Code

The `name_matches()` helper eliminates:
- 7+ instances of `name_lower = name.lower()` variable declarations
- 10+ instances of `x.lower() == y.lower()` comparisons
- Complex multi-check logic in `find_exit_by_name` (lines 888-897)
- Inconsistent matching behavior between different finders

## Testing Strategy

### Phase 1: Unit Tests for `name_matches()`

Create `tests/test_name_matching.py`:

```python
class TestNameMatches(unittest.TestCase):
    def test_exact_match_string(self):
        """Plain string exact match."""
        self.assertTrue(name_matches("sword", "sword"))
        self.assertTrue(name_matches("Sword", "sword"))  # case insensitive

    def test_exact_match_word_entry(self):
        """WordEntry canonical word exact match."""
        entry = WordEntry(word="stairs", word_type=WordType.NOUN,
                         synonyms=["staircase", "steps"])
        self.assertTrue(name_matches(entry, "stairs"))

    def test_synonym_match(self):
        """WordEntry synonym matches target."""
        entry = WordEntry(word="stairs", word_type=WordType.NOUN,
                         synonyms=["staircase", "steps"])
        self.assertTrue(name_matches(entry, "staircase"))
        self.assertTrue(name_matches(entry, "steps"))

    def test_phrase_match_disabled(self):
        """Without match_in_phrase, word in phrase doesn't match."""
        entry = WordEntry(word="stairs", word_type=WordType.NOUN,
                         synonyms=["staircase"])
        self.assertFalse(name_matches(entry, "spiral staircase"))

    def test_phrase_match_enabled(self):
        """With match_in_phrase, synonym matches word in phrase."""
        entry = WordEntry(word="stairs", word_type=WordType.NOUN,
                         synonyms=["staircase"])
        self.assertTrue(name_matches(entry, "spiral staircase",
                                     match_in_phrase=True))

    def test_no_match(self):
        """Non-matching cases return False."""
        entry = WordEntry(word="sword", word_type=WordType.NOUN,
                         synonyms=["blade"])
        self.assertFalse(name_matches(entry, "key"))
        self.assertFalse(name_matches(entry, "staircase"))
```

### Phase 2: Integration Tests for Finders

Add tests to existing finder test files verifying synonym matching:

```python
class TestFindAccessibleItemWithSynonyms(unittest.TestCase):
    def test_find_by_synonym(self):
        """Item can be found using vocabulary synonym."""
        # Create item named "staircase"
        # Search with WordEntry(word="stairs", synonyms=["staircase"])
        # Should find the item
```

### Phase 3: End-to-End Tests

Add to `tests/test_examine_exits.py`:

```python
class TestExamineExitWithSynonyms(unittest.TestCase):
    def test_examine_stairs_finds_staircase(self):
        """'examine stairs' finds exit named 'spiral staircase'."""
        # Uses full game flow with parser
```

### Phase 4: Regression Tests

Run full test suite to ensure no regressions:
- All existing finder tests pass
- All examine/take/drop tests pass
- All door/lock tests pass

## Implementation Phases

### Phase 1: Add Helper Function
1. Add `name_matches()` to `utilities/utils.py`
2. Add unit tests for `name_matches()`
3. Verify tests pass

**Progress**: COMPLETE
- Added `name_matches()` function to `utilities/utils.py` (lines 16-67)
- Created `tests/test_name_matching.py` with 24 comprehensive tests
- All tests pass

### Phase 2: Update Finders
1. Update all finders in `utilities/utils.py` to use `name_matches()`
2. Update type hints to accept `Union[WordEntry, str]`
3. Run finder tests

**Progress**: COMPLETE
- Updated 7 finder functions to use `name_matches()`:
  - `find_accessible_item` (3 call sites)
  - `find_item_in_inventory`
  - `find_container_by_name`
  - `find_container_with_adjective`
  - `find_item_in_container`
  - `find_door_with_adjective` (uses `match_in_phrase=True`)
  - `find_exit_by_name` (uses `match_in_phrase=True`)
- Fixed 8 tests that were passing compound phrases like "iron door" instead of
  properly structured action dicts with `adjective: "iron", object: "door"`
- All 985 tests pass

### Phase 3: Update Action Construction
1. Modify `text_game.py` to pass `WordEntry` objects
2. Modify `llm_narrator.py` similarly
3. Modify `examples/extended_game/run_game.py` similarly

**Progress**: COMPLETE
- Updated `parsed_to_json()` in all three files to pass full WordEntry
  objects for `object` and `indirect_object` fields
- Verbs, directions, and adjectives still use `.word` since they don't
  need synonym matching
- All 985 tests pass

### Phase 4: Update Behavior Handlers
1. Update handlers in `behaviors/core/` that do direct name comparison
2. Run full test suite

**Progress**: COMPLETE
- Updated `behaviors/core/combat.py`:
  - Added import for `name_matches`
  - Updated target actor search to use `name_matches(target_name, actor.name)`
- Updated `behaviors/core/manipulation.py`:
  - Added import for `name_matches`
  - Updated 3 direct comparisons to use `name_matches()`
- All 985 tests pass

### Phase 5: End-to-End Verification
1. Add integration test for "examine stairs" finding "spiral staircase"
2. Manual testing of common synonym cases
3. Verify LLM protocol still works (WordEntry in action dict)

**Progress**: COMPLETE
- Added `TestExitSynonymMatching` class with 5 new tests in `tests/test_examine_exits.py`:
  - `test_find_exit_with_synonym_staircase_matches_stairs`
  - `test_find_exit_with_synonym_steps_matches_stairs`
  - `test_examine_with_synonym_finds_exit` (the key end-to-end test)
  - `test_plain_string_still_works`
  - `test_plain_string_stairs_without_wordentry_fails`
- All 990 tests pass (985 original + 5 new)
- The original bug is fixed: "examine stairs" now finds "spiral staircase"

## Implementation Summary

**Total changes:**
- Added `name_matches()` helper function (52 lines)
- Updated 7 finder functions to use `name_matches()`
- Updated 3 action construction sites to pass `WordEntry`
- Updated 4 direct name comparisons in behavior handlers
- Added 24 unit tests for `name_matches()`
- Added 5 integration tests for synonym matching
- Fixed 8 tests to use proper action dict structure
- Net code reduction of ~15 lines of duplicate matching logic

## Risks and Mitigations

### Risk: WordEntry in Action Dict Breaks LLM Protocol
The action dict is passed to the LLM for narration context. If it contains `WordEntry` objects instead of strings, JSON serialization may fail.

**Mitigation**: The LLM protocol can extract `.word` from WordEntry when building context, or action dict can include both `object` (WordEntry) and `object_word` (string) during transition.

### Risk: Test Fixtures Use Strings
Many tests construct action dicts with plain strings.

**Mitigation**: `name_matches()` accepts both `WordEntry` and `str`, so existing tests continue to work. Finders will also accept both types.

## Success Criteria

1. "examine stairs" successfully finds exit named "spiral staircase"
2. All vocabulary synonyms work for finding entities
3. Code consolidation: ~15 fewer lines of duplicate matching logic
4. All existing tests pass
5. Consistent matching behavior across all entity types
