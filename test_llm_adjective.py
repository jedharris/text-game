#!/usr/bin/env python3
"""Quick test of LLM parser with adjectives."""

from src.state_manager import load_game_state
from src.behavior_manager import BehaviorManager
from src.game_engine import GameEngine
from src.vocabulary_service import build_merged_vocabulary
from src.llm_command_parser import LLMCommandParser

# Load game
state = load_game_state('examples/spatial_game/game_state.json')
bm = BehaviorManager()
# Don't need to load behaviors for this test - just testing parser

# Create engine and vocab
engine = GameEngine(state)
vocab = build_merged_vocabulary(state, bm)
parser = LLMCommandParser(vocab)

# Position player in library (where spellbooks are)
player = state.actors['player']
player.location = 'loc_library'

# Build context
context = engine.build_llm_parser_context('player')
print("Context location_objects:", context['location_objects'])
print()

# Test commands
commands = [
    "examine red spellbook",
    "examine blue spellbook",
    "read red spellbook",
    "read blue spellbook"
]

for cmd in commands:
    print(f"Command: {cmd}")
    result = parser.parse(context, cmd)
    if result:
        print(f"  Type: {result.get('type')}")
        if result['type'] == 'command':
            action = result.get('action', {})
            print(f"  Verb: {action.get('verb')}")
            print(f"  Object: {action.get('object')}")
            print(f"  Adjective: {action.get('adjective')}")
    else:
        print("  Failed to parse")
    print()
