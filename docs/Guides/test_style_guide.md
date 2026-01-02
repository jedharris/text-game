# Test Style Guide

This guide defines the canonical structure for all test files in the text-game project.

## Quick Reference

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

**DO** use base classes from `conftest.py`:
- `BaseTestCase` - Minimal state, no behaviors
- `BehaviorTestCase` - With behaviors loaded
- `SimpleGameTestCase` - Full simple_game state

**DON'T** inherit directly from `unittest.TestCase` unless you have a specific reason.

```python
# GOOD
class TestMyFeature(BaseTestCase):
    def setUp(self):
        super().setUp()

# BAD
class TestMyFeature(unittest.TestCase):
    def setUp(self):
        self.game_state = create_test_state()
        # ... manual setup
```

### 2. Always Call super().setUp()

**DO** call `super().setUp()` first in your setUp method:

```python
# GOOD
def setUp(self):
    super().setUp()  # Gets game_state, accessor, etc.
    self.actor = self.game_state.actors[ActorId("player")]

# BAD - breaks inheritance chain
def setUp(self):
    self.game_state = create_test_state()
    # Doesn't call super()
```

### 3. Use Consistent Naming

**DO** use `self.behavior_manager` (never `self.manager`):

```python
# GOOD
def setUp(self):
    super().setUp()
    self.behavior_manager = BehaviorManager()

# BAD - inconsistent naming
def setUp(self):
    super().setUp()
    self.manager = BehaviorManager()
```

### 4. Create StateAccessor in setUp

**DO** create `self.accessor` in setUp method:

```python
# GOOD
def setUp(self):
    super().setUp()
    self.accessor = StateAccessor(self.game_state, self.behavior_manager)

def test_something(self):
    result = some_function(self.accessor, ...)

# BAD - creates accessor locally in each test
def test_something(self):
    accessor = StateAccessor(self.game_state, None)
    result = some_function(accessor, ...)
```

### 5. Follow Correct Setup Order

**DO** create accessor AFTER loading behaviors:

```python
# GOOD - correct order
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

    # 4. Create handlers/other objects
    self.handler = LLMProtocolHandler(self.game_state, behavior_manager=self.behavior_manager)

# BAD - accessor created before behaviors loaded
def setUp(self):
    self.game_state = load_game_state(...)
    self.behavior_manager = BehaviorManager()
    self.accessor = StateAccessor(self.game_state, self.behavior_manager)  # Too early!

    # Behaviors loaded after accessor created
    modules = self.behavior_manager.discover_modules(...)
    self.behavior_manager.load_modules(modules)
```

**Why it matters**: While the accessor will still work, creating it before loading behaviors is poor practice and suggests confusion about the setup dependencies.

### 6. Use conftest Helpers

**DO** use helper functions from `conftest.py`:
- `create_test_state()` - Minimal game state
- `make_action()` - Create action dicts with WordEntry objects
- `make_word_entry()` - Create WordEntry objects
- `make_game_data()` - Create game state dicts for load_game_state()

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

### 7. No sys.path Manipulation in Unit Tests

**DON'T** manipulate `sys.path` in regular unit tests:

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

**CRITICAL EXCEPTION**: Tests that manipulate sys.path AND use GameEngine with game-specific behaviors MUST use subprocess isolation (see "When to Use Subprocess Isolation" below).

### 8. Consistent Import Order

**DO** follow this import order:

1. Standard library (pathlib, typing, unittest)
2. src modules (state_manager, behavior_manager, etc.)
3. tests modules (conftest)
4. Local test helpers

```python
# GOOD
from pathlib import Path
from typing import Any, Dict
import unittest

from src.state_manager import GameState
from src.behavior_manager import BehaviorManager
from src.state_accessor import StateAccessor
from tests.conftest import BaseTestCase, create_test_state

# Local helpers or fixtures here

class TestFeature(BaseTestCase):
    pass
```

---

## Complete Examples

### Unit Test (No Behaviors)

```python
"""Tests for utility function X."""
import unittest

from src.types import ActorId, ItemId
from tests.conftest import BaseTestCase


class TestUtilityFunction(BaseTestCase):
    """Test utility function X."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.actor = self.game_state.actors[ActorId("player")]

    def test_basic_case(self):
        """Test basic functionality."""
        result = utility_function(self.accessor, self.actor)
        self.assertTrue(result)

    def test_edge_case(self):
        """Test edge case."""
        result = utility_function(self.accessor, None)
        self.assertFalse(result)
```

