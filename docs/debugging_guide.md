# Text Game Debugging Guide

This guide captures knowledge gained from debugging issues #246-250. It covers vocabulary, parsing, handlers, testing, and common pitfalls.

## Quick Reference

### Essential Commands

```bash
# Run all tests
python3 -m unittest discover -s tests -p "test_*.py"

# Run walkthrough (test commands without narrator)
python3 tools/walkthrough.py examples/big_game "cmd1" "cmd2" "cmd3"

# Codebase-wide refactoring
python3 tools/refactor_using_LibCST --dry-run src/
```

### Key Files

| Purpose | File |
|---------|------|
| Parser patterns | `src/parser.py` |
| Protocol handler | `src/llm_protocol.py` |
| State accessor | `src/state_accessor.py` |
| Vocabulary generator | `src/vocabulary_generator.py` |
| Game engine | `src/game_engine.py` |
| Item finding utilities | `utilities/utils.py` |

---

## 1. Vocabulary System

### How Vocabulary Works

The vocabulary is built from three sources merged together:

1. **Base vocabulary** (`src/vocabulary.json`) - Core verbs, prepositions, articles
2. **Behavior vocabulary** - Each behavior module can define a `vocabulary` dict
3. **Game state extraction** - Item names, NPC names, etc. become nouns automatically

```
Base vocab + Behavior vocab + Extracted nouns = Merged vocabulary
```

### Word Types

```python
from src.word_entry import WordType

WordType.VERB        # Action words
WordType.NOUN        # Object/entity names
WordType.ADJECTIVE   # Descriptors
WordType.PREPOSITION # on, in, with, to, etc.
WordType.ARTICLE     # the, a, an (filtered out by parser)
```

### Multi-Type Words

A word can have multiple types. This is critical for words like "water" (verb AND noun) or "open" (verb AND adjective):

```python
# In behavior vocabulary
vocabulary = {
    "verbs": [
        {
            "word": "water",
            "word_type": ["verb", "noun"],  # Multi-type!
            "event": "on_water",
            "object_required": True
        }
    ]
}
```

### Adding Words via Behaviors

Behaviors can extend vocabulary in their `vocabulary` dict:

```python
# In any behavior module
vocabulary: Dict[str, Any] = {
    "verbs": [...],
    "nouns": [...],
    "adjectives": [{"word": "spore", "synonyms": []}],  # Add adjective
    "events": [...]
}
```

When the same word exists in multiple sources with different types, they're merged into a multi-type word.

### Common Issue: Auto-Extracted Words

Words are auto-extracted from item names as NOUNs. If you have an item "gold mushroom":
- "gold" becomes NOUN
- "mushroom" becomes NOUN

But "gold" is really an adjective! The parser may fail on "examine gold mushroom" if it expects ADJECTIVE + NOUN but gets NOUN + NOUN.

**Fix**: Add the word as an adjective in a behavior vocabulary, or the parser will use fallback patterns.

---

## 2. Parser Patterns

### How Parsing Works

1. Tokenize input into words
2. Look up each word in vocabulary → get WordEntry with type
3. Match the sequence of types against known patterns
4. Return ParsedCommand or None

### Key Patterns (in `src/parser.py`)

```
VERB                              → look, wait
VERB + NOUN                       → take bucket
VERB + ADJ + NOUN                 → take gold coin
VERB + NOUN + NOUN                → put key box (implicit prep)
VERB + PREP + NOUN                → look at door
VERB + NOUN + PREP + NOUN         → put key in box
VERB + NOUN + PREP + ADJ + NOUN   → pour water on gold mushroom
VERB + ADJ + NOUN + PREP + NOUN   → put gold key in box
```

### Unknown Words

When a word isn't in vocabulary:
- Before another noun → treated as ADJECTIVE
- Otherwise → treated as NOUN

This allows "examine fluffy kitten" to work even if "fluffy" isn't in vocabulary.

### Debugging Parse Failures

```python
from src.game_engine import GameEngine
from pathlib import Path

engine = GameEngine(Path('examples/big_game'))
parser = engine.create_parser()

# Check what type a word has
entry = parser._lookup_word('water')
print(f"water: {entry.word_type if entry else 'UNKNOWN'}")

# Try parsing a command
parsed = parser.parse_command('pour water on mushroom')
if parsed:
    print(f"verb: {parsed.verb}")
    print(f"object: {parsed.direct_object}")
    print(f"indirect: {parsed.indirect_object}")
else:
    print("PARSE FAILED")
```

---

## 3. Handler Protocol

### WordEntry Throughout

**Always use WordEntry**, not strings. The system is designed to pass WordEntry objects through the entire pipeline:

```python
# In handler
def handle_pour(accessor: StateAccessor, action: Dict[str, Any]) -> HandlerResult:
    object_name = action.get("object")  # This is a WordEntry

    if isinstance(object_name, WordEntry):
        # Correct - work with WordEntry
        if object_name.word.lower() == "water":
            ...
```

### Extracting Strings from WordEntry

When you need the string value:

```python
# Good - extract explicitly
word_str = word_entry.word

# Or use helper
def _extract_word(value: Optional[Union[str, WordEntry]]) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, 'word'):
        return value.word
    return value
```

### StateAccessor API

**Use `accessor.game_state`**, not `accessor.state`:

