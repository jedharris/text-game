# State Invariants Reference

**Extracted from**: infrastructure_detailed_design.md, state_machine_reference.md, cross_reference_report.md
**Date**: 2025-12-11
**Purpose**: Document invariants for assertions, testing, and implementation guidance

---

## Overview

Invariants are conditions that must always be true during valid game execution. They serve three purposes:
1. **Assertions**: Runtime checks that catch bugs early
2. **Testing**: Properties to verify in unit and integration tests
3. **Implementation**: Constraints that guide correct implementation

Invariants are organized by system. Each invariant includes:
- **Statement**: What must always be true
- **Rationale**: Why this matters
- **Violation Indicates**: What bug or error a violation would suggest

---

## 1. Turn System Invariants

### TURN-1: Turn Number Monotonicity
**Statement**: `state.current_turn` only increases, never decreases or stays the same between turn phases.

**Rationale**: Turn number drives all time-based mechanics (deadlines, gossip arrival, spreads).

**Violation Indicates**: Turn processing logic error or state corruption.

### TURN-2: Scheduled Event Ordering
**Statement**: For any scheduled event, `trigger_turn >= current_turn` (unless the event is being fired this turn).

**Rationale**: Events in the past should have already been processed and removed.

**Violation Indicates**: Event processing skipped events or state was modified incorrectly.

### TURN-3: Single Turn Phase Execution
**Statement**: Each turn phase handler runs exactly once per turn, in the defined order.

**Rationale**: Duplicate execution would cause double effects; skipped phases would miss effects.

**Violation Indicates**: Turn processing loop error.

---

## 2. Commitment System Invariants

### COMMIT-1: Terminal State Finality
**Statement**: Once a commitment's state is FULFILLED, WITHDRAWN, or ABANDONED, it cannot change.

**Rationale**: These are terminal states representing completed outcomes.

**Violation Indicates**: State machine transition logic error.

### COMMIT-2: Deadline Consistency
**Statement**: For any ACTIVE commitment, `deadline_turn >= made_at_turn`.

**Rationale**: Deadlines must be in the future relative to when commitment was made.

**Violation Indicates**: Commitment creation or hope bonus logic error.

### COMMIT-3: No Duplicate Active Commitments
**Statement**: No two active commitments can have the same `commitment_id`.

**Rationale**: Each commitment type should only be active once at a time.

**Violation Indicates**: Missing duplicate check in `make_commitment()`.

### COMMIT-4: Config Reference Validity
**Statement**: Every active commitment's `config_id` must reference an existing CommitmentConfig.

**Rationale**: Commitment behavior depends on config lookup.

**Violation Indicates**: Config removed after commitment made, or typo in config_id.

### COMMIT-5: Hope Bonus Non-Negative
**Statement**: `hope_bonus` in CommitmentConfig must be >= 0.

**Rationale**: Negative hope bonus would shorten deadline, contradicting design intent.

**Violation Indicates**: Data entry error in commitment config.

---

## 3. Condition System Invariants

### COND-1: Severity Bounds
**Statement**: For any ConditionInstance, `0 <= severity <= 100`.

**Rationale**: Severity is a percentage; values outside this range are meaningless.

**Violation Indicates**: Missing clamp in condition modification functions.

### COND-2: Condition Removal at Zero
**Statement**: If a condition's severity reaches 0, the condition should be removed from the actor.

**Rationale**: Severity 0 means no condition; keeping it adds unnecessary state.

**Violation Indicates**: Cure/recovery logic not cleaning up.

### COND-3: No Duplicate Conditions
**Statement**: An actor cannot have two ConditionInstances of the same `condition_type`.

**Rationale**: Multiple instances would cause double-ticking and confusion.

**Violation Indicates**: Missing check in `apply_condition()`.

### COND-4: Progression Rate Sign
**Statement**: `progression_rate` should be positive for worsening conditions, negative for recovering conditions.

**Rationale**: Consistent semantics across all conditions.

**Violation Indicates**: Confusion in rate calculation logic.

---

## 4. Trust System Invariants

### TRUST-1: Echo Trust Floor
**Statement**: Echo trust value is always >= -6.

**Rationale**: Trust floor ensures player can always eventually recover.

**Violation Indicates**: Missing floor check in `modify_echo_trust()`.

### TRUST-2: NPC Trust Bounds
**Statement**: If an NPC has `trust.floor` or `trust.ceiling` defined, trust value stays within bounds.

