# Big Game Implementation Plan

**Date**: 2025-12-11
**Status**: Draft - For Review
**Prerequisites**: All detailed designs complete, cross-reference verification complete

---

## Overview

This plan stages the implementation of big_game to maintain testability and catch integration issues early. The key innovation is a **configurable test bed** that uses the detailed designs as test specifications.

### Guiding Principles

1. **TDD throughout** - No production code without tests first
2. **Documentation-as-contract** - Detailed designs drive test bed configuration
3. **Infrastructure first** - Fully testable foundation before content
4. **Vertical integration** - Test cross-region interactions from the start
5. **EventResult discipline** - Every state change must be reportable to narration

---

## Document References

### Source Documents (in `detailed_designs/`)
- `infrastructure_detailed_design.md` - Types, APIs, systems
- `beast_wilds_detailed_design.md`
- `civilized_remnants_detailed_design.md`
- `fungal_depths_detailed_design.md`
- `frozen_reaches_detailed_design.md`
- `sunken_district_detailed_design.md`
- `meridian_nexus_detailed_design.md`

### Reference Documents (in `Reference_docs/`)
- `api_reference.md` - Function signatures, pre/postconditions
- `state_machine_reference.md` - Valid states and transitions
- `state_invariants.md` - Assertions and validation rules
- `narration_state_changes.md` - What EventResult must contain
- `game_wide_rules.md` - Cross-cutting rules
- `cross_region_dependencies.md` - Import/export relationships
- `validation_matrix.md` - API usage by region

### Test Specifications (in `sketches_and_walkthroughs/`)
- `*_sketch.json` - Entity definitions per region
- `*_walkthrough.md` - Scenario sequences
- `cross_region_walkthrough_*.md` - Multi-region scenarios

---

## Phase 1: Infrastructure Foundation

**Goal**: Implement all infrastructure systems with full test coverage.

**Duration estimate**: Foundation for everything else.

### 1.1 Type Definitions and Basic Accessors

**Source**: `infrastructure_detailed_design.md` Part 1-2

**Deliverables**:
- NewType definitions (TurnNumber, CommitmentId, GossipId, ActorId)
- StrEnum definitions (CommitmentState, ConditionType, etc.)
- TypedDict definitions (all from Part 1)
- Accessor functions (Part 2) with initialization behavior
- Pattern matching utilities (Section 2.7)

**Tests**:
- Type construction and serialization
- Accessor initialization of missing data
- Pattern matching edge cases

### 1.2 Flag and Trust Operations

**Source**: `infrastructure_detailed_design.md` Sections 2.2, 2.5, 3.1, 3.4

**Deliverables**:
- `set_flag()`, `get_flag()`, `check_flag()`
- `modify_trust()`, `modify_echo_trust()`, `modify_npc_trust()`
- `calculate_echo_chance()`, `check_echo_appears()`
- Trust bounds enforcement (floor/ceiling)
- Recovery cap logic

**Tests**:
- Flag operations on various targets (player, actor, location)
- Trust modification with bounds
- Echo appearance probability calculation
- Recovery cap timing (10-turn window)

**Invariants to assert** (from `state_invariants.md`):
- TRUST-1: Echo trust >= -6
- TRUST-4: Echo chance in [0.0, 0.95]

### 1.3 Condition System

**Source**: `infrastructure_detailed_design.md` Section 3.3

**Deliverables**:
- `apply_condition()`, `cure_condition()`, `get_actor_condition()`
- Condition tick handlers (infrastructure stubs + game-specific implementations)
- `get_cold_protection()`, `get_temperature_zone()`, `calculate_hypothermia_rate()`
- Severity threshold checks

**Tests**:
- Apply/cure/modify conditions
- Severity clamping [0, 100]
- Tick progression in hazard zones
- Protection factor calculations

**Invariants to assert**:
- COND-1: Severity in [0, 100]
- COND-2: Removal at zero
- COND-3: No duplicate conditions

### 1.4 Scheduled Events

**Source**: `infrastructure_detailed_design.md` Section 3.2

**Deliverables**:
- `schedule_event()`, `cancel_scheduled_event()`, `reschedule_event()`
- Turn phase handler for events
- Event firing mechanism

**Tests**:
- Schedule and fire at correct turn
- Cancel before firing
- Reschedule changes timing
- Multiple events same turn

**Invariants to assert**:
- TURN-2: trigger_turn >= current_turn for pending events

### 1.5 Commitment System

**Source**: `infrastructure_detailed_design.md` Section 3.5

**Deliverables**:
- `make_commitment()`, `fulfill_commitment()`, `withdraw_commitment()`, `abandon_commitment()`
- `check_commitment_phrase()`
- `apply_hope_bonus()`
- Commitment turn phase handler
- State transitions with trust effects

