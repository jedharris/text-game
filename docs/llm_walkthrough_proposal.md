# LLM-Augmented Walkthrough Testing

## Summary

This proposal recommends creating **two complementary walkthrough tools**:

1. **`tools/json_walkthrough.py`** - Automated testing (HIGH PRIORITY)
   - Tests narration JSON structure ("recipe" sent to LLM)
   - Fast, deterministic, suitable for CI
   - Verifies context builder logic (entity_refs, must_mention, scope)
   - Uses JSONPath-style assertions

2. **`tools/llm_walkthrough.py`** - Quality review (LOWER PRIORITY)
   - Tests full end-to-end narration with actual LLM
   - Generates transcripts for review by humans or large models
   - Slower (~1-2s per turn), non-deterministic
   - Good for catching prompt/narrator issues

**Key insight:** Large models (Claude, GPT-4) can effectively review narration transcripts for quality issues like perspective errors, hallucinations, and style violations.

## Goal

Extend walkthrough testing to drive the MLX narrator, enabling end-to-end testing of:
1. **Parser**: Natural language → structured command (LLM input handler)
2. **Narration**: Structured result → natural language prose (LLM narrator)

## What This Enables

### Currently Untestable
- Prompt changes affecting parsing/narration
- LLM perspective errors ("you" vs "I")
- Field name leakage ("Must mention: Exits...")
- Material hallucinations (bench turning from stone to wood)
- Tone/style violations
- Word duplication bugs
- Sentence count adherence

### With LLM Walkthroughs
All of the above become testable by capturing actual LLM output.

## Implementation Options

### Option 1: Extend Existing Walkthrough Tool

Modify `tools/walkthrough.py` to optionally use MLX narrator:

```bash
python tools/walkthrough.py examples/spatial_game \
    --file walkthroughs/test.txt \
    --use-mlx \
    --model qwen-7b
```

**Changes needed:**
1. Add `--use-mlx` flag and `--model` option
2. When enabled, create MLXNarrator instead of direct engine access
3. Process commands through `narrator.process_turn()` instead of handler
4. Capture both narration JSON and final prose
5. Add optional assertions for prose quality

**Pros:**
- Single unified tool
- Reuses existing walkthrough format
- Can compare engine-only vs MLX output

**Cons:**
- Makes walkthrough tool heavier
- Mixing two different testing modes in one tool

### Option 2: New LLM Walkthrough Tool

Create `tools/llm_walkthrough.py` specifically for LLM testing:

```bash
python tools/llm_walkthrough.py examples/spatial_game \
    --file walkthroughs/narration_quality.txt \
    --model qwen-7b \
    --save-transcript output.log
```

**Pros:**
- Cleaner separation of concerns
- Can have LLM-specific features without cluttering main tool
- Easier to optimize for LLM testing workflow

**Cons:**
- Code duplication with existing walkthrough tool
- Two tools to maintain

### Option 3: Hybrid Approach

Keep existing tool simple, create wrapper for LLM mode:

```bash
# Wrapper script that configures walkthrough.py for LLM testing
./scripts/test_narration.sh examples/spatial_game walkthroughs/test.txt
```

**Pros:**
- Minimal changes to existing tool
- Can evolve LLM testing independently

**Cons:**
- Another layer of indirection

## Recommended Approach: Two Complementary Tools

### Tool 1: JSON Walkthrough (Automated Testing)

Create `tools/json_walkthrough.py` for fast, automated testing of narration JSON structure:

```bash
# Run in CI or during development
python tools/json_walkthrough.py examples/spatial_game \
    --file walkthroughs/json/phase1_checks.txt
```

**What it tests:**
- Narration JSON structure (the "recipe" sent to LLM)
- Entity refs presence and content
- Must_mention frequency and conditions
- Scope information (scene_kind, familiarity, outcome)
- Viewpoint data (mode, posture)
- Fast enough for CI (~instant, no LLM inference)

**Example walkthrough format:**
```
# File: walkthroughs/json/phase1_checks.txt

stand on bench
✓ SUCCESS
assert_json: entity_refs is not empty
assert_json: entity_refs contains bench
assert_json: entity_refs[*bench*].traits contains "weathered stone"

north
✓ SUCCESS
assert_json: scope.scene_kind == "location_entry"
# Note: familiarity tracking has a bug - should be "new" on first visit
# assert_json: scope.familiarity == "new"  # DISABLED - bug #XXX

south
✓ SUCCESS

north
✓ SUCCESS
assert_json: scope.familiarity == "familiar"
assert_json: must_mention is empty  # No exits on familiar locations

look
✓ SUCCESS
assert_json: must_mention.exits_text exists  # Look always shows exits
```

**Features:**
- JSONPath-style assertions
- Fast execution (suitable for CI)
- Deterministic (no LLM variability)
- Tests the Context Builder's output
- Can verify fixes to narration assembly logic

