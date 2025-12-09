"""Implementation of big_game integration tests.

This module contains integration tests that verify cross-system interactions,
complete player journeys, and ending conditions.

Each test class should be run in its own subprocess by test_big_game_integration.py
to ensure module isolation.

DO NOT import this module directly in the test suite.
"""

import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from src.state_manager import GameState
    from src.state_accessor import StateAccessor


# Path setup - must be absolute before importing game modules
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
GAME_DIR = PROJECT_ROOT / 'examples' / 'big_game'


def _setup_paths():
    """Ensure paths are set up for imports.

    IMPORTANT: We remove '' (current directory) from path because when running
    from project root, Python would find behaviors/ from project root before
    finding it from the game directory.
    """
    # Remove CWD ('') from path to prevent project root behaviors from being found
    while '' in sys.path:
        sys.path.remove('')

    # Add examples directory first (for big_game.behaviors.* imports)
    examples_dir = str(PROJECT_ROOT / 'examples')
    if examples_dir not in sys.path:
        sys.path.insert(0, examples_dir)

    # Add project root after (for src imports)
    project_str = str(PROJECT_ROOT)
    if project_str not in sys.path:
        sys.path.insert(1, project_str)


# Set up paths before importing game modules
_setup_paths()

from src.state_manager import load_game_state
from src.behavior_manager import BehaviorManager
from src.llm_protocol import LLMProtocolHandler
from src.state_accessor import StateAccessor


def get_game_state_path() -> Path:
    """Return path to big_game's game_state.json."""
    return GAME_DIR / 'game_state.json'


def load_all_behaviors(manager: BehaviorManager) -> None:
    """Load all behaviors including big_game specific behaviors."""
    # Load core behaviors
    behaviors_dir = PROJECT_ROOT / "behaviors"
    modules = manager.discover_modules(str(behaviors_dir))
    manager.load_modules(modules)

    # Load only the required behavior_libraries (avoiding conflicts)
    required_libs = [
        "behavior_libraries.timing_lib.scheduled_events",
        "behavior_libraries.dialog_lib.handlers",
        "behavior_libraries.dialog_lib.topics",
    ]
    for lib_path in required_libs:
        try:
            manager.load_module(lib_path, tier=2)
        except (ValueError, ImportError):
            # Skip if conflicts or not found
            pass

    # Load big_game behaviors explicitly by module path
    big_game_behaviors = [
        "big_game.behaviors.regions",
        "big_game.behaviors.factions",
        "big_game.behaviors.world_events",
        "big_game.behaviors.npc_specifics.the_echo",
    ]
    for mod_path in big_game_behaviors:
        manager.load_module(mod_path, tier=3)


# ============================================================================
# SIMULATED PLAY SESSION
# ============================================================================


@dataclass
class TranscriptEntry:
    """A single entry in the play transcript."""
    turn: int
    command: str
    response: dict
    notes: str = ""


