# Fungal Depths Detailed Design

**Version**: 0.2
**Last Updated**: 2025-12-11
**Status**: Draft

---

## 0. Authoring Guidance

### 0.1 Region Character

The Fungal Depths is a **symbiosis and consequence region** where the player navigates environmental hazards (spores, toxic air) while choosing between violence and healing. The central tension is whether to kill the Spore Mother (quick solution, lasting consequences) or heal her (harder path, transforms the region). Aldric provides time pressure and teaching opportunity, while the Myconids offer services gated by trust that remembers violence.

### 0.2 Content Density Expectations

- **Entity density**: Moderate (5 locations, 6 NPCs - Aldric, Spore Mother, 3 sporelings, Myconid Elder)
- **NPC interaction depth**: Rich (Aldric has dialog tree, Myconid has services, Spore Mother has empathic communication)
- **Environmental complexity**: Complex (3 spore zones, toxic air zone, light puzzle)
- **Time pressure**: Moderate (Aldric dying, but 50+ turns)

### 0.3 What Belongs Here

- Environmental hazards requiring equipment (spore zones need mask, toxic air needs mask, darkness needs light)
- Moral choices with lasting consequences (heal vs kill Spore Mother, help Aldric vs self-cure)
- Trust systems that remember violence (Myconids know if you killed fungi)
- Information breadcrumbs through dialog (Aldric reveals heartmoss, safe path, mushroom hints)
- Puzzles with time cost (light puzzle takes turns, infection progresses)
- NPCs who can't solve their own problems (Aldric too sick, sporelings can't leave Mother, Myconids can't handle cold)
- Teaching/skill acquisition (Aldric teaches mycology, Myconids teach spore resistance)

### 0.4 What Does NOT Belong Here

- **Easy combat victory** - Spore Mother fight is designed to be brutal and discourage violence
- **Consequence-free violence** - Killing fungi sets global flag that Myconids detect
- **Simple cure paths** - Full cure requires multiple silvermoss OR Myconid service with cross-region payment
- **Instant solutions** - Light puzzle takes turns, Deep Roots requires equipment from Myconids

### 0.5 Authoring Notes

- **Aldric is dying**: Track his death timer (50 turns base, +10 with hope). Show warnings. He's the region's urgency source.
- **Violence has memory**: The spore network communicates. Killing any `fungal: true` entity sets a flag Myconids detect on first interaction.
- **Equipment gates**: Breathing mask (Myconids) needed for Deep Root Caverns. Spore lantern (Myconids) needed to see in darkness. If player killed fungi and has negative Myconid trust, they're locked out until they rebuild trust.
- **Safe path reduces but doesn't eliminate spore damage**: Solving the light puzzle makes Spore Heart survivable, not safe.
- **Cross-region dependencies**: Ice crystals from Frozen Reaches are primary Myconid payment. Gold from Civilized Remnants is alternative.

### 0.6 Difficulty Design Notes

**Designed challenges** (intended to be hard):
- **Spore Mother combat is brutal**: 200 HP, 10 HP/turn regen, 20-damage attacks plus infection. Violence is supposed to feel like a bad choice.
- **Equipment lock-out**: Players who kill fungi before visiting Myconids face trust -3, gating mask/lantern access. This is intentional punishment for violence-first approach.
- **Deep Root Caverns require preparation**: Mask + light source both needed. No shortcuts.

**Fair challenges** (hard but solvable with preparation):
- **Light puzzle**: Observable pulse patterns, Aldric hints, journal clues. Patient observation solves it.
- **Aldric's 50-turn timer**: Generous enough for exploration, tight enough to create urgency. Cross-region trip to Frozen Reaches (ice crystal) fits within timer.
- **Myconid trust recovery**: Even with -3 from violence, trust can be rebuilt through meaningful actions (one point at a time).

**First-playthrough expectations**:
- **Likely to accomplish**: Stabilize Aldric (silvermoss is accessible), solve light puzzle, access Myconid services
- **Likely to fail or miss**: Full Aldric cure on first pass (requires Myconid trust OR second silvermoss), Spore Mother healing (requires Deep Roots access), optimal equipment path
- **Teaches for next time**: Violence has consequences (locked out of services), equipment enables exploration, dialog reveals hints

---

## 1. Required Entities

### 1.1 Required Locations

| Location ID | Name | Purpose | Source |
|-------------|------|---------|--------|
| `cavern_entrance` | Cavern Entrance | Entry; Aldric's camp; safe zone | Sketch |
| `luminous_grotto` | Luminous Grotto | Light puzzle; silvermoss; medium spores | Sketch |
| `spore_heart` | Spore Heart | Spore Mother encounter; high spores | Sketch |
| `myconid_sanctuary` | Myconid Sanctuary | Services; equipment; safe zone | Sketch |
| `deep_root_caverns` | Deep Root Caverns | Heartmoss; toxic air; darkness | Sketch |

**Location Details:**

**cavern_entrance**:
- Environmental zone: Safe (no spores)
- Properties: `spore_level: "none"`, `breathable: true`, `temperature: "cool"`
- Required exits: east → `nexus_chamber`, down → `luminous_grotto`
- Key features: Aldric's camp, his journal, empty vial
- Actors: `npc_aldric`
- Traits: Damp stone walls, cool air from below, distant dripping, small campfire

**luminous_grotto**:
- Environmental zone: Medium spores (+5 infection/turn)
- Properties: `spore_level: "medium"`, `breathable: true`, `light_level: 2`, `max_light_level: 6`
- Required exits: up → `cavern_entrance`, down → `spore_heart`, east → `myconid_sanctuary`
- Key features: Crystal pool, bioluminescent mushrooms (puzzle), ceiling inscription (hidden)
- Items: Silvermoss, bucket, pool, 4 mushrooms (blue, gold, violet, black), dead explorer
- Traits: Soft multicolored glow, crystal-clear pool, high vaulted ceiling with carved symbols

**spore_heart**:
- Environmental zone: High spores (+10 infection/turn, +3 with safe_path_known)
- Properties: `spore_level: "high"`, `breathable: true`, `temperature: "warm"`
- Required exits: up → `luminous_grotto`, down → `deep_root_caverns`
- Key features: Pulsing organic walls, Spore Mother, sporelings
- Actors: `npc_spore_mother`, `npc_sporeling_1`, `npc_sporeling_2`, `npc_sporeling_3`
- Traits: Pulsing organic walls, thick golden spore haze, rhythmic breathing sounds

