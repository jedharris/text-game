#!/usr/bin/env python3
"""
Game Runner - Double-click to play the text adventure game.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.resolve()
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

        # Call the main function
        if hasattr(game_module, 'main'):
            game_module.main()

    except Exception as e:
        print(f"Error running game: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
