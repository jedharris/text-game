# Meridian Nexus Detailed Design

**Version**: 0.1
**Last Updated**: 2025-12-11
**Status**: Draft

---

## 0. Authoring Guidance

### 0.1 Region Character

The Meridian Nexus is the game's **sanctuary and moral center**. It's where players start, return repeatedly, and ultimately complete their journey. The region should feel mysterious and melancholy but safe - a place of respite from the dangers of other regions. The Echo's presence (or absence, at low trust) defines the emotional experience here.

### 0.2 Content Density Expectations

- **Entity density**: Sparse (4 locations, 1 NPC)
- **NPC interaction depth**: Rich (Echo relationship is deep but singular)
- **Environmental complexity**: Simple (no hazards, no conditions)
- **Time pressure**: None (absolute safety)

### 0.3 What Belongs Here

- Lore and backstory content (journals, inscriptions, Echo dialog)
- Progress tracking visuals (crystal restoration, waystone sockets)
- Cross-region items that must be transported elsewhere
- Safe item storage
- Quiet character moments with Echo
- Endgame ceremony (waystone repair)

### 0.4 What Does NOT Belong Here

- **Combat encounters** - Magical wards repel all hostiles; this is inviolable
- **Environmental hazards** - No cold, spores, drowning, or other conditions apply here
- **Time-pressured situations** - No NPCs in danger, no spreading threats within the region
- **Dense NPC populations** - Only Echo resides here; isolation is deliberate
- **Service transactions** - Echo provides guidance through relationship, not services

### 0.5 Authoring Notes

- **Many N/A sections expected**: Gossip, environmental conditions, companion recruitment, skills, puzzles, and NPC generation are all N/A for this region. This is correct - the Nexus is deliberately minimal.
- **Echo is not a typical NPC**: Don't apply normal NPC patterns. Echo is a moral compass that responds to player actions across the entire game, not a quest-giver or service-provider.
- **Hub for cross-region content**: The primary mechanical role is importing waystone fragments and exporting items needed in other regions (animator crystal, cleaning supplies, temple password).
- **Temporal stasis in Keeper's Quarters**: Items stored here never despawn - this is a safe storage feature for players.
- **Wolf exclusion**: Wolves cannot enter under any circumstances. Don't create exceptions.

---

## 1. Required Entities

All entities that MUST exist based on the overview, walkthroughs, and cross-region dependencies.

### 1.1 Required Locations

| Location ID | Name | Purpose | Source |
|-------------|------|---------|--------|
| `nexus_chamber` | Nexus Chamber | Central hub with damaged waystone; exits to all regions | `big_game_overview.md` |
| `observatory_platform` | Observatory Platform | Overlooks broken landscape; contains telescope | `big_game_overview.md` |
| `keepers_quarters` | Keeper's Quarters | Echo's primary manifestation location; contains journals | `big_game_overview.md` |
| `crystal_garden` | Crystal Garden | Progress tracking via crystal restoration | `big_game_overview.md` |

**Location Details:**

**nexus_chamber**:
- Environmental zone: Safe (no hazards)
- Properties: `safe_zone: true`, `no_combat: true`, `lighting: "twilight"`
- Required exits: north → `frozen_pass`, south → `forest_edge`, east → `flooded_plaza`, west → `cavern_entrance`, up → `observatory_platform`
- Key features: Damaged waystone (central game goal), reality instability (narrative flavor)
- Wolf exclusion: Magical wards prevent wolves from entering

**observatory_platform**:
- Environmental zone: Safe
- Properties: `safe_zone: true`, `elevation: "high"`, `lighting: "twilight"`
- Required exits: down → `nexus_chamber`, east → `keepers_quarters`
- Key features: Ancient telescope (region overview, syncs with Frozen Reaches telescope when both repaired)

**keepers_quarters**:
- Environmental zone: Safe, temporal stasis
- Properties: `safe_zone: true`, `temporal_stasis: true`, `echo_primary_location: true`
- Required exits: west → `observatory_platform`, down → `crystal_garden`
- Key features: Item storage (never despawns), Echo manifestation location, backstory revelation via journals
- Temporal effect: Time frozen - dust motionless, food preserved

