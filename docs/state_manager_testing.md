# State Manager Test Plan

This document outlines the comprehensive test strategy for the game state manager
described in `docs/state_manager_plan.md`. It ensures the manager correctly loads,
validates, and materializes game state JSON defined in `docs/game_state_spec.md`.

## 1. Test Objectives

1. Verify that valid JSON documents produce equivalent Python objects (dataclasses).
2. Confirm all validation rules are enforced with actionable error messages.
3. Exercise error pathways for malformed JSON, missing sections, type mismatches,
   and file IO issues.
4. Validate extensibility behavior: unknown keys are preserved and do not break
   parsing.
5. Ensure serialization faithfully reproduces the canonical JSON structure so
   `GameState` objects can be written out for authoring/saves.
6. Guarantee lossless round-tripping (`JSON -> GameState -> JSON`) by comparing
   outputs against source fixtures (allowing for canonical ordering).
7. Ensure future schema additions can be tested quickly via fixtures and helper
   utilities.

## 2. Test Suite Organization

```
tests/state_manager/
  __init__.py
  fixtures/
    valid_world.json
    minimal_world.json
    valid_world_canonical.json   # expected serializer output (sorted)
    missing_sections.json
    duplicate_ids.json
    bad_references.json
    container_cycle.json
    invalid_exits.json
    invalid_locks.json
    invalid_scripts.json
    invalid_player_state.json
    global_id_collision.json
    reserved_id_violation.json
    invalid_item_location.json
  test_loader.py
  test_serializer.py
  test_models.py
  test_validators.py
  test_error_handling.py
  test_regressions.py
```

Fixtures represent canonical scenarios; tests should never mutate fixture files.

## 3. Tests by Module

### 3.1 Loader Tests (`test_loader.py`)

* **TL-001** Load full fixture from file path.
  * Expect `GameState` instance with correct counts (locations, items, etc.).
* **TL-002** Load from file-like object (StringIO) to ensure API flexibility.
* **TL-003** Load minimal world: ensures defaults (empty optional sections) work.
* **TL-004** Unknown top-level keys preserved via object extra fields.
* **TL-005** Invalid JSON format raises `SchemaError` (wrap `json.JSONDecodeError`).
* **TL-006** Missing file path triggers `FileLoadError`.
* **TL-007** Loader accepts already-parsed dict (bypass file IO) for embedding.

Assertions:
* Type checking for all nested dataclasses.
* Equality with expected values (e.g., `metadata.start_location`).

### 3.2 Serializer Tests (`test_serializer.py`)

* **TS-001** Serialize `GameState` built from `valid_world.json` to dict and compare
  to loaded JSON (after canonical sorting). Ensures no fields are dropped.
* **TS-002** Serialize to JSON string with pretty-print settings; verify indentation
  and stable key ordering (use `valid_world_canonical.json` as golden file).
* **TS-003** Save to temporary file path and re-load to confirm file IO path works.
* **TS-004** Serialization of intermediate/partial states with preserved extras
  (unknown keys) remains intact when reloaded.
* **TS-005** Error when attempting to serialize invalid `GameState` (e.g., missing
  required metadata) if validation-before-save is enabled.

Assertions:
* Every entity's custom fields/unknown data round-trip accurately.
* No additional fields are introduced; ordering remains deterministic.

### 3.3 Model Tests (`test_models.py`)

* **TM-001** Dataclass field defaults (e.g., `ExitDescriptor.hidden` default False).
* **TM-002** Container items correctly reference `ContainerInfo`.
* **TM-003** Enum string conversion (e.g., `ExitType.from_str` if implemented).
* **TM-004** Round-trip serialization if `to_dict()` helpers exist.
* **TM-005** Items with states dictionary maintain values and types.

### 3.4 Validator Tests (`test_validators.py`)

Test each rule independently using synthetic data to isolate failures:

* **TV-001** Global ID uniqueness: duplicate IDs across any entity types raise `ValidationError`.
* **TV-002** Global ID uniqueness: location ID colliding with item ID raises error.
* **TV-003** Reserved ID validation: entity using ID `"player"` raises error (reserved).
* **TV-004** Reference resolution: exit `to` referencing nonexistent location.
* **TV-005** Door references: exit referencing missing door id.
* **TV-006** Lock references: door requests undefined `lock_id`.
* **TV-007** Item location consistency: mismatch between location `items` list and
  item `location` field produces error (or warning, depending on design).
