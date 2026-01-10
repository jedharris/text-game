# Template NPC Completion Plan

**Purpose:** Complete all capabilities for the 5 template NPCs so they serve as full reference implementations for upgrading the remaining 37 NPCs.

**Context:** Issue #434 validated the 9 reaction types work. However, the template NPCs have additional functionality from the design sketches that hasn't been implemented. This plan addresses those gaps.

**Generated:** 2026-01-10

---

## Current State Assessment

### What's Implemented (from Issue #434)
- ✅ All 9 reaction types working (encounter, death, dialog, item_use, condition, gift, take, commitment, gossip)
- ✅ Core mechanics for each template NPC tested with walkthroughs
- ✅ Trust system infrastructure
- ✅ Trading/merchant services (behavior_libraries/actor_lib/services.py)
- ✅ Morale system for NPCs (behavior_libraries/actor_lib/morale.py)

### What's Missing Per Template NPC

| NPC | Missing Feature | Infrastructure Status |
|-----|-----------------|----------------------|
| healer_elara | Basic herbalism teaching | Needs service config |
| healer_elara | Advanced herbalism teaching | Needs two-tier skill tracking |
| healer_elara | Garden access control | Needs location permission system |
| healer_elara | Aldric rescue trust bonus | Dialog reaction only |
| camp_leader_mira | Camp services (safe rest) | Needs service handler |
| camp_leader_mira | Camp morale system | Connect existing morale to camp |
| camp_leader_mira | Jek referral dialog | Dialog reaction only |
| camp_leader_mira | Garrett recovery tracking | Flag-based dialog |
| merchant_delvan | Undercity access dialog | Dialog reaction only |
| merchant_delvan | delvan_contacts fragment | Needs knowledge fragment system |
| merchant_delvan | Post-rescue trade services | Needs rescued-state service gating |

---

## Infrastructure Analysis

### Tier 1: Dialog Reactions Only (No New Infrastructure)
These can be implemented immediately using existing dialog_reactions:

1. **Aldric rescue trust bonus** (healer_elara)
   - Handler checks `extra.aldric_saved` flag
   - Applies trust +1 if flag set
   - Adds acknowledgment dialog

2. **Jek referral dialog** (camp_leader_mira)
   - Dialog topic "swimming" triggers referral
   - Response mentions old_swimmer_jek

3. **Garrett recovery tracking** (camp_leader_mira)
   - Check turn count since rescue
   - Dialog varies based on recovery state

4. **Undercity access dialog** (merchant_delvan)
   - Post-rescue dialog topic "connections" or "black market"
   - Sets `knows_undercity_entrance` flag
   - Note: Undercity location not yet in game - dialog can set flag for future use

### Tier 2: Service System Extensions (Minor Infrastructure)
These extend the existing services.py infrastructure:

1. **Basic herbalism teaching** (healer_elara)
   - Config: `service_id: "teach_basic_herbalism"`, `requires_trust: 2`, `cost: 50g or rare_herb`
   - Effect: Add `basic_herbalism` to `player.properties.skills`
   - Handler: Extend `execute_service()` for skill granting

2. **Advanced herbalism teaching** (healer_elara)
   - Config: `requires_trust: 3`, `requires_skill: "basic_herbalism"`, `cost: 100g or rare_herb`
   - Effect: Add `advanced_herbalism` to skills
   - Handler: Check prerequisite skill before allowing service

3. **Camp safe rest service** (camp_leader_mira)
   - Config: `service_id: "safe_rest"`, `requires_state: "allied"`, `cost: none`
   - Effect: Restore player health to max
   - Handler: Simple health restoration

4. **Post-rescue trade services** (merchant_delvan)
   - Config: Add `trades` property gated by `requires_state: "rescued"`
   - Effect: Standard trade services become available
   - Handler: Existing trading.py with state check

### Tier 3: New Infrastructure Required

