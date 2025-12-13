# The Shattered Meridian - A Large Game Design

## Overview

**The Shattered Meridian** is a large, challenging text adventure game that demonstrates the full capabilities of the game engine. The player explores a fractured world where an ancient magical disaster has left reality unstable, creating diverse environments connected by the remnants of a once-great civilization.

The game centers on **Echo**, a spectral remnant of the last Meridian Keeper, who serves as the player's guide and moral compass. Echo tracks the player's commitments to NPCs across all regions and reacts to both fulfilled promises and abandonments. The ultimate goal is to repair the broken waystone in the Meridian Nexus, which requires collecting five fragments from across the world—each earned through significant deeds that demonstrate the player's character.

### Core Themes
- **Commitment and consequence** - Promises made to NPCs create timed obligations. Players who overcommit face impossible choices; the system rewards genuine effort even when some failures occur.
- **Recovery and restoration** - Helping NPCs, repairing structures, curing afflictions. Each major restoration contributes a waystone fragment toward the endgame.
- **Trust and reputation** - Echo trust reflects cumulative moral trajectory. NPC trust affects services, reveals, and companion availability. Gossip spreads between regions, so reputations follow players.
- **Companion relationships** - Domesticated creatures and rescued NPCs can become companions with region-specific capabilities and limitations. Managing multiple companions requires understanding their interactions.
- **Moral complexity** - Dark paths (assassination, abandonment) remain viable but permanently lock certain endings. Redemption is possible but consequences persist.

