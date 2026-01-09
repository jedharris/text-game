# Recipe: Fixing NPC Behaviors

## Problem Found
NPCs with dialog_reactions configs were not responding because:
1. Infrastructure modules (dialog_reactions.py) were incorrectly placed in extra.behaviors
2. Command handlers were invoking hook names instead of event names

## Solution

### For Each NPC with dialog_reactions:

Add `behaviors.shared.infrastructure.dialog_reactions` to the NPC's behaviors list:

```json
{
  "id": "herbalist_maren",
  "behaviors": [
    "behaviors.shared.infrastructure.dialog_reactions",
    "behaviors.regions.civilized_remnants.services"
  ],
  "properties": {
    "dialog_reactions": {
      "handler": "examples.big_game.behaviors.regions.civilized_remnants.services:on_service_request"
    }
  }
}
```

### Pattern by Reaction Type:

| Config Property | Required Infrastructure Module | Notes |
|----------------|-------------------------------|-------|
| `dialog_reactions` | `behaviors.shared.infrastructure.dialog_reactions` | For ask/talk commands |
| `item_use_reactions` | `behaviors.shared.infrastructure.item_use_reactions` | For use/apply commands |
| `combat_reactions` | `behaviors.shared.infrastructure.combat_reactions` | For attack commands |
| `gift_reactions` | `behaviors.shared.infrastructure.gift_reactions` | For give commands |
| `encounter_reactions` | `behaviors.shared.infrastructure.encounter_reactions` | For first-time meetings |
| `death_reactions` | `behaviors.shared.infrastructure.death_reactions` | When NPC dies |
| `take_reactions` | `behaviors.shared.infrastructure.take_reactions` | When item is taken |
| `examine_reactions` | `behaviors.shared.infrastructure.examine_reactions` | For examine/look commands |

## All 18 NPCs that Need dialog_reactions Infrastructure:

From Phase 1 audit, these NPCs have dialog_reactions configs:

1. `herbalist_maren` ✅ FIXED
2. `healer_elara`
3. `camp_leader_mira`
4. `blacksmith_vex`
5. `scribe_aldric`
6. `archivist_memoria`
7. `the_echo`
8. `spider_matriarch`
9. `wolf_alpha`
10. `mother_bear`
11. `bee_queen`
12. `hunter_sira`
13. `ice_salamander_group`
14. `ice_golem`
15. `frost_wraith`
16. `pack_elders`
17. `fungal_ancient`
18. `waystone_fragment`

## Verification Command:

```bash
# Check which NPCs are missing dialog_reactions in behaviors
python -c "
import json
with open('examples/big_game/game_state.json') as f:
    data = json.load(f)

for actor_id, actor in data['actors'].items():
    has_config = 'dialog_reactions' in actor.get('properties', {})
    has_infra = 'behaviors.shared.infrastructure.dialog_reactions' in actor.get('behaviors', [])

    if has_config and not has_infra:
        print(f'MISSING: {actor_id}')
    elif has_config and has_infra:
        print(f'OK: {actor_id}')
"
```

## Command Handler Fixes:

**FIXED**: `behavior_libraries/command_lib/dialog.py`
- Changed: `invoke_behavior(npc, "entity_dialog")` → `invoke_behavior(npc, "on_dialog")`

**NEEDS CHECKING**: Other command handlers
- `combat.py` - should invoke event names, not hook names
- `item_use.py` - should invoke event names, not hook names
- `treatment.py` - should invoke event names, not hook names
