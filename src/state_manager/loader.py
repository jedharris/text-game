"""
JSON loader for game state.

Reads JSON files and converts them to GameState objects.
"""

import json
from pathlib import Path
from typing import Union, Dict, Any, List, IO
from io import StringIO

from .models import (
    GameState, Metadata, Vocabulary, Location, ExitDescriptor,
    Door, Item, ContainerInfo, Lock, NPC, Script, ScriptTrigger,
    ScriptEffect, PlayerState
)
from .exceptions import SchemaError, FileLoadError
from .validators import validate_game_state


def load_game_state(source: Union[str, Path, IO, Dict]) -> GameState:
    """
    Load game state from file path, file-like object, or dict.

    Args:
        source: File path, file-like object, or already-parsed dict

    Returns:
        GameState object

    Raises:
        FileLoadError: If file cannot be read
        SchemaError: If JSON is invalid
        ValidationError: If validation fails
    """
    # If already a dict, parse directly
    if isinstance(source, dict):
        return parse_game_state(source)

    # Handle file path
    if isinstance(source, (str, Path)):
        try:
            with open(source, 'r') as f:
                raw_json = f.read()
        except FileNotFoundError as e:
            raise FileLoadError(f"File not found: {source}") from e
        except IOError as e:
            raise FileLoadError(f"Error reading file: {source}") from e

        try:
            raw = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise SchemaError(f"Invalid JSON: {e}") from e

        return parse_game_state(raw)

    # Handle file-like object
    try:
        raw_json = source.read()
        raw = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise SchemaError(f"Invalid JSON: {e}") from e
    except Exception as e:
        raise FileLoadError(f"Error reading source: {e}") from e

    return parse_game_state(raw)


def parse_game_state(raw: Dict[str, Any]) -> GameState:
    """
    Parse raw JSON dict into GameState object.

    Args:
        raw: Raw JSON dictionary

    Returns:
        GameState object

    Raises:
        SchemaError: If structure is invalid
        ValidationError: If validation fails
    """
    # Extract known sections (accept both 'player' and 'player_state')
    known_keys = {
        'metadata', 'vocabulary', 'locations', 'doors', 'items',
        'locks', 'npcs', 'scripts', 'player', 'player_state'
    }

    # Collect extra fields for forward compatibility
    extra = {k: v for k, v in raw.items() if k not in known_keys}

    # Parse metadata (required)
    if 'metadata' not in raw:
        raise SchemaError("Missing required section: metadata")

    metadata = parse_metadata(raw['metadata'])

    # Parse optional sections with defaults
    vocabulary = parse_vocabulary(raw.get('vocabulary', {}))
    locations = parse_locations(raw.get('locations', []))
    doors = parse_doors(raw.get('doors', []))
    items = parse_items(raw.get('items', []))
    locks = parse_locks(raw.get('locks', []))
    npcs = parse_npcs(raw.get('npcs', []))
    scripts = parse_scripts(raw.get('scripts', []))

    # Parse or initialize player state (accept both keys)
    player_data = raw.get('player') or raw.get('player_state')
    if player_data:
        player = parse_player_state(player_data)
    else:
        # Initialize from metadata
        player = PlayerState(
            location=metadata.start_location,
            inventory=[],
            flags={},
            stats={}
        )

    # Build game state
    game_state = GameState(
        metadata=metadata,
        vocabulary=vocabulary,
        locations=locations,
        doors=doors,
        items=items,
        locks=locks,
        npcs=npcs,
        scripts=scripts,
        player=player,
        extra=extra
    )

    # Validate
    validate_game_state(game_state)

    return game_state


def parse_metadata(raw: Dict[str, Any]) -> Metadata:
    """Parse metadata section."""
    if not isinstance(raw, dict):
        raise SchemaError("metadata must be an object")

    return Metadata(
        title=raw.get('title', ''),
        author=raw.get('author', ''),
        version=raw.get('version', '1.0'),
        description=raw.get('description', ''),
        start_location=raw.get('start_location', '')
    )


