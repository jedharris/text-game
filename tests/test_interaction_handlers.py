"""
Tests for interaction handlers (use, read, climb, pull, push) - Phase C-8.
"""
from src.types import ActorId

import unittest
from src.state_manager import GameState, Location, Item, Actor, Metadata
from src.behavior_manager import BehaviorManager
from src.state_accessor import StateAccessor
from tests.conftest import make_action


def create_test_state():
    """Create a minimal test state with interactable items."""
    return GameState(
        metadata=Metadata(title="Test"),
        locations=[
            Location(id="loc1", name="Room", description="A test room")
        ],
        items=[
            Item(
                id="item_lever",
                name="lever",
                description="A rusty lever",
                location="loc1",
                _properties={"pullable": True}
            ),
            Item(
                id="item_button",
                name="button",
                description="A red button",
                location="loc1",
                _properties={"pushable": True}
            ),
            Item(
                id="item_book",
                name="book",
                description="An old book",
                location="loc1",
                _properties={"portable": True, "readable": True, "text": "Once upon a time..."}
            ),
            Item(
                id="item_ladder",
                name="ladder",
                description="A wooden ladder",
                location="loc1",
                _properties={"climbable": True}
            ),
            Item(
                id="item_key",
                name="key",
                description="A brass key",
                location="loc1",
                _properties={"portable": True, "usable": True}
            ),
            Item(
                id="item_rock",
                name="rock",
                description="A plain rock",
                location="loc1",
                _properties={"portable": True}
            )
        ],
        actors={
            "player": Actor(
                id="player",
                name="Adventurer",
                description="The player",
                location="loc1",
                inventory=[]
            ),
            "npc_guard": Actor(
                id="npc_guard",
                name="guard",
                description="A guard",
                location="loc1",
                inventory=[]
            )
        }
    )


