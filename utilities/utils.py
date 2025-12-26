from __future__ import annotations

"""
Shared utility functions for behavior modules.

This module contains helper functions used by command handlers and query handlers.
Functions in this module should be generic and reusable across different behavior modules.

IMPORTANT: All utility functions that operate on entities should accept an actor_id
parameter and use it correctly. Never hardcode "player" - use the actor_id variable.
"""
from typing import Optional, List, Tuple, Dict, Any, Union, TYPE_CHECKING, cast, Callable

from src.state_accessor import EventResult
from src.types import ActorId, LocationId, LockId, HookName
from src.word_entry import WordEntry
from src.hooks import VISIBILITY_CHECK
from utilities.entity_serializer import serialize_for_handler_result

if TYPE_CHECKING:
    from src.state_accessor import StateAccessor
    from src.state_manager import Actor, Item, Location, ExitDescriptor, Lock
    from src.behavior_manager import BehaviorManager


EntityLike = Union["Item", "Actor", "ExitDescriptor", "Lock"]


def _extract_word(value: Optional[Union[str, WordEntry]]) -> Optional[str]:
    """Extract string from WordEntry or return string as-is."""
    if value is None:
        return None
    if hasattr(value, 'word'):
        return value.word
    return value


def find_actor_by_name(
    accessor: "StateAccessor",
    name: WordEntry,
    actor_id: ActorId
) -> Optional["Actor"]:
    """
    Find an actor accessible to the examining actor.

    Handles special cases:
    - "self" (with synonyms "me"/"myself" via WordEntry) -> returns the acting actor
    - Other names -> searches actors in same location

    The name parameter is a WordEntry from the parser, which provides
    synonym information. When the parser sees "me" or "myself", it returns
    the canonical "self" WordEntry with synonyms, so name_matches will work.

    Args:
        accessor: StateAccessor instance
        name: Actor name as WordEntry from parser
        actor_id: ID of the actor doing the examining

    Returns:
        Actor if found, None otherwise
    """
    actor = accessor.get_actor(actor_id)  # Raises KeyError if not found

    # Handle self-reference using name_matches
    # Parser returns canonical WordEntry with synonyms, so name_matches("self", "self") works
    if name_matches(name, "self"):
        return actor

    # Search actors in same location
    location = accessor.get_current_location(actor_id)
    if not location:
        return None

    for other_actor in accessor.get_actors_in_location(location.id):
        # Don't return self when searching by name
        if other_actor.id == actor_id:
            continue
        if name_matches(name, other_actor.name):
            return other_actor

    return None


def format_inventory(
    accessor: "StateAccessor",
    actor: "Actor",
    for_self: bool = True,
    observer_actor_id: Optional[ActorId] = None
) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    """
    Format an actor's inventory for display.

    When for_self=True (examining yourself), shows all inventory items.
    When for_self=False (examining another actor), only shows equipped items.

    Args:
        accessor: StateAccessor instance
        actor: Actor whose inventory to format
        for_self: If True, use "You are carrying" and show all items;
                  if False, use "Carrying" and only show equipped items
        observer_actor_id: Optional actor ID of the observer (for perspective context)

    Returns:
        Tuple of (message string or None if empty, list of serialized items)
    """
    if not actor.inventory:
        return None, []

    item_names = []
    items_data = []
    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item:
            # When examining others, only show equipped items
            if not for_self and not item.states.get("equipped", False):
                continue
            item_names.append(item.name)
            items_data.append(serialize_for_handler_result(item, accessor, observer_actor_id))

    if not item_names:
        return None, []

    prefix = "You are carrying" if for_self else "Carrying"
    return f"{prefix}: {', '.join(item_names)}", items_data


def name_matches(
    search_term: WordEntry,
    target_name: str,
    match_in_phrase: bool = True
) -> bool:
    """
    Check if search_term matches target_name, considering vocabulary synonyms.

    This function provides uniform name matching across all entity finders,
    using the vocabulary's synonym definitions to match player input against
    entity names.

    IMPORTANT: search_term MUST be a WordEntry, not a string. With ActionDict
    enforcement, action.get("object") already returns WordEntry.

    Args:
        search_term: WordEntry with canonical word and synonyms (NOT a string)
        target_name: The entity's name field to match against
        match_in_phrase: If True (default), also match if any search word appears
                        as a complete word within target_name (for multi-word
                        names like "spiral staircase" or "Gate Guard Harmon")

    Returns:
        True if any form of search_term matches target_name

    Examples:
        >>> entry = WordEntry(word="stairs", synonyms=["staircase", "steps"])
        >>> name_matches(entry, "stairs")  # Exact match
        True
        >>> name_matches(entry, "staircase")  # Synonym match
        True
        >>> name_matches(entry, "spiral staircase")  # Phrase match (default)
        True  # "staircase" is a word in the phrase
        >>> name_matches(entry, "spiral staircase", match_in_phrase=False)
        False  # Exact match only
    """
    # Extract all words to check (canonical + synonyms)
    match_words = [search_term.word] + search_term.synonyms

    target_lower = target_name.lower()
    target_words = target_lower.split()

    for word in match_words:
        word_lower = word.lower()
        # Exact match (entire name)
        if target_lower == word_lower:
            return True
        # Word appears as complete word in multi-word name
        if match_in_phrase and word_lower in target_words:
            return True

    return False


