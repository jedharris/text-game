# Narration API Implementation Plan

## Overview

This plan implements the Narration-Oriented Engine API as specified in `game_engine_narration_api_design.md`. The refactor eliminates conditional reasoning in the LLM narrator by having the engine pre-compute a complete narration plan.

**Related Issues:**
- #214: Main implementation issue
- #215: Future exploration of fully structured action reports

**Key Constraints:**
- No backward compatibility - complete replacement
- Tight typing with TypedDicts and mypy validation
- TDD throughout

---

## Phase 1: Define New Types ✅ COMPLETED

**Goal:** Establish the type foundation for the new API.

**Status:** Completed and closed (Issue #217)

### Completed Work

#### 1. Result Type Field Renames

All `message` fields renamed to semantically distinct names:

| Type | Old Field | New Field | Purpose |
|------|-----------|-----------|---------|
| `HandlerResult` | `message` | `primary` | Core statement of what occurred |
| `EventResult` | `message` | `feedback` | Behavior response text |
| `UpdateResult` | `message` | `detail` | Operation detail/error text |

Domain-specific Result types (already had semantic names):

| Type | Field | Semantic Type |
|------|-------|---------------|
| `AttackResult` | `narration` | NarrationText |
| `FleeResult` | `narration` | NarrationText |
| `CraftResult` | `description` | DescriptionText |
| `DialogResult` | `response` | ResponseText |
| `ServiceResult` | `outcome` | OutcomeText |
| `TreatmentResult` | `effect` | EffectText |

#### 2. Semantic Type Aliases (in `src/types.py`)

NewType aliases for documentation and optional strict typing:

```python
# Core Result text types
FeedbackText = NewType('FeedbackText', str)   # EventResult.feedback
DetailText = NewType('DetailText', str)       # UpdateResult.detail
PrimaryText = NewType('PrimaryText', str)     # HandlerResult.primary

# Domain-specific text types
NarrationText = NewType('NarrationText', str)     # Attack/flee descriptions
DescriptionText = NewType('DescriptionText', str) # Crafting descriptions
ResponseText = NewType('ResponseText', str)       # NPC dialog responses
OutcomeText = NewType('OutcomeText', str)         # Service outcomes
EffectText = NewType('EffectText', str)           # Treatment effects
```

**Note:** Field types remain `str` for practical use. Semantic types are:
- Documented in docstrings with "Semantic type: TypeName"
- Available for optional strict typing: `FeedbackText("message")`
- No casting required for normal usage

#### 3. HandlerResult Structure

```python
@dataclass
class HandlerResult:
    success: bool
    primary: str      # Semantic type: PrimaryText
    beats: list[str] = field(default_factory=list)
    data: Optional[Dict[str, Any]] = None
```

#### 4. Files Modified

- `src/types.py` - Added semantic type aliases
- `src/state_accessor.py` - Renamed fields in EventResult, UpdateResult, HandlerResult
- All handlers in `behaviors/core/`, `behavior_libraries/`, `utilities/`
- All behavior files in `behaviors/regions/`
- All test files

#### 5. Narration Types (in `src/narration_types.py`)

```python
from typing import TypedDict, Literal, Optional

class ViewpointInfo(TypedDict, total=False):
    mode: Literal["ground", "elevated", "concealed"]
    posture: Optional[Literal["climbing", "on_surface", "behind_cover"]]
    focus_name: Optional[str]

class ScopeInfo(TypedDict):
    scene_kind: Literal["location_entry", "look", "action_result"]
    outcome: Literal["success", "failure"]
    familiarity: Literal["new", "familiar"]

class EntityState(TypedDict, total=False):
    open: bool
    locked: bool
    lit: bool

class EntityRef(TypedDict, total=False):
    name: str
    type: Literal["item", "container", "door", "actor", "exit", "location"]
    traits: list[str]
    spatial_relation: Literal["within_reach", "below", "above", "nearby"]
    state: EntityState
    salience: Literal["high", "medium", "low"]

class MustMention(TypedDict, total=False):
    exits_text: str

class NarrationPlan(TypedDict, total=False):
    primary_text: str
    secondary_beats: list[str]
    viewpoint: ViewpointInfo
    scope: ScopeInfo
    entity_refs: dict[str, EntityRef]
    must_mention: MustMention

class NarrationResult(TypedDict):
    success: bool
    verbosity: Literal["brief", "full"]
    narration: NarrationPlan
    data: dict  # Raw engine data for debugging/UI
```

**Tests:** All 1893 tests pass. mypy validates with no field-naming errors.

---

## Phase 2: Update HandlerResult and Core Handlers ✅ COMPLETED

**Goal:** Update `HandlerResult` to use `primary`/`beats` structure and migrate core handlers.

**Status:** Completed and closed (Issue #219)

### Completed Work

#### 1. Updated `build_message_with_positioning` (utilities/positioning.py)

Changed return type from `str` to `Tuple[str, List[str]]`:
```python
def build_message_with_positioning(
    base_messages: List[str],
    position_message: Optional[str]
) -> Tuple[str, List[str]]:
    """Returns (primary, beats) tuple."""
```

- `primary`: First message (core action statement)
- `beats`: Positioning message + any additional messages

#### 2. Updated `build_action_result` (utilities/handler_utils.py)

New signature:
```python
def build_action_result(
    item: Item,
    primary: str,
    beats: Optional[List[str]] = None,
    data: Optional[Dict[str, Any]] = None
) -> HandlerResult:
```

#### 3. Updated `execute_entity_action` (utilities/handler_utils.py)

Now uses `build_message_with_positioning` tuple return and populates `beats`.

#### 4. Migrated handlers

- `behaviors/core/manipulation.py` - Updated all 4 `build_action_result` calls
- `behaviors/core/interaction.py` - Updated all `build_message_with_positioning` usages, removed unused import
- `examples/spatial_game/behaviors/lib/spatial/look_out.py` - Updated to use beats

#### 5. Updated Protocol Handler (src/llm_protocol.py)

For backward compatibility, the protocol handler combines `primary` and `beats` into a single `message` field in the response. Phase 4 will change this to return the structured `NarrationResult`.

#### 6. Updated Tests

- `tests/test_handler_utils.py` - Updated `build_action_result` and `execute_entity_action` tests
- `tests/test_take_implicit_positioning.py` - Movement checks now use `result.beats`
- `tests/test_open_close_implicit_positioning.py` - Movement checks now use `result.beats`
- `tests/test_entity_behavior_invocation.py` - Behavior message checks now use `result.beats`
- `tests/test_trading.py` - Behavior message checks now use `result.beats`

**Tests:** All 1893 tests pass. mypy validates with no new errors.

---

## Phase 3: Create NarrationAssembler ✅ COMPLETED

**Goal:** Build the module that constructs `NarrationPlan` from handler results.

**Status:** Completed and closed (Issue #223)

### Completed Work

#### 1. Created NarrationAssembler class (`src/narration_assembler.py`)

The `NarrationAssembler` class takes a `HandlerResult` and game state context, and builds a complete `NarrationPlan` for the LLM narrator.

```python
class NarrationAssembler:
    def __init__(self, accessor: StateAccessor, actor_id: ActorId):
        ...

    def assemble(
        self,
        handler_result: HandlerResult,
        verb: str,
        verbosity: Literal["brief", "full"],
        familiarity: Literal["new", "familiar"]
    ) -> NarrationPlan:
        ...
```

#### 2. Implemented component builders

1. **`_build_secondary_beats`**: Includes handler beats; extracts trait beats from `llm_context` for full verbosity
2. **`_build_viewpoint`**: Maps posture to mode (ground/elevated/concealed); resolves focus_name from entity
3. **`_build_scope`**: Determines scene_kind from verb (location_entry/look/action_result); maps success to outcome
4. **`_build_entity_refs`**: Builds EntityRef from handler data including traits, state flags, and spatial_relation
5. **`_build_must_mention`**: Formats exits_text for location/look scenes

#### 3. Verb classification constants

- `LOCATION_ENTRY_VERBS`: go, north, south, east, west, up, down, etc.
- `LOOK_VERBS`: look, l, examine, x, inspect

#### 4. Posture normalization

- `cover` → `behind_cover`
- `climbing`, `on_surface` → elevated mode
- `behind_cover`, `concealed` → concealed mode

#### 5. Created unit tests (`tests/test_narration_assembler.py`)

32 tests covering:
- Viewpoint building (ground, elevated, concealed modes)
- Scope building (scene_kind, outcome, familiarity)
- Secondary beats (handler beats, trait extraction)
- Entity refs (from handler data, with traits/state)
- Must mention (exits_text formatting)
- Full assembly integration

**Tests:** All 1925 tests pass. mypy validates with no errors.

---

## Phase 4: Update LLMProtocolHandler ✅ COMPLETED

**Goal:** Have the protocol handler return `NarrationResult` instead of current format.

**Status:** Completed and closed (Issue #224)

### Completed Work

#### 1. Core Implementation (src/llm_protocol.py)

- Imported NarrationAssembler and NarrationResult types
- Added visit tracking sets (`visited_locations`, `examined_entities`)
- Rewrote `handle_command` to use NarrationAssembler
- Added helper methods:
  - `_get_narration_mode`: Looks up verb's narration_mode from merged vocabulary
  - `_determine_verbosity`: Decides "brief" vs "full" based on mode, success, and tracking
  - `_determine_familiarity`: Decides "new" vs "familiar" based on visit/examine tracking
  - `_update_tracking`: Updates visited_locations and examined_entities sets

#### 2. Frontend Update (src/text_game.py)

Updated `format_command_result()` to extract text from new NarrationResult format:
```python
def format_command_result(response: Dict[str, Any]) -> str:
    if "narration" in response:
        narration = response["narration"]
        parts = [narration.get("primary_text", "")]
        if "secondary_beats" in narration:
            parts.extend(narration["secondary_beats"])
        return "\n".join(part for part in parts if part)
    # Old format backward compatibility...
```

#### 3. Refactoring Tool (tools/refactor_result_message.py)

Created AST-based tool to safely refactor test assertions for the new format:
- Handles `result["message"]` → `get_result_message(result)`
- Handles `result.get("message", "")` → `get_result_message(result)`
- Handles `result.get("error", {}).get("message", "")` → `get_result_message(result)`
- Handles `assertIn("message", result)` → `assertIn("narration", result)`
- Automatically adds helper function and typing imports where needed

#### 4. Test Updates

- Updated 15+ test files to handle new NarrationResult format
- Added `get_result_message()` helper functions where needed
- Updated assertions checking for "error" key to check for "narration" key
- Fixed mocking in test_turn_phase_hooks.py to patch vocabulary service

**Tests:** All 1925 tests pass. mypy validates with no errors.

---

## Phase 5: Update Narrator Classes

**Goal:** Update all narrator classes to consume `NarrationResult`.

**Files to modify:**
- `src/mlx_narrator.py`
- `src/llm_narrator.py`
- `src/ollama_narrator.py`

**Changes:**

1. Remove verbosity determination logic (now in protocol handler)

2. Remove visit tracking (now handled by protocol handler via assembler)

3. Simplify `process_turn`:
   - Parse input
   - Call handler
   - Pass `NarrationResult` JSON to LLM
   - Return prose

4. Update `_call_llm` to format `NarrationResult` appropriately

**Tests:**
- Update narrator tests to use new result format
- Test that narrators correctly pass through the narration plan

---

## Phase 6: Update Prompts

**Goal:** Update all narrator prompts to match the unified prompt template.

**Files to modify:**
- `src/narrator_protocol.txt`
- `src/ollama_narrator_protocol.txt`
- `examples/fancy_game/narrator_style.txt`
- Any other game-specific prompts

**Changes:**

1. Replace current prompts with unified structure:
   - Section A: Engine API (from `unified_narrator_prompt_revised_api.md`)
   - Section B: Game-specific style

2. Update style files to be Section B only (no API details)

**Tests:**
- Manual testing with each narrator
- Verify narration quality matches or exceeds current

---

## Phase 7: Update GameEngine and Frontends

**Goal:** Ensure all entry points work with the new API.

**Files to modify:**
- `src/game_engine.py`
- `src/mlx_game.py`
- `src/text_game.py`
- `src/llm_game.py` (if exists)
- Any other game frontends

### text_game.py Changes

`text_game.py` directly consumes JSON from `LLMProtocolHandler` without an LLM narrator. It needs to extract display text from the new `NarrationResult` format.

**Current:**
```python
def format_command_result(response: Dict[str, Any]) -> str:
    if response.get("success"):
        return response.get("message", "Done.")
    else:
        error = response.get("error", {})
        return error.get("message", "That didn't work.")
```

**New:**
```python
def format_command_result(response: NarrationResult) -> str:
    narration = response.get("narration", {})
    if response.get("success"):
        # For text_game, just use primary_text directly
        # (no LLM to weave in beats/traits)
        return narration.get("primary_text", "Done.")
    else:
        return narration.get("primary_text", "That didn't work.")
```

**Additional changes:**
- Update `format_item_query` and `format_inventory_query` if query responses also change
- Import `NarrationResult` type for type hints

### Other Frontend Changes

1. Remove any verbosity/tracking logic that moved to protocol handler

2. Ensure narrator creation passes correct parameters

3. Update any direct protocol handler usage

**Tests:**
- End-to-end tests with each frontend
- Manual playtesting with `text_game` to verify basic text output
- Verify save/load/quit signals still work

---

## Phase 8: Cleanup and Documentation

**Goal:** Remove deprecated code and update documentation.

**Files to modify:**
- Remove deprecated `ResultMessage` usage
- Update docstrings throughout
- Update `user_docs/` if affected

**Tasks:**

1. Remove any backward-compatibility shims
2. Run mypy and fix any type errors
3. Run full test suite
4. Update README if API changes affect users

---

## Testing Strategy

### Unit Tests (per phase)
- Type validation
- Component isolation
- Edge cases

### Integration Tests
- Full command flow from input to narration
- Different scene types (location_entry, look, action_result)
- Success and failure paths
- Viewpoint modes

### Manual Testing
- Play through fancy_game with each narrator
- Verify narration quality
- Check for regressions

---

## Risk Assessment

### High Risk
- **Handler migration volume**: Many handlers to update. Mitigate with mechanical find/replace for simple cases.

### Medium Risk
- **Prompt changes**: New prompt format may need tuning. Mitigate with iterative testing.

### Low Risk
- **Type system**: TypedDict is well-supported. Just need mypy compliance.

---

## Estimated Scope

| Phase | Files | Complexity |
|-------|-------|------------|
| 1. Types | 2 | Low |
| 2. Handlers | ~15 | Medium (volume) |
| 3. Assembler | 2 | Medium |
| 4. Protocol | 2 | Medium |
| 5. Narrators | 3 | Low |
| 6. Prompts | ~4 | Low |
| 7. Frontends | ~3 | Low |
| 8. Cleanup | Various | Low |

---

## Success Criteria

1. All tests pass
2. mypy reports no errors
3. Narration quality is equal or better than current
4. No backward compatibility code remains
5. All frontends work correctly
