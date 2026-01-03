#!/usr/bin/env python3
"""Apply Exit migration transformers to test files."""

import argparse
import sys
from pathlib import Path
import libcst as cst
from libcst_transformers import (
    ReplaceExitDescriptorImport,
    ClearLocationExits,
    AddIndexBuildingCalls
)

def apply_transformers(file_path: Path, dry_run: bool = False) -> bool:
    """
    Apply Exit migration transformers to a file.

    Returns True if changes were made, False otherwise.
    """
    # Read file
    content = file_path.read_text()

    # Parse
    tree = cst.parse_module(content)

    # Apply transformers
    total_changes = 0

    transformer1 = ReplaceExitDescriptorImport()
    tree = tree.visit(transformer1)
    total_changes += transformer1.changes

    transformer2 = ClearLocationExits()
    tree = tree.visit(transformer2)
    total_changes += transformer2.changes

    transformer3 = AddIndexBuildingCalls()
    tree = tree.visit(transformer3)
    total_changes += transformer3.changes

    if total_changes == 0:
        print(f"✓ {file_path.name}: No changes needed")
        return False

    if dry_run:
        print(f"  {file_path.name}: Would make {total_changes} changes")
        print(f"    - Import changes: {transformer1.changes}")
        print(f"    - Location exits cleared: {transformer2.changes}")
        print(f"    - Index calls added: {transformer3.changes // 2}")
        return True

    # Write back
    file_path.write_text(tree.code)
    print(f"✓ {file_path.name}: Made {total_changes} changes")
    print(f"    - Import changes: {transformer1.changes}")
    print(f"    - Location exits cleared: {transformer2.changes}")
    print(f"    - Index calls added: {transformer3.changes // 2}")

    return True

def main():
    parser = argparse.ArgumentParser(
        description="Apply Exit migration transformers to test files"
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Test files to transform"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files"
    )

    args = parser.parse_args()

    changed_count = 0
    for file_path in args.files:
        if not file_path.exists():
            print(f"✗ {file_path}: File not found", file=sys.stderr)
            continue

        try:
            if apply_transformers(file_path, args.dry_run):
                changed_count += 1
        except Exception as e:
            print(f"✗ {file_path.name}: Error - {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

    print(f"\nTotal files {'that would be ' if args.dry_run else ''}changed: {changed_count}/{len(args.files)}")

if __name__ == "__main__":
    main()
