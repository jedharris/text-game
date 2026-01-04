#!/usr/bin/env python3
"""
Extract location connectivity from game_state.json and find disconnected locations.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, deque

def load_game_state(path: Path) -> dict:
    """Load game state JSON."""
    with open(path) as f:
        return json.load(f)

def extract_locations(game_state: dict) -> dict:
    """Extract all locations."""
    locations = {}
    for loc in game_state.get("locations", []):
        loc_id = loc["id"]
        region = loc.get("properties", {}).get("region", "unknown")
        name = loc.get("name", loc_id)

        locations[loc_id] = {
            "name": name,
            "region": region,
        }

    return locations

def extract_exits(game_state: dict) -> dict[str, dict[str, str]]:
    """Extract exit entities and build location->exit mapping."""
    # Build mapping: location_id -> {direction: target_location_id}
    location_exits: dict[str, dict[str, str]] = defaultdict(dict)

    for exit_obj in game_state.get("exits", []):
        exit_id = exit_obj["id"]
        location = exit_obj.get("location")
        direction = exit_obj.get("direction")
        connections = exit_obj.get("connections", [])

        if not location or not direction or not connections:
            continue

        # Extract target location from connection exit ID
        # e.g., "exit_frozen_pass_south" -> "frozen_pass"
        target_exit_id = connections[0]
        target_location = "_".join(target_exit_id.split("_")[1:-1])

        location_exits[location][direction] = target_location

    return location_exits

def build_connectivity_graph(location_exits: dict) -> dict:
    """Build bidirectional connectivity graph from exits."""
    graph = defaultdict(set)

    for loc_id, exits in location_exits.items():
        for direction, target_id in exits.items():
            graph[loc_id].add(target_id)
            graph[target_id].add(loc_id)  # Bidirectional

    return graph

def find_reachable_locations(graph: dict, start: str) -> set:
    """BFS to find all reachable locations from start."""
    visited = set()
    queue = deque([start])

    while queue:
        current = queue.popleft()
        if current in visited:
            continue

        visited.add(current)

        for neighbor in graph.get(current, []):
            if neighbor not in visited:
                queue.append(neighbor)

    return visited

def print_location_inventory(locations: dict):
    """Print inventory of all locations grouped by region."""
    by_region = defaultdict(list)

    for loc_id, data in locations.items():
        by_region[data["region"]].append((loc_id, data["name"]))

    print("\n=== LOCATION INVENTORY ===\n")
    for region, locs in sorted(by_region.items()):
        print(f"{region.upper()} ({len(locs)} locations):")
        for loc_id, name in sorted(locs):
            print(f"  - {loc_id} ({name})")
        print()

def print_connectivity_map(locations: dict, location_exits: dict):
    """Print condensed navigation map."""
    by_region = defaultdict(list)

    for loc_id, data in locations.items():
        by_region[data["region"]].append(loc_id)

    print("\n=== CONNECTIVITY MAP ===\n")
    for region, loc_ids in sorted(by_region.items()):
        print(f"{region.upper()}:")
        for loc_id in sorted(loc_ids):
            exits = location_exits.get(loc_id, {})
            if exits:
                exit_str = ", ".join(f"{d}→{t}" for d, t in sorted(exits.items()))
                print(f"  {loc_id}: {exit_str}")
            else:
                print(f"  {loc_id}: NO EXITS")
        print()

def main():
    game_state_path = Path("examples/big_game/game_state.json")

    if not game_state_path.exists():
        print(f"Error: {game_state_path} not found")
        sys.exit(1)

    game_state = load_game_state(game_state_path)
    locations = extract_locations(game_state)
    location_exits = extract_exits(game_state)
    graph = build_connectivity_graph(location_exits)

    print(f"Total locations: {len(locations)}")
    print(f"Total exits defined: {sum(len(exits) for exits in location_exits.values())}")

    # Find starting location
    start_location = "nexus_chamber"
    if start_location not in locations:
        print(f"Error: Starting location '{start_location}' not found")
        sys.exit(1)

    # Find all reachable locations
    reachable = find_reachable_locations(graph, start_location)
    unreachable = set(locations.keys()) - reachable

    print(f"Reachable from {start_location}: {len(reachable)}")
    print(f"DISCONNECTED: {len(unreachable)}")

    if unreachable:
        print("\n=== DISCONNECTED LOCATIONS ===\n")
        for loc_id in sorted(unreachable):
            data = locations[loc_id]
            print(f"  - {loc_id} ({data['name']}) [region: {data['region']}]")
            exits = location_exits.get(loc_id, {})
            if exits:
                print(f"    Exits: {exits}")
            else:
                print(f"    NO EXITS DEFINED")

    # Print full inventory
    print_location_inventory(locations)

    # Print connectivity map
    print_connectivity_map(locations, location_exits)

if __name__ == "__main__":
    main()
