# Infrastructure API Reference

**Extracted from**: infrastructure_detailed_design.md
**Date**: 2025-12-11
**Purpose**: Condensed reference for implementation and region verification

---

## 1. Timer Operations

Location: `src/infrastructure_utils.py` (Section 2.1)

### check_deadline(current_turn, deadline_turn) -> bool
```
Parameters:
  - current_turn: TurnNumber
  - deadline_turn: TurnNumber
Preconditions: None
Postconditions: None (pure function)
Side effects: None
Returns: True if current_turn >= deadline_turn
```

### turns_remaining(current_turn, deadline_turn) -> int
```
Parameters:
  - current_turn: TurnNumber
  - deadline_turn: TurnNumber
Preconditions: None
Postconditions: None (pure function)
Side effects: None
Returns: max(0, deadline_turn - current_turn)
```

### extend_deadline(current_deadline, extension) -> TurnNumber
```
Parameters:
  - current_deadline: TurnNumber
  - extension: int (turns to add)
Preconditions: None
Postconditions: None (pure function)
Side effects: None
Returns: TurnNumber(current_deadline + extension)
```

### create_deadline(current_turn, duration) -> TurnNumber
```
Parameters:
  - current_turn: TurnNumber
  - duration: int (turns until deadline)
Preconditions: None
Postconditions: None (pure function)
Side effects: None
Returns: TurnNumber(current_turn + duration)
```

---

## 2. Trust/Numeric Operations

Location: `src/infrastructure_utils.py` (Section 2.2)

### modify_trust(current, delta, floor, ceiling) -> int
```
Parameters:
  - current: int
  - delta: int (positive or negative)
  - floor: int | None (minimum value)
  - ceiling: int | None (maximum value)
Preconditions: None
Postconditions: None (pure function)
Side effects: None
Returns: Clamped new value
```

### check_trust_threshold(current, threshold, at_least) -> bool
```
Parameters:
  - current: int
  - threshold: int
  - at_least: bool = True (if True: current >= threshold, if False: current <= threshold)
Preconditions: None
Postconditions: None (pure function)
Side effects: None
Returns: Whether threshold is met
```

### calculate_recovery_amount(current, target, max_per_session, recovered_this_session) -> int
```
Parameters:
  - current: int
  - target: int
  - max_per_session: int
  - recovered_this_session: int
Preconditions: None
Postconditions: None (pure function)
Side effects: None
Returns: Actual recovery amount respecting session cap
```

### attempt_trust_recovery(trust_state, recovery_amount, current_turn, recovery_cap) -> tuple[int, int]
```
Parameters:
  - trust_state: TrustState (mutated)
  - recovery_amount: int
  - current_turn: TurnNumber
  - recovery_cap: int = 3
Preconditions: None
Postconditions:
  - trust_state["current"] may be increased
  - trust_state["recovered_this_visit"] updated
  - trust_state["last_recovery_turn"] set to current_turn if recovery occurred
Side effects: Mutates trust_state
Returns: (actual_recovery, new_trust_value)
Note: Session resets when last_recovery_turn > 10 turns ago
```

---

## 3. State Machine Operations

Location: `src/infrastructure_utils.py` (Section 2.3)

### validate_state_machine(config) -> list[str]
```
Parameters:
  - config: StateMachineConfig
Preconditions: None
Postconditions: None (pure function)
Side effects: None
Returns: List of error messages (empty if valid)
```

### get_current_state(config) -> str
```
Parameters:
  - config: StateMachineConfig
Preconditions: config has "initial" field
Postconditions: None (pure function)
Side effects: None
Returns: config["current"] or config["initial"]
```

### transition_state(config, new_state) -> tuple[bool, str]
```
Parameters:
  - config: StateMachineConfig (mutated on success)
  - new_state: str
Preconditions: new_state in config["states"]
Postconditions: config["current"] = new_state (if valid)
Side effects: Mutates config on success
Returns: (success, message)
```

---

## 4. Condition Operations

Location: `src/infrastructure_utils.py` (Section 2.4)

### get_actor_conditions(actor) -> list[ConditionInstance]
```
Parameters:
  - actor: Actor (mutated if conditions missing)
Preconditions: None
Postconditions: actor.properties["conditions"] exists
Side effects: Initializes conditions list if missing
Returns: Mutable list of conditions
```

### create_condition(condition_type, initial_severity, source) -> ConditionInstance
```
Parameters:
  - condition_type: ConditionType
  - initial_severity: int = 0
  - source: str | None = None
Preconditions: None
Postconditions: None (pure function)
Side effects: None
Returns: New ConditionInstance dict
```

