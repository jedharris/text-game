"""
Infrastructure Utility Functions

Core utility functions used across infrastructure systems.

See: docs/big_game_work/detailed_designs/infrastructure_detailed_design.md Part 2
"""

from __future__ import annotations

import fnmatch
from typing import TYPE_CHECKING, Any, cast

from src.infrastructure_types import (
    ActiveCommitment,
    BroadcastGossipEntry,
    CommitmentConfig,
    CommitmentId,
    CommitmentState,
    CompanionComfort,
    CompanionState,
    ConditionInstance,
    ConditionType,
    GossipEntry,
    GossipId,
    NetworkDefinition,
    NetworkGossipEntry,
    ScheduledEvent,
    ScheduledEventId,
    SpreadEffect,
    SpreadMilestone,
    SpreadState,
    StateMachineConfig,
    TrustState,
    TurnNumber,
)
from src.types import ActorId, LocationId

if TYPE_CHECKING:
    from src.state_manager import Actor, GameState


# =============================================================================
# 2.1 Timer Operations
# =============================================================================


def check_deadline(current_turn: TurnNumber, deadline_turn: TurnNumber) -> bool:
    """Check if a deadline has passed.

    Returns True if deadline has passed (current >= deadline).
    """
    return current_turn >= deadline_turn


def turns_remaining(current_turn: TurnNumber, deadline_turn: TurnNumber) -> int:
    """Calculate turns remaining until deadline.

    Returns 0 if deadline has passed, otherwise positive count.
    """
    remaining = deadline_turn - current_turn
    return max(0, remaining)


def extend_deadline(current_deadline: TurnNumber, extension: int) -> TurnNumber:
    """Extend a deadline by a number of turns."""
    return TurnNumber(current_deadline + extension)


def create_deadline(current_turn: TurnNumber, duration: int) -> TurnNumber:
    """Create a deadline from current turn plus duration."""
    return TurnNumber(current_turn + duration)


def get_current_turn(state: GameState) -> TurnNumber:
    """Get the current turn number from game state."""
    return TurnNumber(state.extra.get("turn_count", 0))


def set_current_turn(state: GameState, new_turn: TurnNumber) -> None:
    """Persist the absolute turn counter."""
    state.extra["turn_count"] = int(new_turn)


def increment_turn(state: GameState) -> TurnNumber:
    """Increment the turn counter and return the new value.

    Args:
        state: Game state (mutated)

    Returns:
        New turn number after increment
    """
    current = int(get_current_turn(state))
    new_turn = TurnNumber(current + 1)
    set_current_turn(state, new_turn)
    return new_turn


# =============================================================================
# 2.2 Trust/Numeric Value Operations
# =============================================================================


def _modify_trust(
    current: int,
    delta: int,
    floor: int | None = None,
    ceiling: int | None = None,
) -> int:
    """Modify a trust value with optional bounds.

    Private implementation detail. External code should use apply_trust_change().

    Args:
        current: Current trust value
        delta: Change to apply (positive or negative)
        floor: Minimum value (None = unbounded below)
        ceiling: Maximum value (None = unbounded above)

    Returns:
        New trust value, clamped to bounds.
    """
    new_value = current + delta
    if floor is not None:
        new_value = max(floor, new_value)
    if ceiling is not None:
        new_value = min(ceiling, new_value)
    return new_value


def check_trust_threshold(current: int, threshold: int, at_least: bool = True) -> bool:
    """Check if trust meets a threshold.

    Args:
        current: Current trust value
        threshold: Required threshold
        at_least: If True, check current >= threshold. If False, check current <= threshold.
    """
    if at_least:
        return current >= threshold
    return current <= threshold


