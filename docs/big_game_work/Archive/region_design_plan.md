# Region Detailed Design Plan

This plan drives the creation of detailed designs for each region of The Shattered Meridian.

## Overview

Each region design follows the template in `region_design_template.md`. The process is iterative:
1. Complete one region design
2. Review what worked and what needs refinement in the template
3. Update template if needed
4. Proceed to next region

## Source Documents

When filling out a region template, review these documents in order:

1. **`big_game_overview.md`** - Primary source for required entities
   - Find the region's section
   - Extract all explicitly named: locations, NPCs, items, puzzles
   - Note environmental mechanics and hazards
   - Note commitment timers and gossip timing

2. **`cross_region_dependencies.md`** - Cross-region connections
   - Find all imports (items needed FROM other regions)
   - Find all exports (items this region provides TO others)
   - Note NPC connections across regions
   - Note environmental spread effects

3. **`infrastructure_detailed_design.md`** - How systems work
   - Reference when filling out instance-specific systems (Section 3)
   - Use TypedDicts and API patterns for consistency
   - Ensure behavioral defaults align with infrastructure APIs

4. **Region walkthrough** (in `sketches_and_walkthroughs/`) - Concrete scenarios
   - Extract any additional entities discovered during walkthrough
   - Note timing breakdowns and design inputs
   - Use observations about pacing and difficulty

5. **`walkthrough_guide.md`** - Design patterns
   - Review established patterns (commitment states, difficulty philosophy, etc.)
   - Ensure region design follows these patterns

## Review Process for Each Template Section

### Section 1: Required Entities
- Search overview for all **bold** or explicitly named elements
- Check walkthrough for entities that were invented during simulation
- Every entity in the overview MUST appear in the template

### Section 2: Cross-Region Connections
- Use `cross_region_dependencies.md` tables directly
- Filter to this region only
- Note gossip timing from the Gossip Timing System table

### Section 3: Instance-Specific Systems
- For each system, ask: "Does this region have any instances?"
- If yes, fill in the table with specifics
- If no, write "N/A - [brief rationale]"
- Reference infrastructure_detailed_design.md for field names

### Section 4: Environmental Rules
- Extract from overview's "Environmental Mechanics" subsection
- Conditions from "Region Conditions" subsection
- Companion restrictions from `cross_region_dependencies.md`

### Section 5: Behavioral Defaults
- Infer from region theme and NPC types
- Should cover: disposition, gossip reaction, brand reaction, condition reaction
- These apply to ALL entities including generated ones

### Section 6: Generative Parameters
- Create 2-3 NPC templates based on region theme
- Create 1-2 location templates for connective tissue
- Set density based on region feel (sparse wilderness vs crowded town)
- Thematic constraints prevent off-tone generation

### Section 7: LLM Narration Guidance
- Pull traits directly from overview's "Traits" entries
- State variants from walkthrough observations

### Section 8: Validation Checklist
- Complete after all other sections
- Each checkbox must be verified

---

## Region Order (Simple to Complex)

### Phase 1: Meridian Nexus
**Complexity**: Lowest
**Why first**: Safe hub with minimal mechanics. Good for testing template without complex systems.

