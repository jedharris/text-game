"""
Tests for simplified property-based state manager models.

Phase 1 tests: Models, loader, and serializer with properties dict.
"""
import unittest
import json
import tempfile
import os
from pathlib import Path


class TestSimplifiedItem(unittest.TestCase):
    """Test simplified Item with properties dict."""

    def test_item_core_fields_only(self):
        """Item has only core structural fields as attributes."""
        from src.state_manager import Item

        item = Item(
            id="item_1",
            name="Torch",
            description="A wooden torch",
            location="loc_1"
        )

        self.assertEqual(item.id, "item_1")
        self.assertEqual(item.name, "Torch")
        self.assertEqual(item.location, "loc_1")
        self.assertEqual(item.properties, {})
        self.assertEqual(item.behaviors, [])  # Phase 3: behaviors is now a list

    def test_item_properties_from_json(self):
        """Item properties populated from JSON fields."""
        from src.state_manager import Item

        item = Item(
            id="item_1",
            name="Torch",
            description="A wooden torch",
            location="loc_1",
            properties={
                "type": "tool",
                "portable": True,
                "states": {"lit": False}
            }
        )

        self.assertTrue(item.properties.get("portable", False))
        self.assertEqual(item.properties.get("type"), "tool")
        self.assertFalse(item.properties["states"]["lit"])

    def test_item_container_as_property(self):
        """Container info stored as nested property dict."""
        from src.state_manager import Item

        item = Item(
            id="chest",
            name="Chest",
            description="A wooden chest",
            location="loc_1",
            properties={
                "container": {
                    "is_surface": False,
                    "capacity": 10,
                    "locked": True,
                    "lock_id": "lock_1"
                }
            }
        )

        container = item.properties.get("container", {})
        self.assertEqual(container.get("capacity"), 10)
        self.assertTrue(container.get("locked"))

    def test_item_with_behaviors(self):
        """Item can have behavior handlers."""
        from src.state_manager import Item

        item = Item(
            id="item_1",
            name="Torch",
            description="A torch",
            location="loc_1",
            behaviors={"on_take": "core.items:on_take_torch"}
        )

        self.assertEqual(item.behaviors["on_take"], "core.items:on_take_torch")


