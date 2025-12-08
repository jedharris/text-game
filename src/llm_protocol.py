"""
LLM protocol handler for LLM-Game Engine communication.

Implements the JSON interaction protocol as specified in LLM_game_interaction.md.
Processes commands and queries, returning structured JSON results.
"""

import json
import random
from typing import Any, Dict, List, Optional

from .state_manager import GameState
from .behavior_manager import BehaviorManager
from .word_entry import WordEntry, WordType
from . import hooks


class LLMProtocolHandler:
    """
    Handler for JSON protocol messages between LLM and game engine.

    Processes JSON commands and queries, returning structured JSON results
    conforming to the specification.
    """

    # Meta commands that should still work after state corruption
    # These are handled by behavior modules but need to remain functional
    # even when game state is corrupted
    META_COMMANDS = {"save", "quit", "help", "load"}

    # Turn phase hooks fire in this order after successful commands
    # Each hook may have an event registered that processes the phase
    TURN_PHASE_HOOKS = [
        hooks.NPC_ACTION,
        hooks.ENVIRONMENTAL_EFFECT,
        hooks.CONDITION_TICK,
        hooks.DEATH_CHECK,
    ]

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
        match message.get("type"):
            case "command":
                return self.handle_command(message)
            case "query":
                return self.handle_query(message)
            case _:
                return {
                    "type": "error",
                    "message": f"Unknown message type: {message.get('type')}"
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

    def _convert_action_strings_to_wordentry(self, action: Dict) -> Dict:
        """
        Convert string fields in action dict to WordEntry objects.

        Handlers expect object and indirect_object as WordEntry objects.
        Adjectives, prepositions, and verbs remain as strings.

        Args:
            action: Action dict that may contain strings

        Returns:
            Action dict with WordEntry objects for object/indirect_object fields
        """
        action = action.copy()  # Don't modify original

        # Convert object to WordEntry if it's a string
        if "object" in action and isinstance(action["object"], str):
            action["object"] = WordEntry(
                word=action["object"],
                word_type=WordType.NOUN,
                synonyms=[]
            )

        # Convert indirect_object to WordEntry if it's a string
        if "indirect_object" in action and isinstance(action["indirect_object"], str):
            action["indirect_object"] = WordEntry(
                word=action["indirect_object"],
                word_type=WordType.NOUN,
                synonyms=[]
            )

        return action

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

        # Convert string fields to WordEntry objects for handlers
        action = self._convert_action_strings_to_wordentry(action)

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
                response = {
                    "type": "result",
                    "success": True,
                    "action": verb,
                    "message": result.message
                }
                # Include optional data (e.g., llm_context for examine)
                if result.data:
                    response["data"] = result.data

                # Fire turn phase hooks after successful command
                turn_messages = self._fire_turn_phases(accessor, action)
                if turn_messages:
                    response["turn_phase_messages"] = turn_messages

                return response
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
        player = self.state.actors.get("player")
        context = {
            "location": player.location if player else "",
            "verb": verb
        }

        # Invoke behavior (fallbacks are handled automatically by invoke_behavior)
        behavior_result = self.behavior_manager.invoke_behavior(
            entity_obj, event_name, self.state, context
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

    def _fire_turn_phases(self, accessor, action: Dict) -> List[str]:
        """
        Fire turn phase hooks after a successful command.

        Turn phases run in order: NPC_ACTION, ENVIRONMENTAL_EFFECT,
        CONDITION_TICK, DEATH_CHECK. Each phase may have an event
        registered via vocabulary that handles the phase logic.

        Args:
            accessor: StateAccessor for state queries
            action: The action dict from the command

        Returns:
            List of messages from turn phase handlers
        """
        messages = []

        for hook_name in self.TURN_PHASE_HOOKS:
            event_name = self.behavior_manager.get_event_for_hook(hook_name)
            if event_name:
                # Build context for the turn phase
                context = {
                    "hook": hook_name,
                    "actor_id": action.get("actor_id", "player"),
                }

                # Invoke behaviors registered for this event
                # Note: For turn phases, we don't have a specific entity target,
                # so we pass None and let the behavior handle iteration
                result = self.behavior_manager.invoke_behavior(
                    None, event_name, accessor, context
                )

                if result and result.message:
                    messages.append(result.message)

        return messages

    def handle_query(self, message: Dict) -> Dict:
        """Process a query message and return response."""
        match message.get("query_type"):
            case "location":
                return self._query_location(message)
            case "entity":
                return self._query_entity(message)
            case "entities":
                return self._query_entities(message)
            case "vocabulary":
                return self._query_vocabulary(message)
            case "metadata":
                return self._query_metadata(message)
            case _:
                return {
                    "type": "error",
                    "message": f"Unknown query type: {message.get('query_type')}"
                }

    # Query handlers

    def _query_location(self, message: Dict) -> Dict:
        """Query current location.

        Uses serialize_location_for_llm for unified serialization.
        """
        from utilities.location_serializer import serialize_location_for_llm
        from src.state_accessor import StateAccessor

        loc = self._get_current_location()
        include = message.get("include", [])
        actor_id = message.get("actor_id", "player")

        accessor = StateAccessor(self.state, self.behavior_manager)
        full_data = serialize_location_for_llm(accessor, loc, actor_id)

        # Filter to only included sections (empty include means all)
        if include:
            data = {"location": full_data["location"]}
            for key in ["items", "doors", "exits", "actors"]:
                if key in include:
                    data[key] = full_data[key]
        else:
            data = full_data

        return {
            "type": "query_response",
            "query_type": "location",
            "data": data
        }

    def _query_entity(self, message: Dict) -> Dict:
        """Query a specific entity."""
        entity_type = message.get("entity_type")
        entity_id = message.get("entity_id")

        # Map entity types to (getter, converter) tuples
        entity_handlers = {
            "item": (self._get_item_by_id, self._entity_to_dict),
            "door": (self._get_door_by_id, self._door_to_dict),
            "npc": (self._get_actor_by_id, self._actor_to_dict),
            "location": (self._get_location_by_id, self._location_to_dict),
        }

        entity = None
        if handler := entity_handlers.get(entity_type):
            getter, converter = handler
            if raw_entity := getter(entity_id):
                entity = converter(raw_entity)

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
        loc = self._get_location_by_id(location_id) if location_id else self._get_current_location()

        match entity_type:
            case "door":
                seen_door_ids = set()
                # Check for door items through exits
                for direction, exit_desc in loc.exits.items():
                    if exit_desc.door_id:
                        door = self._get_door_by_id(exit_desc.door_id)
                        if door and exit_desc.door_id not in seen_door_ids:
                            seen_door_ids.add(exit_desc.door_id)
                            door_dict = self._door_to_dict(door)
                            door_dict["direction"] = direction
                            entities.append(door_dict)
            case "item":
                for item in self.state.items:
                    if item.location == loc.id:
                        entities.append(self._entity_to_dict(item))
            case "npc":
                for actor_id, actor in self.state.actors.items():
                    if actor_id != "player" and actor.location == loc.id:
                        entities.append(self._actor_to_dict(actor))

        return {
            "type": "query_response",
            "query_type": "entities",
            "data": {"entities": entities}
        }

    def _query_vocabulary(self, message: Dict) -> Dict:
        """Query game vocabulary.

        Returns merged vocabulary from vocabulary.json and behavior modules.
        Includes verbs with their synonyms, required parameters, and directions.

        NOTE: Directions are now first-class nouns with multi-valued word_type.
        They are extracted from the nouns list by checking for word_type containing
        both "noun" and "adjective".
        """
        from pathlib import Path
        import json

        # Load base vocabulary from vocabulary.json
        vocab_file = Path(__file__).parent / "vocabulary.json"
        if vocab_file.exists():
            try:
                base_vocab = json.loads(vocab_file.read_text())
            except (json.JSONDecodeError, IOError):
                base_vocab = {"verbs": [], "nouns": []}
        else:
            base_vocab = {"verbs": [], "nouns": []}

        # Merge with behavior module vocabulary
        if self.behavior_manager:
            vocab = self.behavior_manager.get_merged_vocabulary(base_vocab)
        else:
            vocab = base_vocab

        # Format verbs for response
        verbs = {}
        for verb_data in vocab.get("verbs", []):
            word = verb_data["word"]
            verbs[word] = {
                "synonyms": verb_data.get("synonyms", []),
                "object_required": verb_data.get("object_required", False)
            }

        # Extract directions (directions have multi-valued word_type with "noun" and "adjective")
        # Check all sections since merged words might end up in verbs or nouns section
        directions = {}
        for section in ["verbs", "nouns"]:
            for word_data in vocab.get(section, []):
                word_type = word_data.get("word_type")
                # Check if word_type is a list containing both "noun" and "adjective"
                if isinstance(word_type, list):
                    word_type_lower = [wt.lower() for wt in word_type]
                    if "noun" in word_type_lower and "adjective" in word_type_lower:
                        # This is a direction
                        word = word_data["word"]
                        directions[word] = {
                            "synonyms": word_data.get("synonyms", [])
                        }

        return {
            "type": "query_response",
            "query_type": "vocabulary",
            "data": {
                "verbs": verbs,
                "directions": directions
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
        player = self.state.actors.get("player")
        if not player:
            return None
        for loc in self.state.locations:
            if loc.id == player.location:
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
        """Get door by ID. Only checks door items (unified model)."""
        for item in self.state.items:
            if item.id == door_id and item.is_door:
                return item
        return None

    def _get_actor_by_id(self, actor_id: str):
        """Get actor by ID (excludes player)."""
        if actor_id == "player":
            return None
        return self.state.actors.get(actor_id)

    def _get_lock_by_id(self, lock_id: str):
        """Get lock by ID."""
        for lock in self.state.locks:
            if lock.id == lock_id:
                return lock
        return None


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

    def _add_llm_context(self, result: Dict, properties: Dict) -> None:
        """Add llm_context to result dict, randomizing traits for narration variety.

        DEPRECATED: Use utilities.entity_serializer.entity_to_dict() instead.
        Kept for exit descriptor handling in _query_location which needs
        to work with dict properties rather than entity objects.
        """
        from utilities.entity_serializer import _add_llm_context, _get_llm_context
        # Create a minimal object-like wrapper for the properties
        class PropsWrapper:
            def __init__(self, props):
                self.properties = props
        wrapper = PropsWrapper(properties)
        _add_llm_context(result, wrapper)

    def _entity_to_dict(self, item) -> Dict:
        """Convert item to dict with llm_context.

        Uses unified entity_serializer for base conversion, then adds
        query-specific container location info.
        """
        from utilities.entity_serializer import entity_to_dict

        result = entity_to_dict(item)

        # Add container location info if item is on a surface or in a container
        # This is query-specific context, not needed for command results
        container = self._get_container_for_item(item)
        if container:
            container_props = container.properties.get("container", {})
            if container_props.get("is_surface", False):
                result["on_surface"] = container.name
            else:
                result["in_container"] = container.name

        return result

    def _door_to_dict(self, door) -> Dict:
        """Convert door item to dict with llm_context."""
        from utilities.entity_serializer import entity_to_dict
        return entity_to_dict(door)

    def _location_to_dict(self, loc) -> Dict:
        """Convert location to dict with llm_context."""
        from utilities.entity_serializer import entity_to_dict
        return entity_to_dict(loc)

    def _actor_to_dict(self, actor) -> Dict:
        """Convert Actor to dict with llm_context."""
        from utilities.entity_serializer import entity_to_dict
        return entity_to_dict(actor)
