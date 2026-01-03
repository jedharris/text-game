#!/usr/bin/env python3
"""LLM-augmented walkthrough testing tool.

Tests full end-to-end narration with actual LLM, generating transcripts
for review by humans or large models.

Usage:
    python tools/llm_walkthrough.py <game_dir> --file walkthrough.txt --model <model>

Examples:
    python tools/llm_walkthrough.py examples/spatial_game \\
        --file walkthroughs/narration/phase1.txt \\
        --model mlx-community/Qwen2.5-7B-Instruct-4bit

    python tools/llm_walkthrough.py examples/spatial_game \\
        --file walkthroughs/narration/phase1.txt \\
        --model mlx-community/Qwen2.5-7B-Instruct-4bit \\
        --save-transcript phase1_output.log

Note:
    - Requires MLX-LM (pip install mlx-lm)
    - Requires macOS 13.5+ and Apple Silicon (M1/M2/M3/M4)
    - Slower than json_walkthrough.py (~1-2s per turn)
    - Non-deterministic (LLM variability)
    - For manual review or large model analysis
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.game_engine import GameEngine


def format_transcript(results: List[Dict[str, Any]], opening: str) -> str:
    """Format results into a readable transcript.

    Args:
        results: List of turn results
        opening: Opening narration

    Returns:
        Formatted transcript string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("LLM WALKTHROUGH TRANSCRIPT")
    lines.append("=" * 70)
    lines.append("")
    lines.append("OPENING:")
    lines.append("-" * 70)
    lines.append(opening)
    lines.append("")

    for i, turn in enumerate(results, 1):
        lines.append("=" * 70)
        lines.append(f"TURN {i}: {turn['input']}")
        lines.append("-" * 70)
        lines.append("")
        lines.append("PROSE:")
        lines.append(turn['prose'])
        lines.append("")

    lines.append("=" * 70)
    lines.append("END OF TRANSCRIPT")
    lines.append("=" * 70)

    return "\n".join(lines)


def run_llm_walkthrough(
    game_dir: Path,
    commands: List[str],
    model: str,
    save_transcript: Path | None = None,
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """Run commands through MLX narrator and capture results.

    Args:
        game_dir: Path to game directory
        commands: List of command strings
        model: MLX model path
        save_transcript: Optional path to save transcript
        verbose: Show additional debug info

    Returns:
        List of turn results
    """
    print(f"Loading game from {game_dir}...")
    engine = GameEngine(game_dir)

    print(f"Loading MLX narrator with model: {model}")
    print("(This may take ~30 seconds on first load...)")

    narrator = engine.create_mlx_narrator(
        model=model,
        temperature=0.0,  # Use deterministic mode for testing
        show_traits=verbose
    )

    print("\nGenerating opening narration...")
    opening = narrator.get_opening()

    print("=" * 70)
    print("OPENING:")
    print("-" * 70)
    print(opening)
    print()

    results = []

    # Process each command
    for i, cmd in enumerate(commands, 1):
        cmd = cmd.strip()
        if not cmd or cmd.startswith("#"):
            continue

        print("=" * 70)
        print(f"TURN {i}: {cmd}")
        print("-" * 70)

        response = narrator.process_turn(cmd)

        print("\nPROSE:")
        print(response)
        print()

        results.append({
            "input": cmd,
            "prose": response
        })

    # Save transcript if requested
    if save_transcript:
        transcript = format_transcript(results, opening)
        save_transcript.write_text(transcript, encoding='utf-8')
        print(f"\n💾 Transcript saved to {save_transcript}")

    return results


def main():
    argparser = argparse.ArgumentParser(
        description="Run LLM-augmented walkthrough for narration quality testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    argparser.add_argument("game_dir", help="Path to game directory")
    argparser.add_argument("--file", "-f", required=True,
                          help="Walkthrough file with commands")
    argparser.add_argument("--model", "-m",
                          default="mlx-community/Qwen2.5-7B-Instruct-4bit",
                          help="MLX model to use (default: Qwen2.5-7B-Instruct-4bit)")
    argparser.add_argument("--save-transcript", metavar="FILE",
                          help="Save transcript to FILE")
    argparser.add_argument("--verbose", "-v", action="store_true",
                          help="Show debug info (traits, etc.)")

    args = argparser.parse_args()

    # Load commands from file
    with open(args.file, "r") as f:
        commands = [line.rstrip() for line in f
                   if line.strip() and not line.strip().startswith("#")]

    print(f"Running {len(commands)} commands through LLM narrator...\n")

    try:
        results = run_llm_walkthrough(
            Path(args.game_dir),
            commands,
            args.model,
            Path(args.save_transcript) if args.save_transcript else None,
            args.verbose
        )

        print("=" * 70)
        print(f"SUMMARY: {len(results)} turns completed")
        print("=" * 70)

        return 0

    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nMLX-LM is required for LLM walkthrough testing.", file=sys.stderr)
        print("Install with: pip install mlx-lm", file=sys.stderr)
        print("Note: Requires macOS 13.5+ and Apple Silicon (M1/M2/M3/M4)", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
