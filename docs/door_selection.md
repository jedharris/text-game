# Door Selection with Adjectives - Design Document

## Overview

This document describes design changes to `simple_engine.py` to support adjective-based door selection and disambiguation when multiple doors are present in a room.

### Key Features

1. **Description-based adjectives**: "open wooden door", "examine iron door"
2. **State-based adjectives**: "close open door", "examine locked door"
3. **Directional adjectives**: "open north door", "close east door"
4. **Interactive disambiguation**: When ambiguous, prompt user to choose
5. **Backward compatibility**: Simple "open door" still works

### Quick Examples

```
> open north door                    # Use direction as adjective
You open the wooden door.

> examine door                       # Ambiguous - triggers disambiguation
Which door do you want to examine?
1. wooden door (north)
2. iron door (east)
> east                              # Can respond with direction
A heavy iron door with a sturdy lock.
  The door is locked.

> open locked door                   # State-based selection
Which locked door do you want to open?
1. iron door (east)
2. steel door (west)
> 1                                 # Can respond with number
The door is locked. You need a key.
```

## Current State

### Limitations
1. **No adjective support**: Commands like "open wooden door" or "examine locked door" don't work
2. **Arbitrary door selection**: When multiple doors exist, the engine picks one based on internal priority (closed before open)
3. **No user feedback**: Users aren't told which door was selected or given a choice
4. **Limited door information**: Door descriptions don't expose distinguishing adjectives

### Current Behavior
- `open door` → Opens the first closed door found (if multiple doors exist)
- `examine door` → Shows all doors in the room
- No way to specify which door when there are multiple

## Design Goals

1. Allow users to specify doors using adjectives from door descriptions
2. Provide interactive disambiguation when user's command is ambiguous
3. Extract adjectives automatically from door descriptions (minimal JSON changes)
4. Maintain backward compatibility with simple "door" commands
5. Support state-based adjectives (locked, open, closed)
6. Support directional/location-based adjectives (north, east, etc.)

## Proposed Changes

### 1. Door Adjective Extraction

**Strategy**: Parse adjectives from existing door descriptions automatically, plus add state-based and directional adjectives.

**Implementation Location**: New helper function in `simple_engine.py`

```python
def extract_door_adjectives(door, state, vocabulary_adjectives) -> List[str]:
    """
    Extract adjectives that describe a door.

    Returns list of adjectives from:
    1. Words in door.description that match vocabulary adjectives
    2. State-based adjectives: "locked", "open", "closed"
    3. Directional adjectives: direction from current location's exits
    """
```

**Extraction Rules**:
- Parse `door.description` and match words against vocabulary adjectives
- Add "locked" if `door.locked == True`
- Add "open" if `door.open == True`
- Add "closed" if `door.open == False`
- **Add direction** (north, south, east, west, up, down) based on current location's exit mapping
- Convert description to lowercase, tokenize, match against vocabulary

**Examples**:
- "A simple wooden door." (north exit) → `["wooden"]` + `["open"]` + `["north"]` → `["wooden", "open", "north"]`
- "A heavy iron door with a sturdy lock." (east exit) → `["heavy", "iron"]` + `["locked", "closed"]` + `["east"]`

**Vocabulary Updates Required**:
- Add "locked" to `data/vocabulary.json` adjectives (value: 213)
- Add "open" to `data/vocabulary.json` adjectives (value: 214)
- Add "closed" to `data/vocabulary.json` adjectives (value: 215)
- **Note**: Directions are already in vocabulary as type DIRECTION, but need to be recognized as adjectives in this context

**Direction Mapping Algorithm**:

To determine which direction a door is in:

```python
def get_door_direction(door, current_location) -> Optional[str]:
    """
    Find the exit direction for a door from the current location.

    Args:
        door: The door object
        current_location: Current Location object

    Returns:
        Direction string ("north", "east", etc.) or None if not found
    """
    # Iterate through location's exits
    for direction, exit_desc in current_location.exits.items():
        # Check if this exit is a door and matches our door's ID
        if exit_desc.type == "door" and exit_desc.door_id == door.id:
            return direction
    return None
```