**crystal_garden**:
- Environmental zone: Safe
- Properties: `safe_zone: true`, `magical_resonance: "high"`
- Required exits: up → `keepers_quarters`, west → `nexus_chamber`
- Key features: Five regional crystals (progress tracking), animator crystal (export item)

### 1.2 Required NPCs

| Actor ID | Name | Role | Commitment Timer | Source |
|----------|------|------|------------------|--------|
| `the_echo` | The Echo | Moral compass, commitment tracker, game guide | N/A | `big_game_overview.md` |
| `waystone_spirit` | The Waystone | Commitment target for waystone repair (minimal NPC) | N/A | Infrastructure requirement |

**The Echo - Full Specification:**

- **Nature**: Spectral remnant of the last Keeper's child
- **Initial disposition**: Curious, hopeful
- **Trust system**: See Section 3.4 for full trust mechanics
- **State machine** (describes what Echo is doing when present):
  - States: `dormant`, `manifesting`, `communicating`, `fading`, `permanent`
  - Initial: `dormant`
  - Note: "refusing" is NOT a state - it's the trust <= -6 behavior where appearance probability is 0%
- **Appearance mechanics** (see game_wide_rules.md Echo Trust Floor for details):
  - Base chance: 20%
  - Trust modifier: +10% per trust level
  - Trust -1 to -2 (Disappointed): Normal appearance chance, dialog sad/concerned
  - Trust -3 to -5 (Reluctant): 5% appearance chance, dialog cold/distant
  - Trust -6 or below (Refuses): No appearance at all
  - Cooldown: 5 turns between appearances
  - Guaranteed appearances: First entry to Keeper's Quarters, after waystone repair, after any abandoned commitment
- **Key dialog topics**: disaster, regions, restoration, waystone, crystals, commitments, progress
- **Transformation**: When waystone repaired, becomes permanent and corporeal
- **Backstory revelation**: At trust 6+, reveals was training to be next Keeper

**The Waystone (Minimal NPC) - Specification:**

The waystone is modeled as a minimal NPC to satisfy the infrastructure requirement that commitments have an `ActorId` target. It is NOT a character - it's a magical object with just enough NPC properties to participate in the commitment system.

- **Nature**: Magical construct, the damaged heart of the meridian
- **Location**: `nexus_chamber` (fixed, cannot move)
- **Interaction**: Player can examine, place fragments, make commitment to repair
- **State machine**:
  - States: `damaged`, `partial`, `repaired`
  - Initial: `damaged`
  - Transitions: `damaged` → `partial` (first fragment placed), `partial` → `repaired` (all 5 fragments)
- **Implementation**: State is derived from `fragments_placed` property:
  - `fragments_placed == 0` → state is `damaged`
  - `fragments_placed` 1-4 → state is `partial`
  - `fragments_placed == 5` → state is `repaired`, also sets `waystone_complete` flag
  - When player places a fragment: increment property, call `transition_state()` if crossing threshold
- **Properties**:
  - `is_object: true` (flag indicating this is not a character)
  - `commitment_target: true`
  - `fragments_placed: 0`
- **No dialog**: The waystone doesn't speak. Narrative descriptions come from the game engine, not NPC dialog.
- **No trust**: The waystone doesn't have a trust relationship with the player.
- **No services**: The waystone provides fast travel only after repair, not as a service.

### 1.3 Required Items

| Item ID | Name | Purpose | Found In | Source |
|---------|------|---------|----------|--------|
| `ancient_telescope` | Ancient Telescope | Region overview; syncs with Frozen Reaches telescope | `observatory_platform` | `big_game_overview.md` |
| `keepers_journal` | Keeper's Journal | Backstory; partial temple password | `keepers_quarters` | `big_game_overview.md` |
| `cleaning_supplies` | Cleaning Supplies | Required for Frozen Reaches telescope repair | `keepers_quarters` | `cross_region_dependencies.md` |
| `animator_crystal` | Animator Crystal | Required for Guardian repair in Civilized Remnants | `crystal_garden` | `cross_region_dependencies.md` |
| `shattered_crystals` | Shattered Crystals | Progress tracking; provide buffs when restored | `crystal_garden` | `big_game_overview.md` |

**Note**: The Damaged Waystone is modeled as an actor (`waystone_spirit`) rather than an item, to satisfy commitment system requirements. See Section 1.2 for details.

