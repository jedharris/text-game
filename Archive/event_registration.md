# Event Type Registry Design

## Goals and Use Cases

### Goals
1. **Discoverability**: Provide a single source of truth for what events exist in the system
2. **Validation**: Enable validation that behaviors reference real events
3. **Extensibility**: Allow new modules to add event types without core changes
4. **Remove Hardcoding**: Eliminate literal event names from core engine code
5. **Documentation**: Support optional event descriptions for authors
6. **Fail Fast**: Catch author errors at load time, not during gameplay

### Use Cases
1. Author queries available events when writing behaviors: `behavior_manager.get_registered_events()`
2. Validation at load time: error if module defines `on_*` function without registered event
3. Debugging: see which modules contribute which events
4. Future tooling: generate documentation, provide IDE autocomplete

## Current State Analysis

### What Works Well

The `BehaviorManager` already has sophisticated vocabulary/event registration:

1. **Verb-to-Event Mapping**: Modules declare vocabulary with event bindings:
   ```python
   vocabulary = {
       "verbs": [
           {"word": "take", "event": "on_take", "synonyms": ["get", "grab"]}
       ]
   }
   ```

2. **Tier-Based Storage**: Events stored as `verb -> [(tier, event_name)]` with conflict detection

3. **Module Tracking**: `_modules` dict stores loaded modules, `_verb_tier_sources` tracks provenance

### The Gap

Knowledge of events is **implicit and scattered**:
- In vocabulary entries: `"event": "on_damage"`
- In behavior functions: `def on_damage(entity, accessor, context)`
- **No central registry** of available events
- **No query API** for "what events exist?"
- **No validation** that referenced events have implementations

### Hardcoded Event Names Found

The following locations have literal event names that should be removed:

1. **`src/llm_protocol.py:234`**: `"on_drop"` fallback for put command
2. **`utilities/utils.py:190`**: `"on_observe"` for visibility checks
3. **`behaviors/core/exits.py:148`**: `"on_enter"` for location entry

These represent events that are:
- Not triggered by player verbs (no vocabulary entry)
- Called programmatically by the engine

## Design Decisions

### Decision 1: Two Categories of Events

**Events have two distinct sources:**

1. **Verb-triggered events**: Registered via vocabulary (`"event": "on_take"`)
   - Already discovered during vocabulary registration
   - Tied to player commands

2. **Internal events**: Called programmatically by engine/handlers
   - `on_observe` - visibility checks
   - `on_enter` - entering a location
   - `on_drop` (as fallback for `on_put`)
   - Future: `on_damage`, `on_death`, `on_condition_change`

**Decision**: Internal events MUST be registered explicitly by modules via a dedicated mechanism. No hardcoded event names in core engine code.

**Rationale**:
- Maintains the principle that modules define all game-specific knowledge
- Makes internal events discoverable alongside verb-triggered events
- Enables validation that engine code only references registered events

### Decision 2: Event Registration Mechanism

**Option A: Vocabulary-only (extend existing)**
```python
vocabulary = {
    "verbs": [...],
    "events": [  # New section
        {"event": "on_observe", "description": "Called to check entity visibility"},
        {"event": "on_enter", "description": "Called when actor enters location"}
    ]
}
```

**Option B: Separate registry dict**
```python
registered_events = {
    "on_observe": {"description": "Called to check entity visibility"},
    "on_enter": {"description": "Called when actor enters location"}
}
```

**Option C: Function decorator**
```python
@event_handler("on_observe", description="Called to check entity visibility")
def on_observe(entity, accessor, context):
    ...
```

**Decision**: Option A (extend vocabulary) with Option C as optional enhancement.

**Rationale**:
- Option A maintains consistency with existing vocabulary pattern
- Keeps all module declarations in one place
- Decorators (Option C) could be added later for documentation/validation
- Avoids adding yet another module-level dict

### Decision 3: Event Fallbacks

**Problem**: The `on_put` event currently falls back to `on_drop` if no `on_put` handler exists. This is hardcoded in `llm_protocol.py`.

**Solution**: Declare fallbacks as event metadata in vocabulary:

