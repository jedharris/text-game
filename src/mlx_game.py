#!/usr/bin/env python3
"""MLX-LM powered text adventure game.

This script provides a natural language interface to the text adventure game,
using Apple's MLX framework for native Metal GPU acceleration on Apple Silicon.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Model presets for easy switching
# Format: "family-size" -> full HuggingFace path
MODEL_PRESETS = {
    # Llama 3.2 (3B max for 3.2 series)
    "llama-3b": "mlx-community/Llama-3.2-3B-Instruct-4bit",
    # Llama 3.1 8B (3.3 only comes in 70B)
    "llama-8b": "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit",
    # Mistral
    "mistral-7b": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
    # Qwen 2.5
    "qwen-3b": "mlx-community/Qwen2.5-3B-Instruct-4bit",
    "qwen-7b": "mlx-community/Qwen2.5-7B-Instruct-4bit",
}

DEFAULT_MODEL_PRESET = "llama-3b"

# Set HuggingFace cache location before any HF imports
# This ensures MLX-LM finds cached models in the user's custom location
_hf_cache = Path.home() / "jed.cache" / "huggingface"
if _hf_cache.exists() and not os.environ.get("HF_HOME"):
    os.environ["HF_HOME"] = str(_hf_cache)

# Add project root to path when run as script (not when imported as module)
if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.game_engine import GameEngine


def resolve_model(model: str) -> str:
    """Resolve a model preset or full path to a HuggingFace model path.

    Args:
        model: Either a preset name (e.g., "llama-3b") or full HF path

    Returns:
        Full HuggingFace model path
    """
    if model in MODEL_PRESETS:
        return MODEL_PRESETS[model]
    return model


def list_models() -> None:
    """Print available model presets."""
    print("Available model presets:")
    print()
    for preset, path in MODEL_PRESETS.items():
        print(f"  {preset:12s}  {path}")
    print()
    print("You can also use any full HuggingFace model path.")


def main(game_dir: str | None = None,
         debug: bool = False,
         show_traits: bool = False,
         model: str = DEFAULT_MODEL_PRESET,
         temperature: float = 0.8,
         max_tokens: int = 300) -> int:
    """Run the MLX-powered text adventure.

    Args:
        game_dir: Path to game directory containing game_state.json (required)
        debug: If True, enable debug logging
        show_traits: If True, print llm_context traits before each LLM narration
        model: Model preset name or full MLX model path
        temperature: Temperature for generation (0.0-2.0)
        max_tokens: Max tokens to generate

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Resolve model preset to full path
    model = resolve_model(model)
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
    # Missing/invalid game files indicate authoring errors and should fail loudly
    engine = GameEngine(Path(game_dir))

    # Create narrator using MLX
    # Missing narrator protocol or files indicate authoring errors and should fail loudly
    print(f"Loading MLX model: {model}")
    print("(This may take a moment on first run as the model downloads...)")
    narrator = engine.create_mlx_narrator(
        model=model,
        show_traits=show_traits,
        temperature=temperature,
        max_tokens=max_tokens
    )

    # Show title and opening
    print(f"\n{engine.game_state.metadata.title}")
    print("=" * len(engine.game_state.metadata.title))
    print(f"[Using MLX model: {model}]")
    print()

    # Errors in opening narration indicate authoring/coding bugs and should fail loudly
    opening = narrator.get_opening()
    print(opening)

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

            # Errors processing turns indicate bugs in behaviors/handlers and should fail loudly
            response = narrator.process_turn(player_input)
            print(f"\n{response}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break

    return 0


def cli_main() -> None:
    """Entry point for console script."""
    preset_names = ", ".join(MODEL_PRESETS.keys())

    parser = argparse.ArgumentParser(
        description='MLX-LM powered text adventure game',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Model presets: {preset_names}\n"
               f"Use --list-models to see full paths."
    )
    parser.add_argument('game_dir', nargs='?',
                        help='Game name (from examples/) or full path to game directory')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--show-traits', '-t', action='store_true',
                        help='Print llm_context traits before each LLM narration')
    parser.add_argument('--model', '-m', default=DEFAULT_MODEL_PRESET,
                        help=f'Model preset or full HF path (default: {DEFAULT_MODEL_PRESET})')
    parser.add_argument('--list-models', '-l', action='store_true',
                        help='List available model presets and exit')
    parser.add_argument('--temperature', type=float, default=0.8,
                        help='Temperature for generation (default: 0.8)')
    parser.add_argument('--max-tokens', type=int, default=300,
                        help='Max tokens to generate (default: 300)')
    args = parser.parse_args()

    # Handle --list-models
    if args.list_models:
        list_models()
        sys.exit(0)

    # Require game_dir if not listing models
    if not args.game_dir:
        parser.error("game_dir is required")

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