### modify_condition_severity(condition, delta, max_severity) -> int
```
Parameters:
  - condition: ConditionInstance (mutated)
  - delta: int
  - max_severity: int = 100
Preconditions: None
Postconditions: condition["severity"] clamped to [0, max_severity]
Side effects: Mutates condition["severity"]
Returns: New severity value
```

### get_condition(conditions, condition_type) -> ConditionInstance | None
```
Parameters:
  - conditions: list[ConditionInstance]
  - condition_type: ConditionType
Preconditions: None
Postconditions: None (pure function)
Side effects: None
Returns: Matching condition or None
```

### remove_condition(conditions, condition_type) -> bool
```
Parameters:
  - conditions: list[ConditionInstance] (mutated)
  - condition_type: ConditionType
Preconditions: None
Postconditions: Condition removed from list if present
Side effects: Mutates list
Returns: True if condition was found and removed
```

### has_condition(conditions, condition_type) -> bool
```
Parameters:
  - conditions: list[ConditionInstance]
  - condition_type: ConditionType
Preconditions: None
Postconditions: None (pure function)
Side effects: None
Returns: True if condition exists in list
```

### get_condition_severity(conditions, condition_type) -> int
```
Parameters:
  - conditions: list[ConditionInstance]
  - condition_type: ConditionType
Preconditions: None
Postconditions: None (pure function)
Side effects: None
Returns: Severity of condition, or 0 if not present
```

---

## 5. Flag Operations

Location: `src/infrastructure_utils.py` (Section 2.5)

### get_bool_flag(flags, name, default) -> bool
```
Parameters:
  - flags: dict[str, bool]
  - name: str
  - default: bool = False
Returns: Flag value or default
```

### set_bool_flag(flags, name, value) -> None
```
Parameters:
  - flags: dict[str, bool] (mutated)
  - name: str
  - value: bool
Side effects: Sets flags[name] = value
```

### check_bool_flag(flags, name) -> bool
```
Parameters:
  - flags: dict[str, bool]
  - name: str
Returns: flags.get(name, False)
```

### get_int_flag(flags, name, default) -> int
```
Parameters:
  - flags: dict[str, int]
  - name: str
  - default: int = 0
Returns: Flag value or default
```

### set_int_flag(flags, name, value) -> None
```
Parameters:
  - flags: dict[str, int] (mutated)
  - name: str
  - value: int
Side effects: Sets flags[name] = value
```

### increment_int_flag(flags, name, delta) -> int
```
Parameters:
  - flags: dict[str, int] (mutated)
  - name: str
  - delta: int = 1
Side effects: Increments flags[name]
Returns: New value
```

### clear_flag(flags, name) -> bool
```
Parameters:
  - flags: dict[str, bool | int] (mutated)
  - name: str
Side effects: Removes flag if present
Returns: True if flag existed
```

### has_flag(flags, name) -> bool
```
Parameters:
  - flags: dict[str, bool | int]
  - name: str
Returns: True if name in flags
```

### get_global_flags(state) -> dict[str, bool | int]
```
Parameters:
  - state: GameState (mutated if flags missing)
Side effects: Initializes state.extra["flags"] if missing
Returns: Mutable flags dict
```

### get_actor_flags(actor) -> dict[str, bool | int]
```
Parameters:
  - actor: Actor
Returns: actor.flags
```

---

## 6. Collection Accessors

Location: `src/infrastructure_utils.py` (Section 2.6)

All accessors initialize collections if missing, returning mutable references.

### get_active_commitments(state) -> list[ActiveCommitment]
```
Side effects: Initializes state.extra["active_commitments"] if missing
```

### get_gossip_queue(state) -> list[GossipEntry]
```
Side effects: Initializes state.extra["gossip_queue"] if missing
```

### get_scheduled_events(state) -> list[ScheduledEvent]
```
Side effects: Initializes state.extra["scheduled_events"] if missing
```

### get_echo_trust(state) -> TrustState
```
Side effects: Initializes state.extra["echo_trust"] = {"current": 0} if missing
```

### get_active_companions(state) -> list[CompanionState]
```
Side effects: Initializes state.extra["companions"] if missing
```

### get_environmental_spreads(state) -> dict[str, SpreadState]
```
Side effects: Initializes state.extra["environmental_spreads"] if missing
```

### get_network_definitions(state) -> dict[str, NetworkDefinition]
```
Side effects: Initializes state.extra["networks"] if missing
```

