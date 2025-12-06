# Actor Interaction System - Conceptual Design

## Document Purpose

This document describes the **conceptual design** for actor interactions in the text adventure engine. It focuses on **what game authors can create** and **how the system supports diverse gameplay**, rather than implementation details.

**Audience**: Game authors who want to understand how to design games with rich actor interactions including combat, cooperation, environmental hazards, and social dynamics.

**Companion Documents**:
- [Actor Interaction Use Cases](actor_interactions.md) - Eight detailed scenarios this design supports
- [Game Author Guide](../user_docs/authoring_manual.md) - How to create games with this framework

---

## Design Goals

### 1. Maximize Author Capability and Player Agency

**Goal**: Authors can create any interaction between actors—combat, cooperation, rescue, trade, teaching—without engine modifications.

**How**: All interaction mechanics emerge from:
- **Properties** on actors and items (flexible, author-defined)
- **Behaviors** that respond to events (modular, stackable)
- **Existing commands** (give, approach, examine) that trigger interactions
- **Spatial system** (positioning, cover, environmental effects)

**From Use Cases**:
- **Disease transmission** (UC1): Properties define contagion, behaviors check proximity
- **Pack coordination** (UC3): Shared pack_id property, behaviors synchronize
- **NPC services** (UC4, UC6): Properties describe what NPCs offer, behaviors implement transactions
- **Environmental hazards** (UC5): Part properties define danger zones, behaviors enforce rules

### 2. Treat All Actors Uniformly

**Goal**: Player, NPCs, and even constructs are the same fundamental entity type, differing only in properties and behaviors.

**How**: The Actor entity has:
- **Core structural fields**: id, name, location, inventory (same for everyone)
- **Properties dict**: Flexible storage for stats, body characteristics, AI, skills, conditions
- **Behaviors list**: Modular event handlers (on_attack, on_receive, on_damage)

**From Use Cases**:
- **Humanoid scholar** (UC1) vs **limbless golem** (UC2) vs **eight-legged spider** (UC7): All actors, different `body.form` and `body.limbs` properties
- **Living wolves** (UC3) vs **clockwork servant** (UC8): Living uses `health`, construct uses `structural_integrity` and `power_level`
- **Player and NPCs**: Both can have conditions, skills, equipment—no special cases

### 3. Interaction ≠ Combat

**Goal**: Combat is one type of interaction among many. The system equally supports cooperation, aid, environmental challenges, and social dynamics.

**How**:
- **No combat-specific engine features**: No hardcoded damage application or death handling
- **Generic condition system**: Poison, disease, exhaustion, bleeding—all use same mechanism
- **Service framework**: NPCs can heal, teach, trade, escort using same pattern
- **Environmental effects**: Drowning, freezing, burning handled via location/part properties

**From Use Cases**:
- **UC1**: Disease spreads via proximity, cured by giving herbs—no combat
- **UC4**: Learning herb identification from NPC teacher—educational interaction
- **UC5**: Rescuing drowning sailor—cooperative emergency
- **UC6**: Escorting injured merchant—protection and aid
- **UC8**: Repairing and programming clockwork servant—technical interaction

### 4. Spatial Integration

**Goal**: Actor interactions are enhanced by the spatial positioning system, creating tactical depth and environmental storytelling.

**How**:
- **Positioning matters**: Cover behind pillars, safe zones vs danger zones
- **Environmental properties**: Parts can be breathable/toxic, covered in webs, pressurized
- **Distance and reach**: Actor interactions check if actors can reach each other
- **Posture tracking**: Taking cover, hiding, climbing affects available interactions

**From Use Cases**:
- **UC2**: Golems activate when player enters center, pillars provide cover
- **UC5**: Breath system tied to part properties (breathable: false)
- **UC7**: Spiders get combat bonuses on web-covered surfaces
- **Spatial tactics**: All combat use cases leverage positioning for strategy

### 5. Progressive and Emergent Gameplay

**Goal**: Simple interactions can grow complex naturally. Authors control depth via properties and behaviors.

**How**:
- **Start simple**: Basic health and damage properties work immediately
- **Add depth gradually**: Layer on conditions, skills, resistances as needed
- **Emergent combinations**: Properties and behaviors combine in unexpected ways
- **No arbitrary limits**: If you can imagine it, you can probably build it

**From Use Cases**:
- **UC3**: Simple "feed wolves" becomes domestication system through relationship tracking
- **UC6**: Basic "bandage merchant" expands to skill-based medicine and escort quests
- **UC7**: Individual spiders are simple, but hive mind property creates swarm behavior
- **Progression**: All use cases show how basic mechanics combine into rich scenarios

