# Combat System Design Sketch for the Unified Actor Framework
### Two Approaches: Basic Combat and Advanced Combat  
*(Designed for compatibility with your engine’s architecture: unified actors, pluggable behaviors, property-driven stats, and spatial relations.)*

This document expands the earlier design sketch into a more complete proposal suitable for implementation and game authoring. It includes:

1. **Combat Goals and Constraints**
2. **Option A: Simple HP + Damage System**
3. **Option B: Advanced System (Hit Chance, Damage Types, Cover, Stealth Interactions)**
4. **Integration with Existing Architecture**
5. **Recommended Extension Points for Authors**
6. **Migration Path: Adding Combat to Existing Actors**
7. **Future Extensions**

---

# 1. Combat Goals and Constraints

Your design goals (uniformity, flexibility, low authorial burden) imply that the combat system must:

### ✓ Treat all combatants as **actors**  
No separate “monster” or “enemy” subclass. Actors differ only by properties and behaviors.

### ✓ Store combat stats in **properties**, not custom fields  
This keeps the engine free of rigid assumptions and allows per-game stat schemas.

### ✓ Use **behaviors** as the unit of combat logic  
Implement combat via behavior libraries such as:
- `behaviors.combat.basic_attack`
- `behaviors.combat.advanced_attack`
- `behaviors.combat.ai.simple`
- `behaviors.combat.ai.ranged`

### ✓ Use the existing spatial model  
Spatial relations (e.g., `NEAR`, `IN_FRONT_OF`, `BEHIND`) modify combat outcomes.

### ✓ Be optional and modular  
Games that do not use combat should not pay a complexity cost.

---

# 2. Option A — Simple Combat System  
### *For fast implementation and minimal author burden*

This system provides:

- Hit points (HP)  
- Flat attack and defense values  
- Guaranteed hits (no miss chance)  
- Damage reduced by defense  
- Simple death/KO handling  
- Optional spatial gating (must be close enough to attack)

---

## 2.1 Actor Stat Block

Add this to each actor’s `properties`:

```jsonc
"properties": {
  "stats": {
    "hp": 10,
    "max_hp": 10,
    "attack": 3,
    "defense": 1
  }
}
```

Minimal, readable, author-friendly.

---

## 2.2 Optional Weapon Stats

```jsonc
"properties": {
  "weapon": {
    "damage": 2
  }
}
```

If equipped, weapon damage is added to actor attack.

You may later add tags like `"range": "long"` or `"type": "slash"`.

---

## 2.3 Attack Behavior (Pseudocode)

```python
def basic_attack(accessor, attacker_id, target_id):
    attacker = accessor.get_actor(attacker_id)
    target = accessor.get_actor(target_id)

    if not accessor.can_reach(attacker, target):
        return accessor.fail("You cannot reach them from here.")

    dmg = compute_damage(attacker, target)
    accessor.apply_damage(target_id, dmg, source=attacker_id)

    return accessor.success(
        f"You hit {target.name} for {dmg} damage."
    )
```

Damage calculation:

```python
def compute_damage(attacker, target):
    atk = attacker.properties["stats"].get("attack", 1)
    weapon = attacker.properties.get("weapon")
    if weapon:
        atk += weapon.get("damage", 0)

    defense = target.properties["stats"].get("defense", 0)
    return max(1, atk - defense)
```

---

## 2.4 Damage Application

```python
def apply_damage(self, actor_id, amount, source=None):
    actor = self.get_actor(actor_id)
    stats = actor.properties.setdefault("stats", {})
    stats["hp"] = max(0, stats["hp"] - amount)

    if stats["hp"] <= 0:
        self.handle_actor_death(actor, source)

    self.save_actor(actor)
```

---

## 2.5 Simple Death Handling

You may choose one of:

- Actor becomes inert: `"dead": true`  
- Actor becomes item-like “corpse”  
- Actor disappears (vanishes)  
- Room-specific death behaviors can trigger via behavior lists  

---

## 2.6 NPC Response Loop

After any action:

1. Find hostile NPCs in same location  
2. For each:
   - If reachable → attack  
   - Else → move closer (adjust spatial relations)

