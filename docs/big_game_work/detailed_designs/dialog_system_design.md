# Dialog System Design for big_game

## Issue Reference
GitHub Issue #231

## 1. Requirements from Walkthroughs

### 1.1 Dialog Interaction Patterns

From analyzing the walkthroughs, dialog interactions follow these patterns:

**Pattern A: Topic Discovery**
```
> talk to aldric
Aldric looks up with tired but hopeful eyes.
You could ask Aldric about: infection, research, myconids
```

**Pattern B: Ask About Topic (Simple)**
```
> ask aldric about infection
Aldric winces. "The spores got into my blood weeks ago..."
[Flag set: knows_aldric_needs_silvermoss = true]
[Aldric trust +1]
```

**Pattern C: Ask About Topic (Gated)**
```
> ask aldric about spore mother
[Requires: knows_aldric_needs_silvermoss = true]
"She's not evil, you know..."
[Flag set: knows_about_heartmoss = true]
[Unlocks topic: safe_path]
```

**Pattern D: Commitment Trigger**
```
> I'll help your cubs
[COMMITMENT TRIGGER]
You speak slowly... "I'll help your cubs."
[Commitment created: bear_cubs_commitment]
```

**Pattern E: State-Dependent Responses**
NPCs respond differently based on their state (e.g., Aldric critical vs. cured, Sira injured vs. healthy).

### 1.2 Topic Capabilities Required

From the sketches, each topic can:
- Have `keywords` (list of trigger words)
- Have `summary` (response text)
- Set flags (`sets_flags`)
- Require flags (`requires_flags`)
- Grant trust bonus (`trust_bonus` or `trust_delta`)
- Unlock other topics (`unlocks_topics`)
- Be one-time only (`one_time`)
- Require items (`requires_items`)
- Grant items (`grants_items`)

### 1.3 Handler Scenarios

Handlers are needed for:
1. **Commitment creation** - When player promises to help
2. **Teaching** - When NPC teaches a skill (requires state checks, consumes time)
3. **State-dependent branching** - When response varies by NPC state
4. **Complex side effects** - Item transfers, stat changes, state machine transitions

## 2. Current Implementation Analysis

### 2.1 Data-Driven System (dialog_lib/topics.py)

The current system handles:
- `get_available_topics()` - Lists topics the player can discuss
- `get_topic_hints()` - Returns first keyword of each available topic
- `handle_ask_about()` - Processes "ask X about Y"
- `handle_talk_to()` - Lists available topics for "talk to X"

**Capabilities:**
- Flag checking (requires_flags)
- Item checking (requires_items)
- Flag setting (sets_flags)
- Item granting (grants_items)
- Topic unlocking (unlocks_topics)
- One-time tracking (one_time)

**Missing:**
- Trust modification
- Handler integration for side effects
- State-dependent responses

### 2.2 Handler System (dialog_lib/handlers.py)

The current handler mechanism:
- Top-level `handler` key in `dialog_topics` intercepts all dialog
- Handler receives `(entity, accessor, context)` where context has `keyword`
- Handler returns `EventResult(allow, feedback)`
- If feedback is None, falls through to data-driven topics

**Problem:** Handler is all-or-nothing. Either it handles everything or nothing.

## 3. Proposed Design

### 3.1 Design Principle

Keep the keyword-based data-driven system as the primary mechanism. Use handlers only for specific topics that need custom logic.

### 3.2 Topic Structure (Enhanced)

```json
{
  "dialog_topics": {
    "infection": {
      "keywords": ["infection", "sick", "illness"],
      "summary": "Aldric winces...",
      "sets_flags": {"knows_aldric_needs_silvermoss": true},
      "trust_delta": 1,
      "one_time": false
    },
    "help": {
      "keywords": ["help", "save", "cure", "promise"],
      "summary": null,
      "handler": "module.path:on_commitment"
    },
    "teaching": {
      "keywords": ["teach", "learn", "mycology"],
      "summary": null,
      "handler": "module.path:on_teach",
      "requires_state": {"current": "cured"}
    }
  }
}
```

**Key changes:**
1. Remove top-level `handler` - handlers are per-topic
2. Add `trust_delta` to topic structure
3. Add `requires_state` for NPC state machine gating
4. Topics with `handler` invoke the handler; topics without use the `summary`

