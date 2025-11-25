# Game State Manager Implementation Plan

This plan describes how to build a Python module that reads JSON conforming to
`docs/game_state_spec.md`, validates it, exposes strongly-typed objects for
use by the game engine, and can write those objects back to the canonical JSON
format for authoring and save/export workflows.

## 1. Goals & Constraints

* Accept a JSON string or file path and produce an in-memory representation of
  the entire game world.
* Serialize a populated `GameState` object back into spec-compliant JSON (either
  a Python dict or file) with no loss of information.
* Enforce the validation rules from the spec (unique ids, valid references, etc.)
  with clear error messages.
* Provide ergonomic Python objects (dataclasses) that make downstream code easy
  to read and type-check.
* Avoid side effects; parser/serializer should not mutate files or global state
  beyond requested read/write operations.

## 2. Module Structure

```
src/
  state_manager/
    __init__.py
    models.py        # Dataclasses / enums for schema entities
    loader.py        # JSON reading and top-level parse function
    serializer.py    # Convert GameState back to dict/JSON and file outputs
    validators.py    # Reusable validation routines
    exceptions.py    # Custom error types (ValidationError, SchemaError, etc.)
```

## 3. Data Models (models.py)

Define dataclasses/enums mirroring the schema:

* `Metadata`
* `Vocabulary` with alias mapping
* `ExitType` enum (`DOOR`, `OPEN`, `PORTAL`, `SCRIPTED`)
* `ExitDescriptor`
* `Location`
* `Door`
* `ItemType` enum (`TOOL`, `KEY`, `CONTAINER`, etc.)
* `ContainerInfo`
* `Item`
* `Lock`
* `Npc`
* `ScriptTrigger`, `ScriptEffect`, `Script` (optional but future-proof)
* `PlayerState` with location, inventory, flags, stats
* `GameState` aggregate dataclass referencing the above

Each dataclass should support both construction from parsed dictionaries and
serialization back to primitive types (e.g., implement `from_dict`/`to_dict`
classmethods or helper functions). Use nested dataclasses (e.g., `ContainerInfo`
inside `Item`) to keep types clean.

## 4. Loading Flow (loader.py)

1. `load_game_state(source: Union[str, Path, IO]) -> GameState`
   * Accepts file path or stream; detect type and read text.
   * Parse JSON via `json.load`/`json.loads`.

2. `parse_game_state(raw: Dict[str, Any]) -> GameState`
   * Convert each section into typed objects.
   * Defer validation to validators module (but call before constructing final
     `GameState` to avoid storing invalid data).

3. For each section:
   * Metadata: enforce required fields, apply defaults.
   * Vocabulary: ensure alias lists are lists of strings.
   * Locations: iterate `raw["locations"]` array building `Location` objects
     with embedded `ExitDescriptor` instances. Each location must have unique `id` field.
   * Locks: iterate `raw["locks"]` array building `Lock` objects with unique `id` fields.
   * Doors/Items/NPCs/Scripts: map through helper functions to create
     typed objects, each with unique `id` field.
   * Build global ID registry and validate all IDs are globally unique.

**V2.0 ID Design Principles:**

This implementation follows the V2.0 ID namespace design:
* All entity IDs are globally unique across ALL entity types (locations, items, doors, locks, npcs, scripts)
* IDs are internal identifiers separate from user-visible names
* The special ID `"player"` is reserved and cannot be used by any entity
* Item locations use simple ID references with no prefixes:
  * `"loc_1"` - item in that location
  * `"item_5"` - item inside that container
  * `"player"` - item in player inventory (no `"inventory:player"` prefix!)
  * `"npc_3"` - item held by that NPC (no `"inventory:npc_3"` prefix!)
* Locations and locks are stored as arrays (not keyed objects)
* Global ID registry maps all IDs to entity types for validation

## 5. Serialization Flow (serializer.py)

1. `game_state_to_dict(state: GameState) -> Dict[str, Any]`
   * Walk every dataclass and produce the exact schema structure (dicts, lists,
     primitives). Preserve unknown/extra fields captured in the models to avoid
     data loss.
   * Ensure ordering rules (e.g., `locations` keyed object ordering, sorted lists)
     are consistent so diffs remain stable.
