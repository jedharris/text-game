# Unified Dialog System Design

## Problem Statement

There are currently two incompatible dialog systems:

1. **`dialog_lib`** (in `behavior_libraries/`): Topic-based system using `dialog_topics` property, with command handlers for `talk to` and `ask about`
2. **`dialog_reactions`** (in `big_game/behaviors/infrastructure/`): Event-hook dispatcher using `dialog_reactions` property

The `dialog_lib` command handlers check for `dialog_topics`, but big_game actors use `dialog_reactions`. Result: players cannot talk to NPCs.

## Goals

1. Single, clean dialog system that works for all games
2. Support both simple data-driven dialog and complex scripted dialog
3. Remove unused features and code
4. Enable "talk to" and "ask about" commands for big_game NPCs

## Design

### Property Name

Use `dialog_topics` - clearer name that describes what it contains.

### Data Format

**Simple data-driven dialog:**
```json
"dialog_topics": {
  "infection": {
    "keywords": ["infection", "sick", "illness"],
    "response": "'The infection spreads from the eastern caves...'"
  },
  "cure": {
    "keywords": ["cure", "remedy", "healing"],
    "response": "'You'll need the moonflower from the garden...'",
    "requires_flags": {"knows_about_infection": true}
  },
  "default_response": "The scholar shakes their head."
}
```

**Handler escape hatch for complex cases:**
```json
"dialog_topics": {
  "handler": "examples.big_game.behaviors.regions.meridian_nexus.echo:on_echo_dialog"
}
```

When `handler` is present at top level, ALL dialog for that NPC routes to the handler. The handler receives the full context and has complete control.

### Layering

| Layer | Location | Responsibility |
|-------|----------|----------------|
| Library | `behavior_libraries/dialog_lib/` | Command handlers, topic matching, prerequisites, effects |
| Region | `examples/big_game/behaviors/regions/` | Complex game-specific handlers (Echo, Aldric) |
| Data | `game_state.json` | `dialog_topics` property on actors |

**No infrastructure dispatcher needed** - unlike gifts/deaths which need central routing, dialog targets a specific NPC who owns their own topics.

### Features Retained

From `dialog_lib`:
- `keywords`: Match player input to topics
- `response`: What NPC says (renamed from `summary` for clarity)
- `requires_flags`: Prerequisites on player flags
- `requires_items`: Prerequisites on player inventory
- `sets_flags`: Set player flags after discussing
- `unlocks_topics`: Progressive dialog
- `grants_items`: Give items to player
- `one_time`: Topic can only be discussed once
- `default_response`: Fallback for unrecognized topics (renamed from `default_topic_summary`)

Added:
- `handler`: Top-level escape hatch to Python function

### Features Removed

From `dialog_reactions` (never used in game data):
- `triggers` (use `keywords` instead)
- `requires_state`, `forbidden_flags` (never used)
- `trust_delta`, `transition_to`, `create_commitment` in data-driven mode (handlers do this)
- The entire `dialog_reactions.py` dispatcher

### Command Interface

- `talk to <npc>` - Lists available topic hints
- `ask <npc> about <topic>` - Discusses specific topic
- Synonyms: `speak to`, `chat with`, `inquire about`, `question about`

### Handler Signature

```python
def on_npc_dialog(
    entity: Any,           # The NPC being spoken to
    accessor: Any,         # StateAccessor instance
    context: dict[str, Any]  # {"keyword": str, "dialog_text": str}
) -> EventResult:
    """Handle dialog for this NPC."""
    # Full control over response
    return EventResult(allow=True, feedback="NPC's response...")
```

For `talk to` (no topic), `keyword` will be empty string.
For `ask about X`, `keyword` will be "X".

## Implementation Plan

### Phase 1: Update dialog_lib

1. Modify `topics.py`:
   - Rename `summary` to `response` in code (data can use either)
   - Rename `default_topic_summary` to `default_response` (support both)

2. Modify `handlers.py`:
   - Before checking for topics, check for top-level `handler` key
   - If handler exists, load and call it with context
   - Pass `keyword` (empty for talk, topic text for ask) in context

### Phase 2: Update big_game data

1. Rename `dialog_reactions` to `dialog_topics` in game_state.json (2 actors: Echo, Aldric)
2. Keep existing handler paths - they work correctly

### Phase 3: Delete dialog_reactions infrastructure

1. Delete `examples/big_game/behaviors/infrastructure/dialog_reactions.py`
2. Update `infrastructure/__init__.py` if needed
3. Update any tests that reference dialog_reactions

### Phase 4: Update tests

1. Update `test_dialog_reactions.py` to test the unified system via dialog_lib
2. Rename test file to `test_dialog_topics.py`

## Rationale

### Why handler at top level only?

Simpler design. If an NPC needs complex logic, the handler handles everything. If an NPC is simple, data-driven topics handle everything. No mixing within one NPC.

### Why keep requires_flags, unlocks_topics, etc?

The design sketches use them extensively. They're implemented and tested. Even if big_game doesn't use them yet, they're valuable for future content.

### Why not per-topic handlers?

Analyzed usage: the 2 NPCs with handlers (Echo, Aldric) route ALL their dialog through handlers. No NPC mixes data-driven and handler-based topics. Simpler to keep it all-or-nothing.

### Why delete dialog_reactions.py?

- It's a dispatcher that hooks into `on_dialog_keyword` event
- But nothing fires that event
- Its data-driven features (`triggers`, `trust_delta`, etc.) are unused
- Handler functionality moves to dialog_lib
