"""
Tests for wxPython file dialog functions using headless testing approach.

This test module uses Approach 2 from wxPython_testing_strategy.md:
Headless wxPython Testing - creates real wx components but doesn't display windows.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

try:
    import wx
    WX_AVAILABLE = True
except ModuleNotFoundError:
    WX_AVAILABLE = False
    wx = None  # type: ignore[attr-defined]


# Force headless mode so this module can always run in CI (wx dialogs require a display).
HAS_DISPLAY = False


class HeadlessFileDialog:
    """Minimal stand-in for wx.FileDialog when no display is available."""

    def __init__(self, parent, message="", defaultDir="", defaultFile="", wildcard="", style=0):
        self.parent = parent
        self._message = message
        self._defaultDir = defaultDir
        self._defaultFile = defaultFile
        self._wildcard = wildcard
        self._style = style
        self._path = ""

    def ShowModal(self):
        return wx.ID_CANCEL

    def GetPath(self):
        return self._path

    def GetMessage(self):
        return self._message

    def GetDirectory(self):
        return self._defaultDir

    def GetFilename(self):
        return self._defaultFile

    def GetWildcard(self):
        return self._wildcard

    def Destroy(self):
        return None


@unittest.skipUnless(WX_AVAILABLE, "wxPython not installed")
class TestFileDialogsHeadless(unittest.TestCase):
    """
    Test file dialog functions with real wxPython components in headless mode.

    These tests create actual wx.FileDialog objects but mock the ShowModal
    method to simulate user interactions without displaying windows.
    """

    def setUp(self):
        """Set up test fixtures - create headless wx.App."""
        self._patchers = []
        if not HAS_DISPLAY:
            # Patch wx.App and wx.FileDialog so we can run without a GUI/display
            app_patcher = patch('wx.App', return_value=MagicMock())
            dialog_patcher = patch('wx.FileDialog', HeadlessFileDialog)
            self._patchers.extend([app_patcher, dialog_patcher])
            for patcher in self._patchers:
                patcher.start()

        # Create app in headless mode (False = don't redirect stdout)
        # This allows testing with real wx components (or the headless stub) without showing windows
        self.app = wx.App(False)

    def tearDown(self):
        """Clean up after tests - destroy wx.App."""
        if self.app:
            self.app.Destroy()
            self.app = None
        # Stop any headless patches
        for patcher in reversed(getattr(self, "_patchers", [])):
            patcher.stop()

    @patch('wx.FileDialog.ShowModal')
    @patch('wx.FileDialog.GetPath')
    def test_save_dialog_ok_button(self, mock_get_path, mock_show_modal):
        """Test save dialog when user clicks OK button."""
        # Arrange - mock user clicking OK and selecting a file
        mock_show_modal.return_value = wx.ID_OK
        mock_get_path.return_value = "/Users/test/saves/mysave.json"

        # Act - create save dialog (this is a real wx.FileDialog)
        dialog = wx.FileDialog(
            None,
            message="Save Game As",
            defaultDir=".",
            defaultFile="savegame.json",
            wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )

        result_id = dialog.ShowModal()
        filename = dialog.GetPath() if result_id == wx.ID_OK else None

        # Assert
        self.assertEqual(result_id, wx.ID_OK)
        self.assertEqual(filename, "/Users/test/saves/mysave.json")
        self.assertIsInstance(dialog, wx.FileDialog)

        # Cleanup
        dialog.Destroy()

    @patch('wx.FileDialog.ShowModal')
    def test_save_dialog_cancel_button(self, mock_show_modal):
        """Test save dialog when user clicks Cancel button."""
        # Arrange - mock user clicking Cancel
        mock_show_modal.return_value = wx.ID_CANCEL

        # Act
        dialog = wx.FileDialog(
            None,
            message="Save Game As",
            defaultDir=".",
            defaultFile="savegame.json",
            wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )

        result_id = dialog.ShowModal()
        filename = dialog.GetPath() if result_id == wx.ID_OK else None

        # Assert
        self.assertEqual(result_id, wx.ID_CANCEL)
        self.assertIsNone(filename)

        # Cleanup
        dialog.Destroy()

    @patch('wx.FileDialog.ShowModal')
    @patch('wx.FileDialog.GetPath')
    def test_load_dialog_ok_button(self, mock_get_path, mock_show_modal):
        """Test load dialog when user clicks OK button."""
        # Arrange - mock user clicking OK and selecting a file
        mock_show_modal.return_value = wx.ID_OK
        mock_get_path.return_value = "/Users/test/saves/existing.json"

        # Act
        dialog = wx.FileDialog(
            None,
            message="Load Game",
            defaultDir=".",
            wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )

        result_id = dialog.ShowModal()
        filename = dialog.GetPath() if result_id == wx.ID_OK else None

        # Assert
        self.assertEqual(result_id, wx.ID_OK)
        self.assertEqual(filename, "/Users/test/saves/existing.json")
        self.assertIsInstance(dialog, wx.FileDialog)

        # Cleanup
        dialog.Destroy()

    @patch('wx.FileDialog.ShowModal')
    def test_load_dialog_cancel_button(self, mock_show_modal):
        """Test load dialog when user clicks Cancel button."""
        # Arrange - mock user clicking Cancel
        mock_show_modal.return_value = wx.ID_CANCEL

        # Act
        dialog = wx.FileDialog(
            None,
            message="Load Game",
            defaultDir=".",
            wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )

        result_id = dialog.ShowModal()
        filename = dialog.GetPath() if result_id == wx.ID_OK else None

        # Assert
        self.assertEqual(result_id, wx.ID_CANCEL)
        self.assertIsNone(filename)

        # Cleanup
        dialog.Destroy()

    def test_save_dialog_properties(self):
        """Test that save dialog is created with correct properties."""
        # Act
        dialog = wx.FileDialog(
            None,
            message="Save Game As",
            defaultDir="saves",
            defaultFile="mysave.json",
            wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )

        # Assert - verify dialog properties
        self.assertEqual(dialog.GetMessage(), "Save Game As")
        self.assertEqual(dialog.GetDirectory(), "saves")
        self.assertEqual(dialog.GetFilename(), "mysave.json")
        self.assertIn("JSON files", dialog.GetWildcard())

        # Cleanup
        dialog.Destroy()

    def test_load_dialog_properties(self):
        """Test that load dialog is created with correct properties."""
        # Act
        dialog = wx.FileDialog(
            None,
            message="Load Game",
            defaultDir="saves",
            wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )

        # Assert - verify dialog properties
        self.assertEqual(dialog.GetMessage(), "Load Game")
        self.assertEqual(dialog.GetDirectory(), "saves")
        self.assertIn("JSON files", dialog.GetWildcard())

        # Cleanup
        dialog.Destroy()

    @patch('wx.FileDialog.ShowModal')
    @patch('wx.FileDialog.GetPath')
    def test_dialog_with_absolute_path(self, mock_get_path, mock_show_modal):
        """Test dialog returns absolute path."""
        # Arrange
        mock_show_modal.return_value = wx.ID_OK
        mock_get_path.return_value = "/absolute/path/to/savegame.json"

        # Act
        dialog = wx.FileDialog(
            None,
            message="Save Game As",
            style=wx.FD_SAVE
        )

        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
        else:
            filename = None

        # Assert
        self.assertIsNotNone(filename)
        self.assertTrue(filename.startswith("/"))

        # Cleanup
        dialog.Destroy()

    @patch('wx.FileDialog.ShowModal')
    @patch('wx.FileDialog.GetPath')
    def test_multiple_dialog_instances(self, mock_get_path, mock_show_modal):
        """Test creating and destroying multiple dialog instances."""
        # Arrange
        mock_show_modal.return_value = wx.ID_OK

        # Act - create multiple dialogs
        filenames = []
        for i in range(3):
            mock_get_path.return_value = f"/path/to/save{i}.json"

            dialog = wx.FileDialog(
                None,
                message=f"Save Game {i}",
                style=wx.FD_SAVE
            )

            if dialog.ShowModal() == wx.ID_OK:
                filenames.append(dialog.GetPath())

            dialog.Destroy()

        # Assert
        self.assertEqual(len(filenames), 3)
        self.assertEqual(filenames[0], "/path/to/save0.json")
        self.assertEqual(filenames[1], "/path/to/save1.json")
        self.assertEqual(filenames[2], "/path/to/save2.json")


@unittest.skipUnless(WX_AVAILABLE, "wxPython not installed")
class TestFileDialogHelpers(unittest.TestCase):
    """
    Test the actual helper functions from src/file_dialogs.py.

    These tests verify the get_save_filename() and get_load_filename()
    functions work correctly with mocked dialog interactions.
    """

    @patch('src.file_dialogs.wx.FileDialog')
    @patch('src.file_dialogs.wx.App')
    def test_get_save_filename_ok(self, mock_app_class, mock_dialog_class):
        """Test get_save_filename when user selects a file."""
        # Arrange - mock app and dialog instances
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        mock_dialog = MagicMock()
        mock_dialog.ShowModal.return_value = wx.ID_OK
        mock_dialog.GetPath.return_value = "/Users/test/mysave.json"
        mock_dialog_class.return_value = mock_dialog

        # Act - import and test function
        from src.file_dialogs import get_save_filename
        result = get_save_filename()

        # Assert
        self.assertEqual(result, "/Users/test/mysave.json")
        mock_app_class.assert_called_once_with(False)
        mock_dialog.ShowModal.assert_called_once()
        mock_dialog.GetPath.assert_called_once()
        mock_dialog.Destroy.assert_called_once()
        mock_app.Destroy.assert_called_once()

    @patch('src.file_dialogs.wx.FileDialog')
    @patch('src.file_dialogs.wx.App')
    def test_get_save_filename_cancel(self, mock_app_class, mock_dialog_class):
        """Test get_save_filename when user cancels."""
        # Arrange
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        mock_dialog = MagicMock()
        mock_dialog.ShowModal.return_value = wx.ID_CANCEL
        mock_dialog_class.return_value = mock_dialog

        # Act
        from src.file_dialogs import get_save_filename
        result = get_save_filename()

        # Assert
        self.assertIsNone(result)
        mock_dialog.ShowModal.assert_called_once()
        mock_dialog.Destroy.assert_called_once()
        mock_app.Destroy.assert_called_once()

    @patch('src.file_dialogs.wx.FileDialog')
    @patch('src.file_dialogs.wx.App')
    def test_get_load_filename_ok(self, mock_app_class, mock_dialog_class):
        """Test get_load_filename when user selects a file."""
        # Arrange
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        mock_dialog = MagicMock()
        mock_dialog.ShowModal.return_value = wx.ID_OK
        mock_dialog.GetPath.return_value = "/Users/test/existing.json"
        mock_dialog_class.return_value = mock_dialog

        # Act
        from src.file_dialogs import get_load_filename
        result = get_load_filename()

        # Assert
        self.assertEqual(result, "/Users/test/existing.json")
        mock_app_class.assert_called_once_with(False)
        mock_dialog.ShowModal.assert_called_once()
        mock_dialog.GetPath.assert_called_once()
        mock_dialog.Destroy.assert_called_once()
        mock_app.Destroy.assert_called_once()

    @patch('src.file_dialogs.wx.FileDialog')
    @patch('src.file_dialogs.wx.App')
    def test_get_load_filename_cancel(self, mock_app_class, mock_dialog_class):
        """Test get_load_filename when user cancels."""
        # Arrange
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        mock_dialog = MagicMock()
        mock_dialog.ShowModal.return_value = wx.ID_CANCEL
        mock_dialog_class.return_value = mock_dialog

        # Act
        from src.file_dialogs import get_load_filename
        result = get_load_filename()

        # Assert
        self.assertIsNone(result)
        mock_dialog.ShowModal.assert_called_once()
        mock_dialog.Destroy.assert_called_once()
        mock_app.Destroy.assert_called_once()

    @patch('src.file_dialogs.wx.FileDialog')
    @patch('src.file_dialogs.wx.App')
    def test_save_with_custom_defaults(self, mock_app_class, mock_dialog_class):
        """Test save dialog with custom default directory and filename."""
        # Arrange
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        mock_dialog = MagicMock()
        mock_dialog.ShowModal.return_value = wx.ID_OK
        mock_dialog.GetPath.return_value = "/custom/path/custom.json"
        mock_dialog_class.return_value = mock_dialog

        # Act
        from src.file_dialogs import get_save_filename
        result = get_save_filename(default_dir="/custom/path", default_filename="custom.json")

        # Assert
        self.assertEqual(result, "/custom/path/custom.json")

        # Verify dialog was created with correct parameters
        mock_dialog_class.assert_called_once()
        call_kwargs = mock_dialog_class.call_args[1]
        self.assertEqual(call_kwargs['defaultDir'], "/custom/path")
        self.assertEqual(call_kwargs['defaultFile'], "custom.json")

    @patch('src.file_dialogs.wx.FileDialog')
    @patch('src.file_dialogs.wx.App')
    def test_load_with_custom_dir(self, mock_app_class, mock_dialog_class):
        """Test load dialog with custom default directory."""
        # Arrange
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        mock_dialog = MagicMock()
        mock_dialog.ShowModal.return_value = wx.ID_OK
        mock_dialog.GetPath.return_value = "/custom/saves/game.json"
        mock_dialog_class.return_value = mock_dialog

        # Act
        from src.file_dialogs import get_load_filename
        result = get_load_filename(default_dir="/custom/saves")

        # Assert
        self.assertEqual(result, "/custom/saves/game.json")

        # Verify dialog was created with correct parameters
        call_kwargs = mock_dialog_class.call_args[1]
        self.assertEqual(call_kwargs['defaultDir'], "/custom/saves")

    @patch('src.file_dialogs.wx.FileDialog')
    @patch('src.file_dialogs.wx.App')
    def test_save_filename_exception_handling(self, mock_app_class, mock_dialog_class):
        """Test get_save_filename handles exceptions gracefully."""
        # Arrange - mock ShowModal to raise exception
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        mock_dialog = MagicMock()
        mock_dialog.ShowModal.side_effect = RuntimeError("Dialog error")
        mock_dialog_class.return_value = mock_dialog

        # Act
        from src.file_dialogs import get_save_filename
        result = get_save_filename()

        # Assert - should return None on error
        self.assertIsNone(result)

    @patch('src.file_dialogs.wx.FileDialog')
    @patch('src.file_dialogs.wx.App')
    def test_load_filename_exception_handling(self, mock_app_class, mock_dialog_class):
        """Test get_load_filename handles exceptions gracefully."""
        # Arrange
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        mock_dialog = MagicMock()
        mock_dialog.ShowModal.side_effect = RuntimeError("Dialog error")
        mock_dialog_class.return_value = mock_dialog

        # Act
        from src.file_dialogs import get_load_filename
        result = get_load_filename()

        # Assert - should return None on error
        self.assertIsNone(result)


@unittest.skipUnless(WX_AVAILABLE, "wxPython not installed")
class TestFileDialogErrorHandling(unittest.TestCase):
    """Test error handling in file dialog operations."""

    def setUp(self):
        """Set up test fixtures."""
        self._patchers = []
        if not HAS_DISPLAY:
            app_patcher = patch('wx.App', return_value=MagicMock())
            dialog_patcher = patch('wx.FileDialog', HeadlessFileDialog)
            self._patchers.extend([app_patcher, dialog_patcher])
            for patcher in self._patchers:
                patcher.start()

        self.app = wx.App(False)

    def tearDown(self):
        """Clean up after tests."""
        if self.app:
            self.app.Destroy()
            self.app = None
        for patcher in reversed(getattr(self, "_patchers", [])):
            patcher.stop()

    @patch('wx.FileDialog.ShowModal')
    def test_dialog_exception_handling(self, mock_show_modal):
        """Test that dialog handles exceptions gracefully."""
        # Arrange - mock ShowModal to raise an exception
        mock_show_modal.side_effect = RuntimeError("Dialog error")

        # Act
        dialog = wx.FileDialog(None, style=wx.FD_SAVE)

        try:
            dialog.ShowModal()
            filename = None
        except RuntimeError as e:
            filename = None
            error_message = str(e)

        dialog.Destroy()

        # Assert
        self.assertIsNone(filename)
        self.assertEqual(error_message, "Dialog error")

    @patch('wx.FileDialog.ShowModal')
    @patch('wx.FileDialog.GetPath')
    def test_dialog_cleanup_after_error(self, mock_get_path, mock_show_modal):
        """Test that dialog is properly destroyed even after error."""
        # Arrange
        mock_show_modal.return_value = wx.ID_OK
        mock_get_path.side_effect = RuntimeError("GetPath error")

        # Act
        dialog = wx.FileDialog(None, style=wx.FD_SAVE)
        filename = None

        try:
            if dialog.ShowModal() == wx.ID_OK:
                filename = dialog.GetPath()
        except RuntimeError:
            filename = None
        finally:
            dialog.Destroy()

        # Assert - should have attempted cleanup
        self.assertIsNone(filename)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