def is_observable(
    entity: EntityLike,
    accessor: "StateAccessor",
    behavior_manager: Optional["BehaviorManager"],
    actor_id: ActorId,
    method: str
) -> Tuple[bool, Optional[str]]:
    """
    Check if an entity is observable.

    Checks the entity's hidden state and invokes any on_observe behaviors.
    The core hidden check happens first, but custom behaviors can override it
    (e.g., to reveal a hidden item when searched).

    For entities without on_observe behaviors:
    - Returns (False, None) if states.hidden is True
    - Returns (True, None) otherwise

    For entities with on_observe behaviors:
    - Behaviors are invoked with context {"actor_id": actor_id, "method": method}
    - Behaviors can modify the entity's hidden state
    - The behavior's EventResult determines visibility

    Args:
        entity: Entity to check (Item, Actor, ExitDescriptor, etc.)
        accessor: StateAccessor instance
        behavior_manager: BehaviorManager instance
        actor_id: Who is observing
        method: The verb/method of observation (e.g., "look", "examine", "search")

    Returns:
        Tuple of (is_visible, message)
    """
    # Get the entity's states dict
    states = _get_entity_states(entity)

    # If entity has behaviors and visibility_check hook is registered, invoke it
    # Behaviors can override the hidden check (e.g., reveal on search)
    event = None
    if behavior_manager is not None:
        event = behavior_manager.get_event_for_hook(HookName(VISIBILITY_CHECK))

    if event and behavior_manager is not None and hasattr(entity, 'behaviors') and entity.behaviors:
        context = {"actor_id": actor_id, "method": method}
        result = behavior_manager.invoke_behavior(entity, event, accessor, context)

        if result is not None:
            return (result.allow, result.feedback)

    # No behavior or behavior didn't handle visibility check
    # Use core hidden state check
    if states.get("hidden", False):
        return (False, None)

    return (True, None)


def _get_entity_states(entity: EntityLike) -> Dict[str, Any]:
    """
    Get the states dict from an entity.

    Handles different entity types:
    - Entities with a 'states' property (Item, ExitDescriptor) return entity.states
    - Entities with properties dict return properties.get("states", {})

    Args:
        entity: Entity to get states from

    Returns:
        Dict of states, empty dict if none found
    """
    # Try the states property first (Item, ExitDescriptor have this)
    if hasattr(entity, 'states'):
        try:
            return entity.states
        except Exception:
            pass

    # Fall back to properties.states
    if hasattr(entity, 'properties') and isinstance(entity.properties, dict):
        states = entity.properties.get("states", {})
        if isinstance(states, dict):
            return states

    return {}


