"""Tests for _handle_door_or_container_state_change helper."""
import unittest
from unittest.mock import Mock
from dataclasses import dataclass
from typing import Optional

from src.types import ActorId
from src.state_accessor import HandlerResult, StateAccessor, UpdateResult
from utilities.handler_utils import _handle_door_or_container_state_change
from utilities.entity_serializer import serialize_for_handler_result


@dataclass
class MockDoor:
    """Mock door item."""
    id: str
    name: str
    is_door: bool = True
    door_open: bool = False
    door_locked: bool = False


@dataclass
class MockContainer:
    open: bool = False


@dataclass
class MockItem:
    """Mock container item."""
    id: str
    name: str
    container: Optional[MockContainer] = None
    is_door: bool = False


class TestDoorOrContainerStateChange(unittest.TestCase):
    """Test _handle_door_or_container_state_change helper."""

    def setUp(self):
        """Set up test fixtures."""
        self.accessor = Mock(spec=StateAccessor)
        self.actor_id = ActorId("player")

    def test_open_already_open_door(self):
        """Test opening a door that's already open."""
        door = MockDoor(id="door1", name="wooden door", door_open=True)

        result = _handle_door_or_container_state_change(
            self.accessor, door, self.actor_id,
            target_state=True, verb="open"
        )

        self.assertTrue(result.success)
        self.assertIn("already open", result.primary)
        self.assertIn("wooden door", result.primary)

    def test_close_already_closed_door(self):
        """Test closing a door that's already closed."""
        door = MockDoor(id="door1", name="wooden door", door_open=False)

        result = _handle_door_or_container_state_change(
            self.accessor, door, self.actor_id,
            target_state=False, verb="close"
        )

        self.assertTrue(result.success)
        self.assertIn("already closed", result.primary)
        self.assertIn("wooden door", result.primary)

    def test_open_locked_door(self):
        """Test opening a locked door fails."""
        door = MockDoor(id="door1", name="wooden door", door_locked=True)

        result = _handle_door_or_container_state_change(
            self.accessor, door, self.actor_id,
            target_state=True, verb="open"
        )

        self.assertFalse(result.success)
        self.assertIn("locked", result.primary)

    def test_open_door_success(self):
        """Test successfully opening a door."""
        door = MockDoor(id="door1", name="wooden door")

        result = _handle_door_or_container_state_change(
            self.accessor, door, self.actor_id,
            target_state=True, verb="open"
        )

        self.assertTrue(result.success)
        self.assertIn("open", result.primary)
        self.assertIn("wooden door", result.primary)
        self.assertTrue(door.door_open)

    def test_close_door_success(self):
        """Test successfully closing a door."""
        door = MockDoor(id="door1", name="wooden door", door_open=True)

        result = _handle_door_or_container_state_change(
            self.accessor, door, self.actor_id,
            target_state=False, verb="close"
        )

        self.assertTrue(result.success)
        self.assertIn("close", result.primary)
        self.assertIn("wooden door", result.primary)
        self.assertFalse(door.door_open)

    def test_open_container_already_open(self):
        """Test opening a container that's already open."""
        item = MockItem(id="item1", name="chest", container=MockContainer(open=True))

        result = _handle_door_or_container_state_change(
            self.accessor, item, self.actor_id,
            target_state=True, verb="open"
        )

        self.assertTrue(result.success)
        self.assertIn("already open", result.primary)

    def test_open_container_success(self):
        """Test successfully opening a container."""
        item = MockItem(id="item1", name="chest", container=MockContainer(open=False))

        # Mock accessor.update() success
        self.accessor.update.return_value = UpdateResult(success=True, detail=None)

        result = _handle_door_or_container_state_change(
            self.accessor, item, self.actor_id,
            target_state=True, verb="open"
        )

        self.assertTrue(result.success)
        self.assertIn("open", result.primary)
        self.assertIn("chest", result.primary)

        # Verify accessor.update was called
        self.accessor.update.assert_called_once_with(
            item,
            {"container.open": True},
            verb="open",
            actor_id=self.actor_id
        )

    def test_close_container_success(self):
        """Test successfully closing a container."""
        item = MockItem(id="item1", name="chest", container=MockContainer(open=True))

        # Mock accessor.update() success
        self.accessor.update.return_value = UpdateResult(success=True, detail=None)

        result = _handle_door_or_container_state_change(
            self.accessor, item, self.actor_id,
            target_state=False, verb="close"
        )

        self.assertTrue(result.success)
        self.assertIn("close", result.primary)
        self.assertIn("chest", result.primary)

        # Verify accessor.update was called
        self.accessor.update.assert_called_once_with(
            item,
            {"container.open": False},
            verb="close",
            actor_id=self.actor_id
        )

    def test_with_move_message(self):
        """Test that move messages are included in beats."""
        door = MockDoor(id="door1", name="wooden door")

        result = _handle_door_or_container_state_change(
            self.accessor, door, self.actor_id,
            target_state=True, verb="open",
            move_msg="You step closer to the door."
        )

        self.assertTrue(result.success)
        self.assertIsNotNone(result.beats)
        self.assertIn("You step closer to the door.", result.beats)

    def test_with_event_detail(self):
        """Test that event details are included in beats."""
        item = MockItem(id="item1", name="chest", container=MockContainer(open=False))

        # Mock accessor.update() with detail
        self.accessor.update.return_value = UpdateResult(
            success=True,
            detail="The chest creaks as it opens."
        )

        result = _handle_door_or_container_state_change(
            self.accessor, item, self.actor_id,
            target_state=True, verb="open"
        )

        self.assertTrue(result.success)
        self.assertIsNotNone(result.beats)
        self.assertIn("The chest creaks as it opens.", result.beats)

    def test_container_open_fails(self):
        """Test failed container opening (behavior blocks it)."""
        item = MockItem(id="item1", name="chest", container=MockContainer(open=False))

        # Mock accessor.update() failure
        self.accessor.update.return_value = UpdateResult(
            success=False,
            detail="The chest is magically sealed."
        )

        result = _handle_door_or_container_state_change(
            self.accessor, item, self.actor_id,
            target_state=True, verb="open"
        )

        self.assertFalse(result.success)
        self.assertIn("magically sealed", result.primary)


if __name__ == '__main__':
    unittest.main()
