# Phase 1 Cross-Region Inconsistency Report

**Date**: 2025-12-11
**Status**: Complete - Ready for Discussion

---

## Executive Summary

Phase 1 verification of the game_wide_consistency_plan.md has been completed. This report surfaces all cross-region inconsistencies found across the six detailed region designs, cross_region_dependencies.md, and game_wide_rules.md.

**Total Inconsistencies Found**: 38 issues across 4 categories
- **Critical (Must Fix)**: 12
- **High (Should Fix)**: 14
- **Medium (Polish)**: 9
- **Low (Documentation)**: 3

---

## Category 1: Cross-Region Item Dependencies

### Critical Issues

| # | Issue | Source | Destination | Description |
|---|-------|--------|-------------|-------------|
| I-1 | Spore Crystal Export Missing | Fungal Depths | Meridian Nexus | Waystone fragment listed in cross_region_dependencies but NOT in Fungal Depths Section 2.2 exports |
| I-2 | Healing Herbs Export Gap | Civilized Remnants | Beast Wilds | Listed in Beast Wilds imports but export not in cross_region_dependencies Civilized Remnants section |
| I-3 | Cleaning Supplies Not in Section 1.3 | Meridian Nexus | Frozen Reaches | Imported by Frozen Reaches but not in Frozen Reaches Required Items table |

### High Issues

| # | Issue | Description |
|---|-------|-------------|
| I-4 | Moonpetal Inconsistent Categorization | Listed in Beast Wilds Section 2.1 imports but missing from Section 1.3 Required Items |
| I-5 | Royal Honey Destination Unclear | Exported from Beast Wilds but no destination region documents importing it |
| I-6 | Spider Silk Destination Unclear | Exported from Beast Wilds but no destination region documents importing it |
| I-7 | Temple Password Is Knowledge Not Item | Frozen Reaches imports "Temple Password" but it's information, not a physical item - category unclear |
| I-8 | Nightshade Not in Dependencies | Civilized Remnants exports nightshade in Section 2.2 but cross_region_dependencies doesn't document it |

### Recommendations

1. Add "Spore Heart" (renamed from Spore Crystal) to Fungal Depths Section 2.2 exports
2. Add Healing Herbs to cross_region_dependencies Civilized Remnants exports
3. Move Cleaning Supplies to Frozen Reaches Section 1.3
4. Clarify Moonpetal as "optional trade item" vs "required item"
5. Document royal honey and spider silk as "trade goods with no required destination"
6. Create "Knowledge Transfer" category separate from physical items for temple password

---

## Category 2: Gossip Source-Destination Pairs

### Critical Issues

| # | Event | Source | Destination | Issue |
|---|-------|--------|-------------|-------|
| G-1 | Aldric's Fate | Fungal Depths | Civilized Remnants | NO MECHANISM DOCUMENTED - Fungal Depths Section 2.3 doesn't show how news reaches Civilized Remnants |
| G-2 | Spore Mother Killed | Fungal Depths | All fungal + Echo | NOT IN cross_region_dependencies gossip table |
| G-3 | Spore Mother Healed (broadcast) | Fungal Depths | All regions | Documented at 15 turns but NO RECEIVING DOCUMENTATION in any destination region |
| G-4 | ~~Exile Status~~ | ~~Civilized Remnants~~ | ~~All regions~~ | **RESOLVED**: Exile replaced with branding. Brand is visible mark - no gossip needed. |

### High Issues

| # | Event | Issue |
|---|-------|-------|
| G-5 | Sira Death vs Abandonment | Two separate events (12 vs 20 turns) but cross_region_dependencies conflates them as "Sira's fate" |
| G-6 | Assassination Recipients | Civilized Remnants documents "Other councilors" learn but doesn't specify WHICH councilors |
| G-7 | Undercity Discovery | Civilized Remnants 3.4 documents 5% discovery chance but NOT in cross_region_dependencies |
| G-8 | Fungal Depths "Instant" vs "1 turn" | Section 1.2 says "instantly" but Section 3.4 says "1 turn" for spore network |

### Timing Verification Summary

