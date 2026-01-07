# Complete Migration to Unified Property-Based Reaction System

**Issue:** #408
**Date:** 2026-01-07
**Updated:** 2026-01-07 (aligned with reaction_system_complete_architecture.md)
**Architecture Spec:** [docs/big_game_work/reaction_system_complete_architecture.md](reaction_system_complete_architecture.md)
**Goal:** Clean, complete migration from mixed vocabulary/property systems to pure property-based reactions

---

## Current State Problems

1. **Two Dialog Systems:**
   - OLD: `behavior_libraries/dialog_lib/` (vocabulary-based, looks for `dialog_topics`)
   - NEW: `dialog_reactions` infrastructure (property-based, listens for `entity_dialog` hook)
   - Result: 9 NPCs unreachable, hook never fired

2. **Mixed Architecture:**
   - Reaction infrastructure in game-specific `examples/big_game/behaviors/shared/infrastructure/`
   - Should be in `behavior_libraries/` (general-purpose)

3. **Incomplete Cleanup:**
   - Old systems not deleted after new systems added
   - NPCs split between old and new
   - No validation old systems replaced

4. **No Command Handlers:**
   - Nothing fires the entity_dialog hook
   - Dialog reactions infrastructure unreachable

---

## Target Architecture (Three Layers)

See [reaction_system_complete_architecture.md](reaction_system_complete_architecture.md) for complete specification.

**Layer 1: COMMANDS** (behavior_libraries/command_lib/)
- Define game verbs (ask, talk, attack, use, etc.)
- Parse user input, validate basic requirements
- Fire appropriate hooks with context
- NEVER look at entity properties
- NEVER contain game logic

**Layer 2: HOOKS** (engine infrastructure)
- Broadcast events to all registered behaviors
- Already implemented in behavior_manager

**Layer 3: REACTIONS** (game-specific infrastructure)
- Subscribe to hooks in vocabulary
- Check entity properties for reaction configs
- Delegate to unified interpreter OR custom handlers
- Return EventResult to hook system

**Directory Structure:**

```
behavior_libraries/
├── reaction_lib/              # LAYER 3 CORE (general-purpose)
│   ├── interpreter.py         # Unified interpreter
│   ├── effects.py             # Effect handlers registry
│   ├── conditions.py          # Condition checkers registry
│   ├── specs.py               # ReactionSpec definitions
│   ├── match_strategies.py   # Matching logic
│   ├── message_templates.py  # Template substitution
│   └── dispatcher_utils.py   # Handler loading/caching
│
├── command_lib/               # LAYER 1 (general-purpose)
│   ├── dialog.py              # ask/talk → entity_dialog hook
│   ├── combat.py              # attack → entity_combat hook
│   ├── treatment.py           # treat → entity_treatment hook
│   └── item_use.py            # use → entity_item_use hook
│
└── [other libs]               # companion_lib, puzzle_lib, etc.

examples/big_game/behaviors/shared/infrastructure/
├── gift_reactions.py          # LAYER 3 (game-specific)
├── dialog_reactions.py        # Hook → interpreter wiring
├── item_use_reactions.py
├── encounter_reactions.py
├── death_reactions.py
├── combat_reactions.py
├── entry_reactions.py
├── commitment_reactions.py
├── take_reactions.py
├── examine_reactions.py
├── trade_reactions.py
└── turn_environmental.py

examples/big_game/behaviors/regions/
└── [region handlers]          # Pure functions, NO vocabulary
```

**Critical Rules:**
1. ONLY command_lib modules have vocabulary with verbs
2. Reaction infrastructure has vocabulary with hook_definitions/events ONLY
3. Region/behavior modules have ZERO vocabulary (pure functions)
4. Commands NEVER access entity properties
5. Reactions ALWAYS use invoke_behavior() for handlers

---

## Implementation Plan

**CRITICAL:** Follow architecture specification exactly. Delete old systems FIRST.

### Phase 0: Delete Old Systems (MANDATORY FIRST STEP - 0.5 day)

**Must complete BEFORE any other work.**

**Tasks:**

1. **Audit vocabulary-based command systems:**
   ```bash
   # Find all verbs in behavior_libraries (excluding command_lib if it exists)
   grep -r '"verbs"' behavior_libraries/ | grep -v command_lib
   ```

2. **Delete old dialog system:**
   ```bash
   rm -rf behavior_libraries/dialog_lib
   ```

3. **Delete unused systems:**
   ```bash
   # Check usage first
   grep -r "crafting_lib" examples/big_game/
   # If no results:
   rm -rf behavior_libraries/crafting_lib

   grep -r "offering_lib" examples/big_game/
   # If no results:
   rm -rf behavior_libraries/offering_lib
   ```

