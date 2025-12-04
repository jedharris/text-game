# Room-Container Unification

## Overview

This document explores the possibility of unifying Locations (rooms) and container Items into a single entity type or shared abstraction. This is a highly speculative design exploration prompted by issue #6.

## Motivation

### The Toy Cottage Scenario

The motivating example from issue #6:
> In a room there's a toy cottage, which is a container. An exit from the room leads into the toy cottage, so you could be looking down into the toy cottage and see a tiny NPC, or in the cottage looking up into the huge room and see a giant NPC.

This scenario highlights an interesting overlap:
- The cottage is an **item** (can be examined, potentially manipulated)
- The cottage is a **container** (can hold other items)
- The cottage is a **location** (has exits, can be entered)

More generally, items like dollhouses, wardrobes, tents, or buildings blur the line between "container item" and "enterable space."

### Ontological Overlap

**Similarities between Locations and Container Items:**
- Both can contain other items
- Both have names and descriptions
- Both have states and properties
- Both can have behaviors
- Both have llm_context for narration
- Both support the same property-based architecture

**Current Structural Differences:**
- **Locations** have:
  - `exits: Dict[str, ExitDescriptor]` - Spatial connections to other locations
  - `items: List[str]` - IDs of items present
  - Not portable (no location field)
  - No concept of "outside"

- **Container Items** have:
  - `location: str` - Where the item exists
  - `properties["container"]` - Container configuration (capacity, open/closed, etc.)
  - `portable: bool` - Whether moveable
  - Can be inside other containers or locations

**The Key Difference:**
Locations have exits (spatial connections), items don't. But as the cottage example shows, this isn't a hard boundary - an item could potentially have exits leading "into" it.

## Current Architecture