---

# 3. Option B — Advanced Combat System  
### *Adds more tactical depth, still using simple relational spatial rules*

This model adds:

- Accuracy / evasion  
- Strength and toughness for damage modeling  
- Armor and resistances  
- Weapon properties (range, damage dice, tags)  
- Cover and flanking bonuses via spatial relations  
- Status effects (stunned, poisoned, bleeding)  
- Initiative ordering for multi-enemy fights  

---

## 3.1 Expanded Actor Stats

```jsonc
"properties": {
  "stats": {
    "max_hp": 14,
    "hp": 14,
    "strength": 3,
    "agility": 2,
    "accuracy": 4,
    "evasion": 3,
    "armor": 1,
    "toughness": 1,
    "initiative": 3
  },
  "status": {
    "stunned": false,
    "bleeding": 0,
    "poisoned": 0
  }
}
```

---

## 3.2 Weapon Properties

```jsonc
"properties": {
  "weapon": {
    "damage_die": "1d6",
    "damage_type": "pierce",
    "accuracy_bonus": 1,
    "reach": "melee",
    "tags": ["finesse"]
  }
}
```

---

## 3.3 Armor Properties

```jsonc
"properties": {
  "armor": {
    "armor_rating": 2,
    "resist": {
      "slash": 1,
      "pierce": 0,
      "fire": 2
    }
  }
}
```

---

## 3.4 Attack Resolution Pipeline

1. **Check reach** — spatial gating  
2. **Accuracy check** — attacker accuracy vs. target evasion  
3. **Damage roll** — weapon dice + strength  
4. **Toughness mitigation**  
5. **Armor and resistance mitigation**  
6. **Status effects**  
7. **Apply damage**  

---

## 3.5 Spatial Effects

Your spatial model enables:

### ✓ Cover  
`BEHIND(target, pillar)` → +2 evasion or partial immunity to ranged weapons.

### ✓ Flanking  
`BEHIND(attacker, target)` → accuracy +1 or extra damage.

### ✓ Reach  
`NEAR(attacker, target)` required for melee.

### ✓ Ranged line-of-sight  
Blocked if `BEHIND(target, obstacle)`.

---

## 3.6 Initiative Model

A simple initiative sequence:

1. Gather all combatants  
2. Sort by `stats.initiative`  
3. Player acts on their turn  
4. NPCs act in order  

This uses no external combat loop and fits your request-driven game cycle.

---

# 4. Integration with Existing Architecture

### ✔ All stats stored in `actor.properties`  
No structural modifications to Actor class.

### ✔ Combat behaviors added through behavior lists  
Per-actor, per-room, per-game.

### ✔ Spatial queries handled through `StateAccessor`  
E.g., `can_reach`, `has_cover`, `behind_relative`.

### ✔ Damage application via an accessor helper  
Consistent with your design for world mutation.

### ✔ Optionality preserved  
Games without combat simply omit combat-related behaviors.

---

# 5. Extension Points for Authors

Authors control combat flavor by editing:

### Actor stats  
Defining weak or strong enemies.

### Item properties  
Weapons and armor adjust combat depth.

### Room behaviors  
Rooms can apply special environmental conditions:
- Darkness penalties  
- Magical distortion  
- Slippery floors  
- Burning terrain

### Behavior modules  
Authors can include:
- Simple AI  
- Advanced AI  
- Special attacks  
- Nonlethal combat modes

---

# 6. Migration Path

To add combat to an existing game:

1. Add default `stats` to player and NPC actors.  
2. Add optional `weapon` or `armor` properties.  
3. Add `ATTACK` verb mapping to a behavior.  
4. Add a post-action tick for NPC retaliation.  
5. Add a death handler behavior.  
6. Test simple combat before enabling advanced stats.

Start small, grow only if needed.

---

# 7. Future Extensions

- **Stealth attacks**: bonuses when behind a target  
- **Area-of-effect attacks**  
- **Fear/morale mechanics**  
- **Skill-based progression**  
- **Critical hits**  
- **Guarding, parrying, dodging verbs**

These layer smoothly over both Option A and B.

---

# End of Document