```python
vocabulary = {
    "verbs": [
        {
            "word": "put",
            "event": "on_put",
            "fallback_event": "on_drop",  # Try this if on_put has no handler
            "synonyms": ["set"],
            ...
        }
    ]
}
```

**Behavior**:
1. When invoking entity behavior for `on_put`, check if entity responds
2. If no response and `fallback_event` is defined, try `on_drop`
3. If still no response, action proceeds without behavior modification

This moves the fallback relationship into vocabulary where it belongs.

### Decision 4: Engine Hooks for Internal Events

**Problem**: Engine code needs to invoke events like `on_enter` and `on_observe` that aren't triggered by player verbs. How does it reference them without hardcoding?

**Solution**: Modules register events with a `hook` name that the engine looks up:

```python
# behaviors/core/exits.py
vocabulary = {
    "events": [
        {
            "event": "on_enter",
            "hook": "location_entered",  # Engine looks up by this name
            "description": "Called when actor enters location"
        }
    ]
}

# behaviors/core/perception.py
vocabulary = {
    "events": [
        {
            "event": "on_observe",
            "hook": "visibility_check",
            "description": "Called to check if entity is visible"
        }
    ]
}
```

**Engine usage**:
```python
# Instead of hardcoded "on_enter"
event = behavior_manager.get_event_for_hook("location_entered")
if event:
    behavior_manager.invoke_behavior(destination, event, accessor, context)
```

**Hook semantics**:
- If no module provides a hook, the engine operation proceeds without invoking any event
- This is appropriate for optional behaviors (visibility, entry effects)
- Required hooks (if any) would error at load time

**Benefits**:
- Engine code never contains literal event names
- Modules define which events serve which engine purposes
- Different games could wire up different events to the same hooks
- Hooks are discoverable via `behavior_manager.get_hooks()`

### Decision 5: Conflict Detection for Events and Hooks

**Event conflicts** are simpler than verb conflicts because events are just identifiers:

| Scenario | Behavior |
|----------|----------|
| Same event registered by multiple modules | **ALLOW** - track all sources |
| Same event, different descriptions | **ALLOW** - keep first description |
| `on_*` function in module without registered event | **ERROR** at load time |

**Hook conflicts** follow the same tier-based precedence as verbs:

| Scenario | Behavior |
|----------|----------|
| Same hook, same event, multiple modules | **ALLOW** - redundant but harmless |
| Same hook, different events, same tier | **ERROR** - design conflict |
| Same hook, different events, different tiers | **ALLOW** - higher precedence (lower tier) wins |

**Examples:**

```python
# Scenario: Game overrides core event for a hook
# behaviors/core/exits.py (library, tier 2)
vocabulary = {"events": [{"event": "on_enter", "hook": "location_entered"}]}

# behaviors/my_game.py (game-specific, tier 1)
vocabulary = {"events": [{"event": "on_enter_with_fanfare", "hook": "location_entered"}]}

# Result: Tier 1 wins, hook maps to "on_enter_with_fanfare"
```

```python
# Scenario: Two libraries at same tier claim same hook
# behaviors/lib_a/movement.py (tier 2)
vocabulary = {"events": [{"event": "on_enter", "hook": "location_entered"}]}

# behaviors/lib_b/teleport.py (tier 2)
vocabulary = {"events": [{"event": "on_teleport_arrive", "hook": "location_entered"}]}

# Result: ERROR - same tier, different events for same hook
```

**Rationale**:
- Event registration: Multiple modules can handle the same event (entity behaviors)
- Hook registration: Only one event can be wired to a hook (engine contract)
- Tier precedence: Games can override library hooks, consistent with verb behavior
- `on_*` without registration is likely a typo or misunderstanding

### Decision 6: Cancellation vs. Error Semantics

**Current `EventResult` structure:**
```python
@dataclass
class EventResult:
    allow: bool
    message: Optional[str] = None
```

**Analysis of current usage:**

1. **`allow=False`**: Used for both:
   - Intentional cancellation ("The sword is cursed and refuses to be picked up!")
   - Error conditions ("No player found.")

2. **`allow=True`**: Action proceeds, optional message is additive

**Question**: Do we need to distinguish cancellation from error?

