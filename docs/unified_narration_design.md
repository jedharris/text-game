# Unified Narration Design

**Status:** Proposed (supersedes individual design documents)
**Audience:** Engine developers, game authors
**Related Issues:** #214, #215

This document unifies several narration-related designs into a single coherent specification:
- `game_engine_narration_api_design.md` — Core API structure
- `structured_action_reports_design.md` — Fragment pools and handler structure
- `combat_stealth_scopes_and_beats_design.md` — Domain handling and beat counts

---

## Core Principles

### Mechanical Engine, Intelligent Model

The engine performs only **mechanical operations**:
- State lookup
- Random selection from pools
- Counting
- Ring buffer management

All **intelligence** resides in the model:
- Prose synthesis
- Tone and pacing
- Fragment weaving
- Contextual emphasis

This separation ensures the engine remains simple, testable, and predictable.

### Fail Loud, Not Silent

Missing or invalid data is an authoring error. The engine must **fail loudly** at load time, never silently degrade at runtime.

- **Missing fragments**: Raise `MissingFragmentError` with specific guidance
- **Invalid keys**: Raise validation error listing the problem
- **Malformed pools**: Raise error explaining the structure requirement

Authors discover problems immediately during development, not after releasing the game. There are no silent fallbacks or graceful degradation for authoring errors.

---

## Part 1: Fragment Architecture

### 1.1 Design Philosophy

Narration is built from **pre-authored fragments** stored in game data. The engine selects fragments mechanically; the model weaves them into prose. This achieves:

- **Variety** through combinatorial selection (core × color × state × traits)
- **Author voice** preserved in authored phrases
- **Simple handlers** that return structure, not prose
- **Predictable quality** from tested fragments

### 1.2 Fragment Types

All fragments live in an entity's `llm_context`:

```json
{
  "id": "item_sword",
  "name": "sword",
  "llm_context": {
    "traits": ["pitted blade", "leather-wrapped hilt", "notches from past battles"],

    "state_variants": {
      "in_location": ["lies forgotten on the floor", "rests against the wall"],
      "in_inventory": ["a reassuring weight at your side", "ready at hand"]
    },

    "action_fragments": {
      "take": {
        "core": ["you claim the blade", "you pick up the sword"],
        "color": ["rust flakes onto your palm", "its weight settles into your grip"]
      },
      "drop": {
        "core": ["you set aside the weapon", "you release the blade"],
        "color": ["with reluctance", "it clatters on stone"]
      }
    },

    "failure_fragments": {
      "too_heavy": {
        "core": ["it refuses to budge", "you can't lift it"],
        "color": ["no matter how you strain"]
      }
    }
  }
}
```

For actors:

```json
{
  "id": "actor_merchant",
  "llm_context": {
    "traits": ["weathered face", "keen eyes", "calloused hands"],

    "behavior_fragments": {
      "accept_gift": {
        "core": ["nods appreciatively", "accepts with a smile"],
        "color": ["eyes brightening", "weighing it carefully"]
      },
      "attack": {
        "core": ["lunges with surprising speed", "strikes without warning"],
        "color": ["eyes gone cold", "merchant's facade dropping"]
      }
    },

    "dialogue_fragments": {
      "greeting": ["'Welcome, traveler.'", "'Ah, a customer!'"],
      "thanks": ["'You have my gratitude.'", "'Most generous.'"]
    }
  }
}
```

For locations:

```json
{
  "id": "loc_frozen_cavern",
  "llm_context": {
    "traits": ["ice-slicked walls", "breath visible", "icicles overhead"],
    "atmosphere": "cold, echoing, treacherous",

    "effect_fragments": {
      "cold_damage": {
        "core": ["the cold bites deep", "you shiver uncontrollably"],
        "color": ["fingers numbing", "teeth chattering"]
      }
    }
  }
}
```

### 1.3 Fragment Structure

Every fragment pool uses the same structure:

