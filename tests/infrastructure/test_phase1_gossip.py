"""
Phase 1 Gossip System Tests

Tests for gossip creation, queries, and confession windows.
"""

import unittest
from typing import cast

from src.infrastructure_types import (
    BroadcastGossipEntry,
    GossipId,
    NetworkGossipEntry,
    TurnNumber,
)
from src.types import ActorId
from src.infrastructure_utils import (
    can_confess,
    create_broadcast_gossip,
    create_gossip,
    create_network_gossip,
    get_arrived_gossip,
    get_gossip_by_id,
    get_gossip_queue,
    get_pending_gossip_about,
    remove_gossip,
)


class MockState:
    """Mock game state for testing."""

    def __init__(self, turn_count: int = 0) -> None:
        self.extra: dict = {"turn_count": turn_count}


class TestCreateGossip(unittest.TestCase):
    """Test point-to-point gossip creation."""

    def test_create_basic_gossip(self) -> None:
        """Create basic gossip entry."""
        state = MockState(turn_count=5)
        gossip_id = create_gossip(
            state,  # type: ignore[arg-type]
            content="Player stole the artifact",
            source_npc=ActorId("merchant"),
            target_npcs=[ActorId("guard_captain"), ActorId("blacksmith")],
            delay_turns=3,
        )

        queue = get_gossip_queue(state)  # type: ignore[arg-type]
        self.assertEqual(len(queue), 1)
        entry = queue[0]
        self.assertEqual(entry["content"], "Player stole the artifact")
        self.assertEqual(entry["source_npc"], "merchant")
        self.assertEqual(entry["target_npcs"], ["guard_captain", "blacksmith"])
        self.assertEqual(entry["created_turn"], 5)
        self.assertEqual(entry["arrives_turn"], 8)  # 5 + 3

    def test_create_gossip_with_confession_window(self) -> None:
        """Create gossip with confession window."""
        state = MockState(turn_count=10)
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Player broke promise",
            source_npc=ActorId("betrayed_npc"),
            target_npcs=[ActorId("friend_npc")],
            delay_turns=5,
            confession_window=3,
        )

        queue = get_gossip_queue(state)  # type: ignore[arg-type]
        entry = queue[0]
        self.assertEqual(entry["confession_window_until"], 13)  # 10 + 3

    def test_create_gossip_custom_id(self) -> None:
        """Create gossip with custom ID."""
        state = MockState()
        gossip_id = create_gossip(
            state,  # type: ignore[arg-type]
            content="Test",
            source_npc=ActorId("npc"),
            target_npcs=[ActorId("other")],
            gossip_id=GossipId("custom_gossip"),
        )

        self.assertEqual(gossip_id, "custom_gossip")


class TestCreateBroadcastGossip(unittest.TestCase):
    """Test broadcast gossip creation."""

    def test_create_broadcast_gossip_regions(self) -> None:
        """Create broadcast gossip to specific regions."""
        state = MockState(turn_count=0)
        gossip_id = create_broadcast_gossip(
            state,  # type: ignore[arg-type]
            content="Major event occurred",
            source_npc=ActorId("herald"),
            target_regions=["sunken_district", "beast_wilds"],
            delay_turns=2,
        )

        queue = get_gossip_queue(state)  # type: ignore[arg-type]
        self.assertEqual(len(queue), 1)
        entry = cast(BroadcastGossipEntry, queue[0])
        self.assertEqual(entry["type"], "broadcast")
        self.assertEqual(entry["target_regions"], ["sunken_district", "beast_wilds"])

    def test_create_broadcast_gossip_all(self) -> None:
        """Create broadcast gossip to all regions."""
        state = MockState()
        create_broadcast_gossip(
            state,  # type: ignore[arg-type]
            content="World-changing event",
            source_npc=ActorId("god"),
            target_regions="ALL",
        )

        queue = get_gossip_queue(state)  # type: ignore[arg-type]
        entry = cast(BroadcastGossipEntry, queue[0])
        self.assertEqual(entry["target_regions"], "ALL")


class TestCreateNetworkGossip(unittest.TestCase):
    """Test network gossip creation."""

    def test_create_network_gossip(self) -> None:
        """Create gossip targeting a network."""
        state = MockState(turn_count=5)
        gossip_id = create_network_gossip(
            state,  # type: ignore[arg-type]
            content="Intruder detected",
            source_npc=ActorId("spore_mother"),
            network_id="spore_network",
            delay_turns=1,
        )

        queue = get_gossip_queue(state)  # type: ignore[arg-type]
        self.assertEqual(len(queue), 1)
        entry = cast(NetworkGossipEntry, queue[0])
        self.assertEqual(entry["type"], "network")
        self.assertEqual(entry["network_id"], "spore_network")
        self.assertEqual(entry["arrives_turn"], 6)


