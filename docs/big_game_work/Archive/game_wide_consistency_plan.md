# Game-Wide Consistency Review Plan

**Version**: 1.0
**Date**: 2025-12-11
**Purpose**: Phased plan to ensure consistency across all region designs, game_wide_rules.md, and infrastructure_detailed_design.md.

---

## Overview

This plan addresses inconsistencies documented in `game_wide_inconsistencies.md` through a systematic phased review. The phases are ordered to:
1. Surface all region-to-region inconsistencies first
2. Update game_wide_rules.md to resolve known issues before cross-checking
3. Verify region-to-rules consistency
4. Identify infrastructure gaps
5. Update infrastructure to support all documented patterns
6. Perform final verification

---

## Phase 1: Region-to-Region Consistency

**Goal**: Ensure all region designs are internally consistent with each other.

### 1.1 Cross-Region Item Dependencies

Verify that items referenced in one region are properly documented in their source region:

| Item | Source Region | Destination Region | Verify |
|------|---------------|-------------------|--------|
| Healing herbs | Civilized Remnants | Beast Wilds | [ ] Source Section 1.2 |
| Ice crystal | Frozen Reaches | Fungal Depths | [ ] Source Section 1.2 |
| Cleaning supplies | Meridian Nexus | Frozen Reaches | [ ] Source Section 1.2 |
| Temple password fragments | Nexus + Frozen Reaches | Frozen Reaches | [ ] Both source sections |
| Animator crystal | Meridian Nexus | Civilized Remnants | [ ] Source Section 1.2 |
| Rare flowers | Multiple | Beast Wilds | [ ] All source sections |

### 1.2 Gossip Source-Destination Pairs

Verify gossip is documented in both source and destination regions:

| Event | Source Region | Destination Region | Verify Source 3.4 | Verify Dest 3.4 |
|-------|---------------|-------------------|-------------------|-----------------|
| Sira's fate | Beast Wilds | Civilized Remnants (Elara) | [ ] | [ ] |
| Aldric's fate | Fungal Depths | Civilized Remnants | [ ] | [ ] |
| Delvan's fate | Sunken District | Civilized Remnants (Undercity) | [ ] | [ ] |
| Spore Mother healed | Fungal Depths | All regions | [ ] | [ ] |
| Bear cubs fate | Beast Wilds | Beast Wilds (Sira) | [ ] | [ ] |
| Garrett fate | Sunken District | Sunken District (Camp) | [ ] | [ ] |

### 1.3 NPC Cross-References

Verify NPCs mentioned across regions are consistently documented:

| NPC | Home Region | Mentioned In | Verify Consistency |
|-----|-------------|--------------|-------------------|
| Sira | Beast Wilds | Civilized Remnants (Elara connection) | [ ] |
| Elara | Civilized Remnants | Beast Wilds (Sira connection) | [ ] |
| Aldric | Fungal Depths | Civilized Remnants (scholar references) | [ ] |
| Echo | Meridian Nexus | All regions (trust system) | [ ] |

### 1.4 Companion Handoff Points

Verify companion behavior at region boundaries is consistent:

| Companion | Cannot Enter | Wait Location | Documented In |
|-----------|--------------|---------------|---------------|
| Wolf pack | Meridian Nexus, Sunken District | Region entry | [ ] Beast Wilds, [ ] Nexus |
| Salamander | Sunken District (water) | Nexus | [ ] Frozen Reaches, [ ] Sunken District |
| Sira | Fungal Depths (optional) | Camp | [ ] Beast Wilds, [ ] Fungal Depths |

### 1.5 Deliverables

- [ ] Updated Section 8.3 in each region design with verified cross-references
- [ ] List of newly discovered inconsistencies (add to game_wide_inconsistencies.md)

---

## Phase 1.5: Update game_wide_rules.md

**Goal**: Resolve known inconsistencies in game_wide_rules.md before cross-checking regions against it.

### 1.5.1 Timer Format Standardization

Update all timer references to use base+hope format:

| NPC | Current Format | Updated Format |
|-----|----------------|----------------|
| Sira | "8-12 turns" | "8 turns base, +4 hope bonus = 12 max" |
| Aldric | "50-60 turns" | "50 turns base, +10 hope bonus = 60 max" |
| Bear cubs | "30-35 turns" | "30 turns base, +5 hope bonus = 35 max" |
| Delvan | "10-13 turns" | Keep as is (already explicit) |