class TestHandleUse(unittest.TestCase):
    """Test handle_use behavior handler."""

    def setUp(self):
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_use_no_object(self):
        """Test use without specifying object."""
        from behaviors.core.interaction import handle_use

        action = {"actor_id": "player"}
        result = handle_use(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what", result.primary.lower())

    def test_use_item_not_found(self):
        """Test using non-existent item."""
        from behaviors.core.interaction import handle_use

        action = make_action(object="wand", actor_id="player")
        result = handle_use(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.primary.lower())

    def test_use_item_success(self):
        """Test using a usable item."""
        from behaviors.core.interaction import handle_use

        action = make_action(verb="use", object="key", actor_id="player")
        result = handle_use(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("use", result.primary.lower())


class TestHandleRead(unittest.TestCase):
    """Test handle_read behavior handler."""

    def setUp(self):
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_read_no_object(self):
        """Test read without specifying object."""
        from behaviors.core.interaction import handle_read

        action = {"actor_id": "player"}
        result = handle_read(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what", result.primary.lower())

    def test_read_item_not_found(self):
        """Test reading non-existent item."""
        from behaviors.core.interaction import handle_read

        action = make_action(object="scroll", actor_id="player")
        result = handle_read(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.primary.lower())

    def test_read_not_readable(self):
        """Test reading non-readable item."""
        from behaviors.core.interaction import handle_read

        action = make_action(verb="read", object="rock", actor_id="player")
        result = handle_read(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't read", result.primary.lower())

    def test_read_success(self):
        """Test reading a readable item."""
        from behaviors.core.interaction import handle_read

        action = make_action(verb="read", object="book", actor_id="player")
        result = handle_read(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("read", result.primary.lower())


class TestHandleClimb(unittest.TestCase):
    """Test handle_climb behavior handler."""

    def setUp(self):
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_climb_no_object(self):
        """Test climb without specifying object."""
        from behaviors.core.spatial import handle_climb

        action = {"actor_id": "player"}
        result = handle_climb(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what", result.primary.lower())

    def test_climb_item_not_found(self):
        """Test climbing non-existent item."""
        from behaviors.core.spatial import handle_climb

        action = make_action(object="tree", actor_id="player")
        result = handle_climb(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.primary.lower())

    def test_climb_not_climbable(self):
        """Test climbing non-climbable item."""
        from behaviors.core.spatial import handle_climb

        action = make_action(object="rock", actor_id="player")
        result = handle_climb(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't climb", result.primary.lower())

    def test_climb_success(self):
        """Test climbing a climbable item."""
        from behaviors.core.spatial import handle_climb

        action = make_action(object="ladder", actor_id="player")
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("climb", result.primary.lower())


class TestHandlePull(unittest.TestCase):
    """Test handle_pull behavior handler."""

    def setUp(self):
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_pull_no_object(self):
        """Test pull without specifying object."""
        from behaviors.core.interaction import handle_pull

        action = {"actor_id": "player"}
        result = handle_pull(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what", result.primary.lower())

    def test_pull_item_not_found(self):
        """Test pulling non-existent item."""
        from behaviors.core.interaction import handle_pull

        action = make_action(object="rope", actor_id="player")
        result = handle_pull(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.primary.lower())

    def test_pull_success(self):
        """Test pulling a pullable item."""
        from behaviors.core.interaction import handle_pull

        action = make_action(verb="pull", object="lever", actor_id="player")
        result = handle_pull(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("pull", result.primary.lower())


class TestHandlePush(unittest.TestCase):
    """Test handle_push behavior handler."""

    def setUp(self):
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_push_no_object(self):
        """Test push without specifying object."""
        from behaviors.core.interaction import handle_push

        action = {"actor_id": "player"}
        result = handle_push(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what", result.primary.lower())

    def test_push_item_not_found(self):
        """Test pushing non-existent item."""
        from behaviors.core.interaction import handle_push

        action = make_action(object="boulder", actor_id="player")
        result = handle_push(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.primary.lower())

    def test_push_success(self):
        """Test pushing a pushable item."""
        from behaviors.core.interaction import handle_push

        action = make_action(verb="push", object="button", actor_id="player")
        result = handle_push(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("push", result.primary.lower())


class TestPushWithAdjective(unittest.TestCase):
    """Test handle_push with adjective for disambiguation (issue #41)."""

    def setUp(self):
        """Set up test state with multiple doors."""
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Add two door items with different adjectives
        iron_door = Item(
            id="door_iron",
            name="door",
            description="A heavy iron door with rivets.",
            location="loc1",
            _properties={"door": {"open": False, "locked": False}}
        )
        wooden_door = Item(
            id="door_wooden",
            name="door",
            description="A rough wooden door with brass hinges.",
            location="loc1",
            _properties={"door": {"open": False, "locked": False}}
        )
        self.game_state.items.append(iron_door)
        self.game_state.items.append(wooden_door)

    def test_push_with_adjective_selects_correct_door(self):
        """Test that push with adjective selects correct door."""
        from behaviors.core.interaction import handle_push

        action = make_action(verb="push", object="door", adjective="iron", actor_id="player")
        result = handle_push(self.accessor, action)

        self.assertTrue(result.success)
        # Check that the message mentions the correct door
        # The data should contain the iron door
        self.assertIn("door", result.primary.lower())
        # Verify we got the right door by checking data.id
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "door_iron")

    def test_push_with_different_adjective_selects_other_door(self):
        """Test that push with different adjective selects other door."""
        from behaviors.core.interaction import handle_push

        action = make_action(verb="push", object="door", adjective="wooden", actor_id="player")
        result = handle_push(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the wooden door
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "door_wooden")

    def test_push_without_adjective_returns_first(self):
        """Test that push without adjective returns first match."""
        from behaviors.core.interaction import handle_push

        action = make_action(verb="push", object="door", actor_id="player")
        result = handle_push(self.accessor, action)

        self.assertTrue(result.success)


class TestPullWithAdjective(unittest.TestCase):
    """Test handle_pull with adjective for disambiguation (issue #41)."""

    def setUp(self):
        """Set up test state with multiple levers."""
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Add two lever items with different adjectives
        # Note: use unique adjectives that don't match the fixture's "rusty lever"
        copper_lever = Item(
            id="lever_copper",
            name="lever",
            description="A tarnished copper lever.",
            location="loc1",
            _properties={"pullable": True}
        )
        brass_lever = Item(
            id="lever_brass",
            name="lever",
            description="A shiny brass lever.",
            location="loc1",
            _properties={"pullable": True}
        )
        self.game_state.items.append(copper_lever)
        self.game_state.items.append(brass_lever)

    def test_pull_with_adjective_selects_correct_lever(self):
        """Test that pull with adjective selects correct lever."""
        from behaviors.core.interaction import handle_pull

        action = make_action(verb="pull", object="lever", adjective="brass", actor_id="player")
        result = handle_pull(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the brass lever
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "lever_brass")

    def test_pull_with_different_adjective_selects_other_lever(self):
        """Test that pull with different adjective selects other lever."""
        from behaviors.core.interaction import handle_pull

        action = make_action(verb="pull", object="lever", adjective="copper", actor_id="player")
        result = handle_pull(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the copper lever
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "lever_copper")


class TestReadWithAdjective(unittest.TestCase):
    """Test handle_read with adjective for disambiguation (Phase 3)."""

    def setUp(self):
        """Set up test state with multiple readable items."""
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Add two book items with different adjectives
        ancient_book = Item(
            id="book_ancient",
            name="book",
            description="An ancient tome.",
            location="loc1",
            _properties={"portable": True, "readable": True, "text": "Ancient secrets..."}
        )
        leather_book = Item(
            id="book_leather",
            name="book",
            description="A leather-bound journal.",
            location="loc1",
            _properties={"portable": True, "readable": True, "text": "Dear diary..."}
        )
        self.game_state.items.append(ancient_book)
        self.game_state.items.append(leather_book)

    def test_read_with_adjective_selects_correct_item(self):
        """Test that read with adjective selects correct item."""
        from behaviors.core.interaction import handle_read

        action = make_action(verb="read", object="book", adjective="ancient", actor_id="player")
        result = handle_read(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the ancient book
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "book_ancient")
        # Verify the text is in the message
        self.assertIn("Ancient secrets", result.primary)

    def test_read_with_different_adjective_selects_other_item(self):
        """Test that read with different adjective selects other item."""
        from behaviors.core.interaction import handle_read

        action = make_action(verb="read", object="book", adjective="leather", actor_id="player")
        result = handle_read(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the leather book
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "book_leather")
        # Verify the text is in the message
        self.assertIn("Dear diary", result.primary)


class TestClimbWithAdjective(unittest.TestCase):
    """Test handle_climb with adjective for disambiguation (Phase 3)."""

    def setUp(self):
        """Set up test state with multiple climbable items."""
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Remove the original ladder from create_test_state()
        self.game_state.items = [item for item in self.game_state.items if item.id != "item_ladder"]

        # Add two ladder items with different adjectives
        rope_ladder = Item(
            id="ladder_rope",
            name="ladder",
            description="A rope ladder.",
            location="loc1",
            _properties={"climbable": True}
        )
        metal_ladder = Item(
            id="ladder_metal",
            name="ladder",
            description="A metal ladder.",
            location="loc1",
            _properties={"climbable": True}
        )
        self.game_state.items.append(rope_ladder)
        self.game_state.items.append(metal_ladder)

    def test_climb_with_adjective_selects_correct_item(self):
        """Test that climb with adjective selects correct item."""
        from behaviors.core.spatial import handle_climb

        action = make_action(verb="climb", object="ladder", adjective="rope", actor_id="player")
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the rope ladder
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "ladder_rope")

    def test_climb_with_different_adjective_selects_other_item(self):
        """Test that climb with different adjective selects other item."""
        from behaviors.core.spatial import handle_climb

        action = make_action(verb="climb", object="ladder", adjective="metal", actor_id="player")
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the metal ladder
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "ladder_metal")


class TestUseWithAdjective(unittest.TestCase):
    """Test handle_use with adjective for disambiguation (Phase 2)."""

    def setUp(self):
        """Set up test state with multiple similar items."""
        self.game_state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

        # Add two key items with different adjectives
        gold_key = Item(
            id="key_gold",
            name="key",
            description="A gleaming gold key.",
            location="loc1",
            _properties={"portable": True, "usable": True}
        )
        silver_key = Item(
            id="key_silver",
            name="key",
            description="A tarnished silver key.",
            location="loc1",
            _properties={"portable": True, "usable": True}
        )
        self.game_state.items.append(gold_key)
        self.game_state.items.append(silver_key)

    def test_use_with_adjective_selects_correct_item(self):
        """Test that use with adjective selects correct item."""
        from behaviors.core.interaction import handle_use

        action = make_action(verb="use", object="key", adjective="gold", actor_id="player")
        result = handle_use(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the gold key
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "key_gold")

    def test_use_with_different_adjective_selects_other_item(self):
        """Test that use with different adjective selects other item."""
        from behaviors.core.interaction import handle_use

        action = make_action(verb="use", object="key", adjective="silver", actor_id="player")
        result = handle_use(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the silver key
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "key_silver")


class TestClimbExit(unittest.TestCase):
    """Test handle_climb for exits (like stairs) - Issue #45."""

    def setUp(self):
        """Set up test state with an exit that has a name."""
        from src.state_manager import ExitDescriptor

        self.game_state = GameState(
            metadata=Metadata(title="Test"),
            locations=[
                Location(
                    id="loc_hallway",
                    name="Long Hallway",
                    description="A long stone hallway.",
                    exits={
                        "up": ExitDescriptor(
                            type="open",
                            to="loc_tower",
                            name="spiral staircase",
                            description="A narrow spiral staircase winds upward."
                        ),
                        "north": ExitDescriptor(
                            type="open",
                            to="loc_courtyard"
                        )
                    }
                ),
                Location(
                    id="loc_tower",
                    name="Tower Room",
                    description="A circular tower room."
                ),
                Location(
                    id="loc_courtyard",
                    name="Courtyard",
                    description="An open courtyard."
                )
            ],
            items=[],
            actors={
                "player": Actor(
                    id="player",
                    name="Adventurer",
                    description="The player",
                    location="loc_hallway",
                    inventory=[]
                )
            }
        )
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        import behaviors.core.exits
        self.behavior_manager.load_module(behaviors.core.interaction)
        self.behavior_manager.load_module(behaviors.core.exits)

        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_climb_stairs_moves_to_destination(self):
        """Test climbing 'stairs' moves player to destination via exit named 'spiral staircase'.

        Uses WordEntry with synonyms as the actual game parser does.
        """
        from behaviors.core.exits import handle_climb
        from src.parser import WordEntry, WordType

        # When player types "climb stairs", parser creates WordEntry with synonyms
        stairs_entry = WordEntry(
            word="stairs",
            word_type=WordType.NOUN,
            synonyms=["staircase", "stairway", "steps"]
        )
        action = {"actor_id": "player", "verb": "climb", "object": stairs_entry}
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("climb", result.primary.lower())
        self.assertIn("spiral staircase", result.primary.lower())
        self.assertIn("Tower Room", result.primary)
        # Verify player actually moved
        player = self.accessor.get_actor(ActorId("player"))
        self.assertEqual(player.location, "loc_tower")

    def test_climb_staircase_moves_to_destination(self):
        """Test climbing 'staircase' moves player to destination."""
        from behaviors.core.exits import handle_climb

        # "staircase" is a direct word match in the exit name
        action = make_action(verb="climb", object="staircase", actor_id="player")
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        # Verify player actually moved
        player = self.accessor.get_actor(ActorId("player"))
        self.assertEqual(player.location, "loc_tower")

    def test_climb_spiral_staircase_moves_to_destination(self):
        """Test climbing 'spiral staircase' moves player to destination."""
        from behaviors.core.exits import handle_climb

        action = make_action(verb="climb", object="spiral staircase", actor_id="player")
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        # Verify player actually moved
        player = self.accessor.get_actor(ActorId("player"))
        self.assertEqual(player.location, "loc_tower")

    def test_climb_nonexistent_exit_fails(self):
        """Test climbing non-existent exit fails silently (for handler chaining)."""
        from behaviors.core.exits import handle_climb

        action = make_action(verb="climb", object="tree", actor_id="player")
        result = handle_climb(self.accessor, action)

        self.assertFalse(result.success)
        # Should return empty message to allow other handlers to try
        self.assertEqual(result.primary, "")

    def test_climb_unnamed_exit_does_not_match(self):
        """Test climbing something that doesn't match an exit name fails."""
        from behaviors.core.exits import handle_climb

        # "north" is a direction, not an object name for climbing
        action = make_action(verb="climb", object="wall", actor_id="player")
        result = handle_climb(self.accessor, action)

        self.assertFalse(result.success)


if __name__ == '__main__':
    unittest.main()
