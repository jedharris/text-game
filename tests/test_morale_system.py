"""Tests for morale and fleeing system (Phase 8 of Actor Interaction)."""

import unittest
from unittest.mock import Mock

from src.state_manager import Actor, Location, GameState, Metadata
from src.state_accessor import StateAccessor


class TestGetMorale(unittest.TestCase):
    """Test get_morale function."""

    def setUp(self):
        """Create test actors and location."""
        self.npc = Actor(
            id="npc_goblin",
            name="Goblin",
            description="A goblin",
            location="loc_cave",
            inventory=[],
            properties={
                "health": 50,
                "max_health": 100,
                "base_morale": 100,
                "disposition": "hostile"
            }
        )

        self.player = Actor(
            id="player",
            name="Player",
            description="The player",
            location="loc_cave",
            inventory=[],
            properties={"disposition": "hostile"}
        )

        self.ally = Actor(
            id="npc_goblin2",
            name="Goblin Scout",
            description="Another goblin",
            location="loc_cave",
            inventory=[],
            properties={
                "pack_id": "goblin_pack",
                "disposition": "hostile"
            }
        )

        self.location = Location(
            id="loc_cave",
            name="Cave",
            description="A dark cave"
        )

    def test_morale_full_health(self):
        """Full health gives full health morale component."""
        from behavior_libraries.actor_lib.morale import get_morale

        self.npc.properties["health"] = 100

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.location],
            items=[],
            actors={"npc_goblin": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        morale = get_morale(accessor, self.npc)

        # Full health = base_morale (100)
        self.assertEqual(morale, 100)

    def test_morale_reduced_by_health(self):
        """Low health reduces morale proportionally."""
        from behavior_libraries.actor_lib.morale import get_morale

        self.npc.properties["health"] = 50  # 50% health

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.location],
            items=[],
            actors={"npc_goblin": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        morale = get_morale(accessor, self.npc)

        # 50% health = 50% of base_morale
        self.assertEqual(morale, 50)

    def test_morale_boosted_by_allies(self):
        """Allies in location boost morale."""
        from behavior_libraries.actor_lib.morale import get_morale

        self.npc.properties["pack_id"] = "goblin_pack"
        self.npc.properties["health"] = 100

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.location],
            items=[],
            actors={
                "npc_goblin": self.npc,
                "npc_goblin2": self.ally
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        morale = get_morale(accessor, self.npc)

        # Base 100 + ally bonus (10 per ally)
        self.assertEqual(morale, 110)

    def test_morale_reduced_by_enemies(self):
        """Enemies in location reduce morale."""
        from behavior_libraries.actor_lib.morale import get_morale

        self.npc.properties["health"] = 100

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.location],
            items=[],
            actors={
                "npc_goblin": self.npc,
                "player": self.player
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        morale = get_morale(accessor, self.npc)

        # Base 100 - enemy penalty (15 per enemy)
        self.assertEqual(morale, 85)

    def test_morale_alpha_presence_bonus(self):
        """Pack alpha presence boosts morale."""
        from behavior_libraries.actor_lib.morale import get_morale

        self.npc.properties["pack_id"] = "goblin_pack"
        self.npc.properties["pack_role"] = "follower"
        self.npc.properties["health"] = 100

        alpha = Actor(
            id="npc_goblin_chief",
            name="Goblin Chief",
            description="Pack leader",
            location="loc_cave",
            inventory=[],
            properties={
                "pack_id": "goblin_pack",
                "pack_role": "alpha"
            }
        )

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.location],
            items=[],
            actors={
                "npc_goblin": self.npc,
                "npc_goblin_chief": alpha
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        morale = get_morale(accessor, self.npc)

        # Base 100 + ally bonus (10) + alpha bonus (20)
        self.assertEqual(morale, 130)

    def test_morale_default_base(self):
        """Uses default base_morale if not specified."""
        from behavior_libraries.actor_lib.morale import get_morale, DEFAULT_BASE_MORALE

        del self.npc.properties["base_morale"]
        self.npc.properties["health"] = 100

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.location],
            items=[],
            actors={"npc_goblin": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        morale = get_morale(accessor, self.npc)

        self.assertEqual(morale, DEFAULT_BASE_MORALE)

    def test_morale_clamped_minimum(self):
        """Morale doesn't go below 0."""
        from behavior_libraries.actor_lib.morale import get_morale

        self.npc.properties["health"] = 10  # Very low health
        self.npc.properties["base_morale"] = 20

        # Add many enemies
        enemies = {}
        for i in range(10):
            enemies[f"enemy_{i}"] = Actor(
                id=f"enemy_{i}",
                name=f"Enemy {i}",
                description="An enemy",
                location="loc_cave",
                inventory=[],
                properties={"disposition": "hostile"}
            )

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.location],
            items=[],
            actors={"npc_goblin": self.npc, **enemies},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        morale = get_morale(accessor, self.npc)

        self.assertGreaterEqual(morale, 0)