class TestSimplifiedLocation(unittest.TestCase):
    """Test simplified Location with properties dict."""

    def test_location_core_fields(self):
        """Location has structural fields plus properties."""
        from src.state_manager import Location

        loc = Location(
            id="loc_1",
            name="Room",
            description="A room",
            exits={},
            items=["item_1"]
        )

        self.assertEqual(loc.id, "loc_1")
        self.assertEqual(loc.items, ["item_1"])

    def test_location_tags_as_property(self):
        """Tags stored in properties."""
        from src.state_manager import Location

        loc = Location(
            id="loc_1",
            name="Room",
            description="A room",
            exits={},
            properties={"tags": ["indoor", "lit"]}
        )

        self.assertEqual(loc.properties.get("tags"), ["indoor", "lit"])

    def test_location_with_exits(self):
        """Location with exit descriptors."""
        from src.state_manager import Location, ExitDescriptor

        loc = Location(
            id="loc_1",
            name="Room",
            description="A room",
            exits={
                "north": ExitDescriptor(type="open", to="loc_2"),
                "east": ExitDescriptor(type="door", door_id="door_1")
            }
        )

        self.assertEqual(loc.exits["north"].to, "loc_2")
        self.assertEqual(loc.exits["east"].door_id, "door_1")

    def test_exit_descriptor_with_properties(self):
        """ExitDescriptor stores description, conditions in properties."""
        from src.state_manager import ExitDescriptor

        exit_desc = ExitDescriptor(
            type="open",
            to="loc_2",
            properties={
                "description": "A dark passage",
                "conditions": ["has_torch"],
                "on_fail": "You can't see in the dark."
            }
        )

        self.assertEqual(exit_desc.type, "open")
        self.assertEqual(exit_desc.to, "loc_2")
        self.assertEqual(exit_desc.properties["description"], "A dark passage")
        self.assertEqual(exit_desc.properties["conditions"], ["has_torch"])
        self.assertEqual(exit_desc.properties["on_fail"], "You can't see in the dark.")

    def test_exit_descriptor_with_behaviors(self):
        """ExitDescriptor can have behaviors list."""
        from src.state_manager import ExitDescriptor

        exit_desc = ExitDescriptor(
            type="open",
            to="loc_2",
            behaviors=["core/observability", "game/magic_portal"]
        )

        self.assertEqual(exit_desc.type, "open")
        self.assertEqual(exit_desc.to, "loc_2")
        self.assertEqual(exit_desc.behaviors, ["core/observability", "game/magic_portal"])

    def test_exit_descriptor_states_property(self):
        """ExitDescriptor states property accesses states within properties."""
        from src.state_manager import ExitDescriptor

        exit_desc = ExitDescriptor(
            type="open",
            to="loc_2"
        )

        # Initially empty
        self.assertEqual(exit_desc.states, {})

        # Can set states
        exit_desc.states["hidden"] = True
        self.assertTrue(exit_desc.states["hidden"])

        # States stored in properties
        self.assertTrue(exit_desc.properties["states"]["hidden"])

    def test_exit_descriptor_with_hidden_state(self):
        """ExitDescriptor with hidden in states (not properties directly)."""
        from src.state_manager import ExitDescriptor

        exit_desc = ExitDescriptor(
            type="open",
            to="loc_2",
            properties={"states": {"hidden": True}}
        )

        self.assertTrue(exit_desc.states.get("hidden"))

    def test_exit_descriptor_with_llm_context(self):
        """ExitDescriptor can have llm_context in properties."""
        from src.state_manager import ExitDescriptor

        exit_desc = ExitDescriptor(
            type="open",
            to="loc_2",
            properties={
                "llm_context": {
                    "traits": ["worn steps", "cold draft"],
                    "state_variants": {
                        "first_visit": "Stairs lead upward."
                    }
                }
            }
        )

        self.assertIsNotNone(exit_desc.llm_context)
        self.assertIn("worn steps", exit_desc.llm_context["traits"])
        self.assertEqual(
            exit_desc.llm_context["state_variants"]["first_visit"],
            "Stairs lead upward."
        )

    def test_exit_descriptor_llm_context_property_accessor(self):
        """ExitDescriptor llm_context property provides convenient access."""
        from src.state_manager import ExitDescriptor

        exit_desc = ExitDescriptor(type="open", to="loc_2")

        # Initially None
        self.assertIsNone(exit_desc.llm_context)

        # Can set via property
        exit_desc.llm_context = {"traits": ["narrow passage"]}
        self.assertEqual(exit_desc.llm_context["traits"], ["narrow passage"])

        # Stored in properties
        self.assertEqual(
            exit_desc.properties["llm_context"]["traits"],
            ["narrow passage"]
        )


class TestSimplifiedActor(unittest.TestCase):
    """Test simplified Actor with properties dict."""

    def test_actor_core_fields(self):
        """Actor has id, name, description, location, inventory as core."""
        from src.state_manager import Actor

        actor = Actor(
            id="npc_1",
            name="Guard",
            description="A guard",
            location="loc_1",
            inventory=["item_5"]
        )

        self.assertEqual(actor.id, "npc_1")
        self.assertEqual(actor.name, "Guard")
        self.assertEqual(actor.location, "loc_1")
        self.assertEqual(actor.inventory, ["item_5"])

    def test_actor_dialogue_as_property(self):
        """Dialogue and states stored in properties."""
        from src.state_manager import Actor

        actor = Actor(
            id="npc_1",
            name="Guard",
            description="A guard",
            location="loc_1",
            inventory=["item_5"],
            properties={
                "dialogue": ["Hello!", "Go away."],
                "states": {"hostile": False}
            }
        )

        self.assertEqual(len(actor.properties["dialogue"]), 2)
        self.assertFalse(actor.properties["states"]["hostile"])
        self.assertEqual(actor.inventory, ["item_5"])


