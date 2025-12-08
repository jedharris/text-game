# The Shattered Meridian - A Large Game Design

## Overview

**The Shattered Meridian** is a large, challenging text adventure game that demonstrates the full capabilities of the game engine. The player explores a fractured world where an ancient magical disaster has left reality unstable, creating diverse environments connected by the remnants of a once-great civilization.

### Core Themes
- **Recovery and restoration** - helping NPCs, repairing structures, curing afflictions
- **Relationship building** - earning trust, loyalty, and alliance through actions
- **Environmental mastery** - understanding and navigating hazardous conditions
- **Moral complexity** - choices with lasting consequences on NPCs and the world

### Design Goals
1. Showcase all actor interaction capabilities (combat, healing, services, domestication, packs, conditions, environmental effects)
2. Provide diverse challenges beyond combat and puzzles
3. Create persistent effects that span multiple rooms and extended time periods
4. Emphasize player agency and multiple solutions to problems
5. Use LLM narration traits effectively for atmospheric storytelling

---

## World Structure

The game is organized into **five major regions** connected by a central hub. Each region emphasizes different interaction types while maintaining thematic coherence.

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

### The Meridian Nexus (Hub)

The shattered remains of the magical ley line intersection that once powered the civilization. Now a crumbling observatory where fragments of reality occasionally overlap.

**Rooms:**
- **Nexus Chamber** - Central hub with exits to all regions; contains a damaged waystone that can be repaired for fast travel
- **Observatory Platform** - Overlooks the broken landscape; telescope reveals clues about distant regions
- **Keeper's Quarters** - Abandoned home of the last Meridian Keeper; contains journals explaining the disaster
- **Crystal Garden** - Shattered power crystals that can be gradually restored; provides persistent buffs when activated

**Key NPCs:**
- **The Echo** - A spectral remnant of the last Keeper who appears intermittently; provides guidance but cannot act directly; trust must be earned through restoring elements of the Nexus

**Traits for LLM:**
- Observatory: "impossibly tall spires", "shimmering air where reality is thin", "distant sounds that don't match what you see", "perpetual twilight", "geometric patterns carved into every surface"
- Keeper's Quarters: "dust motes suspended motionless", "half-completed meals frozen in time", "books open to marked pages", "personal effects arranged with care"

---

## Region 1: The Fungal Depths

An underground network of caverns where a magical fungal infestation has spread following the disaster. The environment itself is hostile, but also contains powerful curative resources.

### Environmental Mechanics
- **Spore zones** with varying contamination levels (low/medium/high)
- **Fungal infection** condition that progresses over time
- **Bioluminescent mushrooms** that respond to water and can light dark areas

### Rooms

#### Cavern Entrance
Gateway to the depths. Safe breathing zone. Contains a **Fungal Scholar** NPC who studies the infection but has become infected themselves (UC1 parallel).

**Scholar Aldric:**
- Has severe fungal infection (severity 80, progressing)
- Offers teaching service (mycology knowledge) in exchange for treatment
- If cured, reveals locations of curative plants and safe paths through the depths
- If the player delays too long, Aldric dies and certain routes become much harder

**Traits:** "damp stone walls", "cool air from below", "distant dripping echoes", "faint phosphorescent glow"

#### Luminous Grotto
Bioluminescent mushroom garden. Medium spore concentration. Contains **silvermoss** (cures fungal infection) growing in hard-to-reach places.

**Puzzle:** Water specific mushrooms in correct sequence to increase light level, revealing ceiling inscriptions that describe the safe path through the Spore Heart.

**Traits:** "soft blue-green glow", "delicate fungal tendrils", "sweet earthy scent mixed with decay", "crystal-clear pool reflecting light"

#### Spore Heart
High contamination zone. The source of the fungal spread. Contains an ancient **Spore Mother** creature.

**Spore Mother:**
- Not inherently hostile - desperate and suffering
- Has `needs: {healing: true}` - the infection is killing her too
- Can be fought (very difficult - regenerates, spawns sporelings)
- Can be healed by applying rare **heartmoss** (found deeper in caves)
- If healed, becomes friendly and the spore spread reverses throughout the region
- Pack of **Sporelings** (followers) mirror her disposition

**Environmental effect:** Each turn in high-spore areas applies fungal infection condition to non-immune actors.

**Traits:** "pulsing organic walls", "thick visible spores in the air", "rhythmic breathing sounds from the fungus itself", "warmth that feels alive"