def find_accessible_item(
    accessor: "StateAccessor",
    name: WordEntry,
    actor_id: ActorId,
    adjective: Optional[Union[str, WordEntry]] = None
) -> Optional["Item"]:
    """
    Find an item that is accessible to the actor, optionally filtered by adjective.

    Search order (first match wins):
    1. Items in actor's current location (includes door items visible via exits)
    2. Items in actor's inventory
    3. Items on surface containers in location
    4. Items in open enclosed containers in location

    Door items are included if they are visible in the location (via exit reference
    or direct location). Hidden items are excluded.

    If adjective is provided, only returns items whose id or description
    contains the adjective. If no adjective or empty adjective, returns
    first matching item by name.

    IMPORTANT: Do not hardcode 'player' - use the actor_id parameter.

    Args:
        accessor: StateAccessor instance
        name: Item name to search for (WordEntry with synonyms or plain string)
        actor_id: ID of the actor looking for the item
        adjective: Optional adjective to filter by (or None/empty for first match)

    Returns:
        Item if found, None otherwise
    """
    actor = accessor.get_actor(actor_id)  # Raises KeyError if not found

    # Get current location
    location = accessor.get_current_location(actor_id)
    if not location:
        return None

    adjective_str = _extract_word(adjective)
    has_adjective = adjective_str and adjective_str.strip()

    # Collect all accessible items matching name
    matching_items = []

    # Check all visible items in location (uses _is_item_visible_in_location)
    # This includes door items visible through exits and excludes hidden items
    for item in accessor.game_state.items:
        if _is_item_visible_in_location(item, location.id, accessor, actor_id):
            if name_matches(name, item.name):
                matching_items.append(item)

    # Check inventory (inventory items use observability check)
    for item_id in actor.inventory:
        inventory_item = accessor.get_item(item_id)
        if inventory_item and name_matches(name, inventory_item.name):
            # Check observability even in inventory
            visible, _ = is_observable(
                inventory_item, accessor, accessor.behavior_manager,
                actor_id=actor_id, method="look"
            )
            if visible:
                matching_items.append(inventory_item)

    # Check equipped items of other visible actors in same location
    # This allows examining items that NPCs are visibly carrying
    for other_actor in accessor.get_actors_in_location(location.id):
        if other_actor.id == actor_id:
            continue  # Already checked player's inventory above
        # Check if actor is visible
        actor_visible, _ = is_observable(
            other_actor, accessor, accessor.behavior_manager,
            actor_id=actor_id, method="look"
        )
        if actor_visible:
            for item_id in other_actor.inventory:
                carried_item = accessor.get_item(item_id)
                # Only include equipped items from other actors
                if carried_item and carried_item.states.get("equipped", False) and name_matches(name, carried_item.name):
                    matching_items.append(carried_item)

    # Check containers in location
    # Get visible items that are containers
    visible_items = [item for item in accessor.game_state.items
                     if _is_item_visible_in_location(item, location.id, accessor, actor_id)]
    for container in visible_items:
        container_info = container.properties.get("container", {})
        if not container_info:
            continue

        is_surface = container_info.get("is_surface", False)
        is_open = container_info.get("open", False)

        # Surface containers are always accessible
        # Enclosed containers must be open
        if is_surface or is_open:
            # Get items inside this container (check observability)
            for item in accessor.game_state.items:
                if item.location == container.id and name_matches(name, item.name):
                    visible, _ = is_observable(
                        item, accessor, accessor.behavior_manager,
                        actor_id=actor_id, method="look"
                    )
                    if visible:
                        matching_items.append(item)

    # If no matches, return None
    if not matching_items:
        return None

    # Sort so non-door items come before door items
    # This ensures regular items are preferred when names match
    matching_items.sort(key=lambda item: item.is_door)

    # If no adjective, return first match (preferring non-door items)
    if not has_adjective:
        return matching_items[0]

    # Filter by adjective
    assert adjective_str is not None  # Guaranteed by has_adjective check
    for item in matching_items:
        if _matches_adjective(adjective_str, item):
            return item

    # No match with adjective
    return None


def find_item_in_inventory(accessor: "StateAccessor", name: WordEntry, actor_id: ActorId) -> Optional["Item"]:
    """
    Find an item in the actor's inventory.

    IMPORTANT: Do not hardcode 'player' - use the actor_id parameter.

    Args:
        accessor: StateAccessor instance
        name: Item name to search for (WordEntry with synonyms or plain string)
        actor_id: ID of the actor whose inventory to search

    Returns:
        Item if found in inventory, None otherwise
    """
    actor = accessor.get_actor(actor_id)  # Raises KeyError if not found

    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item and name_matches(name, item.name):
            return item

    return None


def find_container_by_name(accessor: "StateAccessor", name: WordEntry, location_id: str) -> Optional["Item"]:
    """
    Find a container item in a location.

    A container is an item with properties.is_container == True.

    Args:
        accessor: StateAccessor instance
        name: Container name to search for (WordEntry with synonyms or plain string)
        location_id: ID of the location to search in

    Returns:
        Item if found and is a container, None otherwise
    """
    items = accessor.get_items_in_location(LocationId(location_id))

    for item in items:
        if name_matches(name, item.name):
            # Check if it's a container
            if hasattr(item, 'properties') and isinstance(item.properties, dict):
                if item.properties.get('is_container'):
                    return item

    return None


def actor_has_key_for_door(accessor: "StateAccessor", actor_id: ActorId, door: "Item") -> bool:
    """
    Check if actor has a key that can unlock the door.

    IMPORTANT: Do not hardcode 'player' - use the actor_id parameter.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of the actor to check
        door: Door Item to check

    Returns:
        True if actor has a key for the door, False otherwise
    """
    lock_id = door.door_lock_id

    if not lock_id:
        return False

    lock = accessor.get_lock(LockId(lock_id))
    if not lock:
        return False

    # Get list of keys that open this lock
    if not hasattr(lock, 'opens_with'):
        return False

    key_ids = lock.opens_with
    if not key_ids:
        return False

    # Check if actor has any of these keys
    actor = accessor.get_actor(actor_id)  # Raises KeyError if not found

    for key_id in key_ids:
        if key_id in actor.inventory:
            return True

    return False


def get_visible_items_in_location(accessor: "StateAccessor", location_id: str, actor_id: ActorId) -> List["Item"]:
    """
    Get all visible items in a location.

    Currently returns all items in the location. Future versions may
    implement visibility rules.

    Args:
        accessor: StateAccessor instance
        location_id: ID of the location
        actor_id: ID of the actor viewing (for future visibility rules)

    Returns:
        List of visible Item objects
    """
    return accessor.get_items_in_location(LocationId(location_id))


