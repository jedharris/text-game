# Infrastructure Detailed Design

This document captures the detailed design for The Shattered Meridian's game-wide infrastructure systems. It is the implementation companion to `infrastructure_spec_v2.md`.

## Relationship to Infrastructure Spec v2.0

`infrastructure_spec_v2.md` defines **what** the systems do using JSON schemas and high-level APIs.
This document defines **how** to implement them using Python types, utility functions, and behavior modules.

**Systems Covered Here (with spec section)**:
- §1 Commitment System → Section 3.5 Commitment System
- §2 Echo Trust System → Section 3.4 Trust System
- §3 Gossip Propagation System → Section 3.8 Information Networks (Gossip)
- §4 Companion System → Section 3.7 Companion System
- §5 Environmental Systems → Section 3.6 Environmental System
- §10 Puzzle System → Section 3.9 Puzzle System
- §14 Flag System → Section 3.1 Flag System
- §15 Turn and Timing System → Section 3.2 Turn/Timer System
- Condition System (new) → Section 3.3 Condition System

**Systems NOT Yet in Detailed Design** (remain in spec only):
- §6 NPC State and Services (game-specific behaviors)
- §7 Dialog System Integration (LLM integration)
- §8 Waystone and Ending System (game-specific)
- §9 Branding and Reputation System (game-specific)
- §11 Information Network System (spore network covered partially under Gossip)
- §12 Collection Quest System (game-specific)
- §13 Branding System (game-specific)
- §16 Item and Inventory System (existing engine feature)
- §17 Skill System (game-specific)
- §18 Narration Integration (LLM integration)

The systems marked "game-specific" will be implemented as behaviors within the game, using the infrastructure utilities defined here.

## Relationship to game_wide_rules.md

`game_wide_rules.md` is the authoritative source for game-specific values including:
- Commitment timer base values and hope bonuses
- Gossip propagation delays
- Environmental spread timelines

This document defines the infrastructure utilities; `game_wide_rules.md` defines the authoritative values used by those utilities.

## Design Principles

1. **Type Safety**: Use NewType wrappers, typed dicts, avoid `Any` and untyped strings
2. **Shared Utilities**: Factor common operations into reusable functions
3. **Fail Loudly**: Validation errors surface at load time, not runtime
4. **Behavior-Driven**: Infrastructure provides behavior modules that games layer
5. **Data-Driven**: Configuration in game_state.json, logic in behavior modules

## Design Process

Each phase follows this sequence:

1. **Design**: Specify data structures, behaviors, integration points
2. **Review**: Check for cross-system consistency, unnecessary complexity, architectural fit
3. **Consolidate**: Identify duplicate patterns, extract shared utilities, align types
4. **Write Tests**: Write tests against the API (without implementation). This validates:
   - Interface usability (awkward parameter lists, missing defaults)
   - Edge cases (empty lists, past deadlines, missing data)
   - Type alignment (casts needed, missing fields)
5. **Revise**: Update design based on test-writing insights

Tests are written but not run until implementation. The value is in writing them - forcing concrete use of the API surface.

## Document Structure

- **Part 1**: Type Definitions - New types for infrastructure
- **Part 2**: Core Utilities - Shared functions used across systems
- **Part 3**: System Designs - Each infrastructure system in detail
- **Part 4**: Integration - Turn loop, validation, game state schema

---

# Part 1: Type Definitions

Infrastructure introduces new semantic types. These go in `src/infrastructure_types.py` to keep `src/types.py` focused on core engine types.

## 1.1 ID Types

```python
from typing import NewType

# Turn tracking
TurnNumber = NewType('TurnNumber', int)
"""Turn count value. Used consistently for deadlines, durations, timestamps."""

# Commitment tracking
CommitmentId = NewType('CommitmentId', str)
"""Unique identifier for a commitment (e.g., 'commit_save_garrett')."""

# Gossip/information
GossipId = NewType('GossipId', str)
"""Unique identifier for a gossip entry (e.g., 'gossip_player_abandoned_sira')."""

# Scheduled events
ScheduledEventId = NewType('ScheduledEventId', str)
"""Unique identifier for a scheduled event (e.g., 'event_cold_spread_75')."""
```

**Note on Flags vs Properties**:
- **Flags** (`actor.flags`, `state.extra["flags"]`): Bool and int values only
  - Bool: `visited_nexus`, `met_sira`, `crystal_restored`
  - Int: `wolves_befriended`, `times_died`, `turns_in_cold`
- **Properties** (`actor.properties`, `location.properties`): Entity references, complex data
  - IDs: `current_region: LocationId`, `last_companion: ActorId`
  - Structured: `state_machine`, `conditions`, `trust`

This separation keeps flags simple and typed, while properties handle everything else.

## 1.2 Enumerated Types

Using `StrEnum` for values that appear in JSON and need string serialization:

```python
from enum import StrEnum

class TemperatureZone(StrEnum):
    """Temperature classification for locations."""
    NORMAL = "normal"
    COLD = "cold"
    FREEZING = "freezing"
    EXTREME_COLD = "extreme_cold"

class WaterLevel(StrEnum):
    """Water depth classification for locations."""
    DRY = "dry"
    ANKLE = "ankle"
    WAIST = "waist"
    CHEST = "chest"
    SUBMERGED = "submerged"

class ConditionType(StrEnum):
    """Types of conditions that can affect actors."""
    HYPOTHERMIA = "hypothermia"
    DROWNING = "drowning"
    BLEEDING = "bleeding"
    INFECTION = "infection"
    EXHAUSTION = "exhaustion"
    POISON = "poison"

class CommitmentState(StrEnum):
    """State of a commitment."""
    ACTIVE = "active"
    FULFILLED = "fulfilled"
    WITHDRAWN = "withdrawn"
    ABANDONED = "abandoned"

class CompanionComfort(StrEnum):
    """How comfortable a companion is in a region/location."""
    COMFORTABLE = "comfortable"
    UNCOMFORTABLE = "uncomfortable"
    IMPOSSIBLE = "impossible"
```

## 1.3 Typed Dictionaries

For complex structures that appear in `properties` or `extra`:

```python
from typing import TypedDict, NotRequired

class StateMachineConfig(TypedDict):
    """Configuration for an NPC state machine."""
    states: list[str]
    initial: str
    current: NotRequired[str]  # Runtime state, defaults to initial

class ConditionInstance(TypedDict):
    """An active condition on an actor."""
    type: ConditionType
    severity: int  # 0-100 typically
    source: NotRequired[str]  # What caused it (location, item, etc.)

class CommitmentConfig(TypedDict):
    """A commitment declaration in game state."""
    id: CommitmentId
    target_npc: ActorId
    goal: str
    trigger_phrases: list[str]
    hope_extends_survival: bool
    hope_bonus: NotRequired[int]  # Turns added to NPC survival
    base_timer: NotRequired[int]  # Turns until commitment failure if timed
    fulfillment_flag: NotRequired[str]  # Flag that must be set to fulfill

class ActiveCommitment(TypedDict):
    """Runtime state of an active commitment."""
    id: CommitmentId
    config_id: str  # Reference to CommitmentConfig
    state: CommitmentState
    made_at_turn: TurnNumber
    deadline_turn: NotRequired[TurnNumber]  # If timed
    hope_applied: bool

class GossipEntry(TypedDict):
    """A piece of gossip in the propagation queue."""
    id: GossipId
    content: str  # What happened
    source_npc: ActorId
    target_npcs: list[ActorId]  # Who will eventually know
    created_turn: TurnNumber
    arrives_turn: TurnNumber  # When it reaches targets
    confession_window_until: NotRequired[TurnNumber]  # Turn when confession no longer helps

class ScheduledEvent(TypedDict):
    """An event scheduled to fire at a specific turn."""
    id: ScheduledEventId
    trigger_turn: TurnNumber
    event_type: str  # Handler looks this up
    data: NotRequired[dict[str, str]]  # Event-specific parameters

class TrustState(TypedDict):
    """Trust tracking for an NPC or the Echo."""
    current: int
    floor: NotRequired[int]  # Minimum from negative actions
    recovery_cap: NotRequired[int]  # Max recoverable per visit
    recovered_this_visit: NotRequired[int]  # Amount recovered in current visit
    last_recovery_turn: NotRequired[TurnNumber]  # Turn of last recovery action
```

## 1.4 Companion Types

```python
class CompanionRestriction(TypedDict):
    """Where a companion can/cannot go."""
    location_patterns: list[str]  # Glob patterns like "sunken_district/*"
    comfort: CompanionComfort
    reason: NotRequired[str]  # For narration

class CompanionState(TypedDict):
    """Runtime state of a companion."""
    actor_id: ActorId
    following: bool
    waiting_at: NotRequired[LocationId]
    comfort_in_current: CompanionComfort
```

## 1.5 Gossip Types

```python
class GossipType(StrEnum):
    """Type of gossip propagation."""
    POINT_TO_POINT = "point_to_point"  # Specific source to specific targets
    BROADCAST = "broadcast"  # Source to all NPCs in target regions
    NETWORK = "network"  # Source to all members of a network

class BroadcastGossipEntry(TypedDict):
    """Gossip that broadcasts to all NPCs in target regions.

    Note: For property-based targeting (e.g., "all fungal creatures"),
    use NetworkGossipEntry instead. Broadcast gossip delivers to ALL
    NPCs in the target regions without filtering.
    """
    id: GossipId
    type: Literal["broadcast"]
    content: str
    source_npc: ActorId
    target_regions: list[str] | Literal["ALL"]  # Region IDs or "ALL"
    created_turn: TurnNumber
    arrives_turn: TurnNumber

class NetworkGossipEntry(TypedDict):
    """Gossip that broadcasts to all members of a network."""
    id: GossipId
    type: Literal["network"]
    content: str
    source_npc: ActorId
    network_id: str  # "spore_network", "criminal_network", etc.
    created_turn: TurnNumber
    arrives_turn: TurnNumber

class NetworkDefinition(TypedDict):
    """Definition of a gossip network based on actor properties."""
    property_name: str  # Actor property to check (e.g., "fungal")
    property_value: bool | str | int  # Required value (e.g., True)
```

