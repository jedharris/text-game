# Cross-Region Dependencies - The Shattered Meridian

This document maps all dependencies between regions, showing how items, NPCs, and events in one region affect others.

## World Map

```
                    [Frozen Reaches]
                          |
                          |
    [Fungal Depths] --- [Meridian Nexus] --- [Sunken District]
                          |
                          |
                    [Beast Wilds]
                          |
                          |
                    [Civilized Remnants]
```

---

## Waystone Repair Quest (Major Cross-Region)

The damaged waystone in Meridian Nexus requires one item from each region's heart:

| Item | Source Region | Source Location | How Obtained |
|------|---------------|-----------------|--------------|
| Spore Crystal | Fungal Depths | Spore Heart | Heal the Spore Mother (she gifts it) |
| Ice Shard | Frozen Reaches | Ice Caves | Exploration, careful extraction |
| Water Pearl | Sunken District | Deep Archive | Advanced swimming + light source |
| Alpha Fang | Beast Wilds | Wolf Clearing | High trust (5+) with Alpha Wolf |
| Town Seal | Civilized Remnants | Council Hall | Complete major council quest |

**Reward**: Fast travel between all regions, The Echo becomes permanent, Meridian Blessing buff

---

## Item Dependencies

### Items Needed FROM Other Regions

| Region | Item Needed | Source Region | Purpose |
|--------|-------------|---------------|---------|
| **Fungal Depths** | Ice Crystals | Frozen Reaches | Myconid payment for services |
| **Beast Wilds** | Healing Herbs | Civilized Remnants | Cure bear cubs' wasting sickness |
| **Beast Wilds** | Moonpetal | Civilized Remnants OR Fungal Depths | Bee Queen trade |
| **Beast Wilds** | Frost Lily | Frozen Reaches | Bee Queen trade |
| **Beast Wilds** | Water Bloom | Sunken District | Bee Queen trade |
| **Frozen Reaches** | Cleaning Supplies | Meridian Nexus | Telescope repair |
| **Civilized Remnants** | Animator Crystal | Meridian Nexus | Guardian repair |

### Items Exported TO Other Regions

| Region | Item Available | Destination | Purpose |
|--------|----------------|-------------|---------|
| **Fungal Depths** | Spore Crystal | Nexus | Waystone repair |
| **Fungal Depths** | Moonpetal | Beast Wilds | Bee Queen trade |
| **Frozen Reaches** | Ice Shard | Nexus | Waystone repair |
| **Frozen Reaches** | Frost Lily | Beast Wilds | Bee Queen trade |
| **Frozen Reaches** | Ice Crystals | Fungal Depths | Myconid payment |
| **Sunken District** | Water Pearl | Nexus | Waystone repair |
| **Sunken District** | Water Bloom | Beast Wilds | Bee Queen trade |
| **Beast Wilds** | Alpha Fang | Nexus | Waystone repair |
| **Civilized Remnants** | Town Seal | Nexus | Waystone repair |
| **Civilized Remnants** | Healing Herbs | Beast Wilds | Bear cub cure |
| **Meridian Nexus** | Animator Crystal | Civilized Remnants | Guardian repair |
| **Meridian Nexus** | Cleaning Supplies | Frozen Reaches | Telescope repair |
| **Meridian Nexus** | Temple Password | Frozen Reaches | Golem deactivation |

---

## NPC Dependencies

### NPCs That Move Between Regions

| NPC | Original Region | Can Move To | Condition |
|-----|-----------------|-------------|-----------|
| Aldric (Scholar) | Fungal Depths | Nexus, Civilized Remnants | If cured/stabilized |
| Wolf Pack | Beast Wilds | Nexus (no), C. Remnants (no), Others (yes) | If domesticated |
| Hunter Sira | Beast Wilds | Any region | If companion |
| Sailor Garrett | Sunken District | Stays in camp | If rescued |
| Steam Salamanders | Frozen Reaches | Nexus (yes), Others (uncomfortable) | If befriended |

### NPCs That Affect Other Regions

| NPC | Action | Cross-Region Effect |
|-----|--------|---------------------|
| Spore Mother | Healed | Fungal infection stops spreading to other regions |
| Myconids | Alliance (trust 5+) | Healing items occasionally appear in player inventory |
| Delvan (Merchant) | Rescued | Black market access in Civilized Remnants |
| The Echo | Trust increases | Appears in other regions at critical moments |
| Healer Elara | Trust 5+ | Impressed by healing NPCs from other regions (+trust) |

---

## Environmental Spread Effects

