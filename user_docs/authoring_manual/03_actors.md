# Actors

> **Part of the [Authoring Manual](00_start_here.md)**
>
> Previous: [Core Concepts](02_core_concepts.md) | Next: [Actor Interactions](04_actor_interactions.md)

---

This chapter covers the fundamentals of creating actors in your game: the player, NPCs, creatures, and constructs. It explains the property system that drives actor capabilities and the turn-based system that governs when actors act.

**Prerequisites**: This chapter assumes familiarity with the basic concepts in [Core Concepts](02_core_concepts.md), particularly entity structure, properties, and behaviors.

**Companion chapter**: [Actor Interactions](04_actor_interactions.md) covers how to create specific interactions like combat, healing, services, and environmental effects.

---

## 1. What Are Actors?

Actors are entities that can act in the game world. They include:

- **Player** - The protagonist controlled by the player
- **NPCs** - Non-player characters like merchants, guards, healers
- **Creatures** - Animals and monsters like wolves, spiders, golems
- **Constructs** - Animated objects like statues, automata, magical guardians

**Key principle**: All actors share the same fundamental structure. The player, a wolf, and a stone golem are all actors - they differ only in their properties and behaviors.

### Actor Structure

Every actor has:

```json
{
  "id": "npc_merchant",
  "name": "Traveling Merchant",
  "description": "A jovial merchant with a ready smile.",
  "location": "loc_market",
  "inventory": ["item_coins", "item_healing_potion"],
  "properties": {
    "health": 80,
    "max_health": 80,
    "disposition": "friendly"
  }
}
```

**Core fields:**
- `id` - Unique identifier (e.g., "npc_guard", "player")
- `name` - Display name
- `description` - What players see when examining
- `location` - Current location ID
- `inventory` - List of item IDs the actor carries

**Properties dict**: Flexible storage for all actor characteristics. This is where the actor interaction system stores health, conditions, attacks, services, relationships, and more.

### The Player Actor

The player is always an actor with id `"player"`:

```json
{
  "actors": {
    "player": {
      "id": "player",
      "name": "Adventurer",
      "description": "A brave explorer.",
      "location": "loc_entrance",
      "inventory": [],
      "properties": {
        "health": 100,
        "max_health": 100
      }
    }
  }
}
```

---

## 2. Core Actor Properties

The actor interaction system uses properties to define what actors can do and how they behave. All properties are optional - use only what your game needs.

### 2.1 Health and Vitals

The most basic actor property is health:

```json
{
  "properties": {
    "health": 80,
    "max_health": 100
  }
}
```

**Health tracking:**
- `health` - Current health points
- `max_health` - Maximum health points
- When `health <= 0`, the actor's `on_death` behavior fires

**For drowning scenarios**, add breath:

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