### Unit Test (With Behaviors)

```python
"""Tests for behavior X."""
import unittest

from src.types import ActorId
from tests.conftest import BehaviorTestCase
from behaviors.core import interaction


class TestInteractionBehavior(BehaviorTestCase):
    """Test interaction behavior."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()  # Provides game_state, behavior_manager, accessor
        self.actor = self.game_state.actors[ActorId("player")]

        # Load specific behavior module
        self.behavior_manager.load_module(interaction)

    def test_interaction_success(self):
        """Test successful interaction."""
        context = {"actor_id": "player"}
        result = interaction.on_examine(self.actor, self.accessor, context)
        self.assertIsNotNone(result)
        self.assertTrue(result.allow)
```

### Integration Test (Full Game)

```python
"""Integration tests for simple_game."""
import unittest

from src.types import ActorId
from tests.conftest import SimpleGameTestCase, make_action


class TestSimpleGamePuzzle(SimpleGameTestCase):
    """Test complete puzzle solution."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()  # Provides full simple_game state
        self.player = self.game_state.actors[ActorId("player")]

    def test_unlock_treasure_room(self):
        """Test unlocking and entering treasure room."""
        # Player starts in hallway
        self.assertEqual(self.player.location, "loc_hallway")

        # Take the key
        action = make_action(verb="take", object="key")
        # ... test logic

        # Unlock door
        action = make_action(verb="unlock", object="door")
        # ... test logic

        # Enter treasure room
        action = make_action(verb="east")
        # ... test logic
```

---

## Integration Testing

For tests that need to load game-specific behaviors, use the subprocess isolation pattern.

### When to Use

Use subprocess isolation when:
- Testing a complete example game (big_game, spatial_game, etc.)
- Loading game-specific behaviors from `examples/<game>/behaviors/`
- Multiple test files would load different `behaviors.*` modules

### Structure

Create two files:

1. **Implementation file** (`tests/_<game>_scenarios_impl.py`):
```python
"""Implementation of <game> scenario tests.

DO NOT import this module directly - it will cause module pollution.
Run via test_<game>_scenarios.py wrapper instead.
"""
import sys
import unittest
from pathlib import Path

# Path setup
GAME_DIR = (Path(__file__).parent.parent / 'examples' / '<game>').resolve()
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def _setup_paths():
    """Set up sys.path for game-specific behaviors."""
    while '' in sys.path:
        sys.path.remove('')

    game_dir_str = str(GAME_DIR)
    if game_dir_str not in sys.path:
        sys.path.insert(0, game_dir_str)

    project_str = str(PROJECT_ROOT)
    if project_str not in sys.path:
        sys.path.insert(1, project_str)

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
        # Test logic
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
```

2. **Wrapper file** (`tests/test_<game>_scenarios.py`):
```python
"""Integration tests for <game> scenarios.

Runs scenario tests in isolated subprocesses to avoid module caching issues.
"""
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
            [
                sys.executable,
                '-m', 'unittest',
                f'tests._<game>_scenarios_impl.{class_name}',
                '-v'
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

    def test_game_feature(self):
        """Test game feature."""
        result = self._run_test_class('TestGameFeature')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


if __name__ == '__main__':
    unittest.main()
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

# Custom WordEntry (if you need specific word_type)
from src.word_entry import WordType
key_word = make_word_entry("key", WordType.NOUN, synonyms=["keycard"])
action = {"verb": "take", "object": key_word}
```

### Extracting Test Results

```python
# For NarrationResult format (Phase 4+)
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

## Anti-Patterns

### ❌ Duplicate BehaviorManager

```python
# BAD - creates TWO separate managers!
def setUp(self):
    self.game_state = load_game_state(...)
    self.manager = BehaviorManager()  # First one
    self.accessor = StateAccessor(self.game_state, self.manager)

    self.behavior_manager = BehaviorManager()  # Second one!
    self.behavior_manager.load_modules(...)  # Only this one has behaviors
    # accessor uses empty self.manager!
```

**Fix**: Use one manager with consistent naming:
```python
# GOOD
def setUp(self):
    super().setUp()
    self.behavior_manager = BehaviorManager()
    # Load behaviors into behavior_manager
    self.accessor = StateAccessor(self.game_state, self.behavior_manager)