---

## 7. Pattern Matching Utilities

Location: `src/infrastructure_utils.py` (Section 2.7)

### matches_pattern(target, pattern) -> bool
```
Parameters:
  - target: str (e.g., location ID)
  - pattern: str (glob pattern)
Pattern formats:
  - "exact_id" - exact match
  - "prefix/*" - matches strings starting with "prefix_"
  - "*" - matches everything
  - Standard fnmatch patterns
Examples:
  matches_pattern("beast_wilds_clearing", "beast_wilds/*") -> True
  matches_pattern("nexus_chamber", "nexus_chamber") -> True
```

### find_matching_locations(pattern, state) -> list[str]
```
Parameters:
  - pattern: str
  - state: GameState
Returns: List of location IDs matching pattern
```

### matches_any_pattern(target, patterns) -> bool
```
Parameters:
  - target: str
  - patterns: list[str]
Returns: True if target matches any pattern
```

---

## 8. Turn/Timer System

Location: `behavior_libraries/infrastructure_lib/timing.py` (Section 3.2)

### schedule_event(state, event_type, turns_from_now, event_id, data) -> ScheduledEventId
```
Parameters:
  - state: GameState (mutated)
  - event_type: str
  - turns_from_now: int
  - event_id: ScheduledEventId | None = None
  - data: dict[str, str] | None = None
Postconditions: New ScheduledEvent in state.extra["scheduled_events"]
Returns: Event ID
```

### cancel_scheduled_event(state, event_id) -> bool
```
Parameters:
  - state: GameState (mutated)
  - event_id: ScheduledEventId
Returns: True if event found and cancelled
```

### reschedule_event(state, event_id, new_trigger_turn) -> bool
```
Parameters:
  - state: GameState (mutated)
  - event_id: ScheduledEventId
  - new_trigger_turn: int
Returns: True if event found and rescheduled
```

### Turn Phase Handler: on_scheduled_event_check
```
Hook: turn_phase_scheduled
Behavior: Fires events where trigger_turn <= current turn, removes from queue
Returns: EventResult with fired event messages
```

---

## 9. Condition System

Location: `behavior_libraries/infrastructure_lib/conditions.py` (Section 3.3)

### apply_condition(actor, condition_type, initial_severity, source) -> ConditionInstance
```
Parameters:
  - actor: Actor (mutated)
  - condition_type: ConditionType
  - initial_severity: int = 0
  - source: str | None = None
Postconditions: Condition added to actor or severity increased if exists
Returns: The condition instance
```

### cure_condition(actor, condition_type, amount) -> bool
```
Parameters:
  - actor: Actor (mutated)
  - condition_type: ConditionType
  - amount: int | None = None (None = full cure)
Returns: True if actor had the condition
```

### get_actor_condition(actor, condition_type) -> ConditionInstance | None
```
Parameters:
  - actor: Actor
  - condition_type: ConditionType
Returns: Condition or None
```

### get_cold_protection(actor, accessor) -> float
```
Parameters:
  - actor: Actor
  - accessor: StateAccessor
Protection sources (stacking):
  1. Equipment: cold_weather_gear (0.5), cold_resistance_cloak (1.0)
  2. Companions: salamander warmth aura (1.0) if following
  3. Location: hot_springs (instant cure), warm zones (1.0)
  4. Actor properties: cold_immunity (infinite)
Returns: Protection factor 0.0 to 1.0
```

### get_temperature_zone(location) -> TemperatureZone
```
Parameters:
  - location: Location
Returns: TemperatureZone enum value, defaults to NORMAL
```

### calculate_hypothermia_rate(zone, protection) -> int
```
Parameters:
  - zone: TemperatureZone
  - protection: float (0.0 to 1.0)
Base rates per turn:
  - NORMAL: -10 (recovery)
  - COLD: +5
  - FREEZING: +10
  - EXTREME_COLD: +20
Returns: Effective rate after protection reduction
```

### Turn Phase Handler: on_condition_tick
```
Hook: condition_tick
Behavior: Progress all actor conditions, apply severity changes, check thresholds
Returns: EventResult with condition messages
```

---

## 10. Trust System

Location: Section 3.4 (uses utilities from Section 2.2)

### modify_echo_trust(state, delta) -> int
```
Parameters:
  - state: GameState (mutated)
  - delta: int
Bounds: floor=-6, ceiling=None (unbounded positive)
Postconditions: Echo trust modified
Returns: New trust value
```

