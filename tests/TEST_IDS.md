# Test ID Reference

Quick reference for all test IDs defined in test-plan.md.

## Category 1: WordEntry Class (WE-*) ✅ COMPLETE

| Test ID | Test Name | Status |
|---------|-----------|--------|
| WE-001 | test_word_entry_creation | ✅ PASSING |
| WE-002 | test_word_entry_no_synonyms | ✅ PASSING |
| WE-003 | test_word_entry_no_value | ✅ PASSING |
| WE-004 | test_word_type_enum | ✅ PASSING |
| WE-005 | test_word_entry_equality | ✅ PASSING |
| WE-006 | test_word_entry_string_repr | ✅ PASSING |

**Additional Tests**: 12 extra tests implemented - ALL PASSING
**Total Tests**: 18/18 passing in 0.000s

## Category 2: Vocabulary Loading (VL-*)

| Test ID | Test Name | Status |
|---------|-----------|--------|
| VL-001 | test_load_complete_vocabulary | ⏳ Pending |
| VL-002 | test_load_minimal_vocabulary | ⏳ Pending |
| VL-003 | test_load_empty_vocabulary | ⏳ Pending |
| VL-004 | test_load_missing_file | ⏳ Pending |
| VL-005 | test_load_invalid_json | ⏳ Pending |
| VL-006 | test_verb_synonyms_loaded | ⏳ Pending |
| VL-007 | test_direction_synonyms_loaded | ⏳ Pending |
| VL-008 | test_preposition_loading | ⏳ Pending |
| VL-009 | test_article_loading | ⏳ Pending |
| VL-010 | test_value_field_optional | ⏳ Pending |
| VL-011 | test_missing_sections | ⏳ Pending |
| VL-012 | test_word_table_size | ⏳ Pending |

## Category 3: Word Lookup (WL-*)

| Test ID | Test Name | Status |
|---------|-----------|--------|
| WL-001 | test_lookup_exact_match | ⏳ Pending |
| WL-002 | test_lookup_synonym | ⏳ Pending |
| WL-003 | test_lookup_unknown_word | ⏳ Pending |
| WL-004 | test_lookup_case_insensitive | ⏳ Pending |
| WL-005 | test_lookup_direction_synonym | ⏳ Pending |
| WL-006 | test_lookup_multiple_synonyms | ⏳ Pending |
| WL-007 | test_lookup_preposition | ⏳ Pending |
| WL-008 | test_lookup_article | ⏳ Pending |
| WL-009 | test_lookup_adjective | ⏳ Pending |

## Category 4: Pattern Matching 1-2 Words (PM-001 to PM-006)

| Test ID | Test Name | Status |
|---------|-----------|--------|
| PM-001 | test_single_direction | ⏳ Pending |
| PM-002 | test_direction_synonym | ⏳ Pending |
| PM-003 | test_verb_noun | ⏳ Pending |
| PM-004 | test_verb_direction | ⏳ Pending |
| PM-005 | test_verb_direction_synonym | ⏳ Pending |
| PM-006 | test_synonym_verb_noun | ⏳ Pending |

## Category 5: Pattern Matching 3 Words (PM-101 to PM-105)

| Test ID | Test Name | Status |
|---------|-----------|--------|
| PM-101 | test_verb_adjective_noun | ⏳ Pending |
| PM-102 | test_verb_noun_noun | ⏳ Pending |
| PM-103 | test_verb_prep_noun | ⏳ Pending |
| PM-104 | test_verb_adj_noun_colors | ⏳ Pending |
| PM-105 | test_verb_adj_noun_size | ⏳ Pending |

## Category 6: Pattern Matching 4 Words (PM-201 to PM-203)

| Test ID | Test Name | Status |
|---------|-----------|--------|
| PM-201 | test_verb_adj_noun_noun | ⏳ Pending |
| PM-202 | test_verb_noun_prep_noun | ⏳ Pending |
| PM-203 | test_verb_prep_adj_noun | ⏳ Pending |

## Category 7: Pattern Matching 5-6 Words (PM-301 to PM-305)

| Test ID | Test Name | Status |
|---------|-----------|--------|
| PM-301 | test_verb_adj_noun_prep_noun | ⏳ Pending |
| PM-302 | test_verb_noun_prep_adj_noun | ⏳ Pending |
| PM-303 | test_verb_adj_noun_prep_adj_noun | ⏳ Pending |
| PM-304 | test_complex_color_adjectives | ⏳ Pending |
| PM-305 | test_complex_size_adjectives | ⏳ Pending |

