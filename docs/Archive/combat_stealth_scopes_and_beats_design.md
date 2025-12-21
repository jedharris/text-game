# Design: Combat/Stealth Scopes and Beat Selection (Token-Budget Targeting)

**Status:** Proposed  
**Audience:** Engine developers  
**Assumptions:** The revised narration API and unified prompt are already implemented (i.e., engine emits `narration.primary_text`, `narration.scope`, `narration.viewpoint`, `narration.must_mention`, `narration.entity_refs`, and the narrator prompt consumes them as authoritative). The current system has *no* beats.

This document specifies two enhancements:
1. **Adding Combat/Stealth scopes** using the existing `narration.scope` mechanism (no prompt changes required).
2. **Adding beat selection** with **dynamic token-budget targeting** to trade latency for richness per turn.

---

## 1. Goals and Non-Goals

### Goals
- Extend `narration.scope` to cover **combat** and **stealth** turns without increasing narrator conditional logic.
- Provide a **unified engine-side design** to introduce `secondary_beats` with predictable latency.
- Keep output stable with strict verbosity contracts (e.g., 4–5 sentences for `full`, 1–2 for `brief`) while allowing richer prose when budget permits.
- Ensure beats do not leak mechanics or omniscient knowledge, especially in stealth.

### Non-Goals (for this phase)
- Do not implement full narrative planning (multi-turn arcs, foreshadowing).
- Do not add model-specific prompt tuning.
- Do not require new prompt sections beyond the previously adopted prompt.
- Do not implement speculative decoding or model-side optimizations.

---

## 2. API Extensions (Backward-Compatible)

### 2.1 Extend `scope` with domain tags

Add a **domain tag** and optional subtype to `narration.scope`. This is strictly descriptive for engine policies (beat selection, topic fences). The narrator prompt does not need to branch on it.

```json
"scope": {
  "scene_kind": "action_result",
  "intent": "describe_state_change",
  "domain": "default | combat | stealth",
  "subtype": "melee | ranged | spell | pursuit | infiltration | detection",
  "familiarity": "familiar",
  "lead_in": "",
  "allowed_topics": ["observable_actions", "immediate_sensations"],
  "forbidden_topics": ["numbers", "mechanics", "unobserved_causes", "future_plans"]
}
```

**Notes**
- `domain` and `subtype` are optional; defaults are `domain=default`, `subtype=""`.
- The *existing* `allowed_topics` / `forbidden_topics` remain the primary fences.
- `domain/subtype` are used by the engine to set topic fences and beat policy.

### 2.2 Add `secondary_beats` (optional) to `narration`

```json
"secondary_beats": [
  "Rust flakes off onto your palm.",
  "The metal smells faintly of old iron."
]
```

**Contract**
- Beats are short, standalone sentences or fragments that can be turned into sentences.
- Beats must be **player-safe** and consistent with `scope.allowed_topics`.
- Beats are optional; empty list is valid.

---

## 3. Combat and Stealth Scopes

### 3.1 Scope classification

Implement/extend `ScopeClassifier` to assign:

- `domain = combat` when the turn is within combat resolution or a combat-capable mode.
- `domain = stealth` when the turn is within stealth resolution or stealth-capable mode.

**Inputs (typical)**
- `action` (e.g., attack, defend, hide, sneak, observe)
- World state flags (combat active, stealth active)
- Detection state (spotted/unspotted)
- Turn outcomes (hit/miss, noise generated, alarm status)

**Outputs**
- `scope.domain`, `scope.subtype`
- `scope.intent` (usually `describe_state_change` or `describe_observation`, failure as `describe_failure`)
- `allowed_topics` / `forbidden_topics` tuned for domain

### 3.2 Topic fences (recommended defaults)

#### Combat fences (recommended)
- **Allowed:** `observable_actions`, `visible_injury`, `movement`, `immediate_sensations`, `threat_presence`
- **Forbidden:** `numbers`, `hit_chance`, `damage_math`, `cooldowns`, `turn_order`, `AI_state`, `unobserved_causes`

