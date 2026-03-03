# Complete NPC Authoring: Missing Handlers and Walkthroughs

Issue #398 completed the unified reaction system migration and configured reaction properties for all 17 incomplete NPCs. However, several NPCs still need handler implementation and all NPCs need walkthrough testing.

## Status Summary

**Fully Functional - Handlers Exist (9 NPCs):**
- ✅ The Echo - Full handlers in echo.py (dialog, gossip, trust)
- ✅ Healer Elara - Service handler in services.py (healing, gossip)
- ✅ Alpha Wolf - Gift reactions handler in wolf_pack.py
- ✅ Salamander (leader) - Gift + dialog handlers in salamanders.py
- ✅ Spore Mother - Item use + death handlers in spore_mother.py
- ✅ Spider Matriarch - Death handler in spider_nest.py
- ✅ Hunter Sira - Encounter + death handlers in sira_rescue.py
- ✅ Dire Bear - Encounter handler in bear_cubs.py
- ✅ Bee Queen - Take reactions handler in bee_queen.py

**Fully Functional - Data-Driven (6 NPCs/Items):**
- ✅ Bear Cubs (2) - Item use reactions (healing) - data-driven
- ✅ Damaged Guardian - Item use + dialog reactions - data-driven
- ✅ Stone Golems (2) - Death handlers in golem_puzzle.py
- ✅ Merchant Delvan - Encounter + death handlers in dual_rescue.py
- ✅ Sailor Garrett - Death handler (condition_reactions data-driven)
- ✅ Myconid Elder - Encounter handler in fungal_death_mark.py

**Pack Followers - Need Testing (8 NPCs):**
- ⚠️ Frost Wolves (2) - No reactions configured (should mirror alpha_wolf via pack_behavior)
- ⚠️ Steam Salamanders (2) - Dialog handlers exist but pack mirroring not configured
- ⚠️ Sporelings (3) - No reactions configured (should mirror spore_mother via pack_behavior)
- ⚠️ Giant Spiders (2) - No reactions configured (should mirror matriarch via pack_behavior)

**Missing Implementation (5 NPCs):**
- ⚠️ Gate Guard - Dialog stub only, no region warnings implementation
- ⚠️ Herbalist Maren - Dialog stub only, no trading handler
- ⚠️ Camp Leader Mira - Dialog stub only, no quest/commitment system
- ⚠️ The Archivist - Dialog stub only, no lore trading or state transitions
- ⚠️ Curiosity Dealer Vex - Dialog configured but no trading handler

---

## Missing Handler Implementations

### 1. Herbalist Maren Trading System

**File:** `examples/big_game/behaviors/regions/civilized_remnants/services.py`

**Required Handler:** `on_trade_request(entity, accessor, context) -> EventResult`

**Functionality Needed:**
- Detect trade keywords from dialog context
- Implement item-for-gold exchanges
- Trust-based pricing (higher trust → discounts)
- Inventory management (add/remove items from player/NPC)
- Available items: silvermoss, healing_potion, antidote, warm_clothes
- Prices scale with trust: base_price * (1.0 - (trust * 0.1))

**Current Config:** Dialog stub with trade keywords

**Needs:** Actual trading logic with item grants, gold deductions, inventory checks.

---

### 2. Camp Leader Mira Quest System

**File:** `examples/big_game/behaviors/regions/civilized_remnants/mira.py` (NEW)

**Required Handlers:**
- `on_quest_offer(entity, accessor, context) -> EventResult`
- `on_quest_complete(entity, accessor, context) -> EventResult`
- `on_quest_failed(entity, accessor, context) -> EventResult`

**Functionality Needed:**
- Quest offering via dialog (keywords: help, quest, survivors)
- Create time-limited commitment (20 turns)
- Quest: Rescue survivors from dangerous location
- Success: state → allied, trust +2, unlock camp services
- Failure: state → disappointed, trust -3
- Track commitment in state.extra.active_commitments

**Current Config:** Default response only

**Needs:** Full quest/commitment system implementation.

---

### 3. The Archivist Lore Trading

**File:** `examples/big_game/behaviors/regions/civilized_remnants/archivist.py` (NEW)

**Required Handlers:**
- `on_lore_trade(entity, accessor, context) -> EventResult`
- `on_prove_worth(entity, accessor, context) -> EventResult`

**Functionality Needed:**
- Lore trading: Accept artifacts → grant knowledge
- State transitions:
  - guardian → helpful: Solve library puzzle or prove worth
  - helpful → allied: Multiple successful trades
