# Walkthrough Overview - The Shattered Meridian

## Executive Summary

This document analyzes all six completed region walkthroughs to identify recurring design patterns, extract design principles, and provide guidance for full game implementation. The walkthroughs revealed a remarkably cohesive design philosophy that emerged organically through exploration.

---

## Part 1: Recurring Structural Patterns

### 1.1 The Sanctuary Pattern

**Every region has a safe zone** where the player can recover, plan, and face no threats:

| Region | Sanctuary | Properties |
|--------|-----------|------------|
| Fungal Depths | Myconid Sanctuary | No spores, clean air, neutral NPCs |
| Beast Wilds | Forest Edge | Low danger, entry point, supplies |
| Sunken District | Survivor Camp | Dry ground, fire, NPCs, services |
| Frozen Reaches | Hot Springs Refuge | Instant hypothermia cure, healing, salamanders |
| Civilized Remnants | The entire town | No environmental hazards at all |
| Meridian Nexus | Everything | Absolute safety via magical wards |

**Design Principle**: Players need places to catch their breath. Sanctuaries create pacing rhythm: danger → sanctuary → planning → danger.

### 1.2 The Skill Gate Pattern

**Every region has layered content gated by skills or relationships:**

| Region | Gate | What It Unlocks |
|--------|------|-----------------|
| Fungal Depths | Mycology skill | Safe spore navigation |
| Fungal Depths | Breathing mask | Deep Root Caverns access |
| Beast Wilds | Tracking skill | Hidden paths, creature locations |
| Sunken District | Basic swimming | Flooded areas, Garrett rescue |
| Sunken District | Advanced swimming | Deep Archive access |
| Frozen Reaches | Cold protection | Extended exploration time |
| Civilized Remnants | Basic herbalism | Garden access, safe harvesting |
| Civilized Remnants | Advanced herbalism | Nightshade handling |

**Design Principle**: Skills aren't just numbers - they're narrative permission. Teaching requires trust. Learning requires investment.

### 1.3 The Multi-Solution Encounter Pattern

**Major encounters have 3-4 valid approaches:**

**Temple Golems (Frozen Reaches):**
- Password (research)
- Control crystal (exploration)
- Ritual offering (resource gathering)
- Combat (brute force - deliberately punishing)

**Wolf Pack (Beast Wilds):**
- Feed repeatedly (patience)
- Defeat threat (heroism)
- Fight (difficult)
- Avoid (possible but loses content)

**Spore Mother (Fungal Depths):**
- Heal with heartmoss (quest)
- Wait out hostility (patience)
- Fight (possible but loses alliance)

**Design Principle**: At least one solution should reward patience, one should reward exploration, one should reward relationship-building. Combat should work but feel like the "hard mode."

### 1.4 The Commitment Pattern

**NPCs in distress can receive commitments with meaningful consequences:**

| State | Description | Effect |
|-------|-------------|--------|
| Pending | Player has promised to help | Hope may extend survival, trust building |
| Fulfilled | Promise kept | Base reward + commitment bonus (+2 trust/gratitude) |
| Withdrawn | Player honestly admits inability | Neutral or slight positive, often yields hints |
| Abandoned | Timer expires or NPC dies without player returning | Negative spread, Echo disappointed, trust penalties |

**Critical Mechanic**: Withdrawal is valuable. Returning to say "I can't" often yields helpful information and maintains relationships. Silence is worse than honesty.

### 1.5 The Hope Extension Pattern

**Some NPCs survive longer when they have hope:**

| NPC | Applies? | Notes |
|-----|----------|-------|
| Aldric | Yes | Despair-based illness, hope slows progression |
| Sira | Yes | Bleeding + exhaustion, determination matters |
| Bear Cubs | Yes | Wasting sickness, mother's hope affects them |
| Delvan | Yes | Bleeding, willpower slows blood loss |
| Garrett | No | Drowning - physics doesn't care about promises |
| Spore Mother | No | Too powerful to be affected by hope |
| Salamanders | No | Elemental - not affected, and not in danger |

**Design Principle**: Hope extension should have narrative logic. Drowning, freezing, and elemental beings don't respond to emotional states.

### 1.6 The Cross-Region Connection Pattern

**Every region exports and imports content:**