### Infection Spread (Fungal Depths → Others)
**Trigger**: Spore Mother not healed within turn threshold

| Turn Count | Effect |
|------------|--------|
| 50 | Spores begin appearing in Beast Wilds (Forest Edge) |
| 100 | Town Gate guards begin checking for infection |
| 150 | NPCs in Civilized Remnants may become infected |

**Prevention**: Heal Spore Mother (alliance + heartmoss)

### Cold Spread (Frozen Reaches → Others)
**Trigger**: Observatory telescope not repaired

| Turn Count | Effect |
|------------|--------|
| 75 | Cold zones appear in Beast Wilds (high ground) |
| 125 | Nexus boundary areas become cold |
| 175 | Some Sunken District water freezes (new routes, new hazards) |

**Prevention**: Repair observatory telescope

---

## Companion Restrictions

Restrictions are **dispositions, not iron laws** - an especially brave or foolhardy individual might ignore them in dramatic moments.

See `beast_wilds_sketch.json` companion_restrictions section for the full detailed table by actor type.

### Cannot Enter (Hard Restrictions)

| Actor Type | Cannot Enter | Reason |
|------------|--------------|--------|
| Wolves | Nexus | Magical wards repel beasts |
| Wolves | Civilized Remnants | Guards attack beasts on sight |
| Wolves | Spider Nest Gallery | Territorial instinct (override: exceptional bravery) |
| Bears | Nexus | Magical wards repel beasts |
| Bears | Civilized Remnants | Guards attack beasts on sight |
| Steam Salamanders | Sunken District | Elemental conflict - water extinguishes fire |
| Myconids | Frozen Reaches | Cold kills fungal life |
| Humans | None | Most flexible, but vulnerable to hazards |

### Uncomfortable In (Soft Restrictions)

| Actor Type | Uncomfortable In | Effect |
|------------|------------------|--------|
| Wolves | Sunken District | Combat penalties, may refuse deep water |
| Bears | Frozen Reaches | Reduced endurance, seeks shelter |
| Steam Salamanders | Beast Wilds | Minor penalties, frequent complaints |
| Steam Salamanders | Civilized Remnants | NPCs react with fear |
| Myconids | Beast Wilds | Dry air, predators - reduced effectiveness |
| Myconids | Civilized Remnants | Townsfolk fear infection - hostile reactions |
| Humans | Fungal Deep Roots | Spore damage without protection |
| Humans | Frozen Ice Caves | Cold damage without gear |
| Humans | Sunken Deep Archive | Cannot access without swimming skill |

### Exceptional Individuals

Individual actors can have `ignores_restriction` flags for specific locations. This should be rare and narratively motivated:
- A particularly brave wolf might follow player into spider territory to protect them
- A foolhardy salamander might sacrifice itself in Sunken District
- A curious myconid explorer might venture into Beast Wilds

---

## Skill Dependencies

Skills learned in one region that benefit others:

| Skill | Learned In | Teacher | Benefits In |
|-------|------------|---------|-------------|
| Swimming (Basic) | Sunken District | Old Swimmer Jek | Any water area |
| Swimming (Advanced) | Sunken District | Old Swimmer Jek (after Garrett rescued) | Deep Archive, cold water |
| Tracking | Beast Wilds | Hunter Sira | Any region (find hidden paths) |
| Herbalism (Basic) | Civilized Remnants | Herbalist Maren | Identify dangerous plants |
| Herbalism (Full) | Civilized Remnants | Healer Elara | Harvest any plant safely |
| Mycology | Fungal Depths | Scholar Aldric | Navigate spore areas |
| Spore Resistance | Fungal Depths | Myconids | Fungal Depths survival |

---

## Reputation Spread

Word of player actions spreads:

| Action Type | Spreads To | Effect |
|-------------|------------|--------|
| Rescue NPCs | All regions | NPCs friendlier (+1 initial disposition) |
| Kill friendly NPCs | All regions | NPCs warier (-1 initial disposition) |
| Heal Spore Mother | Civilized Remnants (Healer Elara) | +2 trust with Elara |
| Save Aldric | Civilized Remnants (Healer Elara) | +1 trust with Elara |
| High town reputation | Beast Wilds (Hunter Sira) | Sira more willing to trust |
| Undercity crimes (discovered) | Town NPCs | -2 reputation |

---

## Gossip Timing System

Information spreads between regions at different rates depending on the source.

### Gossip Channels

