# Common Patterns and Recipes

> **Part of the [Authoring Manual](00_start_here.md)**
>
> Previous: [The Behavior System](05_behaviors.md) | Next: [Spatial Rooms](07_spatial.md)

---

This chapter provides practical recipes for common game design goals. For detailed API documentation, see the referenced chapters.

---

## 6.1 Puzzles

### Hidden Items (Revelation)

**Goal:** Item is hidden until revealed by some action.

**Pattern:**
```json
{
  "id": "item_secret_key",
  "name": "key",
  "description": "A hidden key.",
  "location": "loc_study",
  "properties": {
    "portable": true,
    "states": {
      "hidden": true
    }
  }
}
```

**Behavior to reveal:**
```python
def on_push(entity, accessor, context):
    """Pushing the panel reveals the key."""
    if entity.id == "item_panel":
        key = accessor.get_item("item_secret_key")
        if key and key.states.get("hidden", False):
            key.states["hidden"] = False
            return EventResult(
                allow=True,
                message="The panel slides aside, revealing a hidden key!"
            )
    return EventResult(allow=True)
```

### Locked Containers and Doors

**Pattern:**
```json
{
  "id": "item_chest",
  "name": "chest",
  "location": "loc_treasury",
  "properties": {
    "portable": false,
    "container": {
      "is_surface": false,
      "capacity": 10,
      "open": false,
      "locked": true,
      "lock_id": "lock_chest"
    }
  }
}
```

```json
{
  "id": "lock_chest",
  "name": "lock",
  "properties": {
    "opens_with": ["item_iron_key"],
    "auto_unlock": false
  }
}
```

**Commands:** `unlock chest with iron key` → `open chest` → `take gem from chest`

### Sequence Puzzles

**Goal:** Player must perform actions in correct order.

```python
from behavior_libraries.puzzle_lib import sequence_tracker

def on_play(entity, accessor, context):
    """Handle playing notes on the harp."""
    note = context.get("note")
    sequence_tracker.track_action(entity, note)

    if sequence_tracker.check_sequence(entity, ["C", "E", "G", "E", "C"]):
        door = accessor.get_item("door_music_chamber")
        door.door_locked = False
        return EventResult(allow=True,
            message="The harp resonates beautifully, and a door unlocks!")

    if len(entity.states.get("sequence", [])) >= 5:
        sequence_tracker.reset_sequence(entity)
        return EventResult(allow=True, message="Discordant. Try again.")

    return EventResult(allow=True)
```

### Threshold/Weight Puzzles

**Goal:** Achieve exact weight or resource amount.

```python
from behavior_libraries.puzzle_lib import threshold_checker

def on_put(entity, accessor, context):
    """Handle placing items on the scale."""
    items_on_scale = accessor.get_items_in_container("item_scale")
    total_weight = sum(item.properties.get("weight", 0) for item in items_on_scale)

    if threshold_checker.check_threshold(total_weight, 50, tolerance=0):
        accessor.get_item("door_secret").states["revealed"] = True
        return EventResult(allow=True,
            message="The scale balances perfectly, and a door swings open!")

    return EventResult(allow=True,
        message=threshold_checker.get_threshold_feedback(total_weight, 50))
```

---

## 6.2 Interactive Objects

### Containers

**Enclosed container (must open):**
```json
{
  "properties": {
    "container": {
      "is_surface": false,
      "capacity": 10,
      "open": false
    }
  }
}
```

**Surface (always accessible):**
```json
{
  "properties": {
    "container": {
      "is_surface": true,
      "capacity": 5
    }
  }
}
```

### Light Sources

```json
{
  "id": "item_lantern",
  "name": "lantern",
  "properties": {
    "portable": true,
    "provides_light": true,
    "states": { "lit": false }
  },
  "behaviors": ["behaviors.core.light_sources"]
}
```

Core behavior handles `light lantern` and `extinguish lantern` automatically.

### Readable Items

**Simple:**
```json
{
  "properties": {
    "readable": true,
    "text": "The spell of opening: Speak 'alohomora' to any lock."
  }
}
```

**Progressive revelation:**
```python
def on_read(entity, accessor, context):
    times_read = entity.states.get("times_read", 0) + 1
    entity.states["times_read"] = times_read

    pages = [
        "The first page describes a ritual...",
        "The second page reveals the ingredients...",
        "You've learned all the book contains."
    ]
    return EventResult(allow=True, message=pages[min(times_read-1, len(pages)-1)])
```

