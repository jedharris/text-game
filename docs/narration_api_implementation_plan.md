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

## Phase 5: Update Narrator Classes ✅ COMPLETED

**Goal:** Update all narrator classes to consume `NarrationResult`.

**Status:** Completed and closed (Issue #225)

### Completed Work

#### 1. Removed Duplicate Logic from All Narrators

Removed from `src/llm_narrator.py` and `src/mlx_narrator.py` (Ollama narrator retired):
- `visited_locations` and `examined_entities` tracking sets
- `_get_narration_mode()` method
- `_determine_verbosity()` method
- `_update_tracking()` method

These are now handled by `LLMProtocolHandler` which returns `verbosity` in the result.

#### 2. Simplified `process_turn` Method

Before:
```python
result = self.handler.handle_message(json_cmd)
verbosity = self._determine_verbosity(json_cmd, result)
self._update_tracking(json_cmd, result)
result_with_verbosity = dict(result)
result_with_verbosity["verbosity"] = verbosity
narrative = self._call_llm(f"Narrate:\n{json.dumps(result_with_verbosity)}")
```

After:
```python
result = self.handler.handle_message(json_cmd)  # verbosity included
self._print_traits(result)
narrative = self._call_llm(f"Narrate:\n{json.dumps(result)}")
```

#### 3. Simplified `get_opening` Method

Removed local tracking updates. Opening scene queries location but doesn't mark as visited (tracking happens on first command).

#### 4. Updated Mock Narrators and Tests

- Updated `MockLLMNarrator` (tests/llm_interaction/mock_narrator.py)
- Added `visited_locations` and `examined_entities` properties that proxy to handler

#### 5. Updated Tests

- Updated `TestNarrationMode` to test protocol handler's `_get_narration_mode`
- Updated `test_opening_scene_marks_start_location_visited` → `test_opening_scene_queries_location`
- Updated all tests that create handlers per-test instead of using setUp

#### 6. Fixed Pre-existing mypy Issue

**Tests:** All 1925 tests pass. mypy validates with no errors.

---

## Phase 6: Update Prompts ✅ COMPLETED

**Goal:** Update all narrator prompts to match the unified prompt template.

**Status:** Completed (Issue #227)

### Completed Work

#### 1. Updated Core Protocol Files

Replaced `src/narrator_protocol.txt` with unified structure:
- Section A: Invariant API documentation describing NarrationResult format
- `{{STYLE_PROMPT}}` placeholder for game-specific style rules
- Documented all fields: `narration.primary_text`, `narration.secondary_beats`, `viewpoint`, `scope`, `entity_refs`, `must_mention`
- Explained verbosity levels, viewpoint modes, scope fields, and rendering rules
- Removed all references to old `message` field format

#### 2. Updated Game-Specific Style Files

Updated all narrator style files with new NarrationResult format examples:
- `examples/fancy_game/narrator_style.txt`
- `examples/simple_game/narrator_style.txt`
- `examples/extended_game/narrator_style.txt`
- `examples/layered_game/narrator_style.txt`
- `examples/spatial_game/narrator_style.txt`

Each file now contains:
- Style rules (voice, tone, verbosity guidelines)
- Examples using new NarrationResult JSON format with `narration.primary_text`, `secondary_beats`, `scope`, `entity_refs`

#### 3. Key Format Changes in Examples

Old format:
```json
{"success": true, "message": "You pick up the sword.", "verbosity": "full"}
```

New format:
```json
{
  "success": true,
  "verbosity": "full",
  "narration": {
    "primary_text": "You take the sword.",
    "secondary_beats": ["Its weight feels reassuring."],
    "scope": {"scene_kind": "action_result", "outcome": "success", "familiarity": "new"},
    "entity_refs": {"item_sword": {"name": "sword", "traits": ["pitted blade"]}}
  }
}
```

**Tests:** All 1925 tests pass. mypy validates with no errors.

---

## Phase 7: Update GameEngine and Frontends ✅ COMPLETED

**Goal:** Ensure all entry points work with the new API.

**Status:** Completed (Issue #228)

### Completed Work

#### 1. Updated text_game.py

Removed backward compatibility code from `format_command_result`:

```python
def format_command_result(response: Dict[str, Any]) -> str:
    """Format a command result as text.

    Extracts text from NarrationResult format where the message is in
    narration.primary_text and optional secondary_beats.
    """
    narration = response.get("narration", {})
    parts = [narration.get("primary_text", "")]
    if "secondary_beats" in narration:
        parts.extend(narration["secondary_beats"])
    return "\n".join(part for part in parts if part)
```

Fixed remaining references to old message field:
- Updated quit signal handling to use `format_command_result`
- Updated win condition check to use `narration.primary_text`

#### 2. Verified Other Frontends

- `src/game_engine.py` - No old format references
- `src/llm_game.py` - Uses narrator which handles format internally
- `src/mlx_game.py` - Uses narrator which handles format internally

#### 3. Updated Tests

Updated `tests/test_text_game.py`:
- `test_format_command_result_success` - Uses NarrationResult format
- `test_format_command_result_failure` - Uses NarrationResult format
- Added `test_format_command_result_with_beats` - Tests secondary_beats

**Tests:** All 1926 tests pass. mypy validates with no errors.

---

## Phase 8: Cleanup and Documentation ✅ COMPLETED

**Goal:** Remove deprecated code and update documentation.

**Status:** Completed (Issue #229)

### Completed Work

#### 1. Updated Protocol Error Responses in llm_protocol.py

Converted all error responses from old format:
```python
{"type": "error", "message": "..."}
```
To new NarrationResult format:
```python
{
    "type": "error",
    "success": False,
    "verbosity": "brief",
    "narration": {"primary_text": "..."}
}
```

Updated error responses in:
- `handle_message()` - Unknown message type
- `handle_json_string()` - Invalid JSON
- `handle_command()` - Missing action, corrupted state, unknown verb, no handler, inconsistent state
- `handle_query()` - Unknown query type, entity not found, location not found

#### 2. Updated ResultMessage Type in action_types.py

- Removed deprecated `message` field from `ResultMessage`
- Removed `message` field from `ResultError` (kept only `fatal`)
- Added `NarrationPlanDict` type for narration field
- Added `narration` and `verbosity` fields to `ResultMessage`

#### 3. Updated User Documentation

Updated `user_docs/engine_manual.md`:
- Response format section now shows NarrationResult format
- Command flow example uses new format
- Protocol reference uses new format

Updated `user_docs/integration_testing.md`:
- Error message extraction uses `narration.primary_text`
- Helper function updated for new format

**Tests:** All 1926 tests pass. mypy validates with no errors.

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
