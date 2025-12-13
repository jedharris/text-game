# Game-Wide Rules - The Shattered Meridian

This document captures rules that apply across multiple regions and aren't specific to any single sketch.

---

## Commitment System Rules

### Commitment Overlap Priority

When multiple commitments expire on the same turn (or nearly so), process in this order:

1. **By timer expiration**: Earlier expiration processes first
2. **If same turn, by severity**:
   - Death (Garrett drowning, Sira bleeding out)
   - Major harm (cubs dying, Aldric succumbing)
   - Minor harm (trade opportunities lost)
3. **If same turn and severity, by region encounter order**: First-encountered NPC processes first

**Echo commentary**: Echo comments on each abandonment separately, in processing order. If multiple occur in quick succession, Echo may consolidate: "Two promises broken in as many hours..."

### Partial Credit Evidence

For partial credit to apply when a commitment fails, the system checks for evidence of genuine effort:

| Evidence Type | Description | Weight |
|---------------|-------------|--------|
| **Region visited** | Player entered the region containing the needed item/action | Required |
| **Relevant item acquired** | Player picked up the item needed to fulfill commitment | Strong |
| **In transit at expiration** | Player was traveling back when timer expired | Strong |
| **Competing commitment fulfilled** | Player successfully completed a different commitment during same period | Moderate |
| **Time constraint clear** | Failure was mathematically impossible given timer overlap | Automatic |

**Partial credit effects**:
- Echo reaction softened
- Trust penalty reduced from -1 to -0.5
- Related NPCs acknowledge the attempt
- No permanent relationship damage

**No partial credit if**:
- Player never entered relevant region
- Player had item but used it elsewhere
- Sufficient time existed but player spent it on non-urgent activities

**Evidence Checking Mechanics**:
The system tracks these flags automatically:
- `visited_{region}` - Set when player enters a region
- `acquired_{item}` - Set when player picks up an item
- `commitment_{id}_progress` - Incremented for each step toward fulfillment
- `in_transit_to_{location}` - Set during travel between regions

When a commitment expires, the system evaluates:
1. Check for "Automatic" evidence (timer overlap made success impossible)
2. Check for "Required" evidence (region visited) - if absent, no partial credit
3. Sum weights of present evidence types
4. Award partial credit if total weight ≥ 2 (Strong + any, or Required + Moderate)

*Example: Player promised to save Sira but Aldric's timer expired first. Player visited Beast Wilds (Required) and acquired bandages (Strong) but was in Fungal Depths when Sira's timer expired. Result: Partial credit awarded.*

### Commitment Timer Interactions

When player has multiple active commitments with overlapping timers:

**Sunken District (tightest overlap)**:
- Garrett: 5 turns base (no hope bonus) from room entry
- Delvan: 10 turns base (+3 hope bonus = 13 max) from first encounter
- **Designed conflict**: Saving both requires optimal play. First playthrough likely saves one.

**Cross-region overlaps**:
- Sira (8 base +4 hope = 12 max) vs Aldric (50 base +10 hope = 60 max): No real conflict - Aldric timer much longer
- Bear cubs (30 base +5 hope = 35 max) vs Aldric (50 base +10 hope = 60 max): No real conflict
- Sira (8 base +4 hope = 12 max) vs Bear cubs (30 base +5 hope = 35 max): Tight if encountered same session

**Design intent**: Most cross-region timer conflicts are resolvable with reasonable planning. Sunken District dual-rescue is the intentional "impossible first playthrough" challenge.

### Timer Format Reference

All commitment timers use the format: **base turns + hope bonus = maximum turns**

| NPC | Base Turns | Hope Bonus | Maximum | Notes |
|-----|------------|------------|---------|-------|
| Garrett | 5 | 0 | 5 | No extension - drowning is immediate |
| Sira | 8 | +4 | 12 | Bleeding out, hope extends survival |
| Delvan | 10 | +3 | 13 | Trapped, hope encourages him to hold on |
| Bear cubs | 30 | +5 | 35 | Illness progression |
| Aldric | 50 | +10 | 60 | Slow corruption, most forgiving timer |

