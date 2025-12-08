# Design Review: Actor Interaction Conceptual Design v2

**Review Date:** 2025-12-06
**Document Reviewed:** `actor_interaction_conceptual_design_v2.md`
**Reviewer:** Claude Code
**Purpose:** Thorough review for consistency, completeness, clarity, and coverage of simplified use cases

---

## ✅ STRENGTHS

### 1. **Excellent Use Case Coverage**
The design handles all 8 simplified use cases gracefully:
- UC1 (Infected Scholar): ✅ Conditions, contagion, environmental effects, cures
- UC2 (Guardian Golems): ✅ Multiple attacks, cover, immunities, activation
- UC3 (Wolf Pack): ✅ Pack coordination, morale, feeding, relationships
- UC4 (Healer/Garden): ✅ Services, knowledge, treatment, relationships
- UC5 (Drowning Sailor): ✅ Breath tracking, environmental hazards, rescue
- UC6 (Injured Merchant): ✅ Conditions, treatment, escort, trading
- UC7 (Spider Swarm): ✅ Pack behavior, venom, entanglement, web effects
- UC8 (Broken Statue): ✅ Construct repair, activation, knowledge queries

### 2. **Well-Motivated Features**
Every feature is clearly tied to specific use cases and goals. No speculative additions.

### 3. **Strong Consistency with Existing Architecture**
- Reuses entity-behavior pattern
- Reuses StateAccessor
- Reuses spatial system
- Reuses properties dict pattern

### 4. **Good Separation of Public API vs Internal Design**
- Clear property schemas (public API)
- Behavior events well-defined
- Implementation details appropriately deferred

### 5. **Excellent Progressive Complexity**
The phasing approach (Phase 1: Core, Phase 2: Social, Phase 3: Advanced) allows authors to adopt incrementally.

---

## ⚠️ ISSUES FOUND

### **CRITICAL ISSUES**

#### 1. **Inconsistency: `treatable_by` vs `cures`/`treats`** (Multiple locations)

**Problem:** The document uses THREE different property names for the same concept:
- Line 143: Condition has `"treatable_by": ["cutting_tool"]`
- Line 665: Item has `"treats": ["bleeding"]`
- Line 72: Item has `"cures": ["fungal_infection"]`

**Impact:** Authors won't know which to use. Implementation will be inconsistent.

**Location in v2:**
- Line 143 (example condition)
- Lines 664-668 (UC6 bandages)
- Lines 72-75 (UC1 herb)
- Line 870 (schema mentions `treatable_by`)

**Recommendation:** Choose ONE convention:
- **Option A:** Conditions have `treatable_by: [types]`, items have `treats: [condition_names]` AND `cure_amount: number`
- **Option B:** Simpler - just items have `cures: [condition_names]` and `cure_amount: number`, no condition property needed

I recommend **Option B** for simplicity. Remove `treatable_by` from conditions entirely.

**RESOLUTION:** ✅ Accepted - remove `treatable_by` from conditions, use only `cures` on items.

---

#### 2. **Missing Turn Progression Detail: Order of Operations** (Lines 563-600)

**Problem:** The turn sequence (lines 563-600) lists phases but doesn't specify critical ordering details:
- Do conditions tick BEFORE or AFTER environmental effects?
- If breath drops to 0 in environmental phase, does drowning damage apply in the SAME turn?
- Do death checks happen after each phase or only at the end?

**Impact:** Implementation ambiguity. Different behaviors might expect different orderings.

**Example conflict:**
```
Scenario: Player has 5 breath, in non-breathable area
- Environmental phase: breath becomes -5
- Condition phase: Does drowning damage apply THIS turn or NEXT turn?
```

**Recommendation:** Add explicit sub-ordering:
```
3. Environmental Effects Phase:
   - Update breath/temperature for each actor
   - Apply NEW conditions from environment (e.g., hypothermia)
   - Do NOT apply damage yet

4. Condition Progression Phase:
   - Apply damage_per_turn for ALL conditions (including just-added ones)
   - Decrement durations
   - Remove expired conditions

5. Death/Incapacitation Check:
   - Check all actors for health <= 0
   - Invoke on_death behaviors
```

This means environmental conditions START dealing damage the SAME turn they're applied, creating urgency.

**RESOLUTION:** ✅ Accepted - add explicit phase sub-ordering as recommended.

---

#### 3. **Undefined: What IS "touch range"?** (Lines 89, 537)

