"""
NarrationAssembler - Constructs NarrationPlan from handler results.

This module provides the NarrationAssembler class that takes a HandlerResult
and game state context, and builds a complete NarrationPlan for the LLM narrator.

The assembler is responsible for:
1. Building primary_text from handler's primary field
2. Building secondary_beats from handler beats + entity traits
3. Building viewpoint from actor posture/focus state
4. Building scope from verb type and success
5. Building entity_refs from game state
6. Building must_mention (exits_text for location scenes)

See docs/game_engine_narration_api_design.md for full specification.
"""
import random
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING, cast

from src.narration_types import (
    NarrationPlan,
    ViewpointInfo,
    ScopeInfo,
    EntityRef,
    EntityState,
    MustMention,
)
from src.state_accessor import HandlerResult
from src.types import ActorId

if TYPE_CHECKING:
    from src.state_accessor import StateAccessor
    from src.state_manager import Location, Item, Actor


# Verbs that trigger location_entry scene_kind
LOCATION_ENTRY_VERBS = {"go", "north", "south", "east", "west", "up", "down",
                        "northeast", "northwest", "southeast", "southwest",
                        "n", "s", "e", "w", "ne", "nw", "se", "sw"}

# Verbs that trigger look scene_kind
LOOK_VERBS = {"look", "l", "examine", "x", "inspect"}


