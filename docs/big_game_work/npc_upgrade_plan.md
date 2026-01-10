# NPC Upgrade Plan: Bringing All NPCs to Template Quality

**Goal:** Systematically upgrade all ~50 NPCs to match the quality level of the 5 template NPCs (bee_queen, healer_elara, hunter_sira, camp_leader_mira, merchant_delvan).

**Template Quality Standard:**
- Complete scenario document in `tests/core_NPC_scenarios/`
- All required reaction types implemented
- Comprehensive walkthrough covering success, failure, and edge cases
- 100% walkthrough success (no @set hacks bypassing broken mechanics)
- Reference documentation with config examples and flow diagrams

**Scope:** 36 NPCs in game_state.json + 9 NPCs defined in sketches only = 45 total
- 14 placeholders (zero implementation)
- 1 significant gap (merchant_delvan - now complete)
- 21 appear complete (may have subtle gaps)
- 9 not yet implemented (sketches only)

---

## Phase 1: Critical Path Completion (IMMEDIATE)

**Goal:** Unblock core quest progression by implementing NPCs required for main storylines.

### 1.1 old_swimmer_jek (CRITICAL - Blocks Dual Rescue Quest)

**Why Critical:** Player cannot reach sailor_garrett without swimming skill. Entire Sunken District dual rescue quest is unplayable.

**Design:** sunken_district_detailed_design.md (complete spec)

**Implementation Requirements:**
- dialog_reactions: 3 topics (swimming, price, favor)
- Service system: Teach swimming skill (basic OR advanced)
- Commitment integration: Free teaching with mira_favor commitment
- Skill acquisition: Player gains swimming skill (breath +15 basic, +30 advanced)

**Dependencies:**
- Teaching/skill acquisition system (NEW infrastructure needed)
- Service cost checking (gold OR food item)
- Commitment checking (if player has mira_favor, free teaching)

**Testing (Scenario Document):**
Create `tests/core_NPC_scenarios/npc_old_swimmer_jek.md` defining:
- Success: Learn swimming via paid teaching
- Success: Learn swimming via free teaching (with mira_favor)
- Edge: Try advanced without basic first
- Verification: Player gains swimming skill, can traverse tidal_passage

**Success Criteria:**
- Scenario document created and reviewed
- All scenarios have walkthroughs
- All walkthroughs pass 100%
- Player can learn swimming and traverse tidal_passage

**Estimated Effort:** 2-3 phases (1 for teaching system infrastructure, 1 for Jek implementation, 1 for testing/refinement)

---

## Phase 2: Well-Documented Placeholders (SHORT-TERM)

**Goal:** Implement placeholder NPCs with complete design specs in detailed_designs/ documents.

### 2.1 Civilized Remnants Council NPCs (asha, hurst, varn)

**Design:** civilized_remnants_detailed_design.md (complete spec)

**Role:** Quest preference system - player chooses which councilor to support (mutually exclusive paths)

**Implementation Requirements:**
- dialog_reactions: Each councilor has unique dialog topics
- Quest gating: Accept quest from one councilor locks out others
- Un-branding ceremony: Completion removes faction_marker
- Reward delivery: Councilor-specific rewards on quest success

**Dependencies:**
- Quest preference system (NEW infrastructure needed)
- Faction reputation integration
- Reward delivery mechanism

**Testing (Scenario Documents):**
Create `tests/core_NPC_scenarios/npc_councilor_<name>.md` for each (asha, hurst, varn) defining:
- Success: Accept quest, complete quest, receive reward
- Failure: Accept quest, miss deadline
- Edge: Try to accept second quest after first accepted (should fail)
- Verification: Quest states, rewards delivered, faction reputation changes

**Success Criteria:**
- Scenario document for each councilor
- All scenarios have walkthroughs
- All walkthroughs pass 100%

**Estimated Effort:** 3-4 phases (1 for quest preference infrastructure, 1 per councilor, 1 for integration testing)

### 2.2 Undercity NPCs (shadow, the_fence, whisper)

**Design:** civilized_remnants_detailed_design.md (complete spec)

**Role:** Black market services (assassination contracts, stolen goods trading, information brokering)

