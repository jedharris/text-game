# State Manager Test Suite

This test suite validates the game state manager implementation according to the specification in `docs/state_manager_testing.md`.

## Directory Structure

```
tests/state_manager/
  __init__.py                    # Package initialization
  README.md                      # This file
  test_helpers.py                # Helper utilities for tests
  test_loader.py                 # Loader functionality tests (TL-001 to TL-007)
  test_serializer.py             # Serialization tests (TS-001 to TS-005)
  test_models.py                 # Data model tests (TM-001 to TM-005)
  test_validators.py             # Validation tests (TV-001 to TV-018)
  test_error_handling.py         # Error handling tests (TE-001 to TE-005)
  test_regressions.py            # Integration tests (TR-001 to TR-004)
  fixtures/                      # Test fixture JSON files
    valid_world.json             # Complete valid game state
    minimal_world.json           # Minimal valid game state
    missing_sections.json        # Missing required metadata
    duplicate_ids.json           # Duplicate location IDs
    global_id_collision.json     # ID collision across entity types
    reserved_id_violation.json   # Entity using reserved "player" ID
    bad_references.json          # Exit pointing to nonexistent location
    container_cycle.json         # Circular container containment
    invalid_exits.json           # Exit missing required door_id
    invalid_locks.json           # Door referencing undefined lock
    invalid_scripts.json         # Script referencing nonexistent entity
    invalid_player_state.json    # PlayerState with invalid references
    invalid_item_location.json   # Item with invalid location reference
```

## Running Tests

### Run all tests
```bash
cd /Users/jed/Development/text-game
python -m unittest discover tests/state_manager
```

### Run specific test module
```bash
python -m unittest tests.state_manager.test_validators
```

### Run specific test case
```bash
python -m unittest tests.state_manager.test_validators.TestValidators.test_TV001_global_id_uniqueness_duplicate_raises_error
```

### Run with verbose output
```bash
python -m unittest discover tests/state_manager -v
```

## Test Coverage

### Loader Tests (test_loader.py)
- **TL-001**: Load full fixture from file path
- **TL-002**: Load from file-like object (StringIO)
- **TL-003**: Load minimal world with defaults
- **TL-004**: Unknown top-level keys preserved
- **TL-005**: Invalid JSON raises SchemaError
- **TL-006**: Missing file raises FileLoadError
- **TL-007**: Loader accepts already-parsed dict

### Serializer Tests (test_serializer.py)
- **TS-001**: Serialize to dict matches loaded JSON
- **TS-002**: Serialize to JSON string with pretty-print
- **TS-003**: Save to file and re-load
- **TS-004**: Preserve unknown/extra fields
- **TS-005**: Serialize invalid state raises ValidationError

### Model Tests (test_models.py)
- **TM-001**: Dataclass field defaults
- **TM-002**: Container items reference ContainerInfo
- **TM-003**: Enum string conversion
- **TM-004**: Round-trip with to_dict() helper
- **TM-005**: Item states dictionary

### Validator Tests (test_validators.py)
- **TV-001**: Global ID uniqueness - duplicates raise error
- **TV-002**: Global ID collision (location vs item)
- **TV-003**: Reserved ID "player" validation
- **TV-004**: Exit to nonexistent location
- **TV-005**: Door reference missing
- **TV-006**: Lock reference undefined
- **TV-007**: Item location consistency
- **TV-008**: Container cycle detection
- **TV-009**: Start location missing
- **TV-010**: Vocabulary alias validation
- **TV-011**: Script references validation
- **TV-012**: Door one-way conditions
- **TV-013**: PlayerState location exists
- **TV-014**: PlayerState inventory items exist
- **TV-015**: Item location "player" valid
- **TV-016**: Item location NPC validated
- **TV-017**: Item location container validated
- **TV-018**: Item location invalid type

### Error Handling Tests (test_error_handling.py)
- **TE-001**: Multiple errors aggregated
- **TE-002**: Schema error for missing sections
- **TE-003**: Type mismatch error
- **TE-004**: Non-string keys error
- **TE-005**: Warnings don't abort parsing

### Regression Tests (test_regressions.py)
- **TR-001**: Realistic world end-to-end
- **TR-002**: Caching behavior
- **TR-003**: Forward compatibility with extra fields
- **TR-004**: Full round-trip (load → serialize → reload)

## Test Status

All tests are currently stubbed with TODO comments. They will be implemented once the state manager modules are available:

- `src/state_manager/models.py`
- `src/state_manager/loader.py`
- `src/state_manager/serializer.py`
- `src/state_manager/validators.py`
- `src/state_manager/exceptions.py`

## Test Fixtures

All fixtures conform to the V2.0 game state specification with:
- Internal unique IDs separate from user-visible names
- Global ID uniqueness across all entity types
- Array-based storage for locations and locks
- Simple ID references (no prefixes)

See `docs/game_state_spec.md` and `docs/ID_NAMESPACE_DESIGN.md` for details.

## Helper Functions

The `test_helpers.py` module provides:
- `load_fixture(filename)` - Load JSON fixture
- `get_fixture_path(filename)` - Get fixture file path
- `assert_validation_error_contains(error, substring)` - Check error message
- `assert_ids_match(actual, expected)` - Compare ID sets
- `normalize_json(data)` - Normalize for comparison
- `json_equal(data1, data2)` - Semantic JSON equality

## Implementation Notes

When implementing the state manager:

1. Start with `models.py` to define dataclasses
2. Implement `exceptions.py` for error types
3. Implement `loader.py` for JSON parsing
4. Implement `validators.py` for validation rules
5. Implement `serializer.py` for JSON output
6. Uncomment and run tests incrementally

Target coverage: >95% across all state manager modules.