**myconid_sanctuary**:
- Environmental zone: Safe (Myconids filter air)
- Properties: `spore_level: "none"`, `breathable: true`, `temperature: "comfortable"`
- Required exits: west → `luminous_grotto`
- Key features: Geometric fungal patterns, silent spore communication
- Items: Spore lantern, breathing mask (both require trust ≥ 0 to take)
- Actors: `npc_myconid_elder`
- Traits: Orderly rings of mushroom folk, silent communication through spore puffs

**deep_root_caverns**:
- Environmental zone: Toxic air (not breathable, 12 turns breath hold, then 20 damage/turn)
- Properties: `spore_level: "none"`, `breathable: false`, `requires_light: true`, `temperature: "cold"`
- Required exits: up → `spore_heart`
- Key features: Massive ancient roots, heartmoss, absolute darkness
- Items: Heartmoss, ancient bones
- Traits: Absolute darkness, roots thick as trees, ancient silence, bone-deep cold

### 1.2 Required NPCs

| Actor ID | Name | Role | Commitment Timer | Source |
|----------|------|------|------------------|--------|
| `npc_aldric` | Scholar Aldric | Dying scholar; mycology teacher | 50 turns (+10 with hope) | Sketch |
| `npc_spore_mother` | Spore Mother | Antagonist/ally; heal or kill | 200 turns (very slow) | Sketch |
| `npc_sporeling_1` | Sporeling | Pack follower of Spore Mother | N/A | Sketch |
| `npc_sporeling_2` | Sporeling | Pack follower | N/A | Sketch |
| `npc_sporeling_3` | Sporeling | Pack follower (younger) | N/A | Sketch |
| `npc_myconid_elder` | Myconid Elder | Service provider; trust-gated | N/A | Sketch |

**Scholar Aldric - Full Specification:**

- **Nature**: Frail human scholar, severely infected
- **Location**: `cavern_entrance` (immobile - too sick to move)
- **Health**: 40/100
- **Conditions**: Fungal infection severity 80, progression rate 2/turn, damage 2/turn
- **Death timer**: 50 turns base (+10 hope bonus when player commits to help); timer starts on_commitment
- **State machine**:
  - States: `critical`, `stabilized`, `recovering`, `dead`
  - Initial: `critical`
  - Transitions:
    - `critical` → `stabilized`: Given silvermoss (severity -40, progression stops)
    - `stabilized` → `recovering`: Given second silvermoss OR Myconid cure (fully cured, can walk)
    - `critical` → `dead`: Health ≤ 0 OR turn 50 (60 with hope)
- **Dialog topics**: infection, research, spore_mother (requires knows_infection), sporelings (requires knows_heartmoss), myconids, safe_path (requires knows_heartmoss), mushrooms (requires knows_mushroom_hint)
- **Services**: Teach mycology (requires: stabilized state, trust ≥ 2, gift item)
- **Trust sources**: +1 per meaningful dialog topic
- **Why he can't help himself**: Infection at severity 80 means he can barely stand. Entering the spore-heavy Grotto would kill him in minutes.

**Spore Mother - Full Specification:**

- **Nature**: Massive fungal creature, empathic communication
- **Location**: `spore_heart` (immobile - she IS the Spore Heart)
- **Health**: 200/200
- **Conditions**: Fungal blight severity 70, progression rate 1/turn (note: this describes her spreading influence, not damage to herself - she is immune to her own spores)
- **Regeneration**: 10 HP/turn (makes combat extremely difficult)
- **State machine**:
  - States: `hostile`, `wary`, `allied`, `dead`
  - Initial: `hostile`
  - Transitions:
    - `hostile` → `wary`: Player present 3 turns without attacking
    - `wary` → `hostile`: Player attacks
    - `hostile` → `allied`: Given heartmoss (works even mid-combat!)
    - `wary` → `allied`: Given heartmoss
    - `hostile` → `dead`: Health ≤ 0
    - `wary` → `dead`: Health ≤ 0
- **Combat stats**: Tendril lash (20 damage), Spore burst (15 damage + 25 infection)
- **Pack leader**: Sporelings follow her disposition
- **Communication**: Empathic spores - conveys emotions, simple concepts
- **Death effects**: Drops `mother_heart` trophy, spore levels remain indefinitely, Myconid trust -5, sporelings become neutral/confused

**Sporelings - Specification:**