class TestGetGossipById(unittest.TestCase):
    """Test gossip lookup by ID."""

    def test_find_existing_gossip(self) -> None:
        """Find gossip that exists."""
        state = MockState()
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Test content",
            source_npc=ActorId("npc"),
            target_npcs=[ActorId("other")],
            gossip_id=GossipId("find_me"),
        )

        result = get_gossip_by_id(state, GossipId("find_me"))  # type: ignore[arg-type]
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["content"], "Test content")

    def test_find_missing_gossip(self) -> None:
        """Find gossip that doesn't exist returns None."""
        state = MockState()

        result = get_gossip_by_id(state, GossipId("nonexistent"))  # type: ignore[arg-type]
        self.assertIsNone(result)


class TestGetPendingGossipAbout(unittest.TestCase):
    """Test searching gossip by content."""

    def test_find_matching_gossip(self) -> None:
        """Find gossip containing substring."""
        state = MockState()
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Player killed the guardian",
            source_npc=ActorId("witness"),
            target_npcs=[ActorId("npc1")],
        )
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Player helped the merchant",
            source_npc=ActorId("merchant"),
            target_npcs=[ActorId("npc2")],
        )

        results = get_pending_gossip_about(state, "killed")  # type: ignore[arg-type]
        self.assertEqual(len(results), 1)
        self.assertIn("killed", results[0]["content"])

    def test_case_insensitive_search(self) -> None:
        """Search is case insensitive."""
        state = MockState()
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Player KILLED the guardian",
            source_npc=ActorId("witness"),
            target_npcs=[ActorId("npc1")],
        )

        results = get_pending_gossip_about(state, "killed")  # type: ignore[arg-type]
        self.assertEqual(len(results), 1)


class TestGetArrivedGossip(unittest.TestCase):
    """Test getting arrived gossip."""

    def test_no_arrived_gossip(self) -> None:
        """No gossip has arrived yet."""
        state = MockState(turn_count=5)
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Future gossip",
            source_npc=ActorId("npc"),
            target_npcs=[ActorId("other")],
            delay_turns=10,
        )

        arrived = get_arrived_gossip(state)  # type: ignore[arg-type]
        self.assertEqual(len(arrived), 0)

    def test_some_arrived_gossip(self) -> None:
        """Some gossip has arrived."""
        state = MockState(turn_count=10)
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Past gossip",
            source_npc=ActorId("npc"),
            target_npcs=[ActorId("other")],
            delay_turns=-5,  # Arrived at turn 5
        )
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Future gossip",
            source_npc=ActorId("npc"),
            target_npcs=[ActorId("other")],
            delay_turns=5,  # Arrives at turn 15
        )

        arrived = get_arrived_gossip(state)  # type: ignore[arg-type]
        self.assertEqual(len(arrived), 1)
        self.assertEqual(arrived[0]["content"], "Past gossip")


class TestRemoveGossip(unittest.TestCase):
    """Test gossip removal."""

    def test_remove_existing_gossip(self) -> None:
        """Remove existing gossip."""
        state = MockState()
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Remove me",
            source_npc=ActorId("npc"),
            target_npcs=[ActorId("other")],
            gossip_id=GossipId("remove_me"),
        )

        result = remove_gossip(state, GossipId("remove_me"))  # type: ignore[arg-type]
        self.assertTrue(result)

        queue = get_gossip_queue(state)  # type: ignore[arg-type]
        self.assertEqual(len(queue), 0)

    def test_remove_nonexistent_gossip(self) -> None:
        """Removing nonexistent gossip returns False."""
        state = MockState()

        result = remove_gossip(state, GossipId("nonexistent"))  # type: ignore[arg-type]
        self.assertFalse(result)


class TestCanConfess(unittest.TestCase):
    """Test confession window checking."""

    def test_can_confess_within_window(self) -> None:
        """Confession possible within window."""
        state = MockState(turn_count=5)
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Bad action",
            source_npc=ActorId("npc"),
            target_npcs=[ActorId("other")],
            confession_window=5,  # Window until turn 10
            gossip_id=GossipId("confess_me"),
        )

        result = can_confess(state, GossipId("confess_me"))  # type: ignore[arg-type]
        self.assertTrue(result)

    def test_cannot_confess_after_window(self) -> None:
        """Confession not possible after window expires."""
        state = MockState(turn_count=5)
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Bad action",
            source_npc=ActorId("npc"),
            target_npcs=[ActorId("other")],
            confession_window=2,  # Window until turn 7
            gossip_id=GossipId("too_late"),
        )

        # Advance time past window
        state.extra["turn_count"] = 10

        result = can_confess(state, GossipId("too_late"))  # type: ignore[arg-type]
        self.assertFalse(result)

    def test_cannot_confess_no_window(self) -> None:
        """Confession not possible when no window configured."""
        state = MockState()
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Unconfessable",
            source_npc=ActorId("npc"),
            target_npcs=[ActorId("other")],
            gossip_id=GossipId("no_window"),
            # No confession_window parameter
        )

        result = can_confess(state, GossipId("no_window"))  # type: ignore[arg-type]
        self.assertFalse(result)

    def test_cannot_confess_nonexistent(self) -> None:
        """Confession not possible for nonexistent gossip."""
        state = MockState()

        result = can_confess(state, GossipId("nonexistent"))  # type: ignore[arg-type]
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
