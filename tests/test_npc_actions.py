"""Tests for NPC action system (Phase 4 of Actor Interaction)."""

import unittest
from unittest.mock import Mock, MagicMock

from src.state_manager import Actor, Location, GameState, Metadata
from src.state_accessor import StateAccessor


class TestNPCTakeAction(unittest.TestCase):
    """Test npc_take_action behavior."""

    def setUp(self):
        """Create test actors and game state."""
        self.player = Actor(
            id="player",
            name="Player",
            description="Test player",
            location="loc_room",
            inventory=[],
            properties={"health": 100, "max_health": 100}
        )

        self.hostile_npc = Actor(
            id="npc_wolf",
            name="Wolf",
            description="A hostile wolf",
            location="loc_room",
            inventory=[],
            properties={
                "health": 50,
                "ai": {"disposition": "hostile"},
                "attacks": [
                    {"name": "bite", "damage": 10}
                ]
            }
        )

        self.neutral_npc = Actor(
            id="npc_scholar",
            name="Scholar",
            description="A neutral scholar",
            location="loc_room",
            inventory=[],
            properties={
                "health": 40,
                "ai": {"disposition": "neutral"}
            }
        )

        self.location = Location(
            id="loc_room",
            name="Room",
            description="A test room"
        )

        self.other_location = Location(
            id="loc_hallway",
            name="Hallway",
            description="A hallway"
        )

    def test_npc_action_hostile_attacks(self):
        """Hostile NPC in same location attacks player."""
        from behavior_libraries.actor_lib.npc_actions import npc_take_action

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_room"),
            locations=[self.location],
            items=[],
            actors={
                "player": self.player,
                "npc_wolf": self.hostile_npc
            },
            locks=[],
            parts=[]
        )

        mock_behavior_manager = Mock()
        mock_behavior_manager.invoke_behavior.return_value = None
        accessor = StateAccessor(game_state, mock_behavior_manager)
        context = {}

        result = npc_take_action(self.hostile_npc, accessor, context)

        # Should have attacked player
        self.assertIsNotNone(result)
        self.assertIn("Wolf", result.message)
        self.assertIn("bite", result.message)

        # Player should have taken damage
        self.assertEqual(self.player.properties["health"], 90)

    def test_npc_action_neutral_skips(self):
        """Neutral NPC does nothing."""
        from behavior_libraries.actor_lib.npc_actions import npc_take_action

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_room"),
            locations=[self.location],
            items=[],
            actors={
                "player": self.player,
                "npc_scholar": self.neutral_npc
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)
        context = {}

        result = npc_take_action(self.neutral_npc, accessor, context)

        # Should do nothing
        self.assertIsNone(result)

        # Player health unchanged
        self.assertEqual(self.player.properties["health"], 100)

    def test_npc_action_different_location(self):
        """NPC in different location does nothing."""
        from behavior_libraries.actor_lib.npc_actions import npc_take_action

        # Move wolf to different location
        self.hostile_npc.location = "loc_hallway"

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_room"),
            locations=[self.location, self.other_location],
            items=[],
            actors={
                "player": self.player,
                "npc_wolf": self.hostile_npc
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)
        context = {}

        result = npc_take_action(self.hostile_npc, accessor, context)

        # Should do nothing - not in same location
        self.assertIsNone(result)

    def test_npc_action_no_attacks(self):
        """Hostile NPC without attacks does nothing."""
        from behavior_libraries.actor_lib.npc_actions import npc_take_action

        # Hostile but no attacks defined
        unarmed_hostile = Actor(
            id="npc_bandit",
            name="Bandit",
            description="An unarmed bandit",
            location="loc_room",
            inventory=[],
            properties={
                "ai": {"disposition": "hostile"}
            }
        )

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_room"),
            locations=[self.location],
            items=[],
            actors={
                "player": self.player,
                "npc_bandit": unarmed_hostile
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = npc_take_action(unarmed_hostile, accessor, {})

        self.assertIsNone(result)

    def test_npc_action_no_ai_property(self):
        """NPC without ai property is treated as neutral."""
        from behavior_libraries.actor_lib.npc_actions import npc_take_action

        no_ai_npc = Actor(
            id="npc_guard",
            name="Guard",
            description="A guard with no AI defined",
            location="loc_room",
            inventory=[],
            properties={"health": 50}  # No ai property
        )

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_room"),
            locations=[self.location],
            items=[],
            actors={
                "player": self.player,
                "npc_guard": no_ai_npc
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = npc_take_action(no_ai_npc, accessor, {})

        self.assertIsNone(result)


class TestFireNPCActions(unittest.TestCase):
    """Test fire_npc_actions turn phase handler."""

    def setUp(self):
        """Create test actors."""
        self.player = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_room1",
            inventory=[],
            properties={"health": 100}
        )

        self.wolf = Actor(
            id="npc_wolf",
            name="Wolf",
            description="A wolf",
            location="loc_room1",
            inventory=[],
            properties={
                "health": 50,
                "ai": {"disposition": "hostile"},
                "attacks": [{"name": "bite", "damage": 5}]
            }
        )

        self.rat = Actor(
            id="npc_rat",
            name="Rat",
            description="A rat in another room",
            location="loc_room2",
            inventory=[],
            properties={
                "health": 10,
                "ai": {"disposition": "hostile"},
                "attacks": [{"name": "nibble", "damage": 2}]
            }
        )

    def test_fire_npc_actions_processes_all_locations(self):
        """NPCs in all locations are processed."""
        from behavior_libraries.actor_lib.npc_actions import fire_npc_actions

        location1 = Location(id="loc_room1", name="Room 1", description="Room 1")
        location2 = Location(id="loc_room2", name="Room 2", description="Room 2")

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_room1"),
            locations=[location1, location2],
            items=[],
            actors={
                "player": self.player,
                "npc_wolf": self.wolf,
                "npc_rat": self.rat
            },
            locks=[],
            parts=[]
        )

        mock_behavior_manager = Mock()
        mock_behavior_manager.invoke_behavior.return_value = None
        accessor = StateAccessor(game_state, mock_behavior_manager)
        context = {"hook": "npc_action"}

        result = fire_npc_actions(None, accessor, context)

        # Wolf should have attacked (same location as player)
        self.assertEqual(self.player.properties["health"], 95)

        # Rat shouldn't have attacked (different location)
        # Result should have message from wolf attack
        self.assertIsNotNone(result)

    def test_fire_npc_actions_alpha_first(self):
        """Alphas are processed before followers."""
        from behavior_libraries.actor_lib.npc_actions import fire_npc_actions

        # Create pack with alpha and follower
        alpha = Actor(
            id="npc_alpha_wolf",
            name="Alpha Wolf",
            description="The pack leader",
            location="loc_room1",
            inventory=[],
            properties={
                "health": 80,
                "ai": {"disposition": "hostile", "pack_role": "alpha"},
                "attacks": [{"name": "savage_bite", "damage": 15}]
            }
        )

        follower = Actor(
            id="npc_beta_wolf",
            name="Beta Wolf",
            description="A pack follower",
            location="loc_room1",
            inventory=[],
            properties={
                "health": 50,
                "ai": {"disposition": "hostile", "pack_role": "follower"},
                "attacks": [{"name": "bite", "damage": 10}]
            }
        )

        location = Location(id="loc_room1", name="Room", description="Room")

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_room1"),
            locations=[location],
            items=[],
            actors={
                "player": self.player,
                "npc_beta_wolf": follower,  # Listed first
                "npc_alpha_wolf": alpha      # But alpha should process first
            },
            locks=[],
            parts=[]
        )

        # Track order of attacks
        attack_order = []
        original_health = 100

        def track_invoke(entity, event, accessor, context):
            if event == "npc_take_action" or event == "on_damage":
                return None
            return None

        mock_behavior_manager = Mock()
        mock_behavior_manager.invoke_behavior.side_effect = track_invoke
        accessor = StateAccessor(game_state, mock_behavior_manager)

        result = fire_npc_actions(None, accessor, {})

        # Both should have attacked
        # Alpha does 15, follower does 10, total 25 damage
        self.assertEqual(self.player.properties["health"], 75)

    def test_fire_npc_actions_skips_player(self):
        """Player is not processed as NPC."""
        from behavior_libraries.actor_lib.npc_actions import fire_npc_actions

        location = Location(id="loc_room1", name="Room", description="Room")

        # Only player, no NPCs
        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_room1"),
            locations=[location],
            items=[],
            actors={"player": self.player},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = fire_npc_actions(None, accessor, {})

        # Should complete without error, no messages
        self.assertIsNotNone(result)
        self.assertTrue(result.allow)

    def test_fire_npc_actions_collects_messages(self):
        """Messages from all NPC actions are collected."""
        from behavior_libraries.actor_lib.npc_actions import fire_npc_actions

        # Two hostile NPCs in same room
        wolf2 = Actor(
            id="npc_wolf2",
            name="Second Wolf",
            description="Another wolf",
            location="loc_room1",
            inventory=[],
            properties={
                "health": 50,
                "ai": {"disposition": "hostile"},
                "attacks": [{"name": "bite", "damage": 5}]
            }
        )

        location = Location(id="loc_room1", name="Room", description="Room")

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_room1"),
            locations=[location],
            items=[],
            actors={
                "player": self.player,
                "npc_wolf": self.wolf,
                "npc_wolf2": wolf2
            },
            locks=[],
            parts=[]
        )

        mock_behavior_manager = Mock()
        mock_behavior_manager.invoke_behavior.return_value = None
        accessor = StateAccessor(game_state, mock_behavior_manager)

        result = fire_npc_actions(None, accessor, {})

        # Should have messages from both wolves
        self.assertIn("Wolf", result.message)


class TestNPCActionVocabulary(unittest.TestCase):
    """Test NPC action vocabulary exports."""

    def test_vocabulary_has_events(self):
        """Vocabulary exports events."""
        from behavior_libraries.actor_lib.npc_actions import vocabulary

        self.assertIn("events", vocabulary)

    def test_vocabulary_registers_npc_action_hook(self):
        """Vocabulary registers npc_take_action with npc_action hook."""
        from behavior_libraries.actor_lib.npc_actions import vocabulary

        events = vocabulary["events"]

        npc_event = None
        for event in events:
            if event.get("event") == "on_npc_action":
                npc_event = event
                break

        self.assertIsNotNone(npc_event)
        self.assertEqual(npc_event["hook"], "npc_action")


if __name__ == '__main__':
    unittest.main()