---

## Core Concepts

### Actors Are Entities with Vitals, Body, and Mind

Every actor (player, NPC, creature, construct) is defined by:

**Vital Stats** - Current state and resources:
```
health, stamina, breath, hunger, power_level, morale
```

**Body Characteristics** - Physical form and capabilities:
```
form (humanoid, quadruped, arachnid, construct)
material (flesh, stone, clockwork)
limbs (what they have)
features (teeth, claws, wings, spinnerets)
size, weight, movement types
```

**Mental/AI State** - Behavior and disposition:
```
hostile (yes/no/conditional)
disposition (friendly, neutral, desperate, grateful)
morale (courage, willingness to fight)
needs (hunger drives behavior)
goals (escort destination, guarding location)
```

**Skills and Knowledge**:
```
combat, medicine, mechanics, swimming, herbalism
knowledge of topics, locations, people
```

**Conditions** - Temporary states affecting capabilities:
```
Poison, disease, exhaustion, bleeding, paralysis, entanglement
Each with severity, progression, duration, treatment
```

### Interactions Are Events Between Actors

Interactions happen through **events** triggered by player commands or NPC behaviors:

**Direct Interactions** (actor-to-actor):
- **Attack**: Damage another actor (UC2, UC3, UC7)
- **Give**: Transfer items, which may heal, cure, or feed (UC1, UC3, UC4)
- **Escort**: Guide another actor to safety (UC5, UC6)
- **Trade**: Exchange goods and services (UC4, UC6)
- **Teach**: Transfer knowledge or skills (UC4)
- **Heal/Cure**: Restore health or remove conditions (UC1, UC4, UC6)
- **Program**: Assign tasks to automata (UC8)

**Environmental Interactions** (location/part affects actor):
- **Breathing hazards**: Drowning, toxic air, spores (UC1, UC5)
- **Temperature**: Freezing water causes hypothermia (UC5)
- **Terrain effects**: Webs slow movement, provide spider bonuses (UC7)
- **Safe zones**: Areas where certain interactions are prevented (UC2)

**Implicit Interactions** (triggered by proximity/positioning):
- **Contagion**: Disease spreads when near infected actor (UC1)
- **Detection**: Spiders sense vibrations on webs (UC7)
- **Pack awareness**: Pack members know what alpha knows (UC3)

### Properties Drive Mechanics

Authors define interaction mechanics through **properties**, not code:

**Example - Venomous Spider Bite**:
```json
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
    }
  ]
}
```

When spider bites player:
1. Apply immediate damage (8)
2. Behavior checks for `venom` property
3. Adds `spider_venom` condition to player at potency 40
4. Condition applies paralysis effect (reduces agility)

**Example - Healing Service**:
```json
"services": {
  "cure_poison": {
    "offered": true,
    "cost_type": "barter",
    "accepts": ["rare_herbs", "gems"],
    "effectiveness": 100
  }
}
```

When player seeks cure:
1. NPC behavior checks for matching `services` entry
2. Verifies player has acceptable payment
3. If accepted, removes poison conditions
4. Updates relationship (trust increases)

### Behaviors Implement Rules

**Behaviors** are Python modules that implement interaction logic by responding to events:

**Entity Behaviors** (on specific actors/items):
- `on_attack`: What happens when this actor is attacked?
- `on_receive`: What happens when given an item?
- `on_damage`: How does this actor respond to taking damage?
- `on_eat`: What effect does consuming this have?

**Handler Behaviors** (command implementations):
- `handle_attack`: Resolve attack command
- `handle_give`: Transfer items between actors
- `handle_treat`: Apply medical treatment

**Room Behaviors** (location-specific rules):
- Golem activation when player enters center (UC2)
- Spore concentration effects in basement (UC1)

### The Separation: Engine vs Behaviors

**Engine Responsibilities** (built-in, always works the same):
- Store actor properties and state
- Route commands to appropriate handlers
- Update actor locations and inventory
- Track spatial positioning (focused_on, posture)
- Provide access to game state (StateAccessor)
- **Never** apply damage, cause death, or alter stats directly

**Behavior Responsibilities** (author-defined, game-specific):
- Check preconditions (can this actor be attacked?)
- Calculate outcomes (how much damage? did cure work?)
- Apply state changes via `accessor.update()`
- Trigger cascading effects (damage → morale drop → flee)
- Implement interaction rules and consequences

**Why This Matters**: Authors can completely customize interaction mechanics by writing behaviors. The engine provides tools, not rules.

---