**Special considerations**:
- No environmental hazards
- Echo is the only NPC (very special - commitment tracker, not normal NPC)
- Waystone repair is the endgame mechanic
- Crystal Garden restoration mechanic
- All companion types have restrictions here (wolves can't enter)

**Focus areas**:
- Echo's unique role (not a service provider, more like a conscience)
- Waystone fragment requirements (cross-region summary)
- Safe haven mechanics

---

### Phase 2: Frozen Reaches
**Complexity**: Low-Medium
**Why second**: No time-pressured commitments. Environmental challenge is straightforward (cold). Good for testing environmental rules without commitment complexity.

**Special considerations**:
- No dying NPCs - salamanders are fine without help
- Temperature zones are the main mechanic
- Telescope repair is a cross-region fetch quest (no timer)
- Salamander befriending is the companion source
- Temple golems offer puzzle vs combat choice

**Focus areas**:
- Temperature zone definitions
- Salamander companion mechanics
- Telescope as strategic reward
- Cold spread environmental effect

---

### Phase 3: Fungal Depths
**Complexity**: Medium
**Why third**: Introduces commitment system with a forgiving timer (Aldric's 50-60 turns). Good for testing commitment and condition mechanics.

**Special considerations**:
- Infection is the core environmental mechanic
- Aldric's commitment is the most forgiving in the game
- Spore Mother healing is a major quest with environmental consequences
- Myconid services introduce trust-gated services
- Light puzzle (cumulative threshold) in Luminous Grotto

**Focus areas**:
- Infection condition progression
- Commitment mechanics (Aldric)
- Spore spread environmental effect
- Trust-based services (Myconids)

---

### Phase 4: Beast Wilds
**Complexity**: Medium-High
**Why fourth**: Multiple commitments (Sira, bear cubs), companion recruitment (wolves), pack dynamics. Tests multi-commitment and companion systems.

**Special considerations**:
- Sira's 8-turn timer is a designed trap
- Wolf domestication is a multi-step process
- Bear cubs commitment has moderate timer
- Wolf-Sira conflict requires reconciliation
- Spider nest offers coexistence (non-companion) relationship

**Focus areas**:
- Multiple concurrent commitments
- Wolf companion recruitment and restrictions
- Pack dynamics and trust building
- Designed difficulty (Sira trap)

---

### Phase 5: Sunken District
**Complexity**: High
**Why fifth**: Tightest timer overlap (Garrett + Delvan), companion exclusion zone, environmental hazards (drowning). Tests extreme time pressure.

**Special considerations**:
- Designed as solo challenge (all companions excluded)
- Dual rescue is intentionally impossible on first playthrough
- Breath tracking and swimming mechanics
- Archivist quest provides breathing room (no timer)
- Multiple water depth zones

**Focus areas**:
- All companion types excluded
- Impossible dual-rescue design
- Environmental hazard progression (drowning)
- Swimming skill gating

---

### Phase 6: Civilized Remnants
**Complexity**: Highest
**Why last**: Social complexity, dual economy (surface/undercity), exile mechanics, assassination system, moral dilemmas. Tests all social systems.

**Special considerations**:
- Surface town vs undercity dual structure
- Reputation tracking with exile threshold
- Assassination system (dark path)
- Elara-Sira cross-region connection (confession mechanics)
- Council dilemmas (moral complexity)
- Two-tier skill progression (herbalism)
- Guardian repair as redemption valve

**Focus areas**:
- Dual reputation tracks
- Exile and recovery mechanics
- Assassination consequences
- Cross-region NPC connections
- Social vs environmental hazards

---

## Phase 7: Cross-Region Consistency Review

After all six region designs are complete, conduct a cross-region review:

### 7.1 Item Flow Verification
- For each item in an "Exports" table, verify it appears in another region's "Imports" table
- Check that acquisition methods are consistent
- Verify no orphaned items (exported but never imported, or vice versa)

### 7.2 NPC Connection Verification
- For each cross-region NPC connection, verify both sides are documented
- Check gossip timing is consistent (same delay in both region docs)
- Verify confession windows make sense given travel times

### 7.3 Companion Restriction Verification
- Build master companion restriction matrix from all regions
- Verify no contradictions
- Check that "exceptional individual" overrides are narratively justified

### 7.4 Environmental Spread Verification
- Verify spread triggers and timing are consistent across affected regions
- Check that prevention methods are documented in source region

### 7.5 Commitment Timer Verification
- Build master timer table from all regions
- Verify designed overlaps (Sira trap, dual rescue) are achievable/impossible as intended
- Check travel times against timer durations

### 7.6 Waystone Fragment Verification
- Verify all five fragments are documented with acquisition methods
- Check requirements are achievable
- Verify cross-region dependencies for fragment acquisition

### 7.7 Narrative Coherence
- Read through all region designs sequentially
- Note any tone inconsistencies
- Check that generated content seeds don't contradict each other

---

## Iteration Notes

After each region design, note here what worked and what needs template refinement:

### After Meridian Nexus

**Template Changes Made:**
- Added Section 0 "Authoring Guidance" with subsections for Region Character, Content Density Expectations, What Belongs Here, What Does NOT Belong Here, and Authoring Notes
- This section provides high-level guidance for LLM authoring and human reviewers

**What Worked Well:**
- Template structure accommodated a sparse hub region by marking sections N/A with rationale
- Infrastructure integration (TrustState, CommitmentConfig, CompanionRestriction) mapped cleanly
- Cross-region dependencies section effectively captured the hub's import/export role

**Observations:**
- Hub regions will have many N/A sections - this is expected and the template handles it well
- Echo trust is a specialized use of TrustState (custom floor/ceiling, appearance probability) but doesn't require a separate system
- The waystone commitment targets an object rather than an NPC - this works but is an edge case
- Section 0 (Authoring Guidance) is valuable for setting expectations about what content belongs/doesn't belong

**Lessons for Next Regions:**
- Fill Section 0 early to establish authoring constraints before diving into entities
- Environmental regions (Frozen Reaches, Fungal Depths) will have much richer Section 4 (Environmental Rules)
- Social regions (Civilized Remnants) will have much richer Section 3 (Instance-Specific Systems)

### After Frozen Reaches

**Template Changes Made:**
- Rewrote Section 6 (Generative Parameters) to clarify broader purpose
- Added "Generation scope" (None/Limited/Moderate/Extensive) for locations, NPCs, items
- Added Section 6.3 (Item Generation) and 6.4 (Atmospheric Details)
- Split thematic constraints into 6.6 and mechanical requirements into 6.7
- Clarified that generative parameters guide what CAN be added, not just what exists

**What Worked Well:**
- Section 0 (Authoring Guidance) was valuable for establishing the "no time pressure" character upfront
- Environmental rules section (4.1, 4.2) was much richer than Meridian Nexus - good template fit for environmental regions
- Multi-solution puzzle documentation (golem deactivation with 4 paths) fit naturally into Section 1.4
- Companion restrictions section handled the salamander's region-specific comfort levels well

**Observations:**
- Salamander "gratitude" is similar to TrustState but simpler (no negative values, no recovery mechanics). Using simplified TrustState works.
- Golem state machine is a good use of the infrastructure StateMachineConfig
- Temperature zones map cleanly to ConditionType.HYPOTHERMIA with location-based severity rates
- Initial Section 6 was too narrow - marked as "N/A" when it should have specified generation scope and atmospheric guidance

**Lessons for Next Regions:**
- Fungal Depths will have similar environmental complexity (spore zones, infection progression) and should have Limited-Moderate location generation (additional grottos)
- Beast Wilds will have rich companion system content (wolves, bear)
- Sunken District will need timing breakdown section for dual-rescue
- Civilized Remnants will have richest Section 3 (services, reputation, skills) and Extensive generation scope (shops, buildings, residents)

### After Fungal Depths

**Template Changes Made:**
- None - Section 6 (Generative Parameters) revisions from Frozen Reaches applied well

**What Worked Well:**
- Environmental zones (spore levels, toxic air, darkness) mapped cleanly from overview to Section 4
- Commitment system integration (Aldric, Spore Mother) worked well with infrastructure CommitmentConfig
- State machines for Aldric (critical→stabilized→recovering→dead) and Spore Mother (hostile→wary→allied→dead) fit StateMachineConfig pattern
- Light puzzle (cumulative threshold in Luminous Grotto) documented in Section 1.4 puzzles
- Myconid communication vocabulary (spore colors) parallels salamander gesture vocabulary from Frozen Reaches

**Observations:**
- Spore network instant gossip is unique to this region - flagged with has_killed_fungi for immediate trust penalty
- Two parallel commitment tracks (Aldric 50 turns, Spore Mother 200 turns) have very different urgencies
- Myconid services as trust-gated progression fit the infrastructure ServicesConfig pattern
- Limited generation scope appropriate - additional grottos but not extensive content needed

**Lessons for Next Regions:**
- Beast Wilds will have multiple concurrent commitments with competing timers (Sira 8 turns, cubs 30 turns)
- Wolf pack dynamics need pack_follows_alpha pattern documented
- Wolf-Sira reconciliation mechanic is unique companion conflict system
- Spider nest has NO diplomatic path - contrast with wolves/bear/bees

### After Beast Wilds

**Template Changes Made:**
- None - template sections covered all Beast Wilds needs well

**What Worked Well:**
- Pack dynamics system documented cleanly in appendix (shared pattern for wolves and spiders)
- Multiple commitment tracks with competing timers (8 vs 30 turns) documented clearly
- Companion conflict/reconciliation mechanic (Sira + wolves) fit into Section 3.2 and appendix
- Beast communication styles (body language, gestures, vocalizations) documented under Section 6.4
- State machines for multiple NPCs (wolves, bear, spider queen, Sira) all consistent with infrastructure

**Observations:**
- Sira's 8-turn timer is explicitly a designed trap - documented clearly in authoring notes
- Spider nest is deliberately the NO-DIPLOMATIC-PATH contrast to other encounters
- Wolf domestication is multi-step relationship, not a puzzle - important distinction
- Pack dynamics pattern (leader + followers mirror state/location) could be generalized to infrastructure
- Bee Queen trade is technically a cross-region collection but simpler than a formal collection quest

**Lessons for Next Regions:**
- Sunken District will have similar competing timers (Garrett + Delvan) but even tighter
- Civilized Remnants will have the richest NPC interaction depth (speech, not gestures)
- Need to watch for similar companion conflict patterns (salamander + water NPCs?)
- Cross-region item fetches are common - may need to document travel time estimates

### After Sunken District

**Template Changes Made:**
- None - template sections covered all Sunken District needs well

**What Worked Well:**
- Section 0.6 (Difficulty Design Notes) was essential for documenting the intentionally impossible dual-rescue
- Section 2.5 (Travel Times) proved critical for proving the impossibility mathematically
- Environmental zones (water levels) mapped cleanly to Section 4.1
- Breath tracking and swimming skill progression documented clearly in Section 3.8
- Commitment system handled the unique "timer starts on room entry" case for Garrett
- Fish as environmental hazard (not combat) documented well in Section 1.2 and 5.4

**Observations:**
- Garrett's timer-from-room-entry is unique across all regions - important to document clearly
- Hope bonus mechanism (extends survival, not deadline) needs clear explanation
- "Solo challenge" design (all companions excluded) is a strong authoring constraint
- Knowledge quest provides non-timed alternative content - good design for players who fail rescues
- Swimming skill is unique as a permanent cross-region ability learned here
- Fish school behavior is NOT pack dynamics (no leader) - documented in Section 5.4 as N/A with explanation

**Lessons for Next Regions:**
- Civilized Remnants has NO environmental hazards - social hazards instead
- Branding system is like a "social condition" - parallels physical conditions
- Reputation tracks are like trust but more visible/consequential
- Un-branding redemption path parallels condition treatment

### After Civilized Remnants

**Template Changes Made:**
- None - template accommodated the highest-complexity region without changes

**What Worked Well:**
- Section 3.5 (Branding/Reputation) expanded significantly but fit template structure
- Social hazards documented as "environmental rules" alternative (Section 4.1 noted "no environmental hazards")
- Dual-track reputation (surface/undercity) documented cleanly in Section 3.5
- Council dilemmas documented in Section 1.4 as puzzles with probabilistic outcomes
- Gossip/confession mechanics (Elara-Sira) documented in Section 3.4 with timing details
- Assassination system documented with permanent consequence flags
- Guardian repair as "redemption valve" for branded players documented clearly

**Observations:**
- This region has the most Section 3 content (services, commitments, gossip, branding, skills)
- Branding is essentially a "social condition" with a recovery path (un-branding ceremony)
- Asha mercy mechanism (town seal despite brand) is an important edge case
- Assassination permanently blocking un-branding and good endings is a major design decision
- Elara-Sira connection is the most complex gossip/confession test case
- Two-tier herbalism (Maren basic, Elara advanced) parallels swimming skill tiers in Sunken District
- Undercity discovery chance (5% per service) creates risk/reward tension

**Lessons for Cross-Region Review:**
- Verify Elara-Sira gossip timing matches both regions
- Verify Guardian repair requirements (animator crystal, ritual knowledge) are documented in source regions
- Verify town seal acquisition paths are achievable
- Check branding/un-branding interaction with ending system
- Assassination consequences should affect Echo trust and ending availability

**Template Assessment:**
- Template handled all six regions from simplest (Nexus) to most complex (Civilized Remnants)
- Section 0 (Authoring Guidance) consistently valuable for setting expectations
- Section 0.6 (Difficulty Design Notes) essential for documenting designed traps and impossibilities
- Section 2.5 (Travel Times) proved critical for commitment timer validation
- Section 3 scales well from N/A (sparse regions) to extensive (social regions)
- Section 5.4 (Group/Pack Dynamics) useful but only relevant to Beast Wilds and marginally to Sunken District

### After Cross-Region Review
*(To be filled in after Phase 7 review)*
