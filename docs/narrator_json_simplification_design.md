# Narrator JSON Simplification Design

**Status:** Proposed
**Extends:** unified_narration_design.md (fragment architecture, hints, core principles)
**Supersedes:** narration_recipe_design.md (problem statement adopted; structure revised)

## Problem Statement

Small language models (3B-8B parameters) struggle with the current narrator JSON because:

1. **Deep nesting** — Door state appears at depth 5 (`entity_refs.[id].state.open`), which models often miss
2. **Duplicate data** — Same entity appears in `narration.entity_refs` AND `data`, causing confusion
3. **Dangerous leakage** — `data.exits[].to` reveals destinations even when doors are closed, enabling hallucination
4. **Information overload** — Location scenes include full entity arrays with traits, descriptions, nested state

The result: narrators describe walking through closed doors, reveal information the player cannot perceive, and ignore action verbs in favor of inventing their own actions.

## Design Principles

This design follows the principles established in unified_narration_design.md:

### Mechanical Engine, Intelligent Model

The engine performs only **mechanical operations**:
- State lookup and filtering
- Random selection from fragment pools
- Visibility determination
- Structure flattening

All **intelligence** resides in the model:
- Prose synthesis
- Fragment weaving
- Tone and pacing
- Contextual emphasis

### Exclude the Imperceptible

If the player cannot perceive something, it does not exist for narration. The engine enforces this by:
- Excluding hidden entities from `entity_refs`
- Excluding destinations beyond closed doors from exit data
- Not including any information the narrator might accidentally reveal

This is a **hard filter at plan-building time**, not an instruction to the narrator.

### Flat Fragment Delivery

Fragments are delivered in a flat structure that small models can reliably parse:
- Critical action data at depth 1
- Entity data at depth 2 maximum
- No nested state objects within entity references

## Design Goals

1. **Flat structure** — Critical data at depth 1-2, never deeper
2. **Exclude the imperceptible** — Narrator cannot hallucinate what it doesn't receive
3. **Preserve fragment architecture** — Engine selects, model weaves
4. **Minimal tokens** — Reduce JSON size to improve comprehension
5. **No duplication** — Each fact appears exactly once

## Non-Goals

- Changing the fragment/trait system (retained from unified_narration_design.md)
- Pre-writing prose sentences (model does synthesis)
- Changing handler architecture (HandlerResult structure remains)
- Adding narrator-side inference rules

---

## Current vs. Proposed Structure

### Current JSON (Problematic)

```json
{
  "type": "result",
  "success": true,
  "action": "unlock",
  "verbosity": "full",
  "narration": {
    "action_verb": "unlock",
    "primary_text": "You unlock the door.",
    "secondary_beats": [],
    "viewpoint": {"mode": "ground", "posture": null, "focus_name": "door"},
    "scope": {"scene_kind": "action_result", "outcome": "success", "familiarity": "familiar"},
    "entity_refs": {
      "door_sanctum": {
        "name": "door",
        "type": "door",
        "traits": ["glowing runes", "heavy iron"],
        "state": {"open": false, "locked": false},
        "salience": "medium"
      }
    },
    "target_state": {"open": false, "locked": false}
  },
  "data": {
    "id": "door_sanctum",
    "name": "door",
    "description": "An ornate door covered in glowing runes.",
    "type": "door",
    "open": false,
    "locked": false,
    "llm_context": {"traits": ["glowing runes", "heavy iron handle"]}
  }
}
```

**Problems:**
- `data` duplicates `entity_refs` content (same door, same state, same traits)
- Door state appears 3 times: `target_state`, `entity_refs.*.state`, `data`
- Nested `entity_refs.[id].state.open` at depth 5 — small models miss this
- `data` could contain exit destinations the narrator shouldn't reveal

### Proposed JSON (Simplified)

```json
{
  "action": "unlock",
  "success": true,
  "verbosity": "full",
  "primary": "You unlock the door.",
  "door_now_open": false,
  "fragments": {
    "action_core": "the lock clicks open",
    "action_color": ["runes flicker as the mechanism releases"],
    "traits": ["glowing runes", "heavy iron handle"]
  },
  "hints": []
}
```