```
Fungal Depths
├── Exports: Mycology skill, spore resistance, breathing mask, Mother's alliance
└── Imports: Ice crystal (Frozen), gold (Civilized), rare minerals (any)

Beast Wilds
├── Exports: Alpha fang, tracking skill, wolf companion
└── Imports: Healing herbs (Civilized), rare flowers (multiple regions)

Sunken District
├── Exports: Water pearl, swimming skills, enchanted bubble
└── Imports: Items from other regions for Archivist quest fragments

Frozen Reaches
├── Exports: Ice shard, frost lily, ice crystals, salamander companion
└── Imports: Cleaning supplies (Nexus), temple password hints (Nexus)

Civilized Remnants
├── Exports: Town seal, healing herbs, moonpetal, nightshade
└── Imports: Animator crystal (Nexus), healing_herbs destination

Meridian Nexus
├── Exports: Animator crystal, cleaning supplies, password hints
└── Imports: All five waystone fragments
```

---

## Part 2: Hazard Type Distribution

### 2.1 Environmental vs. Social vs. Combat Hazards

| Region | Primary Hazard Type | Examples |
|--------|---------------------|----------|
| Fungal Depths | Environmental | Spore infection, toxic air, darkness |
| Beast Wilds | Combat/Relationship | Hostile packs, territorial behavior |
| Sunken District | Environmental | Drowning, fish attacks, time pressure |
| Frozen Reaches | Environmental | Hypothermia, ice hazards |
| Civilized Remnants | Social | Reputation damage, exile, ethical dilemmas |
| Meridian Nexus | None | Absolute safety |

**Key Discovery**: Environmental hazards and social hazards are NOT combat. They don't reward XP or loot. They're obstacles to navigate around, not enemies to defeat.

### 2.2 Time Pressure Distribution

| Region | Time Pressure | Tension Source |
|--------|---------------|----------------|
| Fungal Depths | Medium | Aldric's declining health (can be stabilized) |
| Beast Wilds | Medium | Sira bleeding, cubs sick (both can be delayed) |
| Sunken District | High | Garrett/Delvan drowning/bleeding (real urgency) |
| Frozen Reaches | None | Salamanders fine without player |
| Civilized Remnants | Variable | Council quests have timers, exploration doesn't |
| Meridian Nexus | None | Echo waits forever |

**Design Principle**: Not every region needs time pressure. Frozen Reaches specifically contrasts with Sunken District's frantic pacing. Variety creates interest.

---

## Part 3: NPC Relationship Patterns

### 3.1 Trust/Gratitude Thresholds

Almost all NPC services and content are gated by relationship thresholds:

| Threshold | Typical Unlocks |
|-----------|-----------------|
| Trust 0 | Basic dialog, minimal services |
| Trust 1 | Expanded dialog, hints |
| Trust 2 | Teaching available (basic skills), supervised access |
| Trust 3 | Full services, advanced teaching, companion option |
| Trust 4+ | Gifts (waystone fragments), special content |
| Trust 5+ | Deep backstory, hidden quests |

### 3.2 State Machine Pattern

**All significant NPCs use explicit state machines:**

```
NPC State Flow:
hostile → wary → neutral → friendly → companion/allied

Transitions require specific actions:
- Feeding (wolves, salamanders)
- Healing (Aldric, cubs, Spore Mother)
- Gifts (appropriate items)
- Time (patience)
- Dialog (meaningful conversation)
```

### 3.3 Pack/Follower Pattern

**Many NPCs exist in leader/follower relationships:**

| Leader | Followers | Behavior |
|--------|-----------|----------|
| Alpha Wolf | Grey wolves 1-3 | Follow alpha state and location |
| Spore Mother | Sporelings 1-3 | Bound to Mother's presence |
| Spider Queen | Giant spiders | Respawn while queen lives |
| Bee Queen | Bee swarm | Attack as unit |
| Steam Salamander 1 | Salamanders 2-3 | Follow leader's relationship state |

**Design Principle**: Changing the leader changes the group. This creates efficient mechanics and narrative coherence.

---

## Part 4: The Companion Restriction System

### 4.1 Restriction Matrix

| Companion Type | Cannot Enter | Uncomfortable In | Narrative Justification |
|----------------|--------------|------------------|------------------------|
| Wolves | Nexus, Civilized | Spider Nest | Wards repel, guards attack |
| Bears | Nexus, Civilized | Frozen Reaches | Wards repel, won't stray far |
| Salamanders | Sunken District | Beast Wilds, Civilized | Water extinguishes fire |
| Myconids | Frozen Reaches | Beast/Civilized | Cold kills, fear of fungi |
| Humans | None | Various hazard zones | Most flexible, most vulnerable |

### 4.2 Design Rationale

**Restrictions create meaningful choices:**
- Can't bring wolf pack to help with town problems
- Can't bring salamander to help in Sunken District
- Must plan which companion to use where

**Restrictions are dispositions, not iron laws:**
- Exceptional bravery can override some
- Narrative moments can justify exceptions
- Player choice + NPC personality

---

## Part 5: Item Flow and Economy