**keepers_journal**:
- Properties: `readable: true`, `portable: true`
- Content: Convergence going unstable (days 1247-1255), Keeper's growing concern, partial password
- Password fragment: "Fire-that-gives-life and water-that-cleanses, un-"
- Flags on read: `has_temple_password_partial`, `knows_keeper_backstory`

**shattered_crystals**:
- Five regional crystals, each with:
  - Restoration trigger (major healing/restoration in corresponding region)
  - Visual state change (lights up with region-appropriate color)
  - Buff granted when touched after restoration

| Crystal | Color | Region | Restores When | Buff |
|---------|-------|--------|---------------|------|
| Frozen | Blue-white | Frozen Reaches | Telescope repaired OR major rescue | Cold resistance |
| Fungal | Green with movement | Fungal Depths | Spore Mother healed OR Aldric saved | Slow poison/infection |
| Water | Blue, rippling | Sunken District | Archivist quest OR major rescue | Improved breath |
| Beast | Tawny with amber | Beast Wilds | Wolf trust 5+ OR cubs saved | +10 max health |
| Civilization | Warm golden | Civilized Remnants | Guardian repaired OR hero status | Merchant discounts |

### 1.4 Required Puzzles/Challenges

| Puzzle | Location | Type | Requirements | Source |
|--------|----------|------|--------------|--------|
| Waystone Repair | `nexus_chamber` | Multi-step ritual | 5 fragments from other regions | `big_game_overview.md` |

**Waystone Repair Ceremony:**
- Type: Multi-step sequential (not a puzzle in the traditional sense)
- Requirements: All five waystone fragments
- Order: Player's choice (any order)
- Fragments needed:

| Fragment | Source Region | Acquisition |
|----------|---------------|-------------|
| Spore Heart | Fungal Depths | Gift from healed Spore Mother |
| Alpha Fang | Beast Wilds | Gift from Alpha Wolf at trust 5+ |
| Water Pearl | Sunken District | Reward from Archivist quest |
| Ice Shard | Frozen Reaches | Extract from ice caves |
| Town Seal | Civilized Remnants | Hero status OR Guardian repair |

---

## 2. Cross-Region Connections

### 2.1 Items This Region Imports

Items that come FROM other regions and are used here:

| Item | Source Region | Purpose Here | Urgency |
|------|---------------|--------------|---------|
| Spore Heart | Fungal Depths | Waystone fragment | Required for endgame |
| Alpha Fang | Beast Wilds | Waystone fragment | Required for endgame |
| Water Pearl | Sunken District | Waystone fragment | Required for endgame |
| Ice Shard | Frozen Reaches | Waystone fragment | Required for endgame |
| Town Seal | Civilized Remnants | Waystone fragment | Required for endgame |

### 2.2 Items This Region Exports

Items that are found here and needed ELSEWHERE:

| Item | Destination Region | Purpose There | Acquisition |
|------|-------------------|---------------|-------------|
| Animator Crystal | Civilized Remnants | Guardian repair (grants Town Seal) | Take from Crystal Garden |
| Cleaning Supplies | Frozen Reaches | Telescope repair | Take from Keeper's Quarters |
| Temple Password (partial) | Frozen Reaches | Golem deactivation (partial) | Read Keeper's Journal |

### 2.3 NPCs With Cross-Region Connections

NPCs here who have relationships with NPCs in other regions:

| NPC Here | Connected To | Connection Type | Gossip Timing |
|----------|--------------|-----------------|---------------|
| The Echo | All NPCs | Commitment awareness | Instant (ley line network) |

**Note**: The Echo knows about all commitments and actions throughout the game instantly through the ley line network. This is not gossip in the traditional sense - Echo is omniscient regarding player moral choices.

### 2.4 Environmental Connections

How this region affects or is affected by other regions:

| Effect | Direction | Trigger | Timing |
|--------|-----------|---------|--------|
| Spore spread halt | From Fungal Depths | Waystone repaired | Immediate |
| Cold spread halt | From Frozen Reaches | Waystone repaired | Immediate |

**Note**: Completing waystone repair halts ALL environmental spreads permanently. This is the "endgame solution" to regional decay.

---

## 3. Instance-Specific Systems

### 3.1 NPC Services

