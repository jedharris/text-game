#!/usr/bin/env python3
"""MLX-powered text adventure with LLM command parsing and narration.

This front end (xplm-game = "eXtended Parser + LLM + MLX") uses:
- LLM parser (via MLX) to parse natural language commands
- MLX narrator to generate narration
- Shared MLX backend for both parser and narrator (memory efficient)
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

DEFAULT_MODEL_PRESET = "qwen-7b"

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
from src.shared_mlx import SharedMLXBackend
from src.command_utils import parsed_to_json
import json


def resolve_model(model: str) -> str:
    """Resolve a model preset or full path to a HuggingFace model path.

    Args:
        model: Either a preset name (e.g., "qwen-7b") or full HF path

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
    """Run the MLX-powered text adventure with LLM command parsing.

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

    # Configure logging to file if debug enabled
    if debug:
        log_file = Path('xplm_game_debug.log')
        # Clear any existing handlers to avoid console output
        logging.root.handlers = []
        # Add only file handler
        file_handler = logging.FileHandler(str(log_file), mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        )
        logging.root.addHandler(file_handler)
        logging.root.setLevel(logging.DEBUG)
        # Log debug info to file, not console
        logging.info(f"Debug logging enabled - writing to {log_file}")
    else:
        logging.basicConfig(level=logging.WARNING)

    if not game_dir:
        print("Error: game_dir is required")
        print("Usage: xplm-game <game_dir>")
        return 1

    # Initialize game engine
    # Missing/invalid game files indicate authoring errors and should fail loudly
    engine = GameEngine(Path(game_dir))

    # Create shared MLX backend (used by both parser and narrator)
    print(f"Loading MLX model: {model}")
    print("(This may take a moment on first run as the model downloads...)")
    shared_backend = SharedMLXBackend(model)

    # Create LLM parser and adapter using shared backend
    parser, adapter = engine.create_llm_parser(shared_backend)

    # Create narrator using shared backend (saves ~4-6GB memory)
    # Missing narrator protocol or files indicate authoring errors and should fail loudly
    narrator = engine.create_mlx_narrator(
        model=model,  # Only used for logging, actual model comes from shared_backend
        show_traits=show_traits,
        temperature=temperature,
        max_tokens=max_tokens,
        shared_backend=shared_backend
    )

    # Show title and opening
    print(f"\n{engine.game_state.metadata.title}")
    print("=" * len(engine.game_state.metadata.title))
    print(f"[Using MLX model: {model}]")
    print("[LLM command parsing enabled]")
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

            # Build context for LLM parser
            context = engine.build_parser_context()
            logging.debug(f"Context: {context}")

            # Parse command using LLM parser
            parser_output = parser.parse_command(player_input, context)
            logging.debug(f"Parser output: {parser_output}")

            # Convert to ParsedCommand
            parsed_command = adapter.to_parsed_command(parser_output, player_input)

            if parsed_command is None:
                print("\nI couldn't understand that command. Try rephrasing?")
                continue

            # Convert ParsedCommand to JSON message format
            json_cmd = parsed_to_json(parsed_command)
            logging.debug(f"Parsed command: {parsed_command}")
            logging.debug(f"JSON command: {json_cmd}")

            # Execute command via game engine
            # Multi-item take is now handled inside the protocol handler
            result = engine.json_handler.handle_message(json_cmd)
            logging.debug(f"Result keys: {result.keys()}")
            logging.debug(f"Result success: {result.get('success')}")
            logging.debug(f"Result verbosity: {result.get('verbosity')}")
            if 'narration' in result:
                logging.debug(f"Narration keys: {result['narration'].keys()}")

            # Print traits if enabled
            if show_traits:
                narrator._print_traits(result)

            # Build narration dict from result
            narration_dict = {
                "success": result.get("success", True),
                "verbosity": result.get("verbosity", "full"),
            }
            if "narration" in result:
                narration_dict.update(result["narration"])

            logging.debug(f"Narration dict: {json.dumps(narration_dict, indent=2)}")

            # Get narrative from LLM
            narration_input = f"Narrate this result:\n{json.dumps(narration_dict, indent=2)}"
            narrative = narrator._call_llm(narration_input)
            print(f"\n{narrative}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break

    return 0


def cli_main() -> None:
    """Entry point for console script."""
    preset_names = ", ".join(MODEL_PRESETS.keys())

    parser = argparse.ArgumentParser(
        description='MLX-powered text adventure with LLM command parsing and narration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Model presets: {preset_names}\n"
               f"Use --list-models to see full paths."
    )
    parser.add_argument('game_dir', nargs='?',
                        help='Game name (from examples/) or full path to game directory')
    parser.add_argument('--no-debug', '--nd', action='store_true',
                        help='Disable debug logging (debug is on by default)')
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
        debug=not args.no_debug,  # Debug on by default, disabled with --no-debug
        show_traits=args.show_traits,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens
    ))


if __name__ == "__main__":
    cli_main()