### 5.1 Waystone Fragment Sources

| Fragment | Region | Requirement |
|----------|--------|-------------|
| Spore Heart | Fungal Depths | Heal Spore Mother (gift) |
| Alpha Fang | Beast Wilds | High wolf trust (trust 5, gift) |
| Water Pearl | Sunken District | Complete Archivist quest (3/5 fragments) |
| Ice Shard | Frozen Reaches | Extract from ice caves (exploration) |
| Town Seal | Civilized Remnants | Hero status OR Guardian repair |

**Pattern**: Each fragment requires different skills - relationship-building, exploration, quest completion, reputation.

### 5.2 Teaching Economy

| Skill | Teacher | Location | Requirements |
|-------|---------|----------|--------------|
| Mycology | Aldric | Fungal Depths | Trust 2, stabilized, gift |
| Spore Resistance | Myconid Elder | Fungal Depths | Trust 2, payment |
| Swimming (Basic) | Old Jek | Sunken District | Payment |
| Swimming (Advanced) | Garrett | Sunken District | Garrett rescued + recovered |
| Tracking | Sira | Beast Wilds | Trust 2, healthy |
| Herbalism (Basic) | Maren | Civilized Remnants | Trust 2, payment |
| Herbalism (Advanced) | Elara | Civilized Remnants | Trust 3, help or payment |

**Two-Tier Pattern**: Basic skills from one source, advanced from another (swimming, herbalism). Creates progression within regions.

---

## Part 6: Discovered Design Principles

### 6.1 Principles to Reinforce

1. **Environmental hazards ≠ combat**: No XP, no loot. Avoidance is the intended solution.

2. **Combat is hard mode, not forbidden**: Players can fight anything, but puzzle solutions should be clearly preferable.

3. **NPCs need narrative justification for limitations**: Why can't Aldric get his own silvermoss? Why can't the Archivist leave? Every limitation needs a reason.

4. **Withdrawal is valuable**: Returning to say "I can't help" yields hints and maintains relationships. Better than silence.

5. **Hope extends survival situationally**: Drowning doesn't care, but despair-based deaths can be delayed.

6. **Each region has distinct hazard vocabulary**: Spores, water, cold, beasts, social reputation. Don't mix unnecessarily.

7. **Sanctuaries create pacing**: Every region needs a place to plan without pressure.

8. **Skills are narrative permission**: Teaching requires relationship. Learning requires investment.

9. **Commitments spread consequences**: The Echo knows everything. NPCs talk to each other. Actions have cross-region effects.

10. **Dark paths exist but have massive consequences**: Assassination is available. Exile is possible. Echo always knows.

### 6.2 Principles to Avoid

1. **Don't create time pressure everywhere**: Frozen Reaches specifically has none. Variety matters.

2. **Don't make combat the only solution**: Multiple approaches for every significant encounter.

3. **Don't punish exploration**: Hidden content (control crystal) should be the best solution, not a trap.

4. **Don't require specific companions**: Alternative paths should exist for every companion-gated content.

5. **Don't let NPCs exist without social connections**: Elara knows Sira. Delvan knows the undercity. The network creates verisimilitude.

6. **Don't make environmental hazards feel like enemies**: They're conditions to manage, not opponents to defeat.

7. **Don't hide critical information**: Hints available through dialog, journals, observation. Obscure optional content, not required content.

---

## Part 7: The Echo and Commitment System

### 7.1 Echo Trust Mechanics

| Trust Range | Effect |
|-------------|--------|
| -5 to -3 | Echo refuses to appear |
| -2 to 0 | Distant, brief appearances |
| 1-2 | Helpful, clearer form |
| 3-4 | Warm, shares freely |
| 5 | Speaks player's name |
| 6+ | Full backstory revealed |

**Recovery from negative**: Actions only, not words. Max +1 per visit through genuine good behavior.

### 7.2 Commitment Consequence Spread

```
Player abandons commitment in Region A
↓
Echo knows immediately (ley line network)
↓
Echo confronts player in Nexus
↓
Over time, NPCs in Region B learn through:
- Direct witnesses
- Traveling NPCs
- Gossip networks (Elara-Sira connection)
- Echo's influence spreading
↓
Trust/reputation penalties in Region B
```

### 7.3 Confession vs. Discovery

**Critical Pattern** (established in Civilized Remnants walkthrough):

| Scenario | Consequence |
|----------|-------------|
| Player confesses broken commitment | -2 trust, respect for honesty, recovery possible |
| NPC discovers through other means | -3 trust, permanent consequences, relationship damaged |

Example: If player abandons Sira (Beast Wilds) and confesses to Elara, Elara is disappointed but teaching continues. If Elara learns from others, advanced herbalism permanently denied.

