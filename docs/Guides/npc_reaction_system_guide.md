# NPC Reaction System Guide

**Purpose:** Complete guide for testing, debugging, and fixing NPCs using the reaction system.

**Status:** Active (Phase 6 of issue #408)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [All 9 Reaction Types](#all-9-reaction-types)
3. [Fix Recipe: Step-by-Step](#fix-recipe-step-by-step)
4. [Debugging Workflow](#debugging-workflow)
5. [Walkthrough Discipline](#walkthrough-discipline)
6. [Common Mistakes](#common-mistakes)

---

## Architecture Overview

### Three-Layer Architecture: Commands → Hooks → Reactions

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: COMMANDS (behavior_libraries/command_lib/)        │
│ ─────────────────────────────────────────────────────────── │
│ Purpose: Define game verbs, parse user input, fire hooks   │
│ Examples: dialog.py, combat.py, item_use.py                │
│ Rules:                                                      │
│   ✓ Defines vocabulary with verbs                          │
│   ✓ Fires hooks on target entities                         │
│   ✓ Returns HandlerResult to engine                        │
│   ✗ NO entity property access                              │
│   ✗ NO business logic                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: HOOKS (engine infrastructure)                     │
│ ─────────────────────────────────────────────────────────── │
│ Purpose: Dispatch events to entity-specific behaviors      │
│ Mechanism: invoke_behavior(entity, "on_dialog", context)   │
│ Complexity: O(1) - only target entity's behaviors invoked  │
│ Rules:                                                      │
│   ✓ Checks entity.behaviors list for modules               │
│   ✓ Calls event handlers (on_dialog, on_combat, etc.)      │
│   ✗ Never invokes extra.behaviors for entity events        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: REACTIONS (game/behaviors/shared/infrastructure/) │
│ ─────────────────────────────────────────────────────────── │
│ Purpose: Subscribe to hooks, execute entity-specific logic │
│ Examples: dialog_reactions.py, combat_reactions.py         │
│ Rules:                                                      │
│   ✓ Subscribes via vocabulary.events                       │
│   ✓ Checks entity.properties for config                    │
│   ✓ Calls custom handlers or unified interpreter           │
│   ✓ Returns EventResult to command                         │
│   ✗ NO command parsing                                     │
└─────────────────────────────────────────────────────────────┘
```

### Why Three Layers?

**Separation of Concerns:**
- Commands know about user input, NOT game logic
- Reactions know about game logic, NOT user input
- Hooks connect them without coupling

**Performance:**
- Entity-specific events use entity.behaviors (O(1))
- Only the target entity processes the event
- Global events use extra.behaviors (O(n), only for turn phases)

**Extensibility:**
- Add new commands without touching NPCs
- Add new NPCs without touching commands
- Each layer can evolve independently

### entity.behaviors vs extra.behaviors

**CRITICAL DISTINCTION:**

**entity.behaviors** (e.g., `maren.behaviors`):
```json
{
  "actors": {
    "herbalist_maren": {
      "behaviors": [
        "behaviors.shared.infrastructure.dialog_reactions",  // ✓ CORRECT
        "behaviors.regions.civilized_remnants.services"
      ]
    }
  }
}
```
- Events: `entity_dialog`, `entity_combat`, `entity_item_use`, `entity_take`, etc.
- Invoked: When `invoke_behavior(entity, event)` called with `entity != None`
- Complexity: **O(1)** - only target entity's behaviors invoked
- Use for: Entity-specific reactions

**extra.behaviors** (`game_state.extra.behaviors`):
```json
{
  "extra": {
    "behaviors": [
      "behaviors.shared.infrastructure.scheduled_events",   // ✓ CORRECT
      "behaviors.shared.infrastructure.gossip",
      "behaviors.regions.frozen_reaches.hypothermia"
    ]
  }
}
```
- Events: `turn_start`, `turn_end`, `turn_tick`, `gossip_spread`, etc.
- Invoked: When `invoke_behavior(None, event)` called with `entity=None`
- Complexity: **O(n)** - invoked once per turn, affects all relevant entities
- Use for: Global systems, turn phases, cross-entity effects

**Common Mistake:**
```json
// ❌ WRONG - dialog_reactions in extra.behaviors causes O(n) scaling!
{
  "extra": {
    "behaviors": [
      "behaviors.shared.infrastructure.dialog_reactions"
    ]
  }
}
```

This would invoke dialog_reactions for EVERY entity on EVERY event, even when not talking to anyone!

---

## All 9 Reaction Types

Complete table of reaction types with infrastructure modules and usage:

| Reaction Type | Property Key | Infrastructure Module | Hook Name | Event Name | Triggered By |
|---------------|--------------|----------------------|-----------|------------|--------------|
| **commitment_reactions** | `commitment_reactions` | `behaviors.shared.infrastructure.commitment_reactions` | `commitment_change` | `on_commitment_change` | Player makes/breaks promises |
| **condition_reactions** | `condition_reactions` | `behaviors.shared.infrastructure.condition_reactions` | `condition_added` | `on_condition_added` | Status effects applied |
| **death_reactions** | `death_reactions` | `behaviors.shared.infrastructure.death_reactions` | `entity_death` | `on_death` | Entity dies |
| **dialog_reactions** | `dialog_reactions` | `behaviors.shared.infrastructure.dialog_reactions` | `entity_dialog` | `on_dialog` | ask/talk commands |
| **encounter_reactions** | `encounter_reactions` | `behaviors.shared.infrastructure.encounter_reactions` | `entity_encounter` | `on_encounter` | First meeting with entity |
| **gift_reactions** | `gift_reactions` | `behaviors.shared.infrastructure.gift_reactions` | `entity_gift` | `on_gift` | give command |
| **gossip_reactions** | `gossip_reactions` | `behaviors.shared.infrastructure.gossip_reactions` | `gossip_received` | `on_gossip` | News spreads to entity |
| **item_use_reactions** | `item_use_reactions` | `behaviors.shared.infrastructure.item_use_reactions` | `entity_item_use` | `on_item_use` | use X on Y commands |
| **take_reactions** | `take_reactions` | `behaviors.shared.infrastructure.take_reactions` | `entity_take` | `on_take` | take command |

### Configuration Patterns

**Handler-Based (Custom Logic):**
```json
{
  "properties": {
    "dialog_reactions": {
      "handler": "examples.big_game.behaviors.regions.civilized_remnants.services:on_service_request"
    }
  }
}
```

**Data-Driven (Unified Interpreter):**
```json
{
  "properties": {
    "gift_reactions": {
      "reactions": {
        "honey": {
          "conditions": [{"type": "trust_threshold", "threshold": 2}],
          "effects": [
            {"type": "trust_change", "amount": 1},
            {"type": "message", "text": "The Queen accepts your offering graciously."}
          ]
        }
      },
      "default_response": "The Queen does not seem interested."
    }
  }
}
```

**Hybrid (Handler + Data):**
```json
{
  "properties": {
    "dialog_reactions": {
      "handler": "path:to:handler",
      "reactions": {
        "trade": {"effects": [{"type": "message", "text": "Default trade response"}]}
      }
    }
  }
}
```

---

## Fix Recipe: Step-by-Step

### Problem Pattern

NPC has `X_reactions` config in properties but doesn't respond to commands.

**Root Cause:** Missing infrastructure module in `entity.behaviors`.

### Solution Steps

**Step 1: Identify Reaction Type**

Check NPC's properties in `game_state.json`:
```json
{
  "id": "herbalist_maren",
  "properties": {
    "dialog_reactions": { ... }  // ← Found it!
  }
}
```

**Step 2: Look Up Infrastructure Module**

From table above: `dialog_reactions` → `behaviors.shared.infrastructure.dialog_reactions`

**Step 3: Add to entity.behaviors**

```json
{
  "id": "herbalist_maren",
  "behaviors": [
    "behaviors.shared.infrastructure.dialog_reactions",  // ← Add this!
    "behaviors.regions.civilized_remnants.services"      // Existing handler module
  ],
  "properties": {
    "dialog_reactions": {
      "handler": "examples.big_game.behaviors.regions.civilized_remnants.services:on_service_request"
    }
  }
}
```

**Step 4: Verify Handler Exists**

If config has `"handler": "path:to:function"`, verify:
- File exists at path
- Function exists with signature: `def func(entity, accessor, context) -> EventResult`
- Function is in module scope (not nested)

**Step 5: Create Walkthrough Test**

Create `walkthroughs/test_<npc_name>.txt`:
```
# Test herbalist_maren dialog
go market square
look
ask maren about trade
@expect "shows you her wares"
ask maren about help
@expect "I can brew healing potions"
```

**Step 6: Add Required Items/Setup**

If walkthrough needs items not in game_state.json:
- Add them to appropriate location/inventory in game_state.json
- Use existing items as templates for structure
- Prefer simple items for testing (complexity can be added later)
- If no obvious location exists, create issue to track proper placement

Example: Testing gift reactions needs giftable items, combat needs weapons, etc.

**Step 7: Run Walkthrough**

```bash
python tools/walkthrough.py examples/big_game --file walkthroughs/test_herbalist_maren.txt
```

**Step 7: Fix Until 100% Success**

All commands must behave as expected (including `# EXPECT_FAIL` commands).

**Step 8: Document Omitted Tests**

If you simplified testing by omitting complex mechanics:
- **REQUIRED:** Add comment to issue #423 describing what was omitted and why
- Include: what needs testing, why it was hard, suggested approach for follow-up
- **Everything must eventually be tested** - #423 tracks deferred work

Example omissions: death scenarios, dynamic spawning, state machine flows.

---

### Example: Complete Fix for herbalist_maren

**Before (broken):**
```json
{
  "id": "herbalist_maren",
  "behaviors": [
    "behaviors.regions.civilized_remnants.services"
  ],
  "properties": {
    "dialog_reactions": {
      "handler": "examples.big_game.behaviors.regions.civilized_remnants.services:on_service_request"
    }
  }
}
```

**After (working):**
```json
{
  "id": "herbalist_maren",
  "behaviors": [
    "behaviors.shared.infrastructure.dialog_reactions",  // ← Added!
    "behaviors.regions.civilized_remnants.services"
  ],
  "properties": {
    "dialog_reactions": {
      "handler": "examples.big_game.behaviors.regions.civilized_remnants.services:on_service_request"
    }
  }
}
```

**Result:** `ask maren about trade` now works!

---

## Debugging Workflow

### Step 1: Identify Failure Type

**Symptom → Likely Cause:**
- "I don't understand that" → Parser failure (missing vocabulary)
- "Maren doesn't respond" → Missing infrastructure module
- "AttributeError: 'NoneType'" → Handler not found or wrong signature
- "Command works sometimes" → Race condition or state-dependent logic

### Step 2: Enable Debug Checks

**Check infrastructure loaded:**
```python
# In Python console
from src.game_state_loader import load_game_state
state = load_game_state('examples/big_game')
npc = state.actors.get('herbalist_maren')
print(npc.behaviors)
# Should see: ['behaviors.shared.infrastructure.dialog_reactions', ...]
```

**Check handler exists:**
```python
from src.behavior_manager import BehaviorManager
mgr = BehaviorManager()
# Try to load the handler path
handler_path = "examples.big_game.behaviors.regions.civilized_remnants.services:on_service_request"
# Parse path
module_path, func_name = handler_path.rsplit(":", 1)
import importlib
module = importlib.import_module(module_path)
handler = getattr(module, func_name)
print(f"Handler found: {handler}")
```

**Check hook fired:**
Add temporary debug print to command handler:
```python
# In behavior_libraries/command_lib/dialog.py
result = accessor.behavior_manager.invoke_behavior(
    npc, "entity_dialog", accessor, context
)
print(f"DEBUG: invoke_behavior returned: {result}")  # ← Add this
```

### Step 3: Check Each Layer

**Layer 1 - Command:**
- Does command have vocabulary defining the verb?
- Does command fire the correct hook?
- Is hook name correct? (`entity_dialog` not `on_dialog`)

**Layer 2 - Hook Dispatch:**
- Is infrastructure module in entity.behaviors?
- Is module path spelled correctly?
- Does vocabulary.events subscribe to correct hook?

**Layer 3 - Reaction:**
- Does event name match hook? (`on_dialog` for `entity_dialog`)
- Does entity have the property? (`dialog_reactions`)
- Does handler path point to existing function?
- Does handler have correct signature?

### Step 4: Verify Infrastructure Completeness

Before assuming data-driven patterns work, verify the underlying infrastructure:

**Check property names used by effects:**
```bash
# Find all condition property access in reaction effects
grep -n "properties\[" behaviors/shared/infrastructure/reaction_effects.py

# Common issue: Old code may use "active_conditions" but all NPCs use "conditions"
# Verify NPCs use consistent property names:
grep -r "\"conditions\"" examples/big_game/game_state.json | wc -l
grep -r "\"active_conditions\"" examples/big_game/game_state.json | wc -l
# First should be > 0, second should be 0
```

**Verify effect handlers fire hooks:**
```python
# Check if remove_condition effect fires entity_condition_change hook
# In behaviors/shared/infrastructure/reaction_effects.py
def _remove_condition(config, state, entity, context):
    # After removing condition, should fire hook:
    accessor.behavior_manager.invoke_behavior(
        entity, "entity_condition_change", accessor,
        {**context, "condition_type": condition_type, "change": "removed"}
    )
```

**Trace complete hook invocation chain:**
```
1. Command fires hook (e.g., item_use.py calls entity_item_use)
2. Engine checks target.behaviors for infrastructure modules
3. Infrastructure module's vocabulary.events subscribes to hook
4. Event handler (e.g., on_item_use) processes entity.properties config
5. Data-driven: Unified interpreter applies effects (remove_condition)
6. Effect handler manipulates state AND fires condition_change hook
7. condition_reactions handler receives notification, updates flags
```

If ANY step is missing, data-driven pattern won't work. Verify each layer.

### Step 5: Common Issues Checklist

- [ ] Infrastructure module in `extra.behaviors` instead of `entity.behaviors`
- [ ] Hook name vs event name mismatch (`entity_dialog` vs `on_dialog`)
- [ ] Handler path typo or wrong module
- [ ] Handler function signature wrong (missing `context` arg)
- [ ] Property name typo (`dialog_reaction` vs `dialog_reactions`)
- [ ] Property name mismatch (effect uses `active_conditions`, NPCs use `conditions`)
- [ ] Effect handler incomplete (removes condition but doesn't fire hook)
- [ ] Module path doesn't match symlink structure
- [ ] Function not in module scope (nested in class or function)
- [ ] Assumed data-driven pattern works without verifying infrastructure

---

## Walkthrough Discipline

### NEVER Ship Without 100% Success

**Rule:** Work is NOT complete until walkthrough shows 100% expected behavior.

**"Expected behavior" includes:**
- Commands that should succeed → succeed
- Commands that should fail → fail (marked with `# EXPECT_FAIL`)
- Assertions pass (`@assert`)
- Output matches expectations (`@expect`)

### Creating Effective Walkthroughs

**Structure:**
```
# Test <feature_name> - <npc_name>
# Purpose: Verify all dialog options work correctly

# Setup - Navigate to NPC
go market square
look

# Happy path - Normal interactions
ask maren about trade
@expect "shows you her wares"

ask maren about herbs
@expect "healing moss"

# Edge cases - Should fail gracefully
ask maren about nonsense  # EXPECT_FAIL
@expect "doesn't seem to understand"

# State changes - Verify effects
@assert player.properties.talked_to_maren == true

# Cleanup - Return to known state
go north
```

**Best Practices:**
1. **Document intent** - Comments explain what you're testing
2. **Test happy paths** - Normal usage should work
3. **Test edge cases** - Invalid input should fail gracefully
4. **Use assertions** - Verify state changes
5. **Use @expect** - Verify output quality
6. **Mark expected failures** - `# EXPECT_FAIL` for blocked actions

### Running Walkthroughs

**During development:**
```bash
# Run with stop-on-error for quick debugging
python tools/walkthrough.py examples/big_game --file test.txt --stop-on-error
```

**Before committing:**
```bash
# Run full walkthrough, check all results
python tools/walkthrough.py examples/big_game --file test.txt

# Check exit code (0 = success)
echo $?
```

**Paste results in issue:**
```
### Walkthrough Results

python tools/walkthrough.py examples/big_game --file walkthroughs/test_herbalist_maren.txt

Summary: 8/8 commands succeeded
No unexpected failures
Exit code: 0

✅ All tests pass, ready to close issue.
```

---

## Common Mistakes

### Mistake 1: Infrastructure in extra.behaviors

**Symptom:** NPC doesn't respond, no errors.

**Wrong:**
```json
{
  "extra": {
    "behaviors": [
      "behaviors.shared.infrastructure.dialog_reactions"  // ❌
    ]
  }
}
```

**Right:**
```json
{
  "actors": {
    "herbalist_maren": {
      "behaviors": [
        "behaviors.shared.infrastructure.dialog_reactions"  // ✓
      ]
    }
  }
}
```

**Why:** Entity-specific events MUST use entity.behaviors for O(1) dispatch.

### Mistake 2: Hook Name vs Event Name Confusion

**Symptom:** Module loaded but event handler never called.

**Wrong (in command handler):**
```python
# ❌ Invoking event name instead of hook name
result = accessor.behavior_manager.invoke_behavior(
    npc, "on_dialog", accessor, context
)
```

**Right (in command handler):**
```python
# ✓ Invoke hook name (engine dispatches to event handlers)
result = accessor.behavior_manager.invoke_behavior(
    npc, "entity_dialog", accessor, context
)
```

**Wrong (in infrastructure vocabulary):**
```python
# ❌ Event name doesn't match hook
vocabulary = {
    "events": [
        {"event": "handle_dialog", "hook": "entity_dialog"}  // Wrong event name
    ]
}
```

**Right (in infrastructure vocabulary):**
```python
# ✓ Event name follows convention: on_<action>
vocabulary = {
    "events": [
        {"event": "on_dialog", "hook": "entity_dialog"}  // Correct!
    ]
}
```

### Mistake 3: Handler Path Errors

**Symptom:** `AttributeError: module has no attribute 'func'` or similar.

**Common errors:**
```json
// ❌ Missing colon separator
"handler": "path.to.module.func_name"

// ❌ Wrong module path (doesn't match file structure)
"handler": "behaviors.services:handler"
// Should be: "examples.big_game.behaviors.regions.civilized_remnants.services:handler"

// ❌ Function doesn't exist
"handler": "correct.path:typo_in_name"

// ❌ Function is nested (not in module scope)
class NPC:
    def on_dialog(self, ...):  # ← Can't reference this!
        ...
```

**Fix:** Verify path matches actual file location and function name exactly.

### Mistake 4: Claiming Complete Without Walkthrough

**Wrong workflow:**
```
1. Write code
2. Manually test "looks good"
3. Close issue ❌
```

**Right workflow:**
```
1. Write code
2. Write walkthrough
3. Run walkthrough → failures found
4. Fix failures
5. Run walkthrough → 100% success
6. Paste results in issue
7. Close issue ✓
```

**Why:** Manual testing misses edge cases. Walkthroughs are repeatable and comprehensive.

### Mistake 5: Testing Only dialog_reactions

**Symptom:** Dialog works, but other reaction types (gift, combat, etc.) untested.

**Incomplete:**
```
# Only tests dialog
ask maren about trade
ask maren about help
```

**Complete:**
```
# Tests dialog
ask maren about trade

# Tests gift_reactions (if NPC accepts gifts)
give honey to bee queen
@expect "accepts your offering"

# Tests item_use_reactions (if NPC can be targeted)
use healing moss on elara
@expect "grateful"

# Tests all applicable reaction types for this NPC
```

**Fix:** For each NPC, test ALL reaction types they have configured.

### Mistake 6: Property Name Mismatches

**Symptom:** Data-driven config looks correct but "Nothing special happens."

**Root Cause:** Effect handler uses different property name than NPCs.

**Example from Issue #437:**
```python
# In reaction_effects.py - WRONG
def _remove_condition(config, state, entity, context):
    active = entity.properties.get("active_conditions", {})  # ❌
    del active[condition_type]

# All NPCs in game_state.json use "conditions" not "active_conditions"
{
  "hunter_sira": {
    "properties": {
      "conditions": {"bleeding": {...}}  // ✓ This is what NPCs use
    }
  }
}
```

**Fix:** Inventory actual property usage across all NPCs, update effect handlers to match:
```bash
# Find what property name NPCs actually use
grep -r "\"conditions\"" examples/big_game/game_state.json
grep -r "\"active_conditions\"" examples/big_game/game_state.json

# Update effect handler to use correct name
def _remove_condition(config, state, entity, context):
    conditions = entity.properties.get("conditions", {})  # ✓ Matches NPCs
```

### Mistake 7: Incomplete Effect Implementations

**Symptom:** Condition removed but condition_reactions handler never fires.

**Root Cause:** Effect handler manipulates state but doesn't fire notification hook.

**Wrong (before Issue #437 fix):**
```python
def _remove_condition(config, state, entity, context):
    conditions = entity.properties.get("conditions", {})
    del conditions[condition_type]
    # ❌ Effect complete but nothing notified condition_reactions!
```

**Right (after fix):**
```python
def _remove_condition(config, state, entity, context):
    conditions = entity.properties.get("conditions", {})
    del conditions[condition_type]

    # ✓ Fire hook so condition_reactions can respond
    from src.state_accessor import StateAccessor
    accessor = StateAccessor(state, state.behavior_manager)
    accessor.behavior_manager.invoke_behavior(
        entity, "entity_condition_change", accessor,
        {**context, "condition_type": condition_type, "change": "removed"}
    )
```

**Why This Matters:** Data-driven architecture often chains reactions:
1. `item_use_reactions` → `remove_condition` effect
2. Effect fires → `entity_condition_change` hook
3. Hook triggers → `condition_reactions` handler tracks success

If step 2 is missing, step 3 never happens.

### Mistake 8: Assuming Data-Driven Patterns Are Complete

**Symptom:** Config matches architecture doc perfectly but doesn't work.

**Root Cause:** Architecture doc describes *intended* design, not *current* implementation.

**Wrong Assumption:**
```json
// "This matches the spec, so it must work"
{
  "item_use_reactions": {
    "heal": {
      "accepted_items": ["bandages"],
      "remove_condition": "bleeding"  // Spec says this should work!
    }
  }
}
```

**Reality Check:**
```python
# Check if effect is actually implemented
grep -n "remove_condition" behaviors/shared/infrastructure/reaction_effects.py
# Does it exist? Does it use correct property names? Does it fire hooks?

# Check if hook is actually fired
grep -rn "entity_condition_change" behaviors/ examples/
# Is hook invoked anywhere? Or just defined but never called?
```

**Fix:** Before using data-driven patterns, verify:
1. Effect handler exists and is registered in EFFECT_REGISTRY
2. Effect uses correct property names (matches NPCs in game_state.json)
3. Effect fires appropriate hooks for downstream reactions
4. Hook is actually invoked somewhere (not just defined in vocabulary)

**Debugging Workflow:**
```
1. Config looks right but doesn't work
2. Trace each layer of architecture (Commands → Hooks → Reactions)
3. Find missing piece (property mismatch, hook not fired, etc.)
4. Fix infrastructure, THEN retry config
5. Document the gap so next person doesn't assume it works
```

---

## Quick Reference: Fix Checklist

For each broken NPC:

- [ ] Identify reaction type from `properties` (e.g., `dialog_reactions`)
- [ ] Look up infrastructure module from table (e.g., `behaviors.shared.infrastructure.dialog_reactions`)
- [ ] Add infrastructure to `entity.behaviors` (NOT `extra.behaviors`)
- [ ] Verify handler exists if config has `handler` key
- [ ] Create walkthrough file
- [ ] Run walkthrough
- [ ] Fix all failures until 100% success
- [ ] Paste walkthrough results in issue
- [ ] Close issue ONLY after 100% success

---

## Minimal NPC Set for Testing

To verify all 9 reaction types work before declaring architecture complete:

1. **hunter_sira** - 4 types: death, dialog, encounter, item_use
2. **bee_queen** - 3 types: dialog, gift, take
3. **camp_leader_mira** - 2 types: commitment, dialog
4. **merchant_delvan** - 3 types: condition, death, encounter
5. **healer_elara** - 2 types: dialog, gossip

**Coverage:** All 9 reaction types tested with minimal NPCs (5 instead of 18).

Once these 5 NPCs work correctly, the recipe is proven and can be applied to remaining NPCs.

---

## Related Documentation

- **Architecture Spec:** [reaction_system_complete_architecture.md](reaction_system_complete_architecture.md)
- **Session Guide:** [../Guides/claude_session_guide.md](../Guides/claude_session_guide.md)
- **Authoring Guide:** [../Guides/authoring_guide.md](../Guides/authoring_guide.md)
- **Issue #408:** Complete migration to unified reaction system

---

## Critical Lessons: Commitment System

### Legacy vs. Entity Architecture

**Problem Pattern:** Two commitment systems existed:
1. **Commitment entities** (`state.commitments`) - First-class entity system ✓
2. **ActiveCommitment dicts** (`state.extra["active_commitments"]`) - Legacy dict system ✗

Turn phase iterated entities but handlers created dicts → handlers never fired.

**Solution:** Eliminate all legacy code, use Commitment entities only.

**Creating Commitments:**
```python
from src.state_manager import Commitment
from src.types import CommitmentId  # NOT src.infrastructure_types!
from src.infrastructure_types import CommitmentState, TurnNumber

commitment = Commitment(
    id=CommitmentId("commit_mira_rescue"),
    name="Rescue Trapped Survivors",
    description="Save survivors before time runs out",
    behaviors=["behaviors.shared.infrastructure.commitments"]  # Use behaviors.* path
)
commitment.properties["state"] = CommitmentState.ACTIVE
commitment.properties["target_actor"] = "camp_leader_mira"
commitment.properties["made_at_turn"] = current_turn
commitment.properties["deadline_turn"] = TurnNumber(current_turn + 20)

state.commitments.append(commitment)
```

**Critical Details:**
- Use `behaviors.shared.*` paths, NOT `examples.big_game.behaviors.*`
- Import CommitmentId from `src.types`, NOT `src.infrastructure_types`
- Clear `__pycache__` if changes don't take effect (Python caching issue)

---

## Session Progress Log

### 2026-01-09: Issue #427 - Comprehensive Testing (Phases 1-4)

**Completed:**
- ✅ Phase 1 (hunter_sira): death_reactions - Fixed encounter/death hook invocations
- ✅ Phase 2 (merchant_delvan): condition_reactions + death_reactions
- ✅ Phase 3 (healer_elara): gossip_reactions - Fixed gossip delivery system (Bug #6)
- ✅ Phase 4 (camp_leader_mira): commitment_reactions - Fixed legacy commitment system (Bug #8)

**Infrastructure Fixes:**
1. encounter_reactions hook now fires in utilities/utils.py:describe_location()
2. death_reactions hook now fires in combat.py:on_death()
3. gossip_delivery.py turn phase created and added to global behaviors
4. Exit system documented in claude_session_guide.md (connections field)
5. **Commitment system migrated from dicts to entities** (Issue #432)

**Bugs Resolved:**
- ✅ Bug #7: Gossip handler duplicate invocation (function name collision) - FIXED
  - Problem: Both services.py and gossip_reactions.py had on_gossip_received()
  - Solution: Renamed services handler to handle_gossip_for_services()
  - Result: Trust penalties now correct (-2 not -4), message appears once

**Next:** Phase 5 (bee_queen) - navigation and item setup needed

---

**Last Updated:** 2026-01-09 (Issue #427 - Phases 1-4 complete, Bug #7 fixed)
