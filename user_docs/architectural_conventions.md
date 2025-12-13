# Architectural Conventions (Current)

This document captures the coding patterns and interfaces that keep the engine consistent and type-safe. New code and tests should follow these conventions.

---

## 1) Entities and IDs
- Entities are dataclasses in `src/state_manager.py` with strongly typed IDs (`LocationId`, `ActorId`, `ItemId`, `LockId`, `PartId`, `ExitId` from `src.types`).
- Common fields: `id`, `name`, `description`, `properties: Dict[str, Any]`, and `behaviors: List[str]` (list of behavior module names).
- Convenience accessors live on the dataclasses (e.g., `states`, `llm_context`, `container`, `stats`, `flags`, `door_open/locked`, etc.) and should be used instead of digging through `properties`.
- Behavior references are **module lists only**. Legacy `{"event": "module:function"}` shapes are normalized at load time to `["module"]`; new content should declare lists directly.

## 2) IDs, Naming, and Validation
- ID types use `NewType` wrappers; pass the correct type to accessors (e.g., `ActorId("player")`).
- Naming prefixes remain: `loc_` for locations, `item_` for items, `npc_` for NPC actors, `door_` for doors, `lock_` for locks, `part_` for parts, synthesized `exit:loc_id:dir` for exits. The ID `player` is reserved for the human-controlled actor.
- Structural validation happens in `src/validators.py`. Prefer to reuse helpers and keep behaviors as lists to avoid validator warnings.

## 3) Behavior Model
- Behavior modules register vocabulary and protocol handlers (`handle_<verb>`), and expose event handlers (`on_<event>`).
- Entity behaviors are invoked via `BehaviorManager.invoke_behavior(entity, event_name, accessor, context)` and are called with `(entity, game_state, context)`; handlers should mutate the passed entity/state directly.
- `EventResult`: `allow: bool`, `message: Optional[str]`. Multiple handlers combine with AND logic on `allow` and concatenated messages.
- Fallbacks: vocab can register `fallback_event`; invoke will recurse to fallbacks when no handler returns a result.
- Only list-based behaviors are supported in the engine; dict-based event mappings are for legacy normalization only.

## 4) Command Handlers and State Changes
- Command handlers have signature `handle_<verb>(accessor: StateAccessor, action: ActionDict) -> HandlerResult`.
- `ActionDict` (see `src/action_types.py`) carries structured fields: `verb`, `object`, `adjective`, `actor_id`, `direction`, `preposition`, `indirect_object`, `indirect_adjective`.
- Use `StateAccessor.update(entity, changes, verb=..., actor_id=...)` for mutations; it invokes behaviors first, applies changes, and returns `UpdateResult` with `success/message`.
- `HandlerResult`: `success: bool`, `message: Optional[str]`, `data: Optional[Dict[str, Any]]`.
- Never mutate `GameState` directly; go through `StateAccessor` methods for reads and writes.

## 5) Vocabulary and Parsing
- Base vocab comes from `src/vocabulary_service.load_base_vocabulary`; merged vocab is built with `build_merged_vocabulary(game_state, behavior_manager)` (base + extracted nouns + behavior vocab).
- `Parser.from_vocab(vocabulary_dict)` is the standard constructor when a merged vocab is already available; it accepts a dict or a file path for legacy cases.
- Word entries: see `src/word_entry.py`. Multi-type words use sets; directions live in vocab with multi-typed word_types.

## 6) Typing and Tooling
- mypy is required and runs with strict options for core modules and utilities; add type annotations for new code, avoid broad `Any`, and prefer narrow `cast` with justification.
- Dev commands: `make mypy`, `make test`, `make check` (runs mypy + unittest). Dev deps live in `requirements-dev.txt`.
- Tests that require a display are pinned to headless mode (`tests/test_file_dialogs.py` sets `HAS_DISPLAY = False`); keep GUI-dependent code behind opt-in flags.

## 7) Serialization and Persistence
- `load_game_state` normalizes behaviors to lists and merges legacy property shapes into `properties`. Keep new fixtures and content in the normalized format.
- `game_state_to_dict` preserves behaviors as lists and merges `properties` back to top-level fields; when adding fields, ensure serializers and validators stay in sync.

## 8) LLM / Protocol Integration
- `LLMProtocolHandler` is the single protocol surface; it uses the behavior manager for post-command hooks and turn phases.
- Vocabulary queries (`_query_vocabulary`) use the merged vocabulary via `vocabulary_service`; avoid ad hoc vocab loads.
- Narration uses `LLMNarrator` with `Parser.from_vocab` and the merged vocab passed in; keep prompt loading separate from vocab loading.