### 1.5.2 Add Missing Documentation

Add documentation for systems currently implied but not explicit:

- [ ] Companion death scenarios and consequences
- [ ] Salamander water-region wait behavior
- [ ] Wolf cold tolerance zone specifics
- [ ] Partial credit evidence checking mechanics

### 1.5.3 Clarify Ambiguous Rules

- [ ] Echo trust vs NPC trust scales (add clarifying note)
- [ ] Confession window applicability (Sira-Elara specific vs general pattern)

### 1.5.4 Incorporate Phase 1 Findings

- [ ] Add any new inconsistencies discovered in Phase 1 to game_wide_rules.md

### 1.5.5 Deliverables

- [ ] Updated game_wide_rules.md with standardized formats
- [ ] Updated game_wide_rules.md with new documentation sections
- [ ] Version bump to v1.4

---

## Phase 2: Region-to-Rules Consistency

**Goal**: Verify each region design is consistent with the updated game_wide_rules.md.

### 2.1 Commitment Timer Verification

For each region, verify commitment timers match game_wide_rules.md:

| Region | Commitments to Verify |
|--------|----------------------|
| Beast Wilds | [ ] Sira (8+4), [ ] Bear cubs (30+5) |
| Fungal Depths | [ ] Aldric (50+10) |
| Sunken District | [ ] Garrett (5+0), [ ] Delvan (10+3) |
| Civilized Remnants | [ ] Guardian repair (no timer) |
| Frozen Reaches | [ ] (no timed commitments) |
| Meridian Nexus | [ ] (no timed commitments) |

### 2.2 Gossip Timing Verification

For each region, verify gossip timings match game_wide_rules.md:

| Region | Gossip Events to Verify |
|--------|------------------------|
| Beast Wilds | [ ] Sira fate (12/20 turns) |
| Fungal Depths | [ ] Aldric fate (25 turns), [ ] Spore Mother healed (15 turns) |
| Sunken District | [ ] Delvan fate (7 turns), [ ] Garrett fate (0 turns) |
| Civilized Remnants | [ ] Assassination (0-5 turns), [ ] Exile (18 turns) |

### 2.3 Environmental Spread Timeline Verification

Verify spread timelines are documented in source regions:

| Spread | Source Region | Verify Section 2.4 |
|--------|---------------|-------------------|
| Spore spread | Fungal Depths | [ ] Turn 50/100/150 documented |
| Cold spread | Frozen Reaches | [ ] Turn 75/125/175 documented |

### 2.4 Companion Behavior Verification

Verify companion restrictions match game_wide_rules.md:

| Companion | Restriction | Region Section 4.3 |
|-----------|-------------|-------------------|
| Wolf | Can't enter Nexus | [ ] Documented |
| Wolf | Can't swim | [ ] Documented |
| Wolf | Can't handle extreme cold | [ ] Documented |
| Salamander | Can't enter water regions | [ ] Documented |
| Salamander | Provides cold immunity | [ ] Documented |

### 2.5 Deliverables

- [ ] Verified consistency checklist (all items above)
- [ ] Updates to region designs where inconsistencies found
- [ ] Updates to game_wide_rules.md if region designs reveal missing rules

---

## Phase 3: Infrastructure Gap Analysis

**Goal**: Identify which systems documented in game_wide_rules.md and region designs need infrastructure support.

### 3.1 Systems Requiring Infrastructure

Review infrastructure_detailed_design.md for coverage of:

| System | game_wide_rules.md Reference | Infrastructure Status |
|--------|------------------------------|----------------------|
| Commitment overlap priority | Lines 9-19 | [ ] Documented / [ ] Gap |
| Partial credit evidence | Lines 24-43 | [ ] Documented / [ ] Gap |
| Confession window mechanics | Lines 80-91 | [ ] Documented / [ ] Gap |
| Environmental spread timelines | Lines 140-149 | [ ] Documented / [ ] Gap |
| Trust recovery limits | Lines 119-121 | [ ] Documented / [ ] Gap |
| Echo trust floor (-6) | Lines 271-275 | [ ] Documented / [ ] Gap |
| Companion wait behavior | Lines 184-188 | [ ] Documented / [ ] Gap |
| Multi-companion interactions | Lines 192-197 | [ ] Documented / [ ] Gap |

### 3.2 Region-Specific Infrastructure Needs

For each region, identify infrastructure patterns used:

