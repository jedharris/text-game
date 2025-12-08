#!/usr/bin/env python3
"""Migration tool: v_0.02 -> v_0.03

Changes:
1. Schema version updated to v_0.03 in metadata

Engine changes (no state format changes):
- Event registry system added to BehaviorManager
- Events discovered from vocabulary at load time
- Engine hooks (location_entered, visibility_check) for internal events
- Event fallbacks declared in vocabulary
- Load-time validation of on_* prefix usage

Usage:
    python -m tools.migrations.migrate_v0_02_to_v0_03 input.json [output.json]

If output.json is not specified, the file is modified in place.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any


def migrate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Update schema version in metadata."""
    metadata["schema_version"] = "v_0.03"
    return metadata


def migrate_game_state(data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate entire game state from v_0.02 to v_0.03.

    This migration only updates the schema version since v_0.03
    introduces engine changes (event registry) without modifying
    the game state format.
    """
    # Migrate metadata
    if "metadata" in data:
        data["metadata"] = migrate_metadata(data["metadata"])

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
    if current_version == "v_0.03":
        print(f"File already at v_0.03: {input_path}")
        sys.exit(0)

    if current_version != "v_0.02":
        print(f"Error: Expected v_0.02, got {current_version}. Run earlier migrations first.")
        sys.exit(1)

    # Migrate
    migrated = migrate_game_state(data)

    # Save output
    with open(output_path, 'w') as f:
        json.dump(migrated, f, indent=2)

    print(f"Migrated {input_path} to v_0.03")
    if output_path != input_path:
        print(f"Output written to: {output_path}")


if __name__ == "__main__":
    main()
