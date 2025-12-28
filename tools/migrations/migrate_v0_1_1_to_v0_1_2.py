"""
State v0.1.2 migration: Convert virtual entities to first-class entities.

What it does:
- Converts state.extra["active_commitments"] → state.commitments list
- Converts state.extra["scheduled_events"] → state.scheduled_events list
- Converts state.extra["gossip_queue"] → state.gossip list
- Converts state.extra["environmental_spreads"] → state.spreads list
- Generates name and description for each virtual entity
- Maps TypedDict fields to properties dict
- Adds appropriate behavior module to each entity
- Sets metadata.version to "0.1.2"

This migration supports Phase 2 of virtual entity standardization by converting
plain TypedDicts in state.extra into first-class entities with standard structure.

Usage:
    python tools/migrations/migrate_v0_1_1_to_v0_1_2.py path/to/game_state.json [more.json ...]

By default, writes changes in-place. Use --stdout to print to stdout instead.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def generate_commitment_name(commitment: Dict[str, Any]) -> str:
    """Generate human-readable name for a commitment."""
    config_id = commitment.get("config_id", "")
    # Extract meaningful part from config_id (e.g., "commit_sira_rescue" → "Sira rescue")
    if config_id.startswith("commit_"):
        name_part = config_id[7:].replace("_", " ").title()
        return f"{name_part} promise"
    return config_id or "Unknown commitment"


def generate_commitment_description(commitment: Dict[str, Any]) -> str:
    """Generate prose description for a commitment."""
    state = commitment.get("state", "ACTIVE")
    deadline = commitment.get("deadline_turn")
    if deadline:
        return f"Commitment in {state} state, deadline at turn {deadline}"
    return f"Commitment in {state} state"


def migrate_commitments(data: Dict[str, Any]) -> int:
    """Convert active_commitments from extra to commitments list.

    Returns:
        Number of commitments migrated
    """
    extra = data.get("extra", {})
    active_commitments = extra.get("active_commitments", [])

    if not active_commitments:
        return 0

    commitments = []
    for commitment in active_commitments:
        if not isinstance(commitment, dict):
            continue

        # Create first-class Commitment entity
        entity = {
            "id": commitment.get("id", ""),
            "name": generate_commitment_name(commitment),
            "description": generate_commitment_description(commitment),
            "properties": {
                "state": commitment.get("state"),
                "made_at_turn": commitment.get("made_at_turn"),
                "deadline_turn": commitment.get("deadline_turn"),
                "hope_applied": commitment.get("hope_applied", False),
                "config_id": commitment.get("config_id", ""),
            },
            "behaviors": ["behaviors.shared.infrastructure.commitments"]
        }

        # Remove None values
        entity["properties"] = {k: v for k, v in entity["properties"].items() if v is not None}

        commitments.append(entity)

    data["commitments"] = commitments
    return len(commitments)


def generate_event_name(event: Dict[str, Any]) -> str:
    """Generate human-readable name for a scheduled event."""
    event_type = event.get("event_type", "")
    trigger_turn = event.get("trigger_turn", "?")

    # Make event type readable
    readable_type = event_type.replace("_", " ").title()
    return f"{readable_type} at turn {trigger_turn}"


def generate_event_description(event: Dict[str, Any]) -> str:
    """Generate prose description for a scheduled event."""
    event_type = event.get("event_type", "unknown")
    trigger_turn = event.get("trigger_turn", "?")
    repeating = event.get("repeating", False)

    desc = f"Event type '{event_type}' scheduled for turn {trigger_turn}"
    if repeating:
        interval = event.get("interval", "?")
        desc += f", repeating every {interval} turns"
    return desc


def migrate_scheduled_events(data: Dict[str, Any]) -> int:
    """Convert scheduled_events from extra to scheduled_events list.

    Returns:
        Number of events migrated
    """
    extra = data.get("extra", {})
    old_events = extra.get("scheduled_events", [])

    if not old_events:
        return 0

    events = []
    for event in old_events:
        if not isinstance(event, dict):
            continue

        # Create first-class ScheduledEvent entity
        entity = {
            "id": event.get("id", ""),
            "name": generate_event_name(event),
            "description": generate_event_description(event),
            "properties": {
                "trigger_turn": event.get("trigger_turn"),
                "event_type": event.get("event_type", ""),
                "data": event.get("data"),
                "repeating": event.get("repeating", False),
                "interval": event.get("interval"),
            },
            "behaviors": ["behaviors.shared.infrastructure.scheduled_events"]
        }

        # Remove None values
        entity["properties"] = {k: v for k, v in entity["properties"].items() if v is not None}

        events.append(entity)

    data["scheduled_events"] = events
    return len(events)


def generate_gossip_name(gossip: Dict[str, Any]) -> str:
    """Generate human-readable name for gossip."""
    content = gossip.get("content", "")
    # Take first few words of content
    words = content.split()[:5]
    if len(words) < len(content.split()):
        return " ".join(words) + "..."
    return " ".join(words) or "Unknown gossip"


def generate_gossip_description(gossip: Dict[str, Any]) -> str:
    """Generate prose description for gossip."""
    source = gossip.get("source_npc", "unknown")
    arrives_turn = gossip.get("arrives_turn", "?")

    # Determine gossip type from fields
    if "target_regions" in gossip:
        gossip_type = "broadcast"
    elif "network_id" in gossip:
        gossip_type = "network"
    else:
        gossip_type = "point-to-point"

    return f"{gossip_type.title()} gossip from {source}, arrives turn {arrives_turn}"


def migrate_gossip(data: Dict[str, Any]) -> int:
    """Convert gossip_queue from extra to gossip list.

    Returns:
        Number of gossip items migrated
    """
    extra = data.get("extra", {})
    gossip_queue = extra.get("gossip_queue", [])

    if not gossip_queue:
        return 0

    gossip_list = []
    for gossip in gossip_queue:
        if not isinstance(gossip, dict):
            continue

        # Determine gossip type and collect all fields
        properties = {
            "content": gossip.get("content", ""),
            "source_npc": gossip.get("source_npc"),
            "created_turn": gossip.get("created_turn"),
            "arrives_turn": gossip.get("arrives_turn"),
        }

        # Type-specific fields
        if "target_npcs" in gossip:
            properties["gossip_type"] = "POINT_TO_POINT"
            properties["target_npcs"] = gossip.get("target_npcs", [])
            if "confession_window_until" in gossip:
                properties["confession_window_until"] = gossip["confession_window_until"]
        elif "target_regions" in gossip:
            properties["gossip_type"] = "BROADCAST"
            properties["target_regions"] = gossip.get("target_regions", [])
        elif "network_id" in gossip:
            properties["gossip_type"] = "NETWORK"
            properties["network_id"] = gossip.get("network_id", "")

        # Create first-class Gossip entity
        entity = {
            "id": gossip.get("id", ""),
            "name": generate_gossip_name(gossip),
            "description": generate_gossip_description(gossip),
            "properties": {k: v for k, v in properties.items() if v is not None},
            "behaviors": ["behaviors.shared.infrastructure.gossip"]
        }

        gossip_list.append(entity)

    data["gossip"] = gossip_list
    return len(gossip_list)


def generate_spread_name(spread_id: str, spread: Dict[str, Any]) -> str:
    """Generate human-readable name for a spread."""
    # Convert spread_id to readable name (e.g., "frozen_reaches_cold" → "Frozen reaches cold spread")
    readable = spread_id.replace("_", " ").title()
    return f"{readable} spread"


def generate_spread_description(spread_id: str, spread: Dict[str, Any]) -> str:
    """Generate prose description for a spread."""
    active = spread.get("active", False)
    milestones = spread.get("milestones", [])
    status = "active" if active else "inactive"
    return f"Environmental spread '{spread_id}' ({status}, {len(milestones)} milestones)"


def migrate_spreads(data: Dict[str, Any]) -> int:
    """Convert environmental_spreads from extra dict to spreads list.

    Returns:
        Number of spreads migrated
    """
    extra = data.get("extra", {})
    env_spreads = extra.get("environmental_spreads", {})

    if not env_spreads or not isinstance(env_spreads, dict):
        return 0

    spreads = []
    for spread_id, spread in env_spreads.items():
        if not isinstance(spread, dict):
            continue

        # Create first-class Spread entity
        entity = {
            "id": spread_id,
            "name": generate_spread_name(spread_id, spread),
            "description": generate_spread_description(spread_id, spread),
            "properties": {
                "active": spread.get("active", False),
                "milestones": spread.get("milestones", []),
                "reached_milestones": spread.get("reached_milestones", []),
                "halt_flag": spread.get("halt_flag", ""),
                "current_milestone": spread.get("current_milestone"),
            },
            "behaviors": ["behaviors.shared.infrastructure.spreads"]
        }

        # Remove None values
        entity["properties"] = {k: v for k, v in entity["properties"].items() if v is not None}

        spreads.append(entity)

    data["spreads"] = spreads
    return len(spreads)


def migrate_file(path: Path, stdout: bool = False) -> bool:
    """Migrate a game_state.json file. Returns True if changes were made."""
    original_text = path.read_text(encoding="utf-8")
    data = json.loads(original_text)

    # Check current version
    metadata = data.get("metadata", {})
    current_version = metadata.get("version", "unknown")

    # Migrate each virtual entity type
    commitment_count = migrate_commitments(data)
    event_count = migrate_scheduled_events(data)
    gossip_count = migrate_gossip(data)
    spread_count = migrate_spreads(data)

    total_migrated = commitment_count + event_count + gossip_count + spread_count

    # Bump version to 0.1.2 (only if we migrated something or version is old)
    if not isinstance(metadata, dict):
        metadata = {}
        data["metadata"] = metadata

    version_changed = False
    if metadata.get("version") != "0.1.2":
        metadata["version"] = "0.1.2"
        version_changed = True

    # Serialize back to JSON
    new_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"

    if new_text == original_text:
        return False

    # No changes if nothing was migrated and version was already correct
    if total_migrated == 0 and not version_changed:
        return False

    if stdout:
        print(new_text, end="")
    else:
        path.write_text(new_text, encoding="utf-8")
        print(f"✓ {path}: migrated from {current_version} to 0.1.2")
        if total_migrated > 0:
            print(f"  Migrated: {commitment_count} commitments, {event_count} events, "
                  f"{gossip_count} gossip, {spread_count} spreads")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate game_state.json from v0.1.1 to v0.1.2 (virtual entity standardization)"
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
                print(f"- {path}: no changes needed (already v0.1.2 or no virtual entities)")
        except Exception as e:
            print(f"✗ {path}: {e}")
            import traceback
            traceback.print_exc()

    return 0 if any_changed else 1


if __name__ == "__main__":
    exit(main())