**Hope bonus mechanics**: When player makes a commitment to help, the NPC gains hope which extends their survival timer. The bonus is applied immediately when the commitment is made.

**Timer trigger vs. hope timing**: Some NPCs have timers that start before commitment (e.g., `on_first_encounter`). In these cases:
- Timer begins when trigger condition is met (e.g., player finds Sira)
- Hope bonus is added when player makes commitment (e.g., "I'll help you")
- The bonus extends the remaining time, not the original timer
- *Example*: Sira's 8-turn timer starts when found. If player commits on turn 3, she gains +4 hope, giving her 5 + 4 = 9 turns remaining (total 12 from start).

---

## Cross-Region Propagation Mechanisms

The game uses three distinct mechanisms for propagating information and effects across regions:

| Mechanism | Speed | Nature | Examples |
|-----------|-------|--------|----------|
| **World State Changes** | Instant | Binary flip, universally perceived | Waystone repair, telescope repair |
| **Environmental Spread** | Gradual (turns) | Slow degradation/recovery | Spore spread, cold spread |
| **Gossip** | Variable (turns) | Information traveling between NPCs | NPC fates, reputation changes |

---

## Gossip Timing System

Gossip is for information that travels between NPCs over time. Instant events (waystone/telescope repair) are NOT gossip - see World State Changes section.

### Specific Gossip Values

| Information | Source | Destination | Turns | Notes |
|-------------|--------|-------------|-------|-------|
| Sira's fate (death/rescue) | Beast Wilds | Elara | 12 | Travelers mention injured hunter |
| Sira abandonment | Beast Wilds | Elara | 20 | Only spreads if Sira survives AND tells others |
| Aldric's fate | Fungal Depths | Civilized Remnants | 25 | Scholar's fate becomes known slowly |
| Delvan's fate | Sunken District | Undercity | 7 | Criminal networks communicate quickly |
| Assassination | Civilized Remnants | Echo | 0 | Instant - Echo always knows |
| Assassination discovery | Civilized Remnants | Other councilors | 0-5 | Depends on 20% discovery roll |
| Spore Mother healed | Fungal Depths | All regions | 15 | Major event, spreads relatively fast |
| Bear cubs fate | Beast Wilds | Sira (if alive) | 8 | Sira notices nearby |
| Garrett fate | Sunken District | Camp NPCs | 0 | Immediate - same location |

### Confession Window Timing