### Design Goals
1. **Commitment system as core mechanic** - Timed promises to NPCs create meaningful tension and replay value. Most timer overlaps are resolvable with planning; some (Sunken District dual-rescue) are intentionally impossible on first playthrough.
2. **Multiple viable paths** - Diplomatic, violent, and dark approaches all complete the game, but with different endings and locked content.
3. **Companion depth** - Each companion type has logical region restrictions (wolves can't swim, salamanders extinguish in water). Companions auto-wait at boundaries and rejoin automatically.
4. **Information as mechanic** - Gossip spreads at specific rates. Confession before discovery produces different outcomes than being caught. Echo always knows.
5. **Persistent consequences** - NPCs can die permanently, environmental spreads affect all regions, and some actions permanently lock endings.
6. **Seven-tier ending system** - Based on Echo trust at waystone completion, ranging from Triumphant (trust 5+, Echo becomes companion) to Pyrrhic (trust -6, Echo refuses ceremony). Assassination permanently locks Triumphant ending.
7. Use LLM narration traits effectively for atmospheric storytelling

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

The shattered remains of the magical ley line intersection that once powered the civilization. Now a crumbling observatory where fragments of reality occasionally overlap. This serves as the player's home base and the location of critical endgame content.

**Rooms:**
- **Nexus Chamber** - Central hub with exits to all regions; contains the damaged waystone that is the ultimate repair goal. Each waystone fragment placed here advances the endgame. Wards prevent wolves from entering.
- **Observatory Platform** - Overlooks the broken landscape; telescope reveals clues about distant regions
- **Keeper's Quarters** - Abandoned home of the last Meridian Keeper; contains journals explaining the disaster and partial temple passwords
- **Crystal Garden** - Shattered power crystals that can be gradually restored; provides persistent buffs when activated. Crystal restoration grants +1 Echo trust.

**Key NPCs:**
- **The Echo** - A spectral remnant of the last Keeper who serves as the game's moral compass and commitment tracker.

**Echo Mechanics:**
- **Trust range**: -6 to 5+. Starting trust is 0.
- **Trust gains**: +1 for saving major NPCs (Aldric, Sira, Garrett, Delvan), +1 for healing Spore Mother, +1 for restoring crystals, +0.5 for fulfilling commitments, +0.5 for placing waystone fragments.
- **Trust losses**: -1 for abandoned commitments (reduced to -0.5 with partial credit), -2 per assassination.
- **Recovery cap**: Maximum +1 trust per Nexus visit (prevents grinding).
- **Trust floor behavior**: At trust -6, Echo refuses to manifest. Player loses commitment tracking and guidance but game remains completable.
- **Commitment tracking**: Echo remembers all promises made to NPCs across all regions. On each Nexus visit, Echo comments on active commitments, recently fulfilled ones, and abandonments.
- **Instant awareness**: Echo knows about assassinations immediately, even if NPCs don't discover them.

**Waystone Repair (Endgame):**
The damaged waystone requires five fragments, each from a different region:
| Fragment | Source | Acquisition |
|----------|--------|-------------|
| Spore Heart | Fungal Depths | Gift from healed Spore Mother |
| Alpha Fang | Beast Wilds | Gift from high-trust wolf pack |
| Water Pearl | Sunken District | Reward from Archivist quest |
| Ice Shard | Frozen Reaches | Extract from ice caves |
| Town Seal | Civilized Remnants | Hero status OR Guardian repair |

Placing all five fragments and completing the ritual produces the ending, which varies based on Echo trust (see Ending System).

**Traits for LLM:**
- Observatory: "impossibly tall spires", "shimmering air where reality is thin", "distant sounds that don't match what you see", "perpetual twilight", "geometric patterns carved into every surface"
- Keeper's Quarters: "dust motes suspended motionless", "half-completed meals frozen in time", "books open to marked pages", "personal effects arranged with care"

---

## Region 1: The Fungal Depths

An underground network of caverns where a magical fungal infestation has spread following the disaster. The environment itself is hostile, but also contains powerful curative resources. This region has the game's longest commitment timer, making it forgiving for new players but still consequential if completely ignored.

### Environmental Mechanics
- **Spore zones** with varying contamination levels (low/medium/high)
- **Fungal infection** condition that progresses over time
- **Bioluminescent mushrooms** that respond to water and can light dark areas

### Region Commitment: Scholar Aldric

**Timer**: 50-60 turns from first encounter (longest in game)

This generous timer allows cross-region exploration without immediate pressure. Aldric's slow decline creates background tension but rarely forces abandonment of other commitments.

**Commitment flow**:
1. Player encounters Aldric, who asks for silvermoss treatment
2. Player promises to help (commitment registered with Echo)
3. Player has 50-60 turns to find and return silvermoss
4. If timer expires: Aldric dies, player discovers on return, Echo comments at Nexus
5. Gossip reaches Civilized Remnants in ~25 turns after death

**Design intent**: Aldric's long timer rarely conflicts with tighter timers (Sira, Garrett). His death is almost always preventable with minimal planning.

### Rooms

#### Cavern Entrance
Gateway to the depths. Safe breathing zone. Contains **Scholar Aldric** NPC who studies the infection but has become infected themselves.

**Scholar Aldric:**
- Has severe fungal infection (severity 80, progressing)
- Offers teaching service (mycology knowledge) in exchange for treatment
- If cured: reveals locations of curative plants and safe paths, becomes available in Nexus as teacher/guide, grants +1 Echo trust
- If player delays too long: Aldric dies, certain routes become harder, -1 Echo trust (or -0.5 with partial credit if player was genuinely trying)

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
- Can be healed by applying rare **heartmoss** (found in Deep Root Caverns)
- If healed: becomes friendly, spore spread reverses throughout the region, **gifts Spore Heart waystone fragment**, grants +1 Echo trust
- Pack of **Sporelings** (followers) mirror her disposition

**Environmental spread mechanic**: If Spore Mother not healed by turn 50, spores begin spreading to other regions. Turn 100: Town gate checks become more suspicious. Turn 150: Town NPCs become infected. Healing the Spore Mother halts spread permanently.

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

### Companion Restrictions
- **Wolves**: Can enter but uncomfortable; spore exposure affects them
- **Salamander**: Can enter; warmth has no benefit here but no restriction
- **Human companions**: Need spore masks or resistance to survive high-contamination zones
- **No single "correct" companion** for this region - tradeoffs exist for each

### Persistent Effects
- Curing the Spore Mother purifies all rooms, removing spore hazards permanently
- Scholar Aldric (if saved) becomes available in Nexus as teacher/guide
- Myconid alliance provides ongoing support (healing items appear in inventory periodically)

---

## Region 2: The Beast Wilds

Overgrown wilderness where magical beasts have become more intelligent and organized since the disaster. Emphasizes pack dynamics, domestication, and the tension between violence and diplomacy.

This region contains the game's tightest non-Sunken-District commitment (Sira's 8-turn timer), which serves as a designed trap for overcommitted players. It's also the primary source of wolf companions and demonstrates the wolf-human conflict theme.

### Region Commitments

**Hunter Sira** - 8-12 turns (tightest non-Sunken commitment)
- Found injured with bleeding condition and cannot_move
- Promises to help create commitment; timer starts immediately
- 8 base turns, +4 with "hope bonus" from positive player actions
- This is intentionally the tightest cross-region timer - a trap for players who have already made commitments elsewhere
- If player makes promises to Sira after committing to Aldric and bear cubs, some failure is likely
- Gossip about Sira's fate reaches Elara in 12 turns; abandonment gossip in 20 turns

**Bear Cubs** - 30-35 turns
- Cubs sick with treatable condition requiring healing herbs from Civilized Remnants
- More forgiving timer than Sira
- If cubs die: Dire Bear becomes permanently hostile and tracks player across region

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

