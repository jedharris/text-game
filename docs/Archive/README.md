# Archive

This directory contains obsolete or implementation-focused documentation that is no longer actively maintained.

## Archived Files

### Test Isolation Documentation (January 2026)

These documents were created during the test suite cleanup to diagnose and fix module cache pollution issues. The problems have been resolved and the patterns are now documented in the active guides.

- **test_isolation_analysis.md** - Analysis of test isolation patterns (superseded by test_style_guide.md)
- **test_isolation_root_cause.md** - Technical deep dive into module cache pollution (superseded by test_style_guide.md)
- **test_module_cleanup.md** - Implementation notes on cleanup patterns (superseded by test_style_guide.md)
- **integration_testing.md** - Integration test structure (consolidated into test_style_guide.md)

### Phase 4 State Variant Design (January 2026)

Design document for state variant selection in location narration.

- **phase4_state_variant_design.md** - Design for Context Builder state variant selection based on environmental spreads, quest flags, and visit history

### Why Archived?

**Test Isolation Docs:**
- **Obsolete:** Problems have been fixed, patterns documented in active guides
- **Implementation-focused:** Details of the cleanup work, not ongoing reference material
- **Superseded:** Content consolidated into test_style_guide.md

**State Variant Design:**
- **Fully Implemented:** All components built and tested
  - `utilities/state_variant_selector.py` - Priority-based selection logic
  - `utilities/location_serializer.py` - Integration with Context Builder
  - `tests/test_state_variant_selector.py` - 15 tests, all passing
  - Used extensively in `examples/big_game/game_state.json` (106 occurrences)
- **Reference available:** Code is self-documenting with comprehensive docstrings
- **Design decisions preserved:** Module comments reference this design doc

## Active Documentation

For current documentation, see:

- **docs/Guides/claude_session_guide.md** - Essential patterns and gotchas for new sessions
- **docs/Guides/test_authoring_guide.md** - Quick test authoring reference
- **docs/Guides/test_style_guide.md** - Complete test style guide with troubleshooting
- **docs/Guides/quick_reference.md** - API reference and common utilities
- **docs/Guides/authoring_guide.md** - Handler patterns and walkthrough testing
- **docs/Guides/debugging_guide.md** - Vocabulary, parsing, and error diagnosis