### Tool 2: LLM Walkthrough (Quality Review)

Create a dedicated `tools/llm_walkthrough.py` for end-to-end quality verification:

### Core Functionality

```python
#!/usr/bin/env python3
"""LLM-augmented walkthrough testing.

Tests both parsing and narration through the full LLM pipeline.
"""

from pathlib import Path
from src.game_engine import GameEngine

def run_llm_walkthrough(game_dir: Path, commands: list[str],
                        model: str, save_transcript: Path | None = None):
    """Run commands through MLX narrator and capture results."""

    engine = GameEngine(game_dir)
    narrator = engine.create_mlx_narrator(model=model)

    results = []

    # Get opening
    opening = narrator.get_opening()
    results.append({
        "type": "opening",
        "prose": opening
    })

    # Process each command
    for cmd in commands:
        if cmd.startswith("#") or not cmd.strip():
            continue

        response = narrator.process_turn(cmd)

        results.append({
            "type": "turn",
            "input": cmd,
            "prose": response,
            # Optionally capture internal state for debugging
            "narration_json": narrator.last_narration_json  # If exposed
        })

    if save_transcript:
        save_transcript.write_text(format_transcript(results))

    return results
```

### Enhanced Walkthrough Format

Extend the format to support prose assertions:

```
# Standard command
stand on bench
✓ SUCCESS

# Command with prose assertion
north
✓ SUCCESS
expect_prose_contains: "north"
expect_prose_not_contains: "Must mention"
expect_prose_not_contains: "wood"  # Bench is stone, not wood

# Sentence count check
look
✓ SUCCESS
expect_sentence_count: 4-5  # Full verbosity

# Perspective check
examine bench
✓ SUCCESS
expect_perspective: second_person  # Should use "you" not "I"
```

### Output Format

```
============================================================
> stand on bench
------------------------------------------------------------
[✓] SUCCESS

PROSE:
I step onto the weathered stone bench, feeling its cool,
moss-covered surface beneath my feet. The sturdy construction
holds my weight easily.

CHECKS:
  ✓ Contains 'weathered stone'
  ✓ Does not contain 'wood'
  ✗ FAILED: Perspective is first_person, expected second_person

NARRATION JSON:
{
  "entity_refs": {
    "item_garden_bench": {
      "name": "bench",
      "traits": ["weathered stone", "moss-covered", "sturdy construction"]
    }
  }
}
```

### Debugging Support

```bash
# Save full transcript
python tools/llm_walkthrough.py examples/spatial_game \
    --file walkthroughs/test.txt \
    --save-transcript debug.log

# Show narration JSON alongside prose
python tools/llm_walkthrough.py examples/spatial_game \
    --file walkthroughs/test.txt \
    --show-json

# Compare two models
python tools/llm_walkthrough.py examples/spatial_game \
    --file walkthroughs/test.txt \
    --model qwen-7b \
    --compare-with llama-3b
```

## Implementation Requirements

### What Needs to Be Exposed

**From MLXNarrator:**
```python
class MLXNarrator:
    def process_turn(self, player_input: str) -> str:
        """Process turn and return prose."""
        # ... existing ...

    # NEW: Expose internal state for testing
    @property
    def last_narration_json(self) -> dict:
        """Get the narration JSON from the last turn."""
        return self._last_narration_plan

    @property
    def last_parser_output(self) -> dict:
        """Get the parsed command from the last turn."""
        return self._last_parsed_command
```

### Model-Based Review Workflow

LLM walkthroughs enable automated quality review by large models:

```bash
# 1. Generate transcript
python tools/llm_walkthrough.py examples/spatial_game \
    --file walkthroughs/narration/phase1.txt \
    --save-transcript phase1_output.log

# 2. Review with Claude/GPT-4
# Paste transcript into model with prompt:
# "Review this game narration transcript. Check for:
#  - Perspective consistency (should use 'you' not 'I')
#  - Material accuracy (bench is weathered stone, not wood)
#  - Field name leakage (literal 'Must mention:' text)
#  - Tone adherence to narrator_style.txt
#  - Word duplication bugs
#  Report any issues found."

# 3. Model provides structured feedback
# - Lists specific errors with line numbers
# - Suggests fixes
# - Identifies patterns
```

**Benefits:**
- Faster than manual review
- More consistent than human review
- Can process long transcripts
- Identifies subtle issues (tone, style consistency)
- Good for regression testing prompt changes

### File Structure

```
tools/
  json_walkthrough.py      # JSON structure testing (CI-friendly)
  llm_walkthrough.py       # Full LLM testing (manual/model review)

walkthroughs/
  json/
    phase1_checks.txt      # Automated JSON assertions
    entity_refs_tests.txt  # Entity reference verification
  narration/
    phase1_quality.txt     # Full narration quality checks
    parser_tests.txt       # Parser accuracy checks
    style_compliance.txt   # Style guide adherence
```

