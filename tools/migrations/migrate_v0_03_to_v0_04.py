"""
State v0.04 migration: normalize behaviors and bump version to 0.04.

What it does:
- Converts legacy behavior dicts (e.g., {"on_take": "module:on_take"}) to lists of modules.
- Strips function names from "module:function" strings, keeping only the module path.
- Deduplicates and preserves order of behavior module references.
- Sets metadata.version to "0.04".

Usage:
    python tools/migrations/state_v_0_04.py path/to/game_state.json [more.json ...]

By default, writes changes in-place. Use --stdout to print to stdout instead.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Set


def _extract_modules(value: Any) -> List[str]:
    """Normalize a behaviors value to a list of module strings."""
    modules: List[str] = []

    def add(ref: Any) -> None:
        if not ref or not isinstance(ref, str):
            return
        module = ref.split(":", 1)[0].strip()
        if module and module not in modules:
            modules.append(module)

    if isinstance(value, dict):
        for v in value.values():
            if isinstance(v, list):
                for item in v:
                    add(item)
            else:
                add(v)
    elif isinstance(value, list):
        for item in value:
            add(item)
    else:
        add(value)

    return modules


def _normalize_behaviors_in_node(node: Any, keys_seen: Set[str]) -> None:
    """Recursively normalize any 'behaviors' keys within a JSON-like structure."""
    if isinstance(node, dict):
        for key, value in list(node.items()):
            if key == "behaviors":
                keys_seen.add(key)
                node[key] = _extract_modules(value)
            else:
                _normalize_behaviors_in_node(value, keys_seen)
    elif isinstance(node, list):
        for item in node:
            _normalize_behaviors_in_node(item, keys_seen)


def normalize_file(path: Path, stdout: bool = False) -> bool:
    """Normalize behaviors in a JSON file. Returns True if changes were made."""
    original_text = path.read_text(encoding="utf-8")
    data = json.loads(original_text)
    keys_seen: Set[str] = set()

    _normalize_behaviors_in_node(data, keys_seen)

    # Bump version to 0.04
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        data["metadata"] = metadata
    if metadata.get("version") != "0.04":
        metadata["version"] = "0.04"

    new_text = json.dumps(data, indent=2, ensure_ascii=False)
    changed = new_text != original_text

    if stdout:
        print(new_text)
    elif changed:
        path.write_text(new_text + "\n", encoding="utf-8")

    return changed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize game_state behaviors to list-only module references."
    )
    parser.add_argument("files", nargs="+", type=Path, help="Paths to JSON files to normalize.")
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print normalized JSON to stdout instead of writing in-place.",
    )
    args = parser.parse_args()

    changed_files = 0
    for path in args.files:
        if not path.exists():
            print(f"Skipping missing file: {path}")
            continue
        try:
            if normalize_file(path, stdout=args.stdout):
                changed_files += 1
                if not args.stdout:
                    print(f"Normalized behaviors in {path}")
        except json.JSONDecodeError as e:
            print(f"Failed to parse {path}: {e}")

    if not args.stdout:
        print(f"Done. Files changed: {changed_files}")


if __name__ == "__main__":
    main()
