# Typing Refinement Plan

## Overview

Following the completion of the initial typing plan (Issue #166), this document identifies remaining weakly typed or untyped values that could be strengthened.

**NOTE**: Phase 2 of the original plan was incomplete - StateAccessor methods were missed and still use `str` instead of typed IDs.

## Decisions

- **Entity Type**: Use Union type (not Protocol) - entity types are a closed set
- **Entity Location**: Define in state_manager.py (not separate module)
- **TypedDicts for properties**: Not needed - typed property accessors already provide access
- **Dead Union types**: Remove `str` branches from `ensure_word_entry`, `get_object_word`, `get_display_name`

## Implementation Plan

### Phase 1: Remove Dead Union Types
1. Simplify `ensure_word_entry` to only accept `WordEntry | None`
2. Simplify `get_object_word` to only accept `WordEntry | None`
3. Simplify `get_display_name` to only accept `WordEntry | None`
4. Fix any tests that pass strings instead of WordEntry

### Phase 2: Entity Type Alias
1. Define `Entity = Location | Item | Lock | Actor | Part | ExitDescriptor` in state_manager.py
2. Export from src/__init__.py

### Phase 3: StateAccessor Type Annotations
1. Add imports for entity types and ID types
2. Update all getter method signatures with typed parameters and return types
3. Fix callers to cast at boundaries where needed

### Phase 4: BehaviorManager Cleanup
1. Replace `entity: Any` with `Optional[Entity]`
2. Replace `accessor: Any` with `StateAccessor`
3. Type `_validate_vocabulary(vocabulary: Dict)`
4. Type `behaviors: List[str]` in validators.py

### Phase 5: Utility Function Types
1. Update utilities/utils.py function signatures with typed IDs
2. Update utilities/handler_utils.py function signatures
3. Add return type annotations

### Phase 6: Behavior Handler Annotations (DEFERRED)
**Status**: Deferred - adding type annotations to handlers exposes numerous mypy errors
throughout the codebase due to `action.get()` returning `Optional` values that are
passed to functions expecting non-optional parameters. Fixing this would require
extensive changes to either:
- Add null checks/assertions throughout handler code
- Change function signatures to accept Optional parameters
- Use TypedDict with Required/NotRequired fields

This is better handled as a separate, larger effort.

## Keep As-Is

- `properties: Dict[str, Any]` - legitimate extensibility for game-specific properties
- `Union[str, Path, Dict]` for load_game_state - legitimate API flexibility
- `Union[WordType, Set[WordType]]` for word_type - legitimate polymorphism
- `FlexDict.get() -> Any` - intentionally flexible
- `set_flag(value: Any)` - flags are dynamic
- LLM Protocol return types - low priority, limited benefit