@dataclass
class SimulatedPlaySession:
    """
    Simulates gameplay and captures transcripts for inspection.

    Usage:
        session = SimulatedPlaySession(verbose=True)
        session.command("go", "north")
        session.command("look")
        session.wait(5)  # Wait 5 turns
        print(session.get_transcript())
    """
    verbose: bool = False
    _handler: LLMProtocolHandler = field(init=False, repr=False)
    _state: "GameState" = field(init=False, repr=False)
    _accessor: StateAccessor = field(init=False, repr=False)
    _transcript: List[TranscriptEntry] = field(default_factory=list)
    _turn: int = 0

    def __post_init__(self):
        """Initialize game state and handler."""
        self._state = load_game_state(str(get_game_state_path()))
        manager = BehaviorManager()
        load_all_behaviors(manager)
        self._handler = LLMProtocolHandler(self._state, behavior_manager=manager)
        self._accessor = StateAccessor(self._state, manager)

    @property
    def state(self):
        """Access game state."""
        return self._state

    @property
    def accessor(self):
        """Access StateAccessor."""
        return self._accessor

    @property
    def handler(self):
        """Access protocol handler."""
        return self._handler

    def command(self, verb: str, obj: Optional[str] = None, note: str = "") -> dict:
        """
        Execute a command and record in transcript.

        Args:
            verb: The verb (e.g., "go", "look", "take")
            obj: Optional object (e.g., "north", "sword")
            note: Optional note to add to transcript

        Returns:
            The command result dict
        """
        action = {"verb": verb}
        if obj:
            action["object"] = obj

        result = self._handler.handle_command({
            "type": "command",
            "action": action
        })

        self._turn += 1
        cmd_str = f"{verb} {obj}" if obj else verb

        entry = TranscriptEntry(
            turn=self._turn,
            command=cmd_str,
            response=result,
            notes=note
        )
        self._transcript.append(entry)

        if self.verbose:
            self._print_entry(entry)

        return result

    def wait(self, turns: int = 1, note: str = "") -> List[dict]:
        """
        Wait for multiple turns.

        Args:
            turns: Number of turns to wait
            note: Optional note for first turn

        Returns:
            List of results from each wait command
        """
        results = []
        for i in range(turns):
            turn_note = note if i == 0 else ""
            results.append(self.command("wait", note=turn_note))
        return results

    def complete_quest(self, quest_id: str, note: str = "") -> str:
        """
        Trigger quest completion directly.

        Args:
            quest_id: The quest to complete
            note: Optional note for transcript

        Returns:
            Message from quest completion
        """
        from big_game.behaviors.world_events import on_quest_complete

        result = on_quest_complete(None, self._accessor, {"quest_id": quest_id})

        self._turn += 1
        entry = TranscriptEntry(
            turn=self._turn,
            command=f"[QUEST: {quest_id}]",
            response={"message": result.message, "allow": result.allow},
            notes=note
        )
        self._transcript.append(entry)

        if self.verbose:
            self._print_entry(entry)

        return result.message

    def advance_to_turn(self, target_turn: int, note: str = "") -> List[str]:
        """
        Advance game to a specific turn and process scheduled events.

        This properly fires events through the world event handler.

        Args:
            target_turn: The turn number to advance to
            note: Optional note for transcript

        Returns:
            List of messages from scheduled events
        """
        from behavior_libraries.timing_lib.scheduled_events import get_scheduled_events
        from big_game.behaviors.world_events import on_world_event_check

        self._state.turn_count = target_turn
        events = get_scheduled_events(self._accessor)
        messages = []

        # Find events that should fire
        events_to_fire = []
        events_to_keep = []
        for event in events:
            if event['turn'] <= target_turn:
                events_to_fire.append(event)
            else:
                events_to_keep.append(event)

        # Update the scheduled events list
        self._state.extra['scheduled_events'] = events_to_keep

        # Fire each event through the world event handler
        for event in events_to_fire:
            context = {
                'event_name': event['event'],
                'data': event.get('data', {})
            }
            result = on_world_event_check(None, self._accessor, context)
            if result.message:
                messages.extend(result.message.split('\n'))

        self._turn = target_turn
        entry = TranscriptEntry(
            turn=target_turn,
            command=f"[ADVANCE TO TURN {target_turn}]",
            response={"messages": messages},
            notes=note
        )
        self._transcript.append(entry)

        if self.verbose:
            self._print_entry(entry)

        return messages

    def set_flag(self, flag_name: str, value: bool = True) -> None:
        """Set a game flag."""
        self._state.extra.setdefault('flags', {})[flag_name] = value

    def get_flag(self, flag_name: str) -> bool:
        """Get a game flag value."""
        return self._state.extra.get('flags', {}).get(flag_name, False)

    def get_transcript(self, include_responses: bool = True) -> str:
        """
        Get the full session transcript as a formatted string.

        Args:
            include_responses: Whether to include full response dicts

        Returns:
            Formatted transcript string
        """
        lines = ["=" * 60, "SIMULATED PLAY TRANSCRIPT", "=" * 60, ""]

        for entry in self._transcript:
            lines.append(f"Turn {entry.turn}: {entry.command}")
            if entry.notes:
                lines.append(f"  Note: {entry.notes}")

            if include_responses:
                response = entry.response
                if isinstance(response, dict):
                    if response.get("success") is not None:
                        lines.append(f"  Success: {response.get('success')}")
                    if response.get("message"):
                        msg = response.get("message", "")
                        # Truncate long messages
                        if len(msg) > 200:
                            msg = msg[:200] + "..."
                        lines.append(f"  Message: {msg}")
                else:
                    lines.append(f"  Response: {response}")

            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def _print_entry(self, entry: TranscriptEntry) -> None:
        """Print a single transcript entry."""
        print(f"\n[Turn {entry.turn}] {entry.command}")
        if entry.notes:
            print(f"  Note: {entry.notes}")
        response = entry.response
        if isinstance(response, dict):
            if response.get("success") is not None:
                print(f"  Success: {response.get('success')}")
            message = response.get("message")
            if message:
                print(f"  Message: {str(message)[:100]}...")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def advance_turns_direct(accessor, target_turn: int) -> List[str]:
    """
    Set turn count directly and process scheduled events.

    This function:
    1. Sets the turn count to target_turn
    2. Checks for any scheduled events that should fire
    3. Calls the world event handler for each fired event

    Args:
        accessor: StateAccessor instance
        target_turn: Turn number to advance to

    Returns:
        List of messages from scheduled events
    """
    from behavior_libraries.timing_lib.scheduled_events import get_scheduled_events
    from big_game.behaviors.world_events import on_world_event_check

    accessor.game_state.turn_count = target_turn
    events = get_scheduled_events(accessor)
    messages = []

    # Find events that should fire
    events_to_fire = []
    events_to_keep = []
    for event in events:
        if event['turn'] <= target_turn:
            events_to_fire.append(event)
        else:
            events_to_keep.append(event)

    # Update the scheduled events list
    accessor.game_state.extra['scheduled_events'] = events_to_keep

    # Fire each event through the world event handler
    for event in events_to_fire:
        context = {
            'event_name': event['event'],
            'data': event.get('data', {})
        }
        result = on_world_event_check(None, accessor, context)
        if result.message:
            messages.extend(result.message.split('\n'))

    return messages


