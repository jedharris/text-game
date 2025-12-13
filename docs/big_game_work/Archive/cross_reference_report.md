# Cross-Reference Verification Report

**Date**: 2025-12-11
**Purpose**: Verify all region designs against infrastructure API and state machine references
**Status**: Complete - Issues identified for discussion

---

## Executive Summary

| Region | API Mismatches | State Machine Issues | Clarifications Needed |
|--------|---------------|---------------------|----------------------|
| Beast Wilds | 0 | 0 | 4 minor |
| Civilized Remnants | 0 | 0 | 4 minor |
| Sunken District | 1 | 0 | 3 |
| Fungal Depths | 2 | 1 | 5 |
| Frozen Reaches | 0 | 0 | 3 |
| Meridian Nexus | 1 CRITICAL | 2 | 3 |

**Critical Issue**: Echo trust threshold inconsistency between API (-3 refuses) and design (-6 refuses)

---

## 1. Beast Wilds

### Issues Found: None Critical

**Verification Status**: PASS

**Minor Clarifications Needed**:

1. **Condition Severity Terminology**: Design references "3 damage/turn" for bleeding but uses severity values (70, 80). Clarify: Does severity map to damage rate via formula, or are these independent?

2. **Wolf Pack as Companion**: Design says "Recruiting alpha recruits entire pack (3 grey wolves follow)" but max companions is 2. **Clarification**: Wolf pack should be treated as 1 companion unit despite 4 entities.

3. **Gossip Source for Sira Death**: `create_gossip()` requires `source_npc` parameter. When Sira dies, who is the source? Design should clarify if player-witnessed events have special handling.

4. **Echo Instant Knowledge**: Design says Echo learns about abandoned cubs with "delay 0 turns". Clarify if `delay_turns=0` is valid or if Echo uses separate mechanism.

---

## 2. Civilized Remnants

### Issues Found: None Critical

**Verification Status**: PASS

**Clarifications Needed**:

1. **Guardian Ritual Knowledge Source**: Design says "Frozen Reaches lore tablets OR Echo's guidance" but no Echo service is documented. Either remove Echo as option OR document Echo ritual knowledge service in Nexus design.

2. **Refugee Cure Types**: Design says "Find cure for infected refugees" but doesn't specify which cure items satisfy the commitment. Clarify: Only Myconid Cure, or any disease cure?

3. **Sira Gossip + Player Location**: What happens if gossip arrives while player is in same region as Elara but hasn't visited her? Does Elara confront player?

4. **Back Tunnel Accessibility**: Is the back tunnel ONLY accessible while branded, or always accessible (just primarily useful for branded)?

---

## 3. Sunken District

### Issues Found: 1 Timer Trigger

**Verification Status**: ~~PASS with clarification~~ RESOLVED

**~~Issue SD-1: Timer Start Trigger~~ RESOLVED**
- **Location**: Section 3.3, Appendix A.1
- **Problem**: Design says Garrett's timer starts "on_room_entry" but infrastructure only defines `timer_starts: "on_commit"`
- **Resolution**: This is NOT a commitment timer - it's a scheduled event triggered by room entry. Implementation:
  1. Behavior trigger: `on_enter_location("sea_caves")`
  2. Effect: `schedule_event("garrett_death", current_turn + 5, {...})`
  3. Cancellation: When Garrett transitions to `rescued`, call `cancel_scheduled_event("garrett_death")`

  The commitment system tracks promises and trust; Garrett's death is an environmental clock. Added implementation notes to design.

**Clarifications Needed**:

1. **Hope Bonus Mechanics**: Does `hope_bonus` extend the commitment deadline OR the NPC survival condition? Design and infrastructure may interpret this differently.

2. **Cold Spread New Routes**: Design says cold spread creates "new routes" in Sunken District when water freezes. How are new routes created dynamically - location property changes or graph modifications?

3. **Partial Credit Trigger**: For multi-step rescues, is partial credit determined by rescue steps completed, time spent attempting, or explicit metrics?

---

## 4. Fungal Depths

### Issues Found: 2 API + 1 State Machine