### modify_npc_trust(actor, delta, floor, ceiling) -> int
```
Parameters:
  - actor: Actor (mutated)
  - delta: int
  - floor: int | None = None
  - ceiling: int | None = None
Postconditions: NPC trust modified, trust state initialized if missing
Returns: New trust value
```

### calculate_echo_chance(trust, base_chance) -> float
```
Parameters:
  - trust: int
  - base_chance: float = 0.2
Returns:
  - 0.0 if trust <= -3 (refuses to appear)
  - Otherwise: clamped to [0.05, 0.95], base + (trust * 0.1)
```

### check_echo_appears(state, base_chance, random_value) -> bool
```
Parameters:
  - state: GameState
  - base_chance: float = 0.2
  - random_value: float | None = None (for testing)
Returns: True if Echo appears
```

---

## 11. Commitment System

Location: `behavior_libraries/infrastructure_lib/commitments.py` (Section 3.5)

### make_commitment(state, config_id, current_turn) -> ActiveCommitment
```
Parameters:
  - state: GameState (mutated)
  - config_id: str (references CommitmentConfig)
  - current_turn: int
Preconditions:
  - CommitmentConfig exists in state.extra["commitment_configs"]
  - No active commitment with same ID
Postconditions:
  - New ActiveCommitment in state.extra["active_commitments"]
  - Hope bonus applied if configured
Returns: The new commitment
```

### fulfill_commitment(state, commitment_id, accessor) -> str
```
Parameters:
  - state: GameState (mutated)
  - commitment_id: CommitmentId
  - accessor: StateAccessor
Preconditions: Commitment exists and is ACTIVE
Postconditions: commitment.state = FULFILLED
Returns: Narration message
```

### withdraw_commitment(state, commitment_id, accessor) -> str
```
Parameters:
  - state: GameState (mutated)
  - commitment_id: CommitmentId
  - accessor: StateAccessor
Preconditions: Commitment exists and is ACTIVE
Postconditions: commitment.state = WITHDRAWN
Returns: Narration message
```

### abandon_commitment(commitment, accessor) -> str
```
Parameters:
  - commitment: ActiveCommitment (mutated)
  - accessor: StateAccessor
Postconditions:
  - commitment.state = ABANDONED
  - Trust penalty applied to NPC
  - Gossip created if configured
Returns: Narration message
```

### check_commitment_phrase(text, location, accessor) -> CommitmentConfig | None
```
Parameters:
  - text: str (player input)
  - location: Location
  - accessor: StateAccessor
Preconditions: Target NPC must be in same location as player
Returns: Matching CommitmentConfig or None
```

### apply_hope_bonus(commitment, config, accessor) -> None
```
Parameters:
  - commitment: ActiveCommitment (mutated)
  - config: CommitmentConfig
  - accessor: StateAccessor
Preconditions: config.hope_extends_survival is True
Postconditions:
  - NPC's critical condition severity reduced
  - commitment.hope_applied = True
Note: Reduces NPC condition severity by (hope_bonus * 10)
```

### Turn Phase Handler: on_commitment_check
```
Hook: turn_phase_commitment
Behavior: Check deadlines, mark expired commitments as ABANDONED
Returns: EventResult with abandonment messages
```

---

## 12. Environmental System

Location: `behavior_libraries/infrastructure_lib/environment.py` (Section 3.6)

### get_temperature_zone(location) -> TemperatureZone
```
Returns: Temperature zone, defaults to NORMAL
```

### get_water_level(location) -> WaterLevel
```
Returns: Water level, defaults to DRY
```

### is_breathable(location) -> bool
```
Returns: location.properties.get("breathable", True)
```

### is_safe_zone(location) -> bool
```
Returns: location.properties.get("safe_zone", False)
```

### Turn Phase Handler: on_environment_tick
```
Hook: environmental_effect
Behavior: Apply environmental effects to actors based on location
Returns: EventResult with effect messages
```

---

## 13. Companion System

Location: `behavior_libraries/infrastructure_lib/companions.py` (Section 3.7)

### check_companion_comfort(actor_id, location_id, accessor) -> CompanionComfort
```
Parameters:
  - actor_id: ActorId
  - location_id: LocationId
  - accessor: StateAccessor
Returns: COMFORTABLE, UNCOMFORTABLE, or IMPOSSIBLE
Note: Matches location against companion's restriction patterns
```

### add_companion(state, actor_id, accessor) -> bool
```
Parameters:
  - state: GameState (mutated)
  - actor_id: ActorId
  - accessor: StateAccessor
Preconditions:
  - Party size < 2
  - Actor not already a companion
Postconditions: New CompanionState added
Returns: True if added successfully
```