**Improvements:**
- Flat structure (max depth 2)
- No duplication — `data` block removed entirely
- Door state as top-level boolean `door_now_open: false` — impossible to miss
- Fragments delivered ready for weaving
- No exit destinations (door is closed, so player can't perceive beyond)

---

## Structural Changes

### Change 1: Remove the `data` Block

The `data` block was intended for "debugging/UI" but causes two problems:
1. **Duplication** — Same entities appear in both `narration.entity_refs` and `data`
2. **Leakage** — Contains information the narrator shouldn't reveal (exit destinations, hidden entity properties)

**Solution:** Remove `data` entirely from narrator input. UI/debugging can use a separate channel.

### Change 2: Flatten Entity State

Current structure nests state deeply:
```json
"entity_refs": {
  "door_sanctum": {
    "state": {
      "open": false,    // Depth 5!
      "locked": false
    }
  }
}
```

**Solution:** For actions affecting an entity's state, promote critical state to top level:
```json
"door_now_open": false,
"door_now_locked": false
```

The narrator prompt can then reference these directly without navigating nested structures.

### Change 3: Pre-resolve Fragments

Current structure sends trait pools; narrator must select and weave:
```json
"entity_refs": {
  "door_sanctum": {
    "traits": ["glowing runes", "heavy iron handle", "ancient oak", "brass fittings"]
  }
}
```

**Solution:** Engine pre-selects fragments per unified_narration_design.md rules:
```json
"fragments": {
  "action_core": "the lock clicks open",
  "action_color": ["runes flicker momentarily"],
  "traits": ["glowing runes", "heavy iron handle"]
}
```

Fragment counts follow verbosity rules from unified_narration_design:
| Verbosity | Core | Color | Traits |
|-----------|------|-------|--------|
| brief     | 1    | 0     | 0      |
| full      | 1    | 1-2   | 2-3    |

### Change 4: Exclude Imperceptible Information

Current structure includes exit destinations even when doors are closed:
```json
"exits": {
  "up": {
    "type": "door",
    "to": "loc_sanctum",      // Leaks destination!
    "door_id": "door_sanctum"
  }
}
```

**Solution:** If a door is closed, exclude the destination entirely:
```json
"exits": {
  "up": {
    "type": "door",
    "blocked": true,
    "door_name": "ornate door"
  }
}
```

The narrator cannot hallucinate about the sanctum if it doesn't know the sanctum exists.

### Change 5: Simplify Scope to Hints

Current structure has mechanical classification:
```json
"scope": {
  "scene_kind": "action_result",
  "outcome": "success",
  "familiarity": "familiar"
}
```

**Solution:** Replace with flat fields and pass-through hints:
```json
"success": true,
"verbosity": "full",
"hints": ["tension"]
```

The `scene_kind` and `familiarity` are derivable from context (verb type, verbosity). Hints provide the only additional guidance needed.

---

## Proposed Field Structure

### Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `action` | string | Canonical verb executed |
| `success` | boolean | Whether action succeeded |
| `verbosity` | string | "brief" or "full" |
| `primary` | string | Core action statement from handler |
| `must_include` | string | Text that MUST appear verbatim in output (dialog topics, etc.) |
| `hints` | list | Pass-through narration hints |

### Entity State Fields (when applicable)

For door/container actions, state promoted to top level:

| Field | Type | Description |
|-------|------|-------------|
| `door_now_open` | boolean | Current door state after action |
| `door_now_locked` | boolean | Current lock state after action |
| `container_now_open` | boolean | Current container state |

### Fragment Fields

Pre-selected fragments ready for weaving:

```json
"fragments": {
  "action_core": "you unlock the door",
  "action_color": ["the mechanism clicks"],
  "traits": ["glowing runes", "heavy iron"],
  "state_variant": "the door remains firmly closed"
}
```

### Entity List (for location/look scenes)

Flat list of visible entities with pre-selected traits:

```json
"visible": [
  {
    "name": "ornate door",
    "traits": ["glowing runes"],
    "note": "closed"
  },
  {
    "name": "stone altar",
    "traits": ["ancient carvings"]
  }
]
```

No entity IDs, no type classifications, no nested state objects.

### Exit List (for location scenes)

Simplified exit structure:

```json
"exits": [
  {"direction": "down", "destination": "Tower Entrance"},
  {"direction": "up", "blocked": true, "door_name": "ornate door"}
]
```

Blocked exits show door name but NOT destination.

---

## Scene Type Examples

### Action Result: Unlock Door

```json
{
  "action": "unlock",
  "success": true,
  "verbosity": "full",
  "primary": "You unlock the door.",
  "door_now_open": false,
  "door_now_locked": false,
  "fragments": {
    "action_core": "the lock clicks open",
    "action_color": ["runes flicker as the mechanism releases"],
    "traits": ["glowing runes", "heavy iron handle"]
  },
  "hints": []
}
```

Note: `door_now_open: false` — narrator sees immediately that door is still closed.

### Action Result: Open Door

```json
{
  "action": "open",
  "success": true,
  "verbosity": "full",
  "primary": "You open the door.",
  "door_now_open": true,
  "fragments": {
    "action_core": "the door swings open",
    "action_color": ["hinges creak softly"],
    "traits": ["glowing runes", "heavy iron handle"],
    "revealed": "stone stairs spiral upward into shadow"
  },
  "hints": []
}
```

Note: `door_now_open: true` and `fragments.revealed` — narrator can now describe what's beyond.

### Location Entry

```json
{
  "action": "go",
  "success": true,
  "verbosity": "full",
  "primary": "You climb the spiral stairs to the Wizard's Sanctum.",
  "transition": {
    "from_location": "Wizard's Library",
    "via": "spiral staircase",
    "direction": "up"
  },
  "location": {
    "name": "Wizard's Sanctum",
    "description": "Arcane symbols cover the circular floor. A large window overlooks the land below.",
    "traits": ["dust motes in pale light", "smell of old parchment"]
  },
  "visible": [
    {"name": "stone altar", "traits": ["ancient carvings"], "note": "at the room's center"},
    {"name": "pale wand", "traits": ["faint glow"], "note": "resting on the altar"},
    {"name": "ornate door", "traits": ["glowing runes"], "note": "leading down"}
  ],
  "exits": [
    {"direction": "down", "destination": "Wizard's Library", "via": "ornate door"}
  ],
  "hints": []
}
```

The `transition` block tells the narrator exactly how the player arrived — climbing stairs, not walking through a door or appearing magically.

### Examine Entity

```json
{
  "action": "examine",
  "success": true,
  "verbosity": "full",
  "primary": "You examine the crystal ball.",
  "fragments": {
    "description": "Mist swirls within its depths, occasionally forming shapes.",
    "traits": ["cool to the touch", "faint inner glow", "silver stand"]
  },
  "hints": []
}
```

### NPC Interaction with Hints

```json
{
  "action": "give",
  "success": true,
  "verbosity": "full",
  "primary": "You offer the silvermoss to Aldric.",
  "fragments": {
    "action_core": "he accepts it with trembling hands",
    "action_color": ["relief floods his pale features"],
    "dialogue": "'Thank you... I thought I was done for.'"
  },
  "hints": ["rescue", "trust-building", "urgent"]
}
```

### Dialog Initiation

When the player initiates dialog with an NPC, provide context for coherent narration:

```json
{
  "action": "talk",
  "success": true,
  "verbosity": "full",
  "primary": "Scholar Aldric looks up with weary eyes.",
  "must_include": "You can ask about: infection, research",
  "context": {
    "actor": {
      "name": "Scholar Aldric",
      "traits": ["frail", "pale skin", "fungal patches on neck"],
      "current_state": "critical",
      "note": "sits weakly by a small campfire"
    },
    "relationship": {
      "trust_level": "neutral",
      "prior_interactions": 0
    }
  },
  "fragments": {
    "action_core": "you address the scholar"
  },
  "hints": []
}
```

**Critical requirements:**

1. **Dialog topics must appear verbatim**: The `must_include` field contains text that the narrator MUST output exactly as written, typically at the end of the narration. This is not a fragment to weave - it's a literal string. Without this, topic keywords get embedded in prose and become unusable for the player.

2. **Entity context prevents hallucination**: Dialog actions must include entity context. Without it, the narrator hallucinates entirely fictional conversations.

3. **Implicit NPC targeting**: When only one NPC with dialog_topics is in the player's location, `talk` (without naming anyone) and `ask about X` (without naming who) default to that NPC. The game engine handles this resolution before generating the narration plan.

### Failure

```json
{
  "action": "open",
  "success": false,
  "verbosity": "brief",
  "primary": "The door is locked.",
  "fragments": {
    "failure_core": "it won't budge",
    "failure_color": ["the lock holds firm"]
  },
  "hints": []
}
```

---

## Narrator Context

The narrator needs context beyond the immediate action to generate coherent, grounded narration. Without context, small models hallucinate freely.

### Context Categories

#### 1. Transition Context (How Did We Get Here?)

For movement actions, the narrator needs to know the path taken:

```json
{
  "action": "go",
  "success": true,
  "primary": "You climb the spiral stairs to the Wizard's Sanctum.",
  "transition": {
    "from_location": "Wizard's Library",
    "via": "spiral staircase",
    "direction": "up"
  },
  "location": {
    "name": "Wizard's Sanctum",
    "description": "...",
    "traits": ["dust motes in pale light"]
  }
}
```

Without `transition.via`, the narrator might describe walking through a door, teleporting, or some other invented mechanism.

#### 2. Entity Context (Who/What Are We Interacting With?)

Any action involving an entity needs that entity's current state:

```json
{
  "action": "give",
  "target": {
    "name": "Scholar Aldric",
    "traits": ["frail", "pale", "fungal patches visible"],
    "current_state": "critical",
    "relationship": "neutral"
  }
}
```

For big_game NPCs with complex state:

```json
{
  "action": "talk",
  "target": {
    "name": "Bee Queen",
    "traits": ["golden-furred", "crowned with antennae"],
    "current_state": "trading",
    "relationship": {
      "trust": 2,
      "trades_completed": 1,
      "trades_remaining": 2
    }
  }
}
```

#### 3. Situational Context (What's Happening Around Us?)

For actions in special circumstances:

```json
{
  "action": "use",
  "success": true,
  "primary": "You apply the bandages to Sira's wounds.",
  "situation": {
    "urgency": "critical",
    "time_pressure": true,
    "environmental": ["campfire smoke", "distant predator sounds"]
  },
  "hints": ["urgent", "rescue"]
}
```

#### 4. Relationship Context (How Do They See Us?)

For NPC interactions, include relationship state:

| Field | Description | Example Values |
|-------|-------------|----------------|
| `trust_level` | Qualitative trust | "hostile", "wary", "neutral", "friendly", "allied" |
| `prior_interactions` | Count of previous exchanges | 0, 1, 5 |
| `standing` | Any special status | "benefactor", "thief", "stranger" |
| `debts` | Outstanding obligations | "owes_honey", "promised_help" |

```json
"relationship": {
  "trust_level": "friendly",
  "prior_interactions": 3,
  "standing": "benefactor",
  "debts": ["owes_teaching"]
}
```

### Context Derivation

The engine derives context from game state — this is mechanical, not intelligent:

| Context Field | Derived From |
|---------------|--------------|
| `transition.via` | Exit name used for movement |
| `transition.from_location` | Player's previous location |
| `target.current_state` | Actor's state machine current state |
| `target.relationship.trust` | Actor's `trust_state.current` |
| `situation.urgency` | Active commitments with timers |
| `situation.environmental` | Location properties, active hazards |

### What Context Prevents

| Without Context | Narrator May... |
|-----------------|-----------------|
| `transition.via` | Invent how player traveled (teleport, door, ladder) |
| `target.current_state` | Describe NPC in wrong state (healthy when dying) |
| `relationship.trust` | Use wrong tone (friendly when hostile) |
| `situation.urgency` | Miss time pressure, narrate casually |
| `target.traits` | Invent appearance, personality |

### Minimal Context for Action Types

| Action Type | Required Context |
|-------------|------------------|
| `go` | `transition` (via, from_location, direction) |
| `talk` | `target` (name, traits, state, relationship) |
| `give`/`use on` | `target` (name, traits, state), `item` context |
| `examine` | Entity traits, current state |
| `take`/`drop` | Item context, location context |
| Combat | Target state, threat level, prior combat |

---

## Visibility Filtering Rules

The engine excludes imperceptible information at plan-building time:

### Doors and Containers

| State | What's Included | What's Excluded |
|-------|-----------------|-----------------|
| Door closed | Door name, traits, "blocked: true" | Destination location, anything beyond |
| Door open | Door name, traits, destination | Nothing |
| Container closed | Container name, traits | Contents |
| Container open | Container name, traits, contents | Nothing |

### Hidden Entities

Entities with `hidden: true` are excluded entirely. They don't appear in `visible` lists or fragment selection.

### Darkness

If location is dark and player has no light source:
- `visible` list is empty or contains only "darkness"
- No entity traits included
- Exits may be listed as directions only, no destinations

---

## Fragment Resolution

The engine performs fragment selection per unified_narration_design.md:

### Selection Process

1. **Identify pools** — Find relevant fragment pools in entity's `llm_context`
2. **Check repetition buffer** — Exclude recently-used fragments
3. **Random selection** — Choose from available fragments
4. **Apply counts** — Limit by verbosity (brief=1 core only, full=1 core + 1-2 color + 2-3 traits)

### Fragment Sources

| Fragment Type | Source |
|---------------|--------|
| `action_core` | `entity.llm_context.action_fragments[verb].core` |
| `action_color` | `entity.llm_context.action_fragments[verb].color` |
| `traits` | `entity.llm_context.traits` |
| `state_variant` | `entity.llm_context.state_variants[current_state]` |
| `failure_core` | `entity.llm_context.failure_fragments[reason].core` |
| `dialogue` | `actor.llm_context.dialogue_fragments[situation]` |

### Fallback Behavior

If an entity lacks specific fragments:
- **Missing action_fragments**: Use `primary` text only, no elaboration
- **Missing traits**: Omit `traits` from fragment object
- **Missing failure_fragments**: Use generic failure from handler

Per unified_narration_design.md, missing required fragments should fail loudly at load time, not at runtime.

---

## Hints System

Hints pass through from handlers unchanged, per unified_narration_design.md:

```python
return HandlerResult(
    success=True,
    primary="You apply the silvermoss to Aldric's wounds.",
    hints=["urgent", "rescue", "trust-building"]
)
```

The narrator prompt defines how to interpret hints:

```
NARRATION HINTS

The input may include hints like ["urgent", "rescue"].
Use these to adjust your narration style:
- "urgent": Short sentences. Active verbs. No dwelling.
- "rescue": Emphasize relief, hope, connection.
- "tense": Heighten sensory details. Slow moments down.

Hints guide HOW you tell the story. Never mention hints in output.
```

---

## Migration Strategy

### Phase 1: Implement Flattened Structure

1. Create `flatten_narration_plan()` function that transforms current `NarrationPlan` to new flat structure
2. Remove `data` block from output
3. Promote entity state to top level (`door_now_open`, etc.)
4. Pre-resolve fragments in engine
5. Implement visibility filtering (exclude destinations behind closed doors)

### Phase 2: Update Narrator Prompt

Rewrite `narrator_protocol.txt` to match the new structure. See "Revised Narrator Protocol" section below.

### Phase 3: Evaluate

Use `narrator_eval_harness.py` to compare:
- Hallucination rate (especially door/container scenarios)
- Action verb compliance
- Fragment weaving quality

### Phase 4: Clean Up

1. Remove `NarrationAssembler` nesting logic
2. Remove `entity_refs` nested state
3. Update any code depending on old structure

---

## Revised Narrator Protocol

The current `narrator_protocol.txt` (215 lines) contains extensive instructions trying to prevent hallucination through closed doors. With the new structure, the prompt becomes simpler because **the narrator cannot hallucinate what it doesn't receive**.

### Current Prompt Problems

The current prompt includes:
- 20+ lines explaining `target_state` and how to interpret nested state
- 10+ lines of "STRICT PROHIBITIONS" about closed doors
- Complex `entity_refs` navigation instructions
- Repeated warnings about unlock ≠ open

These are symptoms of fighting the JSON structure rather than fixing it.

### New Prompt Structure

With flattened JSON, the prompt can focus on **what to do** rather than **what not to do**:

```
You are the narrator for an interactive text adventure game.

## INPUT FORMAT

Each input contains:
- `action` — the verb that was executed
- `success` — whether it succeeded
- `verbosity` — "brief" or "full"
- `primary` — core action statement
- `must_include` — text that MUST appear verbatim in output (optional)
- `fragments` — pre-selected phrases to weave into prose
- `hints` — style guidance (optional)

For location scenes:
- `location` — name, description, traits
- `visible` — list of entities with names, traits, and notes
- `exits` — directions and destinations

## OUTPUT RULES

Output ONLY plain prose text. No JSON, no formatting.

## MUST_INCLUDE (CRITICAL)

If `must_include` is present, you MUST include this text VERBATIM at the end of your narration.
- Do NOT paraphrase, rephrase, or embed the text in prose
- Do NOT add surrounding flourishes that obscure it
- Output it exactly as provided, typically as the final sentence

Example: If `must_include` is "You can ask about: infection, research"
Your narration MUST end with exactly: "You can ask about: infection, research"

## FRAGMENT WEAVING

The `fragments` object contains pre-selected phrases:

- `action_core` — essential action phrase (always include)
- `action_color` — embellishment phrases (weave naturally)
- `traits` — sensory details (incorporate for atmosphere)
- `state_variant` — current state description
- `dialogue` — NPC speech (include as quoted speech)
- `revealed` — what becomes visible (only present when something is newly visible)

Weave fragments into natural prose. Do not list them mechanically.

## VERBOSITY

**"full"** — Detailed narration
- Use all fragment types
- Incorporate traits for atmosphere
- Include sensory details

**"brief"** — Concise narration
- Use `primary` and `action_core` only
- Minimal embellishment

## HINTS

The `hints` list guides your style:
- "urgent" — Short sentences. Active verbs.
- "rescue" — Emphasize relief, hope.
- "tense" — Heighten sensory details.
- "intimate" — Focus on close details.

Hints guide HOW you tell the story. Never mention hints in output.

## EXITS

For location scenes, describe exits naturally. The `exits` list shows:
- Open paths with destinations
- Blocked exits (doors) with door names only

If an exit shows `blocked: true`, there is a door. You know the door exists but NOT what's beyond it.

## STYLE

{{STYLE_PROMPT}}
```

### What's Removed

The new prompt eliminates:
- All `target_state` explanation (state is now top-level or excluded)
- All `entity_refs` navigation instructions (replaced with flat `visible` list)
- All "STRICT PROHIBITIONS" (impossible to violate when data is excluded)
- Repeated unlock ≠ open warnings (narrator only sees `door_now_open: false`)
- `scope`, `viewpoint`, `must_mention` complexity

### Why This Works

With the old structure:
```
Prompt: "if target_state.open is false, don't describe what's beyond"
JSON contains: exits.up.to = "loc_sanctum"  ← model sees this and hallucinates
```

With the new structure:
```
Prompt: (no prohibition needed)
JSON contains: exits: [{direction: "up", blocked: true, door_name: "ornate door"}]
← no destination, can't hallucinate
```

The prompt becomes shorter because the structure makes errors impossible, not because we're trusting the model more.

---

## Test Plan

### Testing Philosophy

Traditional unit and integration tests verify that the engine produces correct JSON structures. But they cannot verify that a language model will **interpret** that JSON correctly and produce appropriate narration.

We need a new level of testing:
1. **Walkthrough tests** — Execute multi-command scenarios and capture narrator output
2. **Narration analysis** — Check output for hallucination, compliance, and quality
3. **Comparative evaluation** — Run same scenarios with old vs. new JSON structure

### Test Tools

#### `tools/eval_json_structure.py`

Inspects the JSON sent to the narrator without calling the LLM.

**Use for:**
- Verifying structural changes (depth, field presence)
- Confirming visibility filtering works (no destinations behind closed doors)
- Checking fragment pre-selection

**Key commands:**
```bash
# Interactive mode - explore JSON for any command
python tools/eval_json_structure.py examples/extended_game

# Door scenario - full unlock/open sequence
python tools/eval_json_structure.py examples/extended_game --door-scenario

# Specific commands with full JSON output
python tools/eval_json_structure.py examples/extended_game -c "unlock door" --json
```

#### `tools/narrator_eval_harness.py`

Runs scenarios through the actual LLM narrator and evaluates output.

**Use for:**
- Hallucination detection (must_not_contain phrases)
- Compliance verification (must_contain phrases)
- Comparative A/B testing between structures

**Key commands:**
```bash
# Run all scenarios for a game
python tools/narrator_eval_harness.py examples/extended_game

# Output to specific file
python tools/narrator_eval_harness.py examples/extended_game -o door_eval.json
```

### Walkthrough Scenarios

Each scenario tests a specific narrator failure mode. Scenarios are defined per-game in the eval harness.

#### Scenario Set 1: Door State (extended_game)

| Scenario | Setup | Test Command | Must Contain | Must NOT Contain |
|----------|-------|--------------|--------------|------------------|
| unlock_closed_door | go north, go up | unlock door | unlock, door | open, beyond, through, see, step, enter |
| open_unlocked_door | go north, go up, unlock door | open door | open, door | unlock, key, lock clicks |
| examine_closed_door | go north, go up | examine door | door | beyond, inside, through, step, enter |

#### Scenario Set 2: Container State (to be added)

| Scenario | Setup | Test Command | Must Contain | Must NOT Contain |
|----------|-------|--------------|--------------|------------------|
| examine_closed_chest | (navigate to chest) | examine chest | chest | contents, inside, contains |
| open_chest | (navigate to chest) | open chest | open, chest | (none) |
| examine_open_chest | (open chest first) | examine chest | chest, contents | (none) |

#### Scenario Set 3: Action Verb Compliance (to be added)

| Scenario | Setup | Test Command | Must Contain | Must NOT Contain |
|----------|-------|--------------|--------------|------------------|
| examine_not_take | (navigate to item) | examine sword | sword, look/see/examine | take, pick up, grab |
| take_item | (navigate to item) | take sword | take/pick up, sword | examine, look at |

#### Scenario Set 4: NPC Interaction (big_game)

| Scenario | Setup | Test Command | Must Contain | Must NOT Contain |
|----------|-------|--------------|--------------|------------------|
| give_healing_item | (navigate to Aldric with silvermoss) | give silvermoss to Aldric | silvermoss, Aldric | (mechanics, turn counts) |
| trade_with_bee_queen | (navigate with flower) | give frost lily to queen | frost lily, queen | (trust values, state machine) |

#### Scenario Set 4a: Dialog Topics (big_game)

| Scenario | Setup | Test Command | Must Contain | Must NOT Contain |
|----------|-------|--------------|--------------|------------------|
| talk_shows_topics | (navigate to Aldric) | talk | "You can ask about:" (verbatim) | (embedded topics in prose) |
| talk_implicit_npc | (navigate to room with single NPC) | talk | NPC name, topics | "whom", "which" |
| ask_about_topic | (navigate to Aldric) | ask about infection | infection, response | (game mechanics) |

**Critical**: The `must_include` text (dialog topics) must appear verbatim, not woven into prose. Test that "You can ask about: infection, research" appears exactly as written.

#### Scenario Set 5: Urgency/Hints (big_game)

| Scenario | Setup | Test Command | Must Contain | Must NOT Contain |
|----------|-------|--------------|--------------|------------------|
| rescue_urgency | (enter flooded room) | look | water, rising | (turn numbers, timer values) |

### Comparative Testing Protocol

To validate the new JSON structure improves narrator behavior:

#### Phase 1: Baseline (Current Structure)

1. Run all scenarios with current `NarrationAssembler` output
2. Record pass/fail rates and specific failures
3. Save full JSON and narration for each test

```bash
python tools/narrator_eval_harness.py examples/extended_game -o baseline_results.json
```

#### Phase 2: New Structure

1. Implement `flatten_narration_plan()`
2. Run identical scenarios with flattened output
3. Record pass/fail rates and specific failures

```bash
python tools/narrator_eval_harness.py examples/extended_game -o flattened_results.json
```

#### Phase 3: Compare

Compare results:
- **Hallucination rate**: Count of must_not_contain violations
- **Compliance rate**: Count of must_contain successes
- **Sentence count**: Are responses appropriately sized?

### Adding New Scenarios

When adding scenarios to `narrator_eval_harness.py`:

1. **Define setup commands** — Commands to reach the test state
2. **Define test command** — The specific action to evaluate
3. **Define must_contain** — Words/phrases that MUST appear
4. **Define must_not_contain** — Words/phrases that must NOT appear (hallucination indicators)
5. **Optionally set sentence limits** — For verbosity compliance

Example:
```python
TestScenario(
    name="unlock_closed_door",
    description="Unlock a locked door - should NOT describe opening or what's beyond",
    setup_commands=["go north", "go up"],
    test_command="unlock door",
    criteria=EvalCriteria(
        must_contain=["unlock", "door"],
        must_not_contain=[
            "open", "opens", "opened", "opening", "swings",
            "step", "enter", "inside", "through",
            "beyond", "reveals", "see"
        ],
        max_sentences=4
    )
)
```

### Regression Testing

After changes to narration code:

1. Run full scenario suite:
   ```bash
   python tools/narrator_eval_harness.py examples/extended_game
   ```

2. Compare to previous results
3. Investigate any new failures
4. Add new scenarios for any bugs discovered in manual testing

### Manual Walkthrough Testing

For issues not captured by automated scenarios:

1. Use `eval_json_structure.py` in interactive mode
2. Execute problem command sequences
3. Inspect JSON structure for leakage or nesting issues
4. If issue found, add automated scenario to prevent regression

### Success Criteria for Migration

The new JSON structure is ready for production when:

1. **All existing scenarios pass** at equal or better rates than baseline
2. **Door scenarios show 0 hallucinations** (currently non-zero with old structure)
3. **No new failure modes** introduced
4. **Prompt size reduced** by at least 50% (215 lines → ~70 lines)

---

## Evaluation Criteria

### Must Pass (Structural Correctness)

1. **Unlock door** — Narrator does NOT describe:
   - Opening the door
   - What's beyond the door
   - Stepping through
   - Sensory details from beyond (air, smells, light)

2. **Closed container** — Narrator does NOT describe:
   - Container contents
   - What might be inside

3. **Action verb compliance** — Narrator describes the action that was performed:
   - `unlock` → unlocking, not opening
   - `examine` → looking, not taking

### Should Pass (Quality)

1. **Fragment weaving** — Fragments woven naturally, not listed mechanically
2. **Trait incorporation** — Sensory details appear organically
3. **Hint response** — Tone/pacing reflects hints without mentioning them
4. **State reflection** — New state clear from narration

---

## Auto-Generation of Test Scenarios

A significant portion of test scenarios can be auto-generated by analyzing game state files. This reduces manual scenario authoring and ensures comprehensive coverage.

### What Can Be Auto-Generated

| Category | Coverage | Method |
|----------|----------|--------|
| Door state scenarios | ~90% | Parse `exits` with `type: "door"`, find path to location, generate unlock/open/examine sequences |
| Container state scenarios | ~90% | Find items with `is_container: true`, generate open/close/examine sequences |
| Navigation paths | ~95% | BFS from start location through open exits, generate "go direction" commands |
| Item examine scenarios | ~95% | List all items in accessible locations, generate examine commands |
| Take/drop scenarios | ~90% | Find portable items, generate take/drop with must_not_contain for wrong verbs |

### Hybrid Authoring for Complex Scenarios

The "manual" cases can actually use **hybrid authoring** where the generator extracts structure from game state and behavior handlers, then asks targeted questions or provides fill-in templates.

#### How Much Logic is in Handlers?

Analyzing big_game handlers reveals a consistent pattern:

1. **Handler functions return `EventResult` with `feedback` strings** — These are the exact narration outcomes
2. **State transitions are explicit** — `transition_state(sm, "stabilized")` tells us what states exist
3. **Conditions are declared** — `conditions: { "bleeding": {...}, "broken_leg": {...} }` tells us what needs healing
4. **Accepted items are listed** — `accepted_items: ["bandages", "silvermoss"]` tells us what can be used
5. **Trust thresholds are explicit** — `if current_trust < 2:` tells us requirements

**Key insight**: The handler code contains precisely the logic needed to generate scenarios — we just need to extract it.

#### Hybrid Authoring Strategy

For each "manual" category, the generator can extract structure and produce a fill-in template:

##### 1. NPC Interactions (from game_state.json + handlers)

**Auto-extracted from Aldric's config:**
```
Actor: npc_aldric
Location: cavern_entrance
State machine: critical → stabilized → recovering → dead
Conditions: fungal_infection (severity: 80)
Item reactions: silvermoss heals
Dialog topics: infection, research, spore_mother, help_commitment, teaching
Trust: starts 0, ceiling 5
```

**Generated template:**
```python
TestScenario(
    name="aldric_give_silvermoss",
    description="Give silvermoss to Aldric — should stabilize, NOT fully cure",
    setup_commands=[
        # AUTO: BFS path from nexus_chamber to cavern_entrance
        "go west", "go north", "go down",
        # FILL IN: How to get silvermoss (requires game knowledge)
        "???",
    ],
    test_command="give silvermoss to aldric",
    criteria=EvalCriteria(
        # AUTO from handler feedback strings:
        must_contain=["silvermoss", "aldric"],
        must_not_contain=[
            # AUTO from handler: first silvermoss doesn't fully cure
            "fully cured", "completely healed",
            # STANDARD: no mechanics
            "severity", "progression", "trust",
        ],
    )
)
```

The author only needs to fill in: *"How does player get silvermoss before reaching Aldric?"*

##### 2. State Machine Transitions (from handlers)

**Auto-extracted from Bee Queen handler:**
```
Actor: bee_queen
Trades for: moonpetal, frost_lily, water_bloom
State transitions: neutral → trading (on first flower), trading → allied (on 3 flowers)
Theft consequence: → hostile (permanent)
```

**Generated scenarios (fully automatic):**
```python
# Positive path
TestScenario(
    name="bee_queen_first_flower",
    description="Give first flower — should transition to trading, mention remaining",
    setup_commands=["???"],  # FILL IN: path + flower acquisition
    test_command="give moonpetal to queen",
    criteria=EvalCriteria(
        must_contain=["accepts", "honey", "exchange"],
        must_not_contain=["allied", "sanctuary", "trust_state"],
    )
)

# Negative path (fully auto from handler)
TestScenario(
    name="bee_queen_honey_theft",
    description="Take honey without alliance — should trigger hostile",
    setup_commands=["???"],  # FILL IN: path to bee clearing
    test_command="take honey",
    criteria=EvalCriteria(
        must_contain=["furious", "hostile", "destroyed"],
        must_not_contain=["allied", "trade", "accepts"],
    )
)
```

##### 3. Timed Rescues (from commitment configs + handlers)

**Auto-extracted from Sira config:**
```
Actor: hunter_sira
Location: hunters_camp
State machine: injured → stabilized → mobile → dead
Timer: 15 turns (starts on encounter)
Conditions: bleeding (severity 60), broken_leg (severity 100)
Accepted items: bandages, healing_herbs
Death reactions: gossip to Elara
```

**Generated template:**
```python
TestScenario(
    name="sira_apply_bandages",
    description="Apply bandages to Sira — should stop bleeding, NOT fully heal",
    setup_commands=[
        # AUTO: path to hunters_camp
        "go south", "go east",
        # FILL IN: How to get bandages
        "???",
    ],
    test_command="use bandages on sira",
    criteria=EvalCriteria(
        must_contain=["bleeding", "stops"],
        must_not_contain=[
            "fully healed", "mobile", "saved",  # From handler: partial healing
            "timer", "turns", "commitment",      # STANDARD: no mechanics
        ],
    )
)
```

##### 4. Hidden Items (from item states)

**Auto-extracted from items with `hidden: true`:**
```
item_sanctum_key: hidden=true, reveal_conditions: {...}
```

The generator can identify hidden items and ask: *"What reveals item_sanctum_key?"*

#### Generator Output Modes

The hybrid generator could operate in three modes:

1. **`--full-auto`**: Generate only scenarios where 100% of setup is determinable
2. **`--template`**: Generate scenarios with `???` placeholders, write to YAML for author review
3. **`--interactive`**: For each scenario, ask specific questions when stuck

#### What Remains Truly Manual

After hybrid authoring, only these require fully manual scenarios:

| Category | Example | Why |
|----------|---------|-----|
| Multi-puzzle sequences | "Solve mushroom puzzle to access deep roots" | Puzzle logic not in state/handlers |
| Narrative timing | "Urgency should feel natural in rescue" | Quality judgment, not correctness |
| Edge case combinations | "What if player has both silvermoss AND breathing mask?" | Emergent interactions |

#### Coverage Estimate with Hybrid Authoring

| Approach | Scenario Coverage |
|----------|-------------------|
| Full auto only | ~60-70% |
| Hybrid (with fill-ins) | ~85-90% |
| Fully manual remainder | ~10-15% |

The hybrid approach dramatically reduces authoring burden because **the structure is extracted automatically** — authors only provide the missing connections (paths to items, puzzle solutions).

### Auto-Generator Design

A tool `tools/generate_narrator_scenarios.py` could:

1. **Parse game_state.json** to extract:
   - All locations and their exits
   - All doors (from `type: "door"` exits)
   - All containers (items with `is_container: true`)
   - All portable items

2. **Generate navigation paths** using BFS:
   - From `start_location` to each door location
   - Skip paths through locked doors (unless key is accessible)

3. **Generate test scenarios** for each entity type:
   ```python
   # For each door
   TestScenario(
       name=f"unlock_{door_id}",
       setup_commands=path_to_door_location,
       test_command="unlock door",
       criteria=DOOR_UNLOCK_CRITERIA  # Standard must_not_contain
   )
   ```

4. **Output** game-specific scenario lists to be imported by `narrator_eval_harness.py`

### Current Game Analysis

| Game | Doors | Containers | Auto-Generatable Scenarios |
|------|-------|------------|---------------------------|
| extended_game | 2 (door_storage, door_sanctum) | 5 | ~15-20 |
| simple_game | 2 (door_wooden, door_treasure) | 2 | ~10-12 |
| spatial_game | 2 (door_storage, door_sanctum) | 6 | ~18-22 |
| big_game | 0 (all open exits) | 2 | ~8-10 (navigation, containers only) |
| fancy_game | 2 (door_wooden, door_treasure) | 2 | ~10-12 |
| layered_game | 1 (door_treasure) | 1 | ~6-8 |

### Estimated Coverage

With auto-generation: **~60-70%** of narrator compliance test scenarios
With manual additions for puzzles/NPCs: **~90%** of meaningful test cases

The remaining ~10% are edge cases that emerge only during playtesting.

---

## Appendix: Structure Comparison

| Current | Proposed | Depth |
|---------|----------|-------|
| `narration.entity_refs.[id].state.open` | `door_now_open` | 5 → 1 |
| `narration.entity_refs.[id].traits` | `fragments.traits` | 4 → 2 |
| `narration.scope.scene_kind` | (removed, derivable) | 3 → N/A |
| `data.exits.[dir].to` | `exits[].destination` (only if visible) | 4 → 2 |
| `data.*` (duplicates) | (removed entirely) | N/A |

Maximum depth reduced from 5 to 2.

---

## Appendix B: Author-Defined Narration Context

The core design above provides the basic narrator JSON structure. This appendix describes how game authors can extend the narrator context with game-specific semantics, following the framework's principle that **the game author controls game semantics, not the framework**.

### B.1 Design Principle: Author-Defined Context

The framework should NOT build in concepts like "trust", "commitment", "spore signals", or "pack dynamics". Instead, it should provide:

1. **A generic `context` object** that handlers populate with author-defined keys and values
2. **Author-defined hints** passed through without framework interpretation
3. **Author-defined fragment types** in entity `llm_context`

The narrator prompt is also author-controlled (per game or per-entity), so authors can explain their custom context fields to the narrator.

### B.2 Generic Context Structure

Instead of framework-defined fields like `commitment`, `relationship`, `environment`, the JSON provides a single extensible `context` object:

```json
{
  "action": "give",
  "success": true,
  "verbosity": "full",
  "primary": "You offer the venison to the wolf.",
  "fragments": {
    "action_core": "the wolf sniffs the meat",
    "action_color": ["its posture relaxes slightly"]
  },
  "context": {
    // Author-defined keys - framework passes through without interpretation
  },
  "hints": ["trust-building"]
}
```

The `context` object is:
- **Populated by handlers** that the game author writes
- **Passed through unchanged** by the framework
- **Interpreted by the narrator prompt** that the game author provides

### B.3 How Authors Populate Context

Game authors populate context in their handlers. The framework provides the hook; the author provides the semantics.

**Example: big_game wolf feeding handler**

```python
def handle_give_food_to_wolf(entity, accessor, context):
    wolf = context["target"]

    # Author's game logic
    old_state = wolf.properties.get("disposition", "hostile")
    new_state = advance_wolf_trust(wolf, accessor)

    # Author populates narrator context with their semantics
    narrator_context = {
        "npc_state": {
            "previous": old_state,
            "current": new_state,
            "changed": old_state != new_state
        },
        "communication": {
            "type": "body_language",
            "signal": get_wolf_signal_for_state(new_state),
            "valence": "positive" if new_state in ["wary", "friendly"] else "negative"
        }
    }

    return HandlerResult(
        success=True,
        primary="You offer the venison to the wolf.",
        context=narrator_context,
        hints=["trust-building"] if old_state != new_state else []
    )
```

**Example: big_game spore communication handler**

```python
def handle_myconid_dialog(entity, accessor, context):
    elder = context["target"]

    # Author's game-specific spore color semantics
    colors = determine_spore_colors(elder, accessor)

    narrator_context = {
        "communication": {
            "type": "spore",
            "colors": colors,
            "pulsing": "slow",
            "meaning": interpret_spore_meaning(colors)
        }
    }

    return HandlerResult(
        success=True,
        primary="The Myconid Elder responds.",
        context=narrator_context,
        hints=["non-verbal"]
    )
```

### B.4 Author-Defined Hints

Hints are already author-defined strings that pass through to the narrator. The framework does not interpret them. Authors define hints in their handlers and explain them in their narrator prompts.

**Example: big_game hints defined in game documentation**

The game author documents their hints in their narrator prompt or game docs:

```
HINTS (defined by this game):

- "urgent": Time-critical situation. Use short sentences, active verbs.
- "rescue": Life-saving action. Emphasize relief, hope.
- "trust-building": Relationship improving. Show behavioral warmth.
- "non-verbal": NPC communicates without speech. Describe body language.
- "pack-reaction": Group responds as unit. Show collective behavior.
- "death": NPC dying. Handle with gravity.
```

The framework passes these through unchanged. Different games can define entirely different hint vocabularies.

### B.5 Author-Defined Fragment Types

Fragment types are already author-defined in entity `llm_context`. Authors can create any fragment types they need:

```json
{
  "id": "npc_alpha_wolf",
  "llm_context": {
    "traits": ["massive", "grey-furred", "amber eyes"],
    "action_fragments": {
      "give": {
        "core": ["the wolf sniffs the offering"],
        "color": ["its ears prick forward", "a low rumble in its throat"]
      }
    },
    "state_fragments": {
      "hostile": ["hackles raised", "teeth bared", "yellow eyes narrowed"],
      "wary": ["watchful", "ears pricked", "sniffing the air"],
      "friendly": ["tail swaying", "ears relaxed", "approaching without threat"]
    },
    "gesture_fragments": {
      "accepting": ["ears flatten back", "tail drops low"],
      "warning": ["stiff posture", "direct stare"]
    }
  }
}
```

The framework's fragment resolution can select from any pool the author defines. Authors document their fragment types in their game's narrator prompt.

### B.6 Author-Controlled Narrator Prompts

The narrator prompt is already per-game. Authors explain their custom context, hints, and fragments:

```
## GAME-SPECIFIC CONTEXT

This game uses the following context fields:

### NPC State
When `context.npc_state` is present:
- `previous` and `current` show state transition
- If `changed` is true, emphasize the behavioral shift
- Use fragments from entity's `state_fragments[current]`

### Non-Verbal Communication
When `context.communication` is present:
- `type` indicates communication method (body_language, spore, gesture, flame)
- `signal` is the specific signal being made
- `valence` is positive/negative/neutral
- Describe the signal; don't explain what it "means"

### Pack Dynamics
When `context.group` is present:
- Describe the group responding as a unit
- The leader's reaction drives follower reactions
```

### B.7 Framework Responsibilities (Minimal)

The framework provides only generic mechanisms:

| Responsibility | Framework Does | Author Does |
|----------------|----------------|-------------|
| Context passing | Pass `context` object unchanged | Define keys, populate values |
| Hints | Pass hints list unchanged | Define hint vocabulary |
| Fragments | Select from pools, avoid repetition | Define pool names and contents |
| Prompt | Load game's narrator prompt | Write prompt explaining their context |

### B.8 What This Simplifies

By keeping game semantics out of the framework:

1. **No framework code for "trust", "commitment", "spores", etc.** - These are just keys in the context object
2. **No framework-defined hint vocabulary** - Authors define their own
3. **No framework-defined fragment types** - Authors define in llm_context
4. **Games can have completely different semantics** - A mystery game's context looks nothing like big_game's

### B.9 Example: Complete Narrator JSON with Author Context

```json
{
  "action": "give",
  "success": true,
  "verbosity": "full",
  "primary": "You offer the silvermoss to Aldric.",
  "fragments": {
    "action_core": "he accepts it with trembling hands",
    "action_color": ["relief floods his pale features"],
    "condition_visible": "the fungal patches seem to recede slightly"
  },
  "context": {
    "npc_state": {
      "previous": "critical",
      "current": "stabilized",
      "changed": true
    },
    "urgency": {
      "level": "critical",
      "visible_signs": ["labored breathing", "pale skin"]
    },
    "relationship": {
      "disposition": "grateful",
      "standing": "benefactor"
    }
  },
  "hints": ["rescue", "urgent", "state-transition"]
}
```

All of `context.npc_state`, `context.urgency`, and `context.relationship` are author-defined. A different game might have `context.mystery_clues` or `context.faction_standing` or anything else.

### B.10 Migration from Current Design

The core design's proposed fields like `door_now_open` remain as framework-provided for common cases. The `context` object extends this for game-specific needs:

| Field | Provider | Notes |
|-------|----------|-------|
| `action`, `success`, `verbosity`, `primary` | Framework | Core fields |
| `door_now_open`, `container_now_open` | Framework | Common state (mechanical) |
| `fragments` | Framework selects from author-defined pools | |
| `context` | Author-populated in handlers | All game semantics |
| `hints` | Author-defined in handlers | Passed through |
| `visible`, `exits`, `location` | Framework | Scene structure |

### B.11 Multiple Entity Reactions

Analysis of big_game reveals two distinct multi-entity patterns:

**Groups with unified state (packs):** Wolf packs, spider swarms, bee colonies, and bear families all follow a leader whose state propagates to followers. The pack shares the leader's state, but the pack's *fragments* are distinct from the leader's - "the pack settles" not "the alpha settles" and not "wolf A relaxes, wolf B relaxes, wolf C relaxes."

The leader entity has individual fragments:
```json
"state_fragments": {
  "friendly": ["ears relax", "tail sways", "amber eyes soften"]
}
```

The pack (or the leader entity) has collective fragments in a separate pool:
```json
"pack_fragments": {
  "friendly": ["the pack settles", "the wolves relax as one", "tension drains from the group"]
}
```

When a pack leader's state changes, the handler selects from both pools - individual fragments for the leader's reaction, pack fragments for the followers' collective reaction. This produces narration like: "The alpha's ears relax, tail swaying. Around her, the pack settles, tension draining from the group."

**Independent individuals reacting to the same event:** When a player enters town with a wolf companion, the guard, the wolf, and nearby merchants each react independently with different states and motivations. These require separate narration.

For independent reactions, the narrator JSON includes a `reactions` array (max 5 entities, typically 2-3):

```json
{
  "action": "enter",
  "success": true,
  "primary": "You enter the market square with your wolf companion.",
  "reactions": [
    {
      "entity": "town_guard",
      "entity_name": "Town Guard",
      "state": "hostile",
      "fragments": ["hand moves to sword hilt", "steps forward to block path"],
      "response": "confrontation"
    },
    {
      "entity": "npc_alpha_wolf",
      "entity_name": "Alpha Wolf",
      "state": "aggressive",
      "fragments": ["hackles rise", "low growl"],
      "response": "defensive"
    },
    {
      "entity": "merchant_tomas",
      "entity_name": "Merchant Tomas",
      "state": "nervous",
      "fragments": ["backs away from stall", "eyes darting"],
      "response": "avoidance"
    }
  ],
  "hints": ["tension", "companion-conflict"]
}
```

**Narrator prompt guidance:**

```
## Multiple Entity Reactions

When `reactions` array is present:
- Describe each entity's reaction in sequence (not interwoven)
- Use fragments from each entity's entry
- Keep each reaction to 1-2 sentences
- Order reflects narrative priority (most important/urgent first)
- Maximum 5 entities; typically 2-3
```

**Expected output:**

> You enter the market square with your wolf companion. The town guard's hand moves to his sword hilt as he steps forward to block your path. Your wolf's hackles rise, a low growl building in its throat. Behind a nearby stall, Merchant Tomas backs away, eyes darting between you and the beast at your side.

**Handler aggregation:**

The infrastructure dispatcher collects individual event results into the `reactions` array:

```python
def aggregate_reactions(event_results: list[EventResult]) -> list[dict]:
    """Collect entity reactions from multiple event handlers."""
    reactions = []
    for result in event_results:
        if result.context and "reaction" in result.context:
            reactions.append(result.context["reaction"])
    return reactions[:5]  # Cap at 5
```

Each entity's behavior handler returns its own reaction context:

```python
def on_player_enters_with_beast(entity, accessor, context):
    return EventResult(
        allow=True,
        context={
            "reaction": {
                "entity": entity.id,
                "entity_name": entity.name,
                "state": get_current_state(entity),
                "fragments": select_state_fragments(entity),
                "response": "confrontation"
            }
        }
    )
```

This keeps the framework generic (just aggregates reactions into an array) while authors define what each entity's reaction contains.

### B.12 Test Scenario Approach

Rather than framework-defined test categories, authors define test scenarios for their games:

```python
# In big_game's test configuration
TEST_SCENARIOS = [
    TestScenario(
        name="wolf_becomes_friendly",
        setup=["go east", "give venison to wolf", "give venison to wolf"],
        test_command="give venison to wolf",
        must_contain=["wolf", "behavioral shift"],  # Author knows their fragments
        must_not_contain=["trust", "state machine", "+1"]  # No mechanics
    ),
    # ... more author-defined scenarios
]
```

The eval harness runs author-defined scenarios. The framework doesn't know what "trust-building" means - the author's tests verify their semantics are narrated correctly.

---

## Appendix C: Implementation Plan

This appendix details the implementation work required to support author-defined narration context across all games.

### C.1 Overview

The implementation requires changes at multiple levels:
1. **Framework types** (EventResult, HandlerResult, NarrationPlan)
2. **Framework code** (narration_assembler, dispatchers)
3. **Game data** (no game_state.json migration needed - llm_context format is compatible)
4. **Tests** (update for new types)

### C.2 Framework Type Extensions

#### C.2.1 Extend EventResult (src/state_accessor.py)

**Current:**
```python
@dataclass
class EventResult:
    allow: bool
    feedback: Optional[str] = None
```

**New:**
```python
@dataclass
class EventResult:
    allow: bool
    feedback: Optional[str] = None
    context: Optional[Dict[str, Any]] = None  # Author-defined narrator context
    hints: list[str] = field(default_factory=list)  # Author-defined hints
    fragments: Optional[Dict[str, Any]] = None  # Author-selected fragments
```

#### C.2.2 Extend HandlerResult (src/state_accessor.py)

**Current:**
```python
@dataclass
class HandlerResult:
    success: bool
    primary: str
    beats: list[str] = field(default_factory=list)
    data: Optional[Dict[str, Any]] = None
```

**New:**
```python
@dataclass
class HandlerResult:
    success: bool
    primary: str
    beats: list[str] = field(default_factory=list)
    data: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None  # Author-defined narrator context
    hints: list[str] = field(default_factory=list)  # Author-defined hints
    fragments: Optional[Dict[str, Any]] = None  # Author-selected fragments
    reactions: Optional[list[Dict[str, Any]]] = None  # Multi-entity reactions
```

#### C.2.3 Extend NarrationPlan (src/narration_types.py)

**Add new TypedDict and fields:**
```python
class ReactionRef(TypedDict, total=False):
    """Single entity reaction for multi-entity scenes."""
    entity: str
    entity_name: str
    state: str
    fragments: list[str]
    response: str

class NarrationPlan(TypedDict, total=False):
    # ... existing fields ...
    context: dict[str, Any]  # Author-defined context (passed through)
    hints: list[str]  # Author-defined hints (passed through)
    fragments: dict[str, Any]  # Selected fragments (state, action, etc.)
    reactions: list[ReactionRef]  # Multi-entity reactions
```

### C.3 Framework Code Updates

#### C.3.1 Update NarrationAssembler (src/narration_assembler.py)

Add methods to:
- Pass through `context` from handler to plan
- Pass through `hints` from handler to plan
- Merge `fragments` from handler with auto-selected fragments
- Aggregate `reactions` from multiple EventResults

#### C.3.2 Create Fragment Selection Helpers (utilities/narrator_context.py)

New helper module for authors:
```python
def select_state_fragments(entity: Any, state: str, max_count: int = 2) -> list[str]:
    """Select fragments from entity's llm_context.state_fragments[state]."""

def select_pack_fragments(entity: Any, state: str, max_count: int = 2) -> list[str]:
    """Select fragments from entity's llm_context.pack_fragments[state]."""

def build_reaction(entity: Any, state: str, response: str) -> dict:
    """Build a reaction dict for multi-entity scenes."""
```

#### C.3.3 Update Infrastructure Dispatchers

Files to modify in `examples/big_game/behaviors/shared/infrastructure/`:

| File | Changes |
|------|---------|
| `dispatcher_utils.py` | Add `merge_event_results()` for aggregating context/hints/reactions |
| `turn_phase_dispatcher.py` | Use merged results |
| `gift_reactions.py` | Return context in EventResult |
| `death_reactions.py` | Return context in EventResult |

### C.4 Game Data (No Migration Needed)

The existing `llm_context` structure in game_state.json files is **compatible** with the new design:
- `traits` - Already used, continues to work
- `state_variants` - Compatible with new `state_fragments` (can coexist)
- `action_fragments` - Already in some games, compatible

**New optional fields authors can add:**
- `state_fragments` - Fragments keyed by state name
- `pack_fragments` - Collective fragments for pack reactions

No migration tool needed for game_state.json files. Authors add new fragment pools as needed.

### C.5 Test Updates

#### C.5.1 Tests Requiring Updates

| Test File | Changes Needed |
|-----------|----------------|
| `tests/test_narration_types.py` | Add tests for new TypedDicts (ReactionRef, extended NarrationPlan) |
| `tests/test_narration_assembler.py` | Test context/hints/fragments pass-through |
| `tests/test_handler_llm_context.py` | Test fragment selection from state_fragments |
| `tests/test_interaction_handlers.py` | Update EventResult assertions for new fields |

#### C.5.2 Using LibCST for Bulk Updates

If EventResult/HandlerResult field additions cause widespread test failures, use `tools/refactor_using_LibCST.py` to update test assertions. However, since new fields have defaults, most existing tests should continue to pass.

### C.6 Work Breakdown

| Phase | Work | Effort |
|-------|------|--------|
| **1. Type Extensions** | Extend EventResult, HandlerResult, NarrationPlan | 1-2 hours |
| **2. Assembler Updates** | Pass through context/hints, add fragment merging | 2-3 hours |
| **3. Helper Module** | Create utilities/narrator_context.py | 1-2 hours |
| **4. Infrastructure Dispatchers** | Update merge logic in big_game infrastructure | 2-3 hours |
| **5. Test Updates** | Update tests for new types | 2-3 hours |
| **6. Narrator Prompt Updates** | Update narrator_protocol.txt for new fields | 1 hour |

**Total: ~10-14 hours**

### C.7 Backward Compatibility (NONE)

Per project guidelines, no backward compatibility code:
- New fields on EventResult/HandlerResult have defaults (empty list/None)
- Existing handlers continue to work - they just don't populate new fields
- Narrator gracefully handles missing context/hints/fragments (uses only what's provided)
- Tests are updated, not shimmed

### C.8 Per-Game Impact

| Game | Changes Needed |
|------|----------------|
| **simple_game** | None - basic game, no complex NPCs |
| **fancy_game** | None - enhanced descriptions but no NPC states |
| **extended_game** | None - magical items but no NPC states |
| **spatial_game** | None - positioning but no NPC states |
| **layered_game** | None - complex behaviors but no NPC state machines |
| **actor_interaction_test** | Optional - could add state_fragments for richer narration |
| **big_game** | Incremental - add state_fragments/pack_fragments to NPCs, update handlers to return context |

Only **big_game** requires significant content authoring work. Other games continue to work unchanged.

### C.9 Implementation Order

1. **Phase 1: Types** - Extend EventResult, HandlerResult, add ReactionRef, extend NarrationPlan
2. **Phase 2: Assembler** - Update NarrationAssembler to pass through new fields
3. **Phase 3: Helpers** - Create utilities/narrator_context.py with fragment selection helpers
4. **Phase 4: Tests** - Update test files for new types, verify all games still pass
5. **Phase 5: Dispatchers** - Update big_game infrastructure dispatchers
6. **Phase 6: Prompt** - Update narrator_protocol.txt with new field documentation
7. **Phase 7: big_game content** - Incrementally add state_fragments/pack_fragments to NPCs and update handlers

Phases 1-6 are framework work (~10-14 hours). Phase 7 is ongoing content authoring that can happen incrementally as NPC interactions are implemented.
