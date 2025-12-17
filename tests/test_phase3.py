"""
Phase 3 tests - Unified Actor Model

These tests verify the refactoring from separate player/npcs to unified actors dict.
Following TDD: Write tests first, then implement to make them pass.

Tests cover:
- Unified actor storage (actors dict contains both player and NPCs)
- StateAccessor.get_actor() works for all actors
- StateAccessor.get_actors_in_location() includes player
- Behaviors field is List[str] not Dict[str, str]
- Serialization works with unified model
"""
from src.types import ActorId
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.conftest import create_test_state
from src.state_accessor import StateAccessor
from src.state_manager import GameState, Actor, Item, Location


class TestUnifiedActorModel(unittest.TestCase):
    """Test unified actor storage in GameState."""

    def test_game_state_has_actors_dict(self):
        """Test that GameState has actors dict (primary field)."""
        state = create_test_state()

        # Should have actors dict as primary field
        self.assertTrue(hasattr(state, 'actors'))
        self.assertIsInstance(state.actors, dict)

        # player and npcs exist as backward compatibility properties
        # but actors is the primary storage
        self.assertGreater(len(state.actors), 0)

    def test_player_in_actors_dict(self):
        """Test that player is stored in actors dict with key 'player'."""
        state = create_test_state()

        self.assertIn('player', state.actors)
        player = state.actors[ActorId('player')]
        self.assertIsInstance(player, Actor)
        self.assertEqual(player.location, "location_room")

    def test_npcs_in_actors_dict(self):
        """Test that NPCs are stored in actors dict with their IDs as keys."""
        state = create_test_state()

        # Add an NPC through the unified model
        npc = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=[],
            properties={},
            behaviors=[]
        )
        state.actors[ActorId("npc_guard")] = npc

        self.assertIn("npc_guard", state.actors)
        self.assertEqual(state.actors[ActorId("npc_guard")].id, "npc_guard")


class TestStateAccessorUnifiedModel(unittest.TestCase):
    """Test StateAccessor with unified actor model."""

    def test_get_actor_player(self):
        """Test getting player actor through unified model."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        player = accessor.get_actor(ActorId("player"))
        self.assertIsNotNone(player)
        self.assertEqual(player.location, "location_room")

    def test_get_actor_npc(self):
        """Test getting NPC actor through unified model."""
        state = create_test_state()

        # Add NPC to actors dict
        npc = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_hall",
            inventory=[],
            properties={},
            behaviors=[]
        )
        state.actors[ActorId("npc_guard")] = npc

        accessor = StateAccessor(state, None)
        retrieved = accessor.get_actor(ActorId("npc_guard"))
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "npc_guard")

    def test_get_actor_not_found(self):
        """Test that get_actor returns None for non-existent actor."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        actor = accessor.get_actor(ActorId("nonexistent"))
        self.assertIsNone(actor)

    def test_get_actors_in_location_includes_player(self):
        """Test that get_actors_in_location includes player when in location."""
        state = create_test_state()
        accessor = StateAccessor(state, None)

        actors = accessor.get_actors_in_location("location_room")
        actor_ids = [actor.id for actor in actors]

        self.assertIn("player", actor_ids)

    def test_get_actors_in_location_includes_npcs(self):
        """Test that get_actors_in_location includes NPCs in location."""
        state = create_test_state()

        # Add NPC in same location as player
        npc = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=[],
            properties={},
            behaviors=[]
        )
        state.actors[ActorId("npc_guard")] = npc

        accessor = StateAccessor(state, None)
        actors = accessor.get_actors_in_location("location_room")
        actor_ids = [actor.id for actor in actors]

        self.assertIn("player", actor_ids)
        self.assertIn("npc_guard", actor_ids)

    def test_get_actors_in_location_excludes_other_locations(self):
        """Test that get_actors_in_location excludes actors in other locations."""
        state = create_test_state()

        # Add NPC in different location
        npc = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_hall",
            inventory=[],
            properties={},
            behaviors=[]
        )
        state.actors[ActorId("npc_guard")] = npc

        accessor = StateAccessor(state, None)
        actors = accessor.get_actors_in_location("location_room")
        actor_ids = [actor.id for actor in actors]

        self.assertIn("player", actor_ids)
        self.assertNotIn("npc_guard", actor_ids)


class TestBehaviorsFieldList(unittest.TestCase):
    """Test that behaviors field is List[str] not Dict[str, str]."""

    def test_actor_behaviors_is_list(self):
        """Test that Actor.behaviors is a list."""
        actor = Actor(
            id="test_actor",
            name="Test",
            description="A test actor",
            location="location_room",
            inventory=[],
            properties={},
            behaviors=["module1", "module2"]
        )

        self.assertIsInstance(actor.behaviors, list)
        self.assertEqual(len(actor.behaviors), 2)
        self.assertIn("module1", actor.behaviors)

    def test_item_behaviors_is_list(self):
        """Test that Item.behaviors is a list."""
        item = Item(
            id="test_item",
            name="Test Item",
            description="A test item",
            location="location_room",
            properties={"portable": True},
            behaviors=["module1"]
        )

        self.assertIsInstance(item.behaviors, list)
        self.assertEqual(len(item.behaviors), 1)

    def test_location_behaviors_is_list(self):
        """Test that Location.behaviors is a list."""
        location = Location(
            id="test_location",
            name="Test Location",
            description="A test location",
            properties={},
            behaviors=["module1"]
        )

        self.assertIsInstance(location.behaviors, list)
        self.assertEqual(len(location.behaviors), 1)


class TestSerializationUnifiedModel(unittest.TestCase):
    """Test serialization/deserialization with unified actor model."""

    def test_save_load_round_trip(self):
        """Test that save and load round-trip works with unified model."""
        from src.state_manager import save_game_state, load_game_state
        import tempfile
        import os

        # Create state with unified model
        state = create_test_state()

        # Add an NPC
        npc = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=[],
            properties={},
            behaviors=[]
        )
        state.actors[ActorId("npc_guard")] = npc

        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            # Save the state
            save_game_state(state, temp_path)

            # Load back
            loaded_state = load_game_state(temp_path)

            # Verify actors dict structure
            self.assertIn('player', loaded_state.actors)
            self.assertIn('npc_guard', loaded_state.actors)

            # Verify player data
            self.assertEqual(loaded_state.actors[ActorId('player')].location, "location_room")

            # Verify NPC data
            self.assertEqual(loaded_state.actors[ActorId('npc_guard')].id, "npc_guard")

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
