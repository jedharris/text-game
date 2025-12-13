# Region Detailed Design Template

This template defines the structure for detailed design of each region in The Shattered Meridian. The template serves two purposes:

1. **Prime the design process** - Categories ensure all required aspects are considered
2. **Guide LLM authoring** - Seeds and constraints enable generative expansion while maintaining mechanical coherence

## How to Use This Template

1. Copy this template for each region (e.g., `fungal_depths_detailed_design.md`)
2. Fill in each section by reviewing: `big_game_overview.md`, `cross_region_dependencies.md`, relevant walkthroughs, and `infrastructure_detailed_design.md`
3. The "Generative Parameters" section provides seeds for LLM authoring to fill in background content
4. After initial fill-in, use this document to guide full region implementation

---

# [Region Name] Detailed Design

**Version**: 0.1
**Last Updated**: [date]
**Status**: Draft | In Review | Approved

## 0. Authoring Guidance

High-level guidance for anyone authoring or expanding content in this region. This section sets expectations about the region's character and helps authors understand what kind of content belongs here.

### 0.1 Region Character

Describe the region's core identity in 2-3 sentences. What makes it distinct? What experience should players have here?

### 0.2 Content Density Expectations

- **Entity density**: Sparse / Moderate / Dense
- **NPC interaction depth**: Minimal / Moderate / Rich
- **Environmental complexity**: Simple / Moderate / Complex
- **Time pressure**: None / Low / Moderate / High

### 0.3 What Belongs Here

List the types of content that fit this region:
- (e.g., "Puzzles involving light and darkness")
- (e.g., "NPCs offering services")
- (e.g., "Environmental hazards requiring preparation")

### 0.4 What Does NOT Belong Here

List content types that would feel wrong or undermine the region's purpose:
- (e.g., "Combat encounters" - if this is a sanctuary)
- (e.g., "Time-pressured rescues" - if this is meant for methodical exploration)
- (e.g., "Dense NPC populations" - if isolation is the theme)

### 0.5 Authoring Notes

Any additional guidance for authors:
- Expected N/A sections and why
- Key relationships to other regions
- Common mistakes to avoid

### 0.6 Difficulty Design Notes

Document intentional difficulty decisions for this region:

**Designed challenges** (intended to be hard):
- (e.g., "Sira's 8-turn timer is a designed trap - players who overcommit will fail")
- (e.g., "Dual rescue is intentionally impossible on first playthrough")

**Fair challenges** (hard but solvable with preparation):
- (e.g., "Cold survival requires gear from another region")

**First-playthrough expectations**:
- What should a new player likely accomplish?
- What should they likely fail?
- What teaches them for subsequent attempts?

---

## 1. Required Entities

List all entities that MUST exist based on the overview, walkthroughs, and cross-region dependencies. These are the designed, non-negotiable elements of the region.

### 1.1 Required Locations

| Location ID | Name | Purpose | Source |
|-------------|------|---------|--------|
| `example_id` | Example Location | Brief purpose | `big_game_overview.md` or walkthrough reference |

For each location, note:
- Environmental zone (temperature, spore level, water depth, etc.)
- Required exits and connections
- Key mechanical features (darkness, hazards, puzzles)

### 1.2 Required NPCs

| Actor ID | Name | Role | Commitment Timer | Source |
|----------|------|------|------------------|--------|
| `example_npc` | Example NPC | Service provider / quest giver / companion | N/A or X turns | Reference |

For each NPC, note:
- Initial disposition and trust requirements
- Services offered (if any)
- Commitment mechanics (if applicable)
- Whether they can become a companion
- Key dialog topics they must support

### 1.3 Required Items

| Item ID | Name | Purpose | Found In | Source |
|---------|------|---------|----------|--------|
| `example_item` | Example Item | Quest item / consumable / tool | Location or NPC | Reference |

For each item, note:
- Whether it's a quest item, consumable, or tool
- Cross-region dependencies (is it needed elsewhere?)
- Any special properties (light source, cold protection, etc.)

