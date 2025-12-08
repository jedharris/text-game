# The Parser and Commands

> **Part of the [Authoring Manual](00_start_here.md)**
>
> Previous: [Spatial Rooms](07_spatial.md) | Next: [LLM Integration](09_llm.md)

---


## 8.1 How Commands Work

When a player types a command, here's what happens:

```
Player: "take the red key from the wooden chest"
    ↓
1. Fast Local Parser (attempts instant parse)
   ├─ Success: Converts to JSON command
   └─ Failure: Falls back to LLM
    ↓
2. LLM Fallback (for complex input)
   ├─ LLM interprets intent
   └─ Generates JSON command
    ↓
3. Game Engine (processes command)
   ├─ Finds handler for verb
   ├─ Resolves entities (red key, wooden chest)
   ├─ Validates action (key in chest? chest open?)
   ├─ Updates state (move key to inventory)
   └─ Returns result JSON
    ↓
4. LLM Narrator (creates prose)
   ├─ Receives result + llm_context
   ├─ Determines verbosity (full/brief)
   └─ Generates narrative
    ↓
Player sees: "You reach into the weathered chest and carefully
             lift out the ornate red key..."
```

**Fast parser handles:** ~70% of commands (directions, common verbs, simple structure)
**LLM fallback handles:** ~30% (complex phrasing, ambiguity, conversational input)

## 8.2 Command Structure

Commands follow this pattern:

**Basic:** `[verb] [object]`
- `take key`
- `examine chest`
- `go north`

**With adjective:** `[verb] [adjective] [object]`
- `take red key`
- `examine wooden chest`

**With preposition:** `[verb] [object] [preposition] [indirect-object]`
- `put key in chest`
- `take gem from box`
- `unlock door with key`

**With both adjectives:** `[verb] [adj] [object] [prep] [adj] [indirect-object]`
- `take red key from wooden chest`
- `put iron sword on stone table`

**Bare directions:** Just the direction
- `north`
- `up`
- `down`

## 8.3 Vocabulary Management

The game uses a merged vocabulary from multiple sources:

1. **Base vocabulary** (`src/vocabulary.json`) - Common words
2. **Core behaviors** - Standard adventure game verbs
3. **Library behaviors** - Additional verbs from libraries
4. **Your behaviors** - Custom verbs you add

### Vocabulary Structure

```python
VOCABULARY = {
    "verbs": [
        {
            "word": "cast",                    # Primary word
            "synonyms": ["invoke", "recite"],  # Alternative words
            "object_required": True,           # Needs an object?
            "narration_mode": "tracking"       # "tracking" or "brief"
        }
    ],
    "nouns": [
        {
            "word": "key",
            "synonyms": ["passkey"]
            # word_type is inferred from section ("nouns" -> noun)
        }
    ],
    "directions": [
        {
            "word": "north",
            "synonyms": ["n"]
            # Directions automatically become multi-type (noun + adjective)
        }
    ]
}
```

**Multi-Type Words**: The engine automatically detects when the same word appears with different grammatical types across multiple vocabulary sources. For example:
- If "stand" appears as a **noun** in your game state (item name) and as a **verb** in a behavior module, it becomes a multi-type word
- **Directions** ("north", "south", etc.) are automatically multi-type because they function as both nouns (for the `go` command) and adjectives (for modifying exits)
- The parser uses grammar rules to disambiguate which type to use in context

You never need to manually specify `word_type: ["type1", "type2"]` - the merging system handles this automatically.

### Adding Custom Vocabulary

**In your behavior module:**
```python
# behaviors/magic_spells.py

VOCABULARY = {
    "verbs": [
        {
            "word": "cast",
            "synonyms": ["invoke", "recite", "chant"],
            "object_required": True,
            "narration_mode": "brief"  # Always brief narration
        },
        {
            "word": "enchant",
            "synonyms": ["bewitch", "charm"],
            "object_required": True,
            "narration_mode": "tracking"  # Full first time, brief after
        }
    ],
    "nouns": [
        {
            "word": "spell",
            "synonyms": ["incantation", "magic"]
            # word_type inferred from "nouns" section
        }
    ]
}
```

Now players can use:
- `cast spell`
- `invoke incantation`
- `enchant sword`
- `charm key`

### Synonyms Best Practices

**Good synonyms:**
- Natural alternatives: "take" / "get" / "grab"
- Common abbreviations: "examine" / "x"
- Thematic variations: "unlock" / "open" (for locks)

**Avoid:**
- Too many synonyms (confusing for players)
- Ambiguous synonyms (words that mean different things)
- Cross-verb synonyms (same word for different verbs)

---


---

> **Next:** [LLM Integration](09_llm.md) - Learn how to customize narration and work with the LLM