def get_visible_actors_in_location(accessor: "StateAccessor", location_id: str, actor_id: ActorId) -> List["Actor"]:
    """
    Get all visible actors in a location, excluding the viewing actor.

    IMPORTANT: Excludes the actor specified by actor_id from the results.
    Also excludes hidden actors (uses is_observable() check).

    Args:
        accessor: StateAccessor instance
        location_id: ID of the location
        actor_id: ID of the actor viewing (excluded from results)

    Returns:
        List of visible Actor objects (excluding actor_id and hidden actors)
    """
    all_actors = accessor.get_actors_in_location(LocationId(location_id))

    # Filter out the viewing actor and hidden actors
    visible_actors = []
    for actor in all_actors:
        if actor.id == actor_id:
            continue
        visible, _ = is_observable(
            actor, accessor, accessor.behavior_manager,
            actor_id=actor_id, method="look"
        )
        if visible:
            visible_actors.append(actor)
    return visible_actors


def get_doors_in_location(accessor: "StateAccessor", location_id: str, actor_id: ActorId) -> List["Item"]:
    """
    Get all doors visible in a location.

    Returns door items that are visible in this location (via exit reference or
    direct location).

    Args:
        accessor: StateAccessor instance
        location_id: ID of the location
        actor_id: ID of the actor viewing (for future visibility rules)

    Returns:
        List of door Item objects
    """
    doors_in_location = []

    # Get door items visible in this location
    for item in accessor.game_state.items:
        if item.is_door and _is_item_visible_in_location(item, location_id, accessor, actor_id):
            doors_in_location.append(item)

    return doors_in_location


def _matches_adjective(adjective: str, entity: "Item") -> bool:
    """
    Check if an adjective matches an entity's id, description, or state properties.

    Matching is case-insensitive and looks for the adjective as a word
    in the entity's id or description. For door items and containers, also
    checks state properties: "locked", "unlocked", "open", "closed".

    Args:
        adjective: The adjective to match
        entity: Entity with id and description attributes

    Returns:
        True if adjective matches, False otherwise
    """
    adj_lower = adjective.lower()

    # For door items, check state-based adjectives first
    if hasattr(entity, 'is_door') and entity.is_door:
        if adj_lower == "locked" and entity.door_locked:
            return True
        if adj_lower == "unlocked" and not entity.door_locked:
            return True
        if adj_lower == "open" and entity.door_open:
            return True
        if adj_lower == "closed" and not entity.door_open:
            return True

    # For container items, check container state
    if hasattr(entity, 'container') and entity.container:
        if adj_lower == "open" and entity.container.open:
            return True
        if adj_lower == "closed" and not entity.container.open:
            return True

    # Check if adjective appears in ID
    if adj_lower in entity.id.lower():
        return True

    # Check if adjective appears in description
    description = getattr(entity, 'description', '') or ''
    if adj_lower in description.lower():
        return True

    return False


def find_container_with_adjective(
    accessor: "StateAccessor", name: WordEntry, adjective: Optional[str], location_id: str
) -> Optional["Item"]:
    """
    Find a container item in a location, optionally filtered by adjective.

    A container is an item with properties.container dict defined.

    Args:
        accessor: StateAccessor instance
        name: Container name to search for (WordEntry with synonyms or plain string)
        adjective: Optional adjective to filter by
        location_id: ID of the location to search in

    Returns:
        Item if found and is a container, None otherwise
    """
    adjective_str = _extract_word(adjective)
    has_adjective = adjective_str and adjective_str.strip()

    # Collect all containers in location matching name
    matching_containers = []

    items = accessor.get_items_in_location(LocationId(location_id))
    for item in items:
        if not name_matches(name, item.name):
            continue

        # Check if it's a container
        container_info = item.properties.get("container", {})
        if container_info:
            matching_containers.append(item)

    # If no matches, return None
    if not matching_containers:
        return None

    # If no adjective, return first match
    if not has_adjective:
        return matching_containers[0]

    # Filter by adjective
    assert adjective_str is not None  # Guaranteed by has_adjective check
    for container in matching_containers:
        if _matches_adjective(adjective_str, container):
            return container

    # No match with adjective
    return None


def find_item_in_container(
    accessor: "StateAccessor", item_name: WordEntry, container_id: str, adjective: Optional[str] = None
) -> Optional["Item"]:
    """
    Find an item inside a specific container.

    Args:
        accessor: StateAccessor instance
        item_name: Name of item to find (WordEntry with synonyms or plain string)
        container_id: ID of the container to search in
        adjective: Optional adjective to filter items by

    Returns:
        Item if found in container, None otherwise
    """
    adjective_str = _extract_word(adjective)
    has_adjective = adjective_str and adjective_str.strip()

    # Get items in this container
    items_in_container = accessor.get_items_in_location(LocationId(container_id))

    matching_items = []
    for item in items_in_container:
        if name_matches(item_name, item.name):
            matching_items.append(item)

    if not matching_items:
        return None

    if not has_adjective:
        return matching_items[0]

    # Filter by adjective
    assert adjective_str is not None  # Guaranteed by has_adjective check
    for item in matching_items:
        if _matches_adjective(adjective_str, item):
            return item

    return None


