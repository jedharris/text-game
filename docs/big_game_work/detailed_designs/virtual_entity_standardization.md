# Virtual Entity Standardization Design

## Goals

Convert all "virtual entities" (commitments, scheduled events, gossip, spreads) from plain data structures managed by centralized handlers into first-class entities with standard structure (id, name, description, properties, behaviors).

This unifies the architecture so ALL game state follows the same entity pattern with per-entity dispatch, eliminating special cases and centralized iteration.

## Use Cases

1. **Commitment lifecycle**: Track player promises to NPCs with deadlines, enable per-commitment behavior
2. **Scheduled events**: Fire timed game events (NPC state changes, environmental effects)
3. **Gossip propagation**: Spread information between NPCs over time with network effects
4. **Environmental spreads**: Model location property changes over time (cold spreading, water rising)

## Current Architecture Problems

### Inconsistent Entity Model
- **First-class entities** (Actor, Item, Location, Lock, Part): Have id, name, description, properties, behaviors
- **Virtual entities** (Commitment, ScheduledEvent, Gossip, Spread): Plain TypedDicts in state.extra, no behaviors

### Centralized Turn Phase Handlers
Current turn phase handlers iterate centrally and call helper functions directly (no dispatch):

```python
# examples/big_game/behaviors/shared/infrastructure/commitments.py
def on_commitment_check(entity, accessor, context):
    expired = get_expired_commitments(state, current_turn)  # Centralized query
    for commitment in expired:
        transition_commitment_state(commitment, ABANDONED)  # Direct call
```

Problems:
- No per-entity dispatch means virtual entities can't have custom behavior
- Centralized iteration couples turn phase logic to specific data structures
- Can't use standard behavior override patterns (entity-specific modules, handler escape hatch)

### Storage in state.extra
Virtual entities stored as lists/dicts in state.extra:
```python
state.extra["commitments"] = [...]  # List of ActiveCommitment dicts
state.extra["scheduled_events"] = [...]  # List of ScheduledEvent dicts
state.extra["gossip"] = [...]  # List of GossipEntry dicts
state.extra["spreads"] = {...}  # Dict of spread_id -> spread config
```

