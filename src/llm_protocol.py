"""
LLM protocol handler for LLM-Game Engine communication.

Implements the JSON interaction protocol as specified in LLM_game_interaction.md.
Processes commands and queries, returning structured JSON results.
"""

import json
from typing import Any, Dict, List, Optional

from .state_manager import GameState
from .behavior_manager import BehaviorManager


class LLMProtocolHandler:
    """
    Handler for JSON protocol messages between LLM and game engine.

    Processes JSON commands and queries, returning structured JSON results
    conforming to the specification.
    """

    # Meta commands that should still work after state corruption
    META_COMMANDS = {"save", "quit", "help", "load"}

    def __init__(self, state: GameState, behavior_manager: Optional[BehaviorManager] = None):
        self.state = state
        self.state_corrupted = False

        # Auto-create behavior manager if not provided
        # This ensures all handlers work even without explicit behavior_manager
        if behavior_manager is None:
            from pathlib import Path
            behavior_manager = BehaviorManager()
            behaviors_dir = Path(__file__).parent.parent / "behaviors"
            if behaviors_dir.exists():
                modules = behavior_manager.discover_modules(str(behaviors_dir))
                behavior_manager.load_modules(modules)

        self.behavior_manager = behavior_manager

    def is_json_input(self, text: str) -> bool:
        """Check if input is JSON (starts with '{' after stripping whitespace)."""
        return text.strip().startswith("{")

    def handle_message(self, message: Dict) -> Dict:
        """Route message to appropriate handler based on type."""
        msg_type = message.get("type")

        if msg_type == "command":
            return self.handle_command(message)
        elif msg_type == "query":
            return self.handle_query(message)
        else:
            return {
                "type": "error",
                "message": f"Unknown message type: {msg_type}"
            }

    def handle_json_string(self, json_str: str) -> Dict:
        """Parse JSON string and handle the message."""
        try:
            message = json.loads(json_str)
            return self.handle_message(message)
        except json.JSONDecodeError as e:
            return {
                "type": "error",
                "message": f"Invalid JSON: {e}"
            }

    def handle_command(self, message: Dict) -> Dict:
        """Process a command message and return result."""
        import sys

        action = message.get("action", {})
        verb = action.get("verb")

        if not verb:
            return {
                "type": "error",
                "message": "Missing required field: action"
            }

        # Check for corrupted state - block non-meta commands
        if self.state_corrupted and verb not in self.META_COMMANDS:
            return {
                "type": "result",
                "success": False,
                "action": verb,
                "error": {
                    "message": "Game state is corrupted. Please save and restart.",
                    "fatal": True
                }
            }

        # Ensure action has actor_id
        if "actor_id" not in action:
            action["actor_id"] = "player"

        # Try new behavior system first (using invoke_handler)
        if self.behavior_manager and self.behavior_manager.has_handler(verb):
            from src.state_accessor import StateAccessor
            accessor = StateAccessor(self.state, self.behavior_manager)

            result = self.behavior_manager.invoke_handler(verb, accessor, action)

            # Check for inconsistent state errors
            if not result.success and result.message.startswith("INCONSISTENT STATE:"):
                self.state_corrupted = True
                print(f"ERROR: {verb}: {result.message}", file=sys.stderr)
                return {
                    "type": "result",
                    "success": False,
                    "action": verb,
                    "error": {
                        "message": result.message,
                        "fatal": True
                    }
                }

            if result.success:
                return {
                    "type": "result",
                    "success": True,
                    "action": verb,
                    "message": result.message
                }
            else:
                return {
                    "type": "result",
                    "success": False,
                    "action": verb,
                    "error": {"message": result.message}
                }

        # Fall back to old _cmd_* methods for unimplemented verbs
        handler = getattr(self, f"_cmd_{verb}", None)
        if handler:
            result = handler(action)

            # Apply behavior if command succeeded and we have a behavior manager
            if result.get("success") and self.behavior_manager:
                result = self._apply_behavior(verb, result)
            else:
                # Remove entity_obj if present (internal reference, not JSON serializable)
                result = {k: v for k, v in result.items() if k != "entity_obj"}

            return result
        else:
            return {
                "type": "result",
                "success": False,
                "action": verb,
                "error": {
                    "message": f"I don't understand '{verb}'. Try actions like go, take, open, or examine."
                }
            }

    def _apply_behavior(self, verb: str, result: Dict) -> Dict:
        """
        Apply entity behavior after a successful command.

        Args:
            verb: The command verb
            result: The command result (must contain entity_obj for behavior invocation)

        Returns:
            Modified result with behavior applied
        """
        entity_obj = result.get("entity_obj")
        if not entity_obj:
            return result

        # Build event name and context
        event_name = f"on_{verb}"
        context = {
            "location": self.state.player.location,
            "verb": verb
        }

        # Invoke behavior
        behavior_result = self.behavior_manager.invoke_behavior(
            entity_obj, event_name, self.state, context
        )

        # If no behavior found for "put", try "drop" as fallback
        # (putting an item down is semantically similar to dropping it)
        if not behavior_result and verb == "put":
            behavior_result = self.behavior_manager.invoke_behavior(
                entity_obj, "on_drop", self.state, context
            )

        # Remove entity_obj from result before returning
        result = {k: v for k, v in result.items() if k != "entity_obj"}

        if behavior_result:
            if behavior_result.message:
                result["message"] = behavior_result.message

            if not behavior_result.allow:
                # Behavior prevented the action - revert changes
                result["success"] = False
                # Note: The actual state reversion would need to be handled
                # by the specific command or behavior

            # Rebuild entity dict to reflect state changes made by behavior
            if "entity" in result:
                result["entity"] = self._entity_to_dict(entity_obj)

        return result

    def handle_query(self, message: Dict) -> Dict:
        """Process a query message and return response."""
        query_type = message.get("query_type")

        if query_type == "location":
            return self._query_location(message)
        elif query_type == "inventory":
            return self._query_inventory(message)
        elif query_type == "entity":
            return self._query_entity(message)
        elif query_type == "entities":
            return self._query_entities(message)
        elif query_type == "vocabulary":
            return self._query_vocabulary(message)
        elif query_type == "metadata":
            return self._query_metadata(message)
        else:
            return {
                "type": "error",
                "message": f"Unknown query type: {query_type}"
            }

    # Query handlers

    def _query_location(self, message: Dict) -> Dict:
        """Query current location.

        Uses gather_location_contents utility for unified item/actor gathering.
        """
        from utilities.utils import gather_location_contents
        from src.state_accessor import StateAccessor

        loc = self._get_current_location()
        include = message.get("include", [])
        actor_id = message.get("actor_id", "player")

        data = {
            "location": self._location_to_dict(loc)
        }

        # Use unified utility for gathering location contents
        accessor = StateAccessor(self.state, self.behavior_manager)
        contents = gather_location_contents(accessor, loc.id, actor_id)

        if "items" in include or not include:
            items = []

            # Items directly in location
            for item in contents["items"]:
                items.append(self._entity_to_dict(item))

            # Items on surfaces - add with on_surface marker
            for container_name, container_items in contents["surface_items"].items():
                for item in container_items:
                    item_dict = self._entity_to_dict(item)
                    item_dict["on_surface"] = container_name
                    items.append(item_dict)

            # Items in open containers - add with in_container marker
            for container_name, container_items in contents["open_container_items"].items():
                for item in container_items:
                    item_dict = self._entity_to_dict(item)
                    item_dict["in_container"] = container_name
                    items.append(item_dict)

            data["items"] = items

        if "doors" in include or not include:
            doors = []
            for door in self.state.doors:
                if loc.id in door.locations:
                    door_dict = self._door_to_dict(door)
                    # Add direction
                    for direction, exit_desc in loc.exits.items():
                        if exit_desc.door_id == door.id:
                            door_dict["direction"] = direction
                            break
                    doors.append(door_dict)
            data["doors"] = doors

        if "exits" in include or not include:
            exits = {}
            for direction, exit_desc in loc.exits.items():
                exits[direction] = {
                    "type": exit_desc.type,
                    "to": exit_desc.to
                }
                if exit_desc.door_id:
                    exits[direction]["door_id"] = exit_desc.door_id
            data["exits"] = exits

        if "actors" in include or "npcs" in include or not include:
            actors = []
            for actor in contents["actors"]:
                actors.append(self._actor_to_dict(actor))
            data["actors"] = actors

        return {
            "type": "query_response",
            "query_type": "location",
            "data": data
        }

    def _query_inventory(self, message: Dict) -> Dict:
        """Query actor inventory.

        Supports actor_id parameter for NPC inventory queries.
        Defaults to player if not specified.
        """
        # Get actor_id from message, default to player
        actor_id = message.get("actor_id", "player")

        # Get the actor from unified actors dict
        actor = self.state.actors.get(actor_id)
        if not actor:
            return {
                "type": "error",
                "message": f"Actor not found: {actor_id}"
            }

        items = []
        for item_id in actor.inventory:
            item = self._get_item_by_id(item_id)
            if item:
                items.append(self._entity_to_dict(item))

        return {
            "type": "query_response",
            "query_type": "inventory",
            "data": {"items": items}
        }

    def _query_entity(self, message: Dict) -> Dict:
        """Query a specific entity."""
        entity_type = message.get("entity_type")
        entity_id = message.get("entity_id")

        entity = None
        if entity_type == "item":
            entity = self._get_item_by_id(entity_id)
            if entity:
                entity = self._entity_to_dict(entity)
        elif entity_type == "door":
            entity = self._get_door_by_id(entity_id)
            if entity:
                entity = self._door_to_dict(entity)
        elif entity_type == "npc":
            entity = self._get_npc_by_id(entity_id)
            if entity:
                entity = self._npc_to_dict(entity)
        elif entity_type == "location":
            entity = self._get_location_by_id(entity_id)
            if entity:
                entity = self._location_to_dict(entity)

        if not entity:
            return {
                "type": "error",
                "message": f"Entity not found: {entity_id}"
            }

        return {
            "type": "query_response",
            "query_type": "entity",
            "data": {"entity": entity}
        }

    def _query_entities(self, message: Dict) -> Dict:
        """Query multiple entities of a type."""
        entity_type = message.get("entity_type")
        location_id = message.get("location_id")

        entities = []

        if entity_type == "door":
            loc = self._get_location_by_id(location_id) if location_id else self._get_current_location()
            for door in self.state.doors:
                if loc.id in door.locations:
                    door_dict = self._door_to_dict(door)
                    # Add direction
                    for direction, exit_desc in loc.exits.items():
                        if exit_desc.door_id == door.id:
                            door_dict["direction"] = direction
                            break
                    entities.append(door_dict)
        elif entity_type == "item":
            loc = self._get_location_by_id(location_id) if location_id else self._get_current_location()
            for item in self.state.items:
                if item.location == loc.id:
                    entities.append(self._entity_to_dict(item))
        elif entity_type == "npc":
            loc = self._get_location_by_id(location_id) if location_id else self._get_current_location()
            for npc in self.state.npcs:
                if npc.location == loc.id:
                    entities.append(self._npc_to_dict(npc))

        return {
            "type": "query_response",
            "query_type": "entities",
            "data": {"entities": entities}
        }

    def _query_vocabulary(self, message: Dict) -> Dict:
        """Query game vocabulary."""
        # Vocabulary is now loaded from vocabulary.json and behavior modules,
        # not stored in game state
        return {
            "type": "query_response",
            "query_type": "vocabulary",
            "data": {
                "aliases": {},
                "verbs": {},
                "nouns": {},
                "adjectives": {}
            }
        }

    def _query_metadata(self, message: Dict) -> Dict:
        """Query game metadata."""
        return {
            "type": "query_response",
            "query_type": "metadata",
            "data": {
                "title": self.state.metadata.title,
                "author": self.state.metadata.author,
                "version": self.state.metadata.version,
                "description": self.state.metadata.description
            }
        }

    # Helper methods

    def _get_current_location(self):
        """Get current location object."""
        for loc in self.state.locations:
            if loc.id == self.state.player.location:
                return loc
        return None

    def _get_location_by_id(self, loc_id: str):
        """Get location by ID."""
        for loc in self.state.locations:
            if loc.id == loc_id:
                return loc
        return None

    def _get_item_by_id(self, item_id: str):
        """Get item by ID."""
        for item in self.state.items:
            if item.id == item_id:
                return item
        return None

    def _get_door_by_id(self, door_id: str):
        """Get door by ID."""
        for door in self.state.doors:
            if door.id == door_id:
                return door
        return None

    def _get_npc_by_id(self, npc_id: str):
        """Get NPC by ID."""
        for npc in self.state.npcs:
            if npc.id == npc_id:
                return npc
        return None

    def _get_lock_by_id(self, lock_id: str):
        """Get lock by ID."""
        for lock in self.state.locks:
            if lock.id == lock_id:
                return lock
        return None

    def _get_doors_in_location(self):
        """Get all doors in current location."""
        loc = self._get_current_location()
        doors = []
        for door in self.state.doors:
            if loc.id in door.locations:
                doors.append(door)
        return doors

    def _get_container_for_item(self, item):
        """Get the container that holds this item, if any."""
        if item.location.startswith("item_"):
            container = self._get_item_by_id(item.location)
            if container and container.properties.get("container"):
                return container
        return None

    def _get_adjectives(self, action: Dict):
        """Extract adjectives from action, supporting both single and multiple."""
        # Support both 'adjective' (string) and 'adjectives' (list)
        adjectives = action.get("adjectives", [])
        if not adjectives:
            adj = action.get("adjective")
            if adj:
                # Handle space-separated adjectives (from parser)
                adjectives = adj.split()
        return [a.lower() for a in adjectives if a]

    def _matches_adjectives(self, description: str, adjectives: list) -> bool:
        """Check if all adjectives appear in description."""
        if not adjectives:
            return True
        desc_lower = description.lower()
        return all(adj in desc_lower for adj in adjectives)

    def _select_door(self, doors, adjective):
        """Select a door based on adjective or default to first closed/locked."""
        # Convert single adjective to list for unified handling
        if isinstance(adjective, str) and adjective:
            adjectives = adjective.lower().split()
        elif isinstance(adjective, list):
            adjectives = [a.lower() for a in adjective if a]
        else:
            adjectives = []

        if adjectives:
            # Try to match by adjectives in description
            for door in doors:
                if self._matches_adjectives(door.description, adjectives):
                    return door
                # Check if any adjective is a direction
                loc = self._get_current_location()
                for direction, exit_desc in loc.exits.items():
                    if exit_desc.door_id == door.id and direction in adjectives:
                        return door

        # Default: prioritize locked/closed doors
        for door in doors:
            if door.properties.get("locked", False) or not door.properties.get("open", False):
                return door
        return doors[0]

    def _entity_to_dict(self, item) -> Dict:
        """Convert item to dict with llm_context."""
        result = {
            "id": item.id,
            "name": item.name,
            "type": "item",
            "description": item.description
        }

        # Add llm_context if available (stored in properties)
        if item.properties.get('llm_context'):
            result["llm_context"] = item.properties['llm_context']

        # Add lit state if present (in states dict within properties)
        states = item.properties.get('states', {})
        if states.get('lit'):
            result["lit"] = states['lit']

        # Add provides_light property if present
        if item.properties.get('provides_light'):
            result["provides_light"] = item.properties['provides_light']

        # Add container location info if item is on a surface or in a container
        container = self._get_container_for_item(item)
        if container:
            container_props = container.properties.get("container", {})
            if container_props.get("is_surface", False):
                result["on_surface"] = container.name
            else:
                result["in_container"] = container.name

        return result

    def _door_to_dict(self, door) -> Dict:
        """Convert door to dict with llm_context."""
        description = door.properties.get("description", "")
        result = {
            "id": door.id,
            "description": description,
            "open": door.properties.get("open", False),
            "locked": door.properties.get("locked", False)
        }

        # Get door name from description for consistency
        # Extract adjective from description for name
        desc_words = description.lower().split()
        adjective = next((word for word in desc_words
                        if word in ["wooden", "iron", "heavy", "simple", "golden", "ancient"]),
                       "")
        result["name"] = f"{adjective} door" if adjective else "door"

        # Add llm_context if available
        if door.properties.get('llm_context'):
            result["llm_context"] = door.properties['llm_context']

        return result

    def _location_to_dict(self, loc) -> Dict:
        """Convert location to dict with llm_context."""
        result = {
            "id": loc.id,
            "name": loc.name,
            "description": loc.description
        }

        # Add llm_context if available
        if loc.properties.get('llm_context'):
            result["llm_context"] = loc.properties['llm_context']

        return result

    def _npc_to_dict(self, npc) -> Dict:
        """Convert NPC to dict with llm_context."""
        return self._actor_to_dict(npc)

    def _actor_to_dict(self, actor) -> Dict:
        """Convert Actor to dict with llm_context."""
        result = {
            "id": actor.id,
            "name": actor.name,
            "description": actor.description
        }

        # Add llm_context if stored in properties
        if actor.properties.get('llm_context'):
            result["llm_context"] = actor.properties['llm_context']

        return result


# Backward compatibility alias
JSONProtocolHandler = LLMProtocolHandler