| Region | Infrastructure Patterns Used |
|--------|------------------------------|
| Beast Wilds | CommitmentConfig, GossipConfig, CompanionConfig |
| Fungal Depths | CommitmentConfig, EnvironmentalSpread, GossipConfig |
| Sunken District | CommitmentConfig (tight overlap), HazardZone |
| Civilized Remnants | ReputationSystem, AssassinationSystem, ExileSystem |
| Frozen Reaches | EnvironmentalSpread, CompanionConfig |
| Meridian Nexus | EchoTrust, WaystoneProgress, EndingSystem |

### 3.3 Deliverables

- [ ] Gap analysis document listing all undocumented infrastructure patterns
- [ ] Priority ranking for infrastructure updates

---

## Phase 4: Infrastructure Updates

**Goal**: Update infrastructure_detailed_design.md to support all documented patterns.

### 4.1 High Priority Updates

Systems that block consistency verification:

- [ ] Commitment overlap priority processing order
- [ ] Partial credit evidence checking mechanics
- [ ] Environmental spread timeline authoritative source

### 4.2 Medium Priority Updates

Systems that improve clarity:

- [ ] Confession window pattern (generalized or Sira-Elara specific)
- [ ] Companion death scenario handling
- [ ] Multi-companion interaction rules

### 4.3 Low Priority Updates

Documentation polish:

- [ ] Trust system scale clarification
- [ ] Cross-document reference matrix

### 4.4 Deliverables

- [ ] Updated infrastructure_detailed_design.md
- [ ] Version bump with changelog

---

## Phase 5: Final Cross-Check

**Goal**: Verify all documents are consistent after updates.

### 5.1 Document Chain Verification

Verify authoritative source → cross-reference pattern:

| System | Authoritative Source | Cross-References | Verified |
|--------|---------------------|------------------|----------|
| Commitment timers | Region Section 3.3 | game_wide_rules.md | [ ] |
| Gossip timing | Region Section 3.4 | game_wide_rules.md | [ ] |
| Environmental spreads | infrastructure | Region 2.4, game_wide_rules.md | [ ] |
| Trust systems | infrastructure | Region appendices | [ ] |
| Ending system | game_wide_rules.md | Nexus Section 3.6 | [ ] |
| Companion restrictions | cross_region_dependencies.md | Region Section 4.3 | [ ] |
| Permanent consequences | Region Section 3.8 | game_wide_rules.md | [ ] |

### 5.2 Complete Verification Checklist

Run through all items from game_wide_inconsistencies.md Section 10:

- [ ] Timer values consistent between game_wide_rules.md and all region designs
- [ ] All gossip timings documented in both source and destination regions
- [ ] Environmental spread timelines documented in source regions
- [ ] Companion death scenarios documented in relevant regions
- [ ] Salamander water behavior documented
- [ ] Wolf cold tolerance zones specified
- [ ] Partial credit system in infrastructure
- [ ] Commitment overlap priority in infrastructure
- [ ] Confession window pattern documented or noted as Sira-Elara specific
- [ ] All permanent consequences cross-referenced correctly

### 5.3 Deliverables

- [ ] Final verification report
- [ ] Updated game_wide_inconsistencies.md marking all items resolved
- [ ] Close-out summary

---

## Execution Notes

### Phase Dependencies

```
Phase 1 ─────────────────────────────────────┐
                                             ↓
Phase 1.5 (update rules based on Phase 1) ───┐
                                             ↓
Phase 2 (verify regions against rules) ──────┐
                                             ↓
Phase 3 (identify infrastructure gaps) ──────┐
                                             ↓
Phase 4 (update infrastructure) ─────────────┐
                                             ↓
Phase 5 (final verification) ────────────────┘
```

### Estimated Scope

| Phase | Documents Affected | Estimated Changes |
|-------|-------------------|-------------------|
| 1 | 6 region designs | Section 8.3 updates |
| 1.5 | game_wide_rules.md | Timer formats, new sections |
| 2 | 6 region designs, game_wide_rules.md | Minor corrections |
| 3 | Analysis only | No changes |
| 4 | infrastructure_detailed_design.md | Multiple new sections |
| 5 | All documents | Verification only |

### Success Criteria

- All items in game_wide_inconsistencies.md Section 10 checklist marked complete
- No cross-references point to missing documentation
- Each system has exactly one authoritative source
- All region designs pass Section 8.3 Cross-Region Verification

---

## Version History

- v1.0: Initial plan based on game_wide_inconsistencies.md analysis