---

## 6.3 NPC Services

For full API documentation, see [Actor Interactions - Services](04_actor_interactions.md#5-services-framework).

### Healer NPC

**Goal:** NPC cures conditions for payment.

```json
{
  "id": "npc_healer",
  "name": "Healer Elara",
  "location": "loc_healer_hut",
  "properties": {
    "health": 60,
    "max_health": 60,
    "services": {
      "cure_poison": {
        "accepts": ["rare_herbs", "gold"],
        "amount_required": 5,
        "cure_amount": 100
      },
      "heal": {
        "accepts": ["gold"],
        "amount_required": 25,
        "restore_amount": 50
      }
    },
    "ai": { "disposition": "friendly" }
  }
}
```

**Player uses:** `ask healer to cure poison` (with herbs/gold in inventory)

### Merchant NPC

**Goal:** NPC sells items for gold.

```json
{
  "properties": {
    "services": {
      "sell_sword": {
        "accepts": ["gold"],
        "amount_required": 50,
        "sells": "item_steel_sword"
      },
      "sell_potion": {
        "accepts": ["gold"],
        "amount_required": 20,
        "sells": "item_healing_potion"
      }
    }
  }
}
```

### Teacher NPC

**Goal:** NPC teaches skills.

```json
{
  "properties": {
    "services": {
      "teach_herbalism": {
        "accepts": ["gold"],
        "amount_required": 100,
        "grants": "herbalism"
      }
    }
  }
}
```

After paying, player gains `"herbalism"` in their `knows` array.

### Trust Discounts

NPCs give discounts to trusted customers. Trust builds through successful transactions.

- `trust >= 3`: 50% discount
- `trust >= 5`: Special services unlocked

---

## 6.4 Combat Encounters

For full API documentation, see [Actor Interactions - Combat](04_actor_interactions.md#4-combat).

### Hostile Creature

**Goal:** Enemy that attacks the player.

```json
{
  "id": "npc_wolf",
  "name": "Wolf",
  "location": "loc_forest",
  "properties": {
    "health": 60,
    "max_health": 60,
    "attacks": [
      { "name": "bite", "damage": 15, "type": "piercing" },
      { "name": "tackle", "damage": 8, "effect": "knockdown" }
    ],
    "ai": {
      "disposition": "hostile",
      "morale": 60,
      "flee_threshold": 20
    }
  }
}
```

Wolf attacks player each turn until killed or fled.

### Pack of Enemies

**Goal:** Group that acts together under alpha leadership.

```json
// Alpha
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

// Followers
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

Followers copy alpha's disposition. Domesticate the alpha → entire pack becomes friendly.

### Construct (Immune to Poison/Disease)

**Goal:** Enemy immune to certain conditions.

```json
{
  "properties": {
    "body": {
      "form": "construct",
      "material": "stone"
    }
  }
}
```

Constructs are automatically immune to poison, disease, bleeding, and don't need to breathe.

### Venomous Creature

**Goal:** Attacks apply conditions.

```json
{
  "properties": {
    "attacks": [
      {
        "name": "venomous_bite",
        "damage": 8,
        "applies_condition": {
          "name": "spider_venom",
          "severity": 40,
          "damage_per_turn": 1,
          "duration": 10
        }
      }
    ]
  }
}
```

---

## 6.5 Relationships and Domestication

For full API documentation, see [Actor Interactions - Relationships](04_actor_interactions.md#6-relationships-and-domestication).

### Tameable Creature

**Goal:** Hostile creature that becomes friendly when fed.

```json
{
  "id": "npc_wolf",
  "properties": {
    "ai": {
      "disposition": "hostile",
      "needs": { "hungry": true }
    },
    "relationships": {}
  }
}
```

**Player action:** `give meat to wolf`

1. Satisfies hunger → disposition changes to neutral
2. Repeated feeding builds gratitude
3. `gratitude >= 3` → domesticated (friendly)

### Intimidation

**Goal:** Scare NPCs into compliance.

Build fear through violence or threats. At `fear >= 5`, NPC may flee or comply with demands.

---

## 6.6 Environmental Hazards

For full API documentation, see [Actor Interactions - Environmental Effects](04_actor_interactions.md#7-environmental-effects).

### Underwater Area

**Goal:** Location where actors lose breath each turn.

```json
{
  "id": "loc_underwater_cave",
  "name": "Underwater Cave",
  "properties": {
    "breathable": false
  }
}
```

Actors with `breath` property lose breath each turn. At `breath <= 0`, they drown.

### Rescue Scenario

**Goal:** NPC in danger that player must save.

```json
{
  "id": "npc_sailor",
  "name": "Drowning Sailor",
  "location": "loc_underwater_cave",
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

Sailor drowns in ~5 turns. Player must rescue them (drag to safety) before they die.

### Contaminated Area

**Goal:** Location that applies conditions over time.

```json
{
  "id": "part_spore_cloud",
  "name": "Spore Cloud",
  "part_of": "loc_fungal_cave",
  "properties": {
    "applies_condition": {
      "name": "fungal_infection",
      "severity_per_turn": 10,
      "contagious_range": "touch"
    }
  }
}
```

Actors in this part gain infection severity each turn.

---

## 6.7 Locations and Navigation

### Exit Types

**Open passage:**
```json
{ "north": { "type": "open", "to": "loc_hallway" } }
```

**Door:**
```json
{ "east": { "type": "door", "to": "loc_storage", "door_id": "door_storage" } }
```

**Named exit:**
```json
{
  "up": {
    "type": "open",
    "to": "loc_tower_top",
    "name": "spiral staircase",
    "description": "A narrow staircase winds upward."
  }
}
```

### Hidden Exits

```json
{
  "west": {
    "type": "open",
    "to": "loc_secret_room",
    "properties": { "states": { "hidden": true } }
  }
}
```

Reveal with behavior: `west_exit.properties["states"]["hidden"] = False`

### Conditional Exits

```python
def on_go(entity, accessor, context):
    """Prevent passage unless condition met."""
    if entity.id == "loc_guard_post" and context.get("direction") == "north":
        actor = accessor.get_actor(context["actor_id"])
        if "item_guard_pass" not in actor.inventory:
            return EventResult(allow=False,
                message="The guard blocks your way. 'Show your pass!'")
    return EventResult(allow=True)
```

### One-Way Passages

Simply don't define the return exit. Player goes down the chute but can't climb back up.

---

## 6.8 Time-Sensitive Scenarios

### Ticking Clock

**Goal:** Player has limited turns to complete a task.

Use turn hooks and the turn counter:

```python
def on_turn_start(state, accessor):
    """Check time limit."""
    if state.turn_count >= 50:
        # Time's up!
        accessor.get_item("item_bomb").states["exploded"] = True
        return EventResult(message="BOOM! The bomb explodes!")
    elif state.turn_count >= 45:
        return EventResult(message="You hear ominous ticking...")
    return None
```

### Progressive Condition

**Goal:** Condition worsens over time, creating urgency.

```json
{
  "conditions": {
    "poison": {
      "severity": 30,
      "damage_per_turn": 2,
      "progression_rate": 5
    }
  }
}
```

Poison deals 2 damage/turn AND increases severity by 5/turn. Player must find cure quickly.

---

## 6.9 Information and Knowledge

### Knowledge Gates

**Goal:** Player needs to learn something before they can act.

```json
{
  "id": "item_ancient_tome",
  "properties": {
    "readable": true,
    "grants_knowledge": "ritual_of_binding"
  }
}
```

```python
def on_use(entity, accessor, context):
    """Use the ritual circle."""
    actor = accessor.get_actor(context["actor_id"])
    if "ritual_of_binding" not in actor.properties.get("knowledge", {}):
        return EventResult(allow=False,
            message="You don't know how to use this circle.")
    # Proceed with ritual...
```

### Skill Checks

**Goal:** Some actions require learned skills.

```python
def on_examine(entity, accessor, context):
    """Herbalism skill reveals plant properties."""
    actor = accessor.get_actor(context["actor_id"])
    if "herbalism" in actor.properties.get("knows", []):
        return EventResult(allow=True,
            message="Your herbalism knowledge tells you this plant cures poison.")
    return EventResult(allow=True,
        message="A strange plant. You're not sure what it does.")
```

---

> **Next:** [Spatial Rooms](07_spatial.md) - Learn about parts, positioning, and complex room layouts
