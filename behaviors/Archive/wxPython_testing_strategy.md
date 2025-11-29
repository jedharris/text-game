# wxPython UI Testing Strategy for Game Engine Integration

## Overview
This document outlines strategies for testing wxPython UI components integrated with the game engine, ensuring proper separation between UI and game logic while verifying correct interaction.

## Testing Approaches

### 1. Unit Testing (Game Logic Only)
Test game engine functions in isolation without UI.

### 2. Integration Testing (UI + Game Logic)
Test that UI correctly calls and responds to game engine functions.

### 3. UI Testing (Simulated User Interaction)
Test UI behavior by simulating user actions programmatically.

---

## Approach 1: Mock UI Pattern

### Concept
Create a mock/test UI that mimics the real wxPython interface but is easier to test programmatically.

### Implementation

**File: `tests/test_game_ui_integration.py`**

```python
"""
Integration tests for game engine with UI.
Uses mock UI to test without actual wxPython windows.
"""

import unittest
from src.parser import Parser
from src.state_manager import load_game_state, save_game_state
from examples.simple_engine import (
    get_current_location, move_player, take_item,
    drop_item, examine_item, show_inventory
)


class MockUI:
    """Mock UI that captures output instead of displaying it."""

    def __init__(self):
        self.output_buffer = []
        self.state = None
        self.parser = None

    def initialize(self, state_file):
        """Initialize game state and parser."""
        self.state = load_game_state(state_file)
        self.parser = Parser('data/vocabulary.json')

    def append_output(self, text):
        """Capture output text."""
        self.output_buffer.append(text)

    def clear_output(self):
        """Clear output buffer."""
        self.output_buffer = []

    def get_output(self):
        """Get all captured output."""
        return '\n'.join(self.output_buffer)

    def process_command(self, command_text):
        """Process a command and return result."""
        self.clear_output()
        result = self.parser.parse_command(command_text)

        if result is None:
            self.append_output("I don't understand that command.")
            return False

        # Execute command (simplified version of simple_engine.py match/case)
        if result.verb and result.verb.word == "inventory":
            if self.state.player.inventory:
                items = [item.name for item_id in self.state.player.inventory
                        for item in self.state.items if item.id == item_id]
                self.append_output(f"You are carrying: {', '.join(items)}")
            else:
                self.append_output("You are not carrying anything.")
            return True

        # Add more command handling as needed...
        return True


class TestGameUIIntegration(unittest.TestCase):
    """Test game engine functions through mock UI."""

    def setUp(self):
        """Set up test fixture."""
        self.ui = MockUI()
        self.ui.initialize('examples/simple_game_state.json')

    def test_initial_state(self):
        """Test initial game state loads correctly."""
        self.assertIsNotNone(self.ui.state)
        self.assertEqual(self.ui.state.player.location, 'loc_start')
        self.assertEqual(len(self.ui.state.player.inventory), 0)

    def test_inventory_empty(self):
        """Test inventory command with empty inventory."""
        self.ui.process_command("inventory")
        output = self.ui.get_output()
        self.assertIn("not carrying anything", output.lower())

    def test_take_item(self):
        """Test taking an item."""
        # Take sword
        result = take_item(self.ui.state, "sword")
        self.assertTrue(result)

        # Verify inventory
        self.assertEqual(len(self.ui.state.player.inventory), 1)
        self.assertIn('item_sword', self.ui.state.player.inventory)

    def test_movement(self):
        """Test player movement."""
        initial_loc = self.ui.state.player.location
        self.assertEqual(initial_loc, 'loc_start')

        # Move north
        result = move_player(self.ui.state, "north")
        self.assertTrue(result)

        # Verify new location
        self.assertEqual(self.ui.state.player.location, 'loc_hallway')
```

### Advantages
- ✅ Fast (no actual windows)
- ✅ Easy to automate
- ✅ Tests game logic thoroughly
- ✅ Can run in CI/CD

### Disadvantages
- ❌ Doesn't test actual UI rendering
- ❌ Doesn't catch UI-specific bugs

---

## Approach 2: Headless wxPython Testing

### Concept
Create real wxPython components but run tests without showing windows.

### Implementation

**File: `tests/test_wxpython_game_integration.py`**

