# Current Test Failures

Generated: 2026-01-13
Summary: 26 failed, 48 errors (LLM parser), 2886 passed

## Fixed This Session
- Cross-region integration tests (6 tests) - Fixed pytest module cleanup hook
- Cross-region scenarios tests (14 tests) - Fixed with proper cleanup
- Condition system tests (11 tests) - Fixed with cleanup, no longer polluted

## Errors (48) - LLM Parser Tests

These all fail with import/setup errors (likely missing LLM config):
- test_game_engine_llm_parser.py (5 errors)
- test_llm_command_parser.py (17 errors)
- test_llm_parser_adapter.py (16 errors)
- test_llm_parser_integration.py (10 errors)

## Remaining Failures (26)

### Handler Escape Hatch Tests (7)
All test custom handler loading via `load_handler()`:
- test_death_reactions.py::TestDeathReactionsHandlerEscapeHatch::test_handler_called
- test_dialog_reactions.py::TestDialogReactionsHandlerEscapeHatch::test_handler_escape_hatch_called
- test_dispatcher_utils.py::TestLoadHandler::test_load_handler_valid_path
- test_gift_reactions.py::TestGiftReactionsHandlerEscapeHatch::test_handler_escape_hatch_called
- test_item_use_reactions.py::TestItemUseReactionsHandlerEscapeHatch::test_item_handler_called
- test_item_use_reactions.py::TestItemUseReactionsHandlerEscapeHatch::test_target_handler_called
- test_item_use_reactions.py::TestItemUseReactionsHandlerEscapeHatch::test_target_handler_takes_precedence
- test_pack_mirroring.py::TestPackMirroringHandlerEscapeHatch::test_handler_called

### Item Use / Gift Reactions (2)
- test_gift_reactions.py::TestGiftReactionsDataDriven::test_track_items_key
- test_item_use_reactions.py::TestItemUseReactionsItemSelfReactions::test_item_self_reaction

### Fungal Depths (2)
- test_fungal_depths.py::TestSporeMother::test_heartmoss_heals_spore_mother
- test_fungal_depths.py::TestLightPuzzle::test_watering_gold_mushroom_increases_light

### Lock Examination (4)
- test_examine_locks.py::TestExamineLockWithDirection::test_examine_east_lock
- test_examine_locks.py::TestExamineLockLLMContext::test_lock_llm_context_included
- test_examine_locks.py::TestFindLockByContext::test_find_lock_by_direction
- test_examine_locks.py::TestFindLockByContext::test_find_lock_unhidden_lock_found

### Exit Migration (3)
- test_exit_migration.py::TestExitMigration::test_connection_mapping_bidirectional
- test_exit_migration.py::TestExitMigration::test_doors_migration
- test_exit_migration.py::TestExitMigration::test_simple_exits_migration

### Interaction Handlers (5)
- test_handler_llm_context.py::TestInteractionHandlersLlmContext::test_handle_use_returns_llm_context
- test_interaction_handlers.py::TestHandleUse::test_use_item_not_found
- test_interaction_handlers.py::TestHandleUse::test_use_item_success
- test_interaction_handlers.py::TestUseWithAdjective::test_use_with_adjective_selects_correct_item
- test_interaction_handlers.py::TestUseWithAdjective::test_use_with_different_adjective_selects_other_item

### Protocol/Services (2)
- test_protocol_behaviors.py::TestProtocolBehaviorCommands::test_use_command_invokes_on_use
- test_services_system.py::TestExecuteService::test_execute_service_cure

## Categories Summary

| Category | Count | Notes |
|----------|-------|-------|
| LLM Parser (errors) | 48 | Config/dependency issue, separate concern |
| Handler Escape Hatch | 8 | All use load_handler(), likely need architecture fix |
| Interaction Handlers | 5 | Use command handling |
| Lock Examination | 4 | Lock finding/context |
| Exit Migration | 3 | Migration tool tests |
| Fungal Depths | 2 | Heartmoss, light puzzle mechanics |
| Item Use/Gift | 2 | Data-driven reactions |
| Protocol/Services | 2 | Use command, cure service |