## 1.6 Environmental Spread Types

```python
class SpreadEffect(TypedDict):
    """An effect applied at a spread milestone."""
    locations: list[str]  # Glob patterns like "beast_wilds/*"
    property_name: str  # Location property to modify
    property_value: str | int | bool  # New value

class SpreadMilestone(TypedDict):
    """A milestone in an environmental spread."""
    turn: TurnNumber
    effects: list[SpreadEffect]

class SpreadState(TypedDict):
    """State of an environmental spread."""
    active: bool
    halt_flag: str  # Global flag that halts this spread when True
    milestones: list[SpreadMilestone]
    current_milestone: NotRequired[TurnNumber]  # Last milestone reached
```

---

# Part 2: Core Utilities

Shared functions that multiple systems use. These go in `src/infrastructure_utils.py`.

## 2.1 Timer Operations

All timer functions use `TurnNumber` for type safety. At runtime these are ints,
but the type wrapper catches bugs where non-turn values are passed.

```python
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
```

## 2.2 Trust/Numeric Value Operations

```python
def modify_trust(
    current: int,
    delta: int,
    floor: int | None = None,
    ceiling: int | None = None
) -> int:
    """Modify a trust value with optional bounds.

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

def calculate_recovery_amount(
    current: int,
    target: int,
    max_per_session: int,
    recovered_this_session: int
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
    recovery_cap: int = 3
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
    last_turn = trust_state.get("last_recovery_turn", 0)

    # Check if session expired (new visit)
    if current_turn - last_turn > 10:
        trust_state["recovery_cap"] = recovery_cap
        trust_state["recovered_this_visit"] = 0

    # Calculate actual recovery
    remaining = trust_state.get("recovery_cap", recovery_cap) - trust_state.get("recovered_this_visit", 0)
    actual = min(recovery_amount, remaining)

    if actual > 0:
        trust_state["current"] = trust_state["current"] + actual
        trust_state["recovered_this_visit"] = trust_state.get("recovered_this_visit", 0) + actual
        trust_state["last_recovery_turn"] = current_turn

    return actual, trust_state["current"]
```

## 2.3 State Machine Operations

```python
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

def transition_state(
    config: StateMachineConfig,
    new_state: str
) -> tuple[bool, str]:
    """Attempt to transition to a new state.

    Returns (success, message). Modifies config in place if successful.
    """
    if new_state not in config["states"]:
        return False, f"Invalid state: {new_state}"

    old_state = get_current_state(config)
    config["current"] = new_state
    return True, f"Transitioned from {old_state} to {new_state}"
```

## 2.4 Condition Operations

```python
def get_actor_conditions(actor: Actor) -> list[ConditionInstance]:
    """Get an actor's conditions list, initializing if needed."""
    if "conditions" not in actor.properties:
        actor.properties["conditions"] = []
    return actor.properties["conditions"]

def create_condition(
    condition_type: ConditionType,
    initial_severity: int = 0,
    source: str | None = None
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
    max_severity: int = 100
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
    condition_type: ConditionType
) -> ConditionInstance | None:
    """Find a condition by type in a list."""
    for condition in conditions:
        if condition["type"] == condition_type:
            return condition
    return None

def remove_condition(
    conditions: list[ConditionInstance],
    condition_type: ConditionType
) -> bool:
    """Remove a condition by type. Returns True if removed."""
    for i, condition in enumerate(conditions):
        if condition["type"] == condition_type:
            conditions.pop(i)
            return True
    return False

def has_condition(
    conditions: list[ConditionInstance],
    condition_type: ConditionType
) -> bool:
    """Check if a condition exists."""
    return get_condition(conditions, condition_type) is not None

def get_condition_severity(
    conditions: list[ConditionInstance],
    condition_type: ConditionType
) -> int:
    """Get severity of a condition, or 0 if not present."""
    condition = get_condition(conditions, condition_type)
    return condition["severity"] if condition else 0
```

## 2.5 Flag Operations

Flags are stored in different places depending on scope:
- Actor flags (including player): `actor.flags`
- Global flags: `state.extra["flags"]`

**Flags are bool or int only.** Entity references and complex data go in `properties`.
Typed accessors enforce consistency - use `get_bool_flag` for bools, `get_int_flag` for ints.

**Note on flag names**: Flag *values* must be bool or int, but flag *names* can be dynamically
generated at runtime (e.g., `knows_gossip_123`). This is common for systems that track
knowledge of specific events.

```python
# Boolean flag operations
def get_bool_flag(flags: dict[str, bool], name: str, default: bool = False) -> bool:
    """Get a boolean flag value."""
    return flags.get(name, default)

def set_bool_flag(flags: dict[str, bool], name: str, value: bool) -> None:
    """Set a boolean flag."""
    flags[name] = value

def check_bool_flag(flags: dict[str, bool], name: str) -> bool:
    """Check if a boolean flag is True (shorthand for get_bool_flag with default False)."""
    return flags.get(name, False)

# Integer flag operations
def get_int_flag(flags: dict[str, int], name: str, default: int = 0) -> int:
    """Get an integer flag value."""
    return flags.get(name, default)

def set_int_flag(flags: dict[str, int], name: str, value: int) -> None:
    """Set an integer flag."""
    flags[name] = value

def increment_int_flag(flags: dict[str, int], name: str, delta: int = 1) -> int:
    """Increment an integer flag, returning new value."""
    current = flags.get(name, 0)
    flags[name] = current + delta
    return flags[name]

# Common operations (work on any flag type)
def clear_flag(flags: dict[str, bool | int], name: str) -> bool:
    """Remove a flag. Returns True if it existed."""
    if name in flags:
        del flags[name]
        return True
    return False

def has_flag(flags: dict[str, bool | int], name: str) -> bool:
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
```

## 2.6 Collection Accessors

Helper functions for accessing infrastructure collections in `state.extra`.

**Design note**: These accessors initialize collections if missing, ensuring callers can
always append to the returned list. This is consistent with `get_global_flags`.

```python
def get_active_commitments(state: GameState) -> list[ActiveCommitment]:
    """Get list of active commitments, initializing if needed."""
    if "active_commitments" not in state.extra:
        state.extra["active_commitments"] = []
    return state.extra["active_commitments"]

def get_gossip_queue(state: GameState) -> list[GossipEntry]:
    """Get the gossip propagation queue, initializing if needed."""
    if "gossip_queue" not in state.extra:
        state.extra["gossip_queue"] = []
    return state.extra["gossip_queue"]

def get_scheduled_events(state: GameState) -> list[ScheduledEvent]:
    """Get list of scheduled events, initializing if needed."""
    if "scheduled_events" not in state.extra:
        state.extra["scheduled_events"] = []
    return state.extra["scheduled_events"]

def get_echo_trust(state: GameState) -> TrustState:
    """Get Echo trust state, initializing if needed."""
    if "echo_trust" not in state.extra:
        state.extra["echo_trust"] = {"current": 0}
    return state.extra["echo_trust"]

def get_active_companions(state: GameState) -> list[CompanionState]:
    """Get list of active companions, initializing if needed."""
    if "companions" not in state.extra:
        state.extra["companions"] = []
    return state.extra["companions"]

def get_environmental_spreads(state: GameState) -> dict[str, SpreadState]:
    """Get environmental spreads dict, initializing if needed."""
    if "environmental_spreads" not in state.extra:
        state.extra["environmental_spreads"] = {}
    return state.extra["environmental_spreads"]

def get_network_definitions(state: GameState) -> dict[str, NetworkDefinition]:
    """Get gossip network definitions, initializing if needed."""
    if "networks" not in state.extra:
        state.extra["networks"] = {}
    return state.extra["networks"]
```

## 2.7 Pattern Matching Utilities

Shared utilities for matching location IDs against glob-like patterns.

```python
import fnmatch

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
    return [
        loc_id for loc_id in state.locations.keys()
        if matches_pattern(loc_id, pattern)
    ]

def matches_any_pattern(target: str, patterns: list[str]) -> bool:
    """Check if target matches any of the given patterns."""
    return any(matches_pattern(target, p) for p in patterns)
```

---

# Part 3: System Designs

## 3.1 Flag System

**Purpose**: Store boolean and simple value flags for tracking game state.

**Storage**:
- Actor flags (including player): `actor.flags`
- Global flags: `state.extra["flags"]`

**Naming Conventions**:
- Player progression: `knows_*`, `visited_*`, `completed_*`
- NPC relationships: `met_*`, `helped_*`, `betrayed_*`
- Global state: `crystal_*_restored`, `waystone_*_placed`
- Commitment outcomes: `broke_promise_*`, `fulfilled_promise_*`

**No Behavior Module Needed**: Flags are simple data. The utilities above provide typed access. Other systems set/check flags as side effects.

---

## 3.2 Turn/Timer System

**Purpose**: Track game turns, manage scheduled events, check deadlines.

**Storage**:
- Turn counter: `state.turn_count` (already exists)
- Scheduled events: `state.extra["scheduled_events"]: list[ScheduledEvent]`

**Behavior Module**: `behavior_libraries/infrastructure_lib/timing.py`

**Vocabulary**:
```python
VOCABULARY = {
    "events": [
        {
            "event": "on_scheduled_event_check",
            "hook": "turn_phase_scheduled",
            "description": "Check and fire scheduled events"
        }
    ]
}
```

**Turn Phase Handler**:
```python
def on_scheduled_event_check(
    entity: None,
    accessor: StateAccessor,
    context: dict[str, str]
) -> EventResult:
    """Check for and fire scheduled events this turn.

    Fires events where trigger_turn <= current turn.
    Removes fired events from queue.
    """
    current_turn = accessor.state.turn_count
    events = get_scheduled_events(accessor.state)

    fired_messages: list[str] = []
    remaining: list[ScheduledEvent] = []

    for event in events:
        if event["trigger_turn"] <= current_turn:
            # Fire event - dispatch to appropriate handler
            message = fire_scheduled_event(event, accessor)
            if message:
                fired_messages.append(message)
        else:
            remaining.append(event)

    accessor.state.extra["scheduled_events"] = remaining

    return EventResult(
        allow=True,
        message="\n".join(fired_messages) if fired_messages else None
    )
```