### 3.3 Processing Flow

**For "talk to X":**
1. Get all available topics (filtered by flags, items, state)
2. Return first keyword of each as hints
3. No handlers invoked - just listing

**For "ask X about Y":**
1. Find topic matching keyword Y
2. Check availability (flags, items, state)
3. If topic has `handler`, invoke it
4. Otherwise, return `summary` and apply effects (flags, trust, items)

### 3.4 State-Dependent Behavior

For NPCs with state machines, topics can be gated by state:

```json
{
  "teaching": {
    "keywords": ["teach", "learn"],
    "requires_state": {"current": "cured"},
    "summary": "I can teach you now that I'm better..."
  },
  "infection_plea": {
    "keywords": ["infection", "help"],
    "requires_state": {"current": "critical"},
    "summary": "Please... the silvermoss..."
  }
}
```

The same keyword can appear in multiple topics with different state requirements. The first matching topic (by state) wins.

### 3.5 Handler Protocol

Handlers receive:
```python
def on_topic_handler(entity, accessor, context) -> EventResult:
    """
    Args:
        entity: The NPC being spoken to
        accessor: StateAccessor instance
        context: {
            "keyword": str,       # The keyword that triggered this
            "topic_name": str,    # The topic name from config
            "dialog_text": str    # Full player input
        }

    Returns:
        EventResult(allow=True, feedback="Response text")
        # feedback=None means "use topic summary instead"
    """
```

## 4. Migration Plan

### 4.1 Aldric (Example)

**Current (broken):**
```json
{
  "dialog_topics": {
    "handler": "...aldric_rescue:on_aldric_commitment",
    "help": {...},
    "teaching": {...},
    "infection": {...}
  }
}
```

**Proposed (fixed):**
```json
{
  "dialog_topics": {
    "infection": {
      "keywords": ["infection", "sick", "help"],
      "summary": "Aldric winces. 'The spores got into my blood...'",
      "sets_flags": {"knows_aldric_needs_silvermoss": true},
      "trust_delta": 1
    },
    "research": {
      "keywords": ["research", "study", "mycology"],
      "summary": "His eyes light up despite his illness...",
      "trust_delta": 1
    },
    "help_commitment": {
      "keywords": ["promise", "save you", "help you", "cure you"],
      "handler": "...aldric_rescue:on_aldric_commitment",
      "requires_state": {"current": "critical"}
    },
    "teaching": {
      "keywords": ["teach", "learn"],
      "handler": "...aldric_rescue:on_aldric_teach",
      "requires_state": {"current": ["cured", "stabilized"]}
    }
  }
}
```

### 4.2 Implementation Steps

1. Add `trust_delta` handling to `handle_ask_about()`
2. Add `requires_state` checking to `get_available_topics()`
3. Add per-topic `handler` invocation to `handle_ask_about()`
4. Remove support for top-level `handler` (deprecated)
5. Update Aldric's config in game_state.json
6. Update other NPCs as needed

## 5. Interactions Not Handled

### 5.1 Commitment Triggers from Free Text

The walkthroughs show commitments triggered by player statements like:
```
> I'll help your cubs
```

This is NOT an "ask about" command. Options:
1. **Ignore** - Require "ask bear about help" instead
2. **LLM extraction** - Have narrator extract intent and map to "ask about help"
3. **Pattern matching** - Match "I'll help" / "I promise" against commitment keywords

**Recommendation:** Use option 2 (LLM extraction). The narrator already processes player input; it can recognize commitment language and generate the appropriate command. This keeps the engine simple.

### 5.2 State Machine Transitions from Dialog

Some dialogs should transition NPC state (e.g., Aldric from "critical" to "hopeful" when player promises help).

**Recommendation:** Handlers can modify state. Add a simple pattern:
```python
# In handler
aldric.properties["state_machine"]["current"] = "hopeful"
```

### 5.3 Complex Multi-Turn Dialogs

The spec mentioned branching dialog trees with explicit choices. The walkthroughs don't use these - all dialogs are single-exchange "ask about X" patterns.

**Recommendation:** Don't implement branching dialog trees. The keyword system is sufficient for all walkthrough scenarios.

