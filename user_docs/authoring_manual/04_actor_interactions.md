# Actor Interactions

> **Part of the [Authoring Manual](00_start_here.md)**
>
> Previous: [Actors](03_actors.md) | Next: [The Behavior System](05_behaviors.md)

---

This chapter covers how to create interactions between actors: combat, healing, services, environmental effects, and more. It builds on the fundamentals from [Actors](03_actors.md).

The actor interaction system is designed to be **property-driven**: you define interactions by setting properties in JSON, not by writing code. Standard behaviors in the library read these properties and handle the mechanics.

---

## 1. The Actor Interaction Library

The framework provides a library of behavior modules for common actor interactions. These live in `behaviors/library/actors/` and handle:

| Module | Purpose |
|--------|---------|
| `conditions.py` | Condition lifecycle (apply, progress, cure) |
| `environment.py` | Environmental effects (breath, spores, temperature) |
| `treatment.py` | Item-based condition treatment |
| `services.py` | NPC services (cure, teach, heal, trade) |
| `relationships.py` | Trust, gratitude, fear tracking |
| `combat.py` | Attack selection, damage, death checking |
| `morale.py` | Morale calculation, fleeing |
| `packs.py` | Pack member coordination |
| `npc_actions.py` | NPC action phase handling |

### Using the Library

To use these behaviors in your game, symlink the library into your behaviors directory:

```bash
# From your game's behaviors/ directory
ln -s ../../../behaviors/library library
```

The library behaviors are automatically loaded and will handle actor interactions based on entity properties.

---

## 2. Conditions

Conditions are temporary states that affect actors. The condition system handles poison, disease, bleeding, exhaustion, entanglement, and any other status effect you define.

### 2.1 Defining Conditions

Conditions are defined in an actor's `properties.conditions`:

```json
{
  "properties": {
    "conditions": {
      "poison": {
        "severity": 60,
        "damage_per_turn": 2,
        "duration": 10
      }
    }
  }
}
```

**Condition properties:**

```json
{
  "severity": 60,           // How severe (0-100)
  "damage_per_turn": 2,     // Health lost each turn
  "duration": 10,           // Turns until auto-removal
  "progression_rate": 3,    // Severity increase per turn
  "effect": "cannot_move",  // Named effect for queries
  "contagious_range": "touch"  // Spreads to nearby actors
}
```

### 2.2 Condition Progression

Each turn, conditions progress automatically:

1. `damage_per_turn` is applied to health
2. `severity` increases by `progression_rate`
3. `duration` decreases by 1
4. If `duration` reaches 0 or `severity` reaches 0, condition is removed

**Example - Worsening Infection:**

```json
{
  "conditions": {
    "fungal_infection": {
      "severity": 40,
      "damage_per_turn": 2,
      "progression_rate": 5
    }
  }
}
```

This infection deals 2 damage per turn and gets 5 points worse each turn. Without treatment, it becomes severe quickly.

### 2.3 Condition Stacking

When a condition is applied to an actor who already has it, severities stack:

- Existing poison (severity 40) + new poison (severity 30) = severity 70
- Severity is capped at 100
- Duration takes the longer of existing vs new

This creates meaningful cumulative danger from multiple attacks or prolonged exposure.

### 2.4 Immunities and Resistances

Actors can be protected from conditions:

**Immunities** block conditions entirely:

```json
{
  "properties": {
    "immunities": ["poison", "disease"]
  }
}
```

**Resistances** reduce severity:

```json
{
  "properties": {
    "resistances": {
      "disease": 30
    }
  }
}
```

A 30% disease resistance means incoming severity is reduced by 30%. Formula: `actual_severity = base_severity * (1 - resistance/100)`

**Automatic immunities**: Constructs (`body.form: "construct"`) are automatically immune to poison, disease, and bleeding.

### 2.5 Condition Library API

The conditions module provides these functions:

```python
from behaviors.library.actors.conditions import (
    apply_condition,    # Add/increase a condition
    remove_condition,   # Remove/reduce a condition
    has_condition,      # Check if actor has condition
    get_condition,      # Get condition data
    has_effect,         # Check if actor has any condition with effect
    is_immune,          # Check if actor is immune
    get_resistance,     # Get resistance percentage
    tick_conditions     # Progress all conditions (called by engine)
)
```

