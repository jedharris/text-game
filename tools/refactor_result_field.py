#!/usr/bin/env python3
"""
Refactoring tool for renaming fields on specific Result types.

This tool uses AST analysis to distinguish between different Result types
and only renames fields on the specified type. It handles:
- Direct attribute access: result.message → result.primary
- Constructor keyword args: HandlerResult(message="x") → HandlerResult(primary="x")

Usage:
    python tools/refactor_result_field.py --type HandlerResult --old message --new primary --path tests/
    python tools/refactor_result_field.py --type HandlerResult --old message --new primary --path tests/ --dry-run

The tool traces variable assignments to determine the type of a variable,
then only renames the field if it matches the target type.
"""

import ast
import argparse
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class FieldRename:
    """Configuration for a field rename operation."""
    target_type: str  # e.g., "HandlerResult"
    old_field: str    # e.g., "message"
    new_field: str    # e.g., "primary"


@dataclass
class Change:
    """A single change to make in a file."""
    line: int
    col_offset: int
    end_col_offset: int
    old_text: str
    new_text: str
    reason: str


class TypeTracker(ast.NodeVisitor):
    """
    Tracks variable types through assignments to determine result types.

    This handles patterns like:
        result = handle_take(...)  # result is HandlerResult
        result = accessor.update(...)  # result is UpdateResult
        result = on_take(...)  # result is EventResult
    """

    # Known functions that return specific types
    HANDLER_PATTERNS = [
        'handle_',  # handle_take, handle_drop, etc.
        'find_action_target',  # Returns HandlerResult on error
        'find_openable_target',
        'validate_actor_and_location',
    ]

    UPDATE_PATTERNS = [
        'accessor.update',
        '.update(',
    ]

    EVENT_PATTERNS = [
        'on_',  # on_take, on_drop, etc.
        'invoke_behavior',
    ]

    def __init__(self, source_lines: list[str]):
        self.source_lines = source_lines
        self.var_types: dict[str, str] = {}  # var_name -> type_name

    def get_call_name(self, node: ast.Call) -> str:
        """Extract the function name from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            # For method calls like accessor.update()
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
            return node.func.attr
        return ""

    def infer_type_from_call(self, call_name: str) -> Optional[str]:
        """Infer the return type based on the function/method name."""
        # Check for handler patterns
        for pattern in self.HANDLER_PATTERNS:
            if pattern in call_name:
                return "HandlerResult"

        # Check for update patterns
        for pattern in self.UPDATE_PATTERNS:
            if pattern in call_name:
                return "UpdateResult"

        # Check for event patterns
        for pattern in self.EVENT_PATTERNS:
            if call_name.startswith(pattern.rstrip('_')) or pattern in call_name:
                return "EventResult"

        return None

    def visit_Assign(self, node: ast.Assign):
        """Track variable assignments to infer types."""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id

            # Direct type construction: result = HandlerResult(...)
            if isinstance(node.value, ast.Call):
                call_name = self.get_call_name(node.value)
                if call_name in ("HandlerResult", "EventResult", "UpdateResult"):
                    self.var_types[var_name] = call_name
                else:
                    # Infer from function name
                    inferred = self.infer_type_from_call(call_name)
                    if inferred:
                        self.var_types[var_name] = inferred

        # Handle tuple unpacking: item, error = find_action_target(...)
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple):
            if isinstance(node.value, ast.Call):
                call_name = self.get_call_name(node.value)
                # These functions return (item, HandlerResult) or similar
                if 'find_action_target' in call_name or 'find_openable_target' in call_name:
                    for elt in node.targets[0].elts:
                        if isinstance(elt, ast.Name) and elt.id in ('error', 'err'):
                            self.var_types[elt.id] = "HandlerResult"
                # validate_actor_and_location returns (actor_id, actor, location, error)
                if 'validate_actor_and_location' in call_name:
                    for elt in node.targets[0].elts:
                        if isinstance(elt, ast.Name) and elt.id == 'error':
                            self.var_types[elt.id] = "HandlerResult"

        self.generic_visit(node)

    def get_type(self, var_name: str) -> Optional[str]:
        """Get the tracked type for a variable."""
        return self.var_types.get(var_name)


class FieldRenamer(ast.NodeVisitor):
    """
    Finds and renames fields on specific Result types.
    """

    def __init__(self, source: str, rename: FieldRename, type_tracker: TypeTracker):
        self.source = source
        self.source_lines = source.split('\n')
        self.rename = rename
        self.type_tracker = type_tracker
        self.changes: list[Change] = []

    def visit_Call(self, node: ast.Call):
        """Handle constructor calls: HandlerResult(message="x")"""
        call_name = ""
        if isinstance(node.func, ast.Name):
            call_name = node.func.id

        if call_name == self.rename.target_type:
            # Check keyword arguments
            for kw in node.keywords:
                if kw.arg == self.rename.old_field:
                    # Found a match - rename the keyword
                    # The keyword arg name starts at kw.col_offset in Python 3.9+
                    # For earlier versions, we need to find it in the source
                    line = self.source_lines[kw.lineno - 1]

                    # Find the keyword in the line
                    # Look for "old_field=" pattern
                    pattern = f"{self.rename.old_field}="
                    start = line.find(pattern)
                    if start != -1:
                        self.changes.append(Change(
                            line=kw.lineno,
                            col_offset=start,
                            end_col_offset=start + len(self.rename.old_field),
                            old_text=self.rename.old_field,
                            new_text=self.rename.new_field,
                            reason=f"Constructor keyword in {call_name}()"
                        ))

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Handle attribute access: result.message"""
        if node.attr == self.rename.old_field:
            # Check if the object is a variable we've tracked
            if isinstance(node.value, ast.Name):
                var_name = node.value.id
                var_type = self.type_tracker.get_type(var_name)

                if var_type == self.rename.target_type:
                    # This is accessing .message on a HandlerResult
                    line = self.source_lines[node.lineno - 1]

                    # Find the attribute access pattern: var.old_field
                    pattern = f".{self.rename.old_field}"
                    # Start searching from where the variable name ends
                    start = line.find(pattern, node.col_offset)
                    if start != -1:
                        self.changes.append(Change(
                            line=node.lineno,
                            col_offset=start + 1,  # +1 to skip the dot
                            end_col_offset=start + 1 + len(self.rename.old_field),
                            old_text=self.rename.old_field,
                            new_text=self.rename.new_field,
                            reason=f"Attribute access on {var_type}"
                        ))

        self.generic_visit(node)