- **Nature**: Small fungal creatures, extensions of Spore Mother
- **Location**: `spore_heart` (cannot leave - bound to Mother's presence)
- **Health**: 30/30 (sporeling_3: 20/20 - younger)
- **Pack**: `sporeling_pack`, role: follower
- **Range limit**: Cannot leave `spore_heart` - would wither if separated from Mother
- **Combat**: Spore puff (5 damage + 10 infection)
- **Disposition**: Follows Spore Mother's state

**Myconid Elder - Full Specification:**

- **Nature**: Sentient mushroom, communicates via colored spores
- **Location**: `myconid_sanctuary`
- **Initial trust**: 0 (or -3 if player has `has_killed_fungi` flag)
- **Dialog topics**: greeting, cure, cold, resistance, equipment, spore_mother, heartmoss
- **Services**:
  - Cure fungal infection: Accepts ice_crystal, rare_mineral, or gold
  - Teach spore resistance: Requires trust ≥ 2 + gift (grants 50% infection reduction)
- **Item permissions**: Spore lantern and breathing mask require trust ≥ 0 to take
- **Trust modifiers**: has_killed_fungi -3, healed_spore_mother +5, brought_offering +1, meaningful_dialog +1
- **Spore network**: Knows instantly if player has killed any `fungal: true` creature anywhere

### 1.3 Required Items

| Item ID | Name | Purpose | Found In | Source |
|---------|------|---------|----------|--------|
| `silvermoss` | Silvermoss | Stabilizes infection (-40 severity) | `luminous_grotto` | Sketch |
| `heartmoss` | Heartmoss | Cures Spore Mother's blight | `deep_root_caverns` | Sketch |
| `aldric_journal` | Aldric's Journal | Puzzle hints, lore | `cavern_entrance` | Sketch |
| `empty_vial` | Empty Vial | Container for samples | `cavern_entrance` | Sketch |
| `bucket` | Bucket | Holds 3 water charges for puzzle | `luminous_grotto` | Sketch |
| `pool` | Pool | Water source for puzzle | `luminous_grotto` (fixed) | Sketch |
| `mushroom_blue` | Blue Mushroom | Puzzle - safe, +1 light | `luminous_grotto` (fixed) | Sketch |
| `mushroom_gold` | Gold Mushroom | Puzzle - safe, +2 light | `luminous_grotto` (fixed) | Sketch |
| `mushroom_violet` | Violet Mushroom | Puzzle - DANGEROUS, releases spores | `luminous_grotto` (fixed) | Sketch |
| `mushroom_black` | Black Mushroom | Puzzle - DANGEROUS, absorbs light | `luminous_grotto` (fixed) | Sketch |
| `dead_explorer` | Dead Explorer | Contains research notes, flint | `luminous_grotto` (fixed) | Sketch |
| `research_notes` | Research Notes | Gift for Aldric teaching | `dead_explorer` (searchable) | Sketch |
| `spore_lantern` | Spore Lantern | Light source (level 3) | `myconid_sanctuary` | Sketch |
| `breathing_mask` | Breathing Mask | Allows breathing in toxic air | `myconid_sanctuary` | Sketch |
| `mother_heart` | Mother's Heart | Trophy if Spore Mother killed | Dropped on death | Sketch |

**Key Item Details:**

**silvermoss**:
- Effect: Reduces fungal infection severity by 40, stops progression
- Does NOT fully cure - need two silvermoss or Myconid service
- Consumable: Yes

**heartmoss**:
- Effect: Fully cures Spore Mother's fungal blight
- Location: Deep Root Caverns (requires light to find, mask to survive)
- Result: Spore Mother → allied, all spore levels → none, sporelings → friendly

**breathing_mask**:
- Effect: Allows breathing in toxic air (Deep Root Caverns)
- Requirement: Must be equipped
- Acquisition: Myconid Sanctuary, requires trust ≥ 0

### 1.4 Required Puzzles/Challenges

| Puzzle | Location | Type | Requirements | Source |
|--------|----------|------|--------------|--------|
| Illuminate Grotto | `luminous_grotto` | Light puzzle | Water 3 correct mushrooms to reach light level 6 | Sketch |
| Deep Root Survival | `deep_root_caverns` | Equipment check | Breathing mask + light source | Sketch |

**Illuminate Grotto Puzzle - Full Specification:**

- **Goal**: Increase room light from 2 to 6 to read ceiling inscription
- **Mechanism**: Fill bucket from pool (3 charges), pour on mushrooms
- **Mushroom effects**:
  - Blue (steady pulse): +1 light - SAFE
  - Gold (irregular pulse): +2 light - SAFE (best)
  - Violet (rapid pulse): +0 light, +15 infection - DANGEROUS
  - Black (no pulse): -2 light - DANGEROUS
- **Hints**: Aldric dialog, journal, observable pulse patterns
- **Optimal solution**: Gold → Blue → Gold (or any combo of safe mushrooms totaling +4)
- **Success**: `safe_path_known` flag set, reduces Spore Heart infection rate from +10 to +3/turn
- **Glow duration**: Each watered mushroom glows for 5 turns

### 1.5 Communication Conventions

How do NPCs in this region communicate?

**Verbal NPCs**:
- Scholar Aldric (speaks normally, weakly due to illness)

**Non-verbal NPCs**:
- Myconid Elder (colored spore puffs)
- Spore Mother (empathic spore waves)
- Sporelings (follow Mother's communication, simpler)

**Myconid Communication Vocabulary**:
```
- Blue spores = calm, neutral, informational
- Green spores = healing, cure, growth, offering help
- Yellow spores = caution, teaching, exchange, transaction
- Grey spores = sadness, fear, warning
- Red spores = anger, denial, refusal
- Dark/black spores = accusation, memory of death, "you killed our kind"
- Color swirls = complex emotions, directions, compound meanings
- Pulsing = emphasis (faster = stronger emotion)
- Spore density = volume/importance (thicker = more urgent)
```

**Spore Mother Empathic Communication**:
```
- Pain spike = sharp sensation through spore contact, player winces
- Waves of need = desperate grasping sensation, seeking help
- Gentle probing = curiosity, attention focusing on player
- Warmth flood = gratitude, relief, connection established
- Pressure surge = hostility, threat, spore burst incoming
- Weakening pulse = her illness, dying, needs heartmoss
```

**Communication Learning Curve**:
- **Myconids**: Aldric's journal mentions colored spores. Player can ask Aldric about "myconids" to unlock hints. Trial and error with offerings teaches the system.
- **Spore Mother**: Empathic communication is visceral and immediate - players feel what she feels. No learning curve needed, but interpretation requires attention.
- **Sporelings**: Mirror Mother's emotions in simpler form. Players who understand Mother understand sporelings.

---

## 2. Cross-Region Connections

### 2.1 Items This Region Imports

| Item | Source Region | Purpose Here | Urgency |
|------|---------------|--------------|---------|
| Ice Crystal | Frozen Reaches | Myconid payment for cure | Moderate (Aldric dying) |
| Gold | Civilized Remnants | Alternative Myconid payment | Moderate |
| Rare Mineral | Various | Alternative Myconid payment | Moderate |

### 2.2 Items This Region Exports

| Item | Destination Region | Purpose There | Acquisition |
|------|-------------------|---------------|-------------|
| Spore Heart | Meridian Nexus | Waystone fragment | Heal Spore Mother (she gifts it) |
| Breathing Mask | Any (universal) | Survive toxic air | Myconid Sanctuary (trust ≥ 0) |
| Spore Lantern | Any (universal) | Light without fire | Myconid Sanctuary (trust ≥ 0) |
| Mycology Skill | Any with fungi | Navigate spore areas, understand fungi | Aldric teaching (stabilized, trust ≥ 2, gift) |
| Spore Resistance | Any with spores | 50% infection reduction | Myconid teaching (trust ≥ 2, gift) |
| Mother's Heart | Various | Trophy (negative reputation) | Kill Spore Mother |

### 2.3 NPCs With Cross-Region Connections

| NPC Here | Connected To | Connection Type | Gossip Timing |
|----------|--------------|-----------------|---------------|
| Myconid Elder | All fungal creatures | Spore network - knows if player killed fungi | 1 turn |
| Aldric | Echo (Nexus) | Echo comments on abandoned commitment | 3-5 turns after death |
| Aldric | Civilized Remnants (scholars, Elara) | Scholar's fate becomes known via travelers | 25 turns |
| Spore Mother | Echo (Nexus) | Echo comments on killing or healing | 1 turn |

**Aldric Gossip Mechanism**: Merchant travelers passing through Nexus carry news of the scholar's fate to Civilized Remnants. If Aldric dies (abandoned commitment), word reaches scholarly circles and Elara in approximately 25 turns.

### 2.4 Environmental Connections

| Effect | Direction | Trigger | Timing |
|--------|-----------|---------|--------|
| Spore spread | From here → Nexus boundary | Spore Mother NOT healed + 100 turns | Turn 100: mild spores at Nexus boundary |
| Spore spread halt | N/A | Spore Mother healed | Immediate |

**Design Clarification**: Healing the Spore Mother alone is sufficient to halt ALL spore spread from this region. Waystone repair is NOT required to stop the spread - it has separate benefits (fast travel, Echo permanence). This is a local vs global distinction: healing the source fixes the problem at its origin.

### 2.5 Travel Times

| From | To | Turns | Notes |
|------|-----|-------|-------|
| Cavern Entrance | Nexus Chamber | 1 | Direct connection |
| Cavern Entrance | Luminous Grotto | 1 | Down |
| Luminous Grotto | Spore Heart | 1 | Down (spore damage in both) |
| Luminous Grotto | Myconid Sanctuary | 1 | Safe destination |
| Spore Heart | Deep Root Caverns | 1 | Down (requires mask + light) |
| Cavern Entrance → Nexus → Frozen Pass | ~6 turns | Via Nexus hub | Cross-region for ice crystal |
| Cavern Entrance → Nexus → Civilized Remnants | ~5 turns | Via Nexus hub | Cross-region for gold |

**Travel time assumptions**:
- Each location transition = 1 turn
- Spore zones deal damage during transit
- Deep Root Caverns held-breath timer starts on entry
- Waystone (if repaired) eliminates cross-region travel time

**Impact on commitments**:
- **Aldric's 50-turn timer**: Round-trip to Frozen Reaches (~12 turns) + exploration time leaves ~30 turns for local exploration. Comfortable if focused.
- **Spore Mother's 200-turn timer**: Extremely generous - no travel pressure at all.
- **Within-region exploration**: Full Fungal Depths can be explored in ~20 turns with equipment. Main constraint is infection accumulation, not time.

---

## 3. Instance-Specific Systems

### 3.1 NPC Services

| NPC | Service | Cost/Requirements | Trust Gate | Notes |
|-----|---------|-------------------|------------|-------|
| Aldric | Teach Mycology | Gift (research notes, rare herb) | Trust ≥ 2, stabilized state | Grants mycology skill |
| Myconid Elder | Cure Fungal Infection | Ice crystal, rare mineral, or gold | None | Full cure |
| Myconid Elder | Teach Spore Resistance | Gift + payment | Trust ≥ 2 | 50% infection reduction |

### 3.2 Companions

No companions can be recruited in this region.

**Companion behavior when entering this region:**

| Companion Type | Can Enter | Comfort Level | Notes |
|----------------|-----------|---------------|-------|
| Wolves | Yes | Uncomfortable | Take spore damage, refuse Spore Heart, can't enter Deep Roots |
| Salamander | Yes | Comfortable | Provides light in Deep Roots, Myconids fascinated (+1 trust) |
| Human (Sira) | Yes | Depends on gear | Takes spore damage without mask, tracking helps (-2 exposure) |

### 3.3 Commitments

What commitments can the player make in this region?

| Target NPC | Trigger | Timer | Timer Trigger | Hope Bonus | Fulfillment Flag |
|------------|---------|-------|---------------|------------|------------------|
| `npc_aldric` | "I'll find silvermoss" / "I'll help you" | 50 turns | `on_commitment` | +10 turns | `aldric_helped` |
| `npc_spore_mother` | "I'll find heartmoss" / "I'll heal her" | 200 turns | `on_commitment` | No (too powerful) | `spore_mother_healed` |

**Aldric Commitment Details:**

```python
CommitmentConfig = {
    "id": "commit_aldric_help",
    "target_npc": ActorId("npc_aldric"),
    "goal": "Give silvermoss to Aldric",
    "trigger_type": "on_commitment",  # Timer starts when player makes promise
    "trigger_phrases": [
        "I'll find silvermoss",
        "I'll help you",
        "I'll bring you the moss"
    ],
    "hope_extends_survival": True,
    "base_timer": 50,
    "survival_extension": 10,
    "fulfillment_flag": "aldric_helped"
}
```

**Withdrawal Response (Aldric)**:
- Dialog: "'I understand. The depths are treacherous. But... if you're still willing to try, there's something I didn't mention. The myconids have masks that filter spores. Earn their trust first.'"
- Gives item: Journal (if not already taken)
- Unlocks topic: Myconid equipment
- Can recommit: Yes

**Spore Mother Commitment Details:**

```python
CommitmentConfig = {
    "id": "commit_spore_mother_heal",
    "target_npc": ActorId("npc_spore_mother"),
    "goal": "Give heartmoss to Spore Mother",
    "trigger_type": "on_commitment",  # Timer starts when player makes promise
    "trigger_phrases": [
        "I'll find heartmoss",
        "I'll help her",
        "I will heal her"
    ],
    "hope_extends_survival": False,  # Too powerful to be affected by hope
    "base_timer": 200,  # Very long - she's not urgent
    "fulfillment_flag": "spore_mother_healed"
}
```

### 3.4 Gossip Sources

| Source | Content | Target NPCs | Delay | Confession Window |
|--------|---------|-------------|-------|-------------------|
| Spore network | Spore Mother healed | All fungal creatures | 1 turn | N/A |
| Spore network | Spore Mother killed | All fungal creatures | 1 turn | N/A |
| Direct to Echo | Spore Mother killed | Echo | 1 turn | N/A |

**Note**: The spore network propagates information to fungal creatures only. Echo receives major event gossip via separate `create_gossip()` call, not via network membership.

### 3.4.1 Fungal Death Mark (Not Gossip)

Killing any `fungal: true` creature does NOT use the gossip system. Instead, it leaves a mystical "death-mark" on the player that any fungal creature can sense instantly.

**Implementation**:
- Behavior trigger: On killing any actor with `fungal: true` property
- Effect: Set player flag `has_killed_fungi: true`
- Detection: Myconids check this flag on first interaction; if true, initial trust is -3 instead of 0
- Narrative: "The Myconid Elder recoils as you approach. Its spores shift to deep crimson. 'You carry the death of our kin upon you. We sense it.'"

This is simpler than gossip and fits the mystical nature of the fungal network - they sense the death directly, like smelling blood.

### 3.5 Branding/Reputation (if applicable)

N/A - This region does not have unique branding or reputation mechanics. The Myconid trust system is documented in Section 3.1 (NPC Services) and behavioral defaults.

### 3.6 Waystones/Endings (if applicable)

| Fragment | Location | Acquisition | Requirements |
|----------|----------|-------------|--------------|
| Spore Heart | Spore Heart (location) | Gift from healed Spore Mother | Apply heartmoss to heal her |

**Note**: The Spore Heart waystone fragment is granted when the Spore Mother is healed (positive outcome). A separate item, Mother's Heart, is a trophy dropped if the Spore Mother is killed (negative outcome with reputation consequences). These are mutually exclusive - you can only obtain one.

### 3.7 Skills

What skills can be learned in this region?

| Skill | Teacher | Requirements | Effects |
|-------|---------|--------------|---------|
| Mycology | Aldric | Stabilized state, trust ≥ 2, gift item | Navigate spore areas, understand fungal creatures |
| Spore Resistance | Myconid Elder | Trust ≥ 2, gift + payment | 50% reduction in fungal infection acquisition |

**Skill Permanence**: Both skills are permanent once learned - they remain available throughout the game.

### 3.8 Permanent Consequences

Document actions in this region that permanently lock content or endings:

| Action | Consequence | Affected Content | Reversible? |
|--------|-------------|------------------|-------------|
| Kill Spore Mother | Spore crystal becomes permanently unobtainable | Myconid trust -5, permanent spore spread, ending impacts | No |
| Kill Aldric (by neglect) | Lose mycology teacher and companion potential | Cannot learn Mycology skill, cannot recruit Aldric | No |
| Kill any fungal creature before meeting Myconids | Initial Myconid trust -3 | Harder to access equipment/services, must rebuild trust | Partial - can rebuild trust but starts at penalty |

**Permanent Blockers**:

```
Permanent Blocker: Spore Mother Death
- Trigger: Player kills Spore Mother (health ≤ 0)
- Locks: Spore crystal (unique item), peaceful Fungal Depths ending, Myconid alliance
- Affects endings: Likely blocks "Triumphant" ending (requires healing major threats)
- Warning signs: Spore Mother is extremely difficult to kill (200 HP, 10 HP/turn regen, brutal attacks), Aldric warns against violence, empathic communication conveys suffering
```

```
Permanent Blocker: Aldric Death
- Trigger: Aldric's timer expires OR health ≤ 0
- Locks: Mycology skill, Aldric as companion
- Affects endings: May impact "Successful" ending (requires saving key NPCs)
- Warning signs: Aldric's visible deterioration, 50-turn timer, clear symptoms of infection
```

**Conditional Locks**:

```
Conditional Lock: Myconid Services
- Required: Do not kill any fungal creatures before first Myconid interaction
- Lost if: Player has `has_killed_fungi` flag when meeting Myconid Elder
- Recovery: Partial - trust starts at -3 instead of 0, can be rebuilt through meaningful actions but requires extra work
```

```
Conditional Lock: Deep Root Caverns Access
- Required: Breathing mask from Myconids (trust ≥ 0)
- Lost if: Myconid trust < 0 (blocked from taking mask)
- Recovery: Yes - rebuild trust to 0 or higher through meaningful actions
```

---

## 4. Region Hazards

This section documents hazards that threaten the player. Hazards can be **environmental** (cold, drowning, infection) or **social** (reputation damage, branding, exile). Most regions have one type; some may have both.

**Hazard Type**: Environmental

For **environmental hazard regions** (Frozen Reaches, Fungal Depths, Sunken District): Fill in Sections 4.1 and 4.2 with physical hazards.

### 4.1 Hazard Zones

Define the hazard conditions in this region (environmental OR social):

**Environmental zones**:

| Zone Type | Locations | Effects | Mitigation |
|-----------|-----------|---------|------------|
| Safe | `cavern_entrance`, `myconid_sanctuary` | No infection progression | N/A |
| Medium Spores | `luminous_grotto` | +5 infection/turn | Breathing mask (full), spore resistance (50%) |
| High Spores | `spore_heart` | +10 infection/turn (+3 with safe_path_known) | Mask (full), safe_path (70% reduction) |
| Toxic Air | `deep_root_caverns` | Cannot breathe (12 turn limit, then 20 damage/turn) | Breathing mask (required) |
| Darkness | `deep_root_caverns` | Cannot see items or navigate precisely | Light source (required) |

### 4.2 Conditions Applied

What conditions can players acquire in this region? Include both environmental and social conditions.

**Environmental conditions**:

| Condition | Source | Severity Progression | Treatment |
|-----------|--------|---------------------|-----------|
| Fungal Infection | Spore zones, sporeling attacks | +5 or +10/turn (zone), +10-25 (attacks) | Silvermoss (-40), Myconid cure (full) |
| Held Breath | Toxic air (no mask) | +1/turn, max 12 | Exit toxic area, equip mask |

**Fungal Infection System:**

```python
ConditionInstance = {
    "type": ConditionType.FUNGAL_INFECTION,
    "severity": 0,  # 0-100 scale
    "acquired_turn": <turn_number>,
    "progression_rate": 5,  # Base per turn in medium spores
}
```

**Severity Effects:**
- 0-19: No effects (uncomfortable)
- 20-39: Occasional coughing, 1 damage/turn
- 40-59: Visible spore patches, 2 damage/turn
- 60-79: Difficult breathing, 3 damage/turn
- 80-99: Immobile, near death, 4 damage/turn
- 100: Death

**Held Breath System:**

```python
ConditionInstance = {
    "type": ConditionType.HELD_BREATH,
    "current": 0,  # 0-12 scale
    "max": 12,
    "warning_at": 8,  # "Your lungs are burning"
    "critical_at": 10,  # "You're suffocating!"
    "damage_after_max": 20  # Per turn after turn 12
}
```

### 4.3 Companion Restrictions

| Companion Type | Can Enter | Comfort Level | Notes |
|----------------|-----------|---------------|-------|
| Wolves | Yes (partial) | Uncomfortable | Take spore damage, refuse to enter Spore Heart or Deep Roots |
| Salamander | Yes | Comfortable | Provides light in Deep Roots, Myconids +1 initial trust |
| Human (Sira) | Yes (with mask) | Uncomfortable | Tracking skill provides -2 spore exposure |
| Human (Aldric) | No | N/A | Too sick to move |

---

## 5. Behavioral Defaults

### 5.1 NPC Behavioral Defaults

```
- Default disposition toward player: Neutral (Myconids), Hostile (Spore Mother/sporelings), Friendly (Aldric)
- Reaction to player brands: N/A (no brand system)
- Reaction to gossip: Myconids check has_killed_fungi on first interaction (-3 trust if true)
- Reaction to companions:
  - Myconids: Nervous around wolves (-1 trust), fascinated by salamander (+1 trust)
  - Spore Mother: Attacks wolves, curious about salamander
- Reaction to conditions:
  - Aldric: Comments if player is visibly infected
  - Myconids: Offer cure service if player has visible infection
```

### 5.2 Location Behavioral Defaults

```
- Environmental zone: Spore-level based (see Section 4.1)
- Lighting: Variable (dim in most areas, dark in Deep Roots)
- Turn phase effects: Infection progression based on zone
- Combat: Spore Mother + sporelings in Spore Heart only
```

### 5.3 Item Behavioral Defaults

```
- Organic items: May be affected by fungal growth over time
- Myconid items: Require trust ≥ 0 to take
- Curative items: Auto-apply when given to relevant NPC
- Water-interaction items: Mushrooms respond to water in puzzle
```

### 5.4 Group/Pack Dynamics

**Skip this section if N/A**: Most regions don't have group dynamics. Only fill this in if the region has NPCs that operate as coordinated groups (wolf packs, spider swarms, myconid colonies, etc.).

If this region has NPCs that operate in groups (packs, swarms, crews), document their collective behavior:

| Group | Leader | Followers | State Mirroring | Location Mirroring |
|-------|--------|-----------|-----------------|-------------------|
| Sporeling Pack | npc_spore_mother | [npc_sporeling_1, npc_sporeling_2, npc_sporeling_3] | Yes | No (bound to Spore Heart) |

**State mirroring**: Yes - sporelings adopt Spore Mother's state machine state (hostile/wary/allied/dead)

**Location mirroring**: No - sporelings cannot leave Spore Heart. They are bound to Mother's presence and would wither if separated.

**Follower respawn**: No - sporelings are unique individuals, not generic spawn.

**Leader death effects**:
- Sporelings become `confused` (new state, not hostile)
- They wander aimlessly, do not attack
- Eventually wither (10 turns after Mother's death)
- Killing confused sporelings still sets `has_killed_fungi` flag

**Communication cascade**:
- Sporelings mirror Mother's empathic communication in simpler form
- When Mother feels pain, sporelings emit distress puffs
- When Mother feels gratitude, sporelings brighten
- This helps players understand Mother's emotions through the sporelings' reactions

---

## 6. Generative Parameters

This section guides LLM authoring to expand the region.

### 6.1 Location Generation

**Generation scope**: Limited

The 5 core locations are complete, but 1-3 additional locations could add exploration depth:

**Location Template: Fungal Side Passage**
- Purpose: Exploration, environmental storytelling, minor loot
- Environmental zone: Medium spores (same as Luminous Grotto)
- Typical features: Strange fungal growths, dead explorers, bioluminescence
- Connection points: Could branch from `luminous_grotto` or `cavern_entrance`
- Hazards: Spore pockets, unstable ground
- Content density: Sparse (1-2 items, no NPCs)

**Location Template: Myconid Outer Ring**
- Purpose: Atmosphere, additional Myconid NPCs for flavor
- Environmental zone: Safe (Myconid-filtered)
- Typical features: Geometric patterns, silent communion circles
- Connection points: Could extend from `myconid_sanctuary`
- Hazards: None
- Content density: Moderate (0-1 items, 1-2 background Myconids)

**What NOT to generate**: Additional safe zones (only hot springs and sanctuary should be safe), surface connections (this is underground), combat encounters (only Spore Mother area has combat).

### 6.2 NPC Generation

**Generation scope**: Limited

**NPC Template: Background Myconid**
- Role: Silent observer, flavor
- Typical count: 1-2 in sanctuary or generated outer areas
- Services: None (Elder handles all services)
- Trust thresholds: N/A
- Disposition: Neutral
- Dialog topics: None (only Elder speaks)
- Mechanical hooks: None

**NPC Template: Dead Explorer**
- Role: Environmental storytelling (corpse, not alive)
- Typical count: 0-1 in generated passages
- Contains: Minor loot, journals with hints
- Notes: NOT an NPC mechanically - a searchable container

### 6.3 Item Generation

**Generation scope**: Limited

**Item categories**:
```
- Trade goods: Rare minerals, fungal samples
- Environmental props: Bones, abandoned equipment, fungal growths
- Flavor loot: Explorer journals, broken tools, coins
- Consumables: None (silvermoss is unique, don't duplicate)
```

**Constraints**: Do NOT generate additional curative items. Silvermoss and heartmoss are deliberately limited. Gift items for Aldric (research notes) should be rare - only one per region.

### 6.4 Atmospheric Details

**Environmental details**:
```
- Sounds: Dripping water, distant rumbling, Spore Mother's breathing, spore puffs
- Visual motifs: Bioluminescence (blue, green, gold, violet), organic textures, geometric Myconid patterns
- Tactile sensations: Damp air, spongy ground, warmth in Spore Heart, cold in Deep Roots
- Smells: Musty decay, sweet earthy scent, sulfur near pools
```

*Note: NPC communication vocabularies (Myconid spore colors, Spore Mother empathic communication) are documented in Section 1.5 Communication Conventions.*

**State-dependent variations**:
```
- Infection mild: "You cough occasionally"
- Infection moderate: "Spore patches are visible on your skin"
- Infection severe: "Every breath is a struggle"
- Spore Mother allied: "The air here is clean and easy to breathe"
- Spore Mother dead: "The organic walls are still. Silent. Decaying."
```

### 6.5 Density Guidelines

| Area Type | NPCs | Items | Locations | Atmosphere |
|-----------|------|-------|-----------|------------|
| Entry (cavern_entrance) | 1 (Aldric) | 2-3 | 0 | Damp, hopeful, urgent |
| Exploration (luminous_grotto) | 0 | 6-8 (puzzle items) | 0-1 branches | Mysterious, dangerous beauty |
| Confrontation (spore_heart) | 4 (Mother + 3 sporelings) | 0 | 0 | Threatening, empathic |
| Service (myconid_sanctuary) | 1 (Elder) | 2 (equipment) | 0-1 outer ring | Orderly, alien, patient |
| Dangerous (deep_root_caverns) | 0 | 2 | 0 | Dark, ancient, lethal |

### 6.6 Thematic Constraints

```
Tone: Symbiosis, decay, consequence, communication
Common motifs: Organic pulsing, spore communication, healing vs killing, patience

MUST include:
- Consequences for violence (spore network remembers)
- Equipment gates (mask, light required for Deep Roots)
- Information breadcrumbs (dialog reveals next steps)
- Time pressure from Aldric

MUST avoid:
- Easy combat victories (Spore Mother fight is brutal)
- Duplicate curative items (silvermoss is limited)
- Surface connections (underground only)
- Consequence-free violence
```

### 6.7 Mechanical Participation Requirements

```
Required systems (generated content MUST use):
- [x] Fungal infection condition (all spore zones)
- [x] Spore levels (location-based)
- [x] Trust system (Myconid interactions)
- [x] has_killed_fungi flag check

Optional systems (use if thematically appropriate):
- [x] Services (Myconid services)
- [x] Commitments (Aldric, Spore Mother)
- [x] Skills (mycology, spore resistance)
- [ ] Puzzles (light puzzle in Grotto only)
```

---

## 7. LLM Narration Guidance

### 7.1 Region Traits

```
Environmental:
- "damp stone walls glistening with moisture"
- "soft bioluminescent glow in multiple colors"
- "thick spore haze catching the light"
- "organic surfaces that pulse like breathing"
- "crystal-clear pools reflecting impossible colors"
- "absolute darkness that swallows light"

Emotional:
- "tension between decay and growth"
- "alien patience (Myconids)"
- "desperate pain (Spore Mother)"
- "scholarly hope despite illness (Aldric)"

Historical:
- "dead explorers claimed by fungus"
- "ancient roots from unimaginable heights"
- "blight that spread from somewhere else"
```

**Location-Specific Traits:**

**cavern_entrance**:
- "cool air rising from below"
- "small campfire with worn bedroll"
- "distant dripping echoes"

**luminous_grotto**:
- "soft multicolored glow"
- "crystal-clear pool reflecting light"
- "ceiling too dark to read"

**spore_heart**:
- "pulsing organic walls"
- "thick golden spore haze"
- "rhythmic breathing sounds"
- "warmth that feels alive"

**myconid_sanctuary**:
- "orderly rings of mushroom folk"
- "silent communication through spore puffs"
- "geometric arrangement of everything"

**deep_root_caverns**:
- "absolute darkness beyond your light"
- "roots as thick as trees"
- "ancient silence"
- "cold that seeps into bones"

### 7.2 State Variants

| State | Trigger | Narration Change |
|-------|---------|------------------|
| `infection_mild` | Severity 20-39 | "You cough occasionally. Spores tickle your lungs." |
| `infection_moderate` | Severity 40-59 | "Pale patches of fungal growth are visible on your skin." |
| `infection_severe` | Severity 60-79 | "Every breath is a struggle. Your vision blurs occasionally." |
| `infection_critical` | Severity 80+ | "You can barely stand. The infection has nearly consumed you." |
| `aldric_stabilized` | Given silvermoss | "Color returns to Aldric's cheeks. He can sit up now." |
| `aldric_recovering` | Fully cured | "Aldric stands straighter, his strength returning." |
| `spore_mother_wary` | 3 turns no attack | "The Spore Mother watches you. The sporelings hesitate." |
| `spore_mother_allied` | Given heartmoss | "The organic walls pulse with healthy rhythm. The air is clean." |
| `spore_mother_dead` | Killed | "The organic walls are still and decaying. Sporelings wander aimlessly." |
| `safe_path_known` | Puzzle complete | "You know where the clean air pockets are." |

### 7.3 NPC Description Evolution

| NPC | State | Traits |
|-----|-------|--------|
| Aldric | critical | "pale", "dark circles", "fungal patches visible", "labored breathing", "can barely stand" |
| Aldric | stabilized | "color returning", "can sit up", "breathing easier", "hopeful eyes" |
| Aldric | recovering | "standing straighter", "strength returning", "grateful smile" |
| Spore Mother | hostile | "massive", "pulsing weakly", "dark blight veins", "pain radiates" |
| Spore Mother | wary | "watching", "not attacking", "curiosity through spores" |
| Spore Mother | allied | "vibrant bioluminescence", "healthy rhythm", "gratitude through spores" |
| Myconid Elder | neutral | "weathered cap", "age-rings", "patient observation" |
| Myconid Elder | trusting | "spores shift warmly", "welcoming posture" |
| Myconid Elder | distrusting | "dark accusatory spores", "closed posture", "wary" |

---

## 8. Validation Checklist

### 8.1 Completeness

- [x] All required entities from overview are listed
- [x] All cross-region dependencies documented
- [x] All instance-specific systems addressed
- [x] Environmental rules fully specified (spore zones, toxic air, darkness)
- [x] Behavioral defaults cover all entity types

### 8.2 Consistency

- [x] Location IDs follow naming convention
- [x] NPC trust thresholds are reasonable
- [x] Commitment timers are fair (Aldric 50+10, Spore Mother 200)
- [x] Companion restrictions match `cross_region_dependencies.md`
- [x] Gossip timing is consistent (spore network is 1 turn)

### 8.3 Cross-Region Verification

- [x] All imported items are exported from documented source regions (ice crystal from Frozen Reaches, gold from Civilized Remnants)
- [x] All exported items are imported by documented destination regions (breathing mask, spore lantern, skills are universal)
- [x] Gossip timing matches in both source and destination region docs (1 turn spore network)
- [x] NPC connections documented on both sides of relationship (Echo comments on Aldric/Spore Mother outcomes)
- [x] Skill dependencies are achievable (can reach Aldric and Myconids before deadlines)
- [x] Permanent consequences don't create impossible states (Spore Mother death blocks only optional content)

### 8.4 Generative Readiness

- [x] Location generation seeds provided with Limited scope
- [x] NPC generation seeds provided (background Myconids, dead explorers)
- [x] Item generation constrained (no duplicate curatives)
- [x] Density guidelines provide clear targets
- [x] Thematic constraints prevent off-tone content

---

## Appendix A: Timer Trigger Types Reference

Commitment timers can start in different ways. Use this reference when documenting commitments in Section 3.3.

| Trigger Type | When Timer Starts | Example | Notes |
|--------------|-------------------|---------|-------|
| `on_commitment` | When player makes promise | Aldric: "Find silvermoss" | Most common. Timer starts when player explicitly commits. |
| `on_room_entry` | When player enters location | Garrett drowning | Timer already running. Player walks into crisis. |
| `on_first_encounter` | When player first meets NPC | Delvan bleeding | Timer starts on discovery, before commitment made. |
| `global_turn` | At specific game turn | Spore spread at turn 50 | Environmental spread timers. Not tied to player action. |
| `none` | Never | Guardian repair | No time pressure. Player can complete at leisure. |

**Important Distinctions:**

- **on_commitment vs on_first_encounter**: Both involve meeting an NPC, but `on_commitment` waits for player's promise while `on_first_encounter` starts immediately on discovery.

- **Hope bonus behavior**:
  - With `on_commitment` triggers: Hope bonus extends timer from commitment point
  - With `on_room_entry` or `on_first_encounter`: Hope bonus typically extends NPC survival, not commitment deadline

**Fungal Depths Commitment Examples:**

Both commitments in this region use `on_commitment` triggers:

```python
# Aldric commitment - standard on_commitment
CommitmentConfig = {
    "trigger_type": "on_commitment",
    "base_timer": 50,  # Starts when player says "I'll help"
    "hope_extends_survival": True,
    "hope_bonus": 10
}

# Spore Mother commitment - on_commitment without hope
CommitmentConfig = {
    "trigger_type": "on_commitment",
    "base_timer": 200,  # Starts when player makes promise
    "hope_extends_survival": False,  # Too powerful for hope
}
```

---

## Appendix B: Infrastructure System Integration

### B.1 Fungal Infection Condition

Uses the Condition System from `infrastructure_detailed_design.md`:

```python
ConditionInstance = {
    "type": ConditionType.FUNGAL_INFECTION,
    "severity": 0,
    "acquired_turn": <turn_number>,
    "progression_rate": 5,  # Modified by zone
}
```

### B.2 Aldric State Machine

```python
StateMachineConfig = {
    "states": ["critical", "stabilized", "recovering", "dead"],
    "initial": "critical",
    "transitions": {
        "critical->stabilized": {"trigger": "given_silvermoss", "effects": ["severity-40", "progression_rate=0"]},
        "stabilized->recovering": {"trigger": "given_second_silvermoss OR myconid_cure"},
        "critical->dead": {"trigger": "health<=0 OR turn>=death_turn"},
        "stabilized->dead": {"trigger": "health<=0"}
    }
}
```

### B.3 Spore Mother State Machine

```python
StateMachineConfig = {
    "states": ["hostile", "wary", "allied", "dead"],
    "initial": "hostile",
    "transitions": {
        "hostile->wary": {"trigger": "player_present_3_turns_no_attack"},
        "wary->hostile": {"trigger": "player_attacks"},
        "hostile->allied": {"trigger": "given_heartmoss"},
        "wary->allied": {"trigger": "given_heartmoss"},
        "hostile->dead": {"trigger": "health<=0"}
    }
}
```

### B.4 Myconid Trust

Uses TrustState from `infrastructure_detailed_design.md`:

```python
TrustState = {
    "current": 0,  # Or -3 if has_killed_fungi
    "floor": -5,
    "ceiling": 5,
    "recovery_cap": 1  # Per visit
}
```

---

## Appendix C: Data Structures

### C.1 Aldric Actor Definition

```json
{
  "id": "npc_aldric",
  "name": "Scholar Aldric",
  "description": "A frail scholar with pale skin and dark circles under his eyes. Fungal patches are visible on his neck and arms.",
  "properties": {
    "health": 40,
    "max_health": 100,
    "mobility": "immobile",
    "mobility_reason": "The infection has spread too far. Even a few steps leave him gasping.",
    "state_machine": {
      "states": ["critical", "stabilized", "recovering", "dead"],
      "initial": "critical"
    },
    "death_turn_threshold": 50,
    "dialog_topics": ["infection", "research", "spore_mother", "sporelings", "myconids", "safe_path", "mushrooms"]
  },
  "conditions": {
    "fungal_infection": {
      "severity": 80,
      "damage_per_turn": 2,
      "progression_rate": 2
    }
  },
  "flags": {},
  "location": "cavern_entrance"
}
```

### C.2 Spore Mother Actor Definition

```json
{
  "id": "npc_spore_mother",
  "name": "Spore Mother",
  "description": "A massive fungal creature, part plant and part something else entirely. Her cap spreads wide, pulsing weakly with sickly bioluminescence.",
  "properties": {
    "health": 200,
    "max_health": 200,
    "fungal": true,
    "pack_id": "sporeling_pack",
    "pack_role": "alpha",
    "regeneration": 10,
    "state_machine": {
      "states": ["hostile", "wary", "allied", "dead"],
      "initial": "hostile"
    },
    "communication": "empathic_spores"
  },
  "conditions": {
    "fungal_blight": {
      "severity": 70,
      "progression_rate": 1
    }
  },
  "attacks": [
    {"name": "tendril_lash", "damage_min": 20, "damage_max": 20, "accuracy": 75},
    {"name": "spore_burst", "damage_min": 15, "damage_max": 15, "accuracy": 90, "applies_condition": {"type": "fungal_infection", "severity": 25}}
  ],
  "flags": {},
  "location": "spore_heart"
}
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2025-12-11 | Initial draft from template |
| 0.2 | 2025-12-11 | Updated to match revised template: Added Hazard Type field to Section 4, Timer Trigger column to Section 3.3 commitments, renumbered collection quests to skills (3.7), added Section 3.8 Permanent Consequences, added guidance to Section 5.4 Group Dynamics, added Section 8.3 Cross-Region Verification, renumbered old 8.3 to 8.4, added Appendix A Timer Trigger Types Reference |
| 0.3 | 2025-12-11 | Phase 2 consistency fixes: Fixed Section 3.6 to correctly document Spore Heart waystone fragment (FD-1), clarified Aldric timer as on_commitment not game start (FD-3), clarified Spore Mother condition describes spreading influence not self-damage (FD-2) |