#### Myconid Sanctuary
Safe zone maintained by **Myconid colony** (sentient mushroom beings). Neutral disposition unless player has killed fungi in other areas.

**Services:**
- Cure fungal infection (accepts healing items or rare minerals)
- Teach spore resistance (grants partial immunity)
- Trade unique items (spore lanterns, breathing masks)

**Relationship effects:**
- Trust >= 3: Discounted services
- Trust >= 5: Myconids share secret passages, avoid fighting player even if provoked
- Killing spore creatures elsewhere decreases trust

**Traits:** "orderly rings of mushroom folk", "silent communication through spore puffs", "strange hospitality", "geometric arrangement of everything"

#### Deep Root Caverns
Lowest level. Non-breathable atmosphere (requires breathing equipment or spell). Contains **heartmoss** needed to cure Spore Mother.

**Environmental hazards:**
- No natural light
- Suffocation mechanics (breath tracking)
- Cold temperature (hypothermia condition over time)

**Traits:** "absolute darkness beyond your light", "roots as thick as trees", "ancient silence", "cold that seeps into bones", "sense of immense depth"

### Region Conditions
- **Fungal Infection:** Progresses without treatment, damages health per turn, is contagious at high severity
- **Spore Resistance:** Temporary buff from Myconid treatment, reduces infection acquisition

### Persistent Effects
- Curing the Spore Mother purifies all rooms, removing spore hazards permanently
- Scholar Aldric (if saved) becomes available in Nexus as teacher/guide
- Myconid alliance provides ongoing support (healing items appear in inventory periodically)

---

## Region 2: The Beast Wilds

Overgrown wilderness where magical beasts have become more intelligent and organized since the disaster. Emphasizes pack dynamics, domestication, and the tension between violence and diplomacy.

### Rooms

#### Forest Edge
Transition zone. Signs of territorial markings. Safe exploration zone for learning about the wildlife.

**Items:** Venison (for feeding), tracking equipment, hunter's journal describing animal behaviors

**Traits:** "claw marks on tree bark", "silence that feels watchful", "game trails through undergrowth", "old hunting blinds reclaimed by vines"

#### Wolf Clearing (UC3 Parallel)
**Winter Wolf Pack** territory. A pack of hungry wolves led by an **Alpha Wolf**.

**Pack Structure:**
- Alpha Wolf (pack_role: "alpha", needs: {hungry: true})
- 3 Grey Wolves (pack_role: "follower", follows_alpha)