def parse_vocabulary(raw: Dict[str, Any]) -> Vocabulary:
    """Parse vocabulary section."""
    if not isinstance(raw, dict):
        return Vocabulary()

    return Vocabulary(
        aliases=raw.get('aliases', {}),
        verbs=raw.get('verbs', {}),
        nouns=raw.get('nouns', {}),
        adjectives=raw.get('adjectives', {})
    )


def parse_locations(raw: Any) -> List[Location]:
    """Parse locations array."""
    if not isinstance(raw, list):
        raise SchemaError("locations must be an array")

    locations = []
    for loc_data in raw:
        if not isinstance(loc_data, dict):
            raise SchemaError("Each location must be an object")

        # Validate ID
        if 'id' not in loc_data:
            raise SchemaError("Location missing required field: id")
        if not isinstance(loc_data['id'], str):
            raise SchemaError(f"Location ID must be a string, got {type(loc_data['id'])}")

        # Parse exits
        exits = {}
        for direction, exit_data in loc_data.get('exits', {}).items():
            if isinstance(exit_data, dict):
                exits[direction] = ExitDescriptor(
                    type=exit_data.get('type', 'open'),
                    to=exit_data.get('to'),
                    door_id=exit_data.get('door_id'),
                    description=exit_data.get('description'),
                    hidden=exit_data.get('hidden', False),
                    conditions=exit_data.get('conditions'),
                    on_fail=exit_data.get('on_fail')
                )

        location = Location(
            id=loc_data['id'],
            name=loc_data.get('name', ''),
            description=loc_data.get('description', ''),
            exits=exits,
            tags=loc_data.get('tags', []),
            items=loc_data.get('items', []),
            npcs=loc_data.get('npcs', []),
            llm_context=loc_data.get('llm_context'),
            behaviors=loc_data.get('behaviors', {})
        )
        locations.append(location)

    return locations


def parse_doors(raw: Any) -> List[Door]:
    """Parse doors array."""
    if not isinstance(raw, list):
        raise SchemaError("doors must be an array")

    doors = []
    for door_data in raw:
        if not isinstance(door_data, dict):
            raise SchemaError("Each door must be an object")

        # Validate ID
        if 'id' not in door_data:
            raise SchemaError("Door missing required field: id")
        if not isinstance(door_data['id'], str):
            raise SchemaError(f"Door ID must be a string, got {type(door_data['id'])}")

        # Convert locations to tuple
        locations = door_data.get('locations', [])
        if isinstance(locations, list):
            locations = tuple(locations)

        door = Door(
            id=door_data['id'],
            locations=locations,
            description=door_data.get('description', ''),
            locked=door_data.get('locked', False),
            lock_id=door_data.get('lock_id'),
            open=door_data.get('open', True),
            one_way=door_data.get('one_way', False),
            llm_context=door_data.get('llm_context'),
            behaviors=door_data.get('behaviors', {})
        )
        doors.append(door)

    return doors


def parse_items(raw: Any) -> List[Item]:
    """Parse items array."""
    if not isinstance(raw, list):
        raise SchemaError("items must be an array")

    items = []
    for item_data in raw:
        if not isinstance(item_data, dict):
            raise SchemaError("Each item must be an object")

        # Validate ID
        if 'id' not in item_data:
            raise SchemaError("Item missing required field: id")
        if not isinstance(item_data['id'], str):
            raise SchemaError(f"Item ID must be a string, got {type(item_data['id'])}")

        # Parse container info
        container = None
        if 'container' in item_data and item_data['container']:
            container_data = item_data['container']
            container = ContainerInfo(
                is_container=container_data.get('is_container', True),
                is_surface=container_data.get('is_surface', False),
                open=container_data.get('open', False),
                locked=container_data.get('locked', False),
                lock_id=container_data.get('lock_id'),
                contents=container_data.get('contents', []),
                capacity=container_data.get('capacity', 0)
            )

        # Get states and merge in llm_context if present
        states = item_data.get('states', {})
        if 'llm_context' in item_data:
            states['llm_context'] = item_data['llm_context']

        item = Item(
            id=item_data['id'],
            name=item_data.get('name', ''),
            description=item_data.get('description', ''),
            type=item_data.get('type', 'scenery'),
            portable=item_data.get('portable', False),
            location=item_data.get('location', ''),
            states=states,
            container=container,
            provides_light=item_data.get('provides_light', False),
            behaviors=item_data.get('behaviors', {}),
            pushable=item_data.get('pushable', False)
        )
        items.append(item)

    return items


