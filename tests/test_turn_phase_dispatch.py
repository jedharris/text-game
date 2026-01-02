"""Tests for virtual entity per-entity turn phase dispatch.

Validates that turn phases correctly dispatch to individual entity handlers
and that each handler receives the correct entity instance.
"""

import unittest
from typing import Any
from pathlib import Path
from src.state_manager import (
    GameState,
    Commitment,
    ScheduledEvent,
    Gossip,
    Spread,
    Location,
)
from src.types import CommitmentId, ScheduledEventId, GossipId, SpreadId, LocationId
from src.behavior_manager import EventResult, BehaviorManager
from src.state_accessor import StateAccessor


class TestCommitmentTurnPhase(unittest.TestCase):
    """Test commitment turn phase per-entity dispatch."""

    def setUp(self):
        """Create minimal game state with commitment."""
        self.game_state = GameState(
            metadata={"title": "Test", "version": "0.1.2"},
            locations=[
                {
                    "id": "loc_start",
                    "name": "Start",
                    "description": "Start location",
                }
            ],
            items=[],
            locks=[],
            actors={
                "player": {
                    "id": "player",
                    "name": "Player",
                    "description": "Test player",
                    "location": "loc_start",
                    "inventory": [],
                }
            },
            extra={},
            commitments=[
                Commitment(
                    id=CommitmentId("commit_active"),
                    name="Active promise",
                    description="Active commitment with deadline",
                    _properties={
                        "state": "active",
                        "made_at_turn": 5,
                        "deadline_turn": 15,
                        "config_id": "commit_test",
                    },
                    behaviors=["behaviors.shared.infrastructure.commitments"],
                ),
                Commitment(
                    id=CommitmentId("commit_fulfilled"),
                    name="Fulfilled promise",
                    description="Already fulfilled commitment",
                    _properties={
                        "state": "fulfilled",
                        "made_at_turn": 5,
                        "config_id": "commit_done",
                    },
                    behaviors=["behaviors.shared.infrastructure.commitments"],
                ),
            ],
        )

        # Set up behavior manager
        self.behavior_manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "examples" / "big_game" / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

    def test_commitment_not_expired(self):
        """Commitment before deadline should return None feedback."""
        from examples.big_game.behaviors.shared.infrastructure.commitments import (
            on_turn_commitments,
        )

        commitment = self.game_state.commitments[0]
        accessor = StateAccessor(self.game_state, self.behavior_manager)
        context = {"current_turn": 10, "hook": "turn_commitment"}

        result = on_turn_commitments(commitment, accessor, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)
        # State should remain active
        self.assertEqual(commitment.properties["state"], "active")

    def test_commitment_expired(self):
        """Commitment past deadline should transition to ABANDONED."""
        from examples.big_game.behaviors.shared.infrastructure.commitments import (
            on_turn_commitments,
        )

        commitment = self.game_state.commitments[0]
        accessor = StateAccessor(self.game_state, self.behavior_manager)
        context = {"current_turn": 20, "hook": "turn_commitment"}

        result = on_turn_commitments(commitment, accessor, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)
        self.assertIn("expired", result.feedback.lower())
        # State should be abandoned
        self.assertEqual(commitment.properties["state"], "abandoned")

    def test_commitment_already_fulfilled(self):
        """Fulfilled commitment should not process expiration."""
        from examples.big_game.behaviors.shared.infrastructure.commitments import (
            on_turn_commitments,
        )

        commitment = self.game_state.commitments[1]
        accessor = StateAccessor(self.game_state, self.behavior_manager)
        context = {"current_turn": 100, "hook": "turn_commitment"}

        result = on_turn_commitments(commitment, accessor, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)
        # State should remain fulfilled
        self.assertEqual(commitment.properties["state"], "fulfilled")