```

### ❌ StateAccessor with None

```python
# BAD - can't invoke behaviors
def test_something(self):
    accessor = StateAccessor(game_state, None)
```

**Fix**: Use BaseTestCase or BehaviorTestCase which provide proper accessor:
```python
# GOOD
class TestFeature(BehaviorTestCase):
    def test_something(self):
        # self.accessor already has behavior_manager
        result = handler(self.accessor, ...)
```

### ❌ Local Accessor Creation

```python
# BAD - creates new accessor in each test
def test_one(self):
    accessor = StateAccessor(self.game_state, self.behavior_manager)

def test_two(self):
    accessor = StateAccessor(self.game_state, self.behavior_manager)
```

**Fix**: Create once in setUp:
```python
# GOOD
def setUp(self):
    super().setUp()
    # self.accessor available to all tests

def test_one(self):
    result = handler(self.accessor, ...)
```

### ❌ Duplicate Manager (Same Name)

```python
# BAD - creates manager twice, wasting first one
def setUp(self):
    self.game_state = load_game_state(...)
    self.behavior_manager = BehaviorManager()
    self.accessor = StateAccessor(self.game_state, self.behavior_manager)  # Uses empty manager!

    # Create AGAIN and load behaviors
    self.behavior_manager = BehaviorManager()
    modules = self.behavior_manager.discover_modules(...)
    self.behavior_manager.load_modules(modules)
```

**Fix**: Create once, in correct order:
```python
# GOOD
def setUp(self):
    self.game_state = load_game_state(...)

    # Create and configure manager
    self.behavior_manager = BehaviorManager()
    modules = self.behavior_manager.discover_modules(...)
    self.behavior_manager.load_modules(modules)

    # Now create accessor
    self.accessor = StateAccessor(self.game_state, self.behavior_manager)
```

### ❌ Inconsistent Naming

```python
# BAD - mixing names
self.manager = BehaviorManager()
self.behavior_manager = BehaviorManager()
manager = BehaviorManager()
```

**Fix**: Always use `self.behavior_manager`:
```python
# GOOD
self.behavior_manager = BehaviorManager()
```

### ❌ Manual Game State Construction

```python
# BAD - verbose and error-prone
def test_something(self):
    game_state = GameState(
        metadata={"title": "Test", "version": "1.0"},
        locations=[...],
        items=[...],
        # ... many more fields
    )
```

**Fix**: Use helpers:
```python
# GOOD
from tests.conftest import create_test_state, make_game_data

def test_something(self):
    game_state = create_test_state()  # Or use BaseTestCase
```

---

## Troubleshooting

### "No module named 'behaviors.xxx'"

**Cause**: Game directory not in sys.path (integration tests only)

**Fix**: Use the subprocess isolation pattern with `_setup_paths()`

### Tests pass individually but fail in discovery

**Cause**: Module caching between tests

**Fix**: Use subprocess isolation for integration tests

### "AttributeError: 'NoneType' object has no attribute 'invoke_behavior'"

**Cause**: StateAccessor created with `None` as behavior_manager

**Fix**: Use `BehaviorTestCase` or pass actual BehaviorManager instance

### Duplicate BehaviorManager instances

**Cause**: Creating both `self.manager` and `self.behavior_manager`

**Fix**: Use only `self.behavior_manager`, ensure accessor uses it

---

## Checklist for New Tests

- [ ] Inherits from `BaseTestCase`, `BehaviorTestCase`, or `SimpleGameTestCase`
- [ ] Calls `super().setUp()` in setUp method
- [ ] Uses `self.behavior_manager` (not `self.manager`)
- [ ] Creates `self.accessor` in setUp (not in individual tests)
- [ ] Uses `conftest` helpers (`make_action`, `make_word_entry`, etc.)
- [ ] No `sys.path` manipulation (unless integration test)
- [ ] Consistent import ordering
- [ ] Docstrings for module, class, and test methods
- [ ] Passes when run individually
- [ ] Passes when run via `unittest discover`

---

## Reference: conftest.py Base Classes

### BaseTestCase
- **Provides**: `self.game_state`, `self.accessor` (no behaviors)
- **Use for**: Unit tests that don't invoke behaviors
- **Example**: Testing utility functions, state accessors

### BehaviorTestCase
- **Provides**: `self.game_state`, `self.behavior_manager`, `self.accessor`
- **Use for**: Tests that invoke behavior handlers
- **Example**: Testing behavior modules, handler functions

### SimpleGameTestCase
- **Provides**: Full simple_game state, `self.behavior_manager`, `self.accessor`
- **Use for**: Integration tests using simple_game
- **Example**: Multi-step puzzle tests, full command flow tests

---

## When to Use Subprocess Isolation

### The Problem

Tests that manipulate `sys.path` and load game-specific behaviors via `GameEngine` cause **module cache pollution**. Python caches imported modules in `sys.modules`, so when tests load behaviors with short names like `behaviors.magic_star`, those modules persist across tests and cause context-dependent failures.

### Symptoms

- Test passes when run individually: `python -m unittest tests.test_foo -v` ✅
- Test fails when run in discovery: `python -m unittest discover -s tests` ❌
- Failure depends on which other tests ran first
- Import errors or wrong behavior implementations

### When Isolation is Required

Use the two-file subprocess isolation pattern when ALL of these are true:

1. ✅ Test manipulates `sys.path` (adds game directory to path)
2. ✅ Test uses `GameEngine(GAME_DIR)` to load a game
3. ✅ Game has custom behaviors in its `behaviors/` directory

### How to Use Subprocess Isolation

Create two files:

**`tests/test_<game>_scenarios.py`** (wrapper):
```python
"""Integration tests for <game> scenarios."""
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

