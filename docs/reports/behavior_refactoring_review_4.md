# Behavior Refactoring Design Review - Session 4 Summary

## Date: 2025-11-24

## Overview

Fourth and final review pass of `behavior_refactoring.md` following three previous reviews. This session addressed all remaining design issues identified in the initial comprehensive review, completing the design validation process.

## Issues Identified and Resolved

### Issue #8: StateAccessor and BehaviorManager Coupling (Accepted as Design Feature)

**Issue**: StateAccessor requires BehaviorManager, creating tight coupling. Question was whether this coupling should be optional.

**Resolution**: Accepted coupling as intentional and justified by design goals. Added comprehensive design rationale section explaining:

1. **Why coupling exists**: StateAccessor's core responsibility is "automatic behavior invocation" - this is a fundamental design principle, not an implementation detail

2. **Why optional would be wrong**:
   - Undermines design principle that all updates trigger behaviors automatically
   - Would require `if self.behavior_manager:` checks everywhere, adding complexity
   - Creates unsupported mode where updates bypass behavior system
   - Violates encapsulation by forcing callers to decide if behaviors should run

3. **Testing approach**: Use real BehaviorManager (potentially with no modules loaded) for testing pure state mutations, consistent with "no mocking" principle

**Documentation Added**: Lines 420-447 - "Design Rationale: StateAccessor and BehaviorManager Coupling" section

**Decision**: Coupling is a **feature** that enforces architectural invariant, not a limitation.

---

### Issue #9: Speculative actor_id in Visibility Functions (Accepted)

**Issue**: Visibility functions in `behaviors/core/visibility.py` include `actor_id` parameter that isn't currently used.

**Resolution**: Leave as-is for consistency and future extensibility.

**Motivation**:
- Consistency with all other utility functions that accept `actor_id`
- Enables future actor-specific perception (e.g., NPC with sonar-like abilities seeing differently than player)
- Low cost to include unused parameter vs. cost of breaking API change later

**Decision**: Keep `actor_id` parameter in visibility functions for future extensibility.

---

### Issue #10: Noun Vocabulary Specification (Documented)

**Issue**: Design didn't clearly document where nouns (item names, NPC names) come from - behavior modules or entity data?

**Resolution**: Added comprehensive documentation explaining that nouns come from entity data, not behavior modules.

**Rationale documented**:

1. **Separation of concerns**: Behavior modules define *what you can do* (verbs/handlers), entity data defines *what exists* (nouns)

2. **Avoids duplication**: Item names already exist in data model (`item.name = "sword"`). Requiring behavior modules to re-register would duplicate and risk inconsistencies

3. **Game knowledge stays in data**: Vocabulary generator knows *data structure* (entities have `.name`), not game semantics (what entities do)

4. **Behavior modules focus on interactions**: Register verbs and handlers, not objects themselves

**Where nouns come from**:
- Item names → `Item.name` property
- NPC names → `NPC.name` property
- Location names → `Location.name` property
- Verbs → behavior module vocabularies

**Documentation Added**: Lines 1367-1393 - "vocabulary_generator.py - Nouns come from entities, not behavior modules" section with complete rationale

**Summary**: Nouns = entity data (what exists), Verbs = behavior modules (what you can do). This separates game content from game behavior.

---

### Issue #11: Error Messages Expose Internal Field Names (Documented as Acceptable)

**Issue**: `_set_path()` error messages expose internal field names like `"Field not found: location"` or `"Cannot append to non-list field: inventory"` to end users.

**Resolution**: Documented that this is acceptable because these errors indicate **developer bugs**, not user errors. Added comprehensive design rationale.

**Why acceptable**:

These errors occur in two scenarios, both developer bugs:
1. **Developer typos**: Handler uses wrong field names (`"loaction"` instead of `"location"`)
2. **Data structure mismatches**: Entity structure doesn't match handler expectations (inventory is string, not list)