## Author's View: How To Create Interactions

### Step 1: Define Actor Properties

Decide what your actors can do by setting properties:

**For Combat Scenario**:
```json
{
  "id": "npc_guard",
  "name": "Guard",
  "properties": {
    "stats": {"health": 100, "max_health": 100},
    "combat": {
      "attacks": [{"name": "sword_strike", "damage": 15}],
      "armor": 5
    },
    "ai": {"hostile": true, "morale": 80}
  }
}
```

**For Healing Scenario**:
```json
{
  "id": "npc_healer",
  "name": "Healer",
  "properties": {
    "services": {
      "healing": {
        "offered": true,
        "cost_type": "coin",
        "cost_amount": 50
      }
    },
    "skills": {"medicine": 90}
  }
}
```

### Step 2: Choose or Write Behaviors

**Use Existing Behaviors** (in `behaviors/core/`):
- `combat.py`: Basic attack command
- `consumables.py`: Eating and drinking
- `manipulation.py`: Giving items between actors

**Write Custom Behaviors** for your game:
- Guard that flees when health drops below 30%
- Healer that offers better prices to grateful players
- Poison that spreads between adjacent actors

**Example Custom Behavior**:
```python
def on_attack(entity, accessor, context):
    """Guard behavior: flee when health is low."""
    current_health = entity.properties.get("stats", {}).get("health", 100)
    max_health = entity.properties.get("stats", {}).get("max_health", 100)

    if current_health < (max_health * 0.3):
        # Update morale to trigger flee behavior
        entity.properties["ai"]["morale"] = 0
        return EventResult(
            allow=True,
            message=f"The {entity.name} looks terrified and begins to flee!"
        )

    return EventResult(allow=True)
```

### Step 3: Design Environmental Context

Use the spatial system to create environmental interactions:

**Breathable Air Zones** (UC5):
```json
{
  "id": "part_tunnel_middle",
  "name": "middle section",
  "part_of": "loc_flooded_tunnel",
  "properties": {
    "breathable": false,
    "water_depth": "full"
  }
}
```

**Tactical Cover** (UC2):
```json
{
  "id": "item_pillar",
  "name": "marble pillar",
  "location": "loc_hall",
  "properties": {
    "provides_cover": true,
    "cover_effectiveness": 80,
    "destructible": true,
    "health": 100
  }
}
```

**Hazardous Surfaces** (UC7):
```json
{
  "id": "part_gallery_wall",
  "name": "north wall",
  "properties": {
    "covered_in_webs": true,
    "web_integrity": 100,
    "spider_population": 4
  }
}
```

### Step 4: Leverage Existing Commands

Many interactions work through **existing commands**:

**Healing**:
- `give antidote to scholar` → Scholar's `on_receive` behavior checks if item cures their condition

**Feeding**:
- `give meat to wolf` → Wolf's `on_receive` behavior reduces hunger, improves relationship

**Teaching**:
- `ask healer about herbs` → Healer behavior checks knowledge, provides information

**Repair**:
- `repair servant` → Servant's `on_repair` behavior checks components, applies fixes

**Environmental Navigation**:
- `approach part_tunnel_middle` → Player's position changes, breath system activates

### Step 5: Create Emergent Complexity

Combine simple properties to create rich scenarios:

**Domestication** (UC3):
1. Wolves have `hunger` property (need)
2. Meat items have `nutrition` property (satisfies need)
3. Actors have `social_bonds` property (relationship tracking)
4. Giving meat: reduces hunger, increases bond
5. Over multiple interactions: bond threshold → domestication

