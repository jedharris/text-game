"""
State v0.1.1 migration: Add default behaviors to all actors.

What it does:
- Adds "behaviors.actor_lib.npc_actions" to all actors that don't have a behaviors list
- For actors with behaviors but missing npc_actions, appends it to their list
- Skips actors marked with "is_object": true (waystone_spirit, etc.)
- Sets metadata.version to "0.1.1"

This migration supports Phase 1 of the hybrid dispatcher implementation by ensuring
all NPCs have the default npc_take_action handler.

Usage:
    python tools/migrations/migrate_v0_1_0_to_v0_1_1.py path/to/game_state.json [more.json ...]

By default, writes changes in-place. Use --stdout to print to stdout instead.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_ACTOR_BEHAVIORS = ["behaviors.shared.lib.actor_lib.npc_actions"]


def add_default_behaviors_to_actors(data: Dict[str, Any]) -> int:
    """Add default behaviors to all actors.

    Returns:
        Number of actors modified
    """
    actors = data.get("actors", {})
    if not isinstance(actors, dict):
        return 0

    modified_count = 0

    for actor_id, actor in actors.items():
        if not isinstance(actor, dict):
            continue

        # Skip actors that are actually objects (waystone_spirit, etc.)
        if actor.get("properties", {}).get("is_object", False):
            continue

        # Get or create behaviors list
        behaviors = actor.get("behaviors")

        if not behaviors:
            # No behaviors at all - add default
            actor["behaviors"] = DEFAULT_ACTOR_BEHAVIORS.copy()
            modified_count += 1
        elif isinstance(behaviors, list):
            # Has behaviors - ensure npc_actions is in the list
            if "behaviors.shared.lib.actor_lib.npc_actions" not in behaviors:
                behaviors.append("behaviors.shared.lib.actor_lib.npc_actions")
                modified_count += 1

    return modified_count


def migrate_file(path: Path, stdout: bool = False) -> bool:
    """Migrate a game_state.json file. Returns True if changes were made."""
    original_text = path.read_text(encoding="utf-8")
    data = json.loads(original_text)

    # Check current version
    metadata = data.get("metadata", {})
    current_version = metadata.get("version", "unknown")

    # Add default behaviors to actors
    modified_count = add_default_behaviors_to_actors(data)

    # Bump version to 0.1.1
    if not isinstance(metadata, dict):
        metadata = {}
        data["metadata"] = metadata

    if metadata.get("version") != "0.1.1":
        metadata["version"] = "0.1.1"

    # Serialize back to JSON
    new_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"

    if new_text == original_text:
        return False

    if stdout:
        print(new_text, end="")
    else:
        path.write_text(new_text, encoding="utf-8")
        print(f"✓ {path}: migrated from {current_version} to 0.1.1 ({modified_count} actors updated)")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate game_state.json from v0.1.0 to v0.1.1 (add default actor behaviors)"
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="One or more game_state.json files to migrate"
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print migrated JSON to stdout instead of writing in-place"
    )
    args = parser.parse_args()

    any_changed = False
    for path in args.files:
        if not path.exists():
            print(f"✗ {path}: file not found")
            continue

        try:
            changed = migrate_file(path, stdout=args.stdout)
            any_changed = any_changed or changed
            if not changed and not args.stdout:
                print(f"- {path}: no changes needed")
        except Exception as e:
            print(f"✗ {path}: {e}")

    return 0 if any_changed else 1


if __name__ == "__main__":
    exit(main())