**Example**:
```json
// Location exits
"exits": {
  "north": {"type": "door", "to": "loc_hallway", "door_id": "door_wooden"},
  "east": {"type": "door", "to": "loc_locked_room", "door_id": "door_treasure"}
}

// Results:
// door_wooden → "north"
// door_treasure → "east"
```

**Edge Case - Same Door, Multiple Directions**:

If a location has multiple exits leading to the same door (rare but possible in circular layouts), include all directions:

```python
# Example: door accessible from both north and northeast
# Result: ["wooden", "north", "northeast"]
```

### 2. Door Matching Function

**Implementation Location**: New helper function in `simple_engine.py`

```python
def find_matching_doors(
    doors: List[Door],
    noun: str,
    adjective: Optional[str],
    vocabulary_adjectives
) -> List[Door]:
    """
    Find doors matching the given noun and optional adjective.

    Args:
        doors: List of doors in current room
        noun: Must be "door"
        adjective: Optional adjective from parsed command
        vocabulary_adjectives: Parser's adjective vocabulary

    Returns:
        List of doors matching the criteria (may be 0, 1, or many)
    """
```

**Matching Logic**:
1. If no adjective provided: return all doors
2. If adjective provided:
   - Extract adjectives for each door using `extract_door_adjectives()`
   - Return only doors whose adjective list contains the specified adjective
   - Match is case-insensitive
   - **Works with both true adjectives (WordType.ADJECTIVE) and directions used as adjectives**

**Examples**:
- Room has wooden door (north) and iron door (east)
- `find_matching_doors(doors, "door", "wooden")` → `[wooden_door]`
- `find_matching_doors(doors, "door", "north")` → `[wooden_door]`
- `find_matching_doors(doors, "door", "east")` → `[iron_door]`
- `find_matching_doors(doors, "door", "locked")` → `[iron_door]` (if only iron is locked)
- `find_matching_doors(doors, "door", None)` → `[wooden_door, iron_door]`

**Direction Word Handling**:

When a user types a direction word in adjective position, the system treats it as an adjective for door matching purposes:

- Parser recognizes "north" as WordType.DIRECTION
- But in context of "open north door", "north" acts as an adjective
- Matching logic accepts both parsed adjectives AND direction words
- Implementation: Check both `command.direct_adjective` and `command.direction` when extracting user's descriptor

### 3. Disambiguation System

**Implementation Location**: New function in `simple_engine.py`

```python
def disambiguate_door(doors: List[Door], action: str) -> Optional[Door]:
    """
    Ask user to choose between multiple doors.

    Args:
        doors: List of door candidates (2 or more)
        action: The action being performed ("open", "close", "examine")

    Returns:
        Selected door, or None if user cancels/invalid input
    """
```

**Disambiguation Flow**:

1. **Generate door labels** from descriptions and directions:
   - Parse first distinctive word from description (wooden, iron, etc.)
   - **Append direction in parentheses** if available
   - Fallback to door.id if no distinctive word found

2. **Display options**:
   ```
   Which door do you want to open?
   1. wooden door (north)
   2. iron door (east)
   ```

3. **Accept user input**:
   - Number (1, 2, ...)
   - Adjective word ("wooden", "iron")
   - **Direction word ("north", "east")**
   - "cancel" or empty input to abort

4. **Validate and return**:
   - Valid number/adjective/direction → return selected door
   - Invalid input → print error, re-prompt (max 3 attempts)
   - Cancel → return None

**Label Extraction**:
```python
def get_door_label(door, current_location, vocabulary_adjectives) -> str:
    """
    Get a short label for a door from its description and location.

    Priority:
    1. First vocabulary adjective in description
    2. First capitalized word (proper noun)
    3. door.id as last resort

    Format:
    - If direction available: "{adjective} door ({direction})"
    - Otherwise: "{adjective} door"
    """
```