def apply_trust_change(
    entity: Any,
    delta: int,
    transitions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Apply trust change to an entity and check for state transitions.

    Unified trust modification for all interaction types (gifts, dialog, etc).

    Args:
        entity: Actor with trust_state property
        delta: Change to apply (positive or negative)
        transitions: Optional dict mapping trust thresholds to state names
                     {"3": "friendly", "5": "companion"}

    Returns:
        {
            "old_trust": int,
            "new_trust": int,
            "state_changed": bool,
            "new_state": str | None
        }
    """
    trust_state = entity.properties.get("trust_state", {"current": 0})
    old_trust = trust_state.get("current", 0)

    new_trust = _modify_trust(
        current=old_trust,
        delta=delta,
        floor=trust_state.get("floor", -5),
        ceiling=trust_state.get("ceiling", 5),
    )
    trust_state["current"] = new_trust
    entity.properties["trust_state"] = trust_state

    # Check for state transitions
    state_changed = False
    new_state = None
    if transitions:
        sm = entity.properties.get("state_machine")
        if sm:
            for threshold_str, target_state in transitions.items():
                threshold = int(threshold_str)
                # Trigger transition when crossing threshold upward
                if old_trust < threshold <= new_trust:
                    transition_state(sm, target_state)
                    state_changed = True
                    new_state = target_state
                    break  # Only transition once per change

    return {
        "old_trust": old_trust,
        "new_trust": new_trust,
        "state_changed": state_changed,
        "new_state": new_state,
    }


def calculate_recovery_amount(
    current: int,
    target: int,
    max_per_session: int,
    recovered_this_session: int,
) -> int:
    """Calculate how much trust can be recovered this session.

    Returns the actual recovery amount, respecting session cap.
    """
    needed = target - current
    if needed <= 0:
        return 0
    remaining_cap = max_per_session - recovered_this_session
    return min(needed, remaining_cap)


def attempt_trust_recovery(
    trust_state: TrustState,
    recovery_amount: int,
    current_turn: TurnNumber,
    recovery_cap: int = 3,
) -> tuple[int, int]:
    """Attempt to recover trust with per-visit cap.

    Args:
        trust_state: The trust state to modify
        recovery_amount: How much the action would recover
        current_turn: Current game turn
        recovery_cap: Maximum recovery per visit (default 3)

    Returns:
        (actual_recovery, new_trust_value)

    Session resets when last_recovery_turn is more than 10 turns ago.
    """
    last_turn = trust_state.get("last_recovery_turn", TurnNumber(0))

    # Check if session expired (new visit)
    if current_turn - last_turn > 10:
        trust_state["recovery_cap"] = recovery_cap
        trust_state["recovered_this_visit"] = 0

    # Calculate actual recovery
    remaining = trust_state.get("recovery_cap", recovery_cap) - trust_state.get(
        "recovered_this_visit", 0
    )
    actual = min(recovery_amount, remaining)

    if actual > 0:
        trust_state["current"] = trust_state["current"] + actual
        trust_state["recovered_this_visit"] = (
            trust_state.get("recovered_this_visit", 0) + actual
        )
        trust_state["last_recovery_turn"] = current_turn

    return actual, trust_state["current"]


# =============================================================================
# 2.3 State Machine Operations
# =============================================================================


def validate_state_machine(config: StateMachineConfig) -> list[str]:
    """Validate a state machine configuration.

    Returns list of error messages, empty if valid.
    """
    errors: list[str] = []

    if not config.get("states"):
        errors.append("State machine has no states")
        return errors

    initial = config.get("initial")
    if not initial:
        errors.append("State machine has no initial state")
    elif initial not in config["states"]:
        errors.append(f"Initial state '{initial}' not in states list")

    current = config.get("current")
    if current and current not in config["states"]:
        errors.append(f"Current state '{current}' not in states list")

    return errors


def get_current_state(config: StateMachineConfig) -> str:
    """Get current state, defaulting to initial if not set."""
    return config.get("current") or config["initial"]


def transition_state(config: StateMachineConfig, new_state: str) -> tuple[bool, str]:
    """Attempt to transition to a new state.

    Returns (success, message). Modifies config in place if successful.
    """
    if new_state not in config["states"]:
        return False, f"Invalid state: {new_state}"

    old_state = get_current_state(config)
    config["current"] = new_state
    return True, f"Transitioned from {old_state} to {new_state}"


# =============================================================================
# 2.4 Condition Operations
# =============================================================================


def get_actor_conditions(actor: Actor) -> list[ConditionInstance]:
    """Get an actor's conditions list, initializing if needed."""
    if "conditions" not in actor.properties:
        actor.properties["conditions"] = []
    return actor.properties["conditions"]


def create_condition(
    condition_type: ConditionType,
    initial_severity: int = 0,
    source: str | None = None,
) -> ConditionInstance:
    """Create a new condition instance."""
    condition: ConditionInstance = {
        "type": condition_type,
        "severity": initial_severity,
    }
    if source:
        condition["source"] = source
    return condition


def modify_condition_severity(
    condition: ConditionInstance,
    delta: int,
    max_severity: int = 100,
) -> int:
    """Modify condition severity, returning new value.

    Clamps to [0, max_severity]. Returns new severity.
    """
    new_severity = condition["severity"] + delta
    new_severity = max(0, min(max_severity, new_severity))
    condition["severity"] = new_severity
    return new_severity


def get_condition(
    conditions: list[ConditionInstance],
    condition_type: ConditionType,
) -> ConditionInstance | None:
    """Find a condition by type in a list."""
    for condition in conditions:
        if condition["type"] == condition_type:
            return condition
    return None


def remove_condition(
    conditions: list[ConditionInstance],
    condition_type: ConditionType,
) -> bool:
    """Remove a condition by type. Returns True if removed."""
    for i, condition in enumerate(conditions):
        if condition["type"] == condition_type:
            conditions.pop(i)
            return True
    return False


def has_condition(
    conditions: list[ConditionInstance],
    condition_type: ConditionType,
) -> bool:
    """Check if a condition exists."""
    return get_condition(conditions, condition_type) is not None


def get_condition_severity(
    conditions: list[ConditionInstance],
    condition_type: ConditionType,
) -> int:
    """Get severity of a condition, or 0 if not present."""
    condition = get_condition(conditions, condition_type)
    return condition["severity"] if condition else 0


# =============================================================================
# 2.5 Flag Operations
# =============================================================================


# Boolean flag operations
def get_bool_flag(flags: dict[str, Any], name: str, default: bool = False) -> bool:
    """Get a boolean flag value."""
    return flags.get(name, default)


def set_bool_flag(flags: dict[str, Any], name: str, value: bool) -> None:
    """Set a boolean flag."""
    flags[name] = value


def check_bool_flag(flags: dict[str, Any], name: str) -> bool:
    """Check if a boolean flag is True (shorthand for get_bool_flag with default False)."""
    return flags.get(name, False)


# Integer flag operations
def get_int_flag(flags: dict[str, Any], name: str, default: int = 0) -> int:
    """Get an integer flag value."""
    return flags.get(name, default)


def set_int_flag(flags: dict[str, Any], name: str, value: int) -> None:
    """Set an integer flag."""
    flags[name] = value


def increment_int_flag(flags: dict[str, Any], name: str, delta: int = 1) -> int:
    """Increment an integer flag, returning new value."""
    current = flags.get(name, 0)
    flags[name] = current + delta
    return flags[name]


# Common operations (work on any flag type)
def clear_flag(flags: dict[str, Any], name: str) -> bool:
    """Remove a flag. Returns True if it existed."""
    if name in flags:
        del flags[name]
        return True
    return False


def has_flag(flags: dict[str, Any], name: str) -> bool:
    """Check if a flag exists (regardless of value)."""
    return name in flags


# Scope accessors
def get_global_flags(state: GameState) -> dict[str, bool | int]:
    """Get the global flags dict, creating if needed."""
    if "flags" not in state.extra:
        state.extra["flags"] = {}
    return state.extra["flags"]


def get_actor_flags(actor: Actor) -> dict[str, bool | int]:
    """Get an actor's flags dict."""
    return actor.flags


# =============================================================================
# 2.6 Collection Accessors
# =============================================================================


def get_active_commitments(state: GameState) -> list[ActiveCommitment]:
    """Get list of active commitments, initializing if needed."""
    if "active_commitments" not in state.extra:
        state.extra["active_commitments"] = []
    return cast(list[ActiveCommitment], state.extra["active_commitments"])


def get_gossip_queue(state: GameState) -> list[GossipEntry]:
    """Get the gossip propagation queue, initializing if needed."""
    if "gossip_queue" not in state.extra:
        state.extra["gossip_queue"] = []
    return cast(list[GossipEntry], state.extra["gossip_queue"])


def get_scheduled_events(state: GameState) -> list[ScheduledEvent]:
    """Get list of scheduled events, initializing if needed."""
    if "scheduled_events" not in state.extra:
        state.extra["scheduled_events"] = []
    return cast(list[ScheduledEvent], state.extra["scheduled_events"])


def get_echo_trust(state: GameState) -> TrustState:
    """Get Echo trust state, initializing if needed."""
    if "echo_trust" not in state.extra:
        state.extra["echo_trust"] = {"current": 0}
    return cast(TrustState, state.extra["echo_trust"])


def get_active_companions(state: GameState) -> list[CompanionState]:
    """Get list of active companions, initializing if needed."""
    if "companions" not in state.extra:
        state.extra["companions"] = []
    return cast(list[CompanionState], state.extra["companions"])


def get_environmental_spreads(state: GameState) -> dict[str, SpreadState]:
    """Get environmental spreads dict, initializing if needed."""
    if "environmental_spreads" not in state.extra:
        state.extra["environmental_spreads"] = {}
    return cast(dict[str, SpreadState], state.extra["environmental_spreads"])


def get_network_definitions(state: GameState) -> dict[str, NetworkDefinition]:
    """Get gossip network definitions, initializing if needed."""
    if "networks" not in state.extra:
        state.extra["networks"] = {}
    return cast(dict[str, NetworkDefinition], state.extra["networks"])


def get_commitment_configs(state: GameState) -> dict[str, CommitmentConfig]:
    """Get commitment configuration map, initializing if needed."""
    if "commitment_configs" not in state.extra:
        state.extra["commitment_configs"] = {}
    return cast(dict[str, CommitmentConfig], state.extra["commitment_configs"])


# =============================================================================
# 2.7 Pattern Matching Utilities
# =============================================================================


def matches_pattern(target: str, pattern: str) -> bool:
    """Check if a target string matches a glob-like pattern.

    Patterns:
    - "exact_id" - matches only that exact string
    - "prefix/*" - matches strings starting with "prefix_" (region wildcard)
    - "*" - matches everything
    - Standard glob patterns via fnmatch

    Examples:
        matches_pattern("beast_wilds_clearing", "beast_wilds/*")  # True
        matches_pattern("beast_wilds_clearing", "sunken_district/*")  # False
        matches_pattern("nexus_chamber", "nexus_chamber")  # True
    """
    if pattern.endswith("/*"):
        prefix = pattern[:-2]
        return target.startswith(prefix + "_") or target == prefix
    return fnmatch.fnmatch(target, pattern)


def find_matching_locations(pattern: str, state: GameState) -> list[str]:
    """Find all location IDs matching a pattern.

    Args:
        pattern: Glob-like pattern (see matches_pattern)
        state: Game state with locations

    Returns:
        List of matching location IDs
    """
    return [loc.id for loc in state.locations if matches_pattern(loc.id, pattern)]


def matches_any_pattern(target: str, patterns: list[str]) -> bool:
    """Check if target matches any of the given patterns."""
    return any(matches_pattern(target, p) for p in patterns)


# =============================================================================
# 2.8 Scheduled Event Operations
# =============================================================================


def schedule_event(
    state: GameState,
    event_type: str,
    turns_from_now: int,
    event_id: ScheduledEventId | None = None,
    data: dict[str, str] | None = None,
) -> ScheduledEventId:
    """Schedule an event to fire at a future turn.

    Args:
        state: Game state (mutated)
        event_type: Type string that handlers match against
        turns_from_now: How many turns until it fires
        event_id: Optional custom ID (auto-generated if not provided)
        data: Optional event-specific data

    Returns:
        The event ID (either provided or generated)
    """
    events = get_scheduled_events(state)

    # Generate ID if not provided
    if event_id is None:
        event_id = ScheduledEventId(f"event_{event_type}_{len(events)}")

    # Calculate trigger turn
    current_turn = get_current_turn(state)
    trigger_turn = TurnNumber(current_turn + turns_from_now)

    # Create event
    event: ScheduledEvent = {
        "id": event_id,
        "trigger_turn": trigger_turn,
        "event_type": event_type,
    }
    if data:
        event["data"] = data

    events.append(event)
    return event_id


def cancel_scheduled_event(state: GameState, event_id: ScheduledEventId) -> bool:
    """Cancel a scheduled event.

    Args:
        state: Game state (mutated)
        event_id: ID of event to cancel

    Returns:
        True if event was found and cancelled, False otherwise
    """
    events = get_scheduled_events(state)
    for i, event in enumerate(events):
        if event["id"] == event_id:
            events.pop(i)
            return True
    return False


def reschedule_event(
    state: GameState,
    event_id: ScheduledEventId,
    new_trigger_turn: TurnNumber,
) -> bool:
    """Reschedule an event to fire at a different turn.

    Args:
        state: Game state (mutated)
        event_id: ID of event to reschedule
        new_trigger_turn: New trigger turn

    Returns:
        True if event was found and rescheduled, False otherwise
    """
    events = get_scheduled_events(state)
    for event in events:
        if event["id"] == event_id:
            event["trigger_turn"] = new_trigger_turn
            return True
    return False


def get_due_events(state: GameState) -> list[ScheduledEvent]:
    """Get events that are due to fire (trigger_turn <= current turn).

    Does not remove them - that's done by fire_due_events.
    """
    events = get_scheduled_events(state)
    current_turn = get_current_turn(state)
    return [e for e in events if e["trigger_turn"] <= current_turn]


def fire_due_events(state: GameState) -> list[ScheduledEvent]:
    """Get and remove events that are due to fire.

    Returns the fired events so handlers can process them.
    """
    events = get_scheduled_events(state)
    current_turn = get_current_turn(state)

    due = [e for e in events if e["trigger_turn"] <= current_turn]
    remaining = [e for e in events if e["trigger_turn"] > current_turn]

    # Replace the list in place (so the reference in state.extra stays valid)
    events.clear()
    events.extend(remaining)

    return due


# =============================================================================
# 2.9 Commitment Operations
# =============================================================================


def get_commitment_config(state: GameState, config_id: str) -> CommitmentConfig | None:
    """Get a commitment configuration by ID.

    Args:
        state: Game state containing configs
        config_id: ID of the config to look up

    Returns:
        The config if found, None otherwise
    """
    configs = get_commitment_configs(state)
    return configs.get(config_id)


def get_active_commitment(state: GameState, commitment_id: CommitmentId) -> ActiveCommitment | None:
    """Find an active commitment by ID.

    Args:
        state: Game state
        commitment_id: ID to find

    Returns:
        The commitment if found, None otherwise
    """
    commitments = get_active_commitments(state)
    for c in commitments:
        if c["id"] == commitment_id:
            return c
    return None


def create_commitment(
    state: GameState,
    config_id: str,
    current_turn: TurnNumber,
    commitment_id: CommitmentId | None = None,
) -> ActiveCommitment | None:
    """Create a new active commitment from a config.

    Args:
        state: Game state (mutated)
        config_id: Reference to CommitmentConfig
        current_turn: Current game turn
        commitment_id: Optional custom ID (defaults to config_id)

    Returns:
        The new commitment, or None if config not found
    """
    config = get_commitment_config(state, config_id)
    if config is None:
        return None

    commitments = get_active_commitments(state)

    # Use provided ID or default to config ID
    if commitment_id is None:
        commitment_id = CommitmentId(config_id)

    # Check for duplicate
    if get_active_commitment(state, commitment_id) is not None:
        return None

    # Create the commitment
    commitment: ActiveCommitment = {
        "id": commitment_id,
        "config_id": config_id,
        "state": CommitmentState.ACTIVE,
        "made_at_turn": current_turn,
        "hope_applied": False,
    }

    # Add deadline if timed
    if "base_timer" in config:
        commitment["deadline_turn"] = TurnNumber(current_turn + config["base_timer"])

    commitments.append(commitment)
    return commitment


def transition_commitment_state(
    commitment: ActiveCommitment,
    new_state: CommitmentState,
) -> bool:
    """Transition a commitment to a new state.

    Args:
        commitment: Commitment to transition (mutated)
        new_state: Target state

    Returns:
        True if transition is valid, False otherwise

    Valid transitions:
        ACTIVE -> FULFILLED | WITHDRAWN | ABANDONED
        (terminal states cannot transition)
    """
    if commitment["state"] != CommitmentState.ACTIVE:
        return False  # Can only transition from ACTIVE

    if new_state == CommitmentState.ACTIVE:
        return False  # Can't transition to current state

    commitment["state"] = new_state
    return True


def get_expired_commitments(state: GameState, current_turn: TurnNumber) -> list[ActiveCommitment]:
    """Get active commitments that have passed their deadline.

    Args:
        state: Game state
        current_turn: Current turn to compare against

    Returns:
        List of commitments that are ACTIVE but past deadline
    """
    commitments = get_active_commitments(state)
    expired = []
    for c in commitments:
        if c["state"] == CommitmentState.ACTIVE:
            deadline = c.get("deadline_turn")
            if deadline is not None and current_turn >= deadline:
                expired.append(c)
    return expired


def check_commitment_phrase(
    text: str,
    location_id: str,
    state: GameState,
) -> CommitmentConfig | None:
    """Check if player text matches a commitment trigger phrase.

    Args:
        text: Player input text
        location_id: Current location ID
        state: Game state with configs

    Returns:
        Matching CommitmentConfig or None
    """
    configs = get_commitment_configs(state)
    text_lower = text.lower()

    for config in configs.values():
        # Check if any trigger phrase matches
        for phrase in config.get("trigger_phrases", []):
            if phrase.lower() in text_lower:
                # Check location restriction if present
                config_location = config.get("location")
                if config_location is None or config_location == location_id:
                    return config
    return None


# =============================================================================
# 2.10 Gossip Operations
# =============================================================================

# Type alias for any gossip entry type
AnyGossipEntry = GossipEntry | BroadcastGossipEntry | NetworkGossipEntry


def create_gossip(
    state: GameState,
    content: str,
    source_npc: ActorId,
    target_npcs: list[ActorId],
    delay_turns: int = 1,
    confession_window: int | None = None,
    gossip_id: GossipId | None = None,
) -> GossipId:
    """Create a point-to-point gossip entry.

    Args:
        state: Game state (mutated)
        content: What happened
        source_npc: Actor ID of source
        target_npcs: Actor IDs who will learn this
        delay_turns: Turns until gossip arrives
        confession_window: Turns after creation when confession helps (None = no window)
        gossip_id: Optional custom ID

    Returns:
        The gossip ID
    """
    queue = get_gossip_queue(state)
    current_turn = get_current_turn(state)

    if gossip_id is None:
        gossip_id = GossipId(f"gossip_{len(queue)}")

    entry: GossipEntry = {
        "id": gossip_id,
        "content": content,
        "source_npc": source_npc,
        "target_npcs": target_npcs,
        "created_turn": current_turn,
        "arrives_turn": TurnNumber(current_turn + delay_turns),
    }

    if confession_window is not None:
        entry["confession_window_until"] = TurnNumber(current_turn + confession_window)

    queue.append(entry)
    return gossip_id


def create_broadcast_gossip(
    state: GameState,
    content: str,
    source_npc: ActorId,
    target_regions: list[str] | str,
    delay_turns: int = 1,
    gossip_id: GossipId | None = None,
) -> GossipId:
    """Create a broadcast gossip that reaches all NPCs in target regions.

    Args:
        state: Game state (mutated)
        content: What happened
        source_npc: Actor ID of source
        target_regions: Region IDs or "ALL" for everywhere
        delay_turns: Turns until gossip arrives
        gossip_id: Optional custom ID

    Returns:
        The gossip ID
    """
    queue = get_gossip_queue(state)
    current_turn = get_current_turn(state)

    if gossip_id is None:
        gossip_id = GossipId(f"broadcast_{len(queue)}")

    # Normalize target_regions to the expected type
    regions: list[str] | str
    if target_regions == "ALL":
        regions = "ALL"
    elif isinstance(target_regions, list):
        regions = target_regions
    else:
        regions = [target_regions]

    entry: BroadcastGossipEntry = {
        "id": gossip_id,
        "type": "broadcast",
        "content": content,
        "source_npc": source_npc,
        "target_regions": regions,  # type: ignore[typeddict-item]
        "created_turn": current_turn,
        "arrives_turn": TurnNumber(current_turn + delay_turns),
    }

    queue.append(entry)  # type: ignore[arg-type]
    return gossip_id


def create_network_gossip(
    state: GameState,
    content: str,
    source_npc: ActorId,
    network_id: str,
    delay_turns: int = 1,
    gossip_id: GossipId | None = None,
) -> GossipId:
    """Create a network gossip that reaches all members of a network.

    Args:
        state: Game state (mutated)
        content: What happened
        source_npc: Actor ID of source
        network_id: Network ID (e.g., "spore_network")
        delay_turns: Turns until gossip arrives
        gossip_id: Optional custom ID

    Returns:
        The gossip ID
    """
    queue = get_gossip_queue(state)
    current_turn = get_current_turn(state)

    if gossip_id is None:
        gossip_id = GossipId(f"network_{len(queue)}")

    entry: NetworkGossipEntry = {
        "id": gossip_id,
        "type": "network",
        "content": content,
        "source_npc": source_npc,
        "network_id": network_id,
        "created_turn": current_turn,
        "arrives_turn": TurnNumber(current_turn + delay_turns),
    }

    queue.append(entry)  # type: ignore[arg-type]
    return gossip_id


def get_gossip_by_id(state: GameState, gossip_id: GossipId) -> AnyGossipEntry | None:
    """Find a gossip entry by ID.

    Args:
        state: Game state
        gossip_id: ID to find

    Returns:
        The entry if found, None otherwise
    """
    queue = get_gossip_queue(state)
    for entry in queue:
        if entry["id"] == gossip_id:
            return entry
    return None


def get_pending_gossip_about(state: GameState, content_substring: str) -> list[AnyGossipEntry]:
    """Get all pending gossip containing a substring.

    Args:
        state: Game state
        content_substring: Substring to search for

    Returns:
        List of matching entries
    """
    queue = get_gossip_queue(state)
    return [e for e in queue if content_substring.lower() in e["content"].lower()]


def get_arrived_gossip(state: GameState) -> list[AnyGossipEntry]:
    """Get gossip that has arrived (arrives_turn <= current turn).

    Does not remove entries - use deliver_due_gossip for that.
    """
    queue = get_gossip_queue(state)
    current_turn = get_current_turn(state)
    return [e for e in queue if e["arrives_turn"] <= current_turn]


def deliver_due_gossip(state: GameState, current_turn: TurnNumber) -> list[AnyGossipEntry]:
    """Get and remove gossip that has arrived at or before current turn.

    This is the main turn-phase handler for gossip delivery.
    Returns the delivered entries so handlers can process effects.

    Args:
        state: Game state (mutated)
        current_turn: Current turn number

    Returns:
        List of gossip entries that were delivered
    """
    queue = get_gossip_queue(state)

    delivered = [e for e in queue if e["arrives_turn"] <= current_turn]
    remaining = [e for e in queue if e["arrives_turn"] > current_turn]

    # Replace the list in place
    queue.clear()
    queue.extend(remaining)

    return delivered  # type: ignore[return-value]


def remove_gossip(state: GameState, gossip_id: GossipId) -> bool:
    """Remove a gossip entry from the queue.

    Args:
        state: Game state (mutated)
        gossip_id: ID of entry to remove

    Returns:
        True if entry was found and removed
    """
    queue = get_gossip_queue(state)
    for i, entry in enumerate(queue):
        if entry["id"] == gossip_id:
            queue.pop(i)
            return True
    return False


def can_confess(state: GameState, gossip_id: GossipId) -> bool:
    """Check if confession is still possible for a gossip entry.

    Args:
        state: Game state
        gossip_id: ID of gossip to check

    Returns:
        True if confession window is still open
    """
    entry = get_gossip_by_id(state, gossip_id)
    if entry is None:
        return False

    # Only point-to-point gossip has confession windows
    if "confession_window_until" not in entry:
        return False

    current_turn = get_current_turn(state)
    window: TurnNumber | None = entry.get("confession_window_until")  # type: ignore[assignment]
    return window is not None and current_turn <= window


# =============================================================================
# 2.11 Companion Operations
# =============================================================================


def get_companion(state: GameState, actor_id: str) -> CompanionState | None:
    """Find a companion by actor ID.

    Args:
        state: Game state
        actor_id: Actor ID to find

    Returns:
        The companion state if found, None otherwise
    """
    companions = get_active_companions(state)
    for c in companions:
        if c["actor_id"] == actor_id:
            return c
    return None


def add_companion(
    state: GameState,
    actor_id: ActorId,
    location_id: LocationId | None = None,
) -> CompanionState | None:
    """Add an actor as a companion.

    Args:
        state: Game state (mutated)
        actor_id: Actor ID to add
        location_id: Current location (for initial comfort check)

    Returns:
        The new companion state, or None if already a companion
    """
    # Check if already a companion
    if get_companion(state, actor_id) is not None:
        return None

    companions = get_active_companions(state)

    companion: CompanionState = {
        "actor_id": actor_id,
        "following": True,
        "comfort_in_current": CompanionComfort.COMFORTABLE,
    }

    companions.append(companion)
    return companion


def remove_companion(state: GameState, actor_id: str) -> bool:
    """Remove an actor from companions.

    Args:
        state: Game state (mutated)
        actor_id: Actor ID to remove

    Returns:
        True if companion was found and removed
    """
    companions = get_active_companions(state)
    for i, c in enumerate(companions):
        if c["actor_id"] == actor_id:
            companions.pop(i)
            return True
    return False


def set_companion_following(state: GameState, actor_id: str, following: bool) -> bool:
    """Set whether a companion is following the player.

    Args:
        state: Game state (mutated)
        actor_id: Actor ID
        following: True if following, False if waiting

    Returns:
        True if companion was found and updated
    """
    companion = get_companion(state, actor_id)
    if companion is None:
        return False

    companion["following"] = following
    return True


def set_companion_waiting(
    state: GameState,
    actor_id: ActorId,
    location_id: LocationId,
) -> bool:
    """Set a companion to wait at a location.

    Args:
        state: Game state (mutated)
        actor_id: Actor ID
        location_id: Location where companion waits

    Returns:
        True if companion was found and updated
    """
    companion = get_companion(state, actor_id)
    if companion is None:
        return False

    companion["following"] = False
    companion["waiting_at"] = location_id
    return True


def update_companion_comfort(
    state: GameState,
    actor_id: str,
    comfort: CompanionComfort,
) -> bool:
    """Update a companion's comfort level.

    Args:
        state: Game state (mutated)
        actor_id: Actor ID
        comfort: New comfort level

    Returns:
        True if companion was found and updated
    """
    companion = get_companion(state, actor_id)
    if companion is None:
        return False

    companion["comfort_in_current"] = comfort
    return True


def get_following_companions(state: GameState) -> list[CompanionState]:
    """Get all companions currently following the player.

    Args:
        state: Game state

    Returns:
        List of following companions
    """
    companions = get_active_companions(state)
    return [c for c in companions if c["following"]]


def check_companion_comfort(
    actor: Actor,
    location_id: str,
) -> CompanionComfort:
    """Check how comfortable an actor would be at a location.

    This is a simple pattern-based check. The actor should have
    'comfort_restrictions' in properties as a dict mapping
    CompanionComfort values to location patterns.

    Args:
        actor: Actor to check
        location_id: Location to check comfort at

    Returns:
        The comfort level at that location
    """
    restrictions = actor.properties.get("comfort_restrictions", {})

    # Check impossible locations first
    impossible_patterns = restrictions.get("impossible", [])
    if isinstance(impossible_patterns, list):
        for pattern in impossible_patterns:
            if matches_pattern(location_id, pattern):
                return CompanionComfort.IMPOSSIBLE

    # Check uncomfortable locations
    uncomfortable_patterns = restrictions.get("uncomfortable", [])
    if isinstance(uncomfortable_patterns, list):
        for pattern in uncomfortable_patterns:
            if matches_pattern(location_id, pattern):
                return CompanionComfort.UNCOMFORTABLE

    # Default to comfortable
    return CompanionComfort.COMFORTABLE


# =============================================================================
# 2.12 Environmental Spread Operations
# =============================================================================


def get_spread(state: GameState, spread_id: str) -> SpreadState | None:
    """Get an environmental spread by ID.

    Args:
        state: Game state
        spread_id: Spread ID to find

    Returns:
        The spread state if found, None otherwise
    """
    spreads = get_environmental_spreads(state)
    return spreads.get(spread_id)


def check_spread_active(state: GameState, spread_id: str) -> bool:
    """Check if a spread is currently active.

    Args:
        state: Game state
        spread_id: Spread ID to check

    Returns:
        True if spread exists and is active
    """
    spread = get_spread(state, spread_id)
    if spread is None:
        return False
    return spread["active"]


def halt_spread(state: GameState, spread_id: str) -> bool:
    """Halt an active spread.

    Args:
        state: Game state (mutated)
        spread_id: Spread ID to halt

    Returns:
        True if spread was active and is now halted
    """
    spread = get_spread(state, spread_id)
    if spread is None:
        return False
    if not spread["active"]:
        return False

    spread["active"] = False
    return True


def activate_spread(state: GameState, spread_id: str) -> bool:
    """Activate an inactive spread.

    Args:
        state: Game state (mutated)
        spread_id: Spread ID to activate

    Returns:
        True if spread was inactive and is now active
    """
    spread = get_spread(state, spread_id)
    if spread is None:
        return False
    if spread["active"]:
        return False

    spread["active"] = True
    return True


def get_spread_progress(
    state: GameState,
    spread_id: str,
) -> tuple[TurnNumber | None, TurnNumber | None]:
    """Get the progress of an environmental spread.

    Args:
        state: Game state
        spread_id: Spread ID to check

    Returns:
        (current_milestone, next_milestone_turn)
        - current_milestone: Turn of last milestone reached, or None
        - next_milestone_turn: Turn of next milestone, or None if no more
    """
    spread = get_spread(state, spread_id)
    if spread is None:
        return (None, None)

    current = spread.get("current_milestone")

    # Find next milestone after current
    milestones = spread.get("milestones", [])
    next_turn: TurnNumber | None = None
    for milestone in milestones:
        turn = milestone["turn"]
        if current is None or turn > current:
            if next_turn is None or turn < next_turn:
                next_turn = turn

    return (current, next_turn)


def get_due_milestones(
    state: GameState,
    spread_id: str,
    current_turn: TurnNumber,
) -> list[SpreadMilestone]:
    """Get milestones that are due to be applied.

    Returns milestones where turn <= current_turn and turn > current_milestone.

    Args:
        state: Game state
        spread_id: Spread ID to check
        current_turn: Current game turn

    Returns:
        List of milestones that should be applied
    """
    spread = get_spread(state, spread_id)
    if spread is None:
        return []
    if not spread["active"]:
        return []

    current_milestone = spread.get("current_milestone")
    milestones = spread.get("milestones", [])

    due = []
    for milestone in milestones:
        turn = milestone["turn"]
        # Due if: turn has arrived AND hasn't been processed yet
        if turn <= current_turn:
            if current_milestone is None or turn > current_milestone:
                due.append(milestone)

    # Sort by turn to process in order
    due.sort(key=lambda m: m["turn"])
    return due


def mark_milestone_reached(
    state: GameState,
    spread_id: str,
    milestone_turn: TurnNumber,
) -> bool:
    """Mark a milestone as reached.

    Args:
        state: Game state (mutated)
        spread_id: Spread ID
        milestone_turn: Turn of milestone reached

    Returns:
        True if spread was found and updated
    """
    spread = get_spread(state, spread_id)
    if spread is None:
        return False

    spread["current_milestone"] = milestone_turn
    return True


def create_spread(
    state: GameState,
    spread_id: str,
    halt_flag: str,
    milestones: list[SpreadMilestone],
    active: bool = True,
) -> SpreadState:
    """Create a new environmental spread.

    Args:
        state: Game state (mutated)
        spread_id: Unique ID for the spread
        halt_flag: Global flag name that halts this spread when True
        milestones: List of milestones with turns and effects
        active: Whether spread starts active

    Returns:
        The created spread state
    """
    spreads = get_environmental_spreads(state)

    spread: SpreadState = {
        "active": active,
        "halt_flag": halt_flag,
        "milestones": milestones,
    }

    spreads[spread_id] = spread
    return spread


def check_spread_halt_flag(state: GameState, spread_id: str) -> bool:
    """Check if a spread's halt flag is set.

    Args:
        state: Game state
        spread_id: Spread ID to check

    Returns:
        True if the halt flag is set (spread should stop)
    """
    spread = get_spread(state, spread_id)
    if spread is None:
        return False

    halt_flag = spread["halt_flag"]
    flags = get_global_flags(state)
    return get_bool_flag(flags, halt_flag)


# =============================================================================
# 4.2 Validation Functions
# =============================================================================


def validate_commitment_configs(state: GameState) -> list[str]:
    """Validate commitment configurations.

    Checks:
    - Each config has required fields (id, target_npc, goal, trigger_phrases)
    - trigger_phrases is a non-empty list
    - base_timer is positive if present

    Args:
        state: Game state to validate

    Returns:
        List of error messages (empty if valid)
    """
    errors: list[str] = []
    configs = get_commitment_configs(state)

    for config_id, config in configs.items():
        prefix = f"Commitment config '{config_id}'"

        # Check required fields
        if "id" not in config:
            errors.append(f"{prefix} missing 'id' field")
        elif config["id"] != config_id:
            errors.append(f"{prefix} has mismatched id: {config['id']}")

        if "target_npc" not in config:
            errors.append(f"{prefix} missing 'target_npc' field")

        if "goal" not in config:
            errors.append(f"{prefix} missing 'goal' field")

        if "trigger_phrases" not in config:
            errors.append(f"{prefix} missing 'trigger_phrases' field")
        elif not isinstance(config["trigger_phrases"], list):
            errors.append(f"{prefix} 'trigger_phrases' must be a list")
        elif len(config["trigger_phrases"]) == 0:
            errors.append(f"{prefix} 'trigger_phrases' cannot be empty")

        # Check optional fields
        if "base_timer" in config:
            if not isinstance(config["base_timer"], int) or config["base_timer"] <= 0:
                errors.append(f"{prefix} 'base_timer' must be a positive integer")

        if "hope_bonus" in config:
            if not isinstance(config["hope_bonus"], int) or config["hope_bonus"] < 0:
                errors.append(f"{prefix} 'hope_bonus' must be a non-negative integer")

    return errors


def validate_state_machines(state: GameState) -> list[str]:
    """Validate state machine configurations on actors.

    Checks:
    - Each state machine has 'states' list
    - Each state machine has 'initial' state
    - Initial state is in states list
    - Current state (if set) is in states list

    Args:
        state: Game state to validate

    Returns:
        List of error messages (empty if valid)
    """
    errors: list[str] = []

    for actor_id, actor in state.actors.items():
        if "state_machine" not in actor.properties:
            continue

        sm = actor.properties["state_machine"]
        prefix = f"Actor '{actor_id}' state_machine"

        if "states" not in sm:
            errors.append(f"{prefix} missing 'states' field")
            continue

        states = sm["states"]
        if not isinstance(states, list) or len(states) == 0:
            errors.append(f"{prefix} 'states' must be a non-empty list")
            continue

        if "initial" not in sm:
            errors.append(f"{prefix} missing 'initial' field")
        elif sm["initial"] not in states:
            errors.append(f"{prefix} 'initial' state '{sm['initial']}' not in states")

        if "current" in sm and sm["current"] not in states:
            errors.append(f"{prefix} 'current' state '{sm['current']}' not in states")

    return errors


def validate_spreads(state: GameState) -> list[str]:
    """Validate environmental spread definitions.

    Checks:
    - Each spread has halt_flag
    - Each spread has milestones list
    - Milestones are in ascending turn order
    - Each milestone has turn and effects

    Args:
        state: Game state to validate

    Returns:
        List of error messages (empty if valid)
    """
    errors: list[str] = []
    spreads = get_environmental_spreads(state)

    for spread_id, spread in spreads.items():
        prefix = f"Spread '{spread_id}'"

        # Check required fields
        if "halt_flag" not in spread:
            errors.append(f"{prefix} missing 'halt_flag'")

        if "milestones" not in spread:
            errors.append(f"{prefix} missing 'milestones'")
            continue

        # Check milestone ordering
        milestones = spread["milestones"]
        last_turn = 0
        for i, milestone in enumerate(milestones):
            if "turn" not in milestone:
                errors.append(f"{prefix} milestone {i} missing 'turn'")
            elif milestone["turn"] <= last_turn:
                errors.append(
                    f"{prefix} milestones not in ascending order at index {i}"
                )
            else:
                last_turn = milestone["turn"]

            if "effects" not in milestone:
                errors.append(f"{prefix} milestone {i} missing 'effects'")

    return errors


def validate_gossip_references(state: GameState) -> list[str]:
    """Validate gossip queue entries.

    Checks:
    - Each gossip has required fields (content, source_npc)
    - Point-to-point gossip has target_npcs
    - Broadcast gossip has target_regions
    - Network gossip has network_id

    Args:
        state: Game state to validate

    Returns:
        List of error messages (empty if valid)
    """
    errors: list[str] = []
    queue = get_gossip_queue(state)

    for i, gossip in enumerate(queue):
        gossip_id = gossip.get("id", f"index_{i}")
        prefix = f"Gossip '{gossip_id}'"

        # Check required fields
        if "content" not in gossip:
            errors.append(f"{prefix} missing 'content'")

        if "source_npc" not in gossip:
            errors.append(f"{prefix} missing 'source_npc'")

        # Check type-specific fields
        gossip_type = gossip.get("type", "point_to_point")

        if gossip_type == "point_to_point":
            if "target_npcs" not in gossip:
                errors.append(f"{prefix} missing 'target_npcs' for point-to-point gossip")
            elif not isinstance(gossip["target_npcs"], list):
                errors.append(f"{prefix} 'target_npcs' must be a list")

        elif gossip_type == "broadcast":
            if "target_regions" not in gossip:
                errors.append(f"{prefix} missing 'target_regions' for broadcast gossip")

        elif gossip_type == "network":
            if "network_id" not in gossip:
                errors.append(f"{prefix} missing 'network_id' for network gossip")

    return errors


def validate_companion_restrictions(state: GameState) -> list[str]:
    """Validate companion state data.

    Checks:
    - Each companion has required fields (actor_id, status)
    - Status is valid (following, waiting)
    - Referenced actor exists

    Args:
        state: Game state to validate

    Returns:
        List of error messages (empty if valid)
    """
    errors: list[str] = []
    companions = get_active_companions(state)

    for i, companion in enumerate(companions):
        companion_id = companion.get("actor_id", f"index_{i}")
        prefix = f"Companion '{companion_id}'"

        # Check required fields
        if "actor_id" not in companion:
            errors.append(f"Companion at index {i} missing 'actor_id'")
            continue

        actor_id = companion["actor_id"]
        if actor_id not in state.actors:
            errors.append(f"{prefix} references non-existent actor")

        # Validate following/waiting state
        if "following" not in companion:
            errors.append(f"{prefix} missing 'following' flag")
        elif not isinstance(companion["following"], bool):
            errors.append(f"{prefix} has non-boolean 'following' flag")

    return errors


def validate_zone_consistency(state: GameState) -> list[str]:
    """Validate zone consistency across locations.

    Checks:
    - Temperature zones are valid values
    - Water levels are valid values

    Args:
        state: Game state to validate

    Returns:
        List of error messages (empty if valid)
    """
    from src.infrastructure_types import TemperatureZone, WaterLevel

    errors: list[str] = []
    valid_temps = {z.value for z in TemperatureZone}
    valid_water = {w.value for w in WaterLevel}

    for loc in state.locations:
        prefix = f"Location '{loc.id}'"

        # Check temperature zone if present
        if "temperature_zone" in loc.properties:
            temp = loc.properties["temperature_zone"]
            if temp not in valid_temps:
                errors.append(f"{prefix} has invalid temperature_zone: {temp}")

        # Check water level if present
        if "water_level" in loc.properties:
            water = loc.properties["water_level"]
            if water not in valid_water:
                errors.append(f"{prefix} has invalid water_level: {water}")

    return errors


def validate_infrastructure(state: GameState) -> list[str]:
    """Validate all infrastructure data structures.

    This is the main entry point for infrastructure validation.
    Called by engine when metadata.validation_module is set.

    Args:
        state: Game state to validate

    Returns:
        List of error messages (empty if all valid)
    """
    errors: list[str] = []

    errors.extend(validate_commitment_configs(state))
    errors.extend(validate_state_machines(state))
    errors.extend(validate_zone_consistency(state))
    errors.extend(validate_companion_restrictions(state))
    errors.extend(validate_gossip_references(state))
    errors.extend(validate_spreads(state))

    return errors