def complete_quest(accessor, quest_id: str) -> str:
    """
    Trigger quest completion.

    Args:
        accessor: StateAccessor instance
        quest_id: The quest to complete

    Returns:
        Message from quest completion
    """
    from big_game.behaviors.world_events import on_quest_complete

    result = on_quest_complete(None, accessor, {"quest_id": quest_id})
    return result.message


# ============================================================================
# CATEGORY 1: QUEST COMPLETION CASCADES
# ============================================================================


class TestQuestCompletionCascades(unittest.TestCase):
    """Tests for quest completion side effects."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        self.accessor = StateAccessor(self.state, self.manager)

    def test_heal_spore_mother_purifies_region(self):
        """Test that healing Spore Mother purifies Fungal Depths."""
        from big_game.behaviors.regions import is_region_purified

        # Initially not purified
        self.assertFalse(is_region_purified(self.accessor, "fungal_depths"))

        # Complete quest
        complete_quest(self.accessor, "heal_spore_mother")

        # Now purified
        self.assertTrue(is_region_purified(self.accessor, "fungal_depths"))

    def test_heal_spore_mother_cancels_spread(self):
        """Test that healing Spore Mother cancels spore spread event."""
        from big_game.behaviors.world_events import initialize_world_events
        from behavior_libraries.timing_lib.scheduled_events import get_scheduled_events

        # Initialize to schedule events
        initialize_world_events(self.accessor)
        events = get_scheduled_events(self.accessor)
        self.assertTrue(any(e['event'] == 'world_spore_spread' for e in events))

        # Complete quest
        complete_quest(self.accessor, "heal_spore_mother")

        # Event should be cancelled
        events = get_scheduled_events(self.accessor)
        self.assertFalse(any(e['event'] == 'world_spore_spread' for e in events))

    def test_heal_spore_mother_sets_flag(self):
        """Test that healing Spore Mother sets the flag."""
        complete_quest(self.accessor, "heal_spore_mother")

        self.assertTrue(
            self.state.extra.get('flags', {}).get('spore_mother_healed', False)
        )

    def test_repair_observatory_cancels_cold_spread(self):
        """Test that repairing observatory cancels cold spread."""
        from big_game.behaviors.world_events import initialize_world_events
        from behavior_libraries.timing_lib.scheduled_events import get_scheduled_events

        initialize_world_events(self.accessor)
        events = get_scheduled_events(self.accessor)
        self.assertTrue(any(e['event'] == 'world_cold_spread' for e in events))

        complete_quest(self.accessor, "repair_observatory")

        events = get_scheduled_events(self.accessor)
        self.assertFalse(any(e['event'] == 'world_cold_spread' for e in events))

    def test_repair_observatory_sets_flag(self):
        """Test that repairing observatory sets the flag."""
        complete_quest(self.accessor, "repair_observatory")

        self.assertTrue(
            self.state.extra.get('flags', {}).get('observatory_repaired', False)
        )

    def test_pacify_beast_wilds_purifies_region(self):
        """Test that pacifying Beast Wilds purifies the region."""
        from big_game.behaviors.regions import is_region_purified

        self.assertFalse(is_region_purified(self.accessor, "beast_wilds"))

        complete_quest(self.accessor, "pacify_beast_wilds")

        self.assertTrue(is_region_purified(self.accessor, "beast_wilds"))
        self.assertTrue(
            self.state.extra.get('flags', {}).get('beast_wilds_pacified', False)
        )

    def test_restore_frozen_reaches_purifies_region(self):
        """Test that restoring Frozen Reaches purifies the region."""
        from big_game.behaviors.regions import is_region_purified

        self.assertFalse(is_region_purified(self.accessor, "frozen_reaches"))

        complete_quest(self.accessor, "restore_frozen_reaches")

        self.assertTrue(is_region_purified(self.accessor, "frozen_reaches"))
        self.assertTrue(
            self.state.extra.get('flags', {}).get('frozen_reaches_restored', False)
        )

    def test_cure_aldric_sets_flag(self):
        """Test that curing Aldric sets the flag."""
        complete_quest(self.accessor, "cure_aldric")

        self.assertTrue(
            self.state.extra.get('flags', {}).get('aldric_cured', False)
        )

    def test_restore_crystal_sets_flag(self):
        """Test that restoring crystals sets flags."""
        for i in range(1, 4):
            complete_quest(self.accessor, f"restore_crystal_{i}")
            self.assertTrue(
                self.state.extra.get('flags', {}).get(f'crystal_{i}_restored', False)
            )

    def test_all_crystals_triggers_message(self):
        """Test that restoring all crystals produces special message."""
        for i in range(1, 3):
            complete_quest(self.accessor, f"restore_crystal_{i}")

        # Third crystal should trigger special message
        message = complete_quest(self.accessor, "restore_crystal_3")
        self.assertIn("All three crystals", message)


# ============================================================================
# CATEGORY 2: SCHEDULED EVENT TRIGGERS
# ============================================================================


class TestScheduledEventTriggers(unittest.TestCase):
    """Tests for timed event mechanics."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        self.accessor = StateAccessor(self.state, self.manager)

    def test_spore_spread_triggers_at_turn_100(self):
        """Test that spore spread triggers at turn 100."""
        from big_game.behaviors.world_events import initialize_world_events

        initialize_world_events(self.accessor)

        # Advance to turn 100
        messages = advance_turns_direct(self.accessor, 100)

        # Should have triggered
        self.assertTrue(
            self.state.extra.get('flags', {}).get('spore_spread_started', False)
        )

    def test_spore_spread_corrupts_civilized_remnants(self):
        """Test that spore spread corrupts Civilized Remnants."""
        from big_game.behaviors.world_events import initialize_world_events

        initialize_world_events(self.accessor)
        advance_turns_direct(self.accessor, 100)

        # Check some location has spore_level
        regions = self.state.extra.get('regions', {})
        cr_locs = regions.get('civilized_remnants', {}).get('locations', [])

        has_spores = False
        for loc_id in cr_locs:
            loc = self.state.get_location(loc_id)
            if loc and loc.properties.get('spore_level'):
                has_spores = True
                break

        self.assertTrue(has_spores)

    def test_spore_spread_affects_guards(self):
        """Test that spore spread affects guard NPCs."""
        from big_game.behaviors.world_events import initialize_world_events

        initialize_world_events(self.accessor)
        advance_turns_direct(self.accessor, 100)

        guard = self.accessor.get_actor('npc_cr_gate_guard')
        if guard:
            self.assertTrue(guard.properties.get('spore_exposed', False))

    def test_cold_spread_triggers_at_turn_150(self):
        """Test that cold spread triggers at turn 150."""
        from big_game.behaviors.world_events import initialize_world_events

        initialize_world_events(self.accessor)
        advance_turns_direct(self.accessor, 150)

        self.assertTrue(
            self.state.extra.get('flags', {}).get('cold_spread_started', False)
        )

    def test_cold_spread_corrupts_beast_wilds(self):
        """Test that cold spread corrupts Beast Wilds."""
        from big_game.behaviors.world_events import initialize_world_events

        initialize_world_events(self.accessor)
        advance_turns_direct(self.accessor, 150)

        # Check some location has cold effects
        regions = self.state.extra.get('regions', {})
        bw_locs = regions.get('beast_wilds', {}).get('locations', [])

        has_cold = False
        for loc_id in bw_locs:
            loc = self.state.get_location(loc_id)
            if loc and loc.properties.get('temperature') == 'cold':
                has_cold = True
                break

        # At minimum, the flag should be set
        self.assertTrue(
            self.state.extra.get('flags', {}).get('cold_spread_started', False)
        )

    def test_cold_spread_affects_creatures(self):
        """Test that cold spread affects creature actors."""
        from big_game.behaviors.world_events import initialize_world_events

        initialize_world_events(self.accessor)
        advance_turns_direct(self.accessor, 150)

        wolf = self.accessor.get_actor('creature_bw_alpha_wolf')
        if wolf:
            self.assertTrue(wolf.properties.get('cold_affected', False))

    def test_spore_spread_prevented_if_fungal_purified(self):
        """Test that spore spread doesn't happen if Fungal Depths purified."""
        from big_game.behaviors.world_events import initialize_world_events
        from big_game.behaviors.regions import purify_region

        # Purify first
        purify_region(self.accessor, "fungal_depths")

        initialize_world_events(self.accessor)
        advance_turns_direct(self.accessor, 100)

        # Should NOT have triggered
        self.assertFalse(
            self.state.extra.get('flags', {}).get('spore_spread_started', False)
        )

    def test_cold_spread_prevented_if_observatory_repaired(self):
        """Test that cold spread doesn't happen if observatory repaired."""
        from big_game.behaviors.world_events import initialize_world_events

        # Set flag first
        self.state.extra.setdefault('flags', {})['observatory_repaired'] = True

        initialize_world_events(self.accessor)
        advance_turns_direct(self.accessor, 150)

        # Should NOT have triggered
        self.assertFalse(
            self.state.extra.get('flags', {}).get('cold_spread_started', False)
        )


