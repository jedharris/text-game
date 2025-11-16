# Parser Test Plan

## Overview

This document provides a comprehensive test plan for the text adventure game parser described in [../docs/initial-design.md](../docs/initial-design.md). The test plan covers unit tests, integration tests, edge cases, error handling, and performance testing.

## Test Infrastructure

### Required Files

```
tests/
├── test-plan.md                    # This file
├── test_parser.py                  # Main parser unit tests
├── test_word_entry.py              # WordEntry class tests
├── test_vocabulary_loading.py      # Vocabulary file loading tests
├── test_pattern_matching.py        # Pattern matching tests
├── test_edge_cases.py              # Edge case and error handling tests
├── test_performance.py             # Performance benchmarks
├── fixtures/
│   ├── test_vocabulary.json        # Complete test vocabulary
│   ├── minimal_vocabulary.json     # Minimal vocabulary for basic tests
│   ├── empty_vocabulary.json       # Empty vocabulary for error tests
│   ├── invalid_vocabulary.json     # Malformed JSON for error tests
│   └── large_vocabulary.json       # Large vocabulary for performance tests
└── __init__.py
```

### Test Vocabulary Files

#### fixtures/test_vocabulary.json

Standard vocabulary file for most tests:

```json
{
  "verbs": [
    { "word": "take", "synonyms": ["get", "grab", "pick"], "value": 1 },
    { "word": "drop", "synonyms": ["put", "place"], "value": 2 },
    { "word": "examine", "synonyms": ["look", "inspect", "x"], "value": 3 },
    { "word": "go", "synonyms": [], "value": 4 },
    { "word": "open", "synonyms": [], "value": 5 },
    { "word": "unlock", "synonyms": [], "value": 6 },
    { "word": "attack", "synonyms": ["hit", "strike", "kill"], "value": 7 },
    { "word": "use", "synonyms": [], "value": 8 },
    { "word": "eat", "synonyms": ["consume"], "value": 9 },
    { "word": "drink", "synonyms": [], "value": 10 }
  ],
  "nouns": [
    { "word": "door", "value": 101 },
    { "word": "key", "value": 102 },
    { "word": "sword", "value": 103 },
    { "word": "chest", "value": 104 },
    { "word": "goblin", "value": 105 },
    { "word": "flask", "value": 106 },
    { "word": "potion", "value": 107 },
    { "word": "coin", "value": 108 },
    { "word": "lock", "value": 109 },
    { "word": "table", "value": 110 }
  ],
  "adjectives": [
    { "word": "red", "value": 201 },
    { "word": "blue", "value": 202 },
    { "word": "rusty", "value": 203 },
    { "word": "wooden", "value": 204 },
    { "word": "iron", "value": 205 },
    { "word": "small", "value": 206 },
    { "word": "large", "value": 207 },
    { "word": "golden", "value": 208 },
    { "word": "silver", "value": 209 },
    { "word": "ancient", "value": 210 }
  ],
  "prepositions": ["with", "to", "in", "on", "under", "behind", "from", "into"],
  "directions": [
    { "word": "north", "synonyms": ["n"], "value": 1 },
    { "word": "south", "synonyms": ["s"], "value": 2 },
    { "word": "east", "synonyms": ["e"], "value": 3 },
    { "word": "west", "synonyms": ["w"], "value": 4 },
    { "word": "up", "synonyms": ["u"], "value": 5 },
    { "word": "down", "synonyms": ["d"], "value": 6 },
    { "word": "northeast", "synonyms": ["ne"], "value": 7 },
    { "word": "northwest", "synonyms": ["nw"], "value": 8 },
    { "word": "southeast", "synonyms": ["se"], "value": 9 },
    { "word": "southwest", "synonyms": ["sw"], "value": 10 }
  ],
  "articles": ["the", "a", "an"]
}
```

#### fixtures/minimal_vocabulary.json

```json
{
  "verbs": [
    { "word": "take", "synonyms": [], "value": 1 }
  ],
  "nouns": [
    { "word": "key", "value": 101 }
  ],
  "adjectives": [
    { "word": "red", "value": 201 }
  ],
  "prepositions": ["with"],
  "directions": [
    { "word": "north", "synonyms": [], "value": 1 }
  ],
  "articles": ["the"]
}
```

