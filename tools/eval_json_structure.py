#!/usr/bin/env python3
"""
Evaluate JSON Structure for Narrator

This tool generates the JSON that would be sent to the narrator for various
game actions, without actually calling the LLM. Useful for:
1. Inspecting the structure the narrator receives
2. Testing changes to the NarrationAssembler
3. Comparing current vs. proposed structures

Usage:
    python tools/eval_json_structure.py <game_dir> [--commands "cmd1" "cmd2" ...]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))


def setup_game(game_dir: Path):
    """Set up game state and handler."""
    from src.state_manager import load_game_state
    from src.llm_protocol import LLMProtocolHandler
    from src.behavior_manager import BehaviorManager
    from src.vocabulary_service import build_merged_vocabulary
    from src.parser import Parser

    # Load game state
    state_file = game_dir / "game_state.json"
    state = load_game_state(state_file)

    # Add game directory to sys.path FIRST so game-specific behaviors can be imported
    # This is critical because game behaviors are referenced as "behaviors.module_name"
    game_dir_str = str(game_dir.absolute())
    if game_dir_str not in sys.path:
        sys.path.insert(0, game_dir_str)

    # Set up behavior manager and load behaviors from game's behaviors/ directory
    # (which typically includes a symlink to core behaviors)
    behavior_manager = BehaviorManager()
    game_behaviors_dir = game_dir / "behaviors"
    if game_behaviors_dir.exists():
        modules = behavior_manager.discover_modules(str(game_behaviors_dir))
        behavior_manager.load_modules(modules)

    # Create protocol handler
    handler = LLMProtocolHandler(state, behavior_manager)

    # Create parser with merged vocabulary
    vocab = build_merged_vocabulary(state, behavior_manager)
    parser = Parser.from_vocab(vocab)

    return handler, parser, state


def run_command(handler, parser, command: str) -> Dict[str, Any]:
    """Run a command and return the JSON result."""
    from src.command_utils import parsed_to_json

    parsed = parser.parse_command(command)
    if parsed is None:
        return {"error": f"Could not parse: {command}"}

    # Convert to JSON command
    if parsed.direct_object and not parsed.verb:
        json_cmd = {"type": "command", "action": {"verb": "go", "object": parsed.direct_object}}
    else:
        json_cmd = parsed_to_json(parsed)

    # Execute and return result
    return handler.handle_message(json_cmd)


def print_narration_structure(result: Dict[str, Any], command: str) -> None:
    """Print the narration-relevant parts of the result."""
    print(f"\n{'='*60}")
    print(f"Command: {command}")
    print(f"{'='*60}")

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print(f"Success: {result.get('success')}")
    print(f"Verbosity: {result.get('verbosity')}")

    narration = result.get("narration", {})

    print(f"\nNarration Plan:")
    print(f"  action_verb: {narration.get('action_verb')}")
    print(f"  primary_text: {narration.get('primary_text')}")

    if narration.get("target_state"):
        print(f"  target_state: {narration.get('target_state')}")

    if narration.get("secondary_beats"):
        print(f"  secondary_beats: {narration.get('secondary_beats')}")

    if narration.get("viewpoint"):
        print(f"  viewpoint: {narration.get('viewpoint')}")

    if narration.get("scope"):
        print(f"  scope: {narration.get('scope')}")

    if narration.get("entity_refs"):
        print(f"  entity_refs:")
        for entity_id, entity_data in narration.get("entity_refs", {}).items():
            print(f"    {entity_id}: {entity_data}")

    if narration.get("must_mention"):
        print(f"  must_mention: {narration.get('must_mention')}")

    # Also show raw data for debugging
    if result.get("data"):
        print(f"\nRaw data (for debugging):")
        data = result["data"]
        if "open" in data:
            print(f"  open: {data['open']}")
        if "locked" in data:
            print(f"  locked: {data['locked']}")
        if "name" in data:
            print(f"  name: {data['name']}")


def setup_door_test_state(state) -> None:
    """Programmatically set up state for door testing.

    Moves player to library, gives them the key, ensures door is locked.
    This bypasses the puzzle mechanics to directly test door interactions.
    """
    from src.types import ActorId, LocationId, ItemId

    # Move player to the library
    player = state.actors.get(ActorId("player"))
    if player:
        player.location = LocationId("loc_library")

    # Give player the sanctum key
    sanctum_key = None
    for item in state.items:
        if item.id == "item_sanctum_key":
            sanctum_key = item
            break

    if sanctum_key:
        # Unhide the key and put it in player inventory
        sanctum_key.states["hidden"] = False
        sanctum_key.location = "player"
        if player and "item_sanctum_key" not in player.inventory:
            player.inventory.append(ItemId("item_sanctum_key"))

    # Ensure the sanctum door is locked and closed
    sanctum_door = None
    for item in state.items:
        if item.id == "door_sanctum":
            sanctum_door = item
            break

    if sanctum_door:
        sanctum_door._door_open = False
        sanctum_door._door_locked = True

    print("State configured: Player in library with sanctum key, door locked.")


def analyze_door_scenario(handler, parser) -> None:
    """Run the unlock/open door scenario and analyze the JSON.

    Sets up state programmatically to test the locked sanctum door.
    """
    print("\n" + "#"*60)
    print("# SANCTUM DOOR SCENARIO ANALYSIS")
    print("#"*60)

    # Set up the test state directly
    setup_door_test_state(handler.state)

    # The critical door interactions
    commands = [
        "look",           # Verify we're in library
        "inventory",      # Verify we have the key
        "examine door",   # Door is locked
        "unlock door",    # Should show: open=false, locked=false
        "examine door",   # Now unlocked but still CLOSED
        "open door",      # Should show: open=true, locked=false
        "examine door",   # Now open
        "look",           # Full location view
        "up",             # Go up through door to sanctum
        "look",           # View from sanctum
    ]

    for cmd in commands:
        result = run_command(handler, parser, cmd)
        print_narration_structure(result, cmd)

        # Add extra analysis for the critical door commands
        if cmd in ("unlock door", "open door"):
            narration = result.get("narration", {})
            target_state = narration.get("target_state", {})
            print(f"\n  >>> CRITICAL CHECK for '{cmd}':")
            print(f"      action_verb: {narration.get('action_verb')}")
            print(f"      target_state.open: {target_state.get('open')}")
            print(f"      target_state.locked: {target_state.get('locked')}")
            if cmd == "unlock door" and target_state.get("open") == False:
                print(f"      ✓ Correct: door is still CLOSED after unlock")
            elif cmd == "unlock door" and target_state.get("open") == True:
                print(f"      ✗ ERROR: door shows OPEN after unlock!")
            if cmd == "open door" and target_state.get("open") == True:
                print(f"      ✓ Correct: door is OPEN after open")
            print()


def output_narrator_json(handler, parser, commands: List[str]) -> None:
    """Output the exact JSON that would be sent to the narrator.

    This is useful for understanding what the model sees and for
    designing improved JSON structures.
    """
    print("\n" + "#"*60)
    print("# NARRATOR JSON OUTPUT")
    print("#"*60)

    for cmd in commands:
        result = run_command(handler, parser, cmd)
        print(f"\n--- Command: {cmd} ---")
        print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Evaluate narrator JSON structure")
    parser.add_argument("game_dir", type=Path, help="Path to game directory")
    parser.add_argument("--commands", "-c", nargs="*", help="Commands to run")
    parser.add_argument("--door-scenario", "-d", action="store_true",
                       help="Run the door unlock/open scenario")
    parser.add_argument("--narrator-json", action="store_true",
                       help="Output full JSON that narrator receives for door scenario")
    parser.add_argument("--json", "-j", action="store_true",
                       help="Output full JSON instead of summary")
    args = parser.parse_args()

    if not args.game_dir.exists():
        print(f"Game directory not found: {args.game_dir}")
        sys.exit(1)

    handler, cmd_parser, state = setup_game(args.game_dir)

    if args.door_scenario:
        analyze_door_scenario(handler, cmd_parser)
    elif args.commands:
        for cmd in args.commands:
            result = run_command(handler, cmd_parser, cmd)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print_narration_structure(result, cmd)
    else:
        # Interactive mode
        print("Interactive mode. Enter commands (or 'quit' to exit):")
        print(f"Game: {args.game_dir.name}")
        print()

        while True:
            try:
                cmd = input("> ").strip()
                if cmd.lower() in ("quit", "exit", "q"):
                    break
                if not cmd:
                    continue

                result = run_command(handler, cmd_parser, cmd)
                if args.json:
                    print(json.dumps(result, indent=2))
                else:
                    print_narration_structure(result, cmd)

            except EOFError:
                break
            except KeyboardInterrupt:
                print()
                break


if __name__ == "__main__":
    main()
