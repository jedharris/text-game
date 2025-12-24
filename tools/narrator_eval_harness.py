#!/usr/bin/env python3
"""
Narrator Evaluation Harness

Captures JSON sent to the narrator and prose returned, then evaluates
compliance with expected characteristics.

Usage:
    python tools/narrator_eval_harness.py <game_dir> [--output eval_results.json]

This runs a series of test scenarios and evaluates narrator compliance.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class EvalCriteria:
    """Criteria for evaluating a narration."""
    must_contain: List[str] = field(default_factory=list)
    must_not_contain: List[str] = field(default_factory=list)
    max_sentences: Optional[int] = None
    min_sentences: Optional[int] = None


@dataclass
class EvalResult:
    """Result of evaluating a single narration."""
    scenario: str
    command: str
    json_sent: Dict[str, Any]
    narration: str
    criteria: EvalCriteria

    # Evaluation results
    missing_required: List[str] = field(default_factory=list)
    unwanted_present: List[str] = field(default_factory=list)
    sentence_count: int = 0
    passed: bool = False
    notes: str = ""

    def evaluate(self) -> None:
        """Run evaluation and populate result fields."""
        narration_lower = self.narration.lower()

        # Check must_contain
        for phrase in self.criteria.must_contain:
            if phrase.lower() not in narration_lower:
                self.missing_required.append(phrase)

        # Check must_not_contain
        for phrase in self.criteria.must_not_contain:
            if phrase.lower() in narration_lower:
                self.unwanted_present.append(phrase)

        # Count sentences (rough)
        self.sentence_count = len(re.findall(r'[.!?]+', self.narration))

        # Determine pass/fail
        self.passed = (
            len(self.missing_required) == 0 and
            len(self.unwanted_present) == 0
        )

        if self.criteria.max_sentences and self.sentence_count > self.criteria.max_sentences:
            self.passed = False
            self.notes += f"Too many sentences ({self.sentence_count} > {self.criteria.max_sentences}). "

        if self.criteria.min_sentences and self.sentence_count < self.criteria.min_sentences:
            self.passed = False
            self.notes += f"Too few sentences ({self.sentence_count} < {self.criteria.min_sentences}). "


@dataclass
class TestScenario:
    """A test scenario with setup commands and evaluation criteria."""
    name: str
    description: str
    setup_commands: List[str]  # Commands to run before the test command
    test_command: str
    criteria: EvalCriteria


# =============================================================================
# GAME-SPECIFIC TEST SCENARIOS
# =============================================================================
# Each game can have its own scenarios. Scenarios are keyed by game directory name.
# The harness will automatically select the appropriate scenarios based on the
# game being tested.

# Scenarios for extended_game (has door_sanctum in loc_library)
EXTENDED_GAME_DOOR_SCENARIOS = [
    TestScenario(
        name="unlock_closed_door",
        description="Unlock a locked door - should NOT describe opening or what's beyond",
        setup_commands=[
            "go north",  # Enter tower from garden
            "go up",     # Go to library
        ],
        test_command="unlock door",
        criteria=EvalCriteria(
            must_contain=["unlock", "door"],
            must_not_contain=[
                "open", "opens", "opened", "opening", "swings",
                "step", "enter", "inside", "through",
                "beyond", "reveals", "see",
                "room", "chamber", "sanctum", "space",
                "air", "smell", "scent", "light spills",
                "walk", "pass"
            ],
            max_sentences=4
        )
    ),
    TestScenario(
        name="open_unlocked_door",
        description="Open a door that was just unlocked - NOW can describe what's beyond",
        setup_commands=[
            "go north",
            "go up",
            "unlock door"
        ],
        test_command="open door",
        criteria=EvalCriteria(
            must_contain=["open", "door"],
            must_not_contain=[
                "unlock", "key", "lock clicks"  # Don't re-describe unlocking
            ],
            # CAN mention what's beyond now
            max_sentences=5
        )
    ),
    TestScenario(
        name="examine_closed_door",
        description="Examine a closed door - describe the door, not what's beyond",
        setup_commands=[
            "go north",
            "go up"
        ],
        test_command="examine door",
        criteria=EvalCriteria(
            must_contain=["door"],
            must_not_contain=[
                "beyond", "inside", "through",
                "room behind", "chamber beyond",
                "step", "enter", "walk"
            ]
        )
    ),
]

# Map game directory names to their scenarios
GAME_SCENARIOS: Dict[str, List[TestScenario]] = {
    "extended_game": EXTENDED_GAME_DOOR_SCENARIOS,
    # Add other games here as scenarios are created:
    # "big_game": BIG_GAME_SCENARIOS,
    # "spatial_game": SPATIAL_GAME_SCENARIOS,
}

# Default scenarios (used when game has no specific scenarios)
DEFAULT_SCENARIOS: List[TestScenario] = []


def get_scenarios_for_game(game_dir: Path) -> List[TestScenario]:
    """Get the appropriate test scenarios for a game.

    Args:
        game_dir: Path to the game directory

    Returns:
        List of TestScenario objects for this game, or empty list if none defined.
    """
    game_name = game_dir.name
    scenarios = GAME_SCENARIOS.get(game_name, DEFAULT_SCENARIOS)

    if not scenarios:
        print(f"NOTE: No test scenarios defined for '{game_name}'.", file=sys.stderr)
        print(f"      Available games with scenarios: {list(GAME_SCENARIOS.keys())}", file=sys.stderr)

    return scenarios


class NarratorEvalHarness:
    """Harness for evaluating narrator output."""

    def __init__(self, game_dir: Path):
        """
        Initialize the evaluation harness.

        Args:
            game_dir: Path to game directory
        """
        self.game_dir = game_dir
        self.results: List[EvalResult] = []
        self.captured_json: List[Dict[str, Any]] = []

    def setup_game(self) -> None:
        """Set up game state and narrator."""
        from src.state_manager import load_game_state
        from src.llm_protocol import LLMProtocolHandler
        from src.behavior_manager import BehaviorManager

        # Load game state
        state_file = self.game_dir / "game_state.json"
        self.state = load_game_state(state_file)

        # Add game directory to sys.path FIRST so game-specific behaviors can be imported
        # This is critical because game behaviors are referenced as "behaviors.module_name"
        game_dir_str = str(self.game_dir.absolute())
        if game_dir_str not in sys.path:
            sys.path.insert(0, game_dir_str)

        # Set up behavior manager and load behaviors from game's behaviors/ directory
        # (which typically includes a symlink to core behaviors)
        self.behavior_manager = BehaviorManager()
        game_behaviors_dir = self.game_dir / "behaviors"
        if game_behaviors_dir.exists():
            modules = self.behavior_manager.discover_modules(str(game_behaviors_dir))
            self.behavior_manager.load_modules(modules)

        # Create protocol handler
        self.handler = LLMProtocolHandler(self.state, self.behavior_manager)

        # Create narrator based on type
        self._setup_narrator()

    def _setup_narrator(self) -> None:
        """Set up the MLX narrator."""
        from src.mlx_narrator import MLXNarrator

        prompt_file = self.game_dir / "narrator_style.txt"
        self.narrator = MLXNarrator(
            json_handler=self.handler,
            prompt_file=prompt_file,
            behavior_manager=self.behavior_manager
        )

    def run_command(self, command: str) -> tuple[Dict[str, Any], str]:
        """
        Run a command and capture the JSON sent to narrator.

        Returns:
            Tuple of (json_sent_to_narrator, narration_text)
        """
        # We need to intercept the JSON before it goes to the narrator
        # The cleanest way is to call the handler directly, then narrate

        from src.parser import Parser
        from src.command_utils import parsed_to_json

        # Parse command
        parsed = self.narrator.parser.parse_command(command)
        if parsed is None:
            return {}, f"Could not parse: {command}"

        # Convert to JSON command
        if parsed.direct_object and not parsed.verb:
            json_cmd = {"type": "command", "action": {"verb": "go", "object": parsed.direct_object}}
        else:
            json_cmd = parsed_to_json(parsed)

        # Execute via handler - this returns the NarrationResult
        result = self.handler.handle_message(json_cmd)

        # Build narration dict - only include fields needed for narration
        # (matches the filtering in llm_narrator.py)
        narration_dict: Dict[str, Any] = {
            "success": result.get("success", True),
            "verbosity": result.get("verbosity", "full"),
        }
        if "narration" in result:
            narration_dict.update(result["narration"])

        # Capture the JSON that would be sent to narrator
        self.captured_json.append(narration_dict)

        # Get narration
        narration = self.narrator._call_llm(
            f"Narrate this result:\n{json.dumps(narration_dict, indent=2)}"
        )

        return narration_dict, narration

    def run_scenario(self, scenario: TestScenario) -> EvalResult:
        """Run a single test scenario and evaluate."""
        # Reset game state for each scenario
        self.setup_game()

        # Run setup commands (don't evaluate these)
        for cmd in scenario.setup_commands:
            try:
                self.run_command(cmd)
            except Exception as e:
                print(f"  Setup command '{cmd}' failed: {e}", file=sys.stderr)

        # Run test command and capture
        json_sent, narration = self.run_command(scenario.test_command)

        # Create and run evaluation
        result = EvalResult(
            scenario=scenario.name,
            command=scenario.test_command,
            json_sent=json_sent,
            narration=narration,
            criteria=scenario.criteria
        )
        result.evaluate()

        return result

    def run_all_scenarios(self, scenarios: List[TestScenario]) -> List[EvalResult]:
        """Run all test scenarios."""
        results = []

        for scenario in scenarios:
            print(f"\nRunning: {scenario.name}")
            print(f"  Description: {scenario.description}")
            print(f"  Command: {scenario.test_command}")

            try:
                result = self.run_scenario(scenario)
                results.append(result)

                print(f"  Narration: {result.narration[:100]}...")
                print(f"  Passed: {result.passed}")
                if result.missing_required:
                    print(f"  Missing: {result.missing_required}")
                if result.unwanted_present:
                    print(f"  Unwanted: {result.unwanted_present}")
                if result.notes:
                    print(f"  Notes: {result.notes}")

            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback
                traceback.print_exc()

        return results

    def summarize(self, results: List[EvalResult]) -> Dict[str, Any]:
        """Generate summary statistics."""
        total = len(results)
        passed = sum(1 for r in results if r.passed)

        hallucination_count = sum(
            len(r.unwanted_present) for r in results
        )
        missing_count = sum(
            len(r.missing_required) for r in results
        )

        return {
            "total_scenarios": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "total_hallucinations": hallucination_count,
            "total_missing_required": missing_count,
        }


def main():
    parser = argparse.ArgumentParser(description="Evaluate narrator compliance")
    parser.add_argument("game_dir", type=Path, help="Path to game directory")
    parser.add_argument("--output", "-o", type=Path, default=Path("eval_results.json"),
                       help="Output file for results")
    args = parser.parse_args()

    if not args.game_dir.exists():
        print(f"Game directory not found: {args.game_dir}")
        sys.exit(1)

    print(f"Evaluating narrator for: {args.game_dir}", file=sys.stderr)

    # Get scenarios for this specific game
    scenarios = get_scenarios_for_game(args.game_dir)
    if not scenarios:
        print("No scenarios to run. Exiting.", file=sys.stderr)
        sys.exit(0)

    harness = NarratorEvalHarness(args.game_dir)

    results = harness.run_all_scenarios(scenarios)
    summary = harness.summarize(results)

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total scenarios: {summary['total_scenarios']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass rate: {summary['pass_rate']:.1%}")
    print(f"Total hallucinations: {summary['total_hallucinations']}")
    print(f"Total missing required: {summary['total_missing_required']}")

    # Save results
    output_data = {
        "summary": summary,
        "results": [
            {
                "scenario": r.scenario,
                "command": r.command,
                "narration": r.narration,
                "passed": r.passed,
                "missing_required": r.missing_required,
                "unwanted_present": r.unwanted_present,
                "sentence_count": r.sentence_count,
                "notes": r.notes,
                "json_sent": r.json_sent
            }
            for r in results
        ]
    }

    with open(args.output, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nDetailed results saved to: {args.output}")


if __name__ == "__main__":
    main()
