# Frozen Reaches Detailed Design

**Version**: 0.2
**Last Updated**: 2025-12-11
**Status**: Draft

---

## 0. Authoring Guidance

### 0.1 Region Character

The Frozen Reaches is an **environmental puzzle region** that rewards patience and preparation over urgency. Unlike regions with dying NPCs and tight timers, this region emphasizes methodical exploration, resource management (warmth), and multiple solutions to obstacles. The hot springs serve as a sanctuary for planning, and the salamanders offer friendship without desperation.

### 0.2 Content Density Expectations

- **Entity density**: Moderate (5 locations, 5 NPCs - 2 golems, 3 salamanders)
- **NPC interaction depth**: Moderate (salamanders befriendable, golems puzzle/combat)
- **Environmental complexity**: Complex (4 temperature zones, hypothermia system)
- **Time pressure**: None (no dying NPCs, no urgent commitments)

### 0.3 What Belongs Here

- Environmental hazards requiring preparation (cold, thin ice)
- Puzzles with multiple solutions (golem deactivation: password, crystal, ritual, combat)
- Non-verbal NPC communication (salamander gestures)
- Exploration rewards (hidden control crystal, fire crystal in side chamber)
- Strategic information gathering (telescope reveals other regions)
- Resource management (warmth sources, hypothermia recovery)
- Items for cross-region trade (ice crystals, frost lily, ice shard)

### 0.4 What Does NOT Belong Here

- **Time-pressured NPC rescues** - Salamanders are elementals, not dying. No urgent commitments.
- **Dense NPC populations** - This is a harsh, depopulated environment. Only salamanders and golems.
- **Easy combat** - Golems are puzzle encounters first. Combat is "hard mode" and deliberately punishing.
- **Instant solutions** - Items frozen in ice require heat and time to extract. Patience rewarded.

### 0.5 Authoring Notes

- **Contrast with other regions**: This region provides pacing variety. Where Sunken District has frantic dual-rescue and Beast Wilds has bleeding NPCs, Frozen Reaches is methodical.
- **Salamander as gear alternative**: The salamander companion provides cold immunity, making it an alternative to the cold resistance cloak. This is intentional - gear vs relationship choice.
- **Telescope as strategic reward**: Completing the telescope provides information about ALL other regions. This rewards players who explore here early or thoroughly.
- **Hot springs as sanctuary**: The hot springs function like the Nexus - a safe place to recover and plan. Design content that encourages retreating here.
- **Fire items are precious**: Fire-aspected items (torch, fire crystal) enable salamander befriending and ice extraction. Don't make them too plentiful.

### 0.6 Difficulty Design Notes

**Designed challenges** (intended to be hard):
- **Golem combat is "hard mode"**: ~36 rounds with optimal tactics, very resource-intensive. This is intentional - combat should feel like the wrong choice.
- **Extreme cold in observatory**: Without cloak or salamander, 5 turns max survival. Players must solve temple puzzle OR befriend salamanders before attempting.
- **Fire items are deliberately scarce**: Only one fire crystal in the region. Players must choose: use it for salamanders OR ice extraction OR keep for later.

**Fair challenges** (hard but solvable with preparation):
- **Hypothermia system**: Rates are tuned so players can reach safety if they don't dawdle. Hot springs provide instant cure.
- **Golem puzzle**: Four solutions of varying difficulty - password (easy research), ritual (easy resources), control crystal (medium exploration), combat (hard).
- **Ice extraction**: Heat + patience. No trick - just requires bringing fire source.

**First-playthrough expectations**:
- **Likely to accomplish**: Survive to hot springs, befriend salamanders (if patient), find cold weather gear, discover password from inscriptions
- **Likely to fail or miss**: Control crystal (hidden passage), optimal telescope repair (requires cross-region fetch), golem combat victory
- **Teaches for next time**: Preparation > rushing, multiple solutions exist, retreat is valid strategy

**No urgency is the design**:
- This region has NO dying NPCs, NO ticking timers, NO commitments that can be abandoned
- Players who feel urgent here have imported that feeling from elsewhere
- The region rewards methodical exploration and returning to hot springs to warm up

---

## 1. Required Entities

### 1.1 Required Locations

| Location ID | Name | Purpose | Source |
|-------------|------|---------|--------|
| `frozen_pass` | Frozen Pass | Entry point; abandoned camp with supplies and map | `big_game_overview.md` |
| `hot_springs_refuge` | Hot Springs Refuge | Safe sanctuary; salamander home | `big_game_overview.md` |
| `ice_caves` | Ice Caves | Treasure location; ice shard, crystal lens, control crystal | `big_game_overview.md` |
| `temple_sanctum` | Temple Sanctum | Golem puzzle; cloak, bracket, lore tablets | `big_game_overview.md` |
| `frozen_observatory` | Frozen Observatory | Telescope repair; strategic reward | `big_game_overview.md` |

**Location Details:**

**frozen_pass**:
- Temperature zone: Cold
- Properties: `hypothermia_rate: 5`, `lighting: "bright"`, `danger_level: "low"`
- Required exits: south → `nexus_chamber`, north → `temple_sanctum`, east → `ice_caves`, west → `hot_springs_refuge`
- Key features: Abandoned camp (cold weather gear, preserved supplies, partial map), frozen travelers (environmental storytelling)
- Sensory hints: Biting wind, snow that doesn't melt, ice crystals in the air, impossible silence between gusts

**hot_springs_refuge**:
- Temperature zone: Normal (warm)
- Properties: `hypothermia_effect: "instant_cure"`, `healing_zone: true`, `safe_zone: true`
- Required exits: east → `frozen_pass`
- Key features: Hot springs (instant hypothermia cure, +5 health/turn), salamander home
- Actors: `steam_salamander_1`, `steam_salamander_2`, `steam_salamander_3`
- Sensory hints: Sulfurous mist, warmth like an embrace, multicolored mineral deposits

