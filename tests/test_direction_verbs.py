"""Tests for direction verbs (north, south, up, down, etc.).

Tests that:
1. Bare directions parse as verbs and invoke direction handlers
2. Direction handlers move player in that direction
3. "go <direction>" still works via handle_go
4. Directions as adjectives still work ("north door")
5. Synonyms work ("n" -> north, "u" -> up)
6. Handler chain fallback works for up/down to spatial handlers
"""
from src.types import ActorId

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.state_manager import GameState, Location, Actor, Exit, Metadata
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.parser import Parser
from src.game_engine import GameEngine


def _clear_behavior_modules():
    """Clear cached behavior modules to ensure fresh loads."""
    to_delete = [k for k in list(sys.modules.keys()) if k.startswith('behaviors.')]
    for k in to_delete:
        del sys.modules[k]


class TestDirectionVerbsParsing(unittest.TestCase):
    """Test that directions parse correctly as verbs."""

    def setUp(self):
        """Set up parser with merged vocabulary."""
        # Clear cached modules to ensure fresh load
        _clear_behavior_modules()
        # Use simple_game because its behavior directory structure is clean
        # (core symlinked directly, not under lib/)
        self.engine = GameEngine(Path('examples/simple_game'))
        self.parser = self.engine.create_parser()

    def test_bare_north_parses_as_verb(self):
        """Bare 'north' should parse as verb."""
        result = self.parser.parse_command('north')
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.verb)
        self.assertEqual(result.verb.word, 'north')
        self.assertIsNone(result.direct_object)

    def test_bare_up_parses_as_verb(self):
        """Bare 'up' should parse as verb."""
        result = self.parser.parse_command('up')
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.verb)
        self.assertEqual(result.verb.word, 'up')
        self.assertIsNone(result.direct_object)

    def test_bare_down_parses_as_verb(self):
        """Bare 'down' should parse as verb."""
        result = self.parser.parse_command('down')
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.verb)
        self.assertEqual(result.verb.word, 'down')
        self.assertIsNone(result.direct_object)

    def test_synonym_n_parses_as_north(self):
        """'n' should parse as verb 'north'."""
        result = self.parser.parse_command('n')
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.verb)
        self.assertEqual(result.verb.word, 'north')

    def test_synonym_u_parses_as_up(self):
        """'u' should parse as verb 'up'."""
        result = self.parser.parse_command('u')
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.verb)
        self.assertEqual(result.verb.word, 'up')

    def test_go_north_parses_with_object(self):
        """'go north' should parse as verb 'go' with object 'north'."""
        result = self.parser.parse_command('go north')
        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, 'go')
        self.assertIsNotNone(result.direct_object)
        self.assertEqual(result.direct_object.word, 'north')

    def test_direction_as_adjective(self):
        """'open north door' should have 'north' as adjective."""
        result = self.parser.parse_command('open north door')
        self.assertIsNotNone(result)
        self.assertEqual(result.verb.word, 'open')
        self.assertIsNotNone(result.direct_adjective)
        self.assertEqual(result.direct_adjective.word, 'north')
        self.assertEqual(result.direct_object.word, 'door')


class TestDirectionHandlers(unittest.TestCase):
    """Test direction handler functionality."""

    def setUp(self):
        """Set up test game state with exits in multiple directions."""
        # Clear cached modules to ensure fresh load
        _clear_behavior_modules()
        self.game_state = GameState(
            metadata=Metadata(title="Test"),
            locations=[
                Location(id="center", name="Center Room", description="A room with exits in all directions.", exits={}),
                Location(id="north_room", name="North Room", description="", exits={}),
                Location(id="south_room", name="South Room", description="", exits={}),
                Location(id="east_room", name="East Room", description="", exits={}),
                Location(id="west_room", name="West Room", description="", exits={}),
                Location(id="upper_room", name="Upper Room", description="", exits={}),
                Location(id="lower_room", name="Lower Room", description="", exits={}),
            ],
            exits=[
                Exit(id="exit_center_north", name="north passage", location="center", direction="north", connections=["exit_north_room_south"]),
                Exit(id="exit_north_room_south", name="south passage", location="north_room", direction="south", connections=["exit_center_north"]),
                Exit(id="exit_center_south", name="south passage", location="center", direction="south", connections=["exit_south_room_north"]),
                Exit(id="exit_south_room_north", name="north passage", location="south_room", direction="north", connections=["exit_center_south"]),
                Exit(id="exit_center_east", name="east passage", location="center", direction="east", connections=["exit_east_room_west"]),
                Exit(id="exit_east_room_west", name="west passage", location="east_room", direction="west", connections=["exit_center_east"]),
                Exit(id="exit_center_west", name="west passage", location="center", direction="west", connections=["exit_west_room_east"]),
                Exit(id="exit_west_room_east", name="east passage", location="west_room", direction="east", connections=["exit_center_west"]),
                Exit(id="exit_center_up", name="stairs up", location="center", direction="up", connections=["exit_upper_room_down"]),
                Exit(id="exit_upper_room_down", name="stairs down", location="upper_room", direction="down", connections=["exit_center_up"]),
                Exit(id="exit_center_down", name="stairs down", location="center", direction="down", connections=["exit_lower_room_up"]),
                Exit(id="exit_lower_room_up", name="stairs up", location="lower_room", direction="up", connections=["exit_center_down"]),
            ],
            actors={"player": Actor(
                id="player",
                name="Player",
                description="The player",
                location="center",
                inventory=[]
            )}
        )
        # Build indices
        from src.state_manager import _build_whereabouts_index, _build_connection_index
        _build_whereabouts_index(self.game_state)
        _build_connection_index(self.game_state)

        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)
        self.accessor = StateAccessor(self.game_state, self.manager)

    def test_handle_north_moves_player(self):
        """handle_north should move player north."""
        from behaviors.core.exits import handle_north
        result = handle_north(self.accessor, {"actor_id": "player"})
        self.assertTrue(result.success)
        self.assertEqual(self.game_state.get_actor(ActorId("player")).location, "north_room")

    def test_handle_south_moves_player(self):
        """handle_south should move player south."""
        from behaviors.core.exits import handle_south
        result = handle_south(self.accessor, {"actor_id": "player"})
        self.assertTrue(result.success)
        self.assertEqual(self.game_state.get_actor(ActorId("player")).location, "south_room")

    def test_handle_up_moves_player(self):
        """handle_up should move player up."""
        from behaviors.core.exits import handle_up
        result = handle_up(self.accessor, {"actor_id": "player"})
        self.assertTrue(result.success)
        self.assertEqual(self.game_state.get_actor(ActorId("player")).location, "upper_room")

    def test_handle_down_moves_player(self):
        """handle_down should move player down."""
        from behaviors.core.exits import handle_down
        result = handle_down(self.accessor, {"actor_id": "player"})
        self.assertTrue(result.success)
        self.assertEqual(self.game_state.get_actor(ActorId("player")).location, "lower_room")

    def test_direction_no_exit_fails(self):
        """Direction handler should fail if no exit in that direction."""
        # Move to north_room which has no exits
        self.accessor.set_entity_where("player", "north_room")
        from behaviors.core.exits import handle_north
        result = handle_north(self.accessor, {"actor_id": "player"})
        self.assertFalse(result.success)
        self.assertIn("can't go north", result.primary.lower())