**Implementation Requirements:**
- dialog_reactions: Service-specific dialog topics
- Service systems:
  - **shadow:** Assassination contracts (target, price, delayed completion)
  - **the_fence:** Buy/sell stolen goods (reputation gates, fencing mechanics)
  - **whisper:** Information sales (NPC secrets, location secrets, valuable secrets)
- Price negotiation: Reputation affects pricing
- Morality flags: Using these services may affect other NPCs' trust

**Dependencies:**
- Trading system enhancements (stolen goods flagging)
- Contract/delayed task system
- Secret/information delivery system

**Testing (Scenario Documents):**
Create `tests/core_NPC_scenarios/npc_<name>.md` for each (shadow, the_fence, whisper) defining:
- Success: Complete transaction successfully
- Failure: Transaction blocked by reputation gate
- Edge: Morality consequences detected by other NPCs
- Verification: Items/gold exchanged, flags set, reputation effects

**Success Criteria:**
- Scenario document for each undercity NPC
- All scenarios have walkthroughs
- All walkthroughs pass 100%

**Estimated Effort:** 4-5 phases (1 for trading/contract infrastructure, 1 per NPC, 1 for integration testing)

### 2.3 weaponsmith_toran

**Design:** civilized_remnants_detailed_design.md (complete spec)

**Role:** Weapon/armor vendor with reputation gates

**Implementation Requirements:**
- dialog_reactions: Services, prices, reputation commentary
- Vendor services: Sell weapons, sell armor, repair items
- Reputation gates: Refuses service at reputation < -3

**Dependencies:**
- Vendor/shop system (may already exist, verify)
- Reputation integration

**Testing (Scenario Document):**
Create `tests/core_NPC_scenarios/npc_weaponsmith_toran.md` defining:
- Success: Purchase weapon, purchase armor, repair item
- Failure: Refused service at low reputation
- Edge: Reputation changes mid-transaction
- Verification: Items gained, gold deducted, reputation gates enforced

**Success Criteria:**
- Scenario document created and reviewed
- All scenarios have walkthroughs
- All walkthroughs pass 100%

**Estimated Effort:** 1-2 phases (depends on existing vendor system completeness)

### 2.4 predatory_fish

**Design:** sunken_district_detailed_design.md (complete spec)

**Role:** Environmental hazard (NOT combat encounter) in flooded_chambers

**Implementation Requirements:**
- encounter_reactions: Watch in shallows (no attack), attack once in deep water
- Hazard properties: `hazard_type="environmental"`, `not_combat_encounter=true`, `no_xp_or_loot=true`
- Damage + condition: 8 HP damage + bleeding condition on attack
- One-time attack: After first attack, becomes passive

**Dependencies:**
- Environmental hazard system (may need NEW infrastructure for non-combat attacks)

**Testing (Scenario Document):**
Create `tests/core_NPC_scenarios/npc_predatory_fish.md` defining:
- Success: Safe passage through shallows
- Hazard: Attack when entering deep water
- Edge: Second entry (fish passive after first attack)
- Verification: HP damage applied, bleeding condition added, one-time attack enforced

**Success Criteria:**
- Scenario document created and reviewed
- All scenarios have walkthroughs
- All walkthroughs pass 100%

**Estimated Effort:** 1-2 phases (depends on whether environmental hazard system exists)

---

## Phase 3: Validation of "Complete" NPCs (MEDIUM-TERM)

**Goal:** Verify that 21 "appear complete" NPCs actually match their sketch designs and have comprehensive test coverage.

**Process for Each NPC:**
1. Read sketch design + any detailed_design references
2. Compare config in game_state.json to design spec
3. Identify missing mechanics (dialog topics, reaction types, state transitions)
4. **Create scenario document** in `tests/core_NPC_scenarios/npc_<npc_id>.md`:
   - List all reaction types (from config) in Core Mechanics
   - Define success/failure/edge cases in Required Scenarios
   - Specify verification criteria (state changes, feedback)
5. Review scenario document with user
6. Create comprehensive walkthrough implementing all scenarios
7. Run walkthrough - if failures, fix mechanics
8. Iterate until 100% success
9. Mark scenario document checkboxes complete