### 1.4 Required Puzzles/Challenges

| Puzzle | Location | Type | Requirements | Source |
|--------|----------|------|--------------|--------|
| Example Puzzle | Where | Multi-solution / Cumulative / Collection / Probabilistic | What player needs | Reference |

For each puzzle, note:
- Puzzle type (multi-solution, cumulative threshold, collection, probabilistic, or other)
- All valid solutions
- What flags/items/skills are involved

**Collection Quests**: If a puzzle requires gathering multiple pieces, document:
- Total pieces needed vs available (e.g., "3 of 5 knowledge fragments")
- Where each piece is found
- Whether some pieces require other actions (e.g., "Garrett's map requires rescuing Garrett")

**Probabilistic Outcomes**: If a puzzle/dilemma has random outcomes, document:
```
Probabilistic Outcome: [Name]
- Choice: [What player decides]
- Outcomes:
  - [X]% chance: [Outcome A with consequences]
  - [Y]% chance: [Outcome B with consequences]
- Design intent: [Why probability is used here]
```

Example:
```
Probabilistic Outcome: Test and Admit Traders
- Choice: Player decides to test traders for infection before admitting
- Outcomes:
  - 80% chance: Clean - all councilors favorable, traders admitted
  - 20% chance: One infected - Hurst blames player, quarantine required
- Design intent: Creates uncertainty in decision-making, realistic outcome
```

### 1.5 Communication Conventions

How do NPCs in this region communicate? Document non-verbal or distinctive communication styles that players must learn to interpret.

**Verbal NPCs**: (List NPCs that speak normally)

**Non-verbal NPCs**: (List NPCs that communicate through other means)

For each non-verbal NPC type, document their communication vocabulary:

```
[NPC Type] Communication:
- [gesture/signal/color] = [meaning]
- [gesture/signal/color] = [meaning]
- ...
```

Example:
```
Salamander Communication:
- Points at object + points at self = wants that object
- Flame brightens = happy/interested
- Flame dims + backs away = frightened/unhappy
- Crackle sound = pleased/greeting

Myconid Communication:
- Blue spores = calm/neutral
- Green spores = pleased/welcoming
- Red spores = warning/anger
- Pulsing = emphasis
```

**Communication learning curve**: How do players learn to interpret these signals? (journal hints, trial and error, NPC reactions)

---

## 2. Cross-Region Connections

### 2.1 Items This Region Imports

Items that come FROM other regions and are used here:

| Item | Source Region | Purpose Here | Urgency |
|------|---------------|--------------|---------|
| Example | Other Region | What it enables | Optional / Required / Time-sensitive |

### 2.2 Items This Region Exports

Items that are found here and needed ELSEWHERE:

| Item | Destination Region | Purpose There | Acquisition |
|------|-------------------|---------------|-------------|
| Example | Other Region | What it enables there | How player gets it here |

### 2.3 NPCs With Cross-Region Connections

NPCs here who have relationships with NPCs in other regions:

| NPC Here | Connected To | Connection Type | Gossip Timing |
|----------|--------------|-----------------|---------------|
| Example | NPC in Other Region | Relationship type | X turns for news to spread |

### 2.4 Environmental Connections

How this region affects or is affected by other regions:

| Effect | Direction | Trigger | Timing |
|--------|-----------|---------|--------|
| Example spread | From/To other region | What triggers it | Turn count |

### 2.5 Travel Times

Estimated turn costs for travel between this region and connected regions. Critical for commitment timer design.

| From | To | Turns | Notes |
|------|-----|-------|-------|
| This region entry | Connected region entry | X turns | One-way travel |

**Travel time assumptions**:
- Each location transition = 1 turn
- Include typical exploration/obstacles
- Note if shortcuts exist (waystone, etc.)

**Impact on commitments**:
- (e.g., "Sira's 8-turn timer requires ~6 turns round-trip to Civilized Remnants, leaving only 2 turns margin")
- (e.g., "Bear cubs' 30-turn timer allows comfortable round-trip with exploration")

