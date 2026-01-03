# Archive

This directory contains obsolete or implementation-focused documentation that is no longer actively maintained.

## Archived Files

### Test Isolation Documentation (January 2026)

These documents were created during the test suite cleanup to diagnose and fix module cache pollution issues. The problems have been resolved and the patterns are now documented in the active guides.

- **test_isolation_analysis.md** - Analysis of test isolation patterns (superseded by test_authoring_guide.md)
- **test_isolation_root_cause.md** - Technical deep dive into module cache pollution (superseded by test_style_guide.md)
- **test_module_cleanup.md** - Implementation notes on cleanup patterns (superseded by test_authoring_guide.md)
- **integration_testing.md** - Integration test structure (consolidated into test_style_guide.md)

### Why Archived?

- **Obsolete:** Problems have been fixed, patterns documented in active guides
- **Implementation-focused:** Details of the cleanup work, not ongoing reference material
- **Superseded:** Content consolidated into test_authoring_guide.md and test_style_guide.md

## Active Documentation

For current documentation, see:

- **docs/Guides/claude_session_guide.md** - Essential patterns and gotchas for new sessions
- **docs/Guides/test_authoring_guide.md** - Quick test authoring reference
- **docs/Guides/test_style_guide.md** - Complete test style guide with troubleshooting
- **docs/Guides/quick_reference.md** - API reference and common utilities
- **docs/Guides/authoring_guide.md** - Handler patterns and walkthrough testing
- **docs/Guides/debugging_guide.md** - Vocabulary, parsing, and error diagnosis
