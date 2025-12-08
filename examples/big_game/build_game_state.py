#!/usr/bin/env python3
"""Build script to merge separate JSON data files into a complete game_state.json.

This script reads the separate location, actor, and item JSON files and merges
them into the main game_state.json to create a playable game.

Usage:
    python build_game_state.py

Output:
    Creates/updates data/game_state.json with merged data
"""

import json
from pathlib import Path


def load_json(filepath: Path) -> dict:
    """Load a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def save_json(filepath: Path, data: dict) -> None:
    """Save data to a JSON file with pretty formatting."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved: {filepath}")


def normalize_exit(direction: str, exit_data) -> dict:
    """Normalize exit data to dict format.

    Exits can be specified as:
    - Simple string: "loc_destination" -> {"type": "open", "to": "loc_destination"}
    - Full dict: {"type": "open", "to": "loc_destination", ...}
    """
    if isinstance(exit_data, str):
        # Simple string format - just the destination
        return {
            "type": "open",
            "to": exit_data,
            "name": direction,
            "description": f"Exit leading {direction}."
        }
    # Already a dict
    return exit_data


def normalize_location_exits(location: dict) -> dict:
    """Normalize all exits in a location to dict format."""
    if 'exits' in location:
        normalized_exits = {}
        for direction, exit_data in location['exits'].items():
            normalized_exits[direction] = normalize_exit(direction, exit_data)
        location['exits'] = normalized_exits
    return location


def merge_locations(data_dir: Path) -> list:
    """Merge all location files into a single list."""
    locations = []
    parts = []
    locations_dir = data_dir / 'locations'

    for filepath in sorted(locations_dir.glob('*.json')):
        print(f"  Loading locations from: {filepath.name}")
        file_data = load_json(filepath)

        # Add locations (normalizing exits)
        if 'locations' in file_data:
            for loc in file_data['locations']:
                locations.append(normalize_location_exits(loc))

        # Add parts (some files have location parts)
        if 'parts' in file_data:
            parts.extend(file_data['parts'])

    print(f"  Total locations: {len(locations)}")
    print(f"  Total parts: {len(parts)}")

    # Return locations with parts appended (they're stored together in our schema)
    return locations, parts


def merge_actors(data_dir: Path) -> dict:
    """Merge all actor files into a single dict keyed by actor ID."""
    actors = {}
    actors_dir = data_dir / 'actors'

    for filepath in sorted(actors_dir.glob('*.json')):
        print(f"  Loading actors from: {filepath.name}")
        file_data = load_json(filepath)

        if 'actors' in file_data:
            actors_data = file_data['actors']

            # Handle both list format and dict format
            if isinstance(actors_data, list):
                # List of actor objects
                for actor in actors_data:
                    actor_id = actor['id']
                    if actor_id in actors:
                        print(f"    WARNING: Duplicate actor ID: {actor_id}")
                    actors[actor_id] = actor
            elif isinstance(actors_data, dict):
                # Dict keyed by actor ID
                for actor_id, actor in actors_data.items():
                    if actor_id in actors:
                        print(f"    WARNING: Duplicate actor ID: {actor_id}")
                    # Ensure actor has id field
                    if 'id' not in actor:
                        actor['id'] = actor_id
                    actors[actor_id] = actor

    print(f"  Total actors: {len(actors)}")
    return actors


def merge_items(data_dir: Path) -> list:
    """Merge all item files into a single list."""
    items = []
    items_dir = data_dir / 'items'

    for filepath in sorted(items_dir.glob('*.json')):
        print(f"  Loading items from: {filepath.name}")
        file_data = load_json(filepath)

        if 'items' in file_data:
            items.extend(file_data['items'])

    print(f"  Total items: {len(items)}")
    return items


def build_game_state():
    """Build the complete game_state.json from component files."""
    # Determine paths
    script_dir = Path(__file__).parent
    data_dir = script_dir / 'data'
    game_state_path = data_dir / 'game_state.json'

    print("Building game_state.json...")
    print()

    # Load the base game_state (contains metadata, player, extra, behaviors)
    print("Loading base game_state.json...")
    game_state = load_json(game_state_path)

    # Remove the note about data files
    if '_note_data_files' in game_state:
        del game_state['_note_data_files']

    # Merge locations
    print("\nMerging locations...")
    locations, parts = merge_locations(data_dir)
    game_state['locations'] = locations
    if parts:
        game_state['parts'] = parts

    # Merge actors
    print("\nMerging actors...")
    actors = merge_actors(data_dir)

    # Move player from root to actors dict (new format)
    if 'player' in game_state:
        player_data = game_state.pop('player')
        if 'id' not in player_data:
            player_data['id'] = 'player'
        actors['player'] = player_data
        print("  Moved player into actors dict")

    game_state['actors'] = actors

    # Merge items
    print("\nMerging items...")
    items = merge_items(data_dir)
    game_state['items'] = items

    # Save the complete game_state
    print("\nSaving merged game_state.json...")
    save_json(game_state_path, game_state)

    # Print summary
    print("\n" + "=" * 50)
    print("Build complete!")
    print(f"  Locations: {len(locations)}")
    print(f"  Parts: {len(parts)}")
    print(f"  Actors: {len(actors)}")
    print(f"  Items: {len(items)}")
    print("=" * 50)


if __name__ == '__main__':
    build_game_state()
