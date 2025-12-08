# Actor Interaction System - Session Handoff

## Session Summary

This session completed the design decision phase for the actor interaction system. We systematically worked through design questions and documented 29 fundamental decisions.

## What Was Accomplished

### Decisions Documented (Questions 1-28 + Command Decision)

1. **Architecture & Integration (Q1-5)**: ✅ Complete
   - Actor framework in core (Decision 1)
   - First-class event integration (Decision 2)
   - NPC action timing and turn progression (Decisions 3-4)
   - Save/load strategy (Decision 5)

2. **Core Systems Design (Q6-13)**: ✅ Complete
   - Condition storage and management (Decision 10)
   - Condition stacking rules (Decision 11)
   - Cure mechanics (Decision 12)
   - Damage calculation (Decision 13)
   - Armor mechanics (Decision 14)
   - Attack target selection (Decision 15)
   - Damage modification pattern (Decision 21)
   - Armor as property only (Decision 22)
   - Morale: properties only (Decision 23)
   - Pack coordination: properties only (Decision 24)

3. **Environmental & Spatial Integration (Q14-17)**: ✅ Complete
   - Environmental hazards automatic (Decision 16)
   - Breath tracking (Decision 17)
   - Environmental constants in metadata (Decision 26)
   - Environmental bonuses as conventions (Decision 27)
   - Cover mechanics author-implemented (Decision 28)

4. **Combat & Interaction Commands (Q18)**: ✅ Complete
   - Core commands: `attack`, `defend`, `guide`, `activate` (Decision 29)
   - Specialized commands remain game-specific

### Key Design Pattern Established

**"Properties Only, Authors Implement Logic"** - Used consistently for:
- Morale and fleeing
- Pack coordination
- Damage type handling (immunities, resistances, weaknesses)
- Environmental bonuses
- Cover mechanics

**Core Principle**: Core provides minimal infrastructure and mechanisms. Authors provide all strategy, meaning, and policy through behaviors.

## What Remains

### Design Questions Still Open

**Questions 19-23** (Combat & Interaction Mechanics):
- Q19: Range modeling (validation logic)
- Q20: Area attack mechanics
- Q21: Health reaching 0 (death/incapacitation)
- Q22: Immunities and resistances (already partially covered in Decision 21)
- Q23: Weaknesses (already partially covered in Decision 21)

**Questions 24-27** (NPC Behavior & AI):
- Q24: When/how NPCs act (already answered in Decision 3)
- Q25: Activation triggers
- Q26: Fleeing mechanics
- Q27: Pack behavior scaling

**Questions 28-30** (Services & Non-Combat):
- Q28: NPC services framework
- Q29: Knowledge modeling
- Q30: Relationship mechanics

**Questions 31-34** (Technical Implementation):
- Q31: Randomness (already decided: deterministic)
- Q32: Turn counters for conditions
- Q33: "After turn" effects ordering
- Q34: Testing strategy

**Questions 35-37** (Scope & Phasing):
- Q35: Minimal Viable Combat System
- Q36: Phase 1 scope
- Q37: Backward compatibility

### Analysis Performed

During the session, I analyzed the remaining questions (19-37) and drafted proposed decisions, but **these were not yet discussed or recorded** because the user wanted to slow down and review the command decision first.

**Drafted but not recorded**:
- Decision 30: Range is validation logic (properties only)
- Decision 31: Area attacks author-implemented
- Decision 32: on_death behavior determines consequences
- Decision 33-34: Immunities/resistances/weaknesses (properties only)
- Decision 35-37: Activation, fleeing, pack scaling (all properties only)
- Decision 38-40: Services, knowledge, relationships (properties only)
- Decision 41-44: Technical implementation details
- Decision 45-46: Phasing and backward compatibility

## Next Session Should Address

### Option 1: Continue Design Questions (Recommended)

Work through remaining questions 19-37 systematically with user review:
1. Review Questions 19-23 (Combat Mechanics) - some already covered in Decision 21
2. Review Questions 24-27 (NPC AI) - some already covered in Decision 3
3. Review Questions 28-30 (Services) - entirely new territory
4. Review Questions 31-34 (Technical) - mostly answered
5. Review Questions 35-37 (Scope & Phasing) - critical for implementation planning

### Option 2: Move to API Design

Begin detailed API design for core systems:
- `apply_damage(actor, amount, accessor)` - exact signature and behavior
- `add_condition(actor, condition_name, properties, accessor)` - condition management API
- `remove_condition(actor, condition_name, accessor)` - cure mechanics
- `progress_conditions(actor, accessor)` - turn-based progression
- `apply_environmental_effects(actor, state, accessor)` - hazard checking
- Event context structure for damage, heal, attack events

### Option 3: Create Property Schemas

Document recommended property schemas based on decisions:
- Actor properties (health, attacks, conditions, armor, ai, etc.)
- Item properties for interactions (cures, treats, provides_breathing, etc.)
- Location part properties (breathable, hazard_condition, cover_value, etc.)

### Option 4: Implementation Phasing Plan

Create detailed implementation plan:
- Phase 1 scope (core infrastructure)
- Phase 2 scope (social systems)
- Phase 3 scope (coordination)
- Test-driven development approach
- Migration strategy

## Important Context for Next Session

### Established Principles

1. **Core provides infrastructure, authors provide strategy**
2. **Deterministic by default** (no random rolls)
3. **Properties are conventions, not requirements** (flexible schemas)
4. **Graceful degradation** over forced migration
5. **Event-driven architecture** (first-class events via accessor.update)
6. **Turn-based progression** (every successful command is a turn)
7. **Cheap early returns** for performance (check before acting)

### Files to Reference

- `/Users/jed/Development/text-game/docs/actor_interaction_design_decisions.md` - 29 decisions documented
- `/Users/jed/Development/text-game/docs/actor_interaction_questions.md` - tracking answered vs open questions
- `/Users/jed/Development/text-game/docs/actor_interaction_simplified_cases.md` - 8 simplified use cases showing desired functionality
- `/Users/jed/Development/text-game/docs/actor_interactions_use_cases.md` - 12 detailed use cases

### Key Unresolved Detail

**Attack Selection**: Decision 29 says "use first attack in array" but Questions 11 and 19 ask about:
- NPC attack selection (which attack to use from multiple options)
- Range validation (when can an attack be used)
- Player attack selection syntax

These may need refinement in next session.

## User's Last Direction

User approved the minimal command set (`attack`, `defend`, `guide`, `activate`) and asked for:
1. Record this as a design decision ✅ Done (Decision 29)
2. Write handoff message for next session ✅ This document

## Recommendation for Next Session

**Start with**: Review the drafted decisions for Questions 19-37 that I analyzed but didn't record. These follow the same "properties only" pattern we've established, so review should be quick. Then move to API design or phasing plan based on user preference.

**Priority**: Questions 35-37 (scope and phasing) are most critical for starting implementation.