1. **Two-tier skill tracking**
   - Current: Skills stored in `player.properties.skills` as array
   - Needed: Check prerequisite skills before granting advanced versions
   - Implementation: Add `has_skill(player, skill_name)` utility
   - Add `requires_skill` to service config schema

2. **Garden access control** (location permissions)
   - Current: No hard-blocking of exits based on permissions
   - Needed: Check skill/trust before allowing entry
   - Options:
     a. Exit handler that checks permission and blocks with message
     b. Location `requires_skill` property checked by movement handler
   - Recommendation: Option (b) - add to existing movement infrastructure

3. **Camp morale system** (game-level morale)
   - Current: NPC morale exists (for combat)
   - Needed: Location-level morale affecting services/atmosphere
   - Implementation: Add `camp_morale` to location properties
   - Update on rescue outcomes via condition_reactions or death_reactions
   - Service availability checks `location.properties.camp_morale >= threshold`

4. **Knowledge fragment system**
   - Current: Not implemented
   - Needed: Track collected fragments, deliver to NPCs, quest completion
   - Implementation:
     - Add `player.properties.knowledge_fragments` array
     - Add `fragment_id` to items that count as fragments
     - Archivist handler checks fragment count for quest completion
   - Note: Full system is substantial; consider minimal implementation for Delvan's contacts only

---

## Phased Implementation Plan

### Phase 1: Tier 1 Dialog Reactions
**Estimated scope:** Small - 4 dialog handlers

1. healer_elara: Aldric rescue trust bonus
2. camp_leader_mira: Jek referral dialog
3. camp_leader_mira: Garrett recovery dialog
4. merchant_delvan: Undercity access dialog

**Files to modify:**
- `examples/big_game/behaviors/regions/civilized_remnants/services.py` (Elara)
- `examples/big_game/behaviors/regions/sunken_district/mira.py` (Mira)
- `examples/big_game/behaviors/regions/sunken_district/dual_rescue.py` (Delvan)

**Walkthroughs to create:**
- `test_elara_aldric_bonus.txt`
- `test_mira_jek_referral.txt`
- `test_mira_garrett_recovery.txt`
- `test_delvan_undercity_dialog.txt`

### Phase 2: Service System Extensions
**Estimated scope:** Medium - extend existing services infrastructure

1. Add `has_skill()` utility to check prerequisite skills
2. Add `requires_skill` to service config schema
3. Implement teach_basic_herbalism service (Elara)
4. Implement teach_advanced_herbalism service (Elara)
5. Implement safe_rest service (Mira)
6. Add state-gated trades for Delvan

**Files to modify:**
- `behavior_libraries/actor_lib/services.py` (core changes)
- `examples/big_game/game_state.json` (service configs)
- `examples/big_game/behaviors/regions/civilized_remnants/services.py` (Elara handlers)
- `examples/big_game/behaviors/regions/sunken_district/mira.py` (Mira handlers)

**Walkthroughs to create:**
- `test_elara_basic_herbalism.txt`
- `test_elara_advanced_herbalism.txt`
- `test_mira_safe_rest.txt`
- `test_delvan_trade_services.txt`

### Phase 3: Location Permission System
**Estimated scope:** Medium - new infrastructure

1. Add `requires_skill` / `requires_trust` to exit schema
2. Modify movement handler to check permissions
3. Add permission-denied feedback messages
4. Configure healer's garden access control
5. Test garden entry with/without herbalism skill

**Files to modify:**
- `game_engine/vocabulary/movement.py` or exit handling code
- `examples/big_game/game_state.json` (garden exit config)
- Schema documentation

**Walkthroughs to create:**
- `test_elara_garden_access.txt`

### Phase 4: Camp Morale System
**Estimated scope:** Medium - connect existing infrastructure

1. Add `camp_morale` property to survivor_camp location
2. Update rescue handlers to modify camp_morale
3. Add morale-based service availability checks
4. Add morale-based dialog variations

