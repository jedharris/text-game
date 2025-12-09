"""
StateAccessor - Clean API for state queries and mutations with automatic behavior invocation.

This module provides the core abstraction for accessing and modifying game state.
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional


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
    a message for the user. Optional data dict can include extra info
    like llm_context for narration.
    """
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


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

        Args:
            actor_id: The actor ID to look up ("player" or NPC id)

        Returns:
            Actor or None if not found
        """
        return self.game_state.actors.get(actor_id)

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

    def get_door_item(self, door_id: str):
        """
        Get a door item by ID. Returns None if not found or not a door.

        This is a convenience method for the unified Item/Door model where
        doors are items with properties.door defined.

        Args:
            door_id: The door item ID to look up

        Returns:
            Item if found and is a door, None otherwise
        """
        item = self.get_item(door_id)
        if item and item.is_door:
            return item
        return None

    def get_door_for_exit(self, location_id: str, direction: str):
        """
        Get the door item for an exit, if any.

        Looks up the exit descriptor for the given direction and returns
        the door item referenced by door_id.

        Args:
            location_id: The location ID
            direction: The exit direction (e.g., "north", "east")

        Returns:
            Item (door) if exit has a door, None otherwise
        """
        location = self.get_location(location_id)
        if not location:
            return None
        exit_desc = location.exits.get(direction)
        if not exit_desc or not exit_desc.door_id:
            return None
        return self.get_door_item(exit_desc.door_id)

    def get_part(self, part_id: str):
        """
        Get part by ID.

        Args:
            part_id: The part ID to look up

        Returns:
            Part or None if not found
        """
        for part in self.game_state.parts:
            if part.id == part_id:
                return part
        return None

    def get_parts_of(self, entity_id: str):
        """
        Get all parts belonging to an entity.

        Args:
            entity_id: The parent entity ID

        Returns:
            List of Part objects belonging to entity
        """
        return [p for p in self.game_state.parts if p.part_of == entity_id]

    def get_items_at_part(self, part_id: str):
        """
        Get items located at a part.

        Args:
            part_id: The part ID

        Returns:
            List of Item objects at this part
        """
        return [i for i in self.game_state.items if i.location == part_id]

    def get_entity(self, entity_id: str):
        """
        Get any entity by ID regardless of type.

        Searches all entity collections: locations, items, actors, locks, parts.

        Args:
            entity_id: The entity ID to look up

        Returns:
            Entity or None if not found
        """
        # Check locations
        entity = self.get_location(entity_id)
        if entity:
            return entity

        # Check items
        entity = self.get_item(entity_id)
        if entity:
            return entity

        # Check actors
        entity = self.get_actor(entity_id)
        if entity:
            return entity

        # Check locks
        entity = self.get_lock(entity_id)
        if entity:
            return entity

        # Check parts
        entity = self.get_part(entity_id)
        if entity:
            return entity

        return None

    def get_focused_entity(self, actor_id: str):
        """
        Get entity actor is focused on.

        The focused_on property can reference any entity type:
        item, container, part, or actor.

        Args:
            actor_id: The actor ID

        Returns:
            Entity actor is focused on, or None
        """
        actor = self.get_actor(actor_id)
        if not actor:
            return None

        focused_id = actor.properties.get("focused_on")
        if not focused_id:
            return None

        return self.get_entity(focused_id)

    def get_actor_part(self, actor):
        """
        Get the spatial part an actor currently occupies.

        Resolution order:
        1. If actor has focused_on pointing to a Part, return that part
        2. If actor's location has a default_part, return that part
        3. Otherwise return None (non-spatial location)

        Args:
            actor: The Actor object (not actor_id)

        Returns:
            Part or None if actor is not in a spatial context
        """
        if not actor:
            return None

        # Check if focused_on references a part
        focused_id = actor.properties.get("focused_on")
        if focused_id:
            part = self.get_part(focused_id)
            if part:
                return part

        # Fall back to location's default part
        location = self.get_location(actor.location)
        if location:
            default_part_id = location.properties.get("default_part")
            if default_part_id:
                return self.get_part(default_part_id)

        return None

    def get_visible_exits(self, location_id: str, actor_id: str) -> dict:
        """
        Get all visible exits for a location.

        Filters out hidden exits using is_observable() check.

        Args:
            location_id: The location ID
            actor_id: The actor observing (for behavior context)

        Returns:
            Dict of direction -> ExitDescriptor for visible exits only
        """
        from utilities.utils import is_observable

        location = self.get_location(location_id)
        if not location:
            return {}

        visible_exits = {}
        for direction, exit_desc in location.exits.items():
            visible, _ = is_observable(
                exit_desc, self, self.behavior_manager,
                actor_id=actor_id, method="look"
            )
            if visible:
                visible_exits[direction] = exit_desc

        return visible_exits

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

        Args:
            location_id: The location ID

        Returns:
            List of Actors in the location (including player if present)
        """
        actors = []

        # Check all actors (including player)
        for actor in self.game_state.actors.values():
            if actor.location == location_id:
                actors.append(actor)

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

    def update(self, entity, changes: dict, verb: Optional[str] = None, actor_id: str = "player") -> UpdateResult:
        """
        Apply state changes to an entity.

        This is the main mutation interface. It checks entity behaviors first,
        then applies changes if allowed.

        Args:
            entity: The entity to modify (Item, Actor, Location, etc.)
            changes: Dict mapping paths to values (e.g., {"location": "room1", "+inventory": "item1"})
            verb: Optional verb that triggered this update (for behavior invocation)
            actor_id: The actor performing the action (default: "player")

        Returns:
            UpdateResult with success flag and optional error message

        Examples:
            >>> accessor.update(item, {"location": "room1"})
            >>> accessor.update(actor, {"+inventory": "item1", "location": "room2"})
            >>> accessor.update(item, {"properties.weight": 10})
        """
        import sys

        # Invoke entity behaviors if verb provided
        if verb and self.behavior_manager:
            # Look up event names from verb (may be multiple tiers)
            events = self.behavior_manager.get_events_for_verb(verb)

            behavior_message = None
            last_deny = False  # Track if all tiers denied

            if events:
                # Try each event in tier order (lowest tier/highest precedence first)
                for tier, event_name in events:
                    # Build context dict
                    context = {
                        "actor_id": actor_id,
                        "changes": changes,
                        "verb": verb
                    }

                    # Invoke behaviors
                    behavior_result = self.behavior_manager.invoke_behavior(
                        entity, event_name, self, context
                    )

                    # If behavior explicitly denies, try next tier
                    if behavior_result and behavior_result.allow is False:
                        behavior_message = behavior_result.message
                        last_deny = True
                        continue  # Try next tier

                    # If behavior returns None, also try next tier (fallthrough)
                    if behavior_result is None:
                        last_deny = False
                        continue  # Try next tier

                    # If behavior allows (explicitly or implicitly), stop trying tiers
                    if behavior_result and behavior_result.allow:
                        behavior_message = behavior_result.message
                        last_deny = False
                        break  # Success, stop delegation

                # After trying all tiers, if last result was deny, return failure
                if last_deny:
                    return UpdateResult(success=False, message=behavior_message)
            else:
                behavior_message = None
        else:
            behavior_message = None

        # Apply each change
        for path, value in changes.items():
            error = self._set_path(entity, path, value)
            if error:
                # Log to stderr and return failure
                print(f"Error updating {path}: {error}", file=sys.stderr)
                return UpdateResult(success=False, message=error)

        # All changes applied successfully
        # Return behavior message if present, otherwise None
        return UpdateResult(success=True, message=behavior_message)
