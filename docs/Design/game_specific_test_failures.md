# Game-Specific Test Failures

Tracked by issue (to be linked). These are failures and errors that require analysis of game design and narrative, not general code fixes.

## Status: 74 failures, 32 errors total across test suite
Of these, the game-specific failures documented here account for approximately 60 failures and 20 errors. The remainder are general code issues tracked in `fix_categories_1_through_9.md`.

---

## GS-1: Waystone `turn_ending_check` depends on undefined `turn_death_check`

**Files:** `examples/big_game/game_behaviors/regions/meridian_nexus/waystone.py`

**Impact:** 9 errors (all `test_big_game_conditions` tests) — cascading, blocks all big_game behavior loading.

**Details:** `waystone.py` defines turn phase hook `turn_ending_check` with `"after": ["turn_death_check"]`, but no module defines a `turn_death_check` hook. `behavior_manager.finalize_loading()` raises `ValueError`.

**Resolution options:**
- Define `turn_death_check` in the appropriate module (death_reactions.py?)
- Change the dependency to reference an existing hook
- Remove the dependency if ordering doesn't matter

---

## GS-2: Beast Wilds — bee queen flower trading not working

**Files:**
- `examples/big_game/game_behaviors/regions/beast_wilds/bee_queen.py`
- `tests/infrastructure/regions/test_beast_wilds.py` (TestFlowerOffer)
- `tests/infrastructure/test_beast_wilds_scenarios.py` (TestBeeQueenScenarios)
- `tests/infrastructure/test_cross_region_scenarios.py` (TestBeeQueenCrossRegionCollectionScenarios)

**Impact:** ~10 failures

**Failing tests:**
- `TestFlowerOffer::test_valid_flower_accepted` — expects flower tracked in `bee_queen_flowers_traded`, list stays empty
- `TestFlowerOffer::test_invalid_item_rejected` — expects "not what she seeks" feedback, gets `''`
- `TestFlowerOffer::test_three_flowers_unlock_allied` — state machine stays "trading" not "allied"
- `TestBeeQueenScenarios::test_first_flower_trade` — expects "accepts" in feedback, gets `''`
- `TestBeeQueenScenarios::test_non_flower_rejected` — expects "not what she seeks", gets `''`
- `TestBeeQueenScenarios::test_duplicate_flower_type_rejected` — expects "already received", gets `''`
- `TestBeeQueenScenarios::test_three_flowers_allies_queen` — expects "ally", gets `''`
- `TestBeeQueenScenarios::test_respawn_happens_with_living_queen` — queen respawn logic
- `TestBeeQueenCrossRegionCollectionScenarios::test_trading_flowers_from_all_regions`

**Details:** The `on_receive_item` handler in `bee_queen.py` returns empty feedback strings and doesn't track flowers. Either the handler logic is incomplete or the test expectations don't match the handler's design.

---

## GS-3: Beast Wilds — wolf feeding trust/state progression

**Files:**
- `examples/big_game/game_behaviors/regions/beast_wilds/wolf_pack.py`
- `tests/infrastructure/regions/test_beast_wilds.py` (TestWolfFeed)
- `tests/infrastructure/test_beast_wilds_scenarios.py` (TestWolfPackScenarios)

**Impact:** ~4 failures

**Failing tests:**
- `TestWolfFeed::test_feeding_wolf_increases_trust` (x2 — in both regions/ and scenarios)
- `TestWolfFeed::test_feeding_hostile_wolf_transitions_to_wary`
- `TestWolfPackScenarios::test_trust_progression_to_neutral`

**Details:** Wolf `on_receive_item` handler doesn't increase trust or transition state machine as tests expect.

---

## GS-4: Beast Wilds — bear cubs state machine mock data

**Files:**
- `tests/infrastructure/regions/test_beast_wilds.py` (TestCubsDied, TestCubsHealed, TestBearCommitment)

**Impact:** ~3 failures/errors

**Failing tests:**
- `TestCubsDied::test_cubs_death_makes_bear_vengeful` — ERROR: mock `state_machine` missing `"current"` key
- `TestCubsHealed::test_healing_herbs_heals_cubs`
- `TestBearCommitment::test_commitment_keywords_create_commitment`

**Details:** The mock state_machine dict is set up with `"states"` and `"initial"` but missing `"current"`. The behavior writes to `state_machine["current"]` and gets `KeyError`. This could be a test mock issue or a behavior that should initialize `"current"` from `"initial"`.

---

## GS-5: Sunken District — drowning/breath handlers produce no feedback

**Files:**
- `examples/big_game/game_behaviors/regions/sunken_district/drowning.py`
- `tests/infrastructure/test_sunken_district_scenarios.py` (TestDrowningScenarios)

**Impact:** 4 failures

