# Actor Interaction Simplified Use Cases

This document presents simplified use cases that maximize rich gameplay while minimizing author effort. These use cases focus on the **highly recommended features** from the evaluation:

1. Condition system (property-driven)
2. Multiple attack types (simple arrays)
3. Body characteristics (form, material, features)
4. Environmental properties affecting actors
5. NPC services framework
6. Morale/fear (simplified)
7. Progressive relationships (simple tracking)
8. Pack coordination (simplified - followers copy leaders)

**Deferred features:** Detailed skills, multiple vital stats, equipment slots, component damage, task programming.

---

## Use Case 1: The Infected Scholar (Disease & Simple Cure)

### Scenario
A scholar has contracted a fungal infection from basement spores. The player can cure them by giving an antifungal herb or become infected through proximity. No skill checks - just condition mechanics and item properties.

### Spatial Context
- **Library Main Floor**: Safe, no spores
- **Basement Parts**: Different spore concentrations
  - `part_basement_entrance`: `spore_level: "low"`
  - `part_basement_center`: `spore_level: "high"`

### Actor Properties

**Scholar NPC:**
```json
{
  "id": "npc_scholar",
  "name": "Scholar Aldric",
  "location": "loc_library",
  "properties": {
    "health": 60,
    "max_health": 100,
    "conditions": {
      "fungal_infection": {
        "severity": 80,
        "contagious_range": "touch",
        "damage_per_turn": 2,
        "progression_rate": 3
      }
    },
    "disposition": "friendly"
  }
}
```

**Player:**
```json
{
  "properties": {
    "health": 100,
    "max_health": 100,
    "resistances": {
      "disease": 30
    }
  }
}
```

**Antifungal Herb:**
```json
{
  "id": "item_silvermoss",
  "name": "silvermoss",
  "properties": {
    "cures": ["fungal_infection"],
    "cure_amount": 100
  }
}
```

### Interactions (Simplified)

1. **Environmental Infection** (deterministic):
   - Player at `part_basement_center` with `spore_level: "high"`
   - Each turn: add/increase `fungal_infection` severity by spore_level value
   - No roll - environmental hazards are predictable
   - Player's `resistances.disease` reduces severity increase

2. **Proximity Contagion** (deterministic):
   - When player is `focused_on` infected scholar
   - Scholar's condition has `contagious_range: "touch"`
   - Each turn near scholar: increase player infection severity by 5
   - Resistance reduces this

3. **Cure via Item**:
   - Player: `give silvermoss to scholar`
   - Scholar's `on_receive` behavior checks if item has `cures` array
   - If matches condition name: reduce severity by `cure_amount`
   - If severity ≤ 0: remove condition entirely

4. **Condition Progression** (automatic):
   - After each player command (turn):
   - For each condition on each actor:
     - Apply `damage_per_turn` to health
     - Increase `severity` by `progression_rate`
   - If health ≤ 0: actor becomes incapacitated

### Author Effort
- **Define** spore_level on location parts (1 property)
- **Define** fungal_infection condition on scholar (5 lines)
- **Define** cures property on herb item (2 lines)
- **No code needed** - all handled by core behaviors

---

## Use Case 2: The Guardian Golems (Spatial Combat with Cover)

### Scenario
Stone golems activate when player enters the hall center. Player can hide behind pillars for cover or deactivate golems via wall runes. Golems have different attacks and are immune to poison. No equipment system - attacks are intrinsic.

### Spatial Context
- `part_hall_entrance`: Safe zone
- `part_hall_center`: Combat trigger zone
- Multiple `item_pillar` entities provide cover
- `part_hall_north_wall`: Has deactivation rune

### Actor Properties