**Examples of Labeled Doors**:
```
"wooden door (north)"      # Has adjective and direction
"iron door (east)"         # Has adjective and direction
"door (up)"                # No distinctive adjective, has direction
"door_mysterious"          # No adjective or direction, uses ID
```

### 4. Modified Door Interaction Functions

Update these existing functions to use the new matching system:

#### `examine_item(state, item_name)` Changes

**Current behavior**: If `item_name == "door"`, shows all doors

**New behavior**:
1. Get parsed command adjective from global/parameter
2. Call `find_matching_doors(doors, "door", adjective, vocab)`
3. If 0 matches: "You don't see that kind of door here."
4. If 1 match: Show that door's details
5. If multiple matches: Call `disambiguate_door()`, then show selected door

#### `open_item(state, item_name)` Changes

**Current behavior**: If `item_name == "door"`, picks first closed door

**New behavior**:
1. Get parsed command adjective from global/parameter
2. Call `find_matching_doors(doors, "door", adjective, vocab)`
3. If 0 matches: "You don't see that kind of door here."
4. If 1 match: Attempt to open that door
5. If multiple matches: Call `disambiguate_door()`, then open selected door

#### `close_door(state, item_name)` Changes

**Current behavior**: If `item_name == "door"`, picks first open door

**New behavior**:
1. Get parsed command adjective from global/parameter
2. Call `find_matching_doors(doors, "door", adjective, vocab)`
3. If 0 matches: "You don't see that kind of door here."
4. If 1 match: Attempt to close that door
5. If multiple matches: Call `disambiguate_door()`, then close selected door

### 5. Command Handler Integration

**Challenge**: Current command handlers don't have access to adjective from parsed command

**Solution**: Modify function signatures to accept `ParsedCommand` object instead of just noun string

**Before**:
```python
case _ if result.verb.word == "open" and result.direct_object:
    open_result = open_item(state, result.direct_object.word)
```

**After**:
```python
case _ if result.verb.word == "open" and result.direct_object:
    open_result = open_item(state, result)  # Pass full ParsedCommand
```

**Updated Signatures**:
```python
def examine_item(state: GameState, command: ParsedCommand) -> bool:
    """Examine an item or door, using adjective/direction if provided."""
    item_name = command.direct_object.word if command.direct_object else None
    # Extract descriptor - could be adjective OR direction
    descriptor = None
    if command.direct_adjective:
        descriptor = command.direct_adjective.word
    elif command.direction and item_name:  # Direction used as adjective
        descriptor = command.direction.word
    # ... rest of function

def open_item(state: GameState, command: ParsedCommand):
    """Open an item or door, using adjective/direction if provided."""
    # Similar pattern - check both direct_adjective and direction

def close_door(state: GameState, command: ParsedCommand):
    """Close a door, using adjective/direction if provided."""
    # Similar pattern - check both direct_adjective and direction
```

**Key Implementation Detail**:

The descriptor extraction must check BOTH `command.direct_adjective` and `command.direction` because:
- "open wooden door" → `direct_adjective = "wooden"`
- "open north door" → `direction = "north"` (parser treats it as direction, not adjective)

Helper function recommended:
```python
def get_descriptor_from_command(command: ParsedCommand) -> Optional[str]:
    """
    Extract the descriptor (adjective or direction) from a parsed command.

    Returns the first available from:
    1. direct_adjective.word
    2. direction.word (if direct_object is present)

    This handles both:
    - "open wooden door" (adjective)
    - "open north door" (direction as adjective)
    """
    if command.direct_adjective:
        return command.direct_adjective.word
    elif command.direction and command.direct_object:
        return command.direction.word
    return None
```

### 6. Parser Access in simple_engine

**Challenge**: Need access to vocabulary adjectives for matching

