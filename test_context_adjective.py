#!/usr/bin/env python3
"""Quick test of context building with container items."""

from pathlib import Path
from src.game_engine import GameEngine

# Create engine
engine = GameEngine(Path('examples/spatial_game'))

# Position player in library (where spellbooks are on desk)
player = engine.game_state.actors['player']
player.location = 'loc_library'

# Build context
context = engine.build_parser_context('player')
print("Context location_objects:", context['location_objects'])
print()
print("Should include: desk, spellbook (appears twice - red and blue)")
