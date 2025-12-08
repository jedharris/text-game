# Feature Evaluation: Actor Interaction System

I've reviewed both documents and analyzed them against your three criteria: gameplay contribution, authoring complexity, and implementation burden. Here's my detailed assessment:

## Overall Assessment

The conceptual design is **extremely well thought out** and aligns beautifully with your existing architecture. Most features have high gameplay value and leverage existing systems effectively. However, some features add significant authoring complexity for marginal gameplay gains.

---

## Feature-by-Feature Evaluation

### ✅ **HIGHLY RECOMMENDED** (High gameplay, Low-moderate authoring, Reasonable implementation)

#### 1. **Condition System** (UC1, UC4, UC5, UC6, UC7)
- **Gameplay Contribution:** ⭐⭐⭐⭐⭐ Essential for rich interactions beyond combat
- **Authoring Complexity:** ⭐⭐ Simple - just add conditions to properties dict
- **Implementation Burden:** ⭐⭐ Moderate - needs progression mechanism and treatment system

**Verdict:** MUST HAVE. Enables disease, poison, exhaustion, bleeding, hypothermia, paralysis, entanglement. Reuses existing properties pattern. Just needs turn-based progression and behavior hooks for treatment.

```python
"conditions": {
  "poison": {"severity": 40, "damage_per_turn": 2, "duration": 20}
}
```

#### 2. **Multiple Attack Types per Actor** (UC2, UC3, UC7)
- **Gameplay Contribution:** ⭐⭐⭐⭐⭐ Creates tactical depth and variety
- **Authoring Complexity:** ⭐⭐ Just list attacks in properties
- **Implementation Burden:** ⭐⭐ Moderate - behaviors select which attack to use

**Verdict:** MUST HAVE. Makes different enemies feel distinct. Wolves bite/tackle, spiders bite/spray webs, golems charge/slam. Simple property-driven approach.

```python
"combat.attacks": [
  {"name": "bite", "damage": 15, "type": "piercing"},
  {"name": "tackle", "damage": 8, "effect": "knockdown"}
]
```

#### 3. **Body Characteristics** (All UCs)
- **Gameplay Contribution:** ⭐⭐⭐⭐ Rich flavor and enables body-specific mechanics
- **Authoring Complexity:** ⭐⭐ Define once per actor type
- **Implementation Burden:** ⭐⭐ Moderate - behaviors check body properties for restrictions

