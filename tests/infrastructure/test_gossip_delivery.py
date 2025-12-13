"""Tests for gossip delivery function."""

import unittest

from src.infrastructure_types import GossipId, TurnNumber
from src.types import ActorId
from src.infrastructure_utils import (
    create_gossip,
    deliver_due_gossip,
    get_gossip_queue,
)


class MockState:
    """Mock game state for testing."""

    def __init__(self) -> None:
        self.extra: dict = {}
        self.actors: dict = {}


class TestDeliverDueGossip(unittest.TestCase):
    """Tests for deliver_due_gossip."""

    def test_delivers_arrived_gossip(self) -> None:
        """Gossip that has arrived is delivered and removed."""
        state = MockState()
        # Set current turn to 10 when creating gossip
        state.extra["turn_count"] = 10
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Test message",
            source_npc=ActorId("npc_a"),
            target_npcs=[ActorId("npc_b")],
            delay_turns=5,
            gossip_id=GossipId("test_gossip"),
        )

        # At turn 15, the gossip should arrive (created at 10 + delay 5 = arrives at 15)
        delivered = deliver_due_gossip(state, TurnNumber(15))  # type: ignore[arg-type]

        self.assertEqual(len(delivered), 1)
        self.assertEqual(delivered[0]["id"], "test_gossip")
        self.assertEqual(len(get_gossip_queue(state)), 0)  # type: ignore[arg-type]

    def test_does_not_deliver_future_gossip(self) -> None:
        """Gossip that hasn't arrived yet is not delivered."""
        state = MockState()
        # Set current turn to 5 when creating gossip
        state.extra["turn_count"] = 5
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Test message",
            source_npc=ActorId("npc_a"),
            target_npcs=[ActorId("npc_b")],
            delay_turns=10,
            gossip_id=GossipId("test_gossip"),
        )

        # At turn 10, the gossip hasn't arrived yet (created at 5 + delay 10 = arrives at 15)
        delivered = deliver_due_gossip(state, TurnNumber(10))  # type: ignore[arg-type]

        self.assertEqual(len(delivered), 0)
        self.assertEqual(len(get_gossip_queue(state)), 1)  # type: ignore[arg-type]

    def test_delivers_multiple_gossip(self) -> None:
        """Multiple arrived gossip entries are all delivered."""
        state = MockState()
        # Set current turn to 0 when creating gossip
        state.extra["turn_count"] = 0
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Message 1",
            source_npc=ActorId("npc_a"),
            target_npcs=[ActorId("npc_b")],
            delay_turns=5,
            gossip_id=GossipId("gossip_1"),
        )
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Message 2",
            source_npc=ActorId("npc_c"),
            target_npcs=[ActorId("npc_d")],
            delay_turns=3,
            gossip_id=GossipId("gossip_2"),
        )

        # At turn 10, both should have arrived
        delivered = deliver_due_gossip(state, TurnNumber(10))  # type: ignore[arg-type]

        self.assertEqual(len(delivered), 2)
        self.assertEqual(len(get_gossip_queue(state)), 0)  # type: ignore[arg-type]

    def test_partial_delivery(self) -> None:
        """Only arrived gossip is delivered, future gossip remains."""
        state = MockState()
        # Set current turn to 0 when creating gossip
        state.extra["turn_count"] = 0
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Early message",
            source_npc=ActorId("npc_a"),
            target_npcs=[ActorId("npc_b")],
            delay_turns=2,
            gossip_id=GossipId("early"),
        )
        create_gossip(
            state,  # type: ignore[arg-type]
            content="Late message",
            source_npc=ActorId("npc_c"),
            target_npcs=[ActorId("npc_d")],
            delay_turns=10,
            gossip_id=GossipId("late"),
        )

        # At turn 5, only the early gossip should arrive
        delivered = deliver_due_gossip(state, TurnNumber(5))  # type: ignore[arg-type]

        self.assertEqual(len(delivered), 1)
        self.assertEqual(delivered[0]["id"], "early")
        self.assertEqual(len(get_gossip_queue(state)), 1)  # type: ignore[arg-type]

    def test_empty_queue(self) -> None:
        """Empty queue returns empty list."""
        state = MockState()
        delivered = deliver_due_gossip(state, TurnNumber(10))  # type: ignore[arg-type]
        self.assertEqual(len(delivered), 0)


if __name__ == "__main__":
    unittest.main()
