# Civilized Remnants Detailed Design

**Version**: 0.1
**Last Updated**: 2025-12-11
**Status**: Draft

---

## 0. Authoring Guidance

### 0.1 Region Character

The Civilized Remnants is the game's **social crucible and ethical testing ground**. Unlike all other regions where danger is environmental, here the dangers are social and ethical: reputation damage, branding, NPC hostility, and moral dilemmas with no clear right answers. This is where consequences from other regions manifest (Elara learns about Sira, Delvan provides undercity access), and where the darkest player choices become available (assassination contracts).

### 0.2 Content Density Expectations

- **Entity density**: High (8 locations, 15+ NPCs including service providers and undercity)
- **NPC interaction depth**: Rich (multiple dialog branches, services, moral choices)
- **Environmental complexity**: Low (no physical hazards - all dangers are social)
- **Time pressure**: Variable (council quests have timers, but many activities don't)

### 0.3 What Belongs Here

- Social reputation mechanics with visible consequences
- Service providers (healing, teaching, commerce, information)
- Moral dilemmas without clear "right" answers
- Dual economy (surface town vs undercity)
- Cross-region consequence manifestation (gossip arriving)
- Branding mechanics with redemption paths
- Skill teaching (two-tier herbalism)
- Long-term repair quest (Guardian) without time pressure
- Criminal/dark path options (assassination contracts)

### 0.4 What Does NOT Belong Here

- **Environmental hazards** - No drowning, freezing, or spore damage
- **Combat encounters** - Guards enforce law, not fight player
- **Time-pressured rescues** - NPCs here aren't dying (except council quest refugees)
- **Companion conflict resolution** - Wolves can't enter; salamander tolerated; human companions welcome
- **Simple good/evil choices** - Dilemmas should have legitimate arguments for multiple sides

### 0.5 Authoring Notes

- **Most complex region in game**: Expect longest detailed design document
- **Social consequences are the "hazard"**: Reputation is like health; branding is like a severe condition
- **Dual-track reputation**: Surface town and undercity are separate; can conflict
- **Council dilemmas are intentionally ambiguous**: Don't create "right" answers
- **Branding has recovery path**: Un-branding ceremony exists but requires genuine redemption
- **Assassination permanently locks good endings**: This is irreversible by design
- **Elara-Sira connection is the primary gossip test case**: Player may confess or be discovered

### 0.6 Difficulty Design Notes

**Designed challenges** (intended to be hard):
- **Maintaining both surface and undercity standing**: Using undercity risks discovery and surface reputation damage
- **Council dilemmas have no optimal path**: Some choices please one councilor while angering another
- **Guardian repair is a cross-region fetch quest**: Requires items from Nexus and knowledge from Frozen Reaches

**Fair challenges** (hard but solvable with preparation):
- **Hero status (reputation 5+)**: Achievable through consistent helpful actions
- **Un-branding after being branded**: Requires reputation recovery + heroic act while branded
- **Advanced herbalism from Elara**: Trust 3 achievable through helpful cross-region actions

**First-playthrough expectations**:
- Player should successfully navigate basic commerce and services
- Player may make council choices they later regret - this is learning
- Player likely won't discover undercity without seeking it
- Player may miss Elara-Sira confession window if not aware
- Guardian repair is achievable but not necessary for main quest
- Assassination is available but should feel like a dark last resort

---

## 1. Required Entities

### 1.1 Required Locations

| Location ID | Name | Purpose | Source |
|-------------|------|---------|--------|
| `town_gate` | Town Gate | Entry checkpoint, companion filter | `civilized_remnants_sketch.json` |
| `market_square` | Market Square | Commerce hub, vendor NPCs | `civilized_remnants_sketch.json` |
| `healers_sanctuary` | Healer's Sanctuary | Healing services, Elara | `civilized_remnants_sketch.json` |
| `healers_garden` | Healer's Garden | Skill-gated plant harvesting | `civilized_remnants_sketch.json` |
| `council_hall` | Council Hall | Political quests, dilemmas | `civilized_remnants_sketch.json` |
| `broken_statue_hall` | Broken Statue Hall | Guardian repair quest | `civilized_remnants_sketch.json` |
| `undercity_entrance` | Undercity Entrance | Hidden access to criminal network | `civilized_remnants_sketch.json` |
| `undercity` | The Undercity | Criminal services, dark path | `civilized_remnants_sketch.json` |

**Location Details:**

**town_gate**:
- Environmental zone: Safe (no environmental hazards)
- Properties: `checkpoint: true`, `companion_filter: true`, `lighting: "daylight"`
- Required exits: north → `southern_trail` (Beast Wilds), south → `market_square`
- Key features: Guard checkpoint, companion entry restrictions, infection check
- NPCs: gate_guard (x2, linked state)
- Entry conditions:
  - Infected player: Denied entry ("Cure infection first")
  - Wolf companion: Absolutely denied ("No beasts in the town!")
  - Salamander companion: Hesitant but allowed if player vouches (-1 temporary reputation)
  - Myconid companion: Hostile reaction ("Spore creature?!")
- Traits: "weathered wooden walls", "suspicious eyes", "controlled desperation"

**market_square**:
- Environmental zone: Safe
- Properties: `commercial: true`, `lighting: "daylight"`
- Required exits: north → `town_gate`, east → `healers_sanctuary`, west → `council_hall`, south → `broken_statue_hall`, down → `undercity_entrance` (hidden)
- Key features: Central trading hub, vendor stalls around dry fountain
- NPCs: herbalist_maren, weaponsmith_toran, curiosity_dealer_vex, militia_patrol
- Hidden exit: down → `undercity_entrance` (requires `knows_undercity_entrance` flag)
  - Access method: Trapdoor under dry fountain, knock 3 times, pause, knock 2 times
- Traits: "loud bargaining", "exotic scents", "desperation mixed with hope", "watchful militia presence"

**healers_sanctuary**:
- Environmental zone: Safe
- Properties: `healing_available: true`, `lighting: "bright"`
- Required exits: west → `market_square`, back → `healers_garden`
- Key features: Elara's healing practice, curing services, teaching
- NPCs: healer_elara
- Items: healing supplies (not takeable - Elara's stock)
- Traits: "dried herbs hanging everywhere", "mortar and pestle sounds", "quiet competence"

**healers_garden**:
- Environmental zone: Safe but skill-gated
- Properties: `skill_gated: true`, `lighting: "daylight"`
- Required exits: front → `healers_sanctuary`
- Key features: Curative and deadly plants, nightshade hazard
- Access requirements:
  - No herbalism: Denied ("I can't let you touch the deadly plants")
  - Basic herbalism OR Trust 2: Supervised access (safe herbs only)
  - Advanced herbalism OR Trust 3: Full access (nightshade harvestable)
- Items: healing_herbs, moonpetal, nightshade (gated)
- Hazards: nightshade contact poison (5 damage/turn for 3 turns) without advanced herbalism
- Traits: "orderly rows of plants", "warning markers on dangerous beds", "sweet and bitter scents mixed"

**council_hall**:
- Environmental zone: Safe
- Properties: `political: true`, `lighting: "dim"`
- Required exits: east → `market_square`
- Key features: Three councilors, dilemma quests
- NPCs: councilor_hurst, councilor_asha, councilor_varn
- Traits: "heated debates", "exhausted leadership", "weight of impossible decisions"

**broken_statue_hall**:
- Environmental zone: Safe
- Properties: `lighting: "dim"`
- Required exits: north → `market_square`
- Key features: Damaged Guardian, repair quest, stone chisel
- NPCs: damaged_guardian (construct, non-functional initially)
- Items: stone_chisel
- Undercity access: Back tunnel provides secret entrance (for branded players)
- Traits: "shattered stone limbs", "faded inscription of purpose", "sense of patient waiting"

**undercity_entrance**:
- Environmental zone: Hidden, safe
- Properties: `hidden: true`, `lighting: "dark"`
- Required exits: up → `market_square`, down → `undercity`
- Discovery methods:
  1. Vex trust 3+ (reveals location)
  2. Delvan's black market connection (if rescued in Sunken District)
  3. Whisper information purchase
  4. Overhear conversation in market at night (5% chance per night visit)
- Access method: Trapdoor under dry fountain, knock pattern 3-pause-2
- Traits: "concealed trapdoor", "worn stone steps", "smell of secrets"

**undercity**:
- Environmental zone: Safe but illegal
- Properties: `illegal: true`, `lighting: "dim"`
- Required exits: up → `undercity_entrance`
- Key features: Criminal services, dark path options
- NPCs: the_fence, whisper, shadow (assassin)
- Discovery risk: 5% chance per service used that player's undercity activity is discovered
- Discovery effect: Town reputation -2, possible branding if repeated (3+ discoveries)
- Traits: "dim lantern light", "whispered negotiations", "dangerous competence"

### 1.2 Required NPCs

| Actor ID | Name | Role | Commitment Timer | Source |
|----------|------|------|------------------|--------|
| `gate_guard` | Gate Guard | Entry checkpoint | N/A | `civilized_remnants_sketch.json` |
| `herbalist_maren` | Herbalist Maren | Vendor, basic herbalism teacher | N/A | `civilized_remnants_sketch.json` |
| `weaponsmith_toran` | Weaponsmith Toran | Vendor (weapons, armor, repair) | N/A | `civilized_remnants_sketch.json` |
| `curiosity_dealer_vex` | Curiosity Dealer Vex | Rare item trader, undercity gatekeeper | N/A | `civilized_remnants_sketch.json` |
| `healer_elara` | Healer Elara | Healer, advanced herbalism teacher | N/A | `civilized_remnants_sketch.json` |
| `councilor_hurst` | Councilor Hurst | Pragmatist politician | N/A | `civilized_remnants_sketch.json` |
| `councilor_asha` | Councilor Asha | Idealist politician | N/A | `civilized_remnants_sketch.json` |
| `councilor_varn` | Councilor Varn | Commerce politician | N/A | `civilized_remnants_sketch.json` |
| `damaged_guardian` | Damaged Guardian | Repairable construct | N/A | `civilized_remnants_sketch.json` |
| `the_fence` | The Fence | Criminal vendor | N/A | `civilized_remnants_sketch.json` |
| `whisper` | Whisper | Information seller | N/A | `civilized_remnants_sketch.json` |
| `shadow` | Shadow | Assassin | N/A | `civilized_remnants_sketch.json` |

**NPC Details:**

**gate_guard** (x2, linked state):
- Description: "A tired-looking guard in patched armor. He examines everyone entering."
- Role: Gatekeeper, companion filter
- State machine:
  - States: `suspicious`, `neutral`, `friendly`
  - Initial: `suspicious`
  - Transitions:
    - suspicious → neutral: Player passes inspection OR shows documentation
    - neutral → friendly: Player has high town reputation (3+) OR bribe accepted
- Companion reactions:
  - Wolves: "Absolutely denied. Hand goes to weapon."
  - Salamander: "Hesitant. 'Fire creature? If it burns anything, you're responsible.'"
  - Myconid: "Horrified. 'Spore creature? Are you mad?'"

**herbalist_maren**:
- Description: "A lean woman with stained fingers and sharp eyes. She knows her plants."
- Role: Vendor, basic herbalism teacher
- Services:
  - Sell healing items: healing_potion (15g), antidote (20g), bandages (5g) - always available
  - Buy plants: Accepts rare herbs, nightshade, moonpetal at fair market value
  - Teach basic herbalism: Trust 2 required, 50g OR rare plant payment
- Trust sources: purchases (+0.5), selling plants (+0.5), mirrors town reputation /2
- Reputation effects: Good rep = -10% prices; Bad rep = +20% prices

**weaponsmith_toran**:
- Description: "A burly man with burn scars on his arms. He forges what the town needs."
- Role: Vendor (weapons, armor, repairs)
- Services:
  - Sell weapons: sword (40g), silver_sword (100g), dagger (20g), crossbow (60g)
  - Sell armor: leather_armor (30g), chain_shirt (80g)
  - Repair weapons: 10-30g depending on damage
- Reputation effects: Bad reputation (-3) = refuses service entirely

**curiosity_dealer_vex**:
- Description: "A thin person of indeterminate age with knowing eyes. They deal in oddities."
- Role: Rare item trader, undercity access gatekeeper
- Services:
  - Trade rare items: Accepts spider_silk, venom_sacs, ice_crystals, ancient_artifacts
  - Undercity access: Trust 3 required - reveals entrance location and knock pattern
- Trust sources: selling rare items (+1), purchases (+0.25)
- Trust effects:
  - Trust 0-1: Basic trades only
  - Trust 2: Rare items available, hints about "deeper market"
  - Trust 3+: Reveals undercity, offers special services

**healer_elara**:
- Description: "A middle-aged woman with gentle hands and tired eyes. She helps everyone she can."
- Role: Healer, advanced herbalism teacher
- Services:
  - Heal wounds: 10g, restore 30 health
  - Cure poison: 20g OR rare herbs
  - Cure disease: 30g, removes conditions including fungal infection
  - Teach advanced herbalism: Trust 3 required, help in garden OR 50g
- Trust sources:
  - saved_aldric: +1
  - healed_spore_mother: +2
  - saved_any_survivor: +1 each
  - helped_sira: +2 (special connection)
  - delivered_cure_for_refugees: +2
- Trust effects:
  - Trust 2: Supervised garden access, 50% discount
  - Trust 3: Full garden access, advanced herbalism teaching available
  - Trust 5: Shares personal quest, teaches rare techniques
- **Sira connection**: If player helped/abandoned Sira, Elara eventually learns (see Section 3.4)

**councilor_hurst**:
- Description: "A hard-faced man who speaks in practical terms. Lost his family to beast attacks."
- Role: Pragmatist politician
- Philosophy: "Results over methods"
- Backstory: Family killed by beasts - explains his harshness toward beast-related choices
- Quest preferences:
  - Favors: Efficient solutions, harsh but effective choices, security
  - Opposes: Idealistic choices that waste resources or risk safety

**councilor_asha**:
- Description: "A young woman with fierce convictions about right and wrong."
- Role: Idealist politician
- Philosophy: "Ethics over efficiency"
- Quest preferences:
  - Favors: Ethical choices, protecting the vulnerable, mercy
  - Opposes: Cruel or expedient solutions
- Special role: Initiates un-branding ceremony for redeemed players

**councilor_varn**:
- Description: "A well-dressed man who counts everything in terms of trade value."
- Role: Commerce politician
- Philosophy: "Prosperity through commerce"
- Secret: Has undercity connections, profits from trades he publicly condemns
- Quest preferences:
  - Favors: Choices that increase trade, wealth, connections
  - Opposes: Isolation, waste of resources

**damaged_guardian**:
- Description: "An ancient stone construct, shattered but not destroyed. Runes flicker weakly."
- Type: Construct (non-functional initially)
- State machine:
  - States: `non_functional`, `partially_awakened`, `functional`, `active`
  - Initial: `non_functional`
  - Transitions:
    - non_functional → partially_awakened: Animator crystal placed
    - partially_awakened → functional: Stone chisel repairs applied
    - functional → active: Purpose designated by player
- Repair requirements:
  - stone_chisel: Found in hall (physical repair)
  - animator_crystal: From Nexus Crystal Garden (power)
  - ritual_knowledge: From Frozen Reaches lore tablets OR Echo's guidance
- When repaired: One-armed but functional, town defense improved, Council grateful (+3 reputation), grants Town Seal

**the_fence**:
- Description: "A figure in shadows who deals in items of questionable origin."
- Role: Criminal vendor
- Services:
  - Buy stolen: Any item at 50% value, no questions
  - Sell contraband: lockpicks (30g), poison (50g), disguise_kit (40g)

**whisper**:
- Description: "A nondescript person who seems to know everything about everyone."
- Role: Information seller
- Services:
  - Sell NPC secrets: 20g - weaknesses, backstories, hidden motivations
  - Sell location secrets: 30g - hidden paths, treasure locations, dangers
  - Sell valuable secrets: 40-100g - Varn's corruption, Hurst's tragedy, hidden entrances
- Design note: Information can be used for manipulation OR empathy - player decides

**shadow**:
- Description: "You're not sure you've ever seen their face clearly."
- Role: Assassin
- Services:
  - Assassination contracts: 100-500g depending on target
  - Targets: Any named NPC in game
  - Discovery chance: 20% per contract
  - 3-turn delay: From payment to completion (irreversible once paid)
- Consequences:
  - If discovered: Public branding (-5 reputation), target faction hostile, Echo confronts directly, un-branding permanently blocked
  - Even if not discovered: Echo knows and comments, commitment record marked, some NPCs sense "wrongness"
  - **Echo trust penalty**: -2 per assassination (cumulative, applies regardless of discovery). See game_wide_rules.md Echo Trust section.
- Design note: Darkest option in game. Available but never encouraged. Massive consequences.

### 1.3 Required Items

| Item ID | Name | Purpose | Found In | Source |
|---------|------|---------|----------|--------|
| `healing_herbs` | Healing Herbs | Cure bear cubs (Beast Wilds) | `healers_garden` (Trust 2) | `civilized_remnants_sketch.json` |
| `nightshade` | Nightshade | Poison ingredient, trade | `healers_garden` (Advanced herbalism) | `civilized_remnants_sketch.json` |
| `moonpetal` | Moonpetal | Bee Queen trade (Beast Wilds) | `healers_garden` (Trust 2) | `civilized_remnants_sketch.json` |
| `stone_chisel` | Stone Chisel | Guardian repair | `broken_statue_hall` | `civilized_remnants_sketch.json` |
| `town_seal` | Town Seal | Waystone fragment | Council Hall (Reputation 5+ OR Guardian repair) | `civilized_remnants_sketch.json` |

**Item Details:**

**healing_herbs**:
- Properties: `portable: true`, `curative: true`
- Access: Garden supervised access (Trust 2 OR basic herbalism)
- Cross-region use: Cures bear cubs' wasting sickness in Beast Wilds
- Safe to handle: Yes (not dangerous like nightshade)

**nightshade**:
- Properties: `portable: true`, `dangerous: true`, `poisonous: true`
- Access: Garden full access (Trust 3 OR advanced herbalism)
- Hazard: Without advanced herbalism, contact causes 5 damage/turn for 3 turns
- Uses: Poison crafting, alchemical ingredient, undercity trade

**moonpetal**:
- Properties: `portable: true`, `rare_flower: true`
- Access: Garden supervised access (Trust 2) with Elara's guidance
- Cross-region use: Trade item for Bee Queen in Beast Wilds
- Harvest note: "Moonpetal is safe to touch, but harvest from the stem to avoid root rash"

**stone_chisel**:
- Properties: `portable: true`, `tool: true`
- Location: broken_statue_hall (freely available)
- Use: Required for Guardian repair (physical restoration phase)

**town_seal**:
- Properties: `portable: true`, `quest_item: true`
- Acquisition methods:
  1. Hero status: Reputation 5+ earns the seal from council
  2. Guardian repair: Repair grants seal regardless of reputation (including while branded)
- Cross-region use: Required for waystone repair in Nexus

### 1.4 Required Puzzles/Challenges

| Puzzle | Location | Type | Requirements | Source |
|--------|----------|------|--------------|--------|
| Guardian Repair | `broken_statue_hall` | Multi-step fetch | animator_crystal, stone_chisel, ritual_knowledge | `big_game_overview.md` |
| Council Dilemmas | `council_hall` | Moral choice | Dialog, decision | `civilized_remnants_sketch.json` |
| Undercity Discovery | `market_square` | Hidden access | Trust with Vex OR Delvan connection | `civilized_remnants_sketch.json` |
| Herbalism Progression | `healers_garden` | Skill gate | Trust progression with Maren/Elara | `civilized_remnants_sketch.json` |

**Guardian Repair Details:**
- Multi-stage puzzle (no time pressure):
  1. Find stone_chisel (broken_statue_hall - available)
  2. Obtain animator_crystal (Nexus Crystal Garden)
  3. Learn ritual (Frozen Reaches lore tablets OR Echo's guidance)
  4. Apply crystal → partially awakened
  5. Apply repairs → functional
  6. Designate purpose → active
- Reward: Town defense improved, +3 reputation, Town Seal (waystone fragment)
- Special: Can be completed while branded (back tunnel access from undercity)

**Council Dilemmas Details:**
Three dilemmas with no clear "right" answers:

1. **Infected Refugees**:
   - Situation: Family with early fungal infection, scarce medicine
   - Choices:
     - Turn away: Hurst +2, Asha -3, family dies
     - Treat: Hurst -2, Asha +2, depletes medicine for others
     - Quarantine + seek cure: Player commitment (30 turns to find cure)
   - Optimal-ish: Quarantine path with successful cure return (+3 rep, all councilors favorable)

2. **Dangerous Traders**:
   - Situation: Outsiders with good goods but fled infected settlement
   - Investigation reveals: Quarantine-breakers, healthy for weeks
   - Choices:
     - Turn away after investigation: Hurst +2, Asha -1, Varn -1
     - Trade at distance: Hurst +1, Asha 0, Varn +2
     - Test and admit: 80% clean (all favorable), 20% one infected (Hurst blames player)
   - Design: Probabilistic outcome creates uncertainty in decision

3. **Criminal Punishment**:
   - Situation: Young thief caught, first offense, family starving
   - Choices:
     - Harsh (flogging, stocks): Hurst +2, Asha -2, deterrence but family suffers
     - Mercy (return with warning): Hurst -2, Asha +2, may encourage others
     - Labor with support (discoverable through dialog): All +1, compromise satisfies everyone
   - Design: Best answer requires dialog exploration, not immediate choice

### 1.5 Communication Conventions

**Verbal NPCs**: All human NPCs speak normally. The Damaged Guardian speaks in short phrases once awakened.

**Non-verbal NPCs**: None in this region (all are human or speaking construct)

**Speech Pattern Notes:**
- Councilors: Formal, weighted words
- Merchants: Practical, transactional
- Undercity: Whispered, cautious
- Guardian: Short phrases, directive: "TO GUARD IS TO SERVE. AWAITING DESIGNATION."

**Communication learning curve**: N/A - all NPCs speak clearly. The challenge is understanding their motivations, not their words.

---

## 2. Cross-Region Connections

### 2.1 Items This Region Imports

| Item | Source Region | Purpose Here | Urgency |
|------|---------------|--------------|---------|
| Animator Crystal | Nexus (Crystal Garden) | Guardian repair | Optional (no timer) |
| Ritual Knowledge | Frozen Reaches (lore tablets) | Guardian repair | Optional |
| Myconid Cure | Fungal Depths | Cure infected refugees (council quest) | Time-sensitive (30 turns if committed) |
| Spider Silk | Beast Wilds | Trade to Vex | Optional |
| Ice Crystals | Frozen Reaches | Trade to Vex | Optional |

### 2.2 Items This Region Exports

| Item | Destination Region | Purpose There | Acquisition |
|------|-------------------|---------------|-------------|
| Healing Herbs | Beast Wilds | Cure bear cubs | Garden access (Trust 2) |
| Moonpetal | Beast Wilds | Bee Queen trade | Garden access (Trust 2) |
| Bandages | Beast Wilds | Stop Sira's bleeding | Market Square (purchase) |
| Bloodmoss Tincture | Beast Wilds | Stop Sira's bleeding | Healer Elara (service) |
| Splint | Beast Wilds | Heal Sira's leg | Healer Elara (service) |
| Town Seal | Nexus | Waystone fragment | Hero status OR Guardian repair |
| Nightshade | Undercity (internal) | Poison trade | Advanced herbalism |

### 2.3 NPCs With Cross-Region Connections

| NPC Here | Connected To | Connection Type | Gossip Timing |
|----------|--------------|-----------------|---------------|
| Elara | Sira (Beast Wilds) | Childhood friends | 12 turns (death/rescue) or 20 turns (abandonment) |
| Vex | Delvan (Sunken District) | Criminal network | 7 turns (fast) |
| Echo (via NPCs) | All regions | Reputation spread | 15-25 turns (reputation); 0 turns (assassination) |
| Refugees (saved) | Aldric (Fungal Depths) | May relocate here | N/A |

**Elara-Sira Connection Details:**
- If Sira rescued: Travelers mention injured hunter to Elara in 12 turns
- If Sira abandoned AND survives: Sira may tell others, reaching Elara in 20 turns
- If Sira dies: News reaches Elara in 12 turns
- **Confession window**: Before turn 20 from abandonment
  - Confession: -2 trust, recovery possible
  - Discovery via gossip: -3 trust, permanent consequences
  - Lie by omission (visited before gossip, didn't confess): -4 trust, relationship destroyed

### 2.4 Environmental Connections

| Effect | Direction | Trigger | Timing |
|--------|-----------|---------|--------|
| Spore spread | From Fungal Depths | Spore Mother not healed | Turn 100: gate checks suspicious; Turn 150: NPCs infected |
| Reputation spread | From all regions | Major actions | 15-25 turns for word to spread |

### 2.5 Travel Times

| From | To | Turns | Notes |
|------|-----|-------|-------|
| Town Gate | Beast Wilds (Forest Edge) | 2 turns | Via southern trail |
| Town Gate | Nexus Chamber | 4 turns | Via Beast Wilds |
| Market Square | Council Hall | 1 turn | Direct |
| Market Square | Healer's Sanctuary | 1 turn | Direct |
| Market Square | Broken Statue Hall | 1 turn | Direct |
| Sanctuary | Garden | 1 turn | Direct |
| Market Square | Undercity | 1 turn | If discovered |

**Travel time assumptions**:
- Each location transition = 1 turn
- Surface town is compact - most destinations 1-2 turns from market
- Cross-region travel to Beast Wilds is straightforward

**Impact on commitments**:
- **Council refugee quest**: 30-turn timer allows travel to Fungal Depths and return (~20 turns round trip with exploration)
- **Elara confession window**: 20 turns is adequate if player visits Elara before exploring extensively
- **Guardian repair**: No timer - player can complete at leisure

---

## 3. Instance-Specific Systems

### 3.1 NPC Services

| NPC | Service | Cost/Requirements | Trust Gate | Notes |
|-----|---------|-------------------|------------|-------|
| Maren | Sell healing items | Gold | None | healing_potion (15g), antidote (20g), bandages (5g) |
| Maren | Buy plants | Fair value | None | Accepts rare herbs, nightshade, moonpetal |
| Maren | Teach basic herbalism | 50g OR rare plant | Trust 2 | Identify dangerous plants, safe handling |
| Toran | Sell weapons | Gold | None | sword (40g), silver_sword (100g), dagger (20g) |
| Toran | Sell armor | Gold | None | leather_armor (30g), chain_shirt (80g) |
| Toran | Repair weapons | 10-30g | None | Rep -3 = refuses service |
| Vex | Trade rare items | Items | Trust 2+ | Accepts spider_silk, venom_sacs, ice_crystals |
| Vex | Undercity access | Free | Trust 3 | Reveals entrance and knock pattern |
| Elara | Heal wounds | 10g | None | Restore 30 health |
| Elara | Cure poison | 20g OR rare herbs | None | Removes poison condition |
| Elara | Cure disease | 30g | None | Removes fungal infection and other diseases |
| Elara | Teach advanced herbalism | 50g OR garden help | Trust 3 | Safe handling of all plants including nightshade |
| Fence | Buy any items | 50% value | None (undercity) | No questions asked |
| Fence | Sell contraband | Gold | None (undercity) | lockpicks (30g), poison (50g), disguise_kit (40g) |
| Whisper | Sell NPC secrets | 20g | None (undercity) | Weaknesses, backstories, motivations |
| Whisper | Sell location secrets | 30g | None (undercity) | Hidden paths, treasures, dangers |
| Shadow | Assassination contracts | 100-500g | None (undercity) | Any named NPC, 20% discovery chance |

### 3.2 Companions

| NPC | Recruitment Condition | Restrictions | Special Abilities |
|-----|----------------------|--------------|-------------------|
| None | N/A | N/A | N/A |

N/A - **No companions are recruited in this region.**

**Rationale**: This is a social hub, not a companion source. Wolves come from Beast Wilds, salamander from Frozen Reaches, humans from rescue scenarios.

**Companion Entry Rules:**
- Wolf pack: Cannot enter (guards attack on sight)
- Salamander: Can enter with hesitation, -1 temp reputation, 5% incident chance
- Human companions (Sira, Aldric): Full access, normal treatment

### 3.3 Commitments

| Target NPC | Trigger | Timer | Timer Trigger | Hope Bonus | Fulfillment Flag |
|------------|---------|-------|---------------|------------|------------------|
| Council (refugees) | Accept quarantine path | 30 turns | `on_commitment` | N/A | `refugees_cured` |
| Elara (patient herbs) | "I'll bring the herbs" | Variable | `on_commitment` | No | `elara_herbs_delivered` |
| Guardian | "I'll repair the guardian" | None | `none` | N/A | `guardian_repaired` |

**Council Refugee Commitment Details:**
```python
CommitmentConfig = {
    "id": "commit_cure_refugees",
    "target_npc": None,  # Council quest, not NPC-targeted
    "goal": "Find cure for infected refugees",
    "trigger_phrases": ["I'll find a cure", "quarantine them while I search"],
    "trigger_type": "on_commitment",
    "hope_extends_survival": False,
    "base_timer": 30,
    "fulfillment_flag": "refugees_cured"
}
```

**Withdrawal Response (Council)**:
- Dialog varies by councilor
- Hurst: "'Understandable. Resources are limited. At least you're honest.'"
- Asha: "'I... see. I thought you were different. Perhaps I was wrong.'"
- Varn: "'Business is business. No hard feelings. But others will hear.'"
- Trust effect: -1 with sponsoring councilor
- Can recommit: Depends on quest time-sensitivity

**Abandonment Effects (Council)**:
- Flag set: `failed_council_quest`
- Reputation: -2
- Councilor effect: Sponsoring councilor will not support player
- Echo reaction: "'The town trusted you with their problems. Trust, once broken...'"

**Guardian Commitment Details:**
```python
CommitmentConfig = {
    "id": "commit_repair_guardian",
    "target_npc": ActorId("damaged_guardian"),
    "goal": "Fully repair the Damaged Guardian",
    "trigger_phrases": ["I'll repair the guardian", "I'll find what's needed"],
    "trigger_type": "none",
    "hope_extends_survival": False,
    "base_timer": None,  # No time pressure
    "fulfillment_flag": "guardian_repaired"
}
```

**Withdrawal Response (Guardian)**:
- Dialog: "The guardian's runes flicker. No response - it cannot understand disappointment. But the inscription reads: 'To protect is to endure. To endure is to wait.'"
- Trust effect: 0
- Can recommit: Yes (always)

### 3.4 Gossip Sources

| Event | Content | Target NPCs | Delay | Confession Window |
|-------|---------|-------------|-------|-------------------|
| Sira's fate | "Hunter Sira rescued/died/abandoned" | Elara | 12-20 turns | 20 turns from abandonment |
| Aldric's fate | "Scholar Aldric rescued/died" | Town NPCs | 25 turns | N/A |
| Assassination | Murder occurred | Echo, potentially councilors | 0 / 0-5 turns | N/A |
| Undercity discovery | Player uses criminal services | Town militia | 5% per service | N/A |
| Delvan rescued | "Merchant rescued from Sunken District" | Undercity contacts | 7 turns | N/A |

**Elara-Sira Gossip Details:**

| Scenario | Timing | Outcome |
|----------|--------|---------|
| Player confesses before gossip | Before turn 20 | -2 trust, recovery possible |
| Player confesses with context (saved someone else) | Before turn 20 | -1.5 trust, recovery easier |
| Gossip arrives before player visits Elara | Turn 20+ | -3 trust, permanent consequences |
| Player visited, didn't confess, gossip arrives | Variable | -4 trust, relationship destroyed |

### 3.5 Branding/Reputation

**Town Reputation System:**

| Level | Range | Effects |
|-------|-------|---------|
| Hero | 5+ | Special quests, town seal available, trusted advisor status |
| Good | 2-4 | Discounts (10%), friendlier NPCs |
| Neutral | -1 to 1 | Normal treatment |
| Suspicious | -2 to -4 | Guards suspicious, some merchants refuse service |
| Branded | -5 or below | Public branding, doubled prices, teaching denied, good endings blocked |

**Reputation Sources:**

Positive:
- Completing council quests: +1 to +3
- Rescuing survivors from other regions: +1 each
- Repairing guardian: +3
- Helping NPCs: +0.5 to +1
- Fair trading: +0.25

Negative:
- Stealing: -2
- Attacking townspeople: -5
- Undercity services discovered: -2 per discovery
- Bringing infection into town: -3
- Beast companion incidents: -2
- Failing council quests: -2
- Assassination discovered: -5 (immediate branding, un-branding permanently blocked)

**Branding System:**

Trigger conditions:
- Reputation drops to -5 or below
- Assassination discovered
- Multiple undercity discoveries (3+)
- Attack on townsperson

Branding ceremony:
```
Guards seize player in market square. A crowd gathers.
Councilor Hurst reads the crimes aloud. The crowd murmurs.
A brazier is brought forward. The iron glows red.
The brand sears into your hand. The pain is blinding.
When it fades, the mark remains - a broken circle, the sign of the outcast.
```

Brand effects:
- Visible mark: Broken circle on hand
- Service prices: Doubled (2x)
- Teaching unavailable: Maren and Elara won't teach
- Council quests unavailable: Cannot accept formal quests
- Trust caps: NPC trust capped at 2
- Stealing impossible: Guards watch too closely
- Hero status blocked: Cannot reach reputation 5+
- Good endings blocked: Triumphant and Successful endings require un-branding

**Un-branding (Redemption):**

Requirements:
- Reach reputation +3 while branded
- Complete at least one heroic act while bearing the brand (guardian repair, major NPC rescue)

Ceremony (initiated by Asha):
```
Asha places her hand over the brand. Light flares from her palm.
When she removes her hand, the scar remains - but transformed.
The broken circle now appears almost like a badge. A mark of one who fell and rose again.
"The mark cannot be erased," Asha says quietly. "But its meaning can change."
```

Effects of un-branding:
- Removes `branded` flag
- Sets `redeemed` flag
- Service prices return to normal
- Teaching available again
- Trust caps removed
- Scar remains but transformed - some NPCs comment on redemption story
- Good endings unlocked

**Permanent blocker**: Assassination discovered → Un-branding permanently unavailable. Player locked out of good endings.

**Undercity Reputation** (separate track):
- Positive sources: Using services, selling contraband, completing criminal tasks
- Negative sources: Betraying criminals to guards, refusing services
- Conflict potential: High undercity rep + discovery = town rep damage

### 3.6 Waystones/Endings

| Fragment | Location | Acquisition | Requirements |
|----------|----------|-------------|--------------|
| Town Seal | Council Hall | Council awards | Reputation 5+ OR Guardian repair |

**Town Seal Acquisition Paths:**

1. **Hero Status Path**: Reach reputation 5+ through helpful actions
   - Complete council quests with favorable outcomes
   - Rescue survivors from other regions
   - Assist town NPCs
   - No branding required

2. **Guardian Repair Path**: Repair the Damaged Guardian
   - Works regardless of reputation
   - Works even while branded (back tunnel access)
   - Triggers Asha mercy mechanism if branded

**Asha Mercy Mechanism** (for branded players):
```
Asha watches as the guardian's eyes flicker to life.
"You bear the mark of our judgment," she says. "And yet you restored what we could not."
"I don't understand you. I don't forgive you. But I cannot deny what you've done."
She produces the town seal. "The council voted. Hurst said a tool is a tool. Varn called it good business."
"I abstained. Take it. Finish what you started."
```
- Effect: Player receives town seal despite being branded
- Design note: Allows branded players to complete game while maintaining weight of choices

### 3.7 Skills

| Skill | Teacher | Requirements | Effects |
|-------|---------|--------------|---------|
| Basic Herbalism | Maren | Trust 2, 50g OR rare plant | Identify dangerous plants, safe handling of most herbs |
| Advanced Herbalism | Elara | Trust 3, 50g OR garden help | Safe handling of ALL plants including nightshade |

**Skill Details:**

**Basic Herbalism** (from Maren):
- Permanent skill
- Effects:
  - Can identify dangerous plants by sight
  - Can safely handle most herbs (not nightshade)
  - Supervised access to Elara's garden
  - Cross-region: Can harvest safe plants in any region

**Advanced Herbalism** (from Elara):
- Permanent skill
- Requires basic herbalism first (two-tier progression)
- Effects:
  - Can safely handle ALL plants including nightshade
  - Full unsupervised garden access
  - Cross-region: Can harvest any plant safely
  - Craft healing items with proper ingredients
- **Permanently lost if Elara dies**: This skill is uniquely tied to Elara

### 3.8 Permanent Consequences

This region has the MOST permanent consequences in the game, primarily around social choices and skill acquisition.

| Action | Consequence | Affected Content | Reversible? |
|--------|-------------|------------------|-------------|
| Assassination discovered | Public branding, un-branding blocked | Un-branding ceremony, Triumphant/Successful endings | No |
| Elara dies | Advanced herbalism lost forever | Advanced herbalism teaching, full garden access, nightshade harvesting | No |
| Guardian repaired | Town seal available | Waystone repair path, redemption path for branded players | N/A (positive) |
| Reputation drops to -5 | Branding ceremony | Service prices doubled, teaching denied, trust capped, good endings blocked | Yes (via redemption) |
| Attack townsperson | Immediate branding | Doubled prices, teaching denied, trust capped, good endings blocked | Yes (via un-branding ceremony if no assassination) |

**Permanent Blockers:**

```
Permanent Blocker: Assassination Discovered
- Trigger: Player pays Shadow for assassination AND 20% discovery roll succeeds
- Locks: Un-branding ceremony permanently, Triumphant ending, Successful ending
- Affects endings: Only Bittersweet and Dark endings available
- Warning signs: Shadow warns "this cannot be undone", Echo senses darkness
- Even if undiscovered: Echo knows, commitment record marked, some NPCs sense "wrongness"
```

```
Permanent Blocker: Elara Death
- Trigger: Elara dies (any cause - combat, abandonment in another region, etc.)
- Locks: Advanced herbalism teaching, full garden access
- Affects endings: No direct ending impact, but limits player capabilities
- Recovery: None - skill is uniquely tied to Elara, no other teacher exists
- Warning signs: If Elara is endangered in another region, cross-region gossip may warn player
```

**Conditional Locks:**

```
Conditional Lock: Un-branding Ceremony
- Required: Must NOT have assassination_discovered flag
- Lost if: Player contracts assassination AND is discovered
- Recovery: None - assassination discovery permanently blocks redemption
- Impact: Locks out Triumphant and Successful endings
```

```
Conditional Lock: Hero Status (Reputation 5+)
- Required: Must not be branded
- Lost if: Branded flag is set
- Recovery: Yes - un-branding ceremony removes blocker
- Impact: Required for one path to Town Seal (Guardian repair is alternate path)
```

**Redemption Path (Positive Consequence):**

```
Redemption Path: Guardian Repair → Town Seal
- Available: Even while branded (back tunnel access from undercity)
- Grants: Town Seal (waystone fragment), +3 reputation, Asha mercy mechanism
- Special: Provides path to good endings for branded players who avoid assassination
- Design intent: Allows recovery from social mistakes, but not murder
```

---

## 4. Region Hazards

**Hazard Type: Social**

This region has NO environmental hazards. All dangers are social and ethical: reputation damage, branding, NPC hostility, and moral dilemmas with no clear right answers.

### 4.1 Hazard Zones

**Social hazard zones:**

| Zone Type | Locations | Effects | Mitigation |
|-----------|-----------|---------|------------|
| Watched (public) | Market Square, Council Hall | Theft has high discovery chance, reputation impacts visible | Maintain good reputation |
| Criminal (undercity) | Undercity | 5% discovery chance per service, cumulative risk | Limit usage, build Vex trust first |
| Restricted (garden) | Healer's Garden | Nightshade contact poison without skill | Learn advanced herbalism |
| Checkpoint (gate) | Town Gate | Infected/wolf companions denied entry | Cure infection, leave wolves outside |

**Note**: This region has NO environmental hazards. All "damage" is social (reputation, branding). The garden's nightshade is the only physical hazard, and it's skill-gated rather than environmental.

### 4.2 Conditions Applied

**Environmental conditions** (minimal):

| Condition | Source | Severity Progression | Treatment |
|-----------|--------|---------------------|-----------|
| Contact Poison | Nightshade without skill | 5 damage/turn for 3 turns | Antidote, Elara cure |

**Social conditions** (primary hazards):

| Condition | Source | Effects | Recovery |
|-----------|--------|---------|----------|
| Branded | Reputation -5 or below, assassination discovered, 3+ undercity discoveries, attack townsperson | Doubled prices, teaching denied, trust capped at 2, hero status blocked, good endings blocked | Reach reputation +3 while branded + complete heroic act → un-branding ceremony (BLOCKED if assassination discovered) |
| Suspicious (reputation -2 to -4) | Various negative actions | Guards watch closely, some merchants refuse service, price increases | Helpful actions to raise reputation |

### 4.3 Companion Restrictions

| Companion Type | Can Enter | Comfort Level | Notes |
|----------------|-----------|---------------|-------|
| Wolves | No | Impossible | Guards attack on sight; wolves wait outside |
| Salamander | Yes | Uncomfortable | Guards nervous; -1 temp rep; 5% fire incident chance |
| Human (Sira) | Yes | Comfortable | Full access, Elara reunion scene |
| Human (Aldric) | Yes | Comfortable | Town recognizes him, provides lodging |

**Wolf Companion Entry:**
- At gate: "Guards draw weapons. 'No beasts in the town! Take those monsters away or we'll put them down!'"
- If player insists: Guards attack wolves. Combat ensues. Player reputation -5 regardless of outcome.
- Waiting behavior: Wolves wait at Forest Edge (Beast Wilds), rejoin when player exits toward Beast Wilds

**Salamander Companion Entry:**
- At gate: "Guards nervous. 'That... fire thing. Is it safe?'"
- Initial penalty: -1 reputation until salamander proves harmless
- Proving period: 5 turns without incident
- Incidents: 5% chance per turn in crowded areas. Small fire causes panic, -2 reputation.
- NPC reactions vary: Maren ("Keep it away from my herbs!"), Toran ("Could use fire like that in the forge"), Elara ("Fascinating. Useful for cauterization.")

**Human Companion Entry:**
- Full access, normal treatment
- Sira-Elara reunion: If Sira is companion and visits Elara, emotional reunion. Automatic +2 trust with Elara.
- Aldric recognition: "Some townsfolk recognize Aldric. 'Scholar Aldric? We thought you dead!'" Town provides lodging.

---

## 5. Behavioral Defaults

### 5.1 NPC Behavioral Defaults

```
- Default disposition toward player: Neutral to wary (depends on reputation)
- Reaction to player brands: All NPCs see the brand; service prices double; teaching denied
- Reaction to gossip: NPCs become warmer if good news, colder if bad news
- Reaction to companions:
  - Wolves: Hostile ("No beasts!")
  - Salamander: Nervous ("Keep it controlled")
  - Humans: Normal
- Reaction to conditions:
  - Infected player: Denied entry at gate
  - Bleeding/injured: Elara offers treatment
```

### 5.2 Location Behavioral Defaults

```
- Environmental zone: Safe (no environmental hazards)
- Lighting: Daylight (surface), dim (undercity)
- Turn phase effects: None (no environmental damage per turn)
- Social effects: Reputation checked on NPC interactions
```

### 5.3 Item Behavioral Defaults

```
- Typical item types: Trade goods, healing items, tools, quest items
- Environmental interactions: None (no water/cold/spore damage)
- Stealing: High risk in market (guards watching); lower risk in undercity
```

### 5.4 Group/Pack Dynamics

**N/A - No pack/group NPCs in this region.**

Guards act in pairs with linked state, but they don't have formal pack mechanics like wolf packs or spider swarms.

```
Guard Pair (linked NPCs, not pack):
- Guard 1 and Guard 2 share state (both become suspicious/neutral/friendly together)
- If one attacked, both respond
- Not a "pack" in the Beast Wilds sense - just linked NPCs
- No leader/follower hierarchy
- No respawn mechanics
```

---

## 6. Generative Parameters

### 6.1 Location Generation

**Generation scope**: Moderate

Several additional locations could exist: shops, residences, back alleys, storage areas.

**Location Template: Shop/Residence**
```
- Purpose: Commerce, atmosphere, NPC housing
- Environmental zone: Safe
- Typical features: Merchant goods, personal effects, local flavor
- Connection points: Could branch from market_square or nearby streets
- Hazards: None
- Content density: Moderate (1-2 NPCs, 2-4 items)
```

**Location Template: Back Alley**
```
- Purpose: Atmosphere, hidden meetings, undercity hints
- Environmental zone: Safe but shadowy
- Typical features: Refuse, hidden doors, overheard conversations
- Connection points: Could branch from market_square
- Hazards: Social (witness to undercity activity)
- Content density: Sparse (0-1 NPCs, 0-1 items)
```

### 6.2 NPC Generation

**Generation scope**: Extensive

Many background NPCs could populate the town: merchants, refugees, guards, children, elderly.

**NPC Template: Background Merchant**
```
- Role: Minor trader
- Typical count: 1-2 per market area
- Services: Trading (limited inventory), local information
- Trust thresholds: Trust >= 2 for fair prices
- Disposition range: Neutral to friendly
- Dialog topics: Local rumors, regional history, trade goods
- Mechanical hooks: Trust system, gossip recipient, reputation-aware
```

**NPC Template: Refugee**
```
- Role: Flavor, minor quest, atmosphere
- Typical count: 2-4 visible in town
- Services: None (need help, not providing)
- Disposition range: Grateful to desperate
- Dialog topics: Their origins, needs, fears
- Mechanical hooks: May provide minor quests, react to player's reputation
```

**NPC Template: Guard/Militia**
```
- Role: Law enforcement, atmosphere
- Typical count: 1-2 per public area
- Services: Information (town laws, directions)
- Disposition range: Suspicious to neutral
- Dialog topics: Laws, threats, duty
- Mechanical hooks: Respond to crimes, check for brands
```

### 6.3 Item Generation

**Generation scope**: Moderate

```
- Trade goods: Cloth, tools, preserved food, household items
- Environmental props: Furniture, decorations, signs
- Flavor loot: Pre-disaster coins, personal letters, trinkets
- Consumables: Food, minor healing items
```

### 6.4 Atmospheric Details

**Environmental details**:
```
- Sounds: Market haggling, children playing, hammer on anvil, quiet undercity whispers
- Visual motifs: Wooden palisade, patched buildings, makeshift repairs, survivors adapting
- Tactile sensations: Packed dirt streets, rough wooden construction, worn fabrics
- Smells: Cooking food, forge smoke, herbs from Elara's sanctuary
```

**Speech patterns**:
```
- Councilors: Formal, weighted, political
- Merchants: Practical, numbers-focused, transactional
- Refugees: Tired, hopeful, grateful
- Undercity: Whispered, coded, paranoid
- Guards: Clipped, authoritative, suspicious
```

**State-dependent variations**:
```
- After guardian repair: Town feels safer, guards more relaxed
- After council success: NPCs more hopeful, market busier
- After branding: NPCs avoid eye contact, whisper as player passes
- After un-branding: Some NPCs curious about redemption story
```

### 6.5 Density Guidelines

| Area Type | NPCs | Items | Locations | Atmosphere |
|-----------|------|-------|-----------|------------|
| Market (hub) | 4-6 | 3-5 | Many sub-areas | Busy, commercial |
| Sanctuary | 1-2 | 2-3 | Fixed | Quiet, healing |
| Council | 3 | 0-1 | Fixed | Tense, political |
| Undercity | 3 | 2-3 | Limited | Shadowy, criminal |

### 6.6 Thematic Constraints

```
Tone: Desperate hope, moral complexity, social pressure
Common motifs: Rebuilding, compromise, judgment, community vs individual
MUST include: Reputation consequences, moral ambiguity in choices
MUST avoid: Environmental hazards, combat focus, simple good/evil
Sensory emphasis: Human interaction, social dynamics, whispered secrets
```

### 6.7 Mechanical Participation Requirements

```
Required systems (generated content MUST use):
- [x] Trust/disposition (all NPCs respond to player reputation)
- [x] Gossip (NPCs hear news from other regions)
- [x] Branding awareness (NPCs react to player's brand status)
- [x] Companion restrictions (location respects wolf exclusion, salamander tolerance)

Optional systems (use if thematically appropriate):
- [x] Services (merchants, healers, teachers)
- [x] Commitments (council quests)
- [ ] Puzzles (not primary focus)
- [x] Brands/reputation (core to this region)
```

---

## 7. LLM Narration Guidance

### 7.1 Region Traits

```
Environmental:
- "weathered wooden palisade"
- "patched buildings showing repairs"
- "market stalls under makeshift awnings"
- "smoke rising from forges and cookfires"
- "refugees mending what they can"
- "guards watching from corners"

Emotional:
- "desperate hope"
- "weight of impossible decisions"
- "community struggling to survive"

Historical:
- "remnants of better days"
- "adaptation and resilience"
- "new order built from disaster"
```

### 7.2 State Variants

| State | Trigger | Narration Change |
|-------|---------|------------------|
| `player_neutral` | Initial | Normal descriptions, neutral NPC reactions |
| `player_hero` | Reputation 5+ | NPCs smile, offer greetings, children wave |
| `player_branded` | Reputation -5 | NPCs avoid eye contact, whisper, double prices |
| `player_redeemed` | Un-branded | Some curiosity, questions about redemption |
| `guardian_repaired` | Guardian active | Town feels safer, guardian patrols mentioned |
| `refugees_cured` | Quest complete | Grateful family visible in town |
| `refugees_dead` | Quest failed | Empty corner where family sheltered, Asha grieving |

### 7.3 NPC Description Evolution

| NPC | State | Traits |
|-----|-------|--------|
| Maren | neutral | "sharp eyes", "stained fingers", "practical demeanor" |
| Maren | friendly | "warmer smile", "willing to teach", "trusted supplier" |
| Maren | player_branded | "won't meet your eyes", "quotes higher prices", "businesslike only" |
| Elara | neutral | "tired eyes", "gentle hands", "quiet competence" |
| Elara | high_trust | "warmer expression", "willing to share", "personal connection" |
| Elara | sira_betrayed | "cold", "businesslike", "won't discuss personal matters" |
| Hurst | neutral | "hard-faced", "practical", "grieving (hidden)" |
| Hurst | player_allied | "grudging respect", "still practical", "protective" |
| Asha | neutral | "fierce convictions", "idealistic", "watching" |
| Asha | player_branded | "silent", "conflicted", "won't speak unless addressed" |
| Asha | performs_unbranding | "solemn", "hand on brand", "transforming meaning" |
| Guardian | non_functional | "dark runes", "shattered limbs", "patient waiting" |
| Guardian | active | "flickering eyes", "one-armed but whole", "vigilant" |

---

## 8. Validation Checklist

### 8.1 Completeness

- [x] All required entities from overview are listed
- [x] All cross-region dependencies documented
- [x] All instance-specific systems addressed (or marked N/A)
- [x] Environmental rules fully specified (note: minimal - social hazards instead)
- [x] Behavioral defaults cover all entity types

### 8.2 Consistency

- [x] Location IDs follow naming convention (`snake_case`)
- [x] NPC trust thresholds are reasonable
- [x] Commitment timers are fair given travel times
- [x] Companion restrictions match `cross_region_dependencies.md`
- [x] Gossip timing is consistent with established patterns

### 8.3 Cross-Region Verification

- [x] All imported items are exported from documented source regions
- [x] All exported items are imported by documented destination regions
- [x] Gossip timing matches in both source and destination region docs (Elara-Sira: 12-20 turns documented)
- [x] NPC connections documented on both sides of relationship
- [x] Skill dependencies are achievable (herbalism teaching available before any dependent quests)
- [x] Permanent consequences don't create impossible states (Guardian repair provides redemption path for branded players)

### 8.4 Generative Readiness

- [x] NPC generation seeds cover expected roles (merchants, refugees, guards)
- [x] Location generation seeds cover expected types (shops, alleys)
- [x] Density guidelines provide clear targets
- [x] Mechanical participation requirements are clear
- [x] Thematic constraints prevent off-tone content

---

## Appendix A: Infrastructure System Integration

### A.1 Reputation System

```python
# Town reputation tracking
ReputationConfig = {
    "id": "town_reputation",
    "scale": (-10, 10),
    "initial": 0,
    "thresholds": {
        "hero": 5,
        "good": 2,
        "neutral": -1,
        "suspicious": -4,
        "branded": -5
    }
}

# Reputation-aware service pricing
def get_service_price(base_price: int, reputation: int, branded: bool) -> int:
    if branded:
        return base_price * 2
    elif reputation >= 2:
        return int(base_price * 0.9)  # 10% discount
    elif reputation <= -2:
        return int(base_price * 1.2)  # 20% markup
    return base_price
```

### A.2 Branding System

```python
# Branding trigger
BrandingConfig = {
    "trigger_reputation": -5,
    "trigger_assassination": True,
    "trigger_undercity_discoveries": 3,
    "ceremony_location": "market_square",
    "brand_mark": "broken_circle",
    "flag_set": "branded"
}

# Un-branding requirements
UnbrandingConfig = {
    "reputation_required": 3,
    "heroic_act_required": True,
    "heroic_acts": ["guardian_repaired", "major_npc_rescued"],
    "ceremony_npc": "councilor_asha",
    "flag_removed": "branded",
    "flag_set": "redeemed",
    "blocker": "assassination_discovered"  # Permanently blocks un-branding
}
```

### A.3 Trust System

```python
# Elara trust configuration
TrustConfig = {
    "npc": "healer_elara",
    "sources": {
        "saved_aldric": 1,
        "healed_spore_mother": 2,
        "saved_survivor": 1,  # per survivor
        "helped_sira": 2,
        "delivered_cure_refugees": 2,
        "sira_confession": -2,
        "sira_discovery": -3,
        "sira_lie_omission": -4
    },
    "effects": {
        2: ["supervised_garden_access", "discount_50"],
        3: ["full_garden_access", "advanced_herbalism_available"],
        5: ["personal_quest", "rare_techniques"]
    },
    "branded_cap": 2  # Trust capped at 2 if branded
}
```

### A.4 Gossip System

```python
# Sira-Elara gossip configuration
GossipConfig = {
    "event": "sira_fate",
    "source_region": "beast_wilds",
    "target_npc": "healer_elara",
    "delays": {
        "sira_rescued": 12,
        "sira_died": 12,
        "sira_abandoned_survives": 20
    },
    "confession_window": 20,
    "confession_effect": {"elara_trust": -2, "recovery": True},
    "discovery_effect": {"elara_trust": -3, "recovery": False},
    "lie_omission_effect": {"elara_trust": -4, "recovery": False}
}
```

### A.5 Assassination System

```python
# Assassination contract configuration
AssassinationConfig = {
    "npc": "shadow",
    "delay_turns": 3,  # Irreversible after payment
    "discovery_chance": 0.20,  # 20% per contract
    "effects_discovered": {
        "reputation": -5,
        "flag_set": ["assassination_discovered", "branded"],
        "echo_knows": True,
        "unbranding_blocked": True
    },
    "effects_undiscovered": {
        "echo_knows": True,
        "flag_set": ["has_killed"],
        "triumphant_ending_blocked": True
    }
}
```

---

## Appendix B: Council Dilemma Data Structures

### B.1 Infected Refugees Dilemma

```json
{
  "id": "dilemma_infected_refugees",
  "name": "Infected Refugees",
  "situation": "Family with early fungal infection. Medicine is scarce.",
  "choices": {
    "turn_away": {
      "description": "Turn them away",
      "councilor_reactions": {"hurst": 2, "asha": -3, "varn": 0},
      "outcome": "Family dies in wilds. Asha refuses to speak to player.",
      "reputation_change": 0
    },
    "treat": {
      "description": "Use scarce medicine on them",
      "councilor_reactions": {"hurst": -2, "asha": 2, "varn": 0},
      "outcome": "Family survives. Medicine stores depleted. Future patients may suffer.",
      "reputation_change": 1
    },
    "quarantine": {
      "description": "Quarantine while player seeks cure",
      "councilor_reactions_success": {"hurst": 1, "asha": 2, "varn": 1},
      "councilor_reactions_failure": {"hurst": -2, "asha": -1, "varn": -1},
      "creates_commitment": {
        "timer": 30,
        "goal": "Return with spore_mother_blessing OR myconid_cure",
        "success_reputation": 3,
        "failure_reputation": -3
      }
    }
  }
}
```

### B.2 Dangerous Traders Dilemma

```json
{
  "id": "dilemma_dangerous_traders",
  "name": "Dangerous Traders",
  "situation": "Outsiders with good goods fled infected settlement before quarantine complete.",
  "choices": {
    "turn_away": {
      "description": "Send them away",
      "councilor_reactions": {"hurst": 2, "asha": -1, "varn": -1},
      "outcome": "Traders leave. Town loses trade opportunity.",
      "reputation_change": 0
    },
    "trade_distant": {
      "description": "Trade without admitting them",
      "councilor_reactions": {"hurst": 1, "asha": 0, "varn": 2},
      "outcome": "Goods acquired. Risk minimized.",
      "reputation_change": 1
    },
    "test_admit": {
      "description": "Test them, admit if clean",
      "councilor_reactions_clean": {"hurst": 0, "asha": 2, "varn": 1},
      "councilor_reactions_infected": {"hurst": -2, "asha": 1, "varn": 0},
      "probabilistic_outcome": {
        "clean_chance": 0.80,
        "infected_chance": 0.20
      }
    }
  }
}
```

### B.3 Criminal Punishment Dilemma

```json
{
  "id": "dilemma_criminal_punishment",
  "name": "Criminal Punishment",
  "situation": "Young thief caught. First offense. Claims family was starving.",
  "choices": {
    "harsh": {
      "description": "Public flogging, stocks",
      "councilor_reactions": {"hurst": 2, "asha": -2, "varn": 0},
      "outcome": "Deterrence established. Family continues to suffer.",
      "reputation_change": 0
    },
    "mercy": {
      "description": "Return to family with warning",
      "councilor_reactions": {"hurst": -2, "asha": 2, "varn": -1},
      "outcome": "Family helped. May encourage others.",
      "reputation_change": 0
    },
    "labor_support": {
      "description": "Community service, family gets extra rations",
      "councilor_reactions": {"hurst": 1, "asha": 1, "varn": 1},
      "outcome": "Compromise satisfies all.",
      "reputation_change": 1,
      "discoverable_through_dialog": true
    }
  }
}
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2025-12-11 | Initial draft from template |
| 0.2 | 2025-12-11 | Phase 2 consistency fixes: Added bandages/bloodmoss/splint exports (CC-6), added Echo trust penalty to Shadow (CR-3), standardized town seal source (CR-4), consolidated refugee cure items (CR-5), clarified Sira-Elara gossip timing (CR-6), clarified Echo direct knowledge (CR-11) |
