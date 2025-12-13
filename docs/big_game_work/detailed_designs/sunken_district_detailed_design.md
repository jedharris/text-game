# Sunken District Detailed Design

**Version**: 0.2
**Last Updated**: 2025-12-11
**Status**: Draft

---

## 0. Authoring Guidance

### 0.1 Region Character

The Sunken District is the game's **isolation crucible and impossible choice**. It's designed to strip away all companions and force the player to face rescue challenges alone. The dual-rescue scenario (Garrett + Delvan) is intentionally impossible on first playthrough - this is the most explicit designed trap in the game, teaching that some failures are unavoidable and creating replay value.

### 0.2 Content Density Expectations

- **Entity density**: Moderate (8 locations, 7 NPCs including hazard fish)
- **NPC interaction depth**: Moderate (survivor camp NPCs + rescue targets)
- **Environmental complexity**: High (water levels, breath tracking, swimming skill gates)
- **Time pressure**: Extreme (Garrett 5 turns, Delvan 10-13 turns, overlapping)

### 0.3 What Belongs Here

- Underwater navigation challenges
- Breath management mechanics
- Rescue scenarios with tight timers
- Swimming skill progression (two tiers)
- Environmental hazards (drowning, cold water, predatory fish)
- Solo challenges (all companions excluded)
- Survivor community with morale tracking
- Knowledge quest for Archivist (non-timed alternative content)

### 0.4 What Does NOT Belong Here

- **Combat encounters** - Fish are hazards, not combat enemies; no XP or loot
- **Companion assistance** - Beast companions (wolves, salamander) permanently excluded; human companions excluded unless they learn swimming skill
- **Easy dual-rescue** - First playthrough should NOT allow saving both
- **Service transactions in crisis** - Rescue targets can't offer services while dying
- **Extended NPC dialog trees** - Timer pressure discourages chatting

### 0.5 Authoring Notes

- **Dual-rescue is designed to fail on first playthrough**: This is intentional. Don't create workarounds.
- **Fish are obstacles, not enemies**: They exist to make traversal costly, not to provide combat content.
- **Companion exclusion is systematic**: Wolves can't swim, salamander extinguishes, humans can't traverse underwater without training. Don't create exceptions.
- **Garrett's timer starts on room entry, not commitment**: Physics doesn't wait for promises.
- **Delvan's hope bonus extends survival, not deadline**: Determination slows blood loss.
- **Swimming skill is permanent**: Once learned, applies everywhere in the game.

### 0.6 Difficulty Design Notes

**Designed challenges** (intended to be hard or impossible):
- **Dual rescue is intentionally impossible on first playthrough**: Total minimum turns for both rescues is ~15; Garrett dies in 5 turns from encounter, Delvan in 10-13. Even optimal play can't save both without foreknowledge.
- **Solo challenge is deliberate**: All companion types excluded to ensure player faces challenges alone.
- **Tidal passage requires swimming skill**: Without basic swimming, passage is extremely dangerous.

**Fair challenges** (hard but solvable with preparation):
- **Either rescue individually**: Both Garrett and Delvan can be saved individually with reasonable efficiency.
- **Deep Archive access**: Requires advanced swimming OR Archivist's bubble - either path is achievable.
- **Knowledge quest**: Non-timed, rewards thorough exploration without pressure.

**First-playthrough expectations**:
- Player should save one of Garrett or Delvan, not both
- Player may fail to save either if they explore too much before committing
- Knowledge quest provides achievable content if rescues fail
- Swimming skill acquisition is straightforward
- The lesson: "You can't save everyone" is the intended takeaway

---

## 1. Required Entities

### 1.1 Required Locations

| Location ID | Name | Purpose | Source |
|-------------|------|---------|--------|
| `flooded_plaza` | Flooded Plaza | Entry point, survivor camp access | `sunken_district_sketch.json` |
| `survivor_camp` | Survivor Camp | Safe zone, NPC services, quest hub | `sunken_district_sketch.json` |
| `flooded_chambers` | Flooded Chambers | Guildhall, first fish encounter | `sunken_district_sketch.json` |
| `tidal_passage` | Tidal Passage | Skill gate to sea caves | `sunken_district_sketch.json` |
| `sea_caves` | Sea Caves | Garrett rescue location | `sunken_district_sketch.json` |
| `merchant_quarter` | Merchant Quarter | Deep water route to Delvan | `sunken_district_sketch.json` |
| `merchant_warehouse` | Merchant Warehouse | Delvan rescue location | `sunken_district_sketch.json` |
| `deep_archive` | Deep Archive | Archivist, water pearl, knowledge quest | `sunken_district_sketch.json` |

**Location Details:**

**flooded_plaza**:
- Environmental zone: Mixed water (ankle to waist)
- Properties: `water_level: "ankle_to_waist"`, `breathable: true`, `lighting: "dim"`
- Required exits: west → `nexus_chamber`, northwest → `survivor_camp`, east → `flooded_chambers`, south → `merchant_quarter`, down → `deep_archive` (hidden, requires advanced swimming or bubble)
- Key features: Entry point from Nexus, colored ribbons marking safe paths, waterproof_sack item
- Traits: "debris floating in murky water", "colored ribbons marking safe paths", "smell of brine and decay"

**survivor_camp**:
- Environmental zone: Dry (elevated ground)
- Properties: `water_level: "dry"`, `breathable: true`, `safe_zone: true`, `lighting: "firelit"`
- Required exits: southeast → `flooded_plaza`
- Key features: Safe rest area, teaching services, quest NPCs, morale tracking
- NPCs: Camp Leader Mira, Old Swimmer Jek, Child Survivor
- Items: air_bladder, basic_supplies
- Traits: "crude map scratched on flat stone", "smell of smoke and damp clothes", "survivors mending nets and gear"

