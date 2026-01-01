#!/usr/bin/env python3
"""Convenience launcher for xplm_game.py that works from the current repository.

This launcher runs src.xplm_game as a module to avoid sys.path manipulation.

Usage:
    python run_xplm_game.py examples/big_game
    python run_xplm_game.py examples/big_game --model qwen-7b
    python run_xplm_game.py examples/big_game --debug --show-traits
"""

import subprocess
import sys

if __name__ == '__main__':
    # Run xplm_game as a module to avoid path manipulation issues
    # This uses Python's module system properly
    cmd = [sys.executable, '-m', 'src.xplm_game'] + sys.argv[1:]
    sys.exit(subprocess.run(cmd).returncode)
