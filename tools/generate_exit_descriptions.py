#!/usr/bin/env python3
"""Generate exit descriptions from destination location data.

For each exit in a game's JSON file, this tool generates a description
by extracting the destination location's name, description, and traits,
then composing them into a natural-sounding phrase.

The generated description uses:
- First sentence from destination location's description
- 1-2 key traits from destination's llm_context.traits

Example output: "A treacherous mountain pass. Windswept, narrow path."

Usage:
    python tools/generate_exit_descriptions.py examples/big_game/game_state.json
    python tools/generate_exit_descriptions.py examples/big_game/game_state.json --dry-run
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def get_first_sentence(text: str) -> str:
    """Extract the first sentence from a text.

    Args:
        text: The text to extract from

    Returns:
        First sentence, or empty string if text is empty
    """
    if not text:
        return ""

    # Find first sentence boundary (., !, ?)
    for delimiter in ['. ', '! ', '? ']:
        if delimiter in text:
            idx = text.index(delimiter)
            return text[:idx + 1].strip()

    # No sentence boundary found - return whole text
    return text.strip()


def generate_exit_description(
    destination_name: str,
    destination_description: str,
    destination_traits: list[str]
) -> str:
    """Generate an exit description from destination data.

    Args:
        destination_name: Name of destination location
        destination_description: Full description of destination
        destination_traits: List of trait strings from llm_context

    Returns:
        Generated description string
    """
    # Get first sentence from description
    first_sentence = get_first_sentence(destination_description)

    # Select up to 2 traits if available
    selected_traits = destination_traits[:2] if destination_traits else []

    # Build description - use traits if available, otherwise first sentence
    if selected_traits:
        # Prefer traits for conciseness
        traits_text = ", ".join(selected_traits)
        return f"{traits_text.capitalize()}."
    elif first_sentence:
        # Fallback to description if no traits
        return first_sentence
    else:
        # Nothing available - use generic description
        return f"A passage leading to {destination_name}."


def find_destination_location(
    exit_obj: Dict[str, Any],
    exits_by_id: Dict[str, Dict[str, Any]]
) -> Optional[str]:
    """Find the destination location ID for an exit.

    Args:
        exit_obj: Exit entity dict
        exits_by_id: Map of exit_id -> exit_obj

    Returns:
        Destination location ID, or None if not found
    """
    connections = exit_obj.get("connections", [])
    if not connections:
        return None

    # Get first connected exit
    connected_exit_id = connections[0]
    connected_exit = exits_by_id.get(connected_exit_id)
    if not connected_exit:
        return None

    # Return its location
    return connected_exit.get("location")


def process_game_file(filepath: Path, dry_run: bool = False) -> int:
    """Process a game JSON file to generate exit descriptions.

    Args:
        filepath: Path to game_state.json
        dry_run: If True, show changes without writing file

    Returns:
        Number of exits updated
    """
    # Load game data
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Build lookup maps
    exits_by_id = {exit_obj["id"]: exit_obj for exit_obj in data.get("exits", [])}
    locations_by_id = {loc["id"]: loc for loc in data.get("locations", [])}

    # Process each exit
    changes = 0
    for exit_obj in data.get("exits", []):
        exit_id = exit_obj["id"]
        direction = exit_obj.get("direction", "unknown")

        # Skip exits that already have descriptions
        if exit_obj.get("description"):
            continue

        # Find destination location
        dest_location_id = find_destination_location(exit_obj, exits_by_id)
        if not dest_location_id:
            print(f"  ⚠ {exit_id}: No destination found, skipping")
            continue

        dest_location = locations_by_id.get(dest_location_id)
        if not dest_location:
            print(f"  ⚠ {exit_id}: Destination location {dest_location_id} not found, skipping")
            continue

        # Extract destination data
        dest_name = dest_location.get("name", "")
        dest_description = dest_location.get("description", "")
        dest_traits = dest_location.get("llm_context", {}).get("traits", [])

        # Generate description
        generated_description = generate_exit_description(
            dest_name,
            dest_description,
            dest_traits
        )

        if dry_run:
            print(f"  {exit_id} ({direction}):")
            print(f"    Current: (empty)")
            print(f"    Generated: {generated_description}")
        else:
            exit_obj["description"] = generated_description
            changes += 1

    # Write back if not dry run
    if not dry_run and changes > 0:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            # Add trailing newline
            f.write('\n')

    return changes


def main():
    parser = argparse.ArgumentParser(
        description="Generate exit descriptions from destination location data"
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
            changes = process_game_file(filepath, args.dry_run)
            total_changes += changes

            if args.dry_run:
                print(f"\n✓ Would update {changes} exits in {filepath.name}")
            else:
                print(f"\n✓ Updated {changes} exits in {filepath.name}")
        except Exception as e:
            print(f"✗ {filepath.name}: Error - {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    if args.dry_run:
        print(f"Total exits that would be updated: {total_changes}")
    else:
        print(f"Total exits updated: {total_changes}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
