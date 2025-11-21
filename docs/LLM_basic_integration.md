# LLM Basic Integration Design

## Overview

This document describes the basic integration between Claude and the text adventure game engine. Claude serves as both the **intent parser** (converting natural language to game commands) and the **narrator** (describing results in immersive prose).

### Design Principles

1. **Vocabulary-driven commands**: Claude uses `vocabulary.json` to understand available actions
2. **Structured communication**: JSON commands and results between Claude and engine
3. **Graceful failure handling**: Failures are narrated as in-world events
4. **Clarification over assumption**: Claude asks when input is ambiguous
5. **Hidden state queries**: Claude can inspect state without user seeing the interaction

## Architecture

```
Player Input (natural language)
       ↓
Claude (Intent Parser)
       ↓ [may query state silently]
       ↓ [may ask clarifying questions]
Game Commands (JSON)
       ↓
Game Engine
       ↓
Structured Results (JSON)
       ↓
Claude (Narrator)
       ↓
Rich Description (to player)
```

## Command Format

### From Claude to Engine

```json
{
  "type": "command",
  "actions": [
    {
      "verb": "take",
      "object": "key",
      "adjective": "silver"
    }
  ]
}
```

Multiple actions for compound commands:
```json
{
  "type": "command",
  "actions": [
    {"verb": "unlock", "object": "door", "adjective": "north"},
    {"verb": "open", "object": "door", "adjective": "north"},
    {"verb": "go", "direction": "north"}
  ]
}
```

### State Query (Hidden from User)

Claude can query state without the player seeing:
```json
{
  "type": "query",
  "target": "location",
  "include": ["items", "npcs", "exits", "doors"]
}
```

```json
{
  "type": "query",
  "target": "inventory"
}
```

```json
{
  "type": "query",
  "target": "item",
  "id": "item_silver_key"
}
```

Query responses include relevant `llm_context` (traits, state_variants, atmosphere).

## Result Format

### From Engine to Claude

Success result:
```json
{
  "success": true,
  "action": "take",
  "item": {
    "id": "item_silver_key",
    "name": "Silver Key",
    "llm_context": {
      "traits": ["raven-shaped bow", "tarnished silver", "surprisingly heavy"],
      "state_variants": {
        "in_inventory": "cold weight in your pocket"
      }
    }
  },
  "location": {
    "name": "Crypt Entrance",
    "atmosphere": "foreboding, ancient"
  }
}
```

Failure result:
```json
{
  "success": false,
  "action": "unlock",
  "error": "missing_key",
  "door": {
    "id": "door_iron",
    "name": "iron door",
    "llm_context": {
      "traits": ["heavy iron gate", "raven sigil on lock", "rust around hinges"]
    }
  },
  "requires": "key_raven",
  "message": "The door is locked. You need the correct key."
}
```

### State Changes in Results

Results include state changes for the narrator to incorporate:
```json
{
  "success": true,
  "action": "open",
  "door": {
    "id": "door_iron",
    "name": "iron door",
    "state_change": {
      "from": {"open": false, "locked": true},
      "to": {"open": true, "locked": false}
    }
  }
}
```

## Ambiguity Handling

### When Claude Should Ask

1. **Multiple matching objects**: "Which key do you mean - the silver key or the brass key?"
2. **Unclear verb intent**: "Do you want to examine the door or open it?"
3. **Missing required information**: "Which direction do you want to go?"
4. **Potentially destructive actions**: "Are you sure you want to attack the guard?"

### When Claude Should Infer

1. **Single matching object**: "take key" when only one key exists
2. **Context from recent actions**: "unlock it" refers to the last-mentioned door
3. **Standard conventions**: "n" means "go north"

### Clarification Format

Claude presents clarifying questions conversationally:

```
Which door do you mean?
  1. wooden door (north) - closed
  2. iron door (east) - locked

You can say the number, direction, or describe it.
```

The player's response goes through the same intent parsing process.

## Failure Narration

### Immediate Failure Reporting

Failures are narrated as events in the game world, not system errors:

**Bad**: "Error: Door is locked"

**Good**: "You grasp the iron handle and pull, but the heavy door doesn't budge. The raven-sigil lock holds fast - you'll need the right key."

### Failure Context

The narrator uses:
- Door/item traits for vivid description
- State information (locked, blocked, etc.)
- What's required (specific key, action, etc.)
- Atmosphere of location

### Cascading Failure Visibility

Failed actions leave visible consequences:

```json
{
  "success": false,
  "action": "unlock",
  "error": "wrong_key",
  "consequence": {
    "type": "evidence",
    "description": "scratch marks on lock",
    "visible_in": ["examine door", "examine lock"]
  }
}
```

Player later sees: "The iron lock shows fresh scratch marks where someone tried the wrong key."

## State Query Protocol

### Hidden Queries

Claude queries state silently to provide better responses:

```
Player: "What am I carrying?"

[Hidden query: {"type": "query", "target": "inventory"}]

Claude: "You're carrying the silver key (cold against your leg),
a worn leather satchel, and three gold coins."
```

### Query Uses

1. **Context gathering**: Before narrating, query for traits/atmosphere
2. **Ambiguity resolution**: Query to see what objects are present
3. **State verification**: Check if action is possible before attempting
4. **Rich description**: Get full context for immersive narration

### Query Frequency

- Query before any narration that mentions game objects
- Cache recent queries to avoid redundant calls
- Include necessary context in results to minimize follow-up queries

## Command Batching

### Atomic vs Partial Execution

**Atomic batch** (all or nothing):
```json
{
  "type": "command",
  "batch_mode": "atomic",
  "actions": [
    {"verb": "unlock", "object": "door"},
    {"verb": "open", "object": "door"},
    {"verb": "go", "direction": "north"}
  ]
}
```
If any action fails, none execute. Engine returns what would have failed.

**Sequential batch** (execute until failure):
```json
{
  "type": "command",
  "batch_mode": "sequential",
  "actions": [
    {"verb": "unlock", "object": "door"},
    {"verb": "open", "object": "door"},
    {"verb": "go", "direction": "north"}
  ]
}
```
Execute actions in order, stop at first failure, return what succeeded and what failed.

### Narrating Partial Success

For sequential batches with partial failure:

```json
{
  "results": [
    {"success": true, "action": "unlock", ...},
    {"success": true, "action": "open", ...},
    {"success": false, "action": "go", "error": "blocked_by_npc", ...}
  ]
}
```

Narration: "You unlock the iron door and swing it open, but the ghostly guard materializes in the doorway, blocking your path."

## System Prompts

### Intent Parser Prompt

```
You are the command interpreter for a text adventure game.

VOCABULARY:
{contents of vocabulary.json}

CURRENT STATE:
{relevant state from query}

Convert the player's input into game commands. You may:
- Ask clarifying questions if the intent is ambiguous
- Query game state silently to resolve ambiguity
- Infer from context when reasonable

Output JSON commands using only verbs, nouns, adjectives, and directions from the vocabulary.

If you cannot interpret the input, explain what you don't understand.
```

### Narrator Prompt

```
You are the narrator for a text adventure game.

RULES:
1. Use ONLY information from traits - never invent details
2. Narrate failures as in-world events, not system errors
3. Describe consequences that will be visible later
4. Use atmosphere and state_variants to set tone
5. Include at least 2-3 traits in each description
6. Be concise but evocative

RESULT TO NARRATE:
{engine result with full context}
```

## Example Flows

### Successful Action

```
Player: "I want to grab that shiny key on the table"

[Query: inventory and current location]

Claude → Engine:
{
  "type": "command",
  "actions": [{"verb": "take", "object": "key", "adjective": "silver"}]
}

Engine → Claude:
{
  "success": true,
  "action": "take",
  "item": {
    "name": "Silver Key",
    "llm_context": {
      "traits": ["raven-shaped bow", "tarnished silver", "surprisingly heavy"],
      "state_variants": {"in_inventory": "cold weight in your pocket"}
    }
  }
}

Claude → Player:
"You lift the silver key from the dusty table. It's surprisingly
heavy, the raven-shaped bow cold against your palm."
```