#### fixtures/empty_vocabulary.json

```json
{
  "verbs": [],
  "nouns": [],
  "adjectives": [],
  "prepositions": [],
  "directions": [],
  "articles": []
}
```

### Test Framework

- **Framework**: Python `unittest` (standard library)
- **Coverage Tool**: `coverage.py`
- **Assertions**: Standard unittest assertions plus custom helpers
- **Mocking**: `unittest.mock` for file I/O testing

### Running Tests

```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_parser

# Run with coverage
coverage run -m unittest discover tests
coverage report
coverage html

# Run specific test case
python -m unittest tests.test_parser.TestBasicParsing.test_verb_noun

# Run with verbose output
python -m unittest discover tests -v
```

## Test Categories

### 1. Unit Tests - WordEntry Class

**File**: `tests/test_word_entry.py`

#### Test Cases

| Test ID | Test Name | Description | Input | Expected Output |
|---------|-----------|-------------|-------|-----------------|
| WE-001 | test_word_entry_creation | Create WordEntry with all fields | word="take", type=VERB, synonyms=["get"], value=1 | WordEntry object created successfully |
| WE-002 | test_word_entry_no_synonyms | Create WordEntry without synonyms | word="door", type=NOUN, value=101 | synonyms defaults to empty list |
| WE-003 | test_word_entry_no_value | Create WordEntry without value | word="with", type=PREPOSITION | value is None |
| WE-004 | test_word_type_enum | Verify WordType enum values | WordType.VERB | Returns "VERB" |
| WE-005 | test_word_entry_equality | Compare two WordEntry objects | Two identical entries | Should be equal |
| WE-006 | test_word_entry_string_repr | Test string representation | WordEntry("take", VERB) | Readable string output |

### 2. Unit Tests - Vocabulary Loading

**File**: `tests/test_vocabulary_loading.py`

#### Test Cases

| Test ID | Test Name | Description | Input | Expected Output |
|---------|-----------|-------------|-------|-----------------|
| VL-001 | test_load_complete_vocabulary | Load complete vocabulary file | test_vocabulary.json | All word types loaded correctly |
| VL-002 | test_load_minimal_vocabulary | Load minimal vocabulary | minimal_vocabulary.json | Minimal entries loaded |
| VL-003 | test_load_empty_vocabulary | Load empty vocabulary | empty_vocabulary.json | Empty word table created |
| VL-004 | test_load_missing_file | Load non-existent file | "nonexistent.json" | FileNotFoundError raised |
| VL-005 | test_load_invalid_json | Load malformed JSON | invalid_vocabulary.json | JSONDecodeError raised |
| VL-006 | test_verb_synonyms_loaded | Verify verb synonyms | "take" with synonyms | All synonyms accessible |
| VL-007 | test_direction_synonyms_loaded | Verify direction synonyms | "north" with "n" | Synonyms loaded correctly |
| VL-008 | test_preposition_loading | Load simple string prepositions | ["with", "to"] | WordEntry objects created |
| VL-009 | test_article_loading | Load simple string articles | ["the", "a"] | WordEntry objects created |
| VL-010 | test_value_field_optional | Verify value field is optional | Entry without value | value=None |
| VL-011 | test_missing_sections | Handle missing JSON sections | JSON without "verbs" | Defaults to empty list |
| VL-012 | test_word_table_size | Verify correct number of entries | Full vocabulary | Count matches expected |

### 3. Unit Tests - Word Lookup

**File**: `tests/test_parser.py` (class TestWordLookup)

#### Test Cases

| Test ID | Test Name | Description | Input | Expected Output |
|---------|-----------|-------------|-------|-----------------|
| WL-001 | test_lookup_exact_match | Find word by exact match | "take" | WordEntry for "take" |
| WL-002 | test_lookup_synonym | Find word by synonym | "grab" (synonym of "take") | WordEntry for "take" |
| WL-003 | test_lookup_unknown_word | Look up non-existent word | "frobulate" | None |
| WL-004 | test_lookup_case_insensitive | Verify case handling | "TAKE", "Take", "take" | All tokenized to lowercase first |
| WL-005 | test_lookup_direction_synonym | Find direction by synonym | "n" | WordEntry for "north" |
| WL-006 | test_lookup_multiple_synonyms | Word with multiple synonyms | "grab", "get", "pick" | All return "take" |
| WL-007 | test_lookup_preposition | Look up preposition | "with" | WordEntry for "with" |
| WL-008 | test_lookup_article | Look up article | "the" | WordEntry for "the" |
| WL-009 | test_lookup_adjective | Look up adjective | "rusty" | WordEntry for "rusty" |

