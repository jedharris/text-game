"""Test what parser does with 'stand on bench'."""

from src.game_engine import GameEngine
from pathlib import Path

# Load spatial_game and create parser
game_dir = Path('examples/spatial_game')
engine = GameEngine(game_dir)
parser = engine.create_parser()

# Test parsing
test_commands = [
    "stand on bench",
    "sit on chair",
    "stand",
    "examine bench",
]

print("Parser tests:")
for cmd in test_commands:
    result = parser.parse_command(cmd)
    if result:
        print(f"\n✓ '{cmd}'")
        print(f"  verb: {result.verb.word if result.verb else None}")
        print(f"  preposition: {result.preposition.word if result.preposition else None}")
        print(f"  direct_object: {result.direct_object.word if result.direct_object else None}")
        print(f"  indirect_object: {result.indirect_object.word if result.indirect_object else None}")
    else:
        print(f"\n✗ '{cmd}' -> None (parser can't handle this)")