**Verification Status**: ~~NEEDS CLARIFICATION~~ RESOLVED

**~~Issue FD-1: Gossip Delivery to Echo via Network~~ RESOLVED**
- **Location**: Section 3.4, lines 440-444
- **Problem**: Design said Spore Mother healed/killed gossip goes to "All fungal creatures, Echo" via spore network
- **API Fact**: `create_network_gossip()` only targets network members (actors with matching property)
- **Resolution**: Updated design to use separate `create_gossip()` call to Echo for major events. Spore network gossip now only targets fungal creatures.

**~~Issue FD-2: Fungal Death Detection Mechanism~~ RESOLVED**
- **Location**: Sections 42, 185, 192, 320
- **Problem**: Design described fungal death detection as both a global flag AND network gossip
- **Resolution**: Removed gossip mechanism. Implemented as "death-mark" - a mystical mark on the player that fungal creatures sense instantly. Sets `has_killed_fungi` flag via behavior trigger. Added Section 3.4.1 documenting this.

**~~Issue FD-3: Spore Mother State Machine Ambiguity~~ RESOLVED**
- **Location**: Lines 158-192
- **Problem**: Notation "hostile/wary → allied" was ambiguous
- **Resolution**: Expanded to explicit individual transitions: `hostile → allied` and `wary → allied` (both triggered by giving heartmoss). Also added `wary → dead` transition.

**Clarifications Needed**:

1. **Spread Specification Incomplete**: No explicit milestones defined for spore_spread. Design says "turn 100" but cross-region doc says "turn 50, 100, 150". Need coordinated specification.

2. **Salamander Light in Deep Roots**: Does salamander companion replace or enhance the lantern requirement?

3. **Sporeling State Machine**: Missing explicit state definition. Do sporelings have own state machine or inherit Mother's state?

4. **Breath-Hold Application**: When does `apply_condition(HELD_BREATH)` get called? Auto on zone entry or only without mask?

5. **has_killed_fungi Flag Setting**: When/how is this flag set? Needs explicit behavior handler.

---

## 5. Frozen Reaches

### Issues Found: None Critical

**Verification Status**: PASS

**Clarifications Needed**:

1. **Telescope Repair Halt Flag**: Design doesn't specify when `observatory_functional` flag is set. Should be set when telescope repair puzzle is completed. Add explicit behavior trigger.

2. **Salamander Death Conditions**: Design includes `dead` state but doesn't specify what triggers it (combat death? forced into water?). Document death conditions and Echo awareness trigger.

3. **Heated Stone Duration**: Design says "~20 turns" but doesn't specify tracking mechanism. Clarify: scheduled event or item flag?

**Positive Notes**:
- ConditionInstance correctly uses game-specific extensions (`progression_rate`, `paused`)
- Temperature zone rates match infrastructure exactly (COLD +5, FREEZING +10, EXTREME_COLD +20)
- Cold spread milestones match game_wide_rules.md exactly

---

## 6. Meridian Nexus

### Issues Found: 1 CRITICAL + 2 State Machine

**Verification Status**: NEEDS RESOLUTION

**~~CRITICAL Issue MN-1: Echo Trust Threshold Mismatch~~ RESOLVED**
- **Location**: Section 1.2, lines 105-110 vs API reference
- **Design says**: Trust -3 to -5 = 5% appearance chance, Trust -6 or below = refuses
- **API said**: Trust <= -3 = refuses (returns 0.0 chance)
- **game_wide_rules.md says**: Trust -3 to -5 = Reluctant (5%), Trust -6 = Refuses
- **Resolution**: Fixed `calculate_echo_chance()` in infrastructure_detailed_design.md to refuse at -6, matching game_wide_rules

**~~Issue MN-2: Waystone State Machine Transitions Unclear~~ RESOLVED**
- **Location**: Section 1.4
- **Problem**: Design didn't specify what triggers state transitions (damaged → partial → repaired)
- **Resolution**: State is derived from `fragments_placed` property. 0=damaged, 1-4=partial, 5=repaired. When player places fragment: increment property, call `transition_state()` if crossing threshold. Added implementation notes to design.