**ice_caves**:
- Temperature zone: Freezing
- Properties: `hypothermia_rate: 10`, `lighting: "variable"`, `danger_level: "medium"`
- Required exits: west → `frozen_pass`
- Sub-locations:
  - Main chamber: ice crystals (walls), frost lily
  - Deep section: ice shard (in frozen pool behind thin ice), crystal lens (frozen in wall)
  - Side passage (hidden): control crystal (frozen in wall)
- Hazards: Thin ice (breaking through = drowning + cold damage + hypothermia spike)
- Sensory hints: Crystal blue walls, breath freezing instantly, cracking sounds underfoot

**temple_sanctum**:
- Temperature zone: Cold
- Properties: `hypothermia_rate: 2.5`, `lighting: "dim"`, `danger_level: "high (conditional)"`
- Required exits: south → `frozen_pass`, up → `frozen_observatory`
- Key features: Golem guardians, altar with mounting bracket, alcove with cold resistance cloak, wall inscriptions (password hints), side chamber with fire crystal (accessible without defeating golems - side chamber is near entrance)
- Actors: `stone_golem_1`, `stone_golem_2`
- Cover system: Stone pillars provide 80% damage reduction
- Guardian behavior: Territorial (don't leave temple), threshold pause (won't attack in doorway)
- Sensory hints: Ancient carved stone faces, glowing runes, grinding stone sounds

**frozen_observatory**:
- Temperature zone: Extreme cold
- Properties: `hypothermia_rate: 20`, `lighting: "bright"`, `danger_level: "environmental"`
- Required exits: down → `temple_sanctum`
- Key features: Damaged telescope (requires 3 components to repair)
- Time limits: Without protection 5 turns, with cloak 15 turns, with salamander unlimited
- When telescope repaired: Reveals NPC states in all regions, prevents cold spread, +1 crystal garden progress
- Sensory hints: Wind trying to tear you away, stars visible during day, staggering view of broken world

### 1.2 Required NPCs

| Actor ID | Name | Role | Commitment Timer | Source |
|----------|------|------|------------------|--------|
| `stone_golem_1` | Stone Guardian | Puzzle encounter / optional combat | N/A | `big_game_overview.md` |
| `stone_golem_2` | Stone Guardian | Linked to golem_1 | N/A | `big_game_overview.md` |
| `steam_salamander_1` | Steam Salamander (Lead) | Befriendable, potential companion | N/A | `big_game_overview.md` |
| `steam_salamander_2` | Steam Salamander | Follows lead salamander | N/A | `big_game_overview.md` |
| `steam_salamander_3` | Steam Salamander | Follows lead salamander | N/A | `big_game_overview.md` |

**Stone Golem - Full Specification:**

- **Nature**: Ancient construct, guardian of the temple and observatory
- **Stats**: Health 150, Damage 25-35, Armor 10, Speed slow
- **Immunities**: Poison, disease, bleeding, drowning, cold, fire
- **State machine**:
  - States: `guarding`, `hostile`, `passive`, `serving`, `destroyed`
  - Initial: `guarding`
  - Transitions:
    - `guarding` → `hostile`: Player enters main hall without authorization
    - `hostile` → `passive`: Password spoken correctly
    - `hostile` → `serving`: Control crystal used
    - `hostile` → `passive`: Ritual offering accepted
    - `hostile` → `destroyed`: Combat (very difficult)
- **Deactivation methods**:
  1. **Password**: "Fire-that-gives-life and water-that-cleanses, united in purpose"
     - Discovery: Wall inscriptions (partial), lore tablets (full), Keeper's journal (partial)
     - Effect: Passive - allow passage but don't serve
  2. **Control crystal**: Found in ice caves side passage (hidden)
     - Effect: Serving - guardians serve player, bow, await orders
  3. **Ritual offering**: Fire-aspected item + hot springs water
     - Effect: Passive - recognize ancient protocol
  4. **Combat**: ~36 rounds with optimal strategy, very resource-intensive
- **Territorial**: Won't leave temple even when serving
- **Linked**: If one is deactivated/pacified, both are. If one destroyed, other continues alone.

**Steam Salamander (Lead) - Full Specification:**

- **Nature**: Fire elemental beast, intelligent, communicates through gesture
- **Stats**: Health 40, Damage 10-15 (fire), Armor 0
- **Properties**: Provides warmth aura (cold immunity when nearby), neutral unless attacked
- **State machine**:
  - States: `neutral`, `friendly`, `companion`, `hostile`, `dead`
  - Initial: `neutral`
  - Transitions:
    - `neutral` → `friendly`: Offered fire-aspected item (gratitude +1)
    - `friendly` → `companion`: Gratitude >= 3 AND player invites
    - `neutral` → `hostile`: Attacked
- **Befriending**:
  - Accepts: Lit torch, fire crystal, warm coal, any fire-aspected item
  - Gratitude per gift: +1
  - Bonus gratitude: +1 for returning borrowed heated stone while still warm
  - Companion threshold: Gratitude 3
- **Services** (when friendly):
  - Heated stone: Portable warmth (~20 turns duration), cold immunity while held
- **Companion benefits**:
  - Warmth aura (indefinite cold immunity when nearby)
  - Light source
  - Minor fire damage in combat (10-15)
  - Can melt ice/provide heat on demand
- **Communication**: Non-verbal (gestures, pantomime)
  - Points at torch → wants fire
  - Shakes head at ice → doesn't want cold things
  - Two fists together then separating → warning about golems
  - Shivering then holding close → caves have valuable but cold treasure