**Example - Applying a condition in behavior code:**

```python
from behaviors.library.actors.conditions import apply_condition

def on_attack(entity, accessor, context):
    """Spider's venomous bite applies poison."""
    target = accessor.get_actor(context.get("target_id"))

    apply_condition(accessor, target, "spider_venom", {
        "severity": 40,
        "damage_per_turn": 1,
        "duration": 10,
        "effect": "agility_reduced"
    }, source_id=entity.id)
```

---

## 3. Treatment and Curing

Items can treat conditions. The treatment system handles this automatically based on item properties.

### 3.1 Curative Items

Define items that cure conditions:

```json
{
  "id": "item_antidote",
  "name": "antidote",
  "properties": {
    "portable": true,
    "cures": ["poison", "spider_venom"],
    "cure_amount": 100,
    "consumable": true
  }
}
```

**Treatment properties:**

| Property | Type | Description |
|----------|------|-------------|
| `cures` | array | Condition names this item treats |
| `treats` | array | Alias for `cures` (author convenience) |
| `cure_amount` | int | Severity to remove (100 = full cure) |
| `consumable` | bool | Item is consumed when used |

### 3.2 Using Treatment Items

**Command**: `use antidote on scholar`

The treatment behavior:
1. Checks if item has `cures` or `treats` matching target's conditions
2. Reduces condition severity by `cure_amount`
3. Removes condition if severity reaches 0
4. Consumes item if `consumable: true`

**Partial cures**: If `cure_amount` is less than severity, the condition remains with reduced severity.

```json
{
  "id": "item_weak_antidote",
  "properties": {
    "cures": ["poison"],
    "cure_amount": 50,
    "consumable": true
  }
}
```

This reduces poison severity by 50 points but may not fully cure it.

### 3.3 Auto-Treatment on Receive

When an actor receives a curative item (via `give antidote to scholar`), the `on_receive` behavior automatically checks if the item can treat the actor's conditions and applies it.

This enables the "give medicine to sick NPC" pattern without custom code.

### 3.4 Treatment Library API

```python
from behaviors.library.actors.treatment import (
    can_treat,              # Check if item treats a condition
    treat_condition,        # Apply treatment
    get_treatable_conditions  # Get list of conditions item treats
)
```

---

## 4. Combat

The combat system handles attacks, damage, armor, cover, and death.

### 4.1 Defining Attacks

Attacks are defined in an actor's `properties.attacks` array:

```json
{
  "properties": {
    "attacks": [
      {
        "name": "bite",
        "damage": 15,
        "type": "piercing"
      },
      {
        "name": "venomous_bite",
        "damage": 8,
        "applies_condition": {
          "name": "spider_venom",
          "severity": 40,
          "damage_per_turn": 1,
          "duration": 10
        }
      },
      {
        "name": "tackle",
        "damage": 8,
        "effect": "knockdown"
      }
    ],
    "armor": 5
  }
}
```

**Attack properties:**

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Attack name for display |
| `damage` | int | Base damage |
| `type` | string | Damage type (descriptive) |
| `effect` | string | Special effect ("knockdown", etc.) |
| `applies_condition` | object | Condition applied on hit |

### 4.2 Attack Selection

When an NPC attacks, the combat system selects an appropriate attack:

1. **Prefer knockdown** if target is healthy (>50% health)
2. **Prefer condition attacks** if target doesn't already have that condition
3. **Otherwise** select highest damage attack

This creates variety in combat without requiring custom AI.

### 4.3 Damage Calculation

```
final_damage = attack.damage - target.armor
```

- Armor provides flat damage reduction
- Minimum damage is 0 (armor can negate weak attacks)

### 4.4 Cover Mechanics

Actors can take cover behind objects with `cover_value`:

```json
{
  "id": "item_pillar",
  "name": "stone pillar",
  "properties": {
    "portable": false,
    "cover_value": 50
  }
}
```