**Tests**:
- Full lifecycle: make → fulfill
- Full lifecycle: make → withdraw
- Full lifecycle: make → abandon (deadline passed)
- Hope bonus extends deadline
- Trust effects on each outcome
- Terminal state immutability

**Invariants to assert**:
- COMMIT-1: Terminal state finality
- COMMIT-2: deadline_turn >= made_at_turn
- COMMIT-3: No duplicate active commitments

### 1.6 Gossip System

**Source**: `infrastructure_detailed_design.md` Section 3.8

**Deliverables**:
- `create_gossip()`, `create_broadcast_gossip()`, `create_network_gossip()`
- Gossip propagation turn phase handler
- Confession mechanism
- Knowledge flag setting on delivery

**Tests**:
- Point-to-point gossip delivery timing
- Broadcast to all NPCs
- Network gossip to members only
- Confession within window
- Knowledge flags set on delivery

**Invariants to assert**:
- GOSSIP-1: arrives_turn > created_turn
- GOSSIP-4: Network targets have matching property

### 1.7 Companion System

**Source**: `infrastructure_detailed_design.md` Section 3.7

**Deliverables**:
- `check_companion_comfort()`, `companion_follow()`, `companion_wait()`
- `get_active_companions()`
- Restriction checking by location
- Override trigger mechanism

**Tests**:
- Comfort levels by location (per companion type)
- Wait behavior at impossible locations
- Maximum companions (2)
- Override triggers

**Invariants to assert**:
- COMP-1: Max 2 companions
- COMP-3: Waiting location consistency

### 1.8 Environmental Spread System

**Source**: `infrastructure_detailed_design.md` Section 3.10

**Deliverables**:
- `check_spread_active()`, `halt_spread()`, `apply_spread_effects()`, `get_spread_progress()`
- Spread turn phase handler
- Milestone application
- Halt flag checking

**Tests**:
- Spread progression by turn
- Milestone effects applied at correct turns
- Halt flag stops progression
- Past milestones not re-applied

**Invariants to assert**:
- SPREAD-1: Halt finality
- SPREAD-3: Past milestones applied

### 1.9 Turn Phase Orchestration

**Source**: `infrastructure_detailed_design.md` Section 4.1

**Deliverables**:
- Turn phase order enforcement
- EventResult aggregation
- Phase handler registration

**Tests**:
- Phases execute in correct order
- EventResult accumulates across phases
- Each phase runs exactly once

**Invariants to assert**:
- TURN-1: Turn number monotonicity
- TURN-3: Single phase execution

### 1.10 Validation Module

**Source**: `infrastructure_detailed_design.md` Section 4.2

**Deliverables**:
- `validate_infrastructure()`
- Individual validators (commitment configs, state machines, zones, etc.)

**Tests**:
- Invalid data rejected at load time
- Valid data passes
- Specific error messages for each validation failure

---

## Phase 2: Test Bed Framework

**Goal**: Build the configurable test bed that loads documented game context and verifies region behavior.

### 2.1 Test Bed Core

**Deliverables**:
```python
class RegionTestBed:
    def __init__(
        self,
        region: str,
        context: str | dict = "fresh",  # "fresh", "mid", or custom state
        stub_regions: list[str] = None,  # Minimal other regions
        log_level: str = "errors",       # "errors" | "all"
    ): ...

    def load_context(self, context_name: str) -> None: ...
    def execute(self, command: str) -> EventResult: ...
    def execute_sequence(self, commands: list[str]) -> list[EventResult]: ...
    def advance_turns(self, count: int) -> list[EventResult]: ...

    # Assertions
    def assert_flag(self, flag: str, expected: bool) -> None: ...
    def assert_trust(self, actor: str, value: int = None, delta: int = None) -> None: ...
    def assert_state(self, actor: str, expected_state: str) -> None: ...
    def assert_condition(self, actor: str, condition: str, severity: int = None) -> None: ...
    def assert_location(self, actor: str, expected_location: str) -> None: ...
    def assert_item(self, item: str, location: str = None, holder: str = None) -> None: ...
    def assert_event_result(self, result: EventResult, contains: dict) -> None: ...

    # Inspection
    def get_state(self) -> GameState: ...
    def get_log(self) -> list[LogEntry]: ...
```

**Tests**:
- Test bed itself needs tests
- Load fresh context, verify initial state
- Execute command, verify state change
- Logging captures expected information

### 2.2 Context Loaders

**Deliverables**:
- `FreshContextLoader` - Load region as documented in Section 1 (entities, initial states)
- `MidGameContextLoader` - Load with progress (from walkthrough midpoints)
- `CustomContextLoader` - Load with specific flags/trust/items

**Source data**:
- Fresh: Extract from `*_detailed_design.md` Section 1 (entities)
- Fresh: Use `*_sketch.json` for entity definitions
- Mid: Extract from `*_walkthrough.md` scenario states