**Problem:** The document uses spatial terms without definition:
- Line 89: `contagious_range: "touch"`
- Line 537: "Player is focused_on scholar (touch range)"

But what defines "touch range"? The spatial system uses:
- Same location
- `focused_on` entity
- `posture`

**Question:** Does "touch range" mean:
- `focused_on` the entity? (most likely)
- Same location part?
- Within the same room but any part?

**Impact:** Implementation confusion. Multiple interpretations possible.

**Initial Recommendation:** Define "touch range" as `focused_on` the entity.

**ISSUE RAISED:** User points out that `focused_on` alone is insufficient. Example: After "examine chandelier", the actor is focused on the chandelier but NOT in touch range (unless standing on something tall). Additional criteria needed beyond just `focused_on`.

**RESOLUTION:** ⚠️ **NEEDS FURTHER DESIGN WORK**

Possible approaches to consider:
1. **Reachability check:** Touch range requires both `focused_on` AND entity must be reachable (not too high/far)
2. **Entity properties:** Some entities have `touchable: false` (like chandelier) vs `touchable: true` (like person)
3. **Posture-based:** Touch range depends on actor's posture and target's location/properties
4. **Spatial part adjacency:** Touch range requires being in same or adjacent spatial part

This needs to be resolved before implementation, as it affects:
- Contagion spread mechanics (UC1)
- Attack range validation
- Item interaction (take/use/give)
- Service provision range

**ACTION REQUIRED:** Design team should specify exact criteria for "touch range" determination.

---

### **MODERATE ISSUES**

#### 4. **Property Schema Duplication** (Lines 1464-1522 vs earlier examples)

**Problem:** The final schema (lines 1464-1522) doesn't match earlier examples:

**Mismatch 1 - Armor:**
- Line 207: `"armor": 5` (simple number)
- Line 1483: `"armor": number` (schema matches)
- Line 153 (UC2): `"armor": 20` ✅ consistent
- But no explanation of how armor works!

**Mismatch 2 - Pack structure:**
- Lines 1500-1501: Schema shows both `pack_id` and `follows_alpha` under `ai`
- Lines 266-268 (UC3): Shows `pack_role` under `ai` but schema omits this
- The schema should include `pack_role: "alpha|follower"`

**Mismatch 3 - Attack types:**
- Line 890: `"type": "piercing"` on attacks
- Schema (line 1476-1481) shows `"type": string (optional)` ✅
- But document NEVER explains what attack types do. Are they just descriptive? Do they interact with armor types?

**Recommendation:**
- Add `pack_role` to schema
- Add brief note: "Armor reduces all incoming attack damage by flat amount. Attack `type` is only descriptive in Phase 1 (can be used for armor type matching in future phases)"

**RESOLUTION:** ✅ Accepted - add `pack_role` to schema and note about armor/attack types.

---

#### 5. **Unclear: When Do Behaviors Check Early and Return?** (Lines 1262-1279)

**Problem:** The document says NPCs should "check early and return" for performance, but doesn't specify WHAT to check.

Line 1266: "Check if NPC should do something"
Line 1272: "Check if player in same room (cheap early return)"

**Question:** Should ALL behaviors do this? What's the canonical check order?

**Impact:** Authors may write inefficient behaviors or miss important optimizations.

**Initial Recommendation:** Add canonical check order pattern to "NPC Action" section.

**RESOLUTION:** ✅ **Rejected - No premature optimization**

We cannot specify what NPCs must check - this is up to authors based on their game's needs. If a game becomes too slow, authors will fix it. If this becomes a chronic problem across multiple games, we can analyze those games and determine how to solve it systematically.

The document should keep the general guidance about "check early and return" but not prescribe specific patterns. Authors know their game logic best.

---

#### 6. **Missing: Resistance Calculation Formula** (Lines 149-156, 728-729)

**Problem:** Document shows resistance percentages but doesn't specify exact formula.

Line 728: `Actual severity increase: 15 * 0.7 = 10.5 → 11`

**Questions:**
- Always round up? Round to nearest?
- Do resistances apply to `damage_per_turn` or just initial severity?
- Can resistance reduce severity increase to 0?

**Recommendation:** Add to "Conditions" section:
```
Resistance Calculation:
- resistance_value is percentage (0-100)
- Actual damage/severity = base_value * (1 - resistance_value/100)
- Round up (ceiling) for severity, round standard for damage
- Minimum 0 (resistance can negate entirely if 100%)
```