#### Stealth fences (recommended)
- **Allowed:** `sounds`, `shadows`, `light`, `cover`, `immediate_sensations`, `visible_patrol_paths` (only if actually visible)
- **Forbidden:** `exact_positions_of_hidden_units`, `omniscient_explanations`, `mechanics`, `numbers`, `unobserved_causes`

**Critical stealth safety rule**
- The engine MUST NOT place unspotted threats into `entity_refs` or beats. If it is not revealed, it does not exist for narration.

### 3.3 Engine outputs (examples)

#### Combat (full)
```json
{
  "verbosity": "full",
  "narration": {
    "primary_text": "You lunge and drive your blade into the bandit’s side.",
    "secondary_beats": [
      "He staggers back, gasping, and his grip on the club falters.",
      "Your arm jolts from the impact as he scrapes at the wound."
    ],
    "scope": {
      "scene_kind": "action_result",
      "intent": "describe_state_change",
      "domain": "combat",
      "subtype": "melee",
      "allowed_topics": ["observable_actions", "visible_injury", "immediate_sensations"],
      "forbidden_topics": ["numbers", "mechanics", "unobserved_causes"]
    }
  }
}
```

#### Stealth (full)
```json
{
  "verbosity": "full",
  "narration": {
    "primary_text": "You ease along the wall, keeping your breath shallow as you pass the doorway.",
    "secondary_beats": [
      "Floorboards complain softly under your weight, then settle.",
      "A strip of lamplight slides over your sleeve and moves on."
    ],
    "scope": {
      "scene_kind": "action_result",
      "intent": "describe_observation",
      "domain": "stealth",
      "subtype": "infiltration",
      "allowed_topics": ["sounds", "light", "shadows", "immediate_sensations"],
      "forbidden_topics": ["mechanics", "omniscient_explanations", "unobserved_causes"]
    }
  }
}
```

---

## 4. Beat Selection: Dynamic Token-Budget Targeting

### 4.1 Overview

The beat system generates a ranked set of candidate beats and then selects a subset whose estimated token cost fits a **per-turn token budget**. This yields predictable latency and controls richness without changing the narrator prompt.

**Key concept:** The engine decides how many beats to provide; the narrator simply uses them (or not) to satisfy sentence-count rules.

### 4.2 Components

Add a new module, `BeatSelector`, invoked during narration planning.

**Pipeline**

1. **Candidate generation**: collect potential beats from traits, state changes, events, and domain templates.
2. **Filtering**: enforce `allowed_topics/forbidden_topics`, visibility rules (especially stealth), and duplication constraints.
3. **Scoring**: assign each beat a relevance score.
4. **Budget packing**: choose the best beats that fit within the token budget.
5. **Post-processing**: ensure beats are short, clean, and non-redundant.

### 4.3 Beat candidate sources (phase 1)

Since existing mechanism has no beats, start with minimal sources:

- **Traits**: location traits, item traits, actor traits (converted into sensory phrasing)
- **State changes**: injured, moved, opened, revealed, extinguished, etc.
- **Domain templates**:
  - combat: exertion, impact, balance, breath, pain cues
  - stealth: light/shadow, sound control, texture underfoot, breath, timing

**Phase 1 guidance:** Prefer a small number of high-quality, reusable templates rather than many special cases.

### 4.4 Beat format

A beat should be usable as a sentence (or easily made into one).

Good beats:
- “Rust flakes off onto your palm.”
- “Your breath catches at the sudden cold.”
- “Lamplight crawls across the floor and disappears.”

Avoid:
- Mechanics (“-3 HP”, “critical hit”)
- Omniscience (“The guard hasn’t noticed you yet.” unless explicitly revealed)
- Multi-clause paragraphs

### 4.5 Token budget policy

Define a per-turn token budget in the engine. This is independent of model brand and can be tuned empirically.

Recommended policy baseline:

- `brief`: target **0 beats** (fastest, consistent)
- `full`: budgets vary by domain and situation

Example budgets (starting point):
- `full` + default: 60–100 tokens available for beats
- `full` + combat: 30–70 tokens (combat is frequent; keep it snappy)
- `full` + stealth: 50–90 tokens (stealth benefits from sensory detail)

**Important:** Budgets apply only to beats. `primary_text` is always included.

### 4.6 Token estimation

