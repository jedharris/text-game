"""
Tests for Phase 14: Adjective-Based Disambiguation

Tests utility functions and handler integration for using adjectives
to select specific entities when multiple match a name.
"""
from src.types import ActorId

import unittest
from tests.conftest import create_test_state, make_word_entry, make_action
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.state_manager import Item, Location


class TestFindItemWithAdjective(unittest.TestCase):
    """Test find_accessible_item utility function with adjective parameter."""

    def setUp(self):
        """Set up test state with multiple items of same name."""
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Get player's location
        player = self.game_state.get_actor(ActorId("player"))
        location_id = player.location

        # Add two keys with different adjectives in their descriptions
        iron_key = Item(
            id="item_iron_key",
            name="key",
            description="A small iron key with rust spots.",
            location=location_id,
            _properties={"portable": True}
        )
        brass_key = Item(
            id="item_brass_key",
            name="key",
            description="A large brass key with ornate handle.",
            location=location_id,
            _properties={"portable": True}
        )
        self.game_state.items.append(iron_key)
        self.game_state.items.append(brass_key)

    def test_find_item_with_matching_adjective(self):
        """Test finding item when adjective matches description."""
        from utilities.utils import find_accessible_item

        key_entry = make_word_entry("key")
        item = find_accessible_item(
            self.accessor, key_entry, "player", adjective="iron"
        )

        self.assertIsNotNone(item)
        self.assertEqual(item.id, "item_iron_key")

    def test_find_item_with_different_adjective(self):
        """Test finding different item with different adjective."""
        from utilities.utils import find_accessible_item

        key_entry = make_word_entry("key")


        item = find_accessible_item(


            self.accessor, key_entry, "player", adjective="brass"
        )

        self.assertIsNotNone(item)
        self.assertEqual(item.id, "item_brass_key")

    def test_find_item_no_adjective_returns_first(self):
        """Test that no adjective returns first matching item."""
        from utilities.utils import find_accessible_item

        key_entry = make_word_entry("key")


        item = find_accessible_item(


            self.accessor, key_entry, "player", adjective=None
        )

        self.assertIsNotNone(item)
        # Should return first match (iron key was added first)
        self.assertEqual(item.id, "item_iron_key")

    def test_find_item_empty_adjective_returns_first(self):
        """Test that empty adjective returns first matching item."""
        from utilities.utils import find_accessible_item

        key_entry = make_word_entry("key")


        item = find_accessible_item(


            self.accessor, key_entry, "player", adjective=""
        )

        self.assertIsNotNone(item)
        self.assertEqual(item.id, "item_iron_key")

    def test_find_item_no_match_returns_none(self):
        """Test that non-matching adjective returns None."""
        from utilities.utils import find_accessible_item

        key_entry = make_word_entry("key")


        item = find_accessible_item(


            self.accessor, key_entry, "player", adjective="golden"
        )

        self.assertIsNone(item)

    def test_find_item_adjective_matches_id(self):
        """Test that adjective can match against item ID."""
        from utilities.utils import find_accessible_item

        # "iron" appears in "item_iron_key"
        key_entry = make_word_entry("key")

        item = find_accessible_item(

            self.accessor, key_entry, "player", adjective="iron"
        )

        self.assertIsNotNone(item)
        self.assertEqual(item.id, "item_iron_key")