**Decision**: No additional metadata needed at this time.

**Rationale**:
- Current usage shows `allow=False` with a message is always displayed to the user
- The message content distinguishes the nature (curse vs. error)
- Adding `is_error` or `error_type` would require updating all existing behaviors
- If needed later, can be added backward-compatibly

**Future consideration**: If we need structured error handling, we could add:
```python
@dataclass
class EventResult:
    allow: bool
    message: Optional[str] = None
    reason: Optional[str] = None  # "cancelled", "error", "blocked"
```

### Decision 7: Handler Identification and `on_*` Prefix Protection

**Current pattern**: `on_*` naming convention for entity behavior handlers.

**Problem**: Authors might accidentally use `on_*` prefix for non-event functions, leading to confusion or silent failures.

**Solution**: Validate at load time that all `on_*` functions in loaded modules correspond to registered events.

```python
def validate_on_prefix_usage(behavior_manager) -> None:
    """
    Ensure all on_* functions correspond to registered events.

    Raises ValueError if any on_* function is not a registered event.
    """
    registered = set(behavior_manager.get_registered_events())

    for module_name, module in behavior_manager._modules.items():
        for name in dir(module):
            if name.startswith("on_") and callable(getattr(module, name)):
                if name not in registered:
                    raise ValueError(
                        f"Module '{module_name}' defines '{name}' but this event "
                        f"is not registered. Either register the event in vocabulary "
                        f"or rename the function to not use 'on_' prefix."
                    )
```

**This catches**:
- Typos: `on_tke` instead of `on_take`
- Misunderstanding: Using `on_` for non-event helper functions
- Missing event registration: Forgot to add event to vocabulary

**This is a load-time error**, not a warning. Fail fast.

### Decision 8: Engine Access to Event Names

**Problem**: How does the engine reference events like `on_enter` without hardcoding?

**Decision**: Use the hook mechanism from Decision 4. Engine code uses well-known hook names, modules wire up events to those hooks.

**Engine uses hook names (not event names)**:
```python
# behaviors/core/exits.py after movement
event = behavior_manager.get_event_for_hook("location_entered")
if event:
    behavior_manager.invoke_behavior(destination, event, accessor, context)

# utilities/utils.py for visibility
event = behavior_manager.get_event_for_hook("visibility_check")
if event:
    result = behavior_manager.invoke_behavior(entity, event, accessor, context)
```

**Hook names are engine constants** (not event names):
```python
# src/hooks.py
"""Well-known hook names used by the engine."""

LOCATION_ENTERED = "location_entered"
VISIBILITY_CHECK = "visibility_check"
```

**Rationale**:
- Hook names are stable engine contracts
- Event names are module implementation details
- Modules can change event names without breaking engine
- Different games could wire different events to same hooks

## Implementation Design

### EventInfo Dataclass

```python
@dataclass
class EventInfo:
    """Metadata about a registered event type."""
    event_name: str                    # e.g., "on_damage"
    registered_by: List[str]           # Module names that register this event
    description: Optional[str] = None  # Optional documentation
    hook: Optional[str] = None         # Engine hook name, if any
```

### Hook Constants

```python
# src/hooks.py
"""
Well-known hook names used by the engine.

Hooks are stable engine contracts. Modules wire events to hooks.
Engine code uses hook names, never event names directly.
"""

LOCATION_ENTERED = "location_entered"
VISIBILITY_CHECK = "visibility_check"
```

### BehaviorManager Changes

