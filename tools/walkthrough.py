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
    python tools/walkthrough.py examples/big_game --file test.txt --stop-on-error
    python tools/walkthrough.py examples/big_game --file test.txt --save-state final.json

The --verbose flag shows full JSON responses instead of just primary_text.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.game_engine import GameEngine


class FailureCategory(Enum):
    """Categories of command failures for better diagnostics."""
    PARSE_ERROR = "Parse Error"
    BLOCKED_ACTION = "Blocked Action"
    MISSING_ITEM = "Missing Item"
    COMBAT_FAILURE = "Combat Failure"
    UNKNOWN = "Unknown Error"


def categorize_failure(result: Dict[str, Any], cmd: str) -> FailureCategory:
    """Categorize a failed command for better error reporting."""
    if "error" in result:
        error_msg = result["error"].get("message", "").lower()

        if "parse" in error_msg or "could not parse" in error_msg:
            return FailureCategory.PARSE_ERROR
        if "block" in error_msg or "can't go" in error_msg:
            return FailureCategory.BLOCKED_ACTION
        if "don't see" in error_msg or "don't have" in error_msg:
            return FailureCategory.MISSING_ITEM

        return FailureCategory.UNKNOWN

    # Check narration for clues
    if "narration" in result:
        primary = result["narration"].get("primary_text", "").lower()

        if "block" in primary or "can't go" in primary:
            return FailureCategory.BLOCKED_ACTION
        if "don't see" in primary or "don't have" in primary:
            return FailureCategory.MISSING_ITEM
        if "hits" in primary and "damage" in primary:
            return FailureCategory.COMBAT_FAILURE

    return FailureCategory.UNKNOWN


def extract_result_message(result: Dict[str, Any]) -> str:
    """Extract human-readable message from result."""
    parts = []

    if "narration" in result:
        narration = result["narration"]
        if narration.get("primary_text"):
            parts.append(narration.get("primary_text"))
        if "secondary_beats" in narration:
            parts.extend(narration["secondary_beats"])

    # Add turn phase messages (NPC actions, death checks, etc.)
    if "turn_phase_messages" in result:
        parts.extend(result["turn_phase_messages"])

    if parts:
        return "\n".join(p for p in parts if p)

    if "error" in result:
        return f"ERROR: {result['error'].get('message', 'Unknown error')}"

    return result.get("primary_text", str(result))


def extract_hp_info(result: Dict[str, Any]) -> Optional[str]:
    """Extract HP information from combat results."""
    # Check for actor status in result
    if "actor_status" in result:
        status_parts = []
        for actor_id, status in result["actor_status"].items():
            hp = status.get("hp")
            max_hp = status.get("max_hp")
            if hp is not None and max_hp is not None:
                status_parts.append(f"{actor_id}: {hp}/{max_hp} HP")

        if status_parts:
            return "  " + " | ".join(status_parts)

    return None


def parse_command_annotations(line: str) -> Tuple[str, bool]:
    """Parse command line and extract annotations.

    Returns:
        (command, expect_success)
    """
    expect_success = True
    cmd = line.strip()

    # Check for EXPECT_FAIL annotation
    if "# EXPECT_FAIL" in cmd or "# EXPECTED_FAILURE" in cmd:
        expect_success = False
        # Remove annotation from command
        cmd = cmd.split("#")[0].strip()

    return cmd, expect_success


