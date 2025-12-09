# Documentation Upgrade Plan

This document describes the complete plan for bringing documentation up to the current implementation.

---

## Goals

1. **Bring all documentation current** - Document all implemented capabilities
2. **Consolidate the authoring manual** - Integrate separate chapter files into the main manual
3. **Fill documentation holes** - Add missing documentation identified during analysis
4. **Update the engine manual** - Bring developer docs up to current implementation
5. **Document behavior libraries** - Add reference documentation for the new libraries

---

## Current State

### Documentation Files

| File | Status | Notes |
|------|--------|-------|
| `user_docs/authoring_manual/` | Restructured | Split into 12 chunk files |
| `user_docs/authoring_manual/00_start_here.md` | Current | Entry point with document map |
| `user_docs/authoring_manual/01_overview.md` | Current | Overview and quick start |
| `user_docs/authoring_manual/02_core_concepts.md` | Current | Game world, JSON format |
| `user_docs/authoring_manual/03_actors.md` | Current | Actor fundamentals |
| `user_docs/authoring_manual/04_actor_interactions.md` | Current | Combat, services, etc. |
| `user_docs/authoring_manual/05_behaviors.md` | Current | Behavior system |
| `user_docs/authoring_manual/06_patterns.md` | Current | Common patterns |
| `user_docs/authoring_manual/07_spatial.md` | Current | Spatial rooms |
| `user_docs/authoring_manual/08_parser.md` | Current | Parser and commands |
| `user_docs/authoring_manual/09_llm.md` | Current | LLM integration |
| `user_docs/authoring_manual/10_testing.md` | Current | Testing and debugging |
| `user_docs/authoring_manual/11_advanced.md` | Current | Advanced topics |
| `user_docs/engine_manual.md` | Current | Updated with turn phases, actor behaviors |
| `user_docs/spatial_quick_reference.md` | Current | No changes needed |
| `user_docs/integration_testing.md` | Current | No changes needed |
| `user_docs/Archive/` | Archived | Old consolidated files moved here |

### Framework Features Implemented (docs/framework_hole_filling.md)

All these are now implemented in `behavior_libraries/`:

1. **Turn Counter** - `state.turn_count`, `state.increment_turn()`
2. **Scheduled Events** - `timing_lib/scheduled_events.py`
3. **Darkness/Visibility** - `darkness_lib/visibility.py`
4. **Companion Following** - `companion_lib/following.py`
5. **NPC Movement/Patrol** - `npc_movement_lib/patrol.py`, `wander.py`
6. **Crafting/Combining** - `crafting_lib/recipes.py`
7. **Dialog/Conversation** - `dialog_lib/topics.py`

### Documentation Holes (identified previously)

1. Global Flags System - ✅ documented in 11_advanced.md
2. Turn Phase Hook System - ✅ documented in 11_advanced.md
3. Environmental Effects System - ✅ documented in 04_actor_interactions.md
4. Light Source Behaviors - ✅ documented in 11_advanced.md
5. Relationship System - ✅ documented in 04_actor_interactions.md
6. Condition System - ✅ documented in 04_actor_interactions.md
7. Services System - ✅ documented in 04_actor_interactions.md
8. Pack System - ✅ documented in 04_actor_interactions.md
9. Morale System - ✅ documented in 04_actor_interactions.md

---

## Implementation Plan

### Phase 1: Add Actor Overview Section

**Goal**: Add overview section linking to actor chapters (COMPLETED).

**Tasks**:
1. ✅ Add Section 4 "Actors and Interactions" overview to authoring_manual.md
2. ✅ Renumber subsequent sections
3. ✅ Add series reference notes to actor chapter files

**Status**: Complete

---

### Phase 1.5: Restructure Authoring Manual into Chunks

**Goal**: Break the ~3900 line authoring manual into logical chunks in a dedicated directory.

**Status**: ✅ Complete

**Tasks completed**:

1. ✅ Created `user_docs/authoring_manual/` directory
2. ✅ Created `00_start_here.md` as entry point with document map
3. ✅ Split authoring_manual.md into 12 logical chunks
4. ✅ Updated cross-references between chunks
5. ✅ Moved original files to `user_docs/Archive/`
6. ✅ Updated this document to reflect new structure

**Structure created**:
```
user_docs/authoring_manual/
├── 00_start_here.md      # Entry point, document map
├── 01_overview.md        # Overview, Quick Start
├── 02_core_concepts.md   # Core Concepts
├── 03_actors.md          # Actor fundamentals
├── 04_actor_interactions.md  # Combat, services, etc.
├── 05_behaviors.md       # The Behavior System
├── 06_patterns.md        # Common Patterns
├── 07_spatial.md         # Spatial Rooms
├── 08_parser.md          # Parser and Commands
├── 09_llm.md             # LLM Integration
├── 10_testing.md         # Testing and Debugging
└── 11_advanced.md        # Save/Load, Advanced, Tips, Help
```

---

### Phase 2: Document Missing Core Features

