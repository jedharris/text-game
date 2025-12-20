# Unified Narration Design

**Status:** Proposed (supersedes individual design documents)
**Audience:** Engine developers, game authors
**Related Issues:** #214, #215

This document unifies several narration-related designs into a single coherent specification:
- `game_engine_narration_api_design.md` — Core API structure
- `structured_action_reports_design.md` — Fragment pools and handler structure
- `combat_stealth_scopes_and_beats_design.md` — Domain handling and beat counts

---

## Core Principle: Mechanical Engine, Intelligent Model

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

### 1.4 Unified Fragment Vocabulary

To avoid duplication, use consistent keys across all entities:

**Action verbs** (maps from game vocabulary):
`take`, `drop`, `open`, `close`, `lock`, `unlock`, `push`, `pull`, `climb`, `descend`, `enter`, `exit`, `examine`, `read`, `light`, `extinguish`, `attack`, `give`, `throw`

**Failure reasons**:
`too_heavy`, `not_portable`, `locked`, `not_visible`, `already_open`, `already_closed`, `no_key`, `wrong_key`, `not_container`, `inventory_full`, `out_of_reach`, `no_target`

**Effect types**:
`position_change`, `state_change`, `inventory_change`, `damage`, `healing`

**Position actions**:
`step_up`, `step_down`, `climb_up`, `climb_down`, `enter`, `exit`

### 1.5 Reducing Author Duplication

**Inherited defaults**: Entity types can define default fragments:

```json
{
  "entity_type": "weapon",
  "default_fragments": {
    "take": {
      "core": ["you take the weapon", "you pick up the weapon"],
      "color": ["testing its balance", "its weight familiar"]
    }
  }
}
```

Individual weapons only override when they need something specific.

**Shared fragment libraries**: Common fragments can be defined once and referenced:

```json
{
  "fragment_library": {
    "heavy_object_failure": {
      "too_heavy": {
        "core": ["it's too heavy to move", "you can't budge it"],
        "color": ["muscles straining", "feet sliding on the floor"]
      }
    }
  }
}
```

Entities reference: `"failure_fragments": "@heavy_object_failure"`

**Trait inheritance**: Sub-types can inherit and extend traits:
- Base `weapon` traits: `["well-crafted", "balanced"]`
- Specific `sword` adds: `["keen edge", "leather-wrapped hilt"]`

### 1.6 Fallback Hierarchy

When fragments are missing, the engine uses fallbacks (no authoring required for basic functionality):

1. Entity-specific fragments
2. Entity-type default fragments
3. Global generic fragments

Global generics (defined once in engine):
```python
GENERIC_FRAGMENTS = {
    "take": {"core": ["you take it"], "color": []},
    "drop": {"core": ["you put it down"], "color": []},
    "open": {"core": ["you open it"], "color": []},
    # ... etc
}
```

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
4. Implement fallback hierarchy
5. Create generic fallback fragments

**Tests**: Selection counts, buffer behavior, fallbacks

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

### 7.3 Avoiding Duplication

1. **Use type defaults**: Define once for entity type, override only when needed
2. **Use fragment libraries**: Share common fragments across entities
3. **Inherit traits**: Base type provides common traits, specific entity adds unique ones
4. **Generic fallbacks exist**: Don't author fragments for every possible action—fallbacks work

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