---

## 3. Instance-Specific Systems

These are the "content-bound" systems from the infrastructure spec that need region-specific design. For each system, either describe the instances in this region OR mark "N/A - not present in this region" with rationale.

### 3.1 NPC Services

What services are offered by NPCs in this region?

| NPC | Service | Cost/Requirements | Trust Gate | Notes |
|-----|---------|-------------------|------------|-------|
| Example | Healing / Teaching / Trading | What player pays | Trust level needed | Special conditions |

### 3.2 Companions

Which NPCs in this region can become companions?

| NPC | Recruitment Condition | Restrictions | Special Abilities |
|-----|----------------------|--------------|-------------------|
| Example | Trust threshold or quest | Where they can't go | What they provide |

### 3.3 Commitments

What commitments can the player make in this region?

| Target NPC | Trigger | Timer | Timer Trigger | Hope Bonus | Fulfillment Flag |
|------------|---------|-------|---------------|------------|------------------|
| Example | What player says/does | X turns | Type (see below) | +Y turns or N/A | `flag_name` |

**Timer Trigger Types** (see Appendix A for full reference):
- **on_commitment**: Timer starts when player makes commitment (most common)
- **on_room_entry**: Timer starts when player enters location (e.g., Garrett already drowning)
- **on_first_encounter**: Timer starts on first meeting (e.g., Delvan bleeding when found)
- **global_turn**: Timer tied to global turn count (e.g., environmental spreads)
- **none**: No timer pressure (e.g., Guardian repair)

### 3.4 Gossip Sources

What gossip originates from this region?

| Event | Content | Target NPCs | Delay | Confession Window |
|-------|---------|-------------|-------|-------------------|
| Example event | What spreads | Who learns | X turns | Y turns or N/A |

### 3.5 Branding/Reputation (if applicable)

Does this region have unique branding or reputation mechanics?

| Brand/Rep | How Earned | Effects | Spread |
|-----------|------------|---------|--------|
| Example | Actions that earn it | What it unlocks/blocks | How others learn |

### 3.6 Waystones/Endings (if applicable)

Does this region contain waystone fragments or ending-related content?

| Fragment | Location | Acquisition | Requirements |
|----------|----------|-------------|--------------|
| Example | Where found | How obtained | What player needs |

### 3.7 Skills (if applicable)

What skills can be learned in this region?

| Skill | Teacher | Requirements | Effects |
|-------|---------|--------------|---------|
| Example | Who teaches | Trust/quest/payment | What it enables |

**Multi-Tier Skills**: If skills have progression tiers, document:
```
Skill Progression: [Skill Name]
- Tier 1: [Name] from [Teacher]
  - Requirements: [what player needs]
  - Effects: [what it enables]
- Tier 2: [Name] from [Teacher] (requires Tier 1)
  - Requirements: [what player needs]
  - Effects: [additional capabilities]
```

Example:
```
Skill Progression: Swimming
- Tier 1: Basic Swimming from Old Swimmer Jek
  - Requirements: 5 gold OR food item
  - Effects: Breath 15, traverse chest-deep water, normal swim speed
- Tier 2: Advanced Swimming from Sailor Garrett (requires Basic Swimming)
  - Requirements: Rescue Garrett, wait 5 turns for recovery
  - Effects: Breath 20, navigate currents, avoid fish attacks
```

**Skill Permanence**: Note whether skills are:
- Permanent (once learned, always available)
- Conditional (requires item, location, or companion)
- Losable (can be removed by certain events)

### 3.8 Permanent Consequences

Document actions in this region that permanently lock content or endings:

| Action | Consequence | Affected Content | Reversible? |
|--------|-------------|------------------|-------------|
| Example | What happens | What's locked/unlocked | Yes/No |

