# State Manager Test Infrastructure

## Overview

Complete test infrastructure created for the game state manager according to `docs/state_manager_testing.md`.

## Files Created

### Test Modules (6 files)
1. **test_loader.py** - 7 test cases (TL-001 to TL-007)
   - File loading, JSON parsing, error handling
2. **test_validators.py** - 18 test cases (TV-001 to TV-018)
   - Global ID validation, reference checking, constraint validation
3. **test_serializer.py** - 5 test cases (TS-001 to TS-005)
   - JSON serialization, round-trip testing
4. **test_models.py** - 5 test cases (TM-001 to TM-005)
   - Dataclass behavior, field defaults, type conversion
5. **test_error_handling.py** - 5 test cases (TE-001 to TE-005)
   - Error aggregation, schema errors, warnings
6. **test_regressions.py** - 4 test cases (TR-001 to TR-004)
   - End-to-end integration, round-trip validation

**Total: 44 test cases**

### Test Fixtures (13 JSON files)

#### Valid Fixtures
- **valid_world.json** - Complete valid game state with all features
- **valid_world_canonical.json** - Expected serializer output (sorted keys)
- **minimal_world.json** - Minimal valid configuration

#### Invalid Fixtures
- **missing_sections.json** - Missing required `metadata` section
- **duplicate_ids.json** - Duplicate location IDs
- **global_id_collision.json** - ID collision between location and item
- **reserved_id_violation.json** - Entity using reserved `"player"` ID
- **bad_references.json** - Exit pointing to nonexistent location
- **container_cycle.json** - Circular container containment
- **invalid_exits.json** - Exit missing required `door_id`
- **invalid_locks.json** - Door referencing undefined lock
- **invalid_scripts.json** - Script referencing nonexistent entity
- **invalid_player_state.json** - PlayerState with invalid location/inventory
- **invalid_item_location.json** - Item with invalid location reference

### Support Files
- **test_helpers.py** - Helper utilities
  - `load_fixture()` - Load JSON fixtures
  - `get_fixture_path()` - Get fixture paths
  - `assert_validation_error_contains()` - Check error messages
  - `assert_ids_match()` - Compare ID sets
  - `normalize_json()` - Normalize for comparison
  - `json_equal()` - Semantic equality check

- **run_tests.py** - Test runner script
- **Makefile** - Convenient test commands
- **README.md** - Test suite documentation
- **TEST_INFRASTRUCTURE.md** - This file
- **__init__.py** - Package initialization

## Test Coverage by Specification

### Loader Functionality (7 tests)
✓ Load from file path
✓ Load from file-like object
✓ Minimal world with defaults
✓ Unknown keys preservation
✓ Invalid JSON error handling
✓ Missing file error handling
✓ Dict input support

### Validation Rules (18 tests)
✓ Global ID uniqueness (3 tests)
✓ Reference validation (5 tests)
✓ Item location validation (4 tests)
✓ Container cycle detection
✓ PlayerState validation (2 tests)
✓ Script validation
✓ Start location validation
✓ Vocabulary validation
✓ Door validation

### Serialization (5 tests)
✓ Dict serialization
✓ JSON string formatting
✓ File I/O round-trip
✓ Extra field preservation
✓ Invalid state handling

### Models (5 tests)
✓ Field defaults
✓ Container structure
✓ Enum conversion
✓ to_dict/from_dict
✓ State dictionaries

### Error Handling (5 tests)
✓ Error aggregation
✓ Schema errors
✓ Type mismatches
✓ ID format errors
✓ Warning handling

### Integration (4 tests)
✓ End-to-end loading
✓ Caching behavior
✓ Forward compatibility
✓ Full round-trip

## Running Tests

### Option 1: Using Makefile
```bash
cd tests/state_manager
make test                 # Run all tests
make test-validators      # Run only validator tests
make test-loader          # Run only loader tests
```

### Option 2: Using run_tests.py
```bash
cd tests/state_manager
python run_tests.py       # Run all tests
python run_tests.py -v    # Verbose output
python run_tests.py validators  # Specific module
```

### Option 3: Using unittest
```bash
# From project root
python -m unittest test.state_manager.test_validators -v

# From test directory
cd tests/state_manager
python -m unittest discover . -v
```

## Implementation Status

All tests are **stubbed with TODO comments** and will pass (skip) until the state manager is implemented.

To implement:
1. Create `src/state_manager/` directory
2. Implement modules in order:
   - `exceptions.py` - Error classes
   - `models.py` - Dataclasses
   - `loader.py` - JSON loading
   - `validators.py` - Validation rules
   - `serializer.py` - JSON output
3. Uncomment test code incrementally
4. Run tests to verify implementation

## Fixture Design

All fixtures use **V2.0 ID design**:
- Internal unique IDs (`loc_1`, `item_1`, etc.)
- Global ID uniqueness enforced
- Array storage for locations/locks
- No special inventory prefixes
- Reserved `"player"` ID

Example valid structure:
```json
{
  "locations": [
    {"id": "loc_1", "name": "Entrance", ...}
  ],
  "items": [
    {"id": "item_1", "location": "player", ...}
  ]
}
```

## Next Steps

1. Implement `src/state_manager/exceptions.py`
2. Implement `src/state_manager/models.py`
3. Uncomment and run `test_models.py`
4. Implement `src/state_manager/loader.py`
5. Uncomment and run `test_loader.py`
6. Implement `src/state_manager/validators.py`
7. Uncomment and run `test_validators.py`
8. Implement `src/state_manager/serializer.py`
9. Uncomment and run `test_serializer.py`
10. Run full test suite and verify >95% coverage

## Test Quality Standards

- All test cases have descriptive docstrings
- Test IDs match specification (TL-001, TV-001, etc.)
- Clear error messages with expected vs actual
- Fixtures are minimal but comprehensive
- Helper functions reduce duplication
- Tests are independent (no shared state)
- Each test validates one specific behavior

## Coverage Target

**Goal: >95% code coverage** across:
- `src/state_manager/loader.py`
- `src/state_manager/serializer.py`
- `src/state_manager/validators.py`
- `src/state_manager/models.py`
- `src/state_manager/exceptions.py`

Use `coverage.py` to measure:
```bash
pip install coverage
coverage run -m unittest discover tests/state_manager
coverage report
coverage html  # Generate HTML report
```
