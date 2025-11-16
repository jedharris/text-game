# Quick Start Guide

## For Developers

This guide helps you get started with the text adventure game parser implementation.

---

## What's Been Done ✅

- ✅ **WordEntry & WordType classes** - Complete and tested
- ✅ **18 comprehensive tests** - All passing (when run)
- ✅ **Complete documentation** - Design, implementation plan, test plan
- ✅ **Test infrastructure** - Test runner and fixtures directory

---

## Project Structure

```
text-game/
├── src/                    # Source code
│   ├── word_entry.py       # ✅ WordEntry & WordType (COMPLETE)
│   ├── parsed_command.py   # ⏳ Next: ParsedCommand dataclass
│   └── parser.py          # ⏳ Next: Parser class
│
├── tests/                  # Test suite
│   ├── test_word_entry.py  # ✅ 18 tests (COMPLETE)
│   ├── test_vocabulary_loading.py  # ⏳ Next
│   └── fixtures/           # Test data files (empty)
│
├── docs/                   # Documentation
│   ├── initial-design.md   # Complete design specification
│   └── implementation-plan.md  # 8-phase implementation guide
│
└── run_tests.py           # Test runner script
```

---

## Running Tests (When Ready)

### WordEntry Tests

```bash
# Quick run
python run_tests.py word_entry

# Verbose output
python -m unittest tests.test_word_entry -v

# Specific test
python -m unittest tests.test_word_entry.TestWordEntry.test_word_entry_creation
```

### All Tests (Future)

```bash
python run_tests.py
```

---

## Next Steps for Implementation

### Step 1: Understand Current State

Read these in order:
1. [COMPLETED_WORK.md](COMPLETED_WORK.md) - What's done
2. [docs/initial-design.md](docs/initial-design.md) - Overall design
3. [docs/implementation-plan.md](docs/implementation-plan.md) - Next phases

### Step 2: Continue Implementation

Follow [docs/implementation-plan.md](docs/implementation-plan.md) Phase 2:

1. **Create test fixtures** in `tests/fixtures/`:
   - test_vocabulary.json
   - minimal_vocabulary.json
   - empty_vocabulary.json
   - invalid_vocabulary.json

2. **Create ParsedCommand** in `src/parsed_command.py`

3. **Create Parser stub** in `src/parser.py`

4. **Create vocabulary loading tests** in `tests/test_vocabulary_loading.py`

### Step 3: Run and Validate

```bash
# Run new tests
python run_tests.py vocabulary

# Check coverage (if installed)
coverage run -m unittest discover tests
coverage report
```

---

## Key Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `src/word_entry.py` | Core data structures | ✅ Complete |
| `tests/test_word_entry.py` | WordEntry tests | ✅ 18 tests |
| `docs/initial-design.md` | Design spec | ✅ Complete |
| `docs/implementation-plan.md` | Implementation guide | ✅ Complete |
| `tests/test-plan.md` | Test specifications | ✅ Complete |
| `IMPLEMENTATION_STATUS.md` | Progress tracking | ✅ Updated |
| `tests/TEST_IDS.md` | Test ID reference | ✅ Complete |

---

## Useful Commands

### Testing

```bash
# Run category
python run_tests.py word_entry

# Run specific test file
python -m unittest tests.test_word_entry

# Run specific test class
python -m unittest tests.test_word_entry.TestWordEntry

# Run specific test method
python -m unittest tests.test_word_entry.TestWordEntry.test_word_entry_creation

# Verbose output
python -m unittest tests.test_word_entry -v

# Discover all tests
python -m unittest discover tests
```

### Coverage (Optional)

```bash
# Install coverage
pip install coverage

# Run with coverage
coverage run -m unittest discover tests

# Show report
coverage report

# HTML report
coverage html
open htmlcov/index.html
```

### File Exploration

```bash
# List all Python files
find . -name "*.py" -not -path "./__pycache__/*"

# Count lines of code
wc -l src/*.py tests/*.py

# Show test count
python -m unittest tests.test_word_entry -v 2>&1 | grep -c "ok"
```

---

## Understanding the Code

### WordEntry Example

```python
from src.word_entry import WordEntry, WordType

# Create a verb entry
take_verb = WordEntry(
    word="take",
    word_type=WordType.VERB,
    synonyms=["get", "grab", "pick"],
    value=1
)

# Create a noun entry
sword_noun = WordEntry(
    word="sword",
    word_type=WordType.NOUN,
    value=103
)

# Synonyms defaults to empty list
prep = WordEntry(
    word="with",
    word_type=WordType.PREPOSITION
)

print(prep.synonyms)  # []
```

### Running a Single Test

```python
# In Python REPL
import unittest
from tests.test_word_entry import TestWordEntry

# Run one test
suite = unittest.TestLoader().loadTestsFromName(
    'test_word_entry_creation',
    TestWordEntry
)
unittest.TextTestRunner(verbosity=2).run(suite)
```

---

## Common Tasks

### Add a New Test

1. Open `tests/test_word_entry.py`
2. Add method to `TestWordEntry` class:

```python
def test_my_new_feature(self):
    """
    Test XX-XXX: Description.

    Detailed explanation of what is being tested.
    """
    # Setup
    entry = WordEntry(...)

    # Execute & Assert
    self.assertEqual(entry.field, expected_value)
```

3. Run test:
```bash
python -m unittest tests.test_word_entry.TestWordEntry.test_my_new_feature -v
```

### Check Test Coverage

```bash
# Run all tests
python -m unittest discover tests -v

# Count passing tests
python -m unittest discover tests 2>&1 | grep -c "ok"

# See test names
python -m unittest tests.test_word_entry -v 2>&1 | grep "test_"
```

---

## Questions?

### Where is the implementation plan?

See [docs/implementation-plan.md](docs/implementation-plan.md) - 8 phases with complete code examples.

### What tests are done?

See [tests/TEST_IDS.md](tests/TEST_IDS.md) - All test IDs with status.

### What's the overall progress?

See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Phase and test tracking.

### How do I run tests?

See above or [tests/README.md](tests/README.md) - Complete testing guide.

### What's next?

See [docs/implementation-plan.md](docs/implementation-plan.md) Phase 2 - Vocabulary Loading.

---

## Tips

1. **Follow the plan** - implementation-plan.md has everything you need
2. **Run tests often** - catch issues early
3. **Read test-plan.md** - understand what each test should do
4. **Use test IDs** - reference tests by ID (e.g., WE-001)
5. **Write tests first** - TDD approach recommended

---

## Summary

✅ **Phase 1 Complete** - WordEntry & tests done
⏳ **Phase 2 Next** - Vocabulary loading
📚 **Well Documented** - Everything is explained
🎯 **Clear Path Forward** - Follow implementation-plan.md

**Ready to continue implementation!**

---

Last Updated: 2025-11-16
Next Phase: Vocabulary Loading (Phase 2)