```python
class BehaviorManager:
    def __init__(self):
        # ... existing fields ...
        self._event_registry: Dict[str, EventInfo] = {}  # event_name -> EventInfo
        self._hook_to_event: Dict[str, tuple] = {}  # hook_name -> (event_name, tier)
        self._fallback_events: Dict[str, str] = {}  # event_name -> fallback_event_name

    def _register_vocabulary(self, vocabulary: dict, module_name: str, tier: int) -> None:
        """Register vocabulary from a module."""
        # ... existing verb registration ...

        # Register events from verb mappings (including fallbacks)
        for verb_spec in vocabulary.get("verbs", []):
            if event := verb_spec.get("event"):
                self._register_event(event, module_name, tier)
                # Register fallback relationship
                if fallback := verb_spec.get("fallback_event"):
                    self._fallback_events[event] = fallback

        # Register explicit events (with optional hooks)
        for event_spec in vocabulary.get("events", []):
            event_name = event_spec["event"]
            self._register_event(
                event_name,
                module_name,
                tier,
                description=event_spec.get("description"),
                hook=event_spec.get("hook")
            )

    def _register_event(
        self,
        event_name: str,
        module_name: str,
        tier: int,
        description: Optional[str] = None,
        hook: Optional[str] = None
    ) -> None:
        """Register an event in the registry."""
        if event_name not in self._event_registry:
            self._event_registry[event_name] = EventInfo(
                event_name=event_name,
                registered_by=[module_name],
                description=description,
                hook=hook
            )
        else:
            info = self._event_registry[event_name]
            if module_name not in info.registered_by:
                info.registered_by.append(module_name)
            # First description wins
            if description and not info.description:
                info.description = description

        # Register hook mapping with tier-based precedence
        if hook:
            if hook in self._hook_to_event:
                existing_event, existing_tier = self._hook_to_event[hook]
                if existing_event != event_name:
                    if existing_tier == tier:
                        # Same tier, different events = conflict
                        raise ValueError(
                            f"Hook '{hook}' conflict at tier {tier}: "
                            f"already mapped to '{existing_event}', "
                            f"cannot also map to '{event_name}'"
                        )
                    elif tier < existing_tier:
                        # New registration has higher precedence (lower tier)
                        self._hook_to_event[hook] = (event_name, tier)
                    # else: existing has higher precedence, keep it
            else:
                self._hook_to_event[hook] = (event_name, tier)

    # Query API
    def get_registered_events(self) -> List[str]:
        """Return list of all registered event names."""
        return list(self._event_registry.keys())

    def get_event_info(self, event_name: str) -> Optional[EventInfo]:
        """Get metadata for a registered event."""
        return self._event_registry.get(event_name)

    def has_event(self, event_name: str) -> bool:
        """Check if an event is registered."""
        return event_name in self._event_registry

    def get_event_for_hook(self, hook_name: str) -> Optional[str]:
        """Get event name for an engine hook. Returns None if hook not registered."""
        entry = self._hook_to_event.get(hook_name)
        return entry[0] if entry else None

    def get_fallback_event(self, event_name: str) -> Optional[str]:
        """Get fallback event for an event. Returns None if no fallback."""
        return self._fallback_events.get(event_name)

    def get_hooks(self) -> List[str]:
        """Return list of all registered hook names."""
        return list(self._hook_to_event.keys())
```

### Validation (Required at Load Time)

```python
def validate_on_prefix_usage(behavior_manager) -> None:
    """
    Ensure all on_* functions correspond to registered events.

    Called after all modules are loaded. Raises ValueError on first error.
    """
    registered = set(behavior_manager.get_registered_events())

    for module_name, module in behavior_manager._modules.items():
        for name in dir(module):
            if name.startswith("on_") and callable(getattr(module, name)):
                if name not in registered:
                    raise ValueError(
                        f"Module '{module_name}' defines '{name}' but this event "
                        f"is not registered. Either:\n"
                        f"  1. Add to vocabulary: {{'events': [{{'event': '{name}'}}]}}\n"
                        f"  2. Rename the function to not use 'on_' prefix"
                    )
```

### Module Vocabulary Examples

```python
# behaviors/core/exits.py
vocabulary = {
    "verbs": [
        {"word": "go", "event": "on_go", ...},
    ],
    "events": [
        {
            "event": "on_enter",
            "hook": "location_entered",
            "description": "Called when an actor enters a location. "
                          "Context includes actor_id and from_direction."
        }
    ]
}

# behaviors/core/perception.py
vocabulary = {
    "verbs": [...],
    "events": [
        {
            "event": "on_observe",
            "hook": "visibility_check",
            "description": "Called to check if entity is visible. "
                          "Return allow=False to hide entity."
        }
    ]
}

# behaviors/core/manipulation.py
vocabulary = {
    "verbs": [
        {
            "word": "put",
            "event": "on_put",
            "fallback_event": "on_drop",  # Use on_drop if entity has no on_put
            "synonyms": ["set"],
            ...
        },
        {
            "word": "drop",
            "event": "on_drop",
            ...
        }
    ]
}
```

