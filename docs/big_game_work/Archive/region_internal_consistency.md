# Phase 2: Region Internal Consistency Report

**Date**: 2025-12-11
**Status**: Complete - 53 issues identified across 6 regions

---

## Summary

This document tracks internal consistency issues found during Phase 2 review of each region's detailed design. Issues are categorized by severity:
- **Critical**: Must fix before implementation
- **High**: Should fix, affects gameplay or implementation
- **Medium**: Polish, minor inconsistencies
- **Low**: Documentation cleanup

---

## Fungal Depths

### Critical Issues

| # | Issue | Description | Resolution |
|---|-------|-------------|------------|
| FD-1 | Waystone Fragment Contradiction | Section 3.6 says "No waystone fragment in this region" but Section 2.2 exports "Spore Heart" as a "Waystone fragment" to Meridian Nexus | Clarify: Spore Heart IS a waystone fragment; update Section 3.6 |
| FD-2 | Spore Mother Timer Ambiguity | Section 1.2 lists 200-turn commitment timer, but she also has "Fungal blight severity 70, progression rate 1/turn" condition - which would kill her in ~30 turns | Clarify: 200 turns is commitment timer (player promise), her condition progression is separate and very slow (not actually threatening) |

### High Issues

| # | Issue | Description |
|---|-------|-------------|
| FD-3 | Aldric Timer "From Game Start" | Section 1.2 says timer starts "from game start" but Section 3.3 uses `trigger_type: "on_commitment"` which starts timer when player commits. Internally inconsistent. |
| FD-4 | Missing Trust Recovery Cap Clarification | Section B.4 shows Myconid trust `recovery_cap: 1` but Section 0.5 doesn't specify whether this is per-visit or per-action |

### Medium Issues

| # | Issue | Description |
|---|-------|-------------|
| FD-5 | Spore Mother Hope Bonus Explanation | Section 3.3 says `hope_extends_survival: False` with note "Too powerful to be affected by hope" - misleading since the 200-turn timer is already so generous that hope is irrelevant |
| FD-6 | Wolf Sub-Location Restriction | Section 4.3 says wolves "refuse to enter Spore Heart or Deep Roots" but game_wide_rules.md Companion Restrictions Matrix only lists region-level restrictions |

---

## Beast Wilds

### Critical Issues

| # | Issue | Description | Resolution |
|---|-------|-------------|------------|
| BW-1 | Sira Timer Trigger vs Hope Mechanics | Section 3.3 uses `trigger_type: "on_first_encounter"` (timer starts when Sira found), but hope bonus is supposed to apply when player commits. Unclear if hope applies retroactively or not. | Clarify: Hope extends NPC survival from commitment point, not from first encounter. If timer already started, hope bonus extends from that point. |
| BW-2 | Moonpetal Not in Fungal Depths | Section 2.1 and Appendix B list moonpetal as available from Fungal Depths (Luminous Grotto), but Fungal Depths Section 1.3 doesn't list moonpetal as an item | Either add moonpetal to Fungal Depths, or remove Fungal Depths as a moonpetal source |

### High Issues

| # | Issue | Description |
|---|-------|-------------|
| BW-3 | Bear Cubs Timer Triplication | Section 1.2 lists the same "30 turns base (+5 hope)" timer on both the dire bear AND both bear cubs. The timer should probably be on the cubs (who are dying) not the bear. |
| BW-4 | Missing Reverse Exit Documentation | Southern Trail connects to Town Gate (Civilized Remnants), but there's no verification that Town Gate connects back to Southern Trail |

### Medium Issues

| # | Issue | Description |
|---|-------|-------------|
| BW-5 | Bandages Source Unclear | Section 2.1 imports bandages from Civilized Remnants for Sira's rescue, but need to verify Civilized Remnants actually exports bandages |

---

## Sunken District

### Critical Issues

| # | Issue | Description | Resolution |
|---|-------|-------------|------------|
| SD-1 | Missing DQ-3 Resolution (Delvan Undercity Access) | consistency_review_followup.md decided Delvan gives narrative hint + player must ask, but Section 1.2 just says "black market connection" without the mechanism | Add to Section 1.2: Delvan's rescue dialog includes hint about "special services" - player must return and ask to learn undercity entrance pattern |
| SD-2 | Sira Companion Contradiction | Section 0.4 says "Companion exclusion is systematic" but Section 4.3 says "Human (Sira) | Limited | Depends on swimming" implying Sira CAN enter with advanced swimming | Decide: Either Sira can enter with swimming (update Section 0.4) or she can't (update Section 4.3) |

### High Issues

| # | Issue | Description |
|---|-------|-------------|
| SD-3 | Timer Trigger Naming Inconsistency | Section 3.3 uses `trigger_type: "on_room_entry"` but Appendix B uses `"timer_trigger": "room_entry"` - should standardize |
| SD-4 | Air Bladder Deep Archive Note Confusing | Section 1.3 says air bladder "Works in: Most flooded areas (NOT Deep Archive without Archivist bubble)" but Deep Archive is a dry sealed chamber - the issue is REACHING it, not breathing inside |