| NPC | Service | Cost/Requirements | Trust Gate | Notes |
|-----|---------|-------------------|------------|-------|
| The Echo | Guidance/information | Free | Trust > -6 (5% at -3 to -5) | Echo provides guidance through dialog topics |
| The Echo | Commitment summary | Free | Trust > -6 (5% at -3 to -5) | Player can ask about their promises |
| The Echo | Region status | Free | Trust > -6 (5% at -3 to -5) | Progress summary for player |

**Note**: Echo provides services through conversation, not transactional service mechanics. No payment required - relationship is trust-gated only.

### 3.2 Companions

N/A - No NPCs in this region can become companions.

**Note**: The Echo is bound to the Nexus (and later, to the waystone network) and cannot travel with the player as a companion. After waystone repair and transformation, Echo becomes "permanent" but still does not travel - it can manifest briefly at critical moments in other regions but is not a companion in the mechanical sense.

### 3.3 Commitments

What commitments can the player make in this region?

| Target NPC | Trigger | Timer | Timer Trigger | Hope Bonus | Fulfillment Flag |
|------------|---------|-------|---------------|------------|------------------|
| `waystone_spirit` | "I'll repair the waystone" / "I'll gather the fragments" | None | `none` | N/A | `waystone_repaired` |

**Waystone Commitment Details:**

```python
CommitmentConfig = {
    "id": "commit_waystone_repair",
    "target_npc": ActorId("waystone_spirit"),  # Minimal NPC representing the waystone
    "goal": "Gather all five fragments and repair the waystone",
    "trigger_phrases": [
        "I'll repair the waystone",
        "I will restore the meridian",
        "I'll gather the fragments"
    ],
    "hope_extends_survival": False,  # Object cannot "survive" - flag is irrelevant
    "base_timer": None,  # No deadline - player can always return
    "fulfillment_flag": "waystone_repaired"
}
```

**Special Characteristics:**
- This is the ONLY untimed commitment in the game
- Cannot be truly "abandoned" - player can always return
- Long delay without progress causes Echo to become pleading/sad
- Echo's dialog references this commitment frequently

**Withdrawal Response:**
- Dialog: "The path is long. Rest. But do not forget - the meridian waits."
- Trust effect: None (neutral)
- Can recommit: Always

### 3.4 Gossip Sources

N/A - No gossip originates from this region.

**Note**: The Echo's awareness of player actions is NOT gossip - it's instant omniscience through the ley line network. Other NPCs do not receive information from the Nexus through gossip mechanics.

### 3.5 Branding/Reputation (if applicable)

N/A - This region does not have unique branding or reputation mechanics.

**Note**: Echo trust is a unique system, not a branding/reputation system. It tracks the player's moral trajectory throughout the entire game, not region-specific actions.

### 3.6 Waystones/Endings (if applicable)

This is the CENTRAL region for waystone and ending mechanics.

**Waystone Fragments:**

| Fragment | Location Found | Acquisition Method | Requirements |
|----------|----------------|-------------------|--------------|
| Spore Heart | Fungal Depths - Spore Heart | Gift from healed Spore Mother | Heartmoss, successful healing |
| Alpha Fang | Beast Wilds - Wolf Clearing | Gift from Alpha Wolf | Trust 5+ with pack |
| Water Pearl | Sunken District - Deep Archive | Archivist quest reward | Swimming skill, breath management |
| Ice Shard | Frozen Reaches - Ice Caves | Extraction | Cold protection (salamander or cloak) |
| Town Seal | Civilized Remnants - Council Hall | Hero status reward OR Guardian repair | Reputation OR animator crystal |

**Ending System:**

| Echo Trust | Waystone Complete | Ending Name | Echo State |
|------------|-------------------|-------------|------------|
| 5+ | Yes | Triumphant | Fully transformed, offers to be permanent companion |
| 3-4 | Yes | Successful | Transformed, grateful but formal |
| 0-2 | Yes | Bittersweet | Transformed, distant |
| -1 to -2 | Yes | Hollow Victory | Transformed but silent |
| -3 to -5 | Yes | Pyrrhic | Present but won't transform |
| -6 or below | Yes | Pyrrhic | Refuses to participate in ceremony |
| Any | No | Abandoned | Remains spectral forever |

