"""Tests for observability feature (Phase 2) - is_observable() helper function.

Tests the is_observable() helper function that checks whether an entity
is visible based on its hidden state and custom on_observe behaviors.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from src.state_manager import Item, Actor, ExitDescriptor
from src.state_accessor import EventResult
from src.behavior_manager import BehaviorManager


class TestIsObservableBasic(unittest.TestCase):
    """Test is_observable() with basic hidden state checks."""

    def setUp(self):
        """Set up test fixtures."""
        self.accessor = Mock()
        self.behavior_manager = BehaviorManager()

    def test_entity_without_hidden_state_is_visible(self):
        """Entity without states.hidden is visible."""
        from utilities.utils import is_observable

        item = Item(
            id="key",
            name="key",
            description="A small key",
            location="room1",
            properties={},
            behaviors=[]
        )

        visible, message = is_observable(
            item, self.accessor, self.behavior_manager,
            actor_id="player", method="look"
        )

        self.assertTrue(visible)
        self.assertIsNone(message)

    def test_entity_with_hidden_false_is_visible(self):
        """Entity with states.hidden=False is visible."""
        from utilities.utils import is_observable

        item = Item(
            id="key",
            name="key",
            description="A small key",
            location="room1",
            properties={"states": {"hidden": False}},
            behaviors=[]
        )

        visible, message = is_observable(
            item, self.accessor, self.behavior_manager,
            actor_id="player", method="look"
        )

        self.assertTrue(visible)
        self.assertIsNone(message)

    def test_entity_with_hidden_true_is_not_visible(self):
        """Entity with states.hidden=True is not visible."""
        from utilities.utils import is_observable

        item = Item(
            id="secret_key",
            name="key",
            description="A hidden key",
            location="room1",
            properties={"states": {"hidden": True}},
            behaviors=[]
        )

        visible, message = is_observable(
            item, self.accessor, self.behavior_manager,
            actor_id="player", method="look"
        )

        self.assertFalse(visible)
        self.assertIsNone(message)

    def test_exit_descriptor_without_hidden_is_visible(self):
        """ExitDescriptor without states.hidden is visible."""
        from utilities.utils import is_observable

        exit_desc = ExitDescriptor(
            type="open",
            to="room2",
            properties={},
            behaviors=[]
        )

        visible, message = is_observable(
            exit_desc, self.accessor, self.behavior_manager,
            actor_id="player", method="look"
        )

        self.assertTrue(visible)
        self.assertIsNone(message)

    def test_exit_descriptor_with_hidden_true_is_not_visible(self):
        """ExitDescriptor with states.hidden=True is not visible."""
        from utilities.utils import is_observable

        exit_desc = ExitDescriptor(
            type="open",
            to="secret_room",
            properties={"states": {"hidden": True}},
            behaviors=[]
        )

        visible, message = is_observable(
            exit_desc, self.accessor, self.behavior_manager,
            actor_id="player", method="look"
        )

        self.assertFalse(visible)
        self.assertIsNone(message)


class TestIsObservableWithBehaviors(unittest.TestCase):
    """Test is_observable() with custom on_observe behaviors."""

    def setUp(self):
        """Set up test fixtures."""
        self.accessor = Mock()
        self.behavior_manager = BehaviorManager()

    def test_behavior_returning_allow_false_hides_entity(self):
        """Custom on_observe behavior returning allow=False hides entity."""
        from utilities.utils import is_observable

        # Create a mock behavior module
        mock_module = MagicMock()
        mock_module.on_observe = Mock(return_value=EventResult(allow=False))

        # Register the mock module
        self.behavior_manager._modules["test_hide"] = mock_module

        item = Item(
            id="magic_cloak",
            name="cloak",
            description="A magical cloak",
            location="room1",
            properties={},
            behaviors=["test_hide"]
        )

        visible, message = is_observable(
            item, self.accessor, self.behavior_manager,
            actor_id="player", method="look"
        )

        self.assertFalse(visible)
        mock_module.on_observe.assert_called_once()

    def test_behavior_returning_allow_true_shows_entity(self):
        """Custom on_observe behavior returning allow=True shows entity."""
        from utilities.utils import is_observable

        mock_module = MagicMock()
        mock_module.on_observe = Mock(return_value=EventResult(allow=True))

        self.behavior_manager._modules["test_show"] = mock_module

        item = Item(
            id="key",
            name="key",
            description="A key",
            location="room1",
            properties={},
            behaviors=["test_show"]
        )

        visible, message = is_observable(
            item, self.accessor, self.behavior_manager,
            actor_id="player", method="look"
        )

        self.assertTrue(visible)

    def test_behavior_message_is_returned(self):
        """Custom on_observe behavior can provide a message."""
        from utilities.utils import is_observable

        mock_module = MagicMock()
        mock_module.on_observe = Mock(return_value=EventResult(
            allow=True,
            message="The key gleams faintly."
        ))

        self.behavior_manager._modules["test_message"] = mock_module

        item = Item(
            id="key",
            name="key",
            description="A key",
            location="room1",
            properties={},
            behaviors=["test_message"]
        )

        visible, message = is_observable(
            item, self.accessor, self.behavior_manager,
            actor_id="player", method="look"
        )

        self.assertTrue(visible)
        self.assertEqual(message, "The key gleams faintly.")

    def test_behavior_can_override_hidden_state(self):
        """Custom behavior can reveal a hidden item (e.g., on search)."""
        from utilities.utils import is_observable

        # Create behavior that reveals on search
        def reveal_on_search(entity, accessor, context):
            if context["method"] == "search":
                # Reveal the item
                entity.states["hidden"] = False
                return EventResult(allow=True, message="You find a key hidden in a crack!")
            return EventResult(allow=False)

        mock_module = MagicMock()
        mock_module.on_observe = Mock(side_effect=reveal_on_search)

        self.behavior_manager._modules["reveal_on_search"] = mock_module

        item = Item(
            id="hidden_key",
            name="key",
            description="A hidden key",
            location="room1",
            properties={"states": {"hidden": True}},
            behaviors=["reveal_on_search"]
        )

        # Looking doesn't reveal
        visible, message = is_observable(
            item, self.accessor, self.behavior_manager,
            actor_id="player", method="look"
        )
        self.assertFalse(visible)

        # Reset hidden state for search test
        item.states["hidden"] = True

        # Searching reveals
        visible, message = is_observable(
            item, self.accessor, self.behavior_manager,
            actor_id="player", method="search"
        )
        self.assertTrue(visible)
        self.assertEqual(message, "You find a key hidden in a crack!")
        self.assertFalse(item.states["hidden"])  # State was modified

    def test_context_contains_actor_id_and_method(self):
        """Behavior receives correct context with actor_id and method."""
        from utilities.utils import is_observable

        captured_context = {}

        def capture_context(entity, accessor, context):
            captured_context.update(context)
            return EventResult(allow=True)

        mock_module = MagicMock()
        mock_module.on_observe = Mock(side_effect=capture_context)

        self.behavior_manager._modules["test_context"] = mock_module

        item = Item(
            id="key",
            name="key",
            description="A key",
            location="room1",
            properties={},
            behaviors=["test_context"]
        )

        is_observable(
            item, self.accessor, self.behavior_manager,
            actor_id="player", method="examine"
        )

        self.assertEqual(captured_context["actor_id"], "player")
        self.assertEqual(captured_context["method"], "examine")


class TestIsObservableBehaviorPrecedence(unittest.TestCase):
    """Test the precedence between hidden state and behaviors."""

    def setUp(self):
        """Set up test fixtures."""
        self.accessor = Mock()
        self.behavior_manager = BehaviorManager()

    def test_hidden_checked_before_behaviors(self):
        """Hidden state is checked first, but behaviors can override."""
        from utilities.utils import is_observable

        # Behavior that always allows
        mock_module = MagicMock()
        mock_module.on_observe = Mock(return_value=EventResult(allow=True))

        self.behavior_manager._modules["always_allow"] = mock_module

        # Hidden item with behavior that would allow
        item = Item(
            id="hidden_key",
            name="key",
            description="A hidden key",
            location="room1",
            properties={"states": {"hidden": True}},
            behaviors=["always_allow"]
        )

        # According to design, core hidden check happens first,
        # then behaviors can override. So behavior's allow=True should win.
        visible, message = is_observable(
            item, self.accessor, self.behavior_manager,
            actor_id="player", method="look"
        )

        # Behavior was invoked and its result is used
        self.assertTrue(visible)
        mock_module.on_observe.assert_called_once()

    def test_entity_without_behaviors_uses_only_hidden_state(self):
        """Entity without behaviors uses only hidden state check."""
        from utilities.utils import is_observable

        item = Item(
            id="hidden_key",
            name="key",
            description="A hidden key",
            location="room1",
            properties={"states": {"hidden": True}},
            behaviors=[]
        )

        visible, message = is_observable(
            item, self.accessor, self.behavior_manager,
            actor_id="player", method="look"
        )

        self.assertFalse(visible)
        self.assertIsNone(message)


class TestIsObservableEntityTypes(unittest.TestCase):
    """Test is_observable() with different entity types."""

    def setUp(self):
        """Set up test fixtures."""
        self.accessor = Mock()
        self.behavior_manager = BehaviorManager()

    def test_actor_with_hidden_properties(self):
        """Actor with hidden state in properties is not visible."""
        from utilities.utils import is_observable

        actor = Actor(
            id="ghost",
            name="ghost",
            description="A spectral figure",
            location="room1",
            properties={"states": {"hidden": True}},
            behaviors=[]
        )

        visible, message = is_observable(
            actor, self.accessor, self.behavior_manager,
            actor_id="player", method="look"
        )

        self.assertFalse(visible)

    def test_actor_without_hidden_is_visible(self):
        """Actor without hidden state is visible."""
        from utilities.utils import is_observable

        actor = Actor(
            id="merchant",
            name="merchant",
            description="A friendly merchant",
            location="room1",
            properties={},
            behaviors=[]
        )

        visible, message = is_observable(
            actor, self.accessor, self.behavior_manager,
            actor_id="player", method="look"
        )

        self.assertTrue(visible)


class TestObservabilityIntegration(unittest.TestCase):
    """Integration tests for observability with utility functions."""

    def setUp(self):
        """Set up test fixtures with a real game state."""
        from src.state_manager import GameState, Metadata, Location, Actor as StateActor

        self.state = GameState(
            metadata=Metadata(title="Observability Test"),
            locations=[
                Location(
                    id="room1",
                    name="Test Room",
                    description="A room for testing",
                    exits={}
                )
            ],
            items=[
                Item(
                    id="visible_key",
                    name="key",
                    description="A shiny key",
                    location="room1",
                    properties={"portable": True},
                    behaviors=[]
                ),
                Item(
                    id="hidden_key",
                    name="key",
                    description="A hidden key",
                    location="room1",
                    properties={"portable": True, "states": {"hidden": True}},
                    behaviors=[]
                )
            ],
            actors={
                "player": StateActor(
                    id="player",
                    name="Adventurer",
                    description="The player",
                    location="room1",
                    inventory=[]
                ),
                "merchant": StateActor(
                    id="merchant",
                    name="friendly merchant",
                    description="A friendly merchant",
                    location="room1",
                    inventory=[]
                ),
                "ghost": StateActor(
                    id="ghost",
                    name="ghost",
                    description="A spectral figure",
                    location="room1",
                    properties={"states": {"hidden": True}},
                    inventory=[]
                )
            }
        )

        self.behavior_manager = BehaviorManager()

        from src.state_accessor import StateAccessor
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_hidden_item_not_in_location_contents(self):
        """Hidden item excluded from gather_location_contents."""
        from utilities.utils import gather_location_contents

        contents = gather_location_contents(self.accessor, "room1", "player")
        item_ids = [item.id for item in contents["items"]]

        self.assertIn("visible_key", item_ids)
        self.assertNotIn("hidden_key", item_ids)

    def test_hidden_item_not_found_by_find_accessible_item(self):
        """Hidden item not found by find_accessible_item."""
        from utilities.utils import find_accessible_item

        # Should find the visible key, not the hidden one
        item = find_accessible_item(self.accessor, "key", "player")
        self.assertEqual(item.id, "visible_key")

    def test_revealed_item_becomes_visible_in_location(self):
        """Item becomes visible after states.hidden=False."""
        from utilities.utils import gather_location_contents

        hidden_key = self.accessor.get_item("hidden_key")
        hidden_key.states["hidden"] = False

        contents = gather_location_contents(self.accessor, "room1", "player")
        item_ids = [item.id for item in contents["items"]]

        self.assertIn("hidden_key", item_ids)

    def test_hidden_item_in_container_not_visible(self):
        """Hidden item in an open container is not visible."""
        from utilities.utils import gather_location_contents

        # Add a container with a hidden item inside
        container = Item(
            id="chest",
            name="chest",
            description="An open chest",
            location="room1",
            properties={"container": {"open": True}},
            behaviors=[]
        )
        hidden_gem = Item(
            id="hidden_gem",
            name="gem",
            description="A hidden gem",
            location="chest",
            properties={"states": {"hidden": True}},
            behaviors=[]
        )
        visible_coin = Item(
            id="coin",
            name="coin",
            description="A gold coin",
            location="chest",
            properties={},
            behaviors=[]
        )
        self.state.items.append(container)
        self.state.items.append(hidden_gem)
        self.state.items.append(visible_coin)

        contents = gather_location_contents(self.accessor, "room1", "player")

        # Check items in open containers
        self.assertIn("chest", contents["open_container_items"])
        container_item_ids = [item.id for item in contents["open_container_items"]["chest"]]
        self.assertIn("coin", container_item_ids)
        self.assertNotIn("hidden_gem", container_item_ids)

    def test_hidden_actor_not_in_location_contents(self):
        """Hidden actor excluded from gather_location_contents."""
        from utilities.utils import gather_location_contents

        contents = gather_location_contents(self.accessor, "room1", "player")
        actor_ids = [actor.id for actor in contents["actors"]]

        self.assertIn("merchant", actor_ids)
        self.assertNotIn("ghost", actor_ids)
        # Player is excluded because they're the viewing actor
        self.assertNotIn("player", actor_ids)

    def test_visible_actor_in_location_contents(self):
        """Actor without hidden state is visible in gather_location_contents."""
        from utilities.utils import gather_location_contents

        contents = gather_location_contents(self.accessor, "room1", "player")
        actor_ids = [actor.id for actor in contents["actors"]]

        self.assertIn("merchant", actor_ids)

    def test_revealed_actor_becomes_visible(self):
        """Actor becomes visible after states.hidden=False."""
        from utilities.utils import gather_location_contents

        ghost = self.state.actors["ghost"]
        ghost.states["hidden"] = False

        contents = gather_location_contents(self.accessor, "room1", "player")
        actor_ids = [actor.id for actor in contents["actors"]]

        self.assertIn("ghost", actor_ids)

    def test_hidden_actor_not_in_get_visible_actors(self):
        """Hidden actor excluded from get_visible_actors_in_location."""
        from utilities.utils import get_visible_actors_in_location

        actors = get_visible_actors_in_location(self.accessor, "room1", "player")
        actor_ids = [actor.id for actor in actors]

        self.assertIn("merchant", actor_ids)
        self.assertNotIn("ghost", actor_ids)

    def test_actor_with_states_hidden_false_is_visible(self):
        """Actor with explicit states.hidden=False is visible."""
        from utilities.utils import get_visible_actors_in_location

        # Set explicit hidden=False
        merchant = self.state.actors["merchant"]
        merchant.states["hidden"] = False

        actors = get_visible_actors_in_location(self.accessor, "room1", "player")
        actor_ids = [actor.id for actor in actors]

        self.assertIn("merchant", actor_ids)


class TestHiddenExitsIntegration(unittest.TestCase):
    """Integration tests for hidden exits."""

    def setUp(self):
        """Set up test fixtures with exits."""
        from src.state_manager import GameState, Metadata, Location, Actor as StateActor

        self.state = GameState(
            metadata=Metadata(title="Hidden Exits Test"),
            locations=[
                Location(
                    id="room1",
                    name="Test Room",
                    description="A room for testing",
                    exits={
                        "north": ExitDescriptor(type="open", to="room2"),
                        "south": ExitDescriptor(
                            type="open",
                            to="secret_room",
                            properties={"states": {"hidden": True}}
                        ),
                        "east": ExitDescriptor(
                            type="door",
                            to="room3",
                            door_id="door_east"
                        )
                    }
                ),
                Location(
                    id="room2",
                    name="North Room",
                    description="A room to the north",
                    exits={}
                ),
                Location(
                    id="secret_room",
                    name="Secret Room",
                    description="A hidden room",
                    exits={}
                ),
                Location(
                    id="room3",
                    name="East Room",
                    description="A room to the east",
                    exits={}
                )
            ],
            items=[
                Item(
                    id="door_east",
                    name="wooden door",
                    description="A wooden door",
                    location="exit:room1:east",
                    properties={"door": {"open": True}},
                    behaviors=[]
                )
            ],
            actors={
                "player": StateActor(
                    id="player",
                    name="Adventurer",
                    description="The player",
                    location="room1",
                    inventory=[]
                )
            }
        )

        self.behavior_manager = BehaviorManager()

        from src.state_accessor import StateAccessor
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_hidden_exit_not_in_query_response(self):
        """Hidden exit excluded from _query_location response."""
        from src.llm_protocol import LLMProtocolHandler

        protocol = LLMProtocolHandler(self.state, self.behavior_manager)
        response = protocol.handle_message({
            "type": "query",
            "query_type": "location",
            "include": ["exits"]
        })

        exits = response["data"]["exits"]
        self.assertIn("north", exits)
        self.assertIn("east", exits)
        self.assertNotIn("south", exits)

    def test_visible_exit_in_query_response(self):
        """Visible exit included in _query_location response."""
        from src.llm_protocol import LLMProtocolHandler

        protocol = LLMProtocolHandler(self.state, self.behavior_manager)
        response = protocol.handle_message({
            "type": "query",
            "query_type": "location",
            "include": ["exits"]
        })

        exits = response["data"]["exits"]
        self.assertIn("north", exits)
        self.assertEqual(exits["north"]["to"], "room2")

    def test_hidden_exit_blocks_movement(self):
        """Hidden exit blocks movement (can't go that direction)."""
        from behaviors.core.movement import handle_go

        result = handle_go(
            self.accessor,
            {"actor_id": "player", "direction": "south"}
        )

        self.assertFalse(result.success)
        self.assertIn("can't go south", result.message.lower())

    def test_visible_exit_allows_movement(self):
        """Visible exit allows movement."""
        from behaviors.core.movement import handle_go

        result = handle_go(
            self.accessor,
            {"actor_id": "player", "direction": "north"}
        )

        self.assertTrue(result.success)
        self.assertEqual(self.state.actors["player"].location, "room2")

    def test_revealed_exit_becomes_usable(self):
        """Exit becomes usable after states.hidden=False."""
        from behaviors.core.movement import handle_go

        # Reveal the hidden exit
        hidden_exit = self.state.locations[0].exits["south"]
        hidden_exit.states["hidden"] = False

        result = handle_go(
            self.accessor,
            {"actor_id": "player", "direction": "south"}
        )

        self.assertTrue(result.success)
        self.assertEqual(self.state.actors["player"].location, "secret_room")

    def test_exit_without_hidden_state_is_visible(self):
        """Exit without states.hidden is visible by default."""
        from src.llm_protocol import LLMProtocolHandler

        protocol = LLMProtocolHandler(self.state, self.behavior_manager)
        response = protocol.handle_message({
            "type": "query",
            "query_type": "location",
            "include": ["exits"]
        })

        # north exit has no hidden state
        exits = response["data"]["exits"]
        self.assertIn("north", exits)


if __name__ == "__main__":
    unittest.main()