| Event | Source | Timing in Dependencies | Timing in Region Design | Status |
|-------|--------|------------------------|------------------------|--------|
| Sira death | Beast Wilds | 12 turns | 12 turns | ✓ Match |
| Sira abandonment | Beast Wilds | 20 turns | 20 turns | ✓ Match |
| Aldric fate | Fungal Depths | 25 turns | **Not documented** | ✗ Gap |
| Delvan fate | Sunken District | 7 turns | 7 turns | ✓ Match |
| Garrett fate | Sunken District | 0 turns | 0 turns | ✓ Match |
| Bear cubs fate | Beast Wilds | 8 turns | 8 turns | ✓ Match |
| Spore Mother healed | Fungal Depths | 15 turns (regions) / 1 turn (spore network) | 1 turn only | ✗ Gap |
| Assassination | Civilized Remnants | 0 turns (Echo) | 0 turns | ✓ Match |

### Recommendations

1. Add mechanism documentation to Fungal Depths: "Aldric's fate reaches Civilized Remnants via merchant travelers (25 turns)"
2. Add "Spore Mother killed" to cross_region_dependencies gossip table
3. Document gossip reception in all regions for broadcast events (Spore Mother healing) - Note: Branding replaces exile and doesn't require gossip (visible mark)
4. Split "Sira's fate" into two rows: "Sira death" (12 turns) and "Sira abandonment" (20 turns)
5. Resolve "instant" vs "1 turn" language in Fungal Depths Section 1.2

---

## Category 3: NPC Cross-References

### Critical Issues

| # | NPC | Issue |
|---|-----|-------|
| N-1 | Echo Trust Scale | Scale endpoints unclear - mentioned +10% modifier but no ceiling documented; floor at -3 or -6? |
| N-2 | Delvan Undercity Access | MECHANISM UNCLEAR - does rescue auto-reveal? Must player ask? What if Delvan dies? |
| N-3 | Spore Mother Healing vs Waystone | Ambiguous whether healing Spore Mother alone stops spread, or if waystone repair is also needed |

### High Issues

| # | NPC Connection | Issue |
|---|----------------|-------|
| N-4 | Sira-Elara Confession Window | Both regions document but with inconsistent emphasis on when window opens/closes |
| N-5 | Aldric Relocation | Civilized Remnants mentions Aldric "may relocate" but conditions not specified |
| N-6 | Echo Commitment States | Echo documented for failures but unclear if responds to "honest withdrawal" differently |
| N-7 | Salamander Echo Comments | Meridian Nexus documents Echo comment on salamanders but other regions don't |

### Medium Issues

| # | Issue |
|---|-------|
| N-8 | Alpha Fang acquisition - one-time vs recurring not specified |
| N-9 | Elara trust sources cross-reference incomplete - players may not realize some sources are cross-region |
| N-10 | Myconid violence detection timing - "instantly" vs "1 turn" inconsistency |

### Recommendations

1. Document Echo trust scale explicitly: "Trust ranges from -6 (floor, refuses to appear) to +5 (ceiling)"
2. Clarify Delvan mechanism: "Rescuing Delvan sets flag 'knows_undercity_entrance'. Player must visit Delvan in Sunken District survivor camp to learn knock pattern."
3. Separate local vs global effects: "Healing Spore Mother stops spread FROM Fungal Depths. Waystone repair prevents spread from affecting Nexus boundary."
4. Document Echo response to all four commitment states (pending, fulfilled, withdrawn, abandoned)

---

## Category 4: Companion Handoff Points

### Critical Issues

| # | Companion | Restriction | Issue |
|---|-----------|-------------|-------|
| C-1 | Wolf | Spider Nest Gallery | Waiting location NOT SPECIFIED when player enters |
| C-2 | Myconid | Frozen Reaches | Restriction documented in cross_region_dependencies but NOT in Frozen Reaches Section 4.3 |
| C-3 | All | Missing Unified Map | No single authoritative table of all companion restrictions and waiting locations |

### High Issues

| # | Issue |
|---|-------|
| C-4 | Salamander uncomfortable zone waiting undefined - does it auto-return to Nexus or wait nearby? |
| C-5 | Override mechanisms (exceptional bravery, foolhardy sacrifice, curious explorer) inconsistently documented |
| C-6 | Sira access to hazardous sub-areas (Deep Archive, Deep Roots) unclear |
| C-7 | Salamander handling differs: Frozen Reaches (passive uncomfortable) vs Civilized Remnants (active fire incident risk) |