**Multiple Approaches:**
1. **Combat:** Defeat the pack (difficult; they coordinate attacks)
2. **Feeding:** Satisfy alpha's hunger repeatedly to build gratitude
3. **Intimidation:** Defeat alpha to cause pack to flee (doesn't create allies)
4. **Luring:** Use food to draw wolves away from key exits

**Domestication:** If alpha's gratitude >= 3, pack becomes friendly and will:
- Follow player as companions
- Help in combat in other areas
- Track scents to find hidden items/NPCs

**Morale:** At low health, alpha flees; pack follows. They return hostile after some time unless domesticated.

**Traits:** "yellow eyes reflecting in shadows", "low warning growls", "restless movement at the edge of sight", "the smell of a recent kill"

#### Bee Hive Grove
Giant bee colony with valuable honey (powerful healing). Requires diplomacy or careful strategy.

**Bee Queen:**
- Neutral unless disturbed
- Can be communicated with through specific flower offerings
- Provides **Royal Honey** (full heal + condition removal) in exchange for rare flowers from other regions

**Violence approach:** Attacking bees triggers swarm (area damage, poisoning). Can be driven off with smoke/fire but damages the grove permanently, losing access to honey.

**Traits:** "constant humming vibration", "honeycomb architecture", "organized worker patterns", "heavy sweetness in the air"

#### Predator's Den
Home of a **Dire Bear** and her cubs. Extremely dangerous if approached carelessly.

**Dire Bear:**
- Hostile by default (protecting cubs)
- Cubs are sick with a treatable condition
- If player heals cubs (using herbs from garden region), bear becomes grateful ally
- If cubs die, bear becomes permanently hostile and tracks player across the wilds

**Traits:** "massive claw marks", "thick musk smell", "scattered bones of past prey", "protective tension in the air"

#### Spider Nest Gallery (UC7 Parallel)
Underground area infested with **Spider Swarm** led by a **Spider Queen**.

**Pack Structure:**
- Spider Queen (alpha, venomous)
- Giant Spider workers (followers, web spray attacks)

**Environmental:**
- Web-covered areas give spiders combat bonuses
- Burning webs reduces their advantage but alerts the swarm
- Can sneak through with high caution

**Loot:** Spider silk (valuable crafting material), venom sacs (alchemical ingredient)

**Traits:** "glistening web strands", "skittering in the darkness", "egg sacs pulsing with movement", "prey wrapped in silk"

#### The Wounded Hunter
Not a room but a **wandering NPC** who appears in various wild locations.

**Hunter Sira:**
- Found injured (bleeding condition, leg injury = cannot_move)
- Hostile toward beasts after they killed her partner
- If healed and befriended, teaches tracking skill
- If player has domesticated wolves, initial hostility - must convince her they can coexist
- Can become companion, helps in combat with ranged attacks

**Relationship complexity:** Saving her creates obligation; her anti-beast prejudice conflicts with domestication approaches

### Persistent Effects
- Domesticated wolf pack follows player throughout game (with limitations in some areas)
- Spider Queen defeat or alliance affects regional safety
- Hunter companion provides combat support and tracking information

---

## Region 3: The Sunken District

A partially flooded urban area where an entire district fell into underground waterways. Combines drowning hazards, underwater exploration, and social interaction with survivors.

### Environmental Mechanics
- **Breath tracking** in submerged areas
- **Swimming** skill affects underwater movement
- **Breathing items** (air bladders, enchanted items) provide limited air
- **Cold water** in deep areas causes hypothermia

### Rooms

#### Flooded Plaza
Entry point. Waist-deep water. A makeshift camp of survivors clings to elevated platforms.

**Survivor Camp NPCs:**
- **Camp Leader Mira:** Manages scarce resources; offers quests; tracks player reputation
- **Old Swimmer Jek:** Teaches swimming skill (service, accepts payment or favors)
- **Child Survivors:** Give small hints; react to player's kindness or cruelty

**Traits:** "debris floating in murky water", "improvised bridges between rubble", "desperate resourcefulness", "constant splashing echoes"

#### Drowning Sailor Cave (UC5 Parallel)
Underwater cave where a **Drowning Sailor** is trapped.

**Sailor Garrett:**
- Low breath, taking damage each turn
- Has exhaustion condition (cannot_swim effect)
- Will drown in ~5 turns without intervention

**Rescue options:**
1. Give breathing item (buys time)
2. Pull/lead to safety
3. Cure exhaustion first then help swim out

**If rescued:**
- Becomes extremely grateful
- Reveals location of sunken treasure
- Can become companion with diving expertise

**Traits:** "bubbles rising desperately", "fingers scraping rock", "muffled cries", "current pulling toward the deep"

#### Submerged Library
A scholarly institution now half-underwater. Contains important lore and unique items.

**Multi-depth structure:**
- Surface level: Breathable, contains soggy but readable books
- Flooded stacks: Non-breathable but breathing items work; contains valuable texts
- Deep archive: Non-breathable, breathing items don't work; requires holding breath or magic

**Waterlogged Archivist (construct):**
- Automaton librarian, still following protocols
- Immune to drowning (construct)
- Will provide information services if player proves "scholarly intent" (present a book or ask knowledge questions)
- Can be repaired for improved services

**Traits:** "ink bleeding from ruined pages", "fish swimming through shelves", "eerie preservation bubbles around some texts", "mechanical clicking from somewhere below"

#### Canal Networks
Maze of flooded tunnels connecting locations. Different routes have different hazards.

**Route options:**
- **Surface canal:** Safe breathing, longer path, guarded by territorial **Canal Eels** (neutral unless provoked)
- **Deep shortcut:** Faster but requires breath management; cold damage
- **Collapsed route:** Blocked but contains air pockets; can be cleared with effort

**Traits:** "narrow stone walls", "current tugging at your legs", "architectural remnants of better days", "bioluminescent algae marking depth"

#### The Merchant's Wreck (UC6 Parallel)
An overturned trade barge where an **Injured Merchant** is trapped.

**Merchant Delvan:**
- Has bleeding condition and broken_leg
- Trapped under cargo
- Will die without treatment

**Rescue requirements:**
1. Stop bleeding (bandages or healing)
2. Free from cargo (strength or lever/tool)
3. Help to safety (carry or support)

**If rescued:**
- Offers substantial reward (gold, rare items)
- Provides discount on services throughout game
- Can connect player to black market contacts in Civilized Remnants

**Traits:** "scattered trade goods", "creaking waterlogged wood", "desperate pleading", "blood mixing with water"

### Persistent Effects
- Rescued NPCs appear in Survivor Camp, improving morale and available services
- Swimming skill learned here applies throughout game
- Good reputation with survivors provides ongoing support (occasional supply gifts)
- Failing to rescue NPCs has consequences (camp morale drops, fewer services available)

---

## Region 4: The Frozen Reaches

A mountain region where the disaster caused perpetual winter. Emphasizes temperature survival, construct combat, and ancient mysteries.

### Environmental Mechanics
- **Temperature zones:** freezing, cold, normal, warm
- **Hypothermia condition:** Progresses in cold areas, damages health
- **Warming items:** Provide protection (enchanted cloaks, fire sources)
- **Ice hazards:** Some surfaces are slippery or breakable

### Rooms

#### Frozen Pass
Entry point. Cold temperature. Path through mountain.

**Environmental storytelling:** Frozen travelers (long dead), abandoned supply caches, signs of rushed evacuation.

**Items:** Cold-weather gear, preserved supplies, partial maps of the region

**Traits:** "biting wind", "snow that doesn't melt", "ice crystals in the air", "impossible silence between gusts"

#### Temple Sanctum (UC2 Parallel)
Ancient temple guarded by **Stone Golems**.

**Guardian Golems (2):**
- Constructs: immune to poison, disease, bleeding; don't need to breathe
- Hostile when player enters
- High health, high armor, devastating attacks

**Combat approach:**
- Use cover (stone pillars provide 80% damage reduction)
- Hit-and-run tactics (they're slow)
- Environmental exploitation (collapsing ice)

**Non-combat approach:**
- Find temple password in Keeper's journals (Nexus)
- Present correct ritual offering
- Repair their control crystal (found elsewhere)

**Treasure:** Contains powerful cold-resistance equipment and lore tablets

**Traits:** "ancient carved stone faces", "glowing runes in geometric patterns", "grinding stone steps", "eternal vigilance"

#### Ice Caves
Natural cave system with treacherous footing. Freezing temperature.

**Hazards:**
- Thin ice over deep water (breaking = drowning + cold damage)
- Ice bridges requiring careful movement
- Hidden crevasses

**Rewards:** Rare ice crystals (alchemical ingredients), frozen artifacts

**Traits:** "crystal blue walls", "your breath freezing instantly", "cracking sounds underfoot", "beautiful deadly formations"

#### Hot Springs Refuge
Volcanic activity creates warm zone. Natural healing area.

**Hot Springs:**
- Normal temperature (hypothermia recovery)
- Bathing restores health over time
- Safe rest area

**Steam Salamanders:**
- Neutral unless attacked
- Can be befriended with fire-aspected items
- Allied salamanders provide warmth aura (cold immunity when nearby)

**Traits:** "sulfurous mist", "warmth like a embrace", "multicolored mineral deposits", "lazy steam creature movements"

#### Frozen Observatory
High peak with clear view. Extreme cold (can only stay briefly without protection).

**Ancient Telescope:**
- Reveals distant locations when repaired
- Shows current state of other regions
- Provides hints about sequence of optimal exploration

**Repair quest:** Requires crystal lens (from Ice Caves), mounting bracket (from Temple), cleaning supplies (from Nexus)

**Traits:** "wind trying to tear you away", "stars visible during day", "impossible distances revealed", "frost forming on your eyelashes"

### Persistent Effects
- Completing temple unlocks fast travel to Frozen Reaches
- Steam Salamander alliance provides cold immunity item
- Observatory repair reveals optimal paths throughout game

---

## Region 5: The Civilized Remnants

The surviving settlement where refugees have gathered. Focuses on social interaction, services, reputation, and morally complex choices.

### Rooms

#### Town Gate
Entry checkpoint. Guards check for infection/contamination.

**Guards:**
- Hostile to obviously infected players
- Can be bribed, intimidated, or convinced with proper documentation
- Befriending guards provides information about town events

**Traits:** "weathered wooden walls", "suspicious eyes", "controlled desperation", "smell of smoke and humanity"

#### Market Square
Central trading area. Multiple vendor NPCs.

**Vendors:**
- **Herbalist:** Sells healing items, buys rare plants, teaches herbalism (UC4 service pattern)
- **Weaponsmith:** Sells/repairs weapons, services require gold
- **Curiosity Dealer:** Trades rare items, reputation-gated inventory

**Reputation effects:**
- Good reputation: Better prices, access to rare items
- Bad reputation: Higher prices, some vendors refuse service
- High trust with specific vendors: Special services unlocked

**Traits:** "loud bargaining", "exotic scents", "desperation mixed with hope", "watchful militia presence"

#### Healer's Sanctuary (UC4 Parallel)
**Healer Elara's** place of practice.

**Services:**
- Cure poison (accepts rare herbs or gold)
- Cure disease (accepts specific items)
- Heal wounds (accepts gold)
- Teach herbalism skill (grants ability to safely handle toxic plants)

**Relationship:**
- Trust >= 3: 50% discount on services
- Trust >= 5: Teaches rare healing techniques, shares personal quest
- If player saved infected NPCs from other regions, Elara is impressed (+trust)

**Garden area:**
- Contains both curative and toxic plants
- Without herbalism knowledge, touching nightshade causes contact poison
- With knowledge, can safely harvest valuable ingredients

**Traits:** "dried herbs hanging everywhere", "mortar and pestle sounds", "smell of clean medicine", "quiet competence"

#### Council Hall
Governing body of survivors. Political quests and reputation tracking.

**Councilors:**
- **Pragmatist:** Values results over methods
- **Idealist:** Values ethics over efficiency
- **Merchant:** Values trade and prosperity

**Quests involve moral choices:**
- Exile infectious refugees vs. allocate scarce medicine?
- Trade with dangerous outsiders vs. maintain isolation?
- Punish criminals harshly vs. show mercy?

Player choices affect town state and NPC availability.

**Traits:** "heated debates", "exhausted leadership", "weight of impossible decisions", "hope struggling against despair"

#### Broken Statue Hall (UC8 Parallel)
Contains damaged **Stone Guardian** that can be repaired.

**Damaged Guardian:**
- Ancient construct, once protected the settlement
- Currently non-functional
- Repair requires: stone chisel, animator crystal (from Nexus), specific ritual

**If repaired:**
- Becomes loyal guardian
- Can defend settlement from external threats
- Changes town's defensive posture

**Traits:** "shattered stone limbs", "faded inscription of purpose", "sense of patient waiting", "ancient protective runes"

#### The Undercity
Secret criminal network beneath the town.

**Contacts:**
- **Fence:** Buys stolen/questionable items
- **Information Broker:** Sells secrets about NPCs and locations
- **Assassin:** Offers contract services (highly morally complex)

**Access:** Requires reputation with certain NPCs or payment

**Consequences:** Using undercity services may be discovered, affecting surface reputation

**Traits:** "dim lantern light", "whispered negotiations", "dangerous competence", "moral flexibility"

### Persistent Effects
- Town reputation affects all NPC interactions
- Council decisions change available services and town safety
- Repaired guardian provides settlement defense
- Undercity reputation tracks separately, can conflict with surface reputation

---

## Cross-Region Mechanics

### The Infection Spread
If the Spore Mother is not healed within a certain turn count:
- Fungal infection begins appearing in other regions
- NPCs in Civilized Remnants become infected
- Town gate guards become more suspicious of everyone

### The Winter's Reach
If the Frozen Observatory is not repaired:
- Cold begins spreading to other regions
- Some outdoor areas become cold-temperature zones
- NPCs comment on worsening conditions

### Pack Companions
Domesticated creatures follow these rules:
- Wolf pack: Cannot enter Civilized Remnants (guards won't allow)
- Steam salamanders: Uncomfortable in cold, won't follow into Frozen Reaches without encouragement
- Domestication status persists through the entire game

### Reputation Networks
NPCs share information:
- Rescuing NPCs in one region improves reputation in others (word spreads)
- Acts of cruelty also spread
- The Echo (Nexus) comments on player's overall trajectory

---

## Persistent Conditions and Long-Term Effects

### Player Conditions
| Condition | Source | Effect | Treatment |
|-----------|--------|--------|-----------|
| Fungal Infection | Spore areas | Damage per turn, progresses, contagious | Silvermoss, Myconid cure, Healer service |
| Hypothermia | Cold areas | Damage per turn, slowed movement | Warm clothing, Hot Springs, warming items |
| Drowning | Underwater | Rapid health loss | Surface, breathing items |
| Contact Poison | Toxic plants | Damage per turn, agility reduction | Antidote, Healer service |
| Bleeding | Combat | Continuous damage | Bandages, Healer, clotting herbs |

### Knowledge/Skills Gained
| Skill | Teacher | Effect |
|-------|---------|--------|
| Herbalism | Healer Elara | Safe plant handling, identify curative plants |
| Swimming | Old Swimmer Jek | Improved underwater mobility, breath efficiency |
| Tracking | Hunter Sira | Find hidden items, track NPCs |
| Mycology | Scholar Aldric | Understand fungal creatures, navigate spore areas |
| Spore Resistance | Myconids | Reduced infection acquisition |

### Relationship Thresholds
| Threshold | Effect |
|-----------|--------|
| Gratitude >= 3 | Creature domestication, companion behavior |
| Trust >= 3 | Service discounts (50%) |
| Trust >= 5 | Special services, loyalty quests |
| Fear >= 5 | NPC compliance, but may flee or betray |

---

## Sample Play Sequences

### Diplomatic Path Through Beast Wilds
1. Find venison at Forest Edge
2. Enter Wolf Clearing, offer venison to Alpha Wolf
3. Alpha's hunger satisfied, disposition shifts to neutral
4. Repeat feeding until gratitude >= 3
5. Pack becomes friendly, follows player
6. Use pack's tracking to find hidden path to Predator's Den
7. Wolf pack intimidates cubs' predator (smaller creature), allowing safe approach to heal cubs
8. Dire Bear becomes grateful, entire Beast Wilds becomes safe

### Rescue Sequence in Sunken District
1. Learn swimming from Old Swimmer Jek
2. Acquire air bladder from dock
3. Dive to Drowning Sailor Cave
4. Give air bladder to Sailor Garrett (buys time)
5. Cure exhaustion with herbs from Garden
6. Guide sailor to surface
7. Sailor reveals location of sunken treasure
8. Use diving expertise to retrieve valuable items
9. Trade items in Civilized Remnants for needed supplies

### Temple Challenge Approach
1. Search Keeper's Quarters for temple research
2. Find partial password
3. Travel to Temple Sanctum
4. Attempt password (partial, golems hesitate but still fight)
5. Use pillars for cover, survive initial assault
6. Find control crystal location hint in temple inscriptions
7. Retrieve control crystal from Ice Caves
8. Return and deactivate golems
9. Access temple treasures and cold-resistance gear

---

## Documentation Issues and Missing Capabilities

> **UPDATE (Post-Framework Upgrade):** Most of the issues listed below have been addressed by the behavior libraries. See updated status.

### Documentation Gaps - NOW ADDRESSED

1. **Darkness and Light Sources** ✅ RESOLVED
   - `darkness_lib` provides full darkness enforcement
   - Documented in [Behavior Libraries](../user_docs/authoring_manual/05_behaviors.md#darkness_lib---visibility-and-darkness)
   - Location property `requires_light: true` enables darkness mechanics

2. **Time Passage and Scheduled Events** ✅ RESOLVED
   - `timing_lib` provides `schedule_event()` and turn counter access
   - Documented in [Behavior Libraries](../user_docs/authoring_manual/05_behaviors.md#timing_lib---turn-counter-and-scheduled-events)
   - Turn counter documented in [Advanced Topics](../user_docs/authoring_manual/11_advanced.md#12-the-turn-system)

3. **NPC Movement Between Rooms** ✅ RESOLVED
   - `npc_movement_lib` provides patrol routes and wandering
   - Documented in [Behavior Libraries](../user_docs/authoring_manual/05_behaviors.md#npc_movement_lib---npc-patrol-and-wandering)
   - Hunter Sira wandering behavior fully supported

4. **Crafting/Combining Items** ✅ RESOLVED
   - `crafting_lib` provides recipe matching and crafting
   - Documented in [Behavior Libraries](../user_docs/authoring_manual/05_behaviors.md#crafting_lib---item-crafting-and-combining)
   - Telescope repair use case fully supported

5. **Inventory Weight/Capacity** - CUSTOM IMPLEMENTATION
   - Still requires custom behavior (game-specific design choice)
   - Example provided in [big_game_implementation.md](big_game_implementation.md)

6. **Dialog Trees/Conversation** ✅ RESOLVED
   - `dialog_lib` provides topic management and prerequisites
   - Documented in [Behavior Libraries](../user_docs/authoring_manual/05_behaviors.md#dialog_lib---npc-dialog-and-topics)
   - Complex NPC conversations fully supported

### Engine Capabilities - NOW ADDRESSED

1. **Global Flags System** ✅ RESOLVED
   - `state.set_flag()` and `state.get_flag()` built into core
   - Documented in [Advanced Topics](../user_docs/authoring_manual/11_advanced.md#111-player-flags)

2. **Timed Events** ✅ RESOLVED
   - `timing_lib.schedule_event()` with repeating support
   - Turn counter via `state.turn_count`

3. **Area-Wide Effects** - CUSTOM IMPLEMENTATION
   - Pattern documented in [big_game_implementation.md](big_game_implementation.md)
   - Region definitions are game-specific

4. **Companion Following** ✅ RESOLVED
   - `companion_lib` provides full companion mechanics
   - Location restrictions and terrain restrictions supported
   - Documented in [Behavior Libraries](../user_docs/authoring_manual/05_behaviors.md#companion_lib---companion-following)

5. **Reputation System** - CUSTOM IMPLEMENTATION
   - Faction reputation pattern in [big_game_implementation.md](big_game_implementation.md)
   - Uses existing relationship system as foundation

---

## LLM Narrator Style Guide

### Overall Tone
The game should feel like a dark fantasy survival story with moments of hope. The world is broken but not beyond saving. NPC interactions should feel meaningful because help is scarce.

### Room Trait Guidelines
Each room should have 5-8 traits covering:
- Sensory detail (sight, sound, smell)
- Emotional atmosphere
- Hints about purpose/history
- Environmental hazards or features

### State Variant Recommendations
Define state variants for key conditions:
- **Purified/Corrupted** states for fungal areas
- **Frozen/Thawed** states for temperature-affected areas
- **Flooded/Drained** states for water areas
- **Hostile/Peaceful** states based on creature disposition

### Example State Variants for Wolf Clearing
```json
{
  "state_variants": {
    "wolves_hostile": "The wolves circle at the edge of the firelight, teeth bared, waiting for weakness.",
    "wolves_neutral": "The wolves watch from the shadows, neither attacking nor fleeing, assessing.",
    "wolves_friendly": "The wolf pack rests nearby, occasionally glancing your way with something like affection.",
    "wolves_absent": "The clearing feels empty. Pawprints mark where the pack once lived."
  }
}
```

### NPC Description Evolution
NPCs should have traits that reflect their condition and relationship:

**Scholar Aldric (infected):**
- Initial: "pale and sweating", "trembling hands", "desperate eyes", "visible fungal patches"
- After cure: "color returning to cheeks", "steady hands", "grateful smile", "scars where infection was"

**Alpha Wolf (hostile):**
- Initial: "hackles raised", "low continuous growl", "muscles tensed to spring", "calculating yellow eyes"
- After domestication: "relaxed posture", "attentive ears", "waiting for direction", "loyal presence"

---

## Estimated Scope

### Rooms
- Nexus Hub: 4 rooms
- Fungal Depths: 5 rooms
- Beast Wilds: 5 rooms
- Sunken District: 5 rooms
- Frozen Reaches: 5 rooms
- Civilized Remnants: 6 rooms
- **Total: ~30 rooms**

### NPCs
- Friendly/service NPCs: ~10
- Hostile creatures (with pack potential): ~15
- Neutral/conditional NPCs: ~8
- **Total: ~33 actors**

### Items
- Curative items: ~10
- Quest items: ~15
- Weapons/equipment: ~10
- Trade goods: ~10
- Environmental tools: ~10
- **Total: ~55 items**

### Custom Behaviors Needed
- Environmental effect processors (spores, cold, drowning)
- Domestication/feeding mechanics
- NPC service provision
- Quest/flag tracking
- Time-based progression

---

## Next Steps

1. Finalize this design document with any requested changes
2. Create detailed room-by-room specifications with JSON structures
3. Define all actors with complete property sets
4. Design custom behaviors for mechanics not covered by library
5. Create test scenarios for each use case pattern
6. Iterative implementation and testing by region