class TestSimplifiedLock(unittest.TestCase):
    """Test simplified Lock with properties dict."""

    def test_lock_minimal_core(self):
        """Lock has id, name, description as core fields."""
        from src.state_manager import Lock

        lock = Lock(
            id="lock_1",
            name="Iron Lock",
            description="A sturdy lock",
            properties={
                "opens_with": ["key_1"]
            }
        )

        self.assertEqual(lock.id, "lock_1")
        self.assertEqual(lock.name, "Iron Lock")
        self.assertEqual(lock.description, "A sturdy lock")
        self.assertEqual(lock.opens_with, ["key_1"])

    def test_lock_with_fail_message(self):
        """Lock can have failure message."""
        from src.state_manager import Lock

        lock = Lock(
            id="lock_1",
            name="Stubborn Lock",
            description="A stubborn lock.",
            properties={
                "opens_with": ["key_1"],
                "fail_message": "The lock won't budge."
            }
        )

        self.assertEqual(lock.properties["fail_message"], "The lock won't budge.")

    def test_lock_with_behaviors(self):
        """Lock can have behaviors list."""
        from src.state_manager import Lock

        lock = Lock(
            id="lock_1",
            name="Enchanted Lock",
            description="A lock requiring an incantation",
            behaviors=["core:lock", "magic:incantation_lock"],
            properties={"opens_with": ["key_1"]}
        )

        self.assertEqual(lock.behaviors, ["core:lock", "magic:incantation_lock"])
        self.assertEqual(lock.name, "Enchanted Lock")

    def test_lock_llm_context_accessor(self):
        """Lock llm_context accessible via property."""
        from src.state_manager import Lock

        lock = Lock(
            id="lock_1",
            name="ancient lock",
            description="An ancient rusted lock",
            properties={
                "opens_with": ["key_1"],
                "llm_context": {
                    "traits": ["ancient", "rusted"],
                    "state_variants": {"locked": "The lock looks impenetrable."}
                }
            }
        )

        self.assertIsNotNone(lock.llm_context)
        self.assertEqual(lock.llm_context["traits"], ["ancient", "rusted"])

    def test_lock_llm_context_setter(self):
        """Lock llm_context can be set via property."""
        from src.state_manager import Lock

        lock = Lock(id="lock_1", name="test lock", description="A test lock", properties={"opens_with": ["key_1"]})
        lock.llm_context = {"traits": ["shiny", "new"]}

        self.assertEqual(lock.llm_context["traits"], ["shiny", "new"])


class TestSimplifiedPlayerState(unittest.TestCase):
    """Test simplified PlayerState (Actor) with properties dict."""

    def test_player_core_fields(self):
        """Actor (player) has location and inventory as core."""
        from src.state_manager import Actor

        player = Actor(
            id="player",
            name="player",
            description="",
            location="loc_1",
            inventory=["item_1"]
        )

        self.assertEqual(player.location, "loc_1")
        self.assertEqual(player.inventory, ["item_1"])

    def test_player_flags_stats_as_properties(self):
        """Flags and stats stored in properties."""
        from src.state_manager import Actor

        player = Actor(
            id="player",
            name="player",
            description="",
            location="loc_1",
            inventory=[],
            properties={
                "flags": {"started": True},
                "stats": {"health": 100, "max_health": 100}
            }
        )

        self.assertTrue(player.properties["flags"]["started"])
        self.assertEqual(player.properties["stats"]["health"], 100)

    def test_actor_llm_context_accessor(self):
        """Actor llm_context accessible via property."""
        from src.state_manager import Actor

        actor = Actor(
            id="guard",
            name="Guard",
            description="A stern guard",
            location="loc_1",
            inventory=[],
            properties={
                "llm_context": {
                    "traits": ["vigilant", "imposing"],
                    "state_variants": {"alerted": "The guard is on high alert."}
                }
            }
        )

        self.assertIsNotNone(actor.llm_context)
        self.assertEqual(actor.llm_context["traits"], ["vigilant", "imposing"])

    def test_actor_llm_context_setter(self):
        """Actor llm_context can be set via property."""
        from src.state_manager import Actor

        actor = Actor(
            id="guard",
            name="Guard",
            description="A guard",
            location="loc_1",
            inventory=[]
        )
        actor.llm_context = {"traits": ["friendly"]}

        self.assertEqual(actor.llm_context["traits"], ["friendly"])


