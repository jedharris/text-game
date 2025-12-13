# Code Quality Analysis & Improvement Plan

Context: focused review on typing completeness, redundant code paths, removal of legacy/back-compat scaffolding, and structural simplification. No code changes were made; this is an actionable plan.

## Typing Gaps & Consistency
- The JSON protocol surface still uses `dict[str, Any]` throughout `src/llm_protocol.py` and `src/llm_narrator.py`; `ActionDict` in `src/action_types.py` is not leveraged, forcing `_convert_action_strings_to_wordentry` to clean up inputs. Introduce TypedDicts (or dataclasses) for commands/queries/responses and pass `ActionDict` end-to-end to drop the conversion shim.
- Handler call signatures in `src/behavior_manager.py` are untyped callables and tuples of `Any`. Define handler and behavior function protocols (e.g., `Callable[[StateAccessor, ActionDict], HandlerResult]`) to align with `StateAccessor.HandlerResult` and surface mypy errors where handlers diverge.
- `src/game_engine.py`, `src/llm_narrator.py`, and `src/text_game.py` expose many untyped returns/attributes (e.g., `create_narrator`, `_call_llm`, `process_turn`, `reload_state`), and sets like `visited_locations`/`examined_entities` are unparameterized. Add explicit return/attribute types and prefer module-level protocol types for LLM responses.
- Parser typing is loose: `_parse_word_type` returns a `set[WordType] | WordType` without a declared union, and `ParsedCommand` consumers rely on runtime `isinstance(..., set)` checks. Define a `WordTypeLike = WordType | set[WordType]` alias and use it in `WordEntry` plus parser helpers to make intent clear to mypy.
- `mypy.ini` currently disables `annotation-unchecked`, so untyped functions are ignored. Plan a staged tightening: enable `warn_return_any`, then `disallow_untyped_defs` module-by-module, starting with `src/action_types.py`, `src/behavior_manager.py`, and `src/llm_protocol.py`.

## Redundant or Divergent Code Paths
- `parsed_to_json` is duplicated in `src/text_game.py`, `src/llm_narrator.py`, and every example `run_game.py`, plus tests import from different copies. Centralize this in a shared helper (e.g., `src/command_utils.py`) to prevent drift and simplify test imports.
- Parser construction is duplicated with temp-file writes in `src/game_engine.py:create_parser` and `src/llm_narrator.py:_create_parser` because `Parser` only accepts a filename. Provide a factory that accepts an in-memory vocabulary dict (or a `Parser.from_vocab` classmethod) so both call sites share one code path and stop touching the filesystem.
- Vocabulary merging happens twice: `GameEngine` builds merged vocab from base + extracted nouns + behaviors, while `_query_vocabulary` in `src/llm_protocol.py` rebuilds base + behaviors without extracted nouns. Consolidate into a single `VocabularyService` so parser, LLM prompt injection, and vocabulary queries all report the same merged set.
- CLI logic is scattered: `src/text_game.py`, `src/llm_game.py`, and example `run_game.py` scripts reimplement loops, save/load prompting, and formatting. Extract a reusable CLI driver to cut duplication and keep behavior consistent across examples.

## Legacy / Back-Compat Code to Retire
- `LLMProtocolHandler` still falls back to `_cmd_*` handlers (none exist now) and keeps the string-to-`WordEntry` adapter for actions. After wiring all verbs through behavior handlers with typed `ActionDict`, drop this fallback and the conversion shim.
- `BehaviorManager._invoke_behavior_internal` supports the old dict-based `behaviors` format; current game states use list-based modules only. Remove the dict path once confirmed by a repo-wide search/tests.
- `utilities/location_serializer.serialize_location_for_llm` handles exits as raw strings for compatibility. If all games now use `ExitDescriptor`, remove the string branch and enforce structured exits.
- Deprecated/unused helpers in `src/llm_protocol.py` (`_add_llm_context`, `_get_lock_by_id`) can be deleted after verifying no external imports.
- Path hacking in `src/game_engine.py` (mutating `sys.path` to import behaviors) is brittle. Prefer package-relative imports or importlib resources once behaviors are packaged/installed, then remove the path mutations.

## Structural Simplification Opportunities
- Define protocol message types (TypedDicts or small dataclasses) for command/query/result payloads and use them across narrator, CLI, and tests. This will also tighten behavior handler signatures and remove ad hoc `Dict[str, Any]` plumbing.
- Fold all vocabulary duties (load base, extract nouns, merge behaviors, expose narration metadata) into one service injected wherever needed (parser creation, narrator prompt, vocabulary query responses).
- Standardize serialization through `utilities.entity_serializer`/`utilities.location_serializer` only; avoid custom container/on_surface logic in `LLMProtocolHandler._entity_to_dict` by extending the serializer instead of layering on top.
- Consolidate CLI drivers (text-only and LLM modes) so save/load handling, meta-command signals, and result formatting live in one place with pluggable input/output adapters.

## Suggested Execution Plan
1) **Type hygiene first**: adopt `ActionDict` and new message TypedDicts in `llm_protocol.py`/`llm_narrator.py`, annotate public methods, and start turning on stricter mypy flags module-by-module. Add focused tests for typed handler contracts.  
2) **Deduplicate**: centralize `parsed_to_json`, add a parser factory that accepts dict vocab, and move vocabulary merging into a shared service consumed by engine, narrator, and protocol queries.  
3) **Retire legacy**: remove `_cmd_*` fallbacks, dict-based behaviors, string-exit handling, and unused helpers after confirming no fixtures rely on them. Update docs/tests accordingly.  
4) **Reshape structure**: refactor CLI entrypoints to reuse a shared driver, replace `sys.path` mutations with package-aware imports, and ensure all serialization and narration flows depend on a single vocabulary/serialization pipeline.
