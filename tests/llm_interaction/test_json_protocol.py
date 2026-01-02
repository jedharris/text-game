"""
Comprehensive test suite for LLM-Game Engine JSON interaction protocol.

Tests the JSON message formats for commands, queries, and results
as specified in LLM_game_interaction.md.

Updated for Phase 4 (Narration API) to handle NarrationResult format.
"""
from src.types import ActorId
from typing import Any, Dict

import unittest
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.state_manager import load_game_state, GameState
from src.llm_protocol import LLMProtocolHandler
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager


def get_result_message(result: Dict[str, Any]) -> str:
    """
    Extract message text from result, handling both old and new formats.

    New format (Phase 4): result["narration"]["primary_text"]
    Old format: result["message"] or result["error"]["message"]

    For the new format, also concatenates secondary_beats.
    """
    # New format: NarrationResult
    if "narration" in result:
        narration = result["narration"]
        parts = [narration.get("primary_text", "")]
        if "secondary_beats" in narration:
            parts.extend(narration["secondary_beats"])
        return "\n".join(parts)

    # Old format - success case
    if result.get("success") and "message" in result:
        return result["message"]

    # Old format - error case
    if "error" in result and "message" in result["error"]:
        return result["error"]["message"]

    return result.get("message", "")


class _LLMProtocolHandlerReference:
    """
    Handler for JSON protocol messages between LLM and game engine.

    This is the implementation being tested - it processes JSON commands
    and queries, returning structured JSON results.
    """

    def __init__(self, state: GameState):
        self.game_state = state
        from src.state_accessor import StateAccessor
        from src.behavior_manager import BehaviorManager
        self.accessor = StateAccessor(state, BehaviorManager())

    def handle_message(self, message: dict) -> dict:
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

    def handle_command(self, message: dict) -> dict:
        """Process a command message and return result."""
        action = message.get("action", {})
        verb = action.get("verb")

        if not verb:
            return {
                "type": "error",
                "message": "Missing required field: action"
            }

        # Route to verb handler
        handler = getattr(self, f"_cmd_{verb}", None)
        if handler:
            return handler(action)
        else:
            return {
                "type": "result",
                "success": False,
                "action": verb,
                "error": {
                    "message": f"I don't understand '{verb}'. Try actions like go, take, open, or examine."
                }
            }

    def handle_query(self, message: dict) -> dict:
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

    # Command handlers

    def _cmd_take(self, action: dict) -> dict:
        """Handle take command."""
        obj_name = action.get("object")
        adjective = action.get("adjective")

        if not obj_name:
            return {
                "type": "result",
                "success": False,
                "action": "take",
                "error": {"message": "Take what?"}
            }

        # Find item in current location
        current_loc = self._get_current_location()
        item = None
        for i in self.game_state.items:
            if i.name == obj_name and i.location == current_loc.id:
                item = i
                break

        if not item:
            return {
                "type": "result",
                "success": False,
                "action": "take",
                "error": {"message": "You don't see that here."}
            }

        if not item.portable:
            return {
                "type": "result",
                "success": False,
                "action": "take",
                "entity": self._entity_to_dict(item),
                "error": {"message": "You can't take that."}
            }

        # Move item to inventory
        item.location = "player"
        self.game_state.get_actor(ActorId("player")).inventory.append(item.id)
        if item.id in current_loc.items:
            current_loc.items.remove(item.id)

        return {
            "type": "result",
            "success": True,
            "action": "take",
            "entity": self._entity_to_dict(item)
        }

    def _cmd_drop(self, action: dict) -> dict:
        """Handle drop command."""
        obj_name = action.get("object")

        if not obj_name:
            return {
                "type": "result",
                "success": False,
                "action": "drop",
                "error": {"message": "Drop what?"}
            }

        # Find item in inventory
        item = None
        for item_id in self.game_state.get_actor(ActorId("player")).inventory:
            i = self._get_item_by_id(item_id)
            if i and i.name == obj_name:
                item = i
                break

        if not item:
            return {
                "type": "result",
                "success": False,
                "action": "drop",
                "error": {"message": "You're not carrying that."}
            }

        # Move item to current location
        current_loc = self._get_current_location()
        item.location = current_loc.id
        self.game_state.get_actor(ActorId("player")).inventory.remove(item.id)
        current_loc.items.append(item.id)

        return {
            "type": "result",
            "success": True,
            "action": "drop",
            "entity": self._entity_to_dict(item)
        }

    def _cmd_examine(self, action: dict) -> dict:
        """Handle examine command."""
        obj_name = action.get("object")

        # Examine room if no object specified
        if not obj_name:
            loc = self._get_current_location()
            return {
                "type": "result",
                "success": True,
                "action": "examine",
                "entity": self._location_to_dict(loc)
            }

        # Find item in location or inventory
        item = self._find_accessible_item(obj_name)
        if item:
            return {
                "type": "result",
                "success": True,
                "action": "examine",
                "entity": self._entity_to_dict(item)
            }

        # Check for doors
        if obj_name == "door":
            doors = self._get_doors_in_location()
            if doors:
                # Return first door for now
                return {
                    "type": "result",
                    "success": True,
                    "action": "examine",
                    "entity": self._door_to_dict(doors[0])
                }

        return {
            "type": "result",
            "success": False,
            "action": "examine",
            "error": {"message": "You don't see that here."}
        }

    def _cmd_go(self, action: dict) -> dict:
        """Handle go command."""
        direction = action.get("direction")

        if not direction:
            return {
                "type": "result",
                "success": False,
                "action": "go",
                "error": {"message": "Go where?"}
            }

        current_loc = self._get_current_location()

        if direction not in current_loc.exits:
            return {
                "type": "result",
                "success": False,
                "action": "go",
                "error": {"message": "You can't go that way."}
            }

        exit_desc = current_loc.exits[direction]

        # Check for door
        if exit_desc.type == "door" and exit_desc.door_id:
            door = self._get_door_by_id(exit_desc.door_id)
            if door:
                if not door.open:
                    if door.locked:
                        return {
                            "type": "result",
                            "success": False,
                            "action": "go",
                            "entity": self._door_to_dict(door),
                            "error": {"message": "The door is locked. You need a key."}
                        }
                    else:
                        return {
                            "type": "result",
                            "success": False,
                            "action": "go",
                            "entity": self._door_to_dict(door),
                            "error": {"message": "The door is closed."}
                        }

        # Move player
        new_loc_id = exit_desc.to
        self.accessor.set_entity_where("player", new_loc_id)
        new_loc = self._get_location_by_id(new_loc_id)

        return {
            "type": "result",
            "success": True,
            "action": "go",
            "entity": self._location_to_dict(new_loc)
        }

    def _cmd_open(self, action: dict) -> dict:
        """Handle open command."""
        obj_name = action.get("object")
        adjective = action.get("adjective")

        if not obj_name:
            return {
                "type": "result",
                "success": False,
                "action": "open",
                "error": {"message": "Open what?"}
            }

        # Check for door
        if obj_name == "door":
            doors = self._get_doors_in_location()
            if not doors:
                return {
                    "type": "result",
                    "success": False,
                    "action": "open",
                    "error": {"message": "There is no door here."}
                }

            # Select door by adjective/direction if provided
            door = self._select_door(doors, adjective)

            if door.open:
                return {
                    "type": "result",
                    "success": False,
                    "action": "open",
                    "entity": self._door_to_dict(door),
                    "error": {"message": "The door is already open."}
                }

            if door.locked:
                # Check for key
                if self._player_has_key_for_door(door):
                    door.locked = False
                    door.open = True
                    return {
                        "type": "result",
                        "success": True,
                        "action": "open",
                        "entity": self._door_to_dict(door)
                    }
                else:
                    return {
                        "type": "result",
                        "success": False,
                        "action": "open",
                        "entity": self._door_to_dict(door),
                        "error": {"message": "The door is locked. You need a key."}
                    }

            door.open = True
            return {
                "type": "result",
                "success": True,
                "action": "open",
                "entity": self._door_to_dict(door)
            }

        # Check for chest or other openable items
        item = self._find_accessible_item(obj_name)
        if item:
            if item.name == "chest":
                return {
                    "type": "result",
                    "success": True,
                    "action": "open",
                    "entity": self._entity_to_dict(item)
                }
            else:
                return {
                    "type": "result",
                    "success": False,
                    "action": "open",
                    "entity": self._entity_to_dict(item),
                    "error": {"message": f"You can't open the {obj_name}."}
                }

        return {
            "type": "result",
            "success": False,
            "action": "open",
            "error": {"message": f"There is no {obj_name} here."}
        }

    def _cmd_close(self, action: dict) -> dict:
        """Handle close command."""
        obj_name = action.get("object")

        if obj_name != "door":
            return {
                "type": "result",
                "success": False,
                "action": "close",
                "error": {"message": f"You can't close the {obj_name}."}
            }

        doors = self._get_doors_in_location()
        if not doors:
            return {
                "type": "result",
                "success": False,
                "action": "close",
                "error": {"message": "There is no door here."}
            }

        # Find an open door
        door = None
        for d in doors:
            if d.open:
                door = d
                break

        if not door:
            door = doors[0]
            return {
                "type": "result",
                "success": False,
                "action": "close",
                "entity": self._door_to_dict(door),
                "error": {"message": "The door is already closed."}
            }

        door.open = False
        return {
            "type": "result",
            "success": True,
            "action": "close",
            "entity": self._door_to_dict(door)
        }

    def _cmd_unlock(self, action: dict) -> dict:
        """Handle unlock command."""
        obj_name = action.get("object")
        adjective = action.get("adjective")

        if obj_name != "door":
            return {
                "type": "result",
                "success": False,
                "action": "unlock",
                "error": {"message": f"You can't unlock the {obj_name}."}
            }

        doors = self._get_doors_in_location()
        if not doors:
            return {
                "type": "result",
                "success": False,
                "action": "unlock",
                "error": {"message": "There is no door here."}
            }

        door = self._select_door(doors, adjective)

        if not door.locked:
            return {
                "type": "result",
                "success": False,
                "action": "unlock",
                "entity": self._door_to_dict(door),
                "error": {"message": "The door is not locked."}
            }

        if not self._player_has_key_for_door(door):
            return {
                "type": "result",
                "success": False,
                "action": "unlock",
                "entity": self._door_to_dict(door),
                "error": {"message": "You need the right key."}
            }

        door.locked = False
        return {
            "type": "result",
            "success": True,
            "action": "unlock",
            "entity": self._door_to_dict(door)
        }

    def _cmd_inventory(self, action: dict) -> dict:
        """Handle inventory command."""
        items = []
        for item_id in self.game_state.get_actor(ActorId("player")).inventory:
            item = self._get_item_by_id(item_id)
            if item:
                items.append(self._entity_to_dict(item))

        return {
            "type": "result",
            "success": True,
            "action": "inventory",
            "entity": {
                "type": "inventory",
                "items": items
            }
        }

    # Query handlers

    def _query_location(self, message: dict) -> dict:
        """Query current location."""
        loc = self._get_current_location()
        include = message.get("include", [])

        data: dict = {
            "location": self._location_to_dict(loc)
        }

        if "items" in include or not include:
            items_list = []
            for item in self.game_state.items:
                if item.location == loc.id:
                    items_list.append(self._entity_to_dict(item))
            data["items"] = items_list

        if "doors" in include or not include:
            doors_list = []
            seen_door_ids = set()
            # Doors are found via exits
            for direction, exit_desc in loc.exits.items():
                if exit_desc.door_id and exit_desc.door_id not in seen_door_ids:
                    door = self._get_door_by_id(exit_desc.door_id)
                    if door:
                        seen_door_ids.add(exit_desc.door_id)
                        door_dict = self._door_to_dict(door)
                        door_dict["direction"] = direction
                        doors_list.append(door_dict)
            data["doors"] = doors_list

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

        if "npcs" in include or not include:
            npcs_list = []
            for actor_id, actor in self.game_state.actors.items():
                if actor_id != "player" and actor.location == loc.id:
                    npcs_list.append(self._npc_to_dict(actor))
            data["npcs"] = npcs_list

        return {
            "type": "query_response",
            "query_type": "location",
            "data": data
        }

    def _query_inventory(self, message: dict) -> dict:
        """Query player inventory."""
        items = []
        for item_id in self.game_state.get_actor(ActorId("player")).inventory:
            item = self._get_item_by_id(item_id)
            if item:
                items.append(self._entity_to_dict(item))

        return {
            "type": "query_response",
            "query_type": "inventory",
            "data": {"items": items}
        }

    def _query_entity(self, message: dict) -> dict:
        """Query a specific entity."""
        entity_type = message.get("entity_type")
        entity_id = message.get("entity_id")

        if not entity_id:
            return {
                "type": "error",
                "message": "Missing entity_id"
            }

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

    def _query_entities(self, message: dict) -> dict:
        """Query multiple entities of a type."""
        entity_type = message.get("entity_type")
        location_id = message.get("location_id")

        entities = []

        if entity_type == "door":
            loc = self._get_location_by_id(location_id) if location_id else self._get_current_location()
            if loc:
                seen_door_ids = set()
                # Doors are found via exits
                for direction, exit_desc in loc.exits.items():
                    if exit_desc.door_id and exit_desc.door_id not in seen_door_ids:
                        door = self._get_door_by_id(exit_desc.door_id)
                        if door:
                            seen_door_ids.add(exit_desc.door_id)
                            door_dict = self._door_to_dict(door)
                            door_dict["direction"] = direction
                            entities.append(door_dict)
        elif entity_type == "item":
            loc = self._get_location_by_id(location_id) if location_id else self._get_current_location()
            if loc:
                for item in self.game_state.items:
                    if item.location == loc.id:
                        entities.append(self._entity_to_dict(item))

        return {
            "type": "query_response",
            "query_type": "entities",
            "data": {"entities": entities}
        }

    def _query_vocabulary(self, message: dict) -> dict:
        """Query game vocabulary."""
        # Return basic vocabulary info
        return {
            "type": "query_response",
            "query_type": "vocabulary",
            "data": {
                "verbs": ["take", "drop", "examine", "go", "open", "close", "unlock", "inventory"],
                "nouns": ["sword", "key", "potion", "chest", "door"]
            }
        }

    def _query_metadata(self, message: dict) -> dict:
        """Query game metadata."""
        return {
            "type": "query_response",
            "query_type": "metadata",
            "data": {
                "title": self.game_state.metadata.title,
                "author": self.game_state.metadata.author,
                "version": self.game_state.metadata.version,
                "description": self.game_state.metadata.description
            }
        }

    # Helper methods

    def _get_current_location(self):
        """Get current location object."""
        for loc in self.game_state.locations:
            if loc.id == self.game_state.get_actor(ActorId("player")).location:
                return loc
        return None

    def _get_location_by_id(self, loc_id: str):
        """Get location by ID."""
        for loc in self.game_state.locations:
            if loc.id == loc_id:
                return loc
        return None

    def _get_item_by_id(self, item_id: str):
        """Get item by ID."""
        for item in self.game_state.items:
            if item.id == item_id:
                return item
        return None

    def _get_door_by_id(self, door_id: str):
        """Get door by ID. Doors are items with is_door property."""
        for item in self.game_state.items:
            if item.id == door_id and item.is_door:
                return item
        return None

    def _get_npc_by_id(self, npc_id: str):
        """Get NPC by ID."""
        from src.types import ActorId
        if npc_id == "player":
            return None
        return self.game_state.actors.get(ActorId(npc_id))

    def _get_lock_by_id(self, lock_id: str):
        """Get lock by ID."""
        for lock in self.game_state.locks:
            if lock.id == lock_id:
                return lock
        return None

    def _get_doors_in_location(self):
        """Get all doors in current location."""
        loc = self._get_current_location()
        doors = []
        for door in self.game_state.doors:
            if loc.id in door.locations:
                doors.append(door)
        return doors

    def _find_accessible_item(self, name: str):
        """Find item in location or inventory by name."""
        loc = self._get_current_location()

        # Check location
        for item in self.game_state.items:
            if item.name == name and item.location == loc.id:
                return item

        # Check inventory
        for item_id in self.game_state.get_actor(ActorId("player")).inventory:
            item = self._get_item_by_id(item_id)
            if item and item.name == name:
                return item

        return None

    def _select_door(self, doors, adjective):
        """Select a door based on adjective or default to first closed/locked."""
        if adjective:
            # Try to match by adjective (iron, wooden, etc.) or direction
            for door in doors:
                if adjective.lower() in door.description.lower():
                    return door
                # Check if adjective is a direction
                loc = self._get_current_location()
                for direction, exit_desc in loc.exits.items():
                    if exit_desc.door_id == door.id and direction == adjective.lower():
                        return door

        # Default: prioritize locked/closed doors
        for door in doors:
            if door.locked or not door.open:
                return door
        return doors[0]

    def _player_has_key_for_door(self, door):
        """Check if player has key for door's lock."""
        if not door.lock_id:
            return False

        lock = self._get_lock_by_id(door.lock_id)
        if not lock:
            return False

        return any(key_id in self.game_state.get_actor(ActorId("player")).inventory for key_id in lock.opens_with)

    def _entity_to_dict(self, item) -> dict:
        """Convert item to dict with llm_context."""
        result = {
            "id": item.id,
            "name": item.name,
            "type": "item",
            "description": item.description
        }

        # Add llm_context if available
        if hasattr(item, 'llm_context') and item.llm_context:
            result["llm_context"] = item.llm_context
        elif hasattr(item, 'states') and item.states.get('llm_context'):
            result["llm_context"] = item.states['llm_context']

        return result

    def _door_to_dict(self, door) -> dict:
        """Convert door to dict with llm_context."""
        result = {
            "id": door.id,
            "description": door.description,
            "open": door.open,
            "locked": door.locked
        }

        # Add llm_context if available
        if hasattr(door, 'llm_context') and door.llm_context:
            result["llm_context"] = door.llm_context

        return result

    def _location_to_dict(self, loc) -> dict:
        """Convert location to dict with llm_context."""
        result = {
            "id": loc.id,
            "name": loc.name,
            "description": loc.description
        }

        # Add llm_context if available
        if hasattr(loc, 'llm_context') and loc.llm_context:
            result["llm_context"] = loc.llm_context

        return result

    def _npc_to_dict(self, npc) -> dict:
        """Convert NPC to dict with llm_context."""
        result = {
            "id": npc.id,
            "name": npc.name,
            "description": npc.description
        }

        # Add llm_context if available
        if hasattr(npc, 'llm_context') and npc.llm_context:
            result["llm_context"] = npc.llm_context

        return result