class NarrationAssembler:
    """
    Assembles NarrationPlan from HandlerResult and game state context.

    The assembler extracts all information the LLM needs for narration,
    eliminating the need for conditional reasoning in the narrator.

    Usage:
        assembler = NarrationAssembler(accessor, actor_id)
        plan = assembler.assemble(result, verb, "full", "new")
    """

    def __init__(self, accessor: "StateAccessor", actor_id: ActorId):
        """
        Initialize NarrationAssembler.

        Args:
            accessor: StateAccessor for state queries
            actor_id: ID of the actor performing the action
        """
        self.accessor = accessor
        self.actor_id = actor_id

    def assemble(
        self,
        handler_result: HandlerResult,
        verb: str,
        verbosity: Literal["brief", "full"],
        familiarity: Literal["new", "familiar"]
    ) -> NarrationPlan:
        """
        Assemble a complete NarrationPlan from handler result and context.

        Args:
            handler_result: Result from the command handler
            verb: The verb that was executed
            verbosity: "brief" or "full" narration mode
            familiarity: "new" or "familiar" (has player seen this before)

        Returns:
            NarrationPlan with all information needed for narration
        """
        plan: NarrationPlan = {}

        # 0. Include the action verb for precise narration
        plan["action_verb"] = verb

        # 1. Build primary_text (direct from handler)
        plan["primary_text"] = handler_result.primary

        # 2. Build secondary_beats
        plan["secondary_beats"] = self._build_secondary_beats(
            handler_result, verbosity
        )

        # 3. Build viewpoint
        plan["viewpoint"] = self._build_viewpoint()

        # 4. Build scope
        plan["scope"] = self._build_scope(verb, handler_result.success, familiarity)

        # 5. Build entity_refs (for full verbosity or location scenes)
        scene_kind = plan["scope"]["scene_kind"]
        if verbosity == "full" or scene_kind in ("location_entry", "look"):
            plan["entity_refs"] = self._build_entity_refs(handler_result)
        else:
            plan["entity_refs"] = {}

        # 6. Build must_mention (exits_text for location scenes, available_topics for dialog)
        must_mention = self._build_must_mention(scene_kind, handler_result)
        if must_mention:
            plan["must_mention"] = must_mention

        # 7. Build target_state for door/container actions (top-level for visibility)
        target_state = self._build_target_state(handler_result)
        if target_state:
            plan["target_state"] = target_state

        # 8. Pass through context (author-defined narrator context)
        if handler_result.context:
            plan["context"] = handler_result.context

        # 9. Pass through hints (author-defined style hints)
        if handler_result.hints:
            plan["hints"] = handler_result.hints

        # 10. Pass through fragments (pre-selected narration fragments)
        if handler_result.fragments:
            plan["fragments"] = handler_result.fragments

        # 11. Pass through reactions (multi-entity reactions)
        if handler_result.reactions:
            plan["reactions"] = handler_result.reactions

        return plan

    def _build_secondary_beats(
        self,
        handler_result: HandlerResult,
        verbosity: Literal["brief", "full"]
    ) -> List[str]:
        """
        Build secondary_beats from handler beats and entity traits.

        Args:
            handler_result: Handler result containing beats
            verbosity: Affects whether to include trait beats

        Returns:
            List of beat strings
        """
        beats: List[str] = []

        # Include handler-provided beats
        if handler_result.beats:
            beats.extend(handler_result.beats)

        # For full verbosity, add trait beats from entities in result.data
        if verbosity == "full" and handler_result.data:
            trait_beats = self._extract_trait_beats(handler_result.data)
            beats.extend(trait_beats)

        return beats

    def _extract_trait_beats(self, data: Dict[str, Any], max_traits: int = 2) -> List[str]:
        """
        Extract trait beats from handler result data.

        Looks for llm_context.traits in the data and selects random traits
        to use as supplementary beats.

        Args:
            data: Handler result data dict
            max_traits: Maximum number of traits to extract

        Returns:
            List of trait strings suitable as beats
        """
        traits: List[str] = []

        # Check for llm_context at top level
        if "llm_context" in data:
            llm_context = data["llm_context"]
            if isinstance(llm_context, dict) and "traits" in llm_context:
                entity_traits = llm_context["traits"]
                if isinstance(entity_traits, list):
                    # Shuffle and limit
                    selected = list(entity_traits)
                    random.shuffle(selected)
                    traits.extend(selected[:max_traits])

        return traits

    def _build_viewpoint(self) -> ViewpointInfo:
        """
        Build viewpoint from actor's posture and focus state.

        Returns:
            ViewpointInfo with mode, posture, and focus_name
        """
        viewpoint: ViewpointInfo = {}

        actor = self.accessor.get_actor(self.actor_id)
        if not actor:
            viewpoint["mode"] = "ground"
            return viewpoint

        posture = actor.properties.get("posture")
        focused_on = actor.properties.get("focused_on")

        # Determine mode from posture
        if posture in ("climbing", "on_surface"):
            viewpoint["mode"] = "elevated"
        elif posture in ("behind_cover", "cover", "concealed"):
            viewpoint["mode"] = "concealed"
        else:
            viewpoint["mode"] = "ground"

        # Include posture if non-null
        if posture:
            # Normalize posture values
            if posture == "cover":
                viewpoint["posture"] = "behind_cover"
            elif posture in ("climbing", "on_surface", "behind_cover"):
                viewpoint["posture"] = posture
            else:
                # Other postures (like "concealed") - include if they map
                pass

        # Resolve focus_name from focused entity
        if focused_on:
            focused_entity = self.accessor.get_item(focused_on)
            if focused_entity and hasattr(focused_entity, "name"):
                viewpoint["focus_name"] = focused_entity.name

        return viewpoint

    def _build_scope(
        self,
        verb: str,
        success: bool,
        familiarity: Literal["new", "familiar"]
    ) -> ScopeInfo:
        """
        Build scope from verb, success, and familiarity.

        Args:
            verb: The command verb
            success: Whether the action succeeded
            familiarity: "new" or "familiar"

        Returns:
            ScopeInfo with scene_kind, outcome, and familiarity
        """
        # Determine scene_kind from verb
        verb_lower = verb.lower()
        if verb_lower in LOCATION_ENTRY_VERBS:
            scene_kind: Literal["location_entry", "look", "action_result"] = "location_entry"
        elif verb_lower in LOOK_VERBS:
            scene_kind = "look"
        else:
            scene_kind = "action_result"

        # Map success to outcome
        outcome: Literal["success", "failure"] = "success" if success else "failure"

        return ScopeInfo(
            scene_kind=scene_kind,
            outcome=outcome,
            familiarity=familiarity
        )

    def _build_entity_refs(
        self,
        handler_result: HandlerResult
    ) -> Dict[str, EntityRef]:
        """
        Build entity_refs from handler result and game state.

        For action_result scenes, includes entities from handler.data.
        For location scenes, could include visible entities (future work).

        Args:
            handler_result: Handler result with optional data

        Returns:
            Dict mapping entity IDs to EntityRef
        """
        entity_refs: Dict[str, EntityRef] = {}

        # Get player context for spatial relations
        player_context = self._get_player_context()

        # Extract entity from handler.data if present
        if handler_result.data:
            data = handler_result.data

            # Check for entity at top level (e.g., examine result)
            entity_id = data.get("id")
            if entity_id:
                entity_ref = self._build_entity_ref_from_data(data, player_context)
                if entity_ref:
                    entity_refs[entity_id] = entity_ref

            # Check for nested entities (items, actors, etc.)
            for key in ("items", "doors", "actors"):
                entities = data.get(key, [])
                if isinstance(entities, list):
                    for entity_data in entities:
                        if isinstance(entity_data, dict):
                            eid = entity_data.get("id")
                            if eid:
                                ref = self._build_entity_ref_from_data(
                                    entity_data, player_context
                                )
                                if ref:
                                    entity_refs[eid] = ref

        return entity_refs

    def _build_entity_ref_from_data(
        self,
        data: Dict[str, Any],
        player_context: Dict[str, Any]
    ) -> Optional[EntityRef]:
        """
        Build EntityRef from serialized entity data.

        Args:
            data: Entity data dict (from entity_serializer)
            player_context: Player positioning context

        Returns:
            EntityRef or None if data is insufficient
        """
        name = data.get("name")
        if not name:
            return None

        entity_ref: EntityRef = {"name": name}

        # Add type if present
        entity_type = data.get("type")
        if entity_type in ("item", "container", "door", "actor", "exit", "location"):
            entity_ref["type"] = entity_type

        # Add traits from llm_context
        llm_context = data.get("llm_context", {})
        if isinstance(llm_context, dict):
            traits = llm_context.get("traits", [])
            if isinstance(traits, list) and traits:
                entity_ref["traits"] = traits

        # Add spatial_relation if present
        spatial = data.get("spatial_relation")
        if spatial in ("within_reach", "below", "above", "nearby"):
            entity_ref["spatial_relation"] = spatial

        # Add state flags
        state: EntityState = {}
        if "open" in data:
            state["open"] = bool(data["open"])
        if "locked" in data:
            state["locked"] = bool(data["locked"])
        if "lit" in data:
            state["lit"] = bool(data["lit"])
        if state:
            entity_ref["state"] = state

        # Default salience (could be computed based on action context)
        entity_ref["salience"] = "medium"

        return entity_ref

    def _get_player_context(self) -> Dict[str, Any]:
        """
        Get player context for spatial relation computation.

        Returns:
            Dict with posture and focused_on
        """
        actor = self.accessor.get_actor(self.actor_id)
        if not actor:
            return {"posture": None, "focused_on": None}

        return {
            "posture": actor.properties.get("posture"),
            "focused_on": actor.properties.get("focused_on")
        }

    def _build_must_mention(
        self,
        scene_kind: Literal["location_entry", "look", "action_result"],
        handler_result: HandlerResult
    ) -> Optional[MustMention]:
        """
        Build must_mention fields (exits_text for location scenes, dialog_topics for dialog).

        Args:
            scene_kind: The type of scene
            handler_result: The handler result containing data

        Returns:
            MustMention dict or None if not applicable
        """
        result: Dict[str, Any] = {}

        # Include exits_text for location-related scenes
        if scene_kind in ("location_entry", "look"):
            actor = self.accessor.get_actor(self.actor_id)
            if actor:
                location = self.accessor.get_location(actor.location)
                if location:
                    visible_exits = self.accessor.get_visible_exits(location.id, self.actor_id)
                    if visible_exits:
                        exits_text = self._format_exits_text(visible_exits)
                        if exits_text:
                            result["exits_text"] = exits_text

        # Include available_topics for dialog actions
        if handler_result.data and "available_topics" in handler_result.data:
            topics = handler_result.data["available_topics"]
            if topics:
                # Format as explicit instruction for narrator
                topic_str = ", ".join(topics)
                result["dialog_topics"] = f"You can ask about: {topic_str}"

        if result:
            return cast(MustMention, result)

        return None

    def _format_exits_text(self, exits: Dict[str, Any]) -> str:
        """
        Format visible exits into prose text.

        For exits blocked by closed doors, only show the exit name (e.g., "ornate door")
        without the destination, since you can't see through a closed door.

        Args:
            exits: Dict of direction -> Exit entity

        Returns:
            Formatted exits text
        """
        if not exits:
            return ""

        exit_parts: List[str] = []

        for direction, exit_entity in exits.items():
            # Check if exit has a closed door
            door_is_closed = self._is_door_closed(exit_entity)

            # Handle named exits
            if exit_entity.name:
                # Get destination name if available and door is not closed
                dest_name = None
                if not door_is_closed:
                    dest_name = self._get_destination_name(exit_entity)

                if dest_name:
                    exit_parts.append(f"{direction} ({exit_entity.name} to {dest_name})")
                else:
                    exit_parts.append(f"{direction} ({exit_entity.name})")
            else:
                # Simple direction exit (no name)
                # For unnamed exits with closed doors, show just direction
                if door_is_closed:
                    exit_parts.append(direction)
                else:
                    dest_name = self._get_destination_name(exit_entity)
                    if dest_name:
                        exit_parts.append(f"{direction} to {dest_name}")
                    else:
                        exit_parts.append(direction)

        if len(exit_parts) == 1:
            return f"There is an exit {exit_parts[0]}."
        elif len(exit_parts) == 2:
            return f"Exits lead {exit_parts[0]} and {exit_parts[1]}."
        else:
            all_but_last = ", ".join(exit_parts[:-1])
            return f"Exits lead {all_but_last}, and {exit_parts[-1]}."

    def _get_destination_name(self, exit_entity: Any) -> Optional[str]:
        """
        Get the destination location name for an exit.

        Args:
            exit_entity: Exit entity

        Returns:
            Destination location name or None
        """
        # Get destination by traversing connections
        if not exit_entity.connections:
            return None

        # Get first connected exit
        connected_exit_id = exit_entity.connections[0]
        try:
            connected_exit = self.accessor.game_state.get_exit(connected_exit_id)
            dest_id = connected_exit.location
        except (KeyError, AttributeError):
            return None

        dest_location = self.accessor.get_location(dest_id)
        if dest_location:
            return dest_location.name

        return None

    def _is_door_closed(self, exit_entity: Any) -> bool:
        """
        Check if an exit is blocked by a closed door.

        Args:
            exit_entity: Exit entity

        Returns:
            True if exit has a door and door is closed, False otherwise
        """
        # Check if exit has a door_id attribute
        if not hasattr(exit_entity, 'door_id') or not exit_entity.door_id:
            return False

        # Get the door item
        door = self.accessor.get_door_item(exit_entity.door_id)
        if not door:
            return False

        # Check if door is closed using the door_open property
        return not door.door_open

    def _build_target_state(
        self,
        handler_result: HandlerResult
    ) -> Optional[EntityState]:
        """
        Build target_state for door/container actions.

        Extracts open/locked state from handler result data and returns it
        as a top-level field for high visibility to the narrator.

        Args:
            handler_result: Handler result with optional data

        Returns:
            EntityState dict or None if not applicable
        """
        if not handler_result.data:
            return None

        data = handler_result.data
        state: EntityState = {}

        # Check for open/locked state in the data (from entity_serializer)
        if "open" in data:
            state["open"] = bool(data["open"])
        if "locked" in data:
            state["locked"] = bool(data["locked"])
        if "lit" in data:
            state["lit"] = bool(data["lit"])

        return state if state else None