### remove_companion(state, actor_id) -> bool
```
Parameters:
  - state: GameState (mutated)
  - actor_id: ActorId
Returns: True if companion found and removed
```

### get_companion(state, actor_id) -> CompanionState | None
```
Parameters:
  - state: GameState
  - actor_id: ActorId
Returns: Companion state or None
```

### companion_refuses_to_follow(companion, destination, accessor) -> str
```
Parameters:
  - companion: CompanionState (mutated)
  - destination: str
  - accessor: StateAccessor
Postconditions:
  - companion.following = False
  - companion.waiting_at = player's current location
Returns: Refusal message
```

### companion_follows_reluctantly(companion, destination, accessor) -> str
```
Parameters:
  - companion: CompanionState (mutated)
  - destination: str
  - accessor: StateAccessor
Postconditions: companion.comfort_in_current = UNCOMFORTABLE
Returns: Reluctance message
```

### Movement Hook: on_player_move
```
Behavior: Check companion restrictions, update following/waiting state
Returns: EventResult with companion messages
```

---

## 14. Gossip System

Location: `behavior_libraries/infrastructure_lib/gossip.py` (Section 3.8)

### create_gossip(state, content, source_npc, target_npcs, delay_turns, confession_window) -> GossipId
```
Parameters:
  - state: GameState (mutated)
  - content: str
  - source_npc: ActorId
  - target_npcs: list[ActorId]
  - delay_turns: int (1 for spore network, 3-5 normal)
  - confession_window: int | None = None
Postconditions: New GossipEntry in gossip queue
Returns: Gossip ID
```

### create_broadcast_gossip(state, content, source_npc, target_regions, delay_turns) -> GossipId
```
Parameters:
  - state: GameState (mutated)
  - content: str
  - source_npc: ActorId
  - target_regions: list[str] | Literal["ALL"]
  - delay_turns: int
Note: For property-based targeting, use create_network_gossip instead
Returns: Gossip ID
```

### create_network_gossip(state, content, source_npc, network_id, delay_turns) -> GossipId
```
Parameters:
  - state: GameState (mutated)
  - content: str
  - source_npc: ActorId
  - network_id: str (e.g., "spore_network", "criminal_network")
  - delay_turns: int (typically 1 for spore network)
Returns: Gossip ID
```

### deliver_gossip(entry, accessor) -> None
```
Parameters:
  - entry: GossipEntry
  - accessor: StateAccessor (mutated via NPCs)
Postconditions: Target NPCs have knows_{gossip_id} flag set
```

### confess_action(state, gossip_id, to_npc) -> bool
```
Parameters:
  - state: GameState (mutated)
  - gossip_id: GossipId
  - to_npc: ActorId
Preconditions: Gossip exists and within confession window
Postconditions: Gossip removed from queue
Returns: True if confession successful
Note: Confession valid when current_turn <= confession_window_until
```

### get_gossip_by_id(state, gossip_id) -> GossipEntry | None
```
Returns: Gossip entry or None
```

### get_pending_gossip_about(state, content_substring) -> list[GossipEntry]
```
Returns: All pending gossip entries containing substring
```

### Turn Phase Handler: on_gossip_propagate
```
Hook: turn_phase_gossip
Behavior: Deliver gossip where arrives_turn <= current turn
Returns: EventResult (no visible message - gossip is background)
```

---

## 15. Puzzle System

Location: `behavior_libraries/infrastructure_lib/puzzles.py` (Section 3.9)

### check_puzzle_solved(entity, accessor) -> tuple[bool, str | None]
```
Parameters:
  - entity: Entity (mutated if solved)
  - accessor: StateAccessor
Returns: (True, solution_id) if solved, (False, None) otherwise
Note: Has side effect - marks puzzle as solved when solution found
```

### get_available_solutions(entity, accessor) -> list[PuzzleSolution]
```
Parameters:
  - entity: Entity
  - accessor: StateAccessor
Returns: Solutions player could potentially use
```

### check_flag(flag_name, accessor) -> bool
```
Parameters:
  - flag_name: str
  - accessor: StateAccessor
Returns: True if flag is set (checks global and player flags)
```

### all_requirements_met(requirements, accessor) -> bool
```
Parameters:
  - requirements: list[str] (flag names)
  - accessor: StateAccessor
Returns: True if all flags are True
```

