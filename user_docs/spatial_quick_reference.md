# Spatial System Quick Reference

A quick reference for all spatial positioning features in the text adventure engine.

---

## Property Reference

### Entity Properties

#### `interaction_distance`
Controls whether player must move close to interact with entity.

- **Values**: `"any"` (default) | `"near"`
- **Applies to**: Items, Parts
- **Behavior**:
  - `"any"` - Can interact from anywhere in location, no movement
  - `"near"` - Must be close to interact, triggers automatic movement

**Example:**
```json
{
  "id": "item_desk",
  "name": "desk",
  "properties": {
    "interaction_distance": "near"
  }
}
```

#### `provides_cover`
Marks entity as suitable for tactical cover.

- **Values**: `true` | `false` (default)
- **Applies to**: Items, Parts
- **Usage**: Required for `take cover` command

**Example:**
```json
{
  "id": "item_pillar",
  "name": "pillar",
  "properties": {
    "provides_cover": true
  }
}
```

#### `allows_concealment`
Marks entity as suitable for hiding inside/within.

- **Values**: `true` | `false` (default)
- **Applies to**: Items, Parts
- **Usage**: Required for `hide` command

**Example:**
```json
{
  "id": "item_wardrobe",
  "name": "wardrobe",
  "properties": {
    "allows_concealment": true
  }
}
```

#### `climbable`
Marks entity as suitable for climbing.

- **Values**: `true` | `false` (default)
- **Applies to**: Items, Parts
- **Usage**: Required for `climb` command

**Example:**
```json
{
  "id": "item_ladder",
  "name": "ladder",
  "properties": {
    "climbable": true
  }
}
```

### Actor Properties

#### `focused_on`
Tracks which entity the actor is currently positioned at.

- **Type**: String (entity ID) | `null`
- **Applies to**: Actors
- **Set by**: All positioning commands (examine, approach, take cover, hide, climb)
- **Cleared by**: Moving to different entity

#### `posture`
Tracks actor's special positioning mode.

- **Values**: `null` (default) | `"cover"` | `"concealed"` | `"climbing"` | custom
- **Applies to**: Actors
- **Set by**: Posture commands (take cover, hide, climb)
- **Cleared by**: Moving to different entity (only on actual movement)

---

## Commands Reference

### Positioning Commands

#### `examine <object>`
Examines an entity and implicitly positions player if `interaction_distance: "near"`.

- **Sets**: `focused_on`
- **Movement**: Only if `interaction_distance: "near"`
- **Clears posture**: Only if movement occurs

**Examples:**
- `examine desk` - Moves close if desk has `interaction_distance: "near"`
- `examine chandelier` - No movement if chandelier has `interaction_distance: "any"`

#### `look at <object>`
Alias for `examine <object>` - identical behavior.

#### `approach <object>` / `go to <object>` / `move to <object>`
Explicitly moves player to an entity.

- **Sets**: `focused_on`
- **Movement**: Always (explicit positioning)
- **Clears posture**: Yes

**Examples:**
- `approach desk`
- `go to bench`
- `move to pillar`

### Posture Commands

#### `take cover behind <object>` / `hide behind <object>`
Takes tactical cover behind an entity.

- **Requires**: `provides_cover: true` on target
- **Sets**: `focused_on`, `posture: "cover"`
- **Clears posture**: Previous posture replaced

**Examples:**
- `take cover behind pillar`
- `hide behind crate`

#### `hide in <object>` / `conceal in <object>`
Hides inside a concealed space.

- **Requires**: `allows_concealment: true` on target
- **Sets**: `focused_on`, `posture: "concealed"`
- **Clears posture**: Previous posture replaced

**Examples:**
- `hide in wardrobe`
- `conceal in shadows`

#### `climb <object>`
Climbs on a vertical object.

- **Requires**: `climbable: true` on target
- **Sets**: `focused_on`, `posture: "climbing"`
- **Clears posture**: Previous posture replaced

**Examples:**
- `climb ladder`
- `climb tree`

### Implicit Positioning Commands

These commands trigger positioning automatically when interacting with `interaction_distance: "near"` entities:

- `take <object>` - Positions before taking
- `open <object>` - Positions before opening
- `close <object>` - Positions before closing

---

## Universal Surfaces

Common room features that exist in every location without requiring explicit Part entities:

- **ceiling** - `examine ceiling`
- **floor** / **ground** - `examine floor` or `examine ground`
- **sky** - `examine sky`
- **walls** - `examine walls`

**Behavior:**
- Returns default description
- Does NOT set `focused_on`
- Does NOT trigger positioning
- Can be overridden with explicit Part entities

