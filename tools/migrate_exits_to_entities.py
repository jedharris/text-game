#!/usr/bin/env python3
"""Migration tool to convert ExitDescriptor-based JSON to Exit entities.

This tool transforms game_state.json files from the old format (exits embedded
in Location.exits dict) to the new format (Exit entities in GameState.exits list).

Usage:
    python tools/migrate_exits_to_entities.py <input.json> [output.json]
    python tools/migrate_exits_to_entities.py --validate <file.json>
    python tools/migrate_exits_to_entities.py --dry-run <input.json>
"""

import argparse
import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional


def generate_exit_id(location_id: str, direction: Optional[str], name: Optional[str]) -> str:
    """Generate deterministic exit ID.

    Args:
        location_id: ID of location where exit is accessed
        direction: Optional direction (north, south, etc.)
        name: Optional exit name

    Returns:
        Unique exit ID
    """
    if direction:
        return f"exit_{location_id}_{direction}"

    if name:
        # Convert name to slug (lowercase, replace spaces with underscores)
        slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
        return f"exit_{location_id}_{slug}"

    # Fallback for unnamed, directionless exit
    return f"exit_{location_id}_unnamed"


def migrate_exit_descriptor(
    descriptor: Dict[str, Any],
    location_id: str,
    direction: Optional[str],
    exit_id: str,
    target_exit_id: Optional[str] = None
) -> Dict[str, Any]:
    """Migrate a single ExitDescriptor to Exit entity format.

    Args:
        descriptor: Original ExitDescriptor dict
        location_id: Location where this exit is accessed
        direction: Direction key (if directional)
        exit_id: Generated exit ID
        target_exit_id: ID of paired exit (for connections)

    Returns:
        Exit entity dict
    """
    # Extract fields with defaults
    name = descriptor.get("name", "exit")
    description = descriptor.get("description", "")
    behaviors = descriptor.get("behaviors", [])
    properties = descriptor.get("properties", {})

    # Extract direct attributes (not in properties)
    door_id = descriptor.get("door_id")
    passage = descriptor.get("passage")
    door_at = descriptor.get("door_at")

    # Build connections list
    connections = []
    if target_exit_id:
        connections.append(target_exit_id)

    # Get traits - merge llm_context if present
    traits = descriptor.get("traits", {})
    if "llm_context" in descriptor:
        traits["llm_context"] = descriptor["llm_context"]

    result = {
        "id": exit_id,
        "name": name,
        "location": location_id,
        "connections": connections,
        "direction": direction,
        "description": description,
        "adjectives": descriptor.get("adjectives", []),
        "synonyms": descriptor.get("synonyms", []),
        "properties": properties,
        "behaviors": behaviors,
        "traits": traits
    }

    # Add optional direct attributes if present
    if door_id is not None:
        result["door_id"] = door_id
    if passage is not None:
        result["passage"] = passage
    if door_at is not None:
        result["door_at"] = door_at

    return result