**Permanent Blockers**: Actions that permanently prevent certain outcomes:
```
Permanent Blocker: [Action]
- Trigger: [What player does]
- Locks: [What becomes unavailable]
- Affects endings: [Which endings blocked]
- Warning signs: [How player might know beforehand]
```

Example:
```
Permanent Blocker: Assassination Discovered
- Trigger: Player pays for assassination AND 20% discovery roll succeeds
- Locks: Un-branding ceremony, Triumphant ending, Successful ending
- Affects endings: Only Bittersweet and Dark endings available
- Warning signs: Shadow warns "this cannot be undone", Echo senses darkness
```

**Conditional Locks**: Content that becomes unavailable if certain conditions aren't met:
```
Conditional Lock: [Content]
- Required: [What must happen to keep available]
- Lost if: [What prevents access]
- Recovery: [None / Partial / Alternative path]
```

Example:
```
Conditional Lock: Advanced Herbalism
- Required: Elara must survive
- Lost if: Elara dies (any cause)
- Recovery: None - skill is uniquely tied to Elara
```

---

## 4. Region Hazards

This section documents hazards that threaten the player. Hazards can be **environmental** (cold, drowning, infection) or **social** (reputation damage, branding, exile). Most regions have one type; some may have both.

**Hazard Type**: [Environmental / Social / Both / None]

For **environmental hazard regions** (Frozen Reaches, Fungal Depths, Sunken District): Fill in Sections 4.1 and 4.2 with physical hazards.

For **social hazard regions** (Civilized Remnants): Section 4.1 may be "N/A - no environmental hazards" and Section 4.2 documents social conditions (branding, exile) instead of physical conditions.

For **safe regions** (Meridian Nexus): Both sections may be minimal or N/A.

### 4.1 Hazard Zones

Define the hazard conditions in this region (environmental OR social):

**Environmental zones** (if applicable):

| Zone Type | Locations | Effects | Mitigation |
|-----------|-----------|---------|------------|
| Example (cold/spore/water) | Which locations | What happens to player | How to counter |

**Social hazard zones** (if applicable):

| Zone Type | Locations | Effects | Mitigation |
|-----------|-----------|---------|------------|
| Example (watched/restricted) | Which locations | Social consequences | How to avoid |

Example (Civilized Remnants):
```
Social hazard zones:
- Market Square: Guards watching, theft has high discovery chance
- Undercity: 5% discovery chance per service, cumulative risk
- Council Hall: Formal behavior expected, missteps affect reputation
```

### 4.2 Conditions Applied

What conditions can players acquire in this region? Include both environmental and social conditions.

**Environmental conditions** (if applicable):

| Condition | Source | Severity Progression | Treatment |
|-----------|--------|---------------------|-----------|
| Example | What causes it | How it worsens | How to cure |

**Social conditions** (if applicable):

| Condition | Source | Effects | Recovery |
|-----------|--------|---------|----------|
| Example | What causes it | What it blocks/enables | How to remove |

Example (Civilized Remnants):
```
Social conditions:
- Branded: Reputation -5 or below → doubled prices, teaching denied, trust capped, good endings blocked
  - Recovery: Reach reputation +3 while branded + complete heroic act → un-branding ceremony
- Exiled: Attack townsperson or 3+ serious crimes → denied entry, only undercity access
  - Recovery: Guardian repair (back tunnel access) + Asha mercy mechanism
```

### 4.3 Companion Restrictions

How do companion restrictions apply in this region?

| Companion Type | Can Enter | Comfort Level | Notes |
|----------------|-----------|---------------|-------|
| Wolves | Yes/No | Comfortable/Uncomfortable/Impossible | Specific rules |
| Salamander | Yes/No | ... | ... |
| Humans | Yes/No | ... | ... |

---

## 5. Behavioral Defaults

These are region-wide rules that all entities (including generated background entities) inherit. They ensure mechanical coherence for content created by LLM authoring.

### 5.1 NPC Behavioral Defaults

Rules that apply to ALL NPCs in this region unless overridden:

