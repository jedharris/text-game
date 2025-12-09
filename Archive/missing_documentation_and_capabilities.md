## Documentation Issues and Missing Capabilities

### Documentation Gaps Encountered

1. **Darkness and Light Sources**
   - The authoring manual mentions `provides_light` and light/extinguish commands
   - No documentation found on how darkness affects room descriptions or prevents certain actions
   - Unclear whether there's a system for rooms requiring light to see/interact
   - **Impact:** Cannot confidently design dark areas requiring light sources
   - **Status:** Light sources exist but darkness enforcement does not
     - Documentation: [documentation_hole_filling.md](documentation_hole_filling.md) - item 4
     - Implementation: [framework_hole_filling.md](framework_hole_filling.md) - item 3 (Darkness/Visibility Library)

2. **Time Passage and Scheduled Events**
   - Turn system is documented, but no mechanism for "X turns have passed since event Y"
   - No clear way to track global turn count for time-pressure scenarios
   - **Impact:** The "Spore spread if not addressed in N turns" mechanic may need custom implementation
   - **Status:** Turn phases exist but no turn counter or scheduling
     - Implementation: [framework_hole_filling.md](framework_hole_filling.md) - items 1 & 2 (Turn Counter, Scheduled Events)

3. **NPC Movement Between Rooms**
   - Actor documentation covers NPCs acting in place
   - No documentation on NPCs moving between locations autonomously
   - The Hunter Sira "wandering NPC" concept may not be supported
   - **Impact:** Wandering NPCs may need custom behavior implementation
   - **Status:** Not implemented
     - Implementation: [framework_hole_filling.md](framework_hole_filling.md) - item 5 (NPC Movement/Patrol Library)

4. **Crafting/Combining Items**
   - No documentation on combining items to create new items
   - Recipe/crafting systems not mentioned
   - **Impact:** The "repair telescope with components" mechanic may need custom implementation
   - **Status:** Not implemented
     - Implementation: [framework_hole_filling.md](framework_hole_filling.md) - item 6 (Crafting Library)

5. **Inventory Weight/Capacity**
   - The handler chaining example shows weight limits as custom code
   - No built-in inventory capacity system documented
   - **Impact:** Encumbrance mechanics would need custom implementation
   - **Status:** Not implemented; recommended as custom game behavior if needed
     - Implementation: [big_game_implementation.md](big_game_implementation.md) - item 4 (deferred)

6. **Dialog Trees/Conversation**
   - Basic NPC dialogue mentioned but no structured conversation system
   - No apparent support for dialog trees, topics, or conditional responses
   - **Impact:** Complex NPC conversations may need custom behavior work
   - **Status:** Not implemented
     - Implementation: [framework_hole_filling.md](framework_hole_filling.md) - item 7 (Dialog Library)

### Potential Missing Engine Capabilities

1. **Global Flags System**
   - Player properties work for individual state
   - Unclear if there's a clean way to track world-state flags (e.g., "spore_mother_healed")
   - Workaround: Use player or specific entity properties as global flags
   - **Status:** EXISTS - `GameState.set_flag()` and `get_flag()`
     - Documentation: [documentation_hole_filling.md](documentation_hole_filling.md) - item 1

2. **Timed Events**
   - No apparent mechanism for "after N turns, do X"
   - Would need custom behavior tracking turn counts
   - **Status:** Turn phases exist but no counter or scheduling
     - Implementation: [framework_hole_filling.md](framework_hole_filling.md) - items 1 & 2

3. **Area-Wide Effects**
   - Each room/part can have environmental effects
   - No clear mechanism for "all rooms in region X now have property Y"
   - Workaround: Update all relevant entities when state changes
   - **Status:** Recommended as custom game behavior pattern
     - Implementation: [big_game_implementation.md](big_game_implementation.md) - item 1 (deferred)

4. **Companion Following**
   - Domesticated creatures becoming companions implies following behavior
   - No documentation on how companions follow player between rooms
   - May need custom implementation in on_go behaviors
   - **Status:** Not implemented
     - Implementation: [framework_hole_filling.md](framework_hole_filling.md) - item 4 (Companion Library)

5. **Reputation System**
   - Relationships are actor-to-actor
   - No apparent faction/group reputation system
   - Workaround: Use relationships with a "faction representative" actor
   - **Status:** Relationship system exists; faction layer recommended as custom behavior
     - Documentation: [documentation_hole_filling.md](documentation_hole_filling.md) - item 5
     - Implementation: [big_game_implementation.md](big_game_implementation.md) - item 2 (deferred)