def build_connection_map(data: Dict[str, Any]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Build map of all exit connections for pairing.

    Args:
        data: Game state JSON data

    Returns:
        Map of (location_id, direction) -> exit info
    """
    connection_map: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for location in data.get("locations", []):
        loc_id = location["id"]
        exits = location.get("exits", {})

        for direction, descriptor in exits.items():
            target_loc = descriptor.get("to")
            if target_loc:
                connection_map[(loc_id, direction)] = {
                    "descriptor": descriptor,
                    "target_location": target_loc,
                    "location_id": loc_id,
                    "direction": direction
                }

    return connection_map


def find_reverse_direction(direction: str) -> Optional[str]:
    """Find reverse direction for symmetric connections.

    Args:
        direction: Direction string

    Returns:
        Reverse direction or None
    """
    reverse_map = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east",
        "northeast": "southwest",
        "northwest": "southeast",
        "southeast": "northwest",
        "southwest": "northeast",
        "up": "down",
        "down": "up",
        "in": "out",
        "out": "in"
    }
    return reverse_map.get(direction)


def migrate_exits(data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate all exits from ExitDescriptor format to Exit entities.

    Args:
        data: Original game state JSON

    Returns:
        Migrated game state JSON with exits list
    """
    # Make a deep copy to avoid mutating input
    migrated = deepcopy(data)

    # Pre-migration validation
    validate_pre_migration(data)

    # Build connection map
    connection_map = build_connection_map(data)

    # Track created exits to avoid duplicates
    created_exits: Dict[Tuple[str, str], str] = {}  # (loc_id, direction) -> exit_id
    exits: List[Dict[str, Any]] = []

    # Process each location's exits
    for location in data.get("locations", []):
        loc_id = location["id"]
        exit_dict = location.get("exits", {})

        for direction, descriptor in exit_dict.items():
            # Skip if already created (from symmetric pair)
            if (loc_id, direction) in created_exits:
                continue

            # Generate exit ID
            exit_id = generate_exit_id(loc_id, direction, descriptor.get("name"))

            # Find paired exit (if exists)
            target_loc = descriptor.get("to")
            target_exit_id = None

            if target_loc:
                reverse_dir = find_reverse_direction(direction)
                if reverse_dir and (target_loc, reverse_dir) in connection_map:
                    # Symmetric connection exists
                    target_exit_id = generate_exit_id(
                        target_loc, reverse_dir,
                        connection_map[(target_loc, reverse_dir)]["descriptor"].get("name")
                    )
                    created_exits[(target_loc, reverse_dir)] = target_exit_id

            # Create exit entity
            exit_entity = migrate_exit_descriptor(
                descriptor, loc_id, direction, exit_id, target_exit_id
            )
            exits.append(exit_entity)
            created_exits[(loc_id, direction)] = exit_id

    # Now create paired exits that weren't created yet
    for (loc_id, direction), target_exit_id in list(created_exits.items()):
        if (loc_id, direction) not in [
            (e["location"], e.get("direction")) for e in exits
        ]:
            # This is the reverse side - create it
            descriptor = connection_map[(loc_id, direction)]["descriptor"]
            exit_id = target_exit_id
            source_exit_id = created_exits.get(
                (descriptor.get("to"), find_reverse_direction(direction))
            )

            exit_entity = migrate_exit_descriptor(
                descriptor, loc_id, direction, exit_id, source_exit_id
            )
            exits.append(exit_entity)

    # Add exits list to migrated data
    migrated["exits"] = exits

    # Post-migration validation
    validate_post_migration(migrated)

    return migrated


def validate_pre_migration(data: Dict[str, Any]) -> None:
    """Validate game state before migration.

    Args:
        data: Game state JSON data

    Raises:
        ValueError: If validation fails
    """
    # Build location ID set
    location_ids = {loc["id"] for loc in data.get("locations", [])}

    # Build item ID set
    item_ids = {item["id"] for item in data.get("items", [])}

    # Validate all exit references
    for location in data.get("locations", []):
        loc_id = location["id"]
        exits = location.get("exits", {})

        for direction, descriptor in exits.items():
            # Check target location exists
            target = descriptor.get("to")
            if target and target not in location_ids:
                raise ValueError(
                    f"Exit {loc_id}:{direction} references location {target} which does not exist"
                )

            # Check door ID exists (if door exit)
            if descriptor.get("type") == "door":
                door_id = descriptor.get("door_id")
                if door_id and door_id not in item_ids:
                    raise ValueError(
                        f"Exit {loc_id}:{direction} references door {door_id} which does not exist"
                    )


def validate_post_migration(data: Dict[str, Any]) -> None:
    """Validate migrated game state.

    Args:
        data: Migrated game state JSON

    Raises:
        ValueError: If validation fails
    """
    # Build exit ID set
    exit_ids = {exit_entity["id"] for exit_entity in data.get("exits", [])}

    # Validate all connections
    for exit_entity in data.get("exits", []):
        exit_id = exit_entity["id"]
        connections = exit_entity.get("connections", [])

        for target_id in connections:
            if target_id not in exit_ids:
                raise ValueError(
                    f"Exit {exit_id} references exit {target_id} which does not exist"
                )


def main():
    """Main entry point for migration tool."""
    parser = argparse.ArgumentParser(
        description="Migrate exits from ExitDescriptor to Exit entities"
    )
    parser.add_argument("input", help="Input game_state.json file")
    parser.add_argument("output", nargs="?", help="Output file (default: overwrite input)")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--validate", action="store_true", help="Only validate, don't migrate")
    parser.add_argument("--backup", action="store_true", help="Create .backup file")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Load input
    with open(input_path, 'r') as f:
        data = json.load(f)

    try:
        # Validate
        validate_pre_migration(data)
        if args.verbose:
            print(f"✓ Pre-migration validation passed")

        if args.validate:
            print(f"✓ {input_path} is valid for migration")
            return

        # Migrate
        migrated = migrate_exits(data)
        if args.verbose:
            exit_count = len(migrated.get("exits", []))
            print(f"✓ Migrated {exit_count} exits")

        # Output
        if args.dry_run:
            print(json.dumps(migrated, indent=2))
            return

        output_path = Path(args.output) if args.output else input_path

        # Create backup if requested
        if args.backup and output_path.exists():
            backup_path = output_path.with_suffix(output_path.suffix + ".backup")
            backup_path.write_text(output_path.read_text())
            if args.verbose:
                print(f"✓ Created backup: {backup_path}")

        # Write output
        with open(output_path, 'w') as f:
            json.dump(migrated, f, indent=2)

        if args.verbose:
            print(f"✓ Wrote migrated data to: {output_path}")

    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Migration error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
