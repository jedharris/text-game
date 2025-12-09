# Actor Interaction Use Cases

This document presents diverse use cases for actor interactions in the text adventure engine, derived from the spatial room ideas. These use cases explore the full range of interaction mechanics beyond simple combat, including environmental hazards, aid, disease, cooperation, and bodily characteristics.

## Purpose

These use cases serve to:
- **Identify required properties** - What actor/item properties are needed?
- **Test spatial integration** - How do spatial features interact with actors?
- **Explore diverse interactions** - Combat is one of many possible interactions
- **Evaluate design approaches** - Can proposals support all these scenarios?
- **Guide implementation** - What features are essential vs. optional?

---

## Use Case 1: The Infected Scholar (Disease & Environmental Hazard)

### Scenario
A scholar in an ancient library has contracted a fungal infection from spores in the flooded basement. The player can help cure them, become infected themselves, or avoid contact. The infection spreads based on proximity and time.

### Spatial Context
- **Library Main Floor**: Safe zone, no spores
- **Basement Flooded Section** (from Room #42): Parts with different water depths
  - `part_basement_entrance`: Water depth "ankle", spore concentration "low"
  - `part_basement_center`: Water depth "waist", spore concentration "high"
  - `part_basement_far`: Water depth "chest", spore concentration "extreme"

### Actor Properties

**Scholar NPC:**
```json
{
  "id": "npc_scholar",
  "name": "Scholar Aldric",
  "location": "loc_library",
  "properties": {
    "stats": {
      "health": 60,
      "max_health": 100,
      "stamina": 30
    },
    "conditions": {
      "fungal_infection": {
        "severity": 80,
        "contagious": true,
        "transmission": "touch_proximity",
        "symptoms": ["coughing", "fatigue", "skin_lesions"],
        "progression_rate": 5
      }
    },
    "disposition": "friendly",
    "knowledge": ["ancient_texts", "fungal_lore"]
  }
}
```

**Player Actor:**
```json
{
  "properties": {
    "stats": {
      "health": 100,
      "max_health": 100,
      "immunity": 50
    },
    "conditions": {},
    "resistances": {
      "disease": 30
    }
  }
}
```

**Antifungal Herb Item:**
```json
{
  "id": "item_antifungal_herb",
  "name": "silvermoss",
  "properties": {
    "medicinal": true,
    "cures": ["fungal_infection"],
    "potency": 100,
    "application": "topical_or_consumed"
  }
}
```

### Interactions

1. **Proximity Infection Check**:
   - When player is `focused_on` same entity as infected scholar
   - Roll against player's `immunity` and `resistances.disease`
   - If failed, add `fungal_infection` to player's `conditions` at low severity

2. **Help Scholar**:
   - Player gives herb to scholar (existing `give` command)
   - Scholar's `on_receive` behavior checks if item has `cures` matching their conditions
   - Reduces `severity` by herb's `potency`, removes condition if ≤ 0

3. **Environmental Infection**:
   - Player at `part_basement_center` or `part_basement_far`
   - Each turn, roll against spore concentration
   - Progressive exposure: time spent increases infection chance

4. **NPC Deterioration**:
   - Each turn, scholar's infection `severity` increases by `progression_rate`
   - When `health` reaches critical (< 20), scholar becomes incapacitated
   - Scholar's dialogue options change based on health/severity

### Design Questions Raised

- **Condition system**: How are temporary/permanent conditions stored?
- **Turn-based effects**: When do conditions progress? After player actions?
- **Transmission mechanics**: Generic proximity? Specific actions (touch, talk)?
- **Multiple conditions**: Can actors have multiple simultaneous conditions?
- **Death vs incapacitation**: What happens when health reaches 0?

---

## Use Case 2: The Guardian Golem (Conditional Combat with Spatial Tactics)

### Scenario
Stone golems in a hall activate when the player approaches the center. Player can use cover behind pillars, deactivate golems via wall runes, or fight them directly. Golems have no limbs but can charge and slam.

### Spatial Context (from Room #2)
- `part_hall_entrance`: Safe zone, `safe_distance: true`
- `part_hall_center`: Combat zone, `exposed: true`
- Multiple `item_pillar` entities with `provides_cover: true`
- Wall parts with deactivation runes

### Actor Properties

**Stone Golem NPC:**
```json
{
  "id": "npc_golem_1",
  "name": "stone golem",
  "location": "part_hall_center",
  "properties": {
    "stats": {
      "health": 200,
      "max_health": 200,
      "strength": 80,
      "speed": 20
    },
    "body": {
      "form": "construct",
      "limbs": [],
      "mass": "massive",
      "material": "stone"
    },
    "combat": {
      "attacks": [
        {
          "name": "charge",
          "damage": 30,
          "range": "near",
          "requires_distance": "far_to_near"
        },
        {
          "name": "slam",
          "damage": 50,
          "range": "melee",
          "windup_turns": 1
        }
      ],
      "armor": 20,
      "immunities": ["poison", "disease", "bleeding"]
    },
    "ai": {
      "hostile": false,
      "activation_trigger": "player_in_center",
      "target_priority": "nearest_exposed"
    }
  }
}
```

**Player with Cover:**
```json
{
  "properties": {
    "stats": {
      "health": 100,
      "max_health": 100,
      "agility": 60
    },
    "posture": "cover",
    "focused_on": "item_pillar_1"
  }
}
```

**Pillar Item:**
```json
{
  "id": "item_pillar_1",
  "name": "marble pillar",
  "location": "loc_guardian_hall",
  "properties": {
    "provides_cover": true,
    "cover_effectiveness": 80,
    "destructible": true,
    "health": 100
  }
}
```

### Interactions

1. **Activation Trigger**:
   - When player's `focused_on` changes to `part_hall_center`
   - All golems with `activation_trigger: "player_in_center"` become `hostile: true`
   - Golems begin AI behavior loop

2. **Golem Attacks Player**:
   - Golem checks if can reach player
   - If player has `posture: "cover"`:
     - Attack has reduced chance to hit based on pillar's `cover_effectiveness`
     - If attack misses player, may hit pillar (damages pillar's `health`)
   - If hit succeeds:
     - Damage = golem's attack damage - player armor
     - Apply to player's `health`

3. **Player Attacks Golem**:
   - Player uses `attack` command on golem
   - Damage calculation uses weapon damage if equipped
   - Golem's `armor` reduces damage
   - Golem's construct `body.material` may resist certain damage types

4. **Pillar Destruction**:
   - After taking damage, pillar's `health` decreases
   - If `health ≤ 0`, pillar is destroyed (removed or becomes debris)
   - Player loses cover, `posture` clears to `null`

5. **Strategic Positioning**:
   - Player can `approach` different pillars to maintain cover
   - Moving between pillars costs turns, golem may attack during movement
   - Staying behind same pillar: golem tries to flank (move around)

6. **Non-Combat Solution**:
   - Player examines wall runes while maintaining safe distance
   - Activating runes requires specific sequence
   - Success: all golems return to `hostile: false`, return to starting positions

### Design Questions Raised

- **Body characteristics**: How to represent non-humanoid forms?
- **Attack types**: Multiple attacks with different properties per actor?
- **AI behavior**: When and how do NPCs take actions?
- **Cover mechanics**: Damage redirection to cover objects?
- **State restoration**: How do deactivated enemies return to neutral?
- **Reach and distance**: How is "near" vs "far" determined?

---

## Use Case 3: The Starving Wolf Pack (Hunger, Pack Tactics, Intimidation)

### Scenario
A pack of wolves is hungry and desperate in winter. They won't attack if intimidated or given food. If combat starts, they use pack tactics. Individual wolves can flee if injured. Player can befriend them with consistent feeding.

### Spatial Context
- Forest clearing with scattered trees providing limited cover
- Wolf den entrance (safe zone for wolves)

### Actor Properties

**Wolf NPC:**
```json
{
  "id": "npc_wolf_alpha",
  "name": "alpha wolf",
  "location": "loc_forest_clearing",
  "properties": {
    "stats": {
      "health": 60,
      "max_health": 60,
      "hunger": 80,
      "max_hunger": 100,
      "morale": 40
    },
    "body": {
      "form": "quadruped",
      "limbs": ["legs", "legs", "legs", "legs"],
      "features": ["teeth", "claws"],
      "size": "medium",
      "speed": "fast"
    },
    "combat": {
      "attacks": [
        {
          "name": "bite",
          "damage": 15,
          "type": "piercing",
          "body_part": "teeth"
        },
        {
          "name": "tackle",
          "damage": 8,
          "type": "blunt",
          "effect": "knockdown"
        }
      ]
    },
    "ai": {
      "pack_role": "alpha",
      "pack_id": "pack_winter_wolves",
      "behavior": "territorial",
      "hostility_threshold": 60,
      "flee_health_percentage": 30,
      "social_bonds": {}
    },
    "needs": {
      "hunger_rate": 5,
      "starvation_threshold": 90
    }
  }
}
```

**Regular Wolf (Pack Member):**
```json
{
  "id": "npc_wolf_2",
  "name": "grey wolf",
  "properties": {
    "stats": {
      "health": 45,
      "max_health": 45,
      "hunger": 85,
      "morale": 30
    },
    "ai": {
      "pack_role": "follower",
      "pack_id": "pack_winter_wolves",
      "follows_alpha": "npc_wolf_alpha"
    }
  }
}
```

**Meat Item:**
```json
{
  "id": "item_venison",
  "name": "venison",
  "properties": {
    "edible": true,
    "nutrition": 50,
    "freshness": 100,
    "appealing_to": ["carnivore", "omnivore"]
  }
}
```

### Interactions

1. **Hunger-Driven Behavior**:
   - Each turn, wolves' `hunger` increases by `hunger_rate`
   - When `hunger` > `starvation_threshold`, wolves become desperate
   - Desperate wolves: `hostility_threshold` drops significantly
   - Alpha decides pack behavior based on combined hunger/morale

2. **Intimidation**:
   - Player can use `intimidate` or `shout` command
   - Roll against player's presence vs wolves' `morale`
   - Success: wolves' `morale` drops, they retreat to den
   - Failure: wolves interpret as threat, hostility increases

3. **Feeding to Pacify**:
   - Player drops meat item near wolves
   - Nearest wolf with highest `hunger` approaches food
   - Consuming food: `hunger` decreases by `nutrition` value
   - Fed wolves: reduced hostility, improved `social_bonds` with player
   - Multiple feedings over time can domesticate wolves

4. **Pack Tactics in Combat**:
   - Follower wolves coordinate with alpha
   - If 2+ wolves are `focused_on` same target (flanking):
     - Increased hit chance for all attacking wolves
     - Target has reduced defense
   - Alpha directs pack: if alpha flees, others follow

5. **Individual Morale**:
   - When wolf's `health` < (`max_health` * `flee_health_percentage`):
     - That wolf's `morale` drops sharply
     - Wolf attempts to flee to den
     - If alpha is still fighting, may override flee instinct

6. **Progressive Relationship**:
   - Player's repeated feeding tracked in `social_bonds`
   - After threshold of positive interactions:
     - Wolves no longer hostile
     - May follow player
     - Can receive simple commands

### Design Questions Raised

- **Pack coordination**: How do multiple NPCs coordinate actions?
- **Needs systems**: Hunger, thirst, fatigue - generic or specific?
- **Morale and psychology**: How are emotional states modeled?
- **Domestication**: Progressive relationship changes over time?
- **Body parts in combat**: Do specific features (teeth, claws) matter?
- **Social memory**: Do NPCs remember past interactions?

---

## Use Case 4: The Poisonous Garden (Alchemical Hazards, Healing NPCs)

### Scenario
An overgrown alchemical garden contains valuable herbs but many are toxic. A hermit healer lives here and will trade healing for rare ingredients. Some plants cause slow poison, others instant harm. The healer can cure poisons and teach identification.

### Spatial Context
- Garden with plant beds as parts of location
- Hermit's hut (safe zone)
- Specific plants at specific beds

### Actor Properties

**Hermit Healer NPC:**
```json
{
  "id": "npc_healer_elara",
  "name": "Healer Elara",
  "location": "loc_hermit_hut",
  "properties": {
    "stats": {
      "health": 70,
      "max_health": 70,
      "expertise": {
        "herbalism": 95,
        "medicine": 90,
        "alchemy": 80
      }
    },
    "services": {
      "healing": {
        "offered": true,
        "cost_type": "barter",
        "accepts": ["rare_herbs", "gems", "information"]
      },
      "cure_poison": {
        "offered": true,
        "cost_type": "barter",
        "effectiveness": 100
      },
      "teaching": {
        "offered": true,
        "subjects": ["herb_identification", "basic_alchemy"],
        "cost_type": "barter"
      }
    },
    "disposition": "neutral",
    "trust_level": 0
  }
}
```

**Player (Poisoned):**
```json
{
  "properties": {
    "stats": {
      "health": 85,
      "max_health": 100
    },
    "conditions": {
      "nightshade_poison": {
        "severity": 40,
        "type": "slow_poison",
        "damage_per_turn": 2,
        "duration_remaining": 20,
        "symptoms": ["dizziness", "nausea"]
      }
    },
    "knowledge": {
      "herb_identification": 20
    }
  }
}
```

**Nightshade Plant:**
```json
{
  "id": "item_nightshade",
  "name": "nightshade plant",
  "location": "part_garden_north_bed",
  "properties": {
    "portable": false,
    "harvestable": true,
    "yields": "item_nightshade_berries",
    "danger": {
      "toxic_to_touch": true,
      "poison_type": "nightshade_poison",
      "severity": 40,
      "onset": "immediate"
    },
    "identification_difficulty": 60
  }
}
```

**Antidote Herb:**
```json
{
  "id": "item_antidote_herb",
  "name": "golden root",
  "properties": {
    "medicinal": true,
    "cures": ["nightshade_poison", "serpent_venom"],
    "potency": 80,
    "rare": true,
    "value": "high"
  }
}
```

### Interactions

1. **Plant Identification**:
   - Player examines plant
   - Roll against player's `knowledge.herb_identification` vs plant's `identification_difficulty`
   - Success: reveals plant's `danger` properties
   - Failure: plant appears safe, danger not revealed

2. **Accidental Poisoning**:
   - Player attempts to `take` or `harvest` nightshade without knowledge
   - Plant's `toxic_to_touch` triggers poison
   - Player receives condition matching plant's `poison_type` at specified `severity`
   - Immediate onset: symptoms appear in same turn

3. **Poison Progression**:
   - Each turn after player action:
     - Player takes `damage_per_turn` from active poisons
     - `duration_remaining` decreases by 1
     - If duration reaches 0, poison ends naturally
     - Multiple poisons can stack

4. **Seeking Healing**:
   - Player approaches healer at hut
   - Initiates conversation about symptoms
   - Healer diagnoses poison based on `symptoms`
   - Offers cure for barter (rare herbs, payment)

5. **Bartering for Cure**:
   - Player must have items matching healer's `services.cure_poison.accepts`
   - Trade negotiation based on healer's `trust_level` and `disposition`
   - If accepted: healer removes poison condition from player
   - Healer's `trust_level` increases with successful trade

6. **Learning Identification**:
   - Player requests teaching (`services.teaching`)
   - Cost in barter goods or coin
   - After lesson: player's `knowledge.herb_identification` increases
   - Higher knowledge = better identification on future plants

7. **Healer Provides Healing**:
   - Separate service from cure poison
   - Healer restores player's `health` toward `max_health`
   - More expensive than cure poison
   - May require rest (time passage)

### Design Questions Raised

- **Knowledge/skill system**: How are learned abilities stored and used?
- **NPC services**: Generic framework for teaching, healing, crafting?
- **Barter system**: How are trades evaluated and resolved?
- **Condition stacking**: Multiple simultaneous poisons/diseases?
- **Time and rest**: Does healing require passage of time?
- **Diagnosis**: Can NPCs identify player conditions and offer help?

---

## Use Case 5: The Drowning Sailor (Environmental Rescue, Breath Mechanics)

### Scenario
A sailor is trapped in a flooded tunnel section (from Room #42), running out of breath. The player must navigate the water hazard, reach the sailor, and either rescue them or provide breathing apparatus. Both the sailor and player have limited breath underwater.

### Spatial Context (from Room #42)
- `part_tunnel_entrance`: Ankle-deep water, breathable
- `part_tunnel_middle`: Fully submerged, `breathable: false`, `swim_distance: 3`
- `part_tunnel_end`: Small air pocket, `breathable: true`
- Sailor trapped at `part_tunnel_end`

### Actor Properties

**Drowning Sailor NPC:**
```json
{
  "id": "npc_sailor_marcus",
  "name": "Sailor Marcus",
  "location": "part_tunnel_end",
  "properties": {
    "stats": {
      "health": 45,
      "max_health": 80,
      "breath": 5,
      "max_breath": 60,
      "stamina": 20,
      "swimming": 40
    },
    "conditions": {
      "exhaustion": {
        "severity": 70,
        "effect": "reduced_stamina"
      },
      "hypothermia": {
        "severity": 30,
        "progression_rate": 5
      }
    },
    "trapped": {
      "reason": "fallen_debris",
      "can_move": false,
      "requires_rescue": true
    },
    "disposition": "desperate"
  }
}
```

**Player Actor:**
```json
{
  "properties": {
    "stats": {
      "health": 100,
      "max_health": 100,
      "breath": 60,
      "max_breath": 60,
      "swimming": 50,
      "strength": 60
    }
  }
}
```

**Breathing Reed Item:**
```json
{
  "id": "item_breathing_reed",
  "name": "hollow reed",
  "properties": {
    "portable": true,
    "equipment_slot": "tool",
    "provides_breathing": true,
    "breathing_range": "surface_to_shallow",
    "fragile": true
  }
}
```

**Rope Item:**
```json
{
  "id": "item_rope",
  "name": "rope",
  "properties": {
    "portable": true,
    "length": 50,
    "strength": 100,
    "uses": ["climbing", "tying", "rescue"]
  }
}
```

### Interactions

1. **Breath Management**:
   - When actor's `focused_on` changes to part with `breathable: false`:
     - Begin breath countdown
     - Each turn in non-breathable area: `breath` decreases by 10
   - When `breath ≤ 0`:
     - Actor takes drowning damage each turn (health decreases rapidly)
   - Moving back to breathable area: `breath` regenerates

2. **Finding the Sailor**:
   - Player must navigate to `part_tunnel_end`
   - Approaching middle section: automatic check if player can swim
   - Player's `swimming` skill determines breath efficiency
   - Higher swimming = slower breath depletion

3. **Sailor's Deteriorating State**:
   - Sailor starts with low `breath` (5 turns until drowning)
   - Each turn: `hypothermia.severity` increases
   - If sailor's `breath` reaches 0 before rescue:
     - Sailor becomes unconscious
     - Player has limited turns to revive before death

4. **Rescue Options**:

   **Option A - Provide Breathing Reed:**
   - Player gives reed to sailor
   - Sailor can use it to breathe if water level allows
   - Stabilizes sailor's `breath`, stops drowning
   - Player still needs to free sailor from debris

   **Option B - Rope Rescue:**
   - Player attaches rope to sailor
   - Strength check to pull debris
   - If successful: sailor can be guided back through water
   - Sailor's low `stamina` means they need help swimming

   **Option C - Clear Debris:**
   - Player examines debris blocking sailor
   - Requires strength check to move
   - Takes multiple turns (breath depleting)
   - Success: sailor can swim out independently if they have breath

5. **Escorting Exhausted Sailor**:
   - Sailor's `exhaustion` means they can't swim well
   - Player must `guide` or `support` sailor
   - This slows player's movement (2 turns per section instead of 1)
   - Both actors' breath depleting simultaneously
   - If either runs out of breath, both in danger

6. **Post-Rescue Care**:
   - Once in safe area, sailor needs treatment
   - Hypothermia continues to worsen unless treated
   - Player can provide warm clothes, build fire, or fetch healer
   - Sailor's `disposition` changes to `grateful` if rescued
   - May offer information, items, or become ally

### Design Questions Raised

- **Breath/oxygen system**: Generic resource for all environmental hazards?
- **Escort mechanics**: How to move with/guide other actors?
- **Multiple simultaneous threats**: Drowning + hypothermia + exhaustion?
- **Time pressure**: How to create urgency without arbitrary timers?
- **Unconscious actors**: How to interact with incapacitated NPCs?
- **Skill checks**: When are they automatic vs player-initiated?

---

## Use Case 6: The Injured Merchant (Medical Aid, Trade, Escort Quest)

### Scenario
A merchant has been attacked by bandits and is injured on the road. The player can provide first aid, escort them to safety, and trade with them. The merchant's inventory includes medicine. The player's medical skill determines treatment effectiveness.

### Spatial Context
- Road location with limited cover
- Nearby town (safety) 3 locations away
- Merchant's wagon (lootable if merchant dies)

### Actor Properties

**Injured Merchant NPC:**
```json
{
  "id": "npc_merchant_helena",
  "name": "Merchant Helena",
  "location": "loc_forest_road",
  "properties": {
    "stats": {
      "health": 30,
      "max_health": 80,
      "stamina": 40,
      "movement_speed": "slow"
    },
    "conditions": {
      "bleeding": {
        "severity": 60,
        "health_loss_per_turn": 3,
        "treatable_by": ["bandage", "healing_magic", "medical_skill"]
      },
      "pain": {
        "severity": 70,
        "effect": "reduced_mobility"
      }
    },
    "inventory": ["item_bandages", "item_health_potion", "item_trade_goods"],
    "services": {
      "trading": {
        "offered": true,
        "markup": 20,
        "will_barter": true
      }
    },
    "ai": {
      "will_flee": false,
      "needs_escort": true,
      "destination": "loc_town",
      "trust_level": 50
    },
    "disposition": "frightened"
  }
}
```

**Player (Skilled Healer):**
```json
{
  "properties": {
    "stats": {
      "health": 100,
      "max_health": 100
    },
    "skills": {
      "medicine": 70,
      "combat": 60,
      "persuasion": 50
    },
    "inventory": ["item_bandages", "item_healing_herbs"]
  }
}
```

**Bandage Item:**
```json
{
  "id": "item_bandages",
  "name": "bandages",
  "properties": {
    "medical": true,
    "treats": ["bleeding", "minor_wounds"],
    "effectiveness": 50,
    "uses_remaining": 3
  }
}
```

### Interactions

1. **Initial Assessment**:
   - Player examines merchant
   - Reveals merchant's `conditions` and severity
   - Player's `skills.medicine` provides more detailed diagnosis
   - High medicine: reveals exact health loss per turn

2. **Providing First Aid**:
   - Player uses `treat` or `bandage` command on merchant
   - Roll: player's `skills.medicine` + item's `effectiveness`
   - Success: reduces `bleeding.severity`
   - Great success: stops bleeding entirely (severity = 0)
   - Failure: no effect, wastes use of bandage

3. **Bleeding Progression**:
   - Each turn: merchant loses `health_loss_per_turn` from bleeding
   - If untreated and `health` reaches 0: merchant dies
   - Creates time pressure for player to act

4. **Trading While Injured**:
   - Merchant can still trade despite injuries
   - Player can buy health potions from merchant
   - Merchant's `pain` condition affects prices (desperate for help)
   - If player helps first: merchant's `trust_level` increases, better prices

5. **Escort Mission**:
   - Merchant asks player to escort to town
   - Merchant has `movement_speed: "slow"` due to injuries
   - Movement to adjacent locations takes 2 turns instead of 1
   - During escort:
     - Random encounter chance (bandits returning?)
     - Player must protect merchant
     - Merchant continues bleeding if not fully treated

6. **Combat During Escort**:
   - If bandits attack while escorting:
     - Merchant cannot fight effectively (low health, pain)
     - Player must defend both themselves and merchant
     - Merchant may die if player fails to protect them
   - Positioning: player tries to keep merchant behind them

7. **Rescue Outcomes**:
   - If merchant reaches town alive:
     - Rewards player with gold, trade discount, or rare item
     - Becomes long-term trading contact
     - `disposition` changes to `grateful` and `friendly`
   - If merchant dies:
     - Player can loot merchant's wagon
     - Moral consequences (reputation system?)
     - Merchant's allies may seek player out

### Design Questions Raised

- **Medical skill system**: Generic skills or specialized medical actions?
- **Treatment effectiveness**: Item quality + skill vs fixed effects?
- **NPC movement speed**: How are movement rates handled?
- **Escort mechanics**: NPCs following player between locations?
- **Reputation**: Do player's choices affect relationships with groups?
- **Moral choices**: Death consequences beyond losing potential ally?

---

## Use Case 7: The Spider Swarm (Hive Mind, Venom, Environmental Control)

### Scenario
Giant spiders in a web-covered gallery (from Room #6) hunt as a coordinated swarm. Individual spiders are weak but venomous. Damaging webs alerts all spiders. Player can burn webs, use repellent, or navigate carefully. Spiders use web-based tactics.

### Spatial Context (from Room #6)
- `part_gallery_north_wall`: `covered_in_webs: true`, `web_integrity: 100`
- `part_gallery_east_wall`: Heavy webs, spider nests
- `part_gallery_south_wall`: Moderate webs
- Center area: Relatively clear

### Actor Properties

**Giant Spider NPC:**
```json
{
  "id": "npc_spider_1",
  "name": "giant spider",
  "location": "part_gallery_north_wall",
  "properties": {
    "stats": {
      "health": 20,
      "max_health": 20,
      "agility": 80,
      "strength": 30
    },
    "body": {
      "form": "arachnid",
      "limbs": ["leg", "leg", "leg", "leg", "leg", "leg", "leg", "leg"],
      "features": ["fangs", "spinnerets"],
      "size": "large",
      "movement": ["walk", "climb", "web_swing"]
    },
    "combat": {
      "attacks": [
        {
          "name": "venomous_bite",
          "damage": 8,
          "venom": {
            "type": "spider_venom",
            "potency": 40,
            "effect": "paralysis"
          }
        },
        {
          "name": "web_spray",
          "damage": 0,
          "effect": "entangle",
          "range": "near"
        }
      ],
      "evasion": 70
    },
    "ai": {
      "hive_mind": true,
      "hive_id": "gallery_spiders",
      "awareness_shared": true,
      "tactical_coordination": true
    },
    "web_affinity": {
      "bonus_on_webs": 30,
      "alerted_by_web_damage": true,
      "can_sense_vibrations": true
    }
  }
}
```

**Web Environment (Part Property):**
```json
{
  "id": "part_gallery_north_wall",
  "properties": {
    "covered_in_webs": true,
    "web_integrity": 100,
    "traversal_difficulty": 60,
    "burnable": true,
    "spider_population": 4
  }
}
```

**Spider Repellent Item:**
```json
{
  "id": "item_spider_repellent",
  "name": "pungent incense",
  "properties": {
    "repels": ["arachnid", "insect"],
    "radius": "near",
    "duration": 10,
    "consumable": true
  }
}
```

**Torch Item:**
```json
{
  "id": "item_torch",
  "name": "torch",
  "properties": {
    "light_source": true,
    "weapon": true,
    "damage": 5,
    "damage_type": "fire",
    "burns_webs": true,
    "duration": 30
  }
}
```

### Interactions

1. **Web Detection**:
   - When player approaches web-covered part:
     - Spiders with `can_sense_vibrations` detect movement
     - If player moves cautiously (sneak), can avoid detection
     - If player damages webs, all spiders with `alerted_by_web_damage` activate

2. **Hive Mind Coordination**:
   - All spiders share `hive_id: "gallery_spiders"`
   - When one spider detects player, all become aware (shared awareness)
   - Spiders coordinate attacks:
     - Some use `web_spray` to entangle player
     - Others position for venomous bites
     - Take turns attacking to maximize effectiveness

3. **Venomous Bite**:
   - Spider's bite does immediate damage (8)
   - Venom application:
     - Adds `spider_venom` condition to player
     - `potency: 40` determines severity
     - Effect is `paralysis`: reduces player's agility and movement
   - Multiple bites: venom potency stacks

4. **Web Entanglement**:
   - Spider uses `web_spray` attack
   - If hits, player receives `entangled` condition
   - Effects:
     - Cannot move between locations
     - Reduced combat effectiveness
     - Must use action to break free (strength check)

5. **Burning Webs**:
   - Player uses torch on web-covered parts
   - Web's `burnable: true` allows it
   - Consequences:
     - `web_integrity` decreases
     - Spiders lose terrain advantage (bonus_on_webs)
     - Fire may spread, damaging multiple web areas
     - Alerts all spiders immediately (hive mind)

6. **Spider Terrain Advantage**:
   - When fighting on web-covered surfaces:
     - Spiders get `bonus_on_webs: 30` to evasion
     - Spiders can use `movement: "web_swing"` for tactical repositioning
     - Player has reduced mobility (high `traversal_difficulty`)

7. **Repellent Strategy**:
   - Player uses repellent incense
   - Creates zone of `radius: "near"` around player
   - Spiders with `body.form: "arachnid"` won't approach
   - Lasts `duration: 10` turns
   - Allows safe passage through webs without combat

8. **Swarm Tactics**:
   - Spiders attack in waves rather than all at once
   - First wave: entangle with webs
   - Second wave: venomous bites on immobilized target
   - If player defeats some spiders:
     - Remaining spiders may retreat to nests
     - Regroup and return with reinforcements

### Design Questions Raised

- **Hive mind AI**: How do multiple NPCs share awareness and coordinate?
- **Environmental bonuses**: How are terrain modifiers applied?
- **Status effect stacking**: Cumulative venom from multiple sources?
- **Area effects**: Fire spreading, repellent zones?
- **Movement types**: Do body features enable special movement?
- **Swarm behavior**: Waves of enemies vs all-at-once encounters?

---

## Use Case 8: The Clockwork Servant (Non-Hostile Automation, Programming, Repair)

### Scenario
A damaged clockwork servant in a mansion needs repairs and reprogramming. It can serve food, provide information, or guard areas depending on programming. Player with mechanical skills can repair and customize it. It has no sentience, only programmed responses.

### Spatial Context
- Servant standing in main hall
- Workshop available with repair tools
- Kitchen, library, armory (potential assignment areas)

### Actor Properties

**Clockwork Servant:**
```json
{
  "id": "npc_clockwork_servant",
  "name": "clockwork butler",
  "location": "loc_main_hall",
  "properties": {
    "stats": {
      "structural_integrity": 60,
      "max_structural_integrity": 100,
      "power_level": 40,
      "max_power_level": 100
    },
    "body": {
      "form": "construct",
      "material": "brass_and_steel",
      "limbs": ["arm", "arm", "leg", "leg"],
      "features": ["gears", "springs", "wind_up_key"],
      "size": "human",
      "weight": "heavy"
    },
    "mechanical": {
      "functional": true,
      "damaged_components": ["speech_module", "right_arm_servo"],
      "maintenance_required": true,
      "power_source": "spring_mechanism",
      "running_time_remaining": 20
    },
    "programming": {
      "current_task": "idle",
      "available_tasks": ["serve_food", "provide_information", "guard_area", "clean", "fetch"],
      "task_restrictions": {
        "serve_food": {"requires": ["kitchen_access", "functional_arms"]},
        "guard_area": {"requires": ["functional_limbs", "power_level_above_50"]}
      },
      "behavior_mode": "butler",
      "hostile": false
    },
    "knowledge_base": {
      "mansion_layout": 100,
      "resident_information": 80,
      "etiquette": 90,
      "historical_events": 60
    },
    "disposition": "neutral"
  }
}
```

**Player (Skilled Mechanic):**
```json
{
  "properties": {
    "skills": {
      "mechanics": 75,
      "engineering": 60
    },
    "inventory": ["item_repair_tools", "item_oil", "item_spare_gears"]
  }
}
```

**Spare Parts Items:**
```json
{
  "id": "item_speech_module",
  "name": "replacement speech module",
  "properties": {
    "component_type": "speech_module",
    "compatible_with": ["clockwork_constructs"],
    "quality": 80
  }
}
```

### Interactions

1. **Diagnosis**:
   - Player examines servant
   - Basic examination reveals `damaged_components`
   - Player's `skills.mechanics` reveals more detail:
     - Low skill: "Something is wrong with the speech and arm"
     - High skill: "Speech module crystal cracked, right servo gear stripped"
   - Can also assess `structural_integrity` and `power_level`

2. **Winding the Spring (Power)**:
   - Servant's `power_level` depletes over time
   - Player can use `wind` command on servant
   - Restores power_level to maximum
   - Each winding provides `running_time_remaining: 20` turns
   - If power reaches 0: servant becomes inactive (immobile)

3. **Repairing Components**:
   - Player needs appropriate spare part
   - Uses `repair` command with part in inventory
   - Skill check: player's `mechanics` vs component complexity
   - Success:
     - Removes component from `damaged_components`
     - Increases `structural_integrity`
     - Enables restricted tasks that required that component
   - Failure:
     - May further damage component
     - Wastes spare part

4. **Programming Tasks**:
   - Player uses `program` or `command` to assign tasks
   - Example: "program butler to guard library"
   - Checks:
     - Is task in `available_tasks`?
     - Are task requirements met? (check `task_restrictions`)
     - Does servant have enough power?
   - If all checks pass:
     - `current_task` changes to new task
     - Servant moves to appropriate location
     - Begins performing task

5. **Information Queries**:
   - Player can ask servant about various topics
   - Servant's response quality based on `knowledge_base`
   - Example: "ask butler about the mansion owner"
     - Checks `resident_information: 80`
     - Provides detailed, useful information
   - If speech_module damaged:
     - Garbled or incomplete responses
     - May provide written responses instead (slower)

6. **Servant Services**:
   - **Serve Food**: Brings food items from kitchen to player
   - **Guard Area**: Prevents NPCs from entering assigned location
   - **Fetch**: Retrieves specific items from known locations
   - **Clean**: Maintains tidiness (cosmetic, or could find hidden items)

7. **Power Management**:
   - Servant performs tasks based on `current_task`
   - Each action consumes `power_level`
   - Complex tasks (guard, fetch) consume more power than simple ones
   - If power depletes during task:
     - Servant stops mid-task
     - Returns to idle location if able
     - Becomes inactive if too low

8. **Customization** (Advanced):
   - Player with high `engineering` skill can reprogram
   - Add new tasks to `available_tasks`
   - Modify behavior patterns
   - Change `behavior_mode` (butler to guard, etc.)

### Design Questions Raised

- **Construct actor type**: How do non-living actors differ from living ones?
- **Power/energy systems**: Generic resource like health but for machines?
- **Component damage**: Specific parts vs general integrity?
- **Task programming**: Scripting NPC behaviors at runtime?
- **Knowledge bases**: How do NPCs store and retrieve information?
- **Skill-gated interactions**: What can players do vs NPCs with skills?

---

## Use Case 9: Guardian Statue Hall (Tactical Construct Combat)

### Scenario
Stone golems stand dormant in a grand hall. When the player approaches the center, they activate and attack. The player can take cover behind pillars, deactivate golems via wall runes, or fight them directly. Golems are limbless constructs with powerful attacks and immunity to biological effects.

### Spatial Context (from Room #2)
- `part_hall_entrance`: Safe zone, `safe_distance: true`
- `part_hall_center`: Combat zone, `exposed: true`
- Multiple `item_pillar` entities with `provides_cover: true`
- `part_hall_north_wall`: Has deactivation rune

### Actor Properties

**Stone Golem NPC:**
```json
{
  "id": "npc_golem_1",
  "name": "stone golem",
  "location": "part_hall_center",
  "properties": {
    "health": 200,
    "max_health": 200,
    "body": {
      "form": "construct",
      "material": "stone",
      "limbs": [],
      "features": ["massive_body"],
      "size": "large"
    },
    "attacks": [
      {
        "name": "charge",
        "damage": 30,
        "range": "near",
        "description": "The golem charges forward with crushing force"
      },
      {
        "name": "slam",
        "damage": 50,
        "range": "touch",
        "description": "A devastating overhead slam"
      }
    ],
    "armor": 20,
    "immunities": ["poison", "disease", "bleeding"],
    "ai": {
      "hostile": false,
      "activation_trigger": "player_enters_center",
      "morale": 100,
      "target_priority": "nearest_exposed"
    }
  }
}
```

**Pillar Item:**
```json
{
  "id": "item_pillar_1",
  "name": "marble pillar",
  "location": "loc_guardian_hall",
  "properties": {
    "portable": false,
    "cover_value": 80,
    "destructible": true,
    "health": 100
  }
}
```

**Wall Part with Rune:**
```json
{
  "id": "part_hall_north_wall",
  "properties": {
    "has_rune": true,
    "rune_effect": "deactivate_golems"
  }
}
```

### Interactions

1. **Activation Trigger**:
   - When player uses `approach part_hall_center`
   - All golems with `activation_trigger: "player_enters_center"` become `hostile: true`
   - Golems take action after player command completes

2. **Golem Attacks Player**:
   - Golem behavior selects attack based on range
   - "charge" used if player is "near", "slam" if at "touch" range
   - If player has `posture: "cover"`:
     - Attack damage reduced by pillar's `cover_value` percentage
     - Excess damage may damage pillar's `health`
   - Damage applied: attack damage - player armor

3. **Player Attacks Golem**:
   - Player uses `attack golem` command
   - Golem's `armor` reduces incoming damage
   - Golem's `body.material: "stone"` provides natural armor
   - Golem's `immunities` prevent biological conditions

4. **Pillar Destruction**:
   - After taking damage, pillar's `health` decreases
   - If `health ≤ 0`, pillar collapses
   - Player loses cover, `posture` clears to null
   - Player must find another pillar

5. **Strategic Positioning**:
   - Player can `approach` different pillars to maintain cover
   - Player: `hide behind pillar` sets posture to "cover"
   - Moving costs turns, golem may attack during movement
   - AI checks player's `focused_on` to determine if player is exposed

6. **Non-Combat Solution**:
   - Player: `examine north wall` (reveals rune inscription)
   - Player: `activate rune` (requires being near wall)
   - Wall's `on_activate` behavior: sets all golems' `ai.hostile = false`
   - Golems return to starting positions

### Design Questions Raised

- **Construct body type**: How do non-living constructs differ mechanically?
- **Material-based immunities**: Should material auto-grant immunities?
- **Attack selection AI**: Simple range-based or more complex?
- **Cover mechanics**: How is damage redirected to cover objects?
- **Environmental deactivation**: Generic pattern for shutting down enemies?

---

## Use Case 10: Spider-Infested Gallery (Swarm Combat with Environment)

### Scenario
Giant spiders inhabit a web-covered gallery. Individual spiders are weak but venomous and work in packs. Damaging webs alerts the swarm. Player can burn webs to remove spider advantages, use repellent, or navigate carefully. Spiders use web-based tactics and coordinate through simple pack behavior.

### Spatial Context (from Room #6)
- `part_gallery_north_wall`: `web_density: "heavy"`, `web_bonus_attacks: 20`
- `part_gallery_east_wall`: Heavy webs, spider nests
- `part_gallery_center`: `web_density: "light"`

### Actor Properties

**Giant Spider NPC:**
```json
{
  "id": "npc_spider_1",
  "name": "giant spider",
  "location": "part_gallery_north_wall",
  "properties": {
    "health": 20,
    "max_health": 20,
    "body": {
      "form": "arachnid",
      "features": ["fangs", "spinnerets"],
      "size": "large",
      "movement": ["climb", "web_swing"]
    },
    "attacks": [
      {
        "name": "venomous_bite",
        "damage": 8,
        "applies_condition": {
          "name": "spider_venom",
          "severity": 40,
          "effect": "agility_reduced",
          "damage_per_turn": 1,
          "duration": 10
        }
      },
      {
        "name": "web_spray",
        "damage": 0,
        "applies_condition": {
          "name": "entangled",
          "severity": 50,
          "effect": "cannot_move",
          "break_difficulty": 30
        }
      }
    ],
    "ai": {
      "hostile": false,
      "pack_id": "gallery_spiders",
      "follows_alpha": "npc_spider_alpha",
      "alerted_by": "web_damage",
      "morale": 50,
      "flee_threshold": 10
    }
  }
}
```

**Spider Alpha:**
```json
{
  "id": "npc_spider_alpha",
  "name": "broodmother",
  "properties": {
    "health": 40,
    "max_health": 40,
    "body": {
      "form": "arachnid",
      "size": "huge"
    },
    "attacks": [
      {
        "name": "venomous_bite",
        "damage": 12,
        "applies_condition": {
          "name": "spider_venom",
          "severity": 60,
          "damage_per_turn": 2,
          "duration": 15
        }
      }
    ],
    "ai": {
      "hostile": false,
      "pack_role": "alpha",
      "pack_id": "gallery_spiders",
      "alerted_by": "web_damage",
      "morale": 80
    }
  }
}
```

**Gallery Part with Webs:**
```json
{
  "id": "part_gallery_north_wall",
  "properties": {
    "web_density": "heavy",
    "web_bonus_attacks": 20,
    "web_integrity": 100,
    "burnable": true
  }
}
```

**Torch Item:**
```json
{
  "id": "item_torch",
  "name": "torch",
  "properties": {
    "light_source": true,
    "damage_type": "fire",
    "damages_webs": true,
    "burn_amount": 50
  }
}
```

**Repellent Item:**
```json
{
  "id": "item_repellent",
  "name": "pungent incense",
  "properties": {
    "repels": ["arachnid"],
    "duration": 10,
    "radius": "near"
  }
}
```

### Interactions

1. **Web Detection**:
   - When player approaches web-covered part
   - If player moves carefully (uses `sneak`): not detected
   - Otherwise: spiders with `alerted_by: "web_damage"` become hostile
   - Deterministic - no random detection

2. **Pack Coordination**:
   - After alert, followers check alpha's hostility
   - If alpha is hostile, all followers become hostile
   - Followers copy alpha's target selection
   - Simple follow-the-leader behavior

3. **Venomous Bite Attack**:
   - Spider uses "venomous_bite" attack
   - Applies immediate damage (8 or 12)
   - Adds `spider_venom` condition from `applies_condition`
   - Condition deals damage per turn and reduces agility
   - Multiple bites stack severity

4. **Web Spray Entanglement**:
   - Spider uses "web_spray" attack
   - Applies `entangled` condition
   - Effect: `cannot_move` prevents location changes
   - Player must `break free` (costs turn, automatic success)
   - Or take damage to break out faster

5. **Web Environmental Advantage**:
   - Spiders in parts with heavy `web_density` get bonus
   - Part's `web_bonus_attacks` adds 20% to spider damage
   - Player movement slowed in heavy webs (costs extra turn)
   - Spiders can use `movement: "web_swing"` for repositioning

6. **Burning Webs**:
   - Player: `use torch on webs` or `burn webs`
   - Torch has `damages_webs: true`
   - Reduces part's `web_integrity` by torch's `burn_amount`
   - If integrity ≤ 0: `web_density` reduced from "heavy" to "light"
   - Removes spider bonuses
   - Alerts all spiders immediately

7. **Repellent Strategy**:
   - Player: `use repellent`
   - Applies condition to player: `repelling_arachnids` for 10 turns
   - Spiders with `body.form: "arachnid"` won't approach player
   - Allows safe passage through gallery
   - Deterministic protection - no failure chance

8. **Morale and Retreat**:
   - When spider takes damage bringing health below threshold
   - If `health < (max_health * flee_threshold / 100)`: morale drops to 0
   - Spider attempts to flee to nest location
   - If alpha flees, all followers flee too

### Design Questions Raised

- **Condition stacking**: How do multiple venomous bites accumulate?
- **Break free mechanics**: Deterministic or contested?
- **Pack coordination scope**: How far can pack communication reach?
- **Environmental bonuses**: Generic system for terrain modifiers?
- **Alert propagation**: How do pack members learn of threats?

---

## Use Case 11: Bank Vault Infiltration (Stealth & Guard AI)

### Scenario
A bank vault with multiple guards on patrol. The player can infiltrate via stealth, social engineering, or combat. Guards have morale - they may flee if outnumbered or after witnessing violence. Guards coordinate to some degree. Player can hide behind pillars and in shadows.

### Spatial Context (from Room #81)
- `part_vault_entrance`: High visibility, guard station
- `part_vault_main`: Medium visibility, safety deposit boxes
- `part_vault_ceiling`: Vent access for stealth entry
- Multiple pillars providing cover

### Actor Properties

**Guard NPC:**
```json
{
  "id": "npc_guard_1",
  "name": "security guard",
  "location": "part_vault_entrance",
  "properties": {
    "health": 80,
    "max_health": 80,
    "body": {
      "form": "humanoid",
      "size": "medium"
    },
    "attacks": [
      {
        "name": "baton_strike",
        "damage": 15,
        "applies_condition": {
          "name": "stunned",
          "severity": 30,
          "duration": 2
        }
      }
    ],
    "ai": {
      "hostile": false,
      "pack_id": "bank_guards",
      "pack_role": "patrol",
      "follows_alpha": "npc_guard_chief",
      "morale": 70,
      "flee_threshold": 30,
      "detection_radius": "same_part",
      "alerted_by": "player_visible"
    },
    "disposition": "professional"
  }
}
```

**Guard Chief:**
```json
{
  "id": "npc_guard_chief",
  "name": "chief guard",
  "properties": {
    "health": 100,
    "max_health": 100,
    "attacks": [
      {
        "name": "baton_strike",
        "damage": 20
      }
    ],
    "ai": {
      "hostile": false,
      "pack_role": "alpha",
      "pack_id": "bank_guards",
      "morale": 90,
      "flee_threshold": 20
    }
  }
}
```

**Vault Part:**
```json
{
  "id": "part_vault_entrance",
  "properties": {
    "visibility": "high",
    "guard_patrol": true,
    "alert_level": 0
  }
}
```

**Pillar (Cover):**
```json
{
  "id": "item_pillar_1",
  "properties": {
    "portable": false,
    "cover_value": 70,
    "blocks_line_of_sight": true
  }
}
```

### Interactions

1. **Detection System**:
   - Guards check if player is in `detection_radius` (same part)
   - If player has `posture: "cover"` behind pillar: not detected
   - If player has `posture: "sneaking"` and part visibility is "low": not detected
   - Otherwise: guard becomes hostile, alerts pack

2. **Pack Alert Propagation**:
   - When one guard detects player, sets `ai.hostile: true`
   - Guard shouts alert (flavor)
   - All guards with same `pack_id` become hostile
   - Simple broadcast - all pack members alerted instantly

3. **Combat Engagement**:
   - Guard uses `baton_strike` attack
   - Moderate damage but may apply `stunned` condition
   - Stunned reduces player actions (flavor only or skip turn)

4. **Morale System**:
   - Each guard tracks individual `morale`
   - When guard takes damage: `morale -= damage_taken / 2`
   - When ally is defeated: all guards `morale -= 10`
   - If `morale < flee_threshold`: guard flees to exit
   - Alpha fleeing causes mass rout (all followers flee)

5. **Intimidation**:
   - Player can `intimidate guards` (new command)
   - Reduces all visible guards' morale by 20
   - If morale drops below threshold: guards flee
   - Non-lethal solution to encounter

6. **Stealth Entry**:
   - Player enters via `part_vault_ceiling` vent
   - Sets player position in vault without entering through entrance
   - Bypasses entrance guards entirely
   - Requires finding and opening vent externally

7. **Cover Tactics**:
   - Player: `hide behind pillar`
   - Sets `posture: "cover"`, `focused_on: pillar_id`
   - Pillar's `blocks_line_of_sight` prevents detection
   - Player can peek out to observe guards

8. **Social Engineering** (simplified):
   - Player with guard uniform (item) reduces detection chance
   - If player's `disposition` with guards is "friendly": not attacked
   - Guards check relationship before engaging
   - Allows talking way past security

### Design Questions Raised

- **Visibility system**: How are line-of-sight and detection modeled?
- **Alert states**: Global alarm vs individual guard awareness?
- **Morale calculation**: Linear reduction or thresholds?
- **Non-lethal options**: Stun, intimidate, befriend - how to balance?
- **Stealth posture**: How does sneaking interact with normal movement?

---

## Use Case 12: Multi-Phase Boss Arena (Environmental Boss Fight)

### Scenario
A powerful elemental boss in an arena with multiple platforms and environmental hazards. The boss has different attacks based on its health/phase. Player must activate elemental vents to damage the boss while avoiding its attacks. Boss behavior changes as it takes damage. Cover and positioning are critical.

### Spatial Context (from Room #91)
- `part_arena_center_platform`: Main fighting area, stable
- `part_arena_north_platform`: Near fire vent, unstable
- `part_arena_south_platform`: Near ice vent, stable
- Multiple pillars for cover

### Actor Properties

**Elemental Boss:**
```json
{
  "id": "npc_boss_inferno",
  "name": "Inferno Titan",
  "location": "part_arena_center_platform",
  "properties": {
    "health": 500,
    "max_health": 500,
    "body": {
      "form": "elemental",
      "material": "living_flame",
      "size": "huge"
    },
    "attacks": [
      {
        "name": "flame_breath",
        "damage": 30,
        "range": "area",
        "applies_condition": {
          "name": "burning",
          "severity": 40,
          "damage_per_turn": 5,
          "duration": 5
        }
      },
      {
        "name": "ground_pound",
        "damage": 40,
        "range": "area",
        "effect": "knockback"
      },
      {
        "name": "flame_whip",
        "damage": 25,
        "range": "melee"
      }
    ],
    "immunities": ["burning", "poison"],
    "weaknesses": {
      "ice": 200
    },
    "ai": {
      "hostile": true,
      "morale": 100,
      "phase": 1,
      "berserk_threshold": 30
    }
  }
}
```

**Arena Part (North Platform):**
```json
{
  "id": "part_arena_north_platform",
  "properties": {
    "stable": false,
    "element_active": false,
    "hazard_condition": {
      "name": "burning",
      "damage_per_turn": 5
    },
    "vent_id": "item_fire_vent"
  }
}
```

**Fire Vent:**
```json
{
  "id": "item_fire_vent",
  "name": "fire vent",
  "location": "part_arena_north_platform",
  "properties": {
    "portable": false,
    "activatable": true,
    "element": "fire",
    "affects_area": "part_arena_center_platform",
    "damage_to_area": 50
  }
}
```

**Ice Vent:**
```json
{
  "id": "item_ice_vent",
  "name": "ice vent",
  "location": "part_arena_south_platform",
  "properties": {
    "portable": false,
    "activatable": true,
    "element": "ice",
    "affects_area": "part_arena_center_platform",
    "damage_to_boss": 100,
    "applies_condition": {
      "name": "frozen",
      "severity": 50,
      "effect": "slowed"
    }
  }
}
```

### Interactions

1. **Phase-Based Combat**:
   - Boss starts in phase 1 (full health)
   - Phase 2 triggers at health < 66%: adds ground_pound to rotation
   - Phase 3 triggers at health < 33%: berserk mode, all attacks
   - Boss behaviors check current phase to select attacks

2. **Environmental Hazard Activation**:
   - Player must approach platform with vent
   - Player: `activate fire vent`
   - Vent damages boss (if weakness matches element)
   - Vent activates hazard on platform (burning damage per turn)
   - Player must leave platform quickly

3. **Boss Attack Selection**:
   - Normal phase: mostly flame_breath and flame_whip
   - Phase 2: adds ground_pound (area damage)
   - Berserk (health < berserk_threshold): uses most damaging attack available
   - Behavior selects based on player position and phase

4. **Burning Condition**:
   - Boss's flame_breath applies `burning` condition
   - Player takes damage per turn from burning
   - Can be extinguished with ice vent (applying ice to self)
   - Multiple flame breaths stack severity

5. **Weakness Exploitation**:
   - Boss has `weaknesses.ice: 200` (damage multiplier: 200%)
   - Ice vent deals 100 base * 2.0 = 200 damage
   - Fire vent deals normal damage (boss immune to burning)
   - Strategy: use ice vent despite personal risk

6. **Cover Mechanics**:
   - Player: `hide behind pillar`
   - Reduces damage from flame_breath (area attack)
   - Ground_pound ignores cover (shockwave)
   - Flame_whip can't reach player behind cover

7. **Platform Instability**:
   - North platform has `stable: false`
   - After activating fire vent, platform begins crumbling
   - Player has 2 turns to leave or takes fall damage
   - Creates time pressure on vent activation

8. **Boss Morale** (unusual for boss):
   - Boss starts with morale: 100 (never flees)
   - Morale drops when weaknesses exploited
   - At very low morale: boss uses desperate final attack
   - Still fights to death (flee_threshold: 0)

### Design Questions Raised

- **Phase transitions**: Triggered by health, time, or player actions?
- **Weakness system**: Elemental types, damage multipliers, or special vulnerabilities?
- **Area attacks**: How are they resolved? All targets in area?
- **Platform hazards**: Damage per turn based on position?
- **Boss-specific mechanics**: How much to generalize vs hardcode?

---

## Cross-Cutting Design Themes

After analyzing these twelve use cases, several cross-cutting themes emerge:

### 1. **Health vs Other Vital Stats**
- Health is insufficient for many scenarios
- Need: breath, hunger, power, structural integrity, stamina
- Question: Generic "vitals" system or specific properties?

### 2. **Body Characteristics Matter**
- Different forms: humanoid, quadruped, arachnid, construct
- Limbs affect actions: wolves use teeth, spiders use fangs, golems have none
- Material: flesh, stone, clockwork affects damage and healing
- Size and weight: affects movement, combat, what can be lifted

### 3. **Conditions Are Rich and Varied**
- Not just combat damage: disease, poison, exhaustion, hypothermia
- Progressive vs instant onset
- Treatable by different means (items, skills, NPCs, time)
- Multiple simultaneous conditions possible
- Some transfer between actors (contagious)

### 4. **NPCs as Service Providers**
- Healing, teaching, trading, information, escort
- Services have costs (barter, coin, favors)
- Relationship systems affect service quality and cost
- Some services require NPC skills/knowledge

### 5. **Environmental Properties Affect Actors**
- Water depth affects breathing
- Web coverage affects spider combat effectiveness
- Safe zones vs danger zones
- Positioning creates tactical options

### 6. **AI Needs Multiple Dimensions**
- Hostility (can change dynamically based on conditions)
- Morale/fear (can flee when low health)
- Coordination (pack tactics, hive minds)
- Needs (hunger drives behavior)
- Memory (relationships, past interactions)

### 7. **Time and Progression**
- Turn-based effects (poison damage, hunger increase)
- Duration-based (repellent lasts 10 turns)
- Progressive conditions (infection worsens over time)
- Urgency (sailor drowning, bleeding out)

### 8. **Skills and Knowledge**
- Player skills affect action outcomes (medicine, mechanics, swimming)
- NPCs have expertise (healer's herbalism, merchant's trading)
- Knowledge can be taught/learned
- Skills enable new interactions

---

## Required Property Categories

Based on these use cases, actors need properties in these categories:

### Core Vital Stats
```json
"stats": {
  "health": number,
  "max_health": number,
  "stamina": number,
  "breath": number,
  "hunger": number,
  "power_level": number,  // for constructs
  "morale": number
}
```

### Body Characteristics
```json
"body": {
  "form": "humanoid|quadruped|arachnid|construct|...",
  "material": "flesh|stone|clockwork|...",
  "limbs": ["arm", "arm", "leg", "leg"],  // or empty for limbless
  "features": ["teeth", "claws", "fangs", "wings"],
  "size": "tiny|small|medium|large|huge",
  "weight": "light|medium|heavy|massive",
  "movement": ["walk", "climb", "swim", "fly", "web_swing"]
}
```

### Conditions (Temporary States)
```json
"conditions": {
  "condition_name": {
    "severity": number,
    "type": "poison|disease|injury|exhaustion|...",
    "effect": "description of mechanical effect",
    "progression_rate": number,
    "duration_remaining": number,
    "treatable_by": ["item_types", "skills", "npc_services"]
  }
}
```

### Combat/Interaction Capabilities
```json
"combat": {
  "attacks": [
    {
      "name": "attack_name",
      "damage": number,
      "type": "piercing|blunt|fire|...",
      "range": "melee|near|far",
      "special_effects": {}
    }
  ],
  "armor": number,
  "evasion": number,
  "immunities": ["poison", "disease"],
  "resistances": {"fire": 50, "cold": 30}
}
```

### AI and Behavior
```json
"ai": {
  "hostile": boolean,
  "disposition": "friendly|neutral|hostile|desperate|...",
  "morale": number,
  "pack_id": "string",  // for coordinated groups
  "hive_mind": boolean,
  "flee_threshold": number,
  "target_priority": "nearest|weakest|strongest|...",
  "needs_escort": boolean,
  "destination": "location_id"
}
```

### Skills and Knowledge
```json
"skills": {
  "combat": number,
  "medicine": number,
  "mechanics": number,
  "swimming": number,
  "herbalism": number
},
"knowledge": {
  "subject_name": number  // 0-100 scale
}
```

### Services and Abilities
```json
"services": {
  "service_name": {
    "offered": boolean,
    "cost_type": "barter|coin|favor",
    "accepts": ["item_types"],
    "effectiveness": number
  }
}
```

### Relationships
```json
"social_bonds": {
  "actor_id": {
    "trust": number,
    "gratitude": number,
    "fear": number
  }
},
"disposition": "friendly|neutral|hostile|grateful|frightened|desperate"
```

---

## Open Design Questions

These use cases raise fundamental questions that any combat/interaction system must answer:

1. **When do actors act?** Turn-based? Event-driven? After each player action?

2. **How are distances modeled?** Same location = can interact? Need positioning levels?

3. **How do multiple conditions interact?** Stacking? Mutual exclusion? Priority?

4. **What's the role of randomness?** Dice rolls? Deterministic? Player-controlled outcomes?

5. **How are skills used?** Automatic checks? Player-initiated? Passive modifiers?

6. **How do relationships persist?** Global reputation? Individual memories? Faction systems?

7. **How is time modeled?** Turns? Real time? Action costs? Rest/waiting?

8. **How do body characteristics affect mechanics?** Flavor text only? Mechanical differences?

9. **How complex should AI be?** Simple scripts? Goal-driven? State machines?

10. **How do environmental effects work?** Location properties? Part properties? Active items?

11. **Can NPCs use items?** Equip weapons? Use healing items? Cast spells?

12. **How are non-combat interactions resolved?** Dialog trees? Skill checks? LLM-driven?

These questions should guide the combat system design and ensure it can support the full richness of actor interactions shown in these use cases.
