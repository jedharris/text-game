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
                _properties={"portable": True}
            ),
            Item(
                id="item_chair",
                name="chair",
                description="A wooden chair",
                location="loc1",
                _properties={"portable": False}
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

if __name__ == '__main__':
    unittest.main()