**Tests**:
- Fresh context matches documented initial state
- Mid context has expected progress flags
- Custom context applies overrides correctly

### 2.3 Stub Region Generator

**Deliverables**:
- Minimal region that provides documented exports
- Minimal region that consumes documented imports
- Cross-region connection stubs

**Purpose**: Test cross-region mechanics without full region implementations.

**Tests**:
- Stub provides expected items
- Stub accepts expected imports
- Cross-region flags propagate

### 2.4 Interaction Logger

**Deliverables**:
```python
@dataclass
class LogEntry:
    turn: int
    phase: str
    action: str
    state_before: dict  # Relevant state snapshot
    state_after: dict
    event_result: EventResult
    issues: list[str]   # Invariant violations, unexpected states
```

- Configurable verbosity
- Issue detection (invariant violations, undocumented state changes)
- Exportable trace for debugging

**Tests**:
- Log captures turn/phase/action correctly
- Issues flagged for invariant violations
- Log can be filtered by severity

---

## Phase 3: Skeleton Game

**Goal**: All entities exist and are navigable, but with minimal behavior.

### 3.1 Location Graph

**Deliverables**:
- All locations from all 6 regions
- All exits/connections
- Location properties (zones, safe areas, etc.)
- No behavior triggers yet

**Source**: Section 1.1 of each detailed design

**Tests**:
- Navigation between all connected locations
- Region boundaries correct
- Zone properties set correctly

### 3.2 NPC Shells

**Deliverables**:
- All NPCs from all 6 regions
- Initial state machines (states defined, no transition triggers)
- Initial trust values
- Initial locations
- No dialog or services yet

**Source**: Section 1.2 of each detailed design

**Tests**:
- NPCs exist at documented locations
- Initial states correct
- Trust values correct

### 3.3 Item Shells

**Deliverables**:
- All items from all 6 regions
- Item properties (portable, readable, etc.)
- Initial locations
- No special effects yet

**Source**: Section 1.3 of each detailed design

**Tests**:
- Items exist at documented locations
- Properties match documentation
- Take/drop/examine work

### 3.4 Cross-Region Connections

**Deliverables**:
- Import/export relationships documented
- Items can move between regions
- NPCs reference cross-region entities correctly

**Source**: `cross_region_dependencies.md`, Section 2 of each detailed design

**Tests**:
- Exported items can be carried to importing region
- NPC references resolve correctly

---

## Phase 4: Region Implementation (Iterative)

**Goal**: Implement regions one at a time, with full test coverage using the test bed.

### Order Rationale

1. **Meridian Nexus** - Simplest (safe zone, Echo only)
2. **Frozen Reaches** - Clearest condition system (hypothermia)
3. **Beast Wilds** - Commitment system (Sira rescue)
4. **Fungal Depths** - Network gossip, death-mark system
5. **Sunken District** - Complex timers, dual rescue
6. **Civilized Remnants** - Most complex (branding, multiple factions)

### Per-Region Implementation Pattern

For each region:

**4.X.1 Load Fresh Context**
- Configure test bed with region's documented initial state
- Verify all Section 1 entities are correct

**4.X.2 Implement State Machine Triggers**
- Add transition triggers to NPC state machines
- Test each transition in isolation

**4.X.3 Implement Commitment Configs**
- Add commitment configurations
- Test commitment lifecycle (make/fulfill/withdraw/abandon)

**4.X.4 Implement Hazard Behaviors** (if applicable)
- Zone effects (conditions, damage)
- Protection mechanics
- Test with various equipment/companion states

**4.X.5 Implement NPC Services**
- Dialog triggers
- Service transactions
- Trust gates

**4.X.6 Implement Puzzles/Challenges**
- Puzzle mechanics
- Success/failure conditions

**4.X.7 Walkthrough Scenarios as Tests**
- Convert walkthrough to test sequence
- Verify outcomes match documentation

**4.X.8 Cross-Region Integration Tests**
- Test imports from previously implemented regions
- Test exports to stub consumers
- Verify gossip propagation

### Phase 4.1: Meridian Nexus

**Key behaviors**:
- Echo appearance based on trust
- Echo dialog (topics, trust-gated revelations)
- Waystone fragment placement
- Crystal restoration tracking
- Wolf exclusion

**Test scenarios** (from `meridian_nexus_walkthrough.md`):
- First entry, Echo appears
- Place waystone fragments (in various orders)
- Trust recovery in Nexus
- Wolf stopped at boundary

### Phase 4.2: Frozen Reaches

**Key behaviors**:
- Hypothermia condition (zones, rates, protection)
- Salamander companion recruitment
- Telescope repair puzzle
- Cold spread halt flag
- Heated stone mechanics

