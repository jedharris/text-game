# Actor Interaction System - Open Design Questions

This document collects all open design questions that must be answered before implementing the actor interaction system. Questions are grouped by topic and prioritized.

---

## Architecture & Integration

### 1. Where does combat/interaction logic live?
- **Core behaviors** (`behaviors/core/`) vs **game-specific behaviors**?
- Should `handle_attack` be in core, or is it game-specific?
- What about condition progression, morale checks, pack coordination?
- **Decision needed**: Which behaviors are "universal enough" to be core vs which are game customizations?

### 2. How do actor behaviors integrate with existing behavior system?
- Current system: entity behaviors fire on events (on_take, on_examine, etc.)
- New system adds: on_attack, on_damage, on_heal, on_condition_change
- **Are these new event types** added to the behavior manager?
- Or are they **special-cased** in combat handlers?
- **How do we maintain consistency** with existing behavior invocation patterns?

### 3. How does NPC action timing work?
- NPCs act "after player command completes" - but **exactly when**?
- Does **every** player command trigger NPC actions, or only certain ones?
- Do all hostile NPCs act, or just those in player's location?
- **Order of execution**: Player acts → all NPCs act → conditions progress → end turn?
- What if player command fails (e.g., can't take item) - do NPCs still act?

### 4. What constitutes a "turn" for progression?
- Conditions progress "per turn" - but what's a turn?
- Is it **every player command**? (including "look", "inventory", "examine"?)
- Only **movement/action commands**? (move, take, attack, use?)
- Do failed commands count as turns?
- **Implications**: affects balance of conditions (poison ticking while player explores)

### 5. How do we handle save/load with active conditions and NPC state?
- Conditions have duration counters that tick down
- NPCs have morale, hostility states, pack relationships
- **Do we serialize all this state** in game_state.json?
- Or **recalculate on load** based on world state?
- What happens to "in-progress" combat when player saves and reloads?

---

## Core Systems Design

### 6. How are conditions stored and managed?
**ANSWERED (Decision 10)**: Conditions stored in `actor.properties.conditions` dict, keyed by condition name. Structure: `{"poison": {"severity": 40, "damage_per_turn": 2, "duration": 10, ...}}`. Core provides utilities (`add_condition`, `remove_condition`, `progress_conditions`), but does NOT auto-progress - turn progression explicitly calls `progress_conditions()`.

**Remaining questions:**
- What utility functions exactly? Full API design needed
- Error handling when adding invalid conditions?
- Validation of condition properties?

### 7. How do multiple conditions stack?
**ANSWERED (Decision 11)**: Same condition type replaces previous instance (no stacking). Different condition types coexist independently. Getting poisoned twice replaces old poison with new poison. Can have poison AND bleeding AND burning simultaneously.

**Remaining questions:**
- None - this is fully decided
- Authors can implement custom accumulation via behaviors if desired

### 8. How are conditions treated/cured?
**ANSWERED (Decision 12)**: Items with `cures: ["poison"]` remove condition entirely. No partial curing, no potency system. Deterministic - using antidote always cures poison completely.

**Remaining questions:**
- None for core system
- Authors can implement partial curing via custom properties if desired

### 9. How is damage calculated and applied?
**ANSWERED (Decision 13)**: Basic formula is `final_damage = max(0, attack_damage - target_armor)`. Flat armor reduction. Minimum damage is 0 (armor can completely block weak attacks).

**Remaining questions:**
- **Damage types and resistances**: Core does NOT interpret damage types - authors implement via behaviors. Need to clarify recommended pattern.
- **Body material bonuses**: Are these part of armor value, or separate? How do they integrate?
- **Order of operations**: Need precise sequence for damage calculation including environmental bonuses, cover, armor
- **Cover mechanics**: Reduces damage before or after armor? (Deferred to Q16)

### 10. How does armor work?
**ANSWERED (Decision 14)**: Armor is flat damage reduction stored in `actor.properties.armor` (single numeric value). Reduces all incoming damage by armor amount. Not from equipped items (equipment system deferred).

**Remaining questions:**
- **Typed armor** (physical vs elemental): Authors can use dict if needed, but what's the recommended pattern?
- **Body material as armor source**: Does `body.material: "stone"` automatically grant armor, or is it just semantic?
- **Multiple armor sources**: If we later add equipment, how do base armor and equipment armor combine?

### 11. How are attack targets selected?
**ANSWERED (Decision 15)**: Core provides infrastructure to invoke behaviors. Authors implement all target selection and attack choice in custom `npc_take_action` behaviors. No default AI.

**Remaining questions:**
- **Core utilities to offer**: Should core provide optional helpers like `select_attack_by_range()`, `find_nearest_target()`, or leave entirely to authors?
- **Player attack selection**: When player has multiple attacks, how to choose? Command syntax? (`attack golem with sword` vs just use first attack?)

### 12. How does morale work mechanically?
**PARTIALLY ANSWERED**: Use cases show morale system (`ai.morale`, `ai.flee_threshold`). Morale is game-specific strategy, not core infrastructure.

**Remaining questions:**
- **Core support needed**: Does core provide any morale utilities, or purely author implementation?
- **Recommended patterns**: What triggers morale changes? Damage taken, allies defeated, intimidation?
- **Calculation formula**: Linear reduction (morale -= damage/2) or threshold-based?
- **Recovery**: Does morale recover over time, or only via explicit events?
- **Flee behavior**: When morale < flee_threshold, what exactly happens? Authors implement in `npc_take_action`?
- **Should morale be in Phase 1**: Or defer to later phase as "advanced AI"?

### 13. How does pack coordination work?
**PARTIALLY ANSWERED**: Use cases show pack system (`ai.pack_id`, `ai.pack_role`, `ai.follows_alpha`). Core/game boundary unclear.

**Remaining questions:**
- **Core utilities needed**: Should core provide `get_pack_members()`, `alert_pack()` helpers, or entirely author implementation?
- **Communication mechanism**: How does alpha's hostility propagate to followers? Instant broadcast? Does core handle this, or behaviors?
- **Range limits**: Can pack coordination work across entire world, or only same location?
- **Action coordination**: Do pack members act in same turn progression (in random/deterministic order), or is there special pack sequencing?
- **Alpha death**: What happens to pack when alpha dies? Core behavior, or author-defined?
- **Should pack coordination be in Phase 1**: Or defer as "advanced AI"?

---

## Environmental & Spatial Integration

### 14. How do environmental properties affect actors?
**FULLY DECIDED (Decisions 16, 26)**: Environmental hazards checked automatically every turn. Constants configurable via metadata. Applied to all actors everywhere.

**Summary:**
- Hazards (`breathable: false`, `hazard_condition`) checked via `apply_environmental_effects()`
- Applied to all actors everywhere during turn progression phase
- Uses configurable constants from game metadata (Decision 26)
- `hazard_condition` adds/replaces condition using same logic as attacks
- Turn sequence: player acts → NPCs act → environmental effects → conditions progress

**Implementation details deferred to detailed design phase.**

### 15. How are environmental bonuses applied?
**FULLY DECIDED (Decision 27)**: Environmental bonuses are properties only. Authors query and apply. Flat bonuses recommended.

**Summary:**
- Bonuses (`web_bonus_attacks`) are properties queried by behaviors
- Core does NOT automatically apply bonuses
- Recommend flat bonuses for simplicity (+20 damage, not +20%)
- Authors can use any semantic meaning they choose
- Multiple bonuses work fine - different property names

**Implementation pattern documented in Decision 27.**

### 16. How does cover work mechanically?
**FULLY DECIDED (Decision 28)**: Cover is entirely author-implemented. Percentage reduction recommended. Pillar damage optional.

**Summary:**
- Cover via `posture: "cover"` and `focused_on: pillar_id` properties
- Authors implement cover reduction in attack behaviors
- Recommend `cover_value: 80` = 80% damage reduction
- Pillar damage is optional pattern (authors choose)
- Cover commands are game-specific (e.g., `hide behind pillar`)

**Implementation patterns documented in Decision 28.**

### 17. How does breath/oxygen tracking work?
**FULLY DECIDED (Decisions 17, 26)**: Breath in properties, constants in metadata. Instant recovery by default.

**Summary:**
- Breath stored in `properties.breath` and `properties.max_breath`
- Depletion rate configurable via metadata (default: 10 per turn)
- Asphyxiation damage configurable via metadata (default: 5 per turn)
- Recovery mode configurable: "instant" (default) or "gradual"
- Actors without breath property don't need air

**Configuration via `environmental_constants` metadata (Decision 26).**

---

## Combat & Interaction Mechanics

### 18. What combat commands exist?
- Obviously `attack <target>`
- What about `defend`, `dodge`, `block`?
- **Cover command**: `hide behind <object>` or `take cover`?
- **Intimidate**: separate command or part of social interaction?
- **Flee**: explicit flee command, or just move away?

### 19. How is "range" modeled?
- Attacks have `range: "melee"`, `"near"`, `"area"`
- **What determines if attacker can use attack?**
- Same location = all ranges work?
- `focused_on` target = melee works?
- **How does spatial distance map to range categories?**

### 20. How do area attacks work?
- Boss uses `flame_breath` with `range: "area"`
- **Who is affected**: everyone in same location? Same part?
- **Cover interaction**: does cover protect from area attacks?
- **Friendly fire**: can area attacks damage allies?
- **Damage distribution**: same damage to all targets, or split?

### 21. What happens when actor health reaches 0?
- **Immediate death**? Actor removed from game?
- **Unconscious state**? Actor present but incapacitated?
- **Behavior-driven**: on_death behavior determines outcome?
- **Different for player**: player gets "you died" game over, NPCs just disappear?

### 22. How do immunities and resistances work?
- Golem has `immunities: ["poison", "disease"]`
- Spider tries to poison golem - **what happens?**
- **Condition not applied at all**?
- **Applied but has no effect**?
- **Reduced severity** (immunity = 100% resistance)?
- **Resistances**: `resistances: {"fire": 30}` means 30% damage reduction from fire?

### 23. How do weaknesses work?
- Boss has `weaknesses: {"ice": 200}`
- **Damage multiplier**: ice damage × 2.0?
- **Condition severity multiplier**: ice conditions at 200% severity?
- **Both**: both damage and conditions enhanced?
- **Elemental typing**: how do we determine if attack is "ice type"?

---

## NPC Behavior & AI

### 24. When and how do NPCs act?
- **Trigger**: after player command? After every command or specific types?
- **Selection**: which NPCs act? All hostile? All in location? All in game?
- **Order**: do NPCs act in sequence or simultaneously?
- **Targeting**: how does NPC decide which target to attack?
- **Movement**: can NPCs move between locations, or only act in current location?

### 25. How do activation triggers work?
- Golem has `activation_trigger: "player_enters_center"`
- **Who checks**: does movement handler check for triggers?
- **Or behavior**: does golem's on_observe behavior check player position?
- **Generic system**: can any NPC have activation triggers?
- **Deactivation**: how do triggers reset when player leaves?

### 26. How does fleeing work?
- Guard has `morale < flee_threshold` and decides to flee
- **Where do they flee to**: specific location? Just leave current location?
- **Can player pursue**: does fleeing NPC leave game entirely?
- **Flee properties**: `flee_destination` property on NPC?
- **Behavior**: is fleeing a special behavior, or just forced movement?

### 27. How does pack behavior scale?
- Pack of 3 wolves vs pack of 20 wolves
- **Performance**: checking all pack members every turn?
- **Range limits**: only pack members in same location coordinate?
- **Multiple packs**: can multiple packs exist, or one pack per game?

---

## Services & Non-Combat Interactions

### 28. How do NPC services work?
- Healer has `services: {"cure_poison": {"accepts": ["rare_herbs"], ...}}`
- **Triggering service**: player gives item, service fires automatically?
- **Or request**: player must `ask healer about cure`?
- **Acceptance logic**: does healer's on_receive check services?
- **Cost validation**: how to check if player has right items/gold?

### 29. How is "knowledge" modeled?
- Binary `knows: ["herbalism", "combat_basics"]` array?
- Or numeric `knowledge: {"herbalism": 60}` levels?
- **Teaching**: what changes when NPC teaches player?
- **Skill checks**: if binary, how do we handle difficulty?

### 30. How do relationships work?
- `relationships: {"player": {"trust": 50, "gratitude": 5}}`
- **Initialization**: start at 0, or need explicit setup?
- **Modification**: when and how do these change?
- **Effects**: what do trust/gratitude actually do mechanically?
- **Persistence**: saved with actor, or separate relationship tracking?

---

## Technical Implementation

### 31. Do we need randomness? If so, how?
- Evaluation recommends deterministic outcomes
- But some use cases mention "rolls" - are these just prose?
- **If deterministic**: how to create variety and uncertainty?
- **If random**: need seeded RNG for save/load consistency

### 32. How do we handle turn counters for conditions?
- Condition has `duration: 10` turns remaining
- **Who decrements**: engine after each turn?
- **Where**: condition progression behavior?
- **Global turn counter**: does game state track current turn number?

### 33. How are "after turn" effects ordered?
- Player acts → NPCs act → conditions progress → ?
- **Specific order matters**: poison might kill before NPC attacks
- **Or simultaneous**: all effects apply, then check for death?
- **Event loop**: explicit turn processing function?

### 34. How do we test these systems?
- Conditions, morale, pack coordination - complex interactions
- **Unit tests**: test condition progression in isolation?
- **Integration tests**: full combat scenarios?
- **Test fixtures**: reusable NPC/item definitions for tests?
- **TDD approach**: write tests before implementation?

---

## Scope & Phasing

### 35. What's the Minimal Viable Combat System?
- Simplest implementation that's useful
- **Phase 1 candidates**:
  - Basic health and damage
  - Single attack per actor
  - Simple conditions (poison only?)
  - No morale, no packs, no services?
- **Or include morale/packs from start** since they're relatively simple?

### 36. How much to implement in Phase 1?
- From evaluation: conditions, attacks, body characteristics, environmental effects
- **All at once**: bigger phase, longer before testing
- **Incrementally**: conditions first, then attacks, then environment
- **Which first**: what has least dependencies?

### 37. How do we maintain backward compatibility?
- Existing games have actors without combat properties
- **Do we require migration**: force all actors to have health/attacks?
- **Or graceful degradation**: actors without combat properties just can't fight?
- **Default values**: empty `attacks: []`, `health: 100`?

---

## Priority Rankings

### Critical (Must answer before any implementation):
- Q3: NPC action timing
- Q4: Turn definition
- Q6: Condition storage
- Q9: Damage calculation
- Q24: When NPCs act
- Q35: MVP scope

### Important (Needed for Phase 1):
- Q7: Condition stacking
- Q8: Condition treatment
- Q11: Attack selection
- Q14: Environmental checks
- Q18: Combat commands
- Q21: Death handling

### Can Defer (Later phases):
- Q12: Morale mechanics (if not in Phase 1)
- Q13: Pack coordination (if not in Phase 1)
- Q23: Weakness system (advanced feature)
- Q28: NPC services (Phase 2)
- Q30: Relationships (Phase 2)

### Design Choices (Not critical path):
- Q10: Armor mechanics (flat vs percentage)
- Q15: Environmental bonus types
- Q16: Cover mechanics details
- Q31: Randomness (already decided: deterministic)

---

## Next Steps

Once these questions are answered, we can:
1. Write formal design document with decisions
2. Define property schemas based on decisions
3. Create implementation phasing plan
4. Begin TDD implementation of Phase 1