**Should never occur in production** because:
- They represent bugs in handler implementation
- Testing (especially NPC tests) should catch all such errors before deployment
- If they appear in production, that's a bug to fix, not an error message to improve

**Error message philosophy**:
- Deliberately technical to help developers debug quickly
- Provide exact information (field path, operation, entity)
- Appear during development/testing, not production
- User-friendly messages would obscure the actual problem

**Production considerations**:
- Implementation *could* be enhanced to log technical errors while showing generic messages to users
- BUT this is **not part of initial design** because proper solution is to prevent bugs via testing
- Adding dual messages (technical + user-friendly) would complicate API unnecessarily

**Recommended approach**: Treat `_set_path()` errors as assertions that should never trigger. If they appear:
1. During development: Fix handler code bug immediately
2. During testing: Write test reproducing bug, then fix
3. In production: Log error, investigate bug, deploy fix

**Documentation Added**: Lines 449-502 - "Design Rationale: _set_path() Error Messages" section

**Conclusion**: Error messages are a **debugging tool**, not a user-facing feature.

---

### Issue #12: Migration Path Missing BehaviorManager Update (Already Fixed)

**Issue**: Original review noted migration path didn't explicitly document implementing `get_event_for_verb()` method.

**Resolution**: Verified this was already fixed in Phase 2a, step 2 (line 1330):
- "Implement `get_event_for_verb()` method"

**Status**: No changes needed - issue was resolved in previous review session.

---

## Summary of Session 4 Work

All remaining design issues from the comprehensive review have been addressed:

1. **Issue #8 (Coupling)**: Accepted as intentional design feature, documented rationale
2. **Issue #9 (Speculative actor_id)**: Accepted for consistency and future extensibility
3. **Issue #10 (Noun vocabulary)**: Documented that nouns come from entity data with complete rationale
4. **Issue #11 (Error messages)**: Documented as acceptable developer-oriented debugging tool
5. **Issue #12 (Migration path)**: Verified already fixed in previous session

## Design Completeness

The design document now includes comprehensive documentation for all design decisions, including:

- **Three design rationale sections** explaining potentially controversial decisions
- **Clear separation** of nouns (entity data) from verbs (behavior modules)
- **Production considerations** for error handling without mandating implementation
- **Complete migration path** with all necessary implementation steps

## Files Modified

- `/Users/jed/Development/text-game/docs/behavior_refactoring.md` - Added three design rationale sections:
  - Lines 420-447: StateAccessor and BehaviorManager Coupling
  - Lines 449-502: _set_path() Error Messages
  - Lines 1367-1393: Noun Vocabulary Specification

## Current Status

**All design review issues resolved.** The behavior refactoring design is complete and ready for implementation:

- All 12 identified issues addressed (8 with design changes, 4 accepted/documented as-is)
- No outstanding design holes or inconsistencies
- Clear rationale documented for all potentially controversial decisions
- Comprehensive migration path with testing strategy
- Complete examples for all major patterns

## Next Steps

The design is ready for implementation. Recommended approach from all review sessions:
- Implement Phase 2a (StateAccessor and utilities) completely with full test coverage
- Implement one complete handler (e.g., `handle_take`) end-to-end in Phase 2b to validate design
- Only proceed with remaining handlers after first handler proves the design works
- Implement `visibility.py` utilities alongside first handler to validate query pattern

## Review Session History

1. **Review 1** (2025-11-23): Initial comprehensive review, fixed terminology (#4) and test structure (#7)
2. **Review 2** (2025-11-23): Fixed handler loading order (#1), handler chaining (#2), removed `related_changes`
3. **Review 3** (2025-11-24): Fixed actor_id threading (#3), imports (#5), conflict detection (#6), query handling (#5)
4. **Review 4** (2025-11-24): Addressed coupling (#8), actor_id in visibility (#9), noun vocabulary (#10), error messages (#11), verified migration path (#12)

All review sessions complete. Design validated and ready for implementation.