## 6. Summary

The dialog system needs modest enhancements:
1. Per-topic handlers (instead of top-level)
2. `trust_delta` in topic effects
3. `requires_state` for state-machine gating

This keeps the keyword-based simplicity while supporting all the interactions shown in the walkthroughs.

Commitment triggers from free text should be handled by the LLM narrator extracting player intent, not by adding complexity to the dialog system.

## 7. Implementation Plan (TDD)

### 7.1 Phases

**Phase 1: Tests for `requires_state`**
- Write tests for state-machine gating in `get_available_topics()`
- Implement `requires_state` checking
- Verify tests pass

**Phase 2: Tests for `trust_delta`**
- Write tests for trust modification in `handle_ask_about()`
- Implement `trust_delta` handling
- Verify tests pass

**Phase 3: Tests for per-topic handlers**
- Write tests for per-topic `handler` invocation
- Implement handler loading and invocation in `handle_ask_about()`
- Update handlers.py to work with new structure
- Verify tests pass

**Phase 4: Game State Updates + Integration Tests**
- Update Aldric's `dialog_topics` to use new structure
- Update Echo's `dialog_topics`
- Run integration tests with text_game
- Verify commitment triggers still work

### 7.2 Text Game Testing for Player Intent

For commitment triggers like "I'll help your cubs", the text game parser doesn't understand free text. Two options:

**Option A: Add "promise" verb to vocabulary**
```
> promise to help aldric
```
This maps to a topic with keywords ["promise", "help", "save"].

**Option B: Use "ask about" with commitment keywords**
```
> ask aldric about help
```
The topic's handler creates the commitment.

**Recommendation:** Option B - it already works with the current parser and matches the walkthrough examples ("ask aldric about infection"). Commitment keywords like "help", "save", "promise" in topics will trigger the handler.

### 7.3 Game State Changes Required

**NPCs needing dialog_topics updates:**

| NPC | Current State | Required Changes |
|-----|---------------|------------------|
| npc_aldric | Has top-level handler + partial topics | Replace with full topic structure from sketch |
| npc_echo | Has top-level handler | Add data-driven topics + keep handler for dynamic state |
| npc_spore_mother | Unknown | Check if exists, add topics from sketch |
| npc_myconid_elder | Unknown | Check if exists, add topics from sketch |

**Estimated scope:**
- Aldric: ~30 lines of JSON changes (replace existing topics)
- Echo: ~20 lines of JSON additions
- Other NPCs: Copy from sketches (already defined there)

**No schema changes needed** - the topic structure is already supported, we're just adding new optional fields (`trust_delta`, `requires_state`, per-topic `handler`).

### 7.4 Phase 1: `requires_state` (TDD)

**Tests to write first:**
```python
def test_requires_state_single_value_matches(self):
    """Topic with requires_state='critical' available when NPC in critical state."""

def test_requires_state_single_value_no_match(self):
    """Topic with requires_state='critical' hidden when NPC in 'stabilized' state."""

def test_requires_state_list_matches(self):
    """Topic with requires_state=['stabilized', 'recovering'] available in either state."""

def test_requires_state_list_no_match(self):
    """Topic with requires_state=['stabilized', 'recovering'] hidden when in 'critical'."""

def test_no_requires_state_always_available(self):
    """Topic without requires_state is available regardless of NPC state."""

def test_requires_state_no_state_machine(self):
    """Topic with requires_state hidden if NPC has no state_machine."""
```

**Implementation:**
- In `get_available_topics()`: check topic's `requires_state` against NPC's `state_machine.current`
- Support both string and list values for `requires_state`

### 7.5 Phase 2: `trust_delta` (TDD)

**Tests to write first:**
```python
def test_trust_delta_positive(self):
    """Topic with trust_delta=1 increases NPC trust by 1."""

def test_trust_delta_negative(self):
    """Topic with trust_delta=-1 decreases NPC trust by 1."""

def test_trust_delta_zero(self):
    """Topic with trust_delta=0 doesn't change trust."""

def test_no_trust_delta(self):
    """Topic without trust_delta doesn't change trust."""

def test_trust_delta_respects_ceiling(self):
    """Trust delta doesn't exceed ceiling (e.g., max 10)."""

def test_trust_delta_respects_floor(self):
    """Trust delta doesn't go below floor (e.g., min -10)."""
```