When an actor has `posture: "cover"` and `focused_on` a cover object, incoming damage is reduced:

```
covered_damage = damage * (1 - cover_value/100)
```

A pillar with `cover_value: 50` reduces damage by 50%.

**Taking cover**: Player uses `hide behind pillar` or similar command (sets posture and focus).

### 4.5 Death

When an actor's health reaches 0, the `on_death` behavior fires. The engine does NOT automatically handle death - authors implement death handling based on their game's needs.

**Common patterns:**
- Remove actor from game
- Drop inventory items
- Create a corpse item
- Set actor to "incapacitated" state

**Example death handler:**

```python
def on_death(entity, accessor, context):
    """Handle actor death."""
    # Drop inventory
    for item_id in entity.inventory:
        item = accessor.get_item(item_id)
        if item:
            item.location = entity.location
    entity.inventory = []

    # Remove from game or mark as dead
    entity.properties["dead"] = True

    return EventResult(allow=True,
                      message=f"{entity.name} collapses!")
```

### 4.6 Combat Library API

```python
from behaviors.library.actors.combat import (
    get_attacks,       # Get actor's attacks array
    select_attack,     # Choose appropriate attack
    execute_attack,    # Perform attack against target
    calculate_damage,  # Calculate damage with armor/cover
    on_death_check     # Check for death (called by engine)
)
```

### 4.7 Combat Example: Guardian Golems

From the Guardian Golems use case:

**Stone Golem:**

```json
{
  "id": "npc_golem",
  "name": "Stone Guardian",
  "properties": {
    "health": 200,
    "max_health": 200,
    "body": {
      "form": "construct",
      "material": "stone"
    },
    "attacks": [
      {
        "name": "charge",
        "damage": 30
      },
      {
        "name": "slam",
        "damage": 50
      }
    ],
    "armor": 20,
    "immunities": ["poison", "disease", "bleeding"],
    "ai": {
      "disposition": "hostile"
    }
  }
}
```

**Stone Pillar for Cover:**

```json
{
  "id": "item_pillar",
  "name": "marble pillar",
  "properties": {
    "portable": false,
    "cover_value": 80
  }
}
```

The player can hide behind pillars to reduce the golem's damage by 80%.

---

## 5. Services Framework

NPCs can offer services in exchange for payment: healing, teaching, trading, and custom services.

### 5.1 Defining Services

Services are defined in an actor's `properties.services`:

```json
{
  "properties": {
    "services": {
      "cure_poison": {
        "accepts": ["rare_herbs", "gold"],
        "amount_required": 5,
        "cure_amount": 100
      },
      "teach_herbalism": {
        "accepts": ["gold"],
        "amount_required": 50,
        "grants": "herbalism"
      },
      "heal": {
        "accepts": ["gold"],
        "amount_required": 25,
        "restore_amount": 50
      }
    }
  }
}
```

### 5.2 Service Types

**Cure Service** - Removes conditions:

```json
{
  "cure_poison": {
    "accepts": ["rare_herbs"],
    "amount_required": 1,
    "cure_amount": 100
  }
}
```

**Teaching Service** - Grants knowledge:

```json
{
  "teach_herbalism": {
    "accepts": ["gold"],
    "amount_required": 50,
    "grants": "herbalism"
  }
}
```

The string from `grants` is added to the customer's `knows` array.

**Healing Service** - Restores health:

```json
{
  "heal": {
    "accepts": ["gold"],
    "amount_required": 25,
    "restore_amount": 50
  }
}
```

### 5.3 Payment

Services are triggered when a player gives an acceptable payment:

**Command**: `give 50 gold to healer`

The service behavior:
1. Checks if item type is in `accepts`
2. Verifies amount meets `amount_required`
3. Executes the service effect
4. Consumes the payment
5. Increments relationship trust

**Payment rules:**
- Exact match or overpayment required
- Underpayment is rejected
- No change given (simplifies implementation)

### 5.4 Trust Discounts

When `relationships[customer].trust >= 3`, service costs are halved:

```python
if trust >= 3:
    effective_cost = base_cost // 2  # 50% discount
```

