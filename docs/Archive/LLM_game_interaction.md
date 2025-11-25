# LLM-Game Engine Interaction Specification

## Overview

This document specifies the JSON message formats for communication between Claude (as intent parser and narrator) and the text adventure game engine. All interactions use structured JSON to ensure reliable parsing and clear semantics.

## Message Flow

```
Player Input (natural language)
       ↓
┌─────────────────┐
│  Claude         │
│  Intent Parser  │
└────────┬────────┘
         ↓
    [Query messages - hidden from player]
         ↓
┌─────────────────┐
│  Game Engine    │
└────────┬────────┘
         ↓
    [Query responses]
         ↓
┌─────────────────┐
│  Claude         │
│  Intent Parser  │
└────────┬────────┘
         ↓
    [Command message]
         ↓
┌─────────────────┐
│  Game Engine    │
└────────┬────────┘
         ↓
    [Result message]
         ↓
┌─────────────────┐
│  Claude         │
│  Narrator       │
└────────┬────────┘
         ↓
Rich Description (to player)
```

## Communication Boundaries

**JSON Protocol (this spec):** Claude ↔ Game Engine only
- Commands, queries, results

**Natural Language:** Claude ↔ Player
- Clarifying questions, narration, error messages

Claude handles disambiguation by asking the player in natural language, then using the response to form a proper command with adjectives.

---

## Message Types

### 1. Command Message

Sent from Claude to the game engine to execute a single player action.

```json
{
  "type": "command",
  "action": {
    "verb": "take",
    "object": "key",
    "adjective": "silver"
  }
}
```

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Always `"command"` |
| `action` | object | Yes | The action to execute |

#### Action Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verb` | string | Yes | Action verb from vocabulary |
| `object` | string | No | Target noun from vocabulary |
| `adjective` | string | No | Adjective to disambiguate object |
| `direction` | string | No | Direction for movement verbs |
| `indirect_object` | string | No | Secondary object (e.g., "unlock door with key") |
| `indirect_adjective` | string | No | Adjective for indirect object |
| `preposition` | string | No | Preposition linking objects |

#### Action Examples

**Simple action:**
```json
{
  "verb": "take",
  "object": "key"
}
```

**Action with adjective:**
```json
{
  "verb": "open",
  "object": "door",
  "adjective": "wooden"
}
```

**Direction-based action:**
```json
{
  "verb": "go",
  "direction": "north"
}
```

**Action with direction as adjective:**
```json
{
  "verb": "open",
  "object": "door",
  "adjective": "north"
}
```

**Two-object action:**
```json
{
  "verb": "unlock",
  "object": "door",
  "adjective": "iron",
  "preposition": "with",
  "indirect_object": "key",
  "indirect_adjective": "silver"
}
```

**Action without object (examine room):**
```json
{
  "verb": "examine"
}
```

#### Multi-Action Player Input

When a player issues a compound command like "take the key, unlock the door, and go through," Claude sends multiple sequential command messages, waiting for each result before sending the next. This keeps the protocol simple and allows proper narration of partial success.

> **Note:** If performance becomes an issue, we can add optional action batching in a future version.

---

### 2. Query Message

Sent from Claude to the game engine to retrieve state information. These queries are hidden from the player.

```json
{
  "type": "query",
  "query_type": "location",
  "include": ["items", "npcs", "exits", "doors"]
}
```

#### Query Types

**Current location:**
```json
{
  "type": "query",
  "query_type": "location",
  "include": ["items", "npcs", "exits", "doors", "llm_context"]
}
```

**Player inventory:**
```json
{
  "type": "query",
  "query_type": "inventory"
}
```

**Specific entity:**
```json
{
  "type": "query",
  "query_type": "entity",
  "entity_type": "item",
  "entity_id": "item_silver_key"
}
```

**Multiple entities:**
```json
{
  "type": "query",
  "query_type": "entities",
  "entity_type": "door",
  "location_id": "loc_hallway"
}
```

**Game metadata:**
```json
{
  "type": "query",
  "query_type": "metadata"
}
```

#### Query Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Always `"query"` |
| `query_type` | string | Yes | Type of query (see above) |
| `include` | array | No | Fields to include in response |
| `entity_type` | string | No | Type of entity for entity queries |
| `entity_id` | string | No | Specific entity ID |
| `location_id` | string | No | Location scope for entity queries |

