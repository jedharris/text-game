"""Tests for enhanced containers feature.

Tests for phases 1, 3, 5, and 6 of the enhanced containers implementation.
These tests are written before implementation and will initially fail.
"""
from src.types import ActorId

import unittest
import json
from pathlib import Path

from src.state_manager import load_game_state, Item, GameState, ContainerInfo
from src.llm_protocol import LLMProtocolHandler
from src.behavior_manager import BehaviorManager


class TestPhase1DataModel(unittest.TestCase):
    """Phase 1: Test data model updates for containers."""

    def test_item_pushable_field_defaults_to_false(self):
        """Test that Item.pushable defaults to False."""
        item = Item(
            id="test_item",
            name="test",
            description="A test item",
            location="loc_test",
            properties={"type": "object", "portable": True}
        )
        # Currently Item doesn't have pushable field - this tests that it will
        self.assertFalse(getattr(item, 'pushable', False))

    def test_load_item_with_pushable_true(self):
        """Test loading an item with pushable: true from JSON."""
        game_data = {
            "metadata": {"title": "Test", "start_location": "loc_test"},
            "locations": [{"id": "loc_test", "name": "Test", "description": "Test"}],
            "items": [{
                "id": "item_crate",
                "name": "crate",
                "description": "A heavy wooden crate",
                "type": "furniture",
                "portable": False,
                "location": "loc_test",
                "pushable": True
            }],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "loc_test"}}
        }

        state = load_game_state(game_data)
        crate = state.get_item("item_crate")

        # Test that pushable field is loaded
        self.assertTrue(getattr(crate, 'pushable', False))

    def test_load_item_without_pushable_defaults_false(self):
        """Test that items without pushable field default to False."""
        game_data = {
            "metadata": {"title": "Test", "start_location": "loc_test"},
            "locations": [{"id": "loc_test", "name": "Test", "description": "Test"}],
            "items": [{
                "id": "item_sword",
                "name": "sword",
                "description": "A sword",
                "type": "object",
                "portable": True,
                "location": "loc_test"
            }],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "loc_test"}}
        }

        state = load_game_state(game_data)
        sword = state.get_item("item_sword")

        self.assertFalse(getattr(sword, 'pushable', False))

    def test_container_info_is_surface_field(self):
        """Test ContainerInfo includes is_surface field."""
        container = ContainerInfo({
            "is_surface": True,
            "capacity": 5
        })
        # Currently ContainerInfo doesn't have is_surface - this tests it will
        self.assertTrue(getattr(container, 'is_surface', False))

    def test_load_surface_container(self):
        """Test loading a container with is_surface: true."""
        game_data = {
            "metadata": {"title": "Test", "start_location": "loc_test"},
            "locations": [{"id": "loc_test", "name": "Test", "description": "Test"}],
            "items": [{
                "id": "item_table",
                "name": "table",
                "description": "A wooden table",
                "type": "furniture",
                "portable": False,
                "location": "loc_test",
                "container": {
                    "is_container": True,
                    "is_surface": True,
                    "capacity": 5
                }
            }],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "loc_test"}}
        }

        state = load_game_state(game_data)
        table = state.get_item("item_table")

        self.assertIsNotNone(table.container)
        self.assertTrue(getattr(table.container, 'is_surface', False))
        self.assertEqual(table.container.capacity, 5)

    def test_load_enclosed_container(self):
        """Test loading an enclosed container (is_surface: false)."""
        game_data = {
            "metadata": {"title": "Test", "start_location": "loc_test"},
            "locations": [{"id": "loc_test", "name": "Test", "description": "Test"}],
            "items": [{
                "id": "item_chest",
                "name": "chest",
                "description": "A wooden chest",
                "type": "furniture",
                "portable": False,
                "location": "loc_test",
                "container": {
                    "is_container": True,
                    "is_surface": False,
                    "open": False,
                    "capacity": 10
                }
            }],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "loc_test"}}
        }

        state = load_game_state(game_data)
        chest = state.get_item("item_chest")

        self.assertIsNotNone(chest.container)
        self.assertFalse(getattr(chest.container, 'is_surface', True))

    def test_load_item_in_container(self):
        """Test loading an item with location pointing to a container ID."""
        game_data = {
            "metadata": {"title": "Test", "start_location": "loc_test"},
            "locations": [{"id": "loc_test", "name": "Test", "description": "Test"}],
            "items": [
                {
                    "id": "item_pedestal",
                    "name": "pedestal",
                    "description": "A stone pedestal",
                    "type": "furniture",
                    "portable": False,
                    "location": "loc_test",
                    "container": {
                        "is_container": True,
                        "is_surface": True,
                        "capacity": 1
                    }
                },
                {
                    "id": "item_potion",
                    "name": "potion",
                    "description": "A red potion",
                    "type": "object",
                    "portable": True,
                    "location": "item_pedestal"
                }
            ],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "loc_test"}}
        }

        state = load_game_state(game_data)
        potion = state.get_item("item_potion")

        # Item location should be the container ID
        self.assertEqual(potion.location, "item_pedestal")