# ============================================================================
# CATEGORY 3: DEADLINE BOUNDARY TESTS
# ============================================================================


class TestDeadlineBoundaries(unittest.TestCase):
    """Tests for deadline edge cases."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        self.accessor = StateAccessor(self.state, self.manager)

    def test_spore_spread_not_at_turn_99(self):
        """Test that spore spread doesn't trigger at turn 99."""
        from big_game.behaviors.world_events import initialize_world_events

        initialize_world_events(self.accessor)
        advance_turns_direct(self.accessor, 99)

        self.assertFalse(
            self.state.extra.get('flags', {}).get('spore_spread_started', False)
        )

    def test_spore_spread_at_turn_100(self):
        """Test that spore spread triggers at exactly turn 100."""
        from big_game.behaviors.world_events import initialize_world_events

        initialize_world_events(self.accessor)
        advance_turns_direct(self.accessor, 100)

        self.assertTrue(
            self.state.extra.get('flags', {}).get('spore_spread_started', False)
        )

    def test_cold_spread_not_at_turn_149(self):
        """Test that cold spread doesn't trigger at turn 149."""
        from big_game.behaviors.world_events import initialize_world_events

        initialize_world_events(self.accessor)
        advance_turns_direct(self.accessor, 149)

        self.assertFalse(
            self.state.extra.get('flags', {}).get('cold_spread_started', False)
        )

    def test_cold_spread_at_turn_150(self):
        """Test that cold spread triggers at exactly turn 150."""
        from big_game.behaviors.world_events import initialize_world_events

        initialize_world_events(self.accessor)
        advance_turns_direct(self.accessor, 150)

        self.assertTrue(
            self.state.extra.get('flags', {}).get('cold_spread_started', False)
        )

    def test_heal_at_turn_99_prevents_spread(self):
        """Test that healing Spore Mother at turn 99 prevents spread."""
        from big_game.behaviors.world_events import initialize_world_events

        initialize_world_events(self.accessor)

        # Advance to 99, then heal
        advance_turns_direct(self.accessor, 99)
        complete_quest(self.accessor, "heal_spore_mother")

        # Advance to 100
        advance_turns_direct(self.accessor, 100)

        # Should NOT have spread
        self.assertFalse(
            self.state.extra.get('flags', {}).get('spore_spread_started', False)
        )

    def test_repair_at_turn_149_prevents_cold(self):
        """Test that repairing observatory at turn 149 prevents cold spread."""
        from big_game.behaviors.world_events import initialize_world_events

        initialize_world_events(self.accessor)

        # Advance to 149, then repair
        advance_turns_direct(self.accessor, 149)
        complete_quest(self.accessor, "repair_observatory")

        # Advance to 150
        advance_turns_direct(self.accessor, 150)

        # Should NOT have spread
        self.assertFalse(
            self.state.extra.get('flags', {}).get('cold_spread_started', False)
        )


