"""
Tests for combat behaviors (attack) - Phase C-8.
"""

import unittest
from src.state_manager import GameState, Location, Item, Actor, Metadata
from src.behavior_manager import BehaviorManager
from src.state_accessor import StateAccessor
from tests.conftest import make_action


def create_test_state():
    """Create a minimal test state with attackable targets."""
    return GameState(
        metadata=Metadata(title="Test"),
        locations=[
            Location(id="loc1", name="Room", description="A test room")
        ],
        items=[
            Item(
                id="item_sword",
                name="sword",
                description="A sharp sword",
                location="player",
                properties={"portable": True}
            ),
            Item(
                id="item_chair",
                name="chair",
                description="A wooden chair",
                location="loc1",
                properties={"portable": False}
            )
        ],
        actors={
            "player": Actor(
                id="player",
                name="Adventurer",
                description="The player",
                location="loc1",
                inventory=["item_sword"]
            ),
            "npc_goblin": Actor(
                id="npc_goblin",
                name="goblin",
                description="A mean-looking goblin",
                location="loc1",
                inventory=[]
            ),
            "npc_guard": Actor(
                id="npc_guard",
                name="guard",
                description="A guard",
                location="loc1",
                inventory=[]
            )
        }
    )


class TestHandleAttack(unittest.TestCase):
    """Test handle_attack behavior handler."""

    def setUp(self):
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        # Load combat behaviors
        import behaviors.core.combat
        self.behavior_manager.load_module(behaviors.core.combat)

        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_attack_no_object(self):
        """Test attack without specifying target."""
        from behaviors.core.combat import handle_attack

        action = make_action(actor_id="player")
        result = handle_attack(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("what", result.primary.lower())

    def test_attack_target_not_found(self):
        """Test attacking non-existent target."""
        from behaviors.core.combat import handle_attack

        action = make_action(object="dragon", actor_id="player")
        result = handle_attack(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.primary.lower())

    def test_attack_npc_success(self):
        """Test attacking an NPC."""
        from behaviors.core.combat import handle_attack

        action = make_action(object="goblin", actor_id="player")
        result = handle_attack(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("attack", result.primary.lower())
        self.assertIn("goblin", result.primary.lower())

    def test_attack_item_fails(self):
        """Test attacking an item (should fail - can't attack items)."""
        from behaviors.core.combat import handle_attack

        action = make_action(object="chair", actor_id="player")
        result = handle_attack(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("can't attack", result.primary.lower())

    def test_attack_npc_by_npc(self):
        """Test NPC attacking another NPC (critical for actor_id threading)."""
        from behaviors.core.combat import handle_attack

        action = make_action(object="goblin", actor_id="npc_guard")
        result = handle_attack(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("attack", result.primary.lower())


class TestCombatVocabulary(unittest.TestCase):
    """Test that combat vocabulary is properly defined."""

    def test_vocabulary_has_attack(self):
        """Test that attack verb is in vocabulary."""
        from behaviors.core.combat import vocabulary

        verbs = {v["word"] for v in vocabulary["verbs"]}
        self.assertIn("attack", verbs)

    def test_attack_has_synonyms(self):
        """Test that attack has synonyms."""
        from behaviors.core.combat import vocabulary

        attack_verb = next(v for v in vocabulary["verbs"] if v["word"] == "attack")
        synonyms = attack_verb.get("synonyms", [])
        self.assertTrue(len(synonyms) > 0)
        self.assertIn("hit", synonyms)


if __name__ == '__main__':
    unittest.main()
