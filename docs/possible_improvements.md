# Possible Improvements

This document tracks potential improvements and design decisions that were deferred for future consideration.

## Lock Reference Validation Inconsistency

There's an inconsistency in how the state manager handles structural references in locks vs doors:

**Door**: The `locations` field (tuple of location IDs) is a core field, allowing structural validation to verify these references exist.

**Lock**: The `opens_with` field (list of item IDs) is in properties, which means structural validation cannot verify these references without special-casing the validation logic.

### Current Approach
Keep `opens_with` in properties since locks are primarily used by behaviors (the unlocking mechanic). The cost is that invalid key references won't be caught by structural validation.

### Alternative Approaches
1. Move `opens_with` to a core field on Lock (breaks the "behaviors own their data" principle)
2. Add a generic "reference validation registry" where behaviors can register property fields that contain IDs requiring validation
3. Accept that some reference validation happens at behavior initialization time rather than load time

This inconsistency is acceptable for now but should be revisited if reference validation becomes important for game authoring tools.

## Lighting System

A lighting system still needs to be implemented. This will have implications for player movement, as dark locations may:
- Restrict what the player can see
- Limit available exits
- Require light sources (items) to navigate

Design should consider how darkness affects:
- Location descriptions
- Exit visibility and accessibility
- Item visibility
- NPC interactions