**RESOLUTION:** ✅ Accepted - add resistance calculation formula as recommended.

---

#### 7. **Ambiguous: Death Behavior Contract** (Lines 1351-1363)

**Problem:** Lines 1351-1363 say "authors decide" what happens at death, but don't specify:
- Who removes the actor from the location?
- Who handles inventory dropping?
- Can multiple behaviors handle `on_death`? What order?

**Impact:** Inconsistent death handling across different games.

**Initial Recommendation:** Add standard behavior template for death handling.

**RESOLUTION:** ✅ **Rejected - Too prescriptive, premature standardization**

Different games will want to handle death very differently. We have no experience yet to know what a "standard" approach should be. This is better handled in a library (lower cost and risk to change) rather than in the core design.

The design should remain flexible: document that `on_death` behavior is invoked when health <= 0, and authors implement whatever makes sense for their game (drop inventory, create corpse, trigger game over, etc.).

---

### **MINOR ISSUES**

#### 8. **Example Inconsistency: Wolf Disposition** (Lines 755, 776)

**Problem:**
- Line 755: Wolf has `"relationships": {}` (empty)
- Line 776: Text says "increment relationships.player.gratitude = 1"

This is actually fine (creates key on first increment), but might confuse authors.

**Recommendation:** Add note:
```
Relationship keys are created dynamically. Empty {} means no relationships yet.
```

**RESOLUTION:** ✅ Accepted - add clarifying note about dynamic relationship key creation.

---

#### 9. **Terminology Inconsistency: "Effectiveness" vs "Cure Amount"** (Lines 384, 681)

**Problem:**
- Line 384 (healer service): `"effectiveness": 100`
- Line 665 (bandages): `"cure_amount": 60`

Are these the same concept? Different?

**Recommendation:** Use ONE term. Suggest `cure_amount` or `restore_amount` consistently.

**RESOLUTION:** ✅ Accepted - standardize on `cure_amount` throughout.

---

#### 10. **Missing: What Happens When Service Payment Doesn't Match?** (Lines 956-975)

UC4 says: `"amount_required": 50`

But what if player gives 30 gold? 70 gold?
- Reject the transaction?
- Partial service?
- Give change?

**Initial Recommendation:** Specify standard service payment matching rules.

**RESOLUTION:** ✅ **Rejected - Taking on too much, leave to authors**

This level of detail about payment matching, change-making, and partial services is game-specific logic. Different games will handle this differently based on their economic systems and narrative style. Leave this up to game authors to implement in their service behaviors.

The design should specify that services can accept items/currency and provide effects, but the exact matching logic is author-defined.

---

#### 11. **Unclear: Pack Coordination Timing** (Lines 549-561, 1027-1032)

**Problem:** "After turn, NPC action phase" but when EXACTLY do pack members sync?

Is it:
- A) Each pack member's individual `npc_take_action` checks alpha
- B) A separate "pack coordination" phase before NPC actions
- C) Only when alpha's state changes

**Initial Recommendation:** Clarify that followers copy `alpha.hostile` in NPC action phase.

**ISSUE RAISED:** The property name `hostile` is too narrow and combat-focused. The pack coordination mechanism should work for allies defending the player, not just enemies. Example: A pack could be friendly, with followers copying the alpha's friendly/protective behavior.

**RESOLUTION:** ⚠️ **NEEDS DESIGN CLARIFICATION - What Properties Do Pack Members Copy?**

### Context: The Pack Coordination Use Cases

The design envisions pack coordination supporting multiple scenarios:

**Hostile Packs (UC3 - Wolf Pack, UC7 - Spider Swarm):**
- Alpha wolf becomes hostile → pack members become hostile
- Alpha wolf flees when injured → pack members flee
- Broodmother attacks → other spiders coordinate attacks

**Friendly/Allied Packs:**
- Guard captain decides to help player → squad follows suit
- Escort leader changes destination → convoy follows
- Pack alpha becomes domesticated → other pack members also friendly

**Current Design Issue:**

The document shows followers copying `alpha.ai.hostile`, but this is:
1. **Too narrow:** Only handles hostile/non-hostile binary
2. **Combat-focused:** Doesn't cover friendly pack behaviors
3. **Inflexible:** Doesn't handle state like "fleeing", "patrolling", "guarding", "escorting"