| Channel | Speed | Description |
|---------|-------|-------------|
| **Echo Network** | Instant | Echo knows everything through ley lines. Will comment on any commitment. |
| **Traveling NPCs** | 10-20 turns | Merchants, refugees move between regions |
| **NPC Connections** | 5-15 turns | Direct relationships (Elara-Sira, Delvan-undercity) |
| **Reputation Spread** | 20-30 turns | General word of mouth across all regions |

### Specific Gossip Paths

| Information | Source | Destination | Timing | Notes |
|-------------|--------|-------------|--------|-------|
| Sira's fate | Beast Wilds | Elara (Civilized) | 10-15 turns | Travelers mention injured hunter. If Sira dies, news reaches Elara. |
| Sira abandonment | Beast Wilds | Elara (Civilized) | 15-25 turns | Only spreads if Sira survives AND tells others. Or through Echo influence. |
| Aldric's fate | Fungal Depths | Civilized Remnants | 20-30 turns | Scholar's fate becomes known over time |
| Delvan's fate | Sunken District | Undercity | 5-10 turns | Fast - criminal networks communicate quickly |
| Assassination | Civilized Remnants | Echo | Instant | Echo always knows immediately |
| Assassination | Civilized Remnants | Other councilors | 0-5 turns | Depends on discovery roll (20%) |
| Exile status | Civilized Remnants | Beast Wilds (Sira) | 15-20 turns | Word reaches other regions eventually |
| Spore Mother healed | Fungal Depths | All regions | 10-20 turns | Major event, spreads relatively fast |

### Confession vs. Discovery Timing

The "confession window" matters for the Sira-Elara connection:

| Scenario | Timing | Outcome |
|----------|--------|---------|
| Player confesses before gossip arrives | N/A | Confession mechanic: -2 trust, recovery possible |
| Gossip arrives before player visits Elara | 15-25 turns after abandonment | Discovery mechanic: -3 trust, permanent consequences |
| Player visits Elara, doesn't confess, gossip arrives later | Variable | Discovery + lie by omission: -4 trust, relationship destroyed |

### Gossip Triggers

Information only spreads if certain conditions are met:

| Information | Trigger Condition |
|-------------|-------------------|
| NPC death | Death is witnessed or discovered |
| Commitment abandoned | NPC dies or tells someone before dying |
| Reputation change | Major action (+/-3 reputation) triggers spread |
| Skill learned | No automatic spread (private knowledge) |
| Items acquired | No automatic spread unless stolen |

### Manipulating Gossip

Players can influence information spread:

| Action | Effect |
|--------|--------|
| Confess to affected NPC | Preempts gossip, reduces penalty |
| Kill all witnesses | Information doesn't spread (but Echo still knows) |
| Help NPC who would gossip | May reduce likelihood of negative spread |
| Complete quest quickly | May outrace gossip entirely |

---

## Crystal Garden Progress (Nexus)

Each major healing/restoration in regions advances the crystal garden:

| Achievement | Crystal Effect |
|-------------|----------------|
| Heal Spore Mother | Crystal 1: +10 max health |
| Repair Observatory | Crystal 2: Slow poison/infection |
| Rescue both survivors (Sunken) | Crystal 3: Improved breath holding |
| Befriend Dire Bear | Crystal 4: Cold resistance |
| Repair Guardian | Crystal 5: Merchant discounts |

---

## Critical Path Analysis

### If Player Goes to Fungal Depths First:
- Can stabilize Aldric with silvermoss (local)
- Cannot fully cure without heartmoss (requires Deep Roots exploration)
- Myconid mask/lantern help with Deep Roots
- Ice crystals from Frozen Reaches can pay for Myconid services

### If Player Goes to Beast Wilds First:
- Can domesticate wolves (local resources)
- Cannot heal bear cubs without herbs from Civilized Remnants
- Spider nest has no external dependencies
- Bee Queen trade requires flowers from 3 other regions

### If Player Goes to Sunken District First:
- Can learn swimming (local)
- Can rescue Garrett and Delvan (local, time-sensitive)
- Deep Archive access requires advanced swimming OR archivist bubble

### If Player Goes to Frozen Reaches First:
- Cold survival difficult without preparation
- Temple golems very hard without password from Nexus
- Hot Springs provides safe haven
- Salamander befriending possible with fire items

### If Player Goes to Civilized Remnants First:
- Easiest start - no environmental hazards
- Can learn herbalism, buy supplies
- Guardian repair requires Nexus item
- Provides healing herbs for Beast Wilds

---

## Recommended Exploration Patterns