### Medium Issues

| # | Issue | Description |
|---|-------|-------------|
| SD-5 | Camp Morale Effects Incomplete | Section 3.5 mentions services unavailable at low morale and bonus services at high morale but doesn't specify which services |
| SD-6 | Knowledge Quest Design Note | If both Garrett and Delvan die, only 3 fragments are available (exactly minimum needed). This seems designed but should be explicitly noted as "always possible to complete" |
| SD-7 | Timer Format Not Standardized | Section 1.2 should use "5 turns base (no hope bonus)" and "10 turns base (+3 hope bonus)" format per game_wide_rules.md |

---

## Frozen Reaches

### High Issues

| # | Issue | Description |
|---|-------|-------------|
| FR-1 | Wolf Cold Tolerance Contradiction | Section 4.3 says wolves are "Comfortable (cold/freezing)" but game_wide_rules.md says wolves have -1 combat effectiveness in "bitter cold" areas like Deep Frost and Ice Caves |
| FR-2 | Cold Spread Timeline Mismatch | Section 2.4 says cold spread starts Turn 75, but game_wide_rules.md says Turn 80+ |
| FR-3 | Fire Crystal Access Unclear | Section 1.1 mentions fire crystal in "side chamber" of temple_sanctum but doesn't clarify if this is accessible before or after solving golem puzzle |

### Medium Issues

| # | Issue | Description |
|---|-------|-------------|
| FR-4 | Duplicate Skills Sections | Section 3.5 says "N/A - No skills" and Section 3.7 says "addressed in Section 3.5 above" - template numbering confusion (3.5 should be Branding/Reputation, 3.7 should be Skills) |
| FR-5 | Hot Springs Temperature Label | Section 4.1 calls it "Normal" zone but earlier says "Normal (warm)" - should clarify this means comfortable temperature, not "no special effects" |

---

## Civilized Remnants

### Critical Issues

| # | Issue | Description | Resolution |
|---|-------|-------------|------------|
| CR-1 | Missing Bandages Export | Beast Wilds imports bandages from Civilized Remnants (for Sira), but Section 2.2 doesn't list bandages as an export | Add bandages to Section 2.2 exports, or clarify which merchant sells them |
| CR-2 | Delvan Undercity Mechanism Missing | Section 1.1 line 160 mentions "Delvan's black market connection" but doesn't specify the DQ-3 resolution (hint during rescue + player must ask) | Add to Section 1.1: "Delvan hints at special services during rescue. Player must return and ask to learn undercity knock pattern." |

### High Issues

| # | Issue | Description |
|---|-------|-------------|
| CR-3 | Assassination Trust Penalty Missing | Section 1.2 (Shadow NPC) doesn't mention Echo trust penalty. game_wide_rules.md says "-2 per assassination (cumulative)" but this is Echo trust, not NPC trust - need to clarify |
| CR-4 | Town Seal Sources Inconsistent | Section 1.3 says "Council Hall (earned)" but Section 3.6 clarifies "Reputation 5+ OR Guardian repair" - consolidate language |
| CR-5 | Refugee Cure Sources Ambiguity | Section 2.1 lists "Spore Mother Blessing" AND "Myconid Cure" as separate items, but unclear if these are alternatives or the same thing |
| CR-6 | Sira-Elara Gossip Timing Ambiguity | Section 2.3 says "12-20 turns" but Section 3.4 breaks this into 12 (death/rescue) vs 20 (abandonment) - should be explicit in Section 2.3 |
| CR-7 | Guardian Repair Imports Incomplete | Section 1.4 lists three requirements (animator_crystal, stone_chisel, ritual_knowledge) but Section 2.1 only lists two imports (animator_crystal and ritual_knowledge) - stone_chisel is local |

### Medium Issues

| # | Issue | Description |
|---|-------|-------------|
| CR-8 | Maren Trust System Missing from Appendix | Section 1.2 describes Maren trust sources but Appendix A.3 only has TrustConfig for Elara |
| CR-9 | Undercity Discovery Tracking Unclear | Section 1.1 says "5% per service" but doesn't specify cumulative tracking. Section 3.5 says "3+ discoveries" triggers branding |
| CR-10 | Salamander Incident Rate Duplicate | Section 4.3 mentions "5% fire incident chance" and later "5% chance per turn in crowded areas" - same mechanic, inconsistent phrasing |
| CR-11 | Echo Direct Connection Missing | Section 2.3 lists "Echo (via NPCs)" but Echo has direct knowledge of assassinations (0 turns) - should clarify direct vs indirect |
| CR-12 | Council Dilemma JSON Terminology | Appendix B uses `turn_away` which is correct post-exile→branding migration, but should verify against Section 1.4 choices |

---

## Meridian Nexus

### Critical Issues