```
- Default disposition toward player: [neutral/wary/friendly]
- Reaction to player brands: [e.g., "refuse service if player has 'predator_brand'"]
- Reaction to gossip: [e.g., "become anxious if violence gossip has spread"]
- Reaction to companions: [e.g., "fear if player has wolf companions"]
- Reaction to conditions: [e.g., "offer shelter if player has 'exposure' condition"]
```

### 5.2 Location Behavioral Defaults

Rules that apply to ALL locations in this region unless overridden:

```
- Environmental zone: [default zone type]
- Lighting: [lit/dark/variable]
- Turn phase effects: [what happens each turn]
```

### 5.3 Item Behavioral Defaults

Rules that apply to items found in this region:

```
- Typical item types: [consumables, tools, quest items]
- Environmental interactions: [e.g., "organic items decay in spore zones"]
```

### 5.4 Group/Pack Dynamics

**Skip this section if N/A**: Most regions don't have group dynamics. Only fill this in if the region has NPCs that operate as coordinated groups (wolf packs, spider swarms, myconid colonies, etc.). Mark "N/A - no group NPCs" if the region has only individuals or simple pairs (like linked guards).

If this region has NPCs that operate in groups (packs, swarms, crews), document their collective behavior:

| Group | Leader | Followers | State Mirroring | Location Mirroring |
|-------|--------|-----------|-----------------|-------------------|
| Example Pack | leader_id | [follower_ids] | Yes/No | Yes/No |

**State mirroring**: Do followers adopt the leader's state machine state? (e.g., all wolves become wary when alpha becomes wary)

**Location mirroring**: Do followers move with the leader? (e.g., pack moves together)

**Follower respawn**: Do followers regenerate if killed while leader lives? (e.g., spider workers respawn every 10 turns)

**Leader death effects**: What happens to followers if leader is killed? (e.g., pack scatters, swarm disperses, crew surrenders)

```
Example:
Wolf Pack:
- Leader: npc_alpha_wolf
- Followers: [npc_grey_wolf_1, npc_grey_wolf_2, npc_grey_wolf_3]
- State mirroring: Yes (all become wary/friendly/companion with alpha)
- Location mirroring: Yes (pack moves together)
- Follower respawn: No (dead wolves stay dead)
- Leader death: Pack scatters, some become hostile loners
```

---

## 6. Generative Parameters

This section guides LLM authoring to expand the region beyond the required entities in Section 1. Generated content can include:

- **Additional locations** (side passages, atmospheric areas, shops, homes)
- **Background NPCs** (merchants, refugees, creatures, ambient characters)
- **Minor items** (flavor loot, environmental props, trade goods)
- **Atmospheric details** (sounds, environmental descriptions, gesture vocabularies)

The required entities define what MUST exist. Generative parameters define what CAN be added and how it should feel. Even regions with complete required entities benefit from generative guidance for narration and potential expansion.

### 6.1 Location Generation

What additional locations could exist in this region? What would they look like?

**Generation scope**: [None / Limited / Moderate / Extensive]
- None: Region is deliberately minimal (e.g., Nexus sanctuary)
- Limited: 1-3 additional locations might exist
- Moderate: Several sub-areas or connecting passages expected
- Extensive: Many shops, buildings, passages could be generated

**Location templates** (if applicable):

```
Location Template: [Template Name]
- Purpose: [transition/exploration/resource/atmosphere/service]
- Environmental zone: [inherit or specific]
- Typical features: [what it might contain]
- Connection points: [which designed locations it could connect to]
- Hazards: [what dangers might exist]
- Content density: [sparse/moderate/dense]
```

Example:
```
Location Template: Side Passage (Frozen Reaches)
- Purpose: Exploration, hidden treasures
- Environmental zone: Freezing (same as ice caves)
- Typical features: Ice formations, frozen objects, environmental storytelling
- Connection points: Could branch from ice_caves or frozen_pass
- Hazards: Thin ice, extreme cold pockets
- Content density: Sparse (1-2 items, no NPCs)
```