Use a light heuristic (phase 1):
- Estimate tokens ~ `ceil(len(text) / 4)` for English prose (simple proxy).
- Maintain a moving average based on actual observed tokenization later if desired.

### 4.7 Packing algorithm (greedy)

Greedy packing works well because beat lists are small.

Pseudo-code:

```text
budget = target_budget_tokens - est(primary_text)
beats = []

for beat in candidates_sorted_by_score_desc:
  if est(beat.text) <= budget:
    beats.append(beat.text)
    budget -= est(beat.text)
  if len(beats) >= max_beats_cap: break
```

**Caps**
- `max_beats_cap` prevents overstuffing even when budget is large (e.g., 4).
- Separate caps per domain: combat 2–3, stealth 3–4, default 2–3.

### 4.8 Scoring (phase 1)

A simple scoring function is sufficient:

- +3 if beat references a **newly changed** element this turn
- +2 if beat matches **domain subtype** templates (melee, infiltration, etc.)
- +1 if beat uses a **high-salience** entity (from `entity_refs`)
- −2 if beat repeats a trait used in last N turns (see §4.10)
- −3 if beat conflicts with constraints (should be filtered earlier; scoring is belt-and-suspenders)

### 4.9 Interaction with strict sentence counts

The narrator style prompt enforces sentence counts. To support this reliably:

- For `brief`: provide **0 beats** (recommended) or at most 1 in exceptional cases.
- For `full`: provide 1–4 beats depending on budget; narrator uses enough beats to meet 4–5 sentences.

**Engine guardrail:** When `verbosity=full`, ensure at least 1 beat exists for turns where `primary_text` is very short and the style demands 4–5 sentences, unless the style explicitly allows expansion without beats. (If you prefer strict determinism, always provide a minimum of 2 beats for `full` on location_entry/look.)

### 4.10 Reducing repetition (phase 1)

Maintain a small ring buffer of recently used beat “keys”:

- For trait-based beats, key by trait string (e.g., “damp walls”)
- For template beats, key by template id

Avoid reusing keys within a short horizon (e.g., last 3 turns), unless the beat is critical to the current action.

### 4.11 Visibility and stealth constraints

Stealth requires stricter filters:

- No beat may mention an unrevealed entity.
- No beat may assert detection state unless explicitly revealed by engine.
- Candidate generation should not include hidden entities unless revealed.

Implement this as a hard filter before scoring.

---

## 5. Implementation Plan (Incremental)

### Phase 1: Add scopes (combat/stealth) without beats
1. Extend `ScopeClassifier` to output `domain` and domain-specific topic fences.
2. Ensure narration remains correct with `primary_text` only.
3. Add validation rules for scope enums and fences.

### Phase 2: Add beats with token-budget targeting (minimal sources)
1. Implement `BeatSelector` with:
   - trait-based beats
   - small set of domain templates
   - greedy packer with token estimation
2. Start with conservative budgets and low caps.
3. Add repetition buffer.

### Phase 3: Expand beat quality and variety
1. Add state-change beats (open/close, injury, movement, reveal).
2. Add per-subtype template libraries.
3. Add richer scoring signals (salience, novelty, pacing).

---

## 6. Validation and Observability

Add validator checks (pre-inference):
- `narration.primary_text` non-empty
- `scope.domain/subtype` within enum sets (if present)
- Beats contain no forbidden tokens/markers (optional lint)
- For stealth: beats/entity_refs do not mention hidden entities

Add logging/metrics:
- Selected beats count per turn
- Estimated beat token budget vs. actual (if you later compute actual)
- Repetition suppression rate
- Inference latency by domain and verbosity

---

## 7. Compatibility Notes

- Existing games can omit beats entirely; `secondary_beats=[]` is valid.
- `domain/subtype` are optional; if absent, default behavior remains unchanged.
- Narrator prompt remains stable; only the engine’s `narration` plan becomes richer.

---

## 8. Acceptance Criteria

1. Combat and stealth turns produce correct narration without mechanics leakage.
2. Stealth narration never reveals unrevealed threats.
3. Average latency does not regress beyond configured targets when budgets are conservative.
4. Increasing budget on a turn produces perceptibly richer narration without prompt changes.
5. Narration remains consistent with strict sentence-count style rules.

