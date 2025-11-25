"""
StateAccessor - Clean API for state queries and mutations with automatic behavior invocation.

This module provides the core abstraction for accessing and modifying game state.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class EventResult:
    """
    Result from an entity behavior event handler.

    Behaviors return this to indicate whether an action should be allowed.
    """
    allow: bool
    message: Optional[str] = None


@dataclass
class UpdateResult:
    """
    Result from a state update operation.

    Returned by StateAccessor.update() to indicate success or failure.
    """
    success: bool
    message: Optional[str] = None


@dataclass
class HandlerResult:
    """
    Result from a command handler.

    Command handlers return this to indicate success/failure and provide
    a message for the user.
    """
    success: bool
    message: str


class StateAccessor:
    """
    Clean API for state queries and mutations.

    Provides generic state operations with automatic behavior invocation.
    All state changes should go through this accessor to ensure behaviors
    are properly invoked.
    """

    def __init__(self, game_state, behavior_manager):
        """
        Initialize StateAccessor.

        Args:
            game_state: The GameState instance to operate on
            behavior_manager: The BehaviorManager instance for invoking behaviors
        """
        self.game_state = game_state
        self.behavior_manager = behavior_manager

    # Getter methods

    def get_item(self, item_id: str):
        """
        Get item by ID.

        Args:
            item_id: The item ID to look up

        Returns:
            Item or None if not found
        """
        for item in self.game_state.items:
            if item.id == item_id:
                return item
        return None

    def get_actor(self, actor_id: str):
        """
        Get actor by ID.

        Note: Currently works with player (PlayerState) and npcs (NPC list).
        Will be unified to actors dict in Phase 3.

        Args:
            actor_id: The actor ID to look up ("player" or NPC id)

        Returns:
            Actor/PlayerState or None if not found
        """
        if actor_id == "player":
            return self.game_state.player

        # Check NPCs
        for npc in self.game_state.npcs:
            if npc.id == actor_id:
                return npc

        return None

    def get_location(self, location_id: str):
        """
        Get location by ID.

        Args:
            location_id: The location ID to look up

        Returns:
            Location or None if not found
        """
        for location in self.game_state.locations:
            if location.id == location_id:
                return location
        return None

    def get_door(self, door_id: str):
        """
        Get door by ID.

        Args:
            door_id: The door ID to look up

        Returns:
            Door or None if not found
        """
        for door in self.game_state.doors:
            if door.id == door_id:
                return door
        return None

    def get_lock(self, lock_id: str):
        """
        Get lock by ID.

        Args:
            lock_id: The lock ID to look up

        Returns:
            Lock or None if not found
        """
        for lock in self.game_state.locks:
            if lock.id == lock_id:
                return lock
        return None

    # Collection methods

    def get_current_location(self, actor_id: str):
        """
        Get the current location of an actor.

        Args:
            actor_id: The actor ID ("player" or NPC id)

        Returns:
            Location or None if actor not found
        """
        actor = self.get_actor(actor_id)
        if not actor:
            return None

        return self.get_location(actor.location)

    def get_items_in_location(self, location_id: str):
        """
        Get all items in a location.

        Args:
            location_id: The location ID

        Returns:
            List of Items in the location
        """
        items = []
        for item in self.game_state.items:
            if item.location == location_id:
                items.append(item)
        return items

    def get_actors_in_location(self, location_id: str):
        """
        Get all actors in a location.

        Note: Currently returns only NPCs. In Phase 3 unified model,
        this will include player when present.

        Args:
            location_id: The location ID

        Returns:
            List of Actors/NPCs in the location
        """
        actors = []

        # Check NPCs
        for npc in self.game_state.npcs:
            if npc.location == location_id:
                actors.append(npc)

        return actors

    # Mutation methods

    def _set_path(self, entity, path: str, value):
        """
        Low-level state mutation primitive.

        Supports:
        - Simple field access: "location"
        - Nested dict access with dots: "properties.container.open"
        - List append with + prefix: "+inventory"
        - List remove with - prefix: "-inventory"

        Args:
            entity: The entity to modify (Item, Actor, Location, etc.)
            path: The path to the field to modify
            value: The value to set/append/remove

        Returns:
            None on success, error string on failure
        """
        # Check for list operations
        if path.startswith('+'):
            # Append operation
            return self._append_to_list(entity, path[1:], value)
        elif path.startswith('-'):
            # Remove operation
            return self._remove_from_list(entity, path[1:], value)
        else:
            # Set operation
            return self._set_field(entity, path, value)

    def _set_field(self, entity, path: str, value):
        """Set a field value, handling nested paths with dots."""
        parts = path.split('.')

        # Navigate to the parent container
        current = entity
        for i, part in enumerate(parts[:-1]):
            # Check if it's a dataclass field or dict key
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict):
                # Create intermediate dicts if needed
                if part not in current:
                    current[part] = {}
                current = current[part]
            else:
                return f"Path component '{part}' not found in {type(current).__name__}"

        # Set the final field
        final_field = parts[-1]

        if hasattr(current, final_field):
            # Dataclass field
            try:
                setattr(current, final_field, value)
                return None
            except AttributeError as e:
                return f"Cannot set field '{final_field}': {e}"
        elif isinstance(current, dict):
            # Dict key
            current[final_field] = value
            return None
        else:
            return f"Field '{final_field}' not found on {type(current).__name__}"

    def _append_to_list(self, entity, path: str, value):
        """Append a value to a list field."""
        parts = path.split('.')

        # Navigate to the container
        current = entity
        for part in parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict):
                if part not in current:
                    return f"Path component '{part}' not found"
                current = current[part]
            else:
                return f"Path component '{part}' not found"

        # Get the list field
        final_field = parts[-1]

        if hasattr(current, final_field):
            target = getattr(current, final_field)
        elif isinstance(current, dict):
            if final_field not in current:
                return f"Field '{final_field}' not found"
            target = current[final_field]
        else:
            return f"Field '{final_field}' not found"

        # Verify it's a list
        if not isinstance(target, list):
            return f"Cannot append to non-list field '{final_field}' (type: {type(target).__name__})"

        target.append(value)
        return None

    def _remove_from_list(self, entity, path: str, value):
        """Remove a value from a list field."""
        parts = path.split('.')

        # Navigate to the container
        current = entity
        for part in parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict):
                if part not in current:
                    return f"Path component '{part}' not found"
                current = current[part]
            else:
                return f"Path component '{part}' not found"

        # Get the list field
        final_field = parts[-1]

        if hasattr(current, final_field):
            target = getattr(current, final_field)
        elif isinstance(current, dict):
            if final_field not in current:
                return f"Field '{final_field}' not found"
            target = current[final_field]
        else:
            return f"Field '{final_field}' not found"

        # Verify it's a list
        if not isinstance(target, list):
            return f"Cannot remove from non-list field '{final_field}' (type: {type(target).__name__})"

        # Try to remove the value
        try:
            target.remove(value)
            return None
        except ValueError:
            return f"Value not in list '{final_field}'"
