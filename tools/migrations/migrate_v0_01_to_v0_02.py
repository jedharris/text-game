#!/usr/bin/env python3
"""Migration tool: v_0.01 -> v_0.02

Changes:
1. Lock `name` field now required (defaults to lock id if missing)
2. Schema version updated to v_0.02 in metadata

Usage:
    python -m tools.migrations.migrate_v0_01_to_v0_02 input.json [output.json]

If output.json is not specified, the file is modified in place.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any


def migrate_lock(lock: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate a single lock entry.

    Adds required 'name' field if missing, defaulting to lock id.
    """
    if "name" not in lock:
        lock_id = lock.get("id", "unknown_lock")
        # Convert id to readable name: "lock_treasure" -> "Treasure Lock"
        name_parts = lock_id.replace("lock_", "").replace("_", " ").split()
        name = " ".join(word.capitalize() for word in name_parts) + " Lock"
        lock["name"] = name
    return lock


def migrate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Update schema version in metadata."""
    metadata["schema_version"] = "v_0.02"
    return metadata


def migrate_game_state(data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate entire game state from v_0.01 to v_0.02."""
    # Migrate metadata
    if "metadata" in data:
        data["metadata"] = migrate_metadata(data["metadata"])

    # Migrate locks
    if "locks" in data:
        data["locks"] = [migrate_lock(lock) for lock in data["locks"]]

    return data


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    # Load input
    with open(input_path, 'r') as f:
        data = json.load(f)

    # Check current version
    current_version = data.get("metadata", {}).get("schema_version", "v_0.01")
    if current_version == "v_0.02":
        print(f"File already at v_0.02: {input_path}")
        sys.exit(0)

    # Migrate
    migrated = migrate_game_state(data)

    # Save output
    with open(output_path, 'w') as f:
        json.dump(migrated, f, indent=2)

    print(f"Migrated {input_path} to v_0.02")
    if output_path != input_path:
        print(f"Output written to: {output_path}")


if __name__ == "__main__":
    main()