```json
{
  "fragment_key": {
    "core": ["required phrase 1", "required phrase 2"],
    "color": ["optional embellishment 1", "optional embellishment 2"]
  }
}
```

- **core**: Required. Engine selects exactly 1 per action.
- **color**: Optional. Engine selects 0-2 for variety.

Simple fragment types (traits, dialogue, state_variants) are just arrays—the engine treats the whole array as a pool and selects from it.

### 1.4 Fragment Key Vocabulary

Fragment keys must be consistent across entities so the engine can look them up. Keys are defined in **game data**, not engine code, allowing games to extend the vocabulary as they add behaviors.

#### Where Keys Are Defined

The game's `vocabulary.json` (or equivalent) defines fragment keys alongside word definitions:

```json
{
  "vocabulary": {
    "take": {
      "type": "verb",
      "synonyms": ["get", "grab", "pick up", "acquire"],
      "fragment_key": "take"
    },
    "attack": {
      "type": "verb",
      "synonyms": ["hit", "strike", "fight"],
      "fragment_key": "attack"
    }
  },

  "fragment_keys": {
    "actions": ["take", "drop", "open", "close", "lock", "unlock", "push", "pull",
                "climb", "descend", "enter", "exit", "examine", "read", "light",
                "extinguish", "attack", "give", "throw"],

    "failures": ["too_heavy", "not_portable", "locked", "not_visible", "already_open",
                 "already_closed", "no_key", "wrong_key", "not_container", "inventory_full",
                 "out_of_reach", "no_target"],

    "effects": ["position_change", "state_change", "inventory_change", "damage", "healing"],

    "position_actions": ["step_up", "step_down", "climb_up", "climb_down", "enter", "exit"]
  }
}
```

#### How Keys Are Extended

When a game adds new behaviors:

1. **Add the fragment key** to `fragment_keys` in vocabulary
2. **Add the verb mapping** if it's a new verb (maps synonyms → canonical key)
3. **Author fragments** in entity `llm_context` using the new key

Example: Adding a "repair" behavior:

```json
{
  "fragment_keys": {
    "actions": [..., "repair"]
  },
  "vocabulary": {
    "repair": {
      "type": "verb",
      "synonyms": ["fix", "mend", "restore"],
      "fragment_key": "repair"
    }
  }
}
```

Then in entities:
```json
{
  "id": "item_broken_sword",
  "llm_context": {
    "action_fragments": {
      "repair": {
        "core": ["you hammer out the dents", "you restore the blade"],
        "color": ["sparks flying", "the metal singing"]
      }
    }
  }
}
```

#### Validation

The engine validates at load time:
- All `action_fragments` keys exist in `fragment_keys.actions`
- All `failure_fragments` keys exist in `fragment_keys.failures`
- All vocabulary entries with `fragment_key` reference valid keys

This catches typos early rather than at runtime.

#### Standard Keys

Core engine behaviors use these standard keys (games may add more):

**Action verbs** (maps from game vocabulary):
`take`, `drop`, `open`, `close`, `lock`, `unlock`, `push`, `pull`, `climb`, `descend`, `enter`, `exit`, `examine`, `read`, `light`, `extinguish`, `attack`, `give`, `throw`

**Failure reasons**:
`too_heavy`, `not_portable`, `locked`, `not_visible`, `already_open`, `already_closed`, `no_key`, `wrong_key`, `not_container`, `inventory_full`, `out_of_reach`, `no_target`

**Effect types**:
`position_change`, `state_change`, `inventory_change`, `damage`, `healing`

**Position actions**:
`step_up`, `step_down`, `climb_up`, `climb_down`, `enter`, `exit`

### 1.5 Required Fragments — No Silent Fallbacks

**Critical design principle**: Missing fragments are authoring errors. The engine must fail loudly, not silently degrade.

When the engine cannot find a required fragment, it raises an error:

