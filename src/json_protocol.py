"""
JSON protocol handler for LLM-Game Engine communication.

Implements the JSON interaction protocol as specified in LLM_game_interaction.md.
Processes commands and queries, returning structured JSON results.
"""

import json
from typing import Any, Dict, List, Optional

from .state_manager import GameState


class JSONProtocolHandler:
    """
    Handler for JSON protocol messages between LLM and game engine.

    Processes JSON commands and queries, returning structured JSON results
    conforming to the specification.
    """

    def __init__(self, state: GameState):
        self.state = state

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

    # Command handlers

    def _cmd_take(self, action: Dict) -> Dict:
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

        # Auto-light items that provide light (magical runes activate on touch)
        if item.provides_light:
            item.states['lit'] = True

        return {
            "type": "result",
            "success": True,
            "action": "take",
            "entity": self._entity_to_dict(item)
        }

    def _cmd_drop(self, action: Dict) -> Dict:
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

        # Extinguish light sources when dropped (magical runes deactivate)
        if item.provides_light:
            item.states['lit'] = False

        return {
            "type": "result",
            "success": True,
            "action": "drop",
            "entity": self._entity_to_dict(item)
        }

    def _cmd_examine(self, action: Dict) -> Dict:
        """Handle examine command."""
        obj_name = action.get("object")
        adjective = action.get("adjective")

        # Examine room if no object specified
        if not obj_name:
            loc = self._get_current_location()
            # Get items in location
            items = []
            for item in self.state.items:
                if item.location == loc.id:
                    items.append(self._entity_to_dict(item))
            return {
                "type": "result",
                "success": True,
                "action": "examine",
                "entity": self._location_to_dict(loc),
                "items": items
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
                door = self._select_door(doors, adjective)
                return {
                    "type": "result",
                    "success": True,
                    "action": "examine",
                    "entity": self._door_to_dict(door)
                }

        # Check for NPCs
        loc = self._get_current_location()
        for npc in self.state.npcs:
            if npc.location == loc.id and npc.name.lower() == obj_name.lower():
                return {
                    "type": "result",
                    "success": True,
                    "action": "examine",
                    "entity": self._npc_to_dict(npc)
                }

        return {
            "type": "result",
            "success": False,
            "action": "examine",
            "error": {"message": "You don't see that here."}
        }

    def _cmd_go(self, action: Dict) -> Dict:
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
                            "error": {"message": "The door is locked."}
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

        # Get items in new location
        items = []
        for item in self.state.items:
            if item.location == new_loc_id:
                items.append(self._entity_to_dict(item))

        return {
            "type": "result",
            "success": True,
            "action": "go",
            "entity": self._location_to_dict(new_loc),
            "items": items
        }

    def _cmd_open(self, action: Dict) -> Dict:
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
                        "error": {"message": "The door is locked."}
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

    def _cmd_close(self, action: Dict) -> Dict:
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

    def _cmd_unlock(self, action: Dict) -> Dict:
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
                "error": {"message": "You don't have the right key."}
            }

        door.locked = False
        return {
            "type": "result",
            "success": True,
            "action": "unlock",
            "entity": self._door_to_dict(door)
        }

    def _cmd_lock(self, action: Dict) -> Dict:
        """Handle lock command."""
        obj_name = action.get("object")
        adjective = action.get("adjective")

        if obj_name != "door":
            return {
                "type": "result",
                "success": False,
                "action": "lock",
                "error": {"message": f"You can't lock the {obj_name}."}
            }

        doors = self._get_doors_in_location()
        if not doors:
            return {
                "type": "result",
                "success": False,
                "action": "lock",
                "error": {"message": "There is no door here."}
            }

        door = self._select_door(doors, adjective)

        if door.locked:
            return {
                "type": "result",
                "success": False,
                "action": "lock",
                "entity": self._door_to_dict(door),
                "error": {"message": "The door is already locked."}
            }

        if not door.lock_id:
            return {
                "type": "result",
                "success": False,
                "action": "lock",
                "entity": self._door_to_dict(door),
                "error": {"message": "This door has no lock."}
            }

        if not self._player_has_key_for_door(door):
            return {
                "type": "result",
                "success": False,
                "action": "lock",
                "entity": self._door_to_dict(door),
                "error": {"message": "You don't have the right key."}
            }

        door.locked = True
        return {
            "type": "result",
            "success": True,
            "action": "lock",
            "entity": self._door_to_dict(door)
        }

    def _cmd_inventory(self, action: Dict) -> Dict:
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

    def _cmd_look(self, action: Dict) -> Dict:
        """Handle look command (alias for examine room)."""
        return self._cmd_examine(action)

    def _cmd_drink(self, action: Dict) -> Dict:
        """Handle drink command."""
        obj_name = action.get("object")

        if not obj_name:
            return {
                "type": "result",
                "success": False,
                "action": "drink",
                "error": {"message": "Drink what?"}
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
                "action": "drink",
                "error": {"message": "You're not carrying that."}
            }

        return {
            "type": "result",
            "success": True,
            "action": "drink",
            "entity": self._entity_to_dict(item)
        }

    def _cmd_eat(self, action: Dict) -> Dict:
        """Handle eat command."""
        obj_name = action.get("object")

        if not obj_name:
            return {
                "type": "result",
                "success": False,
                "action": "eat",
                "error": {"message": "Eat what?"}
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
                "action": "eat",
                "error": {"message": "You're not carrying that."}
            }

        return {
            "type": "result",
            "success": True,
            "action": "eat",
            "entity": self._entity_to_dict(item)
        }

    def _cmd_attack(self, action: Dict) -> Dict:
        """Handle attack command."""
        obj_name = action.get("object")

        if not obj_name:
            return {
                "type": "result",
                "success": False,
                "action": "attack",
                "error": {"message": "Attack what?"}
            }

        # Check for NPCs in location
        loc = self._get_current_location()
        for npc in self.state.npcs:
            if npc.location == loc.id and npc.name.lower() == obj_name.lower():
                return {
                    "type": "result",
                    "success": True,
                    "action": "attack",
                    "entity": self._npc_to_dict(npc)
                }

        # Check for items in location or inventory
        item = self._find_accessible_item(obj_name)
        if item:
            return {
                "type": "result",
                "success": False,
                "action": "attack",
                "entity": self._entity_to_dict(item),
                "error": {"message": f"You can't attack the {obj_name}."}
            }

        return {
            "type": "result",
            "success": False,
            "action": "attack",
            "error": {"message": "You don't see that here."}
        }

    def _cmd_use(self, action: Dict) -> Dict:
        """Handle use command."""
        obj_name = action.get("object")

        if not obj_name:
            return {
                "type": "result",
                "success": False,
                "action": "use",
                "error": {"message": "Use what?"}
            }

        # Find item in inventory or location
        item = self._find_accessible_item(obj_name)
        if not item:
            return {
                "type": "result",
                "success": False,
                "action": "use",
                "error": {"message": "You don't see that here."}
            }

        return {
            "type": "result",
            "success": True,
            "action": "use",
            "entity": self._entity_to_dict(item)
        }

    def _cmd_read(self, action: Dict) -> Dict:
        """Handle read command."""
        obj_name = action.get("object")

        if not obj_name:
            return {
                "type": "result",
                "success": False,
                "action": "read",
                "error": {"message": "Read what?"}
            }

        # Find item in inventory or location
        item = self._find_accessible_item(obj_name)
        if not item:
            return {
                "type": "result",
                "success": False,
                "action": "read",
                "error": {"message": "You don't see that here."}
            }

        return {
            "type": "result",
            "success": True,
            "action": "read",
            "entity": self._entity_to_dict(item)
        }

    def _cmd_climb(self, action: Dict) -> Dict:
        """Handle climb command."""
        obj_name = action.get("object")

        if not obj_name:
            return {
                "type": "result",
                "success": False,
                "action": "climb",
                "error": {"message": "Climb what?"}
            }

        # Find item in location
        item = self._find_accessible_item(obj_name)
        if not item:
            return {
                "type": "result",
                "success": False,
                "action": "climb",
                "error": {"message": "You don't see that here."}
            }

        return {
            "type": "result",
            "success": True,
            "action": "climb",
            "entity": self._entity_to_dict(item)
        }

    def _cmd_pull(self, action: Dict) -> Dict:
        """Handle pull command."""
        obj_name = action.get("object")

        if not obj_name:
            return {
                "type": "result",
                "success": False,
                "action": "pull",
                "error": {"message": "Pull what?"}
            }

        # Find item in location
        item = self._find_accessible_item(obj_name)
        if not item:
            return {
                "type": "result",
                "success": False,
                "action": "pull",
                "error": {"message": "You don't see that here."}
            }

        return {
            "type": "result",
            "success": True,
            "action": "pull",
            "entity": self._entity_to_dict(item)
        }

    def _cmd_push(self, action: Dict) -> Dict:
        """Handle push command."""
        obj_name = action.get("object")

        if not obj_name:
            return {
                "type": "result",
                "success": False,
                "action": "push",
                "error": {"message": "Push what?"}
            }

        # Find item in location
        item = self._find_accessible_item(obj_name)
        if not item:
            return {
                "type": "result",
                "success": False,
                "action": "push",
                "error": {"message": "You don't see that here."}
            }

        return {
            "type": "result",
            "success": True,
            "action": "push",
            "entity": self._entity_to_dict(item)
        }

    # Query handlers

    def _query_location(self, message: Dict) -> Dict:
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

    def _query_inventory(self, message: Dict) -> Dict:
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
        # Build vocabulary from state
        vocab = self.state.vocabulary

        return {
            "type": "query_response",
            "query_type": "vocabulary",
            "data": {
                "aliases": vocab.aliases,
                "verbs": vocab.verbs,
                "nouns": vocab.nouns,
                "adjectives": vocab.adjectives
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

    def _entity_to_dict(self, item) -> Dict:
        """Convert item to dict with llm_context."""
        result = {
            "id": item.id,
            "name": item.name,
            "type": "item",
            "description": item.description
        }

        # Add llm_context if available (stored in states dict)
        if hasattr(item, 'states') and item.states.get('llm_context'):
            result["llm_context"] = item.states['llm_context']

        # Add lit state if present
        if hasattr(item, 'states') and item.states.get('lit'):
            result["lit"] = item.states['lit']

        # Add provides_light property if present
        if hasattr(item, 'provides_light') and item.provides_light:
            result["provides_light"] = item.provides_light

        return result

    def _door_to_dict(self, door) -> Dict:
        """Convert door to dict with llm_context."""
        result = {
            "id": door.id,
            "description": door.description,
            "open": door.open,
            "locked": door.locked
        }

        # Get door name from description for consistency
        # Extract adjective from description for name
        desc_words = door.description.lower().split()
        adjective = next((word for word in desc_words
                        if word in ["wooden", "iron", "heavy", "simple", "golden", "ancient"]),
                       "")
        result["name"] = f"{adjective} door" if adjective else "door"

        # Add llm_context if available
        if hasattr(door, 'llm_context') and door.llm_context:
            result["llm_context"] = door.llm_context

        return result

    def _location_to_dict(self, loc) -> Dict:
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

    def _npc_to_dict(self, npc) -> Dict:
        """Convert NPC to dict with llm_context."""
        result = {
            "id": npc.id,
            "name": npc.name,
            "description": npc.description
        }

        # Add llm_context if stored in states
        if hasattr(npc, 'states') and npc.states.get('llm_context'):
            result["llm_context"] = npc.states['llm_context']

        return result