### Design Questions That Need Resolution:

**Question 1: What gets copied?**

Options:
- **Option A:** Copy entire `ai` dict from alpha to followers
  - Pro: Simple, comprehensive
  - Con: Might override follower-specific AI state

- **Option B:** Copy only `disposition` property
  - Pro: General enough for friendly/hostile/neutral/fleeing
  - Con: Doesn't capture complex behaviors like "guarding location X"

- **Option C:** Copy specific properties listed in follower definition
  - Example: `"copy_from_alpha": ["hostile", "disposition", "destination"]`
  - Pro: Flexible, author-controlled
  - Con: More complex, requires authors to think about what to sync

- **Option D:** Copy behavior, not state
  - Followers invoke same action as alpha (if alpha attacks, followers attack)
  - Pro: Behavior-level coordination, very flexible
  - Con: Requires more complex implementation

**Question 2: When does copying happen?**

Recommendation (from critique): During NPC action phase, each pack member checks alpha.

Detailed mechanism:
```
NPC Action Phase:
1. Sort NPCs by pack_role ("alpha" first, then "follower")
2. For each NPC:
   a. If pack_role == "alpha": take normal action
   b. If pack_role == "follower":
      - First: check alpha and copy specified state
      - Then: take action based on updated state
```

This ensures:
- Alphas act first each turn
- Followers see alpha's current-turn state
- Coordination happens automatically without special phase

**Question 3: Is coordination one-way or bidirectional?**

Current design implies one-way (alpha → followers), but consider:
- Should pack morale affect alpha? (If half the pack flees, should alpha reconsider?)
- Should follower injuries affect alpha behavior?
- Or is it strictly hierarchical?

For Phase 1, **recommend one-way** (alpha → followers) for simplicity.

**Question 4: What about mixed scenarios?**

Example: Wolf pack with alpha + 3 followers
- Player domesticates alpha (alpha becomes friendly)
- Should followers automatically become friendly?
- Or should they require individual domestication?

Current design suggests automatic (followers copy alpha), which creates emergent gameplay: "Befriend the leader and the pack follows."

### Recommended Resolution:

**For Phase 1 (Simplified):**
1. Pack members copy `disposition` from alpha (covers hostile/friendly/neutral/fleeing/desperate)
2. Copying happens during NPC action phase (alpha acts first, followers copy then act)
3. One-way only (alpha → followers)
4. Authors can extend with custom pack behaviors if needed

**Property Schema:**
```json
"ai": {
  "pack_role": "alpha|follower",
  "pack_id": "pack_identifier",
  "follows_alpha": "alpha_actor_id",  // For followers only
  "disposition": "hostile|friendly|neutral|fleeing|desperate"
}
```

**Behavior Implementation:**
```python
def npc_take_action(entity, accessor, context):
    # If this NPC is a pack follower, sync with alpha first
    if entity.properties.get("ai", {}).get("pack_role") == "follower":
        alpha_id = entity.properties["ai"].get("follows_alpha")
        if alpha_id:
            alpha = accessor.get_actor(alpha_id)
            # Copy disposition from alpha
            entity.properties["ai"]["disposition"] = alpha.properties["ai"]["disposition"]

    # Now take action based on (possibly updated) disposition
    # ...
```

**What this enables:**
- UC3: Wolves become friendly when alpha is domesticated
- UC7: Spiders coordinate attacks when broodmother attacks
- Future: Guard squad follows captain's lead (friendly pack)
- Future: Escort convoy follows leader's destination changes

**What this defers:**
- Complex behavior copying (alpha uses ability X → followers use ability X)
- Bidirectional influence (morale contagion)
- Conditional copying (copy only if certain conditions met)
- Multiple states copied beyond disposition

This approach keeps pack coordination **simple and general** while supporting both hostile and friendly pack scenarios.

**RESOLUTION:** ✅ **Accepted - Copy `disposition` during NPC action phase**

Additionally: **Document examples should not default to hostility.** Use varied dispositions in examples (friendly, neutral, desperate) to avoid implying that NPCs are hostile by default.

---

#### 12. **Property Name Inconsistency: "functional" vs "active"** (UC8, line 941)

UC8 uses `"functional": false` but elsewhere the document uses boolean properties like `"breathable": true/false`, and now `"disposition"` for actor state (replacing the old `"hostile": true/false`).