class TestScheduledEventTurnPhase(unittest.TestCase):
    """Test scheduled event turn phase per-entity dispatch."""

    def setUp(self):
        """Create minimal game state with scheduled events."""
        self.game_state = GameState(
            metadata={"title": "Test", "version": "0.1.2"},
            locations=[
                {
                    "id": "loc_start",
                    "name": "Start",
                    "description": "Start location",
                }
            ],
            items=[],
            locks=[],
            actors={
                "player": {
                    "id": "player",
                    "name": "Player",
                    "description": "Test player",
                    "location": "loc_start",
                    "inventory": [],
                }
            },
            extra={},
            scheduled_events=[
                ScheduledEvent(
                    id=ScheduledEventId("evt_one_time"),
                    name="One-time event at turn 10",
                    description="Non-repeating event",
                    _properties={
                        "trigger_turn": 10,
                        "event_type": "test_event",
                        "data": {"message": "Test"},
                        "repeating": False,
                    },
                    behaviors=["behaviors.shared.infrastructure.scheduled_events"],
                ),
                ScheduledEvent(
                    id=ScheduledEventId("evt_repeating"),
                    name="Repeating event",
                    description="Repeats every 5 turns",
                    _properties={
                        "trigger_turn": 15,
                        "event_type": "periodic_tick",
                        "repeating": True,
                        "interval": 5,
                    },
                    behaviors=["behaviors.shared.infrastructure.scheduled_events"],
                ),
            ],
        )

        # Set up behavior manager
        self.behavior_manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "examples" / "big_game" / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

    def test_event_not_triggered(self):
        """Event before trigger turn should return None feedback."""
        from examples.big_game.behaviors.shared.infrastructure.scheduled_events import (
            on_turn_scheduled_events,
        )

        event = self.game_state.scheduled_events[0]
        accessor = StateAccessor(self.game_state, self.behavior_manager)
        context = {"current_turn": 5, "hook": "turn_scheduled_events"}

        result = on_turn_scheduled_events(event, accessor, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_one_time_event_triggered(self):
        """One-time event at trigger turn should fire."""
        from examples.big_game.behaviors.shared.infrastructure.scheduled_events import (
            on_turn_scheduled_events,
        )

        event = self.game_state.scheduled_events[0]
        accessor = StateAccessor(self.game_state, self.behavior_manager)
        context = {"current_turn": 10, "hook": "turn_scheduled_events"}

        result = on_turn_scheduled_events(event, accessor, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)
        self.assertIn("Event fired", result.feedback)

    def test_repeating_event_updates_trigger(self):
        """Repeating event should update trigger_turn after firing."""
        from examples.big_game.behaviors.shared.infrastructure.scheduled_events import (
            on_turn_scheduled_events,
        )

        event = self.game_state.scheduled_events[1]
        accessor = StateAccessor(self.game_state, self.behavior_manager)
        context = {"current_turn": 15, "hook": "turn_scheduled_events"}

        result = on_turn_scheduled_events(event, accessor, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)
        # Trigger should be updated to turn 20
        self.assertEqual(event.properties["trigger_turn"], 20)


class TestGossipTurnPhase(unittest.TestCase):
    """Test gossip turn phase per-entity dispatch."""

    def setUp(self):
        """Create minimal game state with gossip."""
        self.game_state = GameState(
            metadata={"title": "Test", "version": "0.1.2"},
            locations=[
                {
                    "id": "loc_start",
                    "name": "Start",
                    "description": "Start location",
                }
            ],
            items=[],
            locks=[],
            actors={
                "player": {
                    "id": "player",
                    "name": "Player",
                    "description": "Test player",
                    "location": "loc_start",
                    "inventory": [],
                }
            },
            extra={},
            gossip=[
                Gossip(
                    id=GossipId("gossip_pending"),
                    name="News arriving later",
                    description="Point-to-point gossip",
                    _properties={
                        "content": "Important news",
                        "source_npc": "npc_guard",
                        "target_npcs": ["npc_healer"],
                        "created_turn": 5,
                        "arrives_turn": 17,
                        "gossip_type": "POINT_TO_POINT",
                    },
                    behaviors=["behaviors.shared.infrastructure.gossip"],
                ),
            ],
        )

        # Set up behavior manager
        self.behavior_manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "examples" / "big_game" / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

    def test_gossip_not_arrived(self):
        """Gossip before arrival should return None feedback."""
        from examples.big_game.behaviors.shared.infrastructure.gossip import (
            on_turn_gossip_spread,
        )

        gossip = self.game_state.gossip[0]
        accessor = StateAccessor(self.game_state, self.behavior_manager)
        context = {"current_turn": 10, "hook": "turn_gossip_spread"}

        result = on_turn_gossip_spread(gossip, accessor, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_gossip_arrived(self):
        """Gossip at arrival turn should process delivery."""
        from examples.big_game.behaviors.shared.infrastructure.gossip import (
            on_turn_gossip_spread,
        )

        gossip = self.game_state.gossip[0]
        accessor = StateAccessor(self.game_state, self.behavior_manager)
        context = {"current_turn": 17, "hook": "turn_gossip_spread"}

        result = on_turn_gossip_spread(gossip, accessor, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        # Current implementation returns None for gossip delivery
        # (effects are indirect)


class TestSpreadTurnPhase(unittest.TestCase):
    """Test environmental spread turn phase per-entity dispatch."""

    def setUp(self):
        """Create minimal game state with spread."""
        self.game_state = GameState(
            metadata={"title": "Test", "version": "0.1.2"},
            locations=[
                Location(
                    id=LocationId("loc_cave_1"),
                    name="Cave Entrance",
                    description="A cold cave",
                    exits={},
                    items=[],
                    _properties={"region": "caves", "temperature": "COLD"},
                ),
                Location(
                    id=LocationId("loc_cave_2"),
                    name="Cave Depths",
                    description="Deeper in the cave",
                    exits={},
                    items=[],
                    _properties={"region": "caves", "temperature": "COLD"},
                ),
            ],
            items=[],
            locks=[],
            actors={
                "player": {
                    "id": "player",
                    "name": "Player",
                    "description": "Test player",
                    "location": "loc_cave_1",
                    "inventory": [],
                }
            },
            extra={},
            spreads=[
                Spread(
                    id=SpreadId("cave_cold"),
                    name="Cave cold spread",
                    description="Cold spreading through caves",
                    _properties={
                        "active": True,
                        "milestones": [
                            {
                                "turn": 25,
                                "effects": [
                                    {
                                        "locations": ["loc_cave_*"],
                                        "property_name": "temperature",
                                        "property_value": "FREEZING",
                                    }
                                ],
                            },
                        ],
                        "reached_milestones": [],
                    },
                    behaviors=["behaviors.shared.infrastructure.spreads"],
                ),
            ],
        )

        # Set up behavior manager
        self.behavior_manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "examples" / "big_game" / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

    def test_spread_before_milestone(self):
        """Spread before milestone should return None feedback."""
        from examples.big_game.behaviors.shared.infrastructure.spreads import (
            on_turn_condition_spread,
        )

        spread = self.game_state.spreads[0]
        accessor = StateAccessor(self.game_state, self.behavior_manager)
        context = {"current_turn": 10, "hook": "turn_condition_spread"}

        result = on_turn_condition_spread(spread, accessor, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)

    def test_spread_at_milestone(self):
        """Spread at milestone should apply effects and return feedback."""
        from examples.big_game.behaviors.shared.infrastructure.spreads import (
            on_turn_condition_spread,
        )

        spread = self.game_state.spreads[0]
        accessor = StateAccessor(self.game_state, self.behavior_manager)
        context = {"current_turn": 25, "hook": "turn_condition_spread"}

        result = on_turn_condition_spread(spread, accessor, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNotNone(result.feedback)
        self.assertIn("Environmental change", result.feedback)
        # Milestone should be marked as reached
        self.assertIn(25, spread.properties["reached_milestones"])
        # Locations should have updated temperature
        for loc in self.game_state.locations:
            if loc.id.startswith("loc_cave"):
                self.assertEqual(loc.properties.get("temperature"), "FREEZING")

    def test_spread_milestone_not_repeated(self):
        """Already-reached milestone should not fire again."""
        from examples.big_game.behaviors.shared.infrastructure.spreads import (
            on_turn_condition_spread,
        )

        spread = self.game_state.spreads[0]
        spread.properties["reached_milestones"] = [25]
        accessor = StateAccessor(self.game_state, self.behavior_manager)
        context = {"current_turn": 30, "hook": "turn_condition_spread"}

        result = on_turn_condition_spread(spread, accessor, context)

        self.assertIsInstance(result, EventResult)
        self.assertTrue(result.allow)
        self.assertIsNone(result.feedback)


if __name__ == "__main__":
    unittest.main()
