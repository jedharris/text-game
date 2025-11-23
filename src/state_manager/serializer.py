"""
JSON serializer for game state.

Converts GameState objects back to JSON.
"""

import json
from pathlib import Path
from typing import Union, Dict, Any, IO
from dataclasses import asdict

from .models import GameState
from .exceptions import ValidationError
from .validators import validate_game_state


def game_state_to_dict(state: GameState) -> Dict[str, Any]:
    """
    Convert GameState object to dictionary.

    Args:
        state: GameState to serialize

    Returns:
        Dictionary matching JSON schema
    """
    result = {}

    # Serialize metadata (only include non-empty fields)
    result['metadata'] = {
        'title': state.metadata.title,
        'author': state.metadata.author,
        'version': state.metadata.version,
        'start_location': state.metadata.start_location,
    }
    if state.metadata.description:
        result['metadata']['description'] = state.metadata.description

    # Serialize locations
    result['locations'] = []
    for loc in state.locations:
        loc_dict = {
            'id': loc.id,
            'name': loc.name,
            'description': loc.description,
            'exits': {},
            'tags': loc.tags,
            'items': loc.items,
            'npcs': loc.npcs,
        }

        # Serialize exits
        for direction, exit_desc in loc.exits.items():
            exit_dict = {
                'type': exit_desc.type,
            }
            if exit_desc.to:
                exit_dict['to'] = exit_desc.to
            if exit_desc.door_id:
                exit_dict['door_id'] = exit_desc.door_id
            if exit_desc.description:
                exit_dict['description'] = exit_desc.description
            if exit_desc.hidden:
                exit_dict['hidden'] = exit_desc.hidden
            if exit_desc.conditions:
                exit_dict['conditions'] = exit_desc.conditions
            if exit_desc.on_fail:
                exit_dict['on_fail'] = exit_desc.on_fail

            loc_dict['exits'][direction] = exit_dict

        result['locations'].append(loc_dict)

    # Serialize doors
    if state.doors:
        result['doors'] = []
        for door in state.doors:
            door_dict = {
                'id': door.id,
                'locations': list(door.locations),
                'description': door.description,
                'locked': door.locked,
                'open': door.open,
            }
            if door.one_way:
                door_dict['one_way'] = door.one_way
            if door.lock_id:
                door_dict['lock_id'] = door.lock_id

            result['doors'].append(door_dict)

    # Serialize items
    if state.items:
        result['items'] = []
        for item in state.items:
            item_dict = {
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'type': item.type,
                'portable': item.portable,
                'location': item.location,
            }

            if item.states:
                item_dict['states'] = item.states

            if item.container:
                item_dict['container'] = {
                    'is_container': item.container.is_container,
                    'is_surface': item.container.is_surface,
                    'open': item.container.open,
                    'locked': item.container.locked,
                    'capacity': item.container.capacity,
                }
                if item.container.lock_id:
                    item_dict['container']['lock_id'] = item.container.lock_id

            result['items'].append(item_dict)

    # Serialize locks
    if state.locks:
        result['locks'] = []
        for lock in state.locks:
            lock_dict = {
                'id': lock.id,
                'opens_with': lock.opens_with,
                'auto_unlock': lock.auto_unlock,
                'description': lock.description,
            }
            if lock.fail_message:
                lock_dict['fail_message'] = lock.fail_message
            result['locks'].append(lock_dict)

    # Serialize NPCs
    if state.npcs:
        result['npcs'] = []
        for npc in state.npcs:
            npc_dict = {
                'id': npc.id,
                'name': npc.name,
                'description': npc.description,
                'location': npc.location,
            }

            if npc.dialogue:
                npc_dict['dialogue'] = npc.dialogue
            if npc.states:
                npc_dict['states'] = npc.states
            if npc.inventory:
                npc_dict['inventory'] = npc.inventory

            result['npcs'].append(npc_dict)

    # Serialize player state
    if state.player:
        result['player_state'] = {
            'location': state.player.location,
            'inventory': state.player.inventory,
            'flags': state.player.flags,
            'stats': state.player.stats,
        }

    # Add extra fields for forward compatibility
    result.update(state.extra)

    return result


def save_game_state(state: GameState, destination: Union[str, Path, IO],
                    indent: int = 2, sort_keys: bool = False,
                    validate: bool = True) -> None:
    """
    Save GameState to file.

    Args:
        state: GameState to save
        destination: File path or file-like object
        indent: JSON indentation (default 2)
        sort_keys: Whether to sort keys (default False)
        validate: Whether to validate before saving (default True)

    Raises:
        ValidationError: If validation fails and validate=True
    """
    # Validate if requested
    if validate:
        validate_game_state(state)

    # Convert to dict
    data = game_state_to_dict(state)

    # Save to file
    if isinstance(destination, (str, Path)):
        with open(destination, 'w') as f:
            json.dump(data, f, indent=indent, sort_keys=sort_keys)
            f.write('\n')  # Add trailing newline
    else:
        # File-like object
        json.dump(data, destination, indent=indent, sort_keys=sort_keys)
        destination.write('\n')  # Add trailing newline