```python
class FragmentResolver:
    def resolve_action(self, entity_id: str, verb: str) -> FragmentPool:
        entity = self.get_entity(entity_id)
        fragments = entity.llm_context.get("action_fragments", {})

        if verb not in fragments:
            raise MissingFragmentError(
                f"Entity '{entity_id}' has no action_fragments for verb '{verb}'. "
                f"Add action_fragments.{verb} to the entity's llm_context."
            )

        pool = fragments[verb]
        if not pool.get("core"):
            raise MissingFragmentError(
                f"Entity '{entity_id}' action_fragments.{verb} has no 'core' pool. "
                f"At least one core fragment is required."
            )

        return pool
```

**What must be authored for each entity:**

| Entity supports... | Required fragments |
|-------------------|-------------------|
| `take` action | `action_fragments.take.core` |
| `open` action | `action_fragments.open.core` |
| failure reason `locked` | `failure_fragments.locked.core` |
| state `in_inventory` | `state_variants.in_inventory` |
| narration at all | `traits` (minimum 5) |

**Color fragments are optional** — if missing, the engine simply doesn't include color. This is not an error.

**Validation timing**: The engine validates fragment completeness at game load time, not runtime. Authors discover missing fragments immediately when testing, not after releasing the game.

### 1.6 Load-Time Validation

The engine performs comprehensive validation when loading game data:

```python
def validate_entity_fragments(entity: Entity, vocabulary: Vocabulary) -> list[str]:
    """Returns list of validation errors. Empty list = valid."""
    errors = []
    ctx = entity.llm_context or {}

    # Check traits exist and meet minimum
    traits = ctx.get("traits", [])
    if len(traits) < 5:
        errors.append(f"{entity.id}: traits has {len(traits)} items, minimum is 5")

    # Check action_fragments keys are valid
    for verb in ctx.get("action_fragments", {}):
        if verb not in vocabulary.fragment_keys.actions:
            errors.append(f"{entity.id}: action_fragments.{verb} is not a valid action key")

    # Check failure_fragments keys are valid
    for reason in ctx.get("failure_fragments", {}):
        if reason not in vocabulary.fragment_keys.failures:
            errors.append(f"{entity.id}: failure_fragments.{reason} is not a valid failure key")

    # Check each pool has required core
    for verb, pool in ctx.get("action_fragments", {}).items():
        if not pool.get("core"):
            errors.append(f"{entity.id}: action_fragments.{verb} missing 'core' pool")

    return errors
```

**Validation runs at load time** and fails the game load if any errors are found. This ensures authors catch problems during development.

### 1.7 Future: Reducing Author Duplication (Deferred)

The following features could reduce authoring effort but add engine complexity. They are **not in scope for the initial implementation** but can be added later if needed:

**Type-level defaults** (deferred): Entity types (weapon, container, door) could define default fragments inherited by all entities of that type.

**Fragment libraries** (deferred): Shared fragment pools that multiple entities reference by name (e.g., `"@heavy_object_failure"`).

**Trait inheritance** (deferred): Sub-types could inherit and extend parent type traits.