- Knowledge grants (add to player.properties.knowledge)
- Artifact consumption (remove from inventory)
- Accepted items: ancient_artifact, preserved_tome, waystone_fragment

**Current Config:** Guardian response stub

**Needs:** Artifact trading system + state progression logic.

---

### 4. Curiosity Dealer Vex Rare Trading

**File:** `examples/big_game/behaviors/regions/civilized_remnants/vex.py` (NEW)

**Required Handlers:**
- `on_rare_trade(entity, accessor, context) -> EventResult`
- `on_information_sale(entity, accessor, context) -> EventResult`

**Functionality Needed:**
- Buy unusual items at high prices (2x normal value)
- Sell rare items: command_orb, ancient_tools, special_equipment
- Information broker: Sell secrets for 100 gold (trust >= 2)
- Gift reactions for curiosities (strange_artifact, mysterious_object)
- Trust affects item availability and prices

**Current Config:** Dialog with trust_delta

**Needs:** Trading handler + gift reactions handler.

---

### 5. Gate Guard Region Warnings

**Enhancement to:** Data-driven config (no handler needed if implemented correctly)

**Functionality Needed:**
- Provide region-specific warnings based on keyword
- Set flags when warnings given: guard_warned_{region}
- Map keywords to regions:
  - frozen/ice → frozen_reaches warnings
  - beast/wild → beast_wilds warnings
  - fungal/mushroom → fungal_depths warnings
  - sunken/water → sunken_city warnings

**Current Config:** Warning stub with keywords

**Needs:** Either handler or enhanced data-driven support for keyword → message mapping.

---

## Pack Behavior Configuration Issues

Analysis shows pack followers are **not configured with pack_behavior properties**:
- Frost wolves, steam salamanders, sporelings, and giant spiders have no `pack_behavior` in their properties
- They have state machines matching their leaders but no mirroring mechanism
- Pack mirroring requires explicit `pack_behavior: {pack_id, leader, role}` configuration

**Action Required:**
1. Add `pack_behavior` properties to all pack followers in game_state.json
2. Verify pack_mirroring.py hooks properly handle state/trust propagation
3. Create walkthroughs testing pack mirroring behavior

## Required Walkthrough Testing

**Existing Walkthroughs (Coverage Check):**
- ✅ Wolf feeding - EXISTS (test_wolf_feeding.txt)
- ✅ Salamander - EXISTS (4 files: communication, companion, gestures, trust)
- ✅ Fungal depths - EXISTS (6 files covering spore mother, aldric, mushrooms)
- ✅ Frozen reaches - EXISTS (8 files covering golems, telescope, hypothermia)
- ✅ Gift reactions - EXISTS (test_gift_reaction.txt)
- ❌ The Echo - MISSING
- ❌ Healer Elara - MISSING
- ❌ Bear cubs commitment - MISSING (mentioned in git status as "test_bear_cubs_commitment.txt" untracked)
- ❌ Bee Queen - MISSING
- ❌ Hunter Sira - MISSING
- ❌ Damaged Guardian - MISSING
- ❌ Gate Guard - MISSING
- ❌ All town NPCs (Maren, Mira, Archivist, Vex) - MISSING
- ❌ Pack followers mirroring - MISSING

All NPCs need comprehensive walkthrough files. See npc_authoring_plan.md for full testing requirements for each NPC.

**Minimum Coverage:**
- Dialog system (all keywords, trust gates, state gates)
- Gift reactions (accepted items, trust changes)
- Item use reactions (repair sequences, healing)
- State transitions (triggers and effects)
- Pack behaviors (leader state mirroring)
- Commitment systems (quest offer, complete, fail)
- Trust progression (positive and negative events)

---

## Validation Requirements

After implementing handlers and creating walkthroughs:

1. **Code Validation:**
   ```bash
   python tools/validate_game_state.py examples/big_game
   ```
   - Must show 0 errors
   - Warnings acceptable for named reaction configs

2. **Walkthrough Execution:**
   ```bash
   python tools/walkthrough.py walkthroughs/npcs/*.wt
   ```
   - All expected behaviors must occur
   - Expected failures (trust gates, state gates) must work correctly
   - No unexpected errors

3. **Integration Testing:**
   - Test NPC interactions with other systems (gossip, commitments, companions)
   - Test save/load with NPCs in various states
   - Test edge cases (low trust, missing items, wrong states)