2. `save_game_state(state: GameState, destination: Union[str, Path, IO], *, indent=2, sort_keys=False)`
   * Calls `game_state_to_dict`, validates the resulting dict, and writes JSON
     using `json.dump`. Accepts file path or stream.
3. Provide helper `GameState.to_dict()` / `GameState.to_json()` shortcuts that
   defer to serializer functions.

Additional requirements:
* Round-tripping (`load` -> `save`) must yield semantically equivalent JSON.
* Support authoring workflows: allow `game_state_to_dict` to skip validation when
  capturing intermediate edits, but default to validating before disk writes.

## 6. Validation Strategy (validators.py)

Implement reusable validation functions:

* `validate_metadata(metadata, locations)` – check start_location exists
* `build_global_id_registry(game_state)` – build registry mapping all IDs to entity types, checking for duplicates
* `validate_global_uniqueness(registry)` – ensure all IDs globally unique (including reserved `"player"`)
* `validate_references(game_state, registry)` – check all cross-references exist using global registry:
  * `door_id`, `lock_id`, `location`, `contents`, `opens_with`, `exits.to`
  * Item location field (location ID, container ID, "player", or NPC ID)
* `validate_item_locations(items, locations, registry)` – ensure consistency between
  location `items` arrays and item `location` fields; warn or auto-sync.
* `validate_container_cycles(items)` – prevent recursive containment.
* `validate_scripts(scripts, registry)` – check trigger/action reference ids exist in registry.
* `validate_player_state(player, registry)` – check player location and inventory items exist.

**ID Generation:**

Provide helper functions for authoring tools to generate unique IDs:

```python
def generate_id(entity_type: str, counter: int) -> str:
    """Generate sequential prefixed ID (recommended for authored content)."""
    return f"{entity_type}_{counter}"

import uuid
def generate_unique_id(entity_type: str) -> str:
    """Generate UUID-based ID (for runtime/dynamic entities)."""
    return f"{entity_type}_{uuid.uuid4().hex[:8]}"
```

Collect errors and raise a single `ValidationError` with details to help authors.

Example error output format:
```
ValidationError: Found 3 validation errors in game state:
  1. [door:door_1] references unknown lock 'lock_99' (not found in locks)
  2. [item:item_2] location 'item_99' not found in global ID registry
  3. [location:loc_1] lists item 'item_3' but item location is 'loc_2'
```

## 7. Error Handling (exceptions.py)

Define custom exceptions:

* `GameStateError` base class.
* `SchemaError` for missing sections or wrong types.
* `ValidationError` for cross-reference issues (include list of messages).
* `FileLoadError` for IO problems (optional wrapper).

## 8. Testing Plan

* Unit tests per module:
  * `test_models.py` – ensure dataclasses accept expected arguments.
  * `test_loader.py` – round-trip sample JSON files (valid + malformed) into in-memory objects.
  * `test_serializer.py` – verify `GameState` objects serialize back to JSON/dicts, matching fixtures byte-for-byte (after canonical sorting) and preserving all data.
  * `test_validators.py` – synthetic inputs to trigger each validation rule.
  * Integration-style test covering `load -> mutate -> save -> reload` to confirm no information loss.
* Fixture JSONs in `tests/fixtures` (valid world, missing ids, duplicate ids,
  broken references).

## 9. Extensibility Considerations

* Keep dataclasses versioned or include optional `extra` fields to preserve
  unknown keys for future schema additions.
* Provide serialization helpers (e.g., `GameState.to_dict()`) for tooling.
* Consider exposing read-only mapping interfaces to prevent accidental mutation
  (e.g., return `MappingProxyType` for id maps).

## 10. Integration Points

* Parser should integrate with the existing command parser by supplying location
  and item data to drive responses.
* Engine components can subscribe to validation warnings to highlight authoring
  mistakes early (IDE integration).
* Authoring tools and save systems invoke the serializer API to emit canonical
  JSON for edits or runtime checkpoints, guaranteeing that files written by the
  engine can be reloaded without custom post-processing.

Implementing the parser according to this plan ensures the JSON schema defined
in `docs/game_state_spec.md` can be loaded reliably and provides a foundation
for authoring and tooling workflows.