**flooded_chambers**:
- Environmental zone: Chest-deep water
- Properties: `water_level: "chest"`, `breathable: true`, `lighting: "dim"`
- Required exits: west → `flooded_plaza`, east → `tidal_passage`
- Key features: First fish sighting (they watch but don't attack in shallows), guild records fragment
- NPCs: predatory_fish (hazard, not combat)
- Traits: "pillars like drowning fingers", "water-stained ceiling showing flood heights", "shadows moving between columns"

**tidal_passage**:
- Environmental zone: Fully submerged
- Properties: `water_level: "submerged"`, `breathable: false`, `lighting: "dark"`
- Required exits: west → `flooded_chambers`, east → `sea_caves`
- Key features: Skill gate (swimming required), fish attack during crossing, 20-foot underwater passage
- Skill requirements:
  - No swimming: High drowning risk, fish attack likely, severe damage
  - Basic swimming: Passable but slow (2 turns), fish attack once
  - Advanced swimming: Safe passage (1 turn), can avoid fish
- Traits: "murky water obscuring distance", "current tugging at limbs", "light visible at far end"

**sea_caves**:
- Environmental zone: Mixed (rock shelves above water)
- Properties: `water_level: "mixed"`, `breathable: true`, `lighting: "dim_filtered"`
- Required exits: west → `tidal_passage`
- Key features: Garrett rescue location, treasure cache location
- NPCs: sailor_garrett (drowning, 5-turn timer from room entry)
- Items: treasure_cache_location (revealed after rescue)
- Traits: "daylight filtering through ceiling cracks", "shifting light patterns on water", "debris islands amid flooded floor"

**merchant_quarter**:
- Environmental zone: Over-head deep water
- Properties: `water_level: "over_head"`, `breathable: false`, `lighting: "dim"`
- Required exits: north → `flooded_plaza`, south → `merchant_warehouse`
- Key features: Swimming required, tapping sound from warehouse, route to Delvan
- Traits: "dark windows in water-stained buildings", "floating debris and half-submerged carts", "faint rhythmic tapping from somewhere south"

**merchant_warehouse**:
- Environmental zone: Multi-level (flooded ground floor, air pockets, dry second floor)
- Properties: `multi_level: true`
- Sub-locations:
  - Ground floor: `water_level: "submerged"`, `breathable: false`
  - Wine cellar: `water_level: "submerged_with_air_pocket"`, `breathable: true` (air pocket)
  - Second floor: `water_level: "ankle"`, `breathable: true`
- Required exits: north → `merchant_quarter`
- Key features: Delvan rescue, navigation challenge (3 turns breath minimum), lever for extraction
- NPCs: merchant_delvan (bleeding, trapped, 10-13 turn timer)
- Items: merchant_lockbox, lever, scattered_cargo
- Navigation: Dive through flooded ground floor → find hatch → wine cellar air pocket → narrow staircase → second floor
- Traits: "merchant's sign visible above waterline", "tapping from second floor window", "cargo crates floating like ghosts inside"

**deep_archive**:
- Environmental zone: Dry (sealed chamber)
- Properties: `water_level: "dry"`, `breathable: true`, `sealed_chamber: true`, `lighting: "glowworm"`
- Access: Requires advanced swimming (30-foot underwater entrance) OR Archivist's enchanted bubble
- Required exits: up → `flooded_plaza`
- Key features: Archivist, water pearl (waystone fragment), knowledge quest, ancient tomes
- NPCs: the_archivist (spectral, bound to archive)
- Items: water_pearl, ancient_tome, scattered_knowledge_fragments, water_bloom
- Traits: "glowworms covering ceiling", "intact shelves of preserved books", "spectral figure drifting between stacks"

### 1.2 Required NPCs

| Actor ID | Name | Role | Commitment Timer | Source |
|----------|------|------|------------------|--------|
| `camp_leader_mira` | Camp Leader Mira | Quest giver, morale tracker | N/A | `sunken_district_sketch.json` |
| `old_swimmer_jek` | Old Swimmer Jek | Teacher (basic swimming) | N/A | `sunken_district_sketch.json` |
| `child_survivor` | Child Survivor | Hint giver (Archivist) | N/A | `sunken_district_sketch.json` |
| `sailor_garrett` | Sailor Garrett | Rescue target, treasure revealer | 5 turns base (no hope bonus) | `sunken_district_sketch.json` |
| `merchant_delvan` | Merchant Delvan | Rescue target, black market connection | 10 turns base (+3 hope bonus) | `sunken_district_sketch.json` |
| `the_archivist` | The Archivist | Knowledge quest, water pearl | N/A | `sunken_district_sketch.json` |
| `predatory_fish` | Predatory Fish | Environmental hazard | N/A | `sunken_district_sketch.json` |

**NPC Details:**

**camp_leader_mira**:
- Description: "A middle-aged woman with tired eyes but iron determination. She manages the survivors."
- Role: Quest giver (rescue_garrett, rescue_delvan), morale tracker
- Initial disposition: Neutral
- State machine:
  - States: `neutral`, `friendly`, `allied`, `disappointed`
  - Initial: `neutral`
  - Transitions:
    - neutral → friendly: Player rescues one survivor
    - friendly → allied: Player rescues both OR camp morale high
    - any → disappointed: Player lets survivor die without trying
- Services: Information about missing people, morale status
- Trust sources: Rescues (+2 each), helping camp (+0.5)
- Dialog topics: camp, help, garrett, delvan

**old_swimmer_jek**:
- Description: "An elderly man with weathered skin and webbed fingers - a birth defect that made him legendary."
- Role: Teacher (basic swimming only; advanced requires Garrett)
- Services:
  - Basic swimming: 5 gold OR food item, 1 turn, extends breath to 15
  - Advanced swimming: Taught by Garrett (after 5 turn recovery), free (gratitude), 2 turns
- Dialog topics: swimming, price, favor (find Garrett)

**child_survivor**:
- Description: "A young child clutching a sodden doll. They watch everything with wide eyes."
- Role: Hint giver about Archivist ("The library lady is still down there. She clicks and hums. I think she's lonely.")
- Dialog topics: doll, scared (gives Archivist hint)

**sailor_garrett**:
- Description: "A young man with tattooed arms, currently drowning. His eyes show terror."
- Conditions: drowning, exhaustion
- Properties: `breath_remaining: 5`, `damage_per_turn_drowning: 10`
- State machine:
  - States: `drowning`, `stabilized`, `rescued`, `dead`
  - Initial: `drowning`
  - Transitions:
    - drowning → stabilized: Given breathing item
    - stabilized → rescued: Led to surface OR exhaustion cured and swims out
    - drowning → dead: Breath reaches 0 OR health reaches 0
- **Timer**: 5 turns from room entry (NOT from commitment)
- **Hope extends survival**: No (physics doesn't care about promises)
- If rescued: +4 gratitude, reveals treasure location, unlocks advanced swimming lessons (after 5 turn recovery), +1 Echo trust
- If abandoned: Dies, Jek refuses advanced lessons, camp morale -1, -1 Echo trust

**merchant_delvan**:
- Description: "A portly man pinned under cargo. His face is pale from blood loss."
- Conditions: bleeding, broken_leg, trapped
- Properties: `damage_per_turn: 5`
- State machine:
  - States: `trapped`, `freed`, `mobile`, `dead`
  - Initial: `trapped`
  - Transitions:
    - trapped → freed: Cargo removed (strength OR lever)
    - freed → mobile: Bleeding stopped AND leg splinted
    - trapped → dead: Health reaches 0
- **Timer**: 10 turns from first encounter
- **Hope extends survival**: Yes (+3 turns with hope bonus)
- Rescue steps: Stop bleeding → free from cargo → splint leg or carry
- If rescued: 50 gold + rare items, 25% merchant discount, black market connection, +1 Echo trust
- If abandoned: Dies, black market unavailable, camp morale -1, -1 Echo trust
- **Black market mechanism** (DQ-3 resolution): When rescued, Delvan says "I owe you my life. If you ever need... special services... find me at the camp." This sets `delvan_has_undercity_knowledge` flag. Player must return to camp and explicitly ask Delvan about "special services" or "black market" to learn the undercity entrance pattern (`knows_undercity_entrance` flag). Delvan does NOT automatically reveal it - player agency required.

**the_archivist**:
- Description: "A spectral figure in scholar's robes. Not a ghost exactly - more an echo, like in the Nexus."
- Nature: Spirit bound to archive, cannot leave
- State machine:
  - States: `guardian`, `helpful`, `allied`
  - Initial: `guardian`
  - Transitions:
    - guardian → helpful: Player demonstrates scholarly interest (dialog, brings book)
    - helpful → allied: Player completes knowledge quest (brings 3+ lost secrets)
- Services:
  - Information: Free (any trust), history and lore
  - Enchanted bubble: Trust >= 2 (helpful state), breathing in flooded areas
  - Water pearl: Trust >= 3 (allied state), requires knowledge quest
- Knowledge quest: Bring 3 of 5 scattered knowledge fragments
- Dialog topics: identity, disaster, water_pearl, knowledge_quest

**predatory_fish**:
- Description: "Large fish with visible teeth, grown strange since the disaster. They circle and watch."
- Type: Environmental hazard (NOT combat encounter)
- Properties: `hazard_type: "environmental"`, `not_combat_encounter: true`, `no_xp_or_loot: true`
- Behavior:
  - In shallows: Watch but don't attack
  - In deep water: Dart in to bite, retreat before retaliation (attack once per passage)
  - When blood in water: Become cautious (multiple wounded makes them hesitate)
  - Response to combat: Fighting in water heavily penalized (-4 attack, half damage); fish retreat but return
- Damage: 8 HP + bleeding condition

### 1.3 Required Items

| Item ID | Name | Purpose | Found In | Source |
|---------|------|---------|----------|--------|
| `air_bladder` | Air Bladder | Breathing underwater (3 uses) | `survivor_camp` | `sunken_district_sketch.json` |
| `waterproof_sack` | Waterproof Sack | Protect items from water | `flooded_plaza` | `sunken_district_sketch.json` |
| `water_pearl` | Water Pearl | Waystone fragment | `deep_archive` (Archivist reward) | `sunken_district_sketch.json` |
| `ancient_tome` | Ancient Tome | Lore, valuable | `deep_archive` | `sunken_district_sketch.json` |
| `lever` | Lever | Free Delvan from cargo | `merchant_warehouse` | `sunken_district_sketch.json` |
| `water_bloom` | Water Bloom | Bee Queen trade (Beast Wilds) | `deep_archive` | `sunken_district_sketch.json` |

**Item Details:**

**air_bladder**:
- Properties: `portable: true`, `breathing_item: true`, `uses: 3`
- Effect: Restores breath to full when used
- Works in: Most flooded areas (NOT Deep Archive without Archivist bubble)

**waterproof_sack**:
- Properties: `portable: true`, `container: true`
- Effect: Items stored within protected from water damage

**water_pearl**:
- Properties: `portable: true`, `quest_item: true`, `light_source: true`
- Location: Deep Archive (Archivist reward)
- Acquisition: Complete knowledge quest (bring 3 of 5 fragments)
- Use: Required for waystone repair in Nexus

**lever**:
- Properties: `portable: true`, `tool: true`
- Use: Free Delvan from cargo (alternative to high strength)
- Also: Can clear collapsed canal route

**water_bloom**:
- Properties: `portable: true`, `rare_flower: true`
- Location: Deep Archive (flooded stacks area)
- Use: Trade item for Bee Queen in Beast Wilds

### 1.4 Required Puzzles/Challenges

| Puzzle | Location | Type | Requirements | Source |
|--------|----------|------|--------------|--------|
| Garrett Rescue | `sea_caves` | Timed rescue | Swimming skill, breathing item, 5-turn timer | `big_game_overview.md` |
| Delvan Rescue | `merchant_warehouse` | Multi-step timed rescue | Swimming, bandages, lever, 10-13 turn timer | `big_game_overview.md` |
| Warehouse Navigation | `merchant_warehouse` | Environmental | Basic swimming, 3+ turns breath | `sunken_district_sketch.json` |
| Knowledge Quest | `deep_archive` | Collection quest | 3 of 5 knowledge fragments | `sunken_district_sketch.json` |

**Garrett Rescue Details:**
- Timer: 5 turns from room entry (Garrett is already drowning when player arrives)
- Options:
  1. Give air bladder → stabilizes Garrett → still needs help swimming out
  2. Cure exhaustion → can swim but still drowning → needs surface fast
  3. Pull/lead to safety → requires swimming skill OR exceptional strength
- Success: Garrett rescued, reveals treasure, unlocks advanced swimming (after 5 turn recovery)
- Failure: Garrett drowns, body can be found later

**Delvan Rescue Details:**
- Timer: 10-13 turns from first encounter (hope bonus applies)
- Steps:
  1. Stop bleeding (bandages, healing, pressure)
  2. Free from cargo (lever OR high strength)
  3. Splint leg or carry to safety
- Multi-turn process - cannot be rushed
- Success: Substantial rewards, black market access
- Failure: Delvan bleeds out, body found under cargo

**Knowledge Quest Details:**
- Non-timed (Archivist can wait forever)
- Requires 3 of 5 fragments:
  1. Merchant ledger (merchant_warehouse) - Trade routes before disaster
  2. Survivor story (survivor_camp, from Jek or Mira) - Firsthand flooding account
  3. Guild records (flooded_chambers) - Administrative records
  4. Garrett's map (sea_caves, from rescued Garrett) - Underwater passages
  5. Delvan's contacts (merchant_warehouse, from rescued Delvan) - Black market network
- Design: Some fragments come from rescued NPCs, rewarding those relationships

**Knowledge Fragments:**
| Fragment | Location | Source | Content |
|----------|----------|--------|---------|
| Merchant Ledger | Merchant Warehouse | Exploration | Trade routes pre-disaster |
| Survivor Story | Survivor Camp | Jek or Mira (dialog) | Firsthand flooding account |
| Guild Records | Flooded Chambers | Exploration | Administrative records |
| Garrett's Map | Sea Caves | Garrett (if rescued) | Underwater passages |
| Delvan's Contacts | Merchant Warehouse | Delvan (if rescued) | Black market network |

### 1.5 Communication Conventions

**Verbal NPCs**: Camp Leader Mira, Old Swimmer Jek, Child Survivor, Sailor Garrett, Merchant Delvan, The Archivist

**Non-verbal NPCs**: Predatory Fish

```
Predatory Fish Communication:
- Circle lazily = observing, not aggressive
- Dart in quickly = attack incoming
- Retreat to shadows = deterred but not gone
- Multiple fish circling = coordinated threat
```

**Communication learning curve**: Fish behavior is learned through observation. NPCs warn about deep water dangers. Jek specifically explains fish attack patterns as part of swimming instruction.

---

## 2. Cross-Region Connections

### 2.1 Items This Region Imports

| Item | Source Region | Purpose Here | Urgency |
|------|---------------|--------------|---------|
| Bandages | Civilized Remnants OR Nexus | Stop Delvan's bleeding | Time-sensitive |
| Healing items | Any region | Restore health, cure conditions | Optional |
| Cold protection | Frozen Reaches | Deep water hypothermia | Optional |

### 2.2 Items This Region Exports

| Item | Destination Region | Purpose There | Acquisition |
|------|-------------------|---------------|-------------|
| Water Pearl | Nexus | Waystone fragment | Archivist knowledge quest |
| Water Bloom | Beast Wilds | Bee Queen trade | Deep Archive |
| Delvan's connection | Civilized Remnants | Undercity access | Rescue Delvan |
| Swimming skill | All regions | Water traversal everywhere | Learn from Jek/Garrett |

### 2.3 NPCs With Cross-Region Connections

| NPC Here | Connected To | Connection Type | Gossip Timing |
|----------|--------------|-----------------|---------------|
| Delvan | Undercity contacts | Black market access | 7 turns (fast criminal network) |
| Garrett | Jek | Student-teacher | 0 turns (same location) |
| Camp survivors | Civilized Remnants refugees | Shared history | 15 turns |

### 2.4 Environmental Connections

| Effect | Direction | Trigger | Timing |
|--------|-----------|---------|--------|
| Cold spread freeze | From Frozen Reaches | Telescope not repaired | Turn 175 - some water freezes |

**Note**: If Frozen Reaches telescope is not repaired by turn 175, some Sunken District water freezes, creating new routes and new hazards.

### 2.5 Travel Times

| From | To | Turns | Notes |
|------|-----|-------|-------|
| Nexus Chamber | Flooded Plaza | 1 turn | Direct exit |
| Flooded Plaza | Survivor Camp | 1 turn | Direct path |
| Flooded Plaza | Sea Caves (Garrett) | 3 turns | Plaza → Chambers → Passage → Caves |
| Flooded Plaza | Merchant Warehouse (Delvan) | 4 turns | Plaza → Quarter → Warehouse (navigation) |
| Survivor Camp | Sea Caves | 4 turns | Camp → Plaza → Chambers → Passage → Caves |
| Sea Caves | Survivor Camp | 3 turns | Return path |
| Survivor Camp | Merchant Warehouse | 5 turns | Camp → Plaza → Quarter → Warehouse |
| Merchant Warehouse | Survivor Camp | 4 turns | Return path |

**Travel time assumptions**:
- Each location transition = 1 turn
- Warehouse navigation challenge = 1 extra turn (finding hatch, air pocket)
- Advanced swimming reduces passage time by 1 turn
- No shortcuts exist (waystone not available until endgame)

**Impact on commitments**:

**Dual Rescue Analysis** (why it's impossible on first playthrough):
```
Optimal path attempting both rescues:
Turn 0: Arrive at Flooded Plaza
Turn 1: Go to Survivor Camp, learn basic swimming
Turn 2: Go to Flooded Plaza
Turn 3: Go to Flooded Chambers
Turn 4: Go through Tidal Passage
Turn 5: Arrive at Sea Caves - Garrett has 5 turns starting NOW
Turn 6: Stabilize Garrett (air bladder)
Turn 7: Help Garrett to surface
Turn 8: Return through passage
Turn 9: Return through chambers
Turn 10: Return to plaza
Turn 11: Go to Merchant Quarter
Turn 12: Arrive at Warehouse - Find Delvan (timer starts, 10-13 turns)
...
Garrett timer expired at turn 10 (5 turns from turn 5)
OR Delvan timer expires while saving Garrett
```

**The math doesn't work**:
- Garrett has 5 turns from room entry (turn 5-10)
- Minimum time to save Garrett and reach Delvan: ~7 turns after finding Garrett
- First-time player cannot know both exist simultaneously
- This is INTENTIONAL design

---

## 3. Instance-Specific Systems

### 3.1 NPC Services

| NPC | Service | Cost/Requirements | Trust Gate | Notes |
|-----|---------|-------------------|------------|-------|
| Jek | Basic swimming | 5 gold OR food | None | 1 turn, breath → 15 |
| Garrett | Advanced swimming | Free (gratitude) | Must rescue first | 2 turns, breath → 20, requires 5 turn recovery |
| Mira | Quest information | Free | None | Missing people locations |
| Archivist | Information | Free | Guardian state | History, lore |
| Archivist | Enchanted bubble | Free | Helpful state (trust 2+) | Breathing anywhere |
| Archivist | Water pearl | Free | Allied state (trust 3+) | Requires knowledge quest |

### 3.2 Companions

N/A - **No companions can be recruited in this region.**

**Rationale**: This region is designed as a solo challenge. While NPCs can be rescued, they do not become traveling companions. Garrett and Delvan remain at survivor camp after rescue.

### 3.3 Commitments

| Target NPC | Trigger | Timer | Timer Trigger | Hope Bonus | Fulfillment Flag |
|------------|---------|-------|---------------|------------|------------------|
| `sailor_garrett` | "I'll save you", "hold on", "I'm coming back" | 5 turns | `on_room_entry` | No | `garrett_rescued` |
| `merchant_delvan` | "I'll free you", "I'll get help", "I'll stop the bleeding" | 10 turns | `on_first_encounter` | +3 turns | `delvan_rescued` |

**Garrett Commitment Details:**
```python
CommitmentConfig = {
    "id": "commit_save_garrett",
    "target_npc": ActorId("sailor_garrett"),
    "goal": "Rescue Garrett from drowning",
    "trigger_phrases": ["I'll save you", "I'll get you out", "hold on", "I'm coming back"],
    "hope_extends_survival": False,  # Physics doesn't care about promises
    "base_timer": 5,  # From room entry, NOT commitment
    "fulfillment_flag": "garrett_rescued"
}
```

**Special Note**: Garrett's timer starts when player enters Sea Caves, not when commitment is made. This is unique - most commitments start timers on commitment. Garrett is already drowning.

**Implementation (Room-Entry Timer)**:
This is NOT a commitment timer - it's a scheduled event triggered by room entry:
1. Behavior trigger: `on_enter_location("sea_caves")`
2. Effect: `schedule_event("garrett_death", current_turn + 5, {"actor": "sailor_garrett"})`
3. Cancellation: When Garrett transitions to `rescued` state, call `cancel_scheduled_event("garrett_death")`
4. If event fires: Garrett transitions to `dead` state, sets `garrett_dead` flag

The commitment system tracks the player's promise and trust consequences. Garrett's death timer is an environmental clock independent of whether the player makes a promise.

**Withdrawal Response (Garrett)**:
- Dialog: "'The cave... east wall... merchant cache... tell Jek...' He points frantically before the current pulls at him."
- Reveals: Treasure location (even if rescue fails)
- Trust effect: 0 (neutral - player was honest)
- Can recommit: No (time-critical)

**Abandonment Effects (Garrett)**:
- Flag set: `broke_promise_garrett`
- Garrett dies
- Jek refuses advanced swimming lessons
- Mira trust -2, camp morale -1
- Echo reaction: "He believed you. In his final moments, he waited."

**Delvan Commitment Details:**
```python
CommitmentConfig = {
    "id": "commit_save_delvan",
    "target_npc": ActorId("merchant_delvan"),
    "goal": "Free Delvan and stop his bleeding",
    "trigger_phrases": ["I'll free you", "I'll get help", "I'll stop the bleeding", "hold on, I'll save you"],
    "hope_extends_survival": True,
    "hope_bonus": 3,
    "base_timer": 10,  # From first encounter
    "fulfillment_flag": "delvan_rescued"
}
```

**Withdrawal Response (Delvan)**:
- Dialog: "'Wait... please...' His voice weakens. 'My lockbox... combination is my daughter's birthday... fourth month, twelfth day... at least take what you can carry...'"
- Reveals: Lockbox combination
- Unlocks: Merchant lockbox can be opened
- Trust effect: 0
- Can recommit: Yes (if time remains)

**Abandonment Effects (Delvan)**:
- Flag set: `broke_promise_delvan`
- Delvan dies
- Black market unavailable
- Camp morale -1
- Echo reaction: "He offered you everything for his life. You took nothing and gave nothing."

**Both Commitment Special Case:**
If player promises both but can only save one:
- Scenario: Player commits to both, saves Garrett, Delvan dies
- Effect: Garrett grateful but camp morale damaged
- Echo: "You kept one word. The other was drowned by circumstance. Intention matters, but so do results."
- Partial penalty: -0.5 instead of -1 if clearly tried

### 3.4 Gossip Sources

| Event | Content | Target NPCs | Delay | Confession Window |
|-------|---------|-------------|-------|-------------------|
| Garrett fate | "Garrett rescued/died" | Camp NPCs | 0 turns | N/A (same location) |
| Delvan fate | "Delvan rescued/died" | Undercity contacts | 7 turns | N/A |
| Garrett commitment broken | "Promised to save, didn't return" | Echo, Mira | 0 turns | N/A |

**Note**: Gossip is immediate within camp (same location). Delvan's fate spreads fast to undercity (criminal networks communicate quickly).

### 3.5 Branding/Reputation (if applicable)

N/A - No unique branding mechanics in this region.

**Note**: Camp morale affects services but is not a formal reputation system.

**Camp Morale**:
| Level | Trigger | Effects |
|-------|---------|---------|
| Low | Initial / either dies | Desperate survivors, some services unavailable |
| Medium | One rescued | Normal services |
| High | Both rescued | Bonus services, occasional supply gifts |

### 3.6 Waystones/Endings (if applicable)

| Fragment | Location | Acquisition | Requirements |
|----------|----------|-------------|--------------|
| Water Pearl | Deep Archive | Archivist quest reward | 3 of 5 knowledge fragments |

**Water Pearl Acquisition Path:**
1. Reach Deep Archive (advanced swimming OR Archivist bubble)
2. Demonstrate scholarly interest (dialog, bring book)
3. Complete knowledge quest (gather 3 of 5 fragments)
4. Archivist gifts water pearl

### 3.7 Skills (if applicable)

**Skill Progression: Swimming**
- Tier 1: Basic Swimming from Old Swimmer Jek
  - Requirements: 5 gold OR food item, 1 turn
  - Effects: Breath 15, traverse chest-deep water, normal swim speed
- Tier 2: Advanced Swimming from Sailor Garrett (requires Basic Swimming)
  - Requirements: Rescue Garrett, wait 5 turns for recovery
  - Effects: Breath 20, navigate currents, avoid fish attacks

**Skill Permanence**: Once learned, swimming applies everywhere in the game (any water area benefits).

### 3.8 Permanent Consequences

Document actions in this region that permanently lock content or endings:

| Action | Consequence | Affected Content | Reversible? |
|--------|-------------|------------------|-------------|
| Garrett death | Advanced swimming unavailable | Can't access some advanced water content | No |
| Delvan death | Black market access blocked | Undercity services, merchant connections | No |

**Conditional Lock: Advanced Swimming**
- Required: Garrett must survive rescue
- Lost if: Garrett dies (timer expires or player abandons)
- Recovery: None - Jek only teaches basic swimming, advanced requires Garrett
- Impact: Some deep water areas harder to access, fish attacks more dangerous

**Conditional Lock: Black Market Access**
- Required: Delvan must survive rescue
- Lost if: Delvan dies (bleeds out or player abandons)
- Recovery: None - Delvan is the only connection to Civilized Remnants undercity
- Impact: Black market services unavailable, certain items harder to obtain

---

## 4. Region Hazards

**Hazard Type**: Environmental

### 4.1 Hazard Zones

| Zone Type | Locations | Effects | Mitigation |
|-----------|-----------|---------|------------|
| Ankle water | Flooded Plaza edges | No swimming needed, no breath depletion | None needed |
| Waist water | Flooded Plaza center | Movement slowed, no breath depletion | None needed |
| Chest water | Flooded Chambers | Movement very slow, no breath depletion | Basic swimming helps |
| Submerged | Tidal Passage, Merchant Quarter, Warehouse ground | Swimming required, breath depletes | Swimming skill, breathing items |
| Air pocket | Warehouse wine cellar | Breath restored, temporary safe zone | N/A |
| Sealed dry | Deep Archive | Normal breathing, requires access | Advanced swimming OR bubble |

### 4.2 Conditions Applied

| Condition | Source | Severity Progression | Treatment |
|-----------|--------|---------------------|-----------|
| Drowning | Non-breathable water | Breath -1/turn, damage at 0 | Surface, breathing item |
| Hypothermia | Deep cold water | 5 severity/turn | Warm area, return to camp |
| Bleeding | Fish attacks, Delvan | 5 damage/turn | Bandages, healing |

**Breath Tracking:**
| State | Base Breath | Depletion Rate | Warning | Damage |
|-------|-------------|----------------|---------|--------|
| No swimming | 10 | 1/turn underwater | At 3 remaining | 10/turn at 0 |
| Basic swimming | 15 | 1/turn underwater | At 3 remaining | 10/turn at 0 |
| Advanced swimming | 20 | 1/turn underwater | At 3 remaining | 10/turn at 0 |

**Breathing Items:**
- Air bladder: Works in most flooded areas, 3 uses
- Enchanted bubble (Archivist): Works everywhere including Deep Archive

### 4.3 Companion Restrictions

| Companion Type | Can Enter | Comfort Level | Notes |
|----------------|-----------|---------------|-------|
| Wolves | No | Impossible | Cannot swim; instinct prevents entering water |
| Salamander | No | Impossible | Would extinguish in water; auto-returns to Nexus |
| Human (Sira) | Limited | Depends on swimming | Without swimming: stays in camp. Basic: shallow only. Advanced: full access |
| Human (Aldric) | No | Impossible | Too weak for water hazards; stays in camp |

**Waiting Behavior:**
- Wolves: Wait at Forest Edge (Beast Wilds) or Nexus Chamber
- Salamander: Returns to Nexus Chamber automatically
- Humans: Wait at Survivor Camp

**Return Behavior:**
- Non-salamander companions rejoin at waiting location when player returns
- Salamander requires player to physically return to Nexus

---

## 5. Behavioral Defaults

### 5.1 NPC Behavioral Defaults

```
- Default disposition toward player: Neutral to desperate (survivors need help)
- Reaction to player brands: N/A (no brands apply here)
- Reaction to gossip: Mira becomes disappointed if player fails rescues
- Reaction to companions: N/A (all companions excluded)
- Reaction to conditions: NPCs may comment on player's wet/cold state
```

### 5.2 Location Behavioral Defaults

```
- Environmental zone: Water level varies by location (see Section 4.1)
- Lighting: Dim throughout (underwater, flooded)
- Turn phase effects: Breath depletion in submerged areas, hypothermia in deep cold
- Combat: Heavily penalized (-4 attack, half damage in water)
```

### 5.3 Item Behavioral Defaults

```
- Typical item types: Breathing items, tools, quest items
- Environmental interactions: Non-waterproofed items may be damaged by water
- Items in waterproof sack: Protected from damage
- Organic items: May waterlog if exposed
```

### 5.4 Group/Pack Dynamics

**N/A - No group dynamics in this region.**

**Rationale**: Predatory fish are environmental hazards, not coordinated groups. They don't have leaders, pack behavior, or state machines. Fish function as obstacles that threaten traversal, similar to cold or drowning hazards. Individual fish don't coordinate or respond to each other's deaths.

---

## 6. Generative Parameters

### 6.1 Location Generation

**Generation scope**: Limited

Only 1-2 additional locations might exist - flooded side passages or collapsed buildings.

**Location Template: Flooded Side Area**
```
- Purpose: Exploration, minor loot
- Environmental zone: Chest to submerged
- Typical features: Debris, trapped air pockets, environmental storytelling
- Connection points: Could branch from flooded_chambers or merchant_quarter
- Hazards: Deep water, possible fish
- Content density: Sparse (0-1 items, no NPCs)
```

### 6.2 NPC Generation

**Generation scope**: None

This region has exactly the designed NPCs. Additional survivors would dilute the focused rescue narrative.

**Rationale**: The Sunken District is about two specific rescue choices, not a populated refugee camp. Adding generic survivors would undermine the focus on Garrett and Delvan.

### 6.3 Item Generation

**Generation scope**: Limited

```
- Trade goods: Waterlogged merchandise, salvageable goods
- Environmental props: Debris, floating crates, soggy documents
- Flavor loot: Pre-disaster coins, personal effects
- Consumables: Additional air bladders (rare), preserved food
```

### 6.4 Atmospheric Details

**Environmental details**:
```
- Sounds: Dripping, gurgling, distant splashing, eerie silence underwater
- Visual motifs: Murky water, floating debris, ribbons marking paths, filtered light
- Tactile sensations: Cold water, waterlogged clothing, current pulling
- Smells: Brine, decay, damp stone, occasional smoke from camp
```

**State-dependent variations**:
```
- After Garrett rescue: Camp more hopeful, fire brighter
- After Delvan rescue: Camp has more supplies visible
- After both die: Camp quiet, fire dimmer, survivors withdrawn
- With water pearl: Deep archive feels warmer, more welcoming
```

### 6.5 Density Guidelines

| Area Type | NPCs | Items | Locations | Atmosphere |
|-----------|------|-------|-----------|------------|
| Survivor Camp | 3 | 2-3 | Fixed | Desperate hope |
| Flooded areas | 0-1 (fish) | 0-1 | Few branches | Eerie, dangerous |
| Deep Archive | 1 | 3-4 | Fixed | Scholarly, preserved |

### 6.6 Thematic Constraints

```
Tone: Desperate, urgent, melancholy
Common motifs: Rising water, trapped survivors, impossible choices
MUST include: Time pressure for rescues, breathing mechanics
MUST avoid: Easy dual rescue, companion assistance, combat focus
Sensory emphasis: Water sounds, restricted visibility, cold
```

### 6.7 Mechanical Participation Requirements

```
Required systems (generated content MUST use):
- [x] Trust/disposition (NPCs respond to rescue outcomes)
- [x] Gossip (rescue fates spread to camp and beyond)
- [x] Environmental conditions (water levels, breath tracking)
- [x] Companion restrictions (all companions excluded)

Optional systems (use if thematically appropriate):
- [x] Commitments (rescue promises)
- [x] Services (swimming lessons, Archivist services)
- [ ] Puzzles (not primary focus)
- [ ] Brands/reputation (camp morale is simpler)
```

---

## 7. LLM Narration Guidance

### 7.1 Region Traits

```
Environmental:
- "murky water hiding depths"
- "debris floating like ghosts"
- "colored ribbons marking safe paths"
- "the smell of brine and old stone"
- "echoing splashes in flooded halls"
- "dim light filtering through cracks"
- "current tugging at your legs"
- "bubbles rising from below"

Emotional:
- "desperate urgency"
- "the weight of impossible choices"
- "hope struggling against rising water"

Historical:
- "a thriving district now drowned"
- "merchant signs above waterlines"
- "evidence of sudden catastrophe"
```

### 7.2 State Variants

| State | Trigger | Narration Change |
|-------|---------|------------------|
| `garrett_alive` | Initial | "Tapping sounds echo from the east caves" |
| `garrett_rescued` | Rescue complete | "Garrett rests by the fire, breathing steadily" |
| `garrett_dead` | Timer expired | "The tapping has stopped. Silence from the caves." |
| `delvan_alive` | Initial | "Rhythmic tapping from the warehouse - someone is still alive" |
| `delvan_rescued` | Rescue complete | "Delvan sits wrapped in blankets, color returning to his face" |
| `delvan_dead` | Timer expired | "The warehouse is silent now. No more tapping." |
| `camp_morale_high` | Both rescued | "The camp buzzes with cautious hope. Mira almost smiles." |
| `camp_morale_low` | Either/both dead | "The camp is quiet. No one meets your eyes." |

### 7.3 NPC Description Evolution

| NPC | State | Traits |
|-----|-------|--------|
| Garrett | drowning | "panicked eyes", "arms flailing weakly", "bubbles escaping lips", "terror" |
| Garrett | stabilized | "clutching the air bladder", "still terrified but breathing", "exhausted" |
| Garrett | rescued | "grateful beyond words", "still pale", "alive", "recovering" |
| Garrett | dead | Body description only - "still form", "peaceful at last", "cold" |
| Delvan | trapped | "pale from blood loss", "pinned under cargo", "voice weak", "determined" |
| Delvan | freed | "clutching wound", "relief mixed with pain", "grateful" |
| Delvan | mobile | "limping but alive", "color returning", "offering rewards" |
| Delvan | dead | "still form under cargo", "never freed", "blood pooled" |
| Mira | neutral | "tired eyes", "iron determination", "managing" |
| Mira | friendly | "eyes brighter", "grateful", "trusting" |
| Mira | disappointed | "won't meet your eyes", "voice flat", "broken trust" |

---

## 8. Validation Checklist

### 8.1 Completeness

- [x] All required entities from overview are listed
- [x] All cross-region dependencies documented
- [x] All instance-specific systems addressed (or marked N/A)
- [x] Environmental rules fully specified
- [x] Behavioral defaults cover all entity types

### 8.2 Consistency

- [x] Location IDs follow naming convention (`snake_case`)
- [x] NPC trust thresholds are reasonable
- [x] Commitment timers are fair given travel times (dual rescue intentionally unfair)
- [x] Companion restrictions match `cross_region_dependencies.md`
- [x] Gossip timing is consistent with established patterns

### 8.3 Cross-Region Verification

- [x] All imported items are exported from documented source regions
- [x] All exported items are imported by documented destination regions
- [x] Gossip timing matches in both source and destination region docs
- [x] NPC connections documented on both sides of relationship
- [x] Skill dependencies are achievable (swimming taught before needed)
- [x] Permanent consequences don't create impossible states

### 8.4 Generative Readiness

- [x] NPC generation seeds cover expected roles (N/A - no generation)
- [x] Location generation seeds cover expected types (Limited)
- [x] Density guidelines provide clear targets
- [x] Mechanical participation requirements are clear
- [x] Thematic constraints prevent off-tone content

---

## Appendix A: Infrastructure System Integration

### A.1 Commitment System

```python
# Garrett Commitment
CommitmentConfig = {
    "id": CommitmentId("commit_save_garrett"),
    "target_npc": ActorId("sailor_garrett"),
    "goal": "Rescue Garrett from drowning",
    "trigger_phrases": ["I'll save you", "I'll get you out", "hold on", "I'm coming back"],
    "hope_extends_survival": False,
    "base_timer": 5,  # Special: from room entry
    "fulfillment_flag": "garrett_rescued"
}

# Delvan Commitment
CommitmentConfig = {
    "id": CommitmentId("commit_save_delvan"),
    "target_npc": ActorId("merchant_delvan"),
    "goal": "Free Delvan and stop his bleeding",
    "trigger_phrases": ["I'll free you", "I'll get help", "I'll stop the bleeding"],
    "hope_extends_survival": True,
    "hope_bonus": 3,
    "base_timer": 10,
    "fulfillment_flag": "delvan_rescued"
}
```

### A.2 Condition System

```python
# Drowning progression
ConditionInstance = {
    "type": ConditionType.DROWNING,
    "severity": 0,  # Increases by 10 per turn without breath
    "source": "submerged_water"
}

# Hypothermia in deep cold
ConditionInstance = {
    "type": ConditionType.HYPOTHERMIA,
    "severity": 0,  # Increases by 5 per turn in cold water
    "source": "deep_cold_water"
}

# Bleeding from fish or Delvan state
ConditionInstance = {
    "type": ConditionType.BLEEDING,
    "severity": 50,  # 5 damage per turn
    "source": "fish_attack" | "cargo_injury"
}
```

### A.3 Environmental System

```python
# Water level zones
location.properties["water_level"] = WaterLevel.SUBMERGED  # or CHEST, WAIST, etc.
location.properties["breathable"] = False
location.properties["hypothermia_rate"] = 5  # Only in cold deep water
```

### A.4 Companion Restrictions

```python
# Wolf restriction for Sunken District
CompanionRestriction = {
    "location_patterns": ["flooded_*", "survivor_*", "tidal_*", "sea_*", "merchant_*", "deep_*"],
    "comfort": CompanionComfort.IMPOSSIBLE,
    "reason": "Cannot swim - instinct prevents entering water"
}

# Salamander restriction
CompanionRestriction = {
    "location_patterns": ["flooded_*", "survivor_*", "tidal_*", "sea_*", "merchant_*", "deep_*"],
    "comfort": CompanionComfort.IMPOSSIBLE,
    "reason": "Would extinguish in water"
}
```

---

## Appendix B: Data Structures

### B.1 Game State Schema (Sunken District-specific)

```json
{
  "extra": {
    "sunken_district": {
      "garrett_timer_started": null,
      "garrett_timer_room_entry_turn": null,
      "delvan_timer_started": null,
      "delvan_first_encounter_turn": null,
      "camp_morale": "low",
      "garrett_rescued": false,
      "delvan_rescued": false,
      "knowledge_fragments_found": [],
      "archivist_trust": 0
    }
  }
}
```

### B.2 Rescue NPC Actor Definitions

```json
{
  "id": "sailor_garrett",
  "name": "Sailor Garrett",
  "description": "A young man with tattooed arms, currently drowning.",
  "properties": {
    "state_machine": {
      "states": ["drowning", "stabilized", "rescued", "dead"],
      "initial": "drowning"
    },
    "conditions": [
      {"type": "drowning", "severity": 50},
      {"type": "exhaustion", "severity": 80}
    ],
    "commitment_target": true,
    "trigger_type": "on_room_entry",
    "base_timer": 5,
    "hope_extends": false
  },
  "flags": {},
  "location": "sea_caves"
}
```

```json
{
  "id": "merchant_delvan",
  "name": "Merchant Delvan",
  "description": "A portly man pinned under cargo. His face is pale from blood loss.",
  "properties": {
    "state_machine": {
      "states": ["trapped", "freed", "mobile", "dead"],
      "initial": "trapped"
    },
    "conditions": [
      {"type": "bleeding", "severity": 70},
      {"type": "broken_leg", "severity": 100}
    ],
    "commitment_target": true,
    "trigger_type": "on_first_encounter",
    "base_timer": 10,
    "hope_extends": true,
    "hope_bonus": 3
  },
  "flags": {},
  "location": "merchant_warehouse"
}
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2025-12-11 | Initial draft from template |
| 0.2 | 2025-12-11 | Updated to match revised template: Added Hazard Type field, Timer Trigger column in commitments, merged collection quest into Section 1.4, renumbered Section 3.7 to Skills with multi-tier format, added Section 3.8 Permanent Consequences, updated Section 5.4 to N/A with rationale, added Section 8.3 Cross-Region Verification, renumbered old 8.3 to 8.4 |
| 0.3 | 2025-12-11 | Phase 2 consistency fixes: Standardized trigger_type naming in Appendix B (CC-7), added Delvan black market mechanism (DQ-3/SD-1), clarified companion exclusion nuance (SD-2) |
