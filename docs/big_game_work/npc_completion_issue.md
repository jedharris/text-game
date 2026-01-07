# Complete NPC Authoring: Missing Handlers and Walkthroughs

Issue #398 completed the unified reaction system migration and configured reaction properties for all 17 incomplete NPCs. However, several NPCs still need handler implementation and all NPCs need walkthrough testing.

## Status Summary

**Fully Functional (7 NPCs):**
- ✅ The Echo - Full handlers in echo.py (dialog, gossip, trust)
- ✅ Healer Elara - Service handler in services.py (healing, gossip)
- ✅ Wolf Pack (alpha_wolf, frost_wolf_1/2) - Pack behavior + feeding in wolf_pack.py
- ✅ Salamanders (salamander, steam_salamander_2/3) - Pack behavior + gifts in salamanders.py
- ✅ Sporelings (spore_mother, sporelings 1/2/3) - Pack behavior in spore_mother.py
- ✅ Spiders (spider_matriarch, giant_spider_1/2) - Pack behavior + death in spider_nest.py

**Partially Implemented (10 NPCs):**
- ⚠️ Gate Guard - Dialog stub only, no region warnings implementation
- ⚠️ Herbalist Maren - Dialog stub only, no trading handler
- ⚠️ Camp Leader Mira - Dialog stub only, no quest/commitment system
- ⚠️ The Archivist - Dialog stub only, no lore trading or state transitions
- ⚠️ Curiosity Dealer Vex - Dialog configured but no trading handler
- ⚠️ Damaged Guardian - Item_use reactions configured (should work) but untested

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

## Required Walkthrough Testing

All 17 NPCs need comprehensive walkthrough files in `walkthroughs/npcs/`:

See npc_authoring_plan.md for full testing requirements for each NPC.

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

## Success Criteria

- [ ] All 5 missing handler files created and implemented
- [ ] Gate Guard warnings enhanced (handler or data-driven)
- [ ] All 17 walkthrough files created
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

**Phase 5: Walkthroughs for Working NPCs (1 day)**
- Create walkthroughs for: Echo, Elara, wolf pack, salamanders, sporelings, spiders
- Create walkthrough for damaged_guardian
- Create walkthrough for gate_guard (stub)
- Execute all walkthroughs
- Fix any issues discovered

**Phase 6: Integration Testing (0.5 days)**
- Test cross-NPC interactions
- Test edge cases
- Final validation