This rewards players who build relationships with NPCs.

### 5.5 Services Library API

```python
from behaviors.library.actors.services import (
    get_available_services,  # Get NPC's services
    get_service_cost,        # Get effective cost (with discounts)
    can_afford_service,      # Check if customer can pay
    execute_service          # Perform service transaction
)
```

### 5.6 Services Example: The Healer

From the Healer use case:

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
        "amount_required": 1
      },
      "teach_herbalism": {
        "accepts": ["gold"],
        "amount_required": 50,
        "grants": "herbalism"
      }
    },
    "ai": {
      "disposition": "neutral"
    },
    "relationships": {}
  }
}
```

**Interaction flow:**
1. Player examines healer, sees services offered
2. Player: `give rare_herbs to healer`
3. Healer's `on_receive` detects payment for cure_poison
4. All poison conditions removed from player
5. Trust incremented
6. Next transaction may be discounted

---

## 6. Relationships and Domestication

The relationship system tracks progressive bonds between actors, enabling domestication, discounts, and alliances.

### 6.1 Relationship Tracking

Relationships are stored in `properties.relationships`:

```json
{
  "properties": {
    "relationships": {
      "player": {
        "trust": 2,
        "gratitude": 5,
        "fear": 0
      }
    }
  }
}
```

**Metrics** (0-10 scale):
- `trust` - Built through trade, keeping promises
- `gratitude` - Earned through gifts, rescue, healing
- `fear` - Created through intimidation, violence

### 6.2 Threshold Effects

When metrics cross thresholds, behavior changes:

| Metric | Threshold | Effect |
|--------|-----------|--------|
| `gratitude >= 3` | Domestication | Creature becomes friendly |
| `trust >= 3` | Discount | Services cost 50% less |
| `trust >= 5` | Loyalty | NPC offers special help |
| `fear >= 5` | Intimidation | NPC may flee or comply |

### 6.3 Domestication

Domestication turns hostile creatures into friendly companions through repeated positive interactions.

**Wolf Pack Example:**

```json
{
  "id": "npc_alpha_wolf",
  "properties": {
    "ai": {
      "disposition": "hostile",
      "needs": {
        "hungry": true
      }
    },
    "relationships": {}
  }
}
```

**Meat Item:**

```json
{
  "id": "item_venison",
  "properties": {
    "satisfies": ["hunger"],
    "consumable": true
  }
}
```

**Domestication flow:**

1. Player: `give venison to alpha wolf`
2. Wolf's `on_receive` checks if item satisfies a need
3. `needs.hungry` set to false
4. Disposition changes to "neutral" (no longer desperate)
5. `relationships.player.gratitude` incremented
6. Repeat feeding...
7. When `gratitude >= 3`: disposition becomes "friendly"
8. Wolf follows player, pack follows alpha

### 6.4 Relationships Library API

```python
from behaviors.library.actors.relationships import (
    get_relationship,      # Get relationship values
    modify_relationship,   # Change trust/gratitude/fear
    check_threshold,       # Check if metric meets threshold
    get_disposition_from_relationships  # Derive disposition
)
```

---

## 7. Environmental Effects

Location parts can have properties that affect actors each turn.

### 7.1 Parts

Parts are sub-areas within a location (see [Spatial Rooms](07_spatial.md) for full details). They have properties that can affect actors.

**Define parts in your game_state.json:**

```json
{
  "parts": [
    {
      "id": "part_basement_entrance",
      "name": "Basement Entrance",
      "part_of": "loc_basement",
      "properties": {
        "spore_level": "low",
        "breathable": true
      }
    },
    {
      "id": "part_basement_center",
      "name": "Basement Center",
      "part_of": "loc_basement",
      "properties": {
        "spore_level": "high",
        "breathable": true
      }
    }
  ]
}
```

### 7.2 Breath Tracking

For drowning scenarios, parts can be non-breathable:

```json
{
  "id": "part_underwater_deep",
  "properties": {
    "breathable": false
  }
}
```

**Breath mechanics:**
- In breathable areas: breath restores to max
- In non-breathable areas: breath decreases by 10 per turn
- When breath <= 0: actor takes 10 drowning damage per turn

**Breathing items** can provide air:

```json
{
  "id": "item_breathing_reed",
  "properties": {
    "provides_breathing": true
  }
}
```

An actor holding this item doesn't lose breath. Parts can disable this with `breathing_item_works: false` for deep water.

### 7.3 Spore Effects

Parts can have spore contamination:

```json
{
  "properties": {
    "spore_level": "high"
  }
}
```

**Spore levels and severity per turn:**

| Level | Severity/turn |
|-------|---------------|
| `"none"` | 0 |
| `"low"` | 5 |
| `"medium"` | 10 |
| `"high"` | 15 |

Each turn in a spore area, actors gain/increase `fungal_infection` condition (reduced by disease resistance).

### 7.4 Temperature Effects

Parts can have temperature extremes:

```json
{
  "properties": {
    "temperature": "freezing"
  }
}
```

**Temperature effects:**

| Temperature | Condition | Severity/turn |
|-------------|-----------|---------------|
| `"freezing"` | hypothermia | 10 |
| `"cold"` | hypothermia | 5 |
| `"normal"` | none | 0 |
| `"hot"` | heat_exhaustion | 5 |
| `"burning"` | heat_exhaustion | 10 |

### 7.5 Cover Values

Parts can provide cover in combat:

```json
{
  "id": "part_sanctum_alcove",
  "properties": {
    "cover_value": 50
  }
}
```

Actors in this part get 50% damage reduction from attacks.

### 7.6 Environmental Effects Example: Flooded Tunnel

From the Drowning Sailor use case:

**Location with parts:**

```json
{
  "id": "loc_underwater_cave",
  "name": "Underwater Cave",
  "parts": ["part_shallow", "part_deep"]
}
```

**Parts:**

```json
{
  "id": "part_shallow",
  "part_of": "loc_underwater_cave",
  "properties": {
    "breathable": false,
    "breathing_item_works": true
  }
}
```

```json
{
  "id": "part_deep",
  "part_of": "loc_underwater_cave",
  "properties": {
    "breathable": false,
    "breathing_item_works": false,
    "temperature": "cold"
  }
}
```

**Sailor in danger:**

```json
{
  "id": "npc_sailor",
  "properties": {
    "health": 45,
    "breath": 20,
    "max_breath": 60,
    "conditions": {
      "exhaustion": {
        "severity": 70,
        "effect": "cannot_swim"
      }
    }
  }
}
```

**What happens each turn:**
1. Sailor's breath decreases (non-breathable)
2. Cold applies hypothermia (temperature)
3. If breath <= 0, drowning damage
4. Sailor can't rescue themselves (cannot_swim effect)
5. Player must pull them to safety

### 7.7 Environment Library API

```python
from behaviors.library.actors.environment import (
    apply_environmental_effects,  # Apply part effects to actor
    check_breath,                 # Update breath tracking
    needs_breath,                 # Check if actor needs to breathe
    get_cover_value              # Get cover from part
)
```

---

## 8. Morale and Fleeing

Actors can flee when injured or demoralized.

### 8.1 Morale Tracking

Morale is tracked in `properties.ai.morale`:

```json
{
  "properties": {
    "ai": {
      "morale": 60,
      "flee_threshold": 20
    }
  }
}
```

### 8.2 Morale Calculation

The library calculates morale dynamically from health:

- Health >= 50%: morale unchanged
- Health 30-50%: morale halved
- Health < 30%: morale drops to 0

### 8.3 Fleeing

When `morale < flee_threshold`, the actor flees:
- Moves toward a random unlocked exit
- Disposition may change to "fleeing"
- Pack followers flee if alpha flees

**Custom flee destination:**

```json
{
  "properties": {
    "ai": {
      "flee_threshold": 20,
      "flee_destination": "loc_wolf_den"
    }
  }
}
```

### 8.4 Morale Library API

```python
from behaviors.library.actors.morale import (
    get_morale,              # Get current morale
    calculate_morale,        # Calculate from health
    should_flee,             # Check flee threshold
    execute_flee             # Move actor to safety
)
```

---

## 9. Pack Coordination

Packs allow coordinated behavior where followers copy the alpha.

### 9.1 Pack Setup

**Alpha:**

```json
{
  "id": "npc_alpha_wolf",
  "properties": {
    "ai": {
      "disposition": "hostile",
      "pack_id": "winter_wolves",
      "pack_role": "alpha"
    }
  }
}
```

**Followers:**

```json
{
  "id": "npc_wolf_1",
  "properties": {
    "ai": {
      "disposition": "hostile",
      "pack_id": "winter_wolves",
      "pack_role": "follower",
      "follows_alpha": "npc_alpha_wolf"
    }
  }
}
```

### 9.2 Pack Behavior

During the NPC action phase:
1. Alphas are processed first
2. Before each follower acts, it copies the alpha's disposition
3. If alpha is hostile, followers attack
4. If alpha becomes friendly (domesticated), followers become friendly
5. If alpha flees, followers flee

### 9.3 Pack Use Cases

**Combat coordination:**
- Alpha wolf attacks, pack follows
- Damaging alpha affects pack morale

**Domestication:**
- Feed alpha until gratitude >= 3
- Alpha's disposition becomes friendly
- Pack becomes friendly

**Spider swarm:**
- Alert spider queen (alpha)
- All worker spiders become hostile

### 9.4 Packs Library API

```python
from behaviors.library.actors.packs import (
    get_pack_members,       # Get all actors in pack
    get_alpha,              # Get pack alpha
    sync_pack_disposition,  # Sync followers to alpha
    is_alpha               # Check if actor is alpha
)
```

---

## 10. Worked Examples

These examples demonstrate complete interactions using the patterns above.

### 10.1 The Infected Scholar (UC1)

**Scenario**: A scholar has a fungal infection. Player can cure them with silvermoss or become infected through proximity.

**Scholar:**

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
    "ai": {
      "disposition": "friendly"
    }
  }
}
```

