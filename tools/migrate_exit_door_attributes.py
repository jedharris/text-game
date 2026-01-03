#!/usr/bin/env python3
"""Migrate Exit entities from properties-based door_id to direct attributes.

Converts from old format:
    {
      "id": "exit_library_up",
      "properties": {
        "type": "door",
        "door_id": "door_sanctum",
        "passage": "narrow stone stairs",
        "door_at": "loc_library"
      }
    }

To new format (v0.05):
    {
      "id": "exit_library_up",
      "door_id": "door_sanctum",
      "passage": "narrow stone stairs",
      "door_at": "loc_library",
      "properties": {
        "type": "door"
      }
    }

The migration:
1. Moves door_id from properties to direct attribute
2. Moves passage from properties to direct attribute (if present)
3. Moves door_at from properties to direct attribute (if present)
4. Keeps properties.type for backward compatibility
5. Updates game metadata version to 0.05

Usage:
    python tools/migrate_exit_door_attributes.py examples/spatial_game/game_state.json
    python tools/migrate_exit_door_attributes.py examples/*/game_state.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


def migrate_exit(exit_obj: Dict[str, Any]) -> bool:
    """Migrate a single exit from old to new format.

    Args:
        exit_obj: Exit entity dict

    Returns:
        True if exit was modified, False otherwise
    """
    properties = exit_obj.get("properties", {})

    # Check if this exit needs migration
    if "door_id" not in properties:
        return False

    modified = False

    # Move door_id to direct attribute
    if "door_id" in properties:
        exit_obj["door_id"] = properties.pop("door_id")
        modified = True

    # Move passage to direct attribute if present
    if "passage" in properties:
        exit_obj["passage"] = properties.pop("passage")
        modified = True

    # Move door_at to direct attribute if present
    if "door_at" in properties:
        exit_obj["door_at"] = properties.pop("door_at")
        modified = True

    return modified


def migrate_game_file(filepath: Path, dry_run: bool = False) -> int:
    """Migrate all exits in a game file.

    Args:
        filepath: Path to game_state.json
        dry_run: If True, show changes without writing file

    Returns:
        Number of exits modified
    """
    # Load game data
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Check if exits array exists
    if "exits" not in data:
        print(f"  No exits array found in {filepath.name}")
        return 0

    # Migrate each exit
    changes = 0
    for exit_obj in data["exits"]:
        if migrate_exit(exit_obj):
            changes += 1
            if dry_run:
                print(f"  Would migrate: {exit_obj['id']}")

    # Update metadata version if we made changes
    if changes > 0 and not dry_run:
        if "metadata" in data and "version" in data["metadata"]:
            data["metadata"]["version"] = "0.05"

    # Write back if not dry run
    if not dry_run and changes > 0:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            # Add trailing newline
            f.write('\n')

    return changes


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Exit entities from properties-based door_id to direct attributes"
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Game JSON files to process"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files"
    )

    args = parser.parse_args()

    total_changes = 0
    for filepath in args.files:
        if not filepath.exists():
            print(f"✗ {filepath}: File not found", file=sys.stderr)
            continue

        print(f"\n{'=' * 60}")
        print(f"Processing: {filepath.name}")
        print(f"{'=' * 60}")

        try:
            changes = migrate_game_file(filepath, args.dry_run)
            total_changes += changes

            if args.dry_run:
                print(f"\n✓ Would migrate {changes} exits in {filepath.name}")
            else:
                print(f"\n✓ Migrated {changes} exits in {filepath.name}")
        except Exception as e:
            print(f"✗ {filepath.name}: Error - {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    if args.dry_run:
        print(f"Total exits that would be migrated: {total_changes}")
    else:
        print(f"Total exits migrated: {total_changes}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
