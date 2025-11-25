# Converting simple_game_state.json to New Format

## Overview

Phase 3 introduced a unified actor model where player and NPCs are stored in a single `actors` dict. The serialization code supports automatic migration (old saves load fine), but `simple_game_state.json` should be manually converted for clean git history.

## Current Status

- ✅ Load functions support both old and new formats
- ✅ Save functions write new format
- ❌ `data/simple_game_state.json` still uses old format

## Conversion Script

```bash
python3 << 'EOF'
from src.state_manager import load_game_state, save_game_state

# Load (auto-converts old format to new model in memory)
state = load_game_state('data/simple_game_state.json')

# Save in new format
save_game_state(state, 'data/simple_game_state.json')

print(f"✅ Converted! Now has {len(state.actors)} actors:")
for actor_id in state.actors:
    print(f"  - {actor_id}")
EOF
```

## What Changes in the JSON

### Old Format
```json
{
  "metadata": {...},
  "player_state": {
    "location": "room1",
    "inventory": []
  },
  "npcs": [
    {
      "id": "npc_guard",
      "name": "guard",
      "location": "room1",
      "inventory": []
    }
  ]
}
```

### New Format
```json
{
  "metadata": {...},
  "actors": {
    "player": {
      "id": "player",
      "name": "player",
      "description": "The player character",
      "location": "room1",
      "inventory": [],
      "properties": {},
      "behaviors": []
    },
    "npc_guard": {
      "id": "npc_guard",
      "name": "guard",
      "description": "A guard",
      "location": "room1",
      "inventory": [],
      "properties": {},
      "behaviors": []
    }
  }
}
```

## Key Differences

1. **Player**: `player_state` field → `actors["player"]` entry
2. **NPCs**: `npcs` array → `actors[npc_id]` entries
3. **Player now has**: `id`, `name`, `description` (filled with defaults if missing)
4. **All actors have**: Explicit `behaviors` field (empty list if not specified)

## When to Run

**Recommended**: Run this conversion now before proceeding to Phase 4.

**Why**:
- Clean git diff showing the format change
- Ensures all development uses consistent format
- Verifies the conversion works correctly

**Safe to defer**: The automatic migration on load works, so this is not blocking.

## Verification

After conversion, verify with:
```bash
python3 << 'EOF'
from src.state_manager import load_game_state

state = load_game_state('data/simple_game_state.json')

# Should have actors dict
assert hasattr(state, 'actors')
assert isinstance(state.actors, dict)
assert 'player' in state.actors

print("✅ Verification passed!")
print(f"   Actors: {list(state.actors.keys())}")
EOF
```