class TestCommandMessages(unittest.TestCase):
    """Test command message handling."""

    def setUp(self):
        """Load test game state."""
        fixtures_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.game_state = load_game_state(str(fixtures_path))
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)
        self.handler = LLMProtocolHandler(self.game_state)

    def test_take_item_success(self):
        """Test successful take command."""
        message = {
            "type": "command",
            "action": {"verb": "take", "object": "key"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "result")
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "take")
        # New format uses message instead of entity
        self.assertIn("narration", result)
        self.assertIn("key", get_result_message(result))

        # Verify state changed
        self.assertIn("item_key", self.game_state.get_actor(ActorId("player")).inventory)

    def test_take_item_not_found(self):
        """Test take command for non-existent item."""
        message = {
            "type": "command",
            "action": {"verb": "take", "object": "diamond"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "result")
        self.assertFalse(result["success"])
        # In new format, errors are indicated by success=False and message in narration
        self.assertIn("narration", result)
        self.assertIn("diamond", get_result_message(result).lower())

    def test_take_non_portable_item(self):
        """Test take command for non-portable item."""
        # Move player to treasure room
        self.accessor.set_entity_where("player", "loc_treasure")

        message = {
            "type": "command",
            "action": {"verb": "take", "object": "chest"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        self.assertIn("can't take", get_result_message(result).lower())

    def test_drop_item_success(self):
        """Test successful drop command."""
        # First take the item
        self.game_state.get_actor(ActorId("player")).inventory.append("item_key")
        self.game_state.items[1].location = "player"  # item_key

        message = {
            "type": "command",
            "action": {"verb": "drop", "object": "key"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "drop")
        self.assertNotIn("item_key", self.game_state.get_actor(ActorId("player")).inventory)

    def test_drop_item_not_in_inventory(self):
        """Test drop command for item not in inventory."""
        message = {
            "type": "command",
            "action": {"verb": "drop", "object": "sword"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        # Check for any message indicating item not in inventory
        error_msg = get_result_message(result).lower()
        self.assertTrue("don't have" in error_msg or "not carrying" in error_msg)

    def test_go_direction_success(self):
        """Test successful movement."""
        message = {
            "type": "command",
            "action": {"verb": "go", "object": "north"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "go")
        self.assertEqual(self.game_state.get_actor(ActorId("player")).location, "loc_hallway")

    def test_go_invalid_direction(self):
        """Test movement in invalid direction."""
        message = {
            "type": "command",
            "action": {"verb": "go", "object": "west"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        self.assertIn("can't go", get_result_message(result).lower())

    def test_go_through_closed_door(self):
        """Test movement through closed door."""
        # Move to hallway and try to go east through locked door
        self.accessor.set_entity_where("player", "loc_hallway")

        message = {
            "type": "command",
            "action": {"verb": "go", "object": "east"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        # Door is closed, message says "closed" not "locked"
        self.assertIn("closed", get_result_message(result).lower())

    def test_open_door_success(self):
        """Test opening an unlocked door."""
        # Close the wooden door first (door is now an item)
        for item in self.game_state.items:
            if item.id == "door_wooden" and item.is_door:
                item.properties["door"]["open"] = False
                break

        message = {
            "type": "command",
            "action": {"verb": "open", "object": "door"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "open")

    def test_open_locked_door_with_key(self):
        """Test opening locked door after unlocking it with key."""
        # Move to hallway
        self.accessor.set_entity_where("player", "loc_hallway")
        # Give player the key
        self.game_state.get_actor(ActorId("player")).inventory.append("item_key")

        # First unlock the door (use adjective + object as parser would produce)
        unlock_msg = {
            "type": "command",
            "action": {"verb": "unlock", "object": "door", "adjective": "iron"}
        }
        unlock_result = self.handler.handle_message(unlock_msg)
        self.assertTrue(unlock_result["success"])

        # Now open the door (use adjective + object as parser would produce)
        message = {
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "iron"}
        }
        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        # Door should now be open and unlocked
        iron_door = self.handler._get_door_by_id("door_iron")
        self.assertTrue(iron_door.door_open)
        self.assertFalse(iron_door.door_locked)

    def test_open_locked_door_without_key(self):
        """Test opening locked door without key."""
        # Move to hallway
        self.accessor.set_entity_where("player", "loc_hallway")
        # Close the wooden door so we can test the iron door (door is now an item)
        for item in self.game_state.items:
            if item.id == "door_wooden" and item.is_door:
                item.properties["door"]["open"] = False
                break

        # Use adjective + object as parser would produce
        message = {
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "iron"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        self.assertIn("locked", get_result_message(result).lower())

    def test_open_already_open_door(self):
        """Test opening already open door."""
        # Wooden door starts open (use adjective + object as parser would produce)
        message = {
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "wooden"}
        }

        result = self.handler.handle_message(message)

        # Behavior handler returns success with informative message
        self.assertTrue(result["success"])
        self.assertIn("already open", get_result_message(result).lower())

    def test_close_door_success(self):
        """Test closing an open door."""
        message = {
            "type": "command",
            "action": {"verb": "close", "object": "door"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "close")

    def test_examine_item(self):
        """Test examining an item."""
        message = {
            "type": "command",
            "action": {"verb": "examine", "object": "sword"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "examine")
        # New format uses message instead of entity
        self.assertIn("narration", result)

    def test_examine_room(self):
        """Test looking at room (no object) - use look verb for room description."""
        # Use "look" verb for room description (examine requires object)
        message = {
            "type": "command",
            "action": {"verb": "look"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        # New format uses message instead of entity
        self.assertIn("narration", result)
        self.assertIn("Small Room", get_result_message(result))

    def test_unlock_door_with_key(self):
        """Test unlocking a door with key."""
        # Move to hallway and give key
        self.accessor.set_entity_where("player", "loc_hallway")
        self.game_state.get_actor(ActorId("player")).inventory.append("item_key")

        # Use adjective "iron" and object "door" (as parser would produce)
        message = {
            "type": "command",
            "action": {"verb": "unlock", "object": "door", "adjective": "iron"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        iron_door = self.handler._get_door_by_id("door_iron")
        # Handle both door items and old-style doors
        if hasattr(iron_door, 'is_door') and iron_door.is_door:
            self.assertFalse(iron_door.door_locked)
        else:
            self.assertFalse(iron_door.locked)

    def test_unlock_door_without_key(self):
        """Test unlocking door without key."""
        self.accessor.set_entity_where("player", "loc_hallway")

        # Use adjective "iron" and object "door" (as parser would produce)
        message = {
            "type": "command",
            "action": {"verb": "unlock", "object": "door", "adjective": "iron"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        self.assertIn("key", get_result_message(result).lower())

    def test_unknown_verb(self):
        """Test command with unknown verb."""
        message = {
            "type": "command",
            "action": {"verb": "teleport", "object": "north"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        self.assertIn("don't understand", get_result_message(result).lower())

    def test_inventory_command(self):
        """Test inventory command."""
        # Add item to inventory
        self.game_state.get_actor(ActorId("player")).inventory.append("item_sword")

        message = {
            "type": "command",
            "action": {"verb": "inventory"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "inventory")


class TestQueryMessages(unittest.TestCase):
    """Test query message handling."""

    def setUp(self):
        """Load test game state."""
        fixtures_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.game_state = load_game_state(str(fixtures_path))
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)
        self.handler = LLMProtocolHandler(self.game_state)

    def test_query_location(self):
        """Test location query."""
        message = {
            "type": "query",
            "query_type": "location",
            "include": ["items", "doors", "exits", "npcs"]
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "query_response")
        self.assertEqual(result["query_type"], "location")
        self.assertIn("data", result)
        self.assertIn("location", result["data"])
        self.assertIn("items", result["data"])
        self.assertIn("doors", result["data"])
        self.assertIn("exits", result["data"])

    def test_query_specific_entity(self):
        """Test entity query for specific item."""
        message = {
            "type": "query",
            "query_type": "entity",
            "entity_type": "item",
            "entity_id": "item_key"
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "query_response")
        self.assertEqual(result["query_type"], "entity")
        self.assertIn("entity", result["data"])
        self.assertEqual(result["data"]["entity"]["id"], "item_key")

    def test_query_entities_doors(self):
        """Test entities query for doors in location."""
        self.accessor.set_entity_where("player", "loc_hallway")

        message = {
            "type": "query",
            "query_type": "entities",
            "entity_type": "door",
            "location_id": "loc_hallway"
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "query_response")
        self.assertEqual(result["query_type"], "entities")
        self.assertIn("entities", result["data"])
        # Hallway has 2 doors (wooden and iron)
        self.assertEqual(len(result["data"]["entities"]), 2)

    def test_query_metadata(self):
        """Test metadata query."""
        message = {
            "type": "query",
            "query_type": "metadata"
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "query_response")
        self.assertEqual(result["query_type"], "metadata")
        self.assertEqual(result["data"]["title"], "LLM Test Game")

    def test_query_vocabulary(self):
        """Test vocabulary query returns verbs."""
        message = {
            "type": "query",
            "query_type": "vocabulary"
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "query_response")
        self.assertEqual(result["query_type"], "vocabulary")
        self.assertIn("verbs", result["data"])

    def test_query_vocabulary_includes_core_verbs(self):
        """Test vocabulary query includes verbs from behavior modules."""
        message = {
            "type": "query",
            "query_type": "vocabulary"
        }

        result = self.handler.handle_message(message)

        verbs = result["data"]["verbs"]
        # Should include core verbs from behavior modules
        self.assertIn("take", verbs)
        self.assertIn("drop", verbs)
        self.assertIn("examine", verbs)
        self.assertIn("go", verbs)
        self.assertIn("open", verbs)
        self.assertIn("close", verbs)
        self.assertIn("look", verbs)

    def test_query_vocabulary_verb_has_synonyms(self):
        """Test vocabulary query includes synonyms for verbs."""
        message = {
            "type": "query",
            "query_type": "vocabulary"
        }

        result = self.handler.handle_message(message)

        verbs = result["data"]["verbs"]
        # Take should have synonyms like "get", "grab", "pick"
        self.assertIn("take", verbs)
        self.assertIn("synonyms", verbs["take"])
        self.assertIsInstance(verbs["take"]["synonyms"], list)

    def test_query_nonexistent_entity(self):
        """Test query for non-existent entity."""
        message = {
            "type": "query",
            "query_type": "entity",
            "entity_type": "item",
            "entity_id": "item_nonexistent"
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "error")
        self.assertIn("not found", get_result_message(result).lower())

    def test_location_query_includes_exit_llm_context(self):
        """Location query includes llm_context for exits that have it."""
        # Add llm_context to an exit - now stored in traits dict
        # Find the "up" exit from loc_hallway
        exit_entity = None
        for exit_e in self.game_state.exits:
            if exit_e.location == "loc_hallway" and exit_e.direction == "up":
                exit_entity = exit_e
                break

        self.assertIsNotNone(exit_entity, "Should find 'up' exit from loc_hallway")
        exit_entity.traits["llm_context"] = {
            "traits": ["spiral staircase", "worn stone steps"],
            "state_variants": {
                "first_visit": "A winding stair leads upward."
            }
        }

        self.accessor.set_entity_where("player", "loc_hallway")

        message = {
            "type": "query",
            "query_type": "location",
            "include": ["exits"]
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "query_response")
        exits = result["data"]["exits"]
        self.assertIn("up", exits)
        self.assertIn("llm_context", exits["up"])
        self.assertIn("spiral staircase", exits["up"]["llm_context"]["traits"])

    def test_location_query_omits_exit_llm_context_when_missing(self):
        """Location query omits llm_context for exits without it."""
        # Ensure exit has no llm_context - check traits dict
        # Find the "north" exit from loc_start
        exit_entity = None
        for exit_e in self.game_state.exits:
            if exit_e.location == "loc_start" and exit_e.direction == "north":
                exit_entity = exit_e
                break

        self.assertIsNotNone(exit_entity, "Should find 'north' exit from loc_start")
        self.assertNotIn("llm_context", exit_entity.traits)

        self.accessor.set_entity_where("player", "loc_start")

        message = {
            "type": "query",
            "query_type": "location",
            "include": ["exits"]
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "query_response")
        exits = result["data"]["exits"]
        self.assertIn("north", exits)
        self.assertNotIn("llm_context", exits["north"])


class TestVocabularyQueryProtocol(unittest.TestCase):
    """Test vocabulary query protocol in detail."""

    def setUp(self):
        """Load test game state."""
        fixtures_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.game_state = load_game_state(str(fixtures_path))
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)
        self.handler = LLMProtocolHandler(self.game_state)

    def test_vocabulary_query_response_structure(self):
        """Test vocabulary query returns correct response structure."""
        message = {"type": "query", "query_type": "vocabulary"}
        result = self.handler.handle_message(message)

        # Check top-level structure
        self.assertEqual(result["type"], "query_response")
        self.assertEqual(result["query_type"], "vocabulary")
        self.assertIn("data", result)

        # Check data structure
        data = result["data"]
        self.assertIn("verbs", data)
        self.assertIsInstance(data["verbs"], dict)

    def test_vocabulary_verb_entry_structure(self):
        """Test each verb entry has correct structure."""
        message = {"type": "query", "query_type": "vocabulary"}
        result = self.handler.handle_message(message)

        verbs = result["data"]["verbs"]
        # Check at least one verb has the expected structure
        self.assertIn("take", verbs)
        take_entry = verbs["take"]

        self.assertIn("synonyms", take_entry)
        self.assertIn("object_required", take_entry)
        self.assertIsInstance(take_entry["synonyms"], list)
        self.assertIsInstance(take_entry["object_required"], bool)

    def test_vocabulary_includes_behavior_module_verbs(self):
        """Test vocabulary merges verbs from behavior modules."""
        message = {"type": "query", "query_type": "vocabulary"}
        result = self.handler.handle_message(message)

        verbs = result["data"]["verbs"]
        # These come from behavior modules (behaviors/core/)
        behavior_verbs = ["take", "drop", "examine", "look", "go", "open", "close", "lock", "unlock", "put"]
        for verb in behavior_verbs:
            self.assertIn(verb, verbs, f"Missing behavior verb: {verb}")

    def test_vocabulary_verb_synonyms_populated(self):
        """Test verbs have their synonyms populated."""
        message = {"type": "query", "query_type": "vocabulary"}
        result = self.handler.handle_message(message)

        verbs = result["data"]["verbs"]

        # 'take' should have synonyms like 'get', 'grab', 'pick'
        take_synonyms = verbs["take"]["synonyms"]
        self.assertTrue(len(take_synonyms) > 0, "take should have synonyms")
        self.assertIn("get", take_synonyms)

        # 'examine' should have synonyms like 'look at', 'inspect', 'x'
        examine_synonyms = verbs["examine"]["synonyms"]
        self.assertTrue(len(examine_synonyms) > 0, "examine should have synonyms")

    def test_vocabulary_object_required_varies(self):
        """Test object_required varies appropriately between verbs.

        object_required can be:
        - True: object is required
        - False: object is not used
        - "optional": object is optional
        """
        message = {"type": "query", "query_type": "vocabulary"}
        result = self.handler.handle_message(message)

        verbs = result["data"]["verbs"]

        # 'take' requires an object
        self.assertEqual(verbs["take"]["object_required"], True)

        # 'look' has optional object (look vs look at X)
        self.assertIn(verbs["look"]["object_required"], [False, "optional"])

        # 'inventory' does not require an object
        self.assertEqual(verbs["inventory"]["object_required"], False)

    def test_vocabulary_query_is_idempotent(self):
        """Test vocabulary query returns same result on repeated calls."""
        message = {"type": "query", "query_type": "vocabulary"}

        result1 = self.handler.handle_message(message)
        result2 = self.handler.handle_message(message)

        self.assertEqual(result1, result2)


class TestErrorHandling(unittest.TestCase):
    """Test error handling for malformed messages."""

    def setUp(self):
        """Load test game state."""
        fixtures_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.game_state = load_game_state(str(fixtures_path))
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)
        self.handler = LLMProtocolHandler(self.game_state)

    def test_missing_message_type(self):
        """Test message without type field."""
        message = {
            "action": {"verb": "take", "object": "key"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "error")

    def test_unknown_message_type(self):
        """Test message with unknown type."""
        message = {
            "type": "unknown_type",
            "action": {"verb": "take"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "error")
        self.assertIn("unknown", get_result_message(result).lower())

    def test_command_without_action(self):
        """Test command without action field."""
        message = {
            "type": "command"
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "error")
        self.assertIn("action", get_result_message(result).lower())

    def test_command_without_verb(self):
        """Test command with action but no verb."""
        message = {
            "type": "command",
            "action": {"object": "key"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "error")

    def test_unknown_query_type(self):
        """Test query with unknown query_type."""
        message = {
            "type": "query",
            "query_type": "unknown"
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "error")


class TestResultFormat(unittest.TestCase):
    """Test that result messages conform to spec format."""

    def setUp(self):
        """Load test game state."""
        fixtures_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.game_state = load_game_state(str(fixtures_path))
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)
        self.handler = LLMProtocolHandler(self.game_state)

    def test_success_result_format(self):
        """Test that success results have correct format."""
        message = {
            "type": "command",
            "action": {"verb": "take", "object": "key"}
        }

        result = self.handler.handle_message(message)

        # Required fields
        self.assertIn("type", result)
        self.assertEqual(result["type"], "result")
        self.assertIn("success", result)
        self.assertIn("action", result)

        # Entity should have llm_context fields
        if "entity" in result:
            entity = result["entity"]
            self.assertIn("id", entity)
            self.assertIn("name", entity)

    def test_error_result_format(self):
        """Test that error results have correct format.

        In the new NarrationResult format, errors are indicated by:
        - success=False
        - Error message in narration.primary_text
        """
        message = {
            "type": "command",
            "action": {"verb": "take", "object": "nonexistent"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "result")
        self.assertFalse(result["success"])
        # New format uses narration instead of error
        self.assertIn("narration", result)
        self.assertIn("primary_text", result["narration"])

    def test_query_response_format(self):
        """Test that query responses have correct format."""
        message = {
            "type": "query",
            "query_type": "location"
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "query_response")
        self.assertIn("query_type", result)
        self.assertIn("data", result)


class TestEndToEndInteractions(unittest.TestCase):
    """Test complete interaction sequences."""

    def setUp(self):
        """Load test game state."""
        fixtures_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.game_state = load_game_state(str(fixtures_path))
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)
        self.handler = LLMProtocolHandler(self.game_state)

    def test_take_key_unlock_door_sequence(self):
        """Test sequence: take key, go north, unlock door, open door, go east."""
        # Take key
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "take", "object": "key"}
        })
        self.assertTrue(result["success"])

        # Go north to hallway
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "go", "object": "north"}
        })
        self.assertTrue(result["success"])
        self.assertEqual(self.game_state.get_actor(ActorId("player")).location, "loc_hallway")

        # Unlock iron door
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "unlock", "object": "door", "adjective": "iron"}
        })
        self.assertTrue(result["success"])

        # Open iron door
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "iron"}
        })
        self.assertTrue(result["success"])

        # Go east to treasure room
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "go", "object": "east"}
        })
        self.assertTrue(result["success"])
        self.assertEqual(self.game_state.get_actor(ActorId("player")).location, "loc_treasure")

    def test_query_then_command_sequence(self):
        """Test querying state then executing command."""
        # Query location to see what's here
        result = self.handler.handle_message({
            "type": "query",
            "query_type": "location",
            "include": ["items"]
        })

        self.assertEqual(result["type"], "query_response")
        items = result["data"]["items"]
        item_names = [i["name"] for i in items]
        self.assertIn("key", item_names)

        # Take the key we queried
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "take", "object": "key"}
        })
        self.assertTrue(result["success"])

        # Use inventory command to confirm
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "inventory"}
        })

        self.assertTrue(result["success"])
        self.assertIn("key", get_result_message(result).lower())

    def test_disambiguation_with_adjective(self):
        """Test using adjective to disambiguate doors."""
        # Move to hallway (has two doors)
        self.accessor.set_entity_where("player", "loc_hallway")
        self.game_state.get_actor(ActorId("player")).inventory.append("item_key")

        # Query doors
        result = self.handler.handle_message({
            "type": "query",
            "query_type": "entities",
            "entity_type": "door",
            "location_id": "loc_hallway"
        })

        doors = result["data"]["entities"]
        self.assertEqual(len(doors), 2)

        # Unlock the iron door first (it's locked in the fixture)
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "unlock", "object": "door", "adjective": "iron"}
        })
        self.assertTrue(result["success"], f"Unlock failed: {result}")

        # Open the iron door specifically using adjective
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "iron"}
        })

        self.assertTrue(result["success"], f"Open failed: {result}")
        iron_door = self.handler._get_door_by_id("door_iron")
        # Handle both door items and old-style doors
        if hasattr(iron_door, 'is_door') and iron_door.is_door:
            self.assertTrue(iron_door.door_open)
        else:
            self.assertTrue(iron_door.open)

    def test_failed_action_then_retry(self):
        """Test failed action, then success after getting requirements."""
        # Move to hallway
        self.accessor.set_entity_where("player", "loc_hallway")

        # Try to unlock iron door without key - should fail
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "unlock", "object": "door", "adjective": "iron"}
        })
        self.assertFalse(result["success"])

        # Go back and get key
        self.handler.handle_message({
            "type": "command",
            "action": {"verb": "go", "object": "south"}
        })

        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "take", "object": "key"}
        })
        self.assertTrue(result["success"])

        # Return to hallway
        self.handler.handle_message({
            "type": "command",
            "action": {"verb": "go", "object": "north"}
        })

        # Now unlocking should succeed
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "unlock", "object": "door", "adjective": "iron"}
        })
        self.assertTrue(result["success"], f"Unlock failed: {result}")

        # Now opening should succeed
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "iron"}
        })
        self.assertTrue(result["success"], f"Open failed: {result}")