**Game-Specific Functions**:

`fire_scheduled_event(event, accessor)` - Dispatches events to appropriate handlers based on `event_type`. This is game-specific because the game defines what event types exist and how to handle them.

**API Functions**:
```python
def schedule_event(
    state: GameState,
    event_type: str,
    turns_from_now: int,
    event_id: ScheduledEventId | None = None,
    data: dict[str, str] | None = None
) -> ScheduledEventId:
    """Schedule an event to fire in the future."""

def cancel_scheduled_event(
    state: GameState,
    event_id: ScheduledEventId
) -> bool:
    """Cancel a scheduled event. Returns True if found and cancelled."""

def reschedule_event(
    state: GameState,
    event_id: ScheduledEventId,
    new_trigger_turn: int
) -> bool:
    """Change when a scheduled event fires."""
```

---

## 3.3 Condition System

**Purpose**: Track progressive conditions affecting actors (hypothermia, bleeding, etc.)

**Storage**:
- Actor conditions: `actor.properties["conditions"]: list[ConditionInstance]`

**Behavior Module**: `behavior_libraries/infrastructure_lib/conditions.py`

**Vocabulary**:
```python
VOCABULARY = {
    "events": [
        {
            "event": "on_condition_tick",
            "hook": "condition_tick",
            "description": "Progress conditions each turn"
        }
    ]
}
```

**Condition Tick Handler**:
```python
def on_condition_tick(
    entity: None,
    accessor: StateAccessor,
    context: dict[str, str]
) -> EventResult:
    """Progress all actor conditions.

    For each actor with conditions:
    - Apply severity changes based on condition type and location
    - Check for severity thresholds (warnings, damage, incapacitation)
    - Remove conditions that reach 0 severity
    """
    messages: list[str] = []

    for actor_id, actor in accessor.state.actors.items():
        conditions = actor.properties.get("conditions", [])
        if not conditions:
            continue

        actor_messages = tick_actor_conditions(actor, accessor)
        messages.extend(actor_messages)

    return EventResult(
        allow=True,
        message="\n".join(messages) if messages else None
    )
```

**Condition-Specific Logic**:

Each condition type has its own tick behavior. The following functions are **game-specific implementations** - infrastructure defines the pattern, game code provides the handlers:

- `tick_actor_conditions(actor, accessor)` - iterates conditions, calls type-specific handlers
- `tick_drowning`, `tick_bleeding`, `tick_infection`, `tick_exhaustion`, `tick_poison` - game-specific
- `check_hypothermia_thresholds(actor, severity)` - returns warning messages at severity milestones

```python
CONDITION_TICK_HANDLERS: dict[ConditionType, ConditionTickHandler] = {
    ConditionType.HYPOTHERMIA: tick_hypothermia,
    ConditionType.DROWNING: tick_drowning,
    ConditionType.BLEEDING: tick_bleeding,
    ConditionType.INFECTION: tick_infection,
    ConditionType.EXHAUSTION: tick_exhaustion,
    ConditionType.POISON: tick_poison,
}

# Example implementation for hypothermia (others follow similar pattern)
def tick_hypothermia(
    actor: Actor,
    condition: ConditionInstance,
    accessor: StateAccessor
) -> list[str]:
    """Tick hypothermia based on location temperature and protection."""
    location = accessor.get_location(actor.location)
    temp_zone = get_temperature_zone(location)
    protection = get_cold_protection(actor, accessor)

    rate = calculate_hypothermia_rate(temp_zone, protection)

    if rate > 0:
        new_severity = modify_condition_severity(condition, rate)
        return check_hypothermia_thresholds(actor, new_severity)
    elif rate < 0:
        # Recovery in warm area
        new_severity = modify_condition_severity(condition, rate)
        if new_severity == 0:
            remove_condition(actor.properties["conditions"], ConditionType.HYPOTHERMIA)
            return [f"{actor.name} has fully warmed up."]

    return []
```

**API Functions**:
```python
def apply_condition(
    actor: Actor,
    condition_type: ConditionType,
    initial_severity: int = 0,
    source: str | None = None
) -> ConditionInstance:
    """Apply a condition to an actor, or increase severity if already present."""

def cure_condition(
    actor: Actor,
    condition_type: ConditionType,
    amount: int | None = None  # None = full cure
) -> bool:
    """Reduce or remove a condition. Returns True if actor had the condition."""

def get_actor_condition(
    actor: Actor,
    condition_type: ConditionType
) -> ConditionInstance | None:
    """Get an actor's condition of a specific type."""

def get_cold_protection(actor: Actor, accessor: StateAccessor) -> float:
    """Calculate cold protection for an actor from all sources.

    Protection sources (checked in order, stacking):
    1. Equipment: cold_weather_gear (0.5), cold_resistance_cloak (1.0)
    2. Companions: salamander warmth aura (1.0) if within range
    3. Location: hot_springs instant cure, warm zones (1.0)
    4. Actor properties: cold_immunity flag (infinite)

    Returns:
        Protection factor (0.0 = none, 0.5 = halved, 1.0 = full immunity)
    """
    # Check actor immunity
    if actor.properties.get("cold_immunity"):
        return 1.0

    protection = 0.0

    # Check equipment
    for item_id in actor.properties.get("equipped", []):
        item = accessor.get_item(item_id)
        if item:
            protection += item.properties.get("cold_protection", 0.0)

    # Check companion auras
    companions = get_active_companions(accessor.state)
    for companion in companions:
        if companion["following"]:
            companion_actor = accessor.get_actor(companion["actor_id"])
            if companion_actor and companion_actor.properties.get("provides_warmth_aura"):
                protection += 1.0  # Salamander provides full protection

    # Check location warmth
    location = accessor.get_location(actor.location)
    if location:
        if location.properties.get("hypothermia_effect") == "instant_cure":
            protection = 1.0  # Hot springs
        elif location.properties.get("warm_zone"):
            protection += 1.0

    return min(protection, 1.0)  # Cap at full protection

def get_temperature_zone(location: Location) -> TemperatureZone:
    """Get the temperature zone for a location."""
    zone_str = location.properties.get("temperature_zone", "normal")
    try:
        return TemperatureZone(zone_str)
    except ValueError:
        return TemperatureZone.NORMAL

def calculate_hypothermia_rate(zone: TemperatureZone, protection: float) -> int:
    """Calculate hypothermia rate based on zone and protection.

    Base rates per zone (per turn):
    - NORMAL: -10 (recovery)
    - COLD: +5
    - FREEZING: +10
    - EXTREME_COLD: +20

    Protection reduces positive rates (protection 0.5 = halve rate).
    Full protection (1.0) = no hypothermia gain.
    """
    BASE_RATES: dict[TemperatureZone, int] = {
        TemperatureZone.NORMAL: -10,
        TemperatureZone.COLD: 5,
        TemperatureZone.FREEZING: 10,
        TemperatureZone.EXTREME_COLD: 20,
    }
    base_rate = BASE_RATES.get(zone, 0)

    if base_rate <= 0:
        return base_rate  # Recovery not affected by protection

    # Protection reduces rate
    effective_rate = base_rate * (1.0 - protection)
    return int(effective_rate)
```

---

## 3.4 Trust System

**Purpose**: Track relationship values with NPCs and the Echo.

**Storage**:
- Echo trust: `state.extra["echo_trust"]: TrustState`
- NPC trust: `actor.properties["trust"]: TrustState` (on the NPC actor)

**Design Notes**:
- Echo trust is special: -6 floor (refuses to appear at -6), unbounded positive
- NPC trust varies by NPC definition
- Recovery caps prevent immediate redemption

**No Separate Behavior Module**: Trust modifications happen as side effects of other actions. The utilities provide typed access. Commitment system and other behaviors call these.

**API Functions**:
```python
def modify_echo_trust(state: GameState, delta: int) -> int:
    """Modify Echo trust, respecting bounds. Returns new value."""
    trust_state = get_echo_trust(state)
    new_value = modify_trust(
        trust_state["current"],
        delta,
        floor=-6,
        ceiling=None  # Unbounded positive
    )
    trust_state["current"] = new_value
    return new_value

def modify_npc_trust(
    actor: Actor,
    delta: int,
    floor: int | None = None,
    ceiling: int | None = None
) -> int:
    """Modify NPC trust. Returns new value."""
    if "trust" not in actor.properties:
        actor.properties["trust"] = {"current": 0}
    trust_state: TrustState = actor.properties["trust"]

    # Use NPC-specific bounds if defined
    effective_floor = floor if floor is not None else trust_state.get("floor")
    effective_ceiling = ceiling if ceiling is not None else trust_state.get("ceiling")

    new_value = modify_trust(
        trust_state["current"],
        delta,
        floor=effective_floor,
        ceiling=effective_ceiling
    )
    trust_state["current"] = new_value
    return new_value

def calculate_echo_chance(trust: int, base_chance: float = 0.2) -> float:
    """Calculate the probability of Echo appearing based on trust.

    Args:
        trust: Current Echo trust value
        base_chance: Base probability (default 0.2)

    Returns:
        Probability between 0.05 and 0.95, or 0.0 if trust <= -6 (refuses to appear)
    """
    if trust <= -6:
        return 0.0  # Refuses to appear

    modifier = trust * 0.1
    return max(0.05, min(0.95, base_chance + modifier))

def check_echo_appears(
    state: GameState,
    base_chance: float = 0.2,
    random_value: float | None = None
) -> bool:
    """Check if Echo appears based on trust level.

    Args:
        state: Game state
        base_chance: Base probability (default 0.2)
        random_value: If provided, use this instead of random.random() (for testing)

    Returns:
        True if Echo appears
    """
    trust = get_echo_trust(state)["current"]
    chance = calculate_echo_chance(trust, base_chance)

    if random_value is not None:
        return random_value < chance

    import random
    return random.random() < chance
```

---

## 3.5 Commitment System

