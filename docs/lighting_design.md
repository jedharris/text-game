# Lighting System Design

## Overview

This document describes the lighting system for the text adventure game engine. Light sources determine what players can see and how they can interact with their environment.

## Light Source Types

### 1. Portable Light Sources (Items)

Items that can be carried and provide light when active.

**Properties:**
- `provides_light`: boolean - whether the item can emit light
- `light_active`: boolean - whether the light is currently on (for toggleable sources)
- `fuel`: optional number - remaining fuel/charges (null for permanent sources)
- `fuel_per_turn`: optional number - fuel consumed per turn when active

**Examples:**
- Torch (consumable fuel)
- Lantern (refillable)
- Glowing gem (permanent)
- Candle (consumable)

### 2. Ambient Light Sources (Location Properties)

Light intrinsic to a location that cannot be removed.

**Properties on locations:**
- `ambient_light`: boolean - whether location has natural/permanent light
- `light_source_description`: string - description of the light source for narration

**Examples:**
- Outdoor locations (sunlight/moonlight)
- Rooms with windows
- Phosphorescent caves
- Magical illumination

### 3. Fixed Light Sources (Non-portable Items)

Items in locations that provide light but cannot be carried.

**Properties:**
- Same as portable items but with `portable: false`

**Examples:**
- Wall-mounted torches
- Fireplaces
- Braziers

## Lighting States

A location's effective lighting state is determined by combining all available light sources:

### Lit
- Ambient light present, OR
- Player carrying active light source, OR
- Active fixed light source in location

**Effects:**
- Full descriptions available
- All actions permitted
- Items and exits visible

### Dark
- No ambient light AND
- No active light sources present

**Effects:**
- Limited or no description ("It is pitch black. You can't see anything.")
- Most actions restricted
- Cannot examine items or read
- Movement restricted or dangerous

## Consequences of Darkness

### Restricted Actions
The following verbs should fail or have reduced effectiveness in darkness:

| Verb | Dark Behavior |
|------|---------------|
| examine/look | "It's too dark to see." |
| read | "It's too dark to read." |
| take | May fail or require groping ("You fumble in the darkness...") |
| attack | Disadvantage or automatic miss |
| open/close | May work by touch for familiar objects |
| go | See Movement section below |

### Movement in Darkness

Options for handling movement without light:

**Option A: Blocked Movement**
- Cannot move at all: "It's too dark to navigate safely."

**Option B: Dangerous Movement**
- Movement allowed but with consequences:
  - Random chance of injury
  - May stumble into hazards
  - May end up in wrong location
  - "You stumble in the darkness and hurt yourself."

**Option C: Limited Movement**
- Can return the way you came (memory)
- Cannot explore new directions

**Recommended:** Option B for most locations, with some locations using Option A for specific narrative reasons (cliff edges, etc.)

### Actions That Work in Darkness

Some actions should still function:

- `inventory` - Player knows what they're carrying
- `drop` - Can release what you're holding
- `quit/save/load` - Meta commands
- Tactile interactions with held items

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
  "light_active": true,
  "fuel": 100,
  "fuel_per_turn": 1,
  "llm_context": {
    "traits": ["flickering flame", "smoky", "warm glow", "crackling"],
    "state_variants": {
      "lit": "burns steadily, casting dancing shadows",
      "unlit": "cold and dark, ready to be ignited",
      "low_fuel": "gutters and flickers, nearly spent"
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
  "light_source_description": "Sunlight streams down from the open sky above.",
  "exits": { ... },
  "items": [ ... ],
  "llm_context": { ... }
}
```

### Player State Addition

Track light-related state:

```json
{
  "player_state": {
    "location": "loc_start",
    "inventory": ["item_torch"],
    "flags": {},
    "stats": {},
    "turns_in_dark": 0
  }
}
```

## Game Engine Implementation

### Light Check Function

```
function is_location_lit(location, player):
    # Check ambient light
    if location.ambient_light:
        return true

    # Check fixed light sources in location
    for item in items_at_location(location):
        if item.provides_light and item.light_active:
            return true

    # Check player's inventory
    for item_id in player.inventory:
        item = get_item(item_id)
        if item.provides_light and item.light_active:
            return true

    return false
```

### Command Validation

Before executing most commands, check lighting:

```
function validate_command(action, location, player):
    if not is_location_lit(location, player):
        if action.verb in REQUIRES_LIGHT:
            return error("It's too dark to do that.")

    # Continue with normal validation
    ...
```

### Fuel Consumption

At the end of each turn:

```
function consume_fuel(player):
    for item_id in player.inventory:
        item = get_item(item_id)
        if item.provides_light and item.light_active and item.fuel:
            item.fuel -= item.fuel_per_turn
            if item.fuel <= 0:
                item.light_active = false
                notify("Your torch sputters and goes out.")
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
    "light_source": null,
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
    "message": "It's too dark to see.",
    "reason": "no_light"
  }
}
```

## Vocabulary Additions

New verbs for light manipulation:

```json
{
  "word": "light",
  "synonyms": ["ignite", "kindle"],
  "value": 21,
  "object_required": true,
  "llm_context": {
    "traits": ["creates light", "requires fuel source"],
    "failure_narration": {
      "no_fuel": "nothing to light it with",
      "already_lit": "already burning",
      "not_lightable": "cannot be lit"
    }
  }
},
{
  "word": "extinguish",
  "synonyms": ["douse", "snuff"],
  "value": 22,
  "object_required": true,
  "llm_context": {
    "traits": ["removes light", "preserves fuel"],
    "failure_narration": {
      "not_lit": "not currently burning",
      "cannot_extinguish": "cannot be extinguished"
    }
  }
}
```

## LLM Narrator Considerations

### Dark Room Descriptions

When narrating dark locations, the LLM should:
- Emphasize other senses (sound, smell, touch)
- Create atmosphere of uncertainty and tension
- Describe what little can be perceived

Example:
> "Darkness swallows you completely. The air feels cool and damp against your skin. Somewhere ahead, water drips with a steady rhythm. The stone floor is uneven beneath your feet."

### Light Source State

Include light source status in narration:
- "Your torch flickers, casting unsteady shadows."
- "The lantern's flame burns low—perhaps ten minutes of light remain."
- "The gem in your hand pulses with a soft, steady glow."

### Transitional Moments

Narrate lighting changes dramatically:
- Entering dark from light: "The passage ahead yawns black and empty. Your torch barely penetrates the gloom."
- Light source dying: "With a final sputter, your torch dies, plunging you into absolute darkness."
- Finding light: "Relief washes over you as you step into a shaft of daylight from above."

## Migration Path for Existing Games

To add lighting to existing game states:

1. Add `ambient_light: true` to all locations (preserves current behavior)
2. Gradually set `ambient_light: false` for locations that should be dark
3. Add light-providing items where appropriate
4. Update item in starting room to be a portable torch

## Future Enhancements

- **Light radius**: Some sources illuminate adjacent rooms
- **Light colors**: Different sources provide different colors (affects mood)
- **Creatures and light**: Some enemies avoid light, others are attracted
- **Day/night cycle**: Ambient light changes over time
- **Light-sensitive items**: Objects that react to light/dark
