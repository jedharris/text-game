# Cleanup Plan – Next Steps

This document outlines follow-on cleanup tasks, ordered to minimize churn and untangle dependencies.

## 1) Type Expansion Beyond Core *(Completed)*
**Scope:** Add parameter/return types and eliminate `Any` returns in:
- `src/state_manager.py` (helpers for validation, serialization, getters)
- `utilities/entity_serializer.py` (entity/door/location serialization helpers)
- `utilities/utils.py` (dict/list helpers with loose typing)

**Approach:** Tackle one file at a time; add per-file mypy strictness (`warn_return_any`, `disallow_untyped_defs`) once clean. Avoid broad ignores; use narrow `cast` with comments if unavoidable.

**Impact/Risks:** Improves static safety; low risk, but may expose hidden assumptions. Mitigate with targeted unit tests where behavior could change.

**Status/Notes:** Strict mypy is now enabled for all three modules, with `utilities/utils.py` fully typed and the global exclude removed. `python -m mypy src utilities` and the full unittest suite both pass.

## 2) Behavior Path Simplification
**Scope:** Remove or isolate the legacy dict-based behavior path in `BehaviorManager._invoke_behavior_internal`. Confirm no real game content depends on it (tests/fixtures only).

**Approach:** Search for dict-based `behaviors` usage; if only compatibility tests, adjust them or quarantine the path behind a flag. Otherwise, document and leave a thin shim.

**Impact/Risks:** Simplifies behavior invocation; risk of breaking legacy fixtures. Mitigate with repo-wide search and a compatibility toggle if needed.

**Status/Notes:** BehaviorManager now only invokes list-based modules. The state loader normalizes legacy `{"event": "module:function"}` entries to module lists, and tests/fixtures were updated accordingly. Core behavior tests and protocol integration tests pass on the new path.

## 3) Parser Factory Cleanup *(Completed)*
**Scope:** Formalize in-memory parser creation (e.g., `Parser.from_vocab`) and deprecate ad hoc file/dict handling in code paths.

**Approach:** Add a classmethod factory and update callers to use it. Keep current `__init__` signature for backward compatibility.

**Impact/Risks:** Minor code clarity gains; low risk.

**Status/Notes:** `Parser.from_vocab` added and adopted by engine, narrator, and examples so the shared merged vocab path is explicit and file IO is avoided when callers already have a dict.

## 4) Vocabulary Service Adoption Consistency *(Completed)*
**Scope:** Ensure all vocab loading/merging uses `vocabulary_service` where appropriate; document any intentional exceptions (tests/fixtures).

**Approach:** Audit remaining vocab reads (tests, utilities) and switch to service or note exceptions. Remove duplicate base-vocab reads if redundant.

**Impact/Risks:** Reduces drift in vocab handling; low risk.

**Status/Notes:** Protocol vocabulary queries now use `build_merged_vocabulary` (base + extracted nouns + behaviors) instead of ad hoc base loads. Tests/fixtures that load vocab files directly remain as intentional fixtures.

## 5) Docs/Tests Alignment *(Completed)*
**Scope:** Update docs (`code_quality_analysis.md`, typing docs) to reflect completed work and current strictness settings; add a note in tests about wx dialog skip for future CI planning.

**Approach:** Edit docs with concise status/next steps; add inline comment in `tests/test_file_dialogs.py` about the permanent skip rationale.

**Impact/Risks:** Documentation-only; low risk.

**Status/Notes:** Added permanent headless note to `tests/test_file_dialogs.py`; cleanup plan reflects current status.

## 6) CI Prep (Deferred)
**Scope:** Prepare for future CI by adding `requirements-dev.txt` with test/typing deps and documenting the `make check` flow; defer enabling Actions until needed.

**Approach:** Create/dev requirements file; ensure Makefile matches; leave workflow creation for later.

**Impact/Risks:** Low; speeds up future CI setup.

**Status/Notes:** Added `requirements-dev.txt` (mypy, typing_extensions, wxPython) and aligned Makefile `mypy` target with `utilities/`. CI workflow still intentionally deferred.
