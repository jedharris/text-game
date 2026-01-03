# Test Authoring Guide

**Purpose:** Quick reference for writing tests. For complete patterns and troubleshooting, see [test_style_guide.md](test_style_guide.md).

---

## Quick Start Template

```python
"""Test module docstring."""
from pathlib import Path
import unittest

from src.state_manager import GameState
from src.behavior_manager import BehaviorManager
from src.state_accessor import StateAccessor
from tests.conftest import BaseTestCase, create_test_state


class TestFeature(BaseTestCase):
    """Test class docstring."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()  # Provides: game_state, accessor
        # Additional setup if needed

    def test_something(self):
        """Test method docstring."""
        # Test implementation
        pass
```

---

## Core Principles

### 1. Always Inherit from Base Classes

Use base classes from `conftest.py`:

- **BaseTestCase** - Minimal state, no behaviors
- **BehaviorTestCase** - With behaviors loaded
- **SimpleGameTestCase** - Full simple_game state

```python
# GOOD
class TestMyFeature(BaseTestCase):
    def setUp(self):
        super().setUp()

# BAD - manual setup
class TestMyFeature(unittest.TestCase):
    def setUp(self):
        self.game_state = create_test_state()
```

### 2. Always Call super().setUp()

```python
# GOOD
def setUp(self):
    super().setUp()  # Gets game_state, accessor, etc.
    self.actor = self.game_state.actors[ActorId("player")]

# BAD - breaks inheritance
def setUp(self):
    self.game_state = create_test_state()
```

### 3. Use Consistent Naming

```python
# GOOD - always use self.behavior_manager
def setUp(self):
    super().setUp()
    self.behavior_manager = BehaviorManager()

# BAD - inconsistent
def setUp(self):
    super().setUp()
    self.manager = BehaviorManager()  # Don't abbreviate
```

### 4. Correct Setup Order

```python
# GOOD - accessor created AFTER behaviors loaded
def setUp(self):
    super().setUp()

    # 1. Load game state
    self.game_state = load_game_state(...)

    # 2. Create and configure behavior manager
    self.behavior_manager = BehaviorManager()
    modules = self.behavior_manager.discover_modules(str(behaviors_dir))
    self.behavior_manager.load_modules(modules)

    # 3. Create accessor (now behavior_manager is ready)
    self.accessor = StateAccessor(self.game_state, self.behavior_manager)

# BAD - accessor created before behaviors loaded
def setUp(self):
    self.game_state = load_game_state(...)
    self.behavior_manager = BehaviorManager()
    self.accessor = StateAccessor(self.game_state, self.behavior_manager)  # Too early!

    modules = self.behavior_manager.discover_modules(...)
    self.behavior_manager.load_modules(modules)  # Behaviors loaded after accessor
```

### 5. Use conftest Helpers

```python
# GOOD
from tests.conftest import make_action, make_word_entry

def test_take_sword(self):
    action = make_action(verb="take", object="sword")

# BAD - manual construction
def test_take_sword(self):
    from src.word_entry import WordEntry, WordType
    action = {
        "verb": "take",
        "object": WordEntry("sword", {WordType.NOUN}, [])
    }
```

### 6. No sys.path Manipulation in Unit Tests

```python
# BAD - unnecessary in unit tests
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# GOOD - tests run from project root, no path setup needed
import unittest
from src.state_manager import GameState
```

---

## Common Patterns

### Setting Up Actor State

```python
def setUp(self):
    super().setUp()
    self.actor = self.game_state.actors[ActorId("player")]

    # Set location using accessor
    self.accessor.set_entity_where(self.actor.id, "loc_garden")

    # Set properties
    self.actor.properties["posture"] = "standing"
    self.actor.properties["flags"]["has_key"] = True
```

### Creating Test Actions

```python
from tests.conftest import make_action, make_word_entry

# Simple action
action = make_action(verb="take", object="sword")

# Action with adjective
action = make_action(verb="examine", object="door", adjective="wooden")

# Action with preposition
action = make_action(
    verb="put",
    object="key",
    preposition="in",
    indirect_object="box"
)
```

### Extracting Test Results

```python
# For NarrationResult format
def _get_message(self, response):
    """Get message from response."""
    narration = response.get("narration", {})
    primary = narration.get("primary_text", "")
    secondary = narration.get("secondary_beats", [])
    return "\n".join([primary] + secondary)

# Check success
def test_success_case(self):
    result = handler(...)
    self.assertTrue(result.get("success"))
    message = self._get_message(result)
    self.assertIn("expected text", message.lower())
```

---

## Anti-Patterns to Avoid

### ❌ Duplicate BehaviorManager

```python
# BAD - creates TWO separate managers
def setUp(self):
    self.game_state = load_game_state(...)
    self.manager = BehaviorManager()  # First one
    self.accessor = StateAccessor(self.game_state, self.manager)

    self.behavior_manager = BehaviorManager()  # Second one!
    self.behavior_manager.load_modules(...)  # Only this one has behaviors

# GOOD - one manager
def setUp(self):
    super().setUp()
    self.behavior_manager = BehaviorManager()
    self.behavior_manager.load_modules(...)
    self.accessor = StateAccessor(self.game_state, self.behavior_manager)
```