def _get_door_state(door: "Item") -> Tuple[bool, bool, Optional[str]]:
    """
    Get door state (open, locked, lock_id) from a door Item.

    Returns:
        tuple: (is_open, is_locked, lock_id)
    """
    return (door.door_open, door.door_locked, door.door_lock_id)


# Type for door selection strategy
DoorStrategy = Callable[["Item", "StateAccessor", ActorId], bool]


def _unlockable_with_key(door: "Item", accessor: "StateAccessor", actor_id: ActorId) -> bool:
    """Door is locked and actor has key."""
    _, is_locked, _ = _get_door_state(door)
    return is_locked and actor_has_key_for_door(accessor, actor_id, door)


def _locked(door: "Item", accessor: "StateAccessor", actor_id: ActorId) -> bool:
    """Door is locked."""
    _, is_locked, _ = _get_door_state(door)
    return is_locked


def _closed_unlocked(door: "Item", accessor: "StateAccessor", actor_id: ActorId) -> bool:
    """Door is closed and unlocked (immediately actionable for opening)."""
    is_open, is_locked, _ = _get_door_state(door)
    return not is_open and not is_locked


def _closed(door: "Item", accessor: "StateAccessor", actor_id: ActorId) -> bool:
    """Door is closed (any lock state)."""
    is_open, _, _ = _get_door_state(door)
    return not is_open


def _open(door: "Item", accessor: "StateAccessor", actor_id: ActorId) -> bool:
    """Door is open."""
    is_open, _, _ = _get_door_state(door)
    return is_open


def _lockable_with_key(door: "Item", accessor: "StateAccessor", actor_id: ActorId) -> bool:
    """Door is closed, unlocked, and actor has key."""
    is_open, is_locked, _ = _get_door_state(door)
    return not is_open and not is_locked and actor_has_key_for_door(accessor, actor_id, door)


def _lockable(door: "Item", accessor: "StateAccessor", actor_id: ActorId) -> bool:
    """Door is closed, unlocked, and has a lock."""
    is_open, is_locked, lock_id = _get_door_state(door)
    return not is_open and not is_locked and lock_id is not None


def _locked_or_closed(door: "Item", accessor: "StateAccessor", actor_id: ActorId) -> bool:
    """Door is locked or closed (default preference)."""
    is_open, is_locked, _ = _get_door_state(door)
    return is_locked or not is_open


# Map verbs to ordered list of strategies (primary → fallback)
DOOR_SELECTION_STRATEGIES: Dict[str, List[DoorStrategy]] = {
    "unlock": [_unlockable_with_key, _locked],
    "open": [_closed_unlocked, _closed],
    "close": [_open],
    "lock": [_lockable_with_key, _lockable],
}


def _apply_door_strategies(
    matching_doors: List["Item"],
    strategies: List[DoorStrategy],
    accessor: "StateAccessor",
    actor_id: ActorId
) -> Optional["Item"]:
    """Apply ordered list of selection strategies to find best door."""
    for strategy in strategies:
        for door in matching_doors:
            if strategy(door, accessor, actor_id):
                return door
    return None


def find_door_with_adjective(
    accessor: "StateAccessor",
    name: WordEntry,
    adjective: Optional[str],
    location_id: str,
    actor_id: ActorId,
    verb: Optional[str] = None
) -> Optional["Item"]:
    """
    Find a door in a location, optionally filtered by adjective.

    If adjective is provided, only returns doors whose id or description
    contains the adjective. If no adjective, uses smart selection based on
    the verb being performed:
    - For "unlock": prefer locked doors that the actor has a key for
    - For "open": prefer closed unlocked doors, then closed locked doors
    - For "close": prefer open doors
    - Otherwise: prefer closed/locked doors over open ones

    Args:
        accessor: StateAccessor instance
        name: Door name to search for (WordEntry with synonyms or plain string)
        adjective: Optional adjective to filter by (or None/empty for smart selection)
        location_id: ID of the location
        actor_id: Optional actor ID for key checking (defaults to "player")
        verb: Optional verb being performed for smart selection

    Returns:
        Door Item if found, None otherwise
    """
    adjective_str = _extract_word(adjective)
    has_adjective = adjective_str and adjective_str.strip()
    # Collect all doors in location matching name
    matching_doors = []

    # Check door items (unified model)
    for item in accessor.game_state.items:
        if not item.is_door:
            continue
        if not _is_item_visible_in_location(item, location_id, accessor, actor_id, verb or "look"):
            continue
        # Check if name matches - for door items, check name and description
        if name_matches(name, item.name) or \
           name_matches(name, item.description):
            matching_doors.append(item)

    # If no matches, return None
    if not matching_doors:
        return None

    # If adjective provided, filter by it
    if has_adjective:
        assert adjective_str is not None  # Guaranteed by has_adjective check
        adj_lower = adjective_str.lower().strip()

        # Check if adjective is a direction (e.g., "north door", "east door")
        direction_adj = DIRECTION_ABBREVIATIONS.get(adj_lower, adj_lower)
        valid_directions = {"north", "south", "east", "west", "up", "down",
                           "northeast", "northwest", "southeast", "southwest"}
        if direction_adj in valid_directions:
            # Find door via exit in that direction
            location = accessor.get_location(LocationId(location_id))
            if location and direction_adj in location.exits:
                exit_desc = location.exits[direction_adj]
                if exit_desc.door_id:
                    # Return the door if it's in matching_doors
                    for door in matching_doors:
                        if door.id == exit_desc.door_id:
                            return door
            # No door in that direction
            return None

        # Not a direction - check regular adjective matching
        for door in matching_doors:
            if _matches_adjective(adjective_str, door):
                return door
        # No match with adjective
        return None

    # Smart selection when no adjective
    if len(matching_doors) == 1:
        return matching_doors[0]

    # Multiple doors - apply smart selection based on verb
    if verb and verb in DOOR_SELECTION_STRATEGIES:
        selected = _apply_door_strategies(
            matching_doors,
            DOOR_SELECTION_STRATEGIES[verb],
            accessor,
            actor_id
        )
        if selected:
            return selected

    # Default: prefer locked/closed doors over open ones
    for door in matching_doors:
        if _locked_or_closed(door, accessor, actor_id):
            return door

    return matching_doors[0]


