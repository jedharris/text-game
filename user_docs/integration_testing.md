# Integration Testing for Example Games

This document describes how to create integration tests that run complex scenarios in example games. These tests catch bugs that unit tests miss by testing the full stack from command input to output.

## Why Integration Tests?

Unit tests verify individual components work correctly in isolation. Integration tests verify that:
- Behaviors are loaded and invoked correctly
- Visibility checks work with custom behaviors
- Multi-step puzzles can be solved
- The full command → handler → behavior → response chain works

## Architecture

Integration tests use a two-file structure to handle Python's module caching:

```
tests/
├── test_<game>_scenarios.py      # Wrapper that runs tests in subprocesses
└── _<game>_scenarios_impl.py     # Actual test implementations
```

### Why Subprocesses?

Each example game has its own `behaviors/` directory. Python caches modules by name, so if `behaviors.magic_star` is loaded from one game, it can't be loaded from a different game in the same process. Running each test class in a subprocess ensures a fresh Python state.

## Creating Integration Tests

### Step 1: Create the Implementation File

Create `tests/_<game>_scenarios_impl.py` with this structure:

```python
"""Implementation of <game> scenario tests.

This module contains the actual test implementations. Each test class
should be run in its own subprocess by test_<game>_scenarios.py
to ensure module isolation.

DO NOT import this module directly in the test suite - it will cause
module pollution issues.
"""

import sys
import unittest
from pathlib import Path


# Path to game - must be absolute before importing game modules
GAME_DIR = (Path(__file__).parent.parent / 'examples' / '<game>').resolve()
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def _setup_paths():
    """Ensure game directory is first in sys.path for behaviors imports.

    The game directory is added first so that its behaviors/ package is found
    before the project root's behaviors/ package.

    IMPORTANT: We remove '' (current directory) from path because when running
    from project root, Python would find behaviors/ from project root before
    finding it from the game directory.
    """
    # Remove CWD ('') from path to prevent project root behaviors from being found
    while '' in sys.path:
        sys.path.remove('')

    # Add game directory first (for behaviors imports)
    game_dir_str = str(GAME_DIR)
    if game_dir_str not in sys.path:
        sys.path.insert(0, game_dir_str)

    # Add project root after (for src imports)
    project_str = str(PROJECT_ROOT)
    if project_str not in sys.path:
        sys.path.insert(1, project_str)


# Set up paths before importing game modules
_setup_paths()

from src.game_engine import GameEngine
from src.text_game import format_command_result


class TestYourFeature(unittest.TestCase):
    """Test description here."""

    def setUp(self):
        """Set up game engine."""
        self.engine = GameEngine(GAME_DIR)
        self.actor = self.engine.game_state.actors['player']  # Human-controlled actor

    def _execute(self, verb, obj=None):
        """Execute a command and return the response."""
        action = {"verb": verb}
        if obj:
            action["object"] = obj
        return self.engine.json_handler.handle_message({
            "type": "command",
            "action": action
        })

    def _look(self):
        """Execute look and return formatted output."""
        response = self._execute("look")
        return format_command_result(response)

    def test_something(self):
        """Test description."""
        # Set up initial state
        self.actor.location = 'loc_somewhere'

        # Execute commands
        response = self._execute("do_something")

        # Assert results
        self.assertTrue(response.get("success"))


if __name__ == '__main__':
    unittest.main(verbosity=2)
```

### Step 2: Create the Wrapper File

Create `tests/test_<game>_scenarios.py`:

```python
"""Integration tests for <game> scenarios.

These tests play through actual game scenarios to catch bugs that
unit tests miss. They test the full stack from command to output.

Each test class runs in its own subprocess for complete isolation,
avoiding Python module caching issues between test runs.
"""

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

    def test_your_feature(self):
        """Test description."""
        result = self._run_test_class('TestYourFeature')
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, f"Tests failed:\n{result.stderr}")


if __name__ == '__main__':
    unittest.main()
```

### Step 3: Ensure Game Has Core Behaviors Symlink

Each example game needs a symlink to the core behaviors:

```bash
cd examples/<game>/behaviors
ln -s ../../../behaviors/core core
```

Without this symlink, the game won't have access to core verbs like `look`, `take`, `go`, etc.

## Writing Test Cases

### Testing Visibility

```python
def test_item_hidden_without_condition(self):
    """Item should not appear without meeting condition."""
    self.actor.location = 'loc_room'
    self.actor.inventory = []  # No magic item

    output = self._look()

    self.assertNotIn("secret door", output)

def test_item_visible_with_condition(self):
    """Item should appear when condition is met."""
    self.actor.location = 'loc_room'
    self.actor.inventory = ['item_magic_lens']  # Has magic item

    output = self._look()

    self.assertIn("secret door", output)
```