class TestGenericLoader(unittest.TestCase):
    """Test generic property-based loader."""

    def test_load_item_properties_from_json(self):
        """Loader puts non-core fields into properties."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "items": [
                {
                    "id": "item_1",
                    "name": "Torch",
                    "description": "A torch",
                    "location": "loc_1",
                    "type": "tool",
                    "portable": True,
                    "custom_field": "custom_value"
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            item = state.items[0]

            # Core fields are attributes
            self.assertEqual(item.id, "item_1")
            self.assertEqual(item.name, "Torch")
            self.assertEqual(item.location, "loc_1")

            # Everything else in properties
            self.assertEqual(item.properties["type"], "tool")
            self.assertTrue(item.properties["portable"])
            self.assertEqual(item.properties["custom_field"], "custom_value")
        finally:
            os.unlink(temp_path)

    def test_load_nested_container_properties(self):
        """Nested container dict preserved in properties."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "items": [
                {
                    "id": "chest",
                    "name": "Chest",
                    "description": "A chest",
                    "location": "loc_1",
                    "container": {
                        "is_surface": False,
                        "capacity": 10,
                        "locked": True
                    }
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            item = state.items[0]

            container = item.properties.get("container", {})
            self.assertEqual(container["capacity"], 10)
            self.assertTrue(container["locked"])
        finally:
            os.unlink(temp_path)

    def test_load_location_tags_as_property(self):
        """Location tags loaded into properties."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {
                    "id": "loc_1",
                    "name": "Room",
                    "description": "A room",
                    "exits": {},
                    "tags": ["indoor", "lit"],
                    "items": [],
                    "npcs": []
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            loc = state.locations[0]

            self.assertEqual(loc.properties.get("tags"), ["indoor", "lit"])
        finally:
            os.unlink(temp_path)

    def test_load_exit_properties(self):
        """Exit descriptor properties loaded correctly."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {
                    "id": "loc_1",
                    "name": "Room",
                    "description": "A room",
                    "exits": {
                        "north": {
                            "type": "open",
                            "to": "loc_2",
                            "description": "A dark passage",
                            "conditions": ["has_torch"]
                        }
                    }
                },
                {
                    "id": "loc_2",
                    "name": "Room 2",
                    "description": "Another room",
                    "exits": {}
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            loc = state.locations[0]
            exit_desc = loc.exits["north"]

            # Core fields
            self.assertEqual(exit_desc.type, "open")
            self.assertEqual(exit_desc.to, "loc_2")

            # Top-level description field
            self.assertEqual(exit_desc.description, "A dark passage")

            # Extra properties go to properties dict
            self.assertEqual(exit_desc.properties["conditions"], ["has_torch"])
        finally:
            os.unlink(temp_path)

    def test_load_exit_behaviors(self):
        """Exit descriptor behaviors loaded correctly."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {
                    "id": "loc_1",
                    "name": "Room",
                    "description": "A room",
                    "exits": {
                        "north": {
                            "type": "open",
                            "to": "loc_2",
                            "behaviors": ["core/observability", "game/magic_portal"]
                        }
                    }
                },
                {
                    "id": "loc_2",
                    "name": "Room 2",
                    "description": "Another room",
                    "exits": {}
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            loc = state.locations[0]
            exit_desc = loc.exits["north"]

            self.assertEqual(exit_desc.behaviors, ["core/observability", "game/magic_portal"])
        finally:
            os.unlink(temp_path)

    def test_load_exit_with_hidden_state(self):
        """Exit descriptor with hidden in states loaded correctly."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {
                    "id": "loc_1",
                    "name": "Room",
                    "description": "A room",
                    "exits": {
                        "north": {
                            "type": "open",
                            "to": "loc_2",
                            "states": {"hidden": True}
                        }
                    }
                },
                {
                    "id": "loc_2",
                    "name": "Room 2",
                    "description": "Another room",
                    "exits": {}
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            loc = state.locations[0]
            exit_desc = loc.exits["north"]

            # states.hidden should be accessible via the states property
            self.assertTrue(exit_desc.states.get("hidden"))
        finally:
            os.unlink(temp_path)

    def test_load_npc_properties(self):
        """NPC (Actor) dialogue and states loaded into properties, inventory as core."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "npcs": [
                {
                    "id": "npc_1",
                    "name": "Guard",
                    "description": "A guard",
                    "location": "loc_1",
                    "inventory": ["sword"],
                    "dialogue": ["Hello!"],
                    "states": {"hostile": False}
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            npc = state.get_actor("npc_1")

            # Core fields
            self.assertEqual(npc.id, "npc_1")
            self.assertEqual(npc.name, "Guard")
            self.assertEqual(npc.location, "loc_1")
            self.assertEqual(npc.inventory, ["sword"])

            # Properties
            self.assertEqual(npc.properties["dialogue"], ["Hello!"])
            self.assertFalse(npc.properties["states"]["hostile"])
        finally:
            os.unlink(temp_path)

    def test_load_lock_properties(self):
        """Lock name, description, behaviors loaded as core fields; opens_with and messages in properties."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "items": [
                {"id": "key_1", "name": "Key", "description": "A key", "location": "loc_1"}
            ],
            "locks": [
                {
                    "id": "lock_1",
                    "name": "Iron Lock",
                    "description": "A sturdy iron lock",
                    "opens_with": ["key_1"],
                    "behaviors": ["core:lock"],
                    "fail_message": "Won't budge"
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            lock = state.locks[0]

            # Core fields
            self.assertEqual(lock.id, "lock_1")
            self.assertEqual(lock.name, "Iron Lock")
            self.assertEqual(lock.description, "A sturdy iron lock")
            self.assertEqual(lock.behaviors, ["core:lock"])

            # Properties (accessed via accessor)
            self.assertEqual(lock.opens_with, ["key_1"])
            self.assertEqual(lock.properties["fail_message"], "Won't budge")
        finally:
            os.unlink(temp_path)

    def test_load_player_state_properties(self):
        """Player flags and stats loaded into properties."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "items": [
                {"id": "item_1", "name": "Torch", "description": "A torch", "location": "player"}
            ],
            "player_state": {
                "location": "loc_1",
                "inventory": ["item_1"],
                "flags": {"started": True},
                "stats": {"health": 100}
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            player = state.actors.get("player")

            self.assertEqual(player.location, "loc_1")
            self.assertEqual(player.inventory, ["item_1"])
            self.assertTrue(player.properties["flags"]["started"])
            self.assertEqual(player.properties["stats"]["health"], 100)
        finally:
            os.unlink(temp_path)

    def test_load_from_dict(self):
        """Loader accepts dict directly."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ]
        }

        state = load_game_state(data)
        self.assertEqual(len(state.locations), 1)
        self.assertEqual(state.metadata.title, "Test")

    def test_load_preserves_behaviors(self):
        """Behaviors field preserved on entities."""
        from src.state_manager import load_game_state

        data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {"id": "loc_1", "name": "Room", "description": "A room", "exits": {}}
            ],
            "items": [
                {
                    "id": "item_1",
                    "name": "Torch",
                    "description": "A torch",
                    "location": "loc_1",
                    "behaviors": {"on_take": "core.items:on_take"}
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            state = load_game_state(temp_path)
            item = state.items[0]

            self.assertEqual(item.behaviors["on_take"], "core.items:on_take")
        finally:
            os.unlink(temp_path)


class TestGenericSerializer(unittest.TestCase):
    """Test generic property-based serializer."""

    def test_serialize_item_merges_properties(self):
        """Serializer merges properties back to top level."""
        from src.state_manager import (
            Item, game_state_to_dict, GameState, Metadata, Location
        )

        item = Item(
            id="item_1",
            name="Torch",
            description="A torch",
            location="loc_1",
            properties={
                "type": "tool",
                "portable": True,
                "custom": "value"
            }
        )

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            locations=[Location(id="loc_1", name="Room", description="A room", exits={})],
            items=[item]
        )

        result = game_state_to_dict(state)
        item_dict = result["items"][0]

        # Core fields present
        self.assertEqual(item_dict["id"], "item_1")
        self.assertEqual(item_dict["name"], "Torch")
        self.assertEqual(item_dict["location"], "loc_1")

        # Properties merged to top level
        self.assertEqual(item_dict["type"], "tool")
        self.assertTrue(item_dict["portable"])
        self.assertEqual(item_dict["custom"], "value")

        # No 'properties' key in output
        self.assertNotIn("properties", item_dict)

    def test_serialize_preserves_behaviors(self):
        """Behaviors preserved in serialized output."""
        from src.state_manager import (
            Item, game_state_to_dict, GameState, Metadata, Location
        )

        item = Item(
            id="item_1",
            name="Torch",
            description="A torch",
            location="loc_1",
            behaviors={"on_take": "core.items:on_take"}
        )

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            locations=[Location(id="loc_1", name="Room", description="A room", exits={})],
            items=[item]
        )

        result = game_state_to_dict(state)
        item_dict = result["items"][0]

        self.assertEqual(item_dict["behaviors"]["on_take"], "core.items:on_take")

    def test_serialize_exit_behaviors(self):
        """Exit behaviors preserved in serialized output."""
        from src.state_manager import (
            game_state_to_dict, GameState, Metadata, Location, ExitDescriptor
        )

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            locations=[
                Location(
                    id="loc_1",
                    name="Room",
                    description="A room",
                    exits={
                        "north": ExitDescriptor(
                            type="open",
                            to="loc_2",
                            behaviors=["core/observability", "game/magic_portal"]
                        )
                    }
                ),
                Location(id="loc_2", name="Room 2", description="Another room", exits={})
            ],
            items=[]
        )

        result = game_state_to_dict(state)
        exit_dict = result["locations"][0]["exits"]["north"]

        self.assertEqual(exit_dict["behaviors"], ["core/observability", "game/magic_portal"])

    def test_serialize_exit_with_states(self):
        """Exit states preserved in serialized output."""
        from src.state_manager import (
            game_state_to_dict, GameState, Metadata, Location, ExitDescriptor
        )

        exit_desc = ExitDescriptor(type="open", to="loc_2")
        exit_desc.states["hidden"] = True

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            locations=[
                Location(
                    id="loc_1",
                    name="Room",
                    description="A room",
                    exits={"north": exit_desc}
                ),
                Location(id="loc_2", name="Room 2", description="Another room", exits={})
            ],
            items=[]
        )

        result = game_state_to_dict(state)
        exit_dict = result["locations"][0]["exits"]["north"]

        self.assertTrue(exit_dict["states"]["hidden"])

    def test_exit_round_trip_preserves_behaviors_and_states(self):
        """Exit behaviors and states preserved through load -> serialize -> reload."""
        from src.state_manager import load_game_state, game_state_to_dict

        original_data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {
                    "id": "loc_1",
                    "name": "Room",
                    "description": "A room",
                    "exits": {
                        "north": {
                            "type": "open",
                            "to": "loc_2",
                            "behaviors": ["core/observability"],
                            "states": {"hidden": True}
                        }
                    }
                },
                {
                    "id": "loc_2",
                    "name": "Room 2",
                    "description": "Another room",
                    "exits": {}
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(original_data, f)
            temp_path = f.name

        try:
            # Load
            state = load_game_state(temp_path)
            exit_desc = state.locations[0].exits["north"]
            self.assertEqual(exit_desc.behaviors, ["core/observability"])
            self.assertTrue(exit_desc.states.get("hidden"))

            # Serialize
            result = game_state_to_dict(state)
            exit_dict = result["locations"][0]["exits"]["north"]
            self.assertEqual(exit_dict["behaviors"], ["core/observability"])
            self.assertTrue(exit_dict["states"]["hidden"])
        finally:
            os.unlink(temp_path)

    def test_round_trip_preserves_all_data(self):
        """Load -> serialize -> reload preserves all data."""
        from src.state_manager import load_game_state, game_state_to_dict

        original_data = {
            "metadata": {"title": "Test", "version": "1.0", "start_location": "loc_1"},
            "locations": [
                {
                    "id": "loc_1",
                    "name": "Room",
                    "description": "A room",
                    "exits": {},
                    "tags": ["indoor"],
                    "items": ["item_1"],
                    "npcs": []
                }
            ],
            "items": [
                {
                    "id": "item_1",
                    "name": "Torch",
                    "description": "A torch",
                    "location": "loc_1",
                    "type": "tool",
                    "portable": True
                }
            ]
        }

        # Write original
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(original_data, f)
            temp_path = f.name

        try:
            # Load
            state = load_game_state(temp_path)

            # Serialize
            result = game_state_to_dict(state)

            # Compare
            self.assertEqual(result["items"][0]["type"], "tool")
            self.assertTrue(result["items"][0]["portable"])
            self.assertEqual(result["locations"][0]["tags"], ["indoor"])
        finally:
            os.unlink(temp_path)

    def test_serialize_player_state(self):
        """Player state properties serialized correctly."""
        from src.state_manager import (
            Actor, game_state_to_dict, GameState, Metadata, Location
        )

        player = Actor(
            id="player",
            name="player",
            description="",
            location="loc_1",
            inventory=["item_1"],
            properties={
                "flags": {"started": True},
                "stats": {"health": 100}
            }
        )

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            locations=[Location(id="loc_1", name="Room", description="A room", exits={})],
            actors={"player": player}
        )

        result = game_state_to_dict(state)
        # New format uses actors dict instead of player_state
        player_dict = result["actors"]["player"]

        self.assertEqual(player_dict["location"], "loc_1")
        self.assertEqual(player_dict["inventory"], ["item_1"])
        self.assertTrue(player_dict["flags"]["started"])
        self.assertEqual(player_dict["stats"]["health"], 100)


