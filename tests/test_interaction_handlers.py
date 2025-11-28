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


if __name__ == '__main__':
    unittest.main()
