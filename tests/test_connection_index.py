"""Tests for exit connection index."""
import unittest

from src.state_manager import GameState, Exit
from src.types import ActorId
from tests.conftest import BaseTestCase


class TestConnectionIndex(BaseTestCase):
    """Test exit connection index infrastructure."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()

    def test_connection_index_built_from_exits(self):
        """Test connection index is built from Exit entities."""
        # Add exits with connections
        exit_a = Exit(
            id="exit_a_north",
            name="north exit",
            location="loc_a",
            connections=["exit_b_south"]
        )
        exit_b = Exit(
            id="exit_b_south",
            name="south exit",
            location="loc_b",
            connections=["exit_a_north"]
        )
        self.game_state.exits = [exit_a, exit_b]

        # Build connection index
        from src.state_manager import _build_connection_index
        _build_connection_index(self.game_state)

        # Check index
        self.assertIn("exit_a_north", self.game_state._connected_to)
        self.assertIn("exit_b_south", self.game_state._connected_to)

        # Check connections
        self.assertEqual(self.game_state._connected_to["exit_a_north"], {"exit_b_south"})
        self.assertEqual(self.game_state._connected_to["exit_b_south"], {"exit_a_north"})

    def test_connection_index_handles_multiple_connections(self):
        """Test connection index handles exits with multiple connections."""
        # Exit with multiple connections (e.g., doorway connecting 3 areas)
        # Create all exits that are referenced
        exit_center = Exit(
            id="exit_center",
            name="junction",
            location="loc_center",
            connections=["exit_north", "exit_south", "exit_east"]
        )
        exit_north = Exit(
            id="exit_north",
            name="north exit",
            location="loc_north",
            connections=["exit_center"]
        )
        exit_south = Exit(
            id="exit_south",
            name="south exit",
            location="loc_south",
            connections=["exit_center"]
        )
        exit_east = Exit(
            id="exit_east",
            name="east exit",
            location="loc_east",
            connections=["exit_center"]
        )
        self.game_state.exits = [exit_center, exit_north, exit_south, exit_east]

        from src.state_manager import _build_connection_index
        _build_connection_index(self.game_state)

        # Check all connections stored
        self.assertEqual(
            self.game_state._connected_to["exit_center"],
            {"exit_north", "exit_south", "exit_east"}
        )

    def test_connection_index_handles_empty_connections(self):
        """Test connection index handles exits with no connections."""
        exit_a = Exit(
            id="exit_dead_end",
            name="dead end",
            location="loc_dead_end",
            connections=[]
        )
        self.game_state.exits = [exit_a]

        from src.state_manager import _build_connection_index
        _build_connection_index(self.game_state)

        # Should have entry with empty set
        self.assertIn("exit_dead_end", self.game_state._connected_to)
        self.assertEqual(self.game_state._connected_to["exit_dead_end"], set())

    def test_get_exit_connections(self):
        """Test querying connected exits."""
        exit_a = Exit(
            id="exit_a_north",
            name="north exit",
            location="loc_a",
            connections=["exit_b_south"]
        )
        exit_b = Exit(
            id="exit_b_south",
            name="south exit",
            location="loc_b",
            connections=["exit_a_north"]
        )
        self.game_state.exits = [exit_a, exit_b]

        from src.state_manager import _build_connection_index
        _build_connection_index(self.game_state)

        # Query connections
        connections = self.accessor.get_exit_connections("exit_a_north")

        # Should return list of Exit entities
        self.assertEqual(len(connections), 1)
        self.assertEqual(connections[0].id, "exit_b_south")
        self.assertIsInstance(connections[0], Exit)

    def test_get_exits_from_location(self):
        """Test querying all exits from a location."""
        exit_a_north = Exit(
            id="exit_a_north",
            name="north exit",
            location="loc_a",
            connections=["exit_b_south"],
            direction="north"
        )
        exit_a_east = Exit(
            id="exit_a_east",
            name="east exit",
            location="loc_a",
            connections=["exit_c_west"],
            direction="east"
        )
        # Create target exits so validation passes
        exit_b_south = Exit(
            id="exit_b_south",
            name="south exit",
            location="loc_b",
            connections=["exit_a_north"],
            direction="south"
        )
        exit_c_west = Exit(
            id="exit_c_west",
            name="west exit",
            location="loc_c",
            connections=["exit_a_east"],
            direction="west"
        )
        self.game_state.exits = [exit_a_north, exit_a_east, exit_b_south, exit_c_west]

        from src.state_manager import _build_whereabouts_index, _build_connection_index
        _build_whereabouts_index(self.game_state)
        _build_connection_index(self.game_state)

        # Query exits from location
        exits = self.accessor.get_exits_from_location("loc_a")

        # Should return both exits
        self.assertEqual(len(exits), 2)
        exit_ids = {e.id for e in exits}
        self.assertEqual(exit_ids, {"exit_a_north", "exit_a_east"})

    def test_connect_exits(self):
        """Test connecting two exits updates index."""
        exit_a = Exit(
            id="exit_a_north",
            name="north exit",
            location="loc_a",
            connections=[]
        )
        exit_b = Exit(
            id="exit_b_south",
            name="south exit",
            location="loc_b",
            connections=[]
        )
        self.game_state.exits = [exit_a, exit_b]

        from src.state_manager import _build_connection_index
        _build_connection_index(self.game_state)

        # Initially no connections
        self.assertEqual(self.game_state._connected_to["exit_a_north"], set())
        self.assertEqual(self.game_state._connected_to["exit_b_south"], set())

        # Connect exits
        self.accessor.connect_exits("exit_a_north", "exit_b_south")

        # Check index updated
        self.assertEqual(self.game_state._connected_to["exit_a_north"], {"exit_b_south"})
        self.assertEqual(self.game_state._connected_to["exit_b_south"], {"exit_a_north"})

        # Check Exit entities updated
        self.assertIn("exit_b_south", exit_a.connections)
        self.assertIn("exit_a_north", exit_b.connections)

    def test_disconnect_exits(self):
        """Test disconnecting exits updates index."""
        exit_a = Exit(
            id="exit_a_north",
            name="north exit",
            location="loc_a",
            connections=["exit_b_south"]
        )
        exit_b = Exit(
            id="exit_b_south",
            name="south exit",
            location="loc_b",
            connections=["exit_a_north"]
        )
        self.game_state.exits = [exit_a, exit_b]

        from src.state_manager import _build_connection_index
        _build_connection_index(self.game_state)

        # Initially connected
        self.assertEqual(self.game_state._connected_to["exit_a_north"], {"exit_b_south"})

        # Disconnect exits
        self.accessor.disconnect_exits("exit_a_north", "exit_b_south")

        # Check index updated
        self.assertEqual(self.game_state._connected_to["exit_a_north"], set())
        self.assertEqual(self.game_state._connected_to["exit_b_south"], set())

        # Check Exit entities updated
        self.assertNotIn("exit_b_south", exit_a.connections)
        self.assertNotIn("exit_a_north", exit_b.connections)

    def test_validation_catches_invalid_connection(self):
        """Test validation catches connections to non-existent exits."""
        exit_a = Exit(
            id="exit_a_north",
            name="north exit",
            location="loc_a",
            connections=["exit_nonexistent"]
        )
        self.game_state.exits = [exit_a]

        from src.state_manager import _build_connection_index

        with self.assertRaises(ValueError) as ctx:
            _build_connection_index(self.game_state)

        self.assertIn("exit_nonexistent", str(ctx.exception))
        self.assertIn("does not exist", str(ctx.exception))

    def test_connection_index_loaded_at_state_load(self):
        """Test connection index is built when loading state."""
        from src.state_manager import load_game_state

        # Create minimal game state with exits
        data = {
            "metadata": {"title": "Test", "version": "0.1.2"},
            "locations": [
                {"id": "loc_a", "name": "Room A", "description": "A room", "exits": {}},
                {"id": "loc_b", "name": "Room B", "description": "Another room", "exits": {}}
            ],
            "items": [],
            "locks": [],
            "actors": {
                "player": {
                    "id": "player",
                    "name": "Adventurer",
                    "description": "Test player",
                    "location": "loc_a"
                }
            },
            "exits": [
                {
                    "id": "exit_a_north",
                    "name": "north exit",
                    "location": "loc_a",
                    "connections": ["exit_b_south"],
                    "direction": "north"
                },
                {
                    "id": "exit_b_south",
                    "name": "south exit",
                    "location": "loc_b",
                    "connections": ["exit_a_north"],
                    "direction": "south"
                }
            ]
        }

        state = load_game_state(data)

        # Connection index should be built
        self.assertIn("exit_a_north", state._connected_to)
        self.assertEqual(state._connected_to["exit_a_north"], {"exit_b_south"})


if __name__ == '__main__':
    unittest.main()
