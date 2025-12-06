# Automatic Multi-Type Vocabulary Design

## Use Cases and Goals

### Primary Use Case
Automatically handle vocabulary conflicts when the same word appears with different grammatical types from multiple sources (game state extraction, behavior modules, base vocabulary).

**Example**: The word "stand" appears as:
- NOUN (extracted from game items: "umbrella stand", "silver stand")
- VERB (defined in stand_sit.py behavior: "stand on bench")

Currently, the first definition wins and the second is silently skipped, causing parser failures.

### Goal
When the same word is defined with different types, automatically merge them into a multi-type word entry that the parser can disambiguate based on grammatical context.

## Current State

### Multi-Type Support Already Exists
The parser and WordEntry already support multi-type words:
- `WordEntry.word_type` can be `WordType` or `Set[WordType]`
- Parser's `_parse_word_type()` handles both single and list formats
- Directions already work as multi-type: `{"word": "north", "word_type": ["noun", "adjective"]}`

### The Problem: Vocabulary Merging
The vocabulary merge in **behavior_manager.py:303-357** (`get_merged_vocabulary()`) skips duplicate words instead of merging types.

**Note**: The base vocabulary (src/vocabulary.json) is empty except for prepositions and articles, so no conflicts occur in vocabulary_generator.py. All conflicts happen when behavior vocabularies are merged with game-state-extracted nouns.

### Current Manual Multi-Type Words
- **Directions** (10 words): north, south, east, west, up, down, northeast, northwest, southeast, southwest
  - Defined in `behaviors/core/exits.py:58-67` as `["noun", "adjective"]`
- **"stand"** in `examples/spatial_game/behaviors/lib/spatial/stand_sit.py:17` as `["verb", "noun"]`
- **"open"** in `behaviors/core/interaction.py:21` as `["verb", "adjective"]`

## Design

### Approach: Automatic Multi-Type Detection
Remove all manual `word_type: ["type1", "type2"]` markup from vocabulary definitions. Instead, detect and merge types automatically during vocabulary merging.

### Changes Required

#### Update `behavior_manager.py::get_merged_vocabulary()`
Detect conflicts and merge types instead of skipping duplicates.

```python
def get_merged_vocabulary(self, base_vocab: Dict) -> Dict:
    """
    Merge base vocabulary with vocabulary from all loaded modules.

    Automatically creates multi-type entries when the same word appears
    with different types from different modules.
    """
    # Build word -> entry map
    word_map = {}

    # Add base vocab
    for section in ["verbs", "nouns", "adjectives", "directions"]:
        for entry in base_vocab.get(section, []):
            word = entry["word"]
            word_map[word] = entry.copy()

    # Merge module vocabularies
    for module in self._modules.values():
        if not hasattr(module, 'vocabulary') or not module.vocabulary:
            continue
        ext = module.vocabulary

        for section in ["verbs", "nouns", "adjectives", "directions"]:
            for entry in ext.get(section, []):
                word = entry["word"]
                if word in word_map:
                    # Merge types
                    existing_type = word_map[word].get("word_type", _section_to_type(section))
                    new_type = entry.get("word_type", _section_to_type(section))
                    word_map[word]["word_type"] = _merge_types(existing_type, new_type)
                else:
                    word_map[word] = entry.copy()

    return _rebuild_vocab_from_map(word_map)
```

#### 3. Helper Functions
```python
def _section_to_type(section: str) -> str:
    """Map vocabulary section name to type string."""
    mapping = {
        "verbs": "verb",
        "nouns": "noun",
        "adjectives": "adjective",
        "directions": "noun"  # directions are nouns by default
    }
    return mapping.get(section, "noun")

def _merge_types(type1, type2) -> list:
    """
    Merge two word_type values into a multi-type list.

    Args:
        type1, type2: Can be strings or lists

    Returns:
        Sorted list of unique types
    """
    types = set()

    # Add type1
    if isinstance(type1, list):
        types.update(type1)
    elif type1:
        types.add(type1)

    # Add type2
    if isinstance(type2, list):
        types.update(type2)
    elif type2:
        types.add(type2)

    return sorted(list(types))  # Sorted for deterministic output

def _rebuild_vocab_from_map(word_map: Dict) -> Dict:
    """
    Rebuild vocabulary dict from word map.

    Places each entry in the appropriate section based on its primary type
    (first type if multi-type).
    """
    vocab = {
        "verbs": [],
        "nouns": [],
        "adjectives": [],
        "directions": [],
        "prepositions": [],
        "articles": []
    }

    for word, entry in word_map.items():
        word_type = entry.get("word_type")

        # Determine primary section
        if isinstance(word_type, list):
            primary_type = word_type[0]  # First type is primary
        else:
            primary_type = word_type

        # Map type to section
        if primary_type == "verb":
            vocab["verbs"].append(entry)
        elif primary_type == "noun":
            vocab["nouns"].append(entry)
        elif primary_type == "adjective":
            vocab["adjectives"].append(entry)
        # directions stay in nouns section

    return vocab
```

