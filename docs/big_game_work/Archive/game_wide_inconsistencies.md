# Game-Wide Inconsistencies Analysis

**Version**: 1.0
**Date**: 2025-12-11
**Purpose**: Document inconsistencies between `game_wide_rules.md`, region detailed designs, and `infrastructure_detailed_design.md` for resolution in Phase 7 Cross-Region Consistency Review.

---

## 1. Timer Value Discrepancies

### 1.1 Commitment Timer Ranges vs Fixed Values

`game_wide_rules.md` uses ranges while region designs use fixed values:

| NPC | game_wide_rules.md | Region Design | Discrepancy |
|-----|-------------------|---------------|-------------|
| Sira | 8-12 turns | 8 turns (Beast Wilds) | Rules say 8-12, design says 8 |
| Aldric | 50-60 turns | 50 turns (Fungal Depths) | Rules say 50-60, design says 50 |
| Bear cubs | 30-35 turns | 30 turns (Beast Wilds) | Rules say 30-35, design says 30 |
| Delvan | 10-13 turns | 10 + 3 hope (Sunken District) | **Consistent** (10 base + 3 hope = 13 max) |

**Question to Resolve**: Do the ranges in `game_wide_rules.md` include hope bonus, or should designs use base values with separate hope bonus?

**Recommendation**: Standardize on the format used in Sunken District (base value + explicit hope bonus). Update `game_wide_rules.md` to clarify:
- Sira: 8 turns base, +4 hope bonus = 12 max
- Aldric: 50 turns base, +10 hope bonus = 60 max
- Bear cubs: 30 turns base, +5 hope bonus = 35 max

---

## 2. Companion Behavior Inconsistencies

### 2.1 Salamander Water Region Wait Behavior

**game_wide_rules.md** (line 187):
> "Salamander: Nexus (if water region) or region entry"

**Region designs**: None of the region designs specify that salamander returns to Nexus when player enters water regions.

**Affected regions**:
- Sunken District (all companions excluded, but salamander wait location not specified)

**Recommendation**: Add explicit salamander behavior to Sunken District design Section 4.3:
```
Salamander Behavior:
- Cannot enter any flooded location (fire extinguishes)
- Wait location: Returns to Nexus via ley line (instant)
- Rejoin: Automatically returns when player exits to non-water region
```

### 2.2 Wolf Cold Tolerance

**game_wide_rules.md** (line 238):
> "can't handle extreme cold"

**Frozen Reaches design**: Documents wolves as:
- "Uncomfortable" in some areas
- "Impossible" in Ice Caves

**Gap**: Which specific Frozen Reaches locations are accessible to wolves? The design has comfort levels but `game_wide_rules.md` says broadly "can't handle extreme cold."

**Recommendation**: Add location-specific wolf restrictions to Frozen Reaches design:
```
Wolf Cold Tolerance:
- Frozen Pass: Uncomfortable (can enter, -1 comfort per 5 turns)
- Ice Caves: Impossible (wolves refuse to enter)
- Temple: Uncomfortable (interior is warmer)
- Salamander Nest: Comfortable (heat from salamanders)
```

### 2.3 Companion Death Scenarios

**game_wide_rules.md** (lines 255-259) proposes:
> "Companion can die from deliberate player action (forcing salamander into water)"
> "Companion can die protecting player ('exceptional bravery' wolf rescue)"

**Region designs**: No region design documents companion death scenarios or consequences.

**Recommendation**: Add companion death scenarios to relevant regions:

**Frozen Reaches**:
```
Salamander Death Scenarios:
- Forcing into water: Salamander extinguishes permanently
- Exposure without shelter: Cannot happen (salamander generates own heat)
- Combat: Salamander can die protecting player from golems
- Consequence: Warm cloak becomes only cold protection option
```