def _is_item_visible_in_location(
    item: "Item",
    location_id: str,
    accessor: "StateAccessor",
    actor_id: ActorId,
    method: str = "look"
) -> bool:
    """
    Check if item should be visible in a location.

    An item is visible if:
    1. It passes the observability check (not hidden, or behavior allows)
    2. AND one of:
       a. Its location is that room directly
       b. For doors: any exit in that room references it via door_id

    Args:
        item: Item to check visibility for
        location_id: ID of location to check visibility in
        accessor: StateAccessor instance
        actor_id: ID of the actor observing (default "player")
        method: The observation method/verb (default "look")

    Returns:
        True if item should be visible, False otherwise
    """
    # Check observability (hidden state and behaviors)
    visible, _ = is_observable(
        item, accessor, accessor.behavior_manager,
        actor_id=actor_id, method=method
    )
    if not visible:
        return False

    # Direct location match
    if item.location == location_id:
        return True

    # For doors: check if the exit location format matches this location
    # Door items have location format: exit:{location_id}:{direction}
    if item.is_door and item.location.startswith("exit:"):
        parts = item.location.split(":")
        if len(parts) >= 2 and parts[1] == location_id:
            return True

    # For doors: also check if any exit in this location references the door via door_id
    if item.is_door:
        location = accessor.get_location(LocationId(location_id))
        if location:
            for exit_desc in location.exits.values():
                if exit_desc.door_id == item.id:
                    return True

    return False


def gather_location_contents(accessor: "StateAccessor", location_id: str, actor_id: ActorId) -> Dict[str, Any]:
    """
    Gather all visible contents of a location.

    This is the single source of truth for what's visible in a location.
    Used by both text formatting (describe_location) and JSON queries (_query_location).

    Includes door items that are:
    - Located directly in this room (decorative doors)
    - Referenced by an exit in this room via door_id

    Excludes hidden items (uses is_observable() check).

    Args:
        accessor: StateAccessor instance
        location_id: ID of location to gather contents for
        actor_id: ID of the actor viewing (excluded from actor list)

    Returns:
        Dict with keys:
            - items: List of items directly in location (includes visible doors)
            - surface_items: Dict of container_name -> list of items on that surface
            - open_container_items: Dict of container_name -> list of items in open containers
            - actors: List of other actors in location
    """
    # Collect all visible items in location
    items_here = []
    for item in accessor.game_state.items:
        if _is_item_visible_in_location(item, location_id, accessor, actor_id):
            items_here.append(item)

    # Collect items on surfaces and in open containers
    surface_items = {}  # container_name -> [items]
    open_container_items = {}  # container_name -> [items]

    for container in items_here:
        container_props = container.properties.get("container", {})
        if not container_props:
            continue

        is_surface = container_props.get("is_surface", False)
        is_open = container_props.get("open", False)

        if is_surface or is_open:
            items_in_container = []
            for item in accessor.game_state.items:
                if item.location == container.id:
                    # Check observability for items in containers
                    visible, _ = is_observable(
                        item, accessor, accessor.behavior_manager,
                        actor_id=actor_id, method="look"
                    )
                    if visible:
                        items_in_container.append(item)

            if items_in_container:
                if is_surface:
                    surface_items[container.name] = items_in_container
                else:
                    open_container_items[container.name] = items_in_container

    # Collect other visible actors
    actors_here = []
    for other_actor_id, other_actor in accessor.game_state.actors.items():
        if other_actor.location == location_id and other_actor_id != actor_id:
            # Check observability for actors
            visible, _ = is_observable(
                other_actor, accessor, accessor.behavior_manager,
                actor_id=actor_id, method="look"
            )
            if visible:
                actors_here.append(other_actor)

    return {
        "items": items_here,
        "surface_items": surface_items,
        "open_container_items": open_container_items,
        "actors": actors_here
    }