**Test scenarios** (from `frozen_reaches_walkthrough.md`):
- Enter cold zone, hypothermia progresses
- Salamander provides warmth protection
- Repair telescope, halt cold spread
- Various zone transitions

### Phase 4.3: Beast Wilds

**Key behaviors**:
- Sira rescue (commitment with deadline)
- Wolf pack recruitment
- Alpha trust building
- Cub rescue scenario
- Spider gallery hazard

**Test scenarios** (from `beast_wilds_walkthrough.md`):
- Find Sira, make commitment, rescue in time
- Find Sira, fail to rescue (deadline)
- Build wolf trust to 5
- Recruit wolf pack

### Phase 4.4: Fungal Depths

**Key behaviors**:
- Fungal infection condition
- Death-mark system (has_killed_fungi)
- Spore Mother state machine
- Myconid services (trust-gated)
- Aldric rescue
- Heartmoss cure
- Spore spread halt

**Test scenarios** (from `fungal_depths_walkthrough.md`):
- Enter with death-mark, Myconids hostile
- Enter clean, build Myconid trust
- Heal Spore Mother, halt spread
- Aldric rescue timeline

### Phase 4.5: Sunken District

**Key behaviors**:
- Drowning condition
- Garrett rescue (room-entry timer)
- Delvan rescue (multi-step, hope bonus)
- Dual-rescue impossibility
- Swimming skill progression
- Archivist knowledge quest

**Test scenarios** (from `sunken_district_walkthrough.md`):
- Enter sea_caves, Garrett timer starts
- Rescue Garrett within 5 turns
- Fail Garrett rescue (timeout)
- Delvan with hope bonus timing
- Attempt dual rescue (designed to fail)

### Phase 4.6: Civilized Remnants

**Key behaviors**:
- Branding system (thief/hero)
- Faction trust (guards, merchants, refugees)
- Guardian repair quest
- Undercity access
- Temple puzzle
- Refugee crisis

**Test scenarios** (from `civilized_remnants_walkthrough.md`):
- Get branded as thief
- Clear thief brand, become hero
- Guardian repair sequence
- Undercity navigation

---

## Phase 5: Cross-Region Integration

**Goal**: Verify all cross-region mechanics work together.

### 5.1 Spread Systems

**Tests**:
- Spore spread affects Beast Wilds at turn 50
- Cold spread affects Nexus at turn 125
- Halting spread in source region stops progression

### 5.2 Gossip Propagation

**Tests**:
- Sira death gossip reaches Elara
- Fungal death mark affects Myconid first contact
- Cross-region gossip timing

### 5.3 Companion Journeys

**Tests**:
- Wolf through multiple regions (restrictions enforced)
- Salamander through regions (water death)
- Myconid through regions (cold damage)

### 5.4 Full Walkthrough Scenarios

**Source**: `cross_region_walkthrough_*.md`

**Tests**:
- Walkthrough A: Commitment Cascade
- Walkthrough B: Companion Journey
- Walkthrough C: Dark Path

These become the ultimate integration tests.

---

## Phase 6: Narration Integration

**Goal**: Connect state changes to LLM narration.

### 6.1 EventResult Verification

**Tests**:
- Every state change produces appropriate EventResult
- EventResult contains information needed by narration
- Reference: `narration_state_changes.md`

### 6.2 State Query Interface

**Deliverables**:
- Functions for LLM to query game state
- Narrative context builders

### 6.3 Narration Prompts

**Deliverables**:
- System prompts for narration
- EventResult → narrative description patterns

---

## Risk Tracking

### Known Risks

| Risk | Mitigation | Status |
|------|------------|--------|
| Test bed bugs mask real bugs | Test bed has its own tests | Planned |
| Documentation drift | Test failures force updates | Planned |
| Walkthrough ambiguity | Clarify during implementation | Monitor |
| Cross-region combinatorics | Stub regions + targeted tests | Planned |

### Deferred Work Tracking

Maintain a list of behaviors skipped during implementation. Review at end of each phase.

---

## Success Criteria

### Phase 1 Complete When:
- All infrastructure tests pass
- Invariants from `state_invariants.md` are asserted
- API matches `api_reference.md`

### Phase 2 Complete When:
- Test bed can load any region's fresh context
- Test bed assertions work correctly
- Logging captures expected information

### Phase 3 Complete When:
- Player can navigate entire world
- All entities exist at documented locations
- No behaviors yet (just structure)

### Phase 4 Complete When:
- Each region's walkthrough passes as test
- Cross-region imports/exports work
- No invariant violations

### Phase 5 Complete When:
- Full cross-region walkthroughs pass
- Spread systems work across regions
- Companion restrictions enforced everywhere

### Phase 6 Complete When:
- Every state change has narratable EventResult
- LLM can query state and generate appropriate narration

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2025-12-11 | Initial draft |