**Confession windows are currently Sira-Elara specific** - this is the only NPC pair with a gossip-based confession mechanic in the game. The mechanic exists because:
1. Elara and Sira have a documented relationship (Elara is Sira's mentor)
2. Sira's fate (death or abandonment) spreads via normal gossip to Elara
3. The player has opportunity to confess their role before Elara learns from others

For the Sira-Elara connection:

| Scenario | Timing | Outcome |
|----------|--------|---------|
| Player confesses before gossip (turn < 20) | Any time before turn 20 | Confession: -2 trust, recovery possible |
| Player confesses with context (saved someone else) | Any time before turn 20 | Confession with mitigation: -1.5 trust, recovery easier |
| Player visits Elara after gossip arrives | After turn 20 | Discovery: -3 trust, permanent consequences |
| Player visits Elara, doesn't confess, leaves, returns after gossip | Variable | Discovery + lie by omission: -4 trust |

**Turn counts are from the event**, not from game start.

*Note: If other NPC pairs with similar gossip-based relationships are added in the future, this pattern could be generalized. Currently, other NPC fates (Aldric, Delvan, Garrett) don't have confession window mechanics because no NPC has the same invested relationship that Elara has with Sira.*

### Offscreen NPC Death Notifications

When an NPC dies due to abandoned commitment while player is in another region:

- **No immediate notification** - Player is not told the NPC died
- **Discovery on return** - Player discovers death when returning to NPC's location
- **Discovery via gossip** - Player may hear from other NPCs (per gossip timing)
- **Echo awareness** - Echo always knows and will comment on next Nexus visit

This design creates meaningful discovery moments rather than constant interruptions. Confirmed effective in cross-region walkthrough A.

---

## Trust Recovery Rules

### Trust System Overview

The game uses two separate trust systems:

| System | Scale | Purpose | Recovery |
|--------|-------|---------|----------|
| **Echo Trust** | -6 to +5 | Measures Echo's faith in player's honor | Major deeds (+1 cap per Nexus visit) |
| **NPC Trust** | -5 to +5 | Measures individual NPC's relationship with player | Varies by NPC, based on interactions |

**Key Differences:**
- Echo Trust affects ending tier and Echo's willingness to appear
- NPC Trust affects dialog options, services, quest availability, and NPC behavior
- Echo Trust tracks commitment fulfillment globally; NPC Trust is per-relationship
- Some actions affect both (saving an NPC gives +1 Echo trust AND increases that NPC's trust)

### Echo Trust Recovery

| Deed | Trust Restored |
|------|----------------|
| Save major NPC (Aldric, Sira, Garrett, Delvan) | +1 |
| Heal Spore Mother | +1 |
| Restore crystal | +1 |
| Fulfill commitment | +0.5 |
| Place waystone fragment | +0.5 |

**Recovery limits**:
- Maximum +1 per Nexus visit (prevents grinding)
- Actions must be genuine (can't save same NPC twice)
- Assassination permanently locks triumphant ending (but trust CAN recover)

### NPC Trust Recovery

General pattern for recovering damaged trust with NPCs:

| Damage Level | Recovery Method | Time Required |
|--------------|-----------------|---------------|
| Minor (-1 to -2) | Positive actions, dialog | 5-10 turns of positive interaction |
| Moderate (-3 to -4) | Major deed + time | One significant helpful act + 10 turns |
| Severe (-5+) | Exceptional deed | Rare - requires extraordinary action |
| Permanent | None | Some actions (assassination, abandonment leading to death) cannot be undone |

---

## Environmental Spread Mechanics

### Spread Timelines (if not addressed)

| Spread | Trigger | Timeline |
|--------|---------|----------|
| **Spore spread** | Spore Mother not healed | Turn 50: Beast Wilds affected. Turn 100: Town gate checks. Turn 150: Town NPCs infected. |
| **Cold spread** | Telescope not repaired | Turn 75: Beast Wilds high ground cold. Turn 125: Nexus boundary cold. Turn 175: Sunken District water freezes. |

### Halting Spreads

- **Spore spread**: Heal Spore Mother with heartmoss
- **Cold spread**: Repair Frozen Reaches telescope
- **Both halted**: Repair waystone (endgame)

---

## World State Changes

World state changes are **instant, universally perceived events** - fundamental shifts in the world that all beings sense directly, like the lifting of a curse. These are handled via global flags, not gossip.

### Waystone Repair

| Attribute | Value |
|-----------|-------|
| **Trigger** | All 5 waystone fragments placed |
| **Global Flag** | `waystone_complete` |
| **Effects** | Fast travel unlocked, Echo transforms, environmental spreads halt, Meridian Blessing buff |
| **NPC Perception** | Sensed directly ("The old magic stirs again") - no gossip needed |

### Telescope Repair

| Attribute | Value |
|-----------|-------|
| **Trigger** | Observatory telescope functional |
| **Global Flag** | `observatory_functional` |
| **Effects** | Cold spread prevention, crystal garden +1, strategic vision available |
| **NPC Perception** | Sensed directly ("The bitter winds have softened") - no gossip needed |

### Implementation

- Set global flag immediately when trigger met
- NPCs check flag in dialog/behavior conditions
- No gossip queue, no delivery timing
- Narration describes the moment dramatically

---

## Cross-Region Item Dependencies Summary

### Critical Path Items

| Item | Source | Destination | Purpose | Blocking? |
|------|--------|-------------|---------|-----------|
| Healing herbs | Civilized Remnants | Beast Wilds | Cure bear cubs | Yes - cubs die without |
| Ice crystal | Frozen Reaches | Fungal Depths | Myconid payment | No - alternatives exist |
| Cleaning supplies | Nexus | Frozen Reaches | Telescope repair | Yes - required for repair |
| Temple password | Nexus + Frozen Reaches | Frozen Reaches | Golem deactivation | No - alternatives exist |
| Animator crystal | Nexus | Civilized Remnants | Guardian repair | Yes - required for repair |
| Rare flowers | Multiple | Beast Wilds | Bee Queen trade | No - optional content |

### Waystone Fragments (all required)

| Fragment | Source | Acquisition Method |
|----------|--------|-------------------|
| Spore Heart | Fungal Depths | Heal Spore Mother (gift) |
| Alpha Fang | Beast Wilds | High wolf trust (gift) |
| Water Pearl | Sunken District | Complete Archivist quest |
| Ice Shard | Frozen Reaches | Extract from ice caves |
| Town Seal | Civilized Remnants | Hero status OR Guardian repair |

---

## Companion Multi-Region Rules

### Waiting Behavior

When a companion cannot enter a region:

| Companion | Wait Location | Return Behavior |
|-----------|---------------|-----------------|
| Wolf pack | Just outside restricted area | Rejoin immediately when player exits |
| Salamander | Nexus (if water region) or region entry | Rejoin at wait location |
| Human companions | Nearest safe location (camp, town) | Rejoin when player returns |

**Salamander Water Region Behavior:**
- Salamander cannot enter Sunken District (water would extinguish it)
- When player enters Sunken District, salamander auto-returns to Nexus
- Salamander waits at Nexus until player returns there
- If player exits Sunken District to a different region, salamander remains at Nexus until visited

**Wolf Cold Tolerance:**
- Wolves can enter Frozen Reaches but are uncomfortable in extreme cold zones
- In "bitter cold" areas (Deep Frost, Ice Caves), wolves have -1 combat effectiveness
- Wolves will NOT enter water in any region (instinct-based restriction)
- Wolf Clearing is the designated waiting location when entering Spider Nest Gallery

### Companion Restrictions Matrix

**Region-Level Restrictions:**

| Companion | Cannot Enter | Reason | Wait Location |
|-----------|--------------|--------|---------------|
| Wolf pack | Meridian Nexus | Ancient wards | Nexus boundary |
| Wolf pack | Civilized Remnants (core) | Town guards | Town gates |
| Wolf pack | Sunken District | Can't swim | Region entry |
| Salamander | Sunken District | Water extinguishes | Returns to Nexus |
| Myconid | Frozen Reaches | Extreme cold fatal | Fungal Depths exit |
| Human (Sira) | Deep hazard zones | No equipment | Nearest safe camp |
| Human (Aldric) | Frozen Reaches | Health risk | Civilized Remnants |

**Sub-Location Restrictions** (within regions):

| Companion | Cannot Enter | Region | Reason | Wait Location |
|-----------|--------------|--------|--------|---------------|
| Wolf pack | Spider Nest Gallery | Beast Wilds | Fear/instinct | Wolf Clearing |
| Wolf pack | Spore Heart | Fungal Depths | Instinct avoidance | Luminous Grotto |
| Wolf pack | Deep Roots | Fungal Depths | Instinct avoidance | Luminous Grotto |

### Companion Override Mechanism (Exceptional Circumstances)

In rare dramatic situations, companions may violate their normal restrictions:

**Automatic Triggers (companion chooses):**
- Player health below 20% during combat
- Player trapped with no escape
- One-time per playthrough, costs companion (injury/death)

**Player Command (trust 5+ required):**
- Player can explicitly request companion enter restricted area
- Companion refuses unless trust threshold met
- Success costs -1 trust and risks companion injury

| Override Scenario | Companion | Trigger | Cost |
|-------------------|-----------|---------|------|
| Exceptional bravery | Wolf | Player losing fight in Spider Nest | Wolf injury/possible death |
| Foolhardy sacrifice | Salamander | Player drowning in water | Salamander extinguished (death) |
| Curious explorer | Myconid | High trust + player request | Myconid takes cold damage |

*Both automatic and player-command overrides are one-time per playthrough to preserve dramatic weight.*

### Companion Death

Companions can die permanently:

| Death Cause | Trigger | Consequences |
|-------------|---------|--------------|
| Player action | Forcing salamander into water, abandoning wounded companion | Permanent loss, Echo comments (-1 trust for senseless death) |
| Override sacrifice | Companion enters fatal zone to save player | Permanent loss, Echo acknowledges sacrifice (no trust penalty) |
| Combat death | Companion killed in battle | Permanent loss, Echo comments based on circumstances |
| Neglect | Not healing injured companion | Permanent loss after timer expires, Echo disappointed |

**Companion death is permanent** - companions do not respawn. This gives weight to companion relationships and override decisions.

### Multi-Companion Interactions

| Combination | Initial State | Resolution |
|-------------|---------------|------------|
| Wolf + Sira | Hostile (Sira's prejudice) | Reconciliation dialog required |
| Wolf + Salamander | Mutual wariness | Coexist after 3 turns together |
| Salamander + Human | Comfortable | No issues |
| Wolf + Aldric | Neutral | Aldric nervous but accepting |

---

## Design Observations from Cross-Region Walkthroughs

### From Walkthrough A: Commitment Cascade

**Timer Design Philosophy:**
- Most cross-region timer conflicts are resolvable with reasonable planning
- Sira's 8-turn timer is the intentional "trap" for overcommitted players
- Sunken District dual-rescue (Garrett + Delvan) is designed to be impossible on first playthrough
- This creates meaningful replay value - players learn from failures

**Commitment System Balance:**
- Four fulfilled commitments (+2.0 trust) can offset two abandonments (-1.5 with partial credit)
- This means a well-intentioned but overcommitted player ends up net positive
- The system rewards trying even when some failures occur
- Echo trust math prevents the game from feeling punitive

**Information Flow Design:**
- No immediate notification of offscreen NPC deaths is good design
- Creates discovery moments: returning to find Aldric dead, hearing from Elara about Sira
- Echo always knows - provides guaranteed feedback at Nexus
- Gossip timing creates confession windows that reward honesty

**Player Psychology:**
- Making promises is easy and feels good in the moment
- The cascade only becomes apparent when timers start expiring
- Partial credit acknowledgment prevents frustration
- Multiple paths to recovery maintain player agency

### From Walkthrough B: Companion Journey

**Automatic Companion Management:**
- Auto-waiting at boundaries prevents tedious micromanagement
- Auto-return to safe locations (salamander returns to Nexus) is essential QOL
- Companions rejoin automatically when player returns to waiting location
- No manual "dismiss" command needed for most situations

**Companion Boundaries Are Logical:**
- Wolves: can't enter Nexus (wards), can't swim (instinct), can't handle extreme cold
- Salamander: can't enter water regions (extinguishes), provides cold immunity
- Human companions: need equipment for hazards, can't swim without training
- Each restriction follows from companion nature, not arbitrary rules

**Multi-Companion Dynamics:**
- Wolf+Sira conflict requires reconciliation dialog (trust thresholds)
- Wolf+salamander coexistence is automatic (3 turns together)
- Managing 4+ companions needs clear status display in UI
- Companion idle interactions add life when resting together

**Region-Companion Matching:**
- Frozen Reaches: Salamander is "correct" companion (warmth aura, ice melting)
- Beast Wilds: Wolves are "correct" companion (combat, territory knowledge)
- Sunken District: No companion helps - designed as solo challenge
- Fungal Depths: No single best companion - tradeoffs

**Companion Death Rules (Proposed):**
- Companion can die from deliberate player action (forcing salamander into water)
- Companion can die protecting player ("exceptional bravery" wolf rescue)
- Permanent loss - companions don't respawn
- Echo comments on companion deaths, especially senseless ones

### From Walkthrough C: The Dark Path

**Assassination System:**
- Contracts available through Shadow in undercity
- 3-turn delay from payment to completion (irreversible once paid)
- 20% discovery chance per contract
- Echo knows instantly regardless of discovery (special awareness)
- Trust penalty: -2 per assassination (cumulative)

**Echo Trust Floor (Tiered System):**

| Trust Level | Echo Behavior | Effects |
|-------------|---------------|---------|
| -1 to -2 | **Disappointed** | Normal appearance, dialog is concerned/sad |
| -3 to -5 | **Reluctant** | 5% appearance chance, dialog is cold/distant when appearing |
| -6 or below | **Refuses** | No appearance at all, player loses guidance |

- At trust -3, Echo becomes reluctant - only 5% chance to appear, with cold/disappointed dialog
- At trust -6, Echo refuses to manifest entirely
- Player loses access to commitment tracking and guidance at -6
- Game remains completable - Echo doesn't block mechanics
- Trust can recover through major deeds (+1 cap per deed)
- Recovery from -6 to -2 is possible with multiple major deeds

**Branding Gameplay:**
- Triggered at town reputation -5 or below, or assassination discovery
- Brand is visible mark on player's hand - NPCs react directly (no gossip needed)
- All locations remain accessible (unlike exile)
- Service prices doubled, teaching denied, trust capped at 2
- Good endings blocked until un-branded
- Guardian repair path remains viable (tunnels to Broken Statue Hall)
- Human companions can enter normally and provide cover

**Redemption Valve (Un-branding):**
- Reach reputation +3 while branded + complete heroic act
- Asha performs un-branding ceremony (scar remains but meaning transformed)
- Guardian repair while branded triggers complicated NPC reactions
- Asha may secretly provide town seal despite branding (mercy mechanism)
- **BLOCKED permanently** if assassination discovered - no recovery path

---

## Ending System

### Ending Tier Matrix

| Echo Trust | Waystone Complete | Ending Name | Echo State | Notes |
|------------|-------------------|-------------|------------|-------|
| 5+ | Yes | Triumphant | Fully transformed, becomes companion | Best ending |
| 3-4 | Yes | Successful | Transformed, grateful | Good ending |
| 0-2 | Yes | Bittersweet | Transformed, distant | Neutral ending |
| -1 to -2 | Yes | Hollow Victory | Transformed but silent | Echo disappointed |
| -3 to -5 | Yes | Pyrrhic | Present but won't transform | Echo reluctant (5% appearance during game) |
| -6 or below | Yes | Pyrrhic | Refuses to participate in ceremony | Echo refused to appear during game |
| Any | No | Abandoned | Remains spectral forever | Failed main quest |

*Note: Echo trust tiers affect both in-game appearance (see Echo Trust Floor above) and ending quality.*

### Permanent Locks

- **Triumphant ending**: Locked forever after ANY assassination (even undiscovered)
- **Advanced herbalism**: Lost if Elara killed (no substitute teacher)
- **Hero status**: Impossible after assassination discovery
- **Some council quests**: Unavailable while branded

---

## Version History

- v1.0: Initial creation based on completed regional walkthroughs
- v1.1: Added Walkthrough A observations on timer design, commitment balance, information flow
- v1.2: Added Walkthrough B observations on companion management, boundaries, multi-companion dynamics
- v1.3: Added Walkthrough C observations on assassination, branding, Echo trust floor, ending tiers
- v1.4: Phase 1.5 consistency updates:
  - Standardized timer format to "base + hope bonus = maximum" throughout
  - Added Timer Format Reference table with all NPC timers
  - Added Trust System Overview clarifying Echo Trust vs NPC Trust scales
  - Added detailed Echo Trust tier table (disappointed/-1 to -2, reluctant/-3 to -5, refuses/-6)
  - Expanded Companion Multi-Region Rules with:
    - Salamander water region behavior
    - Wolf cold tolerance zones
    - Companion Restrictions Matrix
    - Companion Override Mechanism (DQ-5 resolution)
    - Companion Death scenarios
  - Added Evidence Checking Mechanics for partial credit system
  - Clarified confession windows as Sira-Elara specific
- v1.5: Phase 2 internal consistency fixes:
  - Added Sub-Location Restrictions table (CC-2)
  - Added Timer trigger vs. hope timing clarification (CC-3)
