"""
Pytest configuration and shared test fixtures.

Based on behavior_refactoring_testing.md lines 14-106
"""
from dataclasses import field
from typing import Dict, List, Any
from src.state_manager import GameState, Item, Location, NPC, PlayerState, Metadata


def create_test_state() -> GameState:
    """
    Create a minimal GameState for testing with common test entities.

    Returns:
        GameState with:
        - Player at "location_room"
        - A portable sword (item_sword) in the room
        - A non-portable table (item_table) in the room
        - A magic lantern (item_lantern) in the room with light_sources behavior
        - An anvil (item_anvil) with weight=150 in the room
        - A feather (item_feather) with weight=1 in the room

    NOTE: Uses CURRENT data model (lists, not dicts). Will be refactored to
    unified actor model in Phase 3.
    """
    # Create metadata
    metadata = Metadata(
        title="Test Game",
        version="1.0",
        description="A test game",
        start_location="location_room"
    )

    # Create player
    player = PlayerState(
        location="location_room",
        inventory=[],
        properties={"max_carry_weight": 100}
    )

    # Create location
    room = Location(
        id="location_room",
        name="Test Room",
        description="A room for testing",
        exits={},
        items=["item_sword", "item_table", "item_lantern", "item_anvil", "item_feather"],
        npcs=[],
        properties={},
        behaviors={}
    )

    # Create test items
    sword = Item(
        id="item_sword",
        name="sword",
        description="A test sword",
        location="location_room",
        properties={"portable": True},
        behaviors={}
    )

    table = Item(
        id="item_table",
        name="table",
        description="A heavy table",
        location="location_room",
        properties={"portable": False},
        behaviors={}
    )

    lantern = Item(
        id="item_lantern",
        name="lantern",
        description="A magic lantern",
        location="location_room",
        properties={
            "portable": True,
            "states": {"lit": False}
        },
        behaviors={"on_take": "light_sources"}  # Will become list in Phase 3
    )

    anvil = Item(
        id="item_anvil",
        name="anvil",
        description="A very heavy anvil",
        location="location_room",
        properties={
            "portable": True,
            "weight": 150
        },
        behaviors={}
    )

    feather = Item(
        id="item_feather",
        name="feather",
        description="A light feather",
        location="location_room",
        properties={
            "portable": True,
            "weight": 1
        },
        behaviors={}
    )

    # Create and return game state
    state = GameState(
        metadata=metadata,
        locations=[room],
        items=[sword, table, lantern, anvil, feather],
        doors=[],
        locks=[],
        npcs=[],
        player=player,
        extra={}
    )

    return state
