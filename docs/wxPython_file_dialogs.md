# wxPython File Dialogs Integration Design

## Overview
Integrate wxPython file dialogs into the existing command-line `simple_engine.py` to provide a graphical file picker when users issue `save` or `load` commands without specifying a filename.

## Scope
This is an **extremely limited integration** focused solely on file dialogs:
- **In Scope**: File open/save dialogs for load/save commands
- **Out of Scope**: Full GUI, text output windows, command input fields, menus, etc.

The game remains a command-line application. wxPython is used **only** to display native file picker dialogs.

## Current Behavior

### Save Command
```python
# In simple_engine.py main() loop:
case _ if result.verb and result.verb.word == "save":
    if result.direct_object:
        save_game(state, result.direct_object.word)
    elif result.object_missing:
        parts = result.raw.split(maxsplit=1)
        if len(parts) > 1:
            filename = parts[1].strip()
            save_game(state, filename)
        else:
            print("Please specify a filename: save <filename>")
```

**Current Flow:**
1. User types: `save`
2. Parser returns: `ParsedCommand(verb="save", object_missing=True)`
3. Engine prints: "Please specify a filename: save <filename>"
4. User must type full command: `save mygame.json`

### Load Command
```python
case _ if result.verb and result.verb.word == "load":
    if result.direct_object:
        loaded_state = load_game(result.direct_object.word)
        if loaded_state:
            state = loaded_state
            describe_location(state)
    elif result.object_missing:
        parts = result.raw.split(maxsplit=1)
        if len(parts) > 1:
            filename = parts[1].strip()
            loaded_state = load_game(filename)
            if loaded_state:
                state = loaded_state
                describe_location(state)
        else:
            print("Please specify a filename: load <filename>")
```

**Current Flow:**
1. User types: `load`
2. Parser returns: `ParsedCommand(verb="load", object_missing=True)`
3. Engine prints: "Please specify a filename: load <filename>"
4. User must type full command: `load mygame.json`

## Proposed Behavior

### Save Command with Dialog
```
User Input: save
Parser Output: ParsedCommand(verb="save", object_missing=True)
Engine Action: Open native "Save File" dialog
User Action: Select/enter filename in dialog
Engine Result: Save game to selected file
Console Output: "Game saved to <filename>"
```

### Load Command with Dialog
```
User Input: load
Parser Output: ParsedCommand(verb="load", object_missing=True)
Engine Action: Open native "Open File" dialog
User Action: Select existing file in dialog
Engine Result: Load game from selected file
Console Output: "Game loaded from <filename>"
                <location description>
```

### Backward Compatibility
Users can still specify filenames directly:
```
> save mygame.json
Game saved to mygame.json

> load mygame.json
Game loaded from mygame.json
You are in a small room...
```

## Implementation Design

### 1. File Dialog Helper Functions

Create new file: `src/file_dialogs.py`

```python
"""wxPython file dialog helpers for command-line game."""

import wx
from pathlib import Path
from typing import Optional


def get_save_filename(default_dir: str = ".", default_filename: str = "savegame.json") -> Optional[str]:
    """
    Open a native Save File dialog.

    Args:
        default_dir: Initial directory to show
        default_filename: Suggested filename

    Returns:
        Selected filename as string, or None if canceled
    """
    # Create minimal app if needed (won't show any windows)
    app = wx.App(False)

    # Create save dialog
    dialog = wx.FileDialog(
        None,  # No parent window
        message="Save Game As",
        defaultDir=default_dir,
        defaultFile=default_filename,
        wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
    )

    # Show dialog and get result
    filename = None
    if dialog.ShowModal() == wx.ID_OK:
        filename = dialog.GetPath()

    # Cleanup
    dialog.Destroy()
    app.Destroy()

    return filename


def get_load_filename(default_dir: str = ".") -> Optional[str]:
    """
    Open a native Open File dialog.

    Args:
        default_dir: Initial directory to show

    Returns:
        Selected filename as string, or None if canceled
    """
    # Create minimal app if needed
    app = wx.App(False)

    # Create open dialog
    dialog = wx.FileDialog(
        None,  # No parent window
        message="Load Game",
        defaultDir=default_dir,
        wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
    )

    # Show dialog and get result
    filename = None
    if dialog.ShowModal() == wx.ID_OK:
        filename = dialog.GetPath()

    # Cleanup
    dialog.Destroy()
    app.Destroy()

    return filename
```

