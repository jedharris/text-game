# Game State Format v_0.03

**Version:** v_0.03
**Date:** 2024-12-06
**Previous:** v_0.02

## Changes from v_0.02

### No Game State Format Changes

This version introduces engine improvements (Event Registry) without modifying the game state format. Existing game state files work without changes.

### Engine Changes

1. **Event Registry System**: Events are now discovered from behavior module vocabulary at load time
2. **Engine Hooks**: Internal events use stable hook names (e.g., `location_entered`, `visibility_check`)
3. **Event Fallbacks**: Declared in vocabulary via `fallback_event` field
4. **Load-time Validation**: All `on_*` functions must have registered events

### Schema version in metadata

The `schema_version` field in metadata should be set to `"v_0.03"`.

```json
{
  "metadata": {
    "title": "...",
    "schema_version": "v_0.03",
    ...
  }
}
```

## Migration Tool

Use `tools/migrations/migrate_v0_02_to_v0_03.py` to migrate game state files:

```bash
python -m tools.migrations.migrate_v0_02_to_v0_03 input.json output.json
```

Or migrate in place:

```bash
python -m tools.migrations.migrate_v0_02_to_v0_03 game_state.json
```

Since this version only updates the schema version field, migration is trivial.

## Behavior Module Event Registration

Starting with v_0.03, behavior modules can register events and hooks:

```python
vocabulary = {
    "verbs": [
        {
            "word": "take",
            "event": "on_take",
            "synonyms": ["get", "grab"]
        }
    ],
    "events": [
        {
            "event": "on_enter",
            "hook": "location_entered",
            "description": "Called when actor enters location"
        }
    ]
}
```

Engine code uses hook names (not event names) to invoke behaviors:

```python
from src.hooks import LOCATION_ENTERED

event = behavior_manager.get_event_for_hook(LOCATION_ENTERED)
if event:
    behavior_manager.invoke_behavior(entity, event, accessor, context)
```