**Purpose**: Track promises made to NPCs, with timers, hope bonuses, and outcomes.

**Storage**:
- Commitment configs (definitions): `state.extra["commitment_configs"]: dict[str, CommitmentConfig]`
- Active commitments (runtime): `state.extra["active_commitments"]: list[ActiveCommitment]`

**Behavior Module**: `behavior_libraries/infrastructure_lib/commitments.py`

**Vocabulary**:
```python
VOCABULARY = {
    "events": [
        {
            "event": "on_commitment_check",
            "hook": "turn_phase_commitment",
            "description": "Check commitment deadlines each turn"
        }
    ]
}
```

**Commitment Lifecycle**:

1. **Detection**: Player says trigger phrase near target NPC
2. **Activation**: Commitment becomes active, deadline set based on `base_timer`
3. **Hope Bonus**: If `hope_extends_survival`, extend NPC's death timer by `hope_bonus` turns
4. **Tracking**: Each turn, check for deadline expiry
5. **Resolution**: Fulfilled (player action triggers), withdrawn (explicit), or abandoned (deadline passed)

**Hope Bonus Mechanism**:

The hope bonus extends the NPC's death condition timer, not the commitment deadline. For example:
- Garrett is drowning with 5 turns until death
- Player commits to saving him (`hope_extends_survival: true`, `hope_bonus: 3`)
- Garrett's death timer extends to 8 turns
- The commitment deadline is separate (based on `base_timer`)

This is implemented by modifying the NPC's condition:
```python
def apply_hope_bonus(commitment: ActiveCommitment, config: CommitmentConfig, accessor: StateAccessor) -> None:
    """Apply hope bonus to NPC survival timer."""
    if not config.get("hope_extends_survival"):
        return
    if commitment["hope_applied"]:
        return  # Already applied

    npc = accessor.get_actor(config["target_npc"])
    if not npc:
        return

    # Find the NPC's critical condition and extend it
    conditions = get_actor_conditions(npc)
    for condition in conditions:
        if condition["severity"] >= 50:  # Critical threshold
            # Reduce severity by hope_bonus worth of turns
            # (severity maps to turns remaining in condition tick)
            bonus = config.get("hope_bonus", 3)
            modify_condition_severity(condition, -bonus * 10)  # 10 severity per turn
            commitment["hope_applied"] = True
            break
```

**Fulfillment Detection**:

Commitment fulfillment is detected via behavior, not automatically. The game defines:
- Fulfillment conditions in `CommitmentConfig` (e.g., "garrett_rescued" flag set)
- Behavior handlers that call `fulfill_commitment` when conditions met
- This allows complex multi-step fulfillment (rescue requires: reach garrett, take him, bring to safety)

**Turn Phase Handler**:
```python
def on_commitment_check(
    entity: None,
    accessor: StateAccessor,
    context: dict[str, str]
) -> EventResult:
    """Check commitment deadlines and update states."""
    current_turn = accessor.state.turn_count
    commitments = get_active_commitments(accessor.state)

    messages: list[str] = []

    for commitment in commitments:
        if commitment["state"] != CommitmentState.ACTIVE:
            continue

        deadline = commitment.get("deadline_turn")
        if deadline and check_deadline(current_turn, deadline):
            # Deadline passed - mark as abandoned
            message = abandon_commitment(commitment, accessor)
            messages.append(message)

    return EventResult(
        allow=True,
        message="\n".join(messages) if messages else None
    )
```

**API Functions**:
```python
def make_commitment(
    state: GameState,
    config_id: str,
    current_turn: int
) -> ActiveCommitment:
    """Create a new active commitment from a config."""

def fulfill_commitment(
    state: GameState,
    commitment_id: CommitmentId,
    accessor: StateAccessor
) -> str:
    """Mark commitment as fulfilled, apply bonuses, return narration."""

def withdraw_commitment(
    state: GameState,
    commitment_id: CommitmentId,
    accessor: StateAccessor
) -> str:
    """Explicitly withdraw from commitment, return narration."""

def abandon_commitment(
    commitment: ActiveCommitment,
    accessor: StateAccessor
) -> str:
    """Handle commitment abandonment (deadline passed or NPC died)."""

def check_commitment_phrase(
    text: str,
    location: Location,
    accessor: StateAccessor
) -> CommitmentConfig | None:
    """Check if player text matches any commitment trigger phrase."""
```

---

## 3.6 Environmental System

**Purpose**: Define location zones, apply environmental conditions, handle spreads.

**Storage**:
- Zone properties on locations: `location.properties["temperature"]`, `location.properties["water_level"]`, etc.
- Spread state: `state.extra["environmental_spreads"]: dict[str, SpreadState]`

**Behavior Module**: `behavior_libraries/infrastructure_lib/environment.py`

**Vocabulary**:
```python
VOCABULARY = {
    "events": [
        {
            "event": "on_environment_tick",
            "hook": "environmental_effect",
            "description": "Apply environmental effects each turn"
        }
    ]
}
```

**Environment Tick Handler**:
```python
def on_environment_tick(
    entity: None,
    accessor: StateAccessor,
    context: dict[str, str]
) -> EventResult:
    """Apply environmental effects to actors based on their locations."""
    messages: list[str] = []

    for actor_id, actor in accessor.state.actors.items():
        location = accessor.get_location(actor.location)
        if not location:
            continue

        actor_messages = apply_location_effects(actor, location, accessor)
        messages.extend(actor_messages)

    return EventResult(
        allow=True,
        message="\n".join(messages) if messages else None
    )
```

**Game-Specific Functions**:

`apply_location_effects(actor, location, accessor)` - Applies location-specific environmental effects (cold, water, hazards). This is game-specific because it depends on what environmental hazards exist in the game.

**Zone Helpers**:
```python
def get_temperature_zone(location: Location) -> TemperatureZone:
    """Get location's temperature zone, defaulting to NORMAL."""
    temp = location.properties.get("temperature", "normal")
    return TemperatureZone(temp)

def get_water_level(location: Location) -> WaterLevel:
    """Get location's water level, defaulting to DRY."""
    level = location.properties.get("water_level", "dry")
    return WaterLevel(level)

def is_breathable(location: Location) -> bool:
    """Check if location has breathable air."""
    return location.properties.get("breathable", True)

def is_safe_zone(location: Location) -> bool:
    """Check if location is a safe zone (no hazards)."""
    return location.properties.get("safe_zone", False)
```

---

## 3.7 Companion System

**Purpose**: Track companions, enforce restrictions, handle waiting behavior.

**Storage**:
- Active companions: `state.extra["companions"]: list[CompanionState]`
- Companion restrictions (on NPC definition): `actor.properties["companion_restrictions"]: list[CompanionRestriction]`

**Behavior Module**: `behavior_libraries/infrastructure_lib/companions.py`

**Key Behaviors**:
- **Movement blocking**: When player moves, check if companions can follow
- **Waiting**: Companions that can't follow wait at last valid location
- **Rejoining**: Companions rejoin when player returns

**Movement Hook**:
```python
def on_player_move(
    entity: None,
    accessor: StateAccessor,
    context: dict[str, str]
) -> EventResult:
    """Check companion restrictions when player moves."""
    destination = context.get("destination")
    if not destination:
        return EventResult(allow=True)

    companions = get_active_companions(accessor.state)
    messages: list[str] = []

    for companion in companions:
        if not companion["following"]:
            continue

        comfort = check_companion_comfort(
            companion["actor_id"],
            LocationId(destination),
            accessor
        )

        if comfort == CompanionComfort.IMPOSSIBLE:
            # Companion cannot follow
            message = companion_refuses_to_follow(companion, destination, accessor)
            messages.append(message)
        elif comfort == CompanionComfort.UNCOMFORTABLE:
            # Companion follows reluctantly
            message = companion_follows_reluctantly(companion, destination, accessor)
            messages.append(message)

    return EventResult(
        allow=True,
        message="\n".join(messages) if messages else None
    )
```

**API Functions**:
```python
def check_companion_comfort(
    actor_id: ActorId,
    location_id: LocationId,
    accessor: StateAccessor
) -> CompanionComfort:
    """Check how comfortable a companion is at a location.

    Matches location against companion's restriction patterns.
    Returns COMFORTABLE if no restrictions match.
    """
    actor = accessor.get_actor(actor_id)
    if not actor:
        return CompanionComfort.IMPOSSIBLE

    restrictions = actor.properties.get("companion_restrictions", [])
    location = accessor.get_location(location_id)
    if not location:
        return CompanionComfort.IMPOSSIBLE

    for restriction in restrictions:
        if matches_any_pattern(location_id, restriction["location_patterns"]):
            return CompanionComfort(restriction["comfort"])

    return CompanionComfort.COMFORTABLE

# Note: matches_any_pattern is defined in Section 2.7 Pattern Matching Utilities

def add_companion(
    state: GameState,
    actor_id: ActorId,
    accessor: StateAccessor
) -> bool:
    """Add a companion to the player's party.

    Returns False if party is full (max 2) or actor is already a companion.
    """
    companions = get_active_companions(state)

    # Check max companions
    if len(companions) >= 2:
        return False

    # Check not already following
    for comp in companions:
        if comp["actor_id"] == actor_id:
            return False

    # Get initial comfort at player's location
    player = accessor.get_actor(ActorId("player"))
    comfort = CompanionComfort.COMFORTABLE
    if player:
        comfort = check_companion_comfort(actor_id, player.location, accessor)

    companions.append({
        "actor_id": actor_id,
        "following": True,
        "comfort_in_current": comfort
    })
    return True

def remove_companion(
    state: GameState,
    actor_id: ActorId
) -> bool:
    """Remove a companion from the player's party. Returns True if found."""
    companions = get_active_companions(state)
    for i, comp in enumerate(companions):
        if comp["actor_id"] == actor_id:
            companions.pop(i)
            return True
    return False

def companion_refuses_to_follow(
    companion: CompanionState,
    destination: str,
    accessor: StateAccessor
) -> str:
    """Handle companion refusing to enter a location. Updates state, returns message."""
    # Mark companion as waiting
    companion["following"] = False
    player = accessor.get_actor(ActorId("player"))
    if player:
        companion["waiting_at"] = player.location

    actor = accessor.get_actor(companion["actor_id"])
    name = actor.name if actor else "Your companion"
    return f"{name} cannot follow you there."

def companion_follows_reluctantly(
    companion: CompanionState,
    destination: str,
    accessor: StateAccessor
) -> str:
    """Handle companion following reluctantly. Returns message."""
    companion["comfort_in_current"] = CompanionComfort.UNCOMFORTABLE
    actor = accessor.get_actor(companion["actor_id"])
    name = actor.name if actor else "Your companion"
    return f"{name} follows you reluctantly."

def get_companion(
    state: GameState,
    actor_id: ActorId
) -> CompanionState | None:
    """Get a companion by actor ID."""
    for comp in get_active_companions(state):
        if comp["actor_id"] == actor_id:
            return comp
    return None
```

