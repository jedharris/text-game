# Testing with Walkthroughs

## Overview

Walkthroughs are scripted sequences of commands that test game functionality. They can verify both game mechanics and narration quality. This document covers what can be tested and how.

## Current Walkthrough Tool (`tools/walkthrough.py`)

### What It Tests

The current walkthrough tool runs commands through the **game engine only** (no LLM):

```bash
python tools/walkthrough.py examples/spatial_game --file walkthroughs/test.txt
```

**Tests:**
- ✅ Command parsing (via Parser)
- ✅ Game state changes (inventory, location, posture)
- ✅ Success/failure outcomes
- ✅ Game mechanics (puzzles, locks, movement)

**Does NOT test:**
- ❌ LLM parsing (natural language → structured command)
- ❌ LLM narration (structured result → natural language prose)
- ❌ Narration quality (perspective, tone, sentence count)

### What It Shows

**Default output:**
```
[✓] You stand on the bench.
sturdy construction
weathered stone
```

Shows the `primary_text` and `secondary_beats` from the narration plan.

**With `--verbose`:**
- Currently has a bug (UnboundLocalError with `json`)
- Should show full JSON response including narration plan

### Limitations

Since it bypasses the LLM narrator:
- Cannot verify prompt changes affect output
- Cannot catch narration regressions
- Cannot test if narrator follows instructions
- Only sees the "recipe" sent to narrator, not the final prose

## Testing Narration JSON Structure

To verify what JSON gets sent to the narrator (the "narration recipe"), use a direct test script:

### Example Test Script

```python
#!/usr/bin/env python3
from pathlib import Path
from src.game_engine import GameEngine
from src.llm_protocol import LLMProtocolHandler
from src.command_utils import parsed_to_json

game = GameEngine(Path("examples/spatial_game"))
handler = LLMProtocolHandler(game.game_state, game.behavior_manager)
parser = game.create_parser()

def run_command(cmd_text):
    parsed = parser.parse_command(cmd_text)
    message = parsed_to_json(parsed)
    return handler.handle_command(message)

# Test 1: Check entity_refs presence
result = run_command("stand on bench")
narration = result.get("narration", {})
print(f"Entity refs: {narration.get('entity_refs')}")

# Test 2: Check must_mention behavior
result = run_command("north")
narration = result.get("narration", {})
print(f"Familiarity: {narration['scope']['familiarity']}")
print(f"Must mention: {narration.get('must_mention')}")
```

### What You Can Verify

**Entity References:**
- `entity_refs` dict is populated
- Entities have `traits` arrays
- Traits match authored content

**Must Mention Fields:**
- `must_mention` appears/disappears correctly
- Frequency matches expectations (first visit vs familiar)
- Content is properly formatted

**Scope Information:**
- `scene_kind` is correct (location_entry, look, action_result)
- `familiarity` tracks visits (new vs familiar)
- `outcome` matches success/failure

**Viewpoint:**
- `mode` reflects posture (ground, elevated, concealed)
- `posture` is set when relevant

## Phase 1 Testing Example

Testing the three Phase 1 fixes:

```python
# Fix 1: Stand/sit includes entity_refs
result = run_command("stand on bench")
assert result['narration']['entity_refs']  # Should exist
bench_ref = [r for r in result['narration']['entity_refs'].values()
             if 'bench' in r['name'].lower()][0]
assert 'weathered stone' in bench_ref['traits']  # Not hallucinated

# Fix 2: must_mention doesn't leak field names
# (This requires actual LLM narration to verify - see next section)

# Fix 3: Exits only on first visit or explicit look
result1 = run_command("north")  # First visit
result2 = run_command("south")
result3 = run_command("north")  # Returning
result4 = run_command("look")   # Explicit

# First visit should have exits (if familiarity="new")
assert result1['narration']['scope']['familiarity'] == 'new'
assert result1['narration'].get('must_mention')

# Returning should not
assert result3['narration']['scope']['familiarity'] == 'familiar'
assert not result3['narration'].get('must_mention')

# Look always has exits
assert result4['narration'].get('must_mention')
```

### Key Finding from Phase 1

**Familiarity tracking issue discovered:**
- All `location_entry` scenes showed `familiarity: "familiar"` even on first visit
- This is a separate bug in the visit tracking system
- The `must_mention` logic is correct, but never triggers for `familiarity="new"` because familiarity is always "familiar"

## What's Missing: Testing Actual Narration

The current approach tests the **recipe** but not the **meal**. To test narration quality, we need to:

1. **Send commands through the LLM narrator**
2. **Capture the generated prose**
3. **Verify quality criteria**

This would catch:
- Field name leakage ("Must mention: Exits lead...")
- Perspective errors (mixing "you" and "I")
- Material hallucinations (wood vs stone)
- Tone/style violations
- Word duplication ("ball ball")
- Sentence count violations

## Next Steps

See the next section for proposals on extending walkthrough testing to cover end-to-end narration with LLMs.

---

## Testing Philosophy

**Current approach (engine-only walkthroughs):**
- Fast (no LLM calls)
- Reliable (deterministic)
- Tests game logic
- Good for regression testing
- Misses narration quality

**Proposed approach (LLM-augmented walkthroughs):**
- Slower (LLM inference required)
- Non-deterministic (LLM variability)
- Tests full player experience
- Can catch prompt/narrator bugs
- More expensive to run

**Recommendation:** Use both:
- Engine-only walkthroughs for CI and rapid iteration
- LLM walkthroughs for narration quality verification
- Run LLM tests less frequently (manual, pre-release)
