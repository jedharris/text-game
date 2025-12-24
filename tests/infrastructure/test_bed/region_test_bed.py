"""
Region Test Bed

Configurable test framework for region-based testing.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from tests.infrastructure.test_bed.context_loaders import ContextLoader, FreshContextLoader
from tests.infrastructure.test_bed.logger import InteractionLogger, LogEntry, LogLevel

from src.types import ActorId

if TYPE_CHECKING:
    from src.behavior_manager import BehaviorManager
    from src.llm_protocol import LLMProtocolHandler
    from src.state_accessor import HandlerResult, StateAccessor
    from src.state_manager import GameState


class AssertionError(Exception):
    """Test bed assertion failure."""

    pass


class RegionTestBed:
    """Configurable test bed for region-based testing.

    Provides:
    - Context loading (fresh, mid-game, custom)
    - Command execution with infrastructure hooks
    - State assertions for testing
    - Interaction logging for debugging
    """

    def __init__(
        self,
        context_loader: ContextLoader | None = None,
        game_dir: str | Path | None = None,
        log_level: str = "errors",
    ) -> None:
        """Initialize test bed.

        Args:
            context_loader: Loader for initial game state
            game_dir: Alternative - path to game directory with game_state.json
            log_level: Logging verbosity ("errors", "changes", "all")
        """
        from src.behavior_manager import BehaviorManager
        from src.llm_protocol import LLMProtocolHandler
        from src.state_accessor import StateAccessor

        self._state: GameState | None = None
        self._handler: LLMProtocolHandler | None = None
        self._accessor: StateAccessor | None = None
        self._behavior_manager: BehaviorManager | None = None

        # Set up context loader
        self._context_loader: ContextLoader | None
        if context_loader:
            self._context_loader = context_loader
        elif game_dir:
            game_path = Path(game_dir) / "game_state.json"
            self._context_loader = FreshContextLoader(game_path)
        else:
            self._context_loader = None

        # Set up logger
        level = LogLevel(log_level)
        self._logger = InteractionLogger(level)

    def load_context(self, context_loader: ContextLoader | None = None) -> None:
        """Load game context from loader.

        Args:
            context_loader: Loader to use (or use default from init)
        """
        from src.behavior_manager import BehaviorManager
        from src.llm_protocol import LLMProtocolHandler
        from src.state_accessor import StateAccessor

        loader = context_loader or self._context_loader
        if not loader:
            raise ValueError("No context loader provided")

        self._state = loader.load()

        # Set up behavior manager
        self._behavior_manager = BehaviorManager()

        # Load behaviors from game directory if available
        game_dir = self._get_game_dir()
        if game_dir:
            behaviors_path = game_dir / "behaviors"
            if behaviors_path.exists():
                modules = self._behavior_manager.discover_modules(str(behaviors_path))
                self._behavior_manager.load_modules(modules)

        # Set up protocol handler and accessor
        self._handler = LLMProtocolHandler(self._state, self._behavior_manager)
        self._accessor = StateAccessor(self._state, self._behavior_manager)

    def _get_game_dir(self) -> Path | None:
        """Get game directory from context loader."""
        if isinstance(self._context_loader, FreshContextLoader):
            return self._context_loader.path.parent
        return None

    @property
    def state(self) -> "GameState":
        """Get current game state."""
        if self._state is None:
            raise RuntimeError("No context loaded - call load_context() first")
        return self._state

    @property
    def logger(self) -> InteractionLogger:
        """Get interaction logger."""
        return self._logger

    # =========================================================================
    # Command Execution
    # =========================================================================

    def execute(self, verb: str, obj: str | None = None, **kwargs: Any) -> dict[str, Any]:
        """Execute a command and return result.

        Args:
            verb: Command verb (e.g., "take", "go", "talk")
            obj: Command object (e.g., "sword", "north", "merchant")
            **kwargs: Additional action parameters

        Returns:
            Result dictionary from protocol handler
        """
        if self._handler is None:
            raise RuntimeError("No context loaded - call load_context() first")

        # Build action dict
        action: dict[str, Any] = {"verb": verb}
        if obj:
            action["object"] = obj
        action.update(kwargs)

        # Capture state before
        state_before = self._capture_relevant_state()

        # Execute command
        message = {"type": "command", "action": action}
        result = self._handler.handle_message(message)

        # Capture state after
        state_after = self._capture_relevant_state()

        # Log the interaction
        entry = LogEntry(
            turn=self.game_state.extra.get("turn_count", 0),
            phase="command",
            action=f"{verb} {obj}" if obj else verb,
            state_before=state_before,
            state_after=state_after,
            result=None,  # TODO: Convert result to HandlerResult
            issues=[],
        )
        self._logger.log(entry)

        return result

    def execute_sequence(self, commands: list[tuple[str, str | None]]) -> list[dict[str, Any]]:
        """Execute a sequence of commands.

        Args:
            commands: List of (verb, object) tuples

        Returns:
            List of results
        """
        results = []
        for verb, obj in commands:
            result = self.execute(verb, obj)
            results.append(result)
        return results

    def advance_turns(self, count: int) -> list[dict[str, Any]]:
        """Advance game by executing 'wait' command multiple times.

        Args:
            count: Number of turns to advance

        Returns:
            List of results from each wait command
        """
        results = []
        for _ in range(count):
            result = self.execute("wait")
            results.append(result)
        return results

    def _capture_relevant_state(self) -> dict[str, Any]:
        """Capture relevant state for logging."""
        if self._state is None:
            return {}

        return {
            "turn": self._state.extra.get("turn_count", 0),
            "flags": dict(self._state.extra.get("flags", {})),
            "player_location": self._state.actors.get(ActorId("player"), {}).location  # type: ignore[union-attr]
            if ActorId("player") in self._state.actors
            else None,
        }

    # =========================================================================
    # Assertions
    # =========================================================================

    def assert_flag(self, flag: str, expected: bool | int, scope: str = "global") -> None:
        """Assert a flag has expected value.

        Args:
            flag: Flag name
            expected: Expected value
            scope: "global" or actor ID
        """
        if scope == "global":
            flags = self.game_state.extra.get("flags", {})
        else:
            actor = self.game_state.actors.get(ActorId(scope))
            if not actor:
                raise AssertionError(f"Actor not found: {scope}")
            flags = actor.properties.get("flags", {})

        actual = flags.get(flag)
        if actual != expected:
            raise AssertionError(
                f"Flag '{flag}' (scope={scope}): expected {expected}, got {actual}"
            )

    def assert_trust(
        self,
        actor_id: str,
        value: int | None = None,
        min_value: int | None = None,
        max_value: int | None = None,
    ) -> None:
        """Assert actor trust value or range.

        Args:
            actor_id: Actor ID
            value: Exact expected value (if checking exact)
            min_value: Minimum expected value (if checking range)
            max_value: Maximum expected value (if checking range)
        """
        actor = self.game_state.actors.get(ActorId(actor_id))
        if not actor:
            raise AssertionError(f"Actor not found: {actor_id}")

        trust_data = actor.properties.get("trust", {})
        actual = trust_data.get("current", 0)

        if value is not None and actual != value:
            raise AssertionError(
                f"Trust for '{actor_id}': expected {value}, got {actual}"
            )

        if min_value is not None and actual < min_value:
            raise AssertionError(
                f"Trust for '{actor_id}': expected >= {min_value}, got {actual}"
            )

        if max_value is not None and actual > max_value:
            raise AssertionError(
                f"Trust for '{actor_id}': expected <= {max_value}, got {actual}"
            )

    def assert_state(self, actor_id: str, expected_state: str) -> None:
        """Assert actor is in expected state machine state.

        Args:
            actor_id: Actor ID
            expected_state: Expected state name
        """
        actor = self.game_state.actors.get(ActorId(actor_id))
        if not actor:
            raise AssertionError(f"Actor not found: {actor_id}")

        sm = actor.properties.get("state_machine", {})
        current = sm.get("current", sm.get("initial"))

        if current != expected_state:
            raise AssertionError(
                f"State for '{actor_id}': expected '{expected_state}', got '{current}'"
            )

    def assert_condition(
        self,
        actor_id: str,
        condition: str,
        has_condition: bool = True,
        severity: int | None = None,
        min_severity: int | None = None,
    ) -> None:
        """Assert actor has/doesn't have condition with optional severity check.

        Args:
            actor_id: Actor ID
            condition: Condition type
            has_condition: Whether actor should have condition
            severity: Exact severity (if checking exact)
            min_severity: Minimum severity (if checking threshold)
        """
        actor = self.game_state.actors.get(ActorId(actor_id))
        if not actor:
            raise AssertionError(f"Actor not found: {actor_id}")

        conditions = actor.properties.get("conditions", [])

        # Find condition
        found = None
        for c in conditions:
            if c.get("type") == condition:
                found = c
                break

        if has_condition and found is None:
            raise AssertionError(f"Actor '{actor_id}' missing condition: {condition}")

        if not has_condition and found is not None:
            raise AssertionError(
                f"Actor '{actor_id}' has unexpected condition: {condition}"
            )

        if found and severity is not None:
            actual_sev = found.get("severity", 0)
            if actual_sev != severity:
                raise AssertionError(
                    f"Condition '{condition}' severity: expected {severity}, got {actual_sev}"
                )

        if found and min_severity is not None:
            actual_sev = found.get("severity", 0)
            if actual_sev < min_severity:
                raise AssertionError(
                    f"Condition '{condition}' severity: expected >= {min_severity}, got {actual_sev}"
                )

    def assert_location(self, actor_id: str, expected_location: str) -> None:
        """Assert actor is at expected location.

        Args:
            actor_id: Actor ID
            expected_location: Expected location ID
        """
        actor = self.game_state.actors.get(ActorId(actor_id))
        if not actor:
            raise AssertionError(f"Actor not found: {actor_id}")

        if actor.location != expected_location:
            raise AssertionError(
                f"Location for '{actor_id}': expected '{expected_location}', "
                f"got '{actor.location}'"
            )

    def assert_item(
        self,
        item_id: str,
        location: str | None = None,
        holder: str | None = None,
    ) -> None:
        """Assert item is at location or held by actor.

        Args:
            item_id: Item ID
            location: Expected location ID (mutually exclusive with holder)
            holder: Expected holder actor ID (mutually exclusive with location)
        """
        if location and holder:
            raise ValueError("Specify either location or holder, not both")

        # Find item
        item = None
        for i in self.game_state.items:
            if i.id == item_id:
                item = i
                break

        if item is None:
            raise AssertionError(f"Item not found: {item_id}")

        if location:
            if item.location != location:
                raise AssertionError(
                    f"Item '{item_id}' location: expected '{location}', got '{item.location}'"
                )

        if holder:
            actor = self.game_state.actors.get(ActorId(holder))
            if not actor:
                raise AssertionError(f"Holder not found: {holder}")
            if item_id not in actor.inventory:
                raise AssertionError(f"Item '{item_id}' not in '{holder}' inventory")

    def assert_commitment(
        self,
        commitment_id: str,
        state: str | None = None,
        exists: bool = True,
    ) -> None:
        """Assert commitment exists and has expected state.

        Args:
            commitment_id: Commitment ID
            state: Expected state (ACTIVE, FULFILLED, etc.)
            exists: Whether commitment should exist
        """
        from src.infrastructure_types import CommitmentId
        from src.infrastructure_utils import get_active_commitment

        commitment = get_active_commitment(self.game_state, CommitmentId(commitment_id))

        if exists and commitment is None:
            raise AssertionError(f"Commitment not found: {commitment_id}")

        if not exists and commitment is not None:
            raise AssertionError(f"Unexpected commitment: {commitment_id}")

        if commitment and state:
            actual_state = commitment.get("state")
            if actual_state != state:
                raise AssertionError(
                    f"Commitment '{commitment_id}' state: expected '{state}', got '{actual_state}'"
                )

    def assert_gossip_pending(
        self,
        content_contains: str,
        exists: bool = True,
    ) -> None:
        """Assert gossip with matching content is pending.

        Args:
            content_contains: Substring to match in content
            exists: Whether such gossip should exist
        """
        from src.infrastructure_utils import get_pending_gossip_about

        matches = get_pending_gossip_about(self.game_state, content_contains)

        if exists and not matches:
            raise AssertionError(f"No pending gossip containing: {content_contains}")

        if not exists and matches:
            raise AssertionError(f"Unexpected gossip containing: {content_contains}")

    def assert_spread_active(self, spread_id: str, expected: bool = True) -> None:
        """Assert spread is active or halted.

        Args:
            spread_id: Spread ID
            expected: Whether spread should be active
        """
        from src.infrastructure_utils import check_spread_active

        actual = check_spread_active(self.game_state, spread_id)

        if actual != expected:
            status = "active" if expected else "halted"
            actual_status = "active" if actual else "halted"
            raise AssertionError(
                f"Spread '{spread_id}': expected {status}, got {actual_status}"
            )

    # =========================================================================
    # Inspection
    # =========================================================================

    def get_flag(self, flag: str, scope: str = "global") -> bool | int | None:
        """Get flag value.

        Args:
            flag: Flag name
            scope: "global" or actor ID

        Returns:
            Flag value or None if not set
        """
        if scope == "global":
            flags = self.game_state.extra.get("flags", {})
        else:
            actor = self.game_state.actors.get(ActorId(scope))
            if not actor:
                return None
            flags = actor.properties.get("flags", {})

        return flags.get(flag)

    def get_trust(self, actor_id: str) -> int:
        """Get actor's current trust value."""
        actor = self.game_state.actors.get(ActorId(actor_id))
        if not actor:
            return 0
        trust_data = actor.properties.get("trust", {})
        return trust_data.get("current", 0)

    def get_actor_state(self, actor_id: str) -> str | None:
        """Get actor's current state machine state."""
        actor = self.game_state.actors.get(ActorId(actor_id))
        if not actor:
            return None
        sm = actor.properties.get("state_machine", {})
        return sm.get("current", sm.get("initial"))

    def get_current_turn(self) -> int:
        """Get current turn number."""
        return self.game_state.extra.get("turn_count", 0)
