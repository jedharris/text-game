# Game Engine Narration API – Design Specification

## Purpose
This document defines a **narration‑oriented engine API** whose goal is to eliminate conditional reasoning inside the language model. The engine computes all viewpoint, scope, and precedence decisions up‑front and delivers a narrator‑ready plan. The language model’s role is strictly *rendering prose* according to the provided plan and style rules.

This specification is intended as a **target architecture** for refactoring the current implementation.

---

## Design Principles

1. **No inference in the narrator**
   The model should not deduce viewpoint, reachability, familiarity, or narrative scope.

2. **Single authoritative narration plan**
   All narrator‑relevant decisions are delivered in a dedicated object.

3. **Human‑readable but machine‑authoritative**
   Fields are optimized for direct prose rendering, not internal mechanics.

4. **Extensible without prompt churn**
   New mechanics (combat, stealth, dialogue) should require API changes, not narrator logic changes.

---

## Top‑Level Turn Result

```json
{
  "success": true,
  "verbosity": "full",
  "narration": { ... },
  "data": { ... }
}
```

### Required Fields

- `success` (boolean)
- `verbosity`: `"brief" | "full"`
- `narration`: **authoritative narration plan**

### Optional Fields

- `data`: raw engine data (for debugging, UI, or future use). The narrator does not rely on this.

---

## The Narration Object

The `narration` object is the sole authoritative input for prose rendering.

```json
"narration": {
  "primary_text": "You pick up the rusty sword.",
  "secondary_beats": [ "Its pitted blade feels heavier than expected." ],
  "viewpoint": { ... },
  "scope": { ... },
  "must_mention": { ... },
  "entity_refs": { ... }
}
```

---

## Primary Text

```json
"primary_text": "You pick up the rusty sword."
```

**Contract:**
- The core statement of what occurred
- Always suitable for direct narration
- Used alone (or with minimal enhancement) for `brief` verbosity
- Typically one sentence, but may be multiple for compound actions

The engine must *always* provide this. It comes directly from the handler's `primary` field.

---

## Secondary Beats

```json
"secondary_beats": [
  "You step down from the table.",
  "The pitted blade feels heavier than expected."
]
```

Short sentences that supplement the primary text. Two sources:

1. **Handler beats**: Side effects or context from the action (e.g., positioning changes)
2. **Trait beats**: Sensory details selected from entity `llm_context.traits`

### Handler Responsibility

Handlers return a structured result:
```python
HandlerResult(
    success=True,
    primary="You pick up the rusty sword.",
    beats=["You step down from the table."],
    data={...}
)
```

### Engine Responsibility

The engine assembles `secondary_beats` by:
1. Including all handler-provided beats
2. Selecting additional beats from entity traits (for `full` verbosity)

### Narrator Responsibility

- For `brief`: Use `primary_text` alone or with minimal beats
- For `full`: Weave `primary_text` and `secondary_beats` into cohesive prose

---

## Viewpoint

```json
"viewpoint": {
  "mode": "ground" | "elevated" | "concealed",
  "posture": "climbing" | "on_surface" | "behind_cover" | null,
  "focus_name": "the oak tree"
}
```

Provides mechanical data about the player's perspective. The narrator uses this to frame descriptions appropriately.

### Field Definitions

- `mode`: General perspective category
  - `"ground"`: Normal standing position (default)
  - `"elevated"`: Player is above ground level (climbing, on surface)
  - `"concealed"`: Player is hidden (behind cover, inside container)

- `posture`: Specific positioning state (from actor properties)
  - `null`: Normal standing
  - `"climbing"`: Actively climbing something
  - `"on_surface"`: Standing/sitting on a surface
  - `"behind_cover"`: Using something as cover

- `focus_name`: Human-readable name of the entity the player is positioned at/on/in

### Engine Responsibilities

- Resolve posture and focus from actor properties
- Determine mode from posture
- Resolve focus entity name for narration

### Narrator Responsibilities

The **prompt** (not per-turn data) contains rules for each mode:
- `"ground"`: Normal narration
- `"elevated"`: Describe looking down, mention items below
- `"concealed"`: Describe limited visibility, enclosed feeling

### Design Note

The engine provides **mechanical data only**. Prose generation (e.g., "From the lower branches, you look down...") is the LLM's job, guided by mode-specific rules in the prompt.

---

## Scope

```json
"scope": {
  "scene_kind": "location_entry" | "look" | "action_result",
  "outcome": "success" | "failure",
  "familiarity": "new" | "familiar"
}
```

Defines *what kind of narration this is* using purely mechanical classifications.

### Field Definitions

- `scene_kind`: Determined by verb type
  - `"location_entry"`: Movement commands (`go`, directions)
  - `"look"`: Observation commands (`look`, `examine`)
  - `"action_result"`: All other commands

- `outcome`: Direct mapping from `success` field
  - `"success"`: Action succeeded
  - `"failure"`: Action failed

- `familiarity`: Based on visit/examination tracking
  - `"new"`: First time seeing this location or entity
  - `"familiar"`: Previously visited or examined

### Design Note

Topic restrictions (what to include/exclude in narration) belong in the **invariant prompt section**, not in per-turn data. These are style constraints that apply consistently based on `scene_kind`, not game-state-dependent decisions that the engine must compute.

---

## Entity References

```json
"entity_refs": {
  "item_sword": {
    "name": "rusty sword",
    "type": "item",
    "traits": ["pitted blade", "leather-wrapped hilt", "heavier than expected"],
    "spatial_relation": "below",
    "salience": "high"
  },
  "item_chest": {
    "name": "wooden chest",
    "type": "container",
    "traits": ["iron bands", "dust-covered"],
    "state": {"open": true},
    "salience": "medium"
  }
}
```

Each relevant entity in the scene is included with its narration-ready data.

### Field Definitions

- `name`: Display name for the entity
- `type`: Entity type (item, container, door, actor, exit)
- `traits`: Sensory/descriptive phrases from `llm_context` (randomized, limited)
- `spatial_relation`: Position relative to player (for elevated/concealed viewpoints)
  - `"within_reach"`, `"below"`, `"above"`, `"nearby"`
- `state`: Relevant state flags (open, locked, lit, etc.)
- `salience`: How prominently to mention (`"high"`, `"medium"`, `"low"`)

### Engine Responsibilities

- Include all visible/relevant entities
- Select and randomize traits from `llm_context`
- Compute spatial relations based on viewpoint
- Determine salience based on action relevance

### Narrator Responsibilities

- Use traits to craft descriptive prose
- Respect spatial relations when describing positions
- Prioritize high-salience entities in narration

---

## Must‑Mention Fields

```json
"must_mention": {
  "exits_text": "Exits lead north to the corridor and east to the pantry."
}
```

Pre‑formatted text that **must appear** in narration when relevant.

Typical uses:
- Complete exits descriptions
- Mandatory warnings or scene constraints

---

## Failure Handling

For failures:
- `primary_text` must already contain the correct player‑facing message
- `scope.outcome` will be `"failure"`
- No secondary beats are required

The narrator does not reinterpret or soften failures.

---

## Engine Modules (Suggested)

1. **ViewpointResolver**
2. **ScopeClassifier**
3. **EntityRefBuilder**
4. **ExitTextFormatter**
5. **BeatSelector** (optional but recommended)
6. **NarrationAssembler**

Each module contributes to the final `narration` object.

---

## Outcome

With this design:
- The narrator performs *no conditional reasoning*
- Prompts remain stable as the engine grows
- Narration quality improves without increasing model size or latency