### Engine Code Updates

```python
# behaviors/core/exits.py - after movement
from src.hooks import LOCATION_ENTERED

event = accessor.behavior_manager.get_event_for_hook(LOCATION_ENTERED)
if event:
    behavior_result = accessor.behavior_manager.invoke_behavior(
        destination, event, accessor, context
    )

# utilities/utils.py - visibility check
from src.hooks import VISIBILITY_CHECK

event = behavior_manager.get_event_for_hook(VISIBILITY_CHECK)
if event and hasattr(entity, 'behaviors') and entity.behaviors:
    result = behavior_manager.invoke_behavior(entity, event, accessor, context)

# src/llm_protocol.py - remove hardcoded fallback
# The fallback is now handled in invoke_behavior via get_fallback_event()
```

### Updated invoke_behavior with Fallback Support

```python
def invoke_behavior(
    self,
    entity: Any,
    event_name: str,
    accessor: Any,
    context: Dict[str, Any]
) -> Optional[EventResult]:
    """
    Invoke entity behaviors for an event, with fallback support.

    If no behavior responds to event_name and a fallback is registered,
    tries the fallback event.
    """
    # Try primary event
    result = self._invoke_behavior_internal(entity, event_name, accessor, context)

    # If no result and fallback exists, try fallback
    if result is None:
        fallback = self.get_fallback_event(event_name)
        if fallback:
            result = self._invoke_behavior_internal(entity, fallback, accessor, context)

    return result
```

## Migration Path

### Phase 1: Add Event Registry Infrastructure
1. Add `EventInfo` dataclass to `behavior_manager.py`
2. Add `_event_registry`, `_hook_to_event`, `_fallback_events` to `BehaviorManager`
3. Update `_register_vocabulary` to:
   - Populate registry from verb events
   - Handle `fallback_event` in verb specs
   - Handle new `events` vocabulary section with hooks
4. Add query methods: `get_registered_events()`, `get_event_info()`, `has_event()`, `get_event_for_hook()`, `get_fallback_event()`, `get_hooks()`
5. Create `src/hooks.py` with hook constants

### Phase 2: Register Internal Events in Modules
1. Add `events` section to `behaviors/core/exits.py` with `on_enter` hook
2. Add `events` section to `behaviors/core/perception.py` with `on_observe` hook
3. Add `fallback_event: "on_drop"` to `put` verb in `behaviors/core/manipulation.py`

### Phase 3: Update Engine Code to Use Hooks
1. Update `behaviors/core/exits.py` to use `get_event_for_hook(LOCATION_ENTERED)`
2. Update `utilities/utils.py` to use `get_event_for_hook(VISIBILITY_CHECK)`
3. Remove hardcoded `on_drop` fallback from `src/llm_protocol.py`
4. Update `invoke_behavior` to support fallbacks

### Phase 4: Add Load-Time Validation
1. Add `validate_on_prefix_usage()` function
2. Call it after all modules are loaded in `GameEngine` initialization
3. Ensure it raises `ValueError` on first error (fail fast)

### Phase 5: Test and Verify
1. Write tests for event registry population
2. Write tests for hook lookup
3. Write tests for fallback behavior
4. Write tests for `on_*` validation (should catch typos/missing registrations)
5. Verify existing tests still pass

## Summary

This design:
- Extends the existing vocabulary pattern naturally
- Maintains backward compatibility during migration
- Removes all hardcoded event names from engine code
- Provides discoverability for authors via registry queries
- Uses hooks as stable engine contracts, decoupled from event names
- Supports event fallbacks as vocabulary metadata
- Fails fast on author errors (`on_*` without registration)
- Enables future validation and tooling

Key concepts:
- **Events**: Names like `on_take`, `on_enter` - registered in vocabulary
- **Hooks**: Engine contracts like `location_entered`, `visibility_check` - stable across games
- **Fallbacks**: Declared in vocabulary, transparent to callers
