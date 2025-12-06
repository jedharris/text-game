# Handler Precedence and Tier System Design

## Problem Statement

The current BehaviorManager implementation does not support layered behavior libraries. When multiple modules define vocabulary or handlers for the same verbs, the system throws hard errors instead of providing precedence and delegation mechanisms.

This blocks the implementation of shared behavior libraries (issue #54), which require three-tier hierarchy:
- **Tier 1**: Game-specific behaviors (highest precedence)
- **Tier 2**: Shared library behaviors (middle precedence)
- **Tier 3**: Core behaviors (lowest precedence)

### Current Behavior

**BehaviorManager._register_verb_mapping()** ([src/behavior_manager.py:63](src/behavior_manager.py#L63)):
- Throws ValueError if verb already maps to different event
- No concept of tier precedence or override
- Blocks vocabulary extension by libraries

**BehaviorManager._register_handler()** ([src/behavior_manager.py:89](src/behavior_manager.py#L89)):
- Allows handlers from different source_types to coexist
- Stores handlers in load-order list
- Errors only if same verb from same source_type
- Has basic delegation via `invoke_previous_handler()` (line 521)

### Blocking Example

**layered_game** ([examples/layered_game/](examples/layered_game/)):
```
behaviors/
├── core -> symlink (Tier 3)
├── offering_lib -> symlink (Tier 2)
└── household_shrine.py (Tier 1)
```

**Conflict:**
- `offering_lib` defines "offer" verb → `on_receive_offering` event
- `core` defines "give" verb → different event
- BehaviorManager throws error instead of allowing both to coexist

**From [docs/layered_game_design.md:418](docs/layered_game_design.md#L418):**
> Unable to resolve "offer" vs "give" conflict - blocks game execution
>
> Architectural issue identified: no support for tier precedence or delegation

### Why Extended Game Works Today

**extended_game** ([examples/extended_game/](examples/extended_game/)) has only two tiers:
```
behaviors/
├── core -> symlink
├── magic_wand.py
├── crystal_ball.py
└── spellbook.py
```

It works because game-specific behaviors add NEW vocabulary ("read", "peer", "wave") that doesn't conflict with core. No precedence needed.

## Design Summary

We need to support three key capabilities:

### 1. Tier Precedence (Override Hierarchy)

Game behaviors should override library behaviors, which override core:
- If game defines "examine" handler → use game's handler first
- If library defines "offer" and core defines "give" → both should coexist (different verbs)
- If game and library both define "offer" → game's vocabulary takes precedence
- Vocabulary extensions should merge without conflicts when possible

### 2. Entity-Specific Delegation

If Tier N handler can't process a specific entity, delegate to Tier N+1:
- Game's `handle_examine()` handles custom entities, delegates to core for standard items
- Already partially implemented via `invoke_previous_handler()` (line 521)
- Need to make delegation tier-aware

### 3. Vocabulary Coexistence

Multiple verbs with different semantics should coexist:
- "offer X to Y" (offering_lib) - ritual offering mechanics
- "give X to Y" (core) - simple item transfer
- Both valid commands with different game meanings
- Parser and vocabulary system already support this

## Design Questions

### 1. Tier Assignment ✅ RESOLVED

How do we assign precedence tiers to modules?

**CHOSEN: Directory Depth-Based Tiers**

Tier is determined by directory nesting depth relative to `behaviors/`:
- Files directly in `behaviors/` → Tier 1 (highest precedence, game-specific)
- Files in `behaviors/*/` subdirectories → Tier 2 (libraries)
- Files in `behaviors/*/*/` → Tier 3 (deeper libraries/core)
- And so on...

**Example from layered_game:**
```
examples/layered_game/behaviors/
├── mushroom_grotto.py              # depth 0 → Tier 1 (game)
├── core/                            # symlink
│   └── perception.py                # depth 1 → Tier 2
├── puzzle_lib/                      # symlink
│   └── sequence_tracker.py          # depth 1 → Tier 2
└── offering_lib/                    # symlink
    └── offering_handler.py          # depth 1 → Tier 2
```

**Within-tier ordering:**
- Alphabetical order by directory name (e.g., offering_lib < puzzle_lib)
- Python's os.walk guarantees deterministic ordering
- Game developer controls structure explicitly

**Implementation:**
```python
# In discover_modules():
relative_to_behaviors = py_file.relative_to(path)
depth = len(relative_to_behaviors.parts) - 1  # -1 because filename doesn't count
tier = depth + 1  # Tier 1 = depth 0, Tier 2 = depth 1, etc.
```

**Advantages:**
- ✅ Deterministic: Directory structure + alphabetical ordering = predictable
- ✅ Developer control: Game author controls structure explicitly via directories
- ✅ No metadata: Pure structural approach, can't get out of sync
- ✅ Easy to reason about: "Closer to behaviors/ = higher precedence"
- ✅ Supports multiple libraries: All at same depth have same tier
- ✅ Works with symlinks: Depth measured from behaviors/, not symlink target

### 2. Vocabulary Conflicts ⚠️ ARCHITECTURAL ISSUE IDENTIFIED

When should vocabulary registration error vs override?

**Current behavior:**
- Same verb → different event: ERROR (always)
- Same verb → same event: ALLOW (silent)

**Critical architectural problem discovered:**

The current system has a **1:1 verb-to-event mapping** that fundamentally conflicts with tier-based layering:

```python
# In BehaviorManager:
self._verb_event_map: Dict[str, str] = {}  # ONE verb → ONE event
```

**Command execution flow:**
1. LLMProtocolHandler → BehaviorManager.invoke_handler(verb)
2. Handler → accessor.update(entity, changes, verb=verb)
3. StateAccessor.update() → behavior_manager.get_event_for_verb(verb) → **returns ONE event**
4. Invoke entity behavior with that event
5. Apply state changes

**The problem:** If same verb maps to different events in different tiers:
- Tier 1: "examine" → "on_examine_mushroom"
- Tier 2: "examine" → "on_examine"

Only ONE event can be stored. If Tier 1's event doesn't apply to a particular entity (returns allow=False or entity doesn't have that behavior), Tier 2's event is never tried.

**Example failure scenario:**

```python
# Tier 1 (game): mushroom_grotto.py
vocabulary = {"verbs": [{"word": "examine", "event": "on_examine_mushroom"}]}

def on_examine_mushroom(entity, accessor, context):
    if entity.id.startswith("mushroom_"):
        return EventResult(allow=True, message="Glowing spores...")
    # Not a mushroom - should fall through to Tier 2 event
    return EventResult(allow=False)  # But no fallback!

# Tier 2 (core): perception.py
vocabulary = {"verbs": [{"word": "examine", "event": "on_examine"}]}

def on_examine(entity, accessor, context):
    return EventResult(allow=True, message=entity.description)
```

**What should happen when player types "examine bucket":**
1. Try Tier 1 event "on_examine_mushroom" → returns allow=False (not a mushroom)
2. Fall through to Tier 2 event "on_examine" → returns allow=True with description

**What actually happens:**
1. Only ONE event registered (depending on load order)
2. Either Tier 1 event fails with no fallback, OR Tier 2 event runs (never using game's custom logic)

**Required solution:**
- Change `_verb_event_map` from `Dict[str, str]` to `Dict[str, List[tuple]]`
- Store events in tier order: `[(tier, event, module), ...]`
- StateAccessor.update() must try events in order, falling through if:
  - Entity doesn't have behavior for that event
  - Behavior returns allow=False
  - Behavior returns None (not applicable)

**Two separate delegation mechanisms:**
1. **Handler delegation** (already works via invoke_previous_handler):
   - `_handlers[verb]` stores LIST of handlers
   - Handlers can delegate to next handler in chain
   - ✅ Needs tier ordering, but structure already supports it
2. **Event delegation** (broken - needs implementation):
   - Must support LIST of events per verb
   - StateAccessor must try events in tier order with automatic fallthrough
   - ❌ Requires architectural changes

**Impact on existing code:**

Changes required in **BehaviorManager** ([src/behavior_manager.py](src/behavior_manager.py)):
- **Line 27**: Change `_verb_event_map: Dict[str, str]` → `Dict[str, List[tuple]]`
- **Line 29**: Add tier tracking to `_verb_sources`
- **Line 63-87**: Rewrite `_register_verb_mapping()` to:
  - Accept tier parameter
  - Append to list instead of replacing
  - Sort by tier (lower tier number = higher precedence)
  - Validate conflicts within same tier
- **Line 89-118**: Update `_register_handler()` to use tier instead of source_type
- **Line 174-219**: Update `discover_modules()` to calculate tier from directory depth
- **Line 221-262**: Update `load_module()` to pass tier to registration functions
- **Line 350-360**: Replace `get_event_for_verb()` with `get_events_for_verb()` returning list

Changes required in **StateAccessor** ([src/state_accessor.py](src/state_accessor.py)):
- **Line 389-451**: Rewrite `update()` to:
  - Call new `behavior_manager.get_events_for_verb(verb)` → returns list
  - Loop through events in tier order
  - Try each event with `invoke_behavior()`
  - Continue to next event if:
    - Entity doesn't have behavior module for that event
    - Behavior returns EventResult(allow=False)
    - Behavior returns None (not implemented for this entity)
  - Stop on first EventResult(allow=True)
  - Apply changes only if at least one behavior allowed

Changes required in **existing behavior modules**:
- ❌ **No breaking changes** - all existing behaviors continue working
- Behaviors that return EventResult(allow=False) will now fallthrough to lower tiers
- This is the CORRECT behavior (was broken before)

**Backward compatibility:**
- Extended_game: Single tier (depth 0 regular + depth 1 symlink) continues working
- Simple_game: No custom behaviors, unaffected
- Event fallthrough is transparent - if entity doesn't define higher-tier event, lower-tier event fires automatically

**Proposed conflict resolution rules:**
- **Cross-tier, same verb → different event**: ALLOW (store both, try in tier order)
- **Cross-tier, same verb → same event**: ALLOW (redundant but harmless, deduplicate)
- **Within-tier, same verb → different event**: ERROR (library design conflict)
- **Different verbs**: ALWAYS ALLOW (current behavior)

### 3. Handler Delegation ✅ RESOLVED

Given our solutions to Questions 1 & 2, how should handler delegation work?

**Context from previous decisions:**
- **Q1**: Tiers determined by directory depth, within-tier ordering is alphabetical
- **Q2**: Event delegation is AUTOMATIC (StateAccessor tries events in tier order)
- **Q2**: Handlers already stored in lists by verb, just need tier-based ordering

**Current implementation** ([src/behavior_manager.py:521](src/behavior_manager.py#L521)):
- `invoke_previous_handler()` allows handlers to delegate to next handler in chain
- Uses `_handler_position_list` to track position
- Handlers stored in load order (not tier-ordered)
- Delegation is EXPLICIT (handler must call `accessor.invoke_previous_handler()`)

**CHOSEN: Explicit Handler Delegation with Tier Ordering**

**Rationale:**

Handler delegation is fundamentally different from event delegation:
- **Events** filter on entity-specific applicability (automatic fallthrough makes sense)
- **Handlers** orchestrate entire command flow with game logic (explicit control needed)

**Why explicit delegation is necessary:**

Handlers must be able to:
1. **Intercept**: Prevent deeper handlers from running even when current tier can't fully handle
2. **Augment**: Run deeper handler, then modify its result
3. **Delegate conditionally**: Choose whether to go deeper based on game logic

These capabilities are impossible with automatic delegation.

**Key design decision: What gets passed to deeper handler?**

Handlers receive and pass only the **action dict** (parser output):
- `actor_id`: Who is acting
- `object`: WordEntry from parser (with synonyms)
- `adjective`: Optional
- `direction`: Optional

Each handler independently:
- Parses the action dict
- Finds entities from game state
- Makes decisions based on fresh lookups

**Why not pass computed results?**
- Safety: Avoids silent errors from wrong assumptions passed down
- Independence: Each handler can interpret action differently
- Simplicity: No trust relationships between tiers

**Trade-off:** Some duplicate work (each handler finds entities), but this is unavoidable for safety and is acceptable performance-wise.

**Use Case 1: Interception**

Game layer prevents examining cursed items entirely:

```python
# Tier 1 (game): cursed_items.py
def handle_examine(accessor, action):
    """Prevent examining cursed items."""
    actor_id = action.get("actor_id")
    obj = action.get("object")
    entity = find_accessible_item(accessor, obj, actor_id)

    if entity and entity.properties.get("cursed"):
        # Intercept: Don't let core examine run
        return HandlerResult(
            success=False,
            message="Your eyes slide off the object, unable to focus."
        )

    # Not cursed, delegate to core
    return accessor.invoke_deeper_handler("examine", action)

# Tier 2 (core): perception.py - never called for cursed items
def handle_examine(accessor, action):
    # Standard examine logic
    ...
```

**Use Case 2: Augmentation**

Game layer adds magical aura to core's examine:

```python
# Tier 1 (game): magical_detection.py
def handle_examine(accessor, action):
    """Add magical aura detection to examine."""
    # Let core handle the examine first
    result = accessor.invoke_deeper_handler("examine", action)

    if result.success:
        actor_id = action.get("actor_id")
        obj = action.get("object")
        entity = find_accessible_item(accessor, obj, actor_id)

        if entity and entity.properties.get("magical"):
            # Augment core's message
            return HandlerResult(
                success=True,
                message=result.message + "\n\nThe item glows with magical energy.",
                data=result.data
            )

    return result

# Tier 2 (core): perception.py - runs first, result augmented
def handle_examine(accessor, action):
    actor_id = action.get("actor_id")
    obj = action.get("object")
    entity = find_accessible_item(accessor, obj, actor_id)

    if not entity:
        return HandlerResult(success=False, message="You don't see that here.")

    return HandlerResult(success=True, message=entity.description)
```

**Use Case 3: Conditional Delegation**

Game layer handles magical items specially, delegates mundane items to core:

```python
# Tier 1 (game): custom_examine.py
def handle_examine(accessor, action):
    """Custom examine for magical items."""
    actor_id = action.get("actor_id")
    obj = action.get("object")
    entity = find_accessible_item(accessor, obj, actor_id)

    if entity and entity.properties.get("magical"):
        # Handle magical items completely in game layer
        result = accessor.update(entity, {}, verb="examine", actor_id=actor_id)
        return HandlerResult(
            success=True,
            message=f"It glows with magic! {result.message or entity.description}"
        )

    # Not magical - delegate to core
    return accessor.invoke_deeper_handler("examine", action)

# Tier 2 (core): perception.py
def handle_examine(accessor, action):
    # Standard examine for all items (including magical if Tier 1 doesn't exist)
    actor_id = action.get("actor_id")
    obj = action.get("object")
    entity = find_accessible_item(accessor, obj, actor_id)

    if not entity:
        return HandlerResult(success=False, message="You don't see that here.")

    result = accessor.update(entity, {}, verb="examine", actor_id=actor_id)
    return HandlerResult(
        success=True,
        message=result.message or entity.description
    )
```

**Implementation details:**

1. **Rename for clarity:** `invoke_previous_handler()` → `invoke_deeper_handler()`
   - Matches mental model: Tier 1 (surface) → Tier 2 (deeper) → Tier 3 (core)

2. **Handler storage:** Change handler tuples from `(handler, module_name)` to `(handler, module_name, tier)`

3. **Ordering:** Sort handlers by `(tier, alphabetical)` to ensure deterministic delegation

4. **Within-tier conflicts:** ERROR if same tier defines same handler (forces library designers to use different verbs)

5. **Delegation semantics:** `invoke_deeper_handler()` skips to next tier (not just next handler in list)

**Changes required:**
- **BehaviorManager.invoke_handler()**: Initialize with tier-ordered handlers
- **BehaviorManager.invoke_deeper_handler()**: Renamed from `invoke_previous_handler()`, skip to next tier
- **StateAccessor.invoke_deeper_handler()**: Renamed convenience method
- **Handler tuples**: Add tier field `(handler, module_name, tier)`

### 4. Breaking Changes ✅ RESOLVED

Can we avoid breaking extended_game while adding layering?

**ANSWER: Yes, no breaking changes required**

**Analysis:**

1. **extended_game structure:**
   ```
   behaviors/
   ├── core -> symlink (depth 1 → Tier 2)
   ├── magic_wand.py (depth 0 → Tier 1)
   ├── crystal_ball.py (depth 0 → Tier 1)
   └── spellbook.py (depth 0 → Tier 1)
   ```
   - Game modules (depth 0) become Tier 1
   - Core modules (depth 1 via symlink) become Tier 2
   - This is the CORRECT tier assignment

2. **Why extended_game works today:**
   - Game modules add NEW vocabulary ("read", "peer", "wave")
   - No vocabulary conflicts with core
   - No duplicate handlers for same verb

3. **What changes with tier system:**
   - Vocabulary registration accepts tier parameter, stores in lists
   - Handler registration uses tier instead of source_type
   - No conflicts detected because:
     - Different verbs → always allowed
     - Same verb, same event, different tiers → deduplicated (harmless)

4. **Event delegation (automatic):**
   - If game defines "examine" event, it tries first
   - If game entity doesn't handle it, falls through to core
   - This is BETTER behavior (fixes current limitation)
   - extended_game doesn't use this pattern today, so no change

5. **Handler delegation (explicit):**
   - Renamed `invoke_previous_handler()` → `invoke_deeper_handler()`
   - **BREAKING?** Only if extended_game uses `invoke_previous_handler()`
   - Check: No current usage in behaviors/core or examples
   - Safe to rename

**Compatibility guarantees:**
- ✅ Single-tier games (simple_game) - no behaviors, unaffected
- ✅ Two-tier games (extended_game) - depth-based tiers match current intent
- ✅ Vocabulary merging - works as before, now supports conflicts across tiers
- ✅ Handler invocation - works as before, now with tier ordering
- ✅ Event delegation - new feature, transparent fallthrough (improvement)

**Migration required:**
- ❌ None for existing games
- ✅ New games can use tier system immediately

## Use Cases

### Use Case 1: Game Overrides Library Vocabulary

**Scenario:** Game wants custom "examine" behavior for special entities

**Current:** Game can add `handle_examine()`, but vocabulary conflict if "examine" verb redefined

**Desired:** Game's "examine" vocabulary entry overrides library/core, game's handler called first with delegation available

### Use Case 2: Library Extends Vocabulary Without Conflicts

**Scenario:** offering_lib adds "offer" verb, core has "give" verb

**Current:** Error - both try to register vocabulary

**Desired:** Both verbs coexist, each mapped to their respective events

### Use Case 3: Entity-Specific Handler Delegation

**Scenario:** Game's `handle_examine()` handles magic items, delegates to core for mundane items

**Current:** `invoke_previous_handler()` works but not tier-aware

**Desired:** Handler can delegate to "next tier" explicitly, skipping other same-tier handlers

### Use Case 4: Multiple Libraries at Same Tier

**Scenario:** layered_game uses both puzzle_lib and offering_lib (both Tier 2)

**Current:** May conflict if both define same verb

**Desired:** Libraries at same tier should not conflict (design rule: libraries should be orthogonal)

## Success Criteria

- [ ] layered_game loads successfully with all three tiers
- [ ] Vocabulary from all tiers merges without errors
- [ ] Game behaviors can override library/core behaviors
- [ ] Handler delegation works across tiers
- [ ] No breaking changes to extended_game or simple_game
- [ ] Clear error messages when real conflicts occur (same tier, same verb, different semantics)

## Proposed Design

### Overview

Implement a tier-based behavior precedence system where modules are organized by directory depth, with automatic event delegation and explicit handler delegation.

### Core Principles

1. **Tiers determined by directory structure** - No metadata, purely structural
2. **Automatic event delegation** - Try events in tier order until one succeeds
3. **Explicit handler delegation** - Handlers control flow with `invoke_deeper_handler()`
4. **Safe by default** - Development-time errors for conflicts, no silent failures

### Tier Assignment

**Rule:** Tier = directory depth + 1 from `behaviors/`

```python
# In BehaviorManager.discover_modules()
relative_to_behaviors = py_file.relative_to(path)
depth = len(relative_to_behaviors.parts) - 1  # -1 for filename
tier = depth + 1  # Tier 1 = depth 0, Tier 2 = depth 1, etc.
```

**Within-tier ordering:** Alphabetical by directory name (via os.walk)

**Example:**
```
behaviors/
├── game_specific.py              # Tier 1 (depth 0)
├── puzzle_lib/ (symlink)         # Tier 2 (depth 1)
│   └── sequence_tracker.py
└── core/ (symlink)                # Tier 2 (depth 1)
    └── perception.py
```

### Vocabulary Registration

**Changes to BehaviorManager:**

```python
# OLD:
self._verb_event_map: Dict[str, str] = {}

# NEW:
self._verb_event_map: Dict[str, List[tuple]] = {}  # verb -> [(tier, event, module), ...]
```

**Registration logic:**

```python
def _register_verb_mapping(self, verb: str, event: str, module_name: str, tier: int):
    if verb not in self._verb_event_map:
        self._verb_event_map[verb] = []

    # Check for within-tier conflicts
    for existing_tier, existing_event, existing_module in self._verb_event_map[verb]:
        if existing_tier == tier and existing_event != event:
            raise ValueError(
                f"Vocabulary conflict: '{verb}' maps to '{existing_event}' in {existing_module} "
                f"and '{event}' in {module_name} (both tier {tier})"
            )

    # Add to list, will be sorted by tier later
    self._verb_event_map[verb].append((tier, event, module_name))
```

**Conflict resolution rules:**
- Cross-tier, same verb → different event: **ALLOW** (store both, try in tier order)
- Cross-tier, same verb → same event: **ALLOW** (deduplicate)
- Within-tier, same verb → different event: **ERROR** (library design conflict)
- Different verbs: **ALWAYS ALLOW**

### Event Delegation (Automatic)

**Changes to StateAccessor.update():**

```python
def update(self, entity, changes: dict, verb: str = None, actor_id: str = "player"):
    if verb and self.behavior_manager:
        # Get ALL events for this verb (in tier order)
        events = self.behavior_manager.get_events_for_verb(verb)

        behavior_message = None
        for tier, event_name, module_name in events:
            context = {"actor_id": actor_id, "changes": changes, "verb": verb}

            # Try this event
            result = self.behavior_manager.invoke_behavior(
                entity, event_name, self, context
            )

            # Continue to next event if:
            # - No result (entity doesn't have this behavior)
            # - Result is None (behavior not applicable)
            # - Result.allow is False (behavior rejected)
            if result is None:
                continue
            if not result.allow:
                continue

            # Success! Use this result
            behavior_message = result.message
            break

        # If all events rejected, deny the update
        if behavior_message is None and events:
            return UpdateResult(success=False, message="That action is not allowed.")

    # Apply changes...
    return UpdateResult(success=True, message=behavior_message)
```

**Fallthrough conditions:**
- Entity doesn't have behavior module for that event
- Behavior returns `None` (not applicable to this entity)
- Behavior returns `EventResult(allow=False)`

### Handler Delegation (Explicit)

**Changes to BehaviorManager:**

```python
# OLD:
self._handlers: Dict[str, List[tuple]] = {}  # verb -> [(handler, module), ...]

# NEW:
self._handlers: Dict[str, List[tuple]] = {}  # verb -> [(handler, module, tier), ...]
```

**Handler registration:**

```python
def _register_handler(self, verb: str, handler: Callable, module_name: str, tier: int):
    if verb not in self._handlers:
        self._handlers[verb] = []

    # Check for within-tier conflicts
    for existing_handler, existing_module, existing_tier in self._handlers[verb]:
        if existing_tier == tier:
            raise ValueError(
                f"Handler conflict: '{verb}' already defined in tier {tier} "
                f"by {existing_module}, cannot add from {module_name}"
            )

    # Add to list (will be sorted by tier)
    self._handlers[verb].append((handler, module_name, tier))

def load_modules(self, module_info: List[tuple]):
    # Load all modules first
    for module_path, tier in module_info:
        self.load_module(module_path, tier)

    # Sort handlers by (tier, module_name) for deterministic ordering
    for verb in self._handlers:
        self._handlers[verb].sort(key=lambda x: (x[2], x[1]))  # (tier, module_name)
```

**Delegation method:**

```python
def invoke_deeper_handler(self, verb: str, accessor, action: Dict[str, Any]):
    """Invoke next handler in deeper tier."""
    handlers = self._handlers.get(verb)
    if not handlers:
        return None

    # Get current position
    current_pos = self._handler_position_list[-1]
    current_tier = handlers[current_pos][2]

    # Find next handler in deeper tier
    for i in range(current_pos + 1, len(handlers)):
        handler, module_name, tier = handlers[i]
        if tier > current_tier:
            # Found deeper tier handler
            self._handler_position_list.append(i)
            try:
                return handler(accessor, action)
            finally:
                self._handler_position_list.pop()

    # No deeper handler found
    return None
```

**API rename:**
- `invoke_previous_handler()` → `invoke_deeper_handler()`
- `accessor.invoke_previous_handler()` → `accessor.invoke_deeper_handler()`

### Summary of Changes

**BehaviorManager** ([src/behavior_manager.py](src/behavior_manager.py)):
- Change `_verb_event_map` to store lists of (tier, event, module)
- Change `_handlers` tuples to include tier
- Update `discover_modules()` to calculate tier from directory depth
- Rewrite `_register_verb_mapping()` for tier-based conflict detection
- Update `_register_handler()` for tier-based conflict detection
- Sort handlers by (tier, module_name) after loading
- Rename `invoke_previous_handler()` → `invoke_deeper_handler()`
- Add `get_events_for_verb()` returning list of (tier, event, module)

**StateAccessor** ([src/state_accessor.py](src/state_accessor.py)):
- Rewrite `update()` to try multiple events in tier order
- Rename `invoke_previous_handler()` → `invoke_deeper_handler()`

**No changes required:**
- Existing behavior modules
- Game state files
- Vocabulary files

## Implementation Progress

### Phase 1: Tier Calculation and Storage ✓ COMPLETE

**Implementation:**
- Added `_calculate_tier(behavior_file_path, base_behavior_dir)` method to BehaviorManager
- Changed `_verb_event_map` from `Dict[str, str]` to `Dict[str, List[Tuple[int, str]]]`
- Updated `discover_modules()` to return 3-tuple: `(module_path, source_type, tier)`
- Updated `load_modules()` with backward compatibility for 2-tuple format
- Added `get_events_for_verb()` returning `List[Tuple[int, str]]` sorted by tier
- Updated `get_event_for_verb()` for backward compatibility (returns highest precedence event)

**Testing:**
- 11 new tests covering tier calculation and storage
- All tests passing
- Backward compatibility verified

**Issues Resolved:**
- Within-tier conflict detection working correctly
- Cross-tier vocabulary coexistence working
- Duplicate prevention working

### Phase 2: Event Delegation in StateAccessor ✓ COMPLETE

**Implementation:**
- Updated `StateAccessor.update()` to handle multi-tier event lists
- Automatic delegation logic:
  - Try events in tier order (lowest tier number = highest precedence)
  - If tier returns `allow=True` → stop, use that result
  - If tier returns `allow=False` → continue to next tier
  - If tier returns `None` → continue to next tier (fallthrough)
  - If all tiers deny → update fails with last tier's message

**Testing:**
- 6 new unit tests covering all delegation scenarios
- All tests passing
- Full test suite: 1203 tests, 1192 passing (10 expected wx GUI failures)

**Issues Resolved:**
- UnboundLocalError fixed with `last_deny` flag
- Backward compatibility with single-event systems maintained

## Deferred Work

(To be populated during remaining implementation)