**Implementation:**
- In `handle_ask_about()`: after processing topic, apply `trust_delta`
- Use existing trust modification function if available, or add simple one

### 7.6 Phase 3: Per-topic handlers (TDD)

**Tests to write first:**
```python
def test_topic_handler_invoked(self):
    """Topic with handler key invokes the handler function."""

def test_topic_handler_feedback_returned(self):
    """Handler's feedback is returned instead of topic summary."""

def test_topic_handler_none_uses_summary(self):
    """If handler returns feedback=None, topic summary is used."""

def test_topic_handler_context_includes_topic_name(self):
    """Handler receives topic_name in context."""

def test_topic_without_handler_uses_summary(self):
    """Topic without handler returns its summary."""

def test_top_level_handler_deprecated(self):
    """Top-level handler logs deprecation warning."""
```

**Implementation:**
- In `handle_ask_about()`: if topic has `handler`, load and invoke it
- Pass `topic_name` in context
- Update handlers.py to let topics.py handle per-topic handlers

### 7.7 Phase 4: Game State Updates

1. **Update Aldric in game_state.json**
```json
"dialog_topics": {
  "infection": {
    "keywords": ["infection", "sick", "illness", "help"],
    "summary": "Aldric winces. 'The spores got into my blood weeks ago. I've been rationing the last of my silvermoss, but it only slows the progression. More grows in the Luminous Grotto below, but I can barely stand. And the air down there would finish me in minutes.'",
    "sets_flags": {"knows_aldric_needs_silvermoss": true},
    "trust_delta": 1
  },
  "research": {
    "keywords": ["research", "study", "mycology", "knowledge"],
    "summary": "His eyes light up despite his illness. 'I've spent years studying these fungi. The spores aren't just a disease - they're communication. The Spore Mother sends them to find hosts, yes, but also to connect. If I survive this, I can teach you what I know.'",
    "trust_delta": 1
  },
  "spore_mother": {
    "keywords": ["spore mother", "source", "creature", "monster"],
    "requires_flags": {"knows_aldric_needs_silvermoss": true},
    "summary": "'She's not evil, you know. She's dying too - the same blight that's killing me originated from her. She spreads spores in desperation. There's a rare moss in the Deep Root Caverns - heartmoss - that might heal her. But the air down there...'",
    "sets_flags": {"knows_about_heartmoss": true},
    "trust_delta": 1,
    "one_time": true
  },
  "help_commitment": {
    "keywords": ["promise", "save", "cure", "commitment", "help you"],
    "requires_state": ["critical"],
    "handler": "examples.big_game.behaviors.regions.fungal_depths.aldric_rescue:on_aldric_commitment"
  },
  "teaching": {
    "keywords": ["teach", "learn"],
    "requires_state": ["stabilized", "recovering"],
    "handler": "examples.big_game.behaviors.regions.fungal_depths.aldric_rescue:on_aldric_teach"
  }
}
```

2. **Update Echo** - Add data-driven topics for waystone, regions, progress

3. **Verify other NPCs** - Check if myconid_elder, spore_mother exist in game_state.json

**Integration tests (text_game):**
```bash
# Test sequence for Aldric
echo -e "west\ntalk to aldric\nask aldric about infection\nask aldric about spore mother\nask aldric about help" | python3 -m src.text_game examples/big_game
```

Expected:
1. `talk to aldric` → "You could ask Aldric about: infection, research"
2. `ask aldric about infection` → Summary + sets flag + trust +1
3. `ask aldric about spore mother` → Now available (flag set), returns summary
4. `ask aldric about help` → Triggers commitment handler

### 7.8 Estimated Effort

| Phase | Tasks | Effort |
|-------|-------|--------|
| Phase 1 | `requires_state` tests + implementation | 1.5 hours |
| Phase 2 | `trust_delta` tests + implementation | 1 hour |
| Phase 3 | Per-topic handler tests + implementation | 1.5 hours |
| Phase 4 | Game state updates + integration tests | 2 hours |
| **Total** | | **6 hours**
