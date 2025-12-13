# LLM Integration

> **Part of the [Authoring Manual](00_start_here.md)**
>
> Previous: [Parser & Commands](08_parser.md) | Next: [Testing & Debugging](10_testing.md)

---


## 9.1 How the LLM Works

**Key principle:** The LLM is a narrator, not a game master.

**What the LLM does:**
- Translates complex player input to game commands
- Creates vivid prose descriptions of game events
- Uses llm_context to add flavor and variety

**What the LLM does NOT do:**
- Change game state
- Make up items or locations
- Override game rules
- Remember previous conversations (state is in game engine)

### The Separation

```
┌─────────────────────────────────┐
│  LLM (Narrator)                 │
│  - Interprets input             │
│  - Generates prose              │
│  - No state management          │
└────────┬───────────────▲────────┘
         │ JSON          │ JSON
         │ Commands      │ Results
         ▼               │
┌─────────────────────────────────┐
│  Game Engine                    │
│  - ALL state management         │
│  - Command execution            │
│  - Rules enforcement            │
└─────────────────────────────────┘
```

## 9.2 Customizing Narration

### narrator_style.txt

This file defines the narrative style for your game:

```
You are narrating a dark fantasy adventure game set in a cursed tower.

Tone and Style:
- Gothic and atmospheric
- Emphasis on mood and dread
- Use sensory details: cold, damp, echoing
- Short, punchy sentences for action
- Longer, flowing sentences for description

Voice:
- Second person ("You...")
- Present tense
- Active voice preferred

Mood Keywords:
- Ominous, foreboding, ancient
- Mysterious, eldritch, otherworldly
- Decay, corruption, shadow

Example Narration:
- "You lift the ancient key. Its weight surprises you, and a chill runs through
   your fingers where metal touches skin."
- "The door groans open, revealing darkness beyond. The air that escapes is
   cold and stale, untouched for decades."
- "Darkness presses against you from all sides. Your lantern feels inadequate
   against the weight of so much shadow."

Avoid:
- Modern references or anachronisms
- Humor or levity (unless explicitly part of a puzzle)
- Breaking the fourth wall
- Excessive verbosity
```

### Using llm_context Effectively

**Traits should:**
- Be specific and sensory
- Match your game's tone
- Provide variety (5-8 per entity)
- Avoid generic descriptions

**Example - Generic (bad):**
```json
{
  "llm_context": {
    "traits": ["old", "big", "heavy", "nice"]
  }
}
```

**Example - Specific (good):**
```json
{
  "llm_context": {
    "traits": [
      "weathered oak planks",
      "iron-reinforced corners",
      "tarnished brass hinges",
      "musty interior smell",
      "carved runes along edges"
    ]
  }
}
```

### Perspective Variants

Use `perspective_variants` to provide position-specific descriptions for spatial games. The narrator selects the best match based on the player's current posture and focus.

```json
{
  "llm_context": {
    "traits": ["worn stone steps", "spiral design"],
    "perspective_variants": {
      "default": "A spiral staircase rises through the tower",
      "climbing": "The worn steps continue above and below you",
      "on_surface:item_table": "The staircase is visible across the room"
    }
  }
}
```

**Key naming:**
- `"default"` - Used when no specific match
- `"<posture>"` - Matches posture regardless of focus (e.g., `"climbing"`)
- `"<posture>:<entity_id>"` - Exact match for posture + focus

The engine passes the selected variant to the LLM as `perspective_note`. See [Spatial Rooms - Perspective-Aware Narration](07_spatial.md#perspective-aware-narration) for details.

### Verbosity Modes

The narrator automatically adjusts verbosity:

**Full narration:**
- First visit to a location
- First examination of an entity
- Important events
- Uses most llm_context traits

**Brief narration:**
- Subsequent visits/examinations
- Routine actions
- Uses fewer traits, focuses on action

**Control per verb:**
```python
VOCABULARY = {
    "verbs": [
        {
            "word": "inventory",
            "narration_mode": "brief"     # Always brief
        },
        {
            "word": "examine",
            "narration_mode": "tracking"  # Full first time
        }
    ]
}
```

## 9.3 Debugging Narration

### Show Traits Flag

Run with `--show-traits` to see what the LLM sees:

```bash
python -m src.llm_game my_game --show-traits
```

Output:
```
[location traits: ancient stone, echoing halls, cold draft]
[item_key traits: brass, intricate engravings, cold metal]

You enter the ancient hall. Cold air swirls around you...
```

This helps you:
- Verify traits are appropriate
- See which traits were selected (randomized)
- Debug poor narration

### Debug Flag

Run with `--debug` for detailed logging:

```bash
python -m src.llm_game my_game --debug
```

Shows:
- Parser decisions (local vs LLM)
- Behavior module loading
- Handler invocations
- API cache statistics
- Token usage

### Troubleshooting Poor Narration

**Problem:** Narration is too generic

**Solutions:**
- Add more specific traits to llm_context
- Improve narrator_style.txt with better examples
- Check that traits match your tone

**Problem:** Narration contradicts game state

**Solution:**
- The LLM should never contradict state
- Check that your result messages are clear
- Verify llm_context reflects current state (use state_variants)

**Problem:** Narration is too verbose

**Solutions:**
- Set verbs to `"narration_mode": "brief"`
- Reduce number of traits
- Adjust narrator_style.txt to request brevity

---


---

> **Next:** [Testing & Debugging](10_testing.md) - Learn how to validate, test, and debug your game