**Multi-Threat Rescue** (UC5):
1. Location has `breathable: false` (drowning risk)
2. Water has low temperature (hypothermia condition)
3. Sailor has `exhaustion` (can't swim well)
4. All three conditions progress simultaneously
5. Player must manage all threats to succeed

**Skill-Based Outcomes** (UC4, UC6):
1. Player has `medicine` skill
2. Treatment items have `effectiveness` value
3. Outcome = skill + item effectiveness vs condition severity
4. Better skill → better outcomes, less waste

---

## Integration with Current Architecture

### How Actor Interactions Use Existing Systems

**1. Entity-Behavior Pattern**

Actor interactions build on the existing entity-behavior architecture:

```
Player gives herb to scholar
    ↓
Engine routes to handle_give (existing handler)
    ↓
Handler transfers item to scholar's inventory
    ↓
Handler calls accessor.update(scholar, {}, verb="receive", ...)
    ↓
Engine invokes scholar's on_receive behavior
    ↓
Behavior checks if herb cures scholar's condition
    ↓
If yes: behavior returns state changes (remove condition)
    ↓
Engine applies changes, returns result to handler
    ↓
Handler sends message to player
```

**Authors already know this pattern** - actor interactions just use more sophisticated properties and behaviors.

**2. Spatial System Integration**

Actor interactions leverage the positioning system:

- **focused_on**: Which entity actor is near (enables/restricts interactions)
- **posture**: Special states (cover, concealed, climbing) that modify interactions
- **Part properties**: Environmental effects based on location within room

**Example - Cover Mechanics** (UC2):
```
Player: "take cover behind pillar"
    ↓
Spatial handler sets: player.posture = "cover", player.focused_on = pillar_id
    ↓
Later, when golem attacks:
    ↓
Combat behavior checks player.posture
    ↓
If "cover": apply pillar's cover_effectiveness to hit chance
    ↓
If attack misses, may damage pillar instead
```

**3. StateAccessor Pattern**

All actor interactions use `StateAccessor` for state changes:

```python
# Behavior applies damage
result = accessor.update(
    target_actor,
    {"properties.stats.health": new_health},
    verb="damage",
    actor_id=attacker_id
)
```

This ensures:
- State changes go through proper channels
- Nested behaviors can fire (on_damage events)
- Serialization and save/load work correctly
- No direct state manipulation bypassing validation

**4. Property-Based Design**

Actor interactions use the same **properties dict** pattern as all other entities:

```json
"properties": {
  "stats": {"health": 100},        // Like item.properties
  "combat": {"armor": 5},           // Custom to this actor type
  "conditions": {"poison": {...}},  // Temporary state
  "ai": {"hostile": true}           // Behavior control
}
```

**Authors already understand properties** - actor interactions just define new property schemas.

### What's New for Authors

**New Property Schemas**: Authors can define rich actor properties:
- `stats`, `body`, `combat`, `ai`, `conditions`, `skills`, `services`, `social_bonds`
- These are **conventions, not requirements** - use what you need

**New Behavior Events**: Additional events for actor interactions:
- `on_attack`, `on_damage`, `on_heal`, `on_condition_change`
- Still use the same behavior module pattern

**Environmental Integration**: Part properties now affect actors:
- `breathable`, `covered_in_webs`, `pressurized`, `toxic`
- Behaviors check these when actors enter/act in those areas

**NPC AI Hooks**: Optional AI system for NPC actions:
- Authors can implement "what does NPC do after player acts?"
- Based on properties like `hostile`, `morale`, `pack_id`
- Completely optional - NPCs can be purely reactive if desired

---

## Limitations and Constraints

### 1. Turn-Based Timing

**Limitation**: The engine is **request-driven**, not real-time.

**What This Means**:
- Actor interactions happen in response to player commands
- NPC actions occur "after" player actions, not simultaneously
- No persistent timers or scheduled events during player thinking

**Author Implications**:
- Urgency (drowning sailor, bleeding merchant) simulated via turn counts
- "After each action" means after each player command
- Time pressure is discrete (turns), not continuous (seconds)

**From Use Cases**:
- UC5: Sailor's breath decreases each turn player acts
- UC6: Merchant bleeds 3 health per turn until treated
- UC1: Infection severity increases by progression_rate per turn

### 2. Reach and Distance

**Limitation**: The engine doesn't have a formal distance metric.

**What This Means**:
- "Same location" is the basic proximity check
- Spatial positioning (focused_on) provides finer granularity
- No concept of "10 feet away" or movement speeds in feet/turn

**Author Implications**:
- Combat range is abstraction: "melee", "near", "far"
- Environmental effects tied to parts, not distance
- Tactical positioning via cover/focus, not precise coordinates

**Design Choice**: This matches text adventure conventions and keeps authoring simple.

### 3. Skill System is Author-Defined

**Limitation**: There's no built-in skill resolution system.

**What This Means**:
- Authors decide if skills are deterministic or involve randomness
- Authors implement skill checks in behaviors
- No standard dice rolling or target number mechanics

**Author Implications**:
- Full control over skill mechanics (good!)
- Must implement skill checks in each behavior that uses them (more work)
- Can be inconsistent across different behaviors unless careful

**Recommendation**: Create skill utility functions your behaviors share.

### 4. AI is Event-Driven, Not Goal-Oriented

**Limitation**: NPCs don't have autonomous planning or goal pursuit.

**What This Means**:
- NPCs react to events (on_attack, on_see_player)
- NPCs don't proactively pursue goals like "find food" or "patrol area"
- Complex behaviors require author-written AI in behaviors

**Author Implications**:
- Simple AI (attack when hostile, flee when hurt) is straightforward
- Complex AI (pack tactics, hive minds) requires careful behavior design
- NPCs don't act unless player action triggers them

**From Use Cases**:
- UC3: Pack coordination implemented via behaviors checking pack_id
- UC7: Hive mind via shared awareness property and coordinated behaviors
- UC2: Golems activate when player enters trigger zone (event-driven)

### 5. Death and Incapacitation Are Not Built-In

**Limitation**: The engine doesn't automatically handle actor death.

**What This Means**:
- When health reaches 0, nothing happens automatically
- Authors must implement death/incapacitation in behaviors
- Authors decide: death? unconsciousness? inert actor?

**Author Implications**:
- Consistent death handling requires shared behavior or base behavior
- Each game can handle death differently (flexible!)
- Must consider: What happens to inventory? Can corpse be examined?

**Design Choice**: This maximizes flexibility - some games may not have death at all.

### 6. No Built-In Equipment System

**Limitation**: Wearing/wielding items is not a core engine feature.

**What This Means**:
- Items in inventory, but no concept of "equipped" slots
- Authors must track equipped state in actor properties
- Authors must implement equip/unequip commands

**Author Implications**:
- Combat design sketch assumed equipped weapons - must be implemented
- Simple approach: `equipped_weapon: item_id` property
- Complex approach: Full equipment slots system

**Recommendation**: Start simple. Property `equipped_weapon` + behaviors that check it.

---

## Design Principles Applied

### From Global Design Principles

**1. Always state use cases and goals**:
- Eight use cases demonstrate diverse scenarios this design supports
- Goals explicitly listed at document start
- Features motivated by specific use case requirements

**2. Aim for simplest design**:
- Reuses existing entity-behavior architecture
- No new core engine features required
- Properties and behaviors are sufficient

**3. Maximize extensibility and user agency**:
- Authors define all mechanics via properties and behaviors
- No hardcoded interaction rules
- System supports scenarios beyond use cases

**4. Separate public API from internal design**:
- This document focuses on author experience
- Implementation details deferred to technical design
- Authors work with properties, behaviors, spatial features they already know

### From Game Engine Design Principles

**1. Engine manages state, LLM narrates**:
- All state changes (damage, conditions, relationships) managed by engine
- LLM only describes what happened
- Behaviors calculate outcomes, engine applies changes

**2. Property-driven entities**:
- All actor characteristics in flexible properties dict
- Minimal core fields (id, name, location, inventory)
- Authors define property schemas for their needs

**3. Behavior-driven extension**:
- All interaction logic in behaviors, not engine
- New interaction types via new behaviors
- Existing behaviors can be composed and stacked

**4. First-class entities**:
- Actors participate fully in narration (llm_context)
- Actors can be examined, interacted with like items
- Uniform treatment enables rich NPC personality

---

## Next Steps for Implementation

This conceptual design establishes **what** authors can create. Implementation design should address:

1. **Standard Property Schemas**: Define common property structures for stats, combat, conditions, ai, services
2. **Behavior Event Specification**: Document all actor interaction events and their context
3. **Example Behaviors**: Implement core behaviors for common patterns (attack, heal, cure, escort)
4. **State Change Patterns**: Guidelines for applying stat changes, conditions, relationship updates
5. **Skill System Utilities**: Helper functions for skill checks, randomness, difficulty scaling
6. **AI Framework**: Optional structure for NPC decision-making after player actions
7. **Testing Strategy**: How to test complex multi-actor scenarios

Each implementation decision should be evaluated against these use cases to ensure the system remains flexible and author-friendly.

---

## Summary

Actor interactions in this engine are:

**✓ Property-Driven**: Authors define capabilities via flexible properties
**✓ Behavior-Implemented**: Interaction logic lives in modular behaviors
**✓ Spatially-Integrated**: Positioning and environment affect interactions
**✓ Broadly-Scoped**: Combat, cooperation, rescue, disease, teaching all supported
**✓ Emergent**: Simple properties combine into complex scenarios
**✓ Architecturally-Consistent**: Uses existing entity-behavior patterns

**Not**:
- Combat-focused (combat is one of many interaction types)
- Hardcoded (no engine-level damage or death mechanics)
- Goal-oriented AI (NPCs are event-driven, not autonomous planners)
- Physics-based (abstract ranges and timing, not precise measurements)

This design maximizes **author capability** and **player agency** while maintaining the engine's core principle: **state management separated from narration**, with **behaviors as the unit of game logic**.
