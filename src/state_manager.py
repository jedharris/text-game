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
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Location:
    """Location in the game world."""
    id: str
    name: str
    description: str
    exits: Dict[str, ExitDescriptor] = field(default_factory=dict)
    items: List[str] = field(default_factory=list)
    npcs: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: Dict[str, str] = field(default_factory=dict)

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
    behaviors: Dict[str, str] = field(default_factory=dict)

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


@dataclass
class Door:
    """Door connecting locations."""
    id: str
    locations: Tuple[str, ...]
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: Dict[str, str] = field(default_factory=dict)

    @property
    def description(self) -> str:
        """Access description from properties for backward compatibility."""
        return self.properties.get("description", "")

    @description.setter
    def description(self, value: str) -> None:
        """Set description in properties."""
        self.properties["description"] = value

    @property
    def open(self) -> bool:
        """Access open state from properties for backward compatibility."""
        return self.properties.get("open", False)

    @open.setter
    def open(self, value: bool) -> None:
        """Set open state in properties."""
        self.properties["open"] = value

    @property
    def locked(self) -> bool:
        """Access locked state from properties for backward compatibility."""
        return self.properties.get("locked", False)

    @locked.setter
    def locked(self, value: bool) -> None:
        """Set locked state in properties."""
        self.properties["locked"] = value

    @property
    def lock_id(self) -> Optional[str]:
        """Access lock_id from properties for backward compatibility."""
        return self.properties.get("lock_id")

    @lock_id.setter
    def lock_id(self, value: Optional[str]) -> None:
        """Set lock_id in properties."""
        self.properties["lock_id"] = value


@dataclass
class Lock:
    """Lock mechanism."""
    id: str
    properties: Dict[str, Any] = field(default_factory=dict)

    @property
    def opens_with(self) -> List[str]:
        """Access opens_with from properties for backward compatibility."""
        return self.properties.get("opens_with", [])

    @opens_with.setter
    def opens_with(self, value: List[str]) -> None:
        """Set opens_with in properties."""
        self.properties["opens_with"] = value

    @property
    def auto_unlock(self) -> bool:
        """Access auto_unlock from properties for backward compatibility."""
        return self.properties.get("auto_unlock", False)

    @auto_unlock.setter
    def auto_unlock(self, value: bool) -> None:
        """Set auto_unlock in properties."""
        self.properties["auto_unlock"] = value


@dataclass
class NPC:
    """Non-player character."""
    id: str
    name: str
    description: str
    location: str
    inventory: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: Dict[str, str] = field(default_factory=dict)


@dataclass
class PlayerState:
    """Player state information."""
    location: str
    inventory: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)

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


@dataclass
class GameState:
    """Complete game state."""
    metadata: Metadata
    locations: List[Location] = field(default_factory=list)
    doors: List[Door] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    locks: List[Lock] = field(default_factory=list)
    npcs: List[NPC] = field(default_factory=list)
    player: Optional[PlayerState] = None
    extra: Dict[str, Any] = field(default_factory=dict)

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

    def get_door(self, door_id: str) -> Door:
        """Get door by ID."""
        for door in self.doors:
            if door.id == door_id:
                return door
        raise KeyError(f"Door not found: {door_id}")

    def get_lock(self, lock_id: str) -> Lock:
        """Get lock by ID."""
        for lock in self.locks:
            if lock.id == lock_id:
                return lock
        raise KeyError(f"Lock not found: {lock_id}")

    def get_npc(self, npc_id: str) -> NPC:
        """Get NPC by ID."""
        for npc in self.npcs:
            if npc.id == npc_id:
                return npc
        raise KeyError(f"NPC not found: {npc_id}")

    def move_item(self, item_id: str, to_player: bool = False,
                  to_location: Optional[str] = None, to_container: Optional[str] = None) -> None:
        """Move item to new location."""
        item = self.get_item(item_id)
        old_location = item.location

        # Remove from old location
        if old_location == "player" and self.player:
            if item_id in self.player.inventory:
                self.player.inventory.remove(item_id)
        else:
            # Check if it's in a location
            for loc in self.locations:
                if item_id in loc.items:
                    loc.items.remove(item_id)
                    break

        # Add to new location
        if to_player:
            item.location = "player"
            if self.player and item_id not in self.player.inventory:
                self.player.inventory.append(item_id)
        elif to_location:
            item.location = to_location
            loc = self.get_location(to_location)
            if item_id not in loc.items:
                loc.items.append(item_id)
        elif to_container:
            item.location = to_container

    def set_player_location(self, location_id: str) -> None:
        """Set player's current location."""
        if self.player:
            self.player.location = location_id

    def set_flag(self, flag_name: str, value: Any) -> None:
        """Set a player flag."""
        if self.player:
            if "flags" not in self.player.properties:
                self.player.properties["flags"] = {}
            self.player.properties["flags"][flag_name] = value

    def get_flag(self, flag_name: str, default: Any = None) -> Any:
        """Get a player flag."""
        if self.player:
            flags = self.player.properties.get("flags", {})
            return flags.get(flag_name, default)
        return default

    def build_id_registry(self) -> Dict[str, str]:
        """Build registry of all entity IDs to their types."""
        registry = {"player": "player"}

        for loc in self.locations:
            registry[loc.id] = "location"
        for item in self.items:
            registry[item.id] = "item"
        for door in self.doors:
            registry[door.id] = "door"
        for lock in self.locks:
            registry[lock.id] = "lock"
        for npc in self.npcs:
            registry[npc.id] = "npc"

        return registry


