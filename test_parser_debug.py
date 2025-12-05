"""Debug why 'stand on bench' fails but 'sit on chair' works."""

from src.game_engine import GameEngine
from pathlib import Path

# Load spatial_game and create parser
game_dir = Path('examples/spatial_game')
engine = GameEngine(game_dir)
parser = engine.create_parser()

# Check if 'stand' is in vocabulary
print("Checking vocabulary:")
stand_entry = parser._lookup_word("stand")
sit_entry = parser._lookup_word("sit")

print(f"  'stand': {stand_entry}")
if stand_entry:
    print(f"    word_type: {stand_entry.word_type}")
    print(f"    object_required: {stand_entry.object_required}")

print(f"  'sit': {sit_entry}")
if sit_entry:
    print(f"    word_type: {sit_entry.word_type}")
    print(f"    object_required: {sit_entry.object_required}")

# Try parsing with detailed output
print("\nParsing 'stand on bench':")
tokens = "stand on bench".lower().split()
print(f"  Tokens: {tokens}")

entries = []
for token in tokens:
    entry = parser._lookup_word(token)
    print(f"  '{token}' -> {entry}")
    if entry:
        entries.append(entry)

print(f"\n  Entries to match: {len(entries)}")
for i, entry in enumerate(entries):
    print(f"    {i}: {entry.word} ({entry.word_type})")