**Domestication and Trust:**
- Gratitude >= 3: Pack becomes friendly companions
- Gratitude >= 5: Alpha **gifts Alpha Fang waystone fragment**
- Companions follow player throughout game with region restrictions
- Wolves provide: combat help, tracking to find hidden items/NPCs, territory knowledge in Beast Wilds

**Morale:** At low health, alpha flees; pack follows. They return hostile after some time unless domesticated.

**Wolf Companion Restrictions:**
- Cannot enter Nexus (wards repel them)
- Cannot enter Sunken District (instinct prevents entering water)
- Cannot survive extreme cold in Frozen Reaches (salamander warmth doesn't help)
- Can enter Civilized Remnants only through undercity tunnels
- When blocked: automatically wait outside, rejoin immediately when player exits

**Wolf Death:**
- Wolves can die protecting player (sacrifice mechanic - "exceptional bravery")
- Wolves can die from player forcing them into hazards
- Death is permanent - wolves don't respawn
- Echo comments on wolf deaths, especially senseless ones

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

**Approaches:**
1. **Combat**: Fight through (difficult, multiple spider waves)
2. **Stealth**: Sneak past without disturbing
3. **Coexistence**: Offer food to Spider Queen, establish non-hostility (does not create companion relationship)

**Coexistence mechanic**: Spiders can be pacified with sufficient food offerings. They don't become companions but stop attacking, allowing access to loot. This demonstrates that not all beast relationships need to reach domestication level.

**Loot:** Spider silk (valuable crafting material), venom sacs (alchemical ingredient)

**Traits:** "glistening web strands", "skittering in the darkness", "egg sacs pulsing with movement", "prey wrapped in silk"

#### The Wounded Hunter
Not a room but a **wandering NPC** who appears in various wild locations.

**Hunter Sira:**
- Found injured (bleeding condition, leg injury = cannot_move)
- Timer: 8 turns base, +4 "hope bonus" for positive interactions
- Hostile toward beasts after they killed her partner
- If healed: teaches tracking skill, grants +1 Echo trust
- If abandoned: bleeds out, gossip reaches Elara in 12 turns, player can confess before turn 20 for reduced penalty

**Wolf-Sira Conflict:**
- If player has domesticated wolves when saving Sira, initial hostility
- Sira won't travel with wolves until reconciliation dialog completed
- Reconciliation requires: trust threshold with both, player mediating, time for adjustment
- After reconciliation: can have both wolf and Sira companions simultaneously
- This conflict tests whether player can bridge the human-beast divide

**As Companion:**
- Helps in combat with ranged attacks
- Provides tracking guidance
- Cannot swim (needs training or equipment for Sunken District)
- Human companion rules apply for hazard resistance

**Connection to Elara:**
- Sira and Elara know each other
- If Sira dies or is abandoned, Elara eventually learns (gossip timing: 12-20 turns)
- Player has confession window before gossip arrives
- Confessing abandonment: -2 trust with Elara, recovery possible
- Discovery via gossip: -3 trust, permanent consequences

### Companion Restrictions (Beast Wilds)
- **Wolves**: This is their home region - full capabilities, territory knowledge, tracking
- **Salamander**: Can enter but warmth aura not especially useful
- **Human companions**: Generally safe but cannot enter Spider Nest without light source

### Persistent Effects
- Domesticated wolf pack follows player throughout game (with region restrictions)
- Spider Queen defeat or coexistence affects regional safety
- Hunter Sira (if saved) becomes available as companion with tracking and combat support
- Bear cubs fate affects Dire Bear behavior permanently
- Sira-Elara gossip connection creates confession window mechanic

---

## Region 3: The Sunken District

A partially flooded urban area where an entire district fell into underground waterways. Combines drowning hazards, underwater exploration, and social interaction with survivors.

**Design Intent**: This region is designed as a **solo challenge**. All companion types are systematically excluded, forcing the player to rely only on their own skills and resources. It also contains the game's tightest timer overlap (Garrett + Delvan), which is intentionally impossible to fully resolve on first playthrough.

### Region Commitments

**Dual Rescue Challenge:**
- **Garrett**: 5 turns from room entry, no hope extension possible
- **Delvan**: 10-13 turns from first encounter
- **Design**: Saving both requires optimal play that first-time players cannot achieve. This is intentional - creates replay value and meaningful choice.

**First Playthrough Reality:**
- Player likely saves one, not both
- Which one saved depends on encounter order and resource allocation
- Neither choice is "wrong" - both have value
- Echo reacts to the loss but acknowledges the save

### Environmental Mechanics
- **Breath tracking** in submerged areas
- **Swimming** skill affects underwater movement
- **Breathing items** (air bladders, enchanted items) provide limited air
- **Cold water** in deep areas causes hypothermia

### Companion Restrictions (All Excluded)
- **Wolves**: Instinct prevents entering water - auto-wait at region boundary
- **Salamander**: Would extinguish in water - auto-returns to Nexus
- **Human companions**: Cannot swim without training; training only available within this region
- **Result**: Player must complete Sunken District challenges alone

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
- **Timer: 5 turns from room entry, NO hope extension** (tightest in game)
- This is the first half of the dual rescue challenge

**Rescue options:**
1. Give breathing item (buys time but counts against turn limit)
2. Pull/lead to safety (requires swimmer skill or air bladder for player)
3. Cure exhaustion first then help swim out (uses precious turns)

**Critical Choice**: Resources spent on Garrett are unavailable for Delvan, and vice versa. Optimal first-playthrough cannot save both.

**If rescued:**
- Becomes extremely grateful, grants +1 Echo trust
- Reveals location of sunken treasure
- Can become companion with diving expertise (but can't leave region with companions)
- Gossip reaches camp NPCs immediately (same location)

**If abandoned:**
- Drowns, body can be found later
- -1 Echo trust (or -0.5 with partial credit if player was saving Delvan)
- Camp morale drops

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
- **Completing Archivist quest grants Water Pearl waystone fragment**

**Archivist Quest:**
- Recover three specific texts from different library depths
- Requires breath management and navigation skills
- Not time-pressured - no commitment timer
- Provides lore about the disaster and other regions

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
- **Timer: 10-13 turns from first encounter**
- This is the second half of the dual rescue challenge

**Rescue requirements:**
1. Stop bleeding (bandages or healing - uses resources)
2. Free from cargo (strength or lever/tool - takes time)
3. Help to safety (carry or support - takes time)

**Critical Choice**: Delvan's rescue takes longer than Garrett's but the timer is more forgiving. A player who goes to Garrett first will likely not have time for Delvan. A player who goes to Delvan first may save him but miss Garrett entirely.

**If rescued:**
- Offers substantial reward (gold, rare items), grants +1 Echo trust
- Provides discount on services throughout game
- Can connect player to undercity contacts in Civilized Remnants
- Gossip reaches undercity in 7 turns (criminal networks communicate quickly)

**If abandoned:**
- Dies under cargo, body found later
- -1 Echo trust (or -0.5 with partial credit if player was saving Garrett)
- Undercity contacts less available

**Traits:** "scattered trade goods", "creaking waterlogged wood", "desperate pleading", "blood mixing with water"

### Persistent Effects
- Rescued NPCs appear in Survivor Camp, improving morale and available services
- Swimming skill learned here applies throughout game
- Good reputation with survivors provides ongoing support (occasional supply gifts)
- Failing to rescue NPCs has consequences (camp morale drops, fewer services available)

---

## Region 4: The Frozen Reaches

A mountain region where the disaster caused perpetual winter. Emphasizes temperature survival, construct combat, and ancient mysteries.

**Design Intent**: This region has **no time-pressured commitments**. NPCs here don't need urgent rescue - the challenges are environmental and puzzle-based. This provides breathing room after the intensity of Sunken District and Beast Wilds timers.

**The Salamander Choice**: Without cold protection, the Observatory is inaccessible. Two options:
1. **Enchanted cloak** from Civilized Remnants (expensive, consumable uses)
2. **Salamander companion** from Hot Springs (permanent warmth aura)

The salamander is the "correct" companion for this region - provides cold immunity, can melt ice obstacles, and has no environmental conflicts here.

### Environmental Mechanics
- **Temperature zones:** freezing, cold, normal, warm
- **Hypothermia condition:** Progresses in cold areas, damages health
- **Warming items:** Provide protection (enchanted cloaks, fire sources)
- **Ice hazards:** Some surfaces are slippery or breakable
- **Cold spread mechanic**: If telescope not repaired by turn 75, cold begins spreading to other regions. Turn 125: Nexus boundary cold. Turn 175: Sunken District water freezes.

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
- Allied salamander provides warmth aura (cold immunity when nearby)

**Salamander as Companion:**
- **Primary benefit**: Cold immunity in all cold zones, including extreme cold at Observatory
- **Secondary benefit**: Can melt ice obstacles
- **Region restrictions**: Cannot enter water regions (would extinguish) - auto-returns to Nexus
- **Multi-companion interaction**: Mutual wariness with wolves, coexist after 3 turns together
- **Death risk**: Forcing salamander into water kills it permanently; Echo comments on senseless deaths

**Alternative cold protection**: Enchanted cloak from Civilized Remnants provides limited cold resistance but doesn't grant full immunity or ice-melting ability.

**Traits:** "sulfurous mist", "warmth like a embrace", "multicolored mineral deposits", "lazy steam creature movements"

#### Frozen Observatory
High peak with clear view. Extreme cold (can only stay briefly without salamander or exceptional protection).

**Ancient Telescope:**
- Reveals distant locations when repaired
- Shows current state of other regions (including environmental spread progress)
- Provides hints about sequence of optimal exploration
- **Halts cold spread when repaired** - essential for long games

**Repair quest:** Requires crystal lens (from Ice Caves), mounting bracket (from Temple), cleaning supplies (from Nexus). This is a cross-region fetch quest without time pressure.

**Strategic Value:**
- Without salamander: Very limited time here, repair difficult
- With salamander: Full access, comfortable exploration
- Repairing telescope is one of the two ways to halt environmental spreads (the other is waystone completion)

**Ice Shard waystone fragment**: Found in the extreme cold zone beyond the telescope, requires salamander companion or exceptional cold protection to reach.

**Traits:** "wind trying to tear you away", "stars visible during day", "impossible distances revealed", "frost forming on your eyelashes"

### Companion Restrictions (Frozen Reaches)
- **Wolves**: Cannot survive extreme cold even with salamander warmth - wait at pass entrance
- **Salamander**: The "correct" companion - provides warmth aura, ice melting, full region access
- **Human companions**: Need cold protection equipment; can access with cloak but limited time

### Persistent Effects
- Completing temple unlocks fast travel to Frozen Reaches
- Steam salamander companion provides cold immunity throughout game
- Observatory repair reveals optimal paths and halts cold spread
- Ice Shard fragment obtainable only with adequate cold protection

---

## Region 5: The Civilized Remnants

The surviving settlement where refugees have gathered. Focuses on social interaction, services, reputation, and morally complex choices.

**Design Intent**: This region provides the game's primary social/political content and introduces the **branding/undercity alternative gameplay**. Players with low reputation or who commit assassinations may be branded but can still complete the game, with undercity providing alternative services.

### Region Structure

**Surface Town**: Normal gameplay for players with neutral or positive reputation
- Market Square, Healer's Sanctuary, Council Hall, Broken Statue Hall
- Guards check for infection at town gate
- Services and quests available based on reputation

**Undercity**: Alternative economy for branded players or those preferring criminal paths
- Fence, Information Broker, Assassin (Shadow)
- Access via secret entrance or Delvan connection
- All essential services available, though at different prices/terms

### Branding Mechanics

**Triggers**:
- Town reputation drops to -5 or below
- Assassination discovery (20% chance per contract)
- Attack on townsperson
- 3+ undercity discoveries

**Effects** (branding is a visible mark on player's hand):
- NPCs see the brand directly - no gossip needed
- Service prices doubled
- Teaching denied
- Trust capped at 2 with most NPCs
- Good endings blocked until un-branded
- All locations remain accessible (unlike old exile system)

**Recovery (Un-branding)**:
- Reach reputation +3 while branded
- Complete a heroic act while branded
- Asha performs un-branding ceremony
- Scar remains but meaning transformed
- **BLOCKED permanently if assassination discovered**

**Guardian Path While Branded**:
- Undercity tunnels provide access to Broken Statue Hall
- Guardian can be repaired even when branded
- Triggers complicated NPC reactions (hero who was criminal?)

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
- **Advanced herbalism**: Available only from Elara - permanently lost if she dies

**Relationship:**
- Trust >= 3: 50% discount on services
- Trust >= 5: Teaches rare healing techniques, shares personal quest
- If player saved infected NPCs from other regions, Elara is impressed (+trust)

**Sira-Elara Connection:**
Elara and Sira know each other. This creates the game's primary confession/discovery mechanic:
- If Sira dies or is abandoned, gossip reaches Elara in 12-20 turns
- **Confession window**: Before turn 20, player can confess to Elara
  - Confession: -2 trust, recovery possible
  - Confession with context (saved someone else): -1.5 trust, recovery easier
- **Discovery**: After turn 20, if player visits Elara without confessing
  - Discovery via gossip: -3 trust, permanent consequences
  - Lie by omission (visited before gossip, didn't confess, returned after): -4 trust

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
- Turn away infectious refugees vs. allocate scarce medicine?
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
- **Grants Town Seal waystone fragment** (alternative to hero status)

**Access While Branded:**
- Undercity tunnels provide back entrance to this hall
- Branded player can repair Guardian without surface access
- Creates dramatic tension: outcast performing heroic act

**Asha Mercy Mechanism:**
When branded player repairs the Guardian:
- Council member Asha may secretly support the player
- Depending on prior relationship with Asha, she may provide Town Seal despite branding
- This is the "redemption valve" for dark path players
- Not guaranteed - requires some positive history with Asha

**Traits:** "shattered stone limbs", "faded inscription of purpose", "sense of patient waiting", "ancient protective runes"

#### The Undercity
Secret criminal network beneath the town. Functions as alternative economy for branded players or those preferring dark paths.

**Contacts:**
- **Fence:** Buys stolen/questionable items, sells equipment unavailable on surface
- **Information Broker:** Sells secrets about NPCs and locations, gossip timing information
- **Shadow (Assassin):** Offers contract services for eliminating NPCs

**Access:**
- Requires reputation with Delvan (if rescued) or payment to Information Broker
- Or through undercity discovery while exploring

**The Shadow - Assassination System:**
- Contracts available for council members and some other NPCs
- **3-turn delay** from payment to completion (irreversible once paid)
- **20% discovery chance** per contract (triggers branding if discovered)
- Echo knows instantly regardless of discovery
- Trust penalty: **-2 per assassination** (cumulative with Echo)
- **Permanently locks Triumphant ending** (even if undiscovered)

**Strategic Value of Undercity:**
- Provides all essential services (useful especially if branded)
- Tunnel to Broken Statue Hall allows Guardian repair while branded
- Some information only available here
- Alternative path to Town Seal if hero status impossible

**Consequences:** Using undercity services may be discovered, affecting surface reputation. Assassinations create permanent locks.

**Traits:** "dim lantern light", "whispered negotiations", "dangerous competence", "moral flexibility"

### Companion Restrictions (Civilized Remnants)
- **Wolves**: Cannot enter surface town (guards refuse) but can access through undercity tunnels
- **Salamander**: Can enter (no environmental conflict)
- **Human companions**: Full access, can provide cover for some activities

### Persistent Effects
- Town reputation affects all NPC interactions; reputation -5 triggers branding
- Council decisions change available services and town safety
- Repaired Guardian provides settlement defense and grants Town Seal fragment
- Undercity reputation tracks separately, can conflict with surface reputation
- Assassinations permanently lock Triumphant ending and un-branding recovery
- Elara's fate affects advanced herbalism availability for rest of game

---

## Cross-Region Mechanics

### The Commitment System

The commitment system is the game's core mechanic. When players promise to help NPCs, Echo tracks these commitments and reacts to outcomes.

**Commitment Flow:**
1. Player encounters NPC in distress (Aldric, Sira, Garrett, Delvan, bear cubs)
2. Player can promise to help (creates commitment) or decline (no penalty for declining)
3. Once committed, timer starts
4. Timer may include "hope bonus" if player takes positive actions
5. If fulfilled: Echo trust +0.5, NPC trust gained, possible rewards
6. If abandoned: Echo trust -1 (or -0.5 with partial credit), consequences vary by NPC

**Partial Credit:**
When a commitment fails, the system checks for evidence of genuine effort:
- Region visited (required for any partial credit)
- Relevant item acquired (strong evidence)
- In transit at expiration (strong evidence)
- Competing commitment fulfilled (moderate evidence)
- Mathematically impossible given timer overlap (automatic partial credit)

Effects of partial credit:
- Trust penalty reduced from -1 to -0.5
- Echo reaction softened
- No permanent relationship damage

**Commitment Timer Summary:**
| NPC | Timer | Hope Bonus | Cross-Region Conflict |
|-----|-------|------------|----------------------|
| Aldric | 50-60 turns | Yes | Rarely conflicts with anything |
| Sira | 8 turns | +4 | Designed trap for overcommitted players |
| Bear cubs | 30-35 turns | No | Manageable with planning |
| Garrett | 5 turns | No | Conflicts with Delvan (same region) |
| Delvan | 10-13 turns | No | Conflicts with Garrett (same region) |

**Design Intent:**
- Most cross-region timer conflicts are resolvable with reasonable planning
- Sira's 8-turn timer is the intentional trap
- Sunken District dual-rescue is designed to be impossible on first playthrough
- The system rewards trying even when some failures occur
- Four fulfilled commitments (+2.0) can offset two abandonments (-1.5 with partial credit)

### Gossip Timing System

Information spreads between NPCs at specific rates. This creates confession windows and discovery mechanics.

| Information | Source | Destination | Turns | Notes |
|-------------|--------|-------------|-------|-------|
| Sira's fate | Beast Wilds | Elara | 12 | Travelers mention injured hunter |
| Sira abandonment | Beast Wilds | Elara | 20 | Only if Sira survives AND tells others |
| Aldric's fate | Fungal Depths | Civilized Remnants | 25 | Scholar's fate spreads slowly |
| Delvan's fate | Sunken District | Undercity | 7 | Criminal networks communicate quickly |
| Assassination | Civilized Remnants | Echo | 0 | Instant - Echo always knows |
| Assassination discovery | Civilized Remnants | Councilors | 0-5 | 20% discovery chance per contract |
| Spore Mother healed | Fungal Depths | All regions | 15 | Major event spreads fast |
| Bear cubs fate | Beast Wilds | Sira | 8 | Sira notices nearby |
| Garrett fate | Sunken District | Camp NPCs | 0 | Same location - immediate |

**Confession vs Discovery:**
- Confession before gossip arrives: Reduced trust penalty, recovery possible
- Discovery via gossip: Larger trust penalty, often permanent consequences
- Turn counts are from the event, not game start

### Environmental Spreads

**Spore Spread** (if Spore Mother not healed):
- Turn 50: Beast Wilds affected
- Turn 100: Town gate checks become suspicious
- Turn 150: Town NPCs become infected
- Halted by: Healing Spore Mother with heartmoss

**Cold Spread** (if Observatory telescope not repaired):
- Turn 75: Beast Wilds high ground becomes cold
- Turn 125: Nexus boundary becomes cold
- Turn 175: Sunken District water freezes
- Halted by: Repairing telescope

Both spreads halted by: Completing waystone repair (endgame)

### Companion System

**Available Companions:**
- Wolf pack (from Beast Wilds)
- Steam salamander (from Frozen Reaches)
- Human NPCs: Sira, Garrett, Aldric (if saved and recruited)

**Automatic Waiting:**
When companions cannot enter a region, they automatically wait at boundaries:
- Wolves: Wait just outside restricted area, rejoin immediately when player exits
- Salamander: Returns to Nexus if entering water region, waits at region entry otherwise
- Human companions: Wait at nearest safe location (camp, town)

**Companion Restrictions Summary:**
| Companion | Nexus | Fungal | Beast Wilds | Sunken | Frozen | Town |
|-----------|-------|--------|-------------|--------|--------|------|
| Wolves | No (wards) | Limited | Yes (home) | No (water) | No (cold) | Undercity only |
| Salamander | Yes | Yes | Yes | No (water) | Yes (best) | Yes |
| Sira | Yes | Needs mask | Yes | Needs training | Needs cloak | Yes |

**Multi-Companion Interactions:**
| Combination | Initial State | Resolution |
|-------------|---------------|------------|
| Wolf + Sira | Hostile (prejudice) | Reconciliation dialog required |
| Wolf + Salamander | Mutual wariness | Coexist after 3 turns together |
| Salamander + Human | Comfortable | No issues |
| Wolf + Aldric | Neutral | Aldric nervous but accepting |

**Companion Death:**
- Companions can die protecting player (sacrifice mechanic)
- Companions can die from player forcing them into hazards
- Death is permanent - companions don't respawn
- Echo comments on companion deaths, especially senseless ones

---

## Ending System

The game has seven possible endings, determined by Echo trust level at waystone completion.

### Ending Tier Matrix

| Echo Trust | Waystone Complete | Ending Name | Echo State |
|------------|-------------------|-------------|------------|
| 5+ | Yes | **Triumphant** | Fully transformed, becomes permanent companion |
| 3-4 | Yes | **Successful** | Transformed, grateful |
| 0-2 | Yes | **Bittersweet** | Transformed, distant |
| -1 to -2 | Yes | **Hollow Victory** | Transformed but silent |
| -3 to -5 | Yes | **Pyrrhic** | Present but won't transform |
| -6 or below | Yes | **Pyrrhic** | Refuses to participate in ceremony |
| Any | No | **Abandoned** | Remains spectral forever |

### Ending Requirements

**Triumphant (trust 5+):**
- Requires consistent positive play
- Never assassinated anyone (even undiscovered assassinations lock this ending)
- Fulfilled most commitments
- Saved major NPCs

**Successful/Bittersweet (trust 0-4):**
- Mixed play - some failures balanced by successes
- The "normal" range for first playthroughs

**Hollow Victory/Pyrrhic (trust -1 to -6):**
- Heavy failures or dark path choices
- Game still completable, but Echo relationship damaged
- At trust -6, Echo refuses to manifest at all

**Abandoned:**
- Player never completes waystone repair
- Echo remains spectral forever
- This is a valid ending for players who explore but don't finish

### Permanent Locks

Some actions permanently lock content, regardless of later behavior:

| Lock | Trigger | Effect |
|------|---------|--------|
| Triumphant ending | ANY assassination (even undiscovered) | Best ending impossible |
| Advanced herbalism | Elara killed | Skill permanently unavailable |
| Hero status | Assassination discovery | Surface town hero path blocked |
| Some council quests | Branding | Certain quests unavailable |
| Wolf companion | Wolves killed | Pack unavailable |
| Salamander companion | Salamander killed | Cold immunity unavailable |

### Trust Recovery

Even at low trust, recovery is possible through sustained effort:

| Deed | Trust Restored |
|------|----------------|
| Save major NPC (Aldric, Sira, Garrett, Delvan) | +1 |
| Heal Spore Mother | +1 |
| Restore crystal | +1 |
| Fulfill commitment | +0.5 |
| Place waystone fragment | +0.5 |

**Limits:**
- Maximum +1 per Nexus visit (prevents grinding)
- Actions must be genuine (can't save same NPC twice)
- Recovery from -6 to usable trust requires multiple major deeds

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
7. (Commitment created when seeing sick cubs - timer 30-35 turns)
8. Retrieve healing herbs from Civilized Remnants
9. Return and heal cubs before timer expires
10. Dire Bear becomes grateful, entire Beast Wilds becomes safe
11. Echo trust +0.5 for fulfilled commitment, +potential for saving cubs

### First Playthrough Sunken District (Realistic)
This sequence shows the "impossible dual rescue" in action:
1. Learn swimming from Old Swimmer Jek (few turns)
2. Acquire air bladder from dock
3. Dive to Drowning Sailor Cave - find Garrett (timer: 5 turns starts NOW)
4. Promise to save Garrett (commitment created)
5. Give air bladder, cure exhaustion, guide to surface (uses ~4 turns)
6. Garrett saved! (+1 Echo trust)
7. Continue exploring, find Merchant's Wreck - find Delvan
8. Delvan already dead (timer expired while saving Garrett)
9. Echo notes both the save AND the loss on next Nexus visit
10. Partial credit applies - player was genuinely engaged elsewhere

### Commitment Cascade (Overcommitted Player)
This shows Sira's trap timer in action:
1. Visit Fungal Depths, promise to help Aldric (timer: 50-60 turns)
2. Visit Beast Wilds, find sick cubs, promise to help (timer: 30-35 turns)
3. Continue exploring, find injured Sira, promise to help (timer: 8 turns!)
4. Sira's tight timer conflicts with travel time for cubs' herbs
5. Player chooses to prioritize Sira (nearest, tightest timer)
6. Sira saved (+1 Echo trust)
7. Return to cubs - still alive (timer not expired)
8. Get herbs from town, return, save cubs (+0.5 Echo trust)
9. Check on Aldric - still alive (generous timer)
10. Cure Aldric (+1 Echo trust)
11. Net result: All three saved despite tight overlap

### Temple Challenge Approach
1. Search Keeper's Quarters for temple research
2. Find partial password
3. Travel to Temple Sanctum
4. Attempt password (partial, golems hesitate but still fight)
5. Use pillars for cover, survive initial assault
6. Find control crystal location hint in temple inscriptions
7. Retrieve control crystal from Ice Caves (requires salamander for cold protection)
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

1. **Actor Flags System** ✅ RESOLVED
   - `state.set_actor_flag()` and `state.get_actor_flag()` built into core
   - Documented in [Advanced Topics](../user_docs/authoring_manual/11_advanced.md#111-actor-flags)

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
- Commitment system (timer tracking, Echo commentary, partial credit evaluation)
- Gossip propagation (information spread between regions)
- Companion auto-waiting and boundary management
- Environmental effect processors (spores, cold, drowning)
- Environmental spread progression (spore/cold if not remediated)
- Domestication/feeding mechanics
- NPC service provision
- Confession/discovery dialog management
- Ending determination (Echo trust evaluation at waystone completion)
- Time-based progression

---

## Next Steps

1. Detailed design of commitment system mechanics
2. Detailed design of companion boundary and multi-companion interaction system
3. Create detailed room-by-room specifications with JSON structures
4. Define all actors with complete property sets including commitment timers
5. Design gossip propagation system
6. Design confession/discovery dialog trees
7. Design ending ceremony variations
8. Create test scenarios for each commitment overlap pattern
9. Iterative implementation and testing by region

---

## Related Documents

- [infrastructure_spec.md](infrastructure_spec.md) - **Infrastructure specification**: schemas and APIs for game-wide systems
- [game_wide_rules.md](game_wide_rules.md) - Cross-cutting rules from walkthrough testing
- [cross_region_walkthrough_A_commitment_cascade.md](cross_region_walkthrough_A_commitment_cascade.md) - Timer overlap testing
- [cross_region_walkthrough_B_companion_journey.md](cross_region_walkthrough_B_companion_journey.md) - Companion restriction testing
- [cross_region_walkthrough_C_dark_path.md](cross_region_walkthrough_C_dark_path.md) - Assassination/branding testing
- [walkthrough_guide.md](walkthrough_guide.md) - Status of all regional and cross-region walkthroughs