**Failing tests:**
- `test_breath_warning_at_threshold` — expects "burning" in feedback, gets `''`
- `test_breath_critical_warning` — expects "suffocating", gets `''`
- `test_drowning_damage_at_max` — expects "drowning", gets `''`
- `test_surfacing_resets_breath` — condition `current` stays at 8, expected 0

**Details:** Drowning behavior handlers return empty feedback. Either the handler implementation is incomplete or test expectations need revision.

---

## GS-6: Frozen Reaches — salamander gift feedback

**Files:**
- `examples/big_game/game_behaviors/regions/frozen_reaches/salamanders.py`
- `tests/infrastructure/test_frozen_reaches_scenarios.py` (TestSalamanderScenarios)

**Impact:** 4 failures

**Failing tests:**
- `test_fire_gift_increases_trust`
- `test_first_fire_gift_transitions_to_friendly`
- `test_high_trust_indicates_companion_ready`
- `test_non_fire_gift_rejected`

**Details:** Salamander `on_receive_item` handler returns empty feedback. Same pattern as GS-2 and GS-5.

---

## GS-7: Frozen Reaches — hypothermia conditions format (list vs dict)

**Files:**
- `tests/infrastructure/test_frozen_reaches_scenarios.py` (TestHypothermiaScenarios, TestHotSpringsScenarios)
- `behavior_libraries/actor_lib/conditions.py`

**Impact:** 5 failures/errors

**Failing tests:**
- `test_cold_zone_causes_hypothermia`
- `test_cold_gear_reduces_hypothermia`
- `test_hypothermia_severity_warnings`
- `test_hot_springs_cures_hypothermia` — ERROR: `'list' object has no attribute 'get'`
- `test_hot_springs_without_hypothermia` — ERROR: `'list' object has no attribute 'get'`

**Details:** Tests set up `player.properties["conditions"]` as a list `[{"type": "hypothermia", "severity": 60}]`, but `conditions.py:get_condition()` expects a dict `{"hypothermia": {"severity": 60}}`. The production code uses dict format; tests use list format. Tests need to match production format.

---

## GS-8: Frozen Reaches — E2E navigation routes don't match map topology

**Files:**
- `tests/infrastructure/test_e2e_scenarios.py` (TestE2EFrozenReachesScenarios, TestE2EBeastWildsScenarios)

**Impact:** 6 failures

**Failing tests:**
- `test_navigate_to_wolf_den`
- `test_navigate_to_hot_springs`
- `test_navigate_to_frozen_observatory`
- `test_alpha_wolf_at_den`
- `test_frost_wolves_at_den`
- `test_navigate_to_bee_queen`

**Details:** Test navigation routes don't match actual exit topology in `game_state.json`:
- `frozen_pass → east` goes to `ice_caves`, not `ice_field` as tests expect
- `frozen_pass → north` goes to `temple_sanctum`, not `glacier_approach`
- `exit_glacier_surface_north` has empty connections (`[]`)
- Wolves located at `wolf_clearing` in game_state, tests expect `wolf_den`

---

## GS-9: Fungal Depths — spore mother healing and light puzzle

**Files:**
- `examples/big_game/game_behaviors/regions/fungal_depths/spore_mother.py`
- `examples/big_game/game_behaviors/regions/fungal_depths/light_puzzle.py`
- `tests/infrastructure/regions/test_fungal_depths.py`
- `tests/infrastructure/test_fungal_depths_scenarios.py`

**Impact:** 4 failures/errors

**Failing tests:**
- `TestSporeMother::test_heartmoss_heals_spore_mother` — ERROR: ScenarioState missing `get_item()` method
- `TestLightPuzzle::test_watering_gold_mushroom_increases_light`
- `TestSporeMotherScenarios::test_healing_with_heartmoss` — ERROR: ScenarioState missing `get_item()`
- `TestCombinedFungalScenarios::test_heal_spore_mother_then_meet_myconid` — ERROR

**Details:** Two sub-issues:
1. `ScenarioState` in `test_scenario_framework.py` has `add_item()` but no `get_item()` — spore_mother behavior calls `state.get_item("spore_heart_fragment")`
2. Light puzzle handler not returning expected feedback

---

## GS-10: Consumable healing broken

**Files:**
- `behaviors/core/consumables.py`
- `tests/test_core_behaviors.py` (TestConsumablesBehaviors)
- `tests/test_hardcoded_removal.py` (TestBehaviorDrivenApproach)

**Impact:** 2 failures

**Failing tests:**
- `test_drink_potion_heals`
- `test_potion_with_behavior_heals`

**Details:** Potion consumption doesn't apply healing effect as tests expect.

---

## GS-11: Light source take/put behavior

**Files:**
- `behaviors/core/light_sources.py`
- `tests/test_core_behaviors.py` (TestLightSourcesBehaviors)
- `tests/test_enhanced_containers.py`

**Impact:** 2 failures

**Failing tests:**
- `test_put_lantern_extinguishes`
- `test_take_lantern_from_table`