**Beast Wilds**:
```
Wolf Death Scenarios:
- Combat with spiders: Wolves can die in spider gallery
- Forcing into water: Cannot happen (wolves refuse)
- Alpha death: Pack scatters, some become hostile loners
- Consequence: Alpha Fang unavailable, wolf companion path closed
```

---

## 3. Gossip Timing Gaps

### 3.1 Missing Aldric Gossip in Fungal Depths

**game_wide_rules.md** (line 71):
> "Aldric's fate | Fungal Depths | Civilized Remnants | 25 | Scholar's fate becomes known slowly"

**Fungal Depths design**: Does not explicitly document Aldric gossip timing in Section 3.4.

**Recommendation**: Add to Fungal Depths Section 3.4 Gossip Sources:

| Event | Content | Target NPCs | Delay | Confession Window |
|-------|---------|-------------|-------|-------------------|
| Aldric's fate | "Scholar Aldric rescued/died in the depths" | Town NPCs, Elara | 25 turns | N/A |

### 3.2 Confession Window Mechanics

**game_wide_rules.md** (lines 80-91) documents detailed confession window mechanics for Sira-Elara connection.

**Civilized Remnants design**: Documents gossip timing (12-20 turns) but not the full confession window mechanics.

**Status**: Civilized Remnants Section 3.4 has the timing but could be more explicit about the "visited but didn't confess" scenario (-4 trust).

---

## 4. Environmental Spread Timeline Cross-References

### 4.1 Spore Spread Timeline

**game_wide_rules.md** (line 142):
> "Turn 50: Beast Wilds affected. Turn 100: Town gate checks. Turn 150: Town NPCs infected."

**Fungal Depths design**: References `global_turn` triggers but doesn't specify exact turn numbers for spread effects.

**infrastructure_detailed_design.md**: Should contain authoritative spread timeline.

**Recommendation**: Verify spread timelines are documented in exactly one place (infrastructure) and cross-referenced elsewhere. Add to Fungal Depths Section 2.4:

| Effect | Direction | Trigger | Timeline |
|--------|-----------|---------|----------|
| Spore spread | To Beast Wilds | Spore Mother not healed | Turn 50 |
| Spore spread | To Civilized Remnants gate | Spore Mother not healed | Turn 100 |
| Spore spread | To Civilized Remnants NPCs | Spore Mother not healed | Turn 150 |

### 4.2 Cold Spread Timeline

**game_wide_rules.md** (line 143):
> "Turn 75: Beast Wilds high ground cold. Turn 125: Nexus boundary cold. Turn 175: Sunken District water freezes."

**Frozen Reaches design**: Should reference these timelines but currently doesn't specify exact turn numbers.

**Recommendation**: Add cold spread timeline to Frozen Reaches Section 2.4.

---

## 5. Infrastructure System Coverage Gaps

### 5.1 Partial Credit Evidence Checking

**game_wide_rules.md** (lines 24-43) documents detailed partial credit evidence system:
- Region visited (required)
- Relevant item acquired (strong)
- In transit at expiration (strong)
- Competing commitment fulfilled (moderate)
- Time constraint clear (automatic)

**infrastructure_detailed_design.md**: Should document how this is implemented.

**Question**: Is partial credit evidence checking documented in infrastructure? If not, add it.

### 5.2 Commitment Overlap Priority

**game_wide_rules.md** (lines 9-19) documents processing order for overlapping commitments:
1. By timer expiration (earlier first)
2. By severity (death > major harm > minor harm)
3. By region encounter order

**infrastructure_detailed_design.md**: Should document this processing order.

**Question**: Is commitment overlap priority documented in infrastructure? If not, add it.

### 5.3 Confession Window Mechanics

**game_wide_rules.md** (lines 80-91) documents confession windows with specific trust penalties:
- Confession before gossip: -2 trust, recovery possible
- Confession with context: -1.5 trust
- Discovery via gossip: -3 trust, permanent
- Lie by omission: -4 trust

**infrastructure_detailed_design.md**: Should document the confession window system as a reusable pattern.