**Files to modify:**
- `examples/big_game/game_state.json` (camp properties)
- `examples/big_game/behaviors/regions/sunken_district/dual_rescue.py` (morale updates)
- `examples/big_game/behaviors/regions/sunken_district/mira.py` (morale checks)

**Walkthroughs to create:**
- `test_camp_morale_high.txt`
- `test_camp_morale_low.txt`

### Phase 5: Knowledge Fragment System (Minimal)
**Estimated scope:** Medium - new infrastructure but scoped to Delvan only

1. Add `knowledge_fragments` array to player properties
2. Add dialog handler for Delvan to grant fragment
3. Note: Full Archivist quest implementation deferred

**Files to modify:**
- `examples/big_game/game_state.json` (player properties)
- `examples/big_game/behaviors/regions/sunken_district/dual_rescue.py` (Delvan handler)

**Walkthroughs to create:**
- `test_delvan_contacts_fragment.txt`

---

## Debugging Guidance

### Dialog Reactions Not Firing
1. Check vocabulary registers the dialog verb
2. Verify handler function name matches event name exactly
3. Check `requires_state` or `requires_flags` conditions
4. Use `@debug dialog` in walkthrough to trace

### Service Not Available
1. Check `requires_trust` threshold against current trust
2. Check `requires_state` against NPC state machine
3. Check `requires_skill` against player.properties.skills
4. Verify service is listed in NPC's `services` property

### Location Access Blocked Unexpectedly
1. Check exit's `requires_skill` or `requires_trust` config
2. Verify player has required skill/trust level
3. Check for `requires_flags` that might not be set

### Morale Not Updating
1. Check handler fires on rescue/death
2. Verify location property path is correct
3. Check accessor.update_entity() is called
4. Use `@inspect locations.survivor_camp.properties.camp_morale` in walkthrough

---

## Success Criteria

### Phase 1 Complete When:
- [ ] All 4 Tier 1 dialog reactions implemented
- [ ] All 4 walkthroughs passing
- [ ] No regressions in existing template NPC walkthroughs

### Phase 2 Complete When:
- [ ] `has_skill()` utility exists and tested
- [ ] `requires_skill` in service config works
- [ ] All 4 service extensions implemented
- [ ] All 4 service walkthroughs passing

### Phase 3 Complete When:
- [ ] Location permission system implemented
- [ ] Garden access control working
- [ ] Garden access walkthrough passing

### Phase 4 Complete When:
- [ ] Camp morale property exists
- [ ] Rescue handlers update morale
- [ ] Morale affects service availability
- [ ] Both morale walkthroughs passing

### Phase 5 Complete When:
- [ ] Knowledge fragment storage exists
- [ ] Delvan grants fragment via dialog
- [ ] Fragment walkthrough passing

### All Phases Complete When:
- [ ] All 5 template NPCs have full functionality per scenario documents
- [ ] All walkthroughs passing
- [ ] Template NPCs serve as complete reference implementations

---

## Related Documents

- [npc_implementation_inventory.md](npc_implementation_inventory.md) - Full NPC tracking
- [npc_upgrade_plan.md](npc_upgrade_plan.md) - Plan for remaining 37 NPCs
- [npc_reaction_system_guide.md](../Guides/npc_reaction_system_guide.md) - Reaction system reference
- Scenario documents in `tests/core_NPC_scenarios/`

---

## Open Questions

1. **Garden access**: Should denied entry be a hard block (can't enter) or soft block (can enter but can't harvest)?
   - Recommendation: Soft block - player can enter, but take_reactions prevent harvesting without skill

2. **Camp morale granularity**: Integer scale (0-100) or categorical (low/medium/high)?
   - Recommendation: Categorical for simplicity, maps to service availability tiers

3. **Knowledge fragments**: Implement full Archivist quest or just Delvan's fragment?
   - Recommendation: Just Delvan's fragment for now; full quest is separate work

4. **Undercity**: Dialog sets flag, but undercity doesn't exist yet. Acceptable?
   - Recommendation: Yes - flag enables future content; dialog provides narrative closure