### Testing Behavior Restrictions

```python
def test_cannot_take_without_condition(self):
    """Cannot take item without meeting precondition."""
    response = self._execute("take", "star")

    self.assertFalse(response.get("success"))
    # Check error message mentions the reason
    error_msg = response.get("error", {}).get("message", "")
    self.assertIn("too high", error_msg.lower())

def test_can_take_with_condition(self):
    """Can take item when precondition is met."""
    # Set up player state
    self.actor.properties["posture"] = "climbing"
    self.actor.properties["focused_on"] = "item_tree"

    response = self._execute("take", "star")

    self.assertTrue(response.get("success"))
    self.assertIn("item_star", self.actor.inventory)
```

### Testing Multi-Step Puzzles

```python
def test_complete_puzzle_solution(self):
    """Play through complete puzzle."""
    # Step 1: Go to starting location
    response = self._execute("north")
    self.assertTrue(response.get("success"))
    self.assertEqual(self.actor.location, 'loc_room1')

    # Step 2: Get required item
    response = self._execute("take", "key")
    self.assertTrue(response.get("success"))

    # Step 3: Use item
    response = self._execute("unlock", "door")
    self.assertTrue(response.get("success"))

    # Step 4: Enter new area
    response = self._execute("east")
    self.assertTrue(response.get("success"))
    self.assertEqual(self.actor.location, 'loc_treasure_room')
```

### Testing with WordEntry Objects

When testing commands that need proper vocabulary matching:

```python
def _execute(self, verb, obj=None):
    """Execute a command and return the response."""
    from src.word_entry import WordEntry, WordType
    action = {"verb": verb}
    if obj:
        if isinstance(obj, str):
            action["object"] = WordEntry(obj, {WordType.NOUN}, [])
        else:
            action["object"] = obj
    return self.engine.json_handler.handle_message({
        "type": "command",
        "action": action
    })
```

## Common Patterns

### Getting Error Messages

Responses have different structures for success vs failure:

```python
def _get_message(self, response):
    """Get message from response (handles both success and error formats)."""
    if response.get("success"):
        return response.get("message", "")
    else:
        return response.get("error", {}).get("message", "")
```

### Setting Up Actor State

```python
# Location
self.actor.location = 'loc_garden'

# Inventory
self.actor.inventory = ['item_key', 'item_sword']

# Properties (for spatial behaviors)
self.actor.properties["posture"] = "on_surface"
self.actor.properties["focused_on"] = "item_bench"

# Flags
self.actor.properties["flags"]["has_spoken_to_wizard"] = True
```

### Modifying Item State

```python
# Get an item
star = next(i for i in self.engine.game_state.items if i.id == 'item_star')

# Change its location
star.location = 'loc_garden'  # On ground, not in container

# Change its properties
star.properties["lit"] = True
```

## Running Tests

### Run All Integration Tests

```bash
python -m unittest tests.test_<game>_scenarios -v
```

### Run Single Test Class

```bash
python -m unittest tests._<game>_scenarios_impl.TestYourFeature -v
```

### Run Single Test Method

```bash
python -m unittest tests._<game>_scenarios_impl.TestYourFeature.test_something -v
```

### Run as Part of Full Suite

```bash
python -m unittest discover -s tests
```

## Troubleshooting

### "No module named 'behaviors.xxx'"

**Cause**: The game directory isn't in sys.path, or another behaviors package is being found first.

**Fix**: Ensure `_setup_paths()` removes `''` from sys.path and adds the game directory at index 0.

### Tests Pass Individually But Fail in Suite

**Cause**: Module caching between tests.

**Fix**: Ensure each test class runs in its own subprocess via the wrapper file.

### Behaviors Not Being Invoked

**Cause**: The entity doesn't have behaviors attached, or the behavior module isn't loaded.

**Check**:
1. Entity has `behaviors: ["behaviors.module_name"]` in game_state.json
2. The behavior module exists in `examples/<game>/behaviors/`
3. The behavior module defines the expected function (e.g., `on_take`, `on_observe`)

### "I don't understand 'look'"

**Cause**: Core behaviors aren't loaded.

**Fix**: Ensure the game has `behaviors/core` symlink pointing to `../../../behaviors/core`.

## Checklist for New Integration Tests

- [ ] Create `tests/_<game>_scenarios_impl.py` with path setup
- [ ] Create `tests/test_<game>_scenarios.py` wrapper
- [ ] Ensure game has `behaviors/core` symlink
- [ ] Test passes when run directly: `python tests/_<game>_scenarios_impl.py`
- [ ] Test passes via unittest: `python -m unittest tests.test_<game>_scenarios`
- [ ] Test passes in full suite: `python -m unittest discover -s tests`
