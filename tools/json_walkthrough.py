#!/usr/bin/env python3
"""JSON structure walkthrough testing tool.

Tests narration JSON structure (the "recipe" sent to the LLM narrator).
Fast, deterministic testing suitable for CI.

Usage:
    python tools/json_walkthrough.py <game_dir> --file walkthrough.txt

Examples:
    python tools/json_walkthrough.py examples/spatial_game --file walkthroughs/json/phase1_checks.txt
    python tools/json_walkthrough.py examples/big_game --file walkthroughs/json/entity_refs.txt --verbose

Assertion syntax:
    assert_json: entity_refs is not empty
    assert_json: entity_refs contains bench
    assert_json: entity_refs[*bench*].traits contains "weathered stone"
    assert_json: scope.scene_kind == "location_entry"
    assert_json: scope.familiarity == "new"
    assert_json: must_mention is empty
    assert_json: must_mention.exits_text exists
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.game_engine import GameEngine
from src.llm_protocol import LLMProtocolHandler
from src.command_utils import parsed_to_json


def parse_json_assertion(line: str) -> Optional[Tuple[str, str, Optional[str]]]:
    """Parse JSON assertion line into components.

    Args:
        line: Assertion line like "assert_json: entity_refs is not empty"

    Returns:
        (path, operator, value) or None if not an assertion

    Examples:
        "assert_json: entity_refs is not empty" -> ("entity_refs", "is not empty", None)
        "assert_json: scope.scene_kind == location_entry" -> ("scope.scene_kind", "==", "location_entry")
        "assert_json: entity_refs[*bench*].traits contains weathered stone" -> (...)
    """
    line = line.strip()
    if not line.startswith("assert_json:"):
        return None

    # Remove prefix
    assertion = line[12:].strip()

    # Check for special operators first (multi-word)
    if " is not empty" in assertion:
        path = assertion.replace(" is not empty", "").strip()
        return (path, "is not empty", None)

    if " is empty" in assertion:
        path = assertion.replace(" is empty", "").strip()
        return (path, "is empty", None)

    if " exists" in assertion:
        path = assertion.replace(" exists", "").strip()
        return (path, "exists", None)

    if " not exists" in assertion:
        path = assertion.replace(" not exists", "").strip()
        return (path, "not exists", None)

    # Check for binary operators
    operators = [" contains ", " == ", " != ", " >= ", " <= ", " > ", " < "]
    for op in operators:
        if op in assertion:
            parts = assertion.split(op, 1)
            if len(parts) == 2:
                path = parts[0].strip()
                value = parts[1].strip()
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                return (path, op.strip(), value)

    raise ValueError(f"Invalid assertion syntax: {line}")


def evaluate_json_path(data: Dict[str, Any], path: str) -> Any:
    """Evaluate a path expression on JSON data.

    Supports:
    - Dotted paths: scope.scene_kind
    - Wildcard matching: entity_refs[*bench*] (finds first key containing 'bench')
    - Nested access: entity_refs[*bench*].traits

    Args:
        data: JSON data to evaluate
        path: Path expression

    Returns:
        Value at path, or raises AttributeError if not found
    """
    parts = path.split(".")
    current = data

    for part in parts:
        # Check for wildcard pattern: entity_refs[*bench*]
        wildcard_match = re.match(r"^(\w+)\[\*(\w+)\*\]$", part)
        if wildcard_match:
            dict_name = wildcard_match.group(1)
            search_term = wildcard_match.group(2)

            if not isinstance(current, dict) or dict_name not in current:
                raise AttributeError(f"Field '{dict_name}' not found in path '{path}'")

            target_dict = current[dict_name]
            if not isinstance(target_dict, dict):
                raise AttributeError(f"Field '{dict_name}' is not a dict in path '{path}'")

            # Find first key containing search term
            found_key = None
            for key in target_dict.keys():
                if search_term.lower() in key.lower():
                    found_key = key
                    break

            if not found_key:
                raise AttributeError(f"No key containing '{search_term}' found in '{dict_name}'")

            current = target_dict[found_key]
        else:
            # Regular dict access
            if isinstance(current, dict):
                if part not in current:
                    raise AttributeError(f"Field '{part}' not found in path '{path}'")
                current = current[part]
            else:
                raise AttributeError(f"Cannot access '{part}' on non-dict in path '{path}'")

    return current


def evaluate_json_assertion(
    narration: Dict[str, Any],
    path: str,
    operator: str,
    value: Optional[str]
) -> Tuple[bool, str]:
    """Evaluate a JSON assertion.

    Args:
        narration: Narration JSON dict
        path: Path to evaluate
        operator: Operator (exists, is empty, ==, contains, etc.)
        value: Expected value (for binary operators)

    Returns:
        (success, error_message) - error_message empty if success
    """
    try:
        # Special case: check if path exists
        if operator == "exists":
            try:
                evaluate_json_path(narration, path)
                return True, ""
            except AttributeError:
                return False, f"Path '{path}' does not exist"

        if operator == "not exists":
            try:
                evaluate_json_path(narration, path)
                return False, f"Path '{path}' exists but should not"
            except AttributeError:
                return True, ""

        # For all other operators, get the actual value
        try:
            actual = evaluate_json_path(narration, path)
        except AttributeError as e:
            return False, f"Path error: {e}"

        # Check emptiness
        if operator == "is empty":
            is_empty = (
                actual is None or
                actual == "" or
                actual == [] or
                actual == {}
            )
            if is_empty:
                return True, ""
            else:
                return False, f"Expected '{path}' to be empty, but got: {actual}"

        if operator == "is not empty":
            is_not_empty = (
                actual is not None and
                actual != "" and
                actual != [] and
                actual != {}
            )
            if is_not_empty:
                return True, ""
            else:
                return False, f"Expected '{path}' to not be empty, but it is"

        # Binary operators - convert value
        expected: Any = value

        # Try numeric conversion
        if value and value not in ["true", "false", "null", "none"]:
            try:
                if "." in value:
                    expected = float(value)
                else:
                    expected = int(value)
            except ValueError:
                pass  # Keep as string

        # Boolean/null conversion
        if value == "true":
            expected = True
        elif value == "false":
            expected = False
        elif value in ["null", "none"]:
            expected = None

        # Apply operator
        if operator == "==":
            success = actual == expected
        elif operator == "!=":
            success = actual != expected
        elif operator == ">":
            success = actual > expected
        elif operator == "<":
            success = actual < expected
        elif operator == ">=":
            success = actual >= expected
        elif operator == "<=":
            success = actual <= expected
        elif operator == "contains":
            # Handle different types
            if isinstance(actual, str):
                success = expected in actual
            elif isinstance(actual, list):
                success = expected in actual
            elif isinstance(actual, dict):
                success = expected in actual
            else:
                return False, f"Cannot use 'contains' on type {type(actual)}"
        else:
            return False, f"Unknown operator: {operator}"

        if success:
            return True, ""
        else:
            return False, f"Assertion failed: {path} {operator} {value}\n  Expected: {expected}\n  Actual: {actual}"

    except Exception as e:
        return False, f"Assertion error: {e}"


def run_json_walkthrough(
    engine: GameEngine,
    commands: List[str],
    verbose: bool = False,
    show_json: bool = False
) -> Tuple[int, int, int]:
    """Run commands and evaluate JSON assertions.

    Returns:
        (success_count, failure_count, assertion_failure_count)
    """
    handler = LLMProtocolHandler(engine.game_state, engine.behavior_manager)
    parser = engine.create_parser()

    success_count = 0
    failure_count = 0
    assertion_failures: List[Tuple[int, str, str]] = []

    for i, line in enumerate(commands, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Check for JSON assertion
        assertion = parse_json_assertion(line)
        if assertion:
            path, operator, value = assertion

            # Need previous result
            if not hasattr(run_json_walkthrough, '_last_result'):
                print(f"\n[⚠] Line {i}: Assertion before any command")
                assertion_failures.append((i, line, "No command executed yet"))
                continue

            last_result = run_json_walkthrough._last_result
            narration = last_result.get("narration", {})

            if verbose:
                print(f"  Checking: {path} {operator} {value if value else ''}")

            assert_success, error = evaluate_json_assertion(narration, path, operator, value)
            if assert_success:
                print(f"  [✓] {line}")
            else:
                print(f"  [✗] {line}")
                print(f"      {error}")
                assertion_failures.append((i, line, error))

            continue

        # Regular command - parse and execute
        cmd = line.strip()
        if not cmd:
            continue

        print(f"\n{'='*60}")
        print(f"> {cmd}")
        print("-" * 60)

        # Parse command
        parsed = parser.parse_command(cmd)
        if not parsed:
            print(f"[✗] PARSE ERROR: Could not parse '{cmd}'")
            failure_count += 1
            result = {"success": False, "error": {"message": f"Could not parse: {cmd}"}}
            run_json_walkthrough._last_result = result
            continue

        # Convert to JSON message
        message = parsed_to_json(parsed)

        # Execute via handler
        result = handler.handle_command(message)
        run_json_walkthrough._last_result = result

        # Display result
        success = result.get("success", False)
        if success:
            success_count += 1
            print(f"[✓] SUCCESS")
        else:
            failure_count += 1
            error_msg = result.get("error", {}).get("message", "Unknown error")
            print(f"[✗] FAILURE: {error_msg}")

        # Show narration primary text
        narration = result.get("narration", {})
        primary = narration.get("primary_text", "")
        if primary and not verbose:
            print(f"\n{primary}")

        # Show full JSON if requested
        if show_json or verbose:
            print(f"\nNARRATION JSON:")
            print(json.dumps(narration, indent=2, ensure_ascii=False))

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print("-" * 60)
    print(f"Commands: {success_count} succeeded, {failure_count} failed")
    print(f"Assertions: {len(assertion_failures)} failed")

    if assertion_failures:
        print(f"\n{'='*60}")
        print(f"ASSERTION FAILURES:")
        for line_num, assertion_text, error in assertion_failures:
            print(f"\n  Line {line_num}: {assertion_text}")
            print(f"  {error}")

    return success_count, failure_count, len(assertion_failures)


def main():
    argparser = argparse.ArgumentParser(
        description="Test narration JSON structure with assertions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    argparser.add_argument("game_dir", help="Path to game directory")
    argparser.add_argument("--file", "-f", required=True, help="Walkthrough file with JSON assertions")
    argparser.add_argument("--verbose", "-v", action="store_true",
                          help="Show detailed output")
    argparser.add_argument("--show-json", action="store_true",
                          help="Show full narration JSON for each command")

    args = argparser.parse_args()

    # Load commands from file
    with open(args.file, "r") as f:
        commands = [line.rstrip() for line in f]

    print(f"Loading game from {args.game_dir}...")

    try:
        engine = GameEngine(Path(args.game_dir))
    except Exception as e:
        print(f"Error loading game: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    # Count executable lines
    executable = [c for c in commands if c.strip() and not c.strip().startswith("#")]
    print(f"Running {len(executable)} commands with JSON assertions...\n")

    success_count, failure_count, assertion_failure_count = run_json_walkthrough(
        engine,
        commands,
        args.verbose,
        args.show_json
    )

    return 0 if assertion_failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