---

## Part 8: Crystal Restoration and Progress Tracking

### 8.1 Crystal Buffs

| Crystal | Color | Restores When | Buff |
|---------|-------|---------------|------|
| Fungal | Green with movement | Spore Mother healed OR Aldric saved | Slow poison/infection |
| Beast | Tawny/amber | Wolf trust high OR cubs saved | +10 max health |
| Water | Blue, rippling | Archivist quest complete OR major rescue | Improved breath |
| Frozen | Blue-white | Telescope repaired OR major healing | Cold resistance |
| Civilization | Warm golden | Guardian repaired OR hero status | Better prices |

**Design Principle**: Crystals provide visual progress tracking AND permanent mechanical benefits. Rewards healing in the world.

### 8.2 Cumulative Benefits

Each restored crystal adds +1 to relevant stat when in that region. Multiple crystals stack their benefits. This rewards completing multiple regions rather than rushing to endgame.

---

## Part 9: Recommendations for Implementation

### 9.1 Priority Systems to Build

1. **State machine system for NPCs**: Every significant NPC needs explicit states and transitions
2. **Trust/gratitude tracking**: Relationships need numbers that affect unlocks
3. **Commitment tracking**: Pending/fulfilled/withdrawn/abandoned with Echo awareness
4. **Environmental condition system**: Hypothermia, infection, drowning as progressive states
5. **Skill gating**: Teaching services require trust thresholds
6. **Cross-region flag propagation**: Events in one region affect NPCs in others

### 9.2 Content to Verify

Before implementation, verify:
- Every NPC has a state machine
- Every significant encounter has 3+ solutions
- Every region has a sanctuary
- Every waystone fragment has clear acquisition path
- Every companion has meaningful restrictions
- Every commitment has all four outcome states defined

### 9.3 Testing Priorities

1. **Dual rescue in Sunken District**: The hardest timing challenge
2. **Cross-region commitment spread**: Elara learning about Sira
3. **Crystal restoration triggers**: Each condition properly tracked
4. **Echo trust recovery**: Actions-only recovery from negative
5. **Companion restrictions at boundaries**: Proper feedback when blocked

---

## Part 10: Characteristic Observations

### 10.1 What Makes This Design Cohesive

1. **Consistent mechanics across regions**: Trust thresholds, state machines, sanctuary pattern
2. **Distinct flavor per region**: Each has unique hazard vocabulary while sharing structure
3. **Interconnected world**: NPCs know each other, items flow between regions, consequences spread
4. **Player agency preserved**: Multiple solutions, dark paths available, no forced outcomes
5. **Commitment system as moral backbone**: Echo tracks everything, creating accountability without preaching

### 10.2 Emergent Themes

Through the walkthroughs, several themes emerged that weren't explicitly designed:

- **Patience rewarded**: Every region has content that opens through waiting, feeding, talking
- **Violence closes doors**: Combat works but often removes options permanently
- **Honesty valued**: Withdrawal (admitting inability) often yields hints and maintains relationships
- **Healing as progress**: The crystal system makes healing the world into visible progression
- **Connection creates consequence**: The NPC relationship network means actions ripple outward

### 10.3 What Would Break the Design

Avoid these implementation choices:
- Time pressure in every region (destroys pacing variety)
- Combat as primary solution (closes too many paths)
- Isolated NPCs with no connections (breaks consequence spread)
- Harsh penalties for exploration (control crystal should reward thoroughness)
- Silent abandonment without Echo commentary (removes moral weight)

---

## Appendix: File Reference

| File | Purpose |
|------|---------|
| `fungal_depths_sketch.json` | Region 1 design |
| `fungal_depths_walkthrough.md` | Region 1 exploration |
| `beast_wilds_sketch.json` | Region 2 design |
| `beast_wilds_walkthrough.md` | Region 2 exploration |
| `sunken_district_sketch.json` | Region 3 design |
| `sunken_district_walkthrough.md` | Region 3 exploration |
| `frozen_reaches_sketch.json` | Region 4 design |
| `frozen_reaches_walkthrough.md` | Region 4 exploration |
| `civilized_remnants_sketch.json` | Region 5 design |
| `civilized_remnants_walkthrough.md` | Region 5 exploration |
| `meridian_nexus_sketch.json` | Hub region design |
| `meridian_nexus_walkthrough.md` | Hub exploration |
| `walkthrough_guide.md` | Methodology and patterns |
| `walkthrough_handoff.md` | Status and decisions to preserve |
| `cross_region_dependencies.md` | Item and NPC flows |

---

*Generated after completion of all six region walkthroughs.*