| # | Issue | Description | Resolution |
|---|-------|-------------|------------|
| MN-1 | Echo Trust Floor Inconsistency | Section 1.2 says "Refuses at trust ≤ -3" but Section 3.8 and game_wide_rules.md describe a tiered system (-3 reluctant 5%, -6 refuses entirely) | Update Section 1.2 to match game_wide_rules.md tiered system |
| MN-2 | Echo Appearance Mechanics Conflicts | Section 1.2 says "Minimum (trust ≤ -2): 5%" and "Refuses at trust ≤ -3" - these contradict (is 5% at -2 or at -3 to -5?) | Align with DQ-2 resolution: 5% at -3 to -5, 0% at -6 |

### High Issues

| # | Issue | Description |
|---|-------|-------------|
| MN-3 | Waystone Spirit as Minimal NPC | The waystone is modeled as a "minimal NPC" but this may cause issues with infrastructure systems expecting full actor properties. Verify infrastructure handles `is_object: true` flag correctly |
| MN-4 | Echo Trust Recovery Cap Location | Section 3.8 says "+1 per Nexus visit" but Appendix A.1 TrustState has `recovery_cap: 1` - these need to explicitly connect (is the cap tracked per-visit?) |
| MN-5 | Crystals Restored Triggers Incomplete | Section 1.3 lists restoration triggers but some are ambiguous: "Frozen crystal restores when: Telescope repaired OR major rescue" - which major rescue? |
| MN-6 | Ending Table Missing Echo Trust Tiers | Section 3.6 ending table uses trust levels like "-3 to -5" and "-6 or below" but these should reference the tiered system (reluctant/refuses) for clarity |

### Medium Issues

| # | Issue | Description |
|---|-------|-------------|
| MN-7 | Missing Town Gate Exit | Section 1.1 exits: nexus_chamber south → `forest_edge`, but Civilized Remnants town_gate north → `southern_trail`. These should connect via Beast Wilds |
| MN-8 | Aldric Relocation Incomplete | Section 6.1 mentions "Aldric may appear in Keeper's Quarters as scholar/teacher" but this is described as "future expansion" - should clarify if implemented or not |
| MN-9 | Crystal Restoration Buffs Overlap | Section 1.3: Beast crystal gives "+10 max health" and Water crystal gives "Improved breath" - some buffs seem trivial compared to others |
| MN-10 | Appendix B Trust Floor | Appendix A.1 shows `floor: -6` but earlier in doc it says Echo refuses at -3. The floor should be -6 (mechanical) with behavioral effects starting at -3 |

---

## Cross-Cutting Issues

Issues that affect multiple regions or relate to game_wide_rules.md:

| # | Issue | Affected Regions | Description |
|---|-------|------------------|-------------|
| CC-1 | Timer Format Standardization | All | Not all regions use the "base + hope = max" format consistently |
| CC-2 | Sub-Location Companion Restrictions | Fungal Depths, Beast Wilds | game_wide_rules.md Companion Restrictions Matrix is region-level only, but some regions have sub-location restrictions (wolves won't enter Spider Nest Gallery, Spore Heart, Deep Roots) |
| CC-3 | Hope Bonus Application Timing | Beast Wilds, Sunken District | When timer starts on_first_encounter vs on_commitment, how does hope bonus work? Document in game_wide_rules.md |
| CC-4 | Echo Trust Tiered System | Meridian Nexus, game_wide_rules.md | DQ-2 resolved with tiered system but Meridian Nexus detailed design still has old values |
| CC-5 | Moonpetal Source Mismatch | Beast Wilds, Fungal Depths, Civilized Remnants | Beast Wilds lists Fungal Depths as moonpetal source, but Fungal Depths doesn't export it. Civilized Remnants does export it. |
| CC-6 | Bandages Export Missing | Beast Wilds, Civilized Remnants | Beast Wilds imports bandages from Civilized Remnants but CR doesn't list them as export |
| CC-7 | Trigger Type Naming | Sunken District, infrastructure | `trigger_type: "on_room_entry"` vs `timer_trigger: "room_entry"` - need to standardize naming |
| CC-8 | Cold Spread Timeline | Frozen Reaches, game_wide_rules.md | FR says Turn 75, game_wide_rules.md says Turn 80+ |

---

## Resolution Priority

1. **Critical issues** must be resolved before implementation
2. **High issues** should be resolved before playtesting
3. **Medium issues** can be deferred to polish phase
4. **Low issues** are documentation cleanup

---

## Issue Count Summary

| Region | Critical | High | Medium | Total |
|--------|----------|------|--------|-------|
| Fungal Depths | 2 | 2 | 2 | 6 |
| Beast Wilds | 2 | 2 | 1 | 5 |
| Sunken District | 2 | 2 | 3 | 7 |
| Frozen Reaches | 0 | 3 | 2 | 5 |
| Civilized Remnants | 2 | 5 | 5 | 12 |
| Meridian Nexus | 2 | 4 | 4 | 10 |
| Cross-Cutting | 0 | 8 | 0 | 8 |
| **TOTAL** | **10** | **26** | **17** | **53** |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2025-12-11 | Initial draft - Fungal Depths, Beast Wilds, Sunken District, Frozen Reaches reviewed |
| 0.2 | 2025-12-11 | Completed - All six regions reviewed, cross-cutting issues added, summary table added |