**Solution**: Store parser reference or vocabulary in global scope

**Implementation**:
```python
# At module level in simple_engine.py
parser = None  # Set during main() initialization

def main():
    global parser
    parser = Parser("data/vocabulary.json")
    # ... rest of main
```

Or create a helper:
```python
def get_vocabulary_adjectives(parser: Parser) -> List[str]:
    """Extract list of valid adjectives from parser vocabulary."""
    return [entry.word for entry in parser.word_table
            if entry.word_type == WordType.ADJECTIVE]
```

## Example Usage Scenarios

### Scenario 1: Single Door, No Adjective
```
> open door
You open the door.
```
**Flow**: Matches 1 door, opens it directly

### Scenario 2: Single Door, With Adjective
```
> open wooden door
You open the wooden door.
```
**Flow**: Matches 1 door (the wooden one), opens it directly

### Scenario 3: Multiple Doors, No Adjective
```
> open door
Which door do you want to open?
1. wooden door (north)
2. iron door (east)
> 1
You open the wooden door.
```
**Flow**: Matches 2 doors, disambiguates with directions shown, opens selected

### Scenario 4: Multiple Doors, Specific Adjective
```
> open iron door
The door is locked. You need a key.
```
**Flow**: Matches 1 door (iron), attempts to open, locked

### Scenario 5: Multiple Doors, Ambiguous Adjective
```
> examine locked door
Which locked door do you want to examine?
1. iron door (east)
2. steel door (west)
> iron
A heavy iron door with a sturdy lock.
  The door is locked.
```
**Flow**: Both doors are locked, disambiguates, examines selected

### Scenario 6: State-Based Adjective
```
> close open door
You close the wooden door.
```
**Flow**: Only wooden door is open, matches 1, closes it

### Scenario 7: No Matching Doors
```
> open golden door
You don't see a golden door here.
```
**Flow**: No doors match "golden" adjective

### Scenario 8: Direction as Adjective (NEW)
```
> open north door
You open the wooden door.
```
**Flow**: "north" acts as adjective, matches wooden door in north direction

### Scenario 9: Direction with Disambiguation (NEW)
```
> examine door
Which door do you want to examine?
1. wooden door (north)
2. iron door (east)
> east
A heavy iron door with a sturdy lock.
  The door is locked.
```
**Flow**: User responds to disambiguation with direction word

### Scenario 10: Compound Selection (NEW)
```
> open locked door
Which locked door do you want to open?
1. iron door (east)
2. steel door (west)
> east
The door is locked. You need a key.
```
**Flow**: "locked" narrows to 2 doors, direction "east" disambiguates

### Scenario 11: Unambiguous Direction (NEW)
```
> close east door
You close the iron door.
```
**Flow**: Only one door to the east, direct match, no disambiguation needed

## Data Structure Changes

### Door Model (state_manager/models.py)
**No changes required** - existing structure supports everything needed

### Game State JSON
**Optional Enhancement** - Add explicit `adjectives` field to doors for clarity

**Current** (works with extraction):
```json
{
  "id": "door_wooden",
  "description": "A simple wooden door.",
  "locked": false,
  "open": true
}
```

**Optional Enhanced**:
```json
{
  "id": "door_wooden",
  "description": "A simple wooden door.",
  "adjectives": ["wooden", "simple"],  // Explicit list
  "locked": false,
  "open": true
}
```

**Recommendation**: Start with extraction-based approach (no JSON changes). Add explicit `adjectives` field only if extraction proves insufficient.

## Implementation Complexity

### Low Complexity Components
1. `extract_door_adjectives()` - Simple string parsing and state checks
2. `find_matching_doors()` - List filtering
3. Vocabulary updates - Add 3 adjectives to JSON

### Medium Complexity Components
1. `disambiguate_door()` - User interaction loop, input validation
2. `get_door_label()` - Heuristics for good labels
3. Function signature updates - Mechanical but touches many places

