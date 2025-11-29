# Issue #51: Remove legacy/backward compatibility code from src/

**Status:** Closed

## Problem
The codebase contains legacy code, backward compatibility mechanisms, and test infrastructure in production code that should be removed.

## Items to Remove
- Mock object detection in production code
- Dual code paths for 'legacy' vs 'new' formats
- Test helper classes in production modules
- Backward compatibility aliases
- Misleading docstrings

## Design Document
See docs/remove_legacy.md for detailed phasing plan.

## Files Affected
- src/behavior_manager.py
- src/llm_protocol.py
- src/state_manager.py
- src/llm_narrator.py

---

## Work Log

### Completed Work

**Phase 1: Remove _vocabulary_extensions system**
- Removed redundant `_vocabulary_extensions` field
- Updated `get_merged_vocabulary` to iterate over loaded modules directly

**Phase 2: Simplify module loading**
- Removed mock object detection block
- Updated docstrings to remove "for testing" language
- Fixed 3 tests that relied on mock vocabulary behavior

**Phase 3: Remove legacy handler formats**
- Simplified `get_handler`, `invoke_handler`, `invoke_previous_handler`
- Removed legacy single-function and list-of-functions code paths

**Phase 4: DEFERRED** - Entity behavior format migration requires separate issue

**Phase 5: Clean up llm_protocol.py**
- Removed door name extraction fallback in `_door_to_dict`
- Kept JSONProtocolHandler alias (100+ usages)

**Phase 6: Update state_manager.py docstrings**
- Updated 9 docstrings to remove "for backward compatibility" language

**Phase 7: Move MockLLMNarrator to tests**
- Created `tests/llm_interaction/mock_narrator.py`
- Removed MockLLMNarrator from production code

### Summary
- 6 of 7 phases completed
- Phase 4 deferred due to scope (entity behavior format migration)
- All tests pass (1148 ran)