def run_walkthrough(
    engine: GameEngine,
    commands: List[str],
    verbose: bool = False,
    stop_on_error: bool = False,
    show_hp: bool = False
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Run a sequence of commands and return results.

    Returns:
        (results, failure_counts)
    """
    results = []
    parser = engine.create_parser()
    failure_counts: Dict[str, int] = {}
    unexpected_failures = []

    for i, line in enumerate(commands, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            # Skip empty lines and comments
            continue

        # Parse annotations
        cmd, expect_success = parse_command_annotations(line)
        if not cmd:
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

        success = result.get("success", False)
        results.append({
            "command": cmd,
            "result": result,
            "expect_success": expect_success
        })

        # Categorize failure if command failed
        if not success:
            category = categorize_failure(result, cmd)
            failure_counts[category.value] = failure_counts.get(category.value, 0) + 1

            # Track unexpected failures
            if expect_success:
                unexpected_failures.append((i, cmd, category))

        if verbose:
            print(json.dumps(result, indent=2, default=str))
        else:
            msg = extract_result_message(result)
            status = "✓" if success else "✗"

            # Mark unexpected failures
            if not success and expect_success:
                status = "⚠"
            elif success and not expect_success:
                status = "?"  # Expected to fail but succeeded

            print(f"[{status}] {msg}")

            # Show HP if requested and available
            if show_hp:
                hp_info = extract_hp_info(result)
                if hp_info:
                    print(hp_info)

        # Stop on error if requested
        if stop_on_error and not success:
            print(f"\n⚠️  Stopped at command {i} due to failure")
            break

    # Report unexpected failures
    if unexpected_failures:
        print(f"\n{'='*60}")
        print(f"⚠️  {len(unexpected_failures)} UNEXPECTED FAILURES:")
        for line_num, cmd, category in unexpected_failures:
            print(f"  Line {line_num}: {cmd}")
            print(f"    Category: {category.value}")

    return results, failure_counts


def save_game_state(engine: GameEngine, output_path: Path) -> None:
    """Save current game state to file."""
    from src.state_manager import game_state_to_dict

    state_dict = game_state_to_dict(engine.game_state)
    with open(output_path, "w") as f:
        json.dump(state_dict, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Game state saved to {output_path}")


def main():
    argparser = argparse.ArgumentParser(
        description="Run walkthrough commands against the game engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    argparser.add_argument("game_dir", help="Path to game directory")
    argparser.add_argument("commands", nargs="*", help="Commands to run")
    argparser.add_argument("--file", "-f", help="Read commands from file (one per line)")
    argparser.add_argument("--verbose", "-v", action="store_true",
                          help="Show full JSON output")
    argparser.add_argument("--stop-on-error", action="store_true",
                          help="Stop execution on first failed command")
    argparser.add_argument("--save-state", metavar="FILE",
                          help="Save final game state to FILE")
    argparser.add_argument("--show-hp", action="store_true",
                          help="Show HP after combat rounds")

    args = argparser.parse_args()

    # Collect commands
    commands = list(args.commands)

    if args.file:
        with open(args.file, "r") as f:
            commands.extend(line.rstrip() for line in f)

    if not commands:
        print("No commands provided. Use positional args or --file.", file=sys.stderr)
        return 1

    print(f"Loading game from {args.game_dir}...")

    try:
        engine = GameEngine(Path(args.game_dir))
    except Exception as e:
        print(f"Error loading game: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    # Filter out pure comment lines and empty lines for count
    executable_commands = [c for c in commands if c.strip() and not c.strip().startswith("#")]
    print(f"Running {len(executable_commands)} commands...")

    results, failure_counts = run_walkthrough(
        engine,
        commands,
        args.verbose,
        args.stop_on_error,
        args.show_hp
    )

    # Summary
    print(f"\n{'='*60}")
    success_count = sum(1 for r in results if r["result"].get("success", False))
    total_count = len(results)
    print(f"Summary: {success_count}/{total_count} commands succeeded")

    # Show failure breakdown
    if failure_counts:
        print(f"\nFailure breakdown:")
        for category, count in sorted(failure_counts.items()):
            print(f"  {category}: {count}")

    # Check for unexpected outcomes
    unexpected_failures = sum(1 for r in results
                            if not r["result"].get("success", False)
                            and r.get("expect_success", True))
    unexpected_successes = sum(1 for r in results
                              if r["result"].get("success", False)
                              and not r.get("expect_success", True))

    if unexpected_failures > 0:
        print(f"\n⚠️  {unexpected_failures} commands failed unexpectedly")
    if unexpected_successes > 0:
        print(f"\n?  {unexpected_successes} commands succeeded when expected to fail")

    # Save state if requested
    if args.save_state:
        save_game_state(engine, Path(args.save_state))

    return 0 if unexpected_failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