#### 4. Remove Manual Multi-Type Markup
Clean up vocabulary definitions to remove explicit multi-type markup:

**Files to update:**
- `behaviors/core/exits.py` - Remove `word_type: ["noun", "adjective"]` from 10 directions
- `behaviors/core/interaction.py` - Remove `word_type: ["verb", "adjective"]` from "open"
- `examples/spatial_game/behaviors/lib/spatial/stand_sit.py` - Remove `word_type: ["verb", "noun"]` from "stand"

All will become single-type definitions and will be automatically merged to multi-type when conflicts occur.

## Properties Merging Strategy

When the same word appears with different properties, use this priority:
1. **word_type**: Always merge (combine all types)
2. **synonyms**: Union of all synonyms
3. **event**: Keep first (verbs)
4. **object_required**: Keep first (verbs)
5. **llm_context**: Merge or keep first
6. **properties**: Merge dicts
7. **value**: Keep first

For simplicity in Phase 1, only merge `word_type` and `synonyms`. Other properties come from the first definition.

## Testing Strategy

### Test Cases
1. **Noun-Verb Conflict** (stand): Game state noun + behavior verb → multi-type
2. **Noun-Adjective Conflict** (north): Direction as both → multi-type
3. **Verb-Adjective Conflict** (open): Interactive verb + state adjective → multi-type
4. **No Conflict**: Single definition → stays single-type
5. **Triple Conflict**: Word defined as verb, noun, and adjective → multi-type with all three
6. **Parsing**: Multi-type words disambiguated by grammar pattern

### Test Files
- `tests/test_multi_type_merge.py` - Unit tests for merge functions
- `tests/test_stand_vocab.py` - Existing test for "stand" conflict (should pass after fix)
- `tests/command_parser/test_word_entry.py` - Parser handling of multi-type

## Implementation Plan

### Phase 1: Core Merge Logic (in behavior_manager.py)
1. Write test for `_merge_types()` helper
2. Implement `_merge_types()`
3. Write test for `_section_to_type()` helper
4. Implement `_section_to_type()`
5. Write test for `_rebuild_vocab_from_map()` helper
6. Implement `_rebuild_vocab_from_map()`

### Phase 2: Update behavior_manager.py
1. Write test for verb-verb merge (no conflict, first wins)
2. Write test for verb-noun merge (direction case)
3. Write test for verb-adjective merge (open case)
4. Write test for noun-verb merge ("stand" case - game state noun + behavior verb)
5. Refactor `get_merged_vocabulary()` to use word map approach
6. Verify tests pass

### Phase 3: Remove Manual Multi-Type Markup
1. Update `behaviors/core/exits.py` - Remove word_type arrays from directions
2. Update `behaviors/core/interaction.py` - Remove word_type array from "open"
3. Update `examples/spatial_game/behaviors/lib/spatial/stand_sit.py` - Remove word_type array from "stand"
4. Run all tests to verify automatic detection works

### Phase 4: Integration Testing
1. Run `python -m src.text_game examples/spatial_game`
2. Test "stand on bench" command (currently fails, should now work)
3. Test "north" (should still work as direction)
4. Test "open door" (should still work)
5. Test "sit on chair" (should still work)

## Success Criteria
- "stand on bench" works in text-game mode
- All existing multi-type words continue working
- No manual word_type arrays needed in vocabulary
- All tests pass

## Backward Compatibility
✅ Full backward compatibility maintained:
- Parser already handles multi-type words
- Single-type words continue working unchanged
- Multi-type only created when conflicts detected
