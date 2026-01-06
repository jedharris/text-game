# Parser Context Specification

## Purpose
Define exactly what entities should appear in the LLM parser's context (the "recipe" showing available objects, inventory, exits, and topics). This ensures the parser can understand player commands while respecting game boundaries like closed doors and vision limits.

## Core Principle
**Include exactly what the player can interact with in their current situation.**

## Specification

### Location Objects
Items and entities the player can currently interact with at their location:

#### INCLUDE:
1. **Items directly at the location** (location field matches player's location)
   - Example: bench, tree in Tower Entrance

2. **Items on surfaces** (items whose location is a container with `is_surface: true`)
   - Example: spellbook on desk
   - Rationale: Surface items are visible and accessible without opening anything

3. **Items in open containers** (items whose location is a container with `is_container: true` and `states.open: true`)
   - Example: potion in opened chest
   - Rationale: Contents become accessible once container is opened

4. **NPCs at the location** (actors other than the current actor)
   - Example: shopkeeper, quest giver
   - Exclude the acting player (don't list "yourself")

5. **Exit names** (for "examine staircase", "climb stairs" commands)
   - Include the exit's name field (e.g., "spiral staircase")
   - Rationale: Players should be able to examine/interact with the physical exit structure

6. **Visible door items** (doors that are visible from current location)
   - Include door if it's at the current location OR if an exit from current location references it
   - Include door name if different from exit name (avoid "door" + "staircase" duplication)
   - Rationale: Players can see and interact with doors blocking their path

#### EXCLUDE:
1. **Items in closed containers** (states.open: false)
   - Rationale: Contents aren't visible or accessible until opened
   - Exception: None

2. **Hidden items** (states.hidden: true)
   - Rationale: Hidden items shouldn't appear until revealed by game mechanics
   - Exception: None

3. **Items beyond closed doors**
   - Rationale: Can't see or interact with items in other rooms through closed doors
   - Current: Not explicitly filtered (assumes items are properly located)

4. **Items in other rooms**
   - Rationale: Can only interact with items at current location
   - Current: Filtered by location check

5. **The acting player themselves**
   - Rationale: Don't need "player" in the objects list
   - Current: Explicitly filtered out

### Inventory
Items the player is carrying:

#### INCLUDE:
1. **All items with location matching actor_id**
   - Rationale: Everything in inventory is accessible

#### EXCLUDE:
1. **Worn/equipped items** (if we add equipment system)
   - Decision needed: Should equipped items be separate?

### Exits
Available directions the player can attempt to move:

#### INCLUDE:
1. **Direction strings from exits** (e.g., "north", "up", "down")
   - Include all exits from current location
   - Include even if blocked by closed door (player can try "go north" and get told door is closed)

#### EXCLUDE:
1. **Secret/hidden exits** (if we add states.hidden: true to exits)
   - Rationale: Hidden exits shouldn't appear until discovered

### Topics
Conversation topics available with NPCs:

#### INCLUDE:
1. **Topics from NPCs at current location** (if dialogue system exists)
   - Current: Reads from actor.properties.dialogue.topics

#### EXCLUDE:
1. **Topics from NPCs in other rooms**
   - Current: Filtered by location

## Implementation Location
The specification is implemented in `src/game_engine.py`, method `build_parser_context(actor_id)`.

## Validation Strategy

### Automated Checks
Create a validator that can check if context matches specification:

```python
def validate_parser_context(context: Dict, game_state: GameState, actor_id: str) -> List[str]:
    """
    Validate that parser context matches specification.

    Returns list of violation messages (empty if valid).
    """
    violations = []

    # Check that closed container contents aren't included
    # Check that hidden items aren't included
    # Check that items from other locations aren't included
    # Check that the actor isn't listing themselves
    # etc.

    return violations
```

### Test Cases
Create test cases covering edge cases:

1. **test_closed_container_contents_excluded**: Verify items in closed chest don't appear
2. **test_open_container_contents_included**: Verify items in open chest do appear
3. **test_surface_contents_included**: Verify items on desk/table appear
4. **test_hidden_items_excluded**: Verify hidden items don't appear until revealed
5. **test_doors_appear_when_visible**: Verify door appears if at location or referenced by exit
6. **test_items_beyond_doors_excluded**: Verify can't see items in adjacent room through closed door
7. **test_exit_names_included**: Verify can examine/interact with exit structures
8. **test_actor_not_in_own_context**: Verify player doesn't see themselves in objects list

## Open Questions

### Q1: Items in other actors' inventories
Should you be able to see items an NPC is holding?
- **Proposal**: Include if NPC is at location and item is "visible" (not in closed backpack)
- **Status**: Not implemented

### Q2: Nested containers
Should you see items in an open container that's on a surface?
- Example: Open jewelry box on a desk, with ring inside box
- **Proposal**: Include items from open containers at any depth
- **Status**: Currently only goes one level deep

### Q3: Environmental features
Should non-item features be included (fireplace, window, wall)?
- **Proposal**: Only if they have explicit item entries in game state
- **Status**: Follows proposal (no special handling)

### Q4: Partially visible items
Should items visible but not reachable be included? (item on high shelf)
- **Proposal**: Include in context, let behavior handle "out of reach" message
- **Status**: Not addressed (no reach mechanics yet)

## Relationship to Narration Context

The parser context and narration context have related but different purposes:

| Context Type | Purpose | Scope |
|--------------|---------|-------|
| Parser Context | Help LLM parser understand commands | Only interactive entities |
| Narration Context | Give narrator information for descriptions | Broader - includes descriptions, traits, atmosphere |

**Key Difference**: Narration context may include non-interactive details (smells, sounds, distant objects) while parser context is strictly interactive entities.

**Shared Concern**: Both must respect visibility/accessibility boundaries (closed doors, hidden items).

## Change Management

When adding new entity types or game mechanics:

1. **Review this specification** - Does the new feature change what should be accessible?
2. **Update the spec** - Document the decision for inclusion/exclusion
3. **Update implementation** - Modify `build_parser_context()` accordingly
4. **Add test cases** - Ensure edge cases are covered
5. **Update narration context** - Consider if narration needs same changes

## Examples

### Example 1: Player in Library with Closed Door
```python
Location: Library (loc_library)
Items at location: desk (with spellbooks on it), stand, crystal ball (on stand)
Exits: down (to Tower Entrance), up (to Sanctum - BLOCKED by closed door)
Door: ornate door (closed, at loc_library)

Expected context:
{
    "location_objects": ["desk", "spellbook", "stand", "ball", "ornate door", "door", "spiral staircase"],
    "inventory": [],
    "exits": ["down", "up"],  # Include "up" even though door is closed
    "topics": []
}
```

### Example 2: Player with Open Chest
```python
Location: Treasury (loc_treasury)
Items at location: chest (open), potion (in chest), sword (at location)

Expected context:
{
    "location_objects": ["chest", "potion", "sword"],  # Potion visible because chest is open
    "inventory": [],
    "exits": ["south"],
    "topics": []
}
```

### Example 3: Player with Closed Chest
```python
Location: Treasury (loc_treasury)
Items at location: chest (closed), potion (in chest), sword (at location)

Expected context:
{
    "location_objects": ["chest", "sword"],  # Potion hidden because chest is closed
    "inventory": [],
    "exits": ["south"],
    "topics": []
}
```

## Version History
- 2026-01-05: Initial specification created during adjective disambiguation work