# Parsers
def _parse_exit(direction: str, raw: Dict[str, Any]) -> ExitDescriptor:
    """Parse exit descriptor from JSON dict."""
    core_fields = {'type', 'to', 'door_id'}

    return ExitDescriptor(
        type=raw.get('type', 'open'),
        to=raw.get('to'),
        door_id=raw.get('door_id'),
        properties={k: v for k, v in raw.items() if k not in core_fields}
    )


def _parse_location(raw: Dict[str, Any]) -> Location:
    """Parse location from JSON dict."""
    core_fields = {'id', 'name', 'description', 'exits', 'items', 'npcs', 'behaviors'}

    # Parse exits
    exits = {}
    for direction, exit_data in raw.get('exits', {}).items():
        exits[direction] = _parse_exit(direction, exit_data)

    return Location(
        id=raw['id'],
        name=raw.get('name', ''),
        description=raw.get('description', ''),
        exits=exits,
        items=raw.get('items', []),
        npcs=raw.get('npcs', []),
        properties={k: v for k, v in raw.items() if k not in core_fields},
        behaviors=raw.get('behaviors', {})
    )


def _parse_item(raw: Dict[str, Any]) -> Item:
    """Parse item from JSON dict."""
    core_fields = {'id', 'name', 'description', 'location', 'behaviors'}

    return Item(
        id=raw['id'],
        name=raw.get('name', ''),
        description=raw.get('description', ''),
        location=raw.get('location', ''),
        properties={k: v for k, v in raw.items() if k not in core_fields},
        behaviors=raw.get('behaviors', {})
    )


def _parse_door(raw: Dict[str, Any]) -> Door:
    """Parse door from JSON dict."""
    core_fields = {'id', 'locations', 'behaviors'}

    locations = raw.get('locations', [])
    if isinstance(locations, list):
        locations = tuple(locations)

    return Door(
        id=raw['id'],
        locations=locations,
        properties={k: v for k, v in raw.items() if k not in core_fields},
        behaviors=raw.get('behaviors', {})
    )


def _parse_lock(raw: Dict[str, Any]) -> Lock:
    """Parse lock from JSON dict."""
    core_fields = {'id'}

    return Lock(
        id=raw['id'],
        properties={k: v for k, v in raw.items() if k not in core_fields}
    )


def _parse_npc(raw: Dict[str, Any]) -> NPC:
    """Parse NPC from JSON dict."""
    core_fields = {'id', 'name', 'description', 'location', 'inventory', 'behaviors'}

    return NPC(
        id=raw['id'],
        name=raw.get('name', ''),
        description=raw.get('description', ''),
        location=raw.get('location', ''),
        inventory=raw.get('inventory', []),
        properties={k: v for k, v in raw.items() if k not in core_fields},
        behaviors=raw.get('behaviors', {})
    )