```python
"""
Integration tests using real wxPython components in headless mode.
"""

import unittest
import wx
from pathlib import Path
from src.parser import Parser
from src.state_manager import load_game_state


class GamePanel(wx.Panel):
    """Simplified game panel for testing."""

    def __init__(self, parent):
        super().__init__(parent)

        # Create UI components
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.output = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)

        sizer.Add(self.output, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.input, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

        # Game state
        self.state = load_game_state('examples/simple_game_state.json')
        self.parser = Parser('data/vocabulary.json')

        # Bind events
        self.input.Bind(wx.EVT_TEXT_ENTER, self.on_command_enter)

    def on_command_enter(self, event):
        """Handle command input."""
        command = self.input.GetValue()
        self.input.Clear()
        self.process_command(command)

    def process_command(self, command):
        """Process command and update output."""
        result = self.parser.parse_command(command)
        if result:
            self.output.AppendText(f"> {command}\n")
            # Process result...
        else:
            self.output.AppendText("I don't understand that command.\n")

    def get_output_text(self):
        """Get all output text."""
        return self.output.GetValue()


class TestWxGameIntegration(unittest.TestCase):
    """Test actual wxPython UI with game engine."""

    @classmethod
    def setUpClass(cls):
        """Set up wxPython app once for all tests."""
        cls.app = wx.App(False)  # Don't show windows

    @classmethod
    def tearDownClass(cls):
        """Clean up wxPython app."""
        cls.app.Destroy()

    def setUp(self):
        """Create test frame and panel."""
        self.frame = wx.Frame(None)
        self.panel = GamePanel(self.frame)

    def tearDown(self):
        """Clean up frame."""
        self.frame.Destroy()

    def test_ui_creation(self):
        """Test UI components are created."""
        self.assertIsNotNone(self.panel.output)
        self.assertIsNotNone(self.panel.input)
        self.assertIsNotNone(self.panel.state)
        self.assertIsNotNone(self.panel.parser)

    def test_command_processing(self):
        """Test command processing through UI."""
        # Simulate entering command
        self.panel.input.SetValue("inventory")

        # Create and process enter event
        event = wx.CommandEvent(wx.EVT_TEXT_ENTER.typeId)
        event.SetEventObject(self.panel.input)
        self.panel.input.GetEventHandler().ProcessEvent(event)

        # Verify output contains response
        output = self.panel.get_output_text()
        self.assertIn("inventory", output.lower())

    def test_parser_integration(self):
        """Test parser integration."""
        result = self.panel.parser.parse_command("take sword")
        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, "take")
        self.assertEqual(result.direct_object.word, "sword")
```

### Advantages
- ✅ Tests real UI components
- ✅ Tests event handling
- ✅ Catches UI-specific issues
- ✅ No windows shown (fast)

### Disadvantages
- ❌ Requires wxPython installed
- ❌ More complex setup

---

## Approach 3: Game Controller Pattern

### Concept
Create a separate `GameController` class that mediates between UI and game engine. Test the controller independently.

### Implementation

**File: `src/game_controller.py`**

```python
"""
Game controller - mediates between UI and game engine.
Separates UI concerns from game logic.
"""

from src.parser import Parser
from src.state_manager import load_game_state, save_game_state, GameState
from examples.simple_engine import (
    move_player, take_item, drop_item, examine_item,
    open_item, describe_location, show_inventory
)


class GameController:
    """
    Controls game logic and state.

    UI components call methods on this controller.
    Controller calls UI callbacks to display results.
    """

    def __init__(self, ui_callbacks=None):
        """
        Initialize controller.

        Args:
            ui_callbacks: Dict of UI callback functions:
                - output(text): Display text to user
                - update_status(location, inventory): Update status bar
                - game_over(won): Handle game end
        """
        self.state = None
        self.parser = None
        self.ui_callbacks = ui_callbacks or {}

    def initialize_game(self, state_file):
        """Load game state and initialize parser."""
        self.state = load_game_state(state_file)
        self.parser = Parser('data/vocabulary.json')
        self._display_location()
        self._update_status()

    def process_command(self, command_text):
        """
        Process user command.

        Args:
            command_text: Raw command string from user

        Returns:
            bool: True if command was valid and processed
        """
        result = self.parser.parse_command(command_text)

        if result is None:
            self._output("I don't understand that command.")
            return False

        # Route command to appropriate handler
        return self._execute_command(result)

    def _execute_command(self, result):
        """Execute parsed command."""
        # Handle quit
        if result.verb and result.verb.word == "quit":
            if 'game_over' in self.ui_callbacks:
                self.ui_callbacks['game_over'](won=False)
            return True

        # Handle inventory
        if result.verb and result.verb.word == "inventory":
            self._show_inventory()
            return True

        # Handle movement
        if result.direction and not result.verb:
            return self._move_player(result.direction.word)

        # Handle examine
        if result.verb and result.verb.word == "examine":
            if result.direct_object:
                return self._examine_item(result.direct_object.word)
            elif result.object_missing:
                self._display_location()
                return True

        # Handle take
        if result.verb and result.verb.word == "take" and result.direct_object:
            return self._take_item(result.direct_object.word)

        # Add more handlers...

        self._output("I don't know how to do that.")
        return False

    def _move_player(self, direction):
        """Move player in direction."""
        success = move_player(self.state, direction)
        if success:
            self._update_status()
        return success

    def _take_item(self, item_name):
        """Take an item."""
        success = take_item(self.state, item_name)
        if success:
            self._update_status()
        return success

    def _examine_item(self, item_name):
        """Examine an item."""
        return examine_item(self.state, item_name)

    def _show_inventory(self):
        """Display inventory."""
        if self.state.player.inventory:
            items = []
            for item_id in self.state.player.inventory:
                for item in self.state.items:
                    if item.id == item_id:
                        items.append(item.name)
                        break
            self._output(f"You are carrying: {', '.join(items)}")
        else:
            self._output("You are not carrying anything.")

    def _display_location(self):
        """Display current location description."""
        loc = None
        for location in self.state.locations:
            if location.id == self.state.player.location:
                loc = location
                break

        if loc:
            self._output(loc.description)

            # Show items
            items_here = [item for item in self.state.items
                         if item.location == loc.id]
            if items_here:
                item_names = [item.name for item in items_here]
                self._output(f"You see: {', '.join(item_names)}")

    def _output(self, text):
        """Send text to UI."""
        if 'output' in self.ui_callbacks:
            self.ui_callbacks['output'](text)

    def _update_status(self):
        """Update UI status bar."""
        if 'update_status' in self.ui_callbacks:
            loc_name = "Unknown"
            for loc in self.state.locations:
                if loc.id == self.state.player.location:
                    loc_name = loc.name
                    break

            inv_count = len(self.state.player.inventory)
            self.ui_callbacks['update_status'](loc_name, inv_count)

    def save_game(self, filename):
        """Save game to file."""
        try:
            save_game_state(self.state, filename)
            self._output(f"Game saved to {filename}")
            return True
        except Exception as e:
            self._output(f"Error saving game: {e}")
            return False

    def load_game(self, filename):
        """Load game from file."""
        try:
            self.state = load_game_state(filename)
            self._output(f"Game loaded from {filename}")
            self._display_location()
            self._update_status()
            return True
        except Exception as e:
            self._output(f"Error loading game: {e}")
            return False
```