**Question**: Is confession window pattern documented in infrastructure? If not, consider whether it should be generalized or remain Sira-Elara specific.

---

## 6. Trust System Clarifications

### 6.1 Echo Trust vs NPC Trust Scales

**game_wide_rules.md** documents Echo trust sources:
- Save major NPC: +1
- Heal Spore Mother: +1
- Fulfill commitment: +0.5

**Civilized Remnants design** documents Elara trust sources:
- healed_spore_mother: +2
- helped_sira: +2
- saved_survivor: +1 each

**Not an inconsistency**: These are different trust systems (Echo vs Elara) with different scales. However, the overlap in triggering actions (healed_spore_mother affects both) could be confusing.

**Recommendation**: Add clarifying note to both systems:
> "Note: This trust system is independent of Echo trust. The same action may affect multiple trust relationships with different values."

---

## 7. Ending System Verification

### 7.1 Ending Tier Consistency

**game_wide_rules.md** (lines 297-305) documents ending tiers:

| Echo Trust | Waystone Complete | Ending Name |
|------------|-------------------|-------------|
| 5+ | Yes | Triumphant |
| 3-4 | Yes | Successful |
| 0-2 | Yes | Bittersweet |
| -1 to -2 | Yes | Hollow Victory |
| -3 to -5 | Yes | Pyrrhic |
| -6 or below | Yes | Pyrrhic |

**Meridian Nexus design** (Section 3.6): Documents identical tiers.

**Status**: Consistent.

### 7.2 Permanent Locks

**game_wide_rules.md** (lines 309-313):
- Triumphant ending: Locked after ANY assassination
- Advanced herbalism: Lost if Elara killed
- Hero status: Impossible after assassination discovery
- Some council quests: Unavailable after exile

**Region designs**: All permanent locks documented in Section 3.8 of relevant regions.

**Status**: Consistent, but verify cross-region:
- Assassination locks Triumphant (documented in Nexus and Civilized Remnants)
- Elara death locks Advanced Herbalism (documented in Civilized Remnants)
- Exile effects documented in Civilized Remnants

---

## 8. Cross-Document Reference Matrix

### 8.1 Where Each System Should Be Documented

| System | Authoritative Source | Cross-References |
|--------|---------------------|------------------|
| Commitment timers | Region designs (Section 3.3) | game_wide_rules.md (summary) |
| Gossip timing | Region designs (Section 3.4) | game_wide_rules.md (summary) |
| Environmental spreads | infrastructure_detailed_design.md | Region Section 2.4, game_wide_rules.md |
| Trust systems | infrastructure_detailed_design.md | Region appendices |
| Ending system | game_wide_rules.md | Meridian Nexus Section 3.6 |
| Companion restrictions | cross_region_dependencies.md | Region Section 4.3 |
| Permanent consequences | Region designs (Section 3.8) | game_wide_rules.md (summary) |

### 8.2 Documents Needing Updates

| Document | Updates Needed |
|----------|---------------|
| game_wide_rules.md | Clarify timer ranges vs base+hope format |
| Fungal Depths design | Add Aldric gossip timing, add spread timeline |
| Frozen Reaches design | Add wolf zone restrictions, add spread timeline |
| Sunken District design | Add salamander wait behavior |
| Beast Wilds design | Add companion death scenarios |
| infrastructure_detailed_design.md | Verify partial credit, overlap priority, confession window systems |

---

## 9. Priority for Phase 7 Resolution

### High Priority (blocks consistency)
1. Timer format standardization (ranges vs base+hope)
2. Missing gossip timings (Aldric)
3. Environmental spread timelines in region designs

### Medium Priority (improves clarity)
4. Companion death scenarios
5. Salamander water region behavior
6. Wolf cold zone specifics
7. Confession window mechanics in infrastructure

### Low Priority (documentation polish)
8. Trust system clarification notes
9. Cross-document reference verification

---

## 10. Verification Checklist for Phase 7

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