---

## Additional Findings from Code Analysis

### Reaction Infrastructure Status
- ✅ All 11+ reaction type handlers implemented in behaviors/shared/infrastructure/
- ✅ Core interpreter (reaction_interpreter.py) complete
- ✅ Effect handlers (reaction_effects.py) and conditions (reaction_conditions.py) complete
- ✅ Mypy type errors previously reported are now FIXED

### Reaction Distribution in Game State
- **48 total reaction configs** across actors, items, and locations
- **Gift reactions**: 4 entities (3 handler-based, 1 data-driven)
- **Dialog reactions**: 11 entities (5 handler-based, 6 data-driven)
- **Item use reactions**: 17 entities (4 handler-based, 13 data-driven)
- **Encounter reactions**: 4 entities (all handler-based)
- **Death reactions**: 7 entities (all handler-based)
- **Take reactions**: 1 entity (handler-based)
- **Gossip reactions**: 2 entities (all handler-based)
- **Condition reactions**: 2 entities (all data-driven)

### Pack Behavior Files Exist But Not Configured
- `pack_mirroring.py` infrastructure exists in shared/infrastructure/
- `packs.py` library exists in shared/lib/actor_lib/
- BUT pack followers lack `pack_behavior` property configuration in game_state.json

## Success Criteria

- [ ] All 5 missing handler files created and implemented
- [ ] Gate Guard warnings enhanced (handler or data-driven)
- [ ] **Pack behavior properties added to 8 pack followers**
- [ ] **Pack mirroring tested and working**
- [ ] All 17+ walkthrough files created (including pack followers)
- [ ] All walkthroughs execute successfully
- [ ] Validation shows 0 errors
- [ ] All NPCs respond correctly to player interactions
- [ ] Trust systems functional for all NPCs with trust_state
- [ ] State machines transition correctly
- [ ] Pack behaviors mirror properly
- [ ] Commitment system works for Mira

---

## Related Issues

- #398 - Unified reaction system migration (completed migration)

---

## Implementation Phasing

**Phase 1: Simpler Trading (1 day)**
- Implement Maren trading (builds on existing services.py)
- Create Maren walkthrough
- Test and debug

**Phase 2: Complex Trading (1 day)**
- Implement Vex trading (similar to Maren + information broker)
- Create Vex walkthrough
- Test and debug

**Phase 3: Quest/Commitment System (1-2 days)**
- Implement Mira quests (commitment system)
- Create Mira walkthrough
- Test and debug

**Phase 4: Lore/Artifact Trading (1 day)**
- Implement Archivist lore trading
- Create Archivist walkthrough
- Test and debug

**Phase 5: Configure Pack Behaviors (0.5 days)**
- Add pack_behavior properties to frost_wolf_1, frost_wolf_2
- Add pack_behavior properties to steam_salamander_2, steam_salamander_3
- Add pack_behavior properties to npc_sporeling_1, npc_sporeling_2, npc_sporeling_3
- Add pack_behavior properties to giant_spider_1, giant_spider_2
- Verify pack_mirroring.py infrastructure
- Test pack mirroring manually

**Phase 6: Walkthroughs for Working NPCs (2 days)**
- Create walkthrough: test_echo_dialog.txt (Echo dialog + gossip)
- Create walkthrough: test_healer_elara.txt (Elara healing service)
- Create walkthrough: test_bear_cubs_commitment.txt (Bear encounter + cubs + commitment)
- Create walkthrough: test_bee_queen_honey.txt (Bee queen take reactions)
- Create walkthrough: test_sira_rescue.txt (Sira encounter + rescue)
- Create walkthrough: test_damaged_guardian.txt (Guardian item use reactions)
- Create walkthrough: test_gate_guard.txt (Gate guard dialog stub)
- Create walkthrough: test_pack_wolves.txt (Wolf pack mirroring)
- Create walkthrough: test_pack_salamanders.txt (Salamander pack mirroring)
- Create walkthrough: test_pack_sporelings.txt (Sporeling pack mirroring)
- Create walkthrough: test_pack_spiders.txt (Spider pack mirroring)
- Create walkthrough: test_merchant_delvan.txt (Delvan encounter + condition)
- Create walkthrough: test_myconid_elder.txt (Elder encounter)
- Execute all walkthroughs
- Fix any issues discovered

**Phase 7: Integration Testing (0.5 days)**
- Test cross-NPC interactions
- Test edge cases
- Final validation
