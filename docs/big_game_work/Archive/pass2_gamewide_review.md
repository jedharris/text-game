# Pass 2: Game-Wide Review Plan

**Date**: 2025-12-11
**Status**: Complete
**Prerequisites**: Infrastructure consistency review complete, all region detailed designs complete

---

## Goals

Create four condensed references that strongly structure implementation:

1. **API Reference** - Function signatures, preconditions, postconditions, side effects
2. **State Machine Reference** - States, valid transitions, terminal states
3. **State Invariants** - What must always/never be true (for assertions and testing)
4. **Narration State Changes** - All state changes visible to player (for LLM interface)

These serve dual purposes:
- Requirements for implementation
- Surface issues that aren't adequately specified

---

## Phase 1: API Reference Extraction

**Goal**: Extract `api_reference.md` from infrastructure_detailed_design.md

**For each API function**:
- Function signature with full types
- Parameters with constraints (e.g., "trust: int, range -10 to +10")
- Return type and structure
- Side effects (state mutations)
- Preconditions (what must be true before calling)
- Postconditions (what will be true after calling)

**Organization**:
- Group by system (Commitment, Trust, Gossip, Companion, Environment, Condition, Spread)
- Include turn phase handlers separately
- Include utility functions (pattern matching, flag operations)

**Format example**:
```
## Commitment System

### make_commitment(state, npc_id, commitment_config) -> CommitmentId
Parameters:
  - state: GameState (mutated)
  - npc_id: ActorId - the NPC receiving the commitment
  - commitment_config: CommitmentConfig - from game data
Preconditions:
  - NPC exists and is alive
  - No active commitment with same id exists
Postconditions:
  - New ActiveCommitment added to state.infrastructure.commitments
  - Timer scheduled if commitment_config.deadline_turns is set
Side effects:
  - Schedules turn_phase_commitment_check
Returns: CommitmentId
```

**Output**: `api_reference.md` + list of issues found during extraction

---

## Phase 2: State Machine Reference Extraction

**Goal**: Extract `state_machine_reference.md` from infrastructure_detailed_design.md

**For each state machine**:
- States (enum values)
- Valid transitions (from_state -> to_state)
- Transition triggers (what causes each transition)
- Invalid transitions (explicitly: what CAN'T happen)
- Terminal states

**State machines to document**:
1. CommitmentState: ACTIVE -> FULFILLED | WITHDRAWN | ABANDONED
2. ConditionSeverity: MILD -> MODERATE -> SEVERE -> CRITICAL -> (death/cure)
3. TrustTier: Maps trust values to behavior tiers
4. SpreadState: INACTIVE -> ACTIVE -> HALTED
5. GossipState: PENDING -> DELIVERED | CONFESSED

**Format example**:
```
## CommitmentState

States: ACTIVE, FULFILLED, WITHDRAWN, ABANDONED

Transitions:
  ACTIVE -> FULFILLED: fulfill_commitment() called, requirements met
  ACTIVE -> WITHDRAWN: withdraw_commitment() called before deadline
  ACTIVE -> ABANDONED: deadline passed without fulfillment

Invalid:
  FULFILLED -> any: terminal state
  WITHDRAWN -> any: terminal state
  ABANDONED -> any: terminal state
  any -> ACTIVE: commitments cannot be reactivated

Terminal states: FULFILLED, WITHDRAWN, ABANDONED
```

**Output**: `state_machine_reference.md` + list of issues found during extraction

---

## Phase 3: Cross-Reference Verification

**Goal**: Verify every region design against the references from Phases 1-2

### 3.1 API Usage Verification

For each region detailed design, verify:
1. **Signature match**: Every API call uses correct parameter types
2. **Precondition satisfaction**: Region ensures preconditions before calling
3. **Return value handling**: Region handles return values correctly
4. **Side effect awareness**: Region accounts for state mutations

### 3.2 State Machine Conformance

For each region, verify:
1. **Valid transitions only**: Region never implies invalid state transitions
2. **Terminal state respect**: Region never tries to modify terminal states
3. **Trigger consistency**: Region uses correct triggers for transitions

### 3.3 Output

Create `cross_reference_report.md`:
- Per region: API mismatches, state machine violations, ambiguities
- Summary: Total issues by category, discussion items

---

## Phase 4: Narration State Change Catalog

**Goal**: Document all state changes visible to the player

**For every state mutation**:
```
State Change: commitment_abandoned
Trigger: Deadline passed without fulfillment
State mutations:
  - commitment.state = ABANDONED
  - npc.trust -= penalty
  - gossip created if configured
Output for narration:
  - Which commitment was abandoned
  - Which NPC was affected
  - Trust penalty applied
  - Whether gossip was triggered
Narrative context needed:
  - NPC's personality (for reaction tone)
  - Player's history with NPC
  - Whether player was nearby or far away
```

**Group by trigger type**:
1. Player action results
2. Turn phase results
3. Threshold crossings
4. Scheduled events
5. Cascading effects

**Output**: `narration_state_changes.md`

---

## Phase 5: State Invariants

**Goal**: Document invariants for assertions and testing

**Approach**: Use the analysis methods as *lenses* to find invariants, not as deep analysis processes:

**From Combinatorial State Analysis**:
- What combinations of states are impossible?
- "Actor cannot be dead AND have active commitment as recipient"

**From Boundary Conditions**:
- What ranges must values stay within?
- "Trust must be in [-10, +10]"
- "Condition severity must be in [0, 100]"

**From Failure Mode Analysis**:
- What references must always be valid?
- "Commitment NPC must exist"
- "Gossip target must exist"

**From Temporal Consistency**:
- What ordering must be maintained?
- "deadline_turn >= made_at_turn"
- "arrives_turn > created_turn"

**From Mutual Exclusion**:
- What states cannot co-exist?
- "Actor cannot be in two locations"
- "Commitment cannot be both fulfilled and abandoned"

**Format**:
```
INV-001: commitment_npc_exists
Invariant: Every ActiveCommitment.npc_id references an existing actor
Check: Load-time validation + runtime assertion
Severity: Error (breaks game logic)

INV-002: trust_in_range
Invariant: All trust values in [-10, +10]
Check: modify_trust() clamps values
Severity: Warning (would be clamped anyway)
```

**Output**: `state_invariants.md`

**Error tracking**: When bugs occur during implementation:
1. If bug breaks existing invariant → fix the bug
2. If bug reveals new invariant → add to list, then fix

---

## Execution Order

1. **Phase 1**: API Reference (may find issues)
2. **Phase 2**: State Machine Reference (may find issues)
3. **Phase 4**: Narration State Changes (parallel-safe with Phase 3)
4. **Phase 3**: Cross-Reference Verification (requires Phase 1-2 complete)
5. **Phase 5**: State Invariants (uses all prior phases as input)

Resolve any issues found in Phases 1-2 before proceeding to Phase 3.

---

## Deliverables

| Document | Purpose |
|----------|---------|
| `api_reference.md` | Implementation requirements for all APIs |
| `state_machine_reference.md` | Valid state transitions |
| `cross_reference_report.md` | Region verification results |
| `narration_state_changes.md` | LLM interface requirements |
| `state_invariants.md` | Assertions and validation rules |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2025-12-11 | All phases complete. All deliverables created. |
| 1.0 | 2025-12-11 | Approved plan after discussion. Reframed Phase 3/5 around invariants. |
| 0.1 | 2025-12-11 | Initial draft for discussion |