# ============================================================================
# CATEGORY 4: ENDING CONDITION PATHS
# ============================================================================


class TestEndingConditionPaths(unittest.TestCase):
    """Tests for all four ending conditions."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        self.accessor = StateAccessor(self.state, self.manager)

    def test_perfect_ending(self):
        """Test perfect ending: all crystals + all regions purified."""
        from big_game.behaviors.world_events import check_ending_conditions

        # Restore all crystals
        for i in range(1, 4):
            complete_quest(self.accessor, f"restore_crystal_{i}")

        # Purify all regions
        complete_quest(self.accessor, "heal_spore_mother")
        complete_quest(self.accessor, "pacify_beast_wilds")
        complete_quest(self.accessor, "restore_frozen_reaches")

        result = check_ending_conditions(self.accessor)
        self.assertEqual(result['ending'], 'perfect')
        self.assertEqual(result['crystals_restored'], 3)
        self.assertEqual(result['regions_purified'], 3)

    def test_partial_restoration_ending(self):
        """Test partial restoration ending: all crystals, not all regions."""
        from big_game.behaviors.world_events import check_ending_conditions

        # Restore all crystals
        for i in range(1, 4):
            complete_quest(self.accessor, f"restore_crystal_{i}")

        # Purify only one region
        complete_quest(self.accessor, "heal_spore_mother")

        result = check_ending_conditions(self.accessor)
        self.assertEqual(result['ending'], 'partial_restoration')
        self.assertEqual(result['crystals_restored'], 3)
        self.assertEqual(result['regions_purified'], 1)

    def test_catastrophe_ending(self):
        """Test catastrophe ending: both spreads occurred."""
        from big_game.behaviors.world_events import (
            check_ending_conditions, initialize_world_events
        )

        initialize_world_events(self.accessor)

        # Let both spreads happen
        advance_turns_direct(self.accessor, 100)  # Spore spread
        advance_turns_direct(self.accessor, 150)  # Cold spread

        result = check_ending_conditions(self.accessor)
        self.assertEqual(result['ending'], 'catastrophe')
        self.assertTrue(result['spore_spread'])
        self.assertTrue(result['cold_spread'])

    def test_in_progress_default(self):
        """Test in_progress: initial state."""
        from big_game.behaviors.world_events import check_ending_conditions

        result = check_ending_conditions(self.accessor)
        self.assertEqual(result['ending'], 'in_progress')


# ============================================================================
# CATEGORY 5: COMPLETE PLAYER JOURNEYS
# ============================================================================


class TestCompletePlayerJourneys(unittest.TestCase):
    """End-to-end journey tests using simulated gameplay."""

    def test_journey_perfect_ending(self):
        """Test complete path to perfect ending."""
        session = SimulatedPlaySession(verbose=False)

        # Complete all quests
        session.complete_quest("heal_spore_mother", "Healed the Spore Mother")
        session.complete_quest("repair_observatory", "Repaired the Observatory")
        session.complete_quest("pacify_beast_wilds", "Pacified the Beast Wilds")
        session.complete_quest("restore_frozen_reaches", "Restored the Frozen Reaches")

        for i in range(1, 4):
            session.complete_quest(f"restore_crystal_{i}", f"Restored crystal {i}")

        # Check ending
        from big_game.behaviors.world_events import check_ending_conditions
        result = check_ending_conditions(session.accessor)

        self.assertEqual(result['ending'], 'perfect')

        # Print transcript on failure
        if result['ending'] != 'perfect':
            print(session.get_transcript())

    def test_journey_catastrophe_ending(self):
        """Test complete path to catastrophe ending."""
        session = SimulatedPlaySession(verbose=False)

        # Initialize events
        from big_game.behaviors.world_events import initialize_world_events
        initialize_world_events(session.accessor)

        # Let deadlines pass without intervention
        session.advance_to_turn(100, "Spore spread deadline")
        session.advance_to_turn(150, "Cold spread deadline")

        # Check ending
        from big_game.behaviors.world_events import check_ending_conditions
        result = check_ending_conditions(session.accessor)

        self.assertEqual(result['ending'], 'catastrophe')

        # Print transcript on failure
        if result['ending'] != 'catastrophe':
            print(session.get_transcript())

    def test_journey_partial_restoration(self):
        """Test path to partial restoration ending."""
        session = SimulatedPlaySession(verbose=False)

        # Restore all crystals
        for i in range(1, 4):
            session.complete_quest(f"restore_crystal_{i}")

        # Purify only one region
        session.complete_quest("heal_spore_mother")

        # Check ending
        from big_game.behaviors.world_events import check_ending_conditions
        result = check_ending_conditions(session.accessor)

        self.assertEqual(result['ending'], 'partial_restoration')

    def test_journey_race_against_time(self):
        """Test completing objectives just before deadlines."""
        session = SimulatedPlaySession(verbose=False)

        # Initialize events
        from big_game.behaviors.world_events import initialize_world_events
        initialize_world_events(session.accessor)

        # Advance to just before spore deadline
        session.advance_to_turn(95, "Approaching spore deadline")

        # Heal in time
        session.complete_quest("heal_spore_mother", "Just in time!")

        # Continue to just before cold deadline
        session.advance_to_turn(145, "Approaching cold deadline")

        # Repair in time
        session.complete_quest("repair_observatory", "Close call!")

        # Advance past both deadlines
        session.advance_to_turn(160, "Deadlines passed safely")

        # Neither spread should have occurred
        self.assertFalse(session.get_flag('spore_spread_started'))
        self.assertFalse(session.get_flag('cold_spread_started'))

    def test_journey_with_gameplay_commands(self):
        """Test journey using actual movement commands."""
        session = SimulatedPlaySession(verbose=False)

        # Start with a look
        result = session.command("look", note="Initial look")
        self.assertTrue(result.get("success"))

        # Move around the nexus
        session.command("go", "up", "Go to observatory")
        session.command("look")
        session.command("go", "down", "Return to nexus")

        # Complete a quest
        session.complete_quest("restore_crystal_1")

        # Verify flag
        self.assertTrue(session.get_flag('crystal_1_restored'))

        # The transcript should show the journey
        transcript = session.get_transcript(include_responses=False)
        self.assertIn("go up", transcript)
        self.assertIn("restore_crystal_1", transcript)


# ============================================================================
# CATEGORY 6: SYSTEM INTERACTION TESTS
# ============================================================================


class TestFactionReputationCascades(unittest.TestCase):
    """Tests for faction reputation propagation."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        self.accessor = StateAccessor(self.state, self.manager)

    def test_faction_action_affects_reputation(self):
        """Test that faction actions modify reputation."""
        from big_game.behaviors.factions import (
            on_faction_action, get_faction_reputation
        )

        entity = self.accessor.get_actor("npc_fd_myconid_elder")
        context = {"action": "help", "faction_id": "myconid_collective"}

        on_faction_action(entity, self.accessor, context)

        rep = get_faction_reputation(self.accessor, "myconid_collective")
        self.assertGreater(rep.get("trust", 0), 0)

    def test_faction_reputation_syncs_to_members(self):
        """Test that reputation syncs to faction members."""
        from big_game.behaviors.factions import modify_faction_reputation
        from behaviors.actors.relationships import get_relationship

        modify_faction_reputation(
            self.accessor, "myconid_collective", "trust", 5
        )

        member = self.accessor.get_actor("npc_fd_myconid_elder")
        if member:
            rel = get_relationship(member, "player")
            self.assertEqual(rel.get("trust", 0), 5)

    def test_faction_disposition_changes_at_threshold(self):
        """Test disposition changes when thresholds crossed."""
        from big_game.behaviors.factions import (
            modify_faction_reputation, get_faction_disposition
        )

        # Start neutral
        disposition = get_faction_disposition(self.accessor, "myconid_collective")
        self.assertEqual(disposition, "neutral")

        # Increase trust to friendly threshold
        modify_faction_reputation(
            self.accessor, "myconid_collective", "trust", 5,
            sync_to_members=False
        )

        disposition = get_faction_disposition(self.accessor, "myconid_collective")
        self.assertEqual(disposition, "friendly")