**Ending Locks:**
- ANY assassination (even undiscovered): Triumphant ending locked (max is Successful)
- 3+ assassinations: Pyrrhic ending is best possible

### 3.7 Skills (if applicable)

N/A - No skills are learned in this region.

### 3.8 Permanent Consequences

| Action | Consequence | Affected Content | Reversible? |
|--------|-------------|------------------|-------------|
| Assassination (any) | Triumphant ending locked | Best ending | No |
| 3+ Assassinations | Only Pyrrhic ending possible | All good endings | No |
| Echo trust ≤ -6 | Echo refuses to appear entirely | Echo relationship | Partially (recovery capped) |

**Permanent Blockers:**
```
Permanent Blocker: Assassination
- Trigger: Any assassination contract completed
- Locks: Triumphant ending (max available is Successful)
- Affects endings: Even undiscovered assassination blocks best ending
- Warning signs: Echo immediately comments on "darkness in your choices"
```

**Conditional Locks:**
```
Conditional Lock: Echo Transformation
- Required: Echo trust ≥ 0 at waystone repair ceremony
- Lost if: Trust drops below -6 (Echo refuses participation entirely)
- Trust -3 to -5: Echo reluctant, 5% appearance, may still participate if present
- Recovery: Partial - trust recovery capped at +1 per Nexus visit
```

---

## 4. Region Hazards

**Hazard Type**: None

This region has no hazards - it is a sanctuary protected by magical wards.

### 4.1 Hazard Zones

N/A - No hazard zones in this region.

**Environmental zones** (beneficial only):

| Zone Type | Locations | Effects | Mitigation |
|-----------|-----------|---------|------------|
| Safe Zone | All locations | No environmental hazards | N/A |
| Temporal Stasis | `keepers_quarters` | Items never despawn or decay | N/A (beneficial) |

**Note**: The Nexus is unique in having NO environmental hazards. Magical wards that hold reality together also repel hostile creatures and prevent hazardous conditions from entering.

### 4.2 Conditions Applied

N/A - No conditions (environmental or social) are applied in this region.

### 4.3 Companion Restrictions

How do companion restrictions apply in this region?

| Companion Type | Can Enter | Comfort Level | Notes |
|----------------|-----------|---------------|-------|
| Wolves | No | Impossible | Magical wards repel beasts |
| Salamander | Yes | Comfortable | Warmth welcomed; drawn to Crystal Garden |
| Human companions | Yes | Comfortable | Safe haven for all humans |

**Wolf Restriction Details:**
- Wolves pace at boundary, whining
- Something pushes them back (magical wards)
- Wait just outside any exit direction
- Rejoin immediately when player exits

**Salamander Behavior:**
- Finds Nexus pleasantly warm
- Magical energy invigorates it
- Flame brightens near restored crystals
- Echo comment: "A child of flame. We had many here, before. They helped maintain the ley lines."

**Human Companion Behavior:**
- All humans welcome
- Sira dialog: "This place... it's strange. But peaceful. I could stay here a while."
- Aldric dialog: "The Nexus! I read about this place. The heart of the meridian..."
- Aldric may spend extended time studying if player permits (provides lore unlocks)

---

## 5. Behavioral Defaults

### 5.1 NPC Behavioral Defaults

Rules that apply to ALL NPCs in this region unless overridden:

```
- Default disposition toward player: Neutral to welcoming
- Reaction to player brands: N/A (only Echo here, not affected by brands)
- Reaction to gossip: N/A (Echo doesn't receive gossip, has direct awareness)
- Reaction to companions: Echo curious about salamander, neutral to humans
- Reaction to conditions: N/A (no hazardous conditions apply here)
```