### High Complexity Considerations
1. **Testing disambiguation flow** - Requires input mocking
2. **Edge cases** - Doors with no distinctive adjectives, all doors match adjective
3. **User experience** - Good labels, clear prompts, helpful error messages

## Testing Strategy

### Unit Tests Needed
1. `test_extract_door_adjectives()` - Various descriptions, states
2. `test_find_matching_doors()` - 0/1/many matches, case sensitivity
3. `test_get_door_label()` - Label extraction from descriptions
4. `test_disambiguate_door()` - Mock input, number/word/cancel inputs

### Integration Tests Needed
1. Full command flow with adjectives
2. Disambiguation prompts and responses
3. Error cases (no matches, invalid disambiguation input)

### Manual Testing Scenarios
1. All example scenarios listed above
2. Edge cases: Room with 3+ doors, identical descriptions
3. Stress test: Very long descriptions, special characters

## Migration Path

### Phase 1: Foundation (No Breaking Changes)
1. Add new helper functions
2. Add vocabulary adjectives
3. Update function signatures (maintain backward compatibility)
4. Write unit tests

### Phase 2: Integration
1. Update command handlers to pass `ParsedCommand`
2. Integrate matching logic into door interaction functions
3. Add disambiguation for multiple matches

### Phase 3: Polish
1. Improve door label extraction
2. Add helpful messages for edge cases
3. Optimize adjective extraction performance
4. Consider adding explicit `adjectives` field to JSON if needed

## Edge Cases and Special Considerations

### Directional Edge Cases

1. **Door Not Visible from Current Side**
   - Problem: A door connects two locations, but may have different directions from each side
   - Example: "north" from room A, "south" from room B (same door)
   - Solution: Extract direction from *current* location's exits only
   - Result: Direction adjectives are location-specific

2. **No Direction Available**
   - Problem: Door exists in room but has no exit (e.g., door object placed as decoration)
   - Solution: Skip directional adjective, rely on description adjectives only
   - Label: "wooden door" (no direction suffix)

3. **Same Door, Multiple Exits**
   - Problem: Circular room with north and northeast both going to same door
   - Solution: Include all applicable directions in adjective list
   - Result: `["wooden", "north", "northeast"]` - either direction matches

4. **Direction Conflicts with Description**
   - Problem: Door description says "eastern door" but exit is to the west
   - Solution: Both words become valid adjectives (from description + from exit)
   - User can say: "west door" or "eastern door" - both work
   - Preference: Exit direction is more reliable than description text

### Parser Challenges with Directions

1. **Direction as Standalone Command**
   - `north` → move north (existing behavior)
   - `open north door` → open the door in north direction (new behavior)
   - Solution: Context matters - if "door" noun present, treat "north" as adjective

2. **Preposition Ambiguity**
   - `go to north door` - "north" could be direction or adjective
   - Current parser may not support "to north door" pattern well
   - Recommendation: Keep it simple - "go north" or "open north door", not mixed

3. **Adjective Position in ParsedCommand**
   - "open north door" - parser sees: direction="north", direct_object="door"
   - Need to check BOTH `command.direction` and `command.direct_adjective`
   - When extracting user's descriptor, look in multiple places

## Alternative Approaches Considered

### Alternative 1: Door Names Instead of Adjectives
**Approach**: Give each door a proper name ("wooden door", "iron door") as a noun

**Pros**: Simpler matching, no adjective parsing needed

**Cons**:
- Pollutes noun vocabulary with many door variants
- Doesn't support state-based adjectives (locked, open)
- Less flexible for future items

**Decision**: Rejected - adjective approach is more flexible

### Alternative 2: Always Disambiguate
**Approach**: Always show numbered list, even with one door

**Pros**: Consistent interface

**Cons**:
- Tedious for common case (single door)
- Breaks existing command patterns

**Decision**: Rejected - only disambiguate when necessary