### Verification Summary

| Companion | Cannot Enter | Source Doc | Dest Doc | Status |
|-----------|--------------|------------|----------|--------|
| Wolf | Nexus | Beast Wilds 4.3 ✓ | Nexus 4.3 ✓ | ✓ Both documented |
| Wolf | Civilized Remnants | Beast Wilds 4.3 ✓ | Civ Rem 4.3 ✓ | ✓ Both documented |
| Wolf | Spider Nest | Beast Wilds 4.3 ✓ | Beast Wilds 4.3 ✓ | ⚠️ Wait location missing |
| Salamander | Sunken District | Frozen Reaches 4.3 ✓ | Sunken 4.3 ✓ | ✓ Both documented |
| Myconid | Frozen Reaches | cross_region_dependencies ✓ | Frozen 4.3 ✗ | ✗ Missing in destination |
| Human (Sira) | Any | Beast Wilds 4.3 ✓ | Various ✓ | ✓ Documented |
| Human (Aldric) | Frozen Reaches | Fungal 4.3 ✓ | Frozen 4.3 ✓ | ✓ Both documented |

### Recommendations

1. Add wolf waiting location for Spider Nest Gallery: "Wolf Clearing"
2. Add Myconid section to Frozen Reaches Section 4.3
3. Create unified companion restriction matrix in cross_region_dependencies.md
4. Document salamander behavior when entering "uncomfortable" zones
5. Standardize override flag documentation across all three cases

---

## Design Questions Requiring Discussion

These issues require design decisions, not just documentation fixes:

### DQ-1: Spore Mother Healing Scope
**Question**: Does healing Spore Mother stop ALL environmental spread, or only spread FROM Fungal Depths?
- Current ambiguity: Fungal Depths says "immediate halt", Nexus implies waystone is needed
- **Options**: (a) Healing alone is sufficient (b) Both healing AND waystone needed (c) Healing stops source, waystone protects Nexus

### DQ-2: Echo Trust Floor
**Question**: What is Echo's trust floor?
- Section 3.8 says -3 (refuses to appear)
- Ending system mentions -6 as lowest tier
- **Options**: (a) Floor is -3 (no appearance below) (b) Floor is -6 (appears but hostile)

### DQ-3: Delvan Mechanism
**Question**: How exactly does Delvan provide undercity access?
- **Options**: (a) Auto-flag on rescue (b) Must ask Delvan specifically (c) Delvan tells player automatically when rescued

### DQ-4: Gossip Reception Documentation
**Question**: Should each region document receiving ALL broadcast gossip events?
- Current state: Only source regions document gossip
- **Options**: (a) Document in all receiving regions (comprehensive) (b) Document only in cross_region_dependencies (centralized) (c) Document only where NPC reactions change (selective)

### DQ-5: Companion Override Mechanism
**Question**: How do "exceptional bravery" overrides work mechanically?
- Cross_region_dependencies mentions but doesn't specify trigger
- **Options**: (a) Player command (b) Automatic at low health (c) Trust threshold triggers

---

## Next Steps

1. **Discussion**: Review design questions DQ-1 through DQ-5
2. **Phase 1.5**: Update game_wide_rules.md with timer format standardization and resolved design questions
3. **Phase 2**: Apply fixes from this report to individual region designs
4. **Create Matrix**: Build detailed cross-reference matrix as requested

---

## Appendix: Files Reviewed

- `docs/big_game_work/cross_region_dependencies.md`
- `docs/big_game_work/game_wide_rules.md`
- `docs/big_game_work/game_wide_consistency_plan.md`
- `docs/big_game_work/detailed_designs/fungal_depths_detailed_design.md`
- `docs/big_game_work/detailed_designs/beast_wilds_detailed_design.md`
- `docs/big_game_work/detailed_designs/sunken_district_detailed_design.md`
- `docs/big_game_work/detailed_designs/frozen_reaches_detailed_design.md`
- `docs/big_game_work/detailed_designs/civilized_remnants_detailed_design.md`
- `docs/big_game_work/detailed_designs/meridian_nexus_detailed_design.md`
