#!/usr/bin/env python3
"""
Migrate game state files from pre-versioned format to v_0.01.

Usage:
    python migrate_to_v_0_01.py <input_file> [output_file]

If no output_file is specified, the input file is modified in place
(with a .bak backup created).

The only change in v_0.01 is adding schema_version to metadata.
"""

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Optional

VERSION_TARGET = "v_0.01"


def detect_version(state: dict[str, Any]) -> Optional[str]:
    """
    Detect the schema version of a game state.

    Returns None if no schema_version field exists (pre-versioned).
    Returns the schema_version string otherwise.
    """
    metadata = state.get("metadata", {})
    return metadata.get("schema_version")


def migrate_to_v_0_01(state: dict[str, Any]) -> dict[str, Any]:
    """
    Migrate a pre-versioned game state to v_0.01.

    Args:
        state: The game state dict to migrate.

    Returns:
        A new dict with the migration applied.

    Raises:
        ValueError: If the state is already at v_0.01.
    """
    current_version = detect_version(state)
    if current_version == VERSION_TARGET:
        raise ValueError(f"State is already at version {VERSION_TARGET}")

    # Deep copy to avoid modifying original
    result = copy.deepcopy(state)

    # Ensure metadata exists
    if "metadata" not in result:
        result["metadata"] = {}

    # Add schema version
    result["metadata"]["schema_version"] = VERSION_TARGET

    return result


def migrate_file(input_path: str, output_path: Optional[str] = None) -> None:
    """
    Migrate a game state JSON file to v_0.01.

    Args:
        input_path: Path to the input JSON file.
        output_path: Optional path for output. If None, modifies in place
                    and creates a .bak backup.
    """
    input_file = Path(input_path)

    # Read input
    with open(input_file, "r", encoding="utf-8") as f:
        state = json.load(f)

    # Migrate
    migrated = migrate_to_v_0_01(state)

    # Determine output location
    if output_path is None:
        # In-place: create backup first
        backup_path = input_file.with_suffix(input_file.suffix + ".bak")
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        out_file = input_file
    else:
        out_file = Path(output_path)

    # Write output
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(migrated, f, indent=2)
        f.write("\n")  # Trailing newline


def main() -> int:
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Migrate game state from pre-versioned format to v_0.01."
    )
    parser.add_argument(
        "input_file",
        help="Path to the input JSON file.",
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Optional output path. If omitted, modifies input in place with .bak backup.",
    )

    args = parser.parse_args()

    try:
        migrate_file(args.input_file, args.output_file)
        print(f"Successfully migrated to {VERSION_TARGET}")
        if args.output_file:
            print(f"Output written to: {args.output_file}")
        else:
            print(f"File updated in place: {args.input_file}")
            print(f"Backup created: {args.input_file}.bak")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