### Alternative 3: Smart Defaults Without Prompting
**Approach**: Apply heuristics (prioritize closed/locked) and proceed without asking

**Pros**: Faster interaction

**Cons**:
- Surprising behavior ("I wanted the OTHER door!")
- Hard to undo mistakes
- Hidden assumptions

**Decision**: Rejected - explicit is better than implicit for ambiguous commands

## Open Questions

1. **Should disambiguation remember last selection?**
   - e.g., "open door" → "1", then "close door" defaults to same door?
   - **Recommendation**: No, too much state to track initially

2. **Maximum disambiguation attempts before giving up?**
   - **Recommendation**: 3 attempts, then return to main prompt

3. **Should we support multi-word adjectives?**
   - e.g., "ancient wooden door"
   - **Recommendation**: Not initially - single adjective is sufficient

4. **Case sensitivity for user disambiguation input?**
   - **Recommendation**: Case-insensitive matching

5. **Should direction be shown in disambiguation?**
   - e.g., "wooden door (north)" vs "wooden door"
   - **Recommendation**: Yes, if available from exit direction ✅ IMPLEMENTED IN DESIGN

6. **What if user types direction without "door"?**
   - e.g., "open north" vs "go north"
   - **Recommendation**: "open north" should trigger movement, not door opening (maintain existing behavior)
   - Only "open north door" should use direction as adjective

## Success Criteria

1. ✓ User can type "open wooden door" and it works
2. ✓ User can type "examine locked door" and see only locked doors
3. ✓ User can type "open north door" and it works (directional adjectives)
4. ✓ User can type "close east door" and it works (directional adjectives)
5. ✓ Ambiguous commands trigger helpful disambiguation prompts
6. ✓ Disambiguation accepts numbers, adjectives, AND directions
7. ✓ Disambiguation displays directions in labels: "wooden door (north)"
8. ✓ No breaking changes to existing commands
9. ✓ Clear error messages when no doors match
10. ✓ Works with any number of doors (0, 1, 2, 3+)
11. ✓ State-based adjectives (locked, open, closed) work correctly
12. ✓ Direction adjectives are location-specific (same door, different directions per room)

## Summary of Directional Additions

The following extensions were added to support directional/location-based adjectives:

### Data Flow for Directional Adjectives

1. **Extraction** (`extract_door_adjectives`)
   - Query current location's exits for doors
   - Find which direction(s) lead to this door
   - Add direction(s) to door's adjective list

2. **Matching** (`find_matching_doors`)
   - Accept directions (north, east, etc.) as valid descriptors
   - Parse user's direction from either `command.direct_adjective` or `command.direction`

3. **Display** (`get_door_label`, `disambiguate_door`)
   - Show direction in parentheses: "wooden door (north)"
   - Accept direction words as valid disambiguation responses

4. **Edge Cases**
   - Same door, different directions per location (location-specific)
   - Multiple exits to same door (include all directions)
   - Doors with no exit (skip directional adjective)

### New Functions Required

```python
def get_door_direction(door, current_location) -> Optional[str]:
    """Find exit direction for a door from current location."""

def get_descriptor_from_command(command) -> Optional[str]:
    """Extract descriptor from adjective OR direction field."""
```

### Modified Functions

- `extract_door_adjectives(door, state, vocab)` - Added `state` parameter for location lookup
- `get_door_label(door, current_location, vocab)` - Added `current_location` for direction
- All door interaction functions - Check both adjective and direction fields

## Future Enhancements

1. **Apply to all items, not just doors** - Use adjectives for chests, keys, swords, etc.
2. **Multi-word adjectives** - "ancient wooden door"
3. **Fuzzy matching** - "wood door" matches "wooden door"
4. **Adjective synonyms** - "shut" matches "closed"
5. **Remember context** - Track recently referenced doors for pronoun resolution ("it")
6. **Spatial references** - "the door on the left", "northern door"
7. **Relative directions** - "the door behind me", "the door ahead"
