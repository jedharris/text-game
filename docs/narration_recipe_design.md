# Narration Recipe Design

## Problem Statement

The current narrator API sends structured game state to an LLM and expects it to:
1. Parse nested JSON to find relevant fields
2. Follow complex conditional rules (e.g., "if target_state.open is false, don't describe what's beyond")
3. Assemble prose from disparate pieces

Small models (3B parameters) struggle with this. They ignore `action_verb`, hallucinate content not in the data, and describe walking through closed doors.

## Design Goal

Restructure the JSON to be a **narration recipe** - pre-assembled content that the model weaves into prose, rather than raw state it must interpret.

Key principles:
- **Include everything we want mentioned** - pre-written phrases the model should use
- **Exclude everything we don't want** - don't send information that might trigger hallucination
- **Order suggests narrative flow** - fields appear in logical narration order
- **Simple, flat structure** - minimize nesting, maximize visibility

## Proposed Structure

### Current (State-Oriented)
```json
{
  "success": true,
  "action": "unlock",
  "verbosity": "full",
  "narration": {
    "action_verb": "unlock",
    "primary_text": "You unlock the door.",
    "target_state": {"open": false, "locked": false},
    "entity_refs": {
      "door_sanctum": {
        "name": "ornate door",
        "type": "door",
        "traits": ["glowing runes", "heavy iron handle"],
        "state": {"open": false, "locked": false}
      }
    },
    "scope": {"scene_kind": "action_result", "outcome": "success"}
  }
}
```

### Proposed (Narration-Oriented)
```json
{
  "narrate": {
    "action_sentence": "You turn the key and unlock the ornate door.",
    "result_sentence": "The lock clicks open. The door remains closed.",
    "sensory_beats": [
      "The glowing runes pulse briefly.",
      "You hear the mechanism release."
    ],
    "current_view": "The closed door still bars the way upward.",
    "restrictions": "The door is CLOSED. Do not describe what lies beyond it."
  }
}
```

## Field Definitions

### `narrate.action_sentence` (required)
The core statement of what the player did. Pre-written, grammatically complete.
- For unlock: "You turn the key and unlock the ornate door."
- For open: "You push open the ornate door."
- For examine: "You examine the ornate door closely."

### `narrate.result_sentence` (required)
What happened as a result. States the current situation clearly.
- After unlock: "The lock clicks open. The door remains closed."
- After open: "The door swings open, revealing stone stairs beyond."
- For examine: "The door is covered in glowing runes."

### `narrate.sensory_beats` (optional, list)
Atmospheric details the narrator MAY weave in. Selected from entity traits.
- Limit to 2-3 for brief, 4-5 for full verbosity
- Pre-filtered to be appropriate to current state

### `narrate.current_view` (optional)
What the player can currently see. For location scenes and when relevant.
- After unlock (door closed): "The closed door still bars the way."
- After open: "Stone stairs wind upward into darkness."
- Not included for actions where view doesn't change

### `narrate.context` (optional)
Background context like where player came from, time of day, etc.
- "You arrived from the library below."
- Only included when contextually relevant

### `narrate.restrictions` (optional but important)
Explicit statement of what NOT to describe. Reinforces boundaries.
- "The door is CLOSED. Do not describe what lies beyond it."
- "You cannot see the contents of the locked chest."

### `narrate.exits` (for location scenes)
Pre-formatted exit description to include verbatim.
- "Exits lead north to the garden and east through a wooden door."

## Scene Types

### Action Results (unlock, open, close, take, etc.)
```json
{
  "narrate": {
    "action_sentence": "You unlock the ornate door.",
    "result_sentence": "The lock clicks. The door is now unlocked but still closed.",
    "sensory_beats": ["The runes flicker momentarily."],
    "restrictions": "Door is CLOSED - do not describe beyond it."
  }
}
```

### Location Entry (go north, up, etc.)
```json
{
  "narrate": {
    "action_sentence": "You climb the narrow stone stairs.",
    "arriving_at": "Wizard's Sanctum",
    "scene_description": "Arcane symbols cover the floor. A large window overlooks the land.",
    "sensory_beats": ["Ancient dust motes drift in shafts of light."],
    "visible_items": ["stone altar", "pale wand"],
    "exits": "Stairs lead down through the ornate door.",
    "context": "You came up from the library."
  }
}
```