Breath decreases in non-breathable areas (see [Environmental Effects](04_actor_interactions.md#environmental-effects)).

### 2.2 Body Characteristics

Body properties define what an actor physically is:

```json
{
  "properties": {
    "body": {
      "form": "quadruped",
      "material": "flesh",
      "features": ["teeth", "claws"],
      "size": "medium"
    }
  }
}
```

**Form values:**
- `"humanoid"` - Two arms, two legs (humans, elves)
- `"quadruped"` - Four-legged (wolves, horses)
- `"arachnid"` - Spider-like (spiders, scorpions)
- `"construct"` - Animated object (golems, statues)
- `"serpent"` - Snake-like

**Material values:**
- `"flesh"` - Living tissue (default)
- `"stone"` - Stone constructs
- `"metal"` - Metal constructs
- `"clockwork"` - Mechanical

**Why body matters:**
- **Constructs are immune** to poison, disease, and bleeding
- **Constructs don't need to breathe** (unaffected by non-breathable areas)
- **Features** determine available attacks (needs "teeth" to bite)
- **Form** can affect available actions (quadrupeds can't serve food)

**Example - Stone Golem:**

```json
{
  "id": "npc_golem",
  "name": "Stone Guardian",
  "properties": {
    "health": 200,
    "max_health": 200,
    "body": {
      "form": "construct",
      "material": "stone",
      "size": "large"
    }
  }
}
```

This golem is automatically immune to poison, disease, and bleeding, and doesn't need to breathe.

### 2.3 Conditions

Conditions represent temporary states affecting an actor:

```json
{
  "properties": {
    "conditions": {
      "poison": {
        "severity": 60,
        "damage_per_turn": 2,
        "duration": 10,
        "effect": "agility_reduced"
      },
      "bleeding": {
        "severity": 40,
        "damage_per_turn": 3
      }
    }
  }
}
```

**Condition properties:**

| Property | Type | Description |
|----------|------|-------------|
| `severity` | int | How severe (0-100, caps at 100) |
| `damage_per_turn` | int | Health damage each turn |
| `duration` | int | Turns until auto-removal (optional) |
| `progression_rate` | int | Severity increase per turn (optional) |
| `effect` | string | Named effect for behavior queries |
| `contagious_range` | string | "touch" if spreads to nearby actors |

**Standard effects** (behaviors can check for these):
- `"cannot_move"` - Prevents movement
- `"cannot_swim"` - Prevents swimming/self-rescue
- `"cannot_attack"` - Prevents attacking
- `"agility_reduced"` - Flavor/narrative effect
- `"slowed"` - Movement costs extra

**Example - Infected Scholar:**

```json
{
  "id": "npc_scholar",
  "name": "Scholar Aldric",
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
    }
  }
}
```

This scholar has a worsening fungal infection that can spread to nearby actors.

### 2.4 Immunities and Resistances

Actors can be immune to or resistant to conditions:

```json
{
  "properties": {
    "immunities": ["poison", "disease"],
    "resistances": {
      "disease": 30,
      "cold": 50
    }
  }
}
```

**Immunities**: Condition types that have no effect on this actor.

**Resistances**: Percentage reduction to condition severity. A 30% disease resistance means incoming disease severity is reduced by 30%.

**Automatic immunities**: Constructs (`body.form: "construct"`) are automatically immune to poison, disease, and bleeding without needing to list them in `immunities`.

### 2.5 Attacks

Actors with combat capability have an attacks array:

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
| `name` | string | Attack identifier for display |
| `damage` | int | Base damage |
| `type` | string | Damage type (descriptive) |
| `effect` | string | Special effect ("knockdown", etc.) |
| `applies_condition` | object | Condition to apply on hit |

**Armor**: Flat damage reduction from all attacks.

**Attacks with conditions:**

```json
{
  "attacks": [
    {
      "name": "venomous_bite",
      "damage": 8,
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
```

See [Combat](04_actor_interactions.md#combat) for how attacks are selected and executed.

### 2.6 AI and Disposition

The `ai` property controls NPC behavior:

```json
{
  "properties": {
    "ai": {
      "disposition": "hostile",
      "morale": 60,
      "flee_threshold": 20
    }
  }
}
```

**Disposition values:**
- `"friendly"` - Helpful to player
- `"neutral"` - Neither helpful nor hostile
- `"hostile"` - Attacks player
- `"desperate"` - Driven by need (hungry, trapped)
- `"grateful"` - Thankful toward player

**Morale and fleeing:**
- `morale` - Current morale (0-100)
- `flee_threshold` - Morale level that triggers fleeing
- When health drops below 30%, morale drops to 0
- When morale < flee_threshold, actor flees

### 2.7 Needs

Simple binary needs for creatures:

```json
{
  "properties": {
    "ai": {
      "disposition": "hostile",
      "needs": {
        "hungry": true
      }
    }
  }
}
```

When a need is satisfied (e.g., by feeding), the actor's disposition can change. See [Domestication](04_actor_interactions.md#domestication) for how feeding wolves creates friendship.

### 2.8 Relationships

Actors can have relationships with other actors:

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

**Relationship metrics** (0-10 scale):
- `trust` - Built through trade, help, keeping promises
- `gratitude` - Earned through gifts, rescue, healing
- `fear` - Created through intimidation, violence

**Threshold effects:**
- `gratitude >= 3` - Domestication threshold (creature becomes friendly)
- `trust >= 3` - Discount threshold (services cost 50% less)
- `trust >= 5` - Loyalty threshold (NPC offers special help)
- `fear >= 5` - Intimidation threshold (NPC may flee or comply)

Relationships are created dynamically when first needed. An empty `{}` means no relationships yet.

### 2.9 Services

NPCs can offer services in exchange for payment:

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
        "grants": "knows_herbalism"
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

**Service types:**
- **Cure services** - Remove conditions (`cure_amount`)
- **Teaching services** - Grant knowledge (`grants`)
- **Healing services** - Restore health (`restore_amount`)
- **Trading services** - Exchange goods (`sells`)

See [Services Framework](04_actor_interactions.md#services-framework) for details.

### 2.10 Knowledge

Actors can have knowledge that affects interactions:

```json
{
  "properties": {
    "knows": ["herbalism", "swimming"],
    "knowledge": {
      "mansion_layout": true,
      "ancient_history": true
    }
  }
}
```

**`knows` array**: Skills and capabilities the actor has learned.

**`knowledge` dict**: Specific facts the actor knows.

**Example usage**: A player with `"herbalism"` in their `knows` array sees detailed plant descriptions and can safely handle toxic plants.

---

## 3. Pack Coordination

Actors can be organized into packs where followers copy the alpha's behavior:

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

**Pack properties:**
- `pack_id` - Identifies the pack
- `pack_role` - `"alpha"` or `"follower"`
- `follows_alpha` - ID of the alpha to follow (for followers)

**How it works:**
1. During NPC action phase, alphas are processed first
2. Followers copy their alpha's disposition before acting
3. If alpha becomes hostile, pack attacks
4. If alpha is domesticated (disposition becomes friendly), pack becomes friendly

**Example - Wolf Pack:**

When you feed the alpha wolf enough to domesticate it, the entire pack becomes friendly because followers sync to the alpha's new disposition.

---

## 4. The Turn System

Understanding when things happen is crucial for authoring actors.

### 4.1 What Is a Turn?

A turn occurs after each **successful** player command. Failed commands (like trying to take something that isn't there) don't advance time.

### 4.2 Turn Phases

After a successful command, the engine executes these phases in order:

```
1. Player command executes
2. NPC Action Phase
   - Alphas act first, then followers
   - Hostile NPCs attack
   - Friendly NPCs may help
   - Followers sync disposition from alpha
3. Environmental Effects Phase
   - Breath tracking in non-breathable areas
   - Spore exposure in contaminated areas
   - Temperature effects
4. Condition Progression Phase
   - damage_per_turn applied to health
   - severity increased by progression_rate
   - duration decremented
   - Expired conditions removed
5. Death Check Phase
   - Actors with health <= 0 trigger on_death
6. Narration
   - All events combined into description
```

### 4.3 What This Means for Authors

**Time pressure is turn-based:**
- A drowning sailor has ~5 turns before dying (not 30 seconds)
- Poison deals damage each turn, creating urgency
- Conditions with duration expire after N turns

**NPCs act after the player:**
- If a wolf is hostile, it attacks after the player's action
- NPCs everywhere can act, not just those in the current room
- Alphas always act before followers

**Environmental effects apply every turn:**
- Being in a spore-filled room increases infection each turn
- Being underwater decreases breath each turn
- Moving to safety stops the effects

---

## 5. Complete Actor Examples

### 5.1 Hostile Creature - Wolf

```json
{
  "id": "npc_alpha_wolf",
  "name": "Alpha Wolf",
  "description": "A large grey wolf with piercing yellow eyes.",
  "location": "loc_forest_clearing",
  "inventory": [],
  "properties": {
    "health": 80,
    "max_health": 80,
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
      "pack_id": "winter_wolves",
      "pack_role": "alpha",
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

This wolf:
- Attacks the player on sight (hostile disposition)
- Leads a pack (other wolves follow its lead)
- Has two attacks (bite for damage, tackle for knockdown)
- Flees when badly injured (morale drops below threshold)
- Can be pacified by feeding (satisfying hunger need)
- Can be domesticated through repeated feeding (building gratitude)

### 5.2 Friendly NPC - Healer

```json
{
  "id": "npc_healer",
  "name": "Healer Elara",
  "description": "An elderly woman with kind eyes and herb-stained hands.",
  "location": "loc_healer_hut",
  "inventory": [],
  "properties": {
    "health": 60,
    "max_health": 60,
    "body": {
      "form": "humanoid",
      "material": "flesh"
    },
    "services": {
      "cure": {
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
    },
    "ai": {
      "disposition": "friendly"
    },
    "relationships": {}
  }
}
```

This healer:
- Offers three services (cure conditions, teach herbalism, restore health)
- Accepts either rare herbs or gold for curing
- Gives discounts to trusted customers (trust >= 3)
- Builds trust through successful transactions

### 5.3 Construct - Stone Guardian

```json
{
  "id": "npc_golem",
  "name": "Stone Guardian",
  "description": "A massive stone golem with glowing runes.",
  "location": "loc_temple_sanctum",
  "inventory": [],
  "properties": {
    "health": 200,
    "max_health": 200,
    "body": {
      "form": "construct",
      "material": "stone",
      "size": "large"
    },
    "attacks": [
      {
        "name": "slam",
        "damage": 30
      },
      {
        "name": "stomp",
        "damage": 20,
        "effect": "knockdown"
      }
    ],
    "armor": 20,
    "ai": {
      "disposition": "hostile"
    }
  }
}
```

This golem:
- Is immune to poison, disease, and bleeding (construct)
- Doesn't need to breathe (can fight underwater)
- Has high health and armor (hard to kill)
- Has powerful attacks

### 5.4 Victim NPC - Drowning Sailor

```json
{
  "id": "npc_sailor",
  "name": "Drowning Sailor",
  "description": "A sailor struggling to stay afloat.",
  "location": "loc_underwater_cave",
  "inventory": [],
  "properties": {
    "health": 45,
    "max_health": 80,
    "breath": 20,
    "max_breath": 60,
    "body": {
      "form": "humanoid",
      "material": "flesh"
    },
    "conditions": {
      "exhaustion": {
        "severity": 70,
        "effect": "cannot_swim"
      }
    },
    "ai": {
      "disposition": "friendly"
    }
  }
}
```

This sailor:
- Is in immediate danger (low breath in non-breathable location)
- Cannot rescue themselves (exhaustion with cannot_swim effect)
- Will drown in a few turns without help
- Will be grateful if rescued (relationship changes)

---

## 6. Property Reference

### Actor Properties Summary

| Property | Type | Description |
|----------|------|-------------|
| `health` | int | Current health points |
| `max_health` | int | Maximum health |
| `breath` | int | Current breath (optional) |
| `max_breath` | int | Maximum breath (optional) |
| `body` | object | Physical characteristics |
| `body.form` | string | Body type |
| `body.material` | string | What actor is made of |
| `body.features` | array | Physical features |
| `body.size` | string | Size category |
| `attacks` | array | Available attacks |
| `armor` | int | Damage reduction |
| `conditions` | object | Current conditions |
| `immunities` | array | Condition types with no effect |
| `resistances` | object | Percentage reductions |
| `ai` | object | AI behavior settings |
| `ai.disposition` | string | Attitude toward player |
| `ai.morale` | int | Current morale (0-100) |
| `ai.flee_threshold` | int | Morale level triggering flee |
| `ai.pack_id` | string | Pack identifier |
| `ai.pack_role` | string | "alpha" or "follower" |
| `ai.follows_alpha` | string | Alpha's actor ID |
| `ai.needs` | object | Binary needs (hungry, etc.) |
| `services` | object | Services offered |
| `relationships` | object | Relationships with actors |
| `knows` | array | Skills/knowledge possessed |
| `knowledge` | object | Specific facts known |

---

> **Next:** [Actor Interactions](04_actor_interactions.md) - Learn how to create combat, conditions, services, relationships, and environmental effects