These can be cleanly added later because:
- The fragment lookup is already centralized in `FragmentResolver`
- Adding inheritance just changes where `FragmentResolver` searches
- Entity data format is forward-compatible (current entities won't break)

---

## Part 2: Domain Handling

### 2.1 Domain Classification

The engine classifies each turn into a domain:

- **default**: Normal exploration and interaction
- **combat**: Active combat resolution
- **stealth**: Stealth/infiltration mode

Domain is determined mechanically from game state (combat_active, stealth_active flags).

### 2.2 Scope Extension

The existing `scope` object gains domain information:

```json
"scope": {
  "scene_kind": "action_result",
  "outcome": "success",
  "familiarity": "familiar",
  "domain": "combat",
  "subtype": "melee"
}
```

**Domain values**: `default`, `combat`, `stealth`

**Subtype values**:
- Combat: `melee`, `ranged`, `spell`, `defense`
- Stealth: `infiltration`, `detection`, `pursuit`
- Default: (empty)

### 2.3 Fragment Counts by Domain and Verbosity

The engine uses fixed counts—no scoring, no token budgets, no "smart" selection:

| Domain | Verbosity | Core | Color | Traits | State |
|--------|-----------|------|-------|--------|-------|
| default | brief | 1 | 0 | 0 | 0 |
| default | full | 1 | 1-2 | 2-3 | 1 |
| combat | brief | 1 | 0 | 0 | 0 |
| combat | full | 1 | 1 | 1-2 | 0 |
| stealth | brief | 1 | 0 | 1 | 0 |
| stealth | full | 1 | 1-2 | 2-4 | 1 |

Combat uses fewer fragments (fast pacing). Stealth uses more sensory traits (atmosphere).

Selection is purely random within these counts. No relevance scoring.

### 2.4 Stealth Visibility Rule

**Critical constraint**: Stealth narration never reveals unrevealed entities.

The engine enforces this mechanically:
- Only entities marked `revealed: true` appear in `entity_refs`
- Only fragments from revealed entities are included
- If an entity isn't revealed, it doesn't exist for narration

This is a hard filter, not a scoring adjustment.

---

## Part 3: Repetition Control

### 3.1 Ring Buffer

The engine maintains a ring buffer of recently-used fragment keys:

```python
class RepetitionBuffer:
    def __init__(self, size: int = 5):
        self.buffer = deque(maxlen=size)

    def is_recent(self, key: str) -> bool:
        return key in self.buffer

    def add(self, key: str) -> None:
        self.buffer.append(key)
```

Keys are derived from fragments:
- Trait: `"trait:pitted blade"`
- Action core: `"action:take:0"` (pool index)
- State variant: `"state:in_inventory:1"`

### 3.2 Selection with Repetition Avoidance

When selecting from a pool:

```python
def select_from_pool(pool: list[str], buffer: RepetitionBuffer) -> str:
    available = [f for f in pool if not buffer.is_recent(key_for(f))]
    if not available:
        # Buffer exhausted - use any fragment
        available = pool
    selected = random.choice(available)
    buffer.add(key_for(selected))
    return selected
```

No "unless critical" exceptions. If the buffer is exhausted for a pool, simply select from the full pool.

### 3.3 Buffer Sizing

Default: 5 turns. This prevents immediate repetition while allowing reasonable cycling.

Combat may use a smaller buffer (3) due to faster pace and fewer fragments.

---

## Part 4: Engine API

### 4.1 Handler Returns

Handlers return pure structure:

```python
@dataclass
class HandlerResult:
    success: bool
    action: ActionReport
    effects: list[EffectReport] = field(default_factory=list)
    data: dict = field(default_factory=dict)

@dataclass
class ActionReport:
    verb: str                    # Canonical verb
    object_id: Optional[str]     # Target entity
    outcome: Literal["success", "failure"]
    failure_reason: Optional[str] = None
    indirect_object_id: Optional[str] = None  # For "give X to Y"
    instrument_id: Optional[str] = None       # For "unlock X with Y"

@dataclass
class EffectReport:
    type: str           # position_change, state_change, etc.
    action: str         # step_down, open, etc.
    target_id: str
    from_id: Optional[str] = None
```

### 4.2 Fragment Resolution

The `FragmentResolver` performs lookups and selection:

```python
class FragmentResolver:
    def resolve(
        self,
        action: ActionReport,
        effects: list[EffectReport],
        domain: str,
        verbosity: str
    ) -> ResolvedFragments:
        counts = FRAGMENT_COUNTS[domain][verbosity]

        return ResolvedFragments(
            action_core=self._select_one(entity.action_fragments[action.verb].core),
            action_color=self._select_n(entity.action_fragments[action.verb].color, counts.color),
            state=self._select_one(entity.state_variants[new_state]) if counts.state else None,
            traits=self._select_n(entity.traits, counts.traits),
            effects=[self._resolve_effect(e, counts) for e in effects]
        )
```

All selection is random with repetition avoidance. No scoring.

### 4.3 Narration Plan Output

The complete plan sent to the model:

```json
{
  "success": true,
  "verbosity": "full",
  "narration": {
    "action": {
      "verb": "take",
      "object": "sword",
      "outcome": "success"
    },
    "fragments": {
      "action_core": "you claim the blade",
      "action_color": ["rust flakes onto your palm"],
      "new_state": "a reassuring weight at your side",
      "traits": ["pitted blade", "leather-wrapped hilt"]
    },
    "effects": [
      {
        "core": "stepping down from the table",
        "color": "its surface creaking"
      }
    ],
    "viewpoint": {
      "mode": "ground",
      "posture": null,
      "focus_name": null
    },
    "scope": {
      "scene_kind": "action_result",
      "outcome": "success",
      "familiarity": "familiar",
      "domain": "default"
    },
    "entity_refs": {
      "item_sword": {
        "name": "rusty sword",
        "type": "item"
      }
    },
    "must_mention": {}
  }
}
```

### 4.4 Type Definitions

```python
class ResolvedFragments(TypedDict, total=False):
    action_core: str              # Required
    action_color: list[str]       # 0-2 items
    new_state: Optional[str]      # May be absent
    traits: list[str]             # 0-4 items
    failure_core: Optional[str]   # For failures
    failure_color: list[str]      # For failures

class ResolvedEffect(TypedDict, total=False):
    type: str
    core: str
    color: Optional[str]

class NarrationPlan(TypedDict, total=False):
    action: ActionReport
    fragments: ResolvedFragments
    effects: list[ResolvedEffect]
    viewpoint: ViewpointInfo
    scope: ScopeInfo
    entity_refs: dict[str, EntityRef]
    must_mention: MustMention
```

---

## Part 5: Narrator Prompt

### 5.1 Section A: Engine API (Invariant)

```
You are the narrator for a text adventure game.

Your ONLY job is to weave JSON fragments into immersive prose.

Each input contains pre-selected text fragments and structured data.
Do not infer or assume anything not present in the input.

OUTPUT RULES
- Output ONLY plain prose text
- Never output JSON, code blocks, or field names
- Never mention game mechanics or internal data

FRAGMENT WEAVING

The engine provides pre-selected fragments. Weave them into natural prose.

REQUIRED (must appear in output):
- fragments.action_core — the core action statement
- fragments.new_state — how the entity is after the action (when present)
- effects[].core — any effect statements

OPTIONAL (weave in naturally):
- fragments.action_color — embellishment for the action
- effects[].color — embellishment for effects
- fragments.traits — sensory details

WEAVING GUIDELINES:
- Combine fragments into flowing sentences
- Use traits to add texture and atmosphere
- Never list fragments mechanically
- Vary sentence structure
- Connect fragments with natural transitions

EXAMPLE:

Input:
{
  "fragments": {
    "action_core": "you claim the blade",
    "action_color": ["rust flakes onto your palm"],
    "new_state": "a reassuring weight at your side",
    "traits": ["pitted blade", "leather-wrapped hilt"]
  }
}

Good output:
"You claim the blade, rust flaking onto your palm. The pitted steel
 is a reassuring weight at your side."

Bad output (mechanical):
"You claim the blade. Rust flakes onto your palm. Pitted blade.
 Leather-wrapped hilt. A reassuring weight at your side."

VIEWPOINT MODES

- ground: Normal perspective. Describe straightforwardly.
- elevated: Player is above ground. Describe looking down.
- concealed: Player is hidden. Describe limited visibility.

SCOPE

- scene_kind: location_entry (arrival), look (observation), action_result (action)
- outcome: success or failure
- domain: default, combat, stealth

For combat: Keep descriptions punchy. Fast pace.
For stealth: Emphasize sensory details. Tension.

FAILURES

When outcome is "failure":
- Use fragments.failure_core as the base
- Add fragments.failure_color if present
- Do not soften or explain further

MUST-MENTION

Include any text in must_mention verbatim (typically exits).
```

### 5.2 Section B: Style (Game-Specific)

Game authors provide style instructions:

```
{{STYLE_PROMPT}}
```

Example:
```
Write in second person, present tense.
Use vivid, sensory language.
Keep sentences varied in length.
For combat, favor short punchy sentences.
Never use exclamation marks.
```

---

## Part 6: Implementation Phases

### Phase 1: Schema Extension

**Goal**: Define fragment schema and extend types.

**Tasks**:
1. Add fragment types to `llm_context` schema documentation
2. Extend `NarrationPlan` types with `fragments` and `effects`
3. Define `ResolvedFragments` and `ResolvedEffect` types
4. Add `domain` and `subtype` to `ScopeInfo`
5. Write validation for fragment structure

**Tests**: Schema validation, type checking

### Phase 2: Fragment Resolution

**Goal**: Implement the FragmentResolver.

**Tasks**:
1. Create `FragmentResolver` class
2. Implement pool selection with counts
3. Implement repetition buffer
4. Implement `MissingFragmentError` for missing required fragments
5. Add load-time validation for fragment completeness

**Tests**: Selection counts, buffer behavior, missing fragment errors

### Phase 3: Handler Migration (Pilot)

**Goal**: Migrate 3-4 handlers to return structure.

**Tasks**:
1. Select handlers: `take`, `drop`, `open`, `examine`
2. Refactor to return `ActionReport` + `EffectReport`
3. Remove prose generation from handlers
4. Update tests

**Tests**: Handler output structure, fragment integration

### Phase 4: Prompt Update

**Goal**: Update narrator prompt for fragment weaving.

**Tasks**:
1. Create new prompt with fragment weaving rules
2. Test with sample JSON and model
3. Tune examples and guidelines
4. Validate with pilot handlers

**Tests**: Manual quality review

### Phase 5: Full Handler Migration

**Goal**: Migrate all remaining handlers.

**Tasks**:
1. Migration in handler groups (manipulation, containers, etc.)
2. Author fragments for game entities
3. Update integration tests
4. Performance validation

### Phase 6: Domain Implementation

**Goal**: Add combat/stealth domain handling.

**Tasks**:
1. Implement domain classification
2. Apply fragment count tables
3. Implement stealth visibility filter
4. Update prompt with domain guidance

---

## Part 7: Authoring Guidelines

### 7.1 Fragment Quality

**Good fragments**:
- Complete, grammatical phrases
- Evocative sensory details
- Varying sentence starters
- Mix of short and medium length

**Bad fragments**:
- Mechanical descriptions ("it is heavy")
- Numbers or mechanics ("3 damage")
- Incomplete thoughts
- All starting the same way

### 7.2 Pool Sizing

| Fragment Type | Minimum | Recommended |
|--------------|---------|-------------|
| action core | 2 | 3-4 |
| action color | 2 | 4-6 |
| state variant | 2 | 3-4 |
| failure core | 1 | 2-3 |
| traits | 5 | 15-25 |

More fragments = more variety. The engine selects small subsets, so large pools don't burden the model.

### 7.3 Authoring Workflow

Fragments are required, not optional. The load-time validation ensures you author what's needed:

1. **Add entity to game**: Define the entity with its behaviors
2. **Run validation**: Load the game — validation will list missing fragments
3. **Author required fragments**: Add the fragments the validator requests
4. **Test and iterate**: Run the game, observe narration, improve weak fragments

The validator tells you exactly what's missing. You can't accidentally ship a game with missing fragments because it won't load.

### 7.4 Fragment Testing

Validate fragments produce good narration:
1. Generate sample JSON with all fragment combinations
2. Run through model
3. Review output quality
4. Identify weak fragments and improve

---

## Appendix A: Complete Type Definitions

```python
from typing import TypedDict, Literal, Optional
from dataclasses import dataclass, field

# Scope with domain
class ScopeInfo(TypedDict):
    scene_kind: Literal["location_entry", "look", "action_result"]
    outcome: Literal["success", "failure"]
    familiarity: Literal["new", "familiar"]
    domain: Literal["default", "combat", "stealth"]
    subtype: Optional[str]

# Handler output
@dataclass
class ActionReport:
    verb: str
    object_id: Optional[str]
    outcome: Literal["success", "failure"]
    failure_reason: Optional[str] = None
    indirect_object_id: Optional[str] = None
    instrument_id: Optional[str] = None

@dataclass
class EffectReport:
    type: str
    action: str
    target_id: str
    from_id: Optional[str] = None

@dataclass
class HandlerResult:
    success: bool
    action: ActionReport
    effects: list[EffectReport] = field(default_factory=list)
    data: dict = field(default_factory=dict)

# Resolved fragments for narration
class ResolvedFragments(TypedDict, total=False):
    action_core: str
    action_color: list[str]
    new_state: Optional[str]
    traits: list[str]
    failure_core: Optional[str]
    failure_color: list[str]

class ResolvedEffect(TypedDict, total=False):
    type: str
    core: str
    color: Optional[str]

# Viewpoint (unchanged)
class ViewpointInfo(TypedDict, total=False):
    mode: Literal["ground", "elevated", "concealed"]
    posture: Optional[Literal["climbing", "on_surface", "behind_cover"]]
    focus_name: Optional[str]

# Entity reference (unchanged)
class EntityState(TypedDict, total=False):
    open: bool
    locked: bool
    lit: bool

class EntityRef(TypedDict, total=False):
    name: str
    type: Literal["item", "container", "door", "actor", "exit", "location"]
    traits: list[str]
    spatial_relation: Literal["within_reach", "below", "above", "nearby"]
    state: EntityState
    salience: Literal["high", "medium", "low"]

class MustMention(TypedDict, total=False):
    exits_text: str

# Complete narration plan
class NarrationPlan(TypedDict, total=False):
    action: ActionReport
    fragments: ResolvedFragments
    effects: list[ResolvedEffect]
    viewpoint: ViewpointInfo
    scope: ScopeInfo
    entity_refs: dict[str, EntityRef]
    must_mention: MustMention

class NarrationResult(TypedDict):
    success: bool
    verbosity: Literal["brief", "full"]
    narration: NarrationPlan
    data: dict
```

---

## Appendix B: Fragment Count Tables

### Default Domain

| Verbosity | Core | Color | Traits | State |
|-----------|------|-------|--------|-------|
| brief | 1 | 0 | 0 | 0 |
| full | 1 | 1-2 | 2-3 | 1 |

### Combat Domain

| Verbosity | Core | Color | Traits | State |
|-----------|------|-------|--------|-------|
| brief | 1 | 0 | 0 | 0 |
| full | 1 | 1 | 1-2 | 0 |

### Stealth Domain

| Verbosity | Core | Color | Traits | State |
|-----------|------|-------|--------|-------|
| brief | 1 | 0 | 1 | 0 |
| full | 1 | 1-2 | 2-4 | 1 |

---

## Appendix C: Comparison with Previous Designs

### What This Design Consolidates

| Source Document | What's Kept | What's Changed |
|-----------------|-------------|----------------|
| game_engine_narration_api_design.md | Viewpoint, scope, entity_refs, must_mention | Added fragments, domain |
| structured_action_reports_design.md | Fragment pools, core/color structure | Removed scoring, simplified selection |
| combat_stealth_scopes_and_beats_design.md | Domain classification, stealth visibility | Fixed counts replace token budgets |

### What's Removed

1. **Relevance scoring** — Pure random selection instead
2. **Topic filtering at runtime** — Authoring-time concern
3. **"Unless critical" exceptions** — Simple buffer exhaustion fallback
4. **Token budget packing** — Fixed counts by domain/verbosity
5. **Beat selection complexity** — Fragments replace beats

### Rationale

The previous designs included "smart" features that required engine-side judgment. This unified design removes all such features, keeping the engine purely mechanical. The model handles all intelligent prose decisions.