class TestFindDoorWithAdjective(unittest.TestCase):
    """Test find_door_with_adjective utility function."""

    def setUp(self):
        """Set up test state with multiple doors (as door items)."""
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Get player's location
        player = self.game_state.get_actor(ActorId("player"))
        location_id = player.location

        # Add two door items with different adjectives
        iron_door = Item(
            id="door_iron",
            name="door",
            description="A heavy iron door with rivets.",
            location=f"exit:{location_id}:north",
            _properties={"door": {"open": False, "locked": False}}
        )
        wooden_door = Item(
            id="door_wooden",
            name="door",
            description="A rough wooden door with brass hinges.",
            location=f"exit:{location_id}:east",
            _properties={"door": {"open": False, "locked": False}}
        )
        self.game_state.items.append(iron_door)
        self.game_state.items.append(wooden_door)

    def test_find_door_with_matching_adjective(self):
        """Test finding door when adjective matches description."""
        from utilities.utils import find_door_with_adjective

        player = self.game_state.get_actor(ActorId("player"))
        door_entry = make_word_entry("door")

        door = find_door_with_adjective(
            self.accessor, door_entry, "iron", player.location, ActorId("player")
        )

        self.assertIsNotNone(door)
        self.assertEqual(door.id, "door_iron")

    def test_find_door_with_different_adjective(self):
        """Test finding different door with different adjective."""
        from utilities.utils import find_door_with_adjective

        player = self.game_state.get_actor(ActorId("player"))
        door_entry = make_word_entry("door")

        door = find_door_with_adjective(
            self.accessor, door_entry, "wooden", player.location, ActorId("player")
        )

        self.assertIsNotNone(door)
        self.assertEqual(door.id, "door_wooden")

    def test_find_door_no_adjective_returns_first(self):
        """Test that no adjective returns first matching door."""
        from utilities.utils import find_door_with_adjective

        player = self.game_state.get_actor(ActorId("player"))
        door_entry = make_word_entry("door")

        door = find_door_with_adjective(
            self.accessor, door_entry, None, player.location, ActorId("player")
        )

        self.assertIsNotNone(door)
        # Should return first match

    def test_find_door_no_match_returns_none(self):
        """Test that non-matching adjective returns None."""
        from utilities.utils import find_door_with_adjective

        player = self.game_state.get_actor(ActorId("player"))
        door_entry = make_word_entry("door")

        door = find_door_with_adjective(
            self.accessor, door_entry, "golden", player.location, ActorId("player")
        )

        self.assertIsNone(door)

    def test_find_door_adjective_matches_id(self):
        """Test that adjective can match against door ID."""
        from utilities.utils import find_door_with_adjective

        player = self.game_state.get_actor(ActorId("player"))
        # "iron" appears in "door_iron"
        door_entry = make_word_entry("door")

        door = find_door_with_adjective(
            self.accessor, door_entry, "iron", player.location, ActorId("player")
        )

        self.assertIsNotNone(door)
        self.assertEqual(door.id, "door_iron")


class TestHandleTakeWithAdjective(unittest.TestCase):
    """Test handle_take uses adjective for disambiguation."""

    def setUp(self):
        """Set up test state with multiple items of same name."""
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()

        # Load manipulation module
        import behaviors.core.manipulation
        self.behavior_manager.load_module(behaviors.core.manipulation)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Get player's location
        player = self.game_state.get_actor(ActorId("player"))
        location_id = player.location

        # Add two keys with different adjectives in their descriptions
        iron_key = Item(
            id="item_iron_key",
            name="key",
            description="A small iron key with rust spots.",
            location=location_id,
            _properties={"portable": True}
        )
        brass_key = Item(
            id="item_brass_key",
            name="key",
            description="A large brass key with ornate handle.",
            location=location_id,
            _properties={"portable": True}
        )
        self.game_state.items.append(iron_key)
        self.game_state.items.append(brass_key)

    def test_take_with_adjective_selects_correct_item(self):
        """Test that take with adjective selects correct item."""
        from behaviors.core.manipulation import handle_take

        action = make_action(verb="take", object="key", adjective="brass", actor_id="player")
        result = handle_take(self.accessor, action)

        self.assertTrue(result.success)
        # Verify correct key was taken
        player = self.game_state.get_actor(ActorId("player"))
        self.assertIn("item_brass_key", player.inventory)
        self.assertNotIn("item_iron_key", player.inventory)

    def test_take_without_adjective_takes_first(self):
        """Test that take without adjective takes first match."""
        from behaviors.core.manipulation import handle_take

        action = make_action(verb="take", object="key", actor_id="player")
        result = handle_take(self.accessor, action)

        self.assertTrue(result.success)
        player = self.game_state.get_actor(ActorId("player"))
        # Should take first match (iron key)
        self.assertIn("item_iron_key", player.inventory)


class TestHandleOpenWithAdjective(unittest.TestCase):
    """Test handle_open uses adjective for door disambiguation."""

    def setUp(self):
        """Set up test state with multiple door items."""
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()

        # Load interaction module
        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Get player's location
        player = self.game_state.get_actor(ActorId("player"))
        location_id = player.location

        # Add two door items with different adjectives
        iron_door = Item(
            id="door_iron",
            name="door",
            description="A heavy iron door with rivets.",
            location=f"exit:{location_id}:north",
            _properties={"door": {"open": False, "locked": False}}
        )
        wooden_door = Item(
            id="door_wooden",
            name="door",
            description="A rough wooden door with brass hinges.",
            location=f"exit:{location_id}:east",
            _properties={"door": {"open": False, "locked": False}}
        )
        self.game_state.items.append(iron_door)
        self.game_state.items.append(wooden_door)

    def test_open_with_adjective_selects_correct_door(self):
        """Test that open with adjective selects correct door."""
        from behaviors.core.interaction import handle_open

        action = make_action(verb="open", object="door", adjective="wooden", actor_id="player")
        result = handle_open(self.accessor, action)

        self.assertTrue(result.success)
        # Verify correct door was opened (door items use door_open property)
        wooden_door = next(i for i in self.game_state.items if i.id == "door_wooden")
        iron_door = next(i for i in self.game_state.items if i.id == "door_iron")
        self.assertTrue(wooden_door.door_open)
        self.assertFalse(iron_door.door_open)

    def test_open_without_adjective_opens_first(self):
        """Test that open without adjective opens first match."""
        from behaviors.core.interaction import handle_open

        action = make_action(verb="open", object="door", actor_id="player")
        result = handle_open(self.accessor, action)

        self.assertTrue(result.success)
        # Should open first match (iron door)