### Testing Workflow

```bash
# 1. Rapid iteration - JSON assertions (automated, CI)
python tools/json_walkthrough.py examples/spatial_game \
    --file walkthroughs/json/phase1_checks.txt

# 2. Once JSON tests pass, generate narration transcript
python tools/llm_walkthrough.py examples/spatial_game \
    --file walkthroughs/narration/phase1_quality.txt \
    --save-transcript phase1.log

# 3. Review transcript (human or model)
python tools/llm_walkthrough.py examples/spatial_game \
    --file walkthroughs/narration/phase1_verification.txt \
    --model qwen-7b

# 4. Save transcript for review
python tools/llm_walkthrough.py examples/spatial_game \
    --file walkthroughs/narration/phase1_verification.txt \
    --model qwen-7b \
    --save-transcript phase1_test.log
```

## Cost Considerations

**Engine-only walkthrough:**
- Instant
- Free
- Deterministic

**LLM walkthrough (7B model):**
- ~1-2 seconds per turn (MLX on M-series Mac)
- Free (local inference)
- Non-deterministic (use temperature=0 for more consistency)

**For a 20-command walkthrough:**
- Engine: < 1 second
- MLX: ~30-40 seconds

**Recommendation:**
- Run engine tests in CI
- Run LLM tests manually or in nightly builds
- Use LLM tests for narrator-specific changes (prompts, protocol)

## Example Use Cases

### Phase 1 Verification

```
# File: walkthroughs/narration/phase1_fixes.txt

# Test 1: Entity refs prevent hallucinations
stand on bench
✓ SUCCESS
expect_prose_contains: "stone"
expect_prose_not_contains: "wood"

# Test 2: Must_mention doesn't leak
north
✓ SUCCESS
expect_prose_not_contains: "Must mention"
expect_prose_not_contains: "exits_text"

# Test 3: Exits only on first visit
south
✓ SUCCESS
expect_prose_not_contains: "Exits lead"  # Familiar location

look
✓ SUCCESS
expect_prose_contains: "north"  # Look always shows exits
```

### Parser Testing

```
# File: walkthroughs/narration/parser_tests.txt

# Test natural language variations
put the golden key in my pocket
✓ SUCCESS

place key in pocket
✓ SUCCESS

stash the key
✓ SUCCESS

# Test ambiguity resolution
take key
✓ SUCCESS
# Should ask "Which key?" if multiple keys present

# Test failure cases
xyzzy
✗ FAILURE
expect_prose_contains: "don't understand"
```

## Next Steps

### Phase 1: JSON Walkthrough Tool (High Priority - CI Testing)
1. **Implement `tools/json_walkthrough.py`**
   - Parse walkthrough files with JSON assertions
   - Run commands through LLMProtocolHandler
   - Evaluate JSONPath-style assertions
   - Report pass/fail with clear error messages
2. **Create assertion syntax**
   - `assert_json: path.to.field exists`
   - `assert_json: path.to.field == value`
   - `assert_json: path.to.field contains substring`
   - `assert_json: path.to.field is empty`
3. **Convert Phase 1 test script to walkthrough**
   - Migrate `test_narration_json.py` logic to walkthrough format
   - Add to CI if appropriate
4. **Document patterns** - Best practices for JSON assertions

### Phase 2: LLM Walkthrough Tool (Lower Priority - Manual Review)
1. **Expose narrator internals** - Add properties for test access
2. **Implement core tool** - Basic LLM walkthrough runner
3. **Add transcript formatting** - Clear, reviewable output
4. **Create test walkthroughs** - Convert manual tests
5. **Document model review workflow** - How to use Claude/GPT-4 for review

## Design Decisions

1. **Prose assertions: INLINE** ✓
   - Keep assertions with commands in same file
   - Easier to maintain - no sync issues
   - More readable - see expectation with command

2. **Non-determinism: HUMAN/MODEL REVIEW** ✓
   - LLM walkthroughs produce transcripts for review by humans OR large models
   - Large models (Claude, GPT-4) can effectively spot narration errors:
     - Perspective inconsistencies ("you" vs "I")
     - Material hallucinations (stone → wood)
     - Field name leakage ("Must mention: ...")
     - Tone/style violations
     - Word duplication bugs
   - Use cases: bug reports, regression investigation, quality verification
   - Automated assertions stay in JSON testing (fast, deterministic)

3. **Visual diff: DEFERRED**
   - Potentially useful feature
   - Defer until specific need arises
   - Can add later without breaking changes

4. **Test infrastructure integration**
   - **LLM walkthroughs**: Manual only, not in CI (too slow, for review purposes)
   - **JSON walkthroughs**: Should consider adding to unittest/CI
   - Growing dependency on walkthroughs for verification suggests JSON testing should be automated