Problems:
- No type safety (can't use state.get_commitment() like state.get_actor())
- Hard to examine/debug in game state files
- Doesn't follow standard entity pattern

## Proposed Solution

### New Entity Types

Add four new entity types following the standard pattern:

```python
# src/types.py - New ID types
CommitmentId = NewType('CommitmentId', str)
ScheduledEventId = NewType('ScheduledEventId', str)
GossipId = NewType('GossipId', str)
SpreadId = NewType('SpreadId', str)

# src/state_manager.py - New entity classes
@dataclass
class Commitment:
    """Player promise to an NPC with deadline tracking."""
    id: CommitmentId
    name: str  # "Sira's healing promise"
    description: str  # "Promised to heal beasts by turn 15"
    properties: Dict[str, Any]  # state, deadline_turn, target_npc, etc.
    behaviors: List[str]  # ["behaviors.shared.infrastructure.commitments"]

@dataclass
class ScheduledEvent:
    """Timed event that fires when trigger turn is reached."""
    id: ScheduledEventId
    name: str  # "Cold spread milestone 75"
    description: str  # "Frozen reaches cold spreads to meridian_nexus"
    properties: Dict[str, Any]  # trigger_turn, event_type, data, repeating, etc.
    behaviors: List[str]  # ["behaviors.shared.infrastructure.scheduled_events"]

@dataclass
class Gossip:
    """Information propagating between NPCs over time."""
    id: GossipId
    name: str  # "News of Sira's rescue"
    description: str  # "Player rescued Sira from wolves"
    properties: Dict[str, Any]  # gossip_type, source_npc, target_npcs, arrives_turn, etc.
    behaviors: List[str]  # ["behaviors.shared.infrastructure.gossip"]

@dataclass
class Spread:
    """Environmental effect spreading across locations over time."""
    id: SpreadId
    name: str  # "Frozen reaches cold spread"
    description: str  # "Cold from frozen reaches spreads to other regions"
    properties: Dict[str, Any]  # active, milestones, halt_flag, etc.
    behaviors: List[str]  # ["behaviors.shared.infrastructure.spreads"]
```

### GameState Collections

```python
@dataclass
class GameState:
    # ... existing collections ...
    commitments: List[Commitment] = field(default_factory=list)
    scheduled_events: List[ScheduledEvent] = field(default_factory=list)
    gossip: List[Gossip] = field(default_factory=list)
    spreads: List[Spread] = field(default_factory=list)

    def get_commitment(self, commitment_id: CommitmentId) -> Commitment:
        """Get commitment by ID (fail-fast)."""
        for commitment in self.commitments:
            if commitment.id == commitment_id:
                return commitment
        raise KeyError(f"Commitment not found: {commitment_id}")

    # Similar methods for scheduled_events, gossip, spreads
```

### Property Mapping

Current TypedDict fields → new entity properties:

**Commitment** (from ActiveCommitment + CommitmentConfig):
- `properties["state"]`: CommitmentState enum
- `properties["deadline_turn"]`: TurnNumber
- `properties["target_npc"]`: ActorId
- `properties["goal"]`: str
- `properties["made_at_turn"]`: TurnNumber
- `properties["hope_applied"]`: bool
- `properties["config_id"]`: str (reference to original config)

**ScheduledEvent**:
- `properties["trigger_turn"]`: TurnNumber
- `properties["event_type"]`: str
- `properties["data"]`: Dict[str, Any]
- `properties["repeating"]`: bool
- `properties["interval"]`: int

**Gossip** (from GossipEntry/BroadcastGossipEntry/NetworkGossipEntry):
- `properties["gossip_type"]`: GossipType enum
- `properties["content"]`: str
- `properties["source_npc"]`: ActorId
- `properties["target_npcs"]`: List[ActorId] (or None for broadcast)
- `properties["created_turn"]`: TurnNumber
- `properties["arrives_turn"]`: TurnNumber
- `properties["confession_window_until"]`: TurnNumber (optional)
- `properties["target_regions"]`: List[LocationId] (broadcast only)
- `properties["network_id"]`: str (network gossip only)

**Spread**:
- `properties["active"]`: bool
- `properties["milestones"]`: List[Dict] (turn, effects)
- `properties["reached_milestones"]`: List[TurnNumber]
- `properties["halt_flag"]`: str (name of flag that halts spread)

### Per-Entity Turn Phase Dispatch

Turn phase handlers dispatch to each virtual entity instead of iterating centrally:

```python
# src/turn_phases.py (or wherever turn phases are invoked)
def execute_turn_phase_commitment(accessor):
    """Execute commitment phase by dispatching to each commitment."""
    state = accessor.game_state
    all_feedback = []

    for commitment in state.commitments:
        result = accessor.behavior_manager.invoke_behavior(
            commitment,
            "on_turn_phase_check",
            accessor,
            {"current_turn": state.turn_count}
        )
        if result.feedback:
            all_feedback.append(result.feedback)

    return "\n".join(all_feedback) if all_feedback else None
```

**Behavior handler** (in commitment's behavior module):
```python
# examples/big_game/behaviors/shared/infrastructure/commitments.py
def on_turn_phase_check(entity, accessor, context):
    """Check if this commitment has expired (per-entity handler)."""
    current_turn = context["current_turn"]
    deadline = entity.properties.get("deadline_turn")

    if deadline and current_turn >= deadline:
        state = entity.properties.get("state")
        if state == CommitmentState.ACTIVE:
            # Transition to abandoned
            entity.properties["state"] = CommitmentState.ABANDONED
            return EventResult(
                allow=True,
                feedback=f"Your commitment to {entity.name} has expired."
            )

    return EventResult(allow=True, feedback=None)
```

Benefits:
- Each commitment can have custom behavior via behavior modules
- Standard behavior override patterns work (entity-specific module, handler escape hatch)
- No centralized iteration coupling

## Implementation Phases

### Phase 1: Add Entity Types and Collections
**Goal**: Create new entity structures without changing existing code

1. Add new ID types to src/types.py (CommitmentId, ScheduledEventId, GossipId, SpreadId)
2. Add new entity dataclasses to src/state_manager.py (Commitment, ScheduledEvent, Gossip, Spread)
3. Add new collections to GameState (commitments, scheduled_events, gossip, spreads)
4. Add get_commitment/get_scheduled_event/get_gossip/get_spread methods to GameState
5. Update Entity union type to include new entities
6. Add parsers for new entity types (_parse_commitment, etc.)
7. Add serializers for new entity types (_serialize_commitment, etc.)
8. Write unit tests for entity parsing/serialization

**Success criteria**:
- All new types and classes defined
- Entity parsing/serialization works
- Unit tests pass
- No existing code changed yet

### Phase 2: Convert big_game Virtual Entities
**Goal**: Populate new collections with big_game data

1. Read current big_game state.extra virtual entity data
2. For each commitment in state.extra["commitments"]:
   - Create Commitment entity with appropriate name/description
   - Map TypedDict fields to properties
   - Add to state.commitments list
3. Repeat for scheduled_events, gossip, spreads
4. Update big_game/game_state.json with new entity collections
5. Write validation to ensure no data loss
6. Create migration tool (tools/migrations/migrate_v0_1_1_to_v0_1_2.py)

**Success criteria**:
- All big_game virtual entities converted to first-class entities
- game_state.json validates and loads correctly
- Migration tool works for existing save files

### Phase 3: Refactor Turn Phase Handlers to Per-Entity Dispatch
**Goal**: Eliminate centralized iteration, use invoke_behavior()

For each turn phase handler:

**Commitment phase**:
1. Change turn_phases.py to iterate state.commitments and dispatch to each
2. Update commitments.py behavior to handle per-entity checks
3. Add vocabulary event registration ("on_turn_phase_check" → handler)
4. Remove centralized get_expired_commitments() iteration
5. Write tests for per-commitment dispatch

**Scheduled event phase**:
1. Change turn_phases.py to iterate state.scheduled_events and dispatch
2. Update scheduled_events.py behavior for per-event firing
3. Remove centralized fire_due_events() iteration
4. Write tests for per-event dispatch

**Gossip phase**:
1. Change turn_phases.py to iterate state.gossip and dispatch
2. Update gossip.py behavior for per-gossip delivery
3. Remove centralized deliver_due_gossip() iteration
4. Write tests for per-gossip dispatch

**Spread phase**:
1. Change turn_phases.py to iterate state.spreads and dispatch
2. Update spreads.py behavior for per-spread milestone checks
3. Remove centralized get_due_milestones() iteration
4. Write tests for per-spread dispatch

**Success criteria**:
- All turn phase handlers use per-entity dispatch
- No centralized iteration in turn phase code
- All behavior handlers use standard invoke_behavior()
- Tests pass for all turn phases

### Phase 4: Remove Old Infrastructure
**Goal**: Clean up legacy centralized mechanisms

1. Remove TypedDict definitions from infrastructure_types.py (ActiveCommitment, ScheduledEvent, etc.)
2. Remove centralized helper functions from infrastructure_utils.py (get_expired_commitments, fire_due_events, etc.)
3. Remove state.extra["commitments"], state.extra["scheduled_events"], etc. (data now in first-class collections)
4. Update infrastructure_utils.py to work with entity collections
5. Run full test suite to catch any missed dependencies
6. Update documentation

**Success criteria**:
- No TypedDict definitions for virtual entities
- No centralized iteration helpers
- All data in first-class entity collections
- All tests pass
- Documentation updated

### Phase 5: Walkthroughs and Validation
**Goal**: Verify big_game still works with new architecture

1. Run all existing big_game walkthroughs
2. Test commitment expiration scenarios
3. Test scheduled event firing
4. Test gossip propagation
5. Test environmental spreads
6. Fix any issues found
7. Add new walkthrough tests for virtual entity behaviors

**Success criteria**:
- All existing walkthroughs pass
- New virtual entity walkthroughs pass
- No regressions in big_game functionality

## Non-Requirements

- **No backward compatibility code**: Migration tool handles old format, no runtime compatibility
- **No defensive programming**: Trust entity data is valid (validate at load time)
- **No loose typing**: All new code fully typed with NewType IDs and proper dataclasses
- **No special cases**: Virtual entities follow exact same pattern as other entities

## Testing Strategy

- **Unit tests**: Parse/serialize new entities, GameState accessors work
- **Integration tests**: Turn phase dispatch works, behavior handlers fire correctly
- **Walkthrough tests**: big_game scenarios exercise virtual entity behaviors
- **Migration tests**: Old game_state.json files migrate correctly

## Migration Path

Game state version: 0.1.1 → 0.1.2

Migration tool: `tools/migrations/migrate_v0_1_1_to_v0_1_2.py`

Converts:
- `state.extra["commitments"]` → `state.commitments` list
- `state.extra["scheduled_events"]` → `state.scheduled_events` list
- `state.extra["gossip"]` → `state.gossip` list
- `state.extra["spreads"]` → `state.spreads` list

For each virtual entity, generates:
- `id`: from existing id field or synthesized
- `name`: descriptive name from data
- `description`: prose description from data
- `properties`: all TypedDict fields
- `behaviors`: appropriate infrastructure module

## Design Questions Resolved

**Q: Should virtual entities have name and description?**
A: Yes. Makes them easier to think about, examine in game state, and debug. Names like "Sira's healing promise" are more intuitive than "commit_save_sira_001".

**Q: Should we keep TypedDict definitions?**
A: No. Once data is in entity properties, TypedDict adds no value. Properties dict is already typed as Dict[str, Any], and we validate at load time.

**Q: Do we need centralized helpers like get_expired_commitments()?**
A: No. Each commitment checks itself via on_turn_phase_check handler. Centralized iteration couples turn phases to specific data structures.

**Q: What about performance of iterating all virtual entities each turn?**
A: Not a concern. Big_game has ~10s of commitments/events/gossip at most. Standard entity iteration pattern handles this fine. Don't optimize without evidence.