**NPC List (Priority Order):**

### 3.1 High Priority - Quest/Story Critical
- **npc_aldric** (Civilized Remnants) - item_use + dialog
- **npc_myconid_elder** (Fungal Depths) - encounter + dialog
- **npc_spore_mother** (Fungal Depths) - item_use + death + dialog
- **sailor_garrett** (Sunken District) - death + condition reactions
- **herbalist_maren** (Civilized Remnants) - dialog reactions

**Estimated Effort:** 1-2 phases per NPC (scenario creation + walkthrough validation)

### 3.2 Medium Priority - Enrichment NPCs
- **alpha_wolf** - gift_reactions
- **dire_bear** - encounter + gift reactions
- **curiosity_dealer_vex** - dialog + gift reactions
- **damaged_guardian** - item_use + dialog reactions
- **the_archivist** - dialog + gift reactions
- **the_echo** - dialog + gossip reactions

**Estimated Effort:** 1 phase per NPC (may batch multiple NPCs per phase if similar)

### 3.3 Lower Priority - Creature Encounters
- **bear_cub_1, bear_cub_2** - item_use_reactions
- **stone_golem_1, stone_golem_2** - item_use + death + dialog
- **steam_salamander_2, steam_salamander_3** - dialog reactions

**Estimated Effort:** 1 phase for all cubs/golems/salamanders together (similar mechanics)

---

## Phase 4: Low-Spec Placeholders (LONG-TERM)

**Goal:** Implement placeholders with minimal sketch documentation.

### 4.1 Giant Spiders (giant_spider_1, giant_spider_2)

**Design:** placeholder_npc_specifications.md (complete spec synthesized from beast_wilds_detailed_design.md)

**Role:** Combat followers of spider_matriarch, respawn while queen lives

**Implementation Requirements:**
- encounter_reactions: Immediate hostile attack when player enters spider_thicket
- death_reactions: Loot drop (spider_silk, venom_sac), no respawn if matriarch dead
- Pack dynamics: Follower role, respawn every 10 turns while matriarch alive
- Combat: Bite (12 damage), Web spray (8 damage + restrained condition)

**Dependencies:**
- Pack respawn system (may exist from wolf pack, verify)
- Restrained condition (NEW if not already implemented)

**Success Criteria:**
- Scenario document created
- Walkthrough covers: encounter, combat, loot, respawn mechanics, matriarch death effects
- 100% walkthrough success

**Estimated Effort:** 1-2 phases (combat NPCs are simpler than quest NPCs)

### 4.2 Sporelings (npc_sporeling_1, npc_sporeling_2, npc_sporeling_3)

**Design:** placeholder_npc_specifications.md (complete spec synthesized from fungal_depths_detailed_design.md)

**Role:** Pack followers of npc_spore_mother, mirror her emotional state

**Implementation Requirements:**
- encounter_reactions: Mirror Spore Mother's state (hostile/wary/allied)
- death_reactions: Set `has_killed_fungi` flag (Myconid detection)
- Empathic communication: Emit colored spores matching Mother's emotions
- Pack dynamics: State mirroring, bound to spore_heart, wither 10 turns after Mother dies
- Individual differences: sporeling_1 (bold), sporeling_2 (cautious), sporeling_3 (younger)

**Dependencies:**
- Empathic communication system (NEW infrastructure)
- Spore network integration (Myconid detection)
- Bound_to_location mechanic

**Success Criteria:**
- Scenario document created
- Walkthrough covers: state mirroring, empathic reactions, confusion/withering after Mother's death
- 100% walkthrough success

**Estimated Effort:** 2-3 phases (empathic communication is novel, needs careful design)

---

## Phase 5: Not-Yet-Implemented NPCs (EXPANSION)

**Goal:** Implement NPCs defined in sketches but not in game_state.json.

**NPC List:**
- bee_swarm (beast_wilds) - Encounter reactions for bee queen protection
- child_survivor (sunken_district) - Dialog about parents, fear of water
- gate_guard_1, gate_guard_2 (civilized_remnants) - Dialog about entry, faction reputation
- grey_wolf_1, grey_wolf_2, grey_wolf_3 (beast_wilds) - Pack encounter mechanics
- spider_queen (beast_wilds) - Boss creature, complex encounter + death
- steam_salamander_1 (frozen_reaches) - Gift/dialog reactions

