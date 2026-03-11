#!/usr/bin/env python3
"""Convert walkthrough text commands to JSON format.

Transforms parser-based text commands like:
    go south
    take bandages
    ask echo about help
    use bandages on delvan

Into JSON commands like:
    {"type": "command", "action": {"verb": "go", "object": "south"}}
    {"type": "command", "action": {"verb": "take", "object": "bandages"}}
    {"type": "command", "action": {"verb": "ask", "object": "echo", "indirect_object": "help"}}
    {"type": "command", "action": {"verb": "use", "object": "bandages", "indirect_object": "delvan"}}

Usage:
    python tools/convert_walkthroughs_to_json.py walkthroughs/test_foo.txt
    python tools/convert_walkthroughs_to_json.py --all          # Convert all walkthrough files
    python tools/convert_walkthroughs_to_json.py --dry-run ...  # Preview without writing
"""

import json
import re
import sys
from pathlib import Path


# Verbs that take a preposition to introduce an indirect object
PREPOSITION_VERBS = {
    "ask": "about",
    "use": "on",
    "talk": "to",
    "give": "to",
    "pour": "on",
    "fill": "from",
    "attack": "with",
}

# Verbs that are bare (no object)
BARE_VERBS = {"look", "inventory"}

# Direction words that can be bare commands (synonyms for "go <dir>")
DIRECTIONS = {
    "north", "south", "east", "west",
    "northeast", "northwest", "southeast", "southwest",
    "up", "down", "back", "front",
}


def parse_text_command(text: str) -> dict:
    """Parse a text command into a JSON action dict.

    Args:
        text: Raw text command (e.g., "go south", "ask echo about help")

    Returns:
        JSON-serializable dict with type and action
    """
    text = text.strip()
    parts = text.split()

    if not parts:
        return {}

    verb = parts[0].lower()

    # Bare direction → go <direction>
    if verb in DIRECTIONS:
        return _make_command("go", object=verb)

    # Bare verbs (no arguments)
    if verb in BARE_VERBS or len(parts) == 1:
        return _make_command(verb)

    # Special case: "take off <item>" → unequip pattern
    if verb == "take" and len(parts) >= 3 and parts[1].lower() == "off":
        return _make_command("remove", object=" ".join(parts[2:]))

    # Special case: "take <item> from <source>"
    if verb == "take" and "from" in [p.lower() for p in parts]:
        from_idx = next(i for i, p in enumerate(parts) if p.lower() == "from")
        obj = " ".join(parts[1:from_idx])
        indirect = " ".join(parts[from_idx + 1:])
        return _make_command("take", object=obj, indirect_object=indirect)

    # Special case: "cover behind <thing>"
    if verb == "cover" and len(parts) >= 3 and parts[1].lower() == "behind":
        return _make_command("cover", object=" ".join(parts[2:]),
                             preposition="behind")

    # Special case: "ask <npc> to <action>" (teach pattern)
    if verb == "ask" and "to" in [p.lower() for p in parts[2:]]:
        to_idx = next(i for i, p in enumerate(parts) if i > 1 and p.lower() == "to")
        obj = " ".join(parts[1:to_idx])
        indirect = " ".join(parts[to_idx + 1:])
        return _make_command("ask", object=obj, indirect_object=indirect,
                             preposition="to")

    # Verbs with preposition-based indirect object
    if verb in PREPOSITION_VERBS:
        prep = PREPOSITION_VERBS[verb]
        # Find the preposition in remaining words
        prep_idx = None
        for i in range(1, len(parts)):
            if parts[i].lower() == prep:
                prep_idx = i
                break

        if prep_idx is not None:
            obj = " ".join(parts[1:prep_idx])
            indirect = " ".join(parts[prep_idx + 1:])
            # Strip quotes from indirect object (e.g., ask about "phrase")
            indirect = indirect.strip('"').strip("'")
            return _make_command(verb, object=obj, indirect_object=indirect)

    # Simple verb + object (go, take, examine, drop, wield, remove, read, etc.)
    obj = " ".join(parts[1:])
    return _make_command(verb, object=obj)