**~~Issue MN-3: Echo State Machine vs Trust Tiers~~ RESOLVED**
- **Location**: Section 1.2, lines 102-104
- **Problem**: Design listed "refusing" as a state alongside dormant, manifesting, etc.
- **Resolution**: Removed "refusing" from states list. Clarified that states describe what Echo is doing when present (dormant, manifesting, communicating, fading, permanent). "Refusing" is not a state - it's the trust <= -6 behavior where appearance probability is 0%.

**Clarifications Needed**:

1. **Recovery Cap Semantics**: API default is `recovery_cap=3` (per-turn), design says `recovery_cap=1` (per-visit). Which interpretation is correct?

2. **Wolf Exclusion Narration**: Who is responsible for narrating wolf boundary behavior (wolves pacing, whining)? Region behavior, companion system, or LLM?

3. **TrustState Field Initialization**: API only initializes `{"current": 0}`, but design requires additional fields. Clarify initialization responsibility.

---

## Summary by Issue Category

### Critical (Blocks Implementation)

| ID | Region | Issue | Resolution |
|----|--------|-------|------------|
| ~~MN-1~~ | ~~Nexus~~ | ~~Echo trust threshold -3 vs -6~~ | ~~RESOLVED: Fixed API to refuse at -6~~ |

### High Priority (Needs Clarification Before Implementation)

| ID | Region | Issue | Resolution |
|----|--------|-------|------------|
| ~~FD-1~~ | ~~Fungal~~ | ~~Echo not in spore network~~ | ~~RESOLVED: Separate gossip to Echo~~ |
| ~~FD-2~~ | ~~Fungal~~ | ~~Flag vs gossip detection~~ | ~~RESOLVED: Death-mark flag, not gossip~~ |
| ~~SD-1~~ | ~~Sunken~~ | ~~Timer trigger on_room_entry~~ | ~~RESOLVED: Scheduled event + cancel~~ |
| ~~MN-2~~ | ~~Nexus~~ | ~~Waystone transitions~~ | ~~RESOLVED: Property-derived state~~ |

### Medium Priority (Design Clarity)

| ID | Region | Issue |
|----|--------|-------|
| ~~FD-3~~ | ~~Fungal~~ | ~~State machine "hostile/wary → allied" notation~~ RESOLVED |
| ~~MN-3~~ | ~~Nexus~~ | ~~Echo states vs trust tiers conflation~~ RESOLVED |
| All | Various | Hope bonus mechanics - CLARIFIED: extends deadline, not survival |
| All | Various | Gossip source for player-witnessed events - CLARIFIED: set flags directly |

### Low Priority (Documentation)

- Wolf pack as single companion unit
- Heated stone duration tracking
- Back tunnel accessibility
- Various narration responsibility questions

---

## ~~Recommended Resolutions~~ All Resolutions Applied

All critical and high-priority issues have been resolved. The following changes were made:

### 1. ✅ Echo Trust Threshold - FIXED
Updated `calculate_echo_chance()` in infrastructure_detailed_design.md to refuse at -6 (not -3).

### 2. ✅ Fungal Death Detection - RESOLVED
Implemented as "death-mark" (Option A). Added Section 3.4.1 to fungal_depths_detailed_design.md documenting the behavior trigger and flag mechanism.

### 3. ✅ Timer Trigger Types - RESOLVED
Room-entry timers use scheduled events + behavior triggers, not the commitment system. Added implementation notes to sunken_district_detailed_design.md.

### 4. ✅ Waystone Implementation - CLARIFIED
State is derived from `fragments_placed` property. Added implementation notes to meridian_nexus_detailed_design.md.

### 5. ✅ State Machine Notation - FIXED
Expanded "hostile/wary → allied" to explicit individual transitions in fungal_depths_detailed_design.md.

### 6. ✅ Echo States - CLARIFIED
Removed "refusing" from Echo state machine. Trust tiers drive appearance probability; states describe what Echo does when present. Updated meridian_nexus_detailed_design.md.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2025-12-11 | All critical/high/medium priority issues resolved. Updated report with resolutions. |
| 1.0 | 2025-12-11 | Initial verification of all 6 regions |
