"""Tests for pack coordination system (Phase 9 of Actor Interaction)."""

import unittest
from unittest.mock import Mock

from src.state_manager import Actor, Location, GameState, Metadata
from src.state_accessor import StateAccessor


class TestGetPackMembers(unittest.TestCase):
    """Test get_pack_members function."""

    def setUp(self):
        """Create test pack."""
        self.alpha = Actor(
            id="npc_wolf_alpha",
            name="Alpha Wolf",
            description="A large wolf",
            location="loc_forest",
            inventory=[],
            properties={
                "pack_id": "wolf_pack",
                "pack_role": "alpha",
                "disposition": "neutral"
            }
        )

        self.follower1 = Actor(
            id="npc_wolf_1",
            name="Wolf",
            description="A wolf",
            location="loc_forest",
            inventory=[],
            properties={
                "pack_id": "wolf_pack",
                "pack_role": "follower",
                "disposition": "neutral"
            }
        )

        self.follower2 = Actor(
            id="npc_wolf_2",
            name="Wolf",
            description="A wolf",
            location="loc_clearing",
            inventory=[],
            properties={
                "pack_id": "wolf_pack",
                "pack_role": "follower",
                "disposition": "neutral"
            }
        )

        self.other_pack = Actor(
            id="npc_goblin",
            name="Goblin",
            description="A goblin",
            location="loc_forest",
            inventory=[],
            properties={
                "pack_id": "goblin_pack",
                "disposition": "hostile"
            }
        )

        self.location = Location(
            id="loc_forest",
            name="Forest",
            description="A dark forest"
        )

    def test_get_pack_members_returns_all(self):
        """Returns all actors in a pack."""
        from behaviors.library.actors.packs import get_pack_members

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_forest"),
            locations=[self.location],
            items=[],
            actors={
                "npc_wolf_alpha": self.alpha,
                "npc_wolf_1": self.follower1,
                "npc_wolf_2": self.follower2,
                "npc_goblin": self.other_pack
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        members = get_pack_members(accessor, "wolf_pack")

        self.assertEqual(len(members), 3)
        member_ids = {m.id for m in members}
        self.assertIn("npc_wolf_alpha", member_ids)
        self.assertIn("npc_wolf_1", member_ids)
        self.assertIn("npc_wolf_2", member_ids)

    def test_get_pack_members_excludes_other_packs(self):
        """Does not include members of other packs."""
        from behaviors.library.actors.packs import get_pack_members

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_forest"),
            locations=[self.location],
            items=[],
            actors={
                "npc_wolf_alpha": self.alpha,
                "npc_goblin": self.other_pack
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        members = get_pack_members(accessor, "wolf_pack")

        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].id, "npc_wolf_alpha")

    def test_get_pack_members_empty_pack(self):
        """Returns empty list for unknown pack."""
        from behaviors.library.actors.packs import get_pack_members

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_forest"),
            locations=[self.location],
            items=[],
            actors={"npc_wolf_alpha": self.alpha},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        members = get_pack_members(accessor, "nonexistent_pack")

        self.assertEqual(len(members), 0)