**Echo-Specific Behavioral Rules:**
- Appears based on probability roll modified by trust (see appearance mechanics in Section 1.2)
- Trust -3 to -5: Reluctant, 5% appearance chance
- Trust ≤ -6: Never appears
- Guaranteed appearance on specific triggers (first visit, waystone repair, commitment abandonment) - applies at trust > -6 only
- Comments on player's commitments when asked
- Comments on assassinations immediately (even if NPCs haven't discovered)
- Dialog tone varies by trust level

### 5.2 Location Behavioral Defaults

Rules that apply to ALL locations in this region unless overridden:

```
- Environmental zone: Safe
- Lighting: Twilight (perpetual)
- Turn phase effects: None (no environmental damage)
- Combat: Disabled (wards repel hostiles)
- Reality instability: Narrative flavor only
```

### 5.3 Item Behavioral Defaults

Rules that apply to items found in this region:

```
- Typical item types: Quest items, cross-region items, lore items
- Environmental interactions: Items stored in Keeper's Quarters never despawn or decay
- Portable items: Can be taken to other regions
- Fixed items: Waystone, telescope, shattered crystals cannot be moved
```

### 5.4 Group/Pack Dynamics

N/A - No group NPCs in this region. Only Echo (individual) resides here.

---

## 6. Generative Parameters

### 6.1 NPC Generation Seeds

N/A - This region does not support generated background NPCs.

**Rationale**: The Nexus is deliberately sparse - only the Echo resides here. This maintains the sense of isolation and emphasizes the player's relationship with Echo. Additional NPCs would dilute this focus.

**Exception**: Saved NPCs from other regions may relocate to the Nexus:
- Aldric (if saved from Fungal Depths): May appear in Keeper's Quarters as scholar/teacher
- Future expansion could allow other rescued NPCs to seek refuge here

### 6.2 Location Generation Seeds

N/A - This region does not support generated locations.

**Rationale**: The Nexus has exactly four locations with specific narrative purposes. The region is complete as designed.

### 6.3 Density Guidelines

| Area Type | NPCs per Location | Items per Location | Atmosphere |
|-----------|-------------------|-------------------|------------|
| Hub (Nexus Chamber) | 0 (Echo appears conditionally) | 1 (waystone) | Mysterious, central |
| Observatory | 0 | 1 (telescope) | Awe-inspiring |
| Quarters | 1 (Echo appears here) | 3+ | Frozen in time, personal |
| Garden | 0 | 2 (crystals, animator) | Magical, progressive |

**Note**: The Nexus is deliberately sparse. This is a feature, not a gap.

### 6.4 Thematic Constraints

What should content in this region feel like?

```
Tone: Mysterious, hopeful, melancholy
Common motifs: Shattered reality, frozen time, fading light, geometric patterns
Avoid: Combat, urgency, environmental pressure, populated spaces
Sensory emphasis: Visual distortion, temporal anomalies, magical resonance
```

### 6.5 Mechanical Participation Requirements

ALL content in this region must participate in these systems:

```
Required systems:
- [x] Trust/disposition (Echo trust is the central mechanic)
- [ ] Gossip (N/A - Echo has direct awareness, not gossip)
- [ ] Environmental conditions (N/A - region is safe)
- [x] Companion restrictions (wolves excluded, others welcome)

Optional systems (used):
- [x] Commitments (waystone commitment)
- [ ] Services (Echo provides guidance through dialog, not services)
- [ ] Puzzles (waystone repair is ritual, not puzzle)
```

---

## 7. LLM Narration Guidance

### 7.1 Region Traits

Standard traits for LLM narration in this region:

```
Environmental:
- "shimmering air where reality is thin"
- "geometric patterns carved into every surface"
- "distant sounds that don't match what you see"
- "perpetual twilight - neither day nor night"
- "fragments of land visible at wrong angles"
- "impossibly tall spires"
- "stars visible during day" (Observatory only)

Emotional:
- "sense of waiting"
- "hope struggling against entropy"
- "peaceful melancholy"

Historical:
- "remnants of something vast and broken"
- "evidence of catastrophic failure"
- "personal effects of the lost Keeper"
```

**Location-Specific Traits:**

**Nexus Chamber:**
- "stone platforms float at impossible angles"
- "the waystone pulses weakly, waiting"
- "five pathways lead to different atmospheres"

**Observatory Platform:**
- "wind trying to tear you away"
- "impossible distances revealed"
- "frost forming on your eyelashes" (when looking north)

**Keeper's Quarters:**
- "dust motes suspended motionless"
- "half-completed meals frozen in time"
- "books open to marked pages"
- "personal effects arranged with care"

**Crystal Garden:**
- "fractured light playing across walls"
- "humming that rises and falls"
- "patterns that almost make sense"

### 7.2 State Variants

Key state changes that should alter narration:

| State | Trigger | Narration Change |
|-------|---------|------------------|
| `crystals_0_restored` | Initial | "All five crystals lie dark, waiting" |
| `crystals_1-2_restored` | 1-2 regional healings | "Some crystals glow faintly, responding to distant healing" |
| `crystals_3-4_restored` | 3-4 regional healings | "Most crystals pulse with light now, the garden awakening" |
| `crystals_all_restored` | All 5 healings | "The crystal garden blazes with restored power" |
| `waystone_partial` | 1-4 fragments placed | "The waystone glows stronger, [X] sockets filled" |
| `waystone_repaired` | All 5 fragments | "The waystone pulses with full power, reality steadier around it" |
| `echo_refusing` | Trust ≤ -6 | "The air shimmers faintly but nothing coalesces. Silence." |
| `echo_permanent` | After waystone repair | "The Echo stands solid and present, no longer flickering" |

### 7.3 NPC Description Evolution

How NPC descriptions should change based on state:

| NPC | State | Traits |
|-----|-------|--------|
| Echo | initial (trust 0) | "translucent", "flickering", "voice like an echo of an echo", "eyes that aren't quite there" |
| Echo | medium trust (1-2) | "clearer", "more present", "voice stronger", "curious" |
| Echo | high trust (3-4) | "warm", "steady", "familiar", "speaks your name" |
| Echo | very high trust (5+) | "bright", "solid", "affectionate", "trusting" |
| Echo | disappointed (-1 to -2) | "faint", "withdrawing", "sorrowful", "disappointed" |
| Echo | reluctant (-3 to -5) | "barely visible", "distant", "cold", "silent pauses" |
| Echo | refusing (≤-6) | Does not appear - describe empty air, silence, absence |
| Echo | permanent (after waystone) | "solid", "present", "eyes have color (amber)", "can smile genuinely" |

---

## 8. Validation Checklist

Before considering this design complete:

### 8.1 Completeness

- [x] All required entities from overview are listed
- [x] All cross-region dependencies documented
- [x] All instance-specific systems addressed (or marked N/A)
- [x] Environmental rules fully specified
- [x] Behavioral defaults cover all entity types

### 8.2 Consistency

- [x] Location IDs follow naming convention (`snake_case`)
- [x] NPC trust thresholds are reasonable (Echo: -6 to 5+ scale)
- [N/A] Commitment timers are fair (waystone commitment has no timer)
- [x] Companion restrictions match `cross_region_dependencies.md`
- [N/A] Gossip timing is consistent (no gossip originates here)

### 8.3 Cross-Region Verification

- [x] All imported items are exported from documented source regions (5 waystone fragments)
- [x] All exported items are imported by documented destination regions (animator crystal, cleaning supplies, password)
- [N/A] Gossip timing matches (no gossip originates here)
- [x] NPC connections documented on both sides (Echo's omniscience is unique)
- [N/A] Skill dependencies are achievable (no skills learned here)
- [x] Permanent consequences don't create impossible states (assassination only locks endings, not progress)

### 8.4 Generative Readiness

- [N/A] NPC generation seeds cover expected roles (region is complete, no generation)
- [N/A] Location generation seeds cover expected types (region is complete, no generation)
- [x] Density guidelines provide clear targets
- [x] Mechanical participation requirements are clear
- [x] Thematic constraints prevent off-tone content

---

## Appendix A: Infrastructure System Integration

### A.1 Echo Trust System

Uses the Trust System from `infrastructure_detailed_design.md`:

```python
TrustState = {
    "current": 0,        # Starting trust
    "floor": -6,         # Trust floor (Echo refuses at -3, maximum penalty at -6)
    "ceiling": None,     # No ceiling - can go arbitrarily high
    "recovery_cap": 1,   # Max +1 per Nexus visit (prevents grinding)
}
```

**Trust Sources:**
| Action | Trust Change |
|--------|--------------|
| Restore crystal | +1 |
| Save major NPC (Aldric, Sira, Garrett, Delvan) | +1 |
| Heal Spore Mother | +1 |
| Fulfill commitment | +0.5 |
| Place waystone fragment | +0.5 |
| Abandon commitment | -1 (or -0.5 with partial credit) |
| Assassination (any) | -2 |

### A.2 Commitment System

The waystone commitment uses the Commitment System from `infrastructure_detailed_design.md`:

```python
ActiveCommitment = {
    "id": "commit_waystone_repair",
    "config_id": "commit_waystone_repair",
    "state": CommitmentState.ACTIVE,
    "made_at_turn": <turn_number>,
    "deadline_turn": None,  # No deadline
    "hope_applied": False,
}
```

### A.3 Companion System

Uses Companion System from `infrastructure_detailed_design.md`:

```python
# Wolf companion restriction for Nexus
CompanionRestriction = {
    "location_patterns": ["nexus_*", "observatory_*", "keepers_*", "crystal_*"],
    "comfort": CompanionComfort.IMPOSSIBLE,
    "reason": "Magical wards repel beasts"
}
```

### A.4 Scheduled Events

The Nexus uses scheduled events for:
- Echo appearance cooldown tracking
- Crystal restoration triggers (listening for events from other regions)

```python
ScheduledEvent = {
    "id": "echo_cooldown_expire",
    "trigger_turn": <current_turn + 5>,
    "event_type": "echo_cooldown_reset",
    "data": {}
}
```

---

## Appendix B: Data Structures

### B.1 Game State Schema (Nexus-specific)

```json
{
  "extra": {
    "echo_trust": {
      "current": 0,
      "floor": -6,
      "recovery_cap": 1,
      "recovered_this_visit": 0,
      "last_recovery_turn": null
    },
    "crystals_restored": {
      "frozen": false,
      "fungal": false,
      "water": false,
      "beast": false,
      "civilization": false
    },
    "waystone_fragments": {
      "spore_heart": false,
      "alpha_fang": false,
      "water_pearl": false,
      "ice_shard": false,
      "town_seal": false
    },
    "waystone_repaired": false,
    "echo_last_appearance": null,
    "echo_cooldown_until": null
  }
}
```

### B.2 Echo Actor Definition

```json
{
  "id": "the_echo",
  "name": "The Echo",
  "description": "A spectral remnant of the Keeper's child. It flickers at the edge of visibility.",
  "properties": {
    "corporeal": false,
    "state_machine": {
      "states": ["dormant", "manifesting", "communicating", "fading", "permanent", "refusing"],
      "initial": "dormant"
    },
    "dialog_topics": {
      "disaster": {"requires": [], "unlocks": ["regions", "restoration"]},
      "regions": {"requires": ["knows_disaster_cause"]},
      "restoration": {"requires": ["knows_disaster_cause"], "unlocks": ["waystone", "crystals"]},
      "waystone": {"requires": ["knows_disaster_cause"]},
      "crystals": {"requires": ["knows_disaster_cause"]},
      "commitments": {"requires": []},
      "progress": {"requires": []}
    },
    "backstory_gates": {
      "surface": 0,
      "trust_3": 3,
      "trust_6": 6
    }
  },
  "flags": {},
  "location": "keepers_quarters"
}
```

### B.3 Waystone Spirit Actor Definition (Minimal NPC)

```json
{
  "id": "waystone_spirit",
  "name": "The Waystone",
  "description": "A cracked stone pedestal with faded runes. Five empty sockets around its rim.",
  "properties": {
    "is_object": true,
    "commitment_target": true,
    "state_machine": {
      "states": ["damaged", "partial", "repaired"],
      "initial": "damaged"
    },
    "fragments_placed": 0,
    "fragments": {
      "spore_heart": false,
      "alpha_fang": false,
      "water_pearl": false,
      "ice_shard": false,
      "town_seal": false
    }
  },
  "flags": {},
  "location": "nexus_chamber"
}
```

**Note**: This is a minimal NPC used only to satisfy the infrastructure requirement that commitments target an `ActorId`. The waystone does not have dialog, trust, services, or any other typical NPC behaviors. The `is_object: true` flag signals to behaviors and narration that this should be treated as an interactive object, not a character.

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2025-12-11 | Initial draft from template |
| 0.2 | 2025-12-11 | Phase 2 consistency fixes: Aligned Echo trust tiers with game_wide_rules.md DQ-2 resolution (CC-4/MN-1/MN-2) - tiered system: disappointed/-1 to -2, reluctant/-3 to -5 at 5%, refusing/-6 |