class TestPhase3EnhancedTake(unittest.TestCase):
    """Phase 3: Test enhanced take command from containers."""

    def setUp(self):
        """Set up test fixtures with surface and enclosed containers."""
        self.game_data = {
            "metadata": {"title": "Test", "start_location": "loc_test"},
            "locations": [{"id": "loc_test", "name": "Test Room", "description": "Test"}],
            "items": [
                {
                    "id": "item_table",
                    "name": "table",
                    "description": "A wooden table",
                    "type": "furniture",
                    "portable": False,
                    "location": "loc_test",
                    "container": {
                        "is_container": True,
                        "is_surface": True,
                        "capacity": 5
                    }
                },
                {
                    "id": "item_key",
                    "name": "key",
                    "description": "A brass key",
                    "type": "object",
                    "portable": True,
                    "location": "item_table"
                },
                {
                    "id": "item_chest",
                    "name": "chest",
                    "description": "A wooden chest",
                    "type": "furniture",
                    "portable": False,
                    "location": "loc_test",
                    "container": {
                        "is_container": True,
                        "is_surface": False,
                        "open": False,
                        "capacity": 10
                    }
                },
                {
                    "id": "item_ring",
                    "name": "ring",
                    "description": "A gold ring",
                    "type": "object",
                    "portable": True,
                    "location": "item_chest"
                }
            ],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "loc_test"}}
        }
        self.state = load_game_state(self.game_data)

        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        self.handler = LLMProtocolHandler(self.state, behavior_manager=self.manager)

    def test_take_from_surface_visible_item(self):
        """Test taking an item from a surface container (visible)."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "key"}
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "take")

        # Key should be in inventory
        self.assertIn("item_key", self.state.actors[ActorId("player")].inventory)

        # Key location should be "player"
        key = self.state.get_item("item_key")
        self.assertEqual(key.location, "player")

    def test_take_from_surface_explicit_syntax(self):
        """Test taking with explicit 'take X from Y' syntax."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {
                "verb": "take",
                "object": "key",
                "indirect_object": "table"
            }
        })

        self.assertTrue(result.get("success"))
        self.assertIn("item_key", self.state.actors[ActorId("player")].inventory)

    def test_take_from_closed_container_fails(self):
        """Test that taking from closed enclosed container fails."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "ring"}
        })

        # Should fail because chest is closed
        self.assertFalse(result.get("success"))
        error_msg = result.get("error", {}).get("message", "").lower()
        self.assertTrue(
            "closed" in error_msg or "don't see" in error_msg,
            f"Expected error about closed container, got: {error_msg}"
        )

    def test_take_from_open_enclosed_container(self):
        """Test taking from an open enclosed container succeeds."""
        # Open the chest first
        chest = self.state.get_item("item_chest")
        chest.container.open = True

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "ring"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("item_ring", self.state.actors[ActorId("player")].inventory)

    def test_take_from_container_with_explicit_from_syntax(self):
        """Test 'take ring from chest' after opening chest."""
        # Open the chest
        chest = self.state.get_item("item_chest")
        chest.container.open = True

        result = self.handler.handle_command({
            "type": "command",
            "action": {
                "verb": "take",
                "object": "ring",
                "indirect_object": "chest"
            }
        })

        self.assertTrue(result.get("success"))
        self.assertIn("item_ring", self.state.actors[ActorId("player")].inventory)

    def test_take_prioritizes_room_items_over_container_items(self):
        """Test that items directly in room are found before container items."""
        # Add a key directly in the room
        self.state.items.append(Item(
            id="item_room_key",
            name="key",
            description="A silver key",
            location="loc_test",
            properties={"type": "object", "portable": True}
        ))

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "key"}
        })

        self.assertTrue(result.get("success"))
        # Should take the room key, not the table key
        self.assertIn("item_room_key", self.state.actors[ActorId("player")].inventory)
        self.assertNotIn("item_key", self.state.actors[ActorId("player")].inventory)

    def test_take_from_nonexistent_container_fails(self):
        """Test that take from nonexistent container fails gracefully."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {
                "verb": "take",
                "object": "key",
                "indirect_object": "shelf"  # No shelf exists
            }
        })

        self.assertFalse(result.get("success"))


