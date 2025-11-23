"""
Data models for game state entities.

Defines dataclasses mirroring the JSON schema structure.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum


class ExitType(str, Enum):
    """Exit type enumeration."""
    DOOR = "door"
    OPEN = "open"
    PORTAL = "portal"
    SCRIPTED = "scripted"


class ItemType(str, Enum):
    """Item type enumeration."""
    TOOL = "tool"
    KEY = "key"
    CONTAINER = "container"
    SCENERY = "scenery"
    READABLE = "readable"


@dataclass
class Metadata:
    """Game metadata."""
    title: str
    author: str = ""
    version: str = "1.0"
    description: str = ""
    start_location: str = ""


@dataclass
class Vocabulary:
    """Vocabulary with word aliases."""
    aliases: Dict[str, List[str]] = field(default_factory=dict)
    # Legacy support for separate categories
    verbs: Dict[str, List[str]] = field(default_factory=dict)
    nouns: Dict[str, List[str]] = field(default_factory=dict)
    adjectives: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class ExitDescriptor:
    """Exit descriptor for location connections."""
    type: str
    to: Optional[str] = None
    door_id: Optional[str] = None
    description: Optional[str] = None
    hidden: bool = False
    conditions: Optional[List[str]] = None
    on_fail: Optional[str] = None

    def is_available(self, state: 'GameState') -> bool:
        """Check if exit is available based on conditions."""
        if not self.conditions:
            return True
        # TODO: Implement condition evaluation
        return True


@dataclass
class Location:
    """Location in the game world."""
    id: str
    name: str
    description: str
    exits: Dict[str, ExitDescriptor] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)
    npcs: List[str] = field(default_factory=list)
    llm_context: Optional[Dict[str, Any]] = None
    behaviors: Dict[str, str] = field(default_factory=dict)

    def has_exit(self, direction: str) -> bool:
        """Check if location has an exit in the given direction."""
        return direction in self.exits

    def resolve_exit(self, direction: str) -> Optional[ExitDescriptor]:
        """Get exit descriptor for a direction."""
        return self.exits.get(direction)


@dataclass
class Door:
    """Door connecting locations."""
    id: str
    locations: Tuple[str, ...]
    description: str = ""
    locked: bool = False
    lock_id: Optional[str] = None
    open: bool = True
    one_way: bool = False
    llm_context: Optional[Dict[str, Any]] = None
    behaviors: Dict[str, str] = field(default_factory=dict)

    def unlock(self, key_item_id: Optional[str], state: 'GameState') -> bool:
        """Attempt to unlock the door."""
        if not self.locked:
            return True
        # TODO: Implement unlock logic with lock validation
        return False

    def lock(self) -> None:
        """Lock the door."""
        self.locked = True

    def open_door(self) -> None:
        """Open the door."""
        self.open = True

    def close_door(self) -> None:
        """Close the door."""
        self.open = False


@dataclass
class ContainerInfo:
    """Container information for items."""
    is_container: bool = True
    is_surface: bool = False  # True = items visible on top, False = hidden inside
    open: bool = False  # For enclosed containers
    locked: bool = False
    lock_id: Optional[str] = None
    contents: List[str] = field(default_factory=list)
    capacity: int = 0  # 0 = unlimited


@dataclass
class Item:
    """Item in the game world."""
    id: str
    name: str
    description: str
    type: str
    portable: bool
    location: str
    states: Dict[str, Any] = field(default_factory=dict)
    container: Optional[ContainerInfo] = None
    provides_light: bool = False
    behaviors: Dict[str, str] = field(default_factory=dict)
    pushable: bool = False  # Can be pushed to move it

    def is_accessible(self, state: 'GameState') -> bool:
        """Check if item is accessible to player."""
        # TODO: Implement accessibility logic
        return True

    def add_state(self, key: str, value: Any) -> None:
        """Add or update item state."""
        self.states[key] = value


@dataclass
class Lock:
    """Lock mechanism."""
    id: str
    opens_with: List[str] = field(default_factory=list)
    auto_unlock: bool = False
    description: str = ""
    fail_message: str = ""
    llm_context: Optional[Dict[str, Any]] = None

    def can_unlock(self, state: 'GameState', key_id: Optional[str] = None) -> bool:
        """Check if lock can be unlocked with given key."""
        if not self.opens_with:
            return True
        if key_id is None:
            return False
        return key_id in self.opens_with


@dataclass
class NPC:
    """Non-player character."""
    id: str
    name: str
    description: str
    location: str
    dialogue: Any = field(default_factory=list)  # Can be list or dict
    states: Dict[str, Any] = field(default_factory=dict)
    inventory: List[str] = field(default_factory=list)
    behaviors: Dict[str, str] = field(default_factory=dict)


@dataclass
class ScriptTrigger:
    """Script trigger condition."""
    type: str
    conditions: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)  # Store all other fields


@dataclass
class ScriptEffect:
    """Script effect action."""
    type: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Script:
    """Scripted event or action."""
    id: str
    name: str = ""
    triggers: List[ScriptTrigger] = field(default_factory=list)
    effects: List[ScriptEffect] = field(default_factory=list)


@dataclass
class PlayerState:
    """Player state information."""
    location: str
    inventory: List[str] = field(default_factory=list)
    flags: Dict[str, Any] = field(default_factory=dict)
    stats: Dict[str, int] = field(default_factory=dict)


@dataclass
class GameState:
    """Complete game state."""
    metadata: Metadata
    locations: List[Location] = field(default_factory=list)
    doors: List[Door] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    locks: List[Lock] = field(default_factory=list)
    npcs: List[NPC] = field(default_factory=list)
    scripts: List[Script] = field(default_factory=list)
    player: Optional[PlayerState] = None
    vocabulary: Vocabulary = field(default_factory=Vocabulary)
    extra: Dict[str, Any] = field(default_factory=dict)

    def get_location(self, location_id: str) -> Location:
        """Get location by ID."""
        for loc in self.locations:
            if loc.id == location_id:
                return loc
        raise KeyError(f"Location not found: {location_id}")

    def get_item(self, item_id: str) -> Item:
        """Get item by ID."""
        for item in self.items:
            if item.id == item_id:
                return item
        raise KeyError(f"Item not found: {item_id}")

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

    def move_item(self, item_id: str, *, to_location: str = None,
                  to_container: str = None, to_player: bool = False,
                  to_npc: str = None) -> None:
        """Move item to a new location."""
        item = self.get_item(item_id)

        # Remove from old location
        old_location = item.location
        if old_location == "player":
            if item_id in self.player.inventory:
                self.player.inventory.remove(item_id)
        else:
            # Try to find in location
            try:
                loc = self.get_location(old_location)
                if item_id in loc.items:
                    loc.items.remove(item_id)
            except KeyError:
                # Might be in container or NPC
                pass

        # Set new location
        if to_player:
            item.location = "player"
            if item_id not in self.player.inventory:
                self.player.inventory.append(item_id)
        elif to_location:
            item.location = to_location
            loc = self.get_location(to_location)
            if item_id not in loc.items:
                loc.items.append(item_id)
        elif to_container:
            item.location = to_container
            container = self.get_item(to_container)
            if container.container and item_id not in container.container.contents:
                container.container.contents.append(item_id)
        elif to_npc:
            item.location = to_npc
            npc = self.get_npc(to_npc)
            if item_id not in npc.inventory:
                npc.inventory.append(item_id)

    def set_player_location(self, location_id: str) -> None:
        """Set player's current location."""
        if self.player is None:
            self.player = PlayerState(location=location_id)
        else:
            self.player.location = location_id

    def set_flag(self, name: str, value: Any) -> None:
        """Set a player flag."""
        if self.player is None:
            self.player = PlayerState(location="", flags={name: value})
        else:
            self.player.flags[name] = value

    def get_flag(self, name: str, default: Any = None) -> Any:
        """Get a player flag value."""
        if self.player is None:
            return default
        return self.player.flags.get(name, default)

    def clone(self) -> 'GameState':
        """Create a deep copy of game state."""
        import copy
        return copy.deepcopy(self)

    def build_id_registry(self) -> Dict[str, str]:
        """Build a registry mapping all IDs to their entity types."""
        registry = {}

        # Add reserved player ID
        registry["player"] = "player"

        # Add all entity IDs
        for loc in self.locations:
            registry[loc.id] = "location"
        for door in self.doors:
            registry[door.id] = "door"
        for item in self.items:
            registry[item.id] = "item"
        for lock in self.locks:
            registry[lock.id] = "lock"
        for npc in self.npcs:
            registry[npc.id] = "npc"
        for script in self.scripts:
            registry[script.id] = "script"

        return registry
