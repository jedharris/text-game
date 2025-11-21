# Lighting System Design

## Overview

This document describes the lighting system for the text adventure game engine. Light sources determine what players can see and how they can interact with their environment.

## Light Source Types

### 1. Portable Light Sources (Items)

Items that can be carried and provide light.

**Properties:**
- `provides_light`: boolean - whether the item emits light

**Examples:**
- Torch
- Lantern
- Glowing gem

### 2. Ambient Light Sources (Location Properties)

Light intrinsic to a location that cannot be removed.

**Properties on locations:**
- `ambient_light`: boolean - whether location has natural/permanent light

**Examples:**
- Outdoor locations (sunlight/moonlight)
- Rooms with windows
- Phosphorescent caves
- Magical illumination

## Lighting States

A location's effective lighting state is determined by combining all available light sources:

### Lit
- Ambient light present, OR
- Player carrying a light source

**Effects:**
- Full descriptions available
- All actions permitted
- Items and exits visible

### Dark
- No ambient light AND
- Player not carrying a light source

**Effects:**
- Limited or no description ("It is pitch black. You can't see anything.")
- Most actions restricted
- Cannot examine items or read
- Movement blocked

## Consequences of Darkness

### Restricted Actions

Most actions require light and should fail with the message "It's too dark to do that." This includes:
- examine/look
- read
- take
- attack
- open/close/unlock/lock
- go
- use/push/pull/climb

### Actions That Work in Darkness

Some actions should still function:

- `inventory` - Player knows what they're carrying
- `drop` - Can release what you're holding
- `quit/save/load` - Meta commands

## Data Model Changes

### Item Schema Addition

```json
{
  "id": "item_torch",
  "name": "torch",
  "description": "A wooden torch wrapped in oil-soaked cloth.",
  "type": "object",
  "portable": true,
  "location": "loc_start",
  "provides_light": true,
  "llm_context": {
    "traits": ["flickering flame", "smoky", "warm glow", "crackling"],
    "state_variants": {
      "in_location": "burns in a wall sconce",
      "in_inventory": "illuminates your surroundings"
    }
  }
}
```

### Location Schema Addition

```json
{
  "id": "loc_tower",
  "name": "Tower Top",
  "description": "You are at the top of a tower.",
  "ambient_light": true,
  "exits": { ... },
  "items": [ ... ],
  "llm_context": { ... }
}
```

## Game Engine Implementation

### Light Check Function

```
function is_location_lit(location, player):
    # Check ambient light
    if location.ambient_light:
        return true

    # Check player's inventory
    for item_id in player.inventory:
        item = get_item(item_id)
        if item.provides_light:
            return true

    return false
```

### Command Validation

Before executing most commands, check lighting:

```
function validate_command(action, location, player):
    if not is_location_lit(location, player):
        if action.verb in REQUIRES_LIGHT:
            return error("It's too dark to do that.", reason="no_light")

    # Continue with normal validation
    ...
```

## JSON Protocol Extensions

### Query Response

Location queries should include lighting information:

```json
{
  "type": "result",
  "success": true,
  "query_type": "location",
  "data": {
    "name": "Dark Cellar",
    "description": "...",
    "is_lit": false,
    "ambient_light": false
  }
}
```

### Command Results in Darkness

When actions fail due to darkness:

```json
{
  "type": "result",
  "success": false,
  "action": "examine",
  "error": {
    "message": "It's too dark to do that.",
    "reason": "no_light"
  }
}
```

## LLM Narrator Considerations

When narrating dark locations, the LLM should:
- Emphasize other senses (sound, smell, touch)
- Create atmosphere of uncertainty and tension
- Describe what little can be perceived

Example:
> "Darkness swallows you completely. The air feels cool and damp against your skin. Somewhere ahead, water drips with a steady rhythm."