### 4. Unit Tests - Pattern Matching (1-2 Words)

**File**: `tests/test_pattern_matching.py` (class TestPatternMatching12Words)

#### Test Cases

| Test ID | Test Name | Description | Input | Expected Output |
|---------|-----------|-------------|-------|-----------------|
| PM-001 | test_single_direction | Single direction word | "north" | direction=north |
| PM-002 | test_direction_synonym | Direction synonym | "n" | direction=north |
| PM-003 | test_verb_noun | Basic verb + noun | "take sword" | verb=take, direct_object=sword |
| PM-004 | test_verb_direction | Verb + direction | "go north" | verb=go, direction=north |
| PM-005 | test_verb_direction_synonym | Verb + direction synonym | "go n" | verb=go, direction=north |
| PM-006 | test_synonym_verb_noun | Synonym verb + noun | "grab sword" | verb=take, direct_object=sword |

### 5. Unit Tests - Pattern Matching (3 Words)

**File**: `tests/test_pattern_matching.py` (class TestPatternMatching3Words)

#### Test Cases

| Test ID | Test Name | Description | Input | Expected Output |
|---------|-----------|-------------|-------|-----------------|
| PM-101 | test_verb_adjective_noun | Verb + adjective + noun | "take rusty key" | verb=take, direct_adj=rusty, direct_obj=key |
| PM-102 | test_verb_noun_noun | Verb + noun + noun (implicit with) | "unlock door key" | verb=unlock, direct_obj=door, indirect_obj=key |
| PM-103 | test_verb_prep_noun | Verb + preposition + noun | "look in chest" | verb=look, prep=in, direct_obj=chest |
| PM-104 | test_verb_adj_noun_colors | Adjective for color | "take red key" | verb=take, direct_adj=red, direct_obj=key |
| PM-105 | test_verb_adj_noun_size | Adjective for size | "examine large door" | verb=examine, direct_adj=large, direct_obj=door |

### 6. Unit Tests - Pattern Matching (4 Words)

**File**: `tests/test_pattern_matching.py` (class TestPatternMatching4Words)

#### Test Cases

| Test ID | Test Name | Description | Input | Expected Output |
|---------|-----------|-------------|-------|-----------------|
| PM-201 | test_verb_adj_noun_noun | Verb + adj + noun + noun | "unlock rusty door key" | verb=unlock, direct_adj=rusty, direct_obj=door, indirect_obj=key |
| PM-202 | test_verb_noun_prep_noun | Verb + noun + prep + noun | "unlock door with key" | verb=unlock, direct_obj=door, prep=with, indirect_obj=key |
| PM-203 | test_verb_prep_adj_noun | Verb + prep + adj + noun | "look in wooden chest" | verb=look, prep=in, direct_adj=wooden, direct_obj=chest |

### 7. Unit Tests - Pattern Matching (5-6 Words)

**File**: `tests/test_pattern_matching.py` (class TestPatternMatching56Words)

#### Test Cases

| Test ID | Test Name | Description | Input | Expected Output |
|---------|-----------|-------------|-------|-----------------|
| PM-301 | test_verb_adj_noun_prep_noun | 5 words, adj on direct obj | "unlock rusty door with key" | verb=unlock, direct_adj=rusty, direct_obj=door, prep=with, indirect_obj=key |
| PM-302 | test_verb_noun_prep_adj_noun | 5 words, adj on indirect obj | "unlock door with rusty key" | verb=unlock, direct_obj=door, prep=with, indirect_adj=rusty, indirect_obj=key |
| PM-303 | test_verb_adj_noun_prep_adj_noun | 6 words, both adjectives | "unlock rusty door with iron key" | Both adjectives present |
| PM-304 | test_complex_color_adjectives | Complex with color adjectives | "take red potion with blue flask" | Both color adjectives parsed |
| PM-305 | test_complex_size_adjectives | Complex with size adjectives | "open large chest with small key" | Both size adjectives parsed |