**Curative herb:**

```json
{
  "id": "item_silvermoss",
  "name": "silvermoss",
  "location": "loc_library",
  "properties": {
    "portable": true,
    "cures": ["fungal_infection"],
    "cure_amount": 100,
    "consumable": true
  }
}
```

**Player with resistance:**

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

**Spore-filled basement:**

```json
{
  "id": "part_basement_center",
  "part_of": "loc_basement",
  "properties": {
    "spore_level": "high"
  }
}
```

**Interactions:**
- `give silvermoss to scholar` - Cures the infection
- Staying near scholar - Risk of contagion (proximity)
- Entering basement center - Spore exposure (environmental)
- Player's 30% resistance reduces incoming severity

### 10.2 The Wolf Pack (UC3)

**Scenario**: Hungry wolves can be fought or domesticated through feeding.

**Alpha wolf:**

```json
{
  "id": "npc_alpha_wolf",
  "name": "Alpha Wolf",
  "location": "loc_forest_clearing",
  "properties": {
    "health": 80,
    "max_health": 80,
    "attacks": [
      {"name": "bite", "damage": 15},
      {"name": "tackle", "damage": 8, "effect": "knockdown"}
    ],
    "ai": {
      "disposition": "hostile",
      "pack_id": "winter_wolves",
      "pack_role": "alpha",
      "morale": 60,
      "flee_threshold": 20,
      "needs": {"hungry": true}
    },
    "relationships": {}
  }
}
```

