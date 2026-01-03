#!/usr/bin/env python3
"""
Find tests that likely need subprocess isolation.

Tests need isolation if they:
1. Import GameEngine from src.game_engine
2. Manipulate sys.path
3. Are not already using the subprocess wrapper pattern

This helps identify tests that will fail context-dependently BEFORE they fail.
"""

import ast
import sys
from pathlib import Path
from typing import Set, List, Tuple


class IsolationCandidateDetector(ast.NodeVisitor):
    """Detect patterns that indicate need for subprocess isolation."""

    def __init__(self):
        self.imports_game_engine = False
        self.manipulates_sys_path = False
        self.uses_subprocess = False
        self.is_impl_file = False

    def visit_ImportFrom(self, node):
        """Check for GameEngine import."""
        if node.module == 'src.game_engine':
            for alias in node.names:
                if alias.name == 'GameEngine':
                    self.imports_game_engine = True
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Check for sys.path manipulation."""
        if isinstance(node.value, ast.Name) and node.value.id == 'sys':
            if node.attr == 'path':
                self.manipulates_sys_path = True
        self.generic_visit(node)

    def visit_Call(self, node):
        """Check for subprocess.run usage."""
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'subprocess' and
                node.func.attr == 'run'):
                self.uses_subprocess = True
        self.generic_visit(node)


def analyze_test_file(file_path: Path) -> Tuple[bool, str]:
    """
    Analyze a test file to determine if it needs isolation.

    Returns:
        (needs_isolation, reason)
    """
    try:
        content = file_path.read_text()
        tree = ast.parse(content, filename=str(file_path))

        detector = IsolationCandidateDetector()
        detector.is_impl_file = file_path.name.startswith('_') and file_path.name.endswith('_impl.py')
        detector.visit(tree)

        # If it's an impl file, it's already isolated
        if detector.is_impl_file:
            return (False, "Already an impl file (has isolation)")

        # If it uses subprocess, it's already a wrapper
        if detector.uses_subprocess:
            return (False, "Already uses subprocess wrapper")

        # If it imports GameEngine AND manipulates sys.path, it needs isolation
        if detector.imports_game_engine and detector.manipulates_sys_path:
            return (True, "Imports GameEngine + manipulates sys.path")

        # GameEngine alone doesn't require isolation (unless loading game-specific behaviors)
        # Those are identified by sys.path manipulation

        return (False, "No isolation indicators")

    except Exception as e:
        return (False, f"Error analyzing: {e}")


def find_test_files(tests_dir: Path) -> List[Path]:
    """Find all test files (excluding impl files and infrastructure)."""
    test_files = []

    for test_file in tests_dir.glob("test_*.py"):
        # Skip impl files (they're already isolated)
        if test_file.name.startswith('_'):
            continue
        test_files.append(test_file)

    # Also check subdirectories
    for subdir in tests_dir.iterdir():
        if subdir.is_dir() and not subdir.name.startswith('_'):
            test_files.extend(subdir.glob("test_*.py"))

    return sorted(test_files)


def main():
    """Find and report tests that likely need isolation."""
    project_root = Path.cwd()
    tests_dir = project_root / "tests"

    if not tests_dir.exists():
        print(f"Error: {tests_dir} not found", file=sys.stderr)
        return 1

    test_files = find_test_files(tests_dir)

    needs_isolation = []
    already_isolated = []
    no_isolation_needed = []

    for test_file in test_files:
        rel_path = test_file.relative_to(project_root)
        needs_it, reason = analyze_test_file(test_file)

        if needs_it:
            needs_isolation.append((rel_path, reason))
        elif "Already" in reason:
            already_isolated.append((rel_path, reason))
        else:
            no_isolation_needed.append((rel_path, reason))

    # Report results
    print("=" * 80)
    print("TESTS THAT NEED SUBPROCESS ISOLATION")
    print("=" * 80)
    if needs_isolation:
        for path, reason in needs_isolation:
            print(f"\n{path}")
            print(f"  Reason: {reason}")
    else:
        print("\nNone found!")

    print("\n" + "=" * 80)
    print("TESTS ALREADY USING ISOLATION")
    print("=" * 80)
    for path, reason in already_isolated:
        print(f"{str(path):<60} [{reason}]")

    print(f"\n" + "=" * 80)
    print(f"SUMMARY")
    print("=" * 80)
    print(f"Tests needing isolation:     {len(needs_isolation)}")
    print(f"Tests already isolated:      {len(already_isolated)}")
    print(f"Tests not needing isolation: {len(no_isolation_needed)}")
    print(f"Total tests analyzed:        {len(test_files)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
