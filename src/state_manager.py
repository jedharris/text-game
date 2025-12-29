"""
Simplified property-based state manager.

All non-structural fields go into the properties dict.
"""
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from pathlib import Path

from src.types import LocationId, ActorId, ItemId, LockId, PartId, ExitId, CommitmentId, ScheduledEventId, GossipId, SpreadId


# Exceptions
class ValidationError(Exception):
    """Raised when game state validation fails."""
    pass


class LoadError(Exception):
    """Raised when game state loading fails."""
    pass


class CoreFieldProtectingDict(dict):
    """
    Dict that prevents modification of core entity fields via properties.

    Core fields are structural fields defined in entity dataclass definitions
    (e.g., id, name, location, inventory). These fields should only be modified
    via direct attribute access (entity.location = value), not via properties
    dict (entity.properties['location'] = value).

    This protection catches bugs where code accidentally modifies core fields
    through the properties dict instead of the proper attribute interface.
    """
    _core_fields: set[str]

    def __init__(self, core_fields: set[str], *args: Any, **kwargs: Any):
        """
        Create a protecting dict.

        Args:
            core_fields: Set of field names that cannot be modified via this dict
            *args, **kwargs: Standard dict constructor arguments
        """
        super().__init__(*args, **kwargs)
        # Use object.__setattr__ to bypass our own __setattr__ protection
        object.__setattr__(self, '_core_fields', core_fields)

    def __setitem__(self, key: str, value: Any) -> None:
        """Prevent setting core fields."""
        if key in self._core_fields:
            raise TypeError(
                f"Cannot set core field '{key}' via properties dict. "
                f"Use direct attribute access instead: entity.{key} = value"
            )
        super().__setitem__(key, value)

    def __setattr__(self, key: str, value: Any) -> None:
        """Block attribute-style writes to prevent circumvention."""
        if key == '_core_fields':
            # Allow setting _core_fields during __init__
            object.__setattr__(self, key, value)
        else:
            raise TypeError(
                f"Cannot set attributes on properties dict. "
                f"Use dictionary-style access: properties['{key}'] = value"
            )

    def setdefault(self, key: str, default: Any = None) -> Any:
        """Prevent using setdefault on core fields."""
        if key in self._core_fields:
            raise TypeError(
                f"Cannot set core field '{key}' via properties dict. "
                f"Use direct attribute access instead: entity.{key} = value"
            )
        return super().setdefault(key, default)

    def update(self, *args: Any, **kwargs: Any) -> None:
        """Prevent using update with core fields."""
        # Build a dict of all updates to check
        updates: Dict[str, Any] = {}
        if args:
            if len(args) > 1:
                raise TypeError(f"update expected at most 1 arguments, got {len(args)}")
            other = args[0]
            if hasattr(other, "keys"):
                for key in other.keys():
                    updates[key] = other[key]
            else:
                for key, value in other:
                    updates[key] = value
        updates.update(kwargs)

        # Check for core field violations
        for key in updates:
            if key in self._core_fields:
                raise TypeError(
                    f"Cannot set core field '{key}' via properties dict. "
                    f"Use direct attribute access instead: entity.{key} = value"
                )

        # If no violations, perform the update
        super().update(updates)