---

## 3.8 Information Networks (Gossip)

**Purpose**: Propagate information about player actions with delays.

**Storage**:
- Gossip queue: `state.extra["gossip_queue"]: list[GossipEntry]`

**Behavior Module**: `behavior_libraries/infrastructure_lib/gossip.py`

**Vocabulary**:
```python
VOCABULARY = {
    "events": [
        {
            "event": "on_gossip_propagate",
            "hook": "turn_phase_gossip",
            "description": "Deliver gossip that has reached its destination"
        }
    ]
}
```

**Gossip Turn Handler**:
```python
def on_gossip_propagate(
    entity: None,
    accessor: StateAccessor,
    context: dict[str, str]
) -> EventResult:
    """Deliver gossip entries that have arrived."""
    current_turn = accessor.state.turn_count
    queue = get_gossip_queue(accessor.state)

    delivered: list[GossipEntry] = []
    remaining: list[GossipEntry] = []

    for entry in queue:
        if entry["arrives_turn"] <= current_turn:
            deliver_gossip(entry, accessor)
            delivered.append(entry)
        else:
            remaining.append(entry)

    accessor.state.extra["gossip_queue"] = remaining

    # No player-visible message - gossip is background
    return EventResult(allow=True)
```

**API Functions**:
```python
def create_gossip(
    state: GameState,
    content: str,
    source_npc: ActorId,
    target_npcs: list[ActorId],
    delay_turns: int,
    confession_window: int | None = None
) -> GossipId:
    """Create a new gossip entry to propagate.

    Args:
        state: Game state
        content: Description of what happened
        source_npc: NPC who witnessed the action
        target_npcs: NPCs who will eventually learn about it
        delay_turns: Turns until gossip arrives (1 for spore network, 3-5 normal)
        confession_window: Turns during which confession helps (None = no window)

    Returns:
        ID of the created gossip entry
    """
    queue = get_gossip_queue(state)
    gossip_id = GossipId(f"gossip_{len(queue)}_{state.turn_count}")

    entry: GossipEntry = {
        "id": gossip_id,
        "content": content,
        "source_npc": source_npc,
        "target_npcs": target_npcs,
        "created_turn": state.turn_count,
        "arrives_turn": state.turn_count + delay_turns
    }
    if confession_window is not None:
        entry["confession_window_until"] = state.turn_count + confession_window

    queue.append(entry)
    return gossip_id

def deliver_gossip(entry: GossipEntry, accessor: StateAccessor) -> None:
    """Deliver a gossip entry to its target NPCs.

    Sets flags on target NPCs indicating they know about the content.
    May affect trust relationships.
    """
    content = entry["content"]
    for npc_id in entry["target_npcs"]:
        npc = accessor.get_actor(npc_id)
        if not npc:
            continue

        # Set flag indicating NPC knows this gossip
        flag_name = f"knows_{entry['id']}"
        if "flags" not in npc.properties:
            npc.properties["flags"] = {}
        npc.properties["flags"][flag_name] = True

        # Trust impact is handled by specific gossip content handlers
        # This is a generic delivery - game defines content-specific effects

def confess_action(
    state: GameState,
    gossip_id: GossipId,
    to_npc: ActorId
) -> bool:
    """Player confesses before gossip arrives.

    Returns True if confession is within the window and removes gossip from queue.
    Confession typically reduces trust impact compared to being found out.
    """
    queue = get_gossip_queue(state)
    current_turn = state.turn_count

    for i, entry in enumerate(queue):
        if entry["id"] == gossip_id:
            window_end = entry.get("confession_window_until")
            if window_end is None or current_turn > window_end:
                return False  # No confession window or window expired

            # Remove from queue (player confessed)
            queue.pop(i)
            return True

    return False  # Gossip not found

def get_gossip_by_id(state: GameState, gossip_id: GossipId) -> GossipEntry | None:
    """Get a gossip entry by ID."""
    for entry in get_gossip_queue(state):
        if entry["id"] == gossip_id:
            return entry
    return None

def get_pending_gossip_about(state: GameState, content_substring: str) -> list[GossipEntry]:
    """Get all pending gossip entries containing a substring in content."""
    results: list[GossipEntry] = []
    for entry in get_gossip_queue(state):
        if content_substring in entry["content"]:
            results.append(entry)
    return results

def create_broadcast_gossip(
    state: GameState,
    content: str,
    source_npc: ActorId,
    target_regions: list[str] | Literal["ALL"],
    delay_turns: int
) -> GossipId:
    """Create gossip that broadcasts to all NPCs in specified regions.

    At delivery time, expands target_regions to all active NPCs in those regions.
    For property-based targeting (e.g., "all fungal creatures"), use
    create_network_gossip() instead.

    Args:
        state: Game state
        content: Description of what happened
        source_npc: NPC who originated the gossip
        target_regions: List of region IDs or "ALL" for all regions
        delay_turns: Turns until gossip arrives

    Returns:
        ID of the created gossip entry
    """
    queue = get_gossip_queue(state)
    gossip_id = GossipId(f"broadcast_{len(queue)}_{state.turn_count}")

    entry: BroadcastGossipEntry = {
        "id": gossip_id,
        "type": "broadcast",
        "content": content,
        "source_npc": source_npc,
        "target_regions": target_regions,
        "created_turn": TurnNumber(state.turn_count),
        "arrives_turn": TurnNumber(state.turn_count + delay_turns)
    }
    queue.append(entry)
    return gossip_id

def create_network_gossip(
    state: GameState,
    content: str,
    source_npc: ActorId,
    network_id: str,
    delay_turns: int
) -> GossipId:
    """Create gossip that broadcasts to all members of a network.

    Networks are defined by actor properties (e.g., 'fungal: true' for spore network).
    At delivery time, finds all NPCs matching the network property.

    Args:
        state: Game state
        content: Description of what happened
        source_npc: NPC who originated the gossip
        network_id: ID of the network (e.g., "spore_network", "criminal_network")
        delay_turns: Turns until gossip arrives (typically 1 for spore network)

    Returns:
        ID of the created gossip entry
    """
    queue = get_gossip_queue(state)
    gossip_id = GossipId(f"network_{len(queue)}_{state.turn_count}")

    entry: NetworkGossipEntry = {
        "id": gossip_id,
        "type": "network",
        "content": content,
        "source_npc": source_npc,
        "network_id": network_id,
        "created_turn": TurnNumber(state.turn_count),
        "arrives_turn": TurnNumber(state.turn_count + delay_turns)
    }
    queue.append(entry)
    return gossip_id
```

**Delivery for Broadcast/Network Gossip**:

The `on_gossip_delivery` handler checks entry type and expands targets:
- For `type: "broadcast"`: iterate all NPCs in target_regions
- For `type: "network"`: iterate all NPCs with matching network property
- For regular gossip: deliver to explicit target_npcs list

**Network Definitions** (stored in `state.extra["networks"]`):

Networks are defined by actor properties. Example configuration:
```json
{
  "networks": {
    "spore_network": {"property_name": "fungal", "property_value": true},
    "criminal_network": {"property_name": "criminal", "property_value": true}
  }
}
```

---

## 3.9 Puzzle System

**Purpose**: Support multi-solution puzzles and cumulative threshold puzzles.

**Storage**:
- Puzzle state on items/locations: `entity.properties["puzzle"]`
- Two puzzle types supported: multi-solution and cumulative-threshold

**Behavior Module**: `behavior_libraries/infrastructure_lib/puzzles.py`

### 3.9.1 Multi-Solution Puzzles

For puzzles with discrete alternative solutions (use item A OR item B OR skill C):

**Types**:
```python
class PuzzleSolution(TypedDict):
    """One valid solution to a puzzle."""
    id: str
    requirements: list[str]  # Flags or conditions that must be true
    difficulty: NotRequired[str]  # "easy", "medium", "hard"
    discovery_hint: NotRequired[str]

class MultiSolutionPuzzle(TypedDict):
    """State of a multi-solution puzzle."""
    type: Literal["multi_solution"]
    solutions: list[PuzzleSolution]
    solved: bool
    solved_via: NotRequired[str]  # Which solution was used
```

