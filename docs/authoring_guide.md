# Handler Authoring Guide

This guide documents utility routines and patterns for writing behavior handlers. It complements the debugging_guide.md with focus on authoring new handlers.

## Quick Reference

### Essential Imports

```python
# Types and core
from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult, StateAccessor
from src.types import ActorId, LocationId
from src.word_entry import WordEntry

# Handler utilities
from utilities.handler_utils import (
    validate_actor_and_location,    # Standard handler preamble
    find_action_target,             # Find item from action dict
    find_openable_target,           # Smart door/container finder
    get_object_word,                # Extract word from WordEntry
    get_display_name,               # User-friendly name
    execute_entity_action,          # Action with behavior invocation
    transfer_item_to_actor,         # Add item to inventory
    transfer_item_from_actor,       # Remove item from inventory
    build_action_result,            # Build HandlerResult
)

# Entity utilities
from utilities.utils import (
    find_accessible_item,           # Find item by name
    find_actor_by_name,             # Find actor by name
    name_matches,                   # Name comparison with synonyms
    is_observable,                  # Check visibility
    _extract_word,                  # WordEntry to string
)

# Serialization
from utilities.entity_serializer import serialize_for_handler_result

# Infrastructure utilities
from src.infrastructure_utils import (
    get_current_turn,               # Get turn number
    get_current_state,              # Get state machine current state
    transition_state,               # Transition state machine
    get_actor_conditions,           # Get conditions list
    has_condition,                  # Check if has condition
    modify_trust,                   # Change trust value
    get_bool_flag,                  # Read bool flag
    set_bool_flag,                  # Set bool flag
    create_gossip,                  # Create gossip event
)

# Handler loading (for item_use_reactions, etc.)
from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
```

---

## Handler Return Types

### EventResult (for event handlers)

Event handlers return `EventResult` to control event flow:

```python
from src.behavior_manager import EventResult

# Allow event with no message
return EventResult(allow=True, feedback=None)

# Allow event with message
return EventResult(
    allow=True,
    feedback="The door creaks as you open it."
)

# Block event with message
return EventResult(
    allow=False,
    feedback="The door is locked."
)
```

### HandlerResult (for command handlers)

Command handlers return `HandlerResult` with richer output:

```python
from src.state_accessor import HandlerResult

# Success with message
return HandlerResult(
    success=True,
    primary="You pick up the sword."
)

# Success with beats (secondary messages)
return HandlerResult(
    success=True,
    primary="You open the chest.",
    beats=["It creaks ominously.", "A spider scurries out."],
    data=serialize_for_handler_result(item, accessor, actor_id)
)

# Failure
return HandlerResult(
    success=False,
    primary="The door is locked."
)
```

---

## Common Handler Patterns

### 1. Standard Command Handler Preamble

Use `find_action_target` for most item-targeting handlers:

```python
def handle_read(accessor, action):
    """Handle read command."""
    item, error = find_action_target(accessor, action)
    if error:
        return error

    # item is guaranteed to exist here
    actor_id = action.get("actor_id") or ActorId("player")

    # Check if readable
    if not item.properties.get("readable", False):
        return HandlerResult(
            success=False,
            primary=f"You can't read the {item.name}."
        )

    text = item.properties.get("text", "")
    return HandlerResult(
        success=True,
        primary=f"You read the {item.name}: {text}",
        data=serialize_for_handler_result(item, accessor, actor_id)
    )
```

### 2. Extended Preamble for Complex Handlers

Use `validate_actor_and_location` when you need actor and location:

```python
def handle_put(accessor, action):
    """Handle put X in/on Y command."""
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action,
        require_object=True,
        require_indirect_object=True
    )
    if error:
        return error

    # Now have: actor_id, actor, location all validated
    object_name = action.get("object")
    container_name = action.get("indirect_object")
    # ... continue with handler logic
```

### 3. Event Handler for Entity Behaviors

Event handlers are invoked via `accessor.update()` or registered hooks:

```python
def on_spore_mother_heal(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle healing Spore Mother with heartmoss."""
    state = accessor.game_state

    # Get the target (if item_use_reactions)
    target = context.get("target")

    # Check item
    item_id = entity.id if hasattr(entity, "id") else str(entity)
    if "heartmoss" not in item_id.lower():
        return EventResult(allow=True, feedback=None)

    # Perform state changes
    mother = state.actors.get("npc_spore_mother")
    if mother:
        sm = mother.properties.get("state_machine", {})
        transition_state(sm, "allied")

    return EventResult(
        allow=True,
        feedback="The Spore Mother's pain eases. She radiates gratitude."
    )
```

### 4. Talk/Dialog Handler Pattern

For NPCs without standard dialog_topics (empathic, gestural, etc.):

