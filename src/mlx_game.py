#!/usr/bin/env python3
"""MLX-LM powered text adventure game.

This script provides a natural language interface to the text adventure game,
using Apple's MLX framework for native Metal GPU acceleration on Apple Silicon.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path when run as script (not when imported as module)
if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.game_engine import GameEngine


def main(game_dir: str | None = None,
         debug: bool = False,
         show_traits: bool = False,
         model: str = "mlx-community/Llama-3.2-3B-Instruct-4bit",
         temperature: float = 0.8,
         max_tokens: int = 300) -> int:
    """Run the MLX-powered text adventure.

    Args:
        game_dir: Path to game directory containing game_state.json (required)
        debug: If True, enable debug logging
        show_traits: If True, print llm_context traits before each LLM narration
        model: MLX model path (HuggingFace format)
        temperature: Temperature for generation (0.0-2.0)
        max_tokens: Max tokens to generate

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Configure logging
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='[DEBUG] %(name)s: %(message)s'
        )
    else:
        logging.basicConfig(level=logging.WARNING)

    if not game_dir:
        print("Error: game_dir is required")
        print("Usage: mlx_game <game_dir>")
        return 1

    # Initialize game engine
    try:
        engine = GameEngine(Path(game_dir))
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return 1

    # Create narrator using MLX
    print(f"Loading MLX model: {model}")
    print("(This may take a moment on first run as the model downloads...)")
    try:
        narrator = engine.create_mlx_narrator(
            model=model,
            show_traits=show_traits,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except ImportError as e:
        print(f"Error: {e}")
        print("\nMLX-LM requires:")
        print("  - macOS 13.5+")
        print("  - Apple Silicon (M1/M2/M3/M4)")
        print("  - pip install mlx-lm")
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error loading model: {e}")
        return 1

    # Show title and opening
    print(f"\n{engine.game_state.metadata.title}")
    print("=" * len(engine.game_state.metadata.title))
    print(f"[Using MLX model: {model}]")
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


def cli_main() -> None:
    """Entry point for console script."""
    parser = argparse.ArgumentParser(description='MLX-LM powered text adventure game')
    parser.add_argument('game_dir', help='Game name (from examples/) or full path to game directory')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--show-traits', '-t', action='store_true',
                        help='Print llm_context traits before each LLM narration')
    parser.add_argument('--model', '-m', default='mlx-community/Llama-3.2-3B-Instruct-4bit',
                        help='MLX model path (default: mlx-community/Llama-3.2-3B-Instruct-4bit)')
    parser.add_argument('--temperature', type=float, default=0.8,
                        help='Temperature for generation (default: 0.8)')
    parser.add_argument('--max-tokens', type=int, default=300,
                        help='Max tokens to generate (default: 300)')
    args = parser.parse_args()

    # If it's just a name (no path separators), prefix with examples/
    if '/' not in args.game_dir and not Path(args.game_dir).is_absolute():
        game_path = Path('examples') / args.game_dir
    else:
        game_path = Path(args.game_dir)

    sys.exit(main(
        game_dir=str(game_path),
        debug=args.debug,
        show_traits=args.show_traits,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens
    ))


if __name__ == "__main__":
    cli_main()