**Steam Salamander 2 & 3**: Follow lead salamander's disposition. Become friendly when lead becomes friendly. Won't become companions - stay at springs.

### 1.3 Required Items

| Item ID | Name | Purpose | Found In | Source |
|---------|------|---------|----------|--------|
| `cold_weather_gear` | Cold Weather Gear | Halves hypothermia in cold/freezing | `frozen_pass` (camp) | Sketch |
| `preserved_supplies` | Preserved Supplies | Contains dried meat, bandages, torch | `frozen_pass` (camp) | Sketch |
| `partial_map` | Partial Map | Reveals location hints and danger warnings | `frozen_pass` (camp) | Sketch |
| `ice_crystals` | Ice Crystals | Trade item for Myconids | `ice_caves` (main) | `cross_region_dependencies.md` |
| `frost_lily` | Frost Lily | Trade item for Bee Queen | `ice_caves` (main) | `cross_region_dependencies.md` |
| `ice_shard` | Ice Shard | Waystone fragment | `ice_caves` (deep) | `cross_region_dependencies.md` |
| `crystal_lens` | Crystal Lens | Telescope component | `ice_caves` (deep) | Sketch |
| `control_crystal` | Control Crystal | Full golem control | `ice_caves` (side passage) | Sketch |
| `mounting_bracket` | Mounting Bracket | Telescope component | `temple_sanctum` (altar) | Sketch |
| `cold_resistance_cloak` | Cold Resistance Cloak | Full cold immunity / 50% freezing/extreme | `temple_sanctum` (alcove) | Sketch |
| `fire_crystal` | Fire Crystal | Fire-aspected gift for salamanders | `temple_sanctum` (side chamber) | Sketch |
| `lore_tablets` | Lore Tablets | Backstory, full password, control crystal hint | `temple_sanctum` (walls) | Sketch |
| `salamander_heated_stone` | Salamander-heated Stone | Portable warmth (~20 turns) | Salamander service | Sketch |
| `cleaning_supplies` | Cleaning Supplies | Telescope repair component | Meridian Nexus (imported) | `cross_region_dependencies.md` |

**Key Item Details:**

**ice_shard**:
- Location: Ice caves deep section, in frozen pool behind thin ice
- Acquisition challenge: Thin ice blocks direct approach
- Solutions: Melt path with heat, test ice carefully, risk crossing (may break through)
- Quest purpose: Required for waystone repair in Nexus

**crystal_lens**:
- Location: Ice caves deep section, frozen in wall
- Acquisition challenge: Frozen in ice, requires careful extraction
- Solutions: Melt with fire source (careful), chip away (risk breaking)
- Fragile: Breaking destroys it permanently
- Quest purpose: Telescope repair component

**control_crystal**:
- Location: Ice caves side passage (hidden, not on main path)
- Acquisition: Requires thorough exploration OR hint from temple inscriptions
- Extraction: Frozen in wall, requires heat source
- Effect: Best golem solution - full control, guardians serve

**cold_resistance_cloak**:
- Major reward for solving temple puzzle
- Effects:
  - Cold zones: Full immunity (no hypothermia)
  - Freezing zones: 50% reduction
  - Extreme cold zones: 50% reduction
- Design note: Alternative to salamander companion for cold survival

### 1.4 Required Puzzles/Challenges

| Puzzle | Location | Type | Requirements | Source |
|--------|----------|------|--------------|--------|
| Golem Deactivation | `temple_sanctum` | Multi-solution | Password OR control crystal OR ritual OR combat | Sketch |
| Telescope Repair | `frozen_observatory` | Multi-component | Crystal lens + mounting bracket + cleaning supplies | Sketch |
| Ice Extraction | `ice_caves` | Resource + patience | Heat source + time | Sketch |

**Golem Deactivation - Full Specification:**

Four valid solutions with different rewards:

| Solution | Requirements | Difficulty | Result |
|----------|--------------|------------|--------|
| Password | Read inscriptions/tablets | Easy (research) | Golems passive |
| Control Crystal | Find hidden passage, extract with heat | Medium (exploration) | Golems serve (best outcome) |
| Ritual Offering | Fire item + hot springs water | Easy (resource gathering) | Golems passive |
| Combat | Silver weapon, healing potions, cover tactics | Very Hard | Golems destroyed (lose future protection) |

**Telescope Repair - Full Specification:**

Three components required:

