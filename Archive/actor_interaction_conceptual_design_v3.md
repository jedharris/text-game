# Actor Interaction System - Conceptual Design v3

## Document Purpose

This document describes the **conceptual design** for actor interactions in the text adventure engine. It presents a unified framework that **equally supports combat, cooperation, environmental challenges, and social dynamics**, treating all forms of actor interaction as first-class gameplay.

**Key Evolution from v2**: This version incorporates all design critique resolutions, including terminology standardization, explicit turn phase ordering, and clarifications on pack coordination, range handling, and property conventions.

**Audience**: Game authors who want to understand how to create games with rich actor interactions—not just combat, but healing, teaching, rescue, trading, domestication, and environmental challenges.

**Companion Documents**:
- [Actor Interaction Design Decisions](actor_interaction_design_decisions.md) - Architectural decisions and rationale
- [Actor Interaction Simplified Cases](actor_interaction_simplified_cases.md) - Eight author-friendly scenarios
- [Actor Interaction Evaluation](actor_interaction_evaluation.md) - Feature assessment and recommendations

---

## Design Goals

### 1. Combat and Non-Combat Interactions Are Equal

**Goal**: The system treats combat, cooperation, rescue, teaching, and social interactions as equally important gameplay modes. Combat is one interaction type among many.

**How**:
- **Generic condition system**: Works for poison (combat), disease (environmental), exhaustion (rescue), hunger (survival)
- **Services framework**: NPCs can heal, teach, trade, escort, repair using same pattern
- **Environmental effects**: Drowning, freezing, toxic air use same mechanisms as combat damage
- **Relationship tracking**: Trust, gratitude, fear affect all interactions, not just combat

**Supported Interaction Types**:
- **Combat**: Attack, defend, flee, use tactics
- **Medical**: Heal wounds, cure diseases, treat conditions, stabilize dying actors
- **Educational**: Teach skills, share knowledge, identify plants/creatures
- **Social**: Build trust, earn gratitude, inspire fear, domesticate creatures
- **Commercial**: Trade goods, barter services, negotiate prices
- **Cooperative**: Rescue trapped actors, escort vulnerable NPCs, coordinate actions
- **Environmental**: Navigate hazards, manage breath/temperature, use terrain
- **Technical**: Repair constructs, activate mechanisms, program automata

### 2. Maximize Author Capability and Player Agency

**Goal**: Authors can create any interaction between actors without engine modifications. Players have agency to solve problems through multiple paths.

**How**: All interaction mechanics emerge from:
- **Properties** on actors and items (flexible, author-defined)
- **Behaviors** that respond to events (modular, stackable)
- **Existing commands** (give, approach, examine, use) that trigger interactions
- **Spatial system** (positioning, cover, environmental effects)

**Examples**:
- **Multiple solutions**: Cure poison via healer service, antidote herb, or healing spell
- **Emergent gameplay**: Feeding wolves creates domestication through relationship tracking
- **Environmental tactics**: Use terrain for cover, avoid hazards, exploit enemy weaknesses
- **Social paths**: Build trust to unlock services, earn gratitude for rewards

### 3. Treat All Actors Uniformly

**Goal**: Player, NPCs, creatures, and constructs are the same fundamental entity type, differing only in properties and behaviors.

**How**: Every actor has:
- **Core structural fields**: id, name, location, inventory (same for everyone)
- **Properties dict**: Flexible storage for all characteristics
- **Behaviors list**: Modular event handlers that can be stacked

**What This Enables**:
- **Living creatures** (health, hunger, morale) vs **constructs** (health, power) vs **undead** (no breath needed)
- **Different body forms**: Humanoid, quadruped, arachnid, construct—each with appropriate capabilities
- **Uniform treatment**: All actors can have conditions, relationships, needs, skills

### 4. Spatial Integration Creates Tactical Depth

**Goal**: The spatial positioning system enhances all interactions, not just combat.

**How**:
- **Positioning matters**: Cover during combat, proximity for disease spread, location for environmental hazards
- **Environmental properties**: Parts can be breathable/toxic, covered in webs, pressurized, temperature-controlled
- **Distance and reach**: Interactions check if actors can reach each other based on focus and position
- **Posture tracking**: Cover, hiding, climbing affects available interactions

**Examples**:
- **Combat**: Take cover behind pillars, use high ground, corner enemies
- **Environmental**: Breathable air pockets in flooded tunnels, spore concentrations vary by part
- **Disease**: Contagion spreads to focused_on actors (interaction range)
- **Tactics**: Spiders get bonuses on webs, guards patrol between parts

### 5. Progressive and Emergent Gameplay

**Goal**: Simple properties combine to create complex scenarios. Authors control depth by choosing which features to use.

**How**:
- **Start minimal**: Health alone enables basic interactions
- **Add incrementally**: Layer on conditions, relationships, skills only as needed
- **Emergent combinations**: Simple mechanics interact in rich ways
- **No forced complexity**: Use only what your game needs