4. **Audit actor_lib for vocabulary:**
   ```bash
   grep -r '"verbs"' behavior_libraries/actor_lib/
   # Document what verbs exist, plan migration to command_lib
   ```

5. **Verify deletion:**
   ```bash
   # MUST return zero results
   grep -r "dialog_topics" examples/big_game/game_state.json
   grep -r "from.*dialog_lib" examples/big_game/
   grep -r "behavior_libraries.dialog_lib" examples/big_game/
   ```

**Deliverables:**
- [ ] behavior_libraries/dialog_lib deleted
- [ ] Unused libraries deleted (crafting_lib, offering_lib if unused)
- [ ] List of verbs in actor_lib that need migration
- [ ] Zero grep hits for old systems
- [ ] Commit: "Phase 0: Delete old vocabulary-based command systems"

**DO NOT PROCEED to Phase 1 until all Phase 0 tasks complete.**

---

### Phase 1: Audit NPCs and Handlers (0.5 day)

**After Phase 0 deletion, inventory what needs creation/migration.**

**Tasks:**

1. **List all NPCs with dialog:**
   ```python
   # Check which NPCs have ANY dialog configuration
   import json
   with open('examples/big_game/game_state.json') as f:
       state = json.load(f)

   for actor_id, actor in state['actors'].items():
       if 'dialog_reactions' in actor.get('properties', {}):
           print(f"{actor_id}: has dialog_reactions")
       # Should be ZERO results for dialog_topics after Phase 0
   ```

2. **Audit existing handlers:**
   ```bash
   # Find all handler references in dialog_reactions
   grep -r '"handler":' examples/big_game/game_state.json | grep dialog_reactions
   ```

3. **Verify handler signatures:**
   For each handler found, check:
   - Exists at specified path
   - Has signature: `(entity, accessor, context) -> EventResult`
   - Returns EventResult with allow/feedback

4. **Document missing handlers:**
   List NPCs with dialog_reactions but no handler yet

**Deliverables:**
- [ ] List of all NPCs with dialog_reactions (should be 11)
- [ ] List of existing handlers with file locations
- [ ] List of handlers that need creation
- [ ] Verification: zero NPCs with dialog_topics

---

### Phase 2: Create Command Infrastructure (1 day)

**Follow architecture specification templates exactly.**

**2.1: Create behavior_libraries/command_lib/ directory (0.1 day)**

```bash
mkdir -p behavior_libraries/command_lib
touch behavior_libraries/command_lib/__init__.py
```

**2.2: Create command_lib/dialog.py (0.4 day)**