**Priority:** LOW - These add world richness but are not blocking core gameplay.

**Approach:** Implement after all existing NPCs are at template quality.

**Estimated Effort:** 1-2 phases per NPC, similar to Phase 3 work.

---

## Phase 6: Ad-Hoc NPC Review (INVESTIGATION)

**Goal:** Review NPCs created outside of sketch process for design consistency.

**NPC List:**
- frost_wolf_1, frost_wolf_2 (wolf_clearing)
- gate_guard (town_gate) - vs sketches' gate_guard_1/gate_guard_2
- salamander (hot_springs) - vs steam_salamander_1/2/3
- spider_matriarch (spider_matriarch_lair) - vs spider_queen
- waystone_spirit (nexus_chamber)

**Process:**
1. Determine if these are intentional refactorings or unplanned additions
2. Create scenario documents retroactively
3. Validate with walkthroughs
4. Document design decisions

**Estimated Effort:** 1 phase for investigation + documentation

---

## Infrastructure Needs (Cross-Cutting)

**Required for multiple NPC implementations:**

### Teaching/Skill Acquisition System
- **Needed by:** old_swimmer_jek (swimming), potentially others (herbalist teaching alchemy?)
- **Scope:** Player learns skills, skills persist in properties, skills gate actions
- **Priority:** CRITICAL (blocks Phase 1.1)

### Quest Preference System
- **Needed by:** Council NPCs (asha, hurst, varn)
- **Scope:** Accept quest from one NPC locks out others, track active preference
- **Priority:** HIGH (needed for Phase 2.1)

### Trading/Contract System Enhancements
- **Needed by:** Undercity NPCs (shadow, the_fence, whisper)
- **Scope:** Stolen goods flagging, delayed task completion, contract tracking
- **Priority:** HIGH (needed for Phase 2.2)

### Environmental Hazard System
- **Needed by:** predatory_fish, potentially other non-combat dangers
- **Scope:** Non-combat entities can trigger attacks/conditions without combat mechanics
- **Priority:** MEDIUM (needed for Phase 2.4)

### Empathic Communication System
- **Needed by:** Sporelings (and potentially Spore Mother enhancement)
- **Scope:** Non-verbal emotional signaling through colored spores
- **Priority:** LOW (enrichment for Phase 4.2)

### Reward Delivery Mechanism
- **Needed by:** Council NPCs, potentially other quest-givers
- **Scope:** Delayed item/gold delivery on quest completion
- **Priority:** HIGH (needed for Phase 2.1)

---

## Testing Approach: Scenario Documents First

**Key Principle:** The scenario document is the SPECIFICATION; the walkthrough is the IMPLEMENTATION.

Every NPC gets a scenario document in `tests/core_NPC_scenarios/npc_<npc_id>.md` that defines:
- What mechanics exist (reaction types, systems)
- What scenarios must work (success, failure, edge cases)
- What verification is required (state changes, feedback)

The scenario document is written BEFORE implementation and updated as work progresses.

**Scenario Document Status:**
- 5 template NPCs: Have scenario documents (bee_queen, healer_elara, hunter_sira, camp_leader_mira, merchant_delvan)
- 31 other in-game NPCs: Need scenario documents created
- 9 sketch-only NPCs: Need scenario documents when implemented

---

## Workflow for Each NPC

**Follow Workflow C from CLAUDE.md:**

1. **Create scenario document** in `tests/core_NPC_scenarios/npc_<npc_id>.md`
   - Core Mechanics section (list reaction types, systems)
   - Required Scenarios section (success/failure/edge cases with verification criteria)
   - Dependencies section (items, NPCs, infrastructure)
   - Walkthrough Files section (map scenarios → files)
   - Implementation Status section (checkboxes)

2. **Review scenario document** with user for completeness

3. **Implement missing mechanics** following template patterns:
   - Copy-paste config from [npc_reaction_system_guide.md](../docs/Guides/npc_reaction_system_guide.md) reference examples
   - Adapt handler code to NPC-specific logic
   - Use TDD for handler testing