def _make_command(
    verb: str,
    object: str | None = None,
    indirect_object: str | None = None,
    preposition: str | None = None,
) -> dict:
    """Build a JSON command dict."""
    action: dict = {"verb": verb}
    if object:
        action["object"] = object
    if indirect_object:
        action["indirect_object"] = indirect_object
    if preposition:
        action["preposition"] = preposition
    return {"type": "command", "action": action}


def convert_line(line: str) -> str:
    """Convert a single walkthrough line, preserving comments and directives.

    Returns the converted line (or original if not a command).
    """
    stripped = line.rstrip()

    # Empty line
    if not stripped:
        return ""

    # Comment line
    if stripped.lstrip().startswith("#"):
        return stripped

    # Directive line (@expect, @assert, @set)
    if stripped.lstrip().startswith("@"):
        return stripped

    # Already JSON
    if stripped.lstrip().startswith("{"):
        return stripped

    # ASSERT (legacy uppercase)
    if stripped.lstrip().startswith("ASSERT"):
        return stripped

    # Command line - may have inline comment/annotation
    # Split off inline comment (but preserve EXPECTED_FAILURE annotations)
    command_part = stripped
    comment_part = ""

    # Find inline comment - look for " #" (space + hash)
    hash_match = re.search(r'\s+#\s', stripped)
    if hash_match:
        command_part = stripped[:hash_match.start()].rstrip()
        comment_part = stripped[hash_match.start():]

    # Parse and convert the command
    json_cmd = parse_text_command(command_part)
    if not json_cmd:
        return stripped  # Can't parse, leave as-is

    # Format as compact JSON + inline comment
    json_str = json.dumps(json_cmd, separators=(",", ":"))

    if comment_part:
        return f"{json_str}{comment_part}"
    return json_str


def convert_file(filepath: Path, dry_run: bool = False) -> tuple[int, int]:
    """Convert a walkthrough file from text commands to JSON.

    Args:
        filepath: Path to walkthrough file
        dry_run: If True, print changes but don't write

    Returns:
        Tuple of (total_commands, converted_commands)
    """
    lines = filepath.read_text().splitlines()
    converted_lines = []
    total_commands = 0
    converted_count = 0

    for line in lines:
        stripped = line.rstrip()

        # Check if this is a command line (not empty, not comment, not directive, not JSON)
        is_command = (
            stripped and
            not stripped.lstrip().startswith("#") and
            not stripped.lstrip().startswith("@") and
            not stripped.lstrip().startswith("{") and
            not stripped.lstrip().startswith("ASSERT")
        )

        if is_command:
            total_commands += 1
            new_line = convert_line(stripped)
            if new_line != stripped:
                converted_count += 1
                if dry_run:
                    print(f"  {stripped}")
                    print(f"  → {new_line}")
            converted_lines.append(new_line)
        else:
            converted_lines.append(stripped)

    if not dry_run:
        filepath.write_text("\n".join(converted_lines) + "\n")

    return total_commands, converted_count


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]

    if "--all" in args:
        walkthrough_dir = Path(__file__).parent.parent / "walkthroughs"
        files = sorted(walkthrough_dir.glob("test_*.txt"))
    else:
        files = [Path(a) for a in args]

    if not files:
        print("Usage: python tools/convert_walkthroughs_to_json.py [--dry-run] [--all | file1.txt ...]")
        sys.exit(1)

    total_files = 0
    total_commands = 0
    total_converted = 0

    for filepath in files:
        if not filepath.exists():
            print(f"File not found: {filepath}")
            continue

        if dry_run:
            print(f"\n=== {filepath.name} ===")

        commands, converted = convert_file(filepath, dry_run)
        total_files += 1
        total_commands += commands
        total_converted += converted

        if not dry_run:
            print(f"  {filepath.name}: {converted}/{commands} commands converted")

    print(f"\nTotal: {total_converted}/{total_commands} commands converted across {total_files} files")
    if dry_run:
        print("(dry run - no files modified)")


if __name__ == "__main__":
    main()