**Verdict:** HIGHLY RECOMMENDED. Humanoid vs quadruped vs arachnid vs construct. Enables material-based resistance (stone golems immune to poison), limb requirements (can't serve food without arms), movement types (spiders climb webs).

#### 4. **Environmental Properties Affecting Actors** (UC1, UC2, UC5, UC7)
- **Gameplay Contribution:** ⭐⭐⭐⭐⭐ Massive - creates environmental puzzles and tactics
- **Authoring Complexity:** ⭐⭐ Add properties to location parts
- **Implementation Burden:** ⭐⭐ Already have spatial system! Just need behaviors to check part properties

**Verdict:** MUST HAVE. Leverages existing spatial system perfectly. Breathable/non-breathable parts (UC5), web-covered surfaces giving spider bonuses (UC7), spore concentrations (UC1), cover effectiveness (UC2).

#### 5. **NPC Services Framework** (UC1, UC4, UC6)
- **Gameplay Contribution:** ⭐⭐⭐⭐ Enables non-combat gameplay: healing, teaching, trading, escort
- **Authoring Complexity:** ⭐⭐⭐ Moderate - need to define service properties and costs
- **Implementation Burden:** ⭐⭐⭐ Moderate - need generic service resolution pattern

**Verdict:** HIGHLY RECOMMENDED. Opens up entire categories of gameplay beyond combat. Healer cures poison for barter (UC4), merchant trades (UC6), scholar teaches herb ID (UC1).

```python
"services": {
  "cure_poison": {"offered": true, "cost_type": "barter", "accepts": ["rare_herbs"]}
}
```

---

### ⚠️ **USE WITH CAUTION** (Good gameplay, but higher complexity or burden)

#### 6. **Pack/Hive Mind Coordination** (UC3, UC7)
- **Gameplay Contribution:** ⭐⭐⭐⭐ Creates memorable encounters
- **Authoring Complexity:** ⭐⭐⭐ Moderate - shared IDs and coordination rules
- **Implementation Burden:** ⭐⭐⭐⭐ High - need shared awareness and coordinated AI

**Verdict:** INCLUDE BUT SIMPLIFY. Start with simple pack coordination (shared pack_id, followers copy alpha behavior). Defer full hive mind (shared awareness, tactical coordination) to later. The simple version gives 80% of the gameplay value for 20% of the complexity.

**Simplified approach:**
```python
# Simple: Followers just check what alpha is doing
if pack_member.ai.get("follows_alpha"):
    alpha = accessor.get_actor(pack_member.ai["follows_alpha"])
    if alpha.ai["hostile"]:
        pack_member.ai["hostile"] = True
```

#### 7. **Morale/Fear System** (UC2, UC3, UC6)
- **Gameplay Contribution:** ⭐⭐⭐⭐ Makes NPCs feel alive, creates dynamic combat
- **Authoring Complexity:** ⭐⭐⭐ Moderate - thresholds and flee conditions
- **Implementation Burden:** ⭐⭐⭐ Moderate - behaviors check morale, update on damage

**Verdict:** RECOMMENDED. Wolves flee when injured, guards flee at low health, intimidation affects morale. Adds realism and non-lethal solutions. Implementation is straightforward - just check morale in on_damage behaviors.

#### 8. **Progressive Relationships** (UC3, UC6)
- **Gameplay Contribution:** ⭐⭐⭐⭐ Enables domestication, reputation, long-term consequences
- **Authoring Complexity:** ⭐⭐⭐ Need to track bonds and thresholds
- **Implementation Burden:** ⭐⭐⭐ Moderate - needs persistence and incremental updates

**Verdict:** RECOMMENDED. Feeding wolves over time domesticates them (UC3), helping merchant creates ally (UC6). Very engaging gameplay. Store in `social_bonds` dict per actor pair.

---

### ❌ **DEFER OR SIMPLIFY** (Lower value or excessive complexity)

#### 9. **Detailed Skill System** (UC4, UC6)
- **Gameplay Contribution:** ⭐⭐⭐ Good for depth, but can be simplified
- **Authoring Complexity:** ⭐⭐⭐⭐ High - every skill check needs tuning
- **Implementation Burden:** ⭐⭐⭐⭐ High - need skill resolution, difficulty scaling, randomness

**Verdict:** SIMPLIFY SIGNIFICANTLY. The documents show medicine skill affecting treatment effectiveness, mechanics skill affecting repairs, swimming affecting breath consumption. This creates tuning burden.

**Recommendation:** Start with boolean skills (has_medicine: true/false) or very coarse levels (medicine: "novice"|"expert"). Defer detailed numerical skills until proven necessary.

#### 10. **Multiple Vital Stats** (UC5, UC6, UC8)
- **Gameplay Contribution:** ⭐⭐⭐ Adds depth but also bookkeeping
- **Authoring Complexity:** ⭐⭐⭐⭐ Authors must track health, stamina, breath, hunger, power
- **Implementation Burden:** ⭐⭐⭐ Moderate - each stat needs progression and effects

**Verdict:** START MINIMAL, ADD AS NEEDED. Health alone enables most use cases. Add breath only for drowning scenarios (UC5), power only for constructs (UC8), hunger only if food matters to gameplay.

**Don't implement all vitals upfront** - this creates authoring overhead for every actor. Add vitals incrementally as specific use cases demand them.

#### 11. **Equipment System** (UC2, combat generally)
- **Gameplay Contribution:** ⭐⭐⭐⭐ Traditional RPG mechanic
- **Authoring Complexity:** ⭐⭐⭐⭐ Slots, restrictions, equip/unequip commands
- **Implementation Burden:** ⭐⭐⭐⭐ High - new commands, slot management, stat bonuses

**Verdict:** DEFER. The design correctly notes (line 615) this isn't built-in. Start with simple `equipped_weapon: item_id` property. Only build full equipment system if gameplay clearly demands it. Most use cases work fine without it.

#### 12. **Detailed Component Damage** (UC8)
- **Gameplay Contribution:** ⭐⭐ Niche - only matters for construct repair gameplay
- **Authoring Complexity:** ⭐⭐⭐⭐ High - list every component, model damage
- **Implementation Burden:** ⭐⭐⭐ Moderate but very specific

**Verdict:** DEFER OR SIMPLIFY. UC8 shows damaged speech module and arm servo separately. This is high granularity for one use case (clockwork servant repair). If you want construct repair gameplay, start with binary (working/broken) rather than per-component damage.

#### 13. **Task Programming for NPCs** (UC8)
- **Gameplay Contribution:** ⭐⭐⭐ Interesting for automation gameplay
- **Authoring Complexity:** ⭐⭐⭐⭐⭐ Very high - define tasks, requirements, restrictions
- **Implementation Burden:** ⭐⭐⭐⭐ High - runtime NPC programming system

**Verdict:** DEFER. UC8's programmable clockwork servant is cool but very specific. Requires defining `available_tasks`, `task_restrictions`, programming interface, task execution. Only implement if servant automation is core to your game vision.

---

## Cross-Cutting Concerns

### ⚠️ **Randomness and Skill Checks**
The documents repeatedly show skill checks, rolls against difficulty, chance-based outcomes. But **no randomness system is designed**.

**Issue:** Lines like "roll against player's immunity and resistances.disease" (UC1:92) appear throughout, but there's no specification of:
- Dice mechanics (d20? 2d6? percentile?)
- Target numbers
- Success degrees
- Randomness seed for save/load

**Recommendation:** Either commit to deterministic outcomes or design the randomness system explicitly. Don't leave it implicit in use cases.

### ⚠️ **Turn-Based Progression**
The design notes it's turn-based (lines 520-537) but doesn't specify:
- What constitutes a turn?
- When do conditions progress?
- When do NPCs act?
- How do "per turn" effects fire?

**Recommendation:** Specify "after each player command" or similar. Current ambiguity will cause implementation confusion.

### ✅ **Reuse of Existing Architecture**
**EXCELLENT:** The design correctly leverages:
- Entity-behavior pattern (lines 412-435)
- Properties dict (lines 482-494)
- StateAccessor for changes (lines 462-480)
- Spatial system for positioning (lines 439-460)

This massively reduces implementation burden and keeps authoring consistent.

---

## Priority Recommendations

### Phase 1: Core Combat (Minimal Viable Actor Interactions)
Implement ONLY:
1. **Conditions** - poison, disease, bleeding (property-driven)
2. **Multiple attacks** - array of attack definitions
3. **Body characteristics** - form, material, features (for restrictions)
4. **Environmental effects** - part properties affect actors
5. **Basic health/damage** - single vital stat to start

**Authoring burden:** LOW. Just add properties to actors and locations.
**Gameplay value:** HIGH. Enables UC1, UC2, UC3, UC7 in simplified form.
**Implementation:** Moderate. Extends existing behavior system.

### Phase 2: Non-Combat Interactions
Add:
6. **NPC services** - healing, teaching, trading framework
7. **Morale system** - flee when injured
8. **Simple relationships** - trust/gratitude tracking

**Authoring burden:** MODERATE. Services need cost definitions.
**Gameplay value:** HIGH. Enables UC4, UC5, UC6.
**Implementation:** Moderate. Generic service resolution pattern.

### Phase 3: Advanced Coordination (Optional)
Only if gameplay demands it:
9. **Pack coordination** (simplified version)
10. **Additional vital stats** (breath, hunger, stamina) - only as needed

### Defer Indefinitely Unless Proven Necessary:
- Detailed skill system (use boolean or coarse levels)
- Full equipment system (use simple equipped_weapon property)
- Component-level damage (use overall integrity)
- Task programming (too specific to UC8)

---

## Summary

**Best Features** (must include):
- Condition system
- Multiple attack types
- Body characteristics
- Environmental properties
- NPC services

**Good Features** (include with simplification):
- Pack coordination (simplified)
- Morale/fear
- Progressive relationships

**Avoid/Defer**:
- Detailed skill checks
- Multiple vital stats (add incrementally)
- Equipment system (start minimal)
- Component damage (too granular)
- NPC programming (too specific)

**Critical Missing Pieces:**
- Randomness system design (if using random outcomes)
- Turn progression specification (when do "per turn" effects fire?)
- NPC action timing (when do NPCs act?)

The design is **architecturally sound** and reuses existing systems well. The main risk is **scope creep** - trying to implement every feature from the use cases will create excessive authoring burden. Start with the core features that work property-driven (conditions, attacks, body, environment) and add coordination features incrementally based on actual gameplay needs.