"Functional" is workable, but `"operational"` is clearer and more consistent with boolean flag naming conventions.

**Recommendation:** Change `"functional"` to `"operational"` in UC8 and schema.

**RESOLUTION:** ✅ Accepted - use `"operational"` instead of `"functional"` for construct activation state.

---

## 🔍 UNNECESSARY COMPLEXITY CHECK

The design document follows the principle of starting simple and adding incrementally. I found **NO unnecessary complexity**:

- ✅ Minimal vital stats (health + optional breath)
- ✅ Boolean states instead of complex meters
- ✅ Simple thresholds instead of formulas
- ✅ Property-driven, not code-driven
- ✅ Defers equipment, detailed skills, component damage

The complexity present is well-motivated by the use cases.

---

## 📋 PROPERTY SCHEMA COMPLETENESS

The final schema (lines 1464-1522 and simplified UC doc lines 1050-1143) is mostly complete but missing some properties used in examples.

### Analysis: Core vs Game-Specific Properties

**Question:** Should all properties used in use case examples be included in the core schema, or can they be left to game authors and libraries?

**RESOLUTION:** ✅ **Most properties are game-specific, leave to authors/libraries**

The following properties from the examples are **game-specific** and should NOT be in core schema:
- `trapped: boolean` (UC5, UC6) - specific to rescue scenarios
- `destination: string` (UC6) - specific to escort mechanics
- `alerted_by: string` (UC7) - specific to spider web alerting
- `can_guard/can_inform: boolean` (UC8) - specific capabilities for that construct
- `current_duty: string` (UC8) - specific to task assignment mechanics
- `consumable: boolean` (items, UC6) - item management detail
- `damage_type: string` (items, UC7) - not used in Phase 1
- `light_source: boolean` (items, UC7) - defer until lighting system added
- `activation_trigger: string` (parts, UC2) - game-specific activation logic
- `destructible: boolean` (parts, UC2) - optional destructible environment feature
- `health: number` (parts, UC2) - only needed if parts are destructible
- `burnable: boolean` (parts, UC7) - specific to web-burning mechanic

These are examples of how authors can extend the property system for their game's needs. Including them in the core schema would suggest they're required, which goes against the "use only what you need" philosophy.

### Properties That SHOULD Be Added to Core Schema:

1. **`pack_role: "alpha|follower"`** (under `ai`) - Already resolved in issue #11
2. **`operational: boolean`** - Changed from `functional`, may affect behavior dispatching (constructs that can be activated/deactivated)

### Does This Create Design Problems?

**No.** The property system is explicitly designed to be extensible. Authors define properties as needed for their game. The core schema documents **recommended conventions** for common scenarios, not requirements.

**Benefits of leaving properties to authors:**
- Keeps core schema minimal and focused
- Encourages authorial flexibility
- Reduces burden of maintaining "standard" properties that may not fit all games
- Libraries can emerge organically from common patterns

**When to add to core schema:**
- Property affects engine behavior (like `operational` might affect command dispatching)
- Property is needed for core behaviors to function
- Property is universal across all games using this feature

**Note on `light_source`:** When/if lighting system is added, `light_source` can be added to item schema at that time. Don't add it prematurely.

---

## 🔍 ADDITIONAL ISSUE: Interaction Range Definition (Related to Issue #3)

### Where "range" Is Actually Used

After searching the documents, "range" appears in two distinct contexts:

**1. Contagion Range** (UC1):
- Property: `"contagious_range": "touch"` on conditions
- Purpose: Determines when disease/infection spreads between actors
- Current text: "Player is focused_on scholar (touch range)"

**2. Interaction Range** (UC2 and throughout):
- Property: `"range": "touch"` and `"range": "near"` on attacks
- Purpose: NPC behaviors use this to select appropriate attack
- Example: Golem uses "slam" at touch range, "charge" at near range
- **Applies equally to:** attacks, feeding, medical treatment, services, etc.

### The Core Question

**How does the system determine if an actor/entity is at "touch" range?**

This affects:
- Contagion spread (does disease transfer?)
- Attack selection (which attack should NPC use?)
- Service provision (can healer reach patient?)
- Item interactions (can player give/use item on target?)
- Feeding (can player give food to creature?)

### Current Status

From Issue #3, we know:
- `focused_on` alone is **insufficient** (chandelier example - can examine from distance)
- Some additional criteria needed beyond just `focused_on`

### Analysis Conclusion