```python
# Correct
state = accessor.game_state

# Wrong - this attribute doesn't exist
state = accessor.state  # AttributeError!
```

This was a common bug (issue #249) where tests passed because mocks had `.state` but real code failed.

---

## 4. Testing

### Unit Tests

```bash
# Run all tests
python3 -m unittest discover -s tests -p "test_*.py"

# Run specific test file
python3 -m unittest tests/test_parser.py

# Run specific test
python3 -m unittest tests.test_parser.TestParserIntegration.test_full_game_scenario_1
```

### Walkthrough Tool (End-to-End Testing)

Test command sequences without narrator overhead:

```bash
# Basic usage
python3 tools/walkthrough.py examples/big_game "look" "take bucket" "fill bucket"

# From file
python3 tools/walkthrough.py examples/big_game --file walkthrough.txt

# Verbose (show full JSON)
python3 tools/walkthrough.py examples/big_game -v "pour water on mushroom"
```

The walkthrough tool:
- Uses GameEngine (same as real game)
- Shows success/failure for each command
- Displays primary_text responses
- Skips narrator entirely

### Quick Parser Test

```python
# Test if a specific command parses
python3 -c "
from pathlib import Path
from src.game_engine import GameEngine

engine = GameEngine(Path('examples/big_game'))
parser = engine.create_parser()

for cmd in ['pour water on mushroom', 'fill bucket', 'examine ceiling']:
    parsed = parser.parse_command(cmd)
    print(f'{cmd!r}: {'OK' if parsed else 'FAILED'}')"
```

---

## 5. Common Debugging Scenarios

### "I don't understand that" / Parse Failure

1. **Check word types**: Is each word recognized with the right type?
   ```python
   parser._lookup_word('gold')  # Returns WordEntry with word_type
   ```

2. **Check pattern exists**: Does the type sequence match a parser pattern?
   - VERB + NOUN + PREP + NOUN + NOUN may not have a pattern
   - Look in `src/parser.py` `_match_pattern()` method

3. **Fix options**:
   - Add word to vocabulary with correct type
   - Add new parser pattern
   - Make word multi-type

### Handler Not Found

The verb string must match a registered handler:

```python
# Check registered handlers
print(engine.behavior_manager._handlers.keys())
```

### Narrator Producing Nonsense

1. **Check what JSON narrator receives**:
   ```python
   # The narrator should only get narration-relevant fields
   narration_dict = {
       "success": result.get("success"),
       "verbosity": result.get("verbosity"),
       **result.get("narration", {})
   }
   # NOT the full result dict with "data" field!
   ```

2. **Verify primary_text is correct**: Use walkthrough tool to see engine output

3. **Check for leaked data**: If narrator mentions "state_fragments" or vocabulary data, the filtering is broken

### Mock vs Real Implementation Mismatch

Issue #249 pattern: tests pass but real code fails.

- **Cause**: Test mocks have attributes that real classes don't
- **Detection**: Run actual integration, not just unit tests
- **Prevention**: Make mocks inherit from or wrap real implementations

---

## 6. Refactoring

### Using LibCST

For codebase-wide changes (renaming, API changes):

```bash
# Edit tools/refactor_using_LibCST to configure transformers
# Then run with dry-run first:
python3 tools/refactor_using_LibCST --dry-run src/

# Apply changes:
python3 tools/refactor_using_LibCST src/
```

Available transformers:
- `RenameFunction(old, new)` - Rename function/variable
- `ChangeMethodCall(old, new)` - Rename method calls (e.g., `.state` → `.game_state`)
- `RenameKeywordArg(func, old, new)` - Rename keyword argument
- `RenameImportModule(old, new)` - Rename import path
- `UpdateTypeAnnotation(old, new)` - Change type hints

**Never use sed for Python refactoring** - it doesn't understand syntax and causes errors.

---

## 7. Architecture Quick Reference

### Data Flow for Commands

```
Player Input
    ↓
Parser (parse_command)
    ↓
ParsedCommand (verb, object, adjective, etc. as WordEntry)
    ↓
LLMProtocolHandler.handle_command()
    ↓
BehaviorManager.invoke_handler(verb, accessor, action)
    ↓
Handler function (e.g., handle_pour)
    ↓
HandlerResult (success, primary, data, etc.)
    ↓
NarrationAssembler → NarrationResult
    ↓
LLMNarrator (if using LLM) or direct output
```

### Key Types

```python
from src.word_entry import WordEntry
from src.parsed_command import ParsedCommand
from src.state_accessor import StateAccessor, HandlerResult
from src.types import ActorId, LocationId, ItemId
```

---

## 8. Checklist for New Features

- [ ] Words in vocabulary with correct types?
- [ ] Parser pattern exists for command structure?
- [ ] Handler registered for verb?
- [ ] Handler uses `accessor.game_state` (not `.state`)?
- [ ] Handler accepts WordEntry for object/adjective params?
- [ ] Unit tests added?
- [ ] Walkthrough test verifies end-to-end?

---

## References

- Issue #246: Parser fails on compound noun phrases
- Issue #247: Narrator receiving raw engine data
- Issue #248: Missing puzzle content
- Issue #249: accessor.state vs accessor.game_state inconsistency
- Issue #250: Multi-type words, parser patterns, WordEntry support