**Details:** Light source behavior on take/put doesn't produce expected state changes.

---

## GS-12: Entity behavior invocation missing beats

**Files:**
- `tests/test_entity_behavior_invocation.py`

**Impact:** 2 failures

**Failing tests:**
- `test_take_returns_behavior_message`
- `test_drop_returns_behavior_message`

**Details:** Entity-level behavior invocation for take/drop doesn't return expected behavior messages.

---

## GS-13: Examine lock direction changes

**Files:**
- `tests/test_examine_locks.py`

**Impact:** 4 failures

**Failing tests:**
- `test_examine_east_lock`
- `test_lock_llm_context_included`
- `test_find_lock_by_direction`
- `test_find_lock_unhidden_lock_found`

**Details:** Lock examination and direction-based lock finding behavior has changed from what tests expect.

---

## GS-14: Dialog handler missing available_topics

**Files:**
- `tests/infrastructure/test_dialog_topics.py`

**Impact:** 1 failure

**Failing test:**
- `TestDialogHandlerResultData::test_ask_includes_available_topics`

**Details:** Dialog handler result `data` dict doesn't include `available_topics` key. Either the handler needs to populate this or the test expectation is wrong.

---

## GS-15: Dispatcher utils handler escape hatch feedback

**Files:**
- `tests/infrastructure/test_dispatcher_utils.py`
- `tests/infrastructure/test_item_use_reactions.py`
- `tests/infrastructure/test_pack_mirroring.py`

**Impact:** 4 failures

**Failing tests:**
- `TestLoadHandler::test_load_handler_valid_path`
- `TestItemUseReactionsHandlerEscapeHatch::test_target_handler_called`
- `TestItemUseReactionsHandlerEscapeHatch::test_target_handler_takes_precedence`
- `TestItemUseReactionsItemSelfReactions::test_item_self_reaction`
- `TestPackMirroringHandlerEscapeHatch::test_handler_called`
- `TestDialogHandlerEscapeHatch::test_talk_calls_handler`
- `TestItemHandlerEscapeHatch::test_item_handler_called` (gift_reactions)

**Details:** Multiple infrastructure handlers' "escape hatch" (custom handler function) paths return `feedback=None` instead of expected feedback strings. The `load_handler` + dispatch pattern may not be passing feedback through correctly.

---

## GS-16: Cross-region integration handler wiring

**Files:**
- `tests/infrastructure/test_cross_region_integration.py`

**Impact:** 2 failures

**Failing tests:**
- `test_bee_queen_gift_handler_wiring` — uses `bee_queen:on_flower_offer` but function is `on_receive_item`
- `test_salamander_gift_handler_wiring` — uses `salamanders:on_fire_gift` but function is `on_receive_item`

**Details:** Test fixtures hard-code wrong handler function names. The actual game_state.json uses the correct names (`on_receive_item`).

---

## GS-17: Visited locations initialization

**Files:**
- `tests/llm_interaction/test_llm_narrator.py`

**Impact:** 1 failure

**Failing test:**
- `test_narrator_has_visit_tracking_sets`

**Details:** Narrator visit tracking set initialization has changed.

---

## GS-18: Turn phase dispatch (blocked by GS-1)

**Files:**
- `tests/test_turn_phase_dispatch.py`

**Impact:** 11 errors (all blocked by GS-1 waystone loading failure)

**Failing tests:** All tests in TestCommitmentTurnPhase, TestGossipTurnPhase, TestScheduledEventTurnPhase, TestSpreadTurnPhase

**Details:** These tests load big_game behaviors, which fails due to GS-1 (waystone `turn_death_check` dependency). Fixing GS-1 will reveal whether these tests have additional issues or pass cleanly.

---

## GS-19: Treasure chest test expectations vs narration architecture

**Files:**
- `tests/test_core_behaviors.py` (TestContainersBehaviors, TestBehaviorFunctionSignatures)

**Impact:** 2 failures/errors

**Failing tests:**
- `test_open_chest_has_message` — expects "treasure" or "win" in `feedback`, but `on_open` returns `feedback=""` with structured `data` (correct per narration architecture)
- `test_on_open_returns_event_result_for_treasure_chest` — ERROR: Mock player doesn't support `flags["won"]` assignment

**Details:** `containers.py:on_open` follows the narration architecture (returns structured data, not prose). Tests were written expecting prose feedback. The Mock setup also needs `flags` as a real dict.

---

## Not game-specific (tracked elsewhere)

The following failures are general code issues tracked in `fix_categories_1_through_9.md`:
- state_variants serialization (3 failures/errors in test_json_protocol, test_entity_serializer)
- Missing mlx dependency (4 errors in test_llm_command_parser, test_llm_parser_adapter, test_llm_parser_integration)
- Long-path imports in tests (0 current failures, architectural risk)
