#!/usr/bin/env python3
"""LLM-powered text adventure game.

This script provides a natural language interface to the text adventure game,
using an LLM to translate player input into game commands and narrate results.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.state_manager import load_game_state
from src.json_protocol import JSONProtocolHandler
from src.llm_narrator import LLMNarrator
from src.behavior_manager import BehaviorManager

# Default game state file location
DEFAULT_STATE_FILE = Path(__file__).parent.parent / "examples" / "simple_game_state.json"


def main():
    """Run the LLM-powered text adventure."""
    # Load API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY=sk-ant-...")
        return 1

    # Load game state from examples directory
    if not DEFAULT_STATE_FILE.exists():
        print(f"Error: Game state file not found: {DEFAULT_STATE_FILE}")
        return 1

    state = load_game_state(str(DEFAULT_STATE_FILE))

    # Create behavior manager and load modules
    behavior_manager = BehaviorManager()
    behaviors_dir = project_root / "behaviors"
    modules = behavior_manager.discover_modules(str(behaviors_dir))
    behavior_manager.load_modules(modules)

    # Create JSON handler with behavior manager
    json_handler = JSONProtocolHandler(state, behavior_manager=behavior_manager)

    # Create narrator
    narrator = LLMNarrator(api_key, json_handler)

    # Show title and opening
    print(f"\n{state.metadata.title}")
    print("=" * len(state.metadata.title))
    print()

    try:
        opening = narrator.get_opening()
        print(opening)
    except Exception as e:
        print(f"[Error getting opening: {e}]")
        return 1

    # Game loop
    print("\n(Type 'quit' to exit)")

    while True:
        try:
            player_input = input("\n> ").strip()

            if not player_input:
                continue

            if player_input.lower() in ("quit", "exit", "q"):
                print("\nThanks for playing!")
                break

            response = narrator.process_turn(player_input)
            print(f"\n{response}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n[Error: {e}]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