**Pack member:**

```json
{
  "id": "npc_wolf_1",
  "name": "Grey Wolf",
  "location": "loc_forest_clearing",
  "properties": {
    "health": 50,
    "max_health": 50,
    "attacks": [{"name": "bite", "damage": 12}],
    "ai": {
      "disposition": "hostile",
      "pack_id": "winter_wolves",
      "pack_role": "follower",
      "follows_alpha": "npc_alpha_wolf",
      "morale": 60,
      "flee_threshold": 30
    }
  }
}
```

**Food:**

```json
{
  "id": "item_venison",
  "name": "venison",
  "properties": {
    "portable": true,
    "satisfies": ["hunger"],
    "consumable": true
  }
}
```

**Combat path:**
- Wolves attack player (hostile)
- Damaging alpha reduces pack morale
- At low health, alpha flees
- Pack follows alpha

**Domestication path:**
- `give venison to alpha wolf`
- Hunger satisfied, disposition becomes neutral
- Gratitude incremented
- Repeat feeding until gratitude >= 3
- Alpha becomes friendly
- Pack follows alpha's new disposition

### 10.3 The Healer's Garden (UC4)

**Scenario**: Garden has toxic and curative plants. Healer offers services.

**Healer:**

```json
{
  "id": "npc_healer",
  "name": "Healer Elara",
  "location": "loc_healer_hut",
  "properties": {
    "health": 70,
    "max_health": 70,
    "services": {
      "cure_poison": {
        "accepts": ["rare_herbs", "gold"],
        "amount_required": 5
      },
      "teach_herbalism": {
        "accepts": ["gold"],
        "amount_required": 50,
        "grants": "herbalism"
      }
    },
    "ai": {"disposition": "friendly"},
    "relationships": {}
  }
}
```