class TestDoorStateAdjectives(unittest.TestCase):
    """Test that door state properties work as adjectives (locked, unlocked, open, closed)."""

    def setUp(self):
        """Set up test state with door items having different states."""
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Get player's location
        player = self.game_state.get_actor(ActorId("player"))
        location_id = player.location

        # Create location for exits to point to
        other_location = Location(
            id="loc_other",
            name="Other Room",
            description="Another room.",
            exits={}
        )
        self.game_state.locations.append(other_location)

        # Add two door items - one locked, one unlocked
        # Using unified door item model (properties.door)
        # IMPORTANT: IDs must NOT contain state words (locked/unlocked/open/closed)
        # to properly test that matching works on properties, not ID/description
        iron_door = Item(
            id="door_iron_test",
            name="door",
            description="A heavy iron door.",  # No state words in description
            location=location_id,
            _properties={
                "door": {"open": False, "locked": True}
            }
        )
        wooden_door = Item(
            id="door_wooden_test",
            name="door",
            description="A simple wooden door.",  # No state words in description
            location=location_id,
            _properties={
                "door": {"open": False, "locked": False}
            }
        )
        self.game_state.items.append(iron_door)
        self.game_state.items.append(wooden_door)

    def test_find_door_with_locked_adjective(self):
        """Test that 'locked' adjective matches door with locked=True."""
        from utilities.utils import find_accessible_item

        door_entry = make_word_entry("door")


        item = find_accessible_item(


            self.accessor, door_entry, "player", adjective="locked"
        )

        self.assertIsNotNone(item)
        self.assertEqual(item.id, "door_iron_test")  # iron door is locked

    def test_find_door_with_unlocked_adjective(self):
        """Test that 'unlocked' adjective matches door with locked=False."""
        from utilities.utils import find_accessible_item

        door_entry = make_word_entry("door")


        item = find_accessible_item(


            self.accessor, door_entry, "player", adjective="unlocked"
        )

        self.assertIsNotNone(item)
        self.assertEqual(item.id, "door_wooden_test")  # wooden door is unlocked

    def test_find_door_with_closed_adjective(self):
        """Test that 'closed' adjective matches door with open=False."""
        from utilities.utils import find_accessible_item

        # Both doors are closed, should return first match
        door_entry = make_word_entry("door")

        item = find_accessible_item(

            self.accessor, door_entry, "player", adjective="closed"
        )

        self.assertIsNotNone(item)
        # Should match a door that is closed
        self.assertFalse(item.door_open)

    def test_find_door_with_open_adjective(self):
        """Test that 'open' adjective matches door with open=True."""
        from utilities.utils import find_accessible_item

        # Open one of the doors (iron door)
        iron_door = self.accessor.get_item("door_iron_test")
        iron_door.door_open = True

        door_entry = make_word_entry("door")


        item = find_accessible_item(


            self.accessor, door_entry, "player", adjective="open"
        )

        self.assertIsNotNone(item)
        self.assertEqual(item.id, "door_iron_test")
        self.assertTrue(item.door_open)

    def test_state_adjective_takes_precedence_over_description(self):
        """Test that state adjective matches even if not in description."""
        from utilities.utils import find_accessible_item

        # The iron door is locked but has "iron" in description, not "locked"
        # We search for "locked" which is a state property
        door_entry = make_word_entry("door")

        item = find_accessible_item(

            self.accessor, door_entry, "player", adjective="locked"
        )

        self.assertIsNotNone(item)
        self.assertTrue(item.door_locked)

    def test_open_adjective_parsed_correctly(self):
        """Test that 'examine open door' parses with 'open' as adjective.

        The word 'open' is defined as both VERB and ADJECTIVE (multi-type),
        similar to direction words. The parser selects the appropriate type
        based on pattern matching context.
        """
        from src.parser import Parser

        parser = Parser('tests/command_parser/fixtures/test_vocabulary.json')
        result = parser.parse_command('examine open door')

        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, 'examine')
        self.assertEqual(result.direct_adjective.word, 'open')
        self.assertEqual(result.direct_object.word, 'door')


if __name__ == '__main__':
    unittest.main()