**File: `tests/test_game_controller.py`**

```python
"""
Test game controller independently of UI.
"""

import unittest
from src.game_controller import GameController


class TestGameController(unittest.TestCase):
    """Test game controller without UI."""

    def setUp(self):
        """Set up test fixture with mock callbacks."""
        self.output_buffer = []
        self.status_updates = []
        self.game_over_called = False

        callbacks = {
            'output': lambda text: self.output_buffer.append(text),
            'update_status': lambda loc, inv: self.status_updates.append((loc, inv)),
            'game_over': lambda won: setattr(self, 'game_over_called', True)
        }

        self.controller = GameController(callbacks)
        self.controller.initialize_game('examples/simple_game_state.json')

    def test_initialization(self):
        """Test controller initializes correctly."""
        self.assertIsNotNone(self.controller.state)
        self.assertIsNotNone(self.controller.parser)
        self.assertEqual(self.controller.state.player.location, 'loc_start')

    def test_inventory_command(self):
        """Test inventory command."""
        self.output_buffer.clear()
        result = self.controller.process_command("inventory")

        self.assertTrue(result)
        self.assertTrue(any("not carrying anything" in msg.lower()
                          for msg in self.output_buffer))

    def test_movement_command(self):
        """Test movement."""
        initial_status_count = len(self.status_updates)
        result = self.controller.process_command("north")

        self.assertTrue(result)
        self.assertEqual(self.controller.state.player.location, 'loc_hallway')
        self.assertGreater(len(self.status_updates), initial_status_count)

    def test_take_command(self):
        """Test taking item."""
        result = self.controller.process_command("take sword")

        self.assertTrue(result)
        self.assertEqual(len(self.controller.state.player.inventory), 1)
        self.assertIn('item_sword', self.controller.state.player.inventory)

    def test_quit_command(self):
        """Test quit command."""
        result = self.controller.process_command("quit")

        self.assertTrue(result)
        self.assertTrue(self.game_over_called)

    def test_invalid_command(self):
        """Test invalid command."""
        self.output_buffer.clear()
        result = self.controller.process_command("blargfoo")

        self.assertFalse(result)
        self.assertTrue(any("don't understand" in msg.lower()
                          for msg in self.output_buffer))
```

### Advantages
- ✅ Clean separation of concerns
- ✅ Easy to test controller
- ✅ Easy to test UI separately
- ✅ Reusable controller for different UIs

### Disadvantages
- ❌ Requires refactoring existing code
- ❌ Additional abstraction layer

---

## Approach 4: Integration Test with Manual Verification

### Concept
Create a test UI that can be manually inspected while running automated tests.