**API Functions**:
```python
def check_puzzle_solved(
    entity: Entity,
    accessor: StateAccessor
) -> tuple[bool, str | None]:
    """Check if any solution requirements are met.

    Iterates through solutions, checks if all requirements for any
    solution are satisfied. Requirements are flag names that must be True.

    Returns:
        (True, solution_id) if solved
        (False, None) if not solved
    """
    puzzle = entity.properties.get("puzzle")
    if not puzzle or puzzle.get("solved"):
        return puzzle.get("solved", False), puzzle.get("solved_via") if puzzle else None

    for solution in puzzle.get("solutions", []):
        if all_requirements_met(solution["requirements"], accessor):
            puzzle["solved"] = True
            puzzle["solved_via"] = solution["id"]
            return True, solution["id"]

    return False, None

def get_available_solutions(
    entity: Entity,
    accessor: StateAccessor
) -> list[PuzzleSolution]:
    """Get solutions the player could potentially use.

    Returns solutions where the player has at least one requirement met,
    or solutions with no special requirements.
    """
    puzzle = entity.properties.get("puzzle")
    if not puzzle:
        return []

    available: list[PuzzleSolution] = []
    for solution in puzzle.get("solutions", []):
        reqs = solution["requirements"]
        if not reqs or any_requirement_met(reqs, accessor):
            available.append(solution)

    return available

def check_flag(flag_name: str, accessor: StateAccessor) -> bool:
    """Check if a flag is set (checks both global and player flags).

    Args:
        flag_name: Name of the flag to check
        accessor: State accessor

    Returns:
        True if flag is set and truthy
    """
    # Check global flags first
    global_flags = get_global_flags(accessor.state)
    if check_bool_flag(global_flags, flag_name):
        return True

    # Check player flags
    player = accessor.get_actor(ActorId("player"))
    if player:
        return check_bool_flag(get_actor_flags(player), flag_name)

    return False

def all_requirements_met(requirements: list[str], accessor: StateAccessor) -> bool:
    """Check if all requirement flags are True."""
    return all(check_flag(req, accessor) for req in requirements)

def any_requirement_met(requirements: list[str], accessor: StateAccessor) -> bool:
    """Check if any requirement flag is True."""
    return any(check_flag(req, accessor) for req in requirements)
```

### 3.9.2 Cumulative Threshold Puzzles

For puzzles where you accumulate a value to reach a threshold (light puzzles, weight puzzles):

**Types**:
```python
class CumulativeThresholdPuzzle(TypedDict):
    """Puzzle solved by accumulating a value to a threshold."""
    type: Literal["cumulative_threshold"]
    current_value: int
    target_value: int
    solved: bool
    contributions: dict[str, int]  # source_id -> contribution amount
    contribution_durations: NotRequired[dict[str, int]]  # source_id -> turns remaining
    decay_per_turn: NotRequired[int]  # If contributions fade
    on_solve_flag: NotRequired[str]  # Flag to set when solved
```

**Example** (Fungal Depths light puzzle):
```python
# On the location
location.properties["puzzle"] = {
    "type": "cumulative_threshold",
    "current_value": 2,      # Current light level
    "target_value": 6,       # Success threshold
    "solved": False,
    "contributions": {},
    "contribution_durations": {}
}

# On each mushroom item
item.states["glowing"] = False
item.properties["light_contribution"] = 2  # How much this adds when glowing
```

**API Functions**:
```python
def add_puzzle_contribution(
    entity: Entity,
    source_id: str,
    amount: int,
    duration: int | None = None
) -> bool:
    """Add a contribution to a cumulative puzzle.

    Args:
        entity: The entity with the puzzle
        source_id: Unique ID of the contributing source
        amount: How much to contribute
        duration: Turns until contribution expires (None = permanent)

    Returns:
        True if puzzle is now solved, False otherwise
    """
    puzzle = entity.properties.get("puzzle")
    if not puzzle or puzzle.get("type") != "cumulative_threshold":
        return False

    puzzle["contributions"][source_id] = amount
    if duration is not None:
        if "contribution_durations" not in puzzle:
            puzzle["contribution_durations"] = {}
        puzzle["contribution_durations"][source_id] = duration

    # Recalculate current value
    puzzle["current_value"] = sum(puzzle["contributions"].values())

    # Check if solved
    if puzzle["current_value"] >= puzzle["target_value"] and not puzzle["solved"]:
        puzzle["solved"] = True
        return True

    return False

def remove_puzzle_contribution(
    entity: Entity,
    source_id: str
) -> None:
    """Remove a contribution from a cumulative puzzle."""
    puzzle = entity.properties.get("puzzle")
    if not puzzle or puzzle.get("type") != "cumulative_threshold":
        return

    if source_id in puzzle["contributions"]:
        del puzzle["contributions"][source_id]
        puzzle["current_value"] = sum(puzzle["contributions"].values())

    durations = puzzle.get("contribution_durations", {})
    if source_id in durations:
        del durations[source_id]

def tick_puzzle_contributions(
    entity: Entity
) -> bool:
    """Tick contribution durations and remove expired ones.

    Call this in the turn phase to handle time-limited contributions.

    Returns:
        True if puzzle state changed (contribution expired or solved state changed)
    """
    puzzle = entity.properties.get("puzzle")
    if not puzzle or puzzle.get("type") != "cumulative_threshold":
        return False

    durations = puzzle.get("contribution_durations", {})
    if not durations:
        return False

    changed = False
    expired: list[str] = []

    for source_id, remaining in durations.items():
        durations[source_id] = remaining - 1
        if durations[source_id] <= 0:
            expired.append(source_id)

    for source_id in expired:
        remove_puzzle_contribution(entity, source_id)
        changed = True

    return changed

def get_puzzle_progress(entity: Entity) -> tuple[int, int] | None:
    """Get current and target values for a cumulative puzzle.

    Returns:
        (current_value, target_value) or None if not a cumulative puzzle
    """
    puzzle = entity.properties.get("puzzle")
    if not puzzle or puzzle.get("type") != "cumulative_threshold":
        return None
    return puzzle["current_value"], puzzle["target_value"]

def is_puzzle_solved(entity: Entity) -> bool:
    """Check if a puzzle is solved (works for both puzzle types)."""
    puzzle = entity.properties.get("puzzle")
    return puzzle.get("solved", False) if puzzle else False
```

### 3.9.3 NPC Services

NPC services (merchants, healers, information brokers) are not infrastructure-level systems. They are implemented as game-specific behaviors using the general behavior system. Infrastructure provides the trust and flag systems that services can check for availability.

---

## 3.10 Environmental Spread System

**Purpose**: Track game-wide environmental effects that spread between regions over time unless halted by player actions.

**Examples**:
- Spore spread: If Spore Mother not healed, spores spread to other regions at turn milestones
- Cold spread: If Observatory telescope not repaired, cold spreads to other regions at turn milestones

**Storage**:
- `state.extra["environmental_spreads"]: dict[str, SpreadState]`

**Behavior Module**: `behavior_libraries/infrastructure_lib/spreads.py`

**Vocabulary**:
```python
VOCABULARY = {
    "events": [
        {
            "event": "on_spread_check",
            "hook": "turn_phase_spread",
            "description": "Check environmental spread milestones each turn"
        }
    ]
}
```

**Data Structure Example** (in game_state.json):
```json
{
  "extra": {
    "environmental_spreads": {
      "spore_spread": {
        "active": true,
        "halt_flag": "spore_mother_healed",
        "milestones": [
          {
            "turn": 50,
            "effects": [
              {"locations": ["beast_wilds/*"], "property_name": "spore_level", "property_value": "low"}
            ]
          },
          {
            "turn": 100,
            "effects": [
              {"locations": ["civilized_remnants/town_gate"], "property_name": "infection_check", "property_value": true}
            ]
          },
          {
            "turn": 150,
            "effects": [
              {"locations": ["civilized_remnants/*"], "property_name": "infection_present", "property_value": true}
            ]
          }
        ]
      },
      "cold_spread": {
        "active": true,
        "halt_flag": "observatory_functional",
        "milestones": [
          {
            "turn": 75,
            "effects": [
              {"locations": ["beast_wilds/forest_edge"], "property_name": "temperature_zone", "property_value": "cold"}
            ]
          },
          {
            "turn": 125,
            "effects": [
              {"locations": ["nexus_chamber"], "property_name": "temperature_zone", "property_value": "cold"}
            ]
          },
          {
            "turn": 175,
            "effects": [
              {"locations": ["sunken_district/*"], "property_name": "water_frozen", "property_value": true}
            ]
          }
        ]
      }
    }
  }
}
```

**Turn Phase Handler**:
```python
def on_spread_check(
    entity: None,
    accessor: StateAccessor,
    context: dict[str, str]
) -> EventResult:
    """Check environmental spreads each turn.

    For each active spread:
    1. Check if halt flag is set - if so, deactivate spread
    2. Check if current turn matches a milestone
    3. If milestone reached, apply effects to matching locations
    """
    messages: list[str] = []
    current_turn = accessor.state.turn_count
    spreads = get_environmental_spreads(accessor.state)
    global_flags = get_global_flags(accessor.state)

    for spread_id, spread in spreads.items():
        if not spread["active"]:
            continue

        # Check halt condition
        if check_bool_flag(global_flags, spread["halt_flag"]):
            spread["active"] = False
            messages.append(f"The {spread_id.replace('_', ' ')} has been halted.")
            continue

        # Check for milestone
        for milestone in spread["milestones"]:
            if milestone["turn"] == current_turn:
                affected = apply_spread_effects(milestone["effects"], accessor)
                spread["current_milestone"] = milestone["turn"]
                if affected:
                    messages.append(
                        f"Environmental changes spread to {len(affected)} locations."
                    )

    return EventResult(
        allow=True,
        message="\n".join(messages) if messages else None
    )
```

**API Functions**:
```python
def check_spread_active(state: GameState, spread_id: str) -> bool:
    """Check if a spread is still active."""
    spreads = get_environmental_spreads(state)
    spread = spreads.get(spread_id)
    return spread["active"] if spread else False

def halt_spread(state: GameState, spread_id: str) -> bool:
    """Halt a spread (e.g., when halt condition met).

    Returns:
        True if spread was active and is now halted, False otherwise.
    """
    spreads = get_environmental_spreads(state)
    spread = spreads.get(spread_id)
    if spread and spread["active"]:
        spread["active"] = False
        return True
    return False

def apply_spread_effects(
    effects: list[SpreadEffect],
    accessor: StateAccessor
) -> list[str]:
    """Apply spread effects to matching locations.

    Returns:
        List of affected location IDs.
    """
    affected: list[str] = []

    for effect in effects:
        for pattern in effect["locations"]:
            matching_locations = find_matching_locations(pattern, accessor.state)
            for location_id in matching_locations:
                location = accessor.get_location(location_id)
                if location:
                    location.properties[effect["property_name"]] = effect["property_value"]
                    affected.append(location_id)

    return affected

def get_spread_progress(
    state: GameState,
    spread_id: str
) -> tuple[TurnNumber | None, TurnNumber | None]:
    """Get progress of an environmental spread.

    Returns:
        (current_milestone, next_milestone_turn) or (None, None) if spread doesn't exist.
        next_milestone_turn is None if no more milestones remain.
    """
    spreads = get_environmental_spreads(state)
    spread = spreads.get(spread_id)
    if not spread:
        return (None, None)

    current = spread.get("current_milestone")
    current_turn = state.turn_count

    # Find next milestone
    next_turn: TurnNumber | None = None
    for milestone in spread["milestones"]:
        if milestone["turn"] > current_turn:
            next_turn = milestone["turn"]
            break

    return (current, next_turn)

# Note: Pattern matching uses find_matching_locations from Section 2.7 Pattern Matching Utilities
```