### 8. Unit Tests - Article Filtering

**File**: `tests/test_parser.py` (class TestArticleFiltering)

#### Test Cases

| Test ID | Test Name | Description | Input | Expected Output |
|---------|-----------|-------------|-------|-----------------|
| AF-001 | test_filter_the | Filter "the" | "take the sword" | Same as "take sword" |
| AF-002 | test_filter_a | Filter "a" | "take a sword" | Same as "take sword" |
| AF-003 | test_filter_an | Filter "an" | "take an sword" | Same as "take sword" |
| AF-004 | test_multiple_articles | Multiple articles (unusual) | "take the a sword" | Both articles filtered |
| AF-005 | test_article_with_adjective | Article before adjective | "take the rusty key" | Same as "take rusty key" |
| AF-006 | test_article_complex | Article in complex command | "unlock the rusty door with the iron key" | Both articles filtered |
| AF-007 | test_no_article | No article present | "take sword" | Command unchanged |

### 9. Unit Tests - Error Handling

**File**: `tests/test_edge_cases.py` (class TestErrorHandling)

#### Test Cases

| Test ID | Test Name | Description | Input | Expected Output |
|---------|-----------|-------------|-------|-----------------|
| EH-001 | test_unknown_word | Unknown word in command | "frobulate sword" | "I don't understand the word 'frobulate'" |
| EH-002 | test_invalid_pattern | Invalid word pattern | "the with in" | "I don't understand that command" |
| EH-003 | test_empty_input | Empty string | "" | Error or None |
| EH-004 | test_whitespace_only | Only whitespace | "   " | Error or None |
| EH-005 | test_single_unknown | Single unknown word | "frobulate" | "I don't understand the word 'frobulate'" |
| EH-006 | test_partial_unknown | Known + unknown words | "take frobulate" | "I don't understand the word 'frobulate'" |
| EH-007 | test_all_articles | Only articles | "the a an" | "I don't understand that command" |
| EH-008 | test_noun_only | Single noun | "sword" | "I don't understand that command" |
| EH-009 | test_adjective_only | Single adjective | "rusty" | "I don't understand that command" |
| EH-010 | test_preposition_only | Single preposition | "with" | "I don't understand that command" |
| EH-011 | test_two_verbs | Two verbs | "take drop" | "I don't understand that command" |
| EH-012 | test_two_directions | Two directions | "north south" | "I don't understand that command" |

### 10. Unit Tests - Edge Cases

**File**: `tests/test_edge_cases.py` (class TestEdgeCases)

#### Test Cases

| Test ID | Test Name | Description | Input | Expected Output |
|---------|-----------|-------------|-------|-----------------|
| EC-001 | test_extra_whitespace | Multiple spaces between words | "take    sword" | Same as "take sword" |
| EC-002 | test_leading_whitespace | Leading whitespace | "  take sword" | Same as "take sword" |
| EC-003 | test_trailing_whitespace | Trailing whitespace | "take sword  " | Same as "take sword" |
| EC-004 | test_mixed_case | Mixed case input | "TaKe SwOrD" | Normalized to lowercase |
| EC-005 | test_uppercase_input | All uppercase | "TAKE SWORD" | Same as "take sword" |
| EC-006 | test_tab_characters | Tab separators | "take\tsword" | Treated as whitespace |
| EC-007 | test_very_long_command | Command with max words | 6-word command | Parsed correctly |
| EC-008 | test_too_many_words | More than 6 words | "verb adj noun prep adj noun extra" | Error or truncation |
| EC-009 | test_special_characters | Special characters in input | "take sword!" | Depends on tokenization |
| EC-010 | test_numbers_in_input | Numbers in input | "take 123" | Treated as unknown word |
| EC-011 | test_unicode_input | Unicode characters | "take sẃord" | Unknown word error |
| EC-012 | test_raw_field_preserved | Original input preserved | "TAKE  the SWORD" | raw field contains original |

### 11. Integration Tests

**File**: `tests/test_parser.py` (class TestParserIntegration)

#### Test Cases

