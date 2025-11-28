"""
Simplified property-based state manager.

All non-structural fields go into the properties dict.
"""
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path


# Exceptions
class ValidationError(Exception):
    """Raised when game state validation fails."""
    pass


class LoadError(Exception):
    """Raised when game state loading fails."""
    pass


class ContainerInfo:
    """Wrapper for container dict to provide attribute access."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __bool__(self):
        return bool(self._data)

    @property
    def is_surface(self) -> bool:
        return self._data.get("is_surface", False)

    @property
    def open(self) -> bool:
        return self._data.get("open", False)

    @open.setter
    def open(self, value: bool) -> None:
        self._data["open"] = value

    @property
    def capacity(self) -> int:
        return self._data.get("capacity", 0)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)


# Dataclasses
@dataclass
class Metadata:
    """Game metadata."""
    title: str
    version: str = ""
    description: str = ""
    start_location: str = ""
    author: str = ""


@dataclass
class ExitDescriptor:
    """Exit descriptor for location connections."""
    type: str  # "open" or "door"
    to: Optional[str] = None
    door_id: Optional[str] = None
    name: Optional[str] = None  # User-facing name e.g. "spiral staircase", "stone archway"
    description: Optional[str] = None  # Prose description for examine
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: List[str] = field(default_factory=list)

    @property
    def states(self) -> Dict[str, Any]:
        """Access states dict within properties."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return self.properties["states"]

    @states.setter
    def states(self, value: Dict[str, Any]) -> None:
        """Set states dict within properties."""
        self.properties["states"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return self.properties.get("llm_context")

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value


@dataclass
class Location:
    """Location in the game world."""
    id: str
    name: str
    description: str
    exits: Dict[str, ExitDescriptor] = field(default_factory=dict)
    items: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: List[str] = field(default_factory=list)

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties for backward compatibility."""
        return self.properties.get("llm_context")

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value


@dataclass
class Item:
    """Item in the game world."""
    id: str
    name: str
    description: str
    location: str
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: List[str] = field(default_factory=list)

    @property
    def states(self) -> Dict[str, Any]:
        """Access states dict within properties for backward compatibility."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return self.properties["states"]

    @states.setter
    def states(self, value: Dict[str, Any]) -> None:
        """Set states dict within properties."""
        self.properties["states"] = value

    @property
    def portable(self) -> bool:
        """Access portable from properties for backward compatibility."""
        return self.properties.get("portable", False)

    @portable.setter
    def portable(self, value: bool) -> None:
        """Set portable in properties."""
        self.properties["portable"] = value

    @property
    def pushable(self) -> bool:
        """Access pushable from properties for backward compatibility."""
        return self.properties.get("pushable", False)

    @pushable.setter
    def pushable(self, value: bool) -> None:
        """Set pushable in properties."""
        self.properties["pushable"] = value

    @property
    def provides_light(self) -> bool:
        """Access provides_light from properties for backward compatibility."""
        return self.properties.get("provides_light", False)

    @provides_light.setter
    def provides_light(self, value: bool) -> None:
        """Set provides_light in properties."""
        self.properties["provides_light"] = value

    @property
    def container(self) -> Optional[ContainerInfo]:
        """Access container from properties for backward compatibility."""
        data = self.properties.get("container")
        return ContainerInfo(data) if data else None

    @container.setter
    def container(self, value: Optional[Dict[str, Any]]) -> None:
        """Set container in properties."""
        self.properties["container"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties for backward compatibility."""
        return self.properties.get("llm_context")

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value

    # Door-related properties for unified Item/Door model
    @property
    def is_door(self) -> bool:
        """Check if this item is a door."""
        return "door" in self.properties

    @property
    def door_open(self) -> bool:
        """Get door open state. Returns False if not a door."""
        door_props = self.properties.get("door", {})
        return door_props.get("open", False)

    @door_open.setter
    def door_open(self, value: bool) -> None:
        """Set door open state."""
        if "door" not in self.properties:
            self.properties["door"] = {}
        self.properties["door"]["open"] = value

    @property
    def door_locked(self) -> bool:
        """Get door locked state. Returns False if not a door."""
        door_props = self.properties.get("door", {})
        return door_props.get("locked", False)

    @door_locked.setter
    def door_locked(self, value: bool) -> None:
        """Set door locked state."""
        if "door" not in self.properties:
            self.properties["door"] = {}
        self.properties["door"]["locked"] = value

    @property
    def door_lock_id(self) -> Optional[str]:
        """Get door's lock ID. Returns None if not a door or no lock."""
        door_props = self.properties.get("door", {})
        return door_props.get("lock_id")


@dataclass
class Lock:
    """Lock mechanism."""
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: List[str] = field(default_factory=list)

    @property
    def opens_with(self) -> List[str]:
        """Access opens_with from properties."""
        return self.properties.get("opens_with", [])

    @opens_with.setter
    def opens_with(self, value: List[str]) -> None:
        """Set opens_with in properties."""
        self.properties["opens_with"] = value

    @property
    def auto_unlock(self) -> bool:
        """Access auto_unlock from properties."""
        return self.properties.get("auto_unlock", False)

    @auto_unlock.setter
    def auto_unlock(self, value: bool) -> None:
        """Set auto_unlock in properties."""
        self.properties["auto_unlock"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return self.properties.get("llm_context")

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value


@dataclass
class Actor:
    """Unified actor (player or NPC)."""
    id: str
    name: str
    description: str
    location: str
    inventory: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: List[str] = field(default_factory=list)

    @property
    def stats(self) -> Dict[str, Any]:
        """Access stats dict within properties for backward compatibility."""
        if "stats" not in self.properties:
            self.properties["stats"] = {}
        return self.properties["stats"]

    @stats.setter
    def stats(self, value: Dict[str, Any]) -> None:
        """Set stats dict within properties."""
        self.properties["stats"] = value

    @property
    def flags(self) -> Dict[str, Any]:
        """Access flags dict within properties for backward compatibility."""
        if "flags" not in self.properties:
            self.properties["flags"] = {}
        return self.properties["flags"]

    @flags.setter
    def flags(self, value: Dict[str, Any]) -> None:
        """Set flags dict within properties."""
        self.properties["flags"] = value

    @property
    def states(self) -> Dict[str, Any]:
        """Access states dict within properties."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return self.properties["states"]

    @states.setter
    def states(self, value: Dict[str, Any]) -> None:
        """Set states dict within properties."""
        self.properties["states"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return self.properties.get("llm_context")

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value


@dataclass
class GameState:
    """Complete game state."""
    metadata: Metadata
    locations: List[Location] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    locks: List[Lock] = field(default_factory=list)
    actors: Dict[str, Actor] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)

    def get_actor(self, actor_id: str) -> Actor:
        """Get actor by ID."""
        actor = self.actors.get(actor_id)
        if actor:
            return actor
        raise KeyError(f"Actor not found: {actor_id}")

    def get_item(self, item_id: str) -> Item:
        """Get item by ID."""
        for item in self.items:
            if item.id == item_id:
                return item
        raise KeyError(f"Item not found: {item_id}")

    def get_location(self, location_id: str) -> Location:
        """Get location by ID."""
        for loc in self.locations:
            if loc.id == location_id:
                return loc
        raise KeyError(f"Location not found: {location_id}")

    def get_lock(self, lock_id: str) -> Lock:
        """Get lock by ID."""
        for lock in self.locks:
            if lock.id == lock_id:
                return lock
        raise KeyError(f"Lock not found: {lock_id}")

    def move_item(self, item_id: str, to_player: bool = False,
                  to_location: Optional[str] = None, to_container: Optional[str] = None) -> None:
        """Move item to new location."""
        item = self.get_item(item_id)
        old_location = item.location
        player = self.actors.get("player")

        # Remove from old location
        if old_location == "player" and player:
            if item_id in player.inventory:
                player.inventory.remove(item_id)
        else:
            # Check if it's in a location
            for loc in self.locations:
                if item_id in loc.items:
                    loc.items.remove(item_id)
                    break

        # Add to new location
        if to_player:
            item.location = "player"
            if player and item_id not in player.inventory:
                player.inventory.append(item_id)
        elif to_location:
            item.location = to_location
            loc = self.get_location(to_location)
            if item_id not in loc.items:
                loc.items.append(item_id)
        elif to_container:
            item.location = to_container

    def set_player_location(self, location_id: str) -> None:
        """Set player's current location."""
        player = self.actors.get("player")
        if player:
            player.location = location_id

    def set_flag(self, flag_name: str, value: Any) -> None:
        """Set a player flag."""
        player = self.actors.get("player")
        if player:
            if "flags" not in player.properties:
                player.properties["flags"] = {}
            player.properties["flags"][flag_name] = value

    def get_flag(self, flag_name: str, default: Any = None) -> Any:
        """Get a player flag."""
        player = self.actors.get("player")
        if player:
            flags = player.properties.get("flags", {})
            return flags.get(flag_name, default)
        return default

    def build_id_registry(self) -> Dict[str, str]:
        """Build registry of all entity IDs to their types."""
        registry = {"player": "player"}

        for loc in self.locations:
            registry[loc.id] = "location"
        for item in self.items:
            if item.is_door:
                registry[item.id] = "door_item"
            else:
                registry[item.id] = "item"
        for lock in self.locks:
            registry[lock.id] = "lock"
        for actor_id, actor in self.actors.items():
            if actor_id != "player":
                registry[actor_id] = "npc"

        return registry


# Parsers
def _parse_exit(direction: str, raw: Dict[str, Any]) -> ExitDescriptor:
    """Parse exit descriptor from JSON dict."""
    core_fields = {'type', 'to', 'door_id', 'name', 'description', 'behaviors'}

    return ExitDescriptor(
        type=raw.get('type', 'open'),
        to=raw.get('to'),
        door_id=raw.get('door_id'),
        name=raw.get('name'),
        description=raw.get('description'),
        properties={k: v for k, v in raw.items() if k not in core_fields},
        behaviors=raw.get('behaviors', [])
    )


def _parse_location(raw: Dict[str, Any]) -> Location:
    """Parse location from JSON dict."""
    # Note: 'npcs' is included in core_fields to filter it from properties
    # but it's no longer stored on Location (actors track their own location)
    core_fields = {'id', 'name', 'description', 'exits', 'items', 'npcs', 'behaviors'}

    # Parse exits
    exits = {}
    for direction, exit_data in raw.get('exits', {}).items():
        exits[direction] = _parse_exit(direction, exit_data)

    # Parse behaviors - keep as-is (supports both dict and list)
    behaviors = raw.get('behaviors', [])

    return Location(
        id=raw['id'],
        name=raw.get('name', ''),
        description=raw.get('description', ''),
        exits=exits,
        items=raw.get('items', []),
        properties=_parse_properties(raw, core_fields),
        behaviors=behaviors
    )


def _parse_properties(raw: Dict[str, Any], core_fields: set) -> Dict[str, Any]:
    """Parse properties from JSON dict.

    Supports both formats:
    - New format: explicit 'properties' dict
    - Old format: properties at top level (non-core fields)

    New format takes precedence, but both are merged for compatibility.
    """
    # Start with explicit properties dict if present
    properties = dict(raw.get('properties', {}))

    # Merge in non-core top-level fields (old format)
    # These are overridden by explicit properties if present
    extended_core = core_fields | {'properties'}
    for k, v in raw.items():
        if k not in extended_core and k not in properties:
            properties[k] = v

    return properties


def _parse_item(raw: Dict[str, Any]) -> Item:
    """Parse item from JSON dict."""
    core_fields = {'id', 'name', 'description', 'location', 'behaviors'}

    # Parse behaviors - keep as-is (supports both dict and list)
    behaviors = raw.get('behaviors', [])

    return Item(
        id=raw['id'],
        name=raw.get('name', ''),
        description=raw.get('description', ''),
        location=raw.get('location', ''),
        properties=_parse_properties(raw, core_fields),
        behaviors=behaviors
    )


def _parse_lock(raw: Dict[str, Any]) -> Lock:
    """Parse lock from JSON dict."""
    core_fields = {'id', 'name', 'description', 'properties', 'behaviors'}

    return Lock(
        id=raw['id'],
        name=raw.get('name'),
        description=raw.get('description'),
        properties=_parse_properties(raw, core_fields),
        behaviors=raw.get('behaviors', [])
    )


def _parse_actor(raw: Dict[str, Any], actor_id: str = None) -> Actor:
    """Parse Actor from JSON dict.

    Args:
        raw: Actor data from JSON
        actor_id: Optional ID override (used when parsing from actors dict where key is the ID)
    """
    core_fields = {'id', 'name', 'description', 'location', 'inventory', 'behaviors'}

    # Use actor_id if provided (from dict key), otherwise require id in raw data
    effective_id = actor_id or raw['id']

    return Actor(
        id=effective_id,
        name=raw.get('name', effective_id),
        description=raw.get('description', ''),
        location=raw.get('location', ''),
        inventory=raw.get('inventory', []),
        properties=_parse_properties(raw, core_fields),
        behaviors=raw.get('behaviors', [])
    )


def _parse_metadata(raw: Dict[str, Any]) -> Metadata:
    """Parse metadata from JSON dict."""
    return Metadata(
        title=raw.get('title', ''),
        version=raw.get('version', ''),
        description=raw.get('description', ''),
        start_location=raw.get('start_location', ''),
        author=raw.get('author', '')
    )


def load_game_state(source: Union[str, Path, Dict[str, Any]]) -> GameState:
    """Load game state from file path or dict.

    Supports both old format (player/npcs fields) and new format (actors dict).
    Doors are represented as Items with a 'door' property.
    """
    if isinstance(source, dict):
        data = source
    else:
        path = Path(source)
        with open(path, 'r') as f:
            data = json.load(f)

    # Parse metadata
    metadata = _parse_metadata(data.get('metadata', {}))

    # Parse locations
    locations = [_parse_location(loc) for loc in data.get('locations', [])]

    # Parse items (doors are stored as items with door property)
    items = [_parse_item(item) for item in data.get('items', [])]

    # Parse locks
    locks = [_parse_lock(lock) for lock in data.get('locks', [])]

    # Parse actors - support both old and new formats
    actors = {}

    # New format: actors dict
    if 'actors' in data:
        for actor_id, actor_data in data['actors'].items():
            actors[actor_id] = _parse_actor(actor_data, actor_id=actor_id)
    else:
        # Old format: separate player and npcs fields
        # Parse player state (support both 'player_state' and 'player' keys)
        if 'player_state' in data:
            actors['player'] = _parse_actor(data['player_state'], actor_id='player')
        elif 'player' in data:
            actors['player'] = _parse_actor(data['player'], actor_id='player')
        elif metadata.start_location:
            # Create default player state from metadata.start_location
            actors['player'] = Actor(
                id='player',
                name='player',
                description='The player character',
                location=metadata.start_location,
                inventory=[],
                properties={},
                behaviors=[]
            )

        # Parse NPCs
        for npc_data in data.get('npcs', []):
            npc = _parse_actor(npc_data)
            actors[npc.id] = npc

    state = GameState(
        metadata=metadata,
        locations=locations,
        items=items,
        locks=locks,
        actors=actors
    )

    # Validate after loading
    from src.validators import validate_game_state
    validate_game_state(state)

    return state


# Serializers
def _serialize_entity(
    entity,
    required_fields: List[str],
    optional_fields: List[str] = None
) -> Dict[str, Any]:
    """Generic entity serializer.

    Args:
        entity: Any dataclass with properties and behaviors attributes
        required_fields: Fields to always include (e.g., ['id', 'name', 'description'])
        optional_fields: Fields to include only if truthy (e.g., ['name', 'description'] for Lock)

    Returns:
        Dict with fields, merged properties, and behaviors (if present)
    """
    result = {}

    # Add required fields
    for field in required_fields:
        result[field] = getattr(entity, field)

    # Add optional fields only if they have values
    for field in (optional_fields or []):
        value = getattr(entity, field, None)
        if value:
            result[field] = value

    # Merge properties
    result.update(entity.properties)

    # Add behaviors if present
    if entity.behaviors:
        result['behaviors'] = entity.behaviors

    return result


def _serialize_exit(exit_desc: ExitDescriptor) -> Dict[str, Any]:
    """Serialize exit descriptor to dict."""
    return _serialize_entity(
        exit_desc,
        required_fields=['type'],
        optional_fields=['to', 'door_id', 'name', 'description']
    )


def _serialize_location(loc: Location) -> Dict[str, Any]:
    """Serialize location to dict."""
    result = _serialize_entity(loc, required_fields=['id', 'name', 'description'])
    result['exits'] = {d: _serialize_exit(e) for d, e in loc.exits.items()}
    result['items'] = loc.items
    return result


def _serialize_item(item: Item) -> Dict[str, Any]:
    """Serialize item to dict."""
    return _serialize_entity(item, required_fields=['id', 'name', 'description', 'location'])


def _serialize_lock(lock: Lock) -> Dict[str, Any]:
    """Serialize lock to dict."""
    return _serialize_entity(lock, required_fields=['id'], optional_fields=['name', 'description'])


def _serialize_actor(actor: Actor) -> Dict[str, Any]:
    """Serialize Actor to dict."""
    return _serialize_entity(actor, required_fields=['id', 'name', 'description', 'location', 'inventory'])


def _serialize_metadata(metadata: Metadata) -> Dict[str, Any]:
    """Serialize metadata to dict."""
    result = {
        'title': metadata.title,
        'version': metadata.version
    }

    if metadata.description:
        result['description'] = metadata.description
    if metadata.start_location:
        result['start_location'] = metadata.start_location
    if metadata.author:
        result['author'] = metadata.author

    return result


def game_state_to_dict(state: GameState) -> Dict[str, Any]:
    """Serialize game state to dict using new unified actor format.

    Note: Doors are stored as items with properties.door.
    """
    return {
        'metadata': _serialize_metadata(state.metadata),
        'locations': [_serialize_location(loc) for loc in state.locations],
        'items': [_serialize_item(item) for item in state.items],
        'locks': [_serialize_lock(lock) for lock in state.locks],
        'actors': {actor_id: _serialize_actor(actor) for actor_id, actor in state.actors.items()}
    }


def save_game_state(state: GameState, path: Union[str, Path]) -> None:
    """Save game state to file."""
    data = game_state_to_dict(state)

    path = Path(path)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
