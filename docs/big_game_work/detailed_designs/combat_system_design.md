# Combat System Design for Big Game

**Version:** 1.0
**Date:** 2024-12-26
**Status:** Design - Awaiting Implementation

## 0. Executive Summary

Big_game currently has a combat stub (simple handler that prints "You attack X!") but no actual combat mechanics. This design document specifies how to integrate the existing `behavior_libraries.actor_lib.combat` system into big_game, making combat functional across all encounters.

**Key Decisions:**
- Use existing actor_lib combat system (don't reinvent)
- Combat is **optional** for most encounters (diplomacy preferred)
- Combat is **obligatory** only for spiders (design intent)
- Health tracking integrates with existing environmental hazards (drowning, hypothermia)
- Combat should be **deliberately hard** to encourage diplomatic solutions

---

## 1. Goals and Use Cases

### 1.1 Primary Goals

1. **Enable combat resolution** for encounters designed to support it
2. **Maintain narrative focus** - combat produces narrative text, not dry mechanics
3. **Integrate with existing systems** - health used by drowning, state machines, conditions
4. **Preserve difficulty balance** - combat harder than diplomacy (encourages non-violent solutions)
5. **Support design intent** - spiders obligatory, others optional

### 1.2 Use Cases

**UC1: Golem Combat** (Frozen Reaches)
- Player attacks stone guardian
- Golem transitions to "hostile" state (both golems via linked behavior)
- Golems counter-attack each turn
- Combat continues until player flees or defeats both golems
- **Outcome:** Golem deaths trigger on_golem_death handler, allow observatory access

**UC2: Spider Combat** (Beast Wilds) - OBLIGATORY
- Player attacks giant spider
- Spider attacks back, queen joins if present
- Spiders respawn every 10 turns while queen lives
- Combat continues until spiders defeated
- **Outcome:** Queen death stops respawns, drops loot (spider_silk_bundle, queen_venom_sac)

**UC3: Wolf Combat** (Beast Wilds) - OPTIONAL FALLBACK
- Player attacks alpha wolf
- Entire pack transitions to "hostile" and attacks
- Pack coordination gives combat bonuses
- **Outcome:** Wolf deaths set fungal death mark equivalent, close diplomatic path

**UC4: Spore Mother Combat** (Fungal Depths) - OPTIONAL FALLBACK
- Player attacks Spore Mother
- Sporelings join combat
- **Outcome:** Deaths set fungal death mark, close diplomatic path with Myconid

**UC5: Environmental Damage** (Already Implemented)
- Drowning deals 20 damage per turn when breath exhausted
- Uses `player.properties.health` with default 100
- **Outcome:** Player death when health reaches 0

---

## 2. Technical Design

### 2.1 Core Combat System

**Use existing:** `behavior_libraries.actor_lib.combat`

**Features:**
- Health/damage tracking (`properties.health`, `properties.max_health`)
- Attack arrays (`properties.attacks` with damage/type/effects)
- Armor calculation (`properties.armor`)
- Cover mechanics (reduce damage when in cover)
- Condition application (bleeding, knockdown, etc.)
- Death checking (automatic via turn phase hook)
- Counter-attacks via `on_damage` event

**Events:**
- `on_attack` - Actor initiates attack (verb handler)
- `on_damage` - Actor takes damage (behavior hook for counter-attacks)
- `on_death` - Actor dies (behavior hook for death reactions)
- `death_check` - Turn phase hook to check all actors for death

### 2.2 Data Structures

**Player:**
```json
{
  "id": "player",
  "properties": {
    "health": 100,
    "max_health": 100,
    "armor": 0,
    "attacks": [
      {
        "name": "unarmed strike",
        "damage": 5,
        "type": "melee"
      }
    ]
  }
}
```

**NPC (Generic Combat Actor):**
```json
{
  "id": "npc_example",
  "properties": {
    "health": 150,
    "max_health": 150,
    "armor": 10,
    "attacks": [
      {
        "name": "stone fist",
        "damage": 30,
        "type": "melee"
      },
      {
        "name": "ground slam",
        "damage": 20,
        "type": "melee",
        "effect": "knockdown"
      }
    ],
    "state_machine": {
      "states": ["neutral", "hostile", "dead"],
      "initial": "neutral"
    }
  }
}
```

### 2.3 Integration Points

**1. Remove Stub Handler**
- Delete: `examples/big_game/behaviors/shared/lib/core/combat.py`
- This is the stub that just prints "You attack X!"

**2. Load Actor_lib Combat**
- Create symlink or copy: `examples/big_game/behaviors/shared/lib/actor_lib/combat.py`
- Links to: `behavior_libraries/actor_lib/combat.py`

**3. Load Conditions Module (Dependency)**
- Create symlink: `examples/big_game/behaviors/shared/lib/actor_lib/conditions.py`
- Links to: `behavior_libraries/actor_lib/conditions.py`

**4. Register Death Check Hook**
Add to `game_state.json` metadata:
```json
"extra_turn_phases": [
  "turn_phase_scheduled",
  "turn_phase_commitment",
  "turn_phase_gossip",
  "turn_phase_spread",
  "death_check"
]
```

**5. Compatibility with Existing Systems**
- ✅ Drowning already uses `properties.health` directly
- ✅ State machines compatible with combat states
- ✅ Conditions system separate from health
- ✅ LLM narration uses EventResult.feedback from combat

---

## 3. Combat Encounter Designs

### 3.1 Stone Golems (Frozen Reaches)

**Design Intent:** Multi-solution puzzle with combat as one of 4 paths (password, crystal, ritual, combat). Combat should be **deliberately hard** to encourage other solutions.

**Combat Stats:**
```json
"stone_golem_1": {
  "properties": {
    "health": 150,
    "max_health": 150,
    "armor": 10,
    "attacks": [
      {
        "name": "stone fist",
        "damage": 30,
        "type": "melee"
      },
      {
        "name": "sweeping strike",
        "damage": 25,
        "type": "melee",
        "effect": "knockback"
      }
    ],
    "territorial": true,
    "linked_to": "stone_golem_2",
    "state_machine": {
      "states": ["guarding", "hostile", "passive", "serving", "destroyed"],
      "initial": "guarding"
    }
  }
}
```

**Behavior Hooks:**
- `on_damage` → `on_golem_damaged()` in golem_puzzle.py
  - Transitions this golem to "hostile"
  - Transitions linked golem to "hostile" (both engage)
  - Returns counter-attack via combat system
- `on_death` → `on_golem_death()` already exists
  - Tracks golems_destroyed count
  - Sets golem_protection_lost flag when both dead

**Balance Calculation:**
- Player unarmed: 5 damage - 10 armor = 0 damage (can't hurt golems!)
- Player needs weapon OR better attack
- Golem attack: 30 damage - 0 player armor = 30 damage
- Player dies in ~3 hits (100 health / 30 = 3.3 rounds)
- To kill both golems: 300 total health / 5 damage (if player gets weapon) = 60 attacks
- With golem counter-attacks, player would need ~20+ healing or high armor

**Recommendation:** Player should find weapons in temple or use other solutions. Combat viable but requires preparation.

**Player Weapon Options:**
- Add rusty_sword to temple treasures (damage: 15)
- With sword: 15 - 10 armor = 5 damage per hit
- 300 golem health / 5 = 60 hits needed
- Still takes ~30+ rounds with healing/dodging

### 3.2 Spiders (Beast Wilds) - OBLIGATORY COMBAT

**Design Intent:** NO diplomatic path. Pure combat encounter to contrast with diplomatic options elsewhere.

**Combat Stats:**
```json
"spider_matriarch": {
  "properties": {
    "health": 100,
    "max_health": 100,
    "armor": 5,
    "attacks": [
      {
        "name": "venomous bite",
        "damage": 20,
        "type": "melee",
        "applies_condition": {
          "type": "poison",
          "severity": 10
        }
      },
      {
        "name": "web spray",
        "damage": 10,
        "type": "ranged",
        "effect": "web_slow"
      }
    ],
    "state_machine": {
      "states": ["hostile", "dead"],
      "initial": "hostile"
    }
  }
},
"giant_spider_1/2": {
  "properties": {
    "health": 40,
    "max_health": 40,
    "armor": 2,
    "attacks": [
      {
        "name": "bite",
        "damage": 15,
        "type": "melee"
      }
    ],
    "state_machine": {
      "states": ["hostile", "dead"],
      "initial": "hostile"
    }
  }
}
```

**Behavior Hooks:**
- `on_death` → `on_spider_queen_death()` already exists
  - Stops future respawns
  - Drops loot: spider_silk_bundle, queen_venom_sac

**Web Combat Bonuses:**
- Location property: `"web_effects": true`
- Spiders get +5 damage in web locations
- Player movement slowed (handled by existing spider_nest.py)

**Respawn Mechanics:** Already implemented in spider_nest.py
- 2 spiders respawn every 10 turns while queen alive
- Combat continues until queen defeated

**Balance Calculation:**
- Queen: 100 health / 10 player damage (with weapon) = 10 hits
- 2 Minions: 80 health / 10 player damage = 8 hits each
- Total: 26 hits minimum
- Minions respawn every 10 turns
- Strategy: Kill queen first, then clean up minions

### 3.3 Wolves (Beast Wilds) - OPTIONAL FALLBACK

**Design Intent:** Domestication preferred. Combat possible but closes diplomatic path.

**Combat Stats:**
```json
"alpha_wolf": {
  "properties": {
    "health": 80,
    "max_health": 80,
    "armor": 3,
    "attacks": [
      {
        "name": "alpha bite",
        "damage": 25,
        "type": "melee"
      },
      {
        "name": "howl",
        "damage": 0,
        "type": "special",
        "effect": "rally_pack"
      }
    ],
    "pack_behavior": {
      "pack_follows_alpha_state": true,
      "followers": ["frost_wolf_1", "frost_wolf_2"]
    },
    "state_machine": {
      "states": ["hostile", "wary", "neutral", "friendly", "allied"],
      "initial": "hostile"
    }
  }
},
"frost_wolf_1/2": {
  "properties": {
    "health": 50,
    "max_health": 50,
    "armor": 2,
    "attacks": [
      {
        "name": "bite",
        "damage": 15,
        "type": "melee"
      }
    ],
    "state_machine": {
      "states": ["hostile", "wary", "neutral", "friendly", "allied"],
      "initial": "hostile"
    }
  }
}
```

**Behavior Hooks:**
- `on_damage` → Wolf transitions to "hostile", pack mirrors via existing pack_mirroring.py
- `on_death` → Set flag equivalent to fungal death mark (closes diplomatic paths)

**Pack Combat Mechanics:**
- All wolves attack when one is attacked (state mirroring)
- Coordination bonus: +5 damage when 2+ wolves in same location

**Balance Calculation:**
- 3 wolves: 180 total health
- Combined damage: 55 per round (alpha 25 + 2x15)
- Player dies in 2 rounds without armor
- Wolves die in 18 rounds with player weapon (10 damage)
- Heavily favors wolves - combat is a bad choice

### 3.4 Spore Mother & Sporelings (Fungal Depths) - OPTIONAL FALLBACK

**Design Intent:** Light puzzle solution preferred. Combat alternative but closes diplomatic path with Myconid.

**Combat Stats:**
```json
"npc_spore_mother": {
  "properties": {
    "health": 200,
    "max_health": 200,
    "armor": 8,
    "attacks": [
      {
        "name": "spore cloud",
        "damage": 15,
        "type": "ranged",
        "applies_condition": {
          "type": "spore_infection",
          "severity": 20
        }
      },
      {
        "name": "tendril strike",
        "damage": 25,
        "type": "melee"
      }
    ],
    "state_machine": {
      "states": ["hostile", "wary", "allied", "dead", "confused"],
      "initial": "hostile"
    }
  }
},
"npc_sporeling_1": {
  "properties": {
    "health": 30,
    "max_health": 30,
    "armor": 0,
    "attacks": [
      {
        "name": "spore burst",
        "damage": 8,
        "type": "melee",
        "applies_condition": {
          "type": "spore_infection",
          "severity": 5
        }
      }
    ],
    "state_machine": {
      "states": ["hostile", "wary", "allied", "confused"],
      "initial": "hostile"
    }
  }
}
```

**Behavior Hooks:**
- `on_death` → Trigger on_fungal_kill() from fungal_death_mark.py
  - Sets has_killed_fungi flag
  - Myconid Elder starts at trust -3
  - Closes alliance path

**Spore Infection Condition:**
- Severity increases each turn in fungal zones
- Cured by light (existing light_puzzle.py mechanics)
- High severity causes damage

**Balance Calculation:**
- Spore Mother: 200 health, very tanky
- 3 Sporelings: 90 total health
- Combined: 290 health
- Infection condition makes prolonged combat dangerous
- Encourages puzzle solution

---

## 4. Implementation Phases

### Phase 1: Core Integration (Issue #274)
**Goal:** Make combat system functional

1. Remove stub handler: `behaviors/shared/lib/core/combat.py`
2. Create symlinks:
   - `behaviors/shared/lib/actor_lib/combat.py` → `behavior_libraries/actor_lib/combat.py`
   - `behaviors/shared/lib/actor_lib/conditions.py` → `behavior_libraries/actor_lib/conditions.py`
3. Add death_check to extra_turn_phases in game_state.json
4. Add player combat properties to game_state.json
5. Test basic combat works (player can attack, take damage, die)

**Acceptance:** Attack command deals damage, health tracks, death triggers

### Phase 2: Golem Combat (Issue #274 - Current)
**Goal:** Validate combat system with golem encounter

1. Migrate golem stats to combat format (flatten stats object)
2. Add golem attacks arrays
3. Implement on_golem_damaged handler (state transitions + counter-attack)
4. Update test_golem_combat.txt walkthrough
5. Test full combat loop (attack, damage, counter-attack, death)

**Acceptance:** Golem combat walkthrough passes 100%

### Phase 3: Spider Combat (New Issue - HIGH PRIORITY)
**Goal:** Implement obligatory combat encounter

1. Add spider health/attacks to all spider NPCs
2. Implement web combat bonuses
3. Add loot drops on queen death
4. Create spider combat walkthrough
5. Test respawn mechanics work with combat

**Acceptance:** Spider combat playable, queen defeated grants loot

### Phase 4: Optional Combat Encounters (Future Issues)
**Goal:** Complete combat coverage

1. Wolf combat (low priority - domestication preferred)
2. Spore Mother combat (low priority - puzzle preferred)
3. Any other encounters requiring combat

**Acceptance:** All designed combat encounters functional

### Phase 5: Balance & Polish (Future)
**Goal:** Tune difficulty, add weapons/items

1. Add weapons to game world (swords, bows, etc.)
2. Add healing items (potions, bandages)
3. Add armor items
4. Balance combat encounters based on playtesting
5. Add combat-specific conditions (bleeding, stunned, etc.)

**Acceptance:** Combat difficulty matches design intent

---

## 5. Weapons & Equipment Design

### 5.1 Player Weapons

**Unarmed** (Default):
```json
{
  "name": "unarmed strike",
  "damage": 5,
  "type": "melee"
}
```

**Rusty Sword** (Temple treasure):
```json
{
  "id": "rusty_sword",
  "name": "rusty sword",
  "description": "An old blade, still serviceable despite the rust.",
  "location": "temple_sanctum",
  "properties": {
    "portable": true,
    "weapon": {
      "damage": 15,
      "type": "melee"
    }
  }
}
```

**Future Weapons:**
- Bow (ranged, 12 damage)
- Spear (melee, 18 damage, reach)
- Frost blade (melee, 20 damage, cold type - bonus vs golems)

### 5.2 Armor & Protection

**Cold Weather Gear** (Already exists):
- No armor bonus (it's for hypothermia, not combat)

**Cold Resistance Cloak** (Already exists):
- No armor bonus (cold immunity only)

**Future Armor:**
- Leather armor (armor: 5)
- Chain mail (armor: 10, found in temple)
- Shield (armor: 3, can be used with one-handed weapons)

### 5.3 Healing Items

**Bandages** (Already exists):
```json
{
  "id": "bandages",
  "name": "bandages",
  "effect": "heal",
  "heal_amount": 20
}
```

**Future Healing:**
- Healing potion (heal: 50)
- Campfire rest (heal: full, requires safe location)
- Healer service (Civilized Remnants, heal: full, costs items)

---

## 6. Design Constraints

### 6.1 What Combat MUST Support

1. **Multiple attackers** - Golems, wolf packs, spider swarms
2. **Counter-attacks** - NPCs respond when damaged
3. **Death consequences** - Loot, flags, state changes
4. **Linked behavior** - One golem attacked, both engage
5. **State transitions** - Peaceful → hostile when attacked
6. **Environmental integration** - Health shared with drowning/hypothermia
7. **Narrative focus** - Combat produces story text, not raw numbers

### 6.2 What Combat Does NOT Need

1. ❌ Initiative/turn order (all attacks resolve simultaneously)
2. ❌ Movement/positioning (location-based only)
3. ❌ Complex targeting (attack finds targets by name)
4. ❌ Experience/leveling (no character progression)
5. ❌ Inventory weight limits for weapons/armor
6. ❌ Durability/weapon degradation
7. ❌ Critical hits/misses (deterministic damage)

### 6.3 Compatibility Requirements

1. ✅ Must use `properties.health` (drowning already does)
2. ✅ Must work with state machines (all NPCs have them)
3. ✅ Must work with conditions system (hypothermia, spores use it)
4. ✅ Must trigger on_death behaviors (death_reactions infrastructure)
5. ✅ Must support LLM narration (EventResult.feedback)
6. ✅ Must not break existing non-combat encounters

---

## 7. Open Questions & Decisions Needed

### 7.1 Player Weapon Mechanics

**Question:** How does player equip/use weapons?

**Options:**
1. **Auto-equip** - Taking weapon automatically adds its attack to player
2. **Explicit equip** - Player must "equip sword" before attacks use it
3. **Contextual** - "attack with sword" vs "attack with fists"

**Recommendation:** Auto-equip for Phase 1 (simplest). Can enhance later.

### 7.2 Armor Mechanics

**Question:** Should armor be equipped or automatic?

**Options:**
1. **Auto** - Having armor in inventory grants armor bonus
2. **Equipped** - Must "wear armor" to get bonus
3. **Slot-based** - Head/chest/legs separate

**Recommendation:** Auto for Phase 1. Equipped slots for Phase 5 (polish).

### 7.3 Death Handling

**Question:** What happens when player dies?

**Options:**
1. **Game over** - Session ends, "You died" message
2. **Respawn** - Player returns to safe location with penalty
3. **Save/load** - Player can reload from last save

**Recommendation:** Game over for now. Respawn/save system is out of scope.

### 7.4 NPC Death Permanence

**Question:** Are NPC deaths permanent?

**Current behavior:**
- Spiders: Respawn while queen lives (implemented)
- Others: Transition to "dead" state (reversible?)

**Recommendation:** Deaths are permanent (state machine stays "dead"). Respawns are encounter-specific (spiders only).

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Test Coverage:**
1. ✅ Combat system unit tests (already exist in tests/test_combat_behaviors.py)
2. ✅ Attack selection logic
3. ✅ Damage calculation with armor
4. ✅ Death checking

**New Tests Needed:**
1. Golem linked combat (both engage when one attacked)
2. Wolf pack mirroring in combat
3. Spider respawn during combat
4. Environmental + combat damage stacking (drowning + combat)

### 8.2 Integration Tests

**Walkthroughs:**
1. `test_golem_combat.txt` - Golem encounter (Phase 2)
2. `test_spider_combat.txt` - Spider nest (Phase 3)
3. `test_wolf_combat.txt` - Wolf pack (Phase 4)
4. `test_spore_combat.txt` - Fungal combat (Phase 4)
5. `test_combined_damage.txt` - Drowning + combat (edge case)

**Acceptance Criteria:**
- 100% walkthrough success
- Combat resolves correctly
- Death triggers appropriate handlers
- Loot/flags set correctly

### 8.3 Balance Testing

**Metrics to Track:**
1. Average rounds to defeat encounter
2. Player health remaining after victory
3. Comparison: combat difficulty vs diplomatic difficulty
4. Weapon/armor impact on difficulty

**Balance Goals:**
- Combat should be **harder** than diplomacy (encourage peaceful solutions)
- Combat should be **possible** with preparation (weapons, healing, strategy)
- Combat should be **punishing** without preparation (encourage exploration first)

---

## 9. Migration Path from Current State

### 9.1 Existing Health Values

**Current NPCs with health:**
- Golems: `properties.stats.health` (150) → Migrate to `properties.health`
- Spore Mother: `properties.health` (200) → Keep as-is
- Sporelings: `properties.health` (20-30) → Keep as-is
- Aldric: `properties.health` (40) → Keep (non-combat NPC)

**Migration:**
1. Flatten golem stats (move health/armor to top-level properties)
2. Add max_health to all NPCs with health
3. Add attacks arrays to combat NPCs
4. Leave Aldric as-is (civilian, no attacks)

### 9.2 Existing State Machines

**All combat NPCs already have state machines:**
- ✅ "hostile" state exists
- ✅ "dead" state exists
- ✅ Transitions already implemented

**No changes needed** - combat system works with existing states.

### 9.3 Existing Behaviors

**Death reactions:**
- ✅ Golem: on_golem_death (already exists)
- ✅ Spider Queen: on_spider_queen_death (already exists)
- ✅ Fungal: on_fungal_kill (already exists)

**Add new:**
- on_golem_damaged (counter-attack + state transition)
- on_wolf_damaged (pack coordination)
- on_spore_damaged (spore cloud release)

---

## 10. Success Criteria

### 10.1 Phase 1 Success (Core Integration)

- [ ] Attack command deals damage to NPCs
- [ ] NPCs lose health when attacked
- [ ] NPCs die when health reaches 0
- [ ] Player takes damage from NPC attacks
- [ ] Player dies when health reaches 0
- [ ] Death check runs each turn
- [ ] on_death handlers trigger correctly

### 10.2 Phase 2 Success (Golem Combat)

- [ ] Attacking one golem activates both (linked behavior)
- [ ] Golems transition to "hostile" state
- [ ] Golems counter-attack each turn
- [ ] Golem armor reduces player damage
- [ ] Defeating both golems allows observatory access
- [ ] test_golem_combat.txt passes 100%

### 10.3 Final Success (All Combat)

- [ ] All designed combat encounters functional
- [ ] Combat difficulty matches design intent (hard but fair)
- [ ] Weapons/armor/healing items integrated
- [ ] All walkthroughs pass 100%
- [ ] No regressions in non-combat systems (drowning, etc.)

---

## 11. Related Documents

- **Actor_lib Combat:** `behavior_libraries/actor_lib/combat.py`
- **Beast Wilds Design:** `docs/big_game_work/detailed_designs/beast_wilds_detailed_design.md`
- **Frozen Reaches Design:** `docs/big_game_work/detailed_designs/frozen_reaches_detailed_design.md`
- **Fungal Depths Design:** `docs/big_game_work/detailed_designs/fungal_depths_detailed_design.md`
- **Quick Reference:** `docs/quick_reference.md`
- **Architecture:** `user_docs/architectural_conventions.md`