**Toxic plant:**

```json
{
  "id": "item_nightshade",
  "name": "nightshade",
  "location": "loc_garden",
  "properties": {
    "portable": true,
    "toxic_to_touch": true,
    "applies_condition": {
      "name": "contact_poison",
      "severity": 50,
      "damage_per_turn": 5,
      "duration": 5
    }
  }
}
```

**Curative plant:**

```json
{
  "id": "item_golden_root",
  "name": "golden root",
  "location": "loc_garden",
  "properties": {
    "portable": true,
    "cures": ["contact_poison"],
    "cure_amount": 80
  }
}
```

**Interactions:**
- Taking nightshade without knowledge applies poison
- With `"herbalism"` in player's `knows`: safe handling + detailed description
- `give 50 gold to healer` teaches herbalism
- `give golden_root to healer` pays for cure service
- Building trust unlocks discounts

### 10.4 The Spider Swarm (UC7)

**Scenario**: Spiders coordinate attacks, have venomous bites, and get bonuses in web-covered areas.

**Spider queen (alpha):**

```json
{
  "id": "npc_spider_queen",
  "name": "Spider Queen",
  "location": "loc_spider_gallery",
  "properties": {
    "health": 120,
    "max_health": 120,
    "attacks": [
      {
        "name": "venomous_bite",
        "damage": 15,
        "applies_condition": {
          "name": "spider_venom",
          "severity": 60,
          "damage_per_turn": 2,
          "duration": 15
        }
      }
    ],
    "ai": {
      "disposition": "hostile",
      "pack_id": "spider_swarm",
      "pack_role": "alpha"
    }
  }
}
```

**Worker spider:**

```json
{
  "id": "npc_spider_worker",
  "name": "Giant Spider",
  "location": "loc_spider_gallery",
  "properties": {
    "health": 40,
    "max_health": 40,
    "attacks": [
      {"name": "bite", "damage": 8},
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
      "disposition": "hostile",
      "pack_id": "spider_swarm",
      "pack_role": "follower",
      "follows_alpha": "npc_spider_queen"
    }
  }
}
```

**Web-covered part:**

```json
{
  "id": "part_spider_nest",
  "part_of": "loc_spider_gallery",
  "properties": {
    "web_density": 80,
    "web_bonus_attacks": 10
  }
}
```

**Torch for burning webs:**

```json
{
  "id": "item_torch",
  "name": "torch",
  "properties": {
    "portable": true,
    "burns_webs": true,
    "web_burn_amount": 30
  }
}
```

**Interactions:**
- Entering alerts spiders (pack becomes hostile)
- Venomous bites apply poison condition
- Web spray applies entanglement (cannot_move)
- Spiders get attack bonus in web-heavy areas
- Burning webs reduces their advantage

---

## 11. Custom Behaviors

While the library handles common patterns, you can write custom behaviors for unique interactions.

### 11.1 When to Write Custom Behaviors

Write custom behaviors when you need:
- Game-specific mechanics not covered by the library
- Custom conditions or effects
- Unique NPC responses
- Special item interactions