### 6.2 NPC Generation

What background NPCs could populate this region?

**Generation scope**: [None / Limited / Moderate / Extensive]
- None: Region is deliberately empty or has only designed NPCs
- Limited: 1-3 minor characters might exist
- Moderate: Background characters expected in populated areas
- Extensive: Many merchants, residents, creatures could be generated

**NPC templates** (if applicable):

```
NPC Template: [Template Name]
- Role: [merchant/refugee/guard/creature/etc.]
- Typical count: [X-Y per sub-area]
- Services: [none, or service types]
- Trust thresholds: [default gates]
- Disposition range: [hostile to friendly]
- Dialog topics: [what they might discuss]
- Mechanical hooks: [which infrastructure systems they use]
```

Example:
```
NPC Template: Background Merchant (Civilized Remnants)
- Role: Minor trader
- Typical count: 1-2 per market area
- Services: Trading (limited inventory), local information
- Trust thresholds: Trust >= 2 for fair prices
- Disposition range: Neutral to friendly
- Dialog topics: Local rumors, regional history, trade goods
- Mechanical hooks: Trust system, gossip recipient, reputation-aware
```

### 6.3 Item Generation

What minor items could be found in this region?

**Generation scope**: [None / Limited / Moderate / Extensive]

**Item categories** (if applicable):
```
- Trade goods: [examples]
- Environmental props: [examples]
- Flavor loot: [examples]
- Consumables: [examples]
```

### 6.4 Atmospheric Details

Guidance for narration and description generation:

**Environmental details**:
```
- Sounds: [what players might hear]
- Visual motifs: [recurring imagery]
- Tactile sensations: [temperature, texture, air quality]
- Smells: [what the region smells like]
```

**NPC communication styles** (if non-verbal or distinctive):
```
- Gesture vocabulary: [for non-speaking NPCs like salamanders]
- Speech patterns: [dialects, formality, common phrases]
- Emotional expressions: [how NPCs show feeling]
```

**State-dependent variations**:
```
- How does narration change when [condition]?
- How do descriptions shift between [state A] and [state B]?
```

### 6.5 Density Guidelines

How populated should this region feel overall?

| Area Type | NPCs | Items | Locations | Atmosphere |
|-----------|------|-------|-----------|------------|
| Hub/populated | X-Y per area | X-Y per area | Many sub-locations | Description |
| Wilderness | X-Y per area | X-Y per area | Few sub-locations | Description |
| Dangerous | X-Y per area | X-Y per area | Limited access | Description |

### 6.6 Thematic Constraints

What should ALL generated content feel like? What should it avoid?

```
Tone: [grim/hopeful/mysterious/threatening/etc.]
Common motifs: [what imagery recurs]
MUST include: [required thematic elements]
MUST avoid: [what would feel wrong here]
```

### 6.7 Mechanical Participation Requirements

ALL generated content must participate in these systems:

```
Required systems (generated content MUST use):
- [ ] Trust/disposition (all NPCs must respond to player reputation)
- [ ] Gossip (NPCs in communication range hear news)
- [ ] Environmental conditions (locations in zones apply conditions)
- [ ] Companion restrictions (locations respect restriction rules)

Optional systems (use if thematically appropriate):
- [ ] Services (merchants, healers, teachers)
- [ ] Commitments (if NPC is in distress)
- [ ] Puzzles (if location has obstacles)
- [ ] Brands/reputation (if region has faction system)
```

---

## 7. LLM Narration Guidance

### 7.1 Region Traits

Standard traits for LLM narration in this region:

```
Environmental: [5-8 sensory traits]
Emotional: [2-3 atmosphere traits]
Historical: [2-3 hints about the past]
```

### 7.2 State Variants

Key state changes that should alter narration:

| State | Trigger | Narration Change |
|-------|---------|------------------|
| Example | What causes it | How descriptions change |

### 7.3 NPC Description Evolution

How NPC descriptions should change based on state:

