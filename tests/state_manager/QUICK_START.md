# Quick Start Guide - State Manager Tests

## For Test Users

### Run all tests
```bash
cd tests/state_manager
make test
```

### Run specific test module
```bash
make test-validators     # Validation tests
make test-loader         # Loader tests
make test-serializer     # Serializer tests
```

### Check test status
```bash
python run_tests.py -v
```

All tests are currently **stubbed** and will pass until implementation begins.

## For Implementers

### Step 1: Create module structure
```bash
mkdir -p src/state_manager
touch src/state_manager/__init__.py
```

### Step 2: Implement exceptions
Create `src/state_manager/exceptions.py`:
```python
class GameStateError(Exception):
    """Base exception for game state errors."""
    pass

class SchemaError(GameStateError):
    """Schema validation error."""
    pass

class ValidationError(GameStateError):
    """Cross-reference validation error."""
    def __init__(self, errors):
        self.errors = errors if isinstance(errors, list) else [errors]
        super().__init__(f"Found {len(self.errors)} validation errors")

class FileLoadError(GameStateError):
    """File loading error."""
    pass
```

Uncomment tests in `test_error_handling.py` and verify they pass.

### Step 3: Implement models
Create `src/state_manager/models.py` with dataclasses for:
- `Metadata`
- `Vocabulary`
- `Location`, `ExitDescriptor`
- `Door`
- `Item`, `ContainerInfo`
- `Lock`
- `Npc`
- `Script`, `ScriptTrigger`, `ScriptEffect`
- `PlayerState`
- `GameState`

Uncomment tests in `test_models.py` and verify they pass.

### Step 4: Implement loader
Create `src/state_manager/loader.py`:
```python
from pathlib import Path
from typing import Union, Dict, Any, IO
import json

def load_game_state(source: Union[str, Path, IO]) -> 'GameState':
    """Load game state from file or stream."""
    # Implementation here
    pass

def parse_game_state(data: Dict[str, Any]) -> 'GameState':
    """Parse game state from dict."""
    # Implementation here
    pass
```

Uncomment tests in `test_loader.py` incrementally.

### Step 5: Implement validators
Create `src/state_manager/validators.py`:
```python
def build_global_id_registry(game_state):
    """Build registry of all IDs."""
    pass

def validate_global_uniqueness(registry):
    """Ensure all IDs globally unique."""
    pass

def validate_references(game_state, registry):
    """Validate all cross-references."""
    pass
```

Uncomment tests in `test_validators.py` incrementally.

### Step 6: Implement serializer
Create `src/state_manager/serializer.py`:
```python
def game_state_to_dict(state: 'GameState') -> Dict[str, Any]:
    """Convert GameState to dict."""
    pass

def save_game_state(state: 'GameState', destination, validate=True):
    """Save GameState to file."""
    pass
```

Uncomment tests in `test_serializer.py` incrementally.

### Step 7: Run full test suite
```bash
cd tests/state_manager
make test
```

Target: All 44 tests passing with >95% coverage.

## Test File Reference

| File | Tests | Purpose |
|------|-------|---------|
| test_loader.py | 7 | JSON loading and parsing |
| test_validators.py | 18 | Validation rules (ID uniqueness, references) |
| test_serializer.py | 5 | JSON serialization and file I/O |
| test_models.py | 5 | Dataclass behavior and structure |
| test_error_handling.py | 5 | Error reporting and aggregation |
| test_regressions.py | 4 | Integration and round-trip tests |

## Fixture Reference

| Fixture | Purpose |
|---------|---------|
| valid_world.json | Complete valid game state (all features) |
| minimal_world.json | Minimal valid configuration |
| valid_world_canonical.json | Expected serializer output (sorted) |
| global_id_collision.json | ID collision test |
| reserved_id_violation.json | Reserved "player" ID test |
| bad_references.json | Missing reference test |
| container_cycle.json | Circular containment test |
| invalid_*.json | Various error conditions |

## Helper Functions

```python
from test_helpers import (
    load_fixture,           # Load JSON fixture by name
    get_fixture_path,       # Get path to fixture
    json_equal,             # Compare JSON semantically
    normalize_json,         # Sort and format JSON
    assert_validation_error_contains  # Check error message
)
```

## Coverage Measurement

```bash
pip install coverage
cd tests/state_manager
coverage run -m unittest discover .
coverage report -m
coverage html
open htmlcov/index.html  # View detailed report
```

## Common Issues

**Import errors**: Make sure `src/state_manager/__init__.py` exists

**Test failures**: Tests are stubbed - failures only occur if you uncomment incomplete implementation

**Fixture not found**: Run tests from `tests/state_manager` directory or use absolute paths

**Coverage too low**: Focus on `validators.py` - it has the most complex logic to test
