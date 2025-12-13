# Beast Wilds Detailed Design

**Version**: 0.1
**Last Updated**: 2024
**Status**: Draft

## 0. Authoring Guidance

### 0.1 Region Character

The Beast Wilds is a region of **coexistence and consequence**. Intelligent magical beasts have claimed this overgrown wilderness, forming packs and territories. The core experience is discovering that violence closes doors while patience opens them - every major creature encounter can be resolved through diplomacy, but violent solutions are permanent.

### 0.2 Content Density Expectations

- **Entity density**: Moderate (distinct territories with clear inhabitants)
- **NPC interaction depth**: Rich (wolves, bear, bees all have relationship mechanics)
- **Environmental complexity**: Moderate (territories, pack dynamics, web zones)
- **Time pressure**: High (Sira 8 turns, bear cubs 30 turns - competing commitments)

### 0.3 What Belongs Here

- Pack dynamics and territorial behavior
- Trust-building through repeated interaction (feeding, not attacking)
- NPCs that communicate through action rather than speech (wolves, bear, bees)
- Cross-species relationship mechanics (wolf-Sira reconciliation)
- Companion recruitment with meaningful restrictions
- Domestication as an alternative to combat

### 0.4 What Does NOT Belong Here

- Complex puzzles (this is a relationship region, not a puzzle region)
- Environmental hazards that require gear (no temperature zones, no spores)
- Dense NPC populations (wildlife, not civilization)
- Time-unlimited exploration (two competing commitments create urgency)
- Diplomatic solutions for spiders (they are the combat-only contrast)

### 0.5 Authoring Notes

- Spiders are deliberately the ONE encounter type with no diplomatic path - they exist to contrast with the wolves/bear/bees
- Sira's 8-turn timer is a designed trap - players who explore Sunken District after committing to save her will fail
- Wolf domestication requires multiple feedings, not a single interaction
- Bear cubs timer (30 turns) is more forgiving but requires cross-region travel
- The Elara connection should be established EARLY in Sira dialog (first conversation)

### 0.6 Difficulty Design Notes

**Designed challenges** (intended to be hard):
- **Sira's 8-turn timer is a TRAP**: Players who commit to save Sira and then explore elsewhere WILL fail. This teaches commitment consequences. 8 turns with +4 hope = 12 turns max, but round-trip to Civilized Remnants is ~6-8 turns, leaving almost no margin.
- **Competing commitments**: Sira (8 turns) vs cubs (30 turns) forces prioritization. Players cannot casually help everyone.
- **Spider nest has NO diplomatic solution**: This is intentional contrast. Some problems require combat.

**Fair challenges** (hard but solvable with preparation):
- **Wolf domestication**: 3-4 feedings over time is achievable if player is patient and has meat.
- **Bear cubs 30-turn timer**: Generous enough for round-trip to Civilized Remnants plus exploration. Fair if player knows to go south.
- **Bee Queen trade**: No timer pressure. Requires cross-region travel but player sets the pace.