| NPC | State | Traits |
|-----|-------|--------|
| Example | initial | "trait1", "trait2" |
| Example | after quest | "changed trait1", "changed trait2" |

---

## 8. Validation Checklist

Before considering this design complete:

### 8.1 Completeness

- [ ] All required entities from overview are listed
- [ ] All cross-region dependencies documented
- [ ] All instance-specific systems addressed (or marked N/A)
- [ ] Environmental rules fully specified
- [ ] Behavioral defaults cover all entity types

### 8.2 Consistency

- [ ] Location IDs follow naming convention
- [ ] NPC trust thresholds are reasonable
- [ ] Commitment timers are fair given travel times
- [ ] Companion restrictions match `cross_region_dependencies.md`
- [ ] Gossip timing is consistent with established patterns

### 8.3 Cross-Region Verification

- [ ] All imported items are exported from documented source regions
- [ ] All exported items are imported by documented destination regions
- [ ] Gossip timing matches in both source and destination region docs
- [ ] NPC connections documented on both sides of relationship
- [ ] Skill dependencies are achievable (e.g., can reach teacher before deadline)
- [ ] Permanent consequences don't create impossible states

### 8.4 Generative Readiness

- [ ] NPC generation seeds cover expected roles
- [ ] Location generation seeds cover expected types
- [ ] Density guidelines provide clear targets
- [ ] Mechanical participation requirements are clear
- [ ] Thematic constraints prevent off-tone content

---

## Appendix A: Timer Trigger Types Reference

Commitment timers can start in different ways. Use this reference when documenting commitments in Section 3.3.

| Trigger Type | When Timer Starts | Example | Notes |
|--------------|-------------------|---------|-------|
| `on_commitment` | When player makes promise | Aldric: "Find silvermoss" | Most common. Timer starts when player explicitly commits. |
| `on_room_entry` | When player enters location | Garrett drowning | Timer already running. Player walks into crisis. |
| `on_first_encounter` | When player first meets NPC | Delvan bleeding | Timer starts on discovery, before commitment made. |
| `global_turn` | At specific game turn | Spore spread at turn 50 | Environmental spread timers. Not tied to player action. |
| `none` | Never | Guardian repair | No time pressure. Player can complete at leisure. |

**Important Distinctions:**

- **on_commitment vs on_first_encounter**: Both involve meeting an NPC, but `on_commitment` waits for player's promise while `on_first_encounter` starts immediately on discovery.

- **Hope bonus behavior**:
  - With `on_commitment` triggers: Hope bonus extends timer from commitment point
  - With `on_room_entry` or `on_first_encounter`: Hope bonus typically extends NPC survival, not commitment deadline

**Example Configurations:**

```python
# on_commitment (most common)
CommitmentConfig = {
    "trigger_type": "on_commitment",
    "base_timer": 50,  # Starts when player says "I'll help"
    "hope_extends_survival": True,
    "hope_bonus": 10
}

# on_room_entry (immediate crisis)
CommitmentConfig = {
    "trigger_type": "on_room_entry",
    "base_timer": 5,  # Already counting when player arrives
    "hope_extends_survival": False,  # Physics doesn't wait
    "note": "Timer starts on room entry, NOT commitment"
}

# on_first_encounter (bleeding out)
CommitmentConfig = {
    "trigger_type": "on_first_encounter",
    "base_timer": 10,  # Starts when player first sees NPC
    "hope_extends_survival": True,  # Determination slows blood loss
    "hope_bonus": 3
}

# none (no pressure)
CommitmentConfig = {
    "trigger_type": "none",
    "base_timer": None,
    "note": "Player can complete at leisure"
}
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | [date] | Initial draft |
| 0.2 | 2025-12-11 | Added: Section 4 guidance for social vs environmental hazards, probabilistic outcomes in 1.4, collection quests merged into 1.4, timer trigger types in 3.3, multi-tier skills in 3.7, Section 3.8 Permanent Consequences, cross-region verification in 8.3, Appendix A Timer Trigger Types |