```python
def on_npc_talk(entity, accessor, context):
    """Handle talk/ask commands for non-verbal NPC."""
    state = accessor.game_state

    # Get NPC and current state
    npc = state.actors.get("npc_id")
    if not npc:
        return EventResult(allow=True, feedback=None)

    sm = npc.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "initial"))

    # Different responses based on state
    responses = {
        "hostile": "The creature hisses, spines raised defensively.",
        "wary": "It watches you carefully, neither attacking nor approaching.",
        "friendly": "It chirps softly in greeting.",
    }

    feedback = responses.get(current_state, "It regards you silently.")
    return EventResult(allow=True, feedback=feedback)
```

---

## Entity Access Patterns

### Accessing Game State

Always use `accessor.game_state`, NOT `accessor.state`:

```python
def my_handler(entity, accessor, context):
    state = accessor.game_state  # Correct!

    # Access actors
    player = state.actors.get("player")
    npc = state.actors.get("npc_aldric")

    # Access items
    item = state.get_item("heartmoss")  # Use get_item(), NOT items.get()

    # Access locations
    location = state.get_location("spore_heart")

    # Access extra data
    turn = state.extra.get("turn_count", 0)
    flags = state.extra.get("flags", {})
```

### Finding Items

```python
from utilities.utils import find_accessible_item

# Find item accessible to actor (in inventory, location, or container)
item = find_accessible_item(accessor, object_name, actor_id, adjective)

# object_name and adjective are WordEntry from action dict
# Returns None if not found
```

### Finding Actors

```python
from utilities.utils import find_actor_by_name

# Find actor in same location as another actor
actor = find_actor_by_name(accessor, name_word_entry, searching_actor_id)

# name_word_entry is WordEntry from action dict
# Returns None if not found
```

### Checking Name Matches

```python
from utilities.utils import name_matches

# Check if WordEntry matches a target name
if name_matches(word_entry, "Spore Mother"):
    # Matches "mother", "spore mother", synonyms, etc.
    pass
```

---

## Inventory Operations

### Adding Item to Actor's Inventory

```python
from utilities.handler_utils import transfer_item_to_actor

# This handles behaviors, rollback on failure, and inventory update
result, error = transfer_item_to_actor(
    accessor,
    item,
    actor,
    actor_id,
    verb="take",
    item_changes={"location": actor_id},
    rollback_location=original_location
)
if error:
    return error

# result contains behavior feedback
```

### Manually Adding to Inventory

For reward handlers where you give items directly:

```python
# Get the item
fragment = state.get_item("spore_heart_fragment")
if fragment:
    # Set location AND add to inventory list
    fragment.location = "player"
    player = state.actors.get("player")
    if player and fragment.id not in player.inventory:
        player.inventory.append(fragment.id)
```

---

## State Machine Operations

### Reading Current State

```python
from src.infrastructure_utils import get_current_state

sm = actor.properties.get("state_machine", {})
current_state = get_current_state(sm)  # Returns "initial" if current not set
```

### Transitioning State

```python
from src.infrastructure_utils import transition_state

sm = actor.properties.get("state_machine", {})
success, message = transition_state(sm, "friendly")
# success is True if transition worked
# message is "Transitioned from X to Y" or error
```

### State Machine Structure

In game_state.json:
```json
{
  "id": "npc_spore_mother",
  "properties": {
    "state_machine": {
      "states": ["hostile", "wary", "communicating", "allied"],
      "initial": "hostile"
    }
  }
}
```

---

## Trust and Flags

### Trust Operations

```python
from src.infrastructure_utils import modify_trust, check_trust_threshold

# Modify trust with bounds
new_trust = modify_trust(current_trust, delta=+1, floor=-5, ceiling=5)

# Check threshold
if check_trust_threshold(current_trust, threshold=3, at_least=True):
    # Trust >= 3
    pass
```

### Flag Operations

```python
from src.infrastructure_utils import get_bool_flag, set_bool_flag, get_global_flags

# Global flags (game-wide)
flags = get_global_flags(state)
if get_bool_flag(flags, "spore_mother_healed"):
    pass
set_bool_flag(flags, "spore_mother_healed", True)

# Actor flags
actor_flags = actor.flags
set_bool_flag(actor_flags, "has_spoken", True)
```

---

## Gossip System

```python
from src.infrastructure_utils import create_gossip, get_current_turn

# Create gossip that spreads to specific NPCs
gossip_id = create_gossip(
    state,
    content="The adventurer healed the Spore Mother",
    source_npc=ActorId("npc_myconid_elder"),
    target_npcs=[ActorId("npc_aldric")],
    delay_turns=3,  # Arrives in 3 turns
)
```

---

## Vocabulary Extension