**Default descriptions:**
- "Nothing remarkable about the ceiling."
- "Nothing remarkable about the floor."
- "The sky stretches above you."
- "The walls surround you."

---

## Behavior Summary

### Focus Setting
All positioning and interaction commands set `focused_on`:
- ✅ examine (implicit)
- ✅ take (implicit)
- ✅ open (implicit)
- ✅ close (implicit)
- ✅ approach (explicit)
- ✅ take cover (posture)
- ✅ hide (posture)
- ✅ climb (posture)
- ❌ look (no object) - room description only
- ❌ universal surfaces - no real entity

### Posture Clearing
Posture is automatically cleared when:
- ✅ Moving to different entity (actual movement to "near" entity)
- ✅ Using different posture command
- ❌ NOT when examining "any" distance items (no movement)
- ❌ NOT when re-examining same focused entity

### Movement Messages
Movement messages appear when:
- Entity has `interaction_distance: "near"` AND
- Player not already `focused_on` that entity

**Example flow:**
```
> examine desk       # First time - desk has "near"
(You move closer to the desk.)
desk: A wooden desk with carved legs.

> examine desk       # Already there - no movement message
desk: A wooden desk with carved legs.

> examine chandelier # "any" distance - no movement
chandelier: A crystal chandelier hanging from the ceiling.

> examine desk       # Back to desk - still focused, no movement
desk: A wooden desk with carved legs.

> examine shelf      # Different "near" entity - movement!
(You move closer to the shelf.)
shelf: A bookshelf filled with dusty tomes.
```

---

## Common Patterns

### Multi-Part Object (Workbench with Sides)

```json
{
  "items": [
    {
      "id": "item_bench",
      "name": "workbench",
      "location": "loc_workshop",
      "properties": {
        "interaction_distance": "near"
      }
    }
  ],
  "parts": [
    {
      "id": "part_bench_left",
      "name": "left side of workbench",
      "part_of": "item_bench",
      "properties": {
        "description": "Grinding tools and a mortar.",
        "activity": "grinding"
      }
    },
    {
      "id": "part_bench_right",
      "name": "right side of workbench",
      "part_of": "item_bench",
      "properties": {
        "description": "Beakers and burners for mixing.",
        "activity": "mixing"
      }
    }
  ]
}
```

### Room with Directional Walls

```json
{
  "parts": [
    {
      "id": "part_room_north_wall",
      "name": "north wall",
      "part_of": "loc_room",
      "properties": {
        "description": "A stone wall with ancient carvings."
      }
    },
    {
      "id": "part_room_east_wall",
      "name": "east wall",
      "part_of": "loc_room",
      "properties": {
        "description": "A brick wall with a barred window."
      }
    }
  ]
}
```

### Tactical Cover Object

```json
{
  "items": [
    {
      "id": "item_pillar",
      "name": "stone pillar",
      "location": "loc_hall",
      "properties": {
        "portable": false,
        "interaction_distance": "near",
        "provides_cover": true
      }
    }
  ]
}
```

### Climbable Structure

```json
{
  "items": [
    {
      "id": "item_ladder",
      "name": "ladder",
      "location": "loc_barn",
      "properties": {
        "portable": false,
        "interaction_distance": "near",
        "climbable": true
      }
    }
  ]
}
```

---

## Troubleshooting

### "You don't see that here" when examining ceiling/floor
- ✅ **Normal**: Universal surfaces (ceiling, floor, sky, walls) are built-in
- If you see this error, check spelling or use `look` to see what's in the room

### Movement happens every time I examine something
- Check `interaction_distance` property
- If set to `"near"`, movement occurs when not already focused
- Use `"any"` for items that don't require proximity

### Posture not clearing when I move
- Posture only clears on **actual movement** (to "near" entities)
- Examining "any" distance items doesn't clear posture
- This is intentional - allows looking around without leaving cover

### Can't take cover behind object
- Check entity has `provides_cover: true` property
- Verify entity is in current location
- Use `take cover behind <object>` (not just `cover <object>`)

### Custom behaviors can't access focused_on
- `focused_on` is in `actor.properties["focused_on"]`
- `posture` is in `actor.properties["posture"]`
- Both are optional - check with `.get("focused_on")` and `.get("posture")`

---

## See Also

- [Authoring Spatial Rooms](authoring_spatial_rooms.md) - Complete guide with examples
- [Engine Developer Documentation](../docs/engine_dev_docs.md) - Implementation details
- [Implicit Positioning Patterns](../docs/implicit_positioning_patterns.md) - Handler implementation guide