**Goal**: Add documentation for undocumented core capabilities.

**Status**: ✅ Complete

**Add to Authoring Manual**:

#### 2.1 Game State Management (new section after Actors)

- Global flags: `state.set_flag()`, `state.get_flag()`
- `GameState.extra` for non-player global data
- Use cases and examples

#### 2.2 Turn System (expand existing)

Current coverage is minimal. Add:

- Turn phase hooks (NPC_ACTION, ENVIRONMENTAL_EFFECT, CONDITION_TICK, DEATH_CHECK)
- Hook execution order diagram
- How to register hook handlers via vocabulary
- Turn counter (`state.turn_count`)
- When turns advance (only on successful commands)

#### 2.3 Light Sources (new section or add to Items)

- Creating light source items
- Auto-light on take, extinguish on drop
- `provides_light` property
- Note: Darkness enforcement coming in darkness_lib

**Estimated effort**: ~2 hours

---

### Phase 3: Document Behavior Libraries

**Goal**: Create reference documentation for all new behavior libraries.

**Status**: ✅ Complete

**Add new section to Authoring Manual**: "Behavior Libraries Reference"

Each library needs:
- Purpose and use cases
- How to include in a game
- Configuration properties
- API functions available
- Example usage

#### Libraries to document:

1. **timing_lib** - Turn counter, scheduled events
2. **darkness_lib** - Visibility checks, darkness enforcement
3. **companion_lib** - Companion following, restrictions
4. **npc_movement_lib** - Patrol routes, wandering
5. **crafting_lib** - Recipe matching, combining items
6. **dialog_lib** - Topic management, conversation state

**Structure for each library**:
```
### timing_lib - Turn Counter and Scheduled Events

**Purpose**: Track turn counts and schedule events to fire at specific turns.

**Include in your game**:
[symlink instructions]

**Configuration**:
[property examples]

**API**:
[function list]

**Example**:
[complete example]
```

**Estimated effort**: ~4 hours

---

### Phase 4: Update Engine Manual

**Goal**: Bring developer documentation current with implementation.

**Status**: ✅ Complete

**Updates needed**:

#### 4.1 Module Organization
- Add `behaviors/actors/` directory to the diagram
- Add `behavior_libraries/` with all subdirectories
- Update module listing

#### 4.2 State Manager
- Document `GameState.turn_count`
- Document `GameState.extra` structure
- Document flag methods

#### 4.3 Behavior Manager
- Update vocabulary merging to include hooks
- Document hook registration mechanism

#### 4.4 LLM Protocol Handler
- Document turn phase firing
- Add hook invocation flow

#### 4.5 New Section: Turn Phases
- Detailed explanation of phase execution
- Hook registration and invocation
- Phase hook constants

#### 4.6 New Section: Actor Behaviors
- Overview of actor behavior modules
- Condition system internals
- Relationship system internals
- Combat system flow

**Estimated effort**: ~3 hours

---

### Phase 5: Review and Polish

**Goal**: Ensure consistency and completeness.

**Tasks**:

1. Review all cross-references and fix broken links
2. Verify all code examples are accurate
3. Check consistency of terminology throughout
4. Review against implementation to catch any gaps
5. Test example code snippets
6. Generate table of contents for long documents

**Estimated effort**: ~2 hours

---

### Phase 6: Example Game and Big Game Analysis

**Goal**: Provide working examples and prepare for big game implementation.

**Tasks**:

#### 6.1 Upgrade examples/actor_interaction_test

- Review current implementation
- Update to use new behavior libraries where appropriate
- Demonstrate good game design practices
- Ensure all framework features are exercised
- Add comments explaining design choices

#### 6.2 Analyze big_game_overview.md

After documentation is complete:
- Review for comprehensiveness against new framework capabilities
- Check that all behavior libraries are utilized appropriately
- Identify any gaps or improvements needed
- Document findings in big_game_implementation.md

**Estimated effort**: ~3 hours

---

## Phasing Summary

| Phase | Description | Effort | Dependencies |
|-------|-------------|--------|--------------|
| 1 | Add actor overview section | ~1 hour | None | ✅ Complete |
| 1.5 | Restructure into chunks | ~2 hours | Phase 1 |
| 2 | Document missing core features | ~2 hours | Phase 1.5 |
| 3 | Document behavior libraries | ~4 hours | Phase 1.5 |
| 4 | Update engine manual | ~3 hours | None (parallel) |
| 5 | Review and polish | ~2 hours | Phases 1.5-4 |
| 6 | Example game and big game analysis | ~3 hours | Phases 1.5-5 |

**Total estimated effort**: ~17 hours

**Parallelization**: Phases 2-3 (authoring) and Phase 4 (engine) can run in parallel after Phase 1.5.

---

## Detailed Task Breakdown

### Phase 1 Tasks