class TestJSONDetection(unittest.TestCase):
    """Test JSON input detection (per spec: input starting with '{')."""

    def test_detect_json_input(self):
        """Test that JSON input is correctly detected."""
        json_inputs = [
            '{"type": "command", "action": {"verb": "take"}}',
            '  {"type": "query", "query_type": "location"}',
            '\n{"type": "command"}',
        ]

        for inp in json_inputs:
            stripped = inp.strip()
            self.assertTrue(stripped.startswith("{"), f"Failed for: {inp}")

    def test_text_input_not_json(self):
        """Test that text input is not detected as JSON."""
        text_inputs = [
            "take key",
            "go north",
            "look",
            "inventory",
        ]

        for inp in text_inputs:
            stripped = inp.strip()
            self.assertFalse(stripped.startswith("{"), f"Failed for: {inp}")


class TestLightSourceFunctionality(unittest.TestCase):
    """Test light source auto-lighting functionality."""

    def setUp(self):
        """Load test game state with behavior manager."""
        from src.behavior_manager import BehaviorManager

        fixtures_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.game_state = load_game_state(str(fixtures_path))
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Create behavior manager and load core modules
        self.behavior_manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent.parent / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

        self.handler = LLMProtocolHandler(self.game_state, behavior_manager=self.behavior_manager)

    def test_take_light_source_auto_lights(self):
        """Test that taking an item with provides_light sets lit state."""
        message = {
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "take")
        # New format uses message instead of entity
        self.assertIn("narration", result)
        self.assertIn("lantern", get_result_message(result).lower())

        # Verify item is in inventory
        self.assertIn("item_lantern", self.game_state.get_actor(ActorId("player")).inventory)

        # Verify item is marked as lit
        lantern = None
        for item in self.game_state.items:
            if item.id == "item_lantern":
                lantern = item
                break

        self.assertIsNotNone(lantern)
        self.assertTrue(lantern.states.get('lit'))

    def test_take_light_source_sets_lit_state(self):
        """Test that taking light source sets lit state on entity."""
        message = {
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])

        # Verify lit state on entity object (not in response)
        lantern = None
        for item in self.game_state.items:
            if item.id == "item_lantern":
                lantern = item
                break
        self.assertTrue(lantern.states.get('lit'))

    def test_take_light_source_has_provides_light_property(self):
        """Test that light source entity has provides_light property."""
        # Verify the entity has provides_light property
        lantern = None
        for item in self.game_state.items:
            if item.id == "item_lantern":
                lantern = item
                break
        self.assertIsNotNone(lantern)
        self.assertTrue(lantern.provides_light)

    def test_take_normal_item_not_lit(self):
        """Test that taking normal items doesn't set lit state."""
        message = {
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])

        # Find sword and verify no lit state
        sword = None
        for item in self.game_state.items:
            if item.id == "item_sword":
                sword = item
                break

        self.assertIsNotNone(sword)
        self.assertFalse(sword.states.get('lit', False))

    def test_examine_lit_lantern_shows_lit_state(self):
        """Test that examining a lit lantern shows it's lit in state."""
        # First take the lantern to light it
        take_msg = {
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        }
        self.handler.handle_message(take_msg)

        # Now examine it
        examine_msg = {
            "type": "command",
            "action": {"verb": "examine", "object": "lantern"}
        }
        result = self.handler.handle_message(examine_msg)

        self.assertTrue(result["success"])
        # New format uses message key
        self.assertIn("narration", result)

        # Verify the entity state is lit
        lantern = None
        for item in self.game_state.items:
            if item.id == "item_lantern":
                lantern = item
                break
        self.assertTrue(lantern.states.get('lit'))

    def test_provides_light_property_loaded(self):
        """Test that provides_light property is loaded from game state."""
        lantern = None
        for item in self.game_state.items:
            if item.id == "item_lantern":
                lantern = item
                break

        self.assertIsNotNone(lantern)
        self.assertTrue(lantern.provides_light)

    def test_normal_item_no_provides_light(self):
        """Test that normal items don't have provides_light."""
        sword = None
        for item in self.game_state.items:
            if item.id == "item_sword":
                sword = item
                break

        self.assertIsNotNone(sword)
        self.assertFalse(sword.provides_light)

    def test_drop_light_source_extinguishes(self):
        """Test that dropping a light source sets lit to False."""
        # First take the lantern to light it
        take_msg = {
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        }
        self.handler.handle_message(take_msg)

        # Verify it's lit
        lantern = None
        for item in self.game_state.items:
            if item.id == "item_lantern":
                lantern = item
                break
        self.assertTrue(lantern.states.get('lit'))

        # Now drop it
        drop_msg = {
            "type": "command",
            "action": {"verb": "drop", "object": "lantern"}
        }
        result = self.handler.handle_message(drop_msg)

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "drop")

        # Verify it's no longer lit
        self.assertFalse(lantern.states.get('lit'))

    def test_drop_light_source_sets_unlit_state(self):
        """Test that dropping light source sets lit=False on entity."""
        # Take and then drop the lantern
        take_msg = {
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        }
        self.handler.handle_message(take_msg)

        drop_msg = {
            "type": "command",
            "action": {"verb": "drop", "object": "lantern"}
        }
        result = self.handler.handle_message(drop_msg)

        self.assertTrue(result["success"])
        # Verify entity state is unlit
        lantern = None
        for item in self.game_state.items:
            if item.id == "item_lantern":
                lantern = item
                break
        self.assertFalse(lantern.states.get('lit'))

    def test_retake_light_source_relights(self):
        """Test that retaking a dropped light source lights it again."""
        # Take, drop, then take again
        take_msg = {
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        }
        self.handler.handle_message(take_msg)

        drop_msg = {
            "type": "command",
            "action": {"verb": "drop", "object": "lantern"}
        }
        self.handler.handle_message(drop_msg)

        # Take it again
        result = self.handler.handle_message(take_msg)

        self.assertTrue(result["success"])
        # New format uses message key
        self.assertIn("narration", result)

        # Verify lit state in entity object
        lantern = None
        for item in self.game_state.items:
            if item.id == "item_lantern":
                lantern = item
                break
        self.assertTrue(lantern.states.get('lit'))

    def test_drop_normal_item_no_lit_change(self):
        """Test that dropping normal items doesn't affect lit state."""
        # Take and drop the sword
        take_msg = {
            "type": "command",
            "action": {"verb": "take", "object": "sword"}
        }
        self.handler.handle_message(take_msg)

        drop_msg = {
            "type": "command",
            "action": {"verb": "drop", "object": "sword"}
        }
        result = self.handler.handle_message(drop_msg)

        self.assertTrue(result["success"])

        # Find sword and verify no lit state was set
        sword = None
        for item in self.game_state.items:
            if item.id == "item_sword":
                sword = item
                break

        self.assertFalse(sword.states.get('lit', False))