---

### 3. Result Message

Sent from the game engine to Claude after executing a command.

```json
{
  "type": "result",
  "success": true,
  "action": "take",
  "entity": {
    "id": "item_silver_key",
    "name": "Silver Key",
    "type": "item",
    "llm_context": {
      "traits": ["raven-shaped bow", "tarnished silver", "surprisingly heavy"],
      "state_variants": {
        "in_inventory": "cold weight in your pocket"
      }
    }
  }
}
```

#### Result Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Always `"result"` |
| `success` | boolean | Yes | Whether the action succeeded |
| `action` | string | Yes | The verb that was executed |
| `entity` | object | No | Primary entity involved |
| `error` | object | No | Error details if failed |

---

### 4. Error Result

When an action fails, the result includes the game engine's error message. Claude elaborates this message using the entity's traits to create an immersive in-world description.

```json
{
  "type": "result",
  "success": false,
  "action": "open",
  "entity": {
    "id": "door_treasure",
    "name": "iron door",
    "llm_context": {
      "traits": ["thick iron plates", "riveted construction", "imposing presence"],
      "state_variants": {
        "locked": "sealed tight, the lock gleaming with purpose"
      }
    }
  },
  "error": {
    "message": "The door is locked. You need a key."
  }
}
```

#### Error Message Guidelines

The game engine returns human-readable error messages that Claude can elaborate. No error codes are needed - the message itself tells Claude what happened.

**Example error messages from game engine:**
- `"The door is locked. You need a key."`
- `"You don't see that here."`
- `"You can't take that."`
- `"You're not carrying that."`
- `"The door is already open."`
- `"You can't go that way."`
- `"That won't work as a key."`
- `"You can't eat that."`
- `"There's nothing to read."`

**How Claude uses them:**

1. Read the error message to understand what failed
2. Use the entity's traits and state_variants to elaborate
3. Narrate the failure as an in-world event

**Example transformation:**
- Engine message: `"The door is locked. You need a key."`
- Entity traits: `["thick iron plates", "riveted construction", "imposing presence"]`
- Claude narration: `"You heave against the iron door, but it holds fast. The thick plates don't budge - the lock gleams with purpose, waiting for the right key."`

---

### 5. Query Response

Response from the game engine to a query message.

**Location query response:**
```json
{
  "type": "query_response",
  "query_type": "location",
  "data": {
    "location": {
      "id": "loc_hallway",
      "name": "Long Hallway",
      "description": "You are in a long hallway. There is a locked door to the east and stairs going up.",
      "llm_context": {
        "traits": [
          "high vaulted ceiling",
          "stone floor worn smooth",
          "echoing footsteps",
          "draft from above",
          "faded tapestries on walls"
        ],
        "atmosphere": "transitional, mysterious, ancient",
        "state_variants": {
          "first_visit": "The hallway stretches before you, promising discoveries.",
          "revisit": "The familiar corridor, still echoing your steps."
        }
      }
    },
    "items": [
      {
        "id": "item_key",
        "name": "key",
        "description": "An iron key.",
        "llm_context": {
          "traits": ["solid iron", "intricate teeth", "cold and heavy"],
          "state_variants": {
            "in_location": "glints on the stone floor"
          }
        }
      }
    ],
    "doors": [
      {
        "id": "door_wooden",
        "description": "A simple wooden door.",
        "direction": "south",
        "open": true,
        "locked": false,
        "llm_context": {
          "traits": ["rough-hewn planks", "iron hinges", "creaks when moved"]
        }
      },
      {
        "id": "door_treasure",
        "description": "A heavy iron door with a sturdy lock.",
        "direction": "east",
        "open": false,
        "locked": true,
        "llm_context": {
          "traits": ["thick iron plates", "riveted construction", "imposing presence"]
        }
      }
    ],
    "exits": {
      "south": {"type": "door", "door_id": "door_wooden"},
      "up": {"type": "open", "to": "loc_tower"},
      "east": {"type": "door", "door_id": "door_treasure"}
    },
    "npcs": []
  }
}
```