### ❌ StateAccessor with None

```python
# BAD - can't invoke behaviors
def test_something(self):
    accessor = StateAccessor(game_state, None)

# GOOD - use BehaviorTestCase
class TestFeature(BehaviorTestCase):
    def test_something(self):
        result = handler(self.accessor, ...)  # accessor has behavior_manager
```

### ❌ Local Accessor Creation

```python
# BAD - creates new accessor in each test
def test_one(self):
    accessor = StateAccessor(self.game_state, self.behavior_manager)

def test_two(self):
    accessor = StateAccessor(self.game_state, self.behavior_manager)

# GOOD - create once in setUp
def setUp(self):
    super().setUp()
    # self.accessor available to all tests

def test_one(self):
    result = handler(self.accessor, ...)
```

---

## Integration Testing (Game-Specific Behaviors)

For tests loading game-specific behaviors (e.g., `examples/big_game`), use subprocess isolation to avoid module cache pollution.

### When to Use Subprocess Isolation

Use when ALL of these are true:
1. Test manipulates `sys.path` (adds game directory)
2. Test uses `GameEngine(GAME_DIR)` to load a game
3. Game has custom behaviors in its `behaviors/` directory

### Detection Tool

```bash
python tools/find_isolation_candidates.py
```

### Structure: Two-File Pattern

**Wrapper file** (`tests/test_<game>_scenarios.py`):
```python
"""Integration tests for <game> scenarios."""
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

class TestGameScenarios(unittest.TestCase):
    """Run <game> scenario tests in isolated subprocesses."""

    def _run_test_class(self, class_name: str) -> subprocess.CompletedProcess:
        """Run a single test class in a subprocess."""
        return subprocess.run(
            [sys.executable, '-m', 'unittest',
             f'tests._<game>_scenarios_impl.{class_name}', '-v'],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )

    def test_game_feature(self):
        """Test game feature."""
        result = self._run_test_class('TestGameFeature')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0)
```

**Implementation file** (`tests/_<game>_scenarios_impl.py`):
```python
"""Implementation of <game> scenario tests.

DO NOT import this module directly - run via test_<game>_scenarios.py wrapper.
"""
import sys
import unittest
from pathlib import Path

GAME_DIR = (Path(__file__).parent.parent / 'examples' / '<game>').resolve()
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def _setup_paths():
    """Set up sys.path for game-specific behaviors."""
    while '' in sys.path:
        sys.path.remove('')
    if str(GAME_DIR) not in sys.path:
        sys.path.insert(0, str(GAME_DIR))
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(1, str(PROJECT_ROOT))

_setup_paths()

from src.game_engine import GameEngine

class TestGameFeature(unittest.TestCase):
    """Test game-specific feature."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.actor = self.engine.game_state.actors['player']

    def test_something(self):
        """Test something."""
        pass

if __name__ == '__main__':
    unittest.main(verbosity=2)
```

---

## Troubleshooting

### "No module named 'behaviors.xxx'"

**Cause:** Game directory not in sys.path (integration tests only)
**Fix:** Use subprocess isolation pattern with `_setup_paths()`

### Tests pass individually but fail in discovery

**Cause:** Module caching between tests
**Fix:** Use subprocess isolation for integration tests

### "AttributeError: 'NoneType' object has no attribute 'invoke_behavior'"

**Cause:** StateAccessor created with `None` as behavior_manager
**Fix:** Use `BehaviorTestCase` or pass actual BehaviorManager instance

### Duplicate BehaviorManager instances

**Cause:** Creating both `self.manager` and `self.behavior_manager`
**Fix:** Use only `self.behavior_manager`, ensure accessor uses it

---

## Complete Test Checklist

- [ ] Inherits from `BaseTestCase`, `BehaviorTestCase`, or `SimpleGameTestCase`
- [ ] Calls `super().setUp()` in setUp method
- [ ] Uses `self.behavior_manager` (not `self.manager`)
- [ ] Creates `self.accessor` in setUp (not in individual tests)
- [ ] Uses `conftest` helpers (`make_action`, `make_word_entry`, etc.)
- [ ] No `sys.path` manipulation (unless integration test with subprocess isolation)
- [ ] Consistent import ordering
- [ ] Docstrings for module, class, and test methods
- [ ] Passes when run individually
- [ ] Passes when run via `unittest discover`

---

## Running Tests

```bash
# Run all tests
python -m unittest discover -s tests

# Run specific test file
python -m unittest tests.test_parser

# Run specific test
python -m unittest tests.test_parser.TestParserIntegration.test_full_game
```

---

## For Complete Details

See [test_style_guide.md](test_style_guide.md) for:
- Complete examples (unit tests, behavior tests, integration tests)
- Detailed anti-patterns and fixes
- Module cache pollution deep dive
- When to use subprocess isolation (full decision tree)
- Debugging context-dependent failures