| Test ID | Test Name | Description | Input | Expected Output |
|---------|-----------|-------------|-------|-----------------|
| IT-001 | test_full_game_scenario_1 | Complete game scenario | Series of commands | All parsed correctly |
| IT-002 | test_full_game_scenario_2 | Combat scenario | Attack commands | Correct parsing |
| IT-003 | test_exploration_scenario | Exploration commands | Movement + examination | All work together |
| IT-004 | test_inventory_scenario | Inventory management | Take, drop, use | Commands parsed |
| IT-005 | test_puzzle_scenario | Puzzle solving | Complex multi-word commands | All patterns work |
| IT-006 | test_parser_reuse | Reuse parser instance | Multiple parse calls | State not corrupted |
| IT-007 | test_synonym_consistency | Synonym consistency | Same action, different words | Consistent results |

### 12. Performance Tests

**File**: `tests/test_performance.py`

#### Test Cases

| Test ID | Test Name | Description | Metric | Target |
|---------|-----------|-------------|--------|--------|
| PF-001 | test_single_parse_speed | Time for single parse | Time | < 1ms |
| PF-002 | test_1000_parses | Time for 1000 parses | Time | < 100ms |
| PF-003 | test_large_vocabulary | Large vocabulary (1000+ words) | Load time | < 500ms |
| PF-004 | test_worst_case_lookup | Lookup last word in table | Time | < 1ms |
| PF-005 | test_memory_usage | Memory footprint | Memory | < 10MB for 1000 words |
| PF-006 | test_synonym_lookup_speed | Lookup via synonym | Time | Same as direct lookup |

### 13. Regression Tests

**File**: `tests/test_regression.py`

Specific tests for bugs found during development:

| Test ID | Test Name | Description | Purpose |
|---------|-----------|-------------|---------|
| RG-001 | test_issue_XXX | Specific bug reproduction | Ensure bug stays fixed |

## Test Data and Fixtures

### Command Test Data

Create a comprehensive test data file for various command types:

**File**: `tests/fixtures/test_commands.json`

```json
{
  "valid_commands": [
    {
      "input": "north",
      "expected": {
        "type": "direction",
        "direction": "north"
      }
    },
    {
      "input": "take sword",
      "expected": {
        "type": "verb_noun",
        "verb": "take",
        "direct_object": "sword"
      }
    },
    {
      "input": "take rusty key",
      "expected": {
        "type": "verb_adj_noun",
        "verb": "take",
        "direct_adjective": "rusty",
        "direct_object": "key"
      }
    },
    {
      "input": "unlock door with key",
      "expected": {
        "type": "verb_noun_prep_noun",
        "verb": "unlock",
        "direct_object": "door",
        "preposition": "with",
        "indirect_object": "key"
      }
    },
    {
      "input": "unlock rusty door with iron key",
      "expected": {
        "type": "complex",
        "verb": "unlock",
        "direct_adjective": "rusty",
        "direct_object": "door",
        "preposition": "with",
        "indirect_adjective": "iron",
        "indirect_object": "key"
      }
    }
  ],
  "invalid_commands": [
    {
      "input": "frobulate widget",
      "expected_error": "I don't understand the word 'frobulate'"
    },
    {
      "input": "the in with",
      "expected_error": "I don't understand that command"
    },
    {
      "input": "",
      "expected_error": "I don't understand that command"
    }
  ],
  "article_test_cases": [
    {
      "input": "take the sword",
      "equivalent_to": "take sword"
    },
    {
      "input": "take a rusty key",
      "equivalent_to": "take rusty key"
    }
  ],
  "synonym_test_cases": [
    {
      "input": "grab sword",
      "equivalent_to": "take sword"
    },
    {
      "input": "go n",
      "equivalent_to": "go north"
    }
  ]
}
```

## Test Helpers and Utilities

### Custom Assertion Methods

**File**: `tests/test_helpers.py`

