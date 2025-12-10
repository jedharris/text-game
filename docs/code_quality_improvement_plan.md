# Code Quality Improvement Plan (Next Steps)

This document outlines the next set of code quality improvements, with scope, dependencies, impact, and risks for each item.

## 1) Tighten Mypy Incrementally
**Scope:** Enable stricter mypy settings in stages: first `warn_return_any`, then `disallow_untyped_defs` module-by-module (start with `src/llm_protocol.py`, `src/behavior_manager.py`, `src/state_accessor.py`, `src/parser.py`). Add any missing type stubs/aliases needed to keep signal-to-noise acceptable.

**Dependencies:** Current type aliases (`ActionDict`, `ResultMessage`, `HandlerCallable`, `WordTypeLike`), and an agreed baseline config in `mypy.ini`.

**Maintainability impact:** Earlier detection of interface drift between parser → protocol → behaviors; fewer “Any” escape hatches reduces regression risk.

**Risks:** Noise from legacy patterns; potential churn if we apply `disallow_untyped_defs` too broadly at once. Mitigate by tackling one module at a time and adding targeted ignores only where justified.

## 2) Align Action/Result Types End-to-End
**Scope:** Ensure all callers construct actions/results through shared helpers or constructors (no ad hoc dicts). Introduce small factory helpers for `ActionDict`/`ResultMessage` to remove hand-written literals in CLI runners and tests. Update behaviors’ handler signatures to a shared protocol where practical.

**Dependencies:** Existing `ActionDict`/`ResultMessage` TypedDicts and `HandlerCallable` protocol; shared helper `parsed_to_json`.

**Maintainability impact:** Reduces subtle shape mismatches; improves readability and makes refactors (e.g., adding fields) safer.

**Risks:** Minor refactor churn across tests and runners; need to keep behavior handler signatures consistent. Mitigate with incremental edits and test coverage (unit/integration).

## 3) Retire Dict-Based Behavior Invocation
**Scope:** Remove the legacy dict-based behavior path in `BehaviorManager._invoke_behavior_internal` if no fixtures rely on it. Confirm via repo search/tests that behaviors are list-based. Add a guard/unit test asserting `invoke_handler` returns a `HandlerResult` for registered verbs.

**Dependencies:** Behavior fixtures remaining on the new list-based model; confirmation that test fixtures using dict behaviors are only for compatibility tests (and can be reworked or isolated).

**Maintainability impact:** Simplifies behavior invocation logic; fewer code paths to maintain and reason about.

**Risks:** If any game/fixture still uses the dict format, removing support breaks it. Mitigate with a targeted search and, if needed, a shim for tests only.

## 4) Parser and Word Typing Hygiene
**Scope:** Add `WordTypeLike` alias; annotate `WordEntry.word_type` accordingly; tighten parser return/field types and remove `Any` seepage. Add parser-focused tests for prepositions/adjectives/directions to lock behavior.

**Dependencies:** Current parser/word_entry structures; minor test additions.

**Maintainability impact:** Clearer intent in parsing logic; easier to evolve vocabulary handling; reduces runtime type checks.

**Risks:** Low—primarily test updates if edge behaviors change. Mitigate with focused parser tests.

## 5) Serialization and LLM Context Consistency
**Scope:** Ensure entity/door/location serialization flows through `utilities.entity_serializer` (or a single serializer) and remove any remaining custom llm_context shims if unused. Align protocol outputs with serializer shapes.

**Dependencies:** Current serializer utilities; knowledge of any consumers expecting legacy shapes.

**Maintainability impact:** One serialization path reduces drift and accidental divergence between responses and tests/docs.

**Risks:** Breaking consumers relying on legacy fields/order. Mitigate by auditing consumers (tests, docs) and providing a small compatibility layer if necessary.

## 6) CI/Tooling Hooks
**Scope:** Add a simple task runner (makefile or script) for `python -m unittest` and `mypy`. Integrate mypy into CI with the stricter flags as they land. Optionally add formatting/linting hooks if desired.

**Dependencies:** Agreed mypy settings; existing test suite.

**Maintainability impact:** Makes it easy to run the exact checks used for commits/PRs; reduces “works on my machine” drift.

**Risks:** Minimal. Ensure commands are fast or scoped to avoid slowing dev loops; allow opt-outs for large refactors.
