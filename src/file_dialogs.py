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
    try:
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

    except Exception as e:
        print(f"Error opening file dialog: {e}")
        print("Please specify filename directly: save <filename>")
        return None


def get_load_filename(default_dir: str = ".") -> Optional[str]:
    """
    Open a native Open File dialog.

    Args:
        default_dir: Initial directory to show

    Returns:
        Selected filename as string, or None if canceled
    """
    try:
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

    except Exception as e:
        print(f"Error opening file dialog: {e}")
        print("Please specify filename directly: load <filename>")
        return None