- [ ] Copy authoring_actors.md content into authoring_manual.md as Section 4
- [ ] Copy authoring_actor_interactions.md content into authoring_manual.md as Section 5
- [ ] Renumber subsequent sections (Patterns becomes 6, etc.)
- [ ] Update internal cross-references to use section numbers instead of file links
- [ ] Add section anchors for deep linking
- [ ] Either delete or add deprecation notice to standalone files
- [ ] Test that all examples still make sense in new context

### Phase 2 Tasks

- [ ] Write "Game State Management" section
  - [ ] Document set_flag/get_flag with examples
  - [ ] Document GameState.extra with use cases
  - [ ] Show complete example of flag-based game progression
- [ ] Expand "Turn System" section
  - [ ] Document turn_count and increment_turn
  - [ ] Document all four turn phase hooks
  - [ ] Show hook registration via vocabulary
  - [ ] Add execution order diagram
  - [ ] Clarify when turns advance
- [ ] Write "Light Sources" section
  - [ ] Document provides_light property
  - [ ] Document auto-light/extinguish behaviors
  - [ ] Note darkness_lib for full enforcement

### Phase 3 Tasks

- [ ] Write behavior libraries intro section
- [ ] Document timing_lib
  - [ ] Turn counter API
  - [ ] Scheduled events API
  - [ ] Configuration properties
  - [ ] Example: time-pressure scenario
- [ ] Document darkness_lib
  - [ ] Location darkness properties
  - [ ] Visibility check API
  - [ ] Actions blocked in darkness
  - [ ] Example: torch-required cave
- [ ] Document companion_lib
  - [ ] Making companions
  - [ ] Following mechanics
  - [ ] Location restrictions
  - [ ] Example: wolf pack following
- [ ] Document npc_movement_lib
  - [ ] Patrol routes
  - [ ] Wandering behavior
  - [ ] Movement frequency
  - [ ] Example: wandering merchant
- [ ] Document crafting_lib
  - [ ] Recipe definition
  - [ ] combine/craft commands
  - [ ] Location/skill requirements
  - [ ] Example: telescope repair
- [ ] Document dialog_lib
  - [ ] Topic configuration
  - [ ] Topic prerequisites
  - [ ] ask/talk commands
  - [ ] Example: information NPC

### Phase 4 Tasks

- [ ] Update module organization section
  - [ ] Add new directories to tree
  - [ ] Add new modules to listings
- [ ] Document GameState changes
  - [ ] turn_count field
  - [ ] extra dict
  - [ ] Flag methods
- [ ] Document turn phase system
  - [ ] Hook constants
  - [ ] Phase execution order
  - [ ] Hook invocation mechanism
- [ ] Add actor behaviors overview
  - [ ] Link to implementation files
  - [ ] Explain condition/relationship internals for developers

### Phase 5 Tasks

- [ ] Check all internal links in authoring_manual.md
- [ ] Check all internal links in engine_manual.md
- [ ] Verify code examples compile/run
- [ ] Check terminology consistency
- [ ] Review for gaps against codebase
- [ ] Generate/update table of contents

---

## Decisions (resolved)

1. **Standalone chapters**: Move authoring_actors.md and authoring_actor_interactions.md to Archive after integration.

2. **Library documentation depth**: Match existing document depth. For authoring docs, provide enough API orientation that authors can think constructively about how to achieve their goals.

3. **Example game**: Upgrade existing examples/actor_interaction_test to demonstrate new framework features and good game design practices. After doc work, analyze big_game_overview.md for comprehensiveness and leave design/implementation comments in big_game_implementation.md.

---

## Reference: Previously Identified Documentation Holes

### Already Documented (in authoring_actor_interactions.md)

- Conditions - Section 2
- Treatment/Curing - Section 3
- Combat - Section 4
- Services - Section 5
- Relationships/Domestication - Section 6
- Environmental Effects - Section 7
- Morale/Fleeing - Section 8
- Pack Coordination - Section 9

### Still Need Documentation

1. **Global Flags System** (state_manager.py:471-484)
   - `state.set_flag(name, value)`
   - `state.get_flag(name, default)`
   - Storage in `player.properties["flags"]`

2. **Turn Phase Hook System** (hooks.py, llm_protocol.py:265-301)
   - NPC_ACTION, ENVIRONMENTAL_EFFECT, CONDITION_TICK, DEATH_CHECK
   - Hook registration via vocabulary
   - Execution order

3. **Turn Counter** (state_manager.py)
   - `state.turn_count`
   - `state.increment_turn()`
   - Turn advancement rules

4. **Light Source Behaviors** (behaviors/core/light_sources.py)
   - Auto-light on take
   - Auto-extinguish on drop/put
   - `states["lit"]` tracking

5. **GameState.extra** (state_manager.py)
   - Non-player global data storage
   - Use by behavior libraries

---

## Success Criteria

Documentation upgrade is complete when:

1. Authoring manual is a single consolidated document covering all authoring topics
2. All implemented behavior libraries have reference documentation
3. All core framework features are documented
4. Engine manual reflects current implementation
5. All code examples are accurate and tested
6. Cross-references work correctly
7. No gaps between implementation and documentation
