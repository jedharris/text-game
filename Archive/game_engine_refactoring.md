# Game Engine Refactoring Report

**Date:** 2025-11-25

## Overview

The `game_engine.py` module was refactored from a standalone implementation with its own command handling functions to a thin wrapper around the JSON protocol. This aligns it with `llm_game.py`, ensuring both interfaces use identical game logic.

## Problem Statement

Prior to refactoring, `game_engine.py` and `llm_game.py` had diverged:

1. **Duplicate implementations**: `game_engine.py` had its own `take_item()`, `drop_item()`, `describe_location()`, etc. that duplicated logic in the behavior handlers
2. **Inconsistent behavior**: The two interfaces could produce different results for the same commands
3. **Vocabulary issues**: Prepositions and articles were being dropped during vocabulary merging, causing "put X on Y" commands to fail parsing
4. **Missing features**: `game_engine.py` didn't show items on surfaces (e.g., "lantern on table")

## Solution

### Architecture Change

`game_engine.py` now acts as a text I/O shell around the JSON protocol:

```
Player Input → Parser → JSON Command → JSONProtocolHandler → JSON Response → Format → Text Output
```

Both `game_engine.py` and `llm_game.py` now use `JSONProtocolHandler` for all game logic.

### New Functions in game_engine.py

| Function | Purpose |
|----------|---------|
| `parsed_to_json()` | Converts `ParsedCommand` to JSON protocol format |
| `format_location_query()` | Formats location query response as text |
| `format_item_query()` | Formats entity query response as text |
| `format_inventory_query()` | Formats inventory query response as text |
| `format_command_result()` | Formats command success/error as text |

### Removed Functions

The following duplicate functions were removed:
- `take_item()`
- `drop_item()`
- `describe_location()`
- `examine_item()`
- Various other local implementations

### Command Routing

| User Input | JSON Protocol | Handler |
|------------|---------------|---------|
| `look` (no object) | `{"type": "query", "query_type": "location"}` | Query handler |
| `examine table` | `{"type": "command", "action": {"verb": "examine", "object": "table"}}` | `handle_examine()` |
| `take sword` | `{"type": "command", "action": {"verb": "take", "object": "sword"}}` | `handle_take()` |
| `inventory` | `{"type": "query", "query_type": "inventory"}` | Query handler |
| `go north` | `{"type": "command", "action": {"verb": "go", "direction": "north"}}` | `handle_go()` |

## Bug Fixes

### 1. Vocabulary Merging (vocabulary_generator.py, behavior_manager.py)

**Problem:** `merge_vocabulary()` and `get_merged_vocabulary()` were dropping prepositions and articles.

**Fix:** Added explicit copying of all vocabulary fields:
```python
merged = {
    "verbs": list(base_vocab.get("verbs", [])),
    "nouns": list(base_vocab.get("nouns", [])),
    "adjectives": list(base_vocab.get("adjectives", [])),
    "directions": list(base_vocab.get("directions", [])),
    "prepositions": list(base_vocab.get("prepositions", [])),  # Added
    "articles": list(base_vocab.get("articles", []))           # Added
}
```

### 2. Items on Surfaces

**Problem:** Location descriptions didn't show items on surfaces.

**Fix:** `format_location_query()` now separates direct items from items on surfaces:
```python
for item in items:
    on_surface = item.get("on_surface")
    if on_surface:
        surface_items[on_surface].append(item.get("name"))
    else:
        direct_items.append(item.get("name"))
```

Output example:
```
Hallway
A long hallway with wooden floors.
On the table: lantern
Exits: door (closed) to the north
```

## Interface Alignment

Both interfaces now use identical mechanisms:

| Operation | llm_game.py | game_engine.py |
|-----------|-------------|----------------|
| Opening scene | Location query | Location query |
| Look around | Location query | Location query |
| Examine item | Command (via LLM) | Command (via parser) |
| Take/drop/etc. | Command (via LLM) | Command (via parser) |

The only difference is input translation:
- `llm_game.py`: LLM translates natural language → JSON
- `game_engine.py`: Parser translates structured text → JSON

## Files Modified

| File | Changes |
|------|---------|
| `src/game_engine.py` | Complete rewrite as JSON protocol wrapper |
| `src/vocabulary_generator.py` | Added prepositions/articles to merge |
| `src/behavior_manager.py` | Added prepositions/articles to merge |
| `tests/test_game_engine.py` | Updated to test new architecture |
| `tests/test_game_engine_commands.py` | Updated to test JSON protocol |

## Test Results

All 820 tests pass after refactoring.

## Benefits

1. **Single source of truth**: All game logic lives in behavior handlers
2. **Consistent behavior**: Both interfaces produce identical results
3. **Easier maintenance**: Changes to game logic only need to be made once
4. **Better testing**: Behavior handlers can be tested independently of I/O layer