class TestTraitRandomization(unittest.TestCase):
    """Test trait randomization for narration variety."""

    def setUp(self):
        """Load test game state."""
        fixtures_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.game_state = load_game_state(str(fixtures_path))
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)
        self.handler = LLMProtocolHandler(self.game_state)

    def test_traits_are_shuffled(self):
        """Verify traits list is shuffled (not always in original order)."""
        # Add llm_context with many traits to a location
        loc = self.game_state.get_location("loc_start")
        original_traits = [f"trait_{i}" for i in range(20)]
        loc.properties["llm_context"] = {"traits": original_traits.copy()}

        # Run multiple times and check if at least one shuffle differs
        different_order_found = False
        for _ in range(10):
            result = self.handler._location_to_dict(loc)
            result_traits = result["llm_context"]["traits"]
            if result_traits != original_traits:
                different_order_found = True
                break

        self.assertTrue(different_order_found,
            "Traits should be shuffled at least once in 10 attempts")

    def test_original_traits_not_mutated(self):
        """Verify original entity traits are not modified."""
        loc = self.game_state.get_location("loc_start")
        original_traits = ["trait_a", "trait_b", "trait_c", "trait_d", "trait_e"]
        loc.properties["llm_context"] = {"traits": original_traits.copy()}
        original_copy = original_traits.copy()

        # Call multiple times
        for _ in range(5):
            self.handler._location_to_dict(loc)

        # Original traits should be unchanged
        self.assertEqual(loc.properties["llm_context"]["traits"], original_copy)

    def test_state_variants_preserved(self):
        """Verify state_variants are included unchanged."""
        loc = self.game_state.get_location("loc_start")
        state_variants = {
            "first_visit": "Welcome to the room.",
            "revisit": "You're back again."
        }
        loc.properties["llm_context"] = {
            "traits": ["trait1", "trait2"],
            "state_variants": state_variants.copy()
        }

        result = self.handler._location_to_dict(loc)

        self.assertEqual(result["llm_context"]["state_variants"], state_variants)

    def test_no_llm_context_handled(self):
        """Verify entities without llm_context work correctly."""
        loc = self.game_state.get_location("loc_start")
        loc.properties.pop("llm_context", None)

        result = self.handler._location_to_dict(loc)

        self.assertNotIn("llm_context", result)

    def test_empty_traits_handled(self):
        """Verify empty traits list is handled correctly."""
        loc = self.game_state.get_location("loc_start")
        loc.properties["llm_context"] = {"traits": []}

        result = self.handler._location_to_dict(loc)

        self.assertEqual(result["llm_context"]["traits"], [])

    def test_llm_context_without_traits_preserved(self):
        """Verify llm_context without traits key is preserved."""
        loc = self.game_state.get_location("loc_start")
        loc.properties["llm_context"] = {
            "state_variants": {"default": "A room."}
        }

        result = self.handler._location_to_dict(loc)

        self.assertIn("llm_context", result)
        self.assertIn("state_variants", result["llm_context"])
        self.assertNotIn("traits", result["llm_context"])

    def test_exit_traits_randomized(self):
        """Verify exit llm_context traits are also randomized."""
        # Find the "up" exit from loc_hallway
        exit_entity = None
        for exit_e in self.game_state.exits:
            if exit_e.location == "loc_hallway" and exit_e.direction == "up":
                exit_entity = exit_e
                break

        self.assertIsNotNone(exit_entity, "Should find 'up' exit from loc_hallway")

        original_traits = [f"exit_trait_{i}" for i in range(15)]
        exit_entity.traits["llm_context"] = {"traits": original_traits.copy()}

        self.accessor.set_entity_where("player", "loc_hallway")

        message = {
            "type": "query",
            "query_type": "location",
            "include": ["exits"]
        }

        # Run multiple times to detect shuffling
        different_order_found = False
        for _ in range(10):
            result = self.handler.handle_message(message)
            exit_traits = result["data"]["exits"]["up"]["llm_context"]["traits"]
            if exit_traits != original_traits:
                different_order_found = True
                break

        self.assertTrue(different_order_found,
            "Exit traits should be shuffled at least once in 10 attempts")

    def test_all_traits_present_after_shuffle(self):
        """Verify shuffling preserves all traits (no loss)."""
        loc = self.game_state.get_location("loc_start")
        original_traits = ["alpha", "beta", "gamma", "delta", "epsilon"]
        loc.properties["llm_context"] = {"traits": original_traits.copy()}

        result = self.handler._location_to_dict(loc)
        result_traits = result["llm_context"]["traits"]

        self.assertEqual(sorted(result_traits), sorted(original_traits))
        self.assertEqual(len(result_traits), len(original_traits))


if __name__ == "__main__":
    unittest.main()
