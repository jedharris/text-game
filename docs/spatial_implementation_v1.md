# Spatial Structure Implementation Plan

This document outlines the implementation phases for the spatial structure system described in [spatial_structure.md](spatial_structure.md).

---

## Overview

The spatial structure system will be implemented in 6 phases over approximately 3 weeks. Each phase builds on the previous, with clear goals and deliverables.

---

## Phase 1: Part Entity Infrastructure (Week 1)

**Goal:** Part entity type exists and integrates with core systems.

**Tasks:**
1. Add `Part` class to entity models
2. Add `parts: Dict[str, Part]` to GameState
3. Update JSON loader to load part definitions
4. Update entity resolution in parser to check parts collection
5. Add part-aware methods to StateAccessor
6. Add basic validation for parts
7. Add tests for part creation and lookup

**Result:** Parts can be defined in JSON and referenced like any entity.

---

## Phase 2: Implicit Positioning (Week 1)

**Goal:** Most spatial interactions work automatically.

**Tasks:**
1. Add `focused_on` property to Actor
2. Add `interaction_distance` property support (values: "any", "near")
3. Enhance `handle_examine` to set focused_on based on interaction_distance
4. Enhance other core verbs (open, close, take, drop) to check interaction_distance
5. Add tests for implicit positioning
6. Create simple example game demonstrating implicit positioning

**Result:** Players can interact naturally without explicit movement.

---

## Phase 3: Explicit Positioning (Week 2)

**Goal:** Authors can require precise positioning for puzzles.

**Tasks:**
1. Implement `handle_approach` command for explicit positioning
2. Add vocabulary for approach ("approach", "go to", "move to")
3. Add tests for explicit positioning
4. Create alchemy bench example (multi-part object)
5. Document when to use implicit vs explicit positioning

**Result:** Authors can create position-dependent puzzles.

---

## Phase 4: Wall Parts and Attachments (Week 2)

**Goal:** Rooms can have wall parts, items can be at walls.

**Tasks:**
1. Create standard wall part pattern (4 cardinal walls per room)
2. Update `handle_remove` to handle items at parts
3. Create authoring helper to generate standard wall parts
4. Add tests for wall interactions
5. Create example room with wall-mounted items (tapestry puzzle)

**Result:** Rich environmental detail with walls as first-class entities.

---

## Phase 5: Cover System (Optional - Week 3)

**Goal:** Enable combat/stealth scenarios.

**Tasks:**
1. Add `posture` property to Actor (with "cover" value)
2. Add `provides_cover` property support
3. Implement `handle_take_cover` command
4. Create combat/stealth example behaviors
5. Add tests for cover mechanics
6. Document tactical gameplay patterns

**Result:** Framework supports tactical gameplay.

---

## Phase 6: Documentation and Examples (Week 3)

**Tasks:**
1. Update Game Author Guide with Part entity documentation
2. Create tutorial: "When to Create Parts" decision guide
3. Create pattern library:
   - Standard room walls
   - Multi-sided objects
   - Position-dependent NPCs
   - Environmental obstacles
4. Add troubleshooting guide (common mistakes with parts)
5. Create complete example game using spatial features

**Result:** Authors can easily adopt spatial features.

---

## Estimated Effort

**Core changes:**
1. Add Part entity type and collection to GameState (1 day)
2. Update entity resolution to include parts (1 day)
3. Add implicit positioning to core behaviors (2 days)
4. Add `approach` command (1 day)
5. Add StateAccessor part methods (1 day)
6. Add validation for parts (1 day)
7. Update vocabulary system to handle parts (1 day)
8. Testing (2 days)

**Total: 10 days / 2 weeks for core functionality**
**Additional: 5 days / 1 week for optional features and documentation**

---

## Dependencies

- Phase 2 depends on Phase 1
- Phase 3 depends on Phase 2
- Phase 4 can be done in parallel with Phase 3
- Phase 5 is optional and depends on Phases 2-3
- Phase 6 should be done last, after all implementation is complete

---

## Success Criteria

Each phase is considered complete when:
1. All tasks are finished
2. All tests pass
3. Code is reviewed and approved
4. Documentation is updated
5. Example code demonstrates the feature working correctly

---

## Notes

- This is a living document - update it as implementation progresses
- Track actual time spent vs estimates to improve future planning
- Document any deviations from the plan and reasons why
- Record lessons learned at the end of each phase