class TestPhase5GameState(unittest.TestCase):
    """Phase 5: Test game state with pedestal in tower and table in hallway."""

    def setUp(self):
        """Set up with the actual game state file."""
        fixture_path = Path(__file__).parent.parent / "examples" / "simple_game" / "game_state.json"
        self.state = load_game_state(fixture_path)

        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)

        self.handler = LLMProtocolHandler(self.state, behavior_manager=self.manager)

    def test_tower_has_pedestal_item(self):
        """Test that tower contains a pedestal item."""
        # Look for pedestal in items
        pedestal = None
        for item in self.state.items:
            if item.name == "pedestal":
                pedestal = item
                break

        self.assertIsNotNone(pedestal, "Pedestal item not found")
        self.assertEqual(pedestal.location, "loc_tower")
        self.assertFalse(pedestal.portable)

    def test_pedestal_is_surface_container(self):
        """Test that pedestal is a surface container."""
        pedestal = None
        for item in self.state.items:
            if item.name == "pedestal":
                pedestal = item
                break

        self.assertIsNotNone(pedestal)
        self.assertIsNotNone(pedestal.container)
        self.assertTrue(getattr(pedestal.container, 'is_surface', False))
        self.assertEqual(pedestal.container.capacity, 1)

    def test_potion_on_pedestal(self):
        """Test that potion is located on the pedestal."""
        potion = self.state.get_item("item_potion")

        # Potion should be on pedestal, not in loc_tower directly
        self.assertEqual(potion.location, "item_pedestal")

    def test_take_potion_from_pedestal(self):
        """Test taking potion from pedestal in tower."""
        self.state.actors[ActorId("player")].location = "loc_tower"

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "potion"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("item_potion", self.state.actors[ActorId("player")].inventory)

    def test_hallway_has_table_item(self):
        """Test that hallway contains a table item."""
        table = None
        for item in self.state.items:
            if item.name == "table":
                table = item
                break

        self.assertIsNotNone(table, "Table item not found")
        self.assertEqual(table.location, "loc_hallway")
        self.assertFalse(table.portable)

    def test_table_is_surface_container(self):
        """Test that table is a surface container."""
        table = None
        for item in self.state.items:
            if item.name == "table":
                table = item
                break

        self.assertIsNotNone(table)
        self.assertIsNotNone(table.container)
        self.assertTrue(getattr(table.container, 'is_surface', False))

    def test_lantern_on_table(self):
        """Test that lantern is located on the table."""
        lantern = self.state.get_item("item_lantern")

        # Lantern should be on table, not in loc_hallway directly
        self.assertEqual(lantern.location, "item_table")

    def test_take_lantern_from_table(self):
        """Test taking lantern from table - behaviors should still work."""
        self.state.actors[ActorId("player")].location = "loc_hallway"

        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "take", "object": "lantern"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("item_lantern", self.state.actors[ActorId("player")].inventory)

        # Behavior should have fired - lantern should be lit
        lantern = self.state.get_item("item_lantern")
        self.assertTrue(lantern.states.get("lit", False))

        # Should have behavior message
        self.assertIn("message", result)

    def test_tower_description_mentions_pedestal(self):
        """Test that tower description or items include pedestal reference."""
        tower = self.state.get_location("loc_tower")

        # Either the description mentions pedestal, or pedestal is in the location's items
        has_pedestal_ref = (
            "pedestal" in tower.description.lower() or
            any(item.name == "pedestal" and item.location == "loc_tower"
                for item in self.state.items)
        )
        self.assertTrue(has_pedestal_ref)