**Inventory query response:**
```json
{
  "type": "query_response",
  "query_type": "inventory",
  "data": {
    "items": [
      {
        "id": "item_sword",
        "name": "sword",
        "description": "A rusty but serviceable sword.",
        "llm_context": {
          "traits": ["pitted blade", "leather-wrapped hilt", "still holds an edge"],
          "state_variants": {
            "in_inventory": "a reassuring weight at your side"
          }
        }
      }
    ]
  }
}
```

**Entity query response:**
```json
{
  "type": "query_response",
  "query_type": "entity",
  "data": {
    "entity": {
      "id": "item_silver_key",
      "type": "item",
      "name": "Silver Key",
      "description": "A key with a raven-shaped bow.",
      "portable": true,
      "location": "player",
      "llm_context": {
        "traits": [
          "raven-shaped bow",
          "tarnished silver",
          "surprisingly heavy",
          "cold to the touch"
        ],
        "state_variants": {
          "in_inventory": "cold weight in your pocket",
          "examined": "intricate engravings visible up close"
        }
      }
    }
  }
}
```

---

## Complete Interaction Examples

### Example 1: Simple Take Action

**Player input:** "grab that key"

**Claude sends query:**
```json
{
  "type": "query",
  "query_type": "location",
  "include": ["items"]
}
```

**Engine responds:**
```json
{
  "type": "query_response",
  "query_type": "location",
  "data": {
    "location": {"id": "loc_hallway", "name": "Long Hallway"},
    "items": [
      {
        "id": "item_key",
        "name": "key",
        "llm_context": {
          "traits": ["solid iron", "intricate teeth", "cold and heavy"]
        }
      }
    ]
  }
}
```

**Claude sends command:**
```json
{
  "type": "command",
  "action": {"verb": "take", "object": "key"}
}
```

**Engine responds:**
```json
{
  "type": "result",
  "success": true,
  "action": "take",
  "entity": {
    "id": "item_key",
    "name": "key",
    "llm_context": {
      "traits": ["solid iron", "intricate teeth", "cold and heavy"],
      "state_variants": {"in_inventory": "cold weight in your pocket"}
    }
  }
}
```

**Claude narrates to player:**
"You pick up the iron key. It's cold and surprisingly heavy, the intricate teeth suggesting a complex lock."

---

### Example 2: Failed Unlock Attempt

**Player input:** "unlock the east door with my sword"

**Claude sends command:**
```json
{
  "type": "command",
  "action": {
    "verb": "unlock",
    "object": "door",
    "adjective": "east",
    "preposition": "with",
    "indirect_object": "sword"
  }
}
```

**Engine responds:**
```json
{
  "type": "result",
  "success": false,
  "action": "unlock",
  "entity": {
    "id": "door_treasure",
    "name": "iron door",
    "llm_context": {
      "traits": ["thick iron plates", "riveted construction", "imposing presence", "cold to touch"],
      "state_variants": {"locked": "sealed tight, the lock gleaming with purpose"}
    }
  },
  "error": {
    "message": "That won't work as a key."
  }
}
```

**Claude narrates to player:**
"You try to jam your sword into the keyhole of the iron door, but the blade just scrapes against the cold metal. The imposing lock gleams mockingly - you'll need a proper key."

---

### Example 3: Multi-Action Player Input

**Player input:** "take the key, unlock the door, and go through"

Claude sends multiple sequential commands, narrating results as they complete:

**Command 1:**
```json
{
  "type": "command",
  "action": {"verb": "take", "object": "key"}
}
```

**Result 1:**
```json
{
  "type": "result",
  "success": true,
  "action": "take",
  "entity": {
    "id": "item_key",
    "name": "key",
    "llm_context": {
      "traits": ["solid iron", "intricate teeth", "cold and heavy"],
      "state_variants": {"in_inventory": "cold weight in your pocket"}
    }
  }
}
```

**Command 2:**
```json
{
  "type": "command",
  "action": {"verb": "unlock", "object": "door", "adjective": "iron"}
}
```

**Result 2:**
```json
{
  "type": "result",
  "success": true,
  "action": "unlock",
  "entity": {
    "id": "door_treasure",
    "name": "iron door",
    "llm_context": {
      "traits": ["thick iron plates", "riveted construction", "imposing presence"],
      "state_variants": {"unlocked": "the lock hangs open, defeated"}
    }
  }
}
```

**Command 3:**
```json
{
  "type": "command",
  "action": {"verb": "open", "object": "door", "adjective": "iron"}
}
```

