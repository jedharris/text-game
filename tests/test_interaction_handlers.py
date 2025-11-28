"""
Tests for interaction handlers (use, read, climb, pull, push) - Phase C-8.
"""

import unittest
from src.state_manager import GameState, Location, Item, Actor, Metadata
from src.behavior_manager import BehaviorManager
from src.state_accessor import StateAccessor


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
                properties={"pullable": True}
            ),
            Item(
                id="item_button",
                name="button",
                description="A red button",
                location="loc1",
                properties={"pushable": True}
            ),
            Item(
                id="item_book",
                name="book",
                description="An old book",
                location="loc1",
                properties={"portable": True, "readable": True, "text": "Once upon a time..."}
            ),
            Item(
                id="item_ladder",
                name="ladder",
                description="A wooden ladder",
                location="loc1",
                properties={"climbable": True}
            ),
            Item(
                id="item_key",
                name="key",
                description="A brass key",
                location="loc1",
                properties={"portable": True, "usable": True}
            ),
            Item(
                id="item_rock",
                name="rock",
                description="A plain rock",
                location="loc1",
                properties={"portable": True}
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
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_use_no_object(self):
        """Test use without specifying object."""
        from behaviors.core.interaction import handle_use

        action = {"actor_id": "player"}
        result = handle_use(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what", result.message.lower())

    def test_use_item_not_found(self):
        """Test using non-existent item."""
        from behaviors.core.interaction import handle_use

        action = {"actor_id": "player", "object": "wand"}
        result = handle_use(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())

    def test_use_item_success(self):
        """Test using a usable item."""
        from behaviors.core.interaction import handle_use

        action = {"actor_id": "player", "object": "key"}
        result = handle_use(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("use", result.message.lower())


class TestHandleRead(unittest.TestCase):
    """Test handle_read behavior handler."""

    def setUp(self):
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_read_no_object(self):
        """Test read without specifying object."""
        from behaviors.core.interaction import handle_read

        action = {"actor_id": "player"}
        result = handle_read(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what", result.message.lower())

    def test_read_item_not_found(self):
        """Test reading non-existent item."""
        from behaviors.core.interaction import handle_read

        action = {"actor_id": "player", "object": "scroll"}
        result = handle_read(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())

    def test_read_not_readable(self):
        """Test reading non-readable item."""
        from behaviors.core.interaction import handle_read

        action = {"actor_id": "player", "object": "rock"}
        result = handle_read(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't read", result.message.lower())

    def test_read_success(self):
        """Test reading a readable item."""
        from behaviors.core.interaction import handle_read

        action = {"actor_id": "player", "object": "book"}
        result = handle_read(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("read", result.message.lower())


class TestHandleClimb(unittest.TestCase):
    """Test handle_climb behavior handler."""

    def setUp(self):
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_climb_no_object(self):
        """Test climb without specifying object."""
        from behaviors.core.interaction import handle_climb

        action = {"actor_id": "player"}
        result = handle_climb(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what", result.message.lower())

    def test_climb_item_not_found(self):
        """Test climbing non-existent item."""
        from behaviors.core.interaction import handle_climb

        action = {"actor_id": "player", "object": "tree"}
        result = handle_climb(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())

    def test_climb_not_climbable(self):
        """Test climbing non-climbable item."""
        from behaviors.core.interaction import handle_climb

        action = {"actor_id": "player", "object": "rock"}
        result = handle_climb(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't climb", result.message.lower())

    def test_climb_success(self):
        """Test climbing a climbable item."""
        from behaviors.core.interaction import handle_climb

        action = {"actor_id": "player", "object": "ladder"}
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("climb", result.message.lower())


class TestHandlePull(unittest.TestCase):
    """Test handle_pull behavior handler."""

    def setUp(self):
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_pull_no_object(self):
        """Test pull without specifying object."""
        from behaviors.core.interaction import handle_pull

        action = {"actor_id": "player"}
        result = handle_pull(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what", result.message.lower())

    def test_pull_item_not_found(self):
        """Test pulling non-existent item."""
        from behaviors.core.interaction import handle_pull

        action = {"actor_id": "player", "object": "rope"}
        result = handle_pull(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())

    def test_pull_success(self):
        """Test pulling a pullable item."""
        from behaviors.core.interaction import handle_pull

        action = {"actor_id": "player", "object": "lever"}
        result = handle_pull(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("pull", result.message.lower())


class TestHandlePush(unittest.TestCase):
    """Test handle_push behavior handler."""

    def setUp(self):
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_push_no_object(self):
        """Test push without specifying object."""
        from behaviors.core.interaction import handle_push

        action = {"actor_id": "player"}
        result = handle_push(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what", result.message.lower())

    def test_push_item_not_found(self):
        """Test pushing non-existent item."""
        from behaviors.core.interaction import handle_push

        action = {"actor_id": "player", "object": "boulder"}
        result = handle_push(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())

    def test_push_success(self):
        """Test pushing a pushable item."""
        from behaviors.core.interaction import handle_push

        action = {"actor_id": "player", "object": "button"}
        result = handle_push(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("push", result.message.lower())


class TestPushWithAdjective(unittest.TestCase):
    """Test handle_push with adjective for disambiguation (issue #41)."""

    def setUp(self):
        """Set up test state with multiple doors."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.state, self.behavior_manager)

        # Add two door items with different adjectives
        iron_door = Item(
            id="door_iron",
            name="door",
            description="A heavy iron door with rivets.",
            location="loc1",
            properties={"door": {"open": False, "locked": False}}
        )
        wooden_door = Item(
            id="door_wooden",
            name="door",
            description="A rough wooden door with brass hinges.",
            location="loc1",
            properties={"door": {"open": False, "locked": False}}
        )
        self.state.items.append(iron_door)
        self.state.items.append(wooden_door)

    def test_push_with_adjective_selects_correct_door(self):
        """Test that push with adjective selects correct door."""
        from behaviors.core.interaction import handle_push

        action = {
            "actor_id": "player",
            "object": "door",
            "adjective": "iron"
        }
        result = handle_push(self.accessor, action)

        self.assertTrue(result.success)
        # Check that the message mentions the correct door
        # The data should contain the iron door
        self.assertIn("door", result.message.lower())
        # Verify we got the right door by checking data.id
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "door_iron")

    def test_push_with_different_adjective_selects_other_door(self):
        """Test that push with different adjective selects other door."""
        from behaviors.core.interaction import handle_push

        action = {
            "actor_id": "player",
            "object": "door",
            "adjective": "wooden"
        }
        result = handle_push(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the wooden door
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "door_wooden")

    def test_push_without_adjective_returns_first(self):
        """Test that push without adjective returns first match."""
        from behaviors.core.interaction import handle_push

        action = {
            "actor_id": "player",
            "object": "door"
        }
        result = handle_push(self.accessor, action)

        self.assertTrue(result.success)


class TestPullWithAdjective(unittest.TestCase):
    """Test handle_pull with adjective for disambiguation (issue #41)."""

    def setUp(self):
        """Set up test state with multiple levers."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.state, self.behavior_manager)

        # Add two lever items with different adjectives
        # Note: use unique adjectives that don't match the fixture's "rusty lever"
        copper_lever = Item(
            id="lever_copper",
            name="lever",
            description="A tarnished copper lever.",
            location="loc1",
            properties={"pullable": True}
        )
        brass_lever = Item(
            id="lever_brass",
            name="lever",
            description="A shiny brass lever.",
            location="loc1",
            properties={"pullable": True}
        )
        self.state.items.append(copper_lever)
        self.state.items.append(brass_lever)

    def test_pull_with_adjective_selects_correct_lever(self):
        """Test that pull with adjective selects correct lever."""
        from behaviors.core.interaction import handle_pull

        action = {
            "actor_id": "player",
            "object": "lever",
            "adjective": "brass"
        }
        result = handle_pull(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the brass lever
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "lever_brass")

    def test_pull_with_different_adjective_selects_other_lever(self):
        """Test that pull with different adjective selects other lever."""
        from behaviors.core.interaction import handle_pull

        action = {
            "actor_id": "player",
            "object": "lever",
            "adjective": "copper"
        }
        result = handle_pull(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the copper lever
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "lever_copper")


class TestReadWithAdjective(unittest.TestCase):
    """Test handle_read with adjective for disambiguation (Phase 3)."""

    def setUp(self):
        """Set up test state with multiple readable items."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.state, self.behavior_manager)

        # Add two book items with different adjectives
        ancient_book = Item(
            id="book_ancient",
            name="book",
            description="An ancient tome.",
            location="loc1",
            properties={"portable": True, "readable": True, "text": "Ancient secrets..."}
        )
        leather_book = Item(
            id="book_leather",
            name="book",
            description="A leather-bound journal.",
            location="loc1",
            properties={"portable": True, "readable": True, "text": "Dear diary..."}
        )
        self.state.items.append(ancient_book)
        self.state.items.append(leather_book)

    def test_read_with_adjective_selects_correct_item(self):
        """Test that read with adjective selects correct item."""
        from behaviors.core.interaction import handle_read

        action = {
            "actor_id": "player",
            "verb": "read",
            "object": "book",
            "adjective": "ancient"
        }
        result = handle_read(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the ancient book
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "book_ancient")
        # Verify the text is in the message
        self.assertIn("Ancient secrets", result.message)

    def test_read_with_different_adjective_selects_other_item(self):
        """Test that read with different adjective selects other item."""
        from behaviors.core.interaction import handle_read

        action = {
            "actor_id": "player",
            "verb": "read",
            "object": "book",
            "adjective": "leather"
        }
        result = handle_read(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the leather book
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "book_leather")
        # Verify the text is in the message
        self.assertIn("Dear diary", result.message)


class TestClimbWithAdjective(unittest.TestCase):
    """Test handle_climb with adjective for disambiguation (Phase 3)."""

    def setUp(self):
        """Set up test state with multiple climbable items."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.state, self.behavior_manager)

        # Add two ladder items with different adjectives
        rope_ladder = Item(
            id="ladder_rope",
            name="ladder",
            description="A rope ladder.",
            location="loc1",
            properties={"climbable": True}
        )
        metal_ladder = Item(
            id="ladder_metal",
            name="ladder",
            description="A metal ladder.",
            location="loc1",
            properties={"climbable": True}
        )
        self.state.items.append(rope_ladder)
        self.state.items.append(metal_ladder)

    def test_climb_with_adjective_selects_correct_item(self):
        """Test that climb with adjective selects correct item."""
        from behaviors.core.interaction import handle_climb

        action = {
            "actor_id": "player",
            "verb": "climb",
            "object": "ladder",
            "adjective": "rope"
        }
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the rope ladder
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "ladder_rope")

    def test_climb_with_different_adjective_selects_other_item(self):
        """Test that climb with different adjective selects other item."""
        from behaviors.core.interaction import handle_climb

        action = {
            "actor_id": "player",
            "verb": "climb",
            "object": "ladder",
            "adjective": "metal"
        }
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the metal ladder
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "ladder_metal")


class TestUseWithAdjective(unittest.TestCase):
    """Test handle_use with adjective for disambiguation (Phase 2)."""

    def setUp(self):
        """Set up test state with multiple similar items."""
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        import behaviors.core.interaction
        self.behavior_manager.load_module(behaviors.core.interaction)

        self.accessor = StateAccessor(self.state, self.behavior_manager)

        # Add two key items with different adjectives
        gold_key = Item(
            id="key_gold",
            name="key",
            description="A gleaming gold key.",
            location="loc1",
            properties={"portable": True, "usable": True}
        )
        silver_key = Item(
            id="key_silver",
            name="key",
            description="A tarnished silver key.",
            location="loc1",
            properties={"portable": True, "usable": True}
        )
        self.state.items.append(gold_key)
        self.state.items.append(silver_key)

    def test_use_with_adjective_selects_correct_item(self):
        """Test that use with adjective selects correct item."""
        from behaviors.core.interaction import handle_use

        action = {
            "actor_id": "player",
            "verb": "use",
            "object": "key",
            "adjective": "gold"
        }
        result = handle_use(self.accessor, action)

        self.assertTrue(result.success)
        # Verify we got the gold key
        if result.data and "id" in result.data:
            self.assertEqual(result.data["id"], "key_gold")

    def test_use_with_different_adjective_selects_other_item(self):
        """Test that use with different adjective selects other item."""
        from behaviors.core.interaction import handle_use

        action = {
            "actor_id": "player",
            "verb": "use",
            "object": "key",
            "adjective": "silver"
        }
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

        self.state = GameState(
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
        import behaviors.core.movement
        self.behavior_manager.load_module(behaviors.core.interaction)
        self.behavior_manager.load_module(behaviors.core.movement)

        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_climb_stairs_moves_to_destination(self):
        """Test climbing 'stairs' moves player to destination via exit named 'spiral staircase'.

        Uses WordEntry with synonyms as the actual game parser does.
        """
        from behaviors.core.interaction import handle_climb
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
        self.assertIn("climb", result.message.lower())
        self.assertIn("spiral staircase", result.message.lower())
        self.assertIn("Tower Room", result.message)
        # Verify player actually moved
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "loc_tower")

    def test_climb_staircase_moves_to_destination(self):
        """Test climbing 'staircase' moves player to destination."""
        from behaviors.core.interaction import handle_climb

        # "staircase" is a direct word match in the exit name
        action = {"actor_id": "player", "verb": "climb", "object": "staircase"}
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        # Verify player actually moved
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "loc_tower")

    def test_climb_spiral_staircase_moves_to_destination(self):
        """Test climbing 'spiral staircase' moves player to destination."""
        from behaviors.core.interaction import handle_climb

        action = {"actor_id": "player", "verb": "climb", "object": "spiral staircase"}
        result = handle_climb(self.accessor, action)

        self.assertTrue(result.success)
        # Verify player actually moved
        player = self.accessor.get_actor("player")
        self.assertEqual(player.location, "loc_tower")

    def test_climb_nonexistent_exit_fails(self):
        """Test climbing non-existent exit fails with helpful message."""
        from behaviors.core.interaction import handle_climb

        action = {"actor_id": "player", "verb": "climb", "object": "tree"}
        result = handle_climb(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())

    def test_climb_unnamed_exit_does_not_match(self):
        """Test climbing something that doesn't match an exit name fails."""
        from behaviors.core.interaction import handle_climb

        # "north" is a direction, not an object name for climbing
        action = {"actor_id": "player", "verb": "climb", "object": "wall"}
        result = handle_climb(self.accessor, action)

        self.assertFalse(result.success)


if __name__ == '__main__':
    unittest.main()