def analyze_file(filepath: Path, rename: FieldRename) -> list[Change]:
    """Analyze a single file and return the changes needed."""
    try:
        source = filepath.read_text()
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"  Skipping {filepath}: syntax error: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  Skipping {filepath}: {e}", file=sys.stderr)
        return []

    source_lines = source.split('\n')

    # First pass: track variable types
    tracker = TypeTracker(source_lines)
    tracker.visit(tree)

    # Second pass: find fields to rename
    renamer = FieldRenamer(source, rename, tracker)
    renamer.visit(tree)

    return renamer.changes


def apply_changes(filepath: Path, changes: list[Change]) -> str:
    """Apply changes to a file and return the new content."""
    source = filepath.read_text()
    lines = source.split('\n')

    # Sort changes by line (descending) then column (descending)
    # This way we can apply changes from end to beginning without offset issues
    sorted_changes = sorted(changes, key=lambda c: (c.line, c.col_offset), reverse=True)

    for change in sorted_changes:
        line_idx = change.line - 1
        line = lines[line_idx]
        # Apply the change
        new_line = line[:change.col_offset] + change.new_text + line[change.end_col_offset:]
        lines[line_idx] = new_line

    return '\n'.join(lines)


def process_path(path: Path, rename: FieldRename, dry_run: bool = False) -> tuple[int, int]:
    """
    Process a file or directory.

    Returns (files_changed, total_changes)
    """
    files_changed = 0
    total_changes = 0

    if path.is_file():
        files = [path]
    else:
        files = list(path.rglob("*.py"))

    for filepath in files:
        # Skip __pycache__ and other non-source directories
        if '__pycache__' in str(filepath) or '.pyc' in str(filepath):
            continue

        changes = analyze_file(filepath, rename)

        if changes:
            files_changed += 1
            total_changes += len(changes)

            rel_path = filepath.relative_to(Path.cwd()) if filepath.is_relative_to(Path.cwd()) else filepath
            print(f"\n{rel_path}: {len(changes)} change(s)")

            for change in changes:
                print(f"  Line {change.line}: {change.old_text} → {change.new_text} ({change.reason})")

            if not dry_run:
                new_content = apply_changes(filepath, changes)
                filepath.write_text(new_content)

    return files_changed, total_changes


def main():
    parser = argparse.ArgumentParser(
        description="Rename fields on specific Result types using AST analysis"
    )
    parser.add_argument(
        "--type", "-t",
        required=True,
        help="Target type name (e.g., HandlerResult)"
    )
    parser.add_argument(
        "--old", "-o",
        required=True,
        help="Old field name (e.g., message)"
    )
    parser.add_argument(
        "--new", "-n",
        required=True,
        help="New field name (e.g., primary)"
    )
    parser.add_argument(
        "--path", "-p",
        required=True,
        help="File or directory to process"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Show changes without applying them"
    )

    args = parser.parse_args()

    rename = FieldRename(
        target_type=args.type,
        old_field=args.old,
        new_field=args.new
    )

    path = Path(args.path)
    if not path.exists():
        print(f"Error: {path} does not exist", file=sys.stderr)
        sys.exit(1)

    mode = "DRY RUN" if args.dry_run else "APPLYING"
    print(f"{mode}: Renaming {rename.target_type}.{rename.old_field} → {rename.target_type}.{rename.new_field}")
    print(f"Scanning: {path}")

    files_changed, total_changes = process_path(path, rename, args.dry_run)

    print(f"\nSummary: {total_changes} change(s) in {files_changed} file(s)")

    if args.dry_run and total_changes > 0:
        print("\nRun without --dry-run to apply changes")


if __name__ == "__main__":
    main()
