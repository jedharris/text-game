# Remove Legacy/Backward Compatibility Code

**GitHub Issue:** #51

## Issue
The codebase contains legacy code, backward compatibility mechanisms, and test infrastructure in production code that should be removed. This includes:
- Mock object detection in production code
- Dual code paths for "legacy" vs "new" formats
- Test helper classes in production modules
- Backward compatibility aliases
- Misleading docstrings

## Goals
1. Remove all legacy code paths that are no longer needed
2. Move test infrastructure out of production code
3. Simplify code by removing dual-path handling
4. Update docstrings to remove misleading "backward compatibility" language

## Assumptions
- No external code depends on anything in `src/`
- All game state files have been converted to current format
- No backward compatibility is required
- Tests will reveal any dependencies on removed behavior

---

## Phase 1: Remove `_vocabulary_extensions` System

**Files:** `behavior_manager.py`

**Changes:**
1. Remove `_vocabulary_extensions` field (line 32-33)
2. Remove the append to `_vocabulary_extensions` (line 272-273)
3. Search for any code that reads `_vocabulary_extensions` and remove/update it

**Status:** Complete

**Results:**
- Removed `_vocabulary_extensions` field from `__init__`
- Removed append to `_vocabulary_extensions` in `load_module`
- Updated `get_merged_vocabulary` to iterate over `self._modules.values()` and get vocabulary directly from each module instead of using the redundant `_vocabulary_extensions` list
- All tests pass (1148 ran, 10 errors unrelated to changes - wx display requirement)

---

## Phase 2: Simplify Module Loading (Remove Test-Only Code Path)

**Files:** `behavior_manager.py`

**Changes:**
1. Update `load_module` to only accept string paths, not module objects
2. Remove the if/else branch handling module objects (lines 235-245)
3. Update docstring (line 228)
4. Remove comment about testing vs production (line 234)
5. Remove Mock object detection block (lines 257-264)

**Status:** Complete

**Results:**
- Kept dual path (string or module object) since many tests legitimately pass imported modules. The design is valid, only comments were misleading.
- Updated docstring to say "already-imported module object" instead of "for testing"
- Removed all "for testing" and "for production" comments
- Removed mock object detection block entirely - validation now runs on all vocabularies
- Fixed 3 tests in `test_behavior_manager.py` that used MagicMock modules without setting `vocabulary = None`
- All tests pass (1148 ran, 10 errors unrelated - wx display requirement)

---

## Phase 3: Remove Legacy Handler Formats

**Files:** `behavior_manager.py`

**Changes:**
1. In `get_handler` (lines 361-373): Remove legacy format handling, assume all handlers are list of tuples
2. In `invoke_handler` (lines 546-547): Remove legacy format branch
3. In `invoke_previous_handler` (lines 606-607): Remove legacy format branch

**Status:** Complete

**Results:**
- Simplified `get_handler`: removed isinstance checks and legacy branches, now just returns `handlers[0][0]`
- Simplified `invoke_handler`: removed legacy format checks, now just accesses `handlers[0][0]`
- Simplified `invoke_previous_handler`: removed legacy format checks, now just accesses `handlers[next_pos][0]`
- All tests pass (1148 ran, 10 errors unrelated - wx display requirement)

---

## Phase 4: Remove Accessor Backward Compatibility

**Files:** `behavior_manager.py`

**Changes:**
1. Remove backward compatibility code at lines 456-457 that extracts state from accessor
2. Ensure all callers pass accessor correctly

**Status:** DEFERRED - Requires discussion

**Analysis:**
The backward compatibility code supports two different entity behavior systems:
1. **Old dict format**: `behaviors = {"on_event": "module:function"}` with signature `on_event(entity, state, context)`
2. **New list format**: `behaviors = ["module1", "module2"]` with signature `on_event(entity, accessor, context)`

Migration would require:
- Updating 5 test fixtures in `tests/fixtures/`
- Updating ~12 behavior functions in `behaviors/` using the old signature
- Removing the dict format handling code in `invoke_entity_behavior`

**Files affected:**
- `behaviors/items/rubber_duck.py`
- `behaviors/core/consumables.py`
- `behaviors/core/light_sources.py`
- `behaviors/core/containers.py`
- Tests in `test_protocol_behaviors.py`, `test_behavior_manager.py`
- Fixtures: `test_game_with_behaviors.json`, `test_game_with_core_behaviors.json`

This is a significant migration that should be discussed before proceeding.

---

## Phase 5: Clean Up llm_protocol.py

**Files:** `llm_protocol.py`

**Changes:**
1. Remove `JSONProtocolHandler` alias (lines 606-607)
2. Search for any uses of `JSONProtocolHandler` and update to `LLMProtocolHandler`
3. Remove door name extraction fallback logic (lines 583-591)
4. Update `_door_to_dict` docstring (line 577)

**Status:** Complete

**Results:**
- Removed door name extraction fallback logic in `_door_to_dict` - now just delegates to `entity_to_dict`
- Renamed `JSONProtocolHandler` to `LLMProtocolHandler` across 25 files
- Removed the alias and backward compatibility test
- All tests pass (1147 ran, 10 errors unrelated - wx display requirement)

---

## Phase 6: Update state_manager.py Docstrings

**Files:** `state_manager.py`

**Changes:**
Update docstrings to remove "for backward compatibility" language:
1. `Location.llm_context` (line 132)
2. `Item.states` (line 153)
3. `Item.portable` (line 165)
4. `Item.pushable` (line 175)
5. `Item.provides_light` (line 185)
6. `Item.container` (line 195)
7. `Item.llm_context` (line 206)
8. `Actor.stats` (line 318)
9. `Actor.flags` (line 330)

**Status:** Complete

**Results:**
- Updated 9 docstrings to remove "for backward compatibility" language
- These properties provide convenient access to nested dict data and are part of the intended API
- All tests pass (1148 ran, 10 errors unrelated - wx display requirement)

---

## Phase 7: Move MockLLMNarrator to Tests

**Files:** `llm_narrator.py`, new test helper file

**Changes:**
1. Remove `MockLLMNarrator` class from `llm_narrator.py` (lines 467-512)
2. Create `tests/helpers/mock_narrator.py` (or similar) with the class
3. Update any test imports to use new location

**Status:** Complete

**Results:**
- Created `tests/llm_interaction/mock_narrator.py` with the MockLLMNarrator class
- Updated import in `tests/llm_interaction/test_llm_narrator.py`
- Removed MockLLMNarrator from `src/llm_narrator.py`
- All tests pass (1148 ran, 10 errors unrelated - wx display requirement)

---

## Deferred Work

**Phase 4: Entity Behavior Format Migration**

The backward compatibility code in `invoke_entity_behavior` supports two different entity behavior systems that would require significant migration work:

1. Old dict format: `behaviors = {"on_event": "module:function"}`
2. New list format: `behaviors = ["module1", "module2"]`

Files requiring migration:
- `behaviors/items/rubber_duck.py`
- `behaviors/core/consumables.py`
- `behaviors/core/light_sources.py`
- `behaviors/core/containers.py`
- Test fixtures in `tests/fixtures/`
- Various tests in `test_protocol_behaviors.py`, `test_behavior_manager.py`

This should be a separate issue/PR due to scope.

---

## Final Checklist
- [x] All tests pass
- [x] Most "legacy" and "backward compatibility" comments removed from src/
- [x] MockLLMNarrator moved out of production code
- [x] Legacy handler format code paths removed
- [x] _vocabulary_extensions system removed
- [ ] Entity behavior format migration (deferred to Phase 4)