class Test<Game>Scenarios(unittest.TestCase):
    """Run <game> scenario tests in isolated subprocesses."""

    def _run_test_class(self, class_name: str) -> subprocess.CompletedProcess:
        """Run a single test class in a subprocess."""
        return subprocess.run(
            [
                sys.executable,
                '-m', 'unittest',
                f'tests._<game>_scenarios_impl.{class_name}',
                '-v'
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )

    def test_feature_x(self):
        """Test feature X."""
        result = self._run_test_class('TestFeatureX')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")
```

**`tests/_<game>_scenarios_impl.py`** (implementation):
```python
"""Implementation of <game> scenario tests.

DO NOT import this module directly - it will cause module pollution.
Run via test_<game>_scenarios.py wrapper.
"""
import sys
from pathlib import Path

GAME_DIR = (Path(__file__).parent.parent / 'examples' / '<game>').resolve()
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def _setup_paths():
    """Ensure game directory is first in sys.path."""
    while '' in sys.path:
        sys.path.remove('')
    if str(GAME_DIR) not in sys.path:
        sys.path.insert(0, str(GAME_DIR))
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(1, str(PROJECT_ROOT))

_setup_paths()

from src.game_engine import GameEngine

class TestFeatureX(unittest.TestCase):
    """Test feature X in <game>."""

    def setUp(self):
        self.engine = GameEngine(GAME_DIR)
        # Test implementation
```

### Detecting Tests That Need Isolation

Run the isolation detector tool:
```bash
python tools/find_isolation_candidates.py
```

This scans all test files and reports:
- Tests that need isolation (imports GameEngine + manipulates sys.path)
- Tests already using isolation (subprocess wrapper pattern)
- Tests that don't need isolation

### When NOT to Use Isolation

Don't use subprocess isolation for:
- Tests importing behaviors with absolute paths: `from examples.big_game.behaviors.regions.beast_wilds.sira_rescue import on_sira_encounter`
- Tests using only `behavior_libraries` imports
- Tests using `GameEngine` with games that have no custom behaviors (e.g., simple_game)
- Regular unit tests of src/ modules

### Related Documentation

- [integration_testing.md](integration_testing.md) - Full guide to integration test structure
- [test_isolation_analysis.md](test_isolation_analysis.md) - Deep dive into isolation patterns
- [test_isolation_root_cause.md](test_isolation_root_cause.md) - Technical details of module cache pollution

---

## Migration Strategy

When updating existing tests:

1. **Fix critical bugs first** (duplicate managers, None accessor)
2. **Standardize naming** (`self.manager` → `self.behavior_manager`)
3. **Move to base classes** (inherit from BaseTestCase/BehaviorTestCase)
4. **Add super().setUp() calls**
5. **Use conftest helpers**
6. **Remove sys.path manipulation** (unless test needs isolation)
7. **Check if isolation needed** (run `tools/find_isolation_candidates.py`)
8. **Validate** - run both individually and via discovery

This can be done incrementally as you touch test files for other work.