## Category 8: Article Filtering (AF-*)

| Test ID | Test Name | Status |
|---------|-----------|--------|
| AF-001 | test_filter_the | ⏳ Pending |
| AF-002 | test_filter_a | ⏳ Pending |
| AF-003 | test_filter_an | ⏳ Pending |
| AF-004 | test_multiple_articles | ⏳ Pending |
| AF-005 | test_article_with_adjective | ⏳ Pending |
| AF-006 | test_article_complex | ⏳ Pending |
| AF-007 | test_no_article | ⏳ Pending |

## Category 9: Error Handling (EH-*)

| Test ID | Test Name | Status |
|---------|-----------|--------|
| EH-001 | test_unknown_word | ⏳ Pending |
| EH-002 | test_invalid_pattern | ⏳ Pending |
| EH-003 | test_empty_input | ⏳ Pending |
| EH-004 | test_whitespace_only | ⏳ Pending |
| EH-005 | test_single_unknown | ⏳ Pending |
| EH-006 | test_partial_unknown | ⏳ Pending |
| EH-007 | test_all_articles | ⏳ Pending |
| EH-008 | test_noun_only | ⏳ Pending |
| EH-009 | test_adjective_only | ⏳ Pending |
| EH-010 | test_preposition_only | ⏳ Pending |
| EH-011 | test_two_verbs | ⏳ Pending |
| EH-012 | test_two_directions | ⏳ Pending |

## Category 10: Edge Cases (EC-*)

| Test ID | Test Name | Status |
|---------|-----------|--------|
| EC-001 | test_extra_whitespace | ⏳ Pending |
| EC-002 | test_leading_whitespace | ⏳ Pending |
| EC-003 | test_trailing_whitespace | ⏳ Pending |
| EC-004 | test_mixed_case | ⏳ Pending |
| EC-005 | test_uppercase_input | ⏳ Pending |
| EC-006 | test_tab_characters | ⏳ Pending |
| EC-007 | test_very_long_command | ⏳ Pending |
| EC-008 | test_too_many_words | ⏳ Pending |
| EC-009 | test_special_characters | ⏳ Pending |
| EC-010 | test_numbers_in_input | ⏳ Pending |
| EC-011 | test_unicode_input | ⏳ Pending |
| EC-012 | test_raw_field_preserved | ⏳ Pending |

## Category 11: Integration Tests (IT-*)

| Test ID | Test Name | Status |
|---------|-----------|--------|
| IT-001 | test_full_game_scenario_1 | ⏳ Pending |
| IT-002 | test_full_game_scenario_2 | ⏳ Pending |
| IT-003 | test_exploration_scenario | ⏳ Pending |
| IT-004 | test_inventory_scenario | ⏳ Pending |
| IT-005 | test_puzzle_scenario | ⏳ Pending |
| IT-006 | test_parser_reuse | ⏳ Pending |
| IT-007 | test_synonym_consistency | ⏳ Pending |

## Category 12: Performance Tests (PF-*)

| Test ID | Test Name | Status |
|---------|-----------|--------|
| PF-001 | test_single_parse_speed | ⏳ Pending |
| PF-002 | test_1000_parses | ⏳ Pending |
| PF-003 | test_large_vocabulary | ⏳ Pending |
| PF-004 | test_worst_case_lookup | ⏳ Pending |
| PF-005 | test_memory_usage | ⏳ Pending |
| PF-006 | test_synonym_lookup_speed | ⏳ Pending |

## Category 13: Regression Tests (RG-*)

| Test ID | Test Name | Status |
|---------|-----------|--------|
| RG-001 | test_issue_XXX | ⏳ Pending |

## Summary

- **Total Tests Planned**: 100+
- **Tests Implemented**: 18 (Category 1 complete + extras)
- **Tests Passing**: 18/18 (100%)
- **Tests Pending**: 82+
- **Categories Complete**: 1/13
- **Overall Progress**: ~18%

## Legend

- ✅ PASSING - Test implemented and passing
- ✅ Implemented - Test code written and ready to run
- ⏳ Pending - Not yet implemented
- ✗ Failing - Test implemented but failing
- ⊗ Skipped - Test temporarily disabled

---

Last Updated: 2025-11-16