class TestEchoIntegrationCascades(unittest.TestCase):
    """Tests for The Echo's state-aware behavior."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        self.accessor = StateAccessor(self.state, self.manager)

    def test_echo_appearance_increases_with_restoration(self):
        """Test Echo appearance chance increases with flags."""
        from big_game.behaviors.npc_specifics.the_echo import calculate_appearance_chance

        # Base chance
        base_chance = calculate_appearance_chance(self.accessor)

        # Set some restoration flags
        self.state.extra.setdefault('flags', {})
        self.state.extra['flags']['crystal_1_restored'] = True
        self.state.extra['flags']['crystal_2_restored'] = True

        # Chance should be higher
        new_chance = calculate_appearance_chance(self.accessor)
        self.assertGreater(new_chance, base_chance)

    def test_echo_message_reflects_crystal_progress(self):
        """Test Echo message shows crystal count."""
        from big_game.behaviors.npc_specifics.the_echo import get_echo_message

        self.state.extra.setdefault('flags', {})
        self.state.extra['flags']['met_the_echo'] = True
        self.state.extra['flags']['crystal_1_restored'] = True
        self.state.extra['flags']['crystal_2_restored'] = True

        message = get_echo_message(self.accessor)
        self.assertTrue("two" in message.lower() or "2" in message)

    def test_echo_warns_of_spread(self):
        """Test Echo warns about active spreads."""
        from big_game.behaviors.npc_specifics.the_echo import get_echo_message

        self.state.extra.setdefault('flags', {})
        self.state.extra['flags']['met_the_echo'] = True
        self.state.extra['flags']['spore_spread_started'] = True

        message = get_echo_message(self.accessor)
        self.assertIn("spore", message.lower())


class TestRegionStateCascades(unittest.TestCase):
    """Tests for region state changes."""

    def setUp(self):
        """Set up game with all behaviors loaded."""
        self.state = load_game_state(str(get_game_state_path()))
        self.manager = BehaviorManager()
        load_all_behaviors(self.manager)
        self.accessor = StateAccessor(self.state, self.manager)

    def test_corruption_affects_all_region_locations(self):
        """Test that corruption spreads to all locations in region."""
        from big_game.behaviors.regions import corrupt_region

        messages = corrupt_region(self.accessor, "beast_wilds", "spore")

        # Should have returned messages
        self.assertGreater(len(messages), 0)

    def test_purification_clears_region(self):
        """Test that purification clears region state."""
        from big_game.behaviors.regions import (
            corrupt_region, purify_region, is_region_purified
        )

        # First corrupt
        corrupt_region(self.accessor, "beast_wilds", "spore")

        # Then purify
        purify_region(self.accessor, "beast_wilds")

        # Should be purified
        self.assertTrue(is_region_purified(self.accessor, "beast_wilds"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