**CRITICAL**: Behavior modules MUST extend vocabulary for multi-word entity names.

### Why Vocabulary Matters

The parser auto-extracts words from entity names as **NOUNS only**. For multi-word names like "cold weather gear" or "stone pillar":
- Without vocabulary: Parser sees NOUN + NOUN + NOUN (parse fails)
- With vocabulary: Parser sees ADJ + ADJ + NOUN (parse succeeds)

**Rule**: Every word that appears BEFORE the final noun in an entity name must be added as an adjective.

### Examples

```python
# BAD: No vocabulary - "examine cold weather gear" fails to parse
vocabulary: Dict[str, Any] = {
    "events": []
}

# GOOD: Adjectives defined - "examine cold weather gear" works
vocabulary: Dict[str, Any] = {
    "adjectives": [
        {"word": "cold", "synonyms": []},
        {"word": "weather", "synonyms": []},
    ],
    "events": []
}
```

### Full Vocabulary Structure

```python
vocabulary: Dict[str, Any] = {
    "verbs": [
        {
            "word": "water",
            "word_type": ["verb", "noun"],  # Multi-type!
            "event": "on_water",
            "object_required": True,
            "synonyms": ["pour"]
        }
    ],
    "nouns": [
        {"word": "heartmoss", "synonyms": ["moss"]}
    ],
    "adjectives": [
        {"word": "spore", "synonyms": []},      # For "spore mother"
        {"word": "stone", "synonyms": []},      # For "stone pillar"
        {"word": "control", "synonyms": []},    # For "control crystal"
    ],
    "events": [
        {
            "event": "on_spore_mother_talk",
            "hook": "on_talk",
            "entity_filter": "npc_spore_mother",
            "description": "Handle Spore Mother communication",
        },
    ]
}
```

### Common Vocabulary Issues

| Entity Name | Missing Vocabulary | Fix |
|-------------|-------------------|-----|
| "cold weather gear" | cold, weather | Add as adjectives |
| "preserved supplies" | preserved | Add as adjective |
| "stone pillar" | stone | Add as adjective |
| "fire salamander" | fire | Add as adjective |
| "control crystal" | control | Add as adjective |

**Testing**: If "examine <multi-word-name>" fails to parse, you're missing adjective vocabulary.

---

## Item Use Reactions

Configure in game_state.json to trigger handlers when items are used on entities:

```json
{
  "id": "npc_spore_mother",
  "properties": {
    "item_use_reactions": {
      "healing": {
        "accepted_items": ["heartmoss"],
        "handler": "examples.big_game.behaviors.regions.fungal_depths.spore_mother:on_spore_mother_heal"
      }
    }
  }
}
```

Then "use heartmoss on spore mother" will invoke the handler.

---

## Handler Loading

For dynamic handler dispatch (item_use_reactions, dialog handlers, etc.):

```python
from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler

handler_path = "behaviors.regions.fungal_depths.spore_mother:on_spore_mother_heal"
handler = load_handler(handler_path)
if handler:
    result = handler(entity, accessor, context)
```

---

## Serialization for LLM

Always serialize entity data for the LLM narrator:

```python
from utilities.entity_serializer import serialize_for_handler_result

# Include in HandlerResult.data
return HandlerResult(
    success=True,
    primary="You examine the door.",
    data=serialize_for_handler_result(door, accessor, actor_id)
)
```

This includes llm_context for narrative generation.

---

## WordEntry Handling

Action dictionaries contain WordEntry objects, not strings:

```python
def handle_use(accessor, action):
    verb = action.get("verb")          # WordEntry
    object_name = action.get("object") # WordEntry

    # Extract string when needed
    from utilities.utils import _extract_word
    verb_str = _extract_word(verb)

    # Or use handler_utils
    from utilities.handler_utils import get_object_word
    obj_word = get_object_word(object_name)  # Returns lowercase string
```

---

## Common Pitfalls

1. **Don't use `accessor.state`** - Use `accessor.game_state`

2. **Don't use `state.items.get()`** - Items is a list, use `state.get_item(id)`

3. **Don't assume strings** - Action dict values are WordEntry, extract with helpers

4. **Don't forget inventory list** - Setting `item.location = "player"` isn't enough, must also append to `player.inventory`

5. **Don't hardcode "player"** - Use `actor_id = action.get("actor_id") or ActorId("player")`

6. **Don't skip serialization** - Include `data=serialize_for_handler_result(...)` for narrator context

---

## Testing Handlers

### Walkthrough Testing (MANDATORY)

**CRITICAL**: Every behavior change MUST be verified with walkthrough tests before being considered complete.

#### Why Walkthroughs Are Essential

