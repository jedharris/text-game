# Placeholder NPC Specifications

**Purpose:** Complete specifications for NPCs that only had minimal documentation in sketches, extracted and synthesized from detailed_designs and existing game patterns.

**Context:** Issue #425 - All 14 placeholder NPCs need implementation. This document provides full specs for the 5 NPCs with minimal sketch documentation.

**Generated:** 2026-01-08

---

## 1. Giant Spiders (giant_spider_1, giant_spider_2)

**Source:** beast_wilds_detailed_design.md Section 5.4 (Pack Dynamics)

### Role
Combat followers of spider_queen (currently spider_matriarch in game_state.json). Always hostile, respawn while queen lives.

### Type & Location
- Type: `beast`
- Location: `spider_thicket` (Beast Wilds)
- Pack: `spider_pack`, role: `follower`, leader: `spider_matriarch`

### Properties

```json
{
  "health": 50,
  "pack": {
    "id": "spider_pack",
    "role": "follower",
    "leader": "spider_matriarch"
  },
  "respawn": {
    "enabled": true,
    "interval_turns": 10,
    "max_count": 2,
    "condition": "spider_matriarch.state != 'dead'"
  }
}
```

### State Machine

```json
{
  "states": ["hostile", "dead"],
  "initial": "hostile",
  "transitions": {
    "hostile->dead": "Health reaches 0"
  }
}
```

**Note:** Unlike wolf pack, spiders do NOT mirror leader's state. Spider queen has only hostile/dead states.

### Reactions Required

**encounter_reactions:**
- Trigger: Player enters spider_thicket
- Behavior: Immediate hostile encounter if spider_matriarch is alive
- Combat stats: Bite (12 damage), Web spray (8 damage + restrained condition)

**death_reactions:**
- Loot: spider_silk (common), venom_sac (uncommon)
- No respawn if spider_matriarch is dead

### Pack Dynamics

**State mirroring:** No - always hostile regardless of leader state
**Location mirroring:** No - spread through spider_thicket, don't follow matriarch
**Follower respawn:** Yes - 2 giant spiders respawn every 10 turns while matriarch lives
**Leader death effects:** No more respawns, remaining spiders fight to death

### Implementation Notes

- Combat-only NPCs, no dialog
- Respawn mechanic requires checking spider_matriarch.state each turn
- Web spray condition: `restrained` (movement blocked for 2 turns)
- Lower priority - enrichment content, not blocking any quests

---

## 2. Sporelings (npc_sporeling_1, npc_sporeling_2, npc_sporeling_3)

**Source:** fungal_depths_detailed_design.md Sections 1.2, 5.4

### Role
Pack followers of npc_spore_mother. Mirror her emotional state, bound to Spore Heart location.

### Type & Location
- Type: `fungal_creature`
- Location: `spore_heart` (Fungal Depths)
- Pack: `sporeling_pack`, role: `follower`, leader: `npc_spore_mother`
- **Range limit:** Cannot leave spore_heart - would wither if separated

### Properties

```json
{
  "health": 30,  // sporeling_3: 20 (younger)
  "pack": {
    "id": "sporeling_pack",
    "role": "follower",
    "leader": "npc_spore_mother"
  },
  "bound_to_location": "spore_heart",
  "fungal": true,
  "empathic_link": "npc_spore_mother"
}
```

### State Machine

```json
{
  "states": ["hostile", "wary", "allied", "confused", "withered"],
  "initial": "hostile",
  "transitions": {
    "hostile->wary": "Spore Mother transitions to wary",
    "wary->allied": "Spore Mother transitions to allied",
    "any->confused": "Spore Mother dies",
    "confused->withered": "10 turns after Mother's death"
  },
  "state_source": "mirror_leader"
}
```

### Reactions Required

**encounter_reactions:**
- Disposition: Mirrors Spore Mother's state
- Combat (if hostile): Spore puff (5 damage + 10 infection)
- Non-combat (if wary/allied): Emit curious/friendly spore puffs

**death_reactions:**
- Sets `has_killed_fungi` flag (detected by Myconids via spore network)
- Loot: None (small creatures)
- **Important:** Killing confused sporelings (after Mother's death) still sets flag

**empathic_communication:**
- Mirror Mother's emotions in simpler form:
  - Mother feels pain → sporelings emit distress puffs
  - Mother feels gratitude → sporelings brighten
  - Mother feels curiosity → sporelings hop closer
- Helps players understand Mother's empathic communication

### Pack Dynamics

**State mirroring:** Yes - adopt Spore Mother's state (hostile/wary/allied)
**Location mirroring:** No - bound to spore_heart, cannot leave
**Follower respawn:** No - unique individuals, not generic spawn
**Leader death effects:**
- Become `confused` state (wander aimlessly, do not attack)
- Wither after 10 turns (confused->withered->dead)
- Killing them still sets `has_killed_fungi` flag

### Behavioral Details

**Communication cascade:**
- Sporelings don't have dialog, but emit colored spores matching Mother's emotions
- Players learn to read sporelings' reactions to understand Mother's feelings
- Example: If player approaches with weapon drawn, sporelings emit fear-spores before Mother attacks

**Individual differences:**
- sporeling_1: 30 HP, bold (moves toward player first)
- sporeling_2: 30 HP, cautious (hangs back, observes)
- sporeling_3: 20 HP, younger (smaller, follows siblings)

### Implementation Notes

- No dialog_reactions needed (empathic only)
- Requires spore network integration (Myconids detect kills)
- Bound_to_location mechanic prevents following player
- Lower priority - enrichment for Spore Mother encounter

---

## Implementation Priority

**Spiders:** LOW - Combat enrichment, no quests blocked
**Sporelings:** LOW - Enhance Spore Mother encounter, not critical path

Both are well-specified and can be implemented when enrichment work begins. All necessary mechanics (pack dynamics, state mirroring, respawn, empathic communication) are documented in detailed_designs.

---

## Related

- Issue #425 - Parent issue for all placeholder NPC implementation
- beast_wilds_detailed_design.md - Full spider pack specification
- fungal_depths_detailed_design.md - Full sporeling specification
- npc_implementation_inventory.md - Complete NPC status tracking
