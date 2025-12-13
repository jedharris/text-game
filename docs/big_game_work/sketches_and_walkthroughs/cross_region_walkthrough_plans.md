# Cross-Region Walkthrough Plans

## Purpose

These three walkthroughs are designed to stress-test the cross-region gameplay, specifically examining:

1. How item and NPC dependencies flow between regions
2. How companion restrictions create meaningful choices
3. How commitment consequences spread through the NPC network
4. How the design principles hold up under realistic play patterns

Each walkthrough follows a different player archetype with distinct priorities, revealing different aspects of the design.

---

## Walkthrough A: The Commitment Cascade

### Player Archetype
A well-intentioned but overcommitted player who makes promises faster than they can keep them. Tests the commitment system under stress.

### Focus Areas
- Commitment spreading and consequence propagation
- The confession vs. discovery mechanic
- Echo trust dynamics
- "Hope extends survival" edge cases

### Route

**Phase 1: Fungal Depths (Turns 1-15)**
- Meet Aldric, commit to finding silvermoss ("I'll help you")
- Explore Luminous Grotto, find silvermoss but DON'T give it yet
- Meet Myconids, learn about Spore Mother's illness
- Commit to Spore Mother ("I'll find the heartmoss")
- Leave with two active commitments, neither fulfilled

**Phase 2: Beast Wilds (Turns 16-35)**
- Meet injured Sira, commit to helping ("I'll get you to a healer")
- Discover bear cubs are sick, commit to helping ("I'll find medicine")
- Start wolf domestication (partial)
- Leave with FOUR active commitments total

**Phase 3: Sunken District (Turns 36-50)**
- Learn basic swimming from Jek
- Discover Garrett drowning, commit to rescue
- Discover Delvan trapped, commit to rescue
- Attempt dual rescue (likely fail due to timing)
- SIX commitments, first likely failure

**Phase 4: Consequence Cascade (Turns 51-80)**
- Return to Beast Wilds - how are Sira and cubs?
- Return to Fungal Depths - how is Aldric?
- Check Echo in Nexus - what does trust look like?
- Test confession vs. discovery with Elara about Sira

### Key Questions to Explore

| ID | Question | Tests Principle |
|----|----------|-----------------|
| CRA-1 | When player has multiple dying NPCs, which death triggers Echo commentary first? | Commitment tracking |
| CRA-2 | If player confesses to Elara about Sira BEFORE Elara discovers, does -2 trust apply correctly? | Confession vs. discovery |
| CRA-3 | Does Echo trust compound multiple abandonments (-1 each) or is there a cap? | Echo trust recovery |
| CRA-4 | If Aldric dies while player is saving Garrett, does "tried to help Garrett" mitigate Aldric abandonment? | Partial credit for trying |
| CRA-5 | Can player recover from -3 Echo trust through healing deeds? What's the pace? | Trust recovery mechanics |
| CRA-6 | Do NPCs who learn of broken promises remember permanently or does time heal? | Consequence persistence |

### Expected Discoveries
- The commitment system needs clear priority rules for overlapping timers
- Partial credit for trying may need explicit handling
- Echo trust recovery rate needs verification
- NPC gossip timing (how fast does Elara learn about Sira?) needs definition

---

## Walkthrough B: The Companion Journey

### Player Archetype
A player focused on collecting and using companions, testing the restriction system across the entire map.

### Focus Areas
- Companion restrictions at region boundaries
- Companion benefits in different contexts
- Companion-gated content alternatives
- Companion interactions with NPCs

### Route