### 2. Integration into simple_engine.py

Modify the save/load command handling in `main()`:

```python
# At top of file
from src.file_dialogs import get_save_filename, get_load_filename

# In main() loop, replace save command handler:
case _ if result.verb and result.verb.word == "save":
    if result.direct_object:
        # User provided filename as direct object
        save_game(state, result.direct_object.word)
    elif result.object_missing:
        # Check if filename provided after verb
        parts = result.raw.split(maxsplit=1)
        if len(parts) > 1:
            filename = parts[1].strip()
            save_game(state, filename)
        else:
            # No filename - open dialog
            filename = get_save_filename(default_dir=".", default_filename="savegame.json")
            if filename:
                save_game(state, filename)
            else:
                print("Save canceled.")

# Replace load command handler:
case _ if result.verb and result.verb.word == "load":
    if result.direct_object:
        # User provided filename as direct object
        loaded_state = load_game(result.direct_object.word)
        if loaded_state:
            state = loaded_state
            describe_location(state)
    elif result.object_missing:
        # Check if filename provided after verb
        parts = result.raw.split(maxsplit=1)
        if len(parts) > 1:
            filename = parts[1].strip()
            loaded_state = load_game(filename)
            if loaded_state:
                state = loaded_state
                describe_location(state)
        else:
            # No filename - open dialog
            filename = get_load_filename(default_dir=".")
            if filename:
                loaded_state = load_game(filename)
                if loaded_state:
                    state = loaded_state
                    describe_location(state)
            else:
                print("Load canceled.")
```

### 3. Configuration Options

Optional: Add configuration to control dialog behavior.

Create `examples/game_config.json`:
```json
{
  "use_file_dialogs": true,
  "default_save_dir": "saves",
  "default_save_name": "savegame.json"
}
```

This allows users to disable dialogs if desired:
- `use_file_dialogs: false` → Revert to command-line prompt behavior
- Useful for scripting, testing, or user preference

### 4. Directory Management

Ensure save directory exists:

```python
def ensure_save_directory(save_dir: str = "saves") -> str:
    """
    Ensure save directory exists and return absolute path.

    Args:
        save_dir: Directory name relative to game root

    Returns:
        Absolute path to save directory
    """
    path = Path(save_dir)
    path.mkdir(exist_ok=True)
    return str(path.resolve())
```

Modify dialog calls:
```python
save_dir = ensure_save_directory("saves")
filename = get_save_filename(default_dir=save_dir)
```

## User Experience Flow

### Save Flow
```
Game Console:
> save
[Native file dialog opens]
[User selects/enters: "saves/mysave.json"]
[User clicks Save]
Game saved to saves/mysave.json

Game Console:
>
```

### Load Flow
```
Game Console:
> load
[Native file dialog opens]
[User selects: "saves/mysave.json"]
[User clicks Open]
Game loaded from saves/mysave.json
You are in a small room. There is a rusty sword on the ground...

Game Console:
>
```

### Cancel Flow
```
Game Console:
> save
[Native file dialog opens]
[User clicks Cancel]
Save canceled.

Game Console:
>
```

## Technical Considerations

### wxPython App Lifecycle
- Create `wx.App(False)` before showing dialog
- `False` parameter prevents main loop from running
- Dialog is modal - blocks until user responds
- Destroy app and dialog after use
- No persistent wxPython objects remain

### Cross-Platform Behavior
- **macOS**: Native Cocoa file dialog
- **Linux**: GTK file dialog (platform-dependent)
- **Windows**: Native Windows file dialog