```python
from typing import Optional
from parser import ParsedCommand, WordEntry

class ParserTestHelpers:
    """Helper methods for parser testing."""

    @staticmethod
    def assert_command_equal(cmd1: ParsedCommand, cmd2: ParsedCommand) -> None:
        """Assert two ParsedCommand objects are equivalent."""
        assert cmd1.verb == cmd2.verb
        assert cmd1.direct_object == cmd2.direct_object
        assert cmd1.direct_adjective == cmd2.direct_adjective
        assert cmd1.preposition == cmd2.preposition
        assert cmd1.indirect_object == cmd2.indirect_object
        assert cmd1.indirect_adjective == cmd2.indirect_adjective
        assert cmd1.direction == cmd2.direction

    @staticmethod
    def assert_word_entry(entry: Optional[WordEntry],
                          expected_word: str,
                          expected_value: Optional[int] = None) -> None:
        """Assert a WordEntry has expected properties."""
        assert entry is not None, "WordEntry should not be None"
        assert entry.word == expected_word
        if expected_value is not None:
            assert entry.value == expected_value

    @staticmethod
    def create_command_with_defaults(**kwargs) -> ParsedCommand:
        """Create a ParsedCommand with specified fields."""
        return ParsedCommand(**kwargs)
```

## Coverage Requirements

### Target Coverage Metrics

- **Line Coverage**: Minimum 95%
- **Branch Coverage**: Minimum 90%
- **Function Coverage**: 100%

### Critical Paths (Must have 100% coverage)

1. `parse_command()` - Main parsing function
2. `_lookup_word()` - Word lookup function
3. `_match_pattern()` - Pattern matching function
4. `_load_vocabulary()` - Vocabulary loading function

### Excluded from Coverage

- `__repr__()` methods (unless used in production)
- Debug/logging code
- Type checking code (if using runtime type checking)

## Test Execution Strategy

### Test Phases

#### Phase 1: Unit Tests (Run First)
1. WordEntry class tests
2. Vocabulary loading tests
3. Word lookup tests

#### Phase 2: Pattern Matching (Run Second)
1. 1-2 word patterns
2. 3 word patterns
3. 4 word patterns
4. 5-6 word patterns

#### Phase 3: Integration Tests (Run Third)
1. Article filtering
2. Full parsing scenarios
3. Game scenarios

#### Phase 4: Edge Cases and Performance (Run Last)
1. Error handling
2. Edge cases
3. Performance benchmarks

### Continuous Integration

```yaml
# Example .github/workflows/tests.yml
name: Parser Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install coverage
      - name: Run tests with coverage
        run: |
          coverage run -m unittest discover tests
          coverage report --fail-under=95
          coverage html
      - name: Upload coverage
        uses: actions/upload-artifact@v2
        with:
          name: coverage-report
          path: htmlcov/
```

## Test Development Checklist

### For Each Feature

- [ ] Write test cases before implementation (TDD)
- [ ] Cover happy path
- [ ] Cover error cases
- [ ] Cover edge cases
- [ ] Test with valid and invalid input
- [ ] Test boundary conditions
- [ ] Verify error messages are helpful
- [ ] Check raw field is preserved
- [ ] Test case sensitivity
- [ ] Test whitespace handling

### Before Release

- [ ] All tests pass
- [ ] Coverage meets requirements (95%+)
- [ ] No skipped tests without justification
- [ ] Performance benchmarks pass
- [ ] Integration tests pass
- [ ] Documentation updated
- [ ] Test data files committed
- [ ] CI/CD pipeline green

## Example Test Implementation

### Sample Test File Structure

**File**: `tests/test_parser.py`

