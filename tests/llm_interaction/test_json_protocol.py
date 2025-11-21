"""
Comprehensive test suite for LLM-Game Engine JSON interaction protocol.

Tests the JSON message formats for commands, queries, and results
as specified in LLM_game_interaction.md.
"""

import unittest
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.state_manager import load_game_state, GameState
from src.json_protocol import JSONProtocolHandler


class _JSONProtocolHandlerReference:
    """
    Handler for JSON protocol messages between LLM and game engine.

    This is the implementation being tested - it processes JSON commands
    and queries, returning structured JSON results.
    """

    def __init__(self, state: GameState):
        self.state = state

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
        for i in self.state.items:
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
        self.state.player.inventory.append(item.id)
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
        for item_id in self.state.player.inventory:
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
        self.state.player.inventory.remove(item.id)
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
        self.state.player.location = new_loc_id
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
        for item_id in self.state.player.inventory:
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

        data = {
            "location": self._location_to_dict(loc)
        }

        if "items" in include or not include:
            items = []
            for item in self.state.items:
                if item.location == loc.id:
                    items.append(self._entity_to_dict(item))
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

        if "npcs" in include or not include:
            npcs = []
            for npc in self.state.npcs:
                if npc.location == loc.id:
                    npcs.append(self._npc_to_dict(npc))
            data["npcs"] = npcs

        return {
            "type": "query_response",
            "query_type": "location",
            "data": data
        }

    def _query_inventory(self, message: dict) -> dict:
        """Query player inventory."""
        items = []
        for item_id in self.state.player.inventory:
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
                "nouns": ["sword", "key", "potion", "chest", "door"],
                "directions": ["north", "south", "east", "west", "up", "down"]
            }
        }

    def _query_metadata(self, message: dict) -> dict:
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

    def _find_accessible_item(self, name: str):
        """Find item in location or inventory by name."""
        loc = self._get_current_location()

        # Check location
        for item in self.state.items:
            if item.name == name and item.location == loc.id:
                return item

        # Check inventory
        for item_id in self.state.player.inventory:
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

        return any(key_id in self.state.player.inventory for key_id in lock.opens_with)

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
        self.state = load_game_state(str(fixtures_path))
        self.handler = JSONProtocolHandler(self.state)

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
        self.assertIn("entity", result)
        self.assertEqual(result["entity"]["name"], "key")

        # Verify state changed
        self.assertIn("item_key", self.state.player.inventory)

    def test_take_item_not_found(self):
        """Test take command for non-existent item."""
        message = {
            "type": "command",
            "action": {"verb": "take", "object": "diamond"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "result")
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual(result["error"]["message"], "You don't see that here.")

    def test_take_non_portable_item(self):
        """Test take command for non-portable item."""
        # Move player to treasure room
        self.state.player.location = "loc_treasure"

        message = {
            "type": "command",
            "action": {"verb": "take", "object": "chest"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"]["message"], "You can't take that.")

    def test_drop_item_success(self):
        """Test successful drop command."""
        # First take the item
        self.state.player.inventory.append("item_key")
        self.state.items[1].location = "player"  # item_key

        message = {
            "type": "command",
            "action": {"verb": "drop", "object": "key"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "drop")
        self.assertNotIn("item_key", self.state.player.inventory)

    def test_drop_item_not_in_inventory(self):
        """Test drop command for item not in inventory."""
        message = {
            "type": "command",
            "action": {"verb": "drop", "object": "sword"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"]["message"], "You're not carrying that.")

    def test_go_direction_success(self):
        """Test successful movement."""
        message = {
            "type": "command",
            "action": {"verb": "go", "direction": "north"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "go")
        self.assertEqual(self.state.player.location, "loc_hallway")

    def test_go_invalid_direction(self):
        """Test movement in invalid direction."""
        message = {
            "type": "command",
            "action": {"verb": "go", "direction": "west"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"]["message"], "You can't go that way.")

    def test_go_through_closed_door(self):
        """Test movement through closed door."""
        # Move to hallway and try to go east through locked door
        self.state.player.location = "loc_hallway"

        message = {
            "type": "command",
            "action": {"verb": "go", "direction": "east"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        self.assertIn("locked", result["error"]["message"].lower())

    def test_open_door_success(self):
        """Test opening an unlocked door."""
        # Close the wooden door first
        for door in self.state.doors:
            if door.id == "door_wooden":
                door.open = False
                break

        message = {
            "type": "command",
            "action": {"verb": "open", "object": "door"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "open")

    def test_open_locked_door_with_key(self):
        """Test opening locked door when player has key."""
        # Move to hallway
        self.state.player.location = "loc_hallway"
        # Give player the key
        self.state.player.inventory.append("item_key")

        message = {
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "iron"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        # Door should now be open and unlocked
        iron_door = self.handler._get_door_by_id("door_iron")
        self.assertTrue(iron_door.open)
        self.assertFalse(iron_door.locked)

    def test_open_locked_door_without_key(self):
        """Test opening locked door without key."""
        # Move to hallway
        self.state.player.location = "loc_hallway"

        message = {
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "iron"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        self.assertIn("locked", result["error"]["message"].lower())

    def test_open_already_open_door(self):
        """Test opening already open door."""
        message = {
            "type": "command",
            "action": {"verb": "open", "object": "door"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        self.assertIn("already open", result["error"]["message"].lower())

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
        self.assertIn("entity", result)

    def test_examine_room(self):
        """Test examining room (no object)."""
        message = {
            "type": "command",
            "action": {"verb": "examine"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        self.assertIn("entity", result)
        self.assertEqual(result["entity"]["name"], "Small Room")

    def test_unlock_door_with_key(self):
        """Test unlocking a door with key."""
        # Move to hallway and give key
        self.state.player.location = "loc_hallway"
        self.state.player.inventory.append("item_key")

        message = {
            "type": "command",
            "action": {"verb": "unlock", "object": "door", "adjective": "iron"}
        }

        result = self.handler.handle_message(message)

        self.assertTrue(result["success"])
        iron_door = self.handler._get_door_by_id("door_iron")
        self.assertFalse(iron_door.locked)

    def test_unlock_door_without_key(self):
        """Test unlocking door without key."""
        self.state.player.location = "loc_hallway"

        message = {
            "type": "command",
            "action": {"verb": "unlock", "object": "door", "adjective": "iron"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        self.assertIn("key", result["error"]["message"].lower())

    def test_unknown_verb(self):
        """Test command with unknown verb."""
        message = {
            "type": "command",
            "action": {"verb": "teleport", "direction": "north"}
        }

        result = self.handler.handle_message(message)

        self.assertFalse(result["success"])
        self.assertIn("don't understand", result["error"]["message"].lower())

    def test_inventory_command(self):
        """Test inventory command."""
        # Add item to inventory
        self.state.player.inventory.append("item_sword")

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
        self.state = load_game_state(str(fixtures_path))
        self.handler = JSONProtocolHandler(self.state)

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

    def test_query_inventory(self):
        """Test inventory query."""
        # Add items to inventory
        self.state.player.inventory.append("item_sword")

        message = {
            "type": "query",
            "query_type": "inventory"
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "query_response")
        self.assertEqual(result["query_type"], "inventory")
        self.assertIn("items", result["data"])
        self.assertEqual(len(result["data"]["items"]), 1)

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
        self.state.player.location = "loc_hallway"

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
        """Test vocabulary query."""
        message = {
            "type": "query",
            "query_type": "vocabulary"
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "query_response")
        self.assertEqual(result["query_type"], "vocabulary")
        self.assertIn("verbs", result["data"])
        self.assertIn("nouns", result["data"])

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
        self.assertIn("not found", result["message"].lower())


class TestErrorHandling(unittest.TestCase):
    """Test error handling for malformed messages."""

    def setUp(self):
        """Load test game state."""
        fixtures_path = Path(__file__).parent / "fixtures" / "test_game_state.json"
        self.state = load_game_state(str(fixtures_path))
        self.handler = JSONProtocolHandler(self.state)

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
        self.assertIn("unknown", result["message"].lower())

    def test_command_without_action(self):
        """Test command without action field."""
        message = {
            "type": "command"
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "error")
        self.assertIn("action", result["message"].lower())

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
        self.state = load_game_state(str(fixtures_path))
        self.handler = JSONProtocolHandler(self.state)

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
        """Test that error results have correct format."""
        message = {
            "type": "command",
            "action": {"verb": "take", "object": "nonexistent"}
        }

        result = self.handler.handle_message(message)

        self.assertEqual(result["type"], "result")
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("message", result["error"])

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
        self.state = load_game_state(str(fixtures_path))
        self.handler = JSONProtocolHandler(self.state)

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
            "action": {"verb": "go", "direction": "north"}
        })
        self.assertTrue(result["success"])
        self.assertEqual(self.state.player.location, "loc_hallway")

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
            "action": {"verb": "go", "direction": "east"}
        })
        self.assertTrue(result["success"])
        self.assertEqual(self.state.player.location, "loc_treasure")

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

        # Query inventory to confirm
        result = self.handler.handle_message({
            "type": "query",
            "query_type": "inventory"
        })

        inv_items = result["data"]["items"]
        inv_names = [i["name"] for i in inv_items]
        self.assertIn("key", inv_names)

    def test_disambiguation_with_adjective(self):
        """Test using adjective to disambiguate doors."""
        # Move to hallway (has two doors)
        self.state.player.location = "loc_hallway"
        self.state.player.inventory.append("item_key")

        # Query doors
        result = self.handler.handle_message({
            "type": "query",
            "query_type": "entities",
            "entity_type": "door",
            "location_id": "loc_hallway"
        })

        doors = result["data"]["entities"]
        self.assertEqual(len(doors), 2)

        # Open the iron door specifically using adjective
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "iron"}
        })

        self.assertTrue(result["success"])
        iron_door = self.handler._get_door_by_id("door_iron")
        self.assertTrue(iron_door.open)

    def test_failed_action_then_retry(self):
        """Test failed action, then success after getting requirements."""
        # Move to hallway
        self.state.player.location = "loc_hallway"

        # Try to open iron door without key - should fail
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "iron"}
        })
        self.assertFalse(result["success"])

        # Go back and get key
        self.handler.handle_message({
            "type": "command",
            "action": {"verb": "go", "direction": "south"}
        })

        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "take", "object": "key"}
        })
        self.assertTrue(result["success"])

        # Return to hallway
        self.handler.handle_message({
            "type": "command",
            "action": {"verb": "go", "direction": "north"}
        })

        # Now opening should succeed
        result = self.handler.handle_message({
            "type": "command",
            "action": {"verb": "open", "object": "door", "adjective": "iron"}
        })
        self.assertTrue(result["success"])


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


if __name__ == "__main__":
    unittest.main()