class TestDirectionHandlerChain(unittest.TestCase):
    """Test that handler chain works for up/down fallback to spatial."""

    def setUp(self):
        """Set up game state without up/down exits but with climbable item."""
        # Clear cached modules to ensure fresh load
        _clear_behavior_modules()
        self.game_state = GameState(
            metadata=Metadata(title="Test"),
            locations=[
                Location(
                    id="room",
                    name="Room",
                    description="A room.",
                    exits={}  # No exits
                ),
            ],
            actors={"player": Actor(
                id="player",
                name="Player",
                description="The player",
                location="room",
                inventory=[],
                _properties={"posture": "climbing", "focused_on": "tree"}
            )}
        )

        self.manager = BehaviorManager()
        behaviors_dir = Path(__file__).parent.parent / "behaviors"
        modules = self.manager.discover_modules(str(behaviors_dir))
        self.manager.load_modules(modules)
        self.accessor = StateAccessor(self.game_state, self.manager)

    def test_down_with_posture_uses_spatial_handler(self):
        """'down' when climbing should use spatial handler to descend."""
        # This tests the handler chain: exits.handle_down fails (no exit),
        # then spatial.handle_down succeeds (has posture to clear)
        result = self.manager.invoke_handler("down", self.accessor, {"actor_id": "player"})
        self.assertTrue(result.success)
        # Posture should be cleared
        self.assertNotIn("posture", self.game_state.get_actor(ActorId("player")).properties)

    def test_up_with_posture_uses_spatial_handler(self):
        """'up' when climbing should use spatial handler to descend."""
        result = self.manager.invoke_handler("up", self.accessor, {"actor_id": "player"})
        self.assertTrue(result.success)
        self.assertNotIn("posture", self.game_state.get_actor(ActorId("player")).properties)


class TestDirectionVerbsEndToEnd(unittest.TestCase):
    """End-to-end tests using the game engine."""

    def setUp(self):
        """Set up game engine with simple_game."""
        # Clear cached modules to ensure fresh load
        _clear_behavior_modules()
        # Use simple_game because its behavior directory structure is clean
        self.engine = GameEngine(Path('examples/simple_game'))
        from src.state_accessor import StateAccessor
        self.accessor = StateAccessor(self.engine.game_state, self.engine.behavior_manager)
        # Move player to starting location
        self.accessor.set_entity_where('player', 'loc_start')

    def test_bare_north_moves_player(self):
        """Typing 'north' should move player north from loc_start."""
        # Start at loc_start which has north exit
        self.accessor.set_entity_where('player', 'loc_start')
        response = self.engine.json_handler.handle_message({
            "type": "command",
            "action": {"verb": "north"}
        })
        self.assertTrue(response.get("success"))
        self.assertEqual(self.engine.game_state.get_actor(ActorId("player")).location, "loc_hallway")

    def test_bare_up_moves_player(self):
        """Typing 'up' should move player up from loc_hallway."""
        # Start at loc_hallway which has up exit
        self.accessor.set_entity_where('player', 'loc_hallway')
        response = self.engine.json_handler.handle_message({
            "type": "command",
            "action": {"verb": "up"}
        })
        self.assertTrue(response.get("success"))
        self.assertEqual(self.engine.game_state.get_actor(ActorId("player")).location, "loc_tower")

    def test_go_north_still_works(self):
        """'go north' should still work."""
        from src.word_entry import WordEntry, WordType
        self.accessor.set_entity_where('player', 'loc_start')
        response = self.engine.json_handler.handle_message({
            "type": "command",
            "action": {
                "verb": "go",
                "object": WordEntry("north", {WordType.NOUN, WordType.VERB, WordType.ADJECTIVE}, ["n"])
            }
        })
        self.assertTrue(response.get("success"))
        self.assertEqual(self.engine.game_state.get_actor(ActorId("player")).location, "loc_hallway")


if __name__ == '__main__':
    unittest.main()