### any_requirement_met(requirements, accessor) -> bool
```
Parameters:
  - requirements: list[str] (flag names)
  - accessor: StateAccessor
Returns: True if any flag is True
```

### add_puzzle_contribution(entity, source_id, amount, duration) -> bool
```
Parameters:
  - entity: Entity (mutated)
  - source_id: str
  - amount: int
  - duration: int | None = None (None = permanent)
Preconditions: Entity has cumulative_threshold puzzle
Returns: True if puzzle is now solved
```

### remove_puzzle_contribution(entity, source_id) -> None
```
Parameters:
  - entity: Entity (mutated)
  - source_id: str
Side effects: Removes contribution, recalculates current_value
```

### tick_puzzle_contributions(entity) -> bool
```
Parameters:
  - entity: Entity (mutated)
Returns: True if puzzle state changed
Note: Call in turn phase to handle duration-based expiry
```

### get_puzzle_progress(entity) -> tuple[int, int] | None
```
Parameters:
  - entity: Entity
Returns: (current_value, target_value) or None
```

### is_puzzle_solved(entity) -> bool
```
Parameters:
  - entity: Entity
Returns: True if puzzle is solved (works for both puzzle types)
```

---

## 16. Environmental Spread System

Location: `behavior_libraries/infrastructure_lib/spreads.py` (Section 3.10)

### check_spread_active(state, spread_id) -> bool
```
Parameters:
  - state: GameState
  - spread_id: str
Returns: True if spread is active
```

### halt_spread(state, spread_id) -> bool
```
Parameters:
  - state: GameState (mutated)
  - spread_id: str
Postconditions: spread.active = False
Returns: True if spread was active and is now halted
```

### apply_spread_effects(effects, accessor) -> list[str]
```
Parameters:
  - effects: list[SpreadEffect]
  - accessor: StateAccessor (mutated via locations)
Postconditions: Location properties modified per effects
Returns: List of affected location IDs
```

### get_spread_progress(state, spread_id) -> tuple[TurnNumber | None, TurnNumber | None]
```
Parameters:
  - state: GameState
  - spread_id: str
Returns: (current_milestone, next_milestone_turn)
  - next_milestone_turn is None if no more milestones
```

### validate_spreads(state) -> list[str]
```
Parameters:
  - state: GameState
Returns: List of validation errors
Checks:
  - Required fields present (halt_flag, milestones)
  - Milestones in ascending turn order
  - Each milestone has effects
```

### Turn Phase Handler: on_spread_check
```
Hook: turn_phase_spread
Behavior:
  1. Check halt flags, deactivate halted spreads
  2. Apply effects for current turn milestones
Returns: EventResult with spread messages
```

---

## 17. Turn Phase Order

Location: Section 4.1

```python
TURN_PHASE_HOOKS = [
    "turn_phase_scheduled",      # Fire scheduled events
    "turn_phase_commitment",     # Check commitment deadlines
    "turn_phase_gossip",         # Deliver arrived gossip
    "turn_phase_spread",         # Check environmental spread milestones
    hooks.NPC_ACTION,            # NPCs take actions
    hooks.ENVIRONMENTAL_EFFECT,  # Environmental effects
    hooks.CONDITION_TICK,        # Conditions progress
    hooks.DEATH_CHECK,           # Check for actor deaths
]
```

---

## Extraction Notes

### Issues Found During Extraction

1. **fire_scheduled_event not fully specified**: Section 3.2 references `fire_scheduled_event(event, accessor)` but marks it as "game-specific". The dispatch mechanism needs implementation details.

2. **Condition tick handlers are game-specific**: `tick_hypothermia`, `tick_drowning`, etc. are referenced but marked as game-specific implementations. Their signatures are clear but implementations are not in infrastructure.

3. **apply_location_effects is game-specific**: Section 3.6 references this function but marks it as game-specific. Infrastructure defines the pattern, game provides implementation.

4. **Fulfillment detection mechanism**: Commitment fulfillment is behavior-driven via `fulfillment_flag`. The exact mechanism for checking this flag and calling `fulfill_commitment` is game-specific.

### Implicit Preconditions Discovered

- `check_commitment_phrase` requires target NPC to be in same location as player (documented in design revisions)
- `confess_action` window is inclusive: confession valid when `current_turn <= confession_window_until`
- `add_companion` enforces max 2 companions hard limit
- Gossip delivery stores flags in `npc.properties["flags"]` (not `npc.flags`) for dynamic flag names

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-11 | Initial extraction from infrastructure_detailed_design.md |