def parse_locks(raw: Any) -> List[Lock]:
    """Parse locks array."""
    if not isinstance(raw, list):
        raise SchemaError("locks must be an array")

    locks = []
    for lock_data in raw:
        if not isinstance(lock_data, dict):
            raise SchemaError("Each lock must be an object")

        # Validate ID
        if 'id' not in lock_data:
            raise SchemaError("Lock missing required field: id")
        if not isinstance(lock_data['id'], str):
            raise SchemaError(f"Lock ID must be a string, got {type(lock_data['id'])}")

        lock = Lock(
            id=lock_data['id'],
            opens_with=lock_data.get('opens_with', []),
            auto_unlock=lock_data.get('auto_unlock', False),
            description=lock_data.get('description', ''),
            fail_message=lock_data.get('fail_message', ''),
            llm_context=lock_data.get('llm_context')
        )
        locks.append(lock)

    return locks


def parse_npcs(raw: Any) -> List[NPC]:
    """Parse NPCs array."""
    if not isinstance(raw, list):
        raise SchemaError("npcs must be an array")

    npcs = []
    for npc_data in raw:
        if not isinstance(npc_data, dict):
            raise SchemaError("Each NPC must be an object")

        # Validate ID
        if 'id' not in npc_data:
            raise SchemaError("NPC missing required field: id")
        if not isinstance(npc_data['id'], str):
            raise SchemaError(f"NPC ID must be a string, got {type(npc_data['id'])}")

        # Get states and merge in llm_context if present
        states = npc_data.get('states', {})
        if 'llm_context' in npc_data:
            states['llm_context'] = npc_data['llm_context']

        npc = NPC(
            id=npc_data['id'],
            name=npc_data.get('name', ''),
            description=npc_data.get('description', ''),
            location=npc_data.get('location', ''),
            dialogue=npc_data.get('dialogue', {}),
            states=states,
            inventory=npc_data.get('inventory', []),
            behaviors=npc_data.get('behaviors', {})
        )
        npcs.append(npc)

    return npcs


def parse_scripts(raw: Any) -> List[Script]:
    """Parse scripts array."""
    if not isinstance(raw, list):
        raise SchemaError("scripts must be an array")

    scripts = []
    for script_data in raw:
        if not isinstance(script_data, dict):
            raise SchemaError("Each script must be an object")

        # Validate ID
        if 'id' not in script_data:
            raise SchemaError("Script missing required field: id")
        if not isinstance(script_data['id'], str):
            raise SchemaError(f"Script ID must be a string, got {type(script_data['id'])}")

        # Parse triggers
        triggers = []
        for trigger_data in script_data.get('triggers', []):
            # Extract type and conditions, store everything else as params
            trig_type = trigger_data.get('type', '')
            conditions = trigger_data.get('conditions', [])
            # Store all other fields in params
            params = {k: v for k, v in trigger_data.items() if k not in ['type', 'conditions']}

            triggers.append(ScriptTrigger(
                type=trig_type,
                conditions=conditions,
                params=params
            ))

        # Parse effects
        effects = []
        for effect_data in script_data.get('effects', []):
            # Extract type and gather all other fields as params
            effect_type = effect_data.get('type', '')
            # Copy all fields except 'type' into params (or use params if provided)
            if 'params' in effect_data:
                params = effect_data['params']
            else:
                params = {k: v for k, v in effect_data.items() if k != 'type'}

            effects.append(ScriptEffect(
                type=effect_type,
                params=params
            ))

        script = Script(
            id=script_data['id'],
            name=script_data.get('name', ''),
            triggers=triggers,
            effects=effects
        )
        scripts.append(script)

    return scripts


def parse_player_state(raw: Dict[str, Any]) -> PlayerState:
    """Parse player state."""
    if not isinstance(raw, dict):
        raise SchemaError("player must be an object")

    return PlayerState(
        location=raw.get('location', ''),
        inventory=raw.get('inventory', []),
        flags=raw.get('flags', {}),
        stats=raw.get('stats', {})
    )