**Result 3:**
```json
{
  "type": "result",
  "success": true,
  "action": "open",
  "entity": {
    "id": "door_treasure",
    "name": "iron door",
    "llm_context": {
      "traits": ["thick iron plates", "riveted construction", "imposing presence"],
      "state_variants": {"open": "swung wide, revealing treasures beyond"}
    }
  }
}
```

**Command 4:**
```json
{
  "type": "command",
  "action": {"verb": "go", "direction": "east"}
}
```

**Result 4 (failure):**
```json
{
  "type": "result",
  "success": false,
  "action": "go",
  "entity": {
    "id": "npc_guard",
    "name": "Ghostly Guard",
    "llm_context": {
      "traits": ["translucent armor", "hollow eyes", "stern but not hostile"]
    }
  },
  "error": {
    "message": "Something blocks your way."
  }
}
```

**Claude narrates to player:**
"You snatch up the iron key and thrust it into the lock. It turns with a satisfying click, and you heave the heavy door open. But as you step forward, a ghostly figure materializes in the doorway - a guard in translucent armor, hollow eyes fixed upon you. Though stern, it doesn't seem hostile... yet."

---

### Example 4: Disambiguation Required

**Player input:** "open the door"

**Claude sends query:**
```json
{
  "type": "query",
  "query_type": "entities",
  "entity_type": "door",
  "location_id": "loc_hallway"
}
```

**Engine responds (multiple doors):**
```json
{
  "type": "query_response",
  "query_type": "entities",
  "data": {
    "entities": [
      {
        "id": "door_wooden",
        "direction": "south",
        "open": true,
        "llm_context": {"traits": ["rough-hewn planks"]}
      },
      {
        "id": "door_treasure",
        "direction": "east",
        "open": false,
        "locked": true,
        "llm_context": {"traits": ["thick iron plates"]}
      }
    ]
  }
}
```

**Claude asks player (natural language):**
```
Which door do you want to open?
  1. wooden door (south) - already open
  2. iron door (east) - locked
```

**Player responds:** "the iron one" or "east" or "2"

**Claude interprets response and forms command with adjective:**

**Claude sends command:**
```json
{
  "type": "command",
  "action": {"verb": "open", "object": "door", "adjective": "iron"}
}
```

---

## Vocabulary Reference

Commands must use words from the game's vocabulary. The vocabulary is available via query:

```json
{
  "type": "query",
  "query_type": "vocabulary"
}
```

Response includes all verbs, nouns, adjectives, directions, and their synonyms/values.

---

## Error Handling

### Invalid Command Structure

```json
{
  "type": "error",
  "message": "Missing required field: action"
}
```

### Unknown Vocabulary

```json
{
  "type": "result",
  "success": false,
  "action": "teleport",
  "error": {
    "message": "I don't understand 'teleport'. Try actions like go, take, open, or examine."
  }
}
```

Claude responds to the player: "I don't understand what you mean by 'teleport'. You can try actions like go, take, open, or examine."

---

## State Tracking

The engine maintains a visit history that affects state_variants:

```json
{
  "visit_state": {
    "loc_hallway": {
      "visit_count": 3,
      "first_visit": "2024-01-15T10:00:00Z",
      "last_visit": "2024-01-15T10:15:00Z"
    }
  }
}
```

State variant selection priority:
1. Specific triggered state (e.g., "after_event")
2. Visit-based state ("first_visit" vs "revisit")
3. Object state ("open", "locked", "in_inventory")
4. Default

---

## Implementation Notes

### For Claude (Intent Parser)

1. Query state before sending commands to resolve ambiguity
2. Use adjectives to disambiguate when multiple objects match
3. Ask clarifying questions for genuinely ambiguous input
4. Send sequential commands for multi-action player input
5. Check vocabulary before assuming a word is valid

### For Claude (Narrator)

1. Use at least 2-3 traits from llm_context in each description
2. Reference state_variants for context-appropriate phrasing
3. Narrate failures as in-world events using entity traits
4. Match atmosphere to location mood

### For Game Engine

1. Preserve unknown fields for forward compatibility
2. Include full llm_context in all entity responses
3. Return clear, descriptive error messages that Claude can elaborate
4. Support both string and JSON command input
5. Detect JSON input by checking if the input starts with `{` after stripping whitespace

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-15 | Initial specification |