**Validation**:
```python
def validate_spreads(state: GameState) -> list[str]:
    """Validate environmental spread definitions."""
    errors: list[str] = []
    spreads = get_environmental_spreads(state)

    for spread_id, spread in spreads.items():
        # Check required fields
        if "halt_flag" not in spread:
            errors.append(f"Spread '{spread_id}' missing halt_flag")
        if "milestones" not in spread:
            errors.append(f"Spread '{spread_id}' missing milestones")
            continue

        # Check milestone ordering
        last_turn = 0
        for i, milestone in enumerate(spread["milestones"]):
            if "turn" not in milestone:
                errors.append(f"Spread '{spread_id}' milestone {i} missing turn")
            elif milestone["turn"] <= last_turn:
                errors.append(
                    f"Spread '{spread_id}' milestones not in ascending order at {i}"
                )
            else:
                last_turn = milestone["turn"]

            if "effects" not in milestone:
                errors.append(f"Spread '{spread_id}' milestone {i} missing effects")

    return errors
```

---

# Part 4: Integration

## 4.1 Turn Phase Order

The infrastructure adds new turn phases. Combined order:

```python
TURN_PHASE_HOOKS = [
    "turn_phase_scheduled",      # Fire scheduled events
    "turn_phase_commitment",     # Check commitment deadlines
    "turn_phase_gossip",         # Deliver arrived gossip
    "turn_phase_spread",         # Check environmental spread milestones
    hooks.NPC_ACTION,            # NPCs take actions
    hooks.ENVIRONMENTAL_EFFECT,  # Environmental effects (now includes zones)
    hooks.CONDITION_TICK,        # Conditions progress
    hooks.DEATH_CHECK,           # Check for actor deaths
]
```

## 4.2 Validation Module

The game provides `behaviors/infrastructure/validation.py`:

```python
def validate_infrastructure(state: GameState) -> list[str]:
    """Validate all infrastructure data structures."""
    errors: list[str] = []

    errors.extend(validate_commitment_configs(state))
    errors.extend(validate_state_machines(state))
    errors.extend(validate_zone_consistency(state))
    errors.extend(validate_companion_restrictions(state))
    errors.extend(validate_gossip_references(state))
    errors.extend(validate_spreads(state))  # Section 3.10

    return errors
```

Called by engine when `metadata.validation_module` is set.

**Note**: The individual validation functions (`validate_commitment_configs`, `validate_state_machines`, etc.) are to be implemented based on each system's data structures. `validate_spreads` is defined in Section 3.10.

## 4.3 Game State Schema

Infrastructure data in `game_state.json`:

```json
{
  "metadata": {
    "validation_module": "examples.big_game.behaviors.infrastructure.validation_v1"
  },
  "extra": {
    "flags": {},
    "echo_trust": {"current": 0},
    "active_commitments": [],
    "commitment_configs": {},
    "gossip_queue": [],
    "scheduled_events": [],
    "companions": [],
    "environmental_spreads": {}
  },
  "actors": {
    "npc_garrett": {
      "properties": {
        "state_machine": {
          "states": ["drowning", "stabilized", "rescued", "dead"],
          "initial": "drowning"
        },
        "conditions": [],
        "trust": {"current": 0},
        "commitment_target": true
      }
    }
  },
  "locations": [
    {
      "id": "loc_frozen_pass",
      "properties": {
        "temperature": "cold",
        "hypothermia_rate": 5
      }
    }
  ]
}
```

---

# Appendix A: Phase Notes

After each phase, record consolidation opportunities, test insights, and design revisions.

## Phase 1 (Foundations)

**Systems**: Core utilities, Flag system, Turn/Timer system

### Consolidation

Completed consolidation review:

1. **Added `TurnNumber` type**: All timer operations now use `TurnNumber` NewType for type safety on turn values.

2. **Consistent collection initialization**: All collection accessors (`get_active_commitments`, `get_gossip_queue`, `get_scheduled_events`, `get_echo_trust`) now initialize if missing, matching `get_global_flags` behavior.

3. **Flag scope helpers added**: `get_player_flags` and `get_actor_flags` added for consistency with `get_global_flags`.

### Test Insights

Tests written in `tests/infrastructure/test_phase1_design.py`.

Insights from test writing:

1. **Interface is usable**: The API surface is clean - functions take obvious parameters, return sensible types.

2. **Edge cases identified**:
   - `get_bool_flag` with missing key returns default (False)
   - `check_deadline` at exactly the deadline turn returns `True` (deadline has passed)
   - `get_player_flags` when no player exists returns empty dict (safe default)

3. **Mock complexity is minimal**: Tests only need simple mock objects with `extra` dict and `flags` dict.

### Design Revisions

1. **Flags restricted to bool and int**: Removed string flags. Entity references go in `properties`, not `flags`. This provides:
   - Type safety via typed accessors (`get_bool_flag`, `get_int_flag`)
   - Clear separation of concerns (flags = simple state, properties = complex data)
   - Prevents accidental type mixing within a single flag name

---

## Phase 2 (Core Mechanics)

**Systems**: Condition system, Trust system, Commitment system

### Consolidation

Completed consolidation review:

1. **Added `get_actor_conditions` accessor**: For consistency with other collection accessors, added `get_actor_conditions(actor)` that initializes if missing and returns the mutable list.

2. **Added condition query helpers**: Added `has_condition()` and `get_condition_severity()` for cleaner condition checking without needing to handle None.

3. **Added `attempt_trust_recovery` function**: The `TrustState` TypedDict had `recovery_cap` and `last_recovery_turn` fields, but no utility function used them. Added `attempt_trust_recovery()` that implements the per-visit recovery cap with session reset after 10 turns.

4. **Updated `TrustState` TypedDict**: Added `recovered_this_visit` field to track recovery within a session.

5. **Clarified hope bonus mechanism**: Documented that hope bonus reduces NPC condition severity (extending survival), not the commitment deadline. Added `apply_hope_bonus()` function to the design.

6. **Clarified fulfillment detection**: Documented that fulfillment is behavior-driven via `fulfillment_flag` in `CommitmentConfig`. Added `fulfillment_flag` field to TypedDict.

### Test Insights

Tests written in `tests/infrastructure/test_phase2_design.py`.

Insights from test writing:

1. **Condition operations are clean**: The combination of `get_actor_conditions` accessor + utility functions makes condition manipulation straightforward.

2. **Trust recovery cap needs careful testing**: The 10-turn session reset is a somewhat arbitrary threshold. Tests reveal this could be configurable per-NPC.

3. **Hope bonus calculation is coupled to condition system**: The `apply_hope_bonus` function assumes severity maps to turns at 10 severity/turn. This coupling should be explicit in documentation.

4. **Commitment phrase detection location**: Tests assume `check_commitment_phrase` checks if target NPC is present at location. This needs clarification in the design.

5. **Edge case identified**: What happens if commitment is made when NPC has no critical condition? Hope bonus silently does nothing - this is correct but should be documented.

### Design Revisions

1. **Added location check to commitment detection**: `check_commitment_phrase` should verify the target NPC is present in the same location as the player. Added this requirement to documentation.

2. **Made severity-to-turns conversion configurable**: The hope bonus mechanism should allow different conditions to have different severity-per-turn rates. This is a minor enhancement - current design works but could be improved.

---

## Phase 3 (World Systems)

**Systems**: Environmental system, Companion system, Information Networks

### Consolidation

Completed consolidation review:

1. **Added `get_active_companions` accessor**: For consistency with other collection accessors, added `get_active_companions(state)` that initializes if missing.

2. **Added complete Companion API**: Fleshed out the companion system with full API functions:
   - `check_companion_comfort(actor_id, location_id, accessor)` - check comfort level
   - `matches_location_pattern(location_id, patterns)` - glob pattern matching
   - `add_companion(state, actor_id, accessor)` - add to party (max 2)
   - `remove_companion(state, actor_id)` - remove from party
   - `get_companion(state, actor_id)` - get specific companion
   - `companion_refuses_to_follow(companion, destination, accessor)` - handle refusal
   - `companion_follows_reluctantly(companion, destination, accessor)` - handle reluctant follow

3. **Added complete Gossip API**: Fleshed out the gossip system with full implementations:
   - `create_gossip(state, content, source_npc, target_npcs, delay_turns, confession_window)` - create entry
   - `deliver_gossip(entry, accessor)` - deliver to target NPCs
   - `confess_action(state, gossip_id, to_npc)` - player confesses
   - `get_gossip_by_id(state, gossip_id)` - lookup by ID
   - `get_pending_gossip_about(state, content_substring)` - search by content

### Test Insights

Tests written in `tests/infrastructure/test_phase3_design.py`.

Insights from test writing:

1. **Environmental system is simple**: Zone helpers are straightforward - just property lookups with defaults. No complexity.

2. **Companion pattern matching uses fnmatch**: The glob pattern matching for companion restrictions is standard Python fnmatch, which handles `*` wildcards well.

3. **Max 2 companions is a clear constraint**: Tests confirm the hard limit is easy to implement and reason about.

4. **Gossip confession window edge cases**: Need to be clear that `confession_window_until` is inclusive - if current_turn == window_end, confession still valid.

5. **Gossip delivery is fire-and-forget**: The `deliver_gossip` function just sets flags. Trust impacts are handled separately by game-specific handlers.

### Design Revisions

1. **Clarified confession window semantics**: Confession is valid when `current_turn <= confession_window_until`, making the end turn inclusive.