def describe_location(accessor: "StateAccessor", location: "Location", actor_id: ActorId) -> List[str]:
    """
    Build a text description of a location including items, actors, and exits.

    Uses gather_location_contents for data, then formats as text.
    Includes posture-aware prefix when player is elevated.

    Args:
        accessor: StateAccessor instance
        location: Location object to describe
        actor_id: ID of the actor viewing (excluded from actor list)

    Returns:
        List of strings that can be joined to form the description
    """
    message_parts = []

    # Add posture-aware prefix for elevated positions
    actor = accessor.get_actor(actor_id)  # Raises KeyError if not found
    posture = actor.properties.get("posture")
    focused_on = actor.properties.get("focused_on")

    if posture == "climbing" and focused_on:
        # Get the focused entity name
        focused_entity = accessor.get_item(focused_on)
        if focused_entity:
            message_parts.append(f"[From the {focused_entity.name}]")
    elif posture == "on_surface" and focused_on:
        focused_entity = accessor.get_item(focused_on)
        if focused_entity:
            message_parts.append(f"[Standing on the {focused_entity.name}]")
    elif posture == "cover" and focused_on:
        focused_entity = accessor.get_item(focused_on)
        if focused_entity:
            message_parts.append(f"[Behind the {focused_entity.name}]")
    elif posture == "concealed" and focused_on:
        focused_entity = accessor.get_item(focused_on)
        if focused_entity:
            message_parts.append(f"[Hidden in the {focused_entity.name}]")

    message_parts.append(f"{location.name}\n{location.description}")

    contents = gather_location_contents(accessor, location.id, actor_id)

    if contents["items"]:
        item_names = ", ".join([item.name for item in contents["items"]])
        message_parts.append(f"\nYou see: {item_names}")

    for container_name, items in contents["surface_items"].items():
        item_names = ", ".join([item.name for item in items])
        message_parts.append(f"On the {container_name}: {item_names}")

    for container_name, items in contents["open_container_items"].items():
        item_names = ", ".join([item.name for item in items])
        message_parts.append(f"In the {container_name}: {item_names}")

    if contents["actors"]:
        actor_names = ", ".join([a.name for a in contents["actors"]])
        message_parts.append(f"\nAlso here: {actor_names}")

    # Add visible exits
    visible_exits = accessor.get_visible_exits(location.id, actor_id)
    if visible_exits:
        exit_descriptions = []
        for direction, exit_desc in visible_exits.items():
            if hasattr(exit_desc, 'name') and exit_desc.name:
                exit_descriptions.append(f"{exit_desc.name} ({direction})")
            else:
                exit_descriptions.append(direction)
        message_parts.append(f"\nExits: {', '.join(exit_descriptions)}")

    return message_parts



def find_lock_by_context(
    accessor: "StateAccessor",
    location_id: str,
    actor_id: ActorId,
    direction: Optional[str] = None,
    door_name: Optional[WordEntry] = None,
    door_adjective: Optional[str] = None
) -> Optional["Lock"]:
    """
    Find a lock based on context (direction or door specification).

    Locks don't have a location - they're attached to doors via lock_id.
    This function finds a lock by first finding the door, then getting its lock.

    Search strategy:
    1. If direction provided: Find exit in that direction → get door → get lock
    2. If door_name provided: Find door by name (with optional adjective) → get lock
    3. If neither: Find all visible doors with locks, return lock if exactly one

    Hidden locks (states.hidden == True) are excluded from results.

    Args:
        accessor: StateAccessor instance
        location_id: Current location ID
        direction: Direction to find door with lock (e.g., "east")
        door_name: Name of door to find lock on (WordEntry or string)
        door_adjective: Adjective to disambiguate door
        actor_id: ID of actor looking for the lock (for observability check)

    Returns:
        Lock entity if found and visible, None otherwise
    """
    location = accessor.get_location(LocationId(location_id))
    if not location:
        return None

    def _get_visible_lock(lock_id: str) -> Optional["Lock"]:
        """Get lock if it exists and is visible."""
        lock = accessor.get_lock(LockId(lock_id))
        if not lock:
            return None
        # Check lock visibility
        visible, _ = is_observable(
            lock, accessor, accessor.behavior_manager,
            actor_id=actor_id, method="examine"
        )
        if not visible:
            return None
        return lock

    # Strategy 1: Find lock via direction
    if direction:
        # Expand abbreviation if needed
        dir_expanded = DIRECTION_ABBREVIATIONS.get(direction.lower(), direction.lower())

        # Check if there's an exit in that direction
        if dir_expanded not in location.exits:
            return None

        exit_desc = location.exits[dir_expanded]
        if not exit_desc.door_id:
            return None

        door = accessor.get_door_item(exit_desc.door_id)
        if not door or not door.door_lock_id:
            return None

        return _get_visible_lock(door.door_lock_id)

    # Strategy 2: Find lock via door name
    if door_name:
        door = find_door_with_adjective(accessor, door_name, door_adjective, location_id, actor_id)
        if not door or not door.door_lock_id:
            return None

        return _get_visible_lock(door.door_lock_id)

    # Strategy 3: Find lock if only one visible door has a visible lock
    visible_locks = []
    for item in accessor.game_state.items:
        if item.is_door and item.door_lock_id:
            if _is_item_visible_in_location(item, location_id, accessor, actor_id):
                lock = _get_visible_lock(item.door_lock_id)
                if lock:
                    visible_locks.append(lock)

    if len(visible_locks) == 1:
        return visible_locks[0]

    # Multiple or no visible locks - ambiguous or not found
    return None