**Examples**:
- **Basic**: Give food to hungry actor, receive gratitude
- **Layered**: Repeated feeding → relationship threshold → domestication → companion follows you
- **Complex**: Rescue drowning sailor (breath tracking) + hypothermia (temperature) + exhaustion (can't swim) = multi-threat scenario
- **Minimal viable**: Health + attacks + conditions supports rich combat without equipment, skills, or vitals

---

## Core Concepts

### Actors Are Entities with Body, Mind, and State

Every actor is defined by three categories of properties:

#### Physical State (Body & Vitals)

**Body Characteristics** - What the actor is:
```json
"body": {
  "form": "humanoid|quadruped|arachnid|construct|serpent",
  "material": "flesh|stone|clockwork|spirit",
  "limbs": ["arms", "legs"],
  "features": ["teeth", "claws", "fangs", "spinnerets"],
  "size": "tiny|small|medium|large|huge",
  "movement": ["walk", "climb", "swim", "fly"]
}
```

**Vital Stats** - Current condition:
```json
"health": 80,
"max_health": 100,
"breath": 45,        // Optional - only for drowning scenarios
"max_breath": 60
```

**Conditions** - Temporary states affecting capabilities:
```json
"conditions": {
  "poison": {
    "severity": 40,
    "damage_per_turn": 2,
    "duration": 20,
    "effect": "agility_reduced"
  },
  "entangled": {
    "severity": 60,
    "effect": "cannot_move"
  }
}
```

**Note**: Items have the `cures` property (e.g., `"cures": ["poison"]`), not conditions. Conditions describe what they are, items describe what they can cure.

**Condition Stacking**: When applying a condition that the actor already has, severities are added (not replaced):
- Existing poison severity 40 + new poison severity 30 = total severity 70
- Severity is capped at 100
- Duration takes the longer of existing or new duration
- This creates meaningful cumulative danger from multiple attacks

**Consumable Items**: Items with `"consumable": true` are automatically consumed when used for treatment. The treatment behavior handles consumption internally—no author code required.

**Immunities and Resistances**:
```json
"immunities": ["poison", "disease", "bleeding"],
"resistances": {
  "cold": 50,        // 50% damage reduction
  "disease": 30
}
```

**Resistance Calculation**:
- `resistance_value` is percentage (0-100)
- Actual damage/severity = `base_value * (1 - resistance_value/100)`
- Round up (ceiling) for severity increases
- Round standard for damage application
- Minimum 0 (resistance can negate entirely if 100%)
- Example: Base severity increase 15, resistance 30% → 15 * 0.7 = 10.5 → 11

#### Mental/AI State

**Disposition and Morale**:
```json
"ai": {
  "disposition": "friendly|neutral|hostile|desperate|grateful",
  "morale": 80,
  "flee_threshold": 20
}
```

**Note**: Use `disposition` to express actor attitude. Examples vary across the interaction spectrum: "friendly" allies, "neutral" merchants, "hostile" threats, "desperate" hungry wolves, "grateful" rescued NPCs.

**Needs and Goals**:
```json
"needs": {
  "hungry": true,
  "trapped": false
},
"destination": "loc_town",    // For escort missions
"needs_escort": true
```

**Pack/Group Coordination**:
```json
"pack_id": "winter_wolves",
"pack_role": "alpha|follower",
"follows_alpha": "npc_wolf_alpha"
```

**Pack Coordination**: During the NPC action phase, followers with `pack_role: "follower"` copy the `disposition` property from their alpha. This enables coordinated behavior: if the alpha becomes hostile, the pack attacks; if the alpha is domesticated (disposition becomes "friendly"), the pack becomes friendly too.

#### Capabilities and Services

**Combat Abilities** (one of many interaction types):
```json
"attacks": [
  {
    "name": "bite",
    "damage": 15,
    "type": "piercing",
    "range": "touch",
    "applies_condition": {
      "name": "bleeding",
      "severity": 30
    }
  },
  {
    "name": "tackle",
    "damage": 8,
    "range": "touch",
    "effect": "knockdown"
  }
],
"armor": 5
```

**Note on Armor**: Armor reduces all incoming attack damage by a flat amount. Attack `type` (piercing, slashing, etc.) is only descriptive in Phase 1. Future phases could add armor type matching, but that's deferred for simplicity.

**Note on Range**: The `range` property on attacks (and other interactions) is for author/behavior interpretation, not engine enforcement. Behaviors use range to select appropriate actions (e.g., NPC chooses "charge" attack at "near" range vs "bite" at "touch" range). The engine does not validate or enforce range constraints. This same concept applies to medical treatment, feeding, services—any actor-to-actor interaction.

**Services Offered** (non-combat interactions):
```json
"services": {
  "cure_poison": {
    "accepts": ["rare_herbs", "gold"],
    "amount_required": 1,
    "cure_amount": 100
  },
  "teach_herbalism": {
    "accepts": ["gold"],
    "amount_required": 50,
    "grants": "knows_herbalism"
  },
  "trading": {
    "accepts": ["gold"],
    "sells": ["health_potion", "antidote"]
  }
}
```

**Note on Service Payment**: The default service behavior uses simple matching rules:
- **Exact match required**: Payment must meet `amount_required`
- **Overpayment accepted**: No change given (simplifies implementation)
- **Underpayment rejected**: Service declines with message

Authors wanting complex economics (change, partial services, negotiation) can override the default service behavior.

**Knowledge and Skills**:
```json
"knows": ["herbalism", "swimming", "medicine"],
"knowledge": {
  "mansion_layout": true,
  "ancient_history": true
}
```

#### Social State

**Relationships** (progressive bonds):
```json
"relationships": {
  "player": {
    "trust": 3,
    "gratitude": 5,
    "fear": 0
  }
}
```

**Note on Relationships**: Relationship keys (like "player" above) are created dynamically when first needed. An empty `{}` means no relationships yet. When a behavior increments gratitude toward a new actor, the relationship entry is created automatically.

### Interaction Types: Beyond Combat

The system supports diverse interaction categories:

#### 1. Medical Interactions

**Healing Wounds**:
- Apply bandages to stop bleeding
- Use healing potions to restore health
- Rest to recover naturally

**Curing Conditions**:
- Give antidote to cure poison
- Healer service removes disease
- Time-based condition expiration

**Stabilizing Dying Actors**:
- Treat critical wounds before they die
- Maintain breath for drowning victims
- Warm hypothermic actors

**Examples**:
- Bandage bleeding merchant (UC6)
- Cure scholar's fungal infection (UC1)
- Give healing potion to injured companion

#### 2. Educational Interactions

**Teaching Skills**:
- Pay healer to learn herbalism
- Practice with mentor to improve combat
- Study with scholar to gain knowledge

**Sharing Knowledge**:
- NPC identifies mysterious plant
- Construct provides mansion layout
- Merchant warns about hazards

**Learning Through Experience**:
- Identify plants after being taught
- Remember lessons in future encounters

**Examples**:
- Learn herbalism from healer (UC4)
- Ask construct about mansion history (UC8)
- Study plant identification

#### 3. Social Interactions

**Building Trust**:
- Help NPC before asking favors
- Repeated positive interactions
- Keep promises and agreements

**Earning Gratitude**:
- Rescue trapped or injured NPCs
- Give gifts without expecting return
- Cure diseases or heal wounds

**Domestication**:
- Feed hungry creatures repeatedly
- Show non-aggression over time
- Build bond until creature follows you

**Examples**:
- Feed wolves to domesticate them (UC3)
- Rescue sailor to earn ally (UC5)
- Treat merchant to unlock discounts (UC6)

#### 4. Commercial Interactions

**Trading Goods**:
- Buy healing items from merchant
- Sell found treasures for gold
- Exchange rare herbs for services

**Bartering Services**:
- Pay healer with herbs instead of gold
- Trade knowledge for healing
- Exchange escort for reward

**Dynamic Pricing**:
- Trust affects prices
- Gratitude unlocks discounts
- Reputation opens new inventory

**Examples**:
- Trade with injured merchant (UC6)
- Barter herbs for poison cure (UC4)
- Buy supplies before dangerous journey

#### 5. Cooperative Interactions

**Rescue Missions**:
- Save drowning sailor
- Free trapped actors
- Escort injured NPCs to safety

**Escorting**:
- Guide vulnerable NPC through danger
- Protect merchant from bandits
- Lead ally to destination

**Coordination**:
- Pack members follow alpha
- Coordinated group actions
- Shared awareness in hive minds

**Examples**:
- Rescue sailor from flooded tunnel (UC5)
- Escort merchant to town (UC6)
- Wolf pack coordination (UC3)

#### 6. Environmental Interactions

**Hazard Navigation**:
- Manage breath in non-breathable areas
- Avoid toxic spore concentrations
- Handle temperature extremes

**Terrain Tactics**:
- Use cover during combat
- Climb to avoid ground threats
- Exploit environmental bonuses

**Survival**:
- Find air pockets when drowning
- Use breathing reed in shallow water
- Burn webs to reduce spider advantage

**Examples**:
- Navigate flooded tunnel (UC5)
- Survive spore-filled basement (UC1)
- Burn spider webs to negate bonuses (UC7)

#### 7. Technical Interactions

**Repair**:
- Fix damaged constructs
- Restore functionality to broken automata
- Heal structural damage

**Activation**:
- Turn on dormant constructs
- Activate runes or mechanisms
- Power up magical systems

**Assignment**:
- Command guard to patrol area
- Instruct construct to provide information
- Set automata to specific tasks

**Examples**:
- Repair damaged statue (UC8)
- Activate rune to deactivate golems (UC2)
- Command construct to guard library (UC8)

#### 8. Combat Interactions

**Attack and Defense**:
- Multiple attack types per actor
- Armor reduces incoming damage
- Material-based immunities

**Tactical Positioning**:
- Take cover behind objects
- Use high ground advantage
- Corner enemies for advantage

**Status Effects**:
- Apply poison, bleeding, paralysis
- Entangle to prevent movement
- Knockdown to create openings

**Morale and Retreat**:
- Enemies flee when injured
- Pack members retreat if alpha flees
- Intimidation affects morale

**Examples**:
- Fight guardian golems with cover (UC2)
- Combat spider swarm with fire (UC7)
- Fight wolves until they flee (UC3)

---

## How Interactions Work: The Event Model

### Commands Trigger Events

Player commands and NPC actions trigger **events** that invoke **behaviors**:

#### Direct Actor-to-Actor Events

**Attack Event**:
```
Player: "attack wolf"
  ↓
handle_attack validates action
  ↓
Apply damage to wolf (accessor.update with verb="damage")
  ↓
Wolf's on_damage behavior fires
  ↓
Behavior checks health vs flee_threshold
  ↓
If low health: set morale to 0, trigger flee
  ↓
Return result to player
```

**Give Event** (healing):
```
Player: "give antidote to scholar"
  ↓
handle_give transfers item
  ↓
Scholar's on_receive behavior fires
  ↓
Behavior checks if item cures scholar's condition
  ↓
If "cures": ["fungal_infection"]: remove condition
  ↓
Increment scholar's gratitude toward player
  ↓
Return success message
```

**Service Event** (teaching):
```
Player: "give 50 gold to healer"
  ↓
Healer's on_receive behavior fires
  ↓
Check if amount matches service.teach_herbalism
  ↓
If matches: add "knows_herbalism" to player.knows
  ↓
Increment trust relationship
  ↓
Return teaching success message
```

#### Environmental Events

**Location-Based Effects**:
```
Player: "approach part_basement_center"
  ↓
Spatial handler updates player.location
  ↓
Environmental behavior checks part properties
  ↓
Part has "spore_level": "high"
  ↓
Apply/increase fungal_infection condition
  ↓
Player's resistances reduce severity
  ↓
Narrator describes spore effects
```

**Breath Tracking**:
```
Player in part with "breathable": false
  ↓
Each turn (successful command)
  ↓
Environmental behavior: player.breath -= 10
  ↓
If breath <= 0: health -= 10 (drowning damage)
  ↓
If player has breathing_reed and shallow water: don't decrease breath
  ↓
Narrator describes urgency
```

#### Implicit Proximity Events

**Contagion Spread**:
```
Player: "examine infected scholar"
  ↓
Spatial handler sets focused_on = scholar
  ↓
After turn, condition progression checks
  ↓
Scholar has contagious condition with contagious_range="touch"
  ↓
Player is focused_on scholar (interaction range)
  ↓
Apply/increase infection to player
  ↓
Player resistances reduce severity
```

**Pack Awareness**:
```
Alpha wolf becomes hostile
  ↓
After turn, NPC action phase
  ↓
For each pack member:
  - Check if pack_role="follower" and follows_alpha is set
  - If yes: copy alpha's disposition
  ↓
All pack members become hostile
  ↓
Narrator describes pack coordination
```

### Turn Sequence: When Things Happen

Following **Design Decision 3 & 4**:

```
1. Player issues command
2. Handler executes command
3. If command succeeds:
   a. NPC Action Phase:
      - Sort NPCs by pack_role ("alpha" first, then "follower")
      - For each NPC (in sorted order):
        * If pack_role == "follower":
          - Check follows_alpha and copy disposition from alpha
        * Invoke npc_take_action behavior
        * NPC checks conditions and may return early if nothing to do
        * Example: hostile NPC attacks if player in same room
        * Example: healing NPC offers help if injuries detected
        * Example: merchant NPC offers trades if player nearby
        * Example: friendly follower assists player

   b. Environmental Effects Phase:
      - For each actor everywhere:
        * Check location part properties (breathable, temperature, spores)
        * Update vitals (breath, temperature)
        * Apply NEW conditions from environment (e.g., hypothermia, disease)
        * Do NOT apply damage yet (that happens in next phase)

   c. Condition Progression Phase:
      - For each actor everywhere:
        * For each condition (including just-added ones):
          - Apply damage_per_turn to health
          - Decrease duration (if applicable)
          - Remove if duration reaches 0 or severity <= 0

   d. Death/Incapacitation Check:
      - For each actor everywhere:
        * Check if health <= 0
        * Invoke on_death or on_incapacitated behavior
        * Authors implement death handling (drop inventory, create corpse, etc.)

   e. Narration:
      - Narrator combines all events into cohesive description

4. Return combined result to player
```

**Key Points**:
- **Every successful command is a turn** (Decision 4)
- **Failed commands don't advance time** (merciful to player)
- **All NPCs everywhere can act** (Decision 3) - not just combat NPCs
- **Alphas act before followers** (enables pack coordination)
- **Environmental conditions apply damage the SAME turn** they're added (creates urgency)
- **Random order by default**, deterministic mode for testing
- **Conditions tick every turn**, creating time pressure

**NPC Early-Out Pattern**: Since all NPCs everywhere are processed each turn, behaviors should check early and return if nothing to do:
```python
def npc_take_action(actor, accessor, context):
    # Early out: not hostile, nothing to do
    disposition = actor.properties.get("ai", {}).get("disposition")
    if disposition != "hostile":
        return None

    # Early out: player not in same location
    player = accessor.get_player()
    if actor.location != player.location:
        return None

    # Actually do something...
```
This pattern keeps the system responsive even with many NPCs.

**Note on Death Handling**: The engine invokes `on_death` behaviors when health reaches 0, but does not automatically remove actors, drop inventory, or create corpses. Authors implement death handling in behaviors based on their game's needs. Some games may not have death at all (incapacitation, respawn, etc.). This flexibility is intentional—different games handle death very differently, and we have no single "standard" template.

---

## Property-Driven Design: How Authors Create Interactions

### Principle: Properties Define Capabilities

Authors create interactions by setting **properties**, not by writing code. Behaviors read properties to determine outcomes.

### Example 1: Venomous Attack (Combat)

**Spider Properties**:
```json
{
  "id": "npc_spider",
  "name": "giant spider",
  "properties": {
    "health": 20,
    "max_health": 20,
    "body": {
      "form": "arachnid",
      "features": ["fangs", "spinnerets"]
    },
    "attacks": [
      {
        "name": "venomous_bite",
        "damage": 8,
        "range": "touch",
        "applies_condition": {
          "name": "spider_venom",
          "severity": 40,
          "damage_per_turn": 1,
          "duration": 10,
          "effect": "agility_reduced"
        }
      }
    ]
  }
}
```

**What Happens**:
1. Spider attacks player
2. Combat behavior reads `attacks` array
3. Behavior selects attack (e.g., venomous_bite)
4. Apply immediate damage (8)
5. Check for `applies_condition`
6. Add/increase spider_venom condition on player
7. Each turn: condition applies 1 damage for 10 turns
8. Effect "agility_reduced" can be checked by other behaviors

**No Code Required**: Just property definitions

### Example 2: Healing Service (Non-Combat)

**Healer Properties**:
```json
{
  "id": "npc_healer",
  "name": "Healer Elara",
  "properties": {
    "health": 70,
    "max_health": 70,
    "services": {
      "cure_poison": {
        "accepts": ["rare_herbs", "gold"],
        "amount_required": 1,
        "cure_amount": 100
      },
      "healing": {
        "accepts": ["gold"],
        "amount_required": 25,
        "restore_amount": 50
      }
    },
    "disposition": "neutral",
    "relationships": {}
  }
}
```

**What Happens**:
1. Player gives rare herb to healer
2. Healer's on_receive behavior fires
3. Check if item in `services.cure_poison.accepts`
4. If yes: remove all poison conditions from player
5. Increment `relationships.player.trust`
6. If trust >= 3: future services cost less
7. Return success message

**Emergent Behavior**: Trust system creates dynamic pricing without explicit code

### Example 3: Environmental Hazard (Non-Combat)

**Location Part Properties**:
```json
{
  "id": "part_basement_center",
  "name": "basement center",
  "properties": {
    "spore_level": "high",
    "breathable": true
  }
}
```

**Actor Properties** (resistance):
```json
{
  "properties": {
    "resistances": {
      "disease": 30
    }
  }
}
```

**What Happens**:
1. Player moves to part_basement_center
2. Environmental behavior checks `spore_level`
3. High spore_level = severity increase of 15
4. Check player's `resistances.disease` (30%)
5. Actual severity increase: 15 * 0.7 = 10.5 → 11 (round up)
6. Add/increase fungal_infection condition
7. Each turn in this part: increase condition
8. Leave part: stop increasing

**Layered Properties**: Part properties + actor resistances = outcome

### Example 4: Progressive Domestication (Social)

**Wolf Properties**:
```json
{
  "id": "npc_wolf",
  "name": "grey wolf",
  "properties": {
    "health": 45,
    "max_health": 45,
    "ai": {
      "disposition": "desperate",
      "needs": {
        "hungry": true
      }
    },
    "relationships": {}
  }
}
```

**Meat Properties**:
```json
{
  "id": "item_venison",
  "name": "venison",
  "properties": {
    "edible_by": ["carnivore", "omnivore"],
    "satisfies": "hungry"
  }
}
```

**What Happens (Progressive)**:
```
First feeding:
  - Wolf's on_receive checks if item satisfies "hungry"
  - Set needs.hungry = false
  - Set disposition = "neutral" (no longer desperate)
  - Increment relationships.player.gratitude = 1

Second feeding:
  - gratitude = 2

Third feeding:
  - gratitude = 3
  - Check threshold: if gratitude >= 3
  - Set disposition = "friendly"
  - Wolf will follow player, accept commands

No explicit "domestication system":
  - Just needs + satisfaction + relationship tracking
  - Threshold creates emergent domestication
```

### Example 5: Multi-Threat Rescue (Cooperative)

**Sailor Properties**:
```json
{
  "id": "npc_sailor",
  "name": "Sailor Marcus",
  "properties": {
    "health": 45,
    "max_health": 80,
    "breath": 5,
    "max_breath": 60,
    "conditions": {
      "exhaustion": {
        "severity": 70,
        "effect": "cannot_swim"
      }
    },
    "trapped": true
  }
}
```

**Location Properties**:
```json
{
  "id": "part_tunnel_middle",
  "properties": {
    "breathable": false,
    "water_temp": "freezing"
  }
}
```

**What Happens**:
```
Each turn in tunnel:
  1. Environmental phase: Update vitals
     - Sailor: breath -= 10 (faster decline, low max_breath)
     - Player: breath -= 10
     - Add new conditions from environment (hypothermia from freezing water)

  2. Condition progression phase: Apply damage
     - If breath <= 0: drowning damage (health -= 10 per turn)
     - Hypothermia: deals 2 damage per turn
     - Exhaustion: cannot_swim effect prevents sailor from moving independently

  3. Player must manage multiple threats:
     - Use rope to pull sailor (exhaustion prevents self-rescue)
     - Manage own breath while rescuing
     - ~5 turns before sailor dies from drowning

Multiple threats compound:
  - Drowning + hypothermia + exhaustion
  - Time pressure from turn-based vitals
  - Player must manage own breath while rescuing
```

**Emergent Complexity**: Simple property combinations create rich scenario

---

## Simplified, Author-Friendly Patterns

Based on **Actor Interaction Evaluation** recommendations:

### Phase 1: Core Interactions (Recommended First)

#### 1. Condition System

**Properties**:
```json
"conditions": {
  "condition_name": {
    "severity": 0-100,
    "damage_per_turn": number,
    "duration": number (optional),
    "effect": "string describing effect"
  }
}
```

**Note**: Items have the `cures` property (e.g., `"cures": ["condition_name"]`, `"cure_amount": 100`), not conditions. The `cure_amount` indicates how much severity is removed when the item is used.

**Benefits**:
- Works for poison, disease, bleeding, exhaustion, paralysis, entanglement
- Unified progression mechanism
- Item-based treatment via properties
- No code needed for basic conditions

**Use Cases**: UC1 (disease), UC3 (conditions affect combat), UC5 (exhaustion), UC6 (bleeding), UC7 (venom, entanglement)

#### 2. Multiple Attacks Per Actor

**Properties**:
```json
"attacks": [
  {
    "name": "bite",
    "damage": 15,
    "type": "piercing",
    "range": "touch",
    "applies_condition": {...}  // Optional
  },
  {
    "name": "tackle",
    "damage": 8,
    "range": "touch",
    "effect": "knockdown"
  }
]
```

**Benefits**:
- Different enemies feel distinct
- Tactical variety (melee vs ranged, damage vs status)
- Simple array structure
- Behaviors select appropriate attack based on range and context

**Use Cases**: UC2 (golem attacks), UC3 (wolf bite/tackle), UC7 (spider bite/web spray)

#### 3. Body Characteristics

**Properties**:
```json
"body": {
  "form": "humanoid|quadruped|arachnid|construct",
  "material": "flesh|stone|clockwork",
  "features": ["teeth", "claws", "fangs"],
  "size": "small|medium|large"
}
```

**Benefits**:
- Material-based immunities (stone immune to poison)
- Form-based restrictions (quadruped can't serve food)
- Feature requirements (needs teeth to bite)
- Size affects interactions

**Use Cases**: All use cases (defines what actors can do)

#### 4. Environmental Properties Affecting Actors

**Properties** (on location parts):
```json
{
  "breathable": true|false,
  "spore_level": "none|low|high",
  "web_density": "none|light|heavy",
  "cover_value": 80,  // percentage
  "temperature": "freezing|cold|normal|hot"
}
```

**Benefits**:
- Leverages existing spatial system
- Creates environmental puzzles
- Tactical depth
- No actor-specific code

**Use Cases**: UC1 (spores), UC2 (cover), UC5 (breathable), UC7 (webs)

### Phase 2: Social and Service Interactions (Recommended Second)

#### 5. NPC Services Framework

**Properties**:
```json
"services": {
  "service_name": {
    "accepts": ["item_type", "currency"],
    "amount_required": number,
    "cure_amount": number,
    "grants": "knowledge_or_skill"  // Optional
  }
}
```

**Benefits**:
- Unified pattern for healing, teaching, trading, repair
- Barter or currency-based
- Relationship integration
- Reusable behavior code

**Use Cases**: UC1 (treatment), UC4 (healing, teaching), UC6 (trading, healing), UC8 (repair)

#### 6. Relationship Tracking

**Properties**:
```json
"relationships": {
  "actor_id": {
    "trust": 0-10,
    "gratitude": 0-10,
    "fear": 0-10
  }
}
```

**Benefits**:
- Progressive bonds
- Dynamic pricing (trust affects costs)
- Domestication via thresholds
- Emergent alliances

**Use Cases**: UC3 (wolf domestication), UC4 (trust affects teaching), UC6 (gratitude = rewards)

#### 7. Morale and Fleeing

**Properties**:
```json
"ai": {
  "morale": 0-100,
  "flee_threshold": number,
  "disposition": "friendly|neutral|hostile|desperate|grateful"
}
```

**Benefits**:
- Non-lethal combat resolution
- Realistic NPC behavior
- Creates dynamic encounters
- Simple threshold check

**Use Cases**: UC2 (guards flee), UC3 (wolves flee when injured), UC6 (protect merchant)

### Phase 3: Advanced Coordination (Optional)

#### 8. Simple Pack Following

**Properties**:
```json
"pack_id": "group_identifier",
"pack_role": "alpha|follower",
"follows_alpha": "alpha_actor_id"
```

**Behavior**:
```python
# Followers copy alpha disposition during NPC action phase
if pack_member.properties.get("ai", {}).get("pack_role") == "follower":
    alpha_id = pack_member.properties["ai"].get("follows_alpha")
    if alpha_id:
        alpha = accessor.get_actor(alpha_id)
        pack_member.properties["ai"]["disposition"] = alpha.properties["ai"]["disposition"]
```

**Benefits**:
- Group coordination for both hostile and friendly packs
- Follow-the-leader pattern
- Simple to author
- No complex AI needed
- Supports coordinated attacks AND cooperative allies

**Examples**:
- Hostile wolf pack: alpha becomes hostile → pack attacks
- Friendly guard squad: captain helps player → squad assists
- Domestication: tame alpha wolf → entire pack becomes friendly

**Use Cases**: UC3 (wolf pack), UC7 (spider swarm)

### What to Defer (from Evaluation)

**Not Recommended for Phase 1**:
- Detailed skill system (use boolean or coarse levels)
- Multiple vital stats (add incrementally: health first, then breath only if drowning, etc.)
- Equipment system (use simple `equipped_weapon` property)
- Component-level damage (use overall health)
- Complex AI task programming (use simple command/assignment)

**Rationale**: These add authoring complexity for marginal gameplay gains. The simplified approach gives 80% of gameplay value for 20% of the complexity.

**Note on Game-Specific Properties**: Most properties shown in use case examples (like `trapped`, `destination`, `alerted_by`, `current_duty`) are game-specific and belong in author code or shared libraries, not in the core engine schema. The core schema documents conventions for common scenarios, not requirements. Authors should freely add properties as needed for their game's mechanics.

---

## Integration with Existing Architecture

### Reuses Entity-Behavior Pattern

Actor interactions build on the **existing** architecture:

```
Player gives herb to scholar
  ↓
Engine routes to handle_give
  ↓
Handler transfers item
  ↓
Handler calls accessor.update(scholar, {}, verb="receive", item=herb)
  ↓
Engine invokes scholar's on_receive behavior
  ↓
Behavior checks if herb cures condition
  ↓
Behavior returns state changes
  ↓
Engine applies changes
  ↓
Handler sends result to player
```

**No new pattern to learn**: Same event → behavior → state change flow

### Reuses StateAccessor for All Changes

All interactions use **StateAccessor**:

```python
# Apply damage
result = accessor.update(
    target_actor,
    {"properties.health": new_health},
    verb="damage",
    actor_id=attacker_id,
    damage_amount=damage
)

# This triggers on_damage behavior automatically
```

**Benefits**:
- Proper state management
- Nested behaviors fire correctly
- Serialization works
- No bypassing validation

### Reuses Spatial System

Actor interactions leverage **existing spatial features**:

- `focused_on`: Determines interaction range
- `posture`: Affects combat (cover, concealed)
- Part properties: Environmental effects
- Location tracking: Proximity checks

**Example**:
```python
# Cover mechanics
if player.posture == "cover":
    cover_obj = accessor.get_entity(player.focused_on)
    damage_reduction = cover_obj.properties.get("cover_value", 0)
    damage = damage * (1 - damage_reduction / 100)
```

### Reuses Properties Pattern

Actor interactions use **same properties dict**:

```json
"properties": {
  "health": 100,              // Like items have properties
  "attacks": [...],            // Custom to actors
  "conditions": {...},         // Temporary state
  "services": {...},           // Capabilities
  "relationships": {...}       // Social state
}
```

**Authors already understand this pattern**

---

## What's New for Authors

### New Property Schemas

Authors can use standardized property schemas:

**Health and Vitals** (minimal viable):
```json
{
  "health": number,
  "max_health": number
}
```

**Conditions** (recommended):
```json
{
  "conditions": {
    "condition_name": {
      "severity": number,
      "damage_per_turn": number,
      "duration": number,
      "effect": "string"
    }
  }
}
```

**Combat Abilities** (if combat in game):
```json
{
  "attacks": [...],
  "armor": number,
  "immunities": [...],
  "resistances": {...}
}
```

**Services** (for non-combat NPCs):
```json
{
  "services": {
    "service_name": {
      "accepts": [...],
      "amount_required": number,
      "grants": "string"
    }
  }
}
```

**Social State** (for progressive gameplay):
```json
{
  "relationships": {
    "actor_id": {"trust": n, "gratitude": n}
  }
}
```

### New Behavior Events

Additional events for actor interactions:

**Combat Events**:
- `on_attack`: When this actor attacks
- `on_damage`: When this actor takes damage
- `on_death`: When health reaches 0

**Medical Events**:
- `on_heal`: When this actor is healed
- `on_condition_change`: When condition is added/removed
- `on_cure`: When treated for condition

**Social Events**:
- `on_receive`: When given an item (already exists, extended)
- `on_relationship_change`: When trust/gratitude changes

**Environmental Events**:
- `on_enter_part`: When actor enters location part
- `on_environmental_effect`: When environment affects actor

**NPC Action**:
- `npc_take_action`: Called each turn for NPC to act

### Environmental Integration

Part properties now affect actors:

**Hazards**:
```json
{
  "breathable": false,        // Affects breath
  "spore_level": "high",      // Applies conditions
  "temperature": "freezing"   // Temperature effects
}
```

**Tactical**:
```json
{
  "cover_value": 80,          // Combat advantage
  "web_density": "heavy",     // Movement/combat effects
  "elevation": "high"         // Positioning effects
}
```

**Triggers**:
```json
{
  "activation_trigger": "player_enters_center",  // Events
  "rune_effect": "deactivate_golems"            // Actions
}
```

### Optional AI Hooks

Authors can implement NPC behaviors:

```python
def npc_take_action(entity, accessor, context):
    """Called each turn after player acts."""
    # Authors implement this based on their game's needs
    # General guidance: check early and return if nothing to do

    # Example: Check disposition first
    disposition = entity.properties.get("ai", {}).get("disposition")
    if disposition != "hostile":
        return  # Nothing to do for non-hostile NPCs in this example

    # Example: Check if player is in same room (cheap proximity check)
    player_loc = accessor.get_entity_location(accessor.get_player())
    npc_loc = accessor.get_entity_location(entity)

    if player_loc.id != npc_loc.id:
        return  # Player not here

    # Perform action (attack, heal, flee, etc.)
    # ...
```

**Note on Performance**: The suggestion to "check early and return" is general guidance, not a requirement. Authors know their game logic best and can optimize based on actual performance needs. If a game becomes slow, authors can analyze and optimize their specific NPC behaviors. There's no universal pattern that applies to all games.

---

## Limitations and Constraints

### 1. Turn-Based, Not Real-Time

**Limitation**: Engine is request-driven, not real-time.

**What This Means**:
- Interactions happen after player commands
- NPCs act "after" player, not simultaneously
- No persistent timers during player thinking

**Implications**:
- Time pressure simulated via turn counts
- "Urgency" is discrete (turns), not continuous (seconds)
- Sailor has ~5 turns before drowning (not 30 seconds)

**Design Choice**: Matches text adventure conventions, keeps implementation simple

### 2. Abstract Distance, Not Precise Coordinates

**Limitation**: No formal distance metric.

**What This Means**:
- "Same location" is basic proximity
- `focused_on` provides finer granularity
- No "10 feet away" or movement speeds

**Implications**:
- Interaction range is abstraction: "touch", "near", "far"
- Environmental effects tied to parts, not distance
- Tactical positioning via cover/focus, not coordinates
- Range is author-interpreted in behaviors, not engine-enforced

**Design Choice**: Text-friendly abstraction, simple for authors, flexible for different game styles

### 3. Skills Are Author-Defined

**Limitation**: No built-in skill resolution system.

**What This Means**:
- Authors decide if skills are deterministic or random
- Authors implement skill checks in behaviors
- No standard dice mechanics

**Implications**:
- Full control (good!)
- Must implement checks in behaviors (more work)
- Can be inconsistent unless careful

**Recommendation**: Start with boolean skills (knows_herbalism: true/false) or coarse levels (medicine: "novice"|"expert"). Defer detailed numerical skills.

### 4. Event-Driven AI, Not Goal-Oriented

**Limitation**: NPCs don't have autonomous planning.

**What This Means**:
- NPCs react to events (on_attack, on_see_player)
- NPCs don't proactively pursue goals like "find food"
- Complex behavior requires authored AI

**Implications**:
- Simple AI (attack when hostile) is straightforward
- Complex AI (pack tactics) requires careful design
- NPCs act when triggered, not continuously

**Design Choice**: Simpler implementation, predictable for testing

### 5. Death Is Not Built-In

**Limitation**: Engine doesn't automatically handle death.

**What This Means**:
- When health reaches 0, engine invokes `on_death` behavior
- Authors implement death/incapacitation in behaviors
- Authors decide: death? unconscious? inert?

**Implications**:
- Requires authored behaviors for death handling
- Each game can handle differently (flexible!)
- Must consider: What happens to inventory? Can corpse be examined?
- No single "standard" death template—different games want very different outcomes

**Design Choice**: Maximizes flexibility—some games may not have death at all

### 6. No Built-In Equipment System

**Limitation**: Wearing/wielding items not a core feature.

**What This Means**:
- Items in inventory, but no "equipped" slots
- Authors must track in properties
- Authors must implement equip/unequip commands

**Recommendation**: Start simple—`equipped_weapon: item_id` property. Only build full equipment system if gameplay demands it.

---

## Design Principles Applied

### Maximize Author Capability and Player Agency

✓ Authors define all interactions via properties and behaviors
✓ No hardcoded interaction rules
✓ System supports scenarios beyond use cases
✓ Players have multiple paths to solve problems

### Separation of Concerns

✓ **Engine manages state**: Stores properties, routes commands, tracks positions
✓ **Behaviors implement rules**: Calculate outcomes, apply state changes
✓ **LLM narrates**: Describes what happened in natural language

**Clear boundaries** prevent confusion

### Property-Driven Entities

✓ All actor characteristics in flexible properties dict
✓ Minimal core fields (id, name, location, inventory)
✓ Authors define property schemas for their needs
✓ **Conventions, not requirements**: Use what you need

### Behavior-Driven Extension

✓ All interaction logic in behaviors, not engine
✓ New interaction types via new behaviors
✓ Existing behaviors can be composed and stacked
✓ **First-class events**: actor interactions use same event system

### Reuse Existing Architecture

✓ Entity-behavior pattern (already exists)
✓ StateAccessor for changes (already exists)
✓ Spatial system (already exists)
✓ Properties dict (already exists)

**Minimal new concepts** to learn

---

## Implementation Requirements

This section documents engine-level infrastructure that must be implemented to support the actor interaction system.

### Requirement 1: Property Location for Vitals

Actor vitals (health, breath, conditions, etc.) are stored directly in `actor.properties`, not in a nested structure:

```python
# Correct - directly in properties
actor.properties["health"] = 80
actor.properties["max_health"] = 100
actor.properties["conditions"] = {"poison": {...}}

# NOT in a nested stats dict
# actor.properties["stats"]["health"]  # Wrong
```

The existing `Actor.stats` property accessor in `state_manager.py` provides convenience access to `properties["stats"]` but should not be required for vital stats. Implementation should read vitals directly from properties.

### Requirement 2: Turn Phase Hook System

The engine must implement a hook system that fires multiple phases after each successful player command. These hooks are called in order:

```
1. Command succeeds
2. Hook: NPC_ACTION
   - For each NPC (sorted by pack_role: alphas first)
   - Invoke npc_take_action behavior
3. Hook: ENVIRONMENTAL_EFFECT
   - For each actor everywhere
   - Apply location part effects (breath, spores, temperature)
4. Hook: CONDITION_TICK
   - For each actor everywhere
   - Progress all conditions (damage, duration, severity)
5. Hook: DEATH_CHECK
   - For each actor everywhere
   - Check health <= 0, invoke on_death behavior
```

These hooks should be registered via the event registration system (see [Event Registration](event_registration.md)).

**Hook constants** (in `src/hooks.py`):
```python
TURN_END = "turn_end"
NPC_ACTION = "npc_action"
ENVIRONMENTAL_EFFECT = "environmental_effect"
CONDITION_TICK = "condition_tick"
DEATH_CHECK = "death_check"
```

### Requirement 3: Part Access API

Environmental effects need to determine which spatial part an actor occupies. The StateAccessor must provide:

```python
def get_actor_part(self, actor: Actor) -> Optional[Part]:
    """
    Get the spatial part an actor currently occupies.

    Returns the Part entity based on actor's location and spatial position,
    or None if the actor is not in a spatial location.
    """
```

This integrates with the existing spatial system's `focused_on` and part positioning.

### Requirement 4: Effect String Registry

Condition effects (like `"cannot_move"`, `"agility_reduced"`) should be registered to catch typos at load time. Modules register valid effect strings:

```python
vocabulary = {
    "effects": [
        {"effect": "cannot_move", "description": "Prevents movement commands"},
        {"effect": "cannot_swim", "description": "Prevents swimming/self-rescue"},
        {"effect": "agility_reduced", "description": "Reduces agility (flavor)"},
        {"effect": "blinded", "description": "Affects perception"}
    ]
}
```

**Validation**: At load time, verify that all `effect` strings in condition definitions match registered effects. Raise an error for unregistered effects.

**Extensibility**: Authors can register new effects in their behavior modules. The registry is additive across all loaded modules.

**Standard effects** (provided by core):
| Effect | Description |
|--------|-------------|
| `cannot_move` | Prevents movement commands |
| `cannot_swim` | Prevents swimming, self-rescue in water |
| `cannot_attack` | Prevents attack commands |
| `agility_reduced` | Flavor - behaviors may check |
| `strength_reduced` | Flavor - behaviors may check |
| `blinded` | Affects perception, targeting |
| `slowed` | Movement costs extra turns |

---

## Next Steps for Implementation

Following **Design Decision 1**: Core framework lives in `behaviors/core/actors.py` or `behaviors/core/interactions.py`

### Phase 1: Core Interaction Infrastructure

**Implement**:
1. **Condition system**: Progression, application, treatment
2. **Health and damage**: Vital stats, damage application
3. **Attack framework**: Multiple attacks, attack selection
4. **Body characteristics**: Form, material, features checking
5. **Environmental effects**: Part properties affect actors
6. **Turn progression**: NPC actions, condition ticking, environmental effects

**Deliverables**:
- `behaviors/core/interactions.py` or `behaviors/core/actors.py`
- Standard property schemas documented
- Example behaviors for common patterns
- Test suite for multi-actor scenarios

### Phase 2: Social and Service Systems

**Implement**:
1. **Services framework**: Generic service resolution
2. **Relationship tracking**: Trust, gratitude, fear
3. **Morale system**: Flee when injured
4. **Simple pack coordination**: Follow-the-leader

**Deliverables**:
- Service handler behaviors
- Relationship progression behaviors
- Morale check utilities
- Pack coordination examples

### Phase 3: Polish and Examples

**Implement**:
1. **Example use cases**: Implement simplified use cases from UC doc
2. **Author documentation**: Property schemas, behavior events, patterns
3. **Testing utilities**: Helper functions for testing interactions
4. **Performance optimization**: Ensure efficient NPC action phase

### Standard Property Schemas to Document

```json
{
  "health": number,
  "max_health": number,
  "breath": number,  // Optional
  "max_breath": number,  // Optional
  "body": {
    "form": "string",
    "material": "string",
    "features": ["array"],
    "size": "string"
  },
  "attacks": [
    {
      "name": "string",
      "damage": number,
      "type": "string",
      "range": "touch|near|far",
      "applies_condition": {...}
    }
  ],
  "armor": number,
  "immunities": ["array"],
  "resistances": {"type": percentage},
  "conditions": {
    "name": {
      "severity": number,
      "damage_per_turn": number,
      "duration": number,
      "effect": "string"
    }
  },
  "ai": {
    "disposition": "friendly|neutral|hostile|desperate|grateful",
    "morale": number,
    "flee_threshold": number,
    "pack_id": "string",
    "pack_role": "alpha|follower",
    "follows_alpha": "actor_id"
  },
  "services": {
    "service_name": {
      "accepts": ["array"],
      "amount_required": number,
      "cure_amount": number,
      "grants": "string"
    }
  },
  "relationships": {
    "actor_id": {
      "trust": number,
      "gratitude": number,
      "fear": number
    }
  },
  "knows": ["array"],
  "knowledge": {"topic": boolean}
}
```

**For Constructs**: Use `health` uniformly (same as living creatures). Authors can interpret this as "integrity" or "structural damage" narratively. Use `"operational": boolean` to track whether construct is active/functional (a construct at full health may still be deactivated).

**For Items**: Use `"cures": ["condition_name"]` and `"cure_amount": number` for items that treat conditions.

### Behavior Events to Implement

**Core Events**:
- `on_attack`
- `on_damage`
- `on_heal`
- `on_condition_change`
- `on_death`
- `on_receive` (extend existing)
- `npc_take_action`

**Environmental Events**:
- `on_enter_part`
- `on_environmental_effect`

**Social Events**:
- `on_relationship_change`

---

## Summary

### Actor Interactions in This Engine Are:

✓ **Broadly Scoped**: Combat, cooperation, rescue, disease, teaching, trading all supported
✓ **Property-Driven**: Authors define capabilities via flexible properties
✓ **Behavior-Implemented**: Interaction logic lives in modular behaviors
✓ **Spatially-Integrated**: Positioning and environment affect interactions
✓ **Emergent**: Simple properties combine into complex scenarios
✓ **Architecturally-Consistent**: Uses existing entity-behavior patterns
✓ **Author-Friendly**: Simplified patterns for common use cases

### What Makes This Design Unique:

**Combat ≠ Primary Focus**: Combat is one interaction type among many equal peers

**Service Framework**: NPCs can heal, teach, trade, escort using same pattern as combat

**Environmental Integration**: Location properties create hazards, tactics, and atmosphere

**Progressive Gameplay**: Relationships build over time, creating emergent domestication and alliances

**Minimal Complexity**: Start with health + conditions + attacks, add depth incrementally

**Unified Treatment**: All actors (player, NPCs, creatures, constructs) use same system

### Non-Combat Interactions Are First-Class:

- **Medical**: Heal, cure, stabilize, treat
- **Educational**: Teach, learn, identify, remember
- **Social**: Trust, gratitude, fear, domestication
- **Commercial**: Trade, barter, negotiate
- **Cooperative**: Rescue, escort, coordinate
- **Environmental**: Navigate, survive, exploit
- **Technical**: Repair, activate, command

### The System Enables Authors To Create:

- Poisonous gardens that require knowledge to navigate safely
- Drowning rescue missions with multiple simultaneous threats
- Wolf packs that can be fought or domesticated through feeding
- Healer NPCs who teach skills in exchange for payment or gratitude
- Environmental puzzles where terrain and conditions matter
- Progressive relationships that unlock new interactions
- Complex multi-actor scenarios with emergent outcomes

**All without modifying the engine.**

This design maximizes **author capability** and **player agency** while maintaining the engine's core principle: **state management separated from narration**, with **behaviors as the unit of game logic**—now extended to support the full richness of actor interactions across combat, cooperation, environmental challenges, and social dynamics.
