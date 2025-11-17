"""
Basic wxPython verification tests.

Tests to verify wxPython installation and basic functionality.
"""

import sys
import wx


def test_1_import():
    """Test 1: Verify wxPython imports successfully."""
    try:
        import wx
        print("✓ Test 1 PASSED: wxPython imports successfully")
        print(f"  wxPython version: {wx.version()}")
        return True
    except ImportError as e:
        print(f"✗ Test 1 FAILED: Cannot import wxPython: {e}")
        return False


def test_2_basic_frame():
    """Test 2: Create basic frame without showing it."""
    try:
        app = wx.App(False)  # Create app without showing
        frame = wx.Frame(None, title="Test Frame", size=(400, 300))

        # Verify frame was created
        assert frame is not None
        assert frame.GetTitle() == "Test Frame"
        assert frame.GetSize() == (400, 300)

        frame.Destroy()
        app.Destroy()

        print("✓ Test 2 PASSED: Basic frame creation works")
        return True
    except Exception as e:
        print(f"✗ Test 2 FAILED: Frame creation error: {e}")
        return False


def test_3_text_controls():
    """Test 3: Create text input/output controls."""
    try:
        app = wx.App(False)
        frame = wx.Frame(None)

        # Create a panel
        panel = wx.Panel(frame)

        # Create multiline text output (read-only)
        output_text = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP
        )

        # Create single-line text input
        input_text = wx.TextCtrl(
            panel,
            style=wx.TE_PROCESS_ENTER
        )

        # Test writing to output
        output_text.AppendText("Test output line 1\n")
        output_text.AppendText("Test output line 2\n")

        # Test input
        input_text.SetValue("test input")
        assert input_text.GetValue() == "test input"

        # Test read-only
        assert output_text.IsEditable() == False
        assert input_text.IsEditable() == True

        frame.Destroy()
        app.Destroy()

        print("✓ Test 3 PASSED: Text controls work correctly")
        return True
    except Exception as e:
        print(f"✗ Test 3 FAILED: Text control error: {e}")
        return False


def test_4_event_binding():
    """Test 4: Test event binding functionality."""
    try:
        app = wx.App(False)
        frame = wx.Frame(None)
        panel = wx.Panel(frame)

        # Create a button
        button = wx.Button(panel, label="Test Button")

        # Track if event fired
        event_fired = [False]

        def on_button_click(event):
            event_fired[0] = True

        # Bind event
        button.Bind(wx.EVT_BUTTON, on_button_click)

        # Simulate button click
        click_event = wx.CommandEvent(wx.EVT_BUTTON.typeId, button.GetId())
        button.GetEventHandler().ProcessEvent(click_event)

        assert event_fired[0] == True

        frame.Destroy()
        app.Destroy()

        print("✓ Test 4 PASSED: Event binding works correctly")
        return True
    except Exception as e:
        print(f"✗ Test 4 FAILED: Event binding error: {e}")
        return False


def test_5_layout_managers():
    """Test 5: Test layout managers (BoxSizer)."""
    try:
        app = wx.App(False)
        frame = wx.Frame(None)
        panel = wx.Panel(frame)

        # Create a vertical box sizer
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Add some controls
        output = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        input_ctrl = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)

        # Add to sizer with proportions
        sizer.Add(output, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        sizer.Add(input_ctrl, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)

        # Set sizer for panel
        panel.SetSizer(sizer)

        # Verify sizer was set
        assert panel.GetSizer() is not None
        assert len(sizer.GetChildren()) == 2

        frame.Destroy()
        app.Destroy()

        print("✓ Test 5 PASSED: Layout managers work correctly")
        return True
    except Exception as e:
        print(f"✗ Test 5 FAILED: Layout manager error: {e}")
        return False


def test_6_menu_bar():
    """Test 6: Test menu bar creation."""
    try:
        app = wx.App(False)
        frame = wx.Frame(None)

        # Create menu bar
        menu_bar = wx.MenuBar()

        # Create a File menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, "&New\tCtrl+N", "Create new game")
        file_menu.Append(wx.ID_OPEN, "&Open\tCtrl+O", "Load game")
        file_menu.Append(wx.ID_SAVE, "&Save\tCtrl+S", "Save game")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit application")

        # Add menu to menu bar
        menu_bar.Append(file_menu, "&File")

        # Set menu bar for frame
        frame.SetMenuBar(menu_bar)

        # Verify menu bar was set
        assert frame.GetMenuBar() is not None
        assert frame.GetMenuBar().GetMenuCount() == 1

        frame.Destroy()
        app.Destroy()

        print("✓ Test 6 PASSED: Menu bar creation works")
        return True
    except Exception as e:
        print(f"✗ Test 6 FAILED: Menu bar error: {e}")
        return False


def test_7_status_bar():
    """Test 7: Test status bar creation."""
    try:
        app = wx.App(False)
        frame = wx.Frame(None)

        # Create status bar with 2 fields
        status_bar = frame.CreateStatusBar(2)

        # Set text in status bar
        status_bar.SetStatusText("Location: Start Room", 0)
        status_bar.SetStatusText("Inventory: Empty", 1)

        # Verify status bar
        assert frame.GetStatusBar() is not None
        assert status_bar.GetFieldsCount() == 2

        frame.Destroy()
        app.Destroy()

        print("✓ Test 7 PASSED: Status bar creation works")
        return True
    except Exception as e:
        print(f"✗ Test 7 FAILED: Status bar error: {e}")
        return False


def test_8_text_styling():
    """Test 8: Test text styling capabilities."""
    try:
        app = wx.App(False)
        frame = wx.Frame(None)
        panel = wx.Panel(frame)

        # Create a rich text control
        text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_RICH2)

        # Test different text styles
        text.SetDefaultStyle(wx.TextAttr(wx.BLUE))
        text.AppendText("Blue text\n")

        text.SetDefaultStyle(wx.TextAttr(wx.RED, font=wx.Font(
            12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD
        )))
        text.AppendText("Bold red text\n")

        text.SetDefaultStyle(wx.TextAttr(wx.BLACK))
        text.AppendText("Normal text\n")

        assert text.GetValue().count('\n') == 3

        frame.Destroy()
        app.Destroy()

        print("✓ Test 8 PASSED: Text styling works")
        return True
    except Exception as e:
        print(f"✗ Test 8 FAILED: Text styling error: {e}")
        return False


def run_all_tests():
    """Run all verification tests."""
    print("=" * 70)
    print("wxPython Installation and Functionality Tests")
    print("=" * 70)
    print()

    tests = [
        test_1_import,
        test_2_basic_frame,
        test_3_text_controls,
        test_4_event_binding,
        test_5_layout_managers,
        test_6_menu_bar,
        test_7_status_bar,
        test_8_text_styling,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"✗ Test raised exception: {e}")
            results.append(False)
            print()

    # Summary
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed! wxPython is ready for integration.")
    else:
        print(f"✗ {total - passed} test(s) failed. Review errors above.")

    print("=" * 70)

    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
