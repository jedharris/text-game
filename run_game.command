#!/usr/bin/env python3
"""
Game Runner - Double-click to play the text adventure game.

This script can be copied anywhere. It finds the game project using:
1. A symlink named 'game_project' in the same directory as this script
2. A hardcoded fallback path

To use from outside the project:
  ln -s /path/to/text-game game_project
"""

import sys
import os
from pathlib import Path

def find_game_project():
    """
    Find the game project directory.

    Checks (in order):
    1. Symlink named 'text_game' next to this script
    2. Hardcoded path (if script is in the project)

    Returns:
        Path to project root, or None if not found
    """
    script_dir = Path(__file__).parent.resolve()

    # Option 1: Check for 'game_project' symlink
    symlink_path = script_dir / "text_game"
    if symlink_path.exists():
        resolved = symlink_path.resolve()
        # Verify it's actually the game project
        if (resolved / "examples" / "simple_engine.py").exists():
            return resolved

    # Option 2: Hardcoded path (assumes script is in project)
    hardcoded_path = Path("/Users/jed/Development/text-game")
    if (hardcoded_path / "examples" / "simple_engine.py").exists():
        return hardcoded_path

    return None

# Capture the launch directory BEFORE changing directories
# This is where the user was when they double-clicked the script
launch_dir = Path.cwd().resolve()

# Find the project
project_root = find_game_project()

if project_root is None:
    print("=" * 70)
    print("ERROR: Cannot find the game project!")
    print("=" * 70)
    print()
    print("This script needs to find the game project directory.")
    print()
    print("To use this script from outside the project directory:")
    print("  1. Create a symlink named 'game_project' next to this script:")
    print(f"     cd {Path(__file__).parent.resolve()}")
    print("     ln -s /path/to/text-game game_project")
    print()
    print("Or update the hardcoded path in this script.")
    print()
    input("Press Enter to exit...")
    sys.exit(1)

# Add the project root to the Python path
sys.path.insert(0, str(project_root))

# Change to the project directory so relative paths work
os.chdir(project_root)

# Import and run the game
if __name__ == "__main__":
    try:
        # Import the simple_engine module and run it
        import importlib.util

        game_path = project_root / "examples" / "simple_engine.py"

        # Load the game module
        spec = importlib.util.spec_from_file_location("simple_engine", game_path)
        if spec is None or spec.loader is None:
            print(f"Error: Could not load game from {game_path}")
            sys.exit(1)

        game_module = importlib.util.module_from_spec(spec)
        sys.modules["simple_engine"] = game_module
        spec.loader.exec_module(game_module)

        # Call the main function, passing launch directory for save/load dialogs
        if hasattr(game_module, 'main'):
            game_module.main(save_load_dir=str(launch_dir))

    except Exception as e:
        print(f"Error running game: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
