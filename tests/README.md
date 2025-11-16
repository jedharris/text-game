# Parser Test Suite

This directory contains the comprehensive test suite for the text adventure game parser.

## Test Structure

Tests are organized by category as specified in [test-plan.md](test-plan.md):

### Test Files

- **test_word_entry.py** - Unit tests for WordEntry and WordType classes (Category 1) ✅ IMPLEMENTED
- **test_vocabulary_loading.py** - Tests for JSON vocabulary loading (Category 2)
- **test_parser.py** - Main parser tests including word lookup, article filtering, integration (Categories 3, 8, 11)
- **test_pattern_matching.py** - Pattern matching tests for 1-6 word commands (Categories 4-7)
- **test_edge_cases.py** - Edge cases and error handling (Categories 9-10)
- **test_performance.py** - Performance benchmarks (Category 12)
- **test_regression.py** - Regression tests for bug fixes (Category 13)
- **test_helpers.py** - Test utilities and helper functions

### Fixtures Directory

Test data files are stored in `fixtures/`:

- **test_vocabulary.json** - Complete vocabulary for standard tests
- **minimal_vocabulary.json** - Minimal vocabulary for basic tests
- **empty_vocabulary.json** - Empty vocabulary for error tests
- **invalid_vocabulary.json** - Malformed JSON for error tests
- **large_vocabulary.json** - Large vocabulary for performance tests
- **test_commands.json** - Pre-defined test commands with expected results

## Running Tests

### Using the Test Runner

```bash
# Run all tests
python run_tests.py

# Run specific test category
python run_tests.py word_entry
python run_tests.py vocabulary
python run_tests.py parser
python run_tests.py patterns
python run_tests.py edge_cases
python run_tests.py performance

# Verbose output
python run_tests.py -v
python run_tests.py word_entry -v
```

### Using unittest directly

```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_word_entry
python -m unittest tests.test_vocabulary_loading

# Run specific test class
python -m unittest tests.test_word_entry.TestWordEntry

# Run specific test method
python -m unittest tests.test_word_entry.TestWordEntry.test_word_entry_creation

# Verbose output
python -m unittest discover tests -v
```

### Using coverage

```bash
# Install coverage tool
pip install coverage

# Run tests with coverage
coverage run -m unittest discover tests

# Generate coverage report
coverage report

# Generate HTML coverage report
coverage html
open htmlcov/index.html
```

## Test Categories

### Category 1: WordEntry Class (WE-001 to WE-006) ✅

**Status**: IMPLEMENTED
**File**: test_word_entry.py
**Tests**: 6 required + 9 additional = 15 total

Tests the fundamental WordEntry and WordType data structures:
- WE-001: Create WordEntry with all fields
- WE-002: Create WordEntry without synonyms
- WE-003: Create WordEntry without value
- WE-004: Verify WordType enum values
- WE-005: Compare two WordEntry objects
- WE-006: Test string representation

### Category 2: Vocabulary Loading (VL-001 to VL-012)

**Status**: Not yet implemented
**File**: test_vocabulary_loading.py
**Tests**: 12 required

Tests JSON vocabulary file loading:
- Loading complete, minimal, and empty vocabularies
- Error handling for missing/invalid files
- Synonym loading for verbs and directions
- Optional value fields
- Missing JSON sections

### Category 3: Word Lookup (WL-001 to WL-009)

**Status**: Not yet implemented
**File**: test_parser.py (TestWordLookup class)
**Tests**: 9 required

Tests word lookup functionality:
- Exact word matching
- Synonym resolution
- Case handling
- Unknown word detection

### Category 4-7: Pattern Matching (PM-001 to PM-305)

**Status**: Not yet implemented
**File**: test_pattern_matching.py
**Tests**: 24 required

Tests command pattern recognition:
- 1-2 word patterns (6 tests)
- 3 word patterns (5 tests)
- 4 word patterns (3 tests)
- 5-6 word patterns (5 tests)

### Category 8: Article Filtering (AF-001 to AF-007)

**Status**: Not yet implemented
**File**: test_parser.py (TestArticleFiltering class)
**Tests**: 7 required

Tests article filtering functionality.

### Category 9: Error Handling (EH-001 to EH-012)

**Status**: Not yet implemented
**File**: test_edge_cases.py (TestErrorHandling class)
**Tests**: 12 required

Tests error conditions and messages.

### Category 10: Edge Cases (EC-001 to EC-012)

**Status**: Not yet implemented
**File**: test_edge_cases.py (TestEdgeCases class)
**Tests**: 12 required

Tests boundary conditions and unusual input.

### Category 11: Integration Tests (IT-001 to IT-007)

**Status**: Not yet implemented
**File**: test_parser.py (TestParserIntegration class)
**Tests**: 7 required

Tests complete parsing scenarios.

### Category 12: Performance Tests (PF-001 to PF-006)

**Status**: Not yet implemented
**File**: test_performance.py
**Tests**: 6 required

Tests performance benchmarks.

### Category 13: Regression Tests

**Status**: Not yet implemented
**File**: test_regression.py
**Tests**: As needed

Tests for specific bug fixes.

## Test Coverage Goals

- **Line Coverage**: ≥ 95%
- **Branch Coverage**: ≥ 90%
- **Function Coverage**: 100%

## Writing New Tests

When adding new tests:

1. Follow the test ID naming convention (e.g., WE-001, VL-005, PM-102)
2. Include a descriptive docstring explaining what is being tested
3. Reference the test plan document
4. Use meaningful assertion messages
5. Test both success and failure cases
6. Include edge cases

Example:

```python
def test_word_entry_creation(self):
    """
    Test WE-001: Create WordEntry with all fields.

    Verify that a WordEntry can be created with all fields populated
    and that all values are accessible.
    """
    entry = WordEntry(
        word="take",
        word_type=WordType.VERB,
        synonyms=["get", "grab"],
        value=1
    )

    self.assertEqual(entry.word, "take")
    self.assertEqual(entry.word_type, WordType.VERB)
    # ... more assertions
```

## Current Implementation Status

- ✅ Test infrastructure created
- ✅ Test runner script created
- ✅ Category 1: WordEntry tests implemented (15 tests)
- ⏳ Category 2: Vocabulary loading tests (pending)
- ⏳ Category 3-13: Remaining tests (pending)

## Next Steps

1. Implement Category 2: Vocabulary Loading tests
2. Create test fixture files
3. Implement Category 3: Word Lookup tests
4. Continue with remaining categories per implementation plan
