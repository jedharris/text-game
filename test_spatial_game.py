"""Test script for spatial_game implementation."""

from src.game_engine import GameEngine
from pathlib import Path


def test_scenario(engine, commands, scenario_name):
    """Execute a test scenario."""
    print(f"\n{'='*60}")
    print(f"Testing: {scenario_name}")
    print('='*60)

    for cmd in commands:
        print(f"\n> {cmd}")
        result = engine.json_handler.handle_message({
            "type": "command",
            "action": {"verb": cmd, "actor_id": "player"}
        })
        print(f"  Success: {result.get('success', False)}")
        if result.get('message'):
            msg = result['message'][:200]  # Truncate long messages
            print(f"  Message: {msg}")


def main():
    print("Loading spatial_game...")
    game_dir = Path('examples/spatial_game')
    engine = GameEngine(game_dir)

    print("✓ Game loaded successfully!")

    # Test 1: Check tree climb without bench
    test_scenario(engine, [
        "examine tree",
        "climb tree"
    ], "Tree climb without bench (should fail)")

    # Test 2: Garden puzzle chain
    test_scenario(engine, [
        "examine bench",
        "stand on bench",
        "climb tree",
        "take star"
    ], "Full garden puzzle chain (should succeed)")

    # Test 3: Crystal ball without positioning
    # First reset by loading fresh
    engine = GameEngine(game_dir)
    test_scenario(engine, [
        "go north",
        "up",
        "peer into ball"
    ], "Crystal ball without positioning (should fail)")

    # Test 4: Crystal ball with positioning
    test_scenario(engine, [
        "examine stand",
        "peer into ball"
    ], "Crystal ball after examining stand (should succeed)")

    print("\n" + "="*60)
    print("✓ All test scenarios completed!")
    print("="*60)


if __name__ == "__main__":
    main()
