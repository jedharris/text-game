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

## Phase 1: Define New Types

**Goal:** Establish the type foundation for the new API.

**Files to create/modify:**
- `src/narration_types.py` (new)
- `src/action_types.py` (modify)

**New types in `narration_types.py`:**

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

**Modify `HandlerResult` in `src/state_accessor.py`:**

```python
@dataclass
class HandlerResult:
    success: bool
    primary: str  # Was: message
    beats: list[str] = field(default_factory=list)  # New
    data: Optional[Dict[str, Any]] = None
```

**Tests:**
- Type validation tests ensuring TypedDict structure
- Test that all required fields are present

---

## Phase 2: Update HandlerResult and Core Handlers

**Goal:** Update `HandlerResult` to use `primary`/`beats` structure and migrate core handlers.

**Files to modify:**
- `src/state_accessor.py`
- `utilities/handler_utils.py`
- `behaviors/core/manipulation.py`
- `behaviors/core/perception.py`
- `behaviors/core/containers.py`
- `behaviors/core/locks.py`
- `behaviors/core/exits.py`
- `behaviors/core/spatial.py`
- `behaviors/core/consumables.py`
- `behaviors/core/meta.py`
- `behaviors/core/combat.py`
- `behaviors/core/actors.py`
- `behaviors/core/interaction.py`
- `behaviors/core/light_sources.py`

**Strategy:**

1. Update `HandlerResult` dataclass:
   - Rename `message` to `primary`
   - Add `beats: list[str]` with default empty list

2. Update `build_action_result` helper:
   ```python
   def build_action_result(
       item: Item,
       primary: str,
       beats: Optional[list[str]] = None,
       data: Optional[dict] = None
   ) -> HandlerResult:
       return HandlerResult(
           success=True,
           primary=primary,
           beats=beats or [],
           data=data or serialize_for_handler_result(item)
       )
   ```

3. Migrate handlers:
   - Most handlers: simple rename `message=` to `primary=`
   - Compound handlers: split into `primary=` and `beats=`
   - `build_message_with_positioning`: returns `(primary, beats)` tuple

**Tests:**
- Update all existing handler tests to use new field names
- Add tests for handlers that now return beats

---

## Phase 3: Create NarrationAssembler

**Goal:** Build the module that constructs `NarrationPlan` from handler results.

**Files to create:**
- `src/narration_assembler.py` (new)
- `tests/test_narration_assembler.py` (new)

**NarrationAssembler responsibilities:**

1. **Build primary_text**: Direct from handler's `primary`

2. **Build secondary_beats**:
   - Include handler's `beats`
   - Select trait beats from entity data (for full verbosity)

3. **Build viewpoint**:
   - Get actor posture and focused_on from state
   - Determine mode from posture
   - Resolve focus_name from entity

4. **Build scope**:
   - Determine scene_kind from verb
   - Set outcome from success
   - Determine familiarity from tracking state

5. **Build entity_refs**:
   - Serialize relevant entities with traits
   - Compute spatial_relation based on viewpoint
   - Assign salience based on action context

6. **Build must_mention**:
   - Format exits_text for location scenes

**Interface:**

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

**Tests:**
- Test each component builder in isolation
- Test full assembly for different scene types
- Test trait selection and randomization
- Test viewpoint mode determination

---

## Phase 4: Update LLMProtocolHandler

**Goal:** Have the protocol handler return `NarrationResult` instead of current format.

**Files to modify:**
- `src/llm_protocol.py`
- `src/action_types.py` (deprecate old `ResultMessage`)

**Changes:**

1. Import and use `NarrationAssembler`

2. Update `handle_command` to:
   - Create `NarrationAssembler`
   - Call handler as before
   - Use assembler to build `NarrationPlan`
   - Return `NarrationResult`

3. Update `handle_query` for location queries:
   - Return `NarrationResult` format for consistency

**Tests:**
- Update all protocol handler tests
- Test that returned structure matches `NarrationResult` type

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