2. **Gossip flags stored in NPC properties**: The `deliver_gossip` function stores flags in `npc.properties["flags"]` rather than `npc.flags` to keep them separate from the typed bool/int flags system. This is intentional - gossip knowledge flags are dynamic and string-based.

---

## Phase 4 (Content Support)

**Systems**: Puzzle system (NPC Services handled as game behaviors, not infrastructure)

### Consolidation

Completed consolidation review:

1. **Unified section 3.9 with Appendix B.4**: Moved the `CumulativeThresholdPuzzle` design from Appendix B.4 into section 3.9 with full API implementations.

2. **Added MultiSolutionPuzzle type**: Renamed `PuzzleState` to `MultiSolutionPuzzle` with explicit `type: Literal["multi_solution"]` for consistency with cumulative puzzles.

3. **Added `is_puzzle_solved` helper**: Generic function that works for both puzzle types, simplifying code that just needs to check if a puzzle is done.

4. **Added `get_puzzle_progress` function**: Returns current/target tuple for cumulative puzzles, allowing UI or narration to show progress.

5. **Clarified NPC Services scope**: Explicitly documented that NPC services (merchants, healers, etc.) are game-specific behaviors, not infrastructure. Infrastructure provides trust and flags that services can check.

6. **Added `contribution_durations` to TypedDict**: Made duration tracking explicit in the type definition.

### Test Insights

Tests written in `tests/infrastructure/test_phase4_design.py`.

Insights from test writing:

1. **Two puzzle systems work independently**: Multi-solution and cumulative puzzles are cleanly separated. No shared logic except `is_puzzle_solved`.

2. **Cumulative puzzle tick needs careful ordering**: When multiple contributions expire in the same tick, the order of removal doesn't matter because we recalculate `current_value` from remaining contributions.

3. **Light puzzle scenario is well-supported**: The full Fungal Depths scenario (ambient light + temporary mushroom contributions) works cleanly with the API.

4. **Requirement checking is flag-based**: Multi-solution puzzles use flag names as requirements. The `check_flag` function must be provided by the accessor or a helper.

### Design Revisions

1. **`check_puzzle_solved` marks puzzle as solved**: The function has a side effect - it sets `solved: True` and `solved_via` when a solution is found. This is intentional to avoid repeated checks.

2. **Cumulative puzzle value is recalculated**: Rather than incrementally updating `current_value`, we always recalculate from contributions. This prevents drift from bugs.

3. **Removed decay_per_turn from implementation**: The `decay_per_turn` field in `CumulativeThresholdPuzzle` is for future use. Current implementation only handles duration-based expiry.

---

# Appendix B: Resolved Design Questions

Questions that arose during design, with resolutions:

## B.1 Commitment Detection

**Question**: Should trigger phrase matching be in the parser, or a separate pass on player input?

**Resolution**: Neither - commitment detection is a **behavior**, not a parser feature.

Flow:
1. Player input goes to LLM narrator
2. LLM returns JSON command
3. After command execution, if the command involved talking to an NPC, a behavior hook checks the raw input against trigger phrases
4. The LLM can be given commitment schemas in its system prompt for better recognition
5. For testing without LLM, simple string-match in the behavior suffices

No parser changes required. Detection lives in `behavior_libraries/infrastructure_lib/commitments.py`.

## B.2 Gossip Propagation Speed

**Question**: Spore network provides instant propagation - is this a game reality bug?

**Resolution**: Yes, "instant" breaks causality. Changed to **fast but not instant**.

- Normal gossip: 3-5 turn delay
- Spore network gossip: 1 turn delay (arrives next turn)

This maintains the fiction that the myconid network is remarkably efficient while preserving temporal coherence. The `GossipEntry` type has a `delay_turns` field; spore network entries simply use `delay_turns: 1`.

## B.3 Multi-Companion Complexity

**Question**: How do we handle conflicts when multiple companions are active?

**Resolution**: Bounded to minimal complexity.

**Hard constraints:**
- Maximum 2 active companions
- If player tries to add a third, must dismiss one first
- Region restrictions are the primary limiter (salamander can't enter water, wolves can't enter Nexus)

**Soft constraints (narrative only):**
- Companions may express discomfort with each other via dialog
- No mechanical penalties for companion combinations
- No complex conflict resolution system

**Companion combinations that occur:**
- Wolf + Salamander: Different comfort zones, no direct conflict
- Wolf + Human: Wolves protective, humans nervous - dialog flavor only
- Multiple humans: No mechanical conflict

This keeps implementation simple: track up to 2 companions, check region restrictions on movement, generate flavor text for discomfort.

## B.4 Cumulative Puzzle State (Light Puzzle)

**Question**: How does the light puzzle track progress across multiple interactions?

**Resolution**: Use **location-level numeric state** with item contributions.

The Fungal Depths light puzzle demonstrates the pattern:

**Storage:**
```python
# On the location
location.properties["puzzle"] = {
    "type": "cumulative_threshold",
    "current_value": 2,      # Current light level
    "target_value": 6,       # Success threshold
    "solved": False,
    "contributions": {}      # Track what's contributing
}

# On each mushroom item
item.states["glowing"] = False
item.states["glow_turns_remaining"] = 0
item.properties["light_contribution"] = 2  # How much this adds when glowing
```

**Mechanics:**
1. Action (pour water on mushroom) triggers item behavior
2. Item behavior modifies item state (`glowing: True`, `glow_turns_remaining: 5`)
3. Item behavior updates location puzzle state
4. Turn tick decrements `glow_turns_remaining`, removes contribution when it hits 0
5. When `current_value >= target_value`, puzzle is solved

**General Pattern (CumulativeThresholdPuzzle):**
```python
class CumulativeThresholdPuzzle(TypedDict):
    """Puzzle solved by accumulating a value to a threshold."""
    type: Literal["cumulative_threshold"]
    current_value: int
    target_value: int
    solved: bool
    contributions: dict[str, int]  # source_id -> contribution amount
    decay_per_turn: NotRequired[int]  # If contributions fade
    on_solve_flag: NotRequired[str]  # Flag to set when solved
```

This pattern handles:
- Light puzzles (mushrooms contribute brightness)
- Weight puzzles (items on pressure plate)
- Resource puzzles (fill container to level)
- Any "accumulate to threshold" mechanic

**API:**
```python
def add_puzzle_contribution(
    location: Location,
    source_id: str,
    amount: int,
    duration: int | None = None  # None = permanent
) -> bool:
    """Add a contribution to a cumulative puzzle. Returns True if puzzle now solved."""

def remove_puzzle_contribution(
    location: Location,
    source_id: str
) -> None:
    """Remove a contribution (item removed, glow faded, etc.)."""

def tick_puzzle_contributions(
    location: Location
) -> bool:
    """Decrement durations, remove expired. Returns True if puzzle state changed."""
```

---

# Appendix C: Pending Engine Changes

Engine modifications needed to support infrastructure (to be implemented before or alongside infrastructure):

## C.1 Turn Phase Extensibility

**Issue**: The engine has a hardcoded `TURN_PHASE_HOOKS` list in `LLMProtocolHandler`. Infrastructure needs new turn phases.

**Resolution**: Extend the engine to allow games to declare additional turn phase hooks.

**Implementation approach**: Games declare turn phases in metadata or behavior layer specification. Engine merges game-declared phases with base phases, respecting declared order.

**New infrastructure turn phases** (to be added before existing phases):
- `turn_phase_scheduled` - Fire scheduled events
- `turn_phase_commitment` - Check commitment deadlines
- `turn_phase_gossip` - Deliver arrived gossip

**Resulting order**:
```python
[
    "turn_phase_scheduled",      # Infrastructure: scheduled events
    "turn_phase_commitment",     # Infrastructure: commitment deadlines
    "turn_phase_gossip",         # Infrastructure: gossip delivery
    hooks.NPC_ACTION,            # Base: NPC actions
    hooks.ENVIRONMENTAL_EFFECT,  # Base: environmental effects
    hooks.CONDITION_TICK,        # Base: condition progression
    hooks.DEATH_CHECK,           # Base: death checks
]
```

This will require a small engine change to `LLMProtocolHandler` - separate issue to be created during implementation.

---

# Revision History

- v0.1 (initial): Type definitions, core utilities, system outlines
- v0.2: Resolved open questions B.1-B.4, added CumulativeThresholdPuzzle pattern
- v0.3: Added Design Process section with test-writing subphase, restructured Appendix A for phase tracking
- v0.4: Added flag scope helpers (get_player_flags, get_actor_flags), identified turn phase extensibility issue (Appendix C.1)
- v0.5: Resolved C.1 - engine will be extended to support game-declared turn phases
- v0.6: Phase 1 consolidation - added TurnNumber and FlagValue types, consistent collection initialization
- v0.7: Phase 1 tests written, API validated
- v0.8: Flags restricted to bool/int only, typed accessors (get_bool_flag, get_int_flag), entity refs go in properties
- v0.9: Phase 2 consolidation - added get_actor_conditions, has_condition, get_condition_severity, attempt_trust_recovery; clarified hope bonus mechanism; added fulfillment_flag to CommitmentConfig
- v0.10: Phase 2 tests written, API validated, design revisions documented
- v0.11: Phase 3 consolidation - added get_active_companions, full Companion API (check_companion_comfort, add/remove_companion, etc.), full Gossip API (create_gossip, deliver_gossip, confess_action, etc.)
- v0.12: Phase 3 tests written, API validated
- v0.13: Phase 4 consolidation - unified puzzle section with CumulativeThresholdPuzzle from Appendix B.4, added MultiSolutionPuzzle type, full puzzle APIs
- v0.14: Phase 4 tests written, all phases complete. Infrastructure design validated.
- v0.15: Added cross-reference to infrastructure_spec_v2.md showing which spec sections map to detailed design sections
- v0.16: Added broadcast and network gossip APIs (DQ-4): create_broadcast_gossip for region-wide gossip, create_network_gossip for network-based gossip (e.g., spore network), BroadcastGossipEntry and NetworkGossipEntry types, NetworkDefinition specification