class TestGameStateConvenienceMethods(unittest.TestCase):
    """Test GameState helper methods work with new structure."""

    def test_get_item(self):
        """get_item finds item by id."""
        from src.state_manager import GameState, Metadata, Item

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            items=[
                Item(id="item_1", name="Torch", description="A torch", location="loc_1")
            ]
        )

        item = state.get_item("item_1")
        self.assertEqual(item.name, "Torch")

    def test_get_item_not_found(self):
        """get_item raises KeyError for missing item."""
        from src.state_manager import GameState, Metadata

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1")
        )

        with self.assertRaises(KeyError):
            state.get_item("nonexistent")

    def test_get_location(self):
        """get_location finds location by id."""
        from src.state_manager import GameState, Metadata, Location

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            locations=[
                Location(id="loc_1", name="Room", description="A room", exits={})
            ]
        )

        loc = state.get_location("loc_1")
        self.assertEqual(loc.name, "Room")

    def test_get_lock(self):
        """get_lock finds lock by id."""
        from src.state_manager import GameState, Metadata, Lock

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            locks=[
                Lock(id="lock_1", name="test lock", description="A test lock", properties={"opens_with": ["key_1"]})
            ]
        )

        lock = state.get_lock("lock_1")
        self.assertEqual(lock.properties["opens_with"], ["key_1"])

    def test_get_actor(self):
        """get_actor finds actor by id."""
        from src.state_manager import GameState, Metadata, Actor

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            actors={
                "npc_1": Actor(id="npc_1", name="Guard", description="A guard", location="loc_1")
            }
        )

        npc = state.get_actor("npc_1")
        self.assertEqual(npc.name, "Guard")

    def test_move_item_to_player(self):
        """move_item updates item location to player."""
        from src.state_manager import (
            GameState, Metadata, Item, Location, Actor
        )

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            locations=[
                Location(id="loc_1", name="Room", description="A room", exits={},
                        items=["item_1"])
            ],
            items=[
                Item(id="item_1", name="Torch", description="A torch", location="loc_1")
            ],
            actors={
                "player": Actor(id="player", name="player", description="", location="loc_1", inventory=[])
            }
        )

        state.move_item("item_1", to_player=True)

        item = state.get_item("item_1")
        player = state.actors.get("player")
        self.assertEqual(item.location, "player")
        self.assertIn("item_1", player.inventory)
        self.assertNotIn("item_1", state.locations[0].items)

    def test_move_item_to_location(self):
        """move_item updates item location to another location."""
        from src.state_manager import (
            GameState, Metadata, Item, Location, Actor
        )

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            locations=[
                Location(id="loc_1", name="Room 1", description="A room", exits={},
                        items=["item_1"]),
                Location(id="loc_2", name="Room 2", description="A room", exits={},
                        items=[])
            ],
            items=[
                Item(id="item_1", name="Torch", description="A torch", location="loc_1")
            ],
            actors={
                "player": Actor(id="player", name="player", description="", location="loc_1", inventory=[])
            }
        )

        state.move_item("item_1", to_location="loc_2")

        item = state.get_item("item_1")
        self.assertEqual(item.location, "loc_2")
        self.assertIn("item_1", state.locations[1].items)
        self.assertNotIn("item_1", state.locations[0].items)

    def test_set_player_location(self):
        """set_player_location updates player's location."""
        from src.state_manager import (
            GameState, Metadata, Location, Actor
        )

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            locations=[
                Location(id="loc_1", name="Room 1", description="A room", exits={}),
                Location(id="loc_2", name="Room 2", description="A room", exits={})
            ],
            actors={
                "player": Actor(id="player", name="player", description="", location="loc_1", inventory=[])
            }
        )

        state.set_player_location("loc_2")
        player = state.actors.get("player")
        self.assertEqual(player.location, "loc_2")

    def test_set_flag_and_get_flag(self):
        """set_flag and get_flag work with properties."""
        from src.state_manager import (
            GameState, Metadata, Actor
        )

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            actors={
                "player": Actor(id="player", name="player", description="", location="loc_1", inventory=[], properties={"flags": {}})
            }
        )

        state.set_flag("test_flag", True)
        self.assertTrue(state.get_flag("test_flag"))
        self.assertIsNone(state.get_flag("missing_flag"))
        self.assertEqual(state.get_flag("missing_flag", "default"), "default")

    def test_build_id_registry(self):
        """build_id_registry returns all entity IDs."""
        from src.state_manager import (
            GameState, Metadata, Location, Item, Lock, Actor
        )

        # Create a door item (new unified model)
        door_item = Item(
            id="door_1",
            name="door",
            description="A door",
            location="exit:loc_1:north",
            properties={"door": {"open": False, "locked": False}}
        )

        state = GameState(
            metadata=Metadata(title="Test", version="1.0", start_location="loc_1"),
            locations=[Location(id="loc_1", name="Room", description="A room", exits={})],
            items=[
                Item(id="item_1", name="Torch", description="A torch", location="loc_1"),
                door_item
            ],
            locks=[Lock(id="lock_1", name="test lock", description="A test lock")],
            actors={
                "player": Actor(id="player", name="player", description="", location="loc_1"),
                "npc_1": Actor(id="npc_1", name="Guard", description="A guard", location="loc_1")
            }
        )

        registry = state.build_id_registry()

        self.assertEqual(registry["player"], "player")
        self.assertEqual(registry["loc_1"], "location")
        self.assertEqual(registry["item_1"], "item")
        self.assertEqual(registry["door_1"], "door_item")
        self.assertEqual(registry["lock_1"], "lock")
        self.assertEqual(registry["npc_1"], "npc")