**Phase 1: Befriend Steam Salamander (Turns 1-20)**
- Start in Frozen Reaches (challenging but possible)
- Find Hot Springs quickly (survival)
- Befriend salamanders with fire gifts
- Get salamander companion
- Test: Can salamander enter Nexus? (Yes - wards don't block fire elementals)

**Phase 2: Test Salamander Restrictions (Turns 21-40)**
- Bring salamander to Beast Wilds
  - Test: How do wolves react to fire creature?
  - Test: Does salamander help or hinder bear cub situation?
- Attempt to bring salamander to Sunken District
  - Test: What happens at the boundary? Refusal dialog?
  - Test: If player insists, does salamander die or just refuse?
- Bring salamander to Civilized Remnants
  - Test: Guard reaction? NPC fear?
  - Test: Reputation penalty (-1)? Duration?

**Phase 3: Befriend Wolf Pack (Turns 41-60)**
- Leave salamander somewhere safe
- Feed wolves repeatedly
- Achieve companion status
- Test: Can wolf and salamander coexist as dual companions?

**Phase 4: Test Wolf Restrictions (Turns 61-80)**
- Attempt to bring wolves to Civilized Remnants
  - Test: Guard attack? Can player vouch?
  - Test: Is there any way to bring wolves in?
- Bring wolves to Nexus boundary
  - Test: Ward repulsion description?
- Bring wolves to Sunken District
  - Test: "Uncomfortable" effects? Will they enter water?

**Phase 5: Companion Synergy (Turns 81-100)**
- Try Fungal Depths with wolf pack
  - Test: Do wolves get infected? Can they navigate spores?
- Try Frozen Reaches with wolves
  - Test: Do wolves tolerate cold? Help with golems?
- Achieve multiple companions, test management

### Key Questions to Explore

| ID | Question | Tests Principle |
|----|----------|-----------------|
| CRB-1 | When salamander can't enter Sunken District, where does it wait? Does it return automatically when player exits? | Companion waiting behavior |
| CRB-2 | Can wolf companion fight alongside player against spiders? Does this bypass territorial avoidance? | Combat vs. restriction |
| CRB-3 | If player has salamander companion, does hypothermia system work differently? (Should provide immunity) | Companion benefit stacking |
| CRB-4 | Do NPCs remember companion incidents? (Salamander burns something = permanent reputation loss?) | Consequence persistence |
| CRB-5 | What happens if wolf companion kills an NPC the player was trying to befriend? | Companion agency |
| CRB-6 | Can player have wolf AND salamander simultaneously, or does one require dismissing the other? | Multiple companion rules |
| CRB-7 | If wolves won't enter spider gallery, is spider silk still obtainable? What's the alternative path? | Companion-gated alternatives |

### Expected Discoveries
- Companion waiting/reuniting mechanics need specification
- Multiple companion rules need clarity
- Companion environmental immunity (salamander vs. cold) needs verification
- Alternative paths for companion-gated content should exist but may be underdeveloped

---

## Walkthrough C: The Dark Path

### Player Archetype
A player testing the limits of "dark paths available but with massive consequences." Deliberately antagonistic choices.

### Focus Areas
- Assassination consequences and Echo awareness
- Exile and undercity gameplay
- Violence closing doors permanently
- Recovery (or impossibility thereof) from dark choices

### Route

**Phase 1: Establish Baseline (Turns 1-20)**
- Visit Civilized Remnants first
- Build some positive reputation (+2)
- Learn undercity exists through Vex
- Access undercity, note services available

**Phase 2: First Dark Choice - Minor Violence (Turns 21-35)**
- Kill Spider Queen in Beast Wilds (violence without moral weight)
- Kill bee swarm for honey (destroys renewable resource)
- Test: Does Echo comment on these? Are they truly "neutral" violence?

**Phase 3: Second Dark Choice - Assassination (Turns 36-50)**
- Contract Shadow to assassinate Councilor Hurst
- Test: 20% discovery rate - run simulation multiple times?
- Test: If discovered - immediate exile process?
- Test: If undiscovered - Echo still knows?
- Test: Can player still access town through undercity?

**Phase 4: Consequence Cascade (Turns 51-70)**
- Visit Nexus after assassination
  - Test: Echo trust penalty (-2) applied?
  - Test: Echo dialog references murder?
  - Test: Can Echo trust ever recover from assassination?
- Return to Civilized Remnants (via undercity)
  - Test: Exile gameplay - what's accessible?
  - Test: Can exiled player still get Town Seal?
  - Test: Are certain NPCs still accessible?

**Phase 5: Can Anything Be Saved? (Turns 71-100)**
- Attempt to recover reputation
  - Test: What actions restore exile status?
  - Test: How long does recovery take?
- Test waystone completion
  - Test: Can dark-path player complete the game?
  - Test: What ending does Echo provide?

### Key Questions to Explore

| ID | Question | Tests Principle |
|----|----------|-----------------|
| CRC-1 | Does killing the Spore Mother (not healing her) trigger Echo commentary? | Violence consequences |
| CRC-2 | If assassination is undiscovered by NPCs, does Echo still confront player? | Echo omniscience |
| CRC-3 | Can exiled player get Town Seal through undercity? (Alternative path to waystone) | Dark path completion |
| CRC-4 | What's the minimum Echo trust to complete waystone repair? | Trust floor for endings |
| CRC-5 | If player kills Aldric directly (not abandons), how is this different from abandonment? | Direct vs. indirect harm |
| CRC-6 | Can player use assassination to "solve" council dilemmas? What are consequences? | Dark problem-solving |
| CRC-7 | If player is exiled, can they still access healing from Elara (through undercity)? | Exile access rules |
| CRC-8 | Does Echo ever refuse to help with waystone repair, or just provide worse ending? | Hard gates vs. soft consequences |

### Expected Discoveries
- Exile gameplay loop needs fuller specification
- Alternative paths for Town Seal if exiled need verification
- Echo's hard limits (if any) need definition
- "Dark endings" content needs specification
- Recovery mechanics from worst states need clarity

---

## Sketch Map Update Recommendations

Based on planning these walkthroughs, I recommend the following updates to the sketches:

### High Priority Updates (Should Do Before Walkthroughs)

| Sketch | Update Needed | Rationale |
|--------|---------------|-----------|
| **All Sketches** | Add `commitment_timer` fields with explicit turn counts | Walkthrough A requires precise timer overlaps |
| **beast_wilds_sketch.json** | Define Sira's death timer more precisely (currently "~8 turns") | Need exact values for commitment cascade testing |
| **sunken_district_sketch.json** | Define when Garrett's timer starts (first sight? room entry?) | Critical for dual rescue analysis |
| **civilized_remnants_sketch.json** | Add exile gameplay section with accessible locations/services | Walkthrough C needs this detail |
| **meridian_nexus_sketch.json** | Define minimum Echo trust for waystone completion | Can dark-path player still win? |

### Medium Priority Updates (Would Improve Walkthroughs)

| Sketch | Update Needed | Rationale |
|--------|---------------|-----------|
| **All Sketches** | Add companion_behavior section for each region | Walkthrough B needs systematic companion rules |
| **civilized_remnants_sketch.json** | Add assassination discovery consequences in more detail | Walkthrough C dark path |
| **beast_wilds_sketch.json** | Define wolf behavior toward other companions (salamander, etc.) | Multi-companion scenarios |
| **frozen_reaches_sketch.json** | Clarify salamander waiting behavior when blocked | Companion journey needs this |
| **cross_region_dependencies.md** | Add gossip timing (how many turns until Elara learns about Sira) | Confession vs. discovery timing |

### Low Priority Updates (Nice to Have)

| Sketch | Update Needed | Rationale |
|--------|---------------|-----------|
| **meridian_nexus_sketch.json** | Add dark ending content (what happens if Echo trust very low?) | Walkthrough C endgame |
| **All Sketches** | Add partial_credit mechanics for "tried but failed" scenarios | More nuanced commitment handling |
| **beast_wilds_sketch.json** | Define what happens if wolf pack and spider nest coexist | Edge case for companion journey |

---

## Recommended Order of Work

1. **Update sketches with High Priority items** (estimated: 1-2 hours)
2. **Run Walkthrough A (Commitment Cascade)** - most likely to reveal systemic issues
3. **Update sketches based on Walkthrough A findings**
4. **Run Walkthrough B (Companion Journey)** - will reveal boundary behavior gaps
5. **Update sketches based on Walkthrough B findings**
6. **Run Walkthrough C (Dark Path)** - will reveal consequence depth gaps
7. **Final sketch updates and cross_region_dependencies.md revision**

---

## Success Criteria

Each walkthrough should produce:

1. **Design Inputs table** (concrete decisions made during walkthrough)
2. **Questions table** (ambiguities requiring resolution)
3. **Pattern validations** (which principles held, which broke)
4. **Sketch update recommendations** (specific changes needed)

A successful cross-region walkthrough phase will result in:
- All High Priority sketch updates completed
- Clear rules for commitment timer overlaps
- Explicit companion boundary behavior
- Defined exile gameplay loop
- Echo trust minimum and recovery mechanics verified
- Confidence that the game can be completed via multiple paths (including dark path with consequences)

---

## Notes on Methodology

These walkthroughs differ from region walkthroughs in key ways:

1. **Focus on transitions**: Most interesting moments happen at region boundaries
2. **Multiple saves**: May need to branch at key decision points to test alternatives
3. **Turn counting**: Precise turn counts matter more for timer interactions
4. **NPC tracking**: Need to track multiple NPCs across regions simultaneously
5. **State complexity**: Player state becomes complex (multiple companions, multiple commitments, reputation in multiple factions)

The goal is not to "play through" but to **stress-test the design** at its most complex interactions.

---

## Completed Walkthroughs

All three primary walkthroughs (A, B, C) have been completed. See:
- [cross_region_walkthrough_A_commitment_cascade.md](cross_region_walkthrough_A_commitment_cascade.md)
- [cross_region_walkthrough_B_companion_journey.md](cross_region_walkthrough_B_companion_journey.md)
- [cross_region_walkthrough_C_dark_path.md](cross_region_walkthrough_C_dark_path.md)

Key findings have been consolidated into [game_wide_rules.md](game_wide_rules.md).

---

## Deferred Walkthroughs

The following walkthroughs were identified as potentially valuable but deferred in favor of moving to detailed design. They can be revisited after detailed design if gaps surface, or modeled using the detailed design specifications.

### D: Environmental Spread Scenario (Deferred - Medium Value)

**Purpose**: Test what happens if player ignores Spore Mother and telescope, letting both spreads progress over 150+ turns.

**Why Deferred**:
- Environmental spreads are background systems operating on long timelines
- Spread consequences depend heavily on design specifics that detailed design will clarify
- Can be modeled more efficiently once detailed design specifies exact spread mechanics
- Unlikely to reveal new systemic issues beyond timing/number adjustments

**What It Would Test**:
- Spore spread timeline: Turn 50 (Beast Wilds affected) → Turn 100 (Town gate checks) → Turn 150 (Town NPCs infected)
- Cold spread timeline: Turn 75 (Beast Wilds high ground cold) → Turn 125 (Nexus boundary cold) → Turn 175 (Sunken District water freezes)
- Spread interactions: What happens if both progress simultaneously?
- Late remediation: Can player still heal Spore Mother at turn 140? Does it reverse damage?
- NPC survival: Which NPCs die from spread effects? Are some immune?

**When to Revisit**: After detailed design specifies spread mechanics, if timeline numbers seem arbitrary or consequences unclear.

### E: NPC Persistence/Relocation Scenario (Deferred - Medium Value)

**Purpose**: Track NPC state changes across a full game - Aldric moving to town, Sira's different states, companion NPCs, etc.

**Why Deferred**:
- NPC state tracking gaps are more likely to surface during detailed design
- Individual NPC arcs were tested within region walkthroughs
- Cross-region NPC movement (Aldric to town) is a single well-defined transition
- Can be verified as part of detailed design rather than requiring separate walkthrough

**What It Would Test**:
- Aldric relocation: If saved, does he appear in Civilized Remnants? What services?
- Sira states: Companion vs. rescued-but-independent vs. dead - how does each affect other NPCs?
- Companion NPC tracking: Do wolf pack members persist? Can individual wolves die?
- NPC knowledge updates: When Elara learns about Sira, how does her dialog change?
- Cross-save consistency: Are all NPC states properly saved/loaded?

**When to Revisit**: If detailed design reveals gaps in NPC state machine definitions or cross-region NPC references.

---

## Next Phase

With primary walkthroughs complete, proceed to **detailed design** rather than implementation:
1. Detailed design will specify exact mechanics for systems tested in walkthroughs
2. Environmental spread scenario can be modeled against detailed design specs
3. NPC tracking gaps will surface during detailed design
4. Implementation follows after detailed design is validated
