#!/usr/bin/env python3
"""Walkthrough testing tool.

Run a sequence of commands against the game engine and display results.
Useful for testing puzzles and game scenarios without the narrator.

Usage:
    python tools/walkthrough.py <game_dir> "cmd1" "cmd2" "cmd3" ...
    python tools/walkthrough.py <game_dir> --file walkthrough.txt

Examples:
    python tools/walkthrough.py examples/big_game "look" "take bucket" "go north"
    python tools/walkthrough.py examples/big_game --file grotto_test.txt

The --verbose flag shows full JSON responses instead of just primary_text.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.game_engine import GameEngine


def extract_result_message(result: Dict[str, Any]) -> str:
    """Extract human-readable message from result."""
    if "narration" in result:
        narration = result["narration"]
        parts = [narration.get("primary_text", "")]
        if "secondary_beats" in narration:
            parts.extend(narration["secondary_beats"])
        return "\n".join(p for p in parts if p)

    if "error" in result:
        return f"ERROR: {result['error'].get('message', 'Unknown error')}"

    return result.get("primary_text", str(result))


def run_walkthrough(
    engine: GameEngine,
    commands: List[str],
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """Run a sequence of commands and return results."""
    results = []
    parser = engine.create_parser()

    for i, cmd in enumerate(commands, 1):
        cmd = cmd.strip()
        if not cmd or cmd.startswith("#"):
            # Skip empty lines and comments
            continue

        print(f"\n{'='*60}")
        print(f"> {cmd}")
        print("-" * 60)

        # Parse the command
        parsed = parser.parse_command(cmd)
        if not parsed:
            print(f"PARSE ERROR: Could not parse '{cmd}'")
            result = {"success": False, "error": {"message": f"Could not parse: {cmd}"}}
        else:
            # Build action dict from parsed command
            # All fields can be WordEntry; protocol handler extracts strings as needed
            action: Dict[str, Any] = {"verb": parsed.verb}
            if parsed.direct_object:
                action["object"] = parsed.direct_object
            if parsed.indirect_object:
                action["indirect_object"] = parsed.indirect_object
            if parsed.direct_adjective:
                action["adjective"] = parsed.direct_adjective
            if parsed.indirect_adjective:
                action["indirect_adjective"] = parsed.indirect_adjective
            if parsed.preposition:
                action["preposition"] = parsed.preposition

            result = engine.json_handler.handle_command({
                "type": "command",
                "action": action
            })

        results.append({"command": cmd, "result": result})

        if verbose:
            print(json.dumps(result, indent=2, default=str))
        else:
            msg = extract_result_message(result)
            success = result.get("success", False)
            status = "✓" if success else "✗"
            print(f"[{status}] {msg}")

    return results


def main():
    argparser = argparse.ArgumentParser(
        description="Run walkthrough commands against the game engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    argparser.add_argument("game_dir", help="Path to game directory")
    argparser.add_argument("commands", nargs="*", help="Commands to run")
    argparser.add_argument("--file", "-f", help="Read commands from file (one per line)")
    argparser.add_argument("--verbose", "-v", action="store_true", help="Show full JSON output")

    args = argparser.parse_args()

    # Collect commands
    commands = list(args.commands)

    if args.file:
        with open(args.file, "r") as f:
            commands.extend(line.strip() for line in f if line.strip())

    if not commands:
        print("No commands provided. Use positional args or --file.", file=sys.stderr)
        return 1

    print(f"Loading game from {args.game_dir}...")

    try:
        engine = GameEngine(Path(args.game_dir))
    except Exception as e:
        print(f"Error loading game: {e}", file=sys.stderr)
        return 1

    print(f"Running {len(commands)} commands...")

    results = run_walkthrough(engine, commands, args.verbose)

    # Summary
    print(f"\n{'='*60}")
    success_count = sum(1 for r in results if r["result"].get("success", False))
    print(f"Summary: {success_count}/{len(results)} commands succeeded")

    return 0


if __name__ == "__main__":
    sys.exit(main())
