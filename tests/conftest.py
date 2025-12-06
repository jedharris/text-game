"""
Pytest configuration and shared test fixtures.

Based on behavior_refactoring_testing.md lines 14-106
"""
import unittest
from pathlib import Path
from dataclasses import field
from typing import Dict, List, Any
from src.state_manager import GameState, Item, Location, Actor, Metadata, load_game_state
from src.behavior_manager import BehaviorManager
from src.state_accessor import StateAccessor
from src.word_entry import WordEntry, WordType


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

    Uses unified actor model (Phase 3).
    """
    # Create metadata
    metadata = Metadata(
        title="Test Game",
        version="1.0",
        description="A test game",
        start_location="location_room"
    )

    # Create player
    # Note: player.name must not be "player" - that's a prohibited name
    player = Actor(
        id="player",
        name="Adventurer",
        description="The player character",
        location="location_room",
        inventory=[],
        properties={"max_carry_weight": 100},
        behaviors=[]
    )

    # Create location
    room = Location(
        id="location_room",
        name="Test Room",
        description="A room for testing",
        exits={},
        items=["item_sword", "item_table", "item_lantern", "item_anvil", "item_feather"],
        properties={},
        behaviors=[]
    )

    # Create test items
    sword = Item(
        id="item_sword",
        name="sword",
        description="A test sword",
        location="location_room",
        properties={"portable": True},
        behaviors=[]
    )

    table = Item(
        id="item_table",
        name="table",
        description="A heavy table",
        location="location_room",
        properties={"portable": False},
        behaviors=[]
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
        behaviors=["light_sources"]
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
        behaviors=[]
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
        behaviors=[]
    )

    # Create and return game state
    state = GameState(
        metadata=metadata,
        locations=[room],
        items=[sword, table, lantern, anvil, feather],
        locks=[],
        actors={"player": player},
        extra={}
    )

    return state


def make_word_entry(word: str, word_type: WordType = WordType.NOUN, synonyms: List[str] = None) -> WordEntry:
    """
    Create a WordEntry for testing.

    Helper function to reduce boilerplate when creating WordEntry objects in tests.

    Args:
        word: The word string
        word_type: The grammatical type (defaults to NOUN)
        synonyms: List of synonyms (defaults to empty list)

    Returns:
        WordEntry with specified attributes

    Examples:
        >>> make_word_entry("sword")
        WordEntry(word="sword", word_type=WordType.NOUN, synonyms=[])

        >>> make_word_entry("take", WordType.VERB)
        WordEntry(word="take", word_type=WordType.VERB, synonyms=[])

        >>> make_word_entry("stairs", synonyms=["staircase", "steps"])
        WordEntry(word="stairs", word_type=WordType.NOUN, synonyms=["staircase", "steps"])
    """
    if synonyms is None:
        synonyms = []
    return WordEntry(word=word, word_type=word_type, synonyms=synonyms)


def make_action(verb: str = None, object: str = None, adjective: str = None,
                indirect_object: str = None, indirect_adjective: str = None,
                preposition: str = None, direction: str = None,
                actor_id: str = "player", **kwargs) -> Dict[str, Any]:
    """
    Create an action dictionary with strings auto-converted to WordEntry objects.

    This helper allows tests to use simple strings while ensuring handlers receive
    proper WordEntry objects. This maintains backward compatibility with existing
    tests while supporting the new WordEntry-only infrastructure.

    Args:
        verb: Verb string (optional)
        object: Object string (converted to WordEntry)
        adjective: Adjective string (converted to WordEntry)
        indirect_object: Indirect object string (converted to WordEntry)
        indirect_adjective: Indirect adjective string (converted to WordEntry)
        preposition: Preposition string (converted to WordEntry)
        direction: Direction string (converted to WordEntry)
        actor_id: Actor performing the action (defaults to "player")
        **kwargs: Additional action fields passed through unchanged

    Returns:
        Action dict with WordEntry objects for word fields

    Examples:
        >>> make_action(verb="take", object="sword", actor_id="player")
        {"verb": "take", "object": WordEntry("sword", ...), "actor_id": "player"}

        >>> make_action(object="key", adjective="brass")
        {"object": WordEntry("key", ...), "adjective": WordEntry("brass", ...), "actor_id": "player"}
    """
    action = {"actor_id": actor_id}

    # Add verb as string (verbs don't need to be WordEntry in action dicts)
    if verb is not None:
        action["verb"] = verb

    # Convert word fields to WordEntry
    if object is not None:
        action["object"] = make_word_entry(object)
    if adjective is not None:
        action["adjective"] = adjective  # Adjectives stay as strings for description matching
    if indirect_object is not None:
        action["indirect_object"] = make_word_entry(indirect_object)
    if indirect_adjective is not None:
        action["indirect_adjective"] = indirect_adjective  # Also stays as string
    if preposition is not None:
        action["preposition"] = preposition  # Prepositions stay as strings
    if direction is not None:
        # Direction is now handled as object
        action["object"] = make_word_entry(direction)

    # Add any additional kwargs
    action.update(kwargs)

    return action


# Base test classes for common setUp patterns

class BaseTestCase(unittest.TestCase):
    """
    Base test case with minimal state setup.

    Provides:
    - self.state: Minimal test GameState via create_test_state()
    - self.accessor: StateAccessor with no behavior manager

    Use this for tests that don't need behavior loading.
    """

    def setUp(self):
        self.state = create_test_state()
        self.accessor = StateAccessor(self.state, None)


class BehaviorTestCase(unittest.TestCase):
    """
    Base test case with behaviors loaded.

    Provides:
    - self.state: Minimal test GameState via create_test_state()
    - self.behavior_manager: BehaviorManager with all behaviors loaded from behaviors/ dir
    - self.accessor: StateAccessor with behavior manager

    Use this for tests that need to invoke handlers or behaviors.
    """

    def setUp(self):
        self.state = create_test_state()
        self.behavior_manager = BehaviorManager()

        # Load all behaviors from behaviors directory
        project_root = Path(__file__).parent.parent
        behaviors_dir = project_root / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)

        self.accessor = StateAccessor(self.state, self.behavior_manager)


class SimpleGameTestCase(unittest.TestCase):
    """
    Base test case using the simple_game example.

    Provides:
    - self.state: Full game state from examples/simple_game/game_state.json
    - self.behavior_manager: BehaviorManager with all behaviors loaded
    - self.accessor: StateAccessor with behavior manager

    Use this for integration tests that need a complete game world.
    """

    def setUp(self):
        project_root = Path(__file__).parent.parent
        self.state = load_game_state(str(project_root / "examples" / "simple_game" / "game_state.json"))
        self.behavior_manager = BehaviorManager()
        behaviors_dir = project_root / "behaviors"
        modules = self.behavior_manager.discover_modules(str(behaviors_dir))
        self.behavior_manager.load_modules(modules)
        self.accessor = StateAccessor(self.state, self.behavior_manager)