### Failed Action with Visible Consequence

```
Player: "open the door"

Claude → Engine:
{
  "type": "command",
  "actions": [{"verb": "open", "object": "door", "adjective": "iron"}]
}

Engine → Claude:
{
  "success": false,
  "action": "open",
  "error": "locked",
  "door": {
    "name": "iron door",
    "llm_context": {
      "traits": ["heavy iron gate", "raven sigil on lock"],
      "state_variants": {"locked": "holds fast against your efforts"}
    }
  },
  "requires": "key_raven"
}

Claude → Player:
"You grab the cold iron handle and heave, but the heavy door
holds fast. The raven sigil on the lock seems to watch you -
you'll need the right key."
```

### Ambiguity Resolution

```
Player: "unlock the door"

[Query reveals two doors in room]

Claude → Player:
"Which door do you want to unlock?
  1. wooden door (north) - closed
  2. iron door (east) - locked"

Player: "the iron one"

Claude → Engine:
{
  "type": "command",
  "actions": [{"verb": "unlock", "object": "door", "adjective": "iron"}]
}
```

### Multi-Step Command with Partial Failure

```
Player: "unlock the door, open it, and go through"

Claude → Engine:
{
  "type": "command",
  "batch_mode": "sequential",
  "actions": [
    {"verb": "unlock", "object": "door", "adjective": "iron"},
    {"verb": "open", "object": "door", "adjective": "iron"},
    {"verb": "go", "direction": "east"}
  ]
}

Engine → Claude:
{
  "results": [
    {"success": false, "action": "unlock", "error": "wrong_key", ...}
  ],
  "not_attempted": ["open", "go"]
}

Claude → Player:
"You try the silver key in the lock, but it doesn't fit - the
raven sigil on the lock requires a matching key. The door
remains firmly locked."
```

## Implementation Notes

### Engine Changes Required

1. **JSON input parser**: Accept JSON alongside string commands
2. **Query endpoint**: Return state with llm_context
3. **Structured results**: Return detailed JSON results
4. **Consequence tracking**: Record visible effects of failed actions

### New Data Structures

```python
@dataclass
class CommandRequest:
    type: str  # "command" or "query"
    actions: Optional[List[Action]]
    batch_mode: Optional[str]  # "atomic" or "sequential"
    target: Optional[str]  # for queries

@dataclass
class ActionResult:
    success: bool
    action: str
    error: Optional[str]
    context: Dict  # entity with llm_context
    state_change: Optional[Dict]
    consequence: Optional[Dict]
```

### Integration Points

1. **simple_engine.py**: Add JSON command handling in game loop
2. **parser.py**: Add method to create ParsedCommand from JSON
3. **state_manager**: Add query methods for llm_context
4. **models.py**: Extend entities with llm_context fields

## Error Handling

### Engine Errors vs Game Failures

- **Engine errors** (bugs, missing data): Return error JSON, Claude reports technical issue
- **Game failures** (locked door, no item): Return failure result, Claude narrates in-world

### Validation

Engine validates commands before execution:
```json
{
  "valid": false,
  "error": "unknown_verb",
  "verb": "teleport",
  "message": "I don't understand 'teleport'"
}
```

Claude responds: "I don't understand what you mean by 'teleport'. Try actions like go, take, open, or examine."

## Future Enhancements

1. **Pronoun resolution**: Track recent references for "it", "them"
2. **Command history**: Allow "again" or "undo"
3. **Context memory**: Remember player's style preferences
4. **Adaptive verbosity**: Shorter descriptions for familiar locations
5. **NPC dialogue**: Extended conversation system
6. **Skill checks**: Probabilistic action outcomes

## Related Documents

- [llm_front_end_design_sketch.md](llm_front_end_design_sketch.md) - Full LLM design with traits system
- [vocabulary.json](../data/vocabulary.json) - Available verbs, nouns, adjectives
- [door_selection.md](door_selection.md) - Adjective-based disambiguation