4. Create comprehensive walkthrough in `walkthroughs/test_<npc_id>_<scenario>.txt`
   - Cover ALL scenarios from scenario document
   - Include @expect for success feedback
   - Include @assert for state changes
   - Document expected failures with comments

5. Run walkthrough using `tools/walkthrough.py`
   - If failures occur, follow [Debugging Workflow](../docs/Guides/npc_reaction_system_guide.md#debugging-workflow-infrastructure-first-approach)
   - Fix mechanics (NOT walkthroughs with @set hacks)
   - Iterate until 100% success

6. Update scenario document:
   - Check off implementation status boxes
   - Mark walkthrough files as ✅ EXISTS, PASSING
   - Add reference links to code (file:line)

7. Close NPC sub-issue with summary comment

---

## Success Metrics

**Per-NPC Completion:**
- [ ] Scenario document exists in tests/core_NPC_scenarios/
- [ ] All scenarios have walkthroughs
- [ ] All walkthroughs pass 100%
- [ ] Scenario document checkboxes all marked
- [ ] Config examples added to npc_reaction_system_guide.md (if novel patterns)

**Overall Completion:**
- [ ] All 36 in-game NPCs validated
- [ ] All critical path NPCs implemented (Phase 1)
- [ ] All well-documented placeholders implemented (Phase 2)
- [ ] All "complete" NPCs validated (Phase 3)
- [ ] Low-spec placeholders implemented (Phase 4)
- [ ] Expansion NPCs implemented (Phase 5)
- [ ] Ad-hoc NPCs documented (Phase 6)

---

## Prioritization Rationale

**Phase 1 (CRITICAL):** old_swimmer_jek blocks entire dual rescue quest, must be done first.

**Phase 2 (HIGH):** Well-documented NPCs with complete specs can be implemented immediately, provide high value (council quests, undercity services).

**Phase 3 (MEDIUM):** "Complete" NPCs may have subtle gaps, validation ensures no regressions when other NPCs reference them.

**Phase 4 (LOW):** Spiders/sporelings are enrichment content, not blocking quests.

**Phase 5 (EXPANSION):** Not-yet-implemented NPCs add world richness but can wait.

**Phase 6 (INVESTIGATION):** Ad-hoc NPCs may be intentional, need design review before deciding if work needed.

---

## Estimated Timeline

**Assuming one NPC phase per work session:**

- Phase 1: 2-3 sessions (teaching system + Jek + testing)
- Phase 2: 10-12 sessions (3 infrastructure + 6 NPCs + 2 testing)
- Phase 3: 15-20 sessions (21 NPCs, some batched)
- Phase 4: 4-5 sessions (spiders + sporelings)
- Phase 5: 9 sessions (expansion NPCs)
- Phase 6: 1 session (investigation)

**Total: ~40-50 sessions to bring all NPCs to template quality**

---

## Next Steps

1. **User Decision:** Approve plan, adjust priorities if needed
2. **Create Parent Issue:** "Bring All NPCs to Template Quality" (Issue #???)
3. **Start Phase 1:** Create sub-issue for old_swimmer_jek, begin implementation
4. **Track Progress:** Update current_focus.txt after each NPC completion
5. **Document Learnings:** Add new patterns to npc_reaction_system_guide.md as discovered

---

## Related Documents

- [npc_implementation_inventory.md](npc_implementation_inventory.md) - Current status of all NPCs
- [placeholder_npc_specifications.md](placeholder_npc_specifications.md) - Full specs for low-doc NPCs
- [core_NPC_scenarios_testing.md](../docs/Guides/core_NPC_scenarios_testing.md) - Testing methodology
- [npc_reaction_system_guide.md](../docs/Guides/npc_reaction_system_guide.md) - Reference examples and patterns
- civilized_remnants_detailed_design.md - Council + undercity + toran specs
- sunken_district_detailed_design.md - Jek + predatory_fish specs
- beast_wilds_detailed_design.md - Spider pack specs
- fungal_depths_detailed_design.md - Sporeling specs