All platforms support:
- File filtering by extension
- Directory navigation
- Overwrite confirmation (save)
- File existence checking (load)

### Performance Impact
- Dialog creation: ~50-100ms first time (wxPython init)
- Subsequent dialogs: ~10-20ms
- Negligible impact on command-line game performance
- No memory overhead when dialogs not in use

### Error Handling
```python
def get_save_filename(...) -> Optional[str]:
    try:
        app = wx.App(False)
        # ... dialog code ...
    except Exception as e:
        print(f"Error opening file dialog: {e}")
        print("Please specify filename directly: save <filename>")
        return None
    finally:
        # Ensure cleanup even on error
        if 'dialog' in locals():
            dialog.Destroy()
        if 'app' in locals():
            app.Destroy()
```

## Testing Strategy

### Unit Tests
Create `tests/test_file_dialogs.py`:

```python
"""Tests for file dialog functions."""

import unittest
from unittest.mock import patch, MagicMock
from src.file_dialogs import get_save_filename, get_load_filename


class TestFileDialogs(unittest.TestCase):
    """Test file dialog functions with mocked wx components."""

    @patch('src.file_dialogs.wx.FileDialog')
    @patch('src.file_dialogs.wx.App')
    def test_save_dialog_ok(self, mock_app, mock_dialog):
        """Test save dialog when user clicks OK."""
        # Mock dialog to return OK and a filename
        mock_dialog_instance = MagicMock()
        mock_dialog_instance.ShowModal.return_value = wx.ID_OK
        mock_dialog_instance.GetPath.return_value = "/path/to/save.json"
        mock_dialog.return_value = mock_dialog_instance

        result = get_save_filename()

        self.assertEqual(result, "/path/to/save.json")
        mock_dialog_instance.Destroy.assert_called_once()

    @patch('src.file_dialogs.wx.FileDialog')
    @patch('src.file_dialogs.wx.App')
    def test_save_dialog_cancel(self, mock_app, mock_dialog):
        """Test save dialog when user cancels."""
        mock_dialog_instance = MagicMock()
        mock_dialog_instance.ShowModal.return_value = wx.ID_CANCEL
        mock_dialog.return_value = mock_dialog_instance

        result = get_save_filename()

        self.assertIsNone(result)
        mock_dialog_instance.Destroy.assert_called_once()

    @patch('src.file_dialogs.wx.FileDialog')
    @patch('src.file_dialogs.wx.App')
    def test_load_dialog_ok(self, mock_app, mock_dialog):
        """Test load dialog when user clicks OK."""
        mock_dialog_instance = MagicMock()
        mock_dialog_instance.ShowModal.return_value = wx.ID_OK
        mock_dialog_instance.GetPath.return_value = "/path/to/load.json"
        mock_dialog.return_value = mock_dialog_instance

        result = get_load_filename()

        self.assertEqual(result, "/path/to/load.json")
        mock_dialog_instance.Destroy.assert_called_once()
```

### Manual Testing Checklist
- [ ] `save` with no filename opens save dialog
- [ ] `save mysave.json` bypasses dialog and saves directly
- [ ] Save dialog shows `.json` files by default
- [ ] Save dialog confirms overwrite of existing files
- [ ] Save dialog can create new files
- [ ] Canceling save dialog prints "Save canceled"
- [ ] `load` with no filename opens load dialog
- [ ] `load mysave.json` bypasses dialog and loads directly
- [ ] Load dialog shows `.json` files by default
- [ ] Load dialog only allows selecting existing files
- [ ] Canceling load dialog prints "Load canceled"
- [ ] Dialogs work on target platform (macOS/Linux/Windows)

### Integration Testing
Test with actual game flow:
1. Start new game
2. Type `save` → Select file in dialog → Verify file created
3. Modify game state (move, take item)
4. Type `load` → Select previous save → Verify state restored
5. Type `save anothersave.json` → Verify direct save works
6. Type `load anothersave.json` → Verify direct load works

## Dependencies

### Required
- `wxPython>=4.2.0` (already installed from Phase 1)