### Location Structure
From [state_manager.py:108-138](../src/state_manager.py#L108-L138):
```python
@dataclass
class Location:
    id: str
    name: str
    description: str
    exits: Dict[str, ExitDescriptor]
    items: List[str]  # Item IDs present in this location
    properties: Dict[str, Any]
    behaviors: List[str]
```

### Container Item Structure
From [state_manager.py:142-251](../src/state_manager.py#L142-L251):
```python
@dataclass
class Item:
    id: str
    name: str
    description: str
    location: str  # Where this item is
    properties: Dict[str, Any]  # Contains "container" dict if container
    behaviors: List[str]
```

Container properties (in `properties["container"]`):
- `is_surface: bool` - Table/pedestal vs enclosed container
- `capacity: int` - Maximum items (0 for unlimited)
- `open: bool` - Current state (enclosed containers only)
- `locked: bool` - Whether requires unlocking
- `lock_id: str` - Reference to lock object

### Item Location Reference System

Items use a simple string `location` field:
- `"loc_room"` - In a location
- `"player"` or `"npc_id"` - In an actor's inventory
- `"item_container"` - Inside a container item
- `"exit:loc_id:direction"` - Door attached to an exit (special case)

This system already supports recursive containment (items in items).

## Design Options

### Option A: Full Type Unification

Merge Location and Item into a single unified Entity type.

**Structure:**
```python
@dataclass
class Entity:
    id: str
    name: str
    description: str
    location: Optional[str]  # None for top-level locations
    exits: Dict[str, ExitDescriptor]  # Empty dict if not a location
    items: List[str]  # IDs of items/entities contained
    properties: Dict[str, Any]
    behaviors: List[str]
```

**Pros:**
- Maximum flexibility - any entity can be a container, location, or both
- Enables dollhouse/cottage scenarios naturally
- Simplifies type system conceptually
- Items could have exits (wardrobe → Narnia)
- Locations could be portable (magic carpet, vehicle)

**Cons:**
- **Massive breaking change** - affects entire codebase
- Every system that distinguishes locations from items needs refactoring
- Potential confusion: "Why does this book have an exits field?"
- `location: Optional[str]` for top-level locations is awkward
- Loss of type safety - can't distinguish location entities from item entities
- Unclear semantics: what does it mean to "take" a location?
- **Estimated impact:** 50+ files, 300+ tests, weeks of work

### Option B: Dual-Identity Hybrid

Allow entities to have both location and item identities via cross-references.

**Structure:**
```python
@dataclass
class Location:
    # ... current fields
    item_id: Optional[str]  # If this location is also an item

@dataclass
class Item:
    # ... current fields
    location_id: Optional[str]  # If this item is also a location
    exits: Dict[str, ExitDescriptor]  # Only used if location_id set
```

**Pros:**
- Maintains separate types (better type safety)
- Enables cottage scenario via linked identities
- Less invasive than full merge
- Existing code mostly unchanged

**Cons:**
- Complex semantics: which is the "real" entity?
- Synchronization issues: keeping both identities consistent
- Potential for orphaned references
- Confusing for game authors: "Do I create item or location first?"
- Added cognitive load without clear programming model

### Option C: Container Properties on Locations (Minimal)

Simply add container-like properties to Location without merging types.

**Structure:**
```python
@dataclass
class Location:
    # ... current fields
    # properties can contain "container" dict just like items
```

**Pros:**
- Minimal change
- Locations can act as containers for capacity limits, etc.
- Maintains clear type distinction
- Low risk

**Cons:**
- **Doesn't enable the motivating scenarios**
- Doesn't allow locations to be portable
- Doesn't allow items to have exits
- Doesn't address the ontological overlap
- Misses the point of the exploration

### Option D: Exit-Having Items (Targeted)

Allow items to optionally have exits, without merging types.

**Structure:**
```python
@dataclass
class Item:
    # ... current fields
    exits: Dict[str, ExitDescriptor] = field(default_factory=dict)
```

**Pros:**
- Enables the cottage/dollhouse/wardrobe scenarios
- Maintains type distinction
- Items without exits aren't affected
- Less invasive than full merge
- Clear semantics: some items are enterable spaces

**Cons:**
- Commands need disambiguation: "go into cottage" vs "put item in cottage"
- Location queries would need to check both locations and exit-having items
- Parser complexity for movement commands
- Items with exits are still not truly locations (no top-level status)
- Still significant refactoring of movement/navigation systems

## Philosophical Considerations

### "Rooms Don't Have Outsides"

This observation highlights a key ontological difference:
- **Items** exist within a space (have insides and outsides)
- **Locations** ARE spaces (define the inside, but have no outside)

This distinction matters for:
- **Portability**: Items can be moved between locations, locations can't
- **Perspective**: You're "in" a room, but you're "looking at" an item
- **Description**: Items are described from outside, rooms from inside

**However**, this raises interesting possibilities:
- What if rooms DID have outsides? (Buildings, vehicles, dimensions)
- What if you could describe a room from outside? (Looking through a window)
- What if some locations were portable? (Ship, wagon, flying carpet)

These break the traditional text adventure model but could enable rich gameplay.

### The Scale Problem

The cottage scenario actually requires **scale/perspective mechanics**, not just type unification:
- Being normal-sized outside, seeing tiny cottage
- Being tiny inside, seeing giant room
- Size-relative descriptions and interactions

This is a separable feature from type unification and would require:
- Scale properties on entities and actors
- Perspective-based description generation
- Size-relative interaction rules

Type unification alone doesn't solve this - you still need the scale system.

### Successful Precedent: Item/Door Merge

The item/door merge (already implemented) succeeded because:
- Doors already felt like items (physical objects)
- Doors already stored in items array
- Only added `properties["door"]` to existing items
- Clear conceptual fit
- Limited scope of changes

The location/item merge would be much harder because:
- Locations and items have fundamentally different roles
- Locations don't "exist within" other spaces
- Exits are complex spatial relationships
- Much broader architectural impact

## Implementation Challenges

### 1. Movement vs Manipulation Commands

If items can have exits, commands become ambiguous:
- "go into cottage" (movement) vs "put gem in cottage" (manipulation)
- "enter wardrobe" (movement) vs "open wardrobe" (manipulation)
- "look in dollhouse" (examination) vs "go in dollhouse" (movement)

Resolution would require:
- Verb selection based on item properties (has exits → prefer movement)
- Context from sentence structure (prepositions matter)
- Fallback disambiguation ("Did you want to enter or put something in?")

### 2. Location Query System

Currently location queries are separate from item queries:
- `{"type": "query", "query_type": "location"}` - Get current room
- `{"type": "query", "query_type": "entity"}` - Get specific item

If items can be locations:
- Navigation needs to check both item-locations and pure locations
- "Where am I?" might return an item ID
- Exit resolution needs to handle item-location targets
- Actor tracking needs unified location/item space

### 3. Recursive Containment Complexity

Already supported: items in items in items
New complexity: locations in locations in locations
- What's the top level? (Currently: locations list)
- How do you navigate out of nested item-locations?
- What about portability of nested structures?
- Performance implications for deep nesting?

### 4. Serialization and Game Files

Current format has clear sections:
```json
{
  "locations": [...],
  "items": [...],
  "actors": {...}
}
```

With unification:
- Merge into single "entities" array? (loses clarity)
- Keep separate but allow cross-references? (complex)
- How do authors know which section to use?
- Migration path for existing games?

## Use Cases

### Strong Use Cases for Unification

1. **Enterable Furniture/Items**
   - Wardrobe → Narnia (classic fantasy trope)
   - Dollhouse/toy cottage (the motivating example)
   - Tent (portable location)
   - Vehicle (mobile location)

2. **Buildings as Items**
   - Outside: "You see a small cottage"
   - Inside: A full location with multiple rooms
   - The building is an item when viewed from outside

3. **Portable Locations**
   - Magic carpet you can ride
   - Boat you can enter and sail
   - Carriage that moves between locations

4. **Nested Spaces**
   - Box within a chest within a room
   - Room within a building within a city
   - Unified model for all containment

### Weak Use Cases

1. **Simple Containers**
   - Boxes, chests, tables don't need exits
   - Current item container system works fine
   - No benefit from unification

2. **Standard Rooms**
   - Most locations don't need to be portable
   - Most locations don't exist "within" other locations
   - Current system works fine

3. **Scale/Perspective**
   - Requires separate scale mechanics
   - Type unification doesn't solve this
   - Orthogonal feature

## Recommendations

### Immediate Recommendation: Defer

**Do not implement this now.** The use cases are speculative and the implementation cost is very high.

Reasons to defer:
1. No concrete game design requiring this feature
2. Massive scope (weeks of work, 300+ tests to update)
3. Risk of creating confusing programming model
4. Previous simplifications (item/door merge) were simpler and had clear wins
5. Can be added later if compelling use case emerges

### If Implementing in Future

**Recommended approach: Option D (Exit-Having Items)**

If a concrete game design requires this:
1. Start with Option D: allow items to have exits
2. Keep Location and Item as separate types
3. Add `exits` field to Item (empty dict by default)
4. Update movement commands to check exit-having items
5. Update location queries to support item-locations
6. Require items with exits to be non-portable (validation rule)

This is the minimal change that enables the interesting scenarios without the massive refactoring of full unification.

**Implementation phases (if pursued):**
1. Add exits field to Item dataclass
2. Update parser to handle "go into [item]" commands
3. Update movement system to resolve item-location targets
4. Update location queries to include exit-having items
5. Add validation: items with exits must be portable=false
6. Update narration to handle perspective (inside item-location)
7. Create example game demonstrating the feature

**Prerequisites before implementing:**
- Concrete game design that requires this
- Clear user stories for why players need it
- Design review to ensure the feature doesn't create confusion
- Consider whether simpler alternatives exist

### Alternative: Special-Case Solution

Instead of general unification, handle specific cases as behaviors:
- Create a "magical portal" behavior for wardrobe → Narnia
- Create a "vehicle" behavior for boats/carpets
- Keep locations and items separate
- Use behaviors to add location-like properties to specific items

This avoids architectural changes while still enabling interesting gameplay.

## Open Questions

1. **Top-level vs contained**: Should top-level locations be distinguished from contained locations?
2. **Portability rules**: Can item-locations ever be portable? What are the semantics?
3. **Navigation model**: How do players conceptualize "going into an item" vs "entering a location"?
4. **Performance**: What's the cost of checking items for exits on every movement command?
5. **Author experience**: Would this make game creation easier or more confusing?
6. **Scale integration**: If we add scale mechanics, how does that affect this design?
7. **NPCs as items**: Issue #6 also mentions "NPCs could just be behaviors attached to items" - related?

## Conclusion

Room-container unification is an interesting theoretical exploration that highlights the ontological overlap between locations and container items. The toy cottage scenario is compelling and would enable creative gameplay possibilities.

However, the implementation cost is very high (comparable to the entire behavior system refactor), the use cases are speculative, and the risk of creating a confusing programming model is significant.

**Recommendation: Keep this as a long-term possibility, but do not implement without a concrete game design that requires it.**

The item/door merge succeeded because it was clearly motivated and relatively simple. Location/item unification would be a much more speculative architectural change that should wait until we have real-world experience showing it's needed.

If specific scenarios (wardrobe → Narnia, enterable dollhouse) become important, consider targeted solutions (behaviors, special item types) before undertaking full unification.

## Related Issues

- Issue #6 - The original exploration
- Item/Door merge - Successful precedent for entity type unification
- Possible NPCs as items - Related ontological question about Actor types
