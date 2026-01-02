"""Tests for containment index (whereabouts) infrastructure."""

import unittest
from src.state_manager import GameState, Metadata, Location, Item, Actor
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.types import LocationId, ItemId, ActorId


class TestContainmentIndex(unittest.TestCase):
    """Tests for containment index building and queries."""

    def setUp(self):
        """Create basic game state for testing."""
        self.metadata = Metadata(
            title="Test Game",
            version="1.0",
            start_location="loc_cave"
        )

        self.locations = [
            Location(id=LocationId("loc_cave"), name="Cave", description="A dark cave"),
            Location(id=LocationId("loc_forest"), name="Forest", description="A forest"),
        ]

        self.items = [
            Item(id=ItemId("sword"), name="sword", description="A sword", location="loc_cave"),
            Item(id=ItemId("shield"), name="shield", description="A shield", location="loc_cave"),
            Item(id=ItemId("apple"), name="apple", description="An apple", location="player"),
            Item(id=ItemId("consumed"), name="bread", description="Bread", location="__consumed_by_player__"),
        ]

        self.actors = {
            ActorId("player"): Actor(
                id=ActorId("player"),
                name="Player",
                description="You",
                location=LocationId("loc_cave"),
                inventory=[ItemId("apple")]
            ),
            ActorId("npc_guard"): Actor(
                id=ActorId("npc_guard"),
                name="Guard",
                description="A guard",
                location=LocationId("loc_forest"),
                inventory=[]
            ),
        }

        self.game_state = GameState(
            metadata=self.metadata,
            locations=self.locations,
            items=self.items,
            actors=self.actors
        )

        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_index_fields_exist(self):
        """Test that index fields exist on GameState."""
        self.assertIsNotNone(self.game_state._entities_at)
        self.assertIsNotNone(self.game_state._entity_where)

    def test_index_building_from_items(self):
        """Test that index is built correctly from item locations."""
        # Build the index (would normally be called by load_game_state)
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Check forward index: loc_cave should have sword and shield
        self.assertIn("loc_cave", self.game_state._entities_at)
        entities_at_cave = self.game_state._entities_at["loc_cave"]
        self.assertIn("sword", entities_at_cave)
        self.assertIn("shield", entities_at_cave)

        # Check reverse index: sword should be in loc_cave
        self.assertEqual(self.game_state._entity_where["sword"], "loc_cave")
        self.assertEqual(self.game_state._entity_where["shield"], "loc_cave")

    def test_index_building_from_actors(self):
        """Test that index is built correctly from actor locations."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Check forward index: loc_cave should have player
        entities_at_cave = self.game_state._entities_at["loc_cave"]
        self.assertIn("player", entities_at_cave)

        # Check forward index: loc_forest should have npc_guard
        entities_at_forest = self.game_state._entities_at["loc_forest"]
        self.assertIn("npc_guard", entities_at_forest)

        # Check reverse index
        self.assertEqual(self.game_state._entity_where["player"], "loc_cave")
        self.assertEqual(self.game_state._entity_where["npc_guard"], "loc_forest")

    def test_index_excludes_removed_entities(self):
        """Test that entities with location starting with __ are excluded."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Consumed item should NOT be in index
        self.assertNotIn("consumed", self.game_state._entity_where)
        self.assertNotIn("__consumed_by_player__", self.game_state._entities_at)

    def test_index_handles_actor_inventory(self):
        """Test that items in actor inventory are indexed correctly."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Apple is in player's inventory (location="player")
        self.assertIn("player", self.game_state._entities_at)
        entities_in_player = self.game_state._entities_at["player"]
        self.assertIn("apple", entities_in_player)

        # Check reverse index
        self.assertEqual(self.game_state._entity_where["apple"], "player")

    def test_get_entities_at_all_types(self):
        """Test get_entities_at without entity_type filter."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Get all entities at loc_cave (should include items and actors)
        entities = self.accessor.get_entities_at("loc_cave")
        entity_ids = {e.id for e in entities}

        self.assertIn("sword", entity_ids)
        self.assertIn("shield", entity_ids)
        self.assertIn("player", entity_ids)
        self.assertEqual(len(entities), 3)

    def test_get_entities_at_filter_items(self):
        """Test get_entities_at with entity_type='item' filter."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Get only items at loc_cave
        items = self.accessor.get_entities_at("loc_cave", entity_type="item")
        item_ids = {i.id for i in items}

        self.assertIn("sword", item_ids)
        self.assertIn("shield", item_ids)
        self.assertNotIn("player", item_ids)
        self.assertEqual(len(items), 2)

    def test_get_entities_at_filter_actors(self):
        """Test get_entities_at with entity_type='actor' filter."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Get only actors at loc_cave
        actors = self.accessor.get_entities_at("loc_cave", entity_type="actor")
        actor_ids = {a.id for a in actors}

        self.assertIn("player", actor_ids)
        self.assertNotIn("sword", actor_ids)
        self.assertEqual(len(actors), 1)

    def test_get_entities_at_empty_location(self):
        """Test get_entities_at for location with no entities."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Create empty location
        empty_loc = Location(id=LocationId("loc_empty"), name="Empty", description="Empty")
        self.game_state.locations.append(empty_loc)

        entities = self.accessor.get_entities_at("loc_empty")
        self.assertEqual(len(entities), 0)

    def test_set_entity_where_updates_item_location(self):
        """Test set_entity_where updates item.location."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Move sword from loc_cave to loc_forest
        self.accessor.set_entity_where("sword", "loc_forest")

        # Check entity.location was updated
        sword = self.game_state.get_item(ItemId("sword"))
        self.assertEqual(sword.location, "loc_forest")

    def test_set_entity_where_updates_forward_index(self):
        """Test set_entity_where updates _entities_at."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Move sword from loc_cave to loc_forest
        self.accessor.set_entity_where("sword", "loc_forest")

        # Check forward index
        self.assertNotIn("sword", self.game_state._entities_at["loc_cave"])
        self.assertIn("sword", self.game_state._entities_at["loc_forest"])

    def test_set_entity_where_updates_reverse_index(self):
        """Test set_entity_where updates _entity_where."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Move sword from loc_cave to loc_forest
        self.accessor.set_entity_where("sword", "loc_forest")

        # Check reverse index
        self.assertEqual(self.game_state._entity_where["sword"], "loc_forest")

    def test_set_entity_where_to_removal_state(self):
        """Test set_entity_where with removal state (__consumed__)."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Consume sword
        self.accessor.set_entity_where("sword", "__consumed_by_player__")

        # Check entity.location was updated
        sword = self.game_state.get_item(ItemId("sword"))
        self.assertEqual(sword.location, "__consumed_by_player__")

        # Check sword removed from indices
        self.assertNotIn("sword", self.game_state._entity_where)
        self.assertNotIn("sword", self.game_state._entities_at.get("loc_cave", set()))

    def test_set_entity_where_actor(self):
        """Test set_entity_where works with actors."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Move player from loc_cave to loc_forest
        self.accessor.set_entity_where("player", "loc_forest")

        # Check entity.location was updated
        player = self.game_state.get_actor(ActorId("player"))
        self.assertEqual(player.location, "loc_forest")

        # Check indices updated
        self.assertNotIn("player", self.game_state._entities_at["loc_cave"])
        self.assertIn("player", self.game_state._entities_at["loc_forest"])
        self.assertEqual(self.game_state._entity_where["player"], "loc_forest")

    def test_set_entity_where_entity_not_found(self):
        """Test set_entity_where raises ValueError for unknown entity."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        with self.assertRaises(ValueError) as ctx:
            self.accessor.set_entity_where("unknown_entity", "loc_cave")

        self.assertIn("Entity not found", str(ctx.exception))

    def test_set_entity_where_container_not_found(self):
        """Test set_entity_where raises ValueError for unknown container."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        with self.assertRaises(ValueError) as ctx:
            self.accessor.set_entity_where("sword", "loc_unknown")

        self.assertIn("Container not found", str(ctx.exception))

    def test_set_entity_where_allows_actor_as_container(self):
        """Test set_entity_where allows moving items to actors (inventory)."""
        from src.state_manager import _build_whereabouts_index
        _build_whereabouts_index(self.game_state)

        # Move sword to player's inventory
        self.accessor.set_entity_where("sword", "player")

        # Check entity.location was updated
        sword = self.game_state.get_item(ItemId("sword"))
        self.assertEqual(sword.location, "player")

        # Check indices
        self.assertIn("sword", self.game_state._entities_at["player"])
        self.assertEqual(self.game_state._entity_where["sword"], "player")


if __name__ == '__main__':
    unittest.main()