---

## Capability Analysis and Recommendations

*Analysis conducted by reviewing src/, behaviors/, behavior_libraries/, and examples/*

### Existing Capabilities (Documentation Needed)

These capabilities **already exist** but need better documentation:

#### 1. Global Flags System ✅ EXISTS
- **Location:** `GameState.set_flag()` and `get_flag()` in [state_manager.py:471-484](src/state_manager.py#L471-L484)
- **How it works:** Stores flags in `player.properties["flags"]` dict
- **Usage:** `state.set_flag("spore_mother_healed", True)` / `state.get_flag("spore_mother_healed")`
- **Also available:** `GameState.extra` dict for non-player-specific global state
- **Action:** Document in authoring manual → [documentation_hole_filling.md](documentation_hole_filling.md)

#### 2. Turn Phase Hooks ✅ EXISTS
- **Location:** [hooks.py](src/hooks.py) and [llm_protocol.py:265-301](src/llm_protocol.py#L265-L301)
- **Hooks fire in order after each successful command:**
  1. `NPC_ACTION` - NPCs take actions
  2. `ENVIRONMENTAL_EFFECT` - Apply environmental hazards
  3. `CONDITION_TICK` - Progress all conditions
  4. `DEATH_CHECK` - Check for deaths
- **Action:** Document in authoring manual → [documentation_hole_filling.md](documentation_hole_filling.md)

#### 3. Environmental Effects System ✅ EXISTS
- **Location:** [behaviors/actors/environment.py](behaviors/actors/environment.py)
- **Implemented effects:**
  - Breath/drowning (non-breathable parts)
  - Spore exposure (low/medium/high spore levels)
  - Temperature effects (freezing→hypothermia, burning→burning condition)
- **Part properties:** `breathable`, `breathing_item_works`, `spore_level`, `temperature`
- **Action:** Document in authoring manual → [documentation_hole_filling.md](documentation_hole_filling.md)

#### 4. Light Source Behaviors ✅ EXISTS (Partial)
- **Location:** [behaviors/core/light_sources.py](behaviors/core/light_sources.py)
- **Implemented:** Auto-light on take, extinguish on drop/put, `states["lit"]` tracking
- **NOT implemented:** Darkness preventing actions, visibility checks based on light
- **Action:**
  - Document current state → [documentation_hole_filling.md](documentation_hole_filling.md)
  - Implement darkness enforcement → [framework_hole_filling.md](framework_hole_filling.md)

#### 5. Relationship System ✅ EXISTS
- **Location:** [behaviors/actors/relationships.py](behaviors/actors/relationships.py)
- **Implemented:** Trust, gratitude, fear (0-10 scale) with threshold effects
- **Thresholds:** domestication (gratitude≥3), discount (trust≥3), loyalty (trust≥5), intimidation (fear≥5)
- **Action:** Document in authoring manual → [documentation_hole_filling.md](documentation_hole_filling.md)

---

### Capabilities Needing Implementation

#### 1. Darkness/Visibility System
**Current state:** Light sources track `lit` state but nothing enforces darkness restrictions.

**Recommendation: Game Library** (`behavior_libraries/darkness_lib/`)

**Rationale:** Different games may want different darkness rules (some allow basic movement in dark, others don't). A library allows customization.

**Action:** → [framework_hole_filling.md](framework_hole_filling.md) item 3

---

#### 2. Turn Counter and Timed Events
**Current state:** Turns progress but there's no global counter for "N turns since X".

**Recommendation: Engine Extension** (add to `GameState`)

**Rationale:** Turn counting is fundamental and useful across all games. Simple addition to core.

**Action:** → [framework_hole_filling.md](framework_hole_filling.md) items 1 & 2

---

#### 3. NPC Movement/Patrol
**Current state:** NPCs stay in their initial location. No patrol or wandering system.

**Recommendation: Game Library** (`behavior_libraries/npc_movement_lib/`)

**Rationale:** NPC movement patterns vary widely (patrol routes, wandering, following). Better as optional library.

**Action:** → [framework_hole_filling.md](framework_hole_filling.md) item 5

---

#### 4. Companion Following
**Current state:** No system for NPCs to follow player between rooms.

**Recommendation: Game Library** (`behavior_libraries/companion_lib/`)

**Rationale:** Companion mechanics (who follows, restrictions, combat help) vary by game.

**Action:** → [framework_hole_filling.md](framework_hole_filling.md) item 4

---

#### 5. Crafting/Combining Items
**Current state:** No crafting system exists.

**Recommendation: Game Library** (`behavior_libraries/crafting_lib/`)

**Rationale:** Crafting complexity varies enormously. Some games need simple 2-item combine, others need workbenches, skills, etc.

**Action:** → [framework_hole_filling.md](framework_hole_filling.md) item 6

---

#### 6. Inventory Capacity/Weight
**Current state:** No weight or capacity limits.

**Recommendation: Custom Game Behavior** (if needed)

**Rationale:** Many games don't want encumbrance. When needed, it's simple to implement per-game.

**Action:** → [big_game_implementation.md](big_game_implementation.md) item 4 (deferred)

---

#### 7. Dialog/Conversation System
**Current state:** No structured dialog system. NPC interaction is via verbs (talk, ask).

**Recommendation: Game Library** (`behavior_libraries/dialog_lib/`)

**Rationale:** Dialog trees are a large feature that not all games need. LLM narration often handles conversation naturally.

**Action:** → [framework_hole_filling.md](framework_hole_filling.md) item 7

---

#### 8. Area-Wide Effects / Regions
**Current state:** Each location/part has independent properties. No region grouping.

**Recommendation: Custom Game Behavior** (pattern, not library)

**Rationale:** "Regions" are game-specific organizational concepts. Better to show the pattern.

**Action:** → [big_game_implementation.md](big_game_implementation.md) item 1 (deferred)

---

#### 9. Faction/Group Reputation
**Current state:** Relationships are actor-to-actor only.

**Recommendation: Custom Game Behavior** (using existing relationship system)

**Rationale:** The existing relationship system can model factions by using a "faction representative" actor.

**Action:** → [big_game_implementation.md](big_game_implementation.md) item 2 (deferred)

---

### Summary Table

| Capability | Recommendation | Action Document |
|------------|---------------|-----------------|
| Global flags | ✅ Already exists | [documentation_hole_filling.md](documentation_hole_filling.md) |
| Turn phases/hooks | ✅ Already exists | [documentation_hole_filling.md](documentation_hole_filling.md) |
| Environmental effects | ✅ Already exists | [documentation_hole_filling.md](documentation_hole_filling.md) |
| Light sources | ✅ Partial | [documentation_hole_filling.md](documentation_hole_filling.md) + [framework_hole_filling.md](framework_hole_filling.md) |
| Relationships | ✅ Already exists | [documentation_hole_filling.md](documentation_hole_filling.md) |
| Turn counter | **Engine extension** | [framework_hole_filling.md](framework_hole_filling.md) |
| Scheduled events | **Game library** | [framework_hole_filling.md](framework_hole_filling.md) |
| Darkness/visibility | **Game library** | [framework_hole_filling.md](framework_hole_filling.md) |
| NPC movement/patrol | **Game library** | [framework_hole_filling.md](framework_hole_filling.md) |
| Companion following | **Game library** | [framework_hole_filling.md](framework_hole_filling.md) |
| Crafting/combining | **Game library** | [framework_hole_filling.md](framework_hole_filling.md) |
| Dialog trees | **Game library** | [framework_hole_filling.md](framework_hole_filling.md) |
| Inventory weight | **Custom behavior** | [big_game_implementation.md](big_game_implementation.md) (deferred) |
| Area-wide effects | **Custom behavior** | [big_game_implementation.md](big_game_implementation.md) (deferred) |
| Faction reputation | **Custom behavior** | [big_game_implementation.md](big_game_implementation.md) (deferred) |

---

### Recommended Implementation Priority for Big Game

1. **Immediate (needed for core gameplay):**
   - Turn counter (engine extension) - simple, enables timed events
   - Companion following library - wolf pack, hunter Sira as companions
   - Crafting library - telescope repair, multiple crafting scenarios

2. **High (significant gameplay impact):**
   - Darkness/visibility library - Deep Root Caverns, Ice Caves
   - NPC movement library - Hunter Sira wandering

3. **Medium (enhances but not critical):**
   - Dialog library - richer NPC conversations
   - Scheduled events (timed triggers) - spore spread deadline

4. **Low (use patterns instead):**
   - Area-wide effects - pattern suffices
   - Faction reputation - use relationship system
   - Inventory weight - likely not needed
