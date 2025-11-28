# Game State Format v_0.02

**Version:** v_0.02
**Date:** 2024-11-28
**Previous:** v_0.01

## Changes from v_0.01

### 1. Lock `name` field now required

Previously, Lock entities had an optional `name` field. Now `name` is required for consistency with other entity types.

**v_0.01:**
```json
{
  "id": "lock_treasure",
  "description": "A sturdy lock.",
  "properties": { ... }
}
```

**v_0.02:**
```json
{
  "id": "lock_treasure",
  "name": "Treasure Lock",
  "description": "A sturdy lock.",
  "properties": { ... }
}
```

**Migration:** If `name` is missing, default to the lock's `id`.

### 2. Schema version in metadata

The `schema_version` field in metadata should be set to `"v_0.02"`.

**v_0.02:**
```json
{
  "metadata": {
    "title": "...",
    "schema_version": "v_0.02",
    ...
  }
}
```

## Full Lock Schema

```json
{
  "id": "string (required)",
  "name": "string (required)",
  "description": "string (required)",
  "properties": {
    "opens_with": ["item_id", ...],
    "auto_unlock": "boolean",
    "fail_message": "string (optional)"
  },
  "behaviors": ["module:function", ...],
  "llm_context": {
    "traits": ["string", ...],
    "state_variants": { ... }
  }
}
```

## Entity Consistency

As of v_0.02, all entity types have consistent required fields:

| Entity | id | name | description |
|--------|-----|------|-------------|
| Item | required | required | required |
| Actor | required | required | required |
| Location | required | required | required |
| Lock | required | **required** | required |
| ExitDescriptor | synthesized | optional* | optional |

*ExitDescriptor `name` defaults to direction when parsed from JSON.

## Migration Tool

Use `tools/migrations/migrate_v0_01_to_v0_02.py` to migrate game state files:

```bash
python -m tools.migrations.migrate_v0_01_to_v0_02 input.json output.json
```

Or migrate in place:

```bash
python -m tools.migrations.migrate_v0_01_to_v0_02 game_state.json
```