### Examine/Look
```json
{
  "narrate": {
    "action_sentence": "You examine the crystal ball closely.",
    "object_description": "Mist swirls within its depths, occasionally forming shapes.",
    "sensory_beats": ["cool to the touch", "faint inner glow"],
    "current_state": "The ball rests on an ornate silver stand."
  }
}
```

### Failure
```json
{
  "narrate": {
    "action_sentence": "You try to open the door.",
    "failure_reason": "The door is locked.",
    "restriction": "Do not describe opening or entering."
  }
}
```

## Building the Recipe

The `NarrationAssembler` would be updated to:

1. **Compose sentences** rather than passing raw state
2. **Filter sensory_beats** based on current state (no "light spills through" for closed doors)
3. **Generate restrictions** based on state constraints
4. **Include context** like previous location when relevant

### Example: Unlock Door

Handler returns:
```python
HandlerResult(
    success=True,
    primary="You unlock the door.",
    data={"open": False, "locked": False, "name": "ornate door",
          "traits": ["glowing runes", "heavy iron handle"]}
)
```

Assembler builds:
```python
{
    "action_sentence": "You turn the key and unlock the ornate door.",
    "result_sentence": "The lock clicks open. The door remains closed.",
    "sensory_beats": ["The glowing runes pulse as the mechanism releases."],
    "restrictions": "Door is CLOSED. Do not describe beyond it."
}
```

Note: `sensory_beats` only includes traits compatible with "unlock" action on a closed door.

## Evaluation Strategy

### Test Harness
Create a harness that:
1. Captures the JSON sent to the narrator
2. Captures the prose returned
3. Evaluates compliance with expected characteristics

### Evaluation Criteria
For each test case, define:
- **must_contain**: Phrases/concepts that must appear
- **must_not_contain**: Phrases/concepts that must NOT appear
- **style_check**: Voice, sentence count, etc.

### Example Test Case: Unlock Door
```python
{
    "action": "unlock door",
    "must_contain": ["unlock", "door"],
    "must_not_contain": [
        "open", "opens", "opened", "opening",
        "step", "enter", "inside", "beyond",
        "room", "chamber", "space",
        "air", "smell", "light spills"
    ],
    "style_check": {
        "max_sentences": 3,
        "person": "second"  # "you"
    }
}
```

### Metrics
- **Compliance rate**: % of test cases where must_contain is satisfied
- **Hallucination rate**: % of test cases with must_not_contain violations
- **Style adherence**: % matching style constraints

## Migration Path

1. **Phase 1**: Create evaluation harness with current structure, establish baseline ✓ COMPLETE
   - Built `tools/eval_json_structure.py` for inspecting JSON sent to narrator
   - Built `tools/narrator_eval_harness.py` for evaluating narrator compliance
   - Observed: model leaks any mechanical state data we send (e.g., `target_state` fields appear verbatim in output)
   - This validates the "exclude everything we don't want" principle
2. **Phase 2**: Implement recipe builder alongside current assembler
3. **Phase 3**: A/B test recipe vs. current structure
4. **Phase 4**: If recipe performs better, migrate fully

## Open Questions

1. Should `action_sentence` be fully pre-written or partially templated?
   - Full: "You turn the key and unlock the ornate door."
   - Template: "You {action_verb} the {entity_name}." + traits for elaboration
   - **Recommendation**: Simpler templates are probably better for small models.
     Use "You unlock the ornate door." rather than elaborate phrases.

2. How much context is needed?
   - Previous location? ("You came from the library.")
   - Time/turn? ("After some effort...")
   - Player state? ("Clutching the key...")

3. How to handle multi-step narrations?
   - Movement through a door: unlock + open + enter = one narration?
   - Or keep them separate?

4. Should we include `restrictions` at all?
   - The design includes explicit restrictions like "Do not describe what lies beyond."
   - However, small models may ignore restrictions or, worse, use them as ideas for hallucination.
   - The "exclude everything we don't want" principle may be more effective:
     simply don't send any information about what's beyond a closed door.
   - **Recommendation**: Try without restrictions first; add only if needed.