# Standard direction words for exit lookup
DIRECTION_WORDS = {
    "north", "south", "east", "west", "up", "down",
    "northeast", "northwest", "southeast", "southwest",
    "n", "s", "e", "w", "u", "d", "ne", "nw", "se", "sw"
}

# Direction abbreviation mapping
DIRECTION_ABBREVIATIONS = {
    "n": "north", "s": "south", "e": "east", "w": "west",
    "u": "up", "d": "down",
    "ne": "northeast", "nw": "northwest", "se": "southeast", "sw": "southwest"
}


def find_exit_by_name(
    accessor: "StateAccessor", name: WordEntry, actor_id: ActorId, adjective: Optional[str] = None
) -> Union[Tuple[str, "ExitDescriptor"], Tuple[None, List[str]], None]:
    """
    Find an exit in the current location by name, direction, or adjective.

    Search strategy (first match wins):
    1. Exact direction match (north, up, etc.) or abbreviation (n, u, etc.)
    2. Direction + "exit" (e.g., "north exit", "east exit")
    3. Exit name field match using name_matches with synonyms
       (e.g., "stairs" matches "spiral staircase" via synonym "staircase")

    Hidden exits are excluded via observability check.

    Args:
        accessor: StateAccessor instance
        name: Name to search for (WordEntry with synonyms, or plain string)
        actor_id: ID of the actor looking for the exit
        adjective: Optional adjective/direction to filter by

    Returns:
        - Tuple of (direction, ExitDescriptor) if exactly one match found
        - Tuple of (None, list_of_exit_names) if multiple ambiguous matches found
        - None if no match found
    """
    location = accessor.get_current_location(actor_id)
    if not location:
        return None

    # Extract canonical word for direction/generic checks
    name_lower = name.word.lower().strip()

    # Get visible exits
    visible_exits = accessor.get_visible_exits(location.id, actor_id)
    if not visible_exits:
        return None

    # 1. Check for exact direction match
    # Expand abbreviation if needed
    direction_to_check = DIRECTION_ABBREVIATIONS.get(name_lower, name_lower)
    if direction_to_check in visible_exits:
        return (direction_to_check, visible_exits[direction_to_check])

    # 2. Check for "direction + exit" pattern (e.g., "north exit", "east passage")
    # Parser normalizes synonyms (passage, way, path, opening) to canonical "exit"
    if name_lower == "exit" and adjective:
        adj_lower = adjective.lower().strip()
        adj_direction = DIRECTION_ABBREVIATIONS.get(adj_lower, adj_lower)
        if adj_direction in visible_exits:
            return (adj_direction, visible_exits[adj_direction])

    # 2b. Generic "exit" with no adjective - if only one exit, return it
    if name_lower == "exit" and not adjective:
        if len(visible_exits) == 1:
            direction = next(iter(visible_exits))
            return (direction, visible_exits[direction])

    # 3. If adjective provided, check for adjective + name combination first
    # This handles cases like "spiral stairs" where adjective="spiral", name="stairs"
    # Must check this BEFORE simple name match to avoid "stairs" matching wrong exit
    if adjective:
        # Handle both WordEntry and string adjectives
        adj_str = adjective.word if hasattr(adjective, 'word') else str(adjective)
        adj_lower = adj_str.lower().strip()
        canonical = name.word
        full_search = f"{adj_lower} {canonical}".lower()
        for direction, exit_desc in visible_exits.items():
            if exit_desc.name and full_search in exit_desc.name.lower():
                return (direction, exit_desc)

    # 4. Search by exit.name field using name_matches (handles synonyms)
    # Collect ALL matches to detect ambiguity
    matches = []
    for direction, exit_desc in visible_exits.items():
        if exit_desc.name:
            if name_matches(name, exit_desc.name):
                matches.append((direction, exit_desc))

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        # Return ambiguity indicator with list of matching exit names
        exit_names = [exit_desc.name for _, exit_desc in matches]
        return (None, exit_names)

    return None