### Implementation

**File: `tests/test_wx_manual.py`**

```python
"""
Manual integration tests with visible UI.
Run this to visually verify UI behavior.
"""

import wx
from src.game_controller import GameController


class TestGameFrame(wx.Frame):
    """Test frame with instrumentation."""

    def __init__(self):
        super().__init__(None, title="Game Engine Test UI", size=(600, 400))

        # Create panel
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Output area
        self.output = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        sizer.Add(self.output, 1, wx.EXPAND | wx.ALL, 5)

        # Input area
        self.input = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.input.Bind(wx.EVT_TEXT_ENTER, self.on_command)
        sizer.Add(self.input, 0, wx.EXPAND | wx.ALL, 5)

        # Status bar
        self.CreateStatusBar(2)

        # Test buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for cmd in ["inventory", "take sword", "north", "look"]:
            btn = wx.Button(panel, label=cmd)
            btn.Bind(wx.EVT_BUTTON, lambda evt, c=cmd: self.run_test_command(c))
            btn_sizer.Add(btn, 0, wx.ALL, 2)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER)

        panel.SetSizer(sizer)

        # Initialize controller
        callbacks = {
            'output': self.append_output,
            'update_status': self.update_status,
            'game_over': self.on_game_over
        }
        self.controller = GameController(callbacks)
        self.controller.initialize_game('examples/simple_game_state.json')

    def append_output(self, text):
        """Append text to output area."""
        self.output.AppendText(text + '\n')

    def update_status(self, location, inventory_count):
        """Update status bar."""
        self.SetStatusText(f"Location: {location}", 0)
        self.SetStatusText(f"Items: {inventory_count}", 1)

    def on_game_over(self, won):
        """Handle game over."""
        msg = "You won!" if won else "Game over."
        wx.MessageBox(msg, "Game Over", wx.OK | wx.ICON_INFORMATION)

    def on_command(self, event):
        """Process command from input."""
        command = self.input.GetValue()
        self.input.Clear()
        self.append_output(f"> {command}")
        self.controller.process_command(command)

    def run_test_command(self, command):
        """Run a test command from button."""
        self.append_output(f"> {command} [TEST]")
        self.controller.process_command(command)


if __name__ == '__main__':
    app = wx.App()
    frame = TestGameFrame()
    frame.Show()
    app.MainLoop()
```

### Advantages
- ✅ Visual verification
- ✅ Quick feedback
- ✅ Can test actual UI behavior
- ✅ Good for debugging

### Disadvantages
- ❌ Not automated
- ❌ Requires manual interaction
- ❌ Slower than unit tests

---

## Recommended Testing Strategy

### Phase 1: Unit Tests (Current)
- ✅ Test game engine functions directly
- ✅ Test parser
- ✅ Test state_manager

### Phase 2: Controller Tests
- Create `GameController` class
- Test controller with mock callbacks
- Verify controller correctly calls game engine functions

### Phase 3: Integration Tests
- Test controller with mock UI
- Verify command flow: Input → Parser → Controller → Game Engine → Output

### Phase 4: UI Tests
- Test actual wxPython components headlessly
- Verify event handling
- Verify UI updates

### Phase 5: Manual Verification
- Create test UI for visual verification
- Run through common game scenarios
- Verify user experience

---

## Test Coverage Goals

### Game Engine Functions
- ✅ Movement (all directions)
- ✅ Item manipulation (take, drop, examine)
- ✅ Inventory display
- ✅ Door/lock mechanics
- ✅ Save/load functionality
- ✅ Win condition

### UI Functions
- ✅ Text input/output
- ✅ Command parsing
- ✅ Status bar updates
- ✅ Menu actions
- ✅ Error handling
- ✅ Game over handling

### Integration Points
- ✅ UI → Parser → Controller → Engine
- ✅ Engine → Controller → UI callbacks
- ✅ State persistence
- ✅ Error propagation

---

## Running Tests

```bash
# Run all unit tests
python -m unittest discover tests/

# Run controller tests only
python -m unittest tests.test_game_controller

# Run integration tests
python -m unittest tests.test_game_ui_integration

# Run manual test UI
python tests/test_wx_manual.py
```

---

## Continuous Integration

For automated testing in CI/CD:

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run unit tests
        run: python -m unittest discover tests/
      - name: Run controller tests
        run: python -m unittest tests.test_game_controller
```

---

## Summary

The **GameController pattern (Approach 3)** is the recommended approach because:

1. Clean separation between UI and game logic
2. Easy to test controller independently
3. UI can be tested with mock callbacks
4. Can switch between CLI, wxPython, web UI, etc.
5. Follows MVC/MVP design patterns
6. Maintainable and extensible

Start with unit tests, add controller tests, then integration tests as needed.
