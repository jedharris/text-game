# Region Completion: Beast Wilds (#389) + Sunken District (#388)

## Goal

Wire all existing handler code to game_state configs so every NPC mechanic actually fires during gameplay. Both regions have well-written handler code that's disconnected from the data layer.

## Non-Goals

- New handler code (handlers already exist)
- Swimming skill system (defer — needs design discussion)
- Predatory fish combat (defer — needs combat system work)
- Undercity content (#441 — separate issue)

## Approach

Work entity-by-entity. For each: wire configs → create/update walkthrough → verify passing. Use existing walkthroughs as starting points where they exist.

---

## Phase 1: Beast Wilds — Bear Cubs Commitment

**Problem:** `bear_cubs.py` handlers exist but:
- No `commit_bear_cubs` in `commitment_configs`
- dire_bear has no `encounter_reactions` or `commitment_reactions`
- bear_cub_1/bear_cub_2 have no `item_use_reactions` or `condition_reactions`

**Work:**
1. Add `commit_bear_cubs` to `extra.commitment_configs` in game_state.json
2. Wire dire_bear encounter_reactions → `bear_cubs:on_bear_encounter`
3. Wire bear cub condition_reactions or item_use_reactions for healing
4. Fix/create walkthrough covering encounter → commitment → healing → grateful bear
5. Verify walkthrough passes

**Status: COMPLETE** (#465) — All configs wired, `test_bear_cubs_healing.txt` 6/6 passing. Also fixed `deadline_turns` → `base_timer` globally, fixed handler path prefixes.

---

## Phase 2: Beast Wilds — Wolf Pack Items

**Problem:** Wolf feeding works but `venison` item doesn't exist.

**Work:**
1. Add venison item to game_state.json (location TBD — likely hunters_camp or forest_edge)
2. Verify `test_wolf_feeding.txt` passes without @set for inventory
3. If flowers (moonpetal, frost_lily, water_bloom) are also missing, add them for bee_queen

**Status: COMPLETE** (#466) — Venison and flowers already existed. Added missing exit pair (tangled_path ↔ wolf_clearing). Added `on_receive_item` event to wolf_pack.py vocabulary. `test_wolf_feeding.txt` 6/6 passing. Closed #463 (flowers exist).

---

## Phase 3: Beast Wilds — Spider Nest Bugs

**Problem:** `spider_nest.py` has known bugs:
- `spider.properties["location"]` should be `spider.location`
- Respawn code loops spider_1..spider_9 but only 2 exist

**Work:**
1. Fix location assignment bug
2. Decide: reduce respawn range to match actual spiders, or add more spiders
3. Wire spider_matriarch reactions if needed
4. Create/update spider walkthrough

**Status: COMPLETE** (#464) — Fixed `spider.properties["location"]` → `spider.location`, reduced respawn range(1,10) → range(1,3) to match 2 existing spiders, fixed destination check for spider locations. Updated test to verify correct behavior.

---

## Phase 4: Sunken District — Garrett Rescue

**Problem:** Garrett can't be rescued via item use:
- No `encounter_reactions` configured (timer doesn't start)
- No `item_use_reactions` configured (can't use air_bladder)
- `dual_rescue.py:on_garrett_encounter` checks location ID but Garrett uses encounter_reactions pattern

**Work:**
1. Add encounter_reactions to sailor_garrett → `dual_rescue:on_garrett_encounter`
2. Add item_use_reactions to sailor_garrett: air_bladder removes drowning condition
3. Add `commit_garrett_rescue` to commitment_configs if missing
4. Create walkthrough for Garrett rescue path
5. Update `test_mira_dual_rescue.txt` to use real item use instead of @set

**Status: COMPLETE** (#467) — All configs wired. Key discovery: `entity_item_used` hook fires on the item entity, so air_bladder needed `item_use_reactions` behavior in its behaviors list. `test_garrett_rescue.txt` 5/5 passing. All Delvan walkthroughs still passing.

---

## Phase 5: Sunken District — Drowning System

**Problem:** `drowning.py` handlers exist but vocabulary events empty, `__init__.py` empty.

**Work:**
1. Populate `__init__.py` to register drowning module
2. Wire drowning events to turn/movement hooks
3. Create walkthrough: enter submerged area → breath warnings → surface to reset
4. Test breathing_mask provides immunity

**Note:** This is the most complex phase — drowning hooks into the turn system and movement system. May need infrastructure investigation.

**Status: COMPLETE** — Rewrote drowning.py to use a single turn_phase hook (`turn_drowning`) that detects water transitions by checking location `breathable` property each turn. Simpler than separate movement hooks. Added air_bladder self-use (`use bladder on self`) with use decrement. Items with `breathing_item: true` in inventory grant immunity. `test_drowning_system.txt` 15/15 passing. Updated tests to use new API.

---

## Phase 6: Verification

Run all walkthroughs for both regions. Run full test suite. Update issue comments and close.

**Status: COMPLETE** — All walkthroughs passing:
- `test_bear_cubs_healing.txt`: 6/6
- `test_wolf_feeding.txt`: 6/6
- `test_garrett_rescue.txt`: 5/5
- `test_delvan_rescue_success.txt`: 5/5
- `test_delvan_garrett_choice.txt`: 5/5
- `test_drowning_system.txt`: 15/15
- Infrastructure tests: 574 passed

---

## Deferred Work

### Swimming skill gate (old_swimmer_jek)
**Blocked by:** Dialog system for teaching mechanics. Jek needs a dialog_reactions handler that checks payment (teaching_cost=5), grants `basic_swimming` skill to player, and gates tidal_passage entry. Requires:
- Dialog reaction handler for Jek (new code in sunken_district/)
- Skill-check infrastructure: movement handler that checks player skills before allowing entry to skill-gated locations
- Decision: is `basic_swimming` a player property, an inventory item, or a condition?
**Issue:** #461

### Predatory fish (flooded_chambers)
**Blocked by:** Combat/hazard system. Fish is configured as `hazard_type: "environmental"` with `not_combat_encounter: true`, meaning it's not a standard combat enemy. Requires:
- Environmental hazard handler: damage-on-entry or damage-per-turn while in location
- Hazard avoidance/mitigation mechanics (stealth? speed? equipment?)
- Decision: is this a combat encounter or an environmental tick like drowning?
**Issue:** #462

### Flower item placement (moonpetal, frost_lily, water_bloom)
**Blocked by:** Region content design. These are bee_queen trade items. Questions:
- Which regions contain each flower? (cross-region exploration reward?)
- Are they consumable (one-use) or persistent?
- Can they be found in the wild or only obtained from NPCs?
Currently walkthroughs use @set to inject them. If we add them as items in Phase 2, we need to decide placement.
**Issue:** #463

### Spider population design
**Decision needed:** `spider_nest.py` respawn code iterates spider_1..spider_9 but only giant_spider_1 and giant_spider_2 exist. Options:
- Reduce respawn range to match existing 2 spiders
- Add more spider entities (up to 9) for a swarm feel
- Make respawn count configurable
**Issue:** #464