def _parse_player_state(raw: Dict[str, Any]) -> PlayerState:
    """Parse player state from JSON dict."""
    core_fields = {'location', 'inventory'}

    return PlayerState(
        location=raw.get('location', ''),
        inventory=raw.get('inventory', []),
        properties={k: v for k, v in raw.items() if k not in core_fields}
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
    """Load game state from file path or dict."""
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

    # Parse items
    items = [_parse_item(item) for item in data.get('items', [])]

    # Parse doors
    doors = [_parse_door(door) for door in data.get('doors', [])]

    # Parse locks
    locks = [_parse_lock(lock) for lock in data.get('locks', [])]

    # Parse NPCs
    npcs = [_parse_npc(npc) for npc in data.get('npcs', [])]

    # Parse player state (support both 'player_state' and 'player' keys)
    player = None
    if 'player_state' in data:
        player = _parse_player_state(data['player_state'])
    elif 'player' in data:
        player = _parse_player_state(data['player'])
    elif metadata.start_location:
        # Create default player state from metadata.start_location
        player = PlayerState(location=metadata.start_location)

    state = GameState(
        metadata=metadata,
        locations=locations,
        items=items,
        doors=doors,
        locks=locks,
        npcs=npcs,
        player=player
    )

    # Validate after loading
    from src.validators import validate_game_state
    validate_game_state(state)

    return state


# Serializers
def _serialize_exit(exit_desc: ExitDescriptor) -> Dict[str, Any]:
    """Serialize exit descriptor to dict."""
    result = {'type': exit_desc.type}

    if exit_desc.to:
        result['to'] = exit_desc.to
    if exit_desc.door_id:
        result['door_id'] = exit_desc.door_id

    # Merge properties
    result.update(exit_desc.properties)

    return result


def _serialize_location(loc: Location) -> Dict[str, Any]:
    """Serialize location to dict."""
    result = {
        'id': loc.id,
        'name': loc.name,
        'description': loc.description,
        'exits': {d: _serialize_exit(e) for d, e in loc.exits.items()},
        'items': loc.items,
        'npcs': loc.npcs
    }

    # Merge properties
    result.update(loc.properties)

    # Add behaviors if present
    if loc.behaviors:
        result['behaviors'] = loc.behaviors

    return result


def _serialize_item(item: Item) -> Dict[str, Any]:
    """Serialize item to dict."""
    result = {
        'id': item.id,
        'name': item.name,
        'description': item.description,
        'location': item.location
    }

    # Merge properties
    result.update(item.properties)

    # Add behaviors if present
    if item.behaviors:
        result['behaviors'] = item.behaviors

    return result


def _serialize_door(door: Door) -> Dict[str, Any]:
    """Serialize door to dict."""
    result = {
        'id': door.id,
        'locations': list(door.locations)
    }

    # Merge properties
    result.update(door.properties)

    # Add behaviors if present
    if door.behaviors:
        result['behaviors'] = door.behaviors

    return result


def _serialize_lock(lock: Lock) -> Dict[str, Any]:
    """Serialize lock to dict."""
    result = {'id': lock.id}

    # Merge properties
    result.update(lock.properties)

    return result


def _serialize_npc(npc: NPC) -> Dict[str, Any]:
    """Serialize NPC to dict."""
    result = {
        'id': npc.id,
        'name': npc.name,
        'description': npc.description,
        'location': npc.location,
        'inventory': npc.inventory
    }

    # Merge properties
    result.update(npc.properties)

    # Add behaviors if present
    if npc.behaviors:
        result['behaviors'] = npc.behaviors

    return result


def _serialize_player_state(player: PlayerState) -> Dict[str, Any]:
    """Serialize player state to dict."""
    result = {
        'location': player.location,
        'inventory': player.inventory
    }

    # Merge properties
    result.update(player.properties)

    return result


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
    """Serialize game state to dict."""
    result = {
        'metadata': _serialize_metadata(state.metadata),
        'locations': [_serialize_location(loc) for loc in state.locations],
        'items': [_serialize_item(item) for item in state.items],
        'doors': [_serialize_door(door) for door in state.doors],
        'locks': [_serialize_lock(lock) for lock in state.locks],
        'npcs': [_serialize_npc(npc) for npc in state.npcs]
    }

    if state.player:
        result['player_state'] = _serialize_player_state(state.player)

    return result


def save_game_state(state: GameState, path: Union[str, Path]) -> None:
    """Save game state to file."""
    data = game_state_to_dict(state)

    path = Path(path)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