After analysis, the property name is misleading. "Attack range" implies it's only for combat, but the same concept applies to:
- Medical treatment range
- Feeding range
- Service provision range
- Any actor-to-actor or actor-to-entity interaction

### Resolution

**RESOLUTION:** ✅ **Accepted - Range is author-interpreted, not engine-managed**

**Key Decisions:**
1. **Property name:** Use `"range"` on interactions (attacks, services, etc.) - it's already general enough
2. **Property name for conditions:** Use `"contagious_range"` (already specific to contagion)
3. **Engine enforcement:** NONE - range is a property for author/behavior logic only
4. **Terminology in docs:** Change "attack range" to "interaction range" everywhere

**What This Means:**
- `range` is a **game designer property**, not engine-managed
- Behaviors interpret range values however they want (context-specific)
- No engine-level validation or enforcement
- `focused_on` indicates general proximity; behaviors decide if that's sufficient
- Authors can add properties like `touchable`, `reachable`, etc. if their game needs it

**For Phase 1:**
- Document that `range` on attacks/interactions is for behavior logic only
- Contagion uses `focused_on` as simple proximity indicator
- Don't try to define universal "touch range" mechanically - too constraining
- Let authors refine in their games based on their needs

**Document Updates Needed:**
- Change all instances of "attack range" to "interaction range" in design docs
- Clarify that range is author-interpreted, not engine-enforced
- Note that same range concept applies to attacks, feeding, healing, services, etc.

---

## 📊 SUMMARY

### **Overall Assessment: STRONG DESIGN** ⭐⭐⭐⭐½

The design is **well-structured, thoughtfully motivated, and handles all use cases gracefully**. The issues found are primarily **documentation clarity** problems, not fundamental design flaws.

### **Priority Fixes:**

1. **MUST FIX - Critical Inconsistencies:**
   - Standardize `cures`/`treats`/`treatable_by` terminology
   - Specify exact turn phase ordering
   - Define spatial range terms ("touch", "near", "far")

2. **SHOULD FIX - Moderate Issues:**
   - Complete property schemas with ALL properties used in examples
   - Add resistance calculation formula
   - Clarify death behavior contract
   - Explain service payment matching rules

3. **NICE TO FIX - Minor Issues:**
   - Standardize "effectiveness" vs "cure_amount"
   - Add NPC early-return pattern example
   - Clarify pack coordination timing
   - Add relationship dynamic creation note

### **Design Quality:**
- ✅ Goals clearly stated
- ✅ Features well-motivated
- ✅ Use cases fully covered
- ✅ No unnecessary complexity
- ✅ Good extensibility
- ⚠️ Some terminology inconsistencies
- ⚠️ Some implementation details underspecified

### **Recommended Next Steps:**

1. Fix the 3 critical issues (terminology, turn order, spatial ranges)
2. Complete the property schemas
3. Add the clarifications for moderate issues
4. Then proceed to implementation with confidence

The design is sound and ready for implementation after addressing these documentation issues.

---

## 🎯 VERIFICATION AGAINST DESIGN PRINCIPLES

### From CLAUDE.md Design Principles:

**"Designs should always state their use cases and goals"** ✅
- Document clearly states 5 design goals and 8 use cases

**"Aim for the simplest design that can support the goals"** ✅
- Progressive complexity, minimal vital stats, property-driven

**"Features should be clearly motivated by use cases"** ✅
- Every feature traces to specific use cases

**"Thoroughly review for inconsistencies, holes, and unnecessary complexity"** ⚠️
- This review found 12 issues (3 critical, 4 moderate, 5 minor)
- All are fixable documentation issues, not design flaws

**"Clearly separate public APIs from internal design"** ✅
- Property schemas (public) vs behavior implementation (internal)

**"Always maximize extensibility and user agency"** ✅
- Property-driven, behavior-based, multiple solution paths

**"Never optimize for performance without evidence"** ✅
- Document mentions performance ("cheap early return") but doesn't over-optimize

---

## 📝 CONCLUSION

This is a **high-quality design** that successfully balances:
- Author capability (flexible, property-driven)
- Player agency (multiple solution paths)
- Implementation simplicity (reuses existing patterns)
- Extensibility (behavior-based, not hardcoded)

The identified issues are primarily **documentation consistency** problems that should be fixed before implementation begins. Once these are addressed, the design will be clear, complete, and ready for development.