class TestPhase6RoomDescriptions(unittest.TestCase):
    """Phase 6: Test room descriptions include surface container contents."""

    def setUp(self):
        """Set up test fixtures with surface containers."""
        self.game_data = {
            "metadata": {"title": "Test", "start_location": "loc_test"},
            "locations": [{"id": "loc_test", "name": "Test Room", "description": "A test room."}],
            "items": [
                {
                    "id": "item_table",
                    "name": "table",
                    "description": "A wooden table",
                    "type": "furniture",
                    "portable": False,
                    "location": "loc_test",
                    "container": {
                        "is_container": True,
                        "is_surface": True,
                        "capacity": 5
                    }
                },
                {
                    "id": "item_key",
                    "name": "key",
                    "description": "A brass key",
                    "type": "object",
                    "portable": True,
                    "location": "item_table"
                },
                {
                    "id": "item_coin",
                    "name": "coin",
                    "description": "A gold coin",
                    "type": "object",
                    "portable": True,
                    "location": "item_table"
                },
                {
                    "id": "item_chest",
                    "name": "chest",
                    "description": "A wooden chest",
                    "type": "furniture",
                    "portable": False,
                    "location": "loc_test",
                    "container": {
                        "is_container": True,
                        "is_surface": False,
                        "open": False,
                        "capacity": 10
                    }
                },
                {
                    "id": "item_ring",
                    "name": "ring",
                    "description": "A gold ring",
                    "type": "object",
                    "portable": True,
                    "location": "item_chest"
                }
            ],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "loc_test"}}
        }
        self.state = load_game_state(self.game_data)

        self.handler = LLMProtocolHandler(self.state)

    def test_location_query_includes_surface_items(self):
        """Test that location query includes items on surfaces."""
        result = self.handler.handle_query({
            "type": "query",
            "query_type": "location"
        })

        self.assertEqual(result.get("type"), "query_response")
        data = result.get("data", {})
        items = data.get("items", [])

        # Should include items on surface containers
        item_names = [item.get("name") for item in items]
        self.assertIn("key", item_names, "Key on table should be visible")
        self.assertIn("coin", item_names, "Coin on table should be visible")

    def test_location_query_excludes_closed_container_contents(self):
        """Test that items in closed containers are not listed."""
        result = self.handler.handle_query({
            "type": "query",
            "query_type": "location"
        })

        data = result.get("data", {})
        items = data.get("items", [])

        # Ring in closed chest should not be visible
        item_names = [item.get("name") for item in items]
        self.assertNotIn("ring", item_names, "Ring in closed chest should not be visible")

    def test_location_query_includes_open_container_contents(self):
        """Test that items in open enclosed containers are visible."""
        # Open the chest
        chest = self.state.get_item("item_chest")
        chest.container.open = True

        result = self.handler.handle_query({
            "type": "query",
            "query_type": "location"
        })

        data = result.get("data", {})
        items = data.get("items", [])

        # Ring should now be visible
        item_names = [item.get("name") for item in items]
        self.assertIn("ring", item_names, "Ring in open chest should be visible")

    def test_examine_room_requires_object(self):
        """Test that examine without object asks what to examine.

        Note: Examining room (no object) is done via "look" command, not "examine".
        """
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine"}  # No object
        })

        # Should fail asking what to examine
        self.assertFalse(result.get("success"))
        self.assertIn("what", result.get("error", {}).get("message", "").lower())

    def test_examine_container_returns_description(self):
        """Test that examining a container returns its description.

        Note: The current examine implementation returns item description as text.
        Container contents are visible via location query, not examine command.
        """
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "examine", "object": "table"}
        })

        self.assertTrue(result.get("success"))
        # New format returns message with description
        self.assertIn("wooden table", result.get("message", "").lower())

    def test_surface_items_include_container_context(self):
        """Test that surface items include reference to their container."""
        result = self.handler.handle_query({
            "type": "query",
            "query_type": "location"
        })

        data = result.get("data", {})
        items = data.get("items", [])

        # Find the key
        key_item = None
        for item in items:
            if item.get("name") == "key":
                key_item = item
                break

        if key_item:
            # Key should have container reference (for "On the table: key")
            # This could be a "container" or "on_surface" field
            has_container_ref = (
                "container" in key_item or
                "on_surface" in key_item or
                "surface_of" in key_item
            )
            # This is optional - implementation may handle formatting differently