```python
import unittest
import os
from parser import Parser, ParsedCommand, WordEntry, WordType

class TestBasicParsing(unittest.TestCase):
    """Test basic parsing functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        cls.vocab_path = os.path.join('tests', 'fixtures', 'test_vocabulary.json')
        cls.parser = Parser(cls.vocab_path)

    def test_verb_noun(self):
        """Test basic VERB + NOUN pattern (PM-003)."""
        command = self.parser.parse_command("take sword")

        # Verify it's a ParsedCommand, not an error string
        self.assertIsInstance(command, ParsedCommand)

        # Verify verb
        self.assertIsNotNone(command.verb)
        self.assertEqual(command.verb.word, "take")
        self.assertEqual(command.verb.word_type, WordType.VERB)
        self.assertEqual(command.verb.value, 1)

        # Verify direct object
        self.assertIsNotNone(command.direct_object)
        self.assertEqual(command.direct_object.word, "sword")
        self.assertEqual(command.direct_object.word_type, WordType.NOUN)
        self.assertEqual(command.direct_object.value, 103)

        # Verify other fields are None
        self.assertIsNone(command.direct_adjective)
        self.assertIsNone(command.preposition)
        self.assertIsNone(command.indirect_object)
        self.assertIsNone(command.indirect_adjective)
        self.assertIsNone(command.direction)

        # Verify raw input preserved
        self.assertEqual(command.raw, "take sword")

    def test_verb_adjective_noun(self):
        """Test VERB + ADJECTIVE + NOUN pattern (PM-101)."""
        command = self.parser.parse_command("take rusty key")

        self.assertIsInstance(command, ParsedCommand)

        # Verify verb
        self.assertEqual(command.verb.word, "take")

        # Verify adjective
        self.assertIsNotNone(command.direct_adjective)
        self.assertEqual(command.direct_adjective.word, "rusty")
        self.assertEqual(command.direct_adjective.word_type, WordType.ADJECTIVE)
        self.assertEqual(command.direct_adjective.value, 203)

        # Verify noun
        self.assertEqual(command.direct_object.word, "key")

        # Verify raw
        self.assertEqual(command.raw, "take rusty key")

    def test_unknown_word(self):
        """Test unknown word error handling (EH-001)."""
        result = self.parser.parse_command("frobulate sword")

        # Should return error string
        self.assertIsInstance(result, str)
        self.assertIn("frobulate", result.lower())
        self.assertEqual(result, "I don't understand the word 'frobulate'")

    def test_article_filtering(self):
        """Test article filtering (AF-001)."""
        cmd_with_article = self.parser.parse_command("take the sword")
        cmd_without_article = self.parser.parse_command("take sword")

        # Both should be ParsedCommand instances
        self.assertIsInstance(cmd_with_article, ParsedCommand)
        self.assertIsInstance(cmd_without_article, ParsedCommand)

        # Should have same structure (articles filtered)
        self.assertEqual(cmd_with_article.verb.word, cmd_without_article.verb.word)
        self.assertEqual(cmd_with_article.direct_object.word,
                        cmd_without_article.direct_object.word)

        # Raw should preserve original
        self.assertEqual(cmd_with_article.raw, "take the sword")
        self.assertEqual(cmd_without_article.raw, "take sword")


class TestSynonyms(unittest.TestCase):
    """Test synonym resolution."""

    @classmethod
    def setUpClass(cls):
        cls.vocab_path = os.path.join('tests', 'fixtures', 'test_vocabulary.json')
        cls.parser = Parser(cls.vocab_path)

    def test_verb_synonym(self):
        """Test verb synonym resolution (WL-006)."""
        # "grab" is synonym of "take"
        command = self.parser.parse_command("grab sword")

        self.assertIsInstance(command, ParsedCommand)
        # Should resolve to base word "take"
        self.assertEqual(command.verb.word, "take")
        self.assertEqual(command.verb.value, 1)

    def test_direction_synonym(self):
        """Test direction synonym (PM-002)."""
        # "n" is synonym of "north"
        command = self.parser.parse_command("n")

        self.assertIsInstance(command, ParsedCommand)
        self.assertEqual(command.direction.word, "north")
        self.assertEqual(command.direction.value, 1)


if __name__ == '__main__':
    unittest.main()
```

## Manual Testing Checklist

In addition to automated tests, perform manual testing:

- [ ] Test with real game scenarios
- [ ] Test parser interactively in REPL
- [ ] Verify error messages are user-friendly
- [ ] Test with unexpected user input patterns
- [ ] Verify performance feels responsive
- [ ] Test vocabulary file editing workflow
- [ ] Verify documentation examples work

## Appendix: Test Metrics Tracking

### Metrics to Track

1. **Test Count**: Total number of test cases
2. **Coverage Percentage**: Line and branch coverage
3. **Test Execution Time**: Total time for test suite
4. **Failure Rate**: Percentage of failing tests
5. **Flaky Test Count**: Tests that fail intermittently

### Success Criteria

- All tests pass on main branch
- Coverage ≥ 95%
- Test suite runs in < 5 seconds
- Zero flaky tests
- All features have corresponding tests