### Optional
- None - uses only standard library beyond wxPython

## File Structure

```
text-game/
├── src/
│   ├── file_dialogs.py          # NEW: Dialog helper functions
│   ├── parser.py                # Existing
│   ├── state_manager.py         # Existing
│   └── ...
├── examples/
│   ├── simple_engine.py         # MODIFIED: Add dialog integration
│   ├── simple_game_state.json   # Existing
│   └── game_config.json         # OPTIONAL: Configuration
├── tests/
│   ├── test_file_dialogs.py     # NEW: Dialog unit tests
│   └── ...
├── saves/                        # NEW: Default save directory (auto-created)
└── docs/
    └── wxPython_file_dialogs.md # This document
```

## Implementation Checklist

### Phase 1: File Dialog Module
- [ ] Create `src/file_dialogs.py`
- [ ] Implement `get_save_filename()`
- [ ] Implement `get_load_filename()`
- [ ] Add error handling
- [ ] Test dialogs manually on platform

### Phase 2: Integration
- [ ] Modify `simple_engine.py` save command handler
- [ ] Modify `simple_engine.py` load command handler
- [ ] Add import statements
- [ ] Create default save directory
- [ ] Test integration manually

### Phase 3: Testing
- [ ] Create `tests/test_file_dialogs.py`
- [ ] Write unit tests with mocks
- [ ] Run unit tests
- [ ] Perform manual integration tests
- [ ] Verify all checklist items

### Phase 4: Optional Enhancements
- [ ] Add configuration file support
- [ ] Add directory management helpers
- [ ] Add file filtering options
- [ ] Document user-facing behavior

## Advantages of This Approach

1. **Minimal Scope**: Only touches file operations, no broader UI changes
2. **Non-Invasive**: Game remains command-line; dialogs are optional enhancement
3. **Backward Compatible**: Direct filename entry still works
4. **Native Feel**: Uses system-native file dialogs
5. **Clean Separation**: Dialog code isolated in separate module
6. **Easy to Disable**: Can be toggled via config or removed entirely
7. **Low Risk**: Isolated functionality, easy to test and debug
8. **Leverages Existing Work**: Uses wxPython already installed from Phase 1

## Alternative Approaches Considered

### 1. Command-Line File Browser
**Description**: Use terminal-based file browser (like `curses`)
**Rejected Because**:
- Less intuitive than native dialogs
- Platform-specific terminal compatibility issues
- Not as polished as native file pickers

### 2. Web-Based File Picker
**Description**: Launch browser with file picker interface
**Rejected Because**:
- Overly complex for simple need
- Requires web server
- Security concerns with file system access

### 3. tkinter File Dialogs
**Description**: Use tkinter instead of wxPython
**Rejected Because**:
- Already have wxPython installed
- wxPython dialogs more native-looking on macOS
- Would introduce additional dependency

## Future Expansion Possibilities

While out of scope for this design, the file dialog integration could later expand to:
- Recent files menu (requires UI)
- Quick save/load slots (requires UI)
- Save game thumbnails/previews (requires UI)
- Auto-save functionality (no UI needed)

However, these remain **explicitly out of scope** for this implementation.

## Success Criteria

This implementation is successful when:
1. ✅ `save` command without filename opens native save dialog
2. ✅ `load` command without filename opens native load dialog
3. ✅ Direct filename entry still works (`save file.json`, `load file.json`)
4. ✅ Dialogs are native to the platform (Cocoa on macOS)
5. ✅ Dialog cancellation is handled gracefully
6. ✅ Files are saved to/loaded from correct locations
7. ✅ No persistent wxPython windows remain after dialog closes
8. ✅ Unit tests pass with mocked wx components
9. ✅ Manual integration tests pass
10. ✅ Game remains fully functional as command-line application

## Estimated Implementation Time
- File dialog module: 30-45 minutes
- Integration into simple_engine.py: 15-30 minutes
- Unit tests: 30-45 minutes
- Manual testing: 15-30 minutes

**Total: 1.5-2.5 hours**