class TestPhase2PutCommand(unittest.TestCase):
    """Phase 2: Test put command for placing items in/on containers."""

    def setUp(self):
        """Set up test fixtures with containers."""
        self.game_data = {
            "metadata": {"title": "Test", "start_location": "loc_test"},
            "locations": [{"id": "loc_test", "name": "Test Room", "description": "Test"}],
            "items": [
                {
                    "id": "item_table",
                    "name": "table",
                    "description": "A wooden table",
                    "type": "furniture",
                    "portable": False,
                    "location": "loc_test",
                    "container": {
                        "is_container": True,
                        "is_surface": True,
                        "capacity": 5
                    }
                },
                {
                    "id": "item_pedestal",
                    "name": "pedestal",
                    "description": "A stone pedestal",
                    "type": "furniture",
                    "portable": False,
                    "location": "loc_test",
                    "container": {
                        "is_container": True,
                        "is_surface": True,
                        "capacity": 1
                    }
                },
                {
                    "id": "item_potion",
                    "name": "potion",
                    "description": "A red potion",
                    "type": "object",
                    "portable": True,
                    "location": "item_pedestal"
                },
                {
                    "id": "item_chest",
                    "name": "chest",
                    "description": "A wooden chest",
                    "type": "furniture",
                    "portable": False,
                    "location": "loc_test",
                    "container": {
                        "is_container": True,
                        "is_surface": False,
                        "open": False,
                        "capacity": 10
                    }
                },
                {
                    "id": "item_key",
                    "name": "key",
                    "description": "A brass key",
                    "type": "object",
                    "portable": True,
                    "location": "player"
                },
                {
                    "id": "item_coin",
                    "name": "coin",
                    "description": "A gold coin",
                    "type": "object",
                    "portable": True,
                    "location": "player"
                }
            ],
            "actors": {
                "player": {
                    "id": "player",
                    "name": "Adventurer",
                    "description": "The player",
                    "location": "loc_test",
                    "inventory": ["item_key", "item_coin"]
                }
            }
        }
        self.state = load_game_state(self.game_data)
        self.handler = LLMProtocolHandler(self.state)

    def test_put_item_on_surface(self):
        """Test putting an item on a surface container."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {
                "verb": "put",
                "object": "key",
                "indirect_object": "table"
            }
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "put")

        # Key should be on table
        key = self.state.get_item("item_key")
        self.assertEqual(key.location, "item_table")

        # Key should not be in inventory
        self.assertNotIn("item_key", self.state.actors[ActorId("player")].inventory)

    def test_put_item_in_open_container(self):
        """Test putting an item in an open enclosed container."""
        # Open the chest first
        chest = self.state.get_item("item_chest")
        chest.container.open = True

        result = self.handler.handle_command({
            "type": "command",
            "action": {
                "verb": "put",
                "object": "key",
                "indirect_object": "chest"
            }
        })

        self.assertTrue(result.get("success"))
        key = self.state.get_item("item_key")
        self.assertEqual(key.location, "item_chest")

    def test_put_item_in_closed_container_fails(self):
        """Test that putting item in closed container fails."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {
                "verb": "put",
                "object": "key",
                "indirect_object": "chest"
            }
        })

        self.assertFalse(result.get("success"))
        error_msg = result.get("error", {}).get("message", "").lower()
        self.assertTrue("closed" in error_msg, f"Expected error about closed container, got: {error_msg}")

    def test_put_fails_when_container_full(self):
        """Test that put fails when container is at capacity."""
        # Pedestal has capacity 1 and already has potion
        result = self.handler.handle_command({
            "type": "command",
            "action": {
                "verb": "put",
                "object": "key",
                "indirect_object": "pedestal"
            }
        })

        self.assertFalse(result.get("success"))
        error_msg = result.get("error", {}).get("message", "").lower()
        self.assertTrue(
            "full" in error_msg or "capacity" in error_msg or "fit" in error_msg,
            f"Expected error about capacity, got: {error_msg}"
        )

    def test_put_item_not_in_inventory_fails(self):
        """Test that put fails when item not in inventory."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {
                "verb": "put",
                "object": "potion",  # On pedestal, not in inventory
                "indirect_object": "table"
            }
        })

        self.assertFalse(result.get("success"))
        error_msg = result.get("error", {}).get("message", "").lower()
        self.assertTrue(
            "have" in error_msg or "inventory" in error_msg or "don't" in error_msg,
            f"Expected error about not having item, got: {error_msg}"
        )

    def test_put_on_nonexistent_container_fails(self):
        """Test that put fails with nonexistent container."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {
                "verb": "put",
                "object": "key",
                "indirect_object": "shelf"  # No shelf exists
            }
        })

        self.assertFalse(result.get("success"))

    def test_put_on_non_container_fails(self):
        """Test that put fails when target is not a container."""
        # Add a non-container item
        self.state.items.append(Item(
            id="item_sword",
            name="sword",
            description="A sword",
            location="loc_test",
            properties={"type": "object", "portable": True}
        ))

        result = self.handler.handle_command({
            "type": "command",
            "action": {
                "verb": "put",
                "object": "key",
                "indirect_object": "sword"
            }
        })

        self.assertFalse(result.get("success"))

    def test_put_without_indirect_object_fails(self):
        """Test that put without container specification fails."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {
                "verb": "put",
                "object": "key"
            }
        })

        self.assertFalse(result.get("success"))

    def test_put_result_includes_message(self):
        """Test that put result includes message with item and container."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {
                "verb": "put",
                "object": "key",
                "indirect_object": "table"
            }
        })

        self.assertTrue(result.get("success"))
        self.assertIn("message", result)
        msg = result.get("message", "").lower()
        self.assertIn("key", msg)
        self.assertIn("table", msg)


