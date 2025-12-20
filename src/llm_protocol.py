"""
LLM protocol handler for LLM-Game Engine communication.

Implements the JSON interaction protocol as specified in LLM_game_interaction.md.
Processes commands and queries, returning structured JSON results.

As of Phase 4 (Narration API), handle_command returns NarrationResult format
with a NarrationPlan that the LLM narrator can render directly.
"""

import json
import random
from typing import Any, Dict, List, Literal, Optional, Set, Union, TYPE_CHECKING, Callable, Tuple, cast

from src.action_types import ActionDict, CommandMessage, ResultMessage
from src.narration_assembler import NarrationAssembler
from src.narration_types import NarrationResult, NarrationPlan
from .types import ActorId, HookName, ItemId, LocationId

if TYPE_CHECKING:
    from src.state_manager import Location, Item, Actor
    from src.state_accessor import StateAccessor
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

    # Base turn phase hooks fire in this order after successful commands
    # Each hook may have an event registered that processes the phase
    # Games can declare additional phases via metadata.extra_turn_phases
    BASE_TURN_PHASE_HOOKS = [
        hooks.NPC_ACTION,
        hooks.ENVIRONMENTAL_EFFECT,
        hooks.CONDITION_TICK,
        hooks.DEATH_CHECK,
    ]

    def __init__(self, state: GameState, behavior_manager: Optional[BehaviorManager] = None):
        self.state = state
        self.state_corrupted = False

        # Visit tracking for verbosity/familiarity determination
        self.visited_locations: Set[LocationId] = set()
        self.examined_entities: Set[ItemId] = set()

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

    def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
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

    def handle_json_string(self, json_str: str) -> Dict[str, Any]:
        """Parse JSON string and handle the message."""
        try:
            message = json.loads(json_str)
            return self.handle_message(message)
        except json.JSONDecodeError as e:
            return {
                "type": "error",
                "message": f"Invalid JSON: {e}"
            }

    def _convert_action_strings_to_wordentry(self, action: ActionDict) -> ActionDict:
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

    def handle_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a command message and return NarrationResult.

        Returns a NarrationResult with:
        - success: Whether the action succeeded
        - verbosity: "brief" or "full" based on verb and tracking
        - narration: NarrationPlan with all info needed for LLM narration
        - data: Raw engine data for debugging/UI
        """
        import sys

        action: ActionDict = message.get("action", {})
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
            action["actor_id"] = ActorId("player")

        actor_id: ActorId = action.get("actor_id") or ActorId("player")

        # Convert string fields to WordEntry objects for handlers
        action = self._convert_action_strings_to_wordentry(action)

        # Ensure we have a handler for the verb
        if not self.behavior_manager or not self.behavior_manager.has_handler(verb):
            return {
                "type": "result",
                "success": False,
                "action": verb,
                "error": {
                    "message": f"I don't understand '{verb}'. Try actions like go, take, open, or examine."
                }
            }

        from src.state_accessor import StateAccessor
        accessor = StateAccessor(self.state, self.behavior_manager)

        result = self.behavior_manager.invoke_handler(verb, accessor, action)

        if result is None:
            return {
                "type": "result",
                "success": False,
                "action": verb,
                "error": {"message": "No handler registered for verb"}
            }

        # Check for inconsistent state errors
        if not result.success and result.primary.startswith("INCONSISTENT STATE:"):
            self.state_corrupted = True
            print(f"ERROR: {verb}: {result.primary}", file=sys.stderr)
            return {
                "type": "result",
                "success": False,
                "action": verb,
                "error": {
                    "message": result.primary,
                    "fatal": True
                }
            }

        # Determine verbosity and familiarity
        verbosity = self._determine_verbosity(verb, result.success, result.data)
        familiarity = self._determine_familiarity(verb, result.success, result.data)

        # Build NarrationPlan using assembler
        assembler = NarrationAssembler(accessor, actor_id)
        narration_plan = assembler.assemble(result, verb, verbosity, familiarity)

        # Update tracking after successful command
        if result.success:
            self._update_tracking(verb, result.data)

        # Build response
        response: Dict[str, Any] = {
            "type": "result",
            "success": result.success,
            "action": verb,  # Included for backward compatibility
            "verbosity": verbosity,
            "narration": narration_plan,
            "data": result.data or {}
        }

        # Fire turn phase hooks after successful command
        if result.success:
            turn_messages = self._fire_turn_phases(accessor, action)
            if turn_messages:
                response["turn_phase_messages"] = turn_messages

        return response

    def _get_narration_mode(self, verb: str) -> str:
        """
        Look up narration_mode for a verb from merged vocabulary.

        Args:
            verb: The verb to look up

        Returns:
            "brief" or "tracking" (default: "tracking")
        """
        if not self.behavior_manager:
            return "tracking"

        from src.vocabulary_service import build_merged_vocabulary

        vocab = build_merged_vocabulary(self.state, self.behavior_manager)
        for verb_entry in vocab.get("verbs", []):
            if verb_entry.get("word") == verb:
                mode = verb_entry.get("narration_mode", "tracking")
                return str(mode) if mode else "tracking"

        return "tracking"

    def _determine_verbosity(
        self,
        verb: str,
        success: bool,
        data: Optional[Dict[str, Any]]
    ) -> Literal["brief", "full"]:
        """
        Determine verbosity level based on verb, tracking state, and result.

        Args:
            verb: The verb that was executed
            success: Whether the action succeeded
            data: Handler result data

        Returns:
            "brief" or "full"
        """
        narration_mode = self._get_narration_mode(verb)

        # Brief mode is always brief
        if narration_mode == "brief":
            return "brief"

        # Tracking mode: full on first occurrence, brief on subsequent
        # For go/movement: check if destination is new
        if verb == "go" and success and data:
            loc_id = data.get("location", {}).get("id")
            if loc_id and loc_id not in self.visited_locations:
                return "full"
            return "brief"

        # For examine: check if entity is new
        if verb in ("examine", "x", "inspect") and success and data:
            entity_id = data.get("id")
            if entity_id and entity_id not in self.examined_entities:
                return "full"
            return "brief"

        # For look: check if location is new
        if verb in ("look", "l") and success:
            player = self.state.actors.get(ActorId("player"))
            if player and player.location not in self.visited_locations:
                return "full"
            return "brief"

        # Default: full for first time, brief for repeat
        return "full"

    def _determine_familiarity(
        self,
        verb: str,
        success: bool,
        data: Optional[Dict[str, Any]]
    ) -> Literal["new", "familiar"]:
        """
        Determine familiarity based on tracking state.

        Args:
            verb: The verb that was executed
            success: Whether the action succeeded
            data: Handler result data

        Returns:
            "new" or "familiar"
        """
        if not success:
            return "familiar"

        # For movement: check if destination was visited
        if verb == "go" and data:
            loc_id = data.get("location", {}).get("id")
            if loc_id and loc_id not in self.visited_locations:
                return "new"
            return "familiar"

        # For examine: check if entity was examined
        if verb in ("examine", "x", "inspect") and data:
            entity_id = data.get("id")
            if entity_id and entity_id not in self.examined_entities:
                return "new"
            return "familiar"

        # For look: check current location
        if verb in ("look", "l"):
            player = self.state.actors.get(ActorId("player"))
            if player and player.location not in self.visited_locations:
                return "new"
            return "familiar"

        # Default
        return "familiar"

    def _update_tracking(self, verb: str, data: Optional[Dict[str, Any]]) -> None:
        """
        Update visit/examination tracking after successful command.

        Args:
            verb: The verb that was executed
            data: Handler result data
        """
        # Track visited locations on successful movement
        if verb == "go" and data:
            loc_id = data.get("location", {}).get("id")
            if loc_id:
                self.visited_locations.add(LocationId(loc_id))

        # Track examined entities
        if verb in ("examine", "x", "inspect") and data:
            entity_id = data.get("id")
            if entity_id:
                self.examined_entities.add(ItemId(entity_id))

        # Track location on look
        if verb in ("look", "l"):
            player = self.state.actors.get(ActorId("player"))
            if player:
                self.visited_locations.add(player.location)

    def _get_turn_phase_hooks(self) -> List[str]:
        """
        Get the ordered list of turn phase hooks for this game.

        Games can declare additional phases via metadata.extra_turn_phases.
        Extra phases are prepended to base phases (they run first).

        Returns:
            List of hook names in execution order
        """
        extra_phases = self.state.metadata.extra_turn_phases
        return list(extra_phases) + list(self.BASE_TURN_PHASE_HOOKS)

    def _fire_turn_phases(self, accessor: "StateAccessor", action: ActionDict) -> List[str]:
        """
        Fire turn phase hooks after a successful command.

        Turn phases run in order. Base phases are NPC_ACTION, ENVIRONMENTAL_EFFECT,
        CONDITION_TICK, DEATH_CHECK. Games can declare additional phases via
        metadata.extra_turn_phases which run before base phases.

        Each phase may have an event registered via vocabulary that handles
        the phase logic.

        Args:
            accessor: StateAccessor for state queries
            action: The action dict from the command

        Returns:
            List of messages from turn phase handlers
        """
        # Increment turn counter before processing phases
        self.state.increment_turn()

        messages = []

        for hook_name in self._get_turn_phase_hooks():
            event_name = self.behavior_manager.get_event_for_hook(HookName(hook_name))
            if event_name:
                # Build context for the turn phase
                actor_id: ActorId = action.get("actor_id") or ActorId("player")
                context: Dict[str, Any] = {
                    "hook": hook_name,
                    "actor_id": actor_id,
                }

                # Invoke behaviors registered for this event
                # Note: For turn phases, we don't have a specific entity target,
                # so we pass None and let the behavior handle iteration
                result = self.behavior_manager.invoke_behavior(
                    None, event_name, accessor, context
                )

                if result and result.feedback:
                    messages.append(result.feedback)

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
        actor_id = cast(ActorId, message.get("actor_id") or ActorId("player"))

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
        entity_type: str = message.get("entity_type", "")
        entity_id: str = message.get("entity_id", "")

        # Map entity types to (getter, converter) tuples
        entity_handlers: Dict[str, Tuple[Callable[[str], Optional[Any]], Callable[[Any], Dict[str, Any]]]] = {
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
        if loc is None:
            return {
                "type": "error",
                "message": f"Location not found: {location_id}"
            }

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
        Includes verbs with their synonyms and required parameters.

        NOTE: Directions are regular nouns defined in behaviors/core/exits.py
        with multi-valued word_type ["noun", "adjective", "verb"]. They appear
        in the verbs list since they can be used as bare commands (e.g., "north").
        """
        from src.vocabulary_service import build_merged_vocabulary, load_base_vocabulary

        if self.behavior_manager:
            vocab = build_merged_vocabulary(self.state, self.behavior_manager)
        else:
            vocab = load_base_vocabulary()

        # Format verbs for response
        verbs = {}
        for verb_data in vocab.get("verbs", []):
            word = verb_data["word"]
            verbs[word] = {
                "synonyms": verb_data.get("synonyms", []),
                "object_required": verb_data.get("object_required", False)
            }

        return {
            "type": "query_response",
            "query_type": "vocabulary",
            "data": {
                "verbs": verbs
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

    def _get_current_location(self) -> Optional["Location"]:
        """Get current location object."""
        player = self.state.actors.get(ActorId("player"))
        if not player:
            return None
        for loc in self.state.locations:
            if loc.id == player.location:
                return loc
        return None

    def _get_location_by_id(self, loc_id: str) -> Optional["Location"]:
        """Get location by ID."""
        for loc in self.state.locations:
            if loc.id == loc_id:
                return loc
        return None

    def _get_item_by_id(self, item_id: str) -> Optional["Item"]:
        """Get item by ID."""
        for item in self.state.items:
            if item.id == item_id:
                return item
        return None

    def _get_door_by_id(self, door_id: str) -> Optional["Item"]:
        """Get door by ID. Only checks door items (unified model)."""
        for item in self.state.items:
            if item.id == door_id and item.is_door:
                return item
        return None

    def _get_actor_by_id(self, actor_id: str) -> Optional["Actor"]:
        """Get actor by ID (excludes player)."""
        if actor_id == "player":
            return None
        return self.state.actors.get(ActorId(actor_id))

    def _get_container_for_item(self, item: "Item") -> Optional["Item"]:
        """Get the container that holds this item, if any."""
        if item.location.startswith("item_"):
            container = self._get_item_by_id(item.location)
            if container and container.properties.get("container"):
                return container
        return None

    def _get_adjectives(self, action: ActionDict) -> List[str]:
        """Extract adjectives from action, supporting both single and multiple."""
        # Support both 'adjective' (string) and 'adjectives' (list)
        raw_adjs = action.get("adjectives")
        adjectives: list[str] = []
        if isinstance(raw_adjs, list):
            adjectives = [str(a).lower() for a in raw_adjs if a]
        elif isinstance(raw_adjs, str):
            adjectives = [a for a in raw_adjs.lower().split() if a]
        else:
            adj = action.get("adjective")
            if isinstance(adj, str):
                adjectives = [a for a in adj.lower().split() if a]
        return adjectives

    def _matches_adjectives(self, description: str, adjectives: List[str]) -> bool:
        """Check if all adjectives appear in description."""
        if not adjectives:
            return True
        desc_lower = description.lower()
        return all(adj in desc_lower for adj in adjectives)

    def _select_door(self, doors: List["Item"], adjective: Union[str, List[str], None]) -> Optional["Item"]:
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
                if loc:
                    for direction, exit_desc in loc.exits.items():
                        if exit_desc.door_id == door.id and direction in adjectives:
                            return door

        # Default: prioritize locked/closed doors
        for door in doors:
            if door.properties.get("locked", False) or not door.properties.get("open", False):
                return door
        return doors[0]

    def _entity_to_dict(self, item: "Item") -> Dict[str, Any]:
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

    def _door_to_dict(self, door: "Item") -> Dict[str, Any]:
        """Convert door item to dict with llm_context."""
        from utilities.entity_serializer import entity_to_dict
        return entity_to_dict(door)

    def _location_to_dict(self, loc: "Location") -> Dict[str, Any]:
        """Convert location to dict with llm_context."""
        from utilities.entity_serializer import entity_to_dict
        return entity_to_dict(loc)

    def _actor_to_dict(self, actor: "Actor") -> Dict[str, Any]:
        """Convert Actor to dict with llm_context."""
        from utilities.entity_serializer import entity_to_dict
        return entity_to_dict(actor)