class ContainerInfo:
    """Wrapper for container dict to provide attribute access."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __bool__(self) -> bool:
        return bool(self._data)

    @property
    def is_surface(self) -> bool:
        return bool(self._data.get("is_surface", False))

    @property
    def open(self) -> bool:
        return bool(self._data.get("open", False))

    @open.setter
    def open(self, value: bool) -> None:
        self._data["open"] = value

    @property
    def capacity(self) -> int:
        return int(self._data.get("capacity", 0))

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)


def _parse_behaviors(raw_behaviors: Any, entity_label: str) -> List[str]:
    """
    Ensure behaviors are a list of module strings (no legacy dict or function suffixes).

    Args:
        raw_behaviors: Behaviors value from JSON
        entity_label: Identifier for error messages (e.g., item id)
    """
    if raw_behaviors in (None, False, "", 0):
        return []

    if not isinstance(raw_behaviors, list):
        raise ValueError(f"Behaviors for {entity_label} must be a list of modules.")

    modules: List[str] = []
    for ref in raw_behaviors:
        if not isinstance(ref, str):
            raise ValueError(f"Behaviors for {entity_label} must contain only strings.")
        if ":" in ref:
            raise ValueError(
                f"Behaviors for {entity_label} must be module paths only, not 'module:function'."
            )
        ref = ref.strip()
        if not ref:
            continue
        if ref not in modules:
            modules.append(ref)

    return modules


# Dataclasses
@dataclass
class Metadata:
    """Game metadata."""
    title: str
    version: str = ""
    description: str = ""
    start_location: str = ""
    author: str = ""
    extra_turn_phases: List[str] = field(default_factory=list)


@dataclass
class ExitDescriptor:
    """Exit descriptor for location connections.

    For exits with both a door and a passage (e.g., door leading to stairs),
    use the passage and door_at fields to enable proper traversal narration:

    - passage: Name of traversal structure beyond the door (e.g., "narrow stairs")
    - door_at: Location ID where the door is physically located

    When traversing, the message order depends on which end you're at:
    - If at door_at location: "go through door and climb stairs"
    - If at other end: "descend stairs and go through door"
    """
    type: str  # "open" or "door"
    to: Optional[LocationId] = None
    door_id: Optional[ItemId] = None
    name: str = ""  # User-facing name e.g. "spiral staircase", "stone archway"
    description: str = ""  # Prose description for examine
    passage: Optional[str] = None  # Traversal structure beyond door (e.g., "narrow stairs")
    door_at: Optional[LocationId] = None  # Which end the door is at
    _properties: Dict[str, Any] = field(default_factory=lambda: CoreFieldProtectingDict(
        {'type', 'to', 'door_id', 'name', 'description', 'passage', 'door_at', 'behaviors'}
    ))
    behaviors: List[str] = field(default_factory=list)
    # Internal fields for id synthesis - set by parser
    _direction: str = field(default="", repr=False)
    _location_id: LocationId = field(default=LocationId(""), repr=False)

    @property
    def properties(self) -> Dict[str, Any]:
        """Access properties dict with core field protection."""
        return self._properties

    @property
    def id(self) -> ExitId:
        """Synthesized ID from location and direction."""
        if self._location_id and self._direction:
            return ExitId(f"exit:{self._location_id}:{self._direction}")
        return ExitId("")

    @property
    def states(self) -> Dict[str, Any]:
        """Access states dict within properties."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return cast(Dict[str, Any], self.properties["states"])

    @states.setter
    def states(self, value: Dict[str, Any]) -> None:
        """Set states dict within properties."""
        self.properties["states"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return cast(Optional[Dict[str, Any]], self.properties.get("llm_context"))

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value


@dataclass
class Location:
    """Location in the game world."""
    id: LocationId
    name: str
    description: str
    exits: Dict[str, ExitDescriptor] = field(default_factory=dict)
    items: List[ItemId] = field(default_factory=list)
    _properties: Dict[str, Any] = field(default_factory=lambda: CoreFieldProtectingDict(
        {'id', 'name', 'description', 'exits', 'items', 'behaviors'}
    ))
    behaviors: List[str] = field(default_factory=list)

    @property
    def properties(self) -> Dict[str, Any]:
        """Access properties dict with core field protection."""
        return self._properties

    @property
    def states(self) -> Dict[str, Any]:
        """Access states dict within properties."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return cast(Dict[str, Any], self.properties["states"])

    @states.setter
    def states(self, value: Dict[str, Any]) -> None:
        """Set states dict within properties."""
        self.properties["states"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return cast(Optional[Dict[str, Any]], self.properties.get("llm_context"))

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value


@dataclass
class Item:
    """Item in the game world."""
    id: ItemId
    name: str
    description: str
    location: str  # Can be LocationId, ActorId, ItemId (container), or exit string
    _properties: Dict[str, Any] = field(default_factory=lambda: CoreFieldProtectingDict(
        {'id', 'name', 'description', 'location', 'behaviors'}
    ))
    behaviors: List[str] = field(default_factory=list)

    @property
    def properties(self) -> Dict[str, Any]:
        """Access properties dict with core field protection."""
        return self._properties

    @property
    def states(self) -> Dict[str, Any]:
        """Access states dict within properties."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return cast(Dict[str, Any], self.properties["states"])

    @states.setter
    def states(self, value: Dict[str, Any]) -> None:
        """Set states dict within properties."""
        self.properties["states"] = value

    @property
    def portable(self) -> bool:
        """Access portable from properties."""
        return bool(self.properties.get("portable", False))

    @portable.setter
    def portable(self, value: bool) -> None:
        """Set portable in properties."""
        self.properties["portable"] = value

    @property
    def pushable(self) -> bool:
        """Access pushable from properties."""
        return bool(self.properties.get("pushable", False))

    @pushable.setter
    def pushable(self, value: bool) -> None:
        """Set pushable in properties."""
        self.properties["pushable"] = value

    @property
    def provides_light(self) -> bool:
        """Access provides_light from properties."""
        return bool(self.properties.get("provides_light", False))

    @provides_light.setter
    def provides_light(self, value: bool) -> None:
        """Set provides_light in properties."""
        self.properties["provides_light"] = value

    @property
    def container(self) -> Optional[ContainerInfo]:
        """Access container from properties."""
        data = self.properties.get("container")
        return ContainerInfo(data) if data else None

    @container.setter
    def container(self, value: Optional[Dict[str, Any]]) -> None:
        """Set container in properties."""
        self.properties["container"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return cast(Optional[Dict[str, Any]], self.properties.get("llm_context"))

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
        door_props = cast(Dict[str, Any], self.properties.get("door", {}))
        return bool(door_props.get("open", False))

    @door_open.setter
    def door_open(self, value: bool) -> None:
        """Set door open state."""
        if "door" not in self.properties:
            self.properties["door"] = {}
        self.properties["door"]["open"] = value

    @property
    def door_locked(self) -> bool:
        """Get door locked state. Returns False if not a door."""
        door_props = cast(Dict[str, Any], self.properties.get("door", {}))
        return bool(door_props.get("locked", False))

    @door_locked.setter
    def door_locked(self, value: bool) -> None:
        """Set door locked state."""
        if "door" not in self.properties:
            self.properties["door"] = {}
        self.properties["door"]["locked"] = value

    @property
    def door_lock_id(self) -> Optional[str]:
        """Get door's lock ID. Returns None if not a door or no lock."""
        door_props = cast(Dict[str, Any], self.properties.get("door", {}))
        lock_id = door_props.get("lock_id")
        return cast(Optional[str], lock_id)


@dataclass
class Lock:
    """Lock mechanism."""
    id: LockId
    name: str
    description: str
    _properties: Dict[str, Any] = field(default_factory=lambda: CoreFieldProtectingDict(
        {'id', 'name', 'description', 'behaviors'}
    ))
    behaviors: List[str] = field(default_factory=list)

    @property
    def properties(self) -> Dict[str, Any]:
        """Access properties dict with core field protection."""
        return self._properties

    @property
    def opens_with(self) -> List[ItemId]:
        """Access opens_with from properties."""
        return cast(List[ItemId], self.properties.get("opens_with", []))

    @opens_with.setter
    def opens_with(self, value: List[str]) -> None:
        """Set opens_with in properties."""
        self.properties["opens_with"] = value

    @property
    def auto_unlock(self) -> bool:
        """Access auto_unlock from properties."""
        return bool(self.properties.get("auto_unlock", False))

    @auto_unlock.setter
    def auto_unlock(self, value: bool) -> None:
        """Set auto_unlock in properties."""
        self.properties["auto_unlock"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return cast(Optional[Dict[str, Any]], self.properties.get("llm_context"))

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value

    @property
    def states(self) -> Dict[str, Any]:
        """Access states dict within properties."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return cast(Dict[str, Any], self.properties["states"])

    @states.setter
    def states(self, value: Dict[str, Any]) -> None:
        """Set states dict within properties."""
        self.properties["states"] = value


@dataclass
class Part:
    """A spatial component of another entity (room, item, container, actor)."""
    id: PartId
    name: str
    part_of: str  # Parent entity ID (can be LocationId, ItemId, or ActorId)
    _properties: Dict[str, Any] = field(default_factory=lambda: CoreFieldProtectingDict(
        {'id', 'name', 'part_of', 'behaviors'}
    ))
    behaviors: List[str] = field(default_factory=list)

    @property
    def properties(self) -> Dict[str, Any]:
        """Access properties dict with core field protection."""
        return self._properties

    @property
    def states(self) -> Dict[str, Any]:
        """Access states dict within properties."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return cast(Dict[str, Any], self.properties["states"])

    @states.setter
    def states(self, value: Dict[str, Any]) -> None:
        """Set states dict within properties."""
        self.properties["states"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return cast(Optional[Dict[str, Any]], self.properties.get("llm_context"))

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value


@dataclass
class Actor:
    """Unified actor (player or NPC)."""
    id: ActorId
    name: str
    description: str
    location: LocationId
    inventory: List[ItemId] = field(default_factory=list)
    _properties: Dict[str, Any] = field(default_factory=lambda: CoreFieldProtectingDict(
        {'id', 'name', 'description', 'location', 'inventory', 'behaviors'}
    ))
    behaviors: List[str] = field(default_factory=list)

    @property
    def properties(self) -> Dict[str, Any]:
        """Access properties dict with core field protection."""
        return self._properties

    @property
    def stats(self) -> Dict[str, Any]:
        """Access stats dict within properties."""
        if "stats" not in self.properties:
            self.properties["stats"] = {}
        return cast(Dict[str, Any], self.properties["stats"])

    @stats.setter
    def stats(self, value: Dict[str, Any]) -> None:
        """Set stats dict within properties."""
        self.properties["stats"] = value

    @property
    def flags(self) -> Dict[str, Any]:
        """Access flags dict within properties."""
        if "flags" not in self.properties:
            self.properties["flags"] = {}
        return cast(Dict[str, Any], self.properties["flags"])

    @flags.setter
    def flags(self, value: Dict[str, Any]) -> None:
        """Set flags dict within properties."""
        self.properties["flags"] = value

    @property
    def states(self) -> Dict[str, Any]:
        """Access states dict within properties."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return cast(Dict[str, Any], self.properties["states"])

    @states.setter
    def states(self, value: Dict[str, Any]) -> None:
        """Set states dict within properties."""
        self.properties["states"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return cast(Optional[Dict[str, Any]], self.properties.get("llm_context"))

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value


@dataclass
class Commitment:
    """Player promise to an NPC with deadline tracking."""
    id: CommitmentId
    name: str
    description: str
    _properties: Dict[str, Any] = field(default_factory=lambda: CoreFieldProtectingDict(
        {'id', 'name', 'description', 'behaviors'}
    ))
    behaviors: List[str] = field(default_factory=list)

    @property
    def properties(self) -> Dict[str, Any]:
        """Access properties dict with core field protection."""
        return self._properties

    @property
    def states(self) -> Dict[str, Any]:
        """Access states dict within properties."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return cast(Dict[str, Any], self.properties["states"])

    @states.setter
    def states(self, value: Dict[str, Any]) -> None:
        """Set states dict within properties."""
        self.properties["states"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return cast(Optional[Dict[str, Any]], self.properties.get("llm_context"))

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value


@dataclass
class ScheduledEvent:
    """Timed event that fires when trigger turn is reached."""
    id: ScheduledEventId
    name: str
    description: str
    _properties: Dict[str, Any] = field(default_factory=lambda: CoreFieldProtectingDict(
        {'id', 'name', 'description', 'behaviors'}
    ))
    behaviors: List[str] = field(default_factory=list)

    @property
    def properties(self) -> Dict[str, Any]:
        """Access properties dict with core field protection."""
        return self._properties

    @property
    def states(self) -> Dict[str, Any]:
        """Access states dict within properties."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return cast(Dict[str, Any], self.properties["states"])

    @states.setter
    def states(self, value: Dict[str, Any]) -> None:
        """Set states dict within properties."""
        self.properties["states"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return cast(Optional[Dict[str, Any]], self.properties.get("llm_context"))

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value


@dataclass
class Gossip:
    """Information propagating between NPCs over time."""
    id: GossipId
    name: str
    description: str
    _properties: Dict[str, Any] = field(default_factory=lambda: CoreFieldProtectingDict(
        {'id', 'name', 'description', 'behaviors'}
    ))
    behaviors: List[str] = field(default_factory=list)

    @property
    def properties(self) -> Dict[str, Any]:
        """Access properties dict with core field protection."""
        return self._properties

    @property
    def states(self) -> Dict[str, Any]:
        """Access states dict within properties."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return cast(Dict[str, Any], self.properties["states"])

    @states.setter
    def states(self, value: Dict[str, Any]) -> None:
        """Set states dict within properties."""
        self.properties["states"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return cast(Optional[Dict[str, Any]], self.properties.get("llm_context"))

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value


@dataclass
class Spread:
    """Environmental effect spreading across locations over time."""
    id: SpreadId
    name: str
    description: str
    _properties: Dict[str, Any] = field(default_factory=lambda: CoreFieldProtectingDict(
        {'id', 'name', 'description', 'behaviors'}
    ))
    behaviors: List[str] = field(default_factory=list)

    @property
    def properties(self) -> Dict[str, Any]:
        """Access properties dict with core field protection."""
        return self._properties

    @property
    def states(self) -> Dict[str, Any]:
        """Access states dict within properties."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return cast(Dict[str, Any], self.properties["states"])

    @states.setter
    def states(self, value: Dict[str, Any]) -> None:
        """Set states dict within properties."""
        self.properties["states"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return cast(Optional[Dict[str, Any]], self.properties.get("llm_context"))

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value


# Entity type alias - union of all game entities
Entity = Location | Item | Lock | Part | Actor | ExitDescriptor | Commitment | ScheduledEvent | Gossip | Spread
"""Union type for any game entity.

Entities share a common structure:
- id: Entity-specific typed ID (LocationId, ItemId, etc.)
- name: Display name
- properties: Dict for extensible properties
- behaviors: List of behavior module paths
- states: Dict within properties for state flags

Use this type when a function can accept any entity type.
"""


@dataclass
class GameState:
    """Complete game state."""
    metadata: Metadata
    locations: List[Location] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    locks: List[Lock] = field(default_factory=list)
    actors: Dict[ActorId, Actor] = field(default_factory=dict)
    parts: List[Part] = field(default_factory=list)
    commitments: List[Commitment] = field(default_factory=list)
    scheduled_events: List[ScheduledEvent] = field(default_factory=list)
    gossip: List[Gossip] = field(default_factory=list)
    spreads: List[Spread] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)
    turn_count: int = 0

    def get_actor(self, actor_id: ActorId) -> Actor:
        """Get actor by ID."""
        actor = self.actors.get(actor_id)
        if actor:
            return actor
        raise KeyError(f"Actor not found: {actor_id}")

    def get_item(self, item_id: ItemId) -> Item:
        """Get item by ID."""
        for item in self.items:
            if item.id == item_id:
                return item
        raise KeyError(f"Item not found: {item_id}")

    def get_location(self, location_id: LocationId) -> Location:
        """Get location by ID."""
        for loc in self.locations:
            if loc.id == location_id:
                return loc
        raise KeyError(f"Location not found: {location_id}")

    def get_lock(self, lock_id: LockId) -> Lock:
        """Get lock by ID."""
        for lock in self.locks:
            if lock.id == lock_id:
                return lock
        raise KeyError(f"Lock not found: {lock_id}")

    def get_commitment(self, commitment_id: CommitmentId) -> Commitment:
        """Get commitment by ID."""
        for commitment in self.commitments:
            if commitment.id == commitment_id:
                return commitment
        raise KeyError(f"Commitment not found: {commitment_id}")

    def get_scheduled_event(self, event_id: ScheduledEventId) -> ScheduledEvent:
        """Get scheduled event by ID."""
        for event in self.scheduled_events:
            if event.id == event_id:
                return event
        raise KeyError(f"Scheduled event not found: {event_id}")

    def get_gossip(self, gossip_id: GossipId) -> Gossip:
        """Get gossip by ID."""
        for gossip_item in self.gossip:
            if gossip_item.id == gossip_id:
                return gossip_item
        raise KeyError(f"Gossip not found: {gossip_id}")

    def get_spread(self, spread_id: SpreadId) -> Spread:
        """Get spread by ID."""
        for spread in self.spreads:
            if spread.id == spread_id:
                return spread
        raise KeyError(f"Spread not found: {spread_id}")

    def move_item(self, item_id: ItemId, to_actor: Optional[ActorId] = None,
                  to_location: Optional[LocationId] = None, to_container: Optional[ItemId] = None) -> None:
        """Move item to new location.

        Args:
            item_id: The item to move
            to_actor: Actor ID to move item to (adds to their inventory)
            to_location: Location ID to move item to
            to_container: Container item ID to move item into
        """
        item = self.get_item(item_id)
        old_location = item.location

        # Remove from old location - check if it's in any actor's inventory
        for actor in self.actors.values():
            if item_id in actor.inventory:
                actor.inventory.remove(item_id)
                break
        else:
            # Check if it's in a location
            for loc in self.locations:
                if item_id in loc.items:
                    loc.items.remove(item_id)
                    break

        # Add to new location
        if to_actor:
            target_actor = self.actors.get(to_actor)
            if target_actor:
                item.location = to_actor
                if item_id not in target_actor.inventory:
                    target_actor.inventory.append(item_id)
        elif to_location:
            item.location = to_location
            loc = self.get_location(to_location)
            if item_id not in loc.items:
                loc.items.append(item_id)
        elif to_container:
            item.location = to_container

    def set_actor_location(self, location_id: LocationId, actor_id: ActorId = ActorId("player")) -> None:
        """Set an actor's current location.

        Args:
            location_id: The location to move the actor to
            actor_id: The actor to move (defaults to "player")
        """
        actor = self.actors.get(actor_id)
        if actor:
            actor.location = location_id

    def set_actor_flag(self, flag_name: str, value: Any, actor_id: ActorId = ActorId("player")) -> None:
        """Set a flag on an actor.

        Flags are stored in actor.properties["flags"] and persist across saves.
        Used for tracking game progression, quest states, etc.

        Args:
            flag_name: Name of the flag to set
            value: Value to set
            actor_id: The actor to set the flag on (defaults to "player")
        """
        actor = self.actors.get(actor_id)
        if actor:
            if "flags" not in actor.properties:
                actor.properties["flags"] = {}
            actor.properties["flags"][flag_name] = value

    def get_actor_flag(self, flag_name: str, default: Any = None, actor_id: ActorId = ActorId("player")) -> Any:
        """Get a flag value from an actor.

        Args:
            flag_name: Name of the flag to get
            default: Default value if flag not set
            actor_id: The actor to get the flag from (defaults to "player")

        Returns:
            The flag value, or default if not set
        """
        actor = self.actors.get(actor_id)
        if actor:
            flags = actor.properties.get("flags", {})
            return flags.get(flag_name, default)
        return default

    def increment_turn(self) -> int:
        """Increment turn counter and return new value.

        Called after each successful player command, before turn phases fire.
        """
        self.turn_count += 1
        return self.turn_count

    def build_id_registry(self) -> Dict[str, str]:
        """Build registry of all entity IDs to their types.

        All actors (including the one with id "player") are registered as "actor".
        """
        registry: Dict[str, str] = {}

        for loc in self.locations:
            registry[loc.id] = "location"
        for item in self.items:
            if item.is_door:
                registry[item.id] = "door_item"
            else:
                registry[item.id] = "item"
        for lock in self.locks:
            registry[lock.id] = "lock"
        for actor_id in self.actors:
            registry[actor_id] = "actor"

        return registry


# Parsers
def _parse_exit(direction: str, raw: Dict[str, Any], location_id: str = "") -> ExitDescriptor:
    """Parse exit descriptor from JSON dict.

    Args:
        direction: The direction key (e.g., "north", "up")
        raw: The exit data dict
        location_id: The parent location's ID (for synthesized exit id)
    """
    core_fields = {'type', 'to', 'door_id', 'name', 'description', 'passage', 'door_at', 'behaviors'}

    to_loc = raw.get('to')
    door = raw.get('door_id')
    door_at = raw.get('door_at')

    return ExitDescriptor(
        type=raw.get('type', 'open'),
        to=LocationId(to_loc) if to_loc else None,
        door_id=ItemId(door) if door else None,
        name=raw.get('name', direction),  # Default to direction if no name
        description=raw.get('description', ''),
        passage=raw.get('passage'),
        door_at=LocationId(door_at) if door_at else None,
        _properties=CoreFieldProtectingDict(core_fields, _parse_properties(raw, core_fields)),
        behaviors=_parse_behaviors(raw.get('behaviors', []), f"exit:{location_id}:{direction}"),
        _direction=direction,
        _location_id=LocationId(location_id) if location_id else LocationId("")
    )


def _parse_location(raw: Dict[str, Any]) -> Location:
    """Parse location from JSON dict."""
    # Note: 'npcs' is included in core_fields to filter it from properties
    # but it's no longer stored on Location (actors track their own location)
    core_fields = {'id', 'name', 'description', 'exits', 'items', 'npcs', 'behaviors'}

    location_id = raw['id']

    # Parse exits - pass location_id for synthesized exit ids
    exits = {}
    for direction, exit_data in raw.get('exits', {}).items():
        exits[direction] = _parse_exit(direction, exit_data, location_id)

    behaviors = _parse_behaviors(raw.get('behaviors', []), f"location:{location_id}")
    items = raw.get('items', [])

    return Location(
        id=LocationId(location_id),
        name=raw.get('name', ''),
        description=raw.get('description', ''),
        exits=exits,
        items=[ItemId(i) for i in items],
        _properties=CoreFieldProtectingDict(core_fields, _parse_properties(raw, core_fields)),
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

    behaviors = _parse_behaviors(raw.get('behaviors', []), f"item:{raw.get('id', '')}")

    return Item(
        id=ItemId(raw['id']),
        name=raw.get('name', ''),
        description=raw.get('description', ''),
        location=raw.get('location', ''),  # Keep as str - can be various ID types
        _properties=CoreFieldProtectingDict(core_fields, _parse_properties(raw, core_fields)),
        behaviors=behaviors
    )


def _parse_lock(raw: Dict[str, Any]) -> Lock:
    """Parse lock from JSON dict."""
    core_fields = {'id', 'name', 'description', 'properties', 'behaviors'}

    lock_id = raw['id']
    return Lock(
        id=LockId(lock_id),
        name=raw.get('name', lock_id),  # Default to id if no name
        description=raw.get('description', ''),
        _properties=CoreFieldProtectingDict(core_fields, _parse_properties(raw, core_fields)),
        behaviors=_parse_behaviors(raw.get('behaviors', []), f"lock:{lock_id}")
    )


def _parse_actor(raw: Dict[str, Any], actor_id: Optional[str] = None) -> Actor:
    """Parse Actor from JSON dict.

    Args:
        raw: Actor data from JSON
        actor_id: Optional ID override (used when parsing from actors dict where key is the ID)
    """
    core_fields = {'id', 'name', 'description', 'location', 'inventory', 'behaviors'}

    # Use actor_id if provided (from dict key), otherwise require id in raw data
    effective_id = actor_id or raw['id']

    # Default name: use provided name, or "Adventurer" for player, or ID for others
    # "player" is a prohibited name, so we must use a different default
    default_name = "Adventurer" if effective_id == "player" else effective_id
    location = raw.get('location', '')
    inventory = raw.get('inventory', [])
    return Actor(
        id=ActorId(effective_id),
        name=raw.get('name', default_name),
        description=raw.get('description', ''),
        location=LocationId(location) if location else LocationId(""),
        inventory=[ItemId(i) for i in inventory],
        _properties=CoreFieldProtectingDict(core_fields, _parse_properties(raw, core_fields)),
        behaviors=_parse_behaviors(raw.get('behaviors', []), f"actor:{effective_id}")
    )


def _parse_commitment(raw: Dict[str, Any]) -> Commitment:
    """Parse commitment from JSON dict."""
    core_fields = {'id', 'name', 'description', 'properties', 'behaviors'}

    commitment_id = raw['id']
    return Commitment(
        id=CommitmentId(commitment_id),
        name=raw.get('name', commitment_id),  # Default to id if no name
        description=raw.get('description', ''),
        _properties=CoreFieldProtectingDict(core_fields, _parse_properties(raw, core_fields)),
        behaviors=_parse_behaviors(raw.get('behaviors', []), f"commitment:{commitment_id}")
    )


def _parse_scheduled_event(raw: Dict[str, Any]) -> ScheduledEvent:
    """Parse scheduled event from JSON dict."""
    core_fields = {'id', 'name', 'description', 'properties', 'behaviors'}

    event_id = raw['id']
    return ScheduledEvent(
        id=ScheduledEventId(event_id),
        name=raw.get('name', event_id),  # Default to id if no name
        description=raw.get('description', ''),
        _properties=CoreFieldProtectingDict(core_fields, _parse_properties(raw, core_fields)),
        behaviors=_parse_behaviors(raw.get('behaviors', []), f"scheduled_event:{event_id}")
    )


def _parse_gossip(raw: Dict[str, Any]) -> Gossip:
    """Parse gossip from JSON dict."""
    core_fields = {'id', 'name', 'description', 'properties', 'behaviors'}

    gossip_id = raw['id']
    return Gossip(
        id=GossipId(gossip_id),
        name=raw.get('name', gossip_id),  # Default to id if no name
        description=raw.get('description', ''),
        _properties=CoreFieldProtectingDict(core_fields, _parse_properties(raw, core_fields)),
        behaviors=_parse_behaviors(raw.get('behaviors', []), f"gossip:{gossip_id}")
    )


def _parse_spread(raw: Dict[str, Any]) -> Spread:
    """Parse spread from JSON dict."""
    core_fields = {'id', 'name', 'description', 'properties', 'behaviors'}

    spread_id = raw['id']
    return Spread(
        id=SpreadId(spread_id),
        name=raw.get('name', spread_id),  # Default to id if no name
        description=raw.get('description', ''),
        _properties=CoreFieldProtectingDict(core_fields, _parse_properties(raw, core_fields)),
        behaviors=_parse_behaviors(raw.get('behaviors', []), f"spread:{spread_id}")
    )


def _parse_metadata(raw: Dict[str, Any]) -> Metadata:
    """Parse metadata from JSON dict."""
    return Metadata(
        title=raw.get('title', ''),
        version=raw.get('version', ''),
        description=raw.get('description', ''),
        start_location=raw.get('start_location', ''),
        author=raw.get('author', ''),
        extra_turn_phases=raw.get('extra_turn_phases', [])
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

    # Parse metadata and enforce minimum version
    metadata = _parse_metadata(data.get('metadata', {}))
    if metadata.version and metadata.version < "0.04":
        raise ValueError(
            f"game_state version {metadata.version} is unsupported; "
            "please migrate to version 0.04 or later."
        )

    # Parse locations
    locations = [_parse_location(loc) for loc in data.get('locations', [])]

    # Parse items (doors are stored as items with door property)
    items = [_parse_item(item) for item in data.get('items', [])]

    # Parse locks
    locks = [_parse_lock(lock) for lock in data.get('locks', [])]

    # Parse parts
    parts = []
    for part_data in data.get('parts', []):
        core_fields = {'id', 'name', 'part_of', 'behaviors'}
        part = Part(
            id=PartId(part_data['id']),
            name=part_data['name'],
            part_of=part_data['part_of'],  # Keep as str - can be various ID types
            _properties=CoreFieldProtectingDict(core_fields, part_data.get('properties', {})),
            behaviors=_parse_behaviors(part_data.get('behaviors', []), f"part:{part_data.get('id', '')}")
        )
        parts.append(part)

    # Parse actors from actors dict (required format - no legacy support)
    actors: Dict[ActorId, Actor] = {}

    if 'actors' not in data:
        raise ValueError("game_state.json must have 'actors' dict")

    for actor_id, actor_data in data['actors'].items():
        actors[ActorId(actor_id)] = _parse_actor(actor_data, actor_id=actor_id)

    if ActorId('player') not in actors:
        raise ValueError("actors dict must contain 'player' entry")

    # Parse virtual entities
    commitments = [_parse_commitment(c) for c in data.get('commitments', [])]
    scheduled_events = [_parse_scheduled_event(e) for e in data.get('scheduled_events', [])]
    gossip = [_parse_gossip(g) for g in data.get('gossip', [])]
    spreads = [_parse_spread(s) for s in data.get('spreads', [])]

    state = GameState(
        metadata=metadata,
        locations=locations,
        items=items,
        locks=locks,
        actors=actors,
        parts=parts,
        commitments=commitments,
        scheduled_events=scheduled_events,
        gossip=gossip,
        spreads=spreads,
        turn_count=data.get('turn_count', 0),
        extra=data.get('extra', {})
    )

    # Validate after loading
    from src.validators import validate_game_state
    validate_game_state(state)

    return state


# Serializers
def _serialize_entity(
    entity: Any,
    required_fields: List[str],
    optional_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Generic entity serializer.

    Args:
        entity: Any dataclass with properties and behaviors attributes
        required_fields: Fields to always include (e.g., ['id', 'name', 'description'])
        optional_fields: Fields to include only if truthy (e.g., ['name', 'description'] for Lock)

    Returns:
        Dict with fields, merged properties, and behaviors (if present)
    """
    result: Dict[str, Any] = {}

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
        optional_fields=['to', 'door_id', 'name', 'description', 'passage', 'door_at']
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
    return _serialize_entity(lock, required_fields=['id', 'name', 'description'])


def _serialize_actor(actor: Actor) -> Dict[str, Any]:
    """Serialize Actor to dict."""
    return _serialize_entity(actor, required_fields=['id', 'name', 'description', 'location', 'inventory'])


def _serialize_commitment(commitment: Commitment) -> Dict[str, Any]:
    """Serialize commitment to dict."""
    return _serialize_entity(commitment, required_fields=['id', 'name', 'description'])


def _serialize_scheduled_event(event: ScheduledEvent) -> Dict[str, Any]:
    """Serialize scheduled event to dict."""
    return _serialize_entity(event, required_fields=['id', 'name', 'description'])


def _serialize_gossip(gossip: Gossip) -> Dict[str, Any]:
    """Serialize gossip to dict."""
    return _serialize_entity(gossip, required_fields=['id', 'name', 'description'])


def _serialize_spread(spread: Spread) -> Dict[str, Any]:
    """Serialize spread to dict."""
    return _serialize_entity(spread, required_fields=['id', 'name', 'description'])


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
    result: Dict[str, Any] = {
        'metadata': _serialize_metadata(state.metadata),
        'locations': [_serialize_location(loc) for loc in state.locations],
        'items': [_serialize_item(item) for item in state.items],
        'locks': [_serialize_lock(lock) for lock in state.locks],
        'actors': {actor_id: _serialize_actor(actor) for actor_id, actor in state.actors.items()}
    }

    # Include virtual entities if present
    if state.commitments:
        result['commitments'] = [_serialize_commitment(c) for c in state.commitments]
    if state.scheduled_events:
        result['scheduled_events'] = [_serialize_scheduled_event(e) for e in state.scheduled_events]
    if state.gossip:
        result['gossip'] = [_serialize_gossip(g) for g in state.gossip]
    if state.spreads:
        result['spreads'] = [_serialize_spread(s) for s in state.spreads]

    # Only include turn_count if non-zero (for cleaner save files)
    if state.turn_count > 0:
        result['turn_count'] = state.turn_count

    return result


def save_game_state(state: GameState, path: Union[str, Path]) -> None:
    """Save game state to file."""
    data = game_state_to_dict(state)

    path = Path(path)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