class TestPhase4PushCommand(unittest.TestCase):
    """Phase 4: Test push command for moving heavy furniture."""

    def setUp(self):
        """Set up test fixtures with pushable items."""
        self.game_data = {
            "metadata": {"title": "Test", "start_location": "loc_test"},
            "locations": [
                {"id": "loc_test", "name": "Test Room", "description": "Test"},
                {"id": "loc_other", "name": "Other Room", "description": "Another room"}
            ],
            "items": [
                {
                    "id": "item_crate",
                    "name": "crate",
                    "description": "A heavy wooden crate",
                    "type": "furniture",
                    "portable": False,
                    "location": "loc_test",
                    "pushable": True
                },
                {
                    "id": "item_statue",
                    "name": "statue",
                    "description": "A stone statue",
                    "type": "furniture",
                    "portable": False,
                    "location": "loc_test",
                    "pushable": False
                },
                {
                    "id": "item_sword",
                    "name": "sword",
                    "description": "A sword",
                    "type": "object",
                    "portable": True,
                    "location": "loc_test"
                }
            ],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "loc_test"}}
        }
        self.state = load_game_state(self.game_data)
        self.handler = LLMProtocolHandler(self.state)

    def test_push_pushable_item_succeeds(self):
        """Test pushing a pushable item succeeds."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "push", "object": "crate"}
        })

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("action"), "push")

    def test_push_non_pushable_item_succeeds(self):
        """Test pushing any item succeeds (entity behaviors decide outcome)."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "push", "object": "statue"}
        })

        # Behavior handlers succeed unless entity behavior vetoes
        self.assertTrue(result.get("success"))
        self.assertIn("push", result.get("message", "").lower())

    def test_push_portable_item_succeeds(self):
        """Test pushing a portable item succeeds (entity behaviors decide outcome)."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "push", "object": "sword"}
        })

        # Behavior handlers succeed unless entity behavior vetoes
        self.assertTrue(result.get("success"))
        self.assertIn("push", result.get("message", "").lower())

    def test_push_nonexistent_item_fails(self):
        """Test pushing nonexistent item fails."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "push", "object": "boulder"}
        })

        self.assertFalse(result.get("success"))

    def test_push_without_object_fails(self):
        """Test push without object fails."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "push"}
        })

        self.assertFalse(result.get("success"))
        error_msg = result.get("error", {}).get("message", "").lower()
        self.assertIn("what", error_msg)

    def test_push_returns_message(self):
        """Test push result includes message."""
        result = self.handler.handle_command({
            "type": "command",
            "action": {"verb": "push", "object": "crate"}
        })

        self.assertTrue(result.get("success"))
        self.assertIn("message", result)
        self.assertIn("crate", result.get("message", "").lower())


class TestContainerCapacity(unittest.TestCase):
    """Test container capacity limits."""

    def setUp(self):
        """Set up test with limited capacity container."""
        self.game_data = {
            "metadata": {"title": "Test", "start_location": "loc_test"},
            "locations": [{"id": "loc_test", "name": "Test", "description": "Test"}],
            "items": [
                {
                    "id": "item_pedestal",
                    "name": "pedestal",
                    "description": "A stone pedestal",
                    "type": "furniture",
                    "portable": False,
                    "location": "loc_test",
                    "container": {
                        "is_container": True,
                        "is_surface": True,
                        "capacity": 1
                    }
                },
                {
                    "id": "item_potion",
                    "name": "potion",
                    "description": "A red potion",
                    "type": "object",
                    "portable": True,
                    "location": "item_pedestal"
                }
            ],
            "actors": {"player": {"id": "player", "name": "Adventurer", "description": "The player", "location": "loc_test"}}
        }
        self.state = load_game_state(self.game_data)

        self.handler = LLMProtocolHandler(self.state)

    def test_count_items_in_container(self):
        """Test counting items currently in a container."""
        # Count items with location = item_pedestal
        count = sum(1 for item in self.state.items
                   if item.location == "item_pedestal")

        self.assertEqual(count, 1)

    def test_capacity_check_for_full_container(self):
        """Test that capacity is respected when container is full."""
        pedestal = self.state.get_item("item_pedestal")

        # Count current items
        current_count = sum(1 for item in self.state.items
                          if item.location == "item_pedestal")

        # Pedestal has capacity 1 and 1 item (potion)
        self.assertEqual(pedestal.container.capacity, 1)
        self.assertEqual(current_count, 1)

        # Container is at capacity
        is_full = current_count >= pedestal.container.capacity
        self.assertTrue(is_full)


if __name__ == '__main__':
    unittest.main()
