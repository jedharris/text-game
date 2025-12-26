"""
StateAccessor - Clean API for state queries and mutations with automatic behavior invocation.

This module provides the core abstraction for accessing and modifying game state.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, cast, TYPE_CHECKING

from src.types import LocationId, ActorId, ItemId, LockId, PartId, EntityId, EventName
from src.state_manager import (
    GameState, Location, Item, Actor, Lock, Part, ExitDescriptor, Entity
)
from src.narration_types import ReactionRef

if TYPE_CHECKING:
    from src.behavior_manager import BehaviorManager


@dataclass
class EventResult:
    """
    Result from an entity behavior event handler.

    Behaviors return this to indicate whether an action should be allowed
    and provide optional feedback text for the player.

    Fields:
        allow: Whether the action should proceed
        feedback: Optional feedback text describing behavior's response.
                  Semantic type: FeedbackText
                  Examples: "The door creaks open.", "The sword is stuck to the altar."
        context: Author-defined narrator context (passed through to NarrationPlan).
                 Can include npc_state, communication, relationship, etc.
        hints: Author-defined style hints (e.g., ["urgent", "rescue"]).
               Passed through to narrator for style guidance.
        fragments: Pre-selected fragments for this entity's contribution to narration.
                   Can include state fragments, action fragments, etc.
    """
    allow: bool
    feedback: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    hints: list[str] = field(default_factory=list)
    fragments: Optional[Dict[str, Any]] = None


@dataclass
class UpdateResult:
    """
    Result from a state update operation.

    Returned by StateAccessor.update() to indicate success or failure.

    Fields:
        success: Whether the update succeeded
        detail: Error message if update failed, or behavior feedback on success.
                Semantic type: DetailText
                Examples: "Item moved to inventory.", "Field 'location' not found."
    """
    success: bool
    detail: Optional[str] = None


@dataclass
class HandlerResult:
    """
    Result from a command handler.

    Command handlers return this to indicate success/failure and provide
    text for narration. The primary field contains the core statement of
    what occurred, while beats contains supplemental sentences (e.g.,
    positioning changes, side effects).

    Optional data dict can include extra info like llm_context for narration.

    Fields:
        success: Whether the action succeeded
        primary: The core statement of what occurred.
                 Semantic type: PrimaryText
                 Examples: "You pick up the sword.", "You can't go that way."
        beats: Supplemental sentences (e.g., ["You step down from the table."])
        data: Optional extra data for narration (llm_context, etc.)
        context: Author-defined narrator context (passed through to NarrationPlan).
                 Can include npc_state, urgency, relationship, etc.
        hints: Author-defined style hints (e.g., ["urgent", "rescue"]).
               Passed through to narrator for style guidance.
        fragments: Pre-selected fragments for narration (action_core, action_color, traits).
        reactions: Multi-entity reactions for scenes with multiple reacting entities.
                   Each reaction includes entity info and pre-selected fragments.
    """
    success: bool
    primary: str
    beats: list[str] = field(default_factory=list)
    data: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    hints: list[str] = field(default_factory=list)
    fragments: Optional[Dict[str, Any]] = None
    reactions: Optional[List[ReactionRef]] = None


class StateAccessor:
    """
    Clean API for state queries and mutations.

    Provides generic state operations with automatic behavior invocation.
    All state changes should go through this accessor to ensure behaviors
    are properly invoked.
    """

    def __init__(self, game_state: GameState, behavior_manager: "BehaviorManager"):
        """
        Initialize StateAccessor.

        Args:
            game_state: The GameState instance to operate on
            behavior_manager: The BehaviorManager instance for invoking behaviors
        """
        self.game_state = game_state
        self.behavior_manager = behavior_manager

    def __getattr__(self, name: str) -> Any:
        """
        Provide backward-compatible access to GameState attributes for behaviors.

        Behaviors historically received the raw GameState instance; routing
        unknown attributes to the underlying state lets existing modules
        continue to read fields like .actors or .extra while new code can
        call accessor methods directly.
        """
        return getattr(self.game_state, name)

    # Getter methods

    def get_item(self, item_id: ItemId) -> Optional[Item]:
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

    def get_actor(self, actor_id: ActorId) -> Optional[Actor]:
        """
        Get actor by ID.

        Args:
            actor_id: The actor ID to look up ("player" or NPC id)

        Returns:
            Actor or None if not found

        Note:
            This returns Optional to allow handler utilities like
            validate_actor_and_location() to provide graceful error messages.
            For fail-fast access in tests/internal code, use state.get_actor() instead.
        """
        return self.game_state.actors.get(actor_id)

    def get_location(self, location_id: LocationId) -> Optional[Location]:
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


    def get_lock(self, lock_id: LockId) -> Optional[Lock]:
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

    def get_door_item(self, door_id: ItemId) -> Optional[Item]:
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

    def get_door_for_exit(self, location_id: LocationId, direction: str) -> Optional[Item]:
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

    def get_part(self, part_id: PartId) -> Optional[Part]:
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

    def get_parts_of(self, entity_id: EntityId) -> List[Part]:
        """
        Get all parts belonging to an entity.

        Args:
            entity_id: The parent entity ID

        Returns:
            List of Part objects belonging to entity
        """
        return [p for p in self.game_state.parts if p.part_of == entity_id]

    def get_items_at_part(self, part_id: PartId) -> List[Item]:
        """
        Get items located at a part.

        Args:
            part_id: The part ID

        Returns:
            List of Item objects at this part
        """
        return [i for i in self.game_state.items if i.location == part_id]

    def get_entity(self, entity_id: EntityId) -> Optional[Entity]:
        """
        Get any entity by ID regardless of type.

        Searches all entity collections: locations, items, actors, locks, parts.

        Args:
            entity_id: The entity ID to look up

        Returns:
            Entity or None if not found
        """
        # Cast entity_id to each specific type for lookup
        # At runtime these are all strings, but NewType requires explicit casts

        # Check locations
        result: Optional[Entity] = self.get_location(cast(LocationId, entity_id))
        if result:
            return result

        # Check items
        result = self.get_item(cast(ItemId, entity_id))
        if result:
            return result

        # Check actors
        result = self.get_actor(cast(ActorId, entity_id))
        if result:
            return result

        # Check locks
        result = self.get_lock(cast(LockId, entity_id))
        if result:
            return result

        # Check parts
        result = self.get_part(cast(PartId, entity_id))
        if result:
            return result

        return None

    def get_focused_entity(self, actor_id: ActorId) -> Optional[Entity]:
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

    def get_actor_part(self, actor: Actor) -> Optional[Part]:
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

    def get_visible_exits(self, location_id: LocationId, actor_id: ActorId) -> Dict[str, ExitDescriptor]:
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

    def get_current_location(self, actor_id: ActorId) -> Optional[Location]:
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

    def get_items_in_location(self, location_id: LocationId) -> List[Item]:
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

    def get_actors_in_location(self, location_id: LocationId) -> List[Actor]:
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

    def _set_path(self, entity: Any, path: str, value: Any) -> Optional[str]:
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

    def _set_field(self, entity: Any, path: str, value: Any) -> Optional[str]:
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
            setattr(current, final_field, value)
            return None
        elif isinstance(current, dict):
            # Dict key
            current[final_field] = value
            return None
        else:
            return f"Field '{final_field}' not found on {type(current).__name__}"

    def _append_to_list(self, entity: Any, path: str, value: Any) -> Optional[str]:
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

    def _remove_from_list(self, entity: Any, path: str, value: Any) -> Optional[str]:
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

        # Remove the value - will raise ValueError if not present (indicates state bug)
        target.remove(value)
        return None

    def update(self, entity: Entity, changes: Dict[str, Any], verb: Optional[str] = None, actor_id: ActorId = ActorId("player")) -> UpdateResult:
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
                        entity, EventName(event_name), self, context
                    )

                    # If behavior explicitly denies, try next tier
                    if behavior_result and behavior_result.allow is False:
                        behavior_message = behavior_result.feedback
                        last_deny = True
                        continue  # Try next tier

                    # If behavior returns None, also try next tier (fallthrough)
                    if behavior_result is None:
                        last_deny = False
                        continue  # Try next tier

                    # If behavior allows (explicitly or implicitly), stop trying tiers
                    if behavior_result and behavior_result.allow:
                        behavior_message = behavior_result.feedback
                        last_deny = False
                        break  # Success, stop delegation

                # After trying all tiers, if last result was deny, return failure
                if last_deny:
                    return UpdateResult(success=False, detail=behavior_message)
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
                return UpdateResult(success=False, detail=error)

        # All changes applied successfully
        # Return behavior message if present, otherwise None
        return UpdateResult(success=True, detail=behavior_message)
