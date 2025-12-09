# Mechanisms for Intra-Room Movement in Text Adventures

Text adventure games traditionally treat rooms as atomic locations, but many games implement ways for **players to move within a room** and for **actions to depend on positional state**. This document summarizes the major mechanisms used historically and in modern systems.

---

## 1. Subrooms / Partitions (“Micro-Locations”)

### Summary
A single room is subdivided into smaller, explicit sub-locations that act like mini-rooms.

### How It Works
Players move between:
- corners
- platforms
- alcoves
- under or behind objects

Using verbs like:
- `go to X`
- `climb onto X`
- `stand by X`

### Pros
- Easy to implement using standard room logic.
- Enables detailed spatial puzzles.

### Cons
- Can feel like a maze inside a room if overused.

---

## 2. Room Zones (Adjectival or Relational Positions)

### Summary
The player remains “in the same room,” but a **room-position variable** tracks where they are.

Examples:
- `position = "near the window"`
- `position = "under the chandelier"`

Actions check these flags.

### Pros
- Clean and flexible.
- Doesn’t clutter the room map.

### Cons
- Requires strong descriptive cues for players.

---

## 3. XY Positional Grids

### Summary
A room represented as a **grid of coordinates**.

### Used In
- *Beyond Zork*
- Some MUD tactical areas

### Pros
- Great for combat, stealth, or spatial puzzles.

### Cons
- Very rare in parser IF; can overwhelm players.

---

## 4. Object-Relative Positioning

### Summary
Interaction with an object implicitly moves the player “next to” or “on” that object.

### Example
```
> examine machinery
You step closer to inspect it.
```

Actions afterward assume closeness.

### Pros
- Feels natural.
- Minimizes required movement commands.

### Cons
- Harder to track or reason about exact position.

---

## 5. Verb-Driven Action Zones

### Summary
Players do not explicitly move; instead, **actions transition them into zones**.

Examples:
- `climb crates`
- `crawl under table`
- `approach gate`

### Pros
- Very naturalistic.
- Encourages direct interaction over navigation.

### Cons
- Needs clear affordances in descriptions.

---

## 6. Distance-Based States

### Summary
Room stores abstract distances:
- FAR
- NEAR
- ADJACENT
- TOUCHING
- ON_TOP

Actions have distance prerequisites.

### Pros
- Simple and powerful for stealth or combat.

### Cons
- Needs good UI to convey distance changes.

---

## 7. Orientation-Based Positioning

### Summary
Player has an orientation:
- facing north
- facing south
- turning clockwise
- objects positioned left/right/front/back

### Pros
- Enables puzzles requiring facing or alignment.

### Cons
- Increases parser complexity.

---

## 8. Verticality (Levels Within a Room)

### Summary
Sublocations based on height:
- on dais
- on balcony
- under table
- hanging from chandelier

### Pros
- Easy for players to visualize.

### Cons
- Can add numerous micro-states if overused.

---

## 9. Narrative-State Movement (Abstract Spatial Modes)

### Summary
The game tracks abstract states like:
- investigating
- circling
- hiding
- engaging

Movement is implied through narrative actions.

### Pros
- Smooth for story-heavy IF.

### Cons
- Less structured for puzzle-based games.

---

## 10. Hot-Zone Triggers (Timed or Spatially Sensitive Areas)

### Summary
The room has special zones that trigger events:
- pressure plates
- magical auras
- spotlights
- guard detection cones

### Pros
- Great for tension (stealth, chase scenes).

### Cons
- Hard to describe cleanly in pure text.

---

## Summary Table

| Mechanism | Best For | Complexity |
|----------|-----------|------------|
| Subrooms | Complex space | Medium |
| Room Zones | Contextual puzzles | Low |
| XY grid | Tactical play | High |
| Object-relative | Narrative flow | Medium |
| Verb-driven zones | Natural interaction | Medium |
| Distance states | Stealth/combat | Medium |
| Orientation | Facing puzzles | Medium-High |
| Verticality | Intuitive spatiality | Low |
| Narrative-state | Story-focused IF | Medium |
| Hot-zones | Timed/tense scenes | High |

---

## Conclusion

Text adventure games use a wide spectrum of techniques to model **intra-room movement** and **location-sensitive actions**. You can mix and match these approaches depending on how simulation-heavy or narrative-driven your engine is.