* **TV-008** Container cycles: item containing itself or circular containment.
* **TV-009** Start location validation: metadata points to missing location.
* **TV-010** Vocabulary alias validation: ensure alias arrays contain strings.
* **TV-011** Script validation: triggers referencing nonexistent ids (locations,
  items, locks) produce validation errors.
* **TV-012** Door/exit one-way conditions: ensure doors with one location specify
  direction-specific metadata.
* **TV-013** PlayerState validation: player location must exist in locations.
* **TV-014** PlayerState inventory validation: all inventory item ids must exist in items.
* **TV-015** Item location validation: item location `"player"` is valid (player inventory).
* **TV-016** Item location validation: item location referencing NPC ID validates NPC exists.
* **TV-017** Item location validation: item location referencing container ID validates container exists and has `container` field.
* **TV-018** Item location validation: item location referencing invalid ID type raises error.

For each, confirm `ValidationError` message includes the offending id for
author-friendly debugging.

### 3.5 Error Handling Tests (`test_error_handling.py`)

* **TE-001** Multiple validation errors aggregated into single exception object.
* **TE-002** Schema error for missing required sections (e.g., `metadata` absent).
* **TE-003** Type mismatch (e.g., `locations` not an object) triggers schema-level
  exception before validation.
* **TE-004** Non-string keys in `locations` raise clear error.
* **TE-005** Logging or diagnostic output (if any) is produced for warnings; ensure
  warnings are optional and do not abort parsing.

### 3.6 Regression & Integration Tests (`test_regressions.py`)

* **TR-001** Realistic world fixture (matching `docs/example_game_state.md`)
  loaded end-to-end and compared against stored snapshot (counts, ids).
* **TR-002** Caching behavior (if loader caches parsed files) works across repeated
  loads.
* **TR-003** Forward compatibility: fixture with extra fields is parsed and extra
  data remains accessible.
* **TR-004** Full round-trip: load `valid_world.json`, serialize to temp file, reload
  serialized output, and assert deep equality (locations, items, raw dict) to
  guarantee no loss of information or formatting errors beyond permitted ordering.

## 4. Negative Test Matrix

| Scenario | Expected Exception | Fixture |
|----------|--------------------|---------|
| Missing `metadata` | `SchemaError` | `missing_sections.json` |
| Duplicate IDs across entity types | `ValidationError` | `global_id_collision.json` |
| Entity using reserved ID "player" | `ValidationError` | `reserved_id_violation.json` |
| Exit pointing to invalid location | `ValidationError` | `bad_references.json` |
| Door referencing undefined lock | `ValidationError` | `invalid_locks.json` |
| Container containing itself | `ValidationError` | `container_cycle.json` |
| Scripts referencing missing door | `ValidationError` | `invalid_scripts.json` |
| Item location pointing to invalid ID | `ValidationError` | `invalid_item_location.json` |
| Serialize invalid in-memory state | `ValidationError` | derived from `bad_references.json` |
| Malformed JSON | `SchemaError` | corrupt fixture |
| Non-existent file path | `FileLoadError` | path to missing file |

## 5. Fixture Guidelines

* Fixtures should be minimal but sufficient to trigger the targeted behavior.
* Use comments in companion `.md` files to explain intent (cannot embed comments
  in JSON).
* Provide both valid and invalid variants for each structural feature (doors,
  containers, scripts).
* Maintain canonical-output fixtures (e.g., `valid_world_canonical.json`) that
  represent the serializer's expected pretty-printed format; update snapshots only
  when intentional changes to output occur.

## 6. Automation & CI

* Add `python -m unittest discover tests/state_manager` to CI pipeline.
* Consider running `jsonschema` validation (if a schema is generated) as a
  secondary check.
* Include a golden-file diff step to ensure serializer output for `valid_world.json`
  matches `valid_world_canonical.json` on every run (prevents silent format drift).
* Track coverage metrics; aim for >95% coverage across loader/validator modules.

## 7. Tooling Support

* Provide helper functions inside tests to load fixtures (e.g., `load_fixture(name)`).
* Use custom assertions to compare error lists to avoid brittle string matching.

## 8. Future Enhancements

* Property-based tests (Hypothesis) to generate random game states and ensure
  parser robustness.
* Snapshot tests for serialized outputs when exporting `GameState` back to JSON.
* Integration tests combined with the command parser to ensure the game engine can
  traverse the parsed world without runtime errors.

Adhering to this plan will ensure the state parser is reliable, debuggable, and
ready for future schema evolution.