**First-playthrough expectations**:
- **Likely to accomplish**: Find Sira, domesticate wolves (with patience), reach spider nest
- **Likely to fail**: Save Sira on first commit (if distracted), heal cubs on first pass (don't know herb source), complete bee trade (requires 3 regions)
- **Teaches for next time**: Commitment timing matters, explore hints before committing, diplomacy > violence for most encounters
- **The Sira trap specifically**: First-time players who commit to Sira, then go to Sunken District "to explore first," will return to find her dead. This teaches that commitments have real deadlines.

---

## 1. Required Entities

### 1.1 Required Locations

| Location ID | Name | Purpose | Source |
|-------------|------|---------|--------|
| `loc_forest_edge` | Forest Edge | Transition zone from Nexus, safe exploration area | `big_game_overview.md` |
| `loc_wolf_clearing` | Wolf Clearing | Wolf pack territory, domestication encounter | `big_game_overview.md` |
| `loc_beehive_grove` | Beehive Grove | Bee Queen trade location, peaceful unless disturbed | `big_game_overview.md` |
| `loc_predators_den` | Predator's Den | Dire bear and sick cubs, healing commitment | `big_game_overview.md` |
| `loc_spider_nest_gallery` | Spider Nest Gallery | Combat-only zone, web hazards | `big_game_overview.md` |
| `loc_southern_trail` | Southern Trail | Path to Civilized Remnants, Sira's usual location | `big_game_overview.md` |

**Location Details:**

**Forest Edge** (`loc_forest_edge`):
```json
{
  "id": "loc_forest_edge",
  "name": "Forest Edge",
  "properties": {
    "lighting": "dappled",
    "danger_level": "low",
    "safe_zone": false
  },
  "exits": {
    "north": "loc_nexus_chamber",
    "east": "loc_wolf_clearing",
    "south": "loc_predators_den",
    "west": "loc_beehive_grove"
  }
}
```
- Contains: venison, tracking_equipment, hunters_journal
- Territorial markings visible, watchful silence
- Gateway to all other Beast Wilds locations

**Wolf Clearing** (`loc_wolf_clearing`):
```json
{
  "id": "loc_wolf_clearing",
  "name": "Wolf Clearing",
  "properties": {
    "lighting": "filtered",
    "danger_level": "high",
    "territorial_warning": true
  },
  "exits": {
    "west": "loc_forest_edge",
    "east": "loc_spider_nest_gallery"
  }
}
```
- Wolf pack territory, 4 wolves present
- One-turn territorial warning before attack (if hostile)
- Wolves will NOT pursue into spider gallery (territorial instinct)

**Beehive Grove** (`loc_beehive_grove`):
```json
{
  "id": "loc_beehive_grove",
  "name": "Beehive Grove",
  "properties": {
    "lighting": "bright",
    "danger_level": "conditional"
  },
  "exits": {
    "east": "loc_forest_edge"
  }
}
```
- Giant bee colony, honey cache visible
- Peaceful unless player takes honey without permission
- Bee Queen communicates through offerings, not speech

**Predator's Den** (`loc_predators_den`):
```json
{
  "id": "loc_predators_den",
  "name": "Predator's Den",
  "properties": {
    "lighting": "dim",
    "danger_level": "extreme"
  },
  "exits": {
    "north": "loc_forest_edge",
    "south": "loc_southern_trail"
  }
}
```
- Dire bear guards sick cubs, extremely hostile by default
- NO territorial warning - bear attacks immediately on first visit
- Den becomes safe rest location after cubs healed

**Spider Nest Gallery** (`loc_spider_nest_gallery`):
```json
{
  "id": "loc_spider_nest_gallery",
  "name": "Spider Nest Gallery",
  "properties": {
    "lighting": "dark",
    "danger_level": "high",
    "requires_light": true,
    "web_effects": true
  },
  "exits": {
    "west": "loc_wolf_clearing"
  }
}
```
- Underground web-covered passages
- Webs slow movement, give spiders combat bonuses
- Only location in Beast Wilds with darkness mechanic
- Spiders respawn every 10 turns if queen alive

**Southern Trail** (`loc_southern_trail`):
```json
{
  "id": "loc_southern_trail",
  "name": "Southern Trail",
  "properties": {
    "lighting": "dappled",
    "danger_level": "medium"
  },
  "exits": {
    "north": "loc_predators_den",
    "south": "loc_town_gate"
  }
}
```
- Path to Civilized Remnants
- Hunter Sira's usual location (injured)
- Connection point for cross-region travel

### 1.2 Required NPCs

| Actor ID | Name | Role | Commitment Timer | Source |
|----------|------|------|------------------|--------|
| `npc_alpha_wolf` | Alpha Wolf | Pack leader, companion | N/A (domestication) | `big_game_overview.md` |
| `npc_grey_wolf_1` | Grey Wolf | Pack follower | N/A | `beast_wilds_sketch.json` |
| `npc_grey_wolf_2` | Grey Wolf | Pack follower | N/A | `beast_wilds_sketch.json` |
| `npc_grey_wolf_3` | Grey Wolf | Pack follower | N/A | `beast_wilds_sketch.json` |
| `npc_bee_queen` | Bee Queen | Trader (flowers for honey) | N/A | `big_game_overview.md` |
| `npc_bee_swarm` | Bee Swarm | Combat entity | N/A | `beast_wilds_sketch.json` |
| `npc_dire_bear` | Dire Bear | Hostile guardian, ally if cubs healed | 30 turns base (+5 hope) | `big_game_overview.md` |
| `npc_bear_cub_1` | Bear Cub | Sick cub | 30 turns base (+5 hope) | `beast_wilds_sketch.json` |
| `npc_bear_cub_2` | Bear Cub | Sick cub | 30 turns base (+5 hope) | `beast_wilds_sketch.json` |
| `npc_spider_queen` | Spider Queen | Combat-only boss | N/A | `big_game_overview.md` |
| `npc_giant_spider_1` | Giant Spider | Combat follower | N/A | `beast_wilds_sketch.json` |
| `npc_giant_spider_2` | Giant Spider | Combat follower | N/A | `beast_wilds_sketch.json` |
| `npc_hunter_sira` | Hunter Sira | Injured NPC, companion, tracking teacher | 8 turns base (+4 hope) | `big_game_overview.md` |

**NPC Details:**

**Alpha Wolf** (`npc_alpha_wolf`):
```python
StateMachineConfig = {
    "states": ["hostile", "wary", "neutral", "friendly", "companion", "fled", "dead"],
    "initial": "hostile",
    "transitions": {
        "hostile->wary": "Fed once",
        "wary->neutral": "Fed twice OR player defeats threat to pack",
        "neutral->friendly": "Gratitude >= 3",
        "friendly->companion": "Player invites AND gratitude >= 4",
        "any->fled": "Health < 15 in combat",
        "fled->hostile": "After 10 turns, returns with pack"
    }
}

TrustState = {
    "current": 0,
    "floor": -3,  # Can become permanent enemy
    "ceiling": 6   # Cap on gratitude
}
```
- Pack leader, followers mirror state and location
- Domestication through repeated feeding (venison, meat)
- Gifts alpha_fang at trust 5+ (waystone component)
- Companion benefits: combat assist (+15 damage), tracking, pack intimidation

**Pack Behavior**:
```python
pack_behavior = {
    "leader": "npc_alpha_wolf",
    "followers": ["npc_grey_wolf_1", "npc_grey_wolf_2", "npc_grey_wolf_3"],
    "pack_follows_alpha_state": True,
    "pack_follows_alpha_location": True
}
```
- All wolves mirror alpha's state machine state
- All wolves move with alpha
- If alpha becomes companion, pack becomes companion

**Bee Queen** (`npc_bee_queen`):
```python
StateMachineConfig = {
    "states": ["neutral", "hostile", "trading", "allied", "dead"],
    "initial": "neutral",
    "transitions": {
        "neutral->hostile": "Player attacks OR takes honey without permission",
        "neutral->trading": "Player offers rare flowers",
        "trading->allied": "Completed flower trade 3 times",
        "hostile->dead": "Swarm defeated (very difficult)"
    }
}
```
- Communicates through offerings, not speech
- Accepts: moonpetal (Civilized Remnants), frost_lily (Frozen Reaches), water_bloom (Sunken District)
- Gives: royal_honey (one per flower type)
- Violence destroys grove permanently - no more honey ever

**Dire Bear** (`npc_dire_bear`):
```python
StateMachineConfig = {
    "states": ["hostile", "grateful", "allied", "vengeful", "dead"],
    "initial": "hostile",
    "transitions": {
        "hostile->grateful": "Player heals cubs",
        "grateful->allied": "Gratitude >= 3 (cubs fully recovered)",
        "hostile->vengeful": "Cubs die",
        "vengeful->permanent": "Tracks player, attacks on sight"
    }
}

TrustState = {
    "current": 0,
    "floor": -5,  # Vengeful state
    "ceiling": 5
}
```
- Initial hostility is protective (sick cubs)
- Understands player commitment intent - calms slightly when promised
- Communication: looks pointedly toward southern_trail (herb source hint)
- Allied benefits: intimidates other predators, safe rest in den

**Spider Queen** (`npc_spider_queen`):
```python
StateMachineConfig = {
    "states": ["hostile", "dead"],
    "initial": "hostile"
}
```
- NO diplomatic path - combat or avoidance only
- Pack leader for giant spiders
- Respawns workers every 10 turns while alive
- Loot: spider_silk_bundle, queen_venom_sac

**Hunter Sira** (`npc_hunter_sira`):
```python
StateMachineConfig = {
    "states": ["injured", "recovering", "healthy", "companion", "dead"],
    "initial": "injured",
    "transitions": {
        "injured->recovering": "Bleeding stopped",
        "recovering->healthy": "Leg healed (splint + rest OR healer)",
        "healthy->companion": "Trust >= 3 AND player asks",
        "injured->dead": "Without treatment in ~8 turns"
    }
}

TrustState = {
    "current": 0,
    "floor": -3,
    "ceiling": 5
}

ConditionInstance_bleeding = {
    "type": "bleeding",
    "severity": 70,
    "source": "beast_attack"
}

ConditionInstance_leg_injury = {
    "type": "leg_injury",
    "severity": 80,
    "source": "beast_attack"
}
```
- Initial conditions: bleeding (damage 3/turn), leg_injury (cannot move)
- Key dialog establishes Elara connection EARLY (first conversation)
- Anti-beast prejudice: -2 trust if player has wolf companion
- Reconciliation possible: trust >= 2, wolf companion present, player initiates "coexist" dialog
- Services: teach_tracking (requires healthy state, trust >= 2)
- Companion benefits: ranged combat, tracking skill, Beast Wilds knowledge

**Dialog Topics (Sira)**:
| Topic | Keywords | Effect |
|-------|----------|--------|
| injury | hurt, injury, what happened | Sets `knows_sira_backstory` |
| elara_connection | help, healer, town, south | Sets `knows_sira_elara_connection` - CRITICAL |
| partner | partner, who, Tam | Sets `knows_sira_loss` |
| beasts | beasts, animals, creatures | Reveals prejudice (can soften with domestication proof) |

### 1.3 Required Items

| Item ID | Name | Purpose | Found In | Source |
|---------|------|---------|----------|--------|
| `item_venison` | Venison | Wolf feeding | Forest Edge | `big_game_overview.md` |
| `item_tracking_equipment` | Tracking Equipment | Tool (requires skill) | Forest Edge | `beast_wilds_sketch.json` |
| `item_hunters_journal` | Hunter's Journal | Hint source | Forest Edge | `beast_wilds_sketch.json` |
| `item_royal_honey` | Royal Honey | Full heal + remove condition | Bee Queen trade | `big_game_overview.md` |
| `item_spider_silk` | Spider Silk | Crafting, rope, trade | Spider Nest | `big_game_overview.md` |
| `item_venom_sacs` | Venom Sacs | Alchemy, trade | Spider Nest | `beast_wilds_sketch.json` |
| `item_alpha_fang` | Alpha Fang | Waystone component | Alpha Wolf gift | `big_game_overview.md` |
| `item_healing_herbs` | Healing Herbs | Bear cub cure | Civilized Remnants (imported) | `cross_region_dependencies.md` |

**Item Details:**

**Hunter's Journal** (`item_hunters_journal`):
```
Content reveals:
- Wolf pack patterns and feeding behavior hint
- Bear den location and cubs' sickness
- Spider nest warning
- Bee Queen flower trade hint
```
Critical hint source at region entry point.

**Alpha Fang** (`item_alpha_fang`):
- Quest item for waystone repair in Nexus
- Only obtained at trust 5+ with Alpha Wolf
- "A mark of pack bond" - freely given, not taken

### 1.4 Required Puzzles/Challenges

| Puzzle | Location | Type | Requirements | Source |
|--------|----------|------|--------------|--------|
| Wolf Domestication | Wolf Clearing | Multi-step relationship | 3-4 feedings, no violence | `beast_wilds_sketch.json` |
| Bear Cub Healing | Predator's Den | Cross-region fetch | healing_herbs from Civilized Remnants | `big_game_overview.md` |
| Bee Queen Trade | Beehive Grove | Cross-region collection | Flowers from 3 regions | `big_game_overview.md` |
| Sira Rescue | Southern Trail | Timed medical | Stop bleeding + heal leg within 8 turns | `big_game_overview.md` |

**Wolf Domestication**:
- Not a puzzle, but a multi-step relationship
- Hostile → Wary: 1 feeding
- Wary → Neutral: 2nd feeding OR defeat threat to pack
- Neutral → Friendly: Gratitude >= 3 (3rd feeding or significant help)
- Friendly → Companion: Gratitude >= 4 AND player invites

**Bee Queen Trade**:
- Trade 3 different flower types for 3 royal_honey
- Each trade also advances toward allied state
- Flowers from: Civilized Remnants (moonpetal), Frozen Reaches (frost_lily), Sunken District (water_bloom)

### 1.5 Communication Conventions

How do NPCs in this region communicate?

**Verbal NPCs**:
- Hunter Sira (speaks normally, weakly when injured)

**Non-verbal NPCs**:
- Alpha Wolf and pack (body language, vocalizations)
- Dire Bear (posture, vocalizations, gestures)
- Bee Queen (antennae, wings, positioning)
- Spiders (no meaningful communication - hostile only)

**Wolf Communication Vocabulary**:
```
Body Language:
- Ears forward, hackles raised = alert/aggressive
- Ears back, hackles down = submissive/accepting
- Tail high and stiff = dominant/threatening
- Tail low, wagging slowly = calm/curious
- Direct eye contact = challenge
- Averted gaze = acceptance/submission

Vocalizations:
- Low growl = warning, territorial
- Loud snarl = attack imminent
- Soft rumble = acknowledgment, greeting
- Whine = distress, submission
- Howl = calling pack, celebration

Actions:
- Sitting when player approaches = non-threatening
- Approaching with head low = submissive interest
- Circling = evaluation
- Lying down, showing belly = full submission/trust
```

**Bear Communication Vocabulary**:
```
Posture:
- Reared up = threat display, maximum intimidation
- Low stance, head forward = about to charge
- Turning side to cubs = protective anxiety
- Relaxed posture = calm, non-threatening

Vocalizations:
- Roar = attack, extreme threat
- Grunt = acknowledgment, mild interest
- Whine/moan = cubs, distress
- Huffing = warning, agitation

Gestures:
- Looking pointedly toward location = hint (southern_trail = herbs)
- Nudging cubs toward player = trust
- Standing between player and cubs = protective
- Approaching slowly = tentative acceptance
```

**Bee Queen Communication Vocabulary**:
```
Antennae:
- Twitching = interest, evaluating offering
- Still = waiting, patient
- Rapid movement = agitation, warning

Wings:
- Folded = calm, receptive
- Buzzing = warning, preparing defense
- Slow fan = pleased, welcoming

Positioning:
- Moving toward honey cache = offering trade
- Hovering over flowers = interested in offering
- Backing away = rejection
- Approaching player = curiosity or acceptance
```

**Communication Learning Curve**:
- **Wolves**: Hunter's Journal in Forest Edge contains hints about wolf body language. Sira (if healthy) can explain wolf behavior if asked.
- **Bear**: Bear's gestures toward southern_trail are obvious directional hints. Player should interpret as "go that way."
- **Bees**: Trial and error with offerings. Flowers get positive response, other items get rejection.
- **Spiders**: No communication to learn - they attack on sight.

---

## 2. Cross-Region Connections

### 2.1 Items This Region Imports

| Item | Source Region | Purpose Here | Urgency |
|------|---------------|--------------|---------|
| `healing_herbs` | Civilized Remnants | Cure bear cubs' wasting sickness | Time-sensitive (30 turns) |
| `moonpetal` | Civilized Remnants | Bee Queen trade | Optional |
| `frost_lily` | Frozen Reaches | Bee Queen trade | Optional |
| `water_bloom` | Sunken District | Bee Queen trade | Optional |
| `bandages` | Civilized Remnants | Stop Sira's bleeding | Time-sensitive (8 turns) |
| `bloodmoss_tincture` | Civilized Remnants | Stop Sira's bleeding | Time-sensitive (8 turns) |
| `splint` | Civilized Remnants | Heal Sira's leg | Time-sensitive |

### 2.2 Items This Region Exports

| Item | Destination Region | Purpose There | Acquisition |
|------|-------------------|---------------|-------------|
| `alpha_fang` | Meridian Nexus | Waystone repair | Alpha Wolf trust 5+ gift |
| `spider_silk` | Any (trade goods) | Crafting, rope substitute | Spider Nest combat loot |
| `royal_honey` | Any | Full heal + condition cure | Bee Queen trade |
| `venom_sacs` | Civilized Remnants | Herbalist trade, alchemy | Spider Nest combat loot |

### 2.3 NPCs With Cross-Region Connections

| NPC Here | Connected To | Connection Type | Gossip Timing |
|----------|--------------|-----------------|---------------|
| Hunter Sira | Healer Elara (Civilized Remnants) | Close relationship ("we've been through a lot") | 12-20 turns |
| Hunter Sira | Elara | Death notification | 12 turns |
| Hunter Sira | Elara | Abandonment report (if Sira survives to tell) | 20 turns |

**Sira-Elara Gossip Detail**:
- Sira mentions Elara in first conversation (establishes connection)
- If Sira dies: news reaches Elara in ~12 turns via travelers
- If player abandons Sira (she survives and tells): reaches Elara in ~20 turns
- Confession to Elara before gossip arrives reduces penalty (-1 trust vs -2 trust)

### 2.4 Environmental Connections

| Effect | Direction | Trigger | Timing |
|--------|-----------|---------|--------|
| Spore infection spread | From Fungal Depths | Spore Mother not healed | Turn 50: spores appear at Forest Edge |

If the Spore Mother is not healed by turn 50 in Fungal Depths, spores begin appearing at Forest Edge in Beast Wilds.

### 2.5 Travel Times

| From | To | Turns | Notes |
|------|-----|-------|-------|
| Forest Edge | Nexus Chamber | 1 | Direct connection |
| Forest Edge | Wolf Clearing | 1 | East |
| Forest Edge | Beehive Grove | 1 | West |
| Forest Edge | Predator's Den | 1 | South |
| Predator's Den | Southern Trail | 1 | South |
| Southern Trail | Town Gate (Civilized Remnants) | 1 | Direct connection |
| Wolf Clearing | Spider Nest Gallery | 1 | East |
| Southern Trail → Town Gate → Marketplace | ~3 turns | Via town | To reach herbalist |
| Forest Edge → Town Gate → Healer's Garden | ~3 turns | Via Civilized Remnants | For moonpetal |
| Forest Edge → Nexus → Frozen Reaches | ~4 turns | Via Nexus | For frost lily |
| Forest Edge → Nexus → Sunken District | ~3 turns | Via Nexus | For water bloom |

**Travel time assumptions**:
- Each location transition = 1 turn
- Spider gallery movement costs 2 turns (web slow effect)
- Cross-region trips assume direct travel without exploration

**Impact on commitments**:
- **Sira's 8-turn timer (+4 hope = 12 max)**: Southern Trail → Town Gate → Marketplace → back = ~6-8 turns minimum. This leaves 4-6 turns margin at best - barely enough. **This is the trap**: if player explores ANYTHING else, Sira dies.
- **Bear cubs' 30-turn timer (+5 hope = 35 max)**: Same route is comfortable. Player can explore extensively and still save cubs.
- **Bee Queen flowers**: No timer. Collecting all 3 flowers requires visiting 3 regions - significant travel but no pressure.

**The Sira Trap Analysis**:
```
Optimal path to save Sira:
Turn 0: Find Sira (Southern Trail)
Turn 1: Commit to help (timer starts, 8+4=12 turns)
Turn 2: Go to Town Gate
Turn 3: Go to Marketplace, get bandages/herbs
Turn 4: Return to Town Gate
Turn 5: Return to Southern Trail
Turn 6: Apply bandages (bleeding stops)
Turn 7-8: Apply splint/rest (leg heals)
= Success with 4 turns to spare

Failed path (common first-time mistake):
Turn 0: Find Sira
Turn 1: Commit to help
Turn 2-6: "I'll just explore the wolf clearing first..."
Turn 7: Finally head south
Turn 8: Reach Town Gate
Turn 9: Reach Marketplace
Turn 10: Return to Town Gate
Turn 11: Return to Southern Trail
Turn 12: Sira is dead (timer expired turn 12)
```

---

## 3. Instance-Specific Systems

### 3.1 NPC Services

| NPC | Service | Cost/Requirements | Trust Gate | Notes |
|-----|---------|-------------------|------------|-------|
| Hunter Sira | teach_tracking | Free (gratitude for saving her) | Trust >= 2, state = healthy | Cannot teach while injured |
| Bee Queen | royal_honey trade | 1 rare flower per honey | State = trading or allied | Must offer flower first |

**Sira Teaching Requirement**:
- Sira must be in `healthy` state (not `recovering`)
- She needs to physically demonstrate tracking techniques
- Teaching takes no turns (skill granted immediately upon asking)

### 3.2 Companions

| NPC | Recruitment Condition | Restrictions | Special Abilities |
|-----|----------------------|--------------|-------------------|
| Alpha Wolf (+ pack) | Trust >= 4, player invites | Cannot enter Nexus (wards), Civilized Remnants (guards) | Combat +15 damage/round, track scents, pack intimidation |
| Hunter Sira | Trust >= 3, healthy state | None | Ranged combat 8-12 damage, tracking skill, warns of dangers |

**Wolf Pack Companion**:
- Recruiting alpha recruits entire pack (3 grey wolves follow)
- Pack provides +15 combat damage per round (all wolves attack together)
- Tracking: can reveal hidden paths and creature locations
- Intimidation: smaller creatures flee, larger creatures hesitate

**Companion Conflict (Sira + Wolves)**:
- If player has wolf companion when meeting Sira: Trust -2 immediately
- Reconciliation requires: trust >= 2 with Sira, wolves present, player initiates dialog
- Dialog keywords: "wolves", "pack", "coexist", "trust them"
- Success removes anti-beast prejudice flag

### 3.3 Commitments

| Target NPC | Trigger | Timer | Timer Trigger | Hope Bonus | Fulfillment Flag |
|------------|---------|-------|---------------|------------|------------------|
| `npc_dire_bear` | "I'll heal your cubs", "I'll find medicine" | 30 turns | `on_commitment` | +5 turns | `cubs_healed` |
| `npc_hunter_sira` | "I'll save you", "I'll get help" | 8 turns | `on_first_encounter` | +4 turns | `sira_healed` |
| `npc_bee_queen` | "I'll bring flowers" | N/A (no timer) | `none` | N/A | N/A |

**Bear Cubs Commitment**:
```python
CommitmentConfig = {
    "id": "commit_bear_cubs",
    "target_npc": ActorId("npc_dire_bear"),
    "goal": "Give healing_herbs to bear cubs",
    "trigger_phrases": ["I'll find medicine", "I'll heal your cubs", "I will help them", "I'll bring healing herbs"],
    "trigger_type": "on_commitment",
    "hope_extends_survival": True,
    "hope_bonus": 5,
    "base_timer": 30,
    "fulfillment_flag": "cubs_healed"
}
```
- Commitment made TO bear (she understands), FOR cubs
- Bear calms slightly, looks toward southern_trail (hint)
- Withdrawal response: Bear shows cubs' condition, looks south again (reinforces hint)
- Abandonment: cubs die, bear becomes vengeful, Echo disappointed

**Sira Commitment**:
```python
CommitmentConfig = {
    "id": "commit_sira_rescue",
    "target_npc": ActorId("npc_hunter_sira"),
    "goal": "Stop Sira's bleeding and heal her leg",
    "trigger_phrases": ["I'll get help", "I'll find a healer", "I'll bring bandages", "I will save you"],
    "trigger_type": "on_first_encounter",
    "hope_extends_survival": True,
    "hope_bonus": 4,
    "base_timer": 8,
    "fulfillment_flag": "sira_healed"
}
```
- **DESIGNED TRAP**: 8-turn timer is tightest non-Sunken commitment
- Timer starts when Sira is FOUND (on_first_encounter), not when player commits
- Players who commit then explore elsewhere will fail
- Withdrawal reinforces Elara connection
- Abandonment: Sira dies, Elara loses trust (-2), tracking unavailable

**Bee Queen Commitment**:
- Not a true commitment (no timer, no hope bonus)
- Queen is patient, flowers are rare
- Trade offer remains open indefinitely
- Violence ends all future trade

### 3.4 Gossip Sources

| Event | Content | Target NPCs | Delay | Confession Window |
|-------|---------|-------------|-------|-------------------|
| Sira dies (player present) | "Someone was with Sira when she died" | Elara | 12 turns | 12 turns |
| Sira abandoned (she tells) | "Player promised to save me and didn't" | Elara | 20 turns | 20 turns |
| Cubs die (player committed) | "A mother's cubs died despite promises" | Echo (instant), Sira (if alive) | Echo: 0, Sira: 8 turns | N/A |
| Bear becomes vengeful | "The dire bear hunts humans now" | Sira (if alive) | 5 turns | N/A |

**Confession Mechanics (Sira → Elara)**:
- If player confesses to Elara BEFORE gossip arrives: -1 trust (honesty valued)
- If gossip arrives first: -2 trust, "You were there and did nothing?"
- If player visited Elara, didn't confess, gossip arrives later: -4 trust (lie by omission)

### 3.5 Branding/Reputation

N/A - Beast Wilds has no faction reputation system. Individual NPC relationships matter.

### 3.6 Waystones/Endings

| Fragment | Location | Acquisition | Requirements |
|----------|----------|-------------|--------------|
| Alpha Fang | Wolf Clearing (from Alpha Wolf) | Gift at trust 5+ | Complete wolf domestication |

**Alpha Fang Acquisition**:
- Alpha Wolf offers shed fang at trust 5+ as "mark of pack bond"
- Cannot be taken by force (killing wolves gives no fang)
- Part of the waystone repair quest in Nexus

### 3.7 Skills

| Skill | Teacher | Requirements | Effects |
|-------|---------|--------------|---------|
| Tracking | Hunter Sira | Trust >= 2, Sira healthy | Reveals hidden paths, finds creature locations |

**Tracking Skill**:
- Requires tracking_equipment to use effectively
- Without skill: equipment is just items
- With skill: reveals hidden paths in any region, locate specific creatures
- Essential for Beast Wilds navigation and finding hidden items

**Bee Queen Trade** (optional collection, not a formal quest):
- Trade 3 different flower types for 3 royal_honey
- Each trade also advances toward allied state
- Flowers from: Civilized Remnants (moonpetal), Frozen Reaches (frost_lily), Sunken District (water_bloom)
- See Appendix B for full trade table

### 3.8 Permanent Consequences

| Action | Consequence | Affected Content | Reversible? |
|--------|-------------|------------------|-------------|
| Kill Alpha Wolf | Pack scatters, individual wolves become hostile loners | Wolf domestication impossible, alpha_fang unavailable, waystone repair blocked | No |
| Kill Bee Queen | Grove destroyed, bees disperse | No more royal_honey ever, trade path blocked | No |
| Sira dies | Tracking skill unavailable, Elara trust loss | Cannot learn tracking, affects Elara relationship | No |
| Cubs die | Bear becomes vengeful, hunts player | Safe rest in den unavailable, bear becomes permanent enemy | No |

**Permanent Blocker: Alpha Wolf Death**
```
Permanent Blocker: Kill Alpha Wolf
- Trigger: Alpha Wolf killed in combat
- Locks: Wolf domestication, alpha_fang acquisition, waystone repair path
- Affects pack: Grey wolves scatter, become independent hostile loners (harder to domesticate)
- Affects endings: Waystone repair requires alpha_fang (must use alternative component)
- Warning signs: None - combat is always risky, but fang cannot be taken from corpse
```

**Permanent Blocker: Sira Death**
```
Permanent Blocker: Sira Dies
- Trigger: Sira's bleeding/injuries untreated within timer
- Locks: Tracking skill, Sira as companion
- Affects Elara: Trust -2 (if player was there), affects Civilized Remnants relationships
- Affects endings: Tracking skill may be required for certain content discovery
- Warning signs: Bleeding condition visible, timer communicated clearly
```

**Conditional Lock: Bear Alliance**
```
Conditional Lock: Bear Den Safe Rest
- Required: Cubs must be healed within 30-turn timer
- Lost if: Cubs die from neglect or player kills cubs/bear
- Recovery: None - bear becomes vengeful and permanent enemy if cubs die
```

---

## 4. Region Hazards

**Hazard Type**: Environmental

Beast Wilds has minimal environmental hazards (only spider gallery darkness/webs). The primary hazards are aggressive beasts (wolves, bear, spiders), which are covered in NPC behavior sections rather than environmental zones.

### 4.1 Hazard Zones

| Zone Type | Locations | Effects | Mitigation |
|-----------|-----------|---------|------------|
| Web zone | Spider Nest Gallery | Movement slowed, spiders +combat bonus | Burn webs (alerts spiders, permanent damage) |
| Darkness | Spider Nest Gallery | Cannot see, severe penalties | Light source required |

**Web Zone Effects**:
- Player movement costs 2 turns instead of 1
- Spiders get +5 damage, +2 armor in webs
- Can burn webs with fire (salamander, torch)
- Burning alerts all spiders, damages area permanently

**Darkness**:
- Spider Nest Gallery requires light source
- Without light: cannot see exits, ambush attacks
- Salamander companion provides light

### 4.2 Conditions Applied

| Condition | Source | Severity Progression | Treatment |
|-----------|--------|---------------------|-----------|
| Bleeding | Combat (Sira starts with this) | 3 damage/turn | Bandages, bloodmoss_tincture |
| Poison | Spider bites | 5 damage/turn, reduces over time | Royal honey, antidote |
| Webbed | Spider web spray | Immobilized 1 turn | Wait or burn |

### 4.3 Companion Restrictions

| Companion Type | Can Enter | Comfort Level | Notes |
|----------------|-----------|---------------|-------|
| Wolves | All except Nexus, Civilized Remnants | Uncomfortable in Spider Nest, Sunken District | Won't enter spider gallery (territorial instinct) |
| Bears | Cannot follow far from den | Uncomfortable everywhere | Won't leave cubs unless cubs travel with her |
| Salamanders | Yes | Uncomfortable | Provides light in spider gallery, can burn webs |
| Humans | Yes | Comfortable | Sira has home region bonus (+2 tracking) |
| Myconids | No | N/A | Dry air, predators |

**Wolf Restriction Detail**:
- Cannot enter Nexus (magical wards repel beasts)
- Cannot enter Civilized Remnants (guards attack on sight)
- Won't enter Spider Nest Gallery (territorial instinct)
- Override: Exceptional bravery if player losing fight in gallery (one-time, costs wolves)

**Pack Waiting Behavior**:
- If player enters restricted area: wolves wait at last valid location
- Wolf Clearing if player enters spider gallery
- Forest Edge if player enters town
- Wolves rejoin when player returns

---

## 5. Behavioral Defaults

### 5.1 NPC Behavioral Defaults

```
- Default disposition toward player: wary (beasts), neutral (Sira)
- Reaction to player brands: N/A (no brands in this region)
- Reaction to gossip: N/A (beasts don't receive gossip)
- Reaction to companions:
  - Beasts: curious/wary of salamander, hostile to other beasts (territorial)
  - Sira: hostile to wolf companions (reconciliation possible)
- Reaction to conditions:
  - Bear recognizes sick/injured player, may show concern if allied
```

### 5.2 Location Behavioral Defaults

```
- Environmental zone: None (no temperature, spores, water except spider gallery)
- Lighting: Dappled/filtered (forest), Dark (spider gallery)
- Turn phase effects:
  - Spider gallery: spiders respawn every 10 turns if queen alive
  - Wolf clearing: pack returns after 10 turns if fled
```

### 5.3 Item Behavioral Defaults

```
- Typical item types: Food (venison), tools (tracking equipment), trade goods (spider silk)
- Environmental interactions: Venison attracts predators if dropped
```

### 5.4 Group/Pack Dynamics

| Group | Leader | Followers | State Mirroring | Location Mirroring |
|-------|--------|-----------|-----------------|-------------------|
| Wolf Pack | npc_alpha_wolf | [npc_grey_wolf_1, npc_grey_wolf_2, npc_grey_wolf_3] | Yes | Yes |
| Spider Pack | npc_spider_queen | [npc_giant_spider_1, npc_giant_spider_2] | No | No |
| Bee Swarm | npc_bee_queen | [npc_bee_swarm] | Yes | Yes |

**Wolf Pack**:
- **State mirroring**: Yes - all grey wolves adopt alpha's state (hostile/wary/neutral/friendly/companion)
- **Location mirroring**: Yes - pack moves with alpha
- **Follower respawn**: No - dead wolves stay dead
- **Leader death effects**: Pack scatters, individual wolves become hostile loners (harder to domesticate)
- **Companion recruitment**: Recruiting alpha recruits entire pack

**Spider Pack**:
- **State mirroring**: No - spiders are always hostile regardless of queen state (queen has only hostile/dead)
- **Location mirroring**: No - spiders spread through gallery
- **Follower respawn**: Yes - 2 giant spiders respawn every 10 turns while queen lives
- **Leader death effects**: No more respawns, remaining spiders fight to death

**Bee Swarm**:
- **State mirroring**: Yes - swarm follows queen's disposition (neutral/hostile/trading/allied)
- **Location mirroring**: Yes - swarm stays with queen
- **Follower respawn**: N/A - swarm is a single entity
- **Leader death effects**: Swarm disperses (very difficult to kill queen - designed to discourage violence)

**Bear Cubs** (special case - not a standard pack):
- Cubs are dependents, not followers
- Cubs don't fight or mirror state
- Bear's state depends on cubs' health, not the reverse
- Cubs cannot be recruited as companions

---

## 6. Generative Parameters

### 6.1 Location Generation

**Generation scope**: Limited

While Beast Wilds has defined territories, a few additional locations could exist:

```
Location Template: Forest Clearing
- Purpose: Exploration, hidden treasure
- Environmental zone: None (open air)
- Typical features: Animal signs, old campsites, plant resources
- Connection points: Could branch from forest_edge
- Hazards: Random predator encounters
- Content density: Sparse (1 item, occasional creature)
```

```
Location Template: Hidden Burrow
- Purpose: Resource cache, environmental storytelling
- Environmental zone: None
- Typical features: Animal den, stored food, bones
- Connection points: Wolf clearing, predators_den
- Hazards: Territorial creature may be present
- Content density: Sparse (1-2 items)
```

### 6.2 NPC Generation

**Generation scope**: Limited

Background creatures could populate the region:

```
NPC Template: Prey Animal
- Role: Environmental flavor, potential food source
- Typical count: 1-2 per location
- Services: None (non-sapient)
- Trust thresholds: N/A
- Disposition range: Fearful, flees
- Dialog topics: None
- Mechanical hooks: Can be hunted for food (wolf feeding)
```

### 6.3 Item Generation

**Generation scope**: Limited

```
Item categories:
- Food items: Additional meat sources (rabbit, deer), berries
- Environmental props: Bones, feathers, territorial markings
- Trade goods: Pelts, claws (from hunting)
```

### 6.4 Atmospheric Details

**Environmental details**:
```
- Sounds: Birdsong (wary), growls (danger), rustling (watched), silence (predator near)
- Visual motifs: Claw marks, territorial markings, game trails, bones
- Tactile sensations: Dense undergrowth, wet leaves, spider silk strands
- Smells: Musk (predators), decay (kills), flowers (bees), dampness
```

*Note: Beast communication vocabularies (wolf body language, bear gestures, bee queen signals) are documented in Section 1.5 Communication Conventions.*

**State-dependent variations**:
```
- Wolf Clearing when hostile: "Yellow eyes gleam from shadows, low growls fill the air"
- Wolf Clearing when friendly: "The pack rests in the clearing, the alpha's tail wagging slightly at your approach"
- Predator's Den when hostile: "A massive shape blocks the cave, rage and fear in equal measure"
- Predator's Den when allied: "The bear greets you with a soft grunt, cubs tumbling playfully nearby"
```

### 6.5 Density Guidelines

| Area Type | NPCs | Items | Locations | Atmosphere |
|-----------|------|-------|-----------|------------|
| Entry (Forest Edge) | 0 (hints only) | 3 key items | Fixed | Watchful, hint-rich |
| Territory (Wolf/Bear) | 1-4 pack members | 0-1 | Fixed | Tense, dynamic |
| Trade (Bee Grove) | 2 (queen + swarm) | 1 (honey cache) | Fixed | Peaceful, humming |
| Combat (Spider Nest) | 3+ | 2 loot | Fixed | Dark, dangerous |
| Transition (Southern Trail) | 1 (Sira) | 0 | Fixed | Urgent, path-focused |

### 6.6 Thematic Constraints

```
Tone: Nature red in tooth and claw, but intelligence creates options
Common motifs: Pack loyalty, maternal protection, territorial boundaries, trust earned not given
MUST include: Consequences for violence, rewards for patience
MUST avoid: Easy combat victories, instant friendships, human-level speech from beasts
```

### 6.7 Mechanical Participation Requirements

```
Required systems (generated content MUST use):
- [x] Trust/disposition (all intelligent beasts respond to player behavior)
- [x] Pack dynamics (followers mirror leader state)
- [ ] Gossip (beasts don't participate in gossip network)
- [ ] Environmental conditions (no zones in generated locations)
- [x] Companion restrictions (beasts respect territory)

Optional systems (use if thematically appropriate):
- [ ] Services (only Sira teaches)
- [x] Commitments (any distressed creature could accept commitment)
- [ ] Puzzles (not a puzzle region)
- [ ] Brands/reputation (no faction system)
```

---

## 7. LLM Narration Guidance

### 7.1 Region Traits

```
Environmental:
- Dense undergrowth catching at clothes
- Territorial markings scored into bark
- Game trails winding through shadows
- Watchful silence broken by distant calls
- Smell of predators and prey
- Filtered light through canopy
- Spider silk catching in hair (near gallery)

Emotional:
- Constant sense of being watched
- Respect for nature's dangers
- Wonder at beast intelligence

Historical:
- "Since the disaster, they've changed. Smarter."
- Hunter camps abandoned, torn apart
- Evidence of old human-beast conflict
```

### 7.2 State Variants

| State | Trigger | Narration Change |
|-------|---------|------------------|
| Wolves hostile | Default | "Yellow eyes gleam with hunger and threat" |
| Wolves wary | Fed once | "The wolves watch you, no longer growling but not relaxed" |
| Wolves friendly | Trust 3+ | "The pack greets you, the alpha's tail swaying" |
| Bear hostile | Default | "Rage and fear battle in the bear's eyes - she will kill to protect" |
| Bear grateful | Cubs healed | "The bear's aggression has faded, replaced by watchful gratitude" |
| Bear vengeful | Cubs died | "The bear's eyes hold only hatred now. She remembers your face." |
| Grove peaceful | Default | "Constant humming fills the air, giant bees going about their work" |
| Grove hostile | Honey stolen | "The swarm boils with fury, the queen's compound eyes tracking your every move" |

### 7.3 NPC Description Evolution

| NPC | State | Traits |
|-----|-------|--------|
| Alpha Wolf | hostile | "massive, bristling, teeth bared, eyes narrowed with hunger" |
| Alpha Wolf | wary | "watchful, ears pricked, sniffing, evaluating" |
| Alpha Wolf | friendly | "tail swaying, ears relaxed, approaching without threat" |
| Alpha Wolf | companion | "padding beside you, loyal, pack-bonded, protective" |
| Dire Bear | hostile | "enormous, rearing, protective fury, blocking cave" |
| Dire Bear | grateful | "massive but calm, watching cubs with relief, acknowledging you" |
| Dire Bear | vengeful | "scarred by loss, hatred-filled, hunting" |
| Sira | injured | "pale, blood-soaked, gripping leg, fierce despite pain" |
| Sira | recovering | "color returning, still wincing, sitting straighter" |
| Sira | healthy | "standing, testing leg, hand near weapon, alert" |
| Sira | companion | "moving with hunter's grace, eyes scanning, covering your back" |

---

## 8. Validation Checklist

### 8.1 Completeness

- [x] All required entities from overview are listed
- [x] All cross-region dependencies documented
- [x] All instance-specific systems addressed (or marked N/A)
- [x] Environmental rules fully specified
- [x] Behavioral defaults cover all entity types

### 8.2 Consistency

- [x] Location IDs follow naming convention
- [x] NPC trust thresholds are reasonable
- [x] Commitment timers are fair given travel times (Sira's 8 turns is a designed trap)
- [x] Companion restrictions match `cross_region_dependencies.md`
- [x] Gossip timing is consistent with established patterns

### 8.3 Cross-Region Verification

- [x] All imported items are exported from documented source regions
- [x] All exported items are imported by documented destination regions
- [x] Gossip timing matches in both source and destination region docs
- [x] NPC connections documented on both sides of relationship
- [x] Skill dependencies are achievable (e.g., can reach teacher before deadline)
- [x] Permanent consequences don't create impossible states

### 8.4 Generative Readiness

- [x] NPC generation seeds cover expected roles (prey animals)
- [x] Location generation seeds cover expected types (clearings, burrows)
- [x] Density guidelines provide clear targets
- [x] Mechanical participation requirements are clear
- [x] Thematic constraints prevent off-tone content

---

## Appendix A: Wolf-Sira Reconciliation

Detailed reconciliation dialog flow:

**Initial State** (Sira has wolf companion present):
```
Sira's hand goes to her weapon. "You travel with those killers?"
[Sira trust: -2]
[reconciliation_possible: true if trust >= 2]
```

**Reconciliation Attempt** (trust >= 2, wolf present, player says "coexist"):
```
Player: "They're not like the ones that killed Tam. They've chosen to trust me."

Sira: "Trust?" She watches the alpha, tension in every line of her body.
      "They're killers." Long pause. The alpha sits, watching her back calmly.
      "But... they're not attacking. And they follow you."
      Another pause. "Fine. I'll try. But if they turn..."

[anti_beast_prejudice: removed]
[Both companions can now travel together]
```

**Without Reconciliation**:
- Sira refuses to travel while wolves present
- Player must choose one or the other
- Can attempt reconciliation later if trust rebuilds to 2+

---

## Appendix B: Bee Queen Trade Table

| Flower | Source Region | Source Location | Royal Honey Received |
|--------|---------------|-----------------|---------------------|
| Moonpetal | Civilized Remnants | Healer's Garden | 1 |
| Frost Lily | Frozen Reaches | Ice Caves | 1 |
| Water Bloom | Sunken District | Flooded areas | 1 |

- Maximum 3 royal_honey (one per flower TYPE, not per flower)
- Trading 3 times unlocks allied state
- Royal honey: Full health restore + removes one condition

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2024 | Initial draft |
| 0.2 | 2025-12-11 | Phase 2 consistency fixes: Removed Fungal Depths as moonpetal source (CC-5) |