### Peaceful/Diplomatic Path
1. Civilized Remnants → get herbs, learn herbalism
2. Beast Wilds → heal cubs, start wolf domestication, meet Sira
3. Fungal Depths → use herbs knowledge, help Aldric, earn Myconid trust
4. Frozen Reaches → use preparations, befriend salamanders
5. Sunken District → swimming, rescues
6. Return visits for cross-region completions

### Efficient/Speedrun Path
1. Nexus → get telescope hint about urgent situations
2. Most urgent region first (based on telescope)
3. Collect waystone components as you go
4. Complete repair for fast travel

### Completionist Path
1. Explore each region partially
2. Note all cross-region needs
3. Systematic completion with backtracking
4. All crystals, all NPCs saved, all skills learned

---

## Summary Table: What Each Region Provides

| Region | Unique Resources | Key Skills | Key NPCs | Main Challenge |
|--------|------------------|------------|----------|----------------|
| Nexus | Guidance, safe haven, animator crystal | None | The Echo | None (safe zone) |
| Fungal Depths | Spore crystal, silvermoss, heartmoss | Mycology, Spore Resistance | Aldric, Myconids, Spore Mother | Infection, darkness |
| Beast Wilds | Alpha fang, royal honey, spider silk | Tracking | Wolf Pack, Dire Bear, Sira | Pack dynamics, timing |
| Sunken District | Water pearl, water bloom | Swimming | Garrett, Delvan, Archivist | Drowning, time pressure |
| Frozen Reaches | Ice shard, frost lily, ice crystals | None (gear-based) | Salamanders | Cold, golems |
| Civilized Remnants | Town seal, healing herbs, moonpetal | Herbalism | Elara, Council | Social/ethical |

---

## Commitment System

Player commitments ("I'll help you", "I'll find the silvermoss for you") create stakes beyond the base deed.

### Commitment States

| State | Meaning | Effect |
|-------|---------|--------|
| **pending** | Player has committed, not yet fulfilled | NPC waits, may have extended survival |
| **fulfilled** | Player delivered on promise | Base reward + bonus (+2 trust/gratitude typically) |
| **withdrawn** | Player explicitly returned and said they can't help | Neutral or small positive (honesty valued). NPC may offer helpful hints. |
| **abandoned** | NPC dies or timer expires without player returning | Negative spread to related NPCs. The Echo disappointed. |

### Key Commitments by Region

| Region | NPC | Commitment | Hope Extends Survival? | Cross-Region Effects if Abandoned |
|--------|-----|------------|------------------------|-----------------------------------|
| Fungal Depths | Aldric | Find silvermoss | Yes (+10 turns) | Myconids lose trust, Echo disappointed |
| Fungal Depths | Spore Mother | Find heartmoss | No | Myconids lose trust (-2) |
| Beast Wilds | Dire Bear | Heal cubs | Yes (+5 turns) | Sira comments negatively, Echo disappointed |
| Beast Wilds | Hunter Sira | Save her | Yes (+4 turns) | Elara loses trust if she learns |
| Sunken District | Garrett | Rescue from drowning | No | Jek refuses advanced lessons, camp morale drops |
| Sunken District | Delvan | Free and heal | Yes (+3 turns) | Black market access lost, camp morale drops |
| Civilized Remnants | Council | Complete quest | N/A | Reputation -2, councilor won't support |
| Civilized Remnants | Elara | Bring herbs for patient | No | Trust -2 if patient dies |

### The Echo as Witness

The Echo in the Nexus monitors all commitments through the ley line network:
- Knows when promises are made, kept, or broken
- Dialog changes based on commitment history
- Player can ask Echo about their promises for a summary
- Broken commitments reduce Echo trust, potentially locking endings

### Withdrawal Is Valuable

Coming back to apologize is a **positive action**:
- Shows courage and concern
- NPC often provides helpful information or items
- Player can recommit later in most cases
- No trust penalty (sometimes small positive)

Example withdrawal responses:
- **Aldric**: Reveals Myconid equipment exists, offers journal
- **Dire Bear**: Gestures toward Civilized Remnants (herb source)
- **Spore Mother**: (via Myconid) Mentions Hot Springs as preparation help
- **Delvan**: Gives lockbox combination

### Cross-Region Commitment Spread

| Broken Promise | Who Learns | Effect |
|----------------|------------|--------|
| Aldric dies | Myconids, Echo | Myconids mention "hollow words", Echo disappointed |
| Sira dies | Elara | Elara loses trust (-2) |
| Garrett dies | Jek, Mira | Jek refuses teaching, Mira trust drops |
| Bear cubs die | Sira | Sira questions player's character |
| Council quest failed | Town NPCs | Reputation spreads