**Rationale**: Some NPCs have limited trust ranges for narrative reasons.

**Violation Indicates**: Missing bounds check in `modify_npc_trust()`.

### TRUST-3: Recovery Cap Timing
**Statement**: Echo trust recovery (when below 0) is limited to +1 per "visit" (10+ turns since last recovery).

**Rationale**: Prevents immediate redemption from severe trust damage.

**Violation Indicates**: Recovery cap logic not tracking last recovery time.

### TRUST-4: Echo Appearance Probability Bounds
**Statement**: Echo appearance chance is always in [0.0, 0.95].

**Rationale**: Never guaranteed to appear (max 95%), never negative probability.

**Violation Indicates**: Formula error in `calculate_echo_chance()`.

---

## 5. Gossip System Invariants

### GOSSIP-1: Arrival After Creation
**Statement**: For any gossip entry, `arrives_turn > created_turn`.

**Rationale**: Gossip always has positive propagation delay.

**Violation Indicates**: Delay calculation error or data entry error.

### GOSSIP-2: Confession Window Validity
**Statement**: If confession_window_until is set, `confession_window_until >= created_turn`.

**Rationale**: Confession window must include time after gossip creation.

**Violation Indicates**: Window calculation error.

### GOSSIP-3: Delivered Gossip Sets Flags
**Statement**: When gossip is delivered, target NPC gains `knows_{gossip_id}` flag.

**Rationale**: This is how NPCs "learn" information from gossip.

**Violation Indicates**: Delivery logic not setting flags.

### GOSSIP-4: Network Gossip Target Validity
**Statement**: Network gossip targets only reach actors with the matching network property.

**Rationale**: Spore network gossip shouldn't reach non-fungal creatures.

**Violation Indicates**: Network membership check missing or incorrect.

---

## 6. Companion System Invariants

### COMP-1: Maximum Companions
**Statement**: `len(active_companions) <= 2` at all times.

**Rationale**: Design limit on party size.

**Violation Indicates**: Missing check in companion recruitment.

### COMP-2: No Duplicate Companions
**Statement**: Each companion type can only be active once.

**Rationale**: Can't have two wolf packs following.

**Violation Indicates**: Missing duplicate check.

### COMP-3: Waiting Location Consistency
**Statement**: If `companion.following == False` and companion is waiting, `companion.waiting_at` must be a valid location.

**Rationale**: Companion must be somewhere when not following.

**Violation Indicates**: Waiting state not properly set when entering impossible zone.

### COMP-4: Comfort Level Consistency
**Statement**: Companion comfort level matches current location's restrictions for that companion type.

**Rationale**: Comfort should be recalculated on location change.

**Violation Indicates**: Comfort not updated after movement.

---

## 7. Environmental Spread Invariants

### SPREAD-1: Halt Finality
**Statement**: Once `spread.active == False`, it cannot become True again.

**Rationale**: Halted spreads are permanent - the threat was stopped.

**Violation Indicates**: Spread restart logic exists when it shouldn't.

### SPREAD-2: Milestone Turn Ordering
**Statement**: Milestones in a spread are ordered by turn number (ascending).

**Rationale**: Earlier effects happen first.

**Violation Indicates**: Data definition error.

### SPREAD-3: Past Milestones Applied
**Statement**: All milestones with `turn <= current_turn` should have their effects applied (if spread was active at that turn).

**Rationale**: Milestones are permanent once reached.

**Violation Indicates**: Milestone processing skipped or spread check logic error.

### SPREAD-4: Halt Flag Stops Progression
**Statement**: If halt_flag is True in game state, spread becomes inactive immediately.

**Rationale**: Halt flag represents player solving the problem.

**Violation Indicates**: Halt check not running or running too late.

---

## 8. State Machine Invariants (General)

### SM-1: Valid State Membership
**Statement**: Any actor's state_machine.current_state must be in state_machine.states.

**Rationale**: Can't be in an undefined state.

**Violation Indicates**: Transition to undefined state or data corruption.

### SM-2: Terminal State Stability
**Statement**: If an actor's state is marked as terminal in its state machine, it cannot transition to any other state.

**Rationale**: Terminal states represent completed outcomes.

**Violation Indicates**: State machine definition inconsistency or logic error.

### SM-3: Initial State on Creation
**Statement**: New state machines must have current_state set to a valid initial state.

**Rationale**: Can't have undefined initial state.

**Violation Indicates**: State machine initialization error.

---

## 9. Actor/Entity Invariants