| Component | Location | Challenge |
|-----------|----------|-----------|
| Crystal Lens | Ice caves (frozen in wall) | Requires heat to extract without breaking |
| Mounting Bracket | Temple altar | Requires getting past golems |
| Cleaning Supplies | Nexus (Keeper's Quarters) | Cross-region fetch |

When repaired, telescope reveals:
- NPC survival states in all regions (Aldric's campfire, Sira injured, Delvan tapping, Garrett moving)
- Spore Mother health status
- Waystone repair requirements (five slots)
- Hidden paths in some regions

### 1.5 Communication Conventions

How do NPCs in this region communicate?

**Verbal NPCs**:
- None (region is deliberately empty of speaking NPCs)

**Non-verbal NPCs**:
- Steam Salamanders (gesture, posture, flame behavior, sounds)
- Stone Golems (rune glow colors, stance - minimal communication)

**Salamander Communication Vocabulary**:
```
Gestures:
- Points at object + points at self = wants that object (especially fire items)
- Shakes head + gesture at cold item = dislikes cold things
- Two fists together then apart = warning about golems/danger
- Shivering + holding something close = valuable but cold (treasure hint)
- Warm breath on object = offering to heat it
- Beckoning toward springs = inviting to safe area

Flame Behavior:
- Flame brightens = happy/interested/pleased
- Flame dims + backs away = frightened/unhappy/rejection
- Flame flickers rapidly = excited/agitated
- Steady flame = calm/content

Posture:
- Head tilt + ember eyes focused = curious/waiting for response
- Curls near player = comfortable/trusting
- Backs away = wary/uncertain
- Approaches slowly = interested/friendly

Sounds:
- Crackle sound = pleased/greeting
- Hissing = warning/displeasure
- Low rumble = contentment
- Sharp pop = surprise/alarm
```

**Golem Communication** (minimal):
```
Rune Colors:
- Dim glow = guarding (dormant)
- Red glow = hostile/attacking
- Blue glow = passive (password accepted)
- White glow = serving (control crystal used)

Stance:
- Motionless = guarding or passive
- Stepped aside = allowing passage
- Bowing = serving
- Advancing = hostile
```

**Communication Learning Curve**:
- **Salamanders**: Partial map from frozen_pass mentions "fire creatures that respond to warmth." Salamander gestures are intuitive - pointing at torch while pointing at self is clear. Trial and error with offerings works.
- **Golems**: Temple inscriptions explain golem behavior and deactivation methods. Golem communication is minimal - their state is obvious from rune color and behavior.

---

## 2. Cross-Region Connections

### 2.1 Items This Region Imports

| Item | Source Region | Purpose Here | Urgency |
|------|---------------|--------------|---------|
| Cleaning Supplies | Meridian Nexus | Telescope repair | None (no timer) |
| Temple Password (partial) | Meridian Nexus | Golem deactivation hint | None |

### 2.2 Items This Region Exports

| Item | Destination Region | Purpose There | Acquisition |
|------|-------------------|---------------|-------------|
| Ice Shard | Meridian Nexus | Waystone fragment | Extract from ice caves deep section |
| Frost Lily | Beast Wilds | Bee Queen trade | Collect from ice caves |
| Ice Crystals | Fungal Depths | Myconid payment for services | Chip from cave walls |

### 2.3 NPCs With Cross-Region Connections

| NPC Here | Connected To | Connection Type | Gossip Timing |
|----------|--------------|-----------------|---------------|
| Steam Salamander | Echo (Nexus) | Echo comments on senseless violence if salamanders killed | Instant |

### 2.4 Environmental Connections

| Effect | Direction | Trigger | Timing |
|--------|-----------|---------|--------|
| Cold Spread | From here → other regions | Telescope NOT repaired | Turn 75: Beast Wilds high ground, Turn 125: Nexus boundary, Turn 175: Sunken District water freezes |
| Cold Spread Prevention | N/A | Telescope repaired | Immediate halt |

### 2.5 Travel Times

| From | To | Turns | Notes |
|------|-----|-------|-------|
| Frozen Pass | Nexus Chamber | 1 | South exit |
| Frozen Pass | Hot Springs Refuge | 1 | West (safe destination) |
| Frozen Pass | Ice Caves | 1 | East |
| Frozen Pass | Temple Sanctum | 1 | North |
| Temple Sanctum | Frozen Observatory | 1 | Up (extreme cold) |
| Frozen Pass → Nexus → Fungal Depths | ~3 turns | Via Nexus | For ice crystal delivery to Myconids |
| Frozen Pass → Nexus → Beast Wilds | ~3 turns | Via Nexus | For frost lily delivery |
| Frozen Pass → Nexus → Keeper's Quarters | ~2 turns | Via Nexus | For cleaning supplies |

**Travel time assumptions**:
- Each location transition = 1 turn
- Hypothermia accumulates during travel in cold zones
- Hot Springs provides instant reset - retreat is always viable
- No location in Frozen Reaches is more than 3 turns from Hot Springs

**Impact on commitments**:
- **No commitments with timers in this region** - travel time doesn't create pressure here
- **Cross-region delivery (ice crystals to Fungal Depths)**: ~6 turns round-trip. If player has committed to Aldric (50 turns), this fits comfortably.
- **Telescope cleaning supplies**: ~4 turns round-trip to Nexus. No urgency.

**Hypothermia and travel**:
```
Worst case path (no gear, no salamander):
- Frozen Pass (cold): +5 hypothermia
- Ice Caves (freezing): +10 hypothermia
- Return to Pass: +5 hypothermia
- Return to Hot Springs: +5 hypothermia, then instant cure
Total: 25 hypothermia accumulated = mild (no effects yet)

With cold weather gear (halves rate):
- Same path = ~12 hypothermia = trivial

With salamander companion:
- Any path = 0 hypothermia
```

The region is designed so that players can explore, retreat to hot springs, and return without permanent penalty.

---

## 3. Instance-Specific Systems

### 3.1 NPC Services

| NPC | Service | Cost/Requirements | Trust Gate | Notes |
|-----|---------|-------------------|------------|-------|
| Steam Salamander (Lead) | Heated Stone | Free (while friendly) | Gratitude 1+ | Lasts ~20 turns, returning grants +1 gratitude |
| Stone Guardians (serving) | Temple Protection | Control crystal | N/A | Guard temple, attack intruders |

### 3.2 Companions

| NPC | Companion Trigger | Restrictions | Benefits |
|-----|-------------------|--------------|----------|
| Steam Salamander 1 | Gratitude 3+ AND invitation | Cannot enter Sunken District (water), uncomfortable in Beast Wilds/Civilized Remnants | Warmth aura (cold immunity), light source, fire damage 10-15, ice melting |

**Salamander Companion Restrictions (from infrastructure):**

```python
CompanionRestriction = {
    "actor_type": "salamander",
    "restrictions": [
        {
            "location_patterns": ["sunken_district/*"],
            "comfort": CompanionComfort.IMPOSSIBLE,
            "reason": "Elemental conflict - water extinguishes fire creatures"
        },
        {
            "location_patterns": ["beast_wilds/*", "civilized_remnants/*"],
            "comfort": CompanionComfort.UNCOMFORTABLE,
            "reason": "Out of element, minor penalties, frequent complaints"
        },
        {
            "location_patterns": ["nexus_*", "frozen_reaches/*", "fungal_depths/*"],
            "comfort": CompanionComfort.COMFORTABLE,
            "reason": "Warm environments or home territory"
        }
    ]
}
```

### 3.3 Commitments

| Target NPC | Trigger | Timer | Timer Trigger | Hope Bonus | Fulfillment Flag |
|------------|---------|-------|---------------|------------|------------------|
| `steam_salamander_1` | "I'll bring you fire" / "I'll help warm you" | None | none | No (elemental) | `salamander_fire_gift` |

**Salamander Commitment Details:**

```python
CommitmentConfig = {
    "id": "commit_salamander_fire",
    "target_npc": ActorId("steam_salamander_1"),
    "goal": "Bring fire-aspected item to salamanders",
    "trigger_phrases": [
        "I'll bring you fire",
        "I'll help warm you",
        "I will return with flame"
    ],
    "hope_extends_survival": False,  # Elementals don't "survive" - they exist
    "base_timer": None,  # No deadline - salamanders are patient
    "fulfillment_flag": "salamander_fire_gift"
}
```

**Special Characteristics:**
- Salamanders are elemental beings - not affected by hope mechanics
- No urgency - salamanders are content without player help
- Cannot be truly "abandoned" - salamanders don't die from lack of player attention
- Echo does NOT comment on unfulfilled salamander commitments (no moral weight)

**Withdrawal Response:**
- Dialog: Salamander gestures toward hot springs - showing where it will wait. No judgment.
- Trust effect: None
- Can recommit: Always

### 3.4 Gossip Sources

N/A - No gossip originates from this region.

**Note**: Salamanders don't participate in gossip networks. Their only cross-region effect is that Echo may comment if player kills them (senseless violence).

### 3.5 Skills

N/A - No skills are taught in this region.

**Note**: Cold survival in this region is gear/companion-based, not skill-based.

### 3.6 Waystones/Collection Items

| Collection Item | Location | Acquisition | Purpose |
|-----------------|----------|-------------|---------|
| Ice Shard | Ice caves (deep) | Extract from frozen pool | Waystone fragment |

### 3.7 Skills

N/A - This section is addressed in Section 3.5 above.

### 3.8 Permanent Consequences

| Action | Consequence | Content Locked | Reversible? |
|--------|-------------|----------------|-------------|
| Kill Steam Salamander | Cannot befriend salamanders, lose warmth aura option, Echo comments on senseless violence | Salamander companion path, heated stone service | No |
| Destroy both golems | Cannot use golems for temple protection, lose serving state benefits | Temple guardian services | No |
| Break crystal lens | Cannot repair telescope, miss strategic information reward | Telescope vision of other regions, cold spread prevention | No |

**Design notes:**
- **Salamander death**: Permanent loss of companion option. This is the main "bad ending" path for this region. Salamanders respawn as elementals, but lead salamander won't trust player again if killed.
- **Golem destruction**: Combat is "hard mode" and results in losing future benefits. Golems don't respawn - they're unique constructs.
- **Crystal lens breaking**: Fragile item can break during extraction if not careful. This locks the telescope reward permanently.

---

## 4. Region Hazards

**Hazard Type: Environmental**

### 4.1 Environmental Zones

| Zone Type | Locations | Hypothermia Rate | Mitigation |
|-----------|-----------|------------------|------------|
| Normal | `hot_springs_refuge` | 0 (instant cure) | N/A |
| Cold | `frozen_pass`, `temple_sanctum` | +5/turn | Gear: 2.5, Cloak: 0, Salamander: 0 |
| Freezing | `ice_caves` | +10/turn | Gear: 5, Cloak: 5, Salamander: 0 |
| Extreme Cold | `frozen_observatory` | +20/turn | Gear: ineffective, Cloak: 10, Salamander: 0 |

### 4.2 Conditions Applied

| Condition | Acquisition | Effects | Treatment |
|-----------|-------------|---------|-----------|
| Hypothermia | Time in cold zones | Severity 30: Movement slowed, Severity 60: Actions impaired (-2 damage), Severity 80: -5 health/turn, Severity 100: Collapse | Normal temp: -10/turn, Hot springs: instant cure, Warming items: prevent progression |

**Hypothermia System (from infrastructure):**

```python
ConditionInstance = {
    "type": ConditionType.HYPOTHERMIA,
    "severity": 0,  # 0-100 scale
    "acquired_turn": <turn_number>
}
```

### 4.3 Companion Restrictions

| Companion Type | Can Enter | Comfort Level | Notes |
|----------------|-----------|---------------|-------|
| Wolves | Yes | Comfortable (cold/freezing), -1 combat in bitter cold (Deep Frost, Ice Caves), Wait at temple (extreme) | Natural fur provides cold resistance but combat debuff in coldest areas |
| Salamander | Yes | Comfortable (home region) | Provides warmth aura |
| Human (Sira) | Yes | Depends on gear | Suffers hypothermia same as player |
| Human (Aldric) | No | Too weak | Cannot handle cold exposure at all |
| Myconids | No | Impossible | Cold kills fungal life - wait at Nexus |

**Wolf behavior in Frozen Reaches:**
- Cold zones: Comfortable (no penalties)
- Freezing zones: Uncomfortable but functional, -1 combat effectiveness in Deep Frost and Ice Caves
- Extreme cold (observatory): Wait at temple entrance
- See game_wide_rules.md "Wolf Cold Tolerance" for full details
- Golem combat: Attack but ineffective (5 damage per hit)
- Exceptional bravery: If player trapped/dying in temple, alpha may charge in (one-time rescue)

---

## 5. Behavioral Defaults

### 5.1 NPC Behavioral Defaults

```
- Default disposition toward player: Neutral (salamanders), Hostile (golems unless authorized)
- Reaction to player brands: N/A (no brand system in this region)
- Reaction to gossip: N/A (no gossip participation)
- Reaction to companions:
  - Salamanders: Curious about wolves, frightened by other salamanders (reunion joy)
  - Golems: Attack all unauthorized intruders, ignore companions if player authorized
- Reaction to conditions:
  - Salamanders: Will offer heated stone if player seems cold
  - Golems: Unaffected by all conditions
```

### 5.2 Location Behavioral Defaults

```
- Environmental zone: Temperature-based (see Section 4.1)
- Lighting: Variable (bright outside, dim inside)
- Turn phase effects: Hypothermia progression based on zone
- Combat: Limited (golems are puzzle-first, salamanders only if attacked)
- Extraction mechanics: Items frozen in ice require heat + time
```

### 5.3 Item Behavioral Defaults

```
- Fire-aspected items: Can melt ice, gift to salamanders, provide warmth
- Cold-aspected items: Salamanders dislike, useful for trade (Myconids)
- Fragile items: Crystal lens can break if extracted carelessly
- Duration items: Heated stone lasts ~20 turns before cooling
```

### 5.4 Group/Pack Dynamics

**Skip this section if N/A**: This section applies - salamanders have group dynamics.

| Group | Leader | Followers | State Mirroring | Location Mirroring |
|-------|--------|-----------|-----------------|-------------------|
| Salamander Trio | steam_salamander_1 | [steam_salamander_2, steam_salamander_3] | Yes | Partial |
| Golem Pair | None (linked) | N/A | Yes | No |

**Salamander Trio**:
- **State mirroring**: Yes - followers become friendly when lead becomes friendly
- **Location mirroring**: Partial - followers stay at hot springs even if lead becomes companion
- **Follower respawn**: N/A - elementals
- **Leader as companion**: Only lead salamander (salamander_1) can become companion. Other two stay at springs.
- **Reunion behavior**: If companion salamander returns to springs, all three interact warmly

**Golem Pair** (linked, not leader/follower):
- **State mirroring**: Yes - both golems share state. Deactivating one deactivates both.
- **Location mirroring**: No - each guards their position
- **Destruction**: If one is destroyed, other continues alone (harder fight)
- **Linked mechanic**: Password, control crystal, or ritual affects both simultaneously

**Note**: Neither group is a traditional "pack" like wolves. Salamanders are a loose social group where individuals can act independently. Golems are linked constructs that share magical state but not location.

---

## 6. Generative Parameters

This section guides LLM authoring to expand the region. The required entities (Section 1) define what MUST exist; this section defines what CAN be added.

### 6.1 Location Generation

**Generation scope**: Limited

The 5 core locations are complete, but 1-3 additional locations could exist to add exploration depth:

**Location Template: Ice Cave Branch**
- Purpose: Exploration, hidden treasures, environmental storytelling
- Environmental zone: Freezing (same as main ice caves)
- Typical features: Frozen objects, ice formations, dead explorers, minor loot
- Connection points: Branches from `ice_caves` (main or deep section)
- Hazards: Thin ice, dead-end cold pockets, ice collapses
- Content density: Sparse (1-2 items, no NPCs)

**Location Template: Mountain Overlook**
- Purpose: Atmosphere, environmental storytelling, minor reward
- Environmental zone: Cold or Extreme cold
- Typical features: Panoramic views, frozen corpses of climbers, wind-scoured rock
- Connection points: Could branch from `frozen_pass` or `temple_sanctum`
- Hazards: Wind exposure (hypothermia acceleration), unstable footing
- Content density: Sparse (0-1 items, no NPCs)

**What NOT to generate**: Settlements, inhabited areas, warm shelters (other than hot springs). The region's emptiness is deliberate.

### 6.2 NPC Generation

**Generation scope**: None

The Frozen Reaches is deliberately depopulated. Only the salamanders (3) and golems (2) exist here. The harsh environment explains why no travelers, merchants, or other characters are present.

**Exception**: Environmental storytelling via corpses. Frozen travelers can be described in generated locations, but they are dead - not NPCs.

### 6.3 Item Generation

**Generation scope**: Limited

Minor items could be added to generated locations or as additional flavor in existing locations.

**Item categories**:
```
- Trade goods: Ice crystals (plentiful), frozen flowers, preserved artifacts
- Environmental props: Frozen corpse belongings, abandoned gear, ice-locked chests
- Flavor loot: Journals/letters from dead travelers, minor valuables, broken equipment
- Consumables: Preserved food, frozen potions (may need thawing)
```

**Constraints**: Fire-aspected items should be rare (only the fire crystal in temple side chamber). Don't generate additional fire sources that would trivialize salamander befriending or ice extraction.

### 6.4 Atmospheric Details

**Environmental details**:
```
- Sounds: Wind howling, ice cracking, silence between gusts, grinding stone (temple), crackling fire (salamanders)
- Visual motifs: Crystal clarity, blue-white ice, steam clouds, rune glow, frozen moments
- Tactile sensations: Biting cold, wind pressure, ice slick underfoot, warmth radiating from salamanders/springs
- Smells: Clean cold air, sulfur at hot springs, ancient dust in temple
```

*Note: Salamander and golem communication vocabularies are documented in Section 1.5 Communication Conventions.*

**State-dependent variations**:
```
- Hypothermia mild: Descriptions mention sluggish movement, visible breath
- Hypothermia severe: Descriptions mention shaking, difficulty thinking, blurred vision
- Near salamander: Warmth emphasized, cold descriptions absent
- Golems passive: Descriptions emphasize stillness, watchfulness
- Golems hostile: Descriptions emphasize grinding movement, glowing runes, inexorable advance
- Telescope repaired: Observatory descriptions include humming telescope, glowing runes
```

### 6.5 Density Guidelines

| Area Type | NPCs | Items | Locations | Atmosphere |
|-----------|------|-------|-----------|------------|
| Entry (frozen_pass) | 0 (corpses only) | 3-4 (supplies, map, gear) | 0-1 branches | Harsh, survival-focused |
| Sanctuary (hot_springs) | 3 salamanders | 1 (heated stone service) | 0 | Warm, welcoming, peaceful |
| Dungeon (ice_caves) | 0 | 4-6 (treasures frozen in ice) | 1-2 branches | Beautiful, deadly, quiet |
| Challenge (temple) | 2 golems | 4-5 (rewards behind puzzle) | 0 | Tense, ancient, geometric |
| Reward (observatory) | 0 | 1 (telescope) | 0 | Awe-inspiring, exposed, extreme |

### 6.6 Thematic Constraints

```
Tone: Harsh beauty, patient danger, earned warmth
Common motifs: Ice and fire opposition, ancient guardians, survival through preparation, frozen time

MUST include:
- Cold as ever-present threat
- Warmth as precious and earned
- Patience rewarded (no urgency)
- Beauty in danger (ice formations, frozen moments)

MUST avoid:
- Urgency or time pressure
- Crowded spaces or settlements
- Easy warmth sources (fire items are rare)
- Combat encounters beyond golems (region is empty for a reason)
- Living NPCs other than salamanders and golems
```

### 6.7 Mechanical Participation Requirements

```
Required systems (generated content MUST use):
- [x] Hypothermia condition (all outdoor locations cause progression)
- [x] Temperature zones (all locations have defined zone)
- [x] Companion restrictions (generated locations follow same rules)

Optional systems (use if thematically appropriate):
- [ ] Trust/disposition (N/A - no generated NPCs)
- [ ] Gossip (N/A - no gossip network here)
- [ ] Services (N/A - only salamander heated stone)
- [ ] Commitments (N/A - no additional commitment sources)
- [ ] Puzzles (could add minor environmental puzzles in generated caves)
```

---

## 7. LLM Narration Guidance

### 7.1 Region Traits

```
Environmental:
- "biting wind that cuts through clothing"
- "snow that hasn't melted in years"
- "ice crystals suspended in the air"
- "impossible silence between gusts"
- "breath freezing instantly"
- "cracking sounds underfoot"

Emotional:
- "harsh beauty"
- "warmth as precious resource"
- "ancient patience (golems, ice)"
- "elemental friendship (salamanders)"

Historical:
- "frozen travelers with peaceful faces"
- "abandoned camps half-buried in snow"
- "temple built to guard secrets"
- "disaster that froze a living world"
```

**Location-Specific Traits:**

**frozen_pass**:
- "wind like a physical force"
- "shapes that might once have been travelers"
- "camp supplies still usable after years"

**hot_springs_refuge**:
- "sulfurous mist"
- "warmth like an embrace"
- "lazy movements of fire creatures"
- "multicolored mineral deposits"

**ice_caves**:
- "crystal blue walls"
- "beautiful deadly formations"
- "thin ice over dark water"
- "treasures frozen in time"

**temple_sanctum**:
- "ancient carved stone faces"
- "glowing runes in geometric patterns"
- "grinding stone sounds"
- "eternal vigilance"

**frozen_observatory**:
- "wind trying to tear you away"
- "stars visible during day"
- "frost forming on your eyelashes"
- "staggering view of broken world"

### 7.2 State Variants

| State | Trigger | Narration Change |
|-------|---------|------------------|
| `hypothermia_mild` | Severity 30+ | "Your movements feel sluggish. The cold is getting to you." |
| `hypothermia_severe` | Severity 60+ | "Your hands shake. Thinking is difficult. Warmth feels like a distant memory." |
| `hypothermia_critical` | Severity 80+ | "The cold has teeth. Each breath hurts. You need warmth NOW." |
| `golems_passive` | Password spoken | "The guardians stand aside, watchful but not hostile." |
| `golems_serving` | Control crystal used | "The guardians bow, awaiting your command." |
| `golems_destroyed` | Combat victory | "The temple is silent. Rubble where guardians once stood." |
| `salamander_friendly` | Gratitude 1+ | "The salamander regards you warmly. It makes pleased crackling sounds." |
| `salamander_companion` | Gratitude 3+ | "Your salamander companion stays close, its warmth a constant comfort." |
| `telescope_repaired` | All components installed | "The telescope hums with purpose. Ancient runes glow along its frame." |

### 7.3 NPC Description Evolution

| NPC | State | Traits |
|-----|-------|--------|
| Golem | guarding | "motionless stone", "rune-eyes dimly glowing", "ancient patience" |
| Golem | hostile | "grinding advance", "rune-eyes blazing red", "inexorable" |
| Golem | passive | "stepped aside", "rune-eyes calm blue", "watchful but still" |
| Golem | serving | "bowing", "rune-eyes white", "awaiting command" |
| Salamander | neutral | "watching with ember eyes", "wreathed in steam", "curious but distant" |
| Salamander | friendly | "moved closer", "warmth a pleasant aura", "making pleased sounds" |
| Salamander | companion | "pressed against your side", "flame brightened", "protective warmth" |

---

## 8. Validation Checklist

### 8.1 Completeness

- [x] All required entities from overview are listed
- [x] All cross-region dependencies documented
- [x] All instance-specific systems addressed (or marked N/A)
- [x] Environmental rules fully specified (4 temperature zones, hypothermia system)
- [x] Behavioral defaults cover all entity types

### 8.2 Consistency

- [x] Location IDs follow naming convention (`snake_case`)
- [x] NPC trust thresholds are reasonable (salamander: gratitude 3 for companion)
- [x] Commitment timers are fair (no timer - salamanders patient)
- [x] Companion restrictions match `cross_region_dependencies.md`
- [N/A] Gossip timing (no gossip in this region)

### 8.3 Cross-Region Verification

- [x] All exported items are listed in Section 2.2 (ice shard, frost lily, ice crystals)
- [x] All imported items are listed in Section 2.1 (cleaning supplies, temple password partial)
- [x] All NPC cross-region connections documented in Section 2.3 (salamander-Echo connection)
- [x] All environmental connections documented in Section 2.4 (cold spread)
- [x] Travel times account for cross-region journeys in Section 2.5
- [x] Companion restrictions match infrastructure spec (salamander restrictions documented)
- [x] Timer triggers in Section 3.3 use standard values (none for salamander commitment)
- [x] Permanent consequences in Section 3.8 don't contradict other regions

### 8.4 Generative Readiness

- [N/A] NPC generation seeds (region is complete, no generation)
- [N/A] Location generation seeds (region is complete, no generation)
- [x] Density guidelines provide clear targets
- [x] Mechanical participation requirements are clear
- [x] Thematic constraints prevent off-tone content

---

## Appendix A: Infrastructure System Integration

### A.1 Hypothermia Condition

Uses the Condition System from `infrastructure_detailed_design.md`:

```python
ConditionInstance = {
    "type": ConditionType.HYPOTHERMIA,
    "severity": 0,  # 0-100 scale
    "acquired_turn": <turn_number>,
    "progression_rate": <varies by zone>,
    "paused": False  # True if wearing cloak or near salamander
}
```

### A.2 Salamander Gratitude (Trust-like)

Uses a simplified TrustState:

```python
TrustState = {
    "current": 0,  # "gratitude" for salamander
    "floor": 0,    # Cannot go negative (salamanders don't hold grudges)
    "ceiling": None,
    "recovery_cap": None  # Not applicable
}
```

### A.3 Golem State Machine

```python
StateMachineConfig = {
    "states": ["guarding", "hostile", "passive", "serving", "destroyed"],
    "initial": "guarding",
    "transitions": {
        "guarding->hostile": {"trigger": "unauthorized_entry"},
        "hostile->passive": {"trigger": "password_spoken"},
        "hostile->serving": {"trigger": "control_crystal_used"},
        "hostile->passive": {"trigger": "ritual_accepted"},
        "hostile->destroyed": {"trigger": "combat_victory"}
    }
}
```

### A.4 Scheduled Events

The Frozen Reaches uses scheduled events for:
- Cold spread progression (if telescope not repaired)
- Heated stone cooling countdown

```python
ScheduledEvent = {
    "id": "heated_stone_cool",
    "trigger_turn": <current_turn + 20>,
    "event_type": "item_state_change",
    "data": {"item_id": "salamander_heated_stone", "new_state": "cooled"}
}
```

---

## Appendix B: Data Structures

### B.1 Salamander Actor Definition

```json
{
  "id": "steam_salamander_1",
  "name": "Steam Salamander",
  "description": "A lizard-like creature wreathed in steam. It regards you with glowing ember eyes.",
  "properties": {
    "elemental": "fire",
    "neutral_unless_attacked": true,
    "provides_warmth_aura": true,
    "intelligent": true,
    "communicates_through_gesture": true,
    "state_machine": {
      "states": ["neutral", "friendly", "companion", "hostile", "dead"],
      "initial": "neutral"
    },
    "gratitude": 0,
    "companion_threshold": 3
  },
  "stats": {
    "health": 40,
    "damage_min": 10,
    "damage_max": 15,
    "damage_type": "fire"
  },
  "flags": {},
  "location": "hot_springs_refuge"
}
```

### B.2 Golem Actor Definition

```json
{
  "id": "stone_golem_1",
  "name": "Stone Guardian",
  "description": "A massive humanoid of carved stone, runes glowing along its limbs.",
  "properties": {
    "construct": true,
    "immunities": ["poison", "disease", "bleeding", "drowning", "cold", "fire"],
    "guardian": true,
    "territorial": true,
    "linked_to": "stone_golem_2",
    "state_machine": {
      "states": ["guarding", "hostile", "passive", "serving", "destroyed"],
      "initial": "guarding"
    }
  },
  "stats": {
    "health": 150,
    "damage_min": 25,
    "damage_max": 35,
    "armor": 10,
    "speed": "slow"
  },
  "flags": {},
  "location": "temple_sanctum"
}
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 0.3 | 2025-12-11 | Phase 2 consistency fixes: Added wolf combat debuff in bitter cold areas (FR-1), clarified fire crystal access (FR-3) |
| 0.2 | 2025-12-11 | Updated to match new template: Added Timer Trigger column to Section 3.3, renamed Section 3.5 to Skills, added Section 3.7 Skills, added Section 3.8 Permanent Consequences, updated Section 4 header to Region Hazards with Hazard Type: Environmental, added N/A guidance to Section 5.4, added Section 8.3 Cross-Region Verification, renumbered old 8.3 to 8.4 |
| 0.1 | 2025-12-11 | Initial draft from template |