class TestBackwardCompatibility(unittest.TestCase):
    """Test that game files with unified door items load correctly."""

    def test_load_valid_world_fixture(self):
        """Load existing valid_world.json fixture with unified door items."""
        from src.state_manager import load_game_state

        fixture_path = Path(__file__).parent / "fixtures" / "valid_world.json"
        state = load_game_state(fixture_path)

        self.assertEqual(len(state.locations), 3)
        # Items includes door item
        self.assertEqual(len(state.items), 6)
        # NPCs are actors (excluding player)
        npcs = [a for aid, a in state.actors.items() if aid != "player"]
        self.assertEqual(len(npcs), 1)
        # Door items
        door_items = [i for i in state.items if i.is_door]
        self.assertEqual(len(door_items), 1)
        self.assertEqual(len(state.locks), 2)

        # Check properties populated
        chest = state.get_item("item_2")
        self.assertIn("container", chest.properties)
        self.assertTrue(chest.properties["container"]["locked"])

    def test_serialized_output_matches_input(self):
        """Serialized output semantically matches input."""
        from src.state_manager import load_game_state, game_state_to_dict

        fixture_path = Path(__file__).parent / "fixtures" / "valid_world.json"

        # Load original
        with open(fixture_path) as f:
            original = json.load(f)

        # Load and serialize
        state = load_game_state(fixture_path)
        serialized = game_state_to_dict(state)

        # Items count should match (including door items)
        original_items = len(original.get("items", []))
        self.assertEqual(len(serialized["items"]), original_items)

        # Compare specific values for original items (excluding door items)
        for orig_item in original["items"]:
            if "door" not in orig_item:
                ser_item = next((i for i in serialized["items"] if i["id"] == orig_item["id"]), None)
                if ser_item:
                    # Properties may be at top level or nested in "properties"
                    orig_props = orig_item.get("properties", orig_item)
                    ser_props = ser_item.get("properties", ser_item)
                    self.assertEqual(
                        ser_props.get("portable"),
                        orig_props.get("portable"),
                        f"Mismatch in portable for {orig_item['id']}"
                    )
                    self.assertEqual(
                        ser_props.get("type"),
                        orig_props.get("type"),
                        f"Mismatch in type for {orig_item['id']}"
                    )


if __name__ == '__main__':
    unittest.main()