### 11.2 Extending Library Behaviors

You can extend library behaviors rather than replacing them:

```python
from behaviors.library.actors.conditions import apply_condition
from behaviors.library.actors.relationships import modify_relationship

def on_receive(entity, accessor, context):
    """Custom on_receive that adds relationship building."""
    item_id = context.get("item_id")
    giver_id = context.get("giver_id")
    item = accessor.get_item(item_id)

    # Check for food gifts
    if item and item.properties.get("is_gift"):
        modify_relationship(accessor, entity, giver_id, "gratitude", 2)
        return EventResult(allow=True,
                          message=f"{entity.name} is pleased by your gift!")

    # Let library handle other cases
    return None
```

### 11.3 Registering Custom Events

For custom verbs and events, register them in your behavior's vocabulary:

```python
vocabulary = {
    "verbs": [
        {
            "word": "pet",
            "synonyms": ["stroke", "pat"],
            "object_required": True
        }
    ],
    "events": [
        {
            "event": "on_pet",
            "description": "Called when actor is petted"
        }
    ]
}

def handle_pet(accessor, action):
    """Handle the pet command."""
    target = accessor.find_entity_in_location(
        action.get("object"),
        accessor.get_actor("player").location
    )

    if not target:
        return EventResult(success=False,
                          message="You don't see that here.")

    # Invoke on_pet behavior on target
    result = accessor.behavior_manager.invoke_behavior(
        target, "on_pet", accessor, {"actor_id": "player"}
    )

    if result:
        return result

    return EventResult(success=True,
                      message=f"You pet {target.name}.")

def on_pet(entity, accessor, context):
    """Called when this entity is petted."""
    if entity.properties.get("ai", {}).get("likes_petting"):
        from behaviors.library.actors.relationships import modify_relationship
        modify_relationship(accessor, entity, context["actor_id"], "trust", 1)
        return EventResult(allow=True,
                          message=f"{entity.name} enjoys the attention!")
    return None
```

---

## 12. Property Reference

### Item Properties for Actor Interactions

| Property | Type | Description |
|----------|------|-------------|
| `cures` | array | Condition names item treats |
| `treats` | array | Alias for `cures` |
| `cure_amount` | int | Severity to remove |
| `consumable` | bool | Item consumed on use |
| `applies_condition` | object | Condition applied on contact/use |
| `toxic_to_touch` | bool | Applies condition when taken |
| `satisfies` | array | Needs this item satisfies |
| `provides_breathing` | bool | Prevents breath loss |
| `cover_value` | int | Damage reduction percentage |
| `burns_webs` | bool | Can destroy webs |
| `repairs` | array | Entity types this repairs |
| `repair_amount` | int | Health to restore |

### Part Properties

| Property | Type | Description |
|----------|------|-------------|
| `breathable` | bool | Whether actors can breathe |
| `breathing_item_works` | bool | Whether breathing items help |
| `spore_level` | string | "none", "low", "medium", "high" |
| `temperature` | string | "freezing", "cold", "normal", "hot", "burning" |
| `cover_value` | int | Damage reduction for actors in part |
| `web_density` | int | Web coverage (affects movement/combat) |
| `web_bonus_attacks` | int | Attack bonus for spiders |

---

## Summary

The actor interaction system enables rich gameplay through property-driven design:

1. **Conditions** - Temporary states with damage, duration, and effects
2. **Treatment** - Items cure conditions based on `cures` property
3. **Combat** - Multi-attack actors with armor and cover
4. **Services** - NPCs offer services for payment
5. **Relationships** - Trust, gratitude, fear with threshold effects
6. **Environment** - Parts affect breath, apply conditions
7. **Morale** - Actors flee when injured
8. **Packs** - Followers copy alpha behavior

The library provides standard behaviors that read these properties. For unique mechanics, write custom behaviors that extend the library functions.

See [Actors](03_actors.md) for the foundational actor properties this chapter builds upon.

---

> **Next:** [The Behavior System](05_behaviors.md) - Learn how to extend the framework with custom behaviors