### ACTOR-1: Unique Actor IDs
**Statement**: All actor IDs in `state.actors` must be unique.

**Rationale**: IDs are used for lookups and references.

**Violation Indicates**: Duplicate ID creation or merge error.

### ACTOR-2: Location Validity
**Statement**: Every actor's `location` must be a valid location ID in the game.

**Rationale**: Actors can't be in nonexistent places.

**Violation Indicates**: Movement to invalid location or location removal.

### ACTOR-3: Player Singleton
**Statement**: Exactly one actor with ID "player" exists.

**Rationale**: Player is special and must always exist.

**Violation Indicates**: Player deletion or duplication.

### ACTOR-4: Dead Actors Don't Act
**Statement**: If an actor has state "dead", they cannot be targets of most interactions.

**Rationale**: Dead actors are narratively unavailable.

**Violation Indicates**: Dead state not checked before interaction.

---

## 10. Location Invariants

### LOC-1: Connection Symmetry
**Statement**: If location A has exit to location B, B should have a return path (unless explicitly one-way).

**Rationale**: Players shouldn't get trapped unexpectedly.

**Violation Indicates**: Missing connection in level design.

### LOC-2: Zone Property Validity
**Statement**: Temperature zones must use defined values (NORMAL, COLD, FREEZING, EXTREME_COLD).

**Rationale**: Zone handling depends on known values.

**Violation Indicates**: Typo in zone property or new zone type not implemented.

---

## 11. Cross-System Invariants

### CROSS-1: Dead NPCs Can't Complete Commitments
**Statement**: If commitment target NPC is dead, commitment cannot transition to FULFILLED.

**Rationale**: Can't fulfill promise to dead NPC.

**Violation Indicates**: NPC death not checked during fulfillment.

### CROSS-2: Gossip About Dead Stops
**Statement**: Gossip about a dead NPC should still propagate but have reduced narrative impact.

**Rationale**: Death doesn't undo information, but context changes.

**Violation Indicates**: N/A - this is narrative guidance, not hard constraint.

### CROSS-3: Companion Death Updates State
**Statement**: If companion dies, `active_companions` must be updated and companion removed.

**Rationale**: Dead companions can't follow.

**Violation Indicates**: Death handling not cleaning up companion state.

### CROSS-4: Environmental Effects Match Zones
**Statement**: Hypothermia progression should only occur in COLD/FREEZING/EXTREME_COLD zones.

**Rationale**: Can't get colder in warm areas.

**Violation Indicates**: Zone check missing in condition tick.

### CROSS-5: Spread Effects Match Halt State
**Statement**: If spread is halted, new milestone effects should not apply (even if turn passes their threshold).

**Rationale**: Halting prevents future damage.

**Violation Indicates**: Halt check not happening before milestone application.

---

## Assertion Implementation Guide

### Priority 1: Always Assert (Critical)
These should be checked on every state mutation:
- TURN-1: Turn monotonicity
- COND-1: Severity bounds
- TRUST-1: Echo trust floor
- COMP-1: Maximum companions
- ACTOR-3: Player singleton

### Priority 2: Assert on Relevant Operations
- COMMIT-1: After any commitment state change
- GOSSIP-1: When creating gossip
- SPREAD-1: After any spread state check
- SM-1: After any state transition

### Priority 3: Validate on Load
- COMMIT-4: Config references
- LOC-1: Connection symmetry (optional, may be intentional)
- LOC-2: Zone properties
- SPREAD-2: Milestone ordering

### Priority 4: Test Coverage
All invariants should have corresponding unit tests that:
1. Verify the invariant holds after normal operations
2. Verify that operations which would violate the invariant are prevented

---

## Invariants Discovered During Cross-Reference

These invariants were identified from issues found during region design verification:

### From Cross-Reference Report

**INV-NEW-1: Echo Trust Threshold Consistency**
**Statement**: Echo refuses to appear at trust <= -6 (not -3).
**Status**: CRITICAL - API needs update to match design intent.

**INV-NEW-2: Network Gossip Scope**
**Statement**: Echo cannot receive gossip via spore_network (Echo is not a fungal creature).
**Status**: Designs need separate gossip call to Echo for fungal events.

**INV-NEW-3: Timer Trigger Types**
**Statement**: Timer triggers must be one of: on_commit, on_room_entry (if supported), or custom behavior.
**Status**: Clarify if on_room_entry is valid trigger or requires behavior hook.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-11 | Initial extraction from infrastructure and cross-reference review |