class TestGetAlpha(unittest.TestCase):
    """Test get_alpha function."""

    def setUp(self):
        """Create test pack with alpha."""
        self.alpha = Actor(
            id="npc_wolf_alpha",
            name="Alpha Wolf",
            description="A large wolf",
            location="loc_forest",
            inventory=[],
            properties={
                "pack_id": "wolf_pack",
                "pack_role": "alpha",
                "disposition": "neutral"
            }
        )

        self.follower = Actor(
            id="npc_wolf_1",
            name="Wolf",
            description="A wolf",
            location="loc_forest",
            inventory=[],
            properties={
                "pack_id": "wolf_pack",
                "pack_role": "follower",
                "disposition": "neutral"
            }
        )

        self.location = Location(
            id="loc_forest",
            name="Forest",
            description="A dark forest"
        )

    def test_get_alpha_returns_alpha(self):
        """Returns the alpha of an actor's pack."""
        from behaviors.library.actors.packs import get_alpha

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_forest"),
            locations=[self.location],
            items=[],
            actors={
                "npc_wolf_alpha": self.alpha,
                "npc_wolf_1": self.follower
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        alpha = get_alpha(accessor, self.follower)

        self.assertIsNotNone(alpha)
        self.assertEqual(alpha.id, "npc_wolf_alpha")

    def test_get_alpha_for_alpha_returns_self(self):
        """Alpha's alpha is itself."""
        from behaviors.library.actors.packs import get_alpha

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_forest"),
            locations=[self.location],
            items=[],
            actors={"npc_wolf_alpha": self.alpha},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        alpha = get_alpha(accessor, self.alpha)

        self.assertIsNotNone(alpha)
        self.assertEqual(alpha.id, "npc_wolf_alpha")

    def test_get_alpha_no_pack(self):
        """Returns None for actor without pack."""
        from behaviors.library.actors.packs import get_alpha

        loner = Actor(
            id="npc_loner",
            name="Loner",
            description="A lone wolf",
            location="loc_forest",
            inventory=[],
            properties={}
        )

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_forest"),
            locations=[self.location],
            items=[],
            actors={"npc_loner": loner},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        alpha = get_alpha(accessor, loner)

        self.assertIsNone(alpha)

    def test_get_alpha_pack_without_alpha(self):
        """Returns None for pack without alpha."""
        from behaviors.library.actors.packs import get_alpha

        # Remove alpha role
        self.follower.properties["pack_role"] = "follower"
        self.alpha.properties["pack_role"] = "follower"

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_forest"),
            locations=[self.location],
            items=[],
            actors={
                "npc_wolf_alpha": self.alpha,
                "npc_wolf_1": self.follower
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        alpha = get_alpha(accessor, self.follower)

        self.assertIsNone(alpha)


class TestIsAlpha(unittest.TestCase):
    """Test is_alpha function."""

    def test_is_alpha_true(self):
        """Returns True for alpha actors."""
        from behaviors.library.actors.packs import is_alpha

        alpha = Actor(
            id="npc_wolf_alpha",
            name="Alpha Wolf",
            description="A large wolf",
            location="loc_forest",
            inventory=[],
            properties={
                "pack_id": "wolf_pack",
                "pack_role": "alpha"
            }
        )

        self.assertTrue(is_alpha(alpha))

    def test_is_alpha_false_for_follower(self):
        """Returns False for follower actors."""
        from behaviors.library.actors.packs import is_alpha

        follower = Actor(
            id="npc_wolf_1",
            name="Wolf",
            description="A wolf",
            location="loc_forest",
            inventory=[],
            properties={
                "pack_id": "wolf_pack",
                "pack_role": "follower"
            }
        )

        self.assertFalse(is_alpha(follower))

    def test_is_alpha_false_no_role(self):
        """Returns False for actors without pack_role."""
        from behaviors.library.actors.packs import is_alpha

        loner = Actor(
            id="npc_loner",
            name="Loner",
            description="A lone wolf",
            location="loc_forest",
            inventory=[],
            properties={}
        )

        self.assertFalse(is_alpha(loner))


class TestSyncPackDisposition(unittest.TestCase):
    """Test sync_pack_disposition function."""

    def setUp(self):
        """Create test pack."""
        self.alpha = Actor(
            id="npc_wolf_alpha",
            name="Alpha Wolf",
            description="A large wolf",
            location="loc_forest",
            inventory=[],
            properties={
                "pack_id": "wolf_pack",
                "pack_role": "alpha",
                "disposition": "hostile"
            }
        )

        self.follower1 = Actor(
            id="npc_wolf_1",
            name="Wolf",
            description="A wolf",
            location="loc_forest",
            inventory=[],
            properties={
                "pack_id": "wolf_pack",
                "pack_role": "follower",
                "disposition": "neutral"
            }
        )

        self.follower2 = Actor(
            id="npc_wolf_2",
            name="Wolf",
            description="A wolf",
            location="loc_forest",
            inventory=[],
            properties={
                "pack_id": "wolf_pack",
                "pack_role": "follower",
                "disposition": "neutral"
            }
        )

        self.location = Location(
            id="loc_forest",
            name="Forest",
            description="A dark forest"
        )

    def test_sync_followers_to_alpha(self):
        """Followers sync to alpha's disposition."""
        from behaviors.library.actors.packs import sync_pack_disposition

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_forest"),
            locations=[self.location],
            items=[],
            actors={
                "npc_wolf_alpha": self.alpha,
                "npc_wolf_1": self.follower1,
                "npc_wolf_2": self.follower2
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        changed = sync_pack_disposition(accessor, "wolf_pack")

        self.assertEqual(len(changed), 2)
        self.assertEqual(self.follower1.properties["disposition"], "hostile")
        self.assertEqual(self.follower2.properties["disposition"], "hostile")

    def test_sync_no_change_if_already_synced(self):
        """No change if followers already match alpha."""
        from behaviors.library.actors.packs import sync_pack_disposition

        self.follower1.properties["disposition"] = "hostile"
        self.follower2.properties["disposition"] = "hostile"

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_forest"),
            locations=[self.location],
            items=[],
            actors={
                "npc_wolf_alpha": self.alpha,
                "npc_wolf_1": self.follower1,
                "npc_wolf_2": self.follower2
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        changed = sync_pack_disposition(accessor, "wolf_pack")

        self.assertEqual(len(changed), 0)

    def test_sync_does_not_change_alpha(self):
        """Sync does not change alpha's disposition."""
        from behaviors.library.actors.packs import sync_pack_disposition

        original_disposition = self.alpha.properties["disposition"]

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_forest"),
            locations=[self.location],
            items=[],
            actors={
                "npc_wolf_alpha": self.alpha,
                "npc_wolf_1": self.follower1
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        sync_pack_disposition(accessor, "wolf_pack")

        self.assertEqual(self.alpha.properties["disposition"], original_disposition)

    def test_sync_no_alpha_returns_empty(self):
        """Returns empty list if pack has no alpha."""
        from behaviors.library.actors.packs import sync_pack_disposition

        # Make alpha a follower
        self.alpha.properties["pack_role"] = "follower"

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_forest"),
            locations=[self.location],
            items=[],
            actors={
                "npc_wolf_alpha": self.alpha,
                "npc_wolf_1": self.follower1
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        changed = sync_pack_disposition(accessor, "wolf_pack")

        self.assertEqual(len(changed), 0)


class TestSyncFollowerDisposition(unittest.TestCase):
    """Test sync_follower_disposition for individual actors."""

    def setUp(self):
        """Create test pack."""
        self.alpha = Actor(
            id="npc_wolf_alpha",
            name="Alpha Wolf",
            description="A large wolf",
            location="loc_forest",
            inventory=[],
            properties={
                "pack_id": "wolf_pack",
                "pack_role": "alpha",
                "disposition": "hostile"
            }
        )

        self.follower = Actor(
            id="npc_wolf_1",
            name="Wolf",
            description="A wolf",
            location="loc_forest",
            inventory=[],
            properties={
                "pack_id": "wolf_pack",
                "pack_role": "follower",
                "disposition": "neutral"
            }
        )

        self.location = Location(
            id="loc_forest",
            name="Forest",
            description="A dark forest"
        )

    def test_sync_single_follower(self):
        """Syncs a single follower to alpha."""
        from behaviors.library.actors.packs import sync_follower_disposition

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_forest"),
            locations=[self.location],
            items=[],
            actors={
                "npc_wolf_alpha": self.alpha,
                "npc_wolf_1": self.follower
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        changed = sync_follower_disposition(accessor, self.follower)

        self.assertTrue(changed)
        self.assertEqual(self.follower.properties["disposition"], "hostile")

    def test_sync_follower_no_change_if_synced(self):
        """Returns False if follower already synced."""
        from behaviors.library.actors.packs import sync_follower_disposition

        self.follower.properties["disposition"] = "hostile"

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_forest"),
            locations=[self.location],
            items=[],
            actors={
                "npc_wolf_alpha": self.alpha,
                "npc_wolf_1": self.follower
            },
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        changed = sync_follower_disposition(accessor, self.follower)

        self.assertFalse(changed)

    def test_sync_follower_alpha_not_changed(self):
        """Alpha actors are not changed by sync."""
        from behaviors.library.actors.packs import sync_follower_disposition

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_forest"),
            locations=[self.location],
            items=[],
            actors={"npc_wolf_alpha": self.alpha},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        changed = sync_follower_disposition(accessor, self.alpha)

        self.assertFalse(changed)


class TestPackVocabulary(unittest.TestCase):
    """Test pack vocabulary exports."""

    def test_vocabulary_has_events(self):
        """Vocabulary exports events."""
        from behaviors.library.actors.packs import vocabulary

        self.assertIn("events", vocabulary)


if __name__ == '__main__':
    unittest.main()