**Stone Golem:**
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
      "features": ["massive_body"]
    },
    "attacks": [
      {
        "name": "charge",
        "damage": 30,
        "range": "near"
      },
      {
        "name": "slam",
        "damage": 50,
        "range": "touch"
      }
    ],
    "armor": 20,
    "immunities": ["poison", "disease", "bleeding"],
    "ai": {
      "disposition": "neutral",
      "activation_trigger": "player_enters_center",
      "morale": 100
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

### Interactions (Simplified)

1. **Activation Trigger**:
   - When player uses `approach part_hall_center`
   - All golems in location with `activation_trigger: "player_enters_center"` become `disposition: "hostile"`
   - Golem takes action after player command completes

2. **Cover Mechanics**:
   - Player: `hide behind pillar`
   - Sets `player.posture = "cover"` and `player.focused_on = pillar_id`
   - When golem attacks, check player posture
   - If "cover": attack damage reduced by pillar's `cover_value` percentage
   - Excess damage may damage pillar's health

3. **Multiple Attacks** (behavior chooses):
   - Golem behavior selects from `attacks` array
   - Simple rule: use "charge" if player is "near", "slam" if at "touch" range
   - No complex AI - just range-based selection

4. **Material Immunity**:
   - Golem's `body.material: "stone"` and `immunities` array
   - When applying poison/disease/bleeding condition: check immunities first
   - Constructs automatically immune (checked by body.form)

5. **Deactivation**:
   - Player: `examine north wall` (reveals rune)
   - Player: `activate rune` (custom verb)
   - Wall's `on_activate` behavior: sets all golems' `ai.hostile = false`
   - Golems return to starting positions

### Author Effort
- **Define** golem with attacks array, body properties, immunities (15 lines)
- **Define** pillar with cover_value (3 lines)
- **Define** wall part with rune effect (3 lines)
- **Write** simple `on_activate` behavior for rune (10 lines of Python)

---

## Use Case 3: The Hungry Wolf Pack (Morale and Feeding)

### Scenario
Starving wolves are desperate but can be pacified with food. If combat starts, they use pack tactics. Individual wolves flee when injured. Repeated feeding creates friendship. No complex hunger stat - just binary (hungry/fed).

### Spatial Context
- Forest clearing with scattered trees
- Wolf den (safe zone for wolves)

### Actor Properties

**Alpha Wolf:**
```json
{
  "id": "npc_wolf_alpha",
  "name": "alpha wolf",
  "location": "loc_forest_clearing",
  "properties": {
    "health": 60,
    "max_health": 60,
    "body": {
      "form": "quadruped",
      "features": ["teeth", "claws"],
      "size": "medium"
    },
    "attacks": [
      {
        "name": "bite",
        "damage": 15,
        "type": "piercing"
      },
      {
        "name": "tackle",
        "damage": 8,
        "effect": "knockdown"
      }
    ],
    "ai": {
      "disposition": "hostile",
      "pack_role": "alpha",
      "pack_id": "winter_wolves",
      "morale": 60,
      "flee_threshold": 20,
      "needs": {
        "hungry": true
      }
    },
    "relationships": {}
  }
}
```

**Pack Member:**
```json
{
  "id": "npc_wolf_2",
  "name": "grey wolf",
  "properties": {
    "health": 45,
    "max_health": 45,
    "body": {
      "form": "quadruped",
      "features": ["teeth", "claws"]
    },
    "attacks": [
      {
        "name": "bite",
        "damage": 12
      }
    ],
    "ai": {
      "disposition": "hostile",
      "pack_role": "follower",
      "pack_id": "winter_wolves",
      "follows_alpha": "npc_wolf_alpha",
      "morale": 60,
      "flee_threshold": 15
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
    "edible_by": ["carnivore", "omnivore"],
    "satisfies": "hungry"
  }
}
```

### Interactions (Simplified)

1. **Simple Pack Coordination**:
   - After each turn, pack members check if `follows_alpha` is set
   - Copy alpha's `ai.disposition` state
   - If alpha flees, followers flee too
   - No complex tactics - just follow-the-leader

2. **Feeding to Pacify**:
   - Player: `give venison to alpha`
   - Wolf's `on_receive` behavior checks if item has `satisfies: "hungry"`
   - Sets wolf's `ai.needs.hungry = false`
   - Sets `ai.disposition` to `"neutral"`
   - Increments `relationships.player.gratitude` by 1

3. **Morale-Based Fleeing**:
   - When wolf takes damage, `on_damage` behavior checks health
   - If `health < (max_health * 0.3)`: set `ai.morale = 0`
   - If `ai.morale < flee_threshold`: wolf flees to den
   - Simple deterministic threshold

4. **Progressive Relationship**:
   - Each feeding increments `relationships.player.gratitude`
   - When gratitude ≥ 3: wolf's disposition becomes permanently `"friendly"`
   - Wolf may follow player or accept simple commands
   - Simple counter, no complex reputation

5. **Attack Selection**:
   - Wolf behavior chooses from `attacks` array
   - Simple rule: "bite" if target health > 50%, "tackle" otherwise
   - No randomness needed

### Author Effort
- **Define** wolves with attacks, pack_id, morale (20 lines per wolf)
- **Define** meat with satisfies property (2 lines)
- **Use** existing `give` command - no new commands needed
- **No AI scripting** - behaviors handle morale and pack following

---

## Use Case 4: The Healer and the Poisonous Garden

### Scenario
A garden contains toxic plants. A healer NPC offers services (cure poison, teach plant identification) in exchange for items. No skill system - player either knows plants or doesn't. Binary knowledge states.

### Spatial Context
- Garden with plant beds as location parts
- Healer's hut (safe zone)

### Actor Properties

**Healer NPC:**
```json
{
  "id": "npc_healer_elara",
  "name": "Healer Elara",
  "location": "loc_hermit_hut",
  "properties": {
    "health": 70,
    "max_health": 70,
    "services": {
      "cure_poison": {
        "accepts": ["rare_herbs", "gold"],
        "amount_required": 1
      },
      "teach_herbalism": {
        "accepts": ["gold"],
        "amount_required": 50,
        "grants": "knows_herbalism"
      }
    },
    "disposition": "neutral",
    "relationships": {}
  }
}
```

**Player (Initially Ignorant):**
```json
{
  "properties": {
    "health": 100,
    "max_health": 100,
    "knows": []
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
    "toxic_to_touch": true,
    "applies_condition": {
      "name": "nightshade_poison",
      "severity": 40,
      "damage_per_turn": 2,
      "duration": 20
    }
  }
}
```

**Safe Plant:**
```json
{
  "id": "item_golden_root",
  "name": "golden root",
  "location": "part_garden_south_bed",
  "properties": {
    "portable": false,
    "harvestable": true,
    "cures": ["nightshade_poison"],
    "cure_amount": 80
  }
}
```

### Interactions (Simplified)

1. **Binary Plant Knowledge**:
   - Player examines plant without "knows_herbalism"
   - Generic description: "A plant with dark berries"
   - Player examines plant WITH "knows_herbalism"
   - Full description: "Deadly nightshade - toxic to touch"
   - No skill checks - just boolean knowledge state

2. **Accidental Poisoning** (deterministic):
   - Player: `take nightshade` (without knowledge)
   - Plant's `on_take` behavior: if `toxic_to_touch` and player lacks knowledge
   - Applies condition from `applies_condition` property
   - No randomness - touching toxic plants always poisons

3. **Cure Service** (barter):
   - Player: `ask healer about poison`
   - Healer: "I can cure that for a rare herb or 50 gold"
   - Player: `give golden_root to healer`
   - Healer's `on_receive` behavior:
     - Checks if item is in `services.cure_poison.accepts`
     - If yes: removes all poison conditions from player
     - Increments `relationships.player.trust`

4. **Teaching Service** (barter):
   - Player: `ask healer about plants`
   - Healer: "I can teach herbalism for 50 gold"
   - Player: `give 50 gold to healer`
   - Healer's `on_receive` behavior:
     - Checks amount and type match `services.teach_herbalism`
   - Adds "knows_herbalism" to `player.properties.knows` array
   - Now player can identify plants safely

5. **Relationship Effect**:
   - High trust: healer accepts smaller payments
   - Check `relationships.player.trust` threshold
   - If trust ≥ 3: accepts half cost
   - Simple threshold, no complex calculation

### Author Effort
- **Define** healer with services (10 lines)
- **Define** plants with toxic/cure properties (5 lines each)
- **Define** knowledge strings (1 line per plant type)
- **Use** existing `give` and `ask` commands
- **Write** simple service handler behavior (20 lines, reusable)

---

## Use Case 5: The Drowning Sailor (Environmental Hazard)

### Scenario
A sailor is trapped in a flooded tunnel. Player must navigate non-breathable sections and rescue them. No stamina/swimming stats - just binary breath tracking. No equipment system - use simple item properties.

### Spatial Context
- `part_tunnel_entrance`: Ankle-deep, `breathable: true`
- `part_tunnel_middle`: Fully submerged, `breathable: false`
- `part_tunnel_end`: Small air pocket, `breathable: true`, sailor trapped here

### Actor Properties

**Sailor NPC:**
```json
{
  "id": "npc_sailor_marcus",
  "name": "Sailor Marcus",
  "location": "part_tunnel_end",
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
    "trapped": true,
    "disposition": "desperate"
  }
}
```

**Player:**
```json
{
  "properties": {
    "health": 100,
    "max_health": 100,
    "breath": 60,
    "max_breath": 60
  }
}
```

**Breathing Reed:**
```json
{
  "id": "item_breathing_reed",
  "name": "hollow reed",
  "properties": {
    "provides_breathing": true
  }
}
```

**Rope:**
```json
{
  "id": "item_rope",
  "name": "rope",
  "properties": {
    "can_pull_actors": true
  }
}
```

### Interactions (Simplified)

1. **Breath Tracking** (deterministic):
   - When player moves to part with `breathable: false`
   - Start breath countdown
   - Each turn in non-breathable area: `breath -= 10`
   - When `breath ≤ 0`: `health -= 10` per turn (drowning)
   - Moving to breathable area: `breath` regenerates to max

2. **Breathing Reed**:
   - Player holds reed (in inventory)
   - Reed's `provides_breathing` property checked
   - While holding: `breath` doesn't decrease in shallow water
   - Doesn't work in deep water (too far from surface)

3. **Finding Sailor**:
   - Player approaches `part_tunnel_end` (air pocket)
   - Sailor visible, health declining
   - Sailor's breath nearly depleted
   - Time pressure: sailor has ~5 turns before drowning

4. **Rescue via Rope**:
   - Player: `tie rope to sailor`
   - Player: `pull sailor`
   - Rope's `can_pull_actors` property allows this
   - Moves sailor to player's location
   - Requires multiple pulls to get through tunnel
   - Both breath meters declining

5. **Escorting**:
   - Sailor has `trapped: false` after rope use
   - But `conditions.exhaustion` with `cannot_swim` effect
   - Player must `guide sailor` back
   - Sailor follows player but can't move independently
   - Both vulnerable to drowning

6. **Post-Rescue**:
   - Once in safe area, sailor's `disposition` becomes "grateful"
   - Sailor's `relationships.player.gratitude = 5` (high value)
   - Sailor may offer information or items
   - Simple consequence - no complex reputation

### Author Effort
- **Define** breath stat on actors (2 lines)
- **Define** breathable property on parts (1 line each)
- **Define** provides_breathing on reed (1 line)
- **Define** can_pull_actors on rope (1 line)
- **Write** breath system behavior (30 lines, core engine)
- **Use** existing movement and item commands

---

## Use Case 6: The Injured Merchant (Medical Aid & Escort)

### Scenario
An injured merchant needs first aid and escort. Player can treat them with bandages and escort them to town. No detailed medical skills - treatment success is deterministic based on having right items. No stamina system - just wounded/not wounded.

### Spatial Context
- Road location (merchant's starting point)
- Town (safety) 3 locations away
- Forest road between (potential danger)

### Actor Properties

**Merchant NPC:**
```json
{
  "id": "npc_merchant_helena",
  "name": "Merchant Helena",
  "location": "loc_forest_road",
  "properties": {
    "health": 30,
    "max_health": 80,
    "conditions": {
      "bleeding": {
        "severity": 60,
        "damage_per_turn": 3,
        "treatable_by": ["bandages"]
      }
    },
    "inventory": ["item_trade_goods", "item_health_potion"],
    "services": {
      "trading": {
        "accepts": ["gold"],
        "sells": ["health_potion", "trade_goods"]
      }
    },
    "ai": {
      "needs_escort": true,
      "destination": "loc_town"
    },
    "disposition": "frightened",
    "relationships": {}
  }
}
```

**Bandages:**
```json
{
  "id": "item_bandages",
  "name": "bandages",
  "properties": {
    "treats": ["bleeding"],
    "cure_amount": 60,
    "consumable": true
  }
}
```

### Interactions (Simplified)

1. **Assessment** (no skill check):
   - Player: `examine merchant`
   - Reveals conditions and current health
   - Shows "bleeding severely, needs treatment"
   - No hidden information - transparent state

2. **Treatment** (deterministic):
   - Player: `use bandages on merchant`
   - Bandages have `treats: ["bleeding"]`
   - Reduces bleeding severity by `cure_amount`
   - If severity ≤ 0: removes condition
   - Bandages consumed
   - No skill check - just have right item

3. **Bleeding Progression**:
   - Each turn: merchant loses 3 health (from condition)
   - Creates time pressure
   - Player must act quickly
   - Deterministic countdown

4. **Trading While Injured**:
   - Merchant can still trade despite injuries
   - Player: `buy health potion from merchant`
   - Simple service interaction
   - Merchant accepts gold, transfers potion

5. **Building Trust**:
   - If player treats bleeding before trading:
   - Increments `relationships.player.trust`
   - If trust > 0: merchant offers discount
   - Simple threshold: trust = normal price, trust > 2 = 20% off

6. **Escort Mission**:
   - Player: `guide merchant to town`
   - Merchant follows player between locations
   - Merchant has `ai.needs_escort: true` and `destination`
   - Engine handles following behavior
   - No complex AI pathfinding

7. **Combat During Escort** (simplified):
   - If bandits attack en route
   - Merchant cannot fight (low health)
   - Player must defeat bandits alone
   - Merchant stays out of combat automatically
   - If merchant's health ≤ 0: escort fails

8. **Completion**:
   - Arriving at `loc_town` with merchant alive
   - Merchant's `relationships.player.gratitude = 5`
   - Merchant offers reward (gold or rare item)
   - Becomes permanent trading contact
   - Simple binary outcome: success or failure

### Author Effort
- **Define** merchant with conditions and services (15 lines)
- **Define** bandages with treats property (3 lines)
- **Define** bleeding condition (5 lines)
- **Use** existing `use` and `guide` commands
- **Write** simple escort behavior (20 lines, reusable)

---

## Use Case 7: The Spider Swarm (Multi-Attacker Encounters)

### Scenario
Giant spiders hunt in web-covered areas. They're individually weak but venomous. Damaging webs alerts them. Player can burn webs or use repellent. Spiders coordinate through simple pack behavior (simplified from hive mind).

### Spatial Context
- Gallery parts with varying web coverage
- `part_gallery_north_wall`: `web_density: "heavy"`
- `part_gallery_center`: `web_density: "light"`

### Actor Properties

**Giant Spider:**
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
          "effect": "cannot_move"
        }
      }
    ],
    "ai": {
      "disposition": "neutral",
      "pack_id": "gallery_spiders",
      "follows_alpha": "npc_spider_alpha",
      "alerted_by": "web_damage"
    }
  }
}
```

**Spider Alpha** (pack leader):
```json
{
  "id": "npc_spider_alpha",
  "name": "broodmother",
  "properties": {
    "health": 40,
    "max_health": 40,
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
      "disposition": "neutral",
      "pack_role": "alpha",
      "pack_id": "gallery_spiders",
      "alerted_by": "web_damage"
    }
  }
}
```

**Gallery Part:**
```json
{
  "id": "part_gallery_north_wall",
  "properties": {
    "web_density": "heavy",
    "web_bonus_attacks": 20,
    "burnable": true
  }
}
```

**Torch:**
```json
{
  "id": "item_torch",
  "name": "torch",
  "properties": {
    "light_source": true,
    "damage_type": "fire",
    "damages_webs": true
  }
}
```

**Repellent:**
```json
{
  "id": "item_repellent",
  "name": "pungent incense",
  "properties": {
    "repels": ["arachnid"],
    "duration": 10
  }
}
```

### Interactions (Simplified)

1. **Web Detection** (deterministic):
   - When player approaches part with `web_density`
   - If player moves quietly (uses `sneak` command): not detected
   - Otherwise: spiders with `alerted_by: "web_damage"` become hostile
   - No randomness - predictable outcome

2. **Pack Coordination** (simple):
   - After alert, followers check alpha
   - If alpha is hostile, followers become hostile
   - All spiders attack same turn
   - Simple follow-the-leader, no complex tactics

3. **Venomous Attacks**:
   - Spider uses "venomous_bite" attack
   - Does immediate damage (8)
   - Applies condition from `applies_condition` property
   - Condition gives "agility_reduced" effect and deals 1 damage/turn
   - Multiple bites stack severity

4. **Entanglement**:
   - Spider uses "web_spray" attack
   - Does no damage but applies "entangled" condition
   - Condition has `effect: "cannot_move"`
   - Player must `break free` (uses turn, deterministic success)

5. **Web Advantage**:
   - Spiders in heavy web areas get bonus
   - Part has `web_bonus_attacks: 20`
   - Spider attack damage increased by 20%
   - Player movement slowed (costs extra turn)

6. **Burning Webs**:
   - Player: `use torch on webs`
   - Torch has `damages_webs: true`
   - Reduces part's `web_density` from "heavy" to "light"
   - Removes spider bonuses
   - Alerts all spiders (damages their webs)

7. **Repellent Strategy**:
   - Player: `use repellent`
   - Creates condition on player: `repelling_arachnids` for 10 turns
   - Spiders with `body.form: "arachnid"` won't approach
   - Allows safe passage
   - Deterministic - no chance of failure

### Author Effort
- **Define** spiders with attacks and conditions (20 lines)
- **Define** web properties on parts (3 lines)
- **Define** torch and repellent properties (5 lines)
- **Use** simple pack following (alpha sets hostility)
- **No complex AI** - just follow alpha and attack

---

## Use Case 8: The Broken Statue (Simple Construct Interaction)

### Scenario (Simplified from Clockwork Servant)
A magical statue can be activated to guard an area or provide information. It's damaged and needs repair. No component-level damage - just overall integrity. No task programming - just binary states (guarding/not guarding).

### Spatial Context
- Main hall with statue
- Library (optional assignment location)

### Actor Properties

**Magical Statue:**
```json
{
  "id": "npc_statue_guardian",
  "name": "stone guardian",
  "location": "loc_main_hall",
  "properties": {
    "health": 60,
    "max_health": 100,
    "body": {
      "form": "construct",
      "material": "stone",
      "size": "large"
    },
    "functional": false,
    "can_guard": true,
    "can_inform": true,
    "knowledge": {
      "mansion_layout": true,
      "mansion_history": true
    },
    "ai": {
      "disposition": "neutral",
      "current_duty": "idle"
    }
  }
}
```

**Repair Kit:**
```json
{
  "id": "item_repair_kit",
  "name": "stonemason's tools",
  "properties": {
    "repairs": ["construct"],
    "restore_amount": 40
  }
}
```

### Interactions (Simplified)

1. **Simple Diagnosis**:
   - Player: `examine statue`
   - Shows health (60/100) and `functional: false`
   - Message: "Damaged and inactive"
   - No hidden components - simple state

2. **Repair** (deterministic):
   - Player: `use repair kit on statue`
   - Kit has `repairs: ["construct"]`
   - Checks statue's `body.form` matches
   - Restores `health` by `restore_amount` (40)
   - If health ≥ 80: sets `functional: true`
   - Kit consumed

3. **Activation**:
   - Once functional, player: `activate statue`
   - Changes `ai.current_duty` from "idle" to "guarding"
   - Statue becomes hostile to other NPCs entering hall
   - Simple binary state

4. **Information Queries**:
   - Player: `ask statue about mansion`
   - Statue checks `knowledge.mansion_layout`
   - If true: provides information
   - No complex knowledge base - just boolean flags

5. **Reassignment**:
   - Player: `command statue to guard library`
   - Changes statue's location to library
   - Changes `ai.current_duty` to "guarding"
   - Simple location change, no pathfinding

6. **Deactivation**:
   - Player: `deactivate statue`
   - Changes `ai.current_duty` back to "idle"
   - Statue stops guarding

### Author Effort
- **Define** statue with health and knowledge flags (12 lines)
- **Define** repair kit (3 lines)
- **Use** existing `examine`, `use`, `ask` commands
- **Write** simple guard behavior (15 lines)
- **No complex programming system**

---

## Summary: Author-Friendly Patterns

### What Makes These Use Cases Author-Friendly

1. **Property-Driven Mechanics**:
   - No code for basic interactions
   - Define properties in JSON
   - Engine behaviors handle the rest

2. **Deterministic Outcomes**:
   - No skill checks to balance
   - No randomness to tune
   - Predictable, testable results

3. **Simple Binary States**:
   - hungry/fed, not hunger meter
   - knows/doesn't know, not skill levels
   - trapped/free, not complex status

4. **Reusable Behaviors**:
   - Condition system works for all ailments
   - Service framework works for all NPCs
   - Pack following works for all groups

5. **Minimal Vital Stats**:
   - Health for everyone
   - Breath only for drowning scenarios
   - No stamina, hunger meters, etc.

6. **No Equipment Slots**:
   - Items work from inventory
   - No equip/unequip complexity
   - Simple item properties

### Property Schemas to Implement

**Actor Properties:**
```json
{
  "health": number,
  "max_health": number,
  "breath": number (optional, drowning only),
  "body": {
    "form": "humanoid|quadruped|arachnid|construct",
    "material": "flesh|stone|metal",
    "features": ["teeth", "claws", "fangs"],
    "size": "small|medium|large"
  },
  "attacks": [
    {
      "name": string,
      "damage": number,
      "type": string (optional),
      "applies_condition": {...} (optional)
    }
  ],
  "immunities": [string],
  "resistances": {
    "condition_type": number (percentage reduction)
  },
  "conditions": {
    "condition_name": {
      "severity": number,
      "damage_per_turn": number,
      "duration": number,
      "effect": string
    }
  },
  "ai": {
    "disposition": "friendly|neutral|hostile|desperate|grateful",
    "pack_id": string (optional),
    "pack_role": "alpha|follower" (optional),
    "follows_alpha": string (optional),
    "morale": number,
    "flee_threshold": number,
    "needs": {
      "hungry": boolean,
      "other_need": boolean
    }
  },
  "services": {
    "service_name": {
      "accepts": [string],
      "amount_required": number,
      "grants": string (optional)
    }
  },
  "relationships": {
    "actor_id": {
      "trust": number,
      "gratitude": number
    }
  },
  "knows": [string]
}
```

**Item Properties for Actor Interactions:**
```json
{
  "cures": [string],
  "cure_amount": number,
  "treats": [string],
  "applies_condition": {...},
  "toxic_to_touch": boolean,
  "edible_by": [string],
  "satisfies": string,
  "provides_breathing": boolean,
  "can_pull_actors": boolean,
  "damages_webs": boolean,
  "repels": [string],
  "duration": number,
  "repairs": [string],
  "restore_amount": number
}
```

**Location Part Properties:**
```json
{
  "breathable": boolean,
  "spore_level": "low|medium|high",
  "web_density": "none|light|heavy",
  "web_bonus_attacks": number,
  "cover_value": number (percentage),
  "has_rune": boolean,
  "rune_effect": string
}
```

### Estimated Implementation Effort

**Phase 1 - Core Systems** (~2-3 weeks):
- Condition system with progression
- Multiple attacks per actor
- Body characteristics checking
- Environmental property effects

**Phase 2 - Social Systems** (~1-2 weeks):
- NPC services framework
- Relationship tracking
- Morale and fleeing

**Phase 3 - Coordination** (~1 week):
- Simple pack following
- Alert propagation

**Total: ~4-6 weeks for full implementation**

All use cases achievable with ~500 lines of core behavior code + property definitions in game JSON.