Use template from [reaction_system_complete_architecture.md](reaction_system_complete_architecture.md#layer-1-command-handlers).

**Critical requirements:**
- Define ask/talk verbs in vocabulary
- NEVER access entity properties
- Fire entity_dialog hook with context: `{"keyword": str, "dialog_text": str, "speaker": actor_id}`
- Return HandlerResult with serialized NPC data
- If no EventResult from hook, return default "not interested" message

**2.3: Create command_lib/item_use.py (0.3 day)**

Use architecture template for "use X on Y" command.

**Requirements:**
- Define use verb with object and indirect_object
- Fire entity_item_use hook with context: `{"item": item, "target": target}`
- NEVER access item/target properties

**2.4: Migrate combat/treatment verbs from actor_lib (0.2 day)**

If actor_lib has vocabulary with verbs:
- Extract verb definitions to command_lib/combat.py or command_lib/treatment.py
- Keep ONLY hook-firing logic
- Remove all property access from commands

**Deliverables:**
- [ ] behavior_libraries/command_lib/dialog.py created
- [ ] behavior_libraries/command_lib/item_use.py created
- [ ] combat/treatment verbs migrated to command_lib if needed
- [ ] All commands fire hooks, zero property access
- [ ] Commit: "Phase 2: Create command infrastructure"

---

### Phase 3: Create Reaction Infrastructure (0.5 day)

**Verify reaction infrastructure modules exist and follow spec.**

**Tasks:**

1. **Audit existing infrastructure:**
   ```bash
   ls examples/big_game/behaviors/shared/infrastructure/
   ```

2. **Verify each module follows architecture:**
   - Has vocabulary with hook_definitions and events
   - Subscribes to correct hook
   - Checks entity properties for reaction config
   - Delegates to handler OR unified interpreter
   - Returns EventResult

3. **Create missing infrastructure if needed:**
   - If item_use_reactions doesn't exist, create using architecture template
   - If turn_environmental doesn't exist, create using architecture template

4. **Update dialog_reactions.py:**
   - Verify it listens for entity_dialog hook
   - Verify it checks dialog_reactions property
   - Add default reject message if no handler

**Deliverables:**
- [ ] All 12 reaction infrastructure modules exist
- [ ] All follow architecture specification
- [ ] dialog_reactions verified to work with command_lib/dialog.py
- [ ] Commit: "Phase 3: Verify reaction infrastructure"

---

### Phase 4: Integration Testing (0.5 day)

**Test end-to-end flow: command → hook → reaction → response**

**Tasks:**

1. **Update global behaviors in game_state.json:**
   ```json
   "extra": {
     "behaviors": [
       "behavior_libraries.command_lib.dialog",
       "examples.big_game.behaviors.shared.infrastructure.dialog_reactions",
       ...other behaviors
     ]
   }
   ```

2. **Create minimal integration test walkthrough:**
   ```
   # walkthroughs/integration_test_dialog.txt
   # Test: command → hook → reaction flow

   # Setup
   @set player.location = herbalist_shop

   # Test 1: Talk to Maren fires hook
   talk to maren
   @expect "Maren"

   # Test 2: Ask Maren about topic fires hook with keyword
   ask maren about trade
   @expect "trade" OR "wares" OR "silvermoss"
   ```

3. **Run integration test:**
   ```bash
   python tools/walkthrough.py examples/big_game --file walkthroughs/integration_test_dialog.txt
   ```

4. **Debug if fails:**
   - Verify command_lib/dialog.py loaded
   - Verify dialog_reactions.py loaded
   - Verify entity_dialog hook registered
   - Add debug logging to trace hook firing

**Deliverables:**
- [ ] Global behaviors updated
- [ ] Integration test walkthrough created
- [ ] Integration test passes
- [ ] End-to-end flow verified: ask maren about trade → response
- [ ] Commit: "Phase 4: Integration testing passes"

---

### Phase 5: Verify All NPCs (0.5 day)

**After Phase 0, all NPCs should already use dialog_reactions. Verify configuration.**

**Tasks:**

1. **Verify all 11 NPCs with dialog:**
   - herbalist_maren
   - apothecary_elara
   - weaponsmith_toran
   - curiosity_dealer_vex
   - sailor_garrett
   - merchant_delvan
   - the_echo
   - salamander
   - And any others from Phase 1 audit

2. **For each NPC, verify:**
   ```bash
   # Check handler path exists
   python -c "
   import importlib
   module_path, func = 'examples.big_game.behaviors.regions.X:handler'.split(':')
   mod = importlib.import_module(module_path)
   handler = getattr(mod, func)
   print(f'✓ {func} exists')
   "
   ```

3. **Verify handler signatures:**
   - Parameters: (entity, accessor, context)
   - Returns: EventResult
   - Accesses context["keyword"] for topic matching

4. **Create missing handlers if needed:**
   - Follow architecture template
   - Use EventResult with allow/feedback
   - Check keyword in context for topic matching

**Deliverables:**
- [ ] All NPCs verified to have dialog_reactions property
- [ ] All handlers exist and accessible
- [ ] All handler signatures correct
- [ ] Missing handlers created
- [ ] Commit: "Phase 5: All NPC dialog handlers verified"

---

### Phase 6: Smoke Test Migration (0.5 day)

**Run minimal smoke tests to verify migration architecture works. Full testing is issue #406.**

**6.1: Run critical dialog walkthroughs (0.3 day)**

Test representative NPCs to verify command → hook → reaction flow:
```bash
# Test vendor dialog (Maren)
python tools/walkthrough.py examples/big_game --file walkthroughs/test_herbalist_maren.txt

# Test creature dialog (Echo or Salamander)
python tools/walkthrough.py examples/big_game --file walkthroughs/test_echo_dialog.txt

# Test quest-giver dialog (Sira or Camp Leader)
python tools/walkthrough.py examples/big_game --file walkthroughs/test_sira_rescue.txt
```

**6.2: Debug critical failures only (0.2 day)**

If smoke tests fail:
- Verify architecture violation (commands accessing properties, etc.)
- Check hook firing
- Fix architecture issues ONLY
- Re-run smoke tests

**Note:** Do NOT attempt to fix all bugs or make all walkthroughs pass. That's issue #406's scope (56 walkthroughs, estimated 3-5 days).

**Deliverables:**
- [ ] 3 representative dialog walkthroughs pass
- [ ] Architecture verified working (commands → hooks → reactions)
- [ ] No architecture violations detected
- [ ] Commit: "Phase 6: Smoke tests passing, migration complete"
- [ ] **Close #408, unblock #406**

---

## Success Criteria Checklist

**From Architecture Specification:**

### Phase 0 (Delete)
- [ ] behavior_libraries/dialog_lib deleted
- [ ] behavior_libraries/crafting_lib deleted (if unused)
- [ ] behavior_libraries/offering_lib deleted (if unused)
- [ ] Zero grep hits for "dialog_topics" in game_state.json
- [ ] Zero grep hits for "dialog_lib" in codebase

### Phase 2 (Commands)
- [ ] behavior_libraries/command_lib/dialog.py created
- [ ] behavior_libraries/command_lib/item_use.py created
- [ ] Commands fire hooks only, zero property access
- [ ] Commands return HandlerResult with serialized data

### Phase 3 (Reactions)
- [ ] dialog_reactions.py listens for entity_dialog hook
- [ ] item_use_reactions.py listens for entity_item_use hook
- [ ] All reaction modules follow architecture template

### Phase 4 (Integration)
- [ ] Global behaviors include command_lib.dialog
- [ ] Integration test passes: ask maren about trade → response
- [ ] Hook firing verified with logging

### Phase 5 (NPCs)
- [ ] All NPCs use dialog_reactions (not dialog_topics)
- [ ] All handlers exist and accessible
- [ ] All handlers have correct signature: (entity, accessor, context) -> EventResult

### Phase 6 (Smoke Testing)
- [ ] 3 representative dialog walkthroughs pass
- [ ] No architecture violations
- [ ] Migration verified functional (full testing in #406)

### Architecture Compliance
- [ ] ONLY command_lib has vocabulary with verbs
- [ ] Reaction infrastructure has vocabulary with hooks only
- [ ] Region behaviors have ZERO vocabulary
- [ ] Commands NEVER access entity properties
- [ ] Reactions ALWAYS use invoke_behavior() for handlers
- [ ] Clean three-layer separation: Commands → Hooks → Reactions

---

## Estimated Effort

| Phase | Days | Description |
|-------|------|-------------|
| 0. Delete Old Systems | 0.5 | Delete dialog_lib, verify zero refs |
| 1. Audit NPCs/Handlers | 0.5 | Inventory NPCs, verify handlers |
| 2. Create Commands | 1.0 | command_lib/dialog.py, item_use.py |
| 3. Verify Reactions | 0.5 | Audit infrastructure modules |
| 4. Integration Test | 0.5 | End-to-end command→hook→reaction |
| 5. Verify NPCs | 0.5 | Check all handlers exist/correct |
| 6. Smoke Testing | 0.5 | 3 critical walkthroughs, unblock #406 |
| **Total** | **4.0 days** | Complete clean migration |

**Note:** Full walkthrough testing (56 tests) is issue #406, estimated 3-5 additional days.

---

## What Could Have Been Done Differently?

### Issues That Led to This Mess

1. **No Deletion Step in Migration Plan**
   - Issues #392, #398, #399 added new systems but didn't DELETE old ones
   - Should have had explicit "Phase: Delete Old Systems" with checklist

2. **No Validation That Migration Was Complete**
   - No check that all NPCs migrated
   - No verification old systems unused
   - Should have had: "Zero NPCs using dialog_topics" success criterion

3. **Incremental Migration Without Cleanup**
   - New systems added alongside old
   - "We'll clean up later" approach
   - Should have been: migrate entity → delete old path → test

4. **No Architecture Documentation**
   - Unclear where things belong (game vs behavior_libraries)
   - Should have had clear diagram like above

5. **Missing Integration Testing**
   - Commands created but hook dispatch not tested
   - Should have had end-to-end test: command → hook → reaction → response

### Prevention Strategies

**For Future Migrations:**

1. **Explicit Deletion Phase**
   ```
   Phase N: DELETE OLD SYSTEMS
   - [ ] Delete old_system/
   - [ ] Grep codebase, verify zero references
   - [ ] Run tests, must pass
   ```

2. **Validation Gates**
   ```
   Before closing migration issue:
   - [ ] Run: grep -r "old_pattern" → must be 0 results
   - [ ] All entities use new system (script to verify)
   - [ ] Old directories deleted
   ```

3. **Clear Success Criteria**
   ```
   NOT: "Add new dialog system"
   YES: "All NPCs using dialog_reactions, dialog_topics deleted, dialog_lib removed"
   ```

4. **Architecture Diagram First**
   - Before starting migration, draw target state
   - Review and approve diagram
   - Migration plan must reach that target

5. **Integration Testing Required**
   - Every new infrastructure module needs walkthrough
   - Test: user command → system response
   - Not just: "module exists and loads"

6. **Regular Audits During Work**
   - After each phase: "What old code can we delete NOW?"
   - Don't accumulate cleanup debt
   - Delete as you go

**Better Workflow:**

```
Phase 1: Design target architecture
  → Review and approve diagram
Phase 2: Create new system
  → Integration test passes
Phase 3: Migrate first entity
  → Walkthrough passes
Phase 4: Migrate remaining entities
  → All walkthroughs pass
Phase 5: DELETE old system
  → Grep shows zero references
  → All tests still pass
Phase 6: Validate
  → Checklist all green
  → ONLY THEN close issue
```

The key insight: **Migration is not complete until old system is DELETED and VERIFIED gone.**