1. **Catch vocabulary issues immediately** - Missing adjectives cause parse failures
2. **Verify navigation works** - Locations must be accessible
3. **Test actual playability** - Code may work but game may be unplayable
4. **Document expected behavior** - Walkthrough files serve as regression tests

#### Walkthrough Discipline

**Required process for every sub-phase/feature**:

1. ✅ Create walkthrough command file BEFORE implementation (defines "done")
2. ✅ Implement the feature
3. ✅ Run walkthrough: `python tools/walkthrough.py examples/big_game --file walkthroughs/[feature].txt`
4. ✅ Fix ALL failures (usually vocabulary, sometimes navigation)
5. ✅ Re-run until 100% success rate
6. ✅ Paste walkthrough output in GitHub issue closing comment
7. ✅ ONLY THEN mark feature complete

**Never mark work complete without 100% walkthrough success.**

#### Usage Examples

```bash
# Test specific commands
python tools/walkthrough.py examples/big_game "take bucket" "fill bucket" "pour water on mushroom"

# Test from file (preferred for features)
python tools/walkthrough.py examples/big_game --file walkthroughs/test_frozen_reaches.txt

# Verbose output (shows full JSON)
python tools/walkthrough.py examples/big_game -v "use heartmoss on spore mother"

# Save output for documentation
python tools/walkthrough.py examples/big_game --file walkthroughs/test.txt | tee walkthroughs/test_output.txt
```

#### Example Walkthrough File

```
# Frozen Reaches Spatial Test
# Tests locations, items, NPCs

# Navigate to new location
look
go north
look

# Test item interaction
examine gear
take gear

# Test NPC interaction
examine guardian
talk to salamander

# Expected: All commands succeed
```

#### Common Walkthrough Failures

| Failure Message | Cause | Fix |
|----------------|-------|-----|
| "Could not parse 'examine cold gear'" | Missing adjective vocabulary | Add "cold" as adjective |
| "You don't see any pillar here" | Wrong location or missing entity | Fix navigation or add entity |
| "I don't understand 'hide'" | Verb doesn't exist | Use different verb or add to vocabulary |
| "You can't go north from here" | Missing exit | Add exit to location |

#### Real Example: Frozen Reaches Phase 4

**First attempt**: 16/36 commands (44% success) - missing vocabulary
**Second attempt**: 32/44 commands (73% success) - wrong navigation
**Final attempt**: 28/28 commands (100% success) - all fixed

**Lesson**: Without walkthroughs, would have shipped unplayable content.

### Unit Test Pattern

```python
class TestMyHandler(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(Path("examples/big_game"))
        self.accessor = self.engine.state_accessor

    def test_my_handler(self):
        action = {
            "verb": WordEntry("use", {"VERB"}),
            "object": WordEntry("heartmoss", {"NOUN"}),
            "actor_id": ActorId("player"),
        }
        result = handle_use(self.accessor, action)
        self.assertTrue(result.success)
```

---

## Checklist for New Handlers

**BEFORE Implementation**:
- [ ] Create walkthrough test file defining expected behavior
- [ ] Identify multi-word entity names requiring vocabulary

**During Implementation**:
- [ ] Correct imports (EventResult or HandlerResult)
- [ ] Use standard preamble (find_action_target or validate_actor_and_location)
- [ ] Access game state via `accessor.game_state`
- [ ] Extract WordEntry values using helpers
- [ ] Include serialized data in successful results
- [ ] Handle inventory properly (location AND list)

**CRITICAL - Vocabulary** (Most Common Failure Point):
- [ ] Add adjective entries for EVERY word before final noun in multi-word names
  - Example: "cold weather gear" → add "cold" and "weather" as adjectives
  - Example: "stone pillar" → add "stone" as adjective
  - Example: "fire salamander" → add "fire" as adjective
- [ ] Test: Try "examine <full-name>" - if parse fails, missing vocabulary

**BEFORE Marking Complete**:
- [ ] Run walkthrough: `python tools/walkthrough.py examples/big_game --file walkthroughs/[feature].txt`
- [ ] Fix ALL failures (aim for 100% success rate)
- [ ] Re-run until 100% success
- [ ] Save walkthrough output: `... | tee walkthroughs/[feature]_output.txt`
- [ ] Paste walkthrough results in GitHub issue comment
- [ ] Add unit test (optional but recommended)
- [ ] **ONLY THEN** close issue/mark complete

**Never ship without 100% walkthrough success.**

---

## References

- [Debugging Guide](debugging_guide.md) - Parser, vocabulary, and error diagnosis
- [Infrastructure Design](big_game_work/detailed_designs/infrastructure_detailed_design.md) - State machines, gossip, commitments
- [NPC Authoring Plan](big_game_work/npc_authoring_implementation_plan.md) - Implementation workflow