class TestCheckFleeCondition(unittest.TestCase):
    """Test check_flee_condition function."""

    def setUp(self):
        """Create test NPC."""
        self.npc = Actor(
            id="npc_goblin",
            name="Goblin",
            description="A goblin",
            location="loc_cave",
            inventory=[],
            properties={
                "health": 100,
                "max_health": 100,
                "base_morale": 100,
                "flee_threshold": 30
            }
        )

        self.location = Location(
            id="loc_cave",
            name="Cave",
            description="A dark cave"
        )

    def test_should_flee_low_morale(self):
        """Returns True when morale below threshold."""
        from behavior_libraries.actor_lib.morale import check_flee_condition

        self.npc.properties["health"] = 20  # 20% health = 20 morale

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.location],
            items=[],
            actors={"npc_goblin": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        should_flee = check_flee_condition(accessor, self.npc)

        self.assertTrue(should_flee)

    def test_should_not_flee_high_morale(self):
        """Returns False when morale above threshold."""
        from behavior_libraries.actor_lib.morale import check_flee_condition

        self.npc.properties["health"] = 100

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.location],
            items=[],
            actors={"npc_goblin": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        should_flee = check_flee_condition(accessor, self.npc)

        self.assertFalse(should_flee)

    def test_default_flee_threshold(self):
        """Uses default threshold if not specified."""
        from behavior_libraries.actor_lib.morale import check_flee_condition, DEFAULT_FLEE_THRESHOLD

        del self.npc.properties["flee_threshold"]
        self.npc.properties["health"] = 100

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.location],
            items=[],
            actors={"npc_goblin": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        # With full health and default threshold, should not flee
        should_flee = check_flee_condition(accessor, self.npc)

        self.assertFalse(should_flee)

    def test_no_flee_for_fearless(self):
        """Actors with fearless property never flee."""
        from behavior_libraries.actor_lib.morale import check_flee_condition

        self.npc.properties["health"] = 10
        self.npc.properties["fearless"] = True

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.location],
            items=[],
            actors={"npc_goblin": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        should_flee = check_flee_condition(accessor, self.npc)

        self.assertFalse(should_flee)


class TestAttemptFlee(unittest.TestCase):
    """Test attempt_flee function."""

    def setUp(self):
        """Create test actors and locations."""
        self.npc = Actor(
            id="npc_goblin",
            name="Goblin",
            description="A goblin",
            location="loc_cave",
            inventory=[],
            properties={
                "health": 20,
                "max_health": 100,
                "base_morale": 100,
                "flee_threshold": 30
            }
        )

        self.cave = Location(
            id="loc_cave",
            name="Cave",
            description="A dark cave",
            exits={"north": "loc_tunnel"}
        )

        self.tunnel = Location(
            id="loc_tunnel",
            name="Tunnel",
            description="A narrow tunnel"
        )

    def test_flee_success_moves_actor(self):
        """Successful flee moves actor to adjacent location."""
        from behavior_libraries.actor_lib.morale import attempt_flee

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.cave, self.tunnel],
            items=[],
            actors={"npc_goblin": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        # Force success by setting seed or high flee_chance
        result = attempt_flee(accessor, self.npc, force_success=True)

        self.assertTrue(result.success)
        self.assertEqual(self.npc.location, "loc_tunnel")

    def test_flee_no_exits(self):
        """Cannot flee when no exits available."""
        from behavior_libraries.actor_lib.morale import attempt_flee

        # Location with no exits
        dead_end = Location(
            id="loc_dead_end",
            name="Dead End",
            description="No way out",
            exits={}
        )

        self.npc.location = "loc_dead_end"

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_dead_end"),
            locations=[dead_end],
            items=[],
            actors={"npc_goblin": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = attempt_flee(accessor, self.npc)

        self.assertFalse(result.success)
        self.assertIn("no escape", result.message.lower())

    def test_flee_failure_stays_in_place(self):
        """Failed flee keeps actor in current location."""
        from behavior_libraries.actor_lib.morale import attempt_flee

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.cave, self.tunnel],
            items=[],
            actors={"npc_goblin": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        # Force failure
        result = attempt_flee(accessor, self.npc, force_success=False)

        self.assertFalse(result.success)
        self.assertEqual(self.npc.location, "loc_cave")

    def test_flee_avoids_locked_exits(self):
        """Flee doesn't use locked exits (via door item)."""
        from behavior_libraries.actor_lib.morale import attempt_flee
        from src.state_manager import Item

        # Only exit has a locked door
        self.cave.exits = {"north": "loc_tunnel"}

        door = Item(
            id="door_north",
            name="door",
            description="A locked door",
            location="exit:loc_cave:north",
            properties={"door": {"open": False, "locked": True}}
        )

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.cave, self.tunnel],
            items=[door],
            actors={"npc_goblin": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = attempt_flee(accessor, self.npc)

        self.assertFalse(result.success)
        self.assertIn("no escape", result.message.lower())


class TestFleeResult(unittest.TestCase):
    """Test FleeResult dataclass."""

    def test_flee_result_creation(self):
        """FleeResult can be created with all fields."""
        from behavior_libraries.actor_lib.morale import FleeResult

        result = FleeResult(
            success=True,
            destination="loc_tunnel",
            message="Goblin flees to the north!"
        )

        self.assertTrue(result.success)
        self.assertEqual(result.destination, "loc_tunnel")


class TestGetAlliesAndEnemies(unittest.TestCase):
    """Test ally and enemy detection functions."""

    def setUp(self):
        """Create test actors."""
        self.npc = Actor(
            id="npc_goblin",
            name="Goblin",
            description="A goblin",
            location="loc_cave",
            inventory=[],
            properties={
                "pack_id": "goblin_pack",
                "disposition": "hostile"
            }
        )

        self.ally = Actor(
            id="npc_goblin2",
            name="Goblin Scout",
            description="Another goblin",
            location="loc_cave",
            inventory=[],
            properties={
                "pack_id": "goblin_pack",
                "disposition": "hostile"
            }
        )

        self.enemy = Actor(
            id="player",
            name="Player",
            description="The player",
            location="loc_cave",
            inventory=[],
            properties={}
        )

        self.neutral = Actor(
            id="npc_rat",
            name="Rat",
            description="A rat",
            location="loc_cave",
            inventory=[],
            properties={"disposition": "neutral"}
        )

        self.location = Location(
            id="loc_cave",
            name="Cave",
            description="A dark cave"
        )

    def test_get_allies_same_pack(self):
        """Allies are actors in same pack at same location."""
        from behavior_libraries.actor_lib.morale import get_allies

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.location],
            items=[],
            actors={
                "npc_goblin": self.npc,
                "npc_goblin2": self.ally,
                "player": self.enemy
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        allies = get_allies(accessor, self.npc)

        self.assertEqual(len(allies), 1)
        self.assertEqual(allies[0].id, "npc_goblin2")

    def test_get_enemies_hostile_disposition(self):
        """Enemies are non-pack actors at same location."""
        from behavior_libraries.actor_lib.morale import get_enemies

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.location],
            items=[],
            actors={
                "npc_goblin": self.npc,
                "npc_goblin2": self.ally,
                "player": self.enemy
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        enemies = get_enemies(accessor, self.npc)

        self.assertEqual(len(enemies), 1)
        self.assertEqual(enemies[0].id, "player")

    def test_neutral_not_counted_as_enemy(self):
        """Neutral actors are not counted as enemies."""
        from behavior_libraries.actor_lib.morale import get_enemies

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_cave"),
            locations=[self.location],
            items=[],
            actors={
                "npc_goblin": self.npc,
                "npc_rat": self.neutral
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        enemies = get_enemies(accessor, self.npc)

        self.assertEqual(len(enemies), 0)


class TestMoraleVocabulary(unittest.TestCase):
    """Test morale vocabulary exports."""

    def test_vocabulary_has_events(self):
        """Vocabulary exports events."""
        from behavior_libraries.actor_lib.morale import vocabulary

        self.assertIn("events", vocabulary)


if __name__ == '__main__':
    unittest.main()